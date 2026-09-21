"""Focused synthetic tests for the bounded DR9 resource contract stage."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oc3_resource_contract as cli
import oc3lib.resource_contract as stage
from oc3lib.core import canonical


PROJECT = Path(__file__).resolve().parents[2]
BRICKS = PROJECT / "oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv"
REAL_CONTRACT_PATH = (PROJECT /
    "oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/RESOURCE_CONTRACT_RESOLVED.json")
CANDIDATE_PATH = PROJECT / stage.AUXILIARY_CANDIDATE_RELATIVE


def card(key, value=None):
    if value is None: text = key
    elif isinstance(value, bool): text = f"{key:<8}= {'T' if value else 'F':>20}"
    elif isinstance(value, str): text = f"{key:<8}= '{value}'"
    else: text = f"{key:<8}= {value:>20}"
    return text.ljust(80).encode("ascii")


def header(cards):
    raw = b"".join(cards + [card("END")])
    return raw.ljust(((len(raw) + 2879) // 2880) * 2880, b" ")


PRIMARY = header([card("SIMPLE", True), card("BITPIX", 8), card("NAXIS", 0), card("EXTEND", True)])
COMPRESSED = header([card("XTENSION", "BINTABLE"), card("BITPIX", 8), card("NAXIS", 2),
                     card("NAXIS1", 16), card("NAXIS2", 1), card("PCOUNT", 0),
                     card("ZIMAGE", True), card("ZBITPIX", -32), card("ZNAXIS", 2),
                     card("ZNAXIS1", 3600), card("ZNAXIS2", 3600)])
HEADER_BYTES = PRIMARY + COMPRESSED


def base_contract():
    return stage.build_contract({"south": "0001p001", "north": "0002m002"})


def probe_binding(contract):
    rows = []
    for row in contract["resources"][:14]:
        region = row["region"]["value"]; brick = row["brick"]["value"]
        filename = row["filename"]["value"]; directory = "verified_" + region
        rows.append({"resource_id": row["resource_id"], "region": region, "brick": brick,
                     "product": row["product"]["value"], "band": row["band"]["value"],
                     "filename": filename, "directory_component": directory,
                     "literal_url": f"https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/{region}/coadd/{directory}/{brick}/{filename}",
                     "max_bytes": 100_000})
    return stage._seal({"schema_version": stage.PROBE_BINDING_VERSION, "stage_id": stage.PROBE_ID,
                        "development_bricks_sha256": stage.BRICKS_SHA256,
                        "aaa_evidence": {"south": ["reviewed:test"], "north": ["reviewed:test"]},
                        "resources": rows})


class ProbeTransport:
    def __init__(self, binding, bad_range=False):
        self.binding = {r["literal_url"]: r for r in binding["resources"]}; self.calls = []
        self.bad_range = bad_range
    def head(self, url):
        self.calls.append(("HEAD", url)); return 200, {"content-length": "100000", "accept-ranges": "bytes"}, b"", url
    def range(self, url, start, end):
        self.calls.append(("RANGE", url, start, end)); body = HEADER_BYTES[start:end + 1]
        total = 100000; cr = f"bytes {start}-{end}/{total}"
        return (200 if self.bad_range else 206), {"content-range": cr}, body, url


def resolved_contract(contract, size=16):
    value = json.loads(json.dumps(contract))
    for row in value["resources"][:14]:
        region = row["region"]["value"]; brick = row["brick"]["value"]
        filename = row["filename"]["value"]; directory = "verified_" + region
        url = f"https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/{region}/coadd/{directory}/{brick}/{filename}"
        row["literal_url"] = stage._prop("OBSERVED_BY_BOUNDED_PROBE", url, "synthetic")
        row["directory_component"] = stage._prop("OBSERVED_BY_BOUNDED_PROBE", directory, "synthetic")
        row["max_bytes"] = stage._prop("OBSERVED_BY_BOUNDED_PROBE", size, "synthetic")
        prior = row["hdu_contract"]["value"] or {}
        row["hdu_contract"] = stage._prop("OBSERVED_BY_BOUNDED_PROBE",
                                          {**prior, "physical_image_hdu": 1,
                                           "compression_mapping": "synthetic"}, "synthetic")
    return stage._seal(value)


def production_contract():
    return stage.load_canonical_json(REAL_CONTRACT_PATH)


def acquisition_candidate(contract):
    return stage.build_acquisition_candidate(contract, PROJECT)


def authorization(candidate, resume=False):
    candidate_sha = hashlib.sha256(canonical(candidate) + b"\n").hexdigest()
    return stage._seal({
        "schema_version": stage.ACQUISITION_AUTHORIZATION_SCHEMA,
        "authorization_type": "AUXILIARY_14_ACQUISITION_FINAL_HUMAN_AUTHORIZATION",
        "authorization_state": "FINAL_HUMAN_AUTHORIZATION", "authorized": True,
        "authorized_by": "synthetic test", "authorized_at_utc": "2026-09-21T00:00:00Z",
        "stage_id": stage.STAGE_ID, "scope": "AUXILIARY_14_ONLY",
        "candidate_path": str(CANDIDATE_PATH.resolve()), "candidate_sha256": candidate_sha,
        "resume": resume,
    })


class BulkTransport:
    def __init__(self, contract, fail_get=None):
        self.fail_get = fail_get; self.calls = []
        self.urls = {r["literal_url"]["value"]: r["resource_id"] for r in contract["resources"][:14]}
        self.rows = {r["resource_id"]: r for r in contract["resources"][:14]}
    def head(self, url):
        rid = self.urls[url]; row = self.rows[rid]; self.calls.append(("HEAD", rid))
        constraints = row["representation_constraints"]["value"]
        return 200, {"content-length": str(row["max_bytes"]["value"]),
                     "etag": constraints["etag"]}, b"", url
    def get(self, url, max_bytes):
        rid = self.urls[url]; self.calls.append(("GET", rid))
        status = 500 if rid == self.fail_get else 200
        size = self.rows[rid]["max_bytes"]["value"]; body = b"x" * size
        return status, {"content-length": str(size)}, body, url


def descriptors(paths, contract):
    result = []
    for row in contract["resources"][:14]:
        result.append({"resource_id": row["resource_id"], "region": row["region"]["value"],
                       "shape": [3600, 3600], "ndim": 2, "wcs_vector": [1.0] * 8,
                       "resampled": False})
    return result


class ResourceContractTests(unittest.TestCase):
    def test_01_frozen_two_bricks(self):
        self.assertEqual(set(stage.load_frozen_bricks(BRICKS)), {"south", "north"})

    def test_02_exact_14_aux_and_12_future(self):
        rows = base_contract()["resources"]
        self.assertEqual(sum(r["batch"] == "AUXILIARY_FIRST" for r in rows), 14)
        self.assertEqual(sum(r["batch"] == "FUTURE_IMAGE_INVVAR" for r in rows), 12)

    def test_03_exact_aux_order(self):
        rows = base_contract()["resources"][:14]
        got = tuple((r["region"]["value"], r["product"]["value"], r["band"]["value"]) for r in rows)
        self.assertEqual(got, stage.AUX_ORDER)

    def test_04_filename_families(self):
        for row in base_contract()["resources"]:
            self.assertTrue(row["filename"]["value"].startswith("legacysurvey-"))
            self.assertTrue(row["filename"]["value"].endswith(".fits.fz"))

    def test_05_aaa_and_url_initially_unresolved(self):
        for row in base_contract()["resources"]:
            self.assertEqual(row["directory_component"]["state"], "UNRESOLVED")
            self.assertIsNone(row["literal_url"]["value"])

    def test_06_documented_and_observed_states(self):
        contract = base_contract(); binding = probe_binding(contract)
        resolved, _ = stage.probe_contract(contract, binding, ProbeTransport(binding))
        self.assertEqual(resolved["resources"][0]["filename"]["state"], "DOCUMENTED")
        self.assertEqual(resolved["resources"][0]["literal_url"]["state"], "OBSERVED_BY_BOUNDED_PROBE")

    def test_07_image_primary_rule(self):
        image = next(r for r in base_contract()["resources"] if r["product"]["value"] == "image")
        self.assertEqual(image["hdu_contract"]["value"]["logical_hdu"], 0)

    def test_08_maskbits_hdu1_optical(self):
        mask = next(r for r in base_contract()["resources"] if r["product"]["value"] == "maskbits")
        self.assertEqual(mask["hdu_contract"]["value"]["logical_hdu"], 1)
        self.assertEqual(mask["hdu_contract"]["value"]["excluded_logical_hdus"], [2, 3])

    def test_09_three_products_hdu_unresolved(self):
        for product in ("invvar", "nexp", "psfsize"):
            row = next(r for r in base_contract()["resources"] if r["product"]["value"] == product)
            self.assertEqual(row["hdu_contract"]["state"], "UNRESOLVED")

    def test_10_compressed_physical_mapping_observed(self):
        binding = probe_binding(base_contract()); resolved, _ = stage.probe_contract(base_contract(), binding, ProbeTransport(binding))
        self.assertEqual(resolved["resources"][0]["hdu_contract"]["value"]["physical_image_hdu"], 1)

    def test_11_probe_decodes_no_science_pixels(self):
        binding = probe_binding(base_contract()); _, summary = stage.probe_contract(base_contract(), binding, ProbeTransport(binding))
        self.assertEqual(summary["science_pixels_decoded"], 0)
        self.assertTrue(all(o["fits"]["science_pixels_decoded"] == 0 for o in summary["observations"].values()))

    def test_12_all_heads_before_ranges(self):
        binding = probe_binding(base_contract()); transport = ProbeTransport(binding)
        stage.probe_contract(base_contract(), binding, transport)
        self.assertEqual([c[0] for c in transport.calls[:14]], ["HEAD"] * 14)
        self.assertNotIn("HEAD", [c[0] for c in transport.calls[14:]])

    def test_13_probe_has_no_bulk_get(self):
        binding = probe_binding(base_contract()); transport = ProbeTransport(binding)
        stage.probe_contract(base_contract(), binding, transport)
        self.assertFalse(any(c[0] == "GET" for c in transport.calls))

    def test_14_range_must_be_exact_206(self):
        binding = probe_binding(base_contract())
        with self.assertRaisesRegex(stage.ResourceContractError, "RANGE_NOT_EXACT"):
            stage.probe_contract(base_contract(), binding, ProbeTransport(binding, bad_range=True))

    def test_15_binding_rejects_unverified_aaa(self):
        value = probe_binding(base_contract()); value["aaa_evidence"]["south"] = []; value = stage._seal(value)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "binding.json"; p.write_bytes(canonical(value) + b"\n")
            with self.assertRaisesRegex(stage.ResourceContractError, "PROBE_BINDING_INVALID"):
                stage.load_probe_binding(p, base_contract())

    def test_16_binding_rejects_wrong_url_path(self):
        value = probe_binding(base_contract()); value["resources"][0]["literal_url"] += ".wrong"; value = stage._seal(value)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "binding.json"; p.write_bytes(canonical(value) + b"\n")
            with self.assertRaisesRegex(stage.ResourceContractError, "PROBE_URL_INVALID"):
                stage.load_probe_binding(p, base_contract())

    def test_17_imported_global_accounting(self):
        budget = base_contract()["budget"]
        self.assertEqual((budget["used_bytes"], budget["used_requests"]), (89_461_646, 8))
        self.assertEqual((budget["remaining_bytes"], budget["remaining_requests"]), (1_521_151_090, 192))

    def test_18_insufficient_budget_fails_before_get(self):
        contract = production_contract(); candidate = acquisition_candidate(contract)
        transport = BulkTransport(contract)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); state = stage._load_state(root / "AUXILIARY_LEDGER.json")
            state["used_bytes"] = stage.GLOBAL_MAX_BYTES - 1
            stage._write_state(root / "AUXILIARY_LEDGER.json", state)
            with self.assertRaisesRegex(stage.ResourceContractError, "INSUFFICIENT_GLOBAL_BUDGET_BEFORE_GET"):
                stage.acquire_auxiliary(
                    contract, candidate, authorization(candidate), transport, root, descriptors,
                    project=PROJECT, candidate_path=CANDIDATE_PATH)
        self.assertTrue(transport.calls and all(c[0] == "HEAD" for c in transport.calls))

    def test_19_exact_acquisition_order_and_publication(self):
        contract = production_contract(); candidate = acquisition_candidate(contract)
        transport = BulkTransport(contract)
        with tempfile.TemporaryDirectory() as td:
            terminal = stage.acquire_auxiliary(
                contract, candidate, authorization(candidate), transport, Path(td), descriptors,
                project=PROJECT, candidate_path=CANDIDATE_PATH)
            self.assertEqual(terminal["state"], stage.SUCCESS_TERMINAL)
            self.assertEqual([c[0] for c in transport.calls[:14]], ["HEAD"] * 14)
            self.assertEqual([c[1] for c in transport.calls[14:]], [r["resource_id"] for r in contract["resources"][:14]])
            self.assertEqual(len(list((Path(td) / "RAW_IMMUTABLE").glob("*.fits.fz"))), 14)
            ledger = json.loads((Path(td) / "AUXILIARY_LEDGER.json").read_text())
            self.assertEqual(ledger["body_plan_reserved"], stage.ACQUISITION_EXPECTED_BODY_BYTES)

    def test_20_partial_failure_requires_resume_authorization(self):
        contract = production_contract(); candidate = acquisition_candidate(contract)
        fail = contract["resources"][1]["resource_id"]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(stage.ResourceContractError, "AUXILIARY_GET_FAILURE"):
                stage.acquire_auxiliary(
                    contract, candidate, authorization(candidate), BulkTransport(contract, fail_get=fail),
                    root, descriptors, project=PROJECT, candidate_path=CANDIDATE_PATH)
            with self.assertRaisesRegex(stage.ResourceContractError, "SEPARATE_RESUME_AUTHORIZATION_REQUIRED"):
                stage.acquire_auxiliary(
                    contract, candidate, authorization(candidate), BulkTransport(contract), root,
                    descriptors, project=PROJECT, candidate_path=CANDIDATE_PATH)

    def test_21_resume_requires_sealed_resume_flag(self):
        contract = production_contract(); candidate = acquisition_candidate(contract)
        fail = contract["resources"][0]["resource_id"]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(stage.ResourceContractError):
                stage.acquire_auxiliary(
                    contract, candidate, authorization(candidate), BulkTransport(contract, fail_get=fail),
                    root, descriptors, project=PROJECT, candidate_path=CANDIDATE_PATH)
            with self.assertRaisesRegex(stage.ResourceContractError, "ACQUISITION_AUTHORIZATION_INVALID"):
                stage.acquire_auxiliary(
                    contract, candidate, authorization(candidate), BulkTransport(contract), root,
                    descriptors, project=PROJECT, candidate_path=CANDIDATE_PATH, resume=True)

    def test_22_grid_wcs_mismatch_fails_without_resampling(self):
        rows = descriptors([], base_contract()); rows[-1]["wcs_vector"][0] += 1e-3
        with self.assertRaisesRegex(stage.ResourceContractError, "AUXILIARY_GRID_MISMATCH"):
            stage.validate_native_grids(rows)

    def test_23_no_location_selection_in_contract_or_terminal(self):
        serialized = canonical(base_contract()).decode()
        self.assertNotIn('"locations"', serialized)
        self.assertNotIn('"location_selection":true', serialized)

    def test_24_dry_run_zero_network_and_exact_inventory(self):
        with patch.object(stage.LiteralHTTPTransport, "__init__", side_effect=AssertionError("network")):
            result = stage.dry_run(BRICKS, PROJECT)
        self.assertEqual(result["inventory_count"], 14)
        self.assertEqual(result["network_requests"], 0)
        self.assertFalse(result["bulk_authorized"])

    def test_25_cli_help_and_dry_run(self):
        with self.assertRaises(SystemExit) as caught: cli.parser().parse_args(["--help"])
        self.assertEqual(caught.exception.code, 0)
        with patch("builtins.print"):
            self.assertEqual(cli.main(["--dry-run", "--project", str(PROJECT)]), 0)

    def test_26_schema_is_closed(self):
        schema = json.loads((PROJECT / "oc3/schemas/oc3_dr9_coadd_resource_contract_001.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["$defs"]["resource"]["additionalProperties"])

    def test_27_probe_runtime_cap_stops_before_excess_request(self):
        binding = probe_binding(base_contract()); transport = ProbeTransport(binding)
        with self.assertRaisesRegex(stage.ResourceContractError, "PROBE_BUDGET_EXCEEDED"):
            stage.probe_contract(base_contract(), binding, transport, max_requests=14)
        self.assertEqual(len(transport.calls), 14)


if __name__ == "__main__":
    unittest.main()
