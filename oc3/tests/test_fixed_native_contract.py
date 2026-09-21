"""Focused synthetic tests for the fixed native-resource contract stage."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oc3_fixed_native_resource_contract as cli
from oc3lib.core import canonical, file_hash
from oc3lib import fixed_native_contract as stage


PROJECT = Path(__file__).resolve().parents[2]
BINDING = PROJECT / stage.BINDING_RELATIVE
CONTRACT = PROJECT / stage.CONTRACT_RELATIVE
PSF_CONTRACT = PROJECT / stage.PSF_CONTRACT_RELATIVE


def card(key, value=None):
    if value is None:
        text = key
    elif isinstance(value, bool):
        text = f"{key:<8}= {'T' if value else 'F':>20}"
    elif isinstance(value, str):
        text = f"{key:<8}= '{value}'"
    else:
        text = f"{key:<8}= {value:>20}"
    return text.ljust(80).encode("ascii")


def header(cards, blocks=1):
    capacity = blocks * 36
    fillers = [card(f"K{index:07d}", index)
               for index in range(capacity - len(cards) - 1)]
    value = b"".join(cards + fillers + [card("END")])
    assert len(value) == blocks * stage.HEADER_BLOCK
    return value


PRIMARY = header([card("SIMPLE", True), card("BITPIX", 8),
                  card("NAXIS", 0), card("EXTEND", True)])


def payload(product="image", blocks=1):
    cards = [
        card("XTENSION", "BINTABLE"), card("BITPIX", 8), card("NAXIS", 2),
        card("NAXIS1", 16), card("NAXIS2", 1), card("PCOUNT", 0), card("GCOUNT", 1),
        card("ZIMAGE", True), card("ZBITPIX", -32), card("ZNAXIS", 2),
        card("ZNAXIS1", 3600), card("ZNAXIS2", 3600), card("ZCMPTYPE", "RICE_1"),
        card("IMTYPE", product), card("BUNIT", "nanomaggy"),
        card("CTYPE1", "RA---TAN"), card("CTYPE2", "DEC--TAN"),
        card("CRPIX1", 1800.5), card("CRPIX2", 1800.5),
        card("CRVAL1", 1.0), card("CRVAL2", 2.0),
        card("CD1_1", -0.0000727778), card("CD1_2", 0.0),
        card("CD2_1", 0.0), card("CD2_2", 0.0000727778),
    ]
    return PRIMARY + header(cards, blocks)


def production_contract():
    return json.loads(CONTRACT.read_text())


def production_binding():
    binding, _ = stage.load_probe_binding(BINDING, PROJECT)
    return binding


class FakeTransport:
    def __init__(self, binding, fail_resource=None):
        self.resources = {row["literal_url"]: row for row in binding["resources"]}
        self.data = {url: payload(row["product"]) for url, row in self.resources.items()}
        self.fail_resource = fail_resource
        self.calls = []

    def head(self, url):
        row = self.resources[url]
        self.calls.append(("HEAD", row["resource_id"]))
        return 200, {"content-length": str(len(self.data[url]) + 100000),
                     "content-encoding": "identity", "etag": '"synthetic"'}, b"", url

    def range(self, url, start, end):
        row = self.resources[url]
        self.calls.append(("RANGE", row["resource_id"], start, end))
        body = self.data[url][start:end + 1]
        status = 500 if row["resource_id"] == self.fail_resource else 206
        length = len(self.data[url]) + 100000
        return status, {"content-range": f"bytes {start}-{end}/{length}",
                        "content-encoding": "identity"}, body, url


class FixedNativeContractTests(unittest.TestCase):
    def test_001_exact_twelve_identities(self):
        contract = production_contract()
        identities = [(r["fields"]["region"]["value"],
                       r["fields"]["product"]["value"],
                       r["fields"]["band"]["value"]) for r in contract["resources"]]
        self.assertEqual(identities, list(stage.RESOURCE_ORDER))

    def test_002_reuses_frozen_directory_components(self):
        contract = production_contract()
        by_region = {r["fields"]["region"]["value"]:
                     r["fields"]["directory_component"]["value"]
                     for r in contract["resources"]}
        self.assertEqual(by_region, {"south": "344", "north": "247"})
        self.assertTrue(all(r["fields"]["directory_component"]["state"] ==
                            "OBSERVED_BY_BOUNDED_PROBE" for r in contract["resources"]))

    def test_003_exact_grz_inventory(self):
        contract = production_contract()
        for region in ("south", "north"):
            for product in ("image", "invvar"):
                bands = [r["fields"]["band"]["value"] for r in contract["resources"]
                         if r["fields"]["region"]["value"] == region and
                         r["fields"]["product"]["value"] == product]
                self.assertEqual(bands, ["g", "r", "z"])

    def test_004_image_primary_role_is_documented(self):
        images = [r for r in production_contract()["resources"]
                  if r["fields"]["product"]["value"] == "image"]
        self.assertTrue(all(r["fields"]["logical_hdu"] ==
                            {"state": "DOCUMENTED", "value": "PRIMARY",
                             "evidence": ["https://www.legacysurvey.org/dr9/files/#image-stacks-region-coadd"]}
                            for r in images))

    def test_005_invvar_hdu_unresolved_until_observed(self):
        contract = production_contract()
        invvars = [r for r in contract["resources"]
                   if r["fields"]["product"]["value"] == "invvar"]
        self.assertTrue(all(r["fields"]["logical_hdu"]["state"] == "UNRESOLVED"
                            for r in invvars))
        with self.assertRaisesRegex(stage.FixedNativeContractError,
                                    "FIXED_CONTRACT_UNRESOLVED"):
            stage.validate_fixed_native_contract(contract, require_resolved=True)

    def test_006_literal_url_families(self):
        binding = production_binding()
        self.assertTrue(all(r["literal_url"].endswith(
            f"legacysurvey-{r['brick']}-{r['product']}-{r['band']}.fits.fz")
                            for r in binding["resources"]))

    def test_007_aligned_header_ranges_stop_at_data(self):
        resource = production_binding()["resources"][0]
        data = payload(resource["product"], blocks=3)
        calls = []
        result = stage.inspect_header(resource,
            lambda start, end: calls.append((start, end)) or data[start:end + 1])
        self.assertTrue(all(start % 2880 == 0 and end - start + 1 == 2880
                            for start, end in calls))
        self.assertTrue(all(end < result["first_data_offset"] for _, end in calls))
        self.assertEqual(len(calls), 4)

    def test_008_science_canary_is_never_requested(self):
        resource = production_binding()["resources"][0]
        data = payload(resource["product"]) + b"SCIENCE_PIXEL_CANARY" * 1000
        calls = []
        result = stage.inspect_header(resource,
            lambda start, end: calls.append((start, end)) or data[start:end + 1])
        self.assertEqual(result["science_pixel_values_observed"], 0)
        self.assertEqual(calls[-1][1], result["first_data_offset"] - 1)

    def test_009_durable_head_and_resource_checkpoints(self):
        binding = production_binding()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "probe"
            terminal, success = stage.run_probe(binding, production_contract(),
                                                FakeTransport(binding), root)
            self.assertTrue(success)
            self.assertEqual(len(list((root / "HEAD_EVIDENCE").glob("*.json"))), 12)
            self.assertEqual(len(list((root / "RESOURCE_CHECKPOINTS").glob("*.json"))), 12)
            self.assertEqual(terminal["science_pixel_values_observed"], 0)

    def test_010_cumulative_accounting_starts_at_194(self):
        binding = production_binding()
        with tempfile.TemporaryDirectory() as td:
            store = stage.EvidenceStore(Path(td) / "probe", binding)
            self.assertEqual(store.aggregate["counters"]["cumulative_requests"], 194)
            self.assertEqual(store.aggregate["counters"]["cumulative_body_bytes"], 93663566)
            store.reserve("HEAD", binding["resources"][0]["resource_id"])
            self.assertEqual(store.aggregate["counters"]["cumulative_requests"], 195)

    def test_011_historical_200_is_not_future_hard_stop(self):
        binding = production_binding()
        with tempfile.TemporaryDirectory() as td:
            store = stage.EvidenceStore(Path(td) / "probe", binding)
            for row in binding["resources"][:7]:
                store.reserve("HEAD", row["resource_id"])
            self.assertEqual(store.aggregate["counters"]["cumulative_requests"], 201)

    def test_012_partial_probe_preserves_completed_resource(self):
        binding = production_binding()
        failed = binding["resources"][1]["resource_id"]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "probe"
            terminal, success = stage.run_probe(binding, production_contract(),
                                                FakeTransport(binding, failed), root)
            self.assertFalse(success)
            self.assertEqual(terminal["state"], stage.PARTIAL)
            first = binding["resources"][0]["resource_id"]
            self.assertTrue((root / "RESOURCE_CHECKPOINTS" / f"{first}.json").is_file())
            self.assertEqual(len(list((root / "HEAD_EVIDENCE").glob("*.json"))), 12)

    def test_013_exact_frozen_six_locations(self):
        before = file_hash(PROJECT / stage.LOCATIONS_RELATIVE)
        stage.verify_locations(PROJECT)
        self.assertEqual(before, stage.LOCATIONS_FILE_SHA256)
        self.assertEqual(file_hash(PROJECT / stage.LOCATIONS_RELATIVE), before)

    def test_014_exact_eighteen_psf_points(self):
        value = json.loads(PSF_CONTRACT.read_text())
        self.assertEqual(len(value["spatial_points"]), 18)
        self.assertEqual([(p["point_id"], p["offset_xy"]) for p in value["spatial_points"][:3]],
                         [("P0", [0, 0]), ("P1", [-32, -32]), ("P2", [32, 32])])

    def test_015_exact_fifty_four_observational_identities(self):
        value = json.loads(PSF_CONTRACT.read_text())
        self.assertEqual(len(value["observational_identities"]), 54)
        self.assertEqual(len({r["identity_id"] for r in value["observational_identities"]}), 54)

    def test_016_transport_bundling_is_independent(self):
        value = json.loads(PSF_CONTRACT.read_text())
        self.assertEqual(len(value["transport_requests"]), 18)
        groups = {}
        for identity in value["observational_identities"]:
            groups.setdefault(identity["transport_id"], set()).add(identity["band"])
        self.assertEqual(set(map(frozenset, groups.values())), {frozenset(stage.BANDS)})

    def test_017_region_layer_binding(self):
        value = json.loads(PSF_CONTRACT.read_text())
        for point in value["spatial_points"]:
            expected = "ls-dr9-south" if point["region"] == "south" else "ls-dr9-north"
            self.assertEqual(point["layer"], expected)

    def test_018_no_location_mutation_from_builders(self):
        path = PROJECT / stage.LOCATIONS_RELATIVE
        before = path.read_bytes()
        stage.build_fixed_native_contract(PROJECT)
        stage.build_psf_contract(PROJECT)
        self.assertEqual(path.read_bytes(), before)

    def test_019_binding_is_canonical_and_exact(self):
        raw = BINDING.read_bytes()
        value = json.loads(raw)
        self.assertEqual(raw, canonical(value) + b"\n")
        stage.validate_probe_binding(value, PROJECT, production_contract())
        self.assertFalse(value["acquisition_authorized"])

    def test_020_probe_success_resolves_invvar_layout(self):
        binding = production_binding()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "probe"
            terminal, success = stage.run_probe(binding, production_contract(),
                                                FakeTransport(binding), root)
            resolved = json.loads((root / "FIXED_NATIVE_RESOURCE_CONTRACT_RESOLVED.json").read_text())
            self.assertTrue(success)
            stage.validate_fixed_native_contract(resolved, require_resolved=True)
            invvars = [r for r in resolved["resources"]
                       if r["fields"]["product"]["value"] == "invvar"]
            self.assertTrue(all(r["fields"]["logical_hdu"]["state"] ==
                                "OBSERVED_BY_BOUNDED_PROBE" for r in invvars))
            self.assertEqual(terminal["bulk_get_requests"], 0)

    def test_021_dry_run_zero_network(self):
        value = stage.dry_run(production_binding(), PROJECT)
        self.assertEqual(value["network_requests"], 0)
        self.assertEqual(value["resources"], 12)
        self.assertEqual(value["max_new_requests"], 204)
        self.assertEqual(value["max_range_body_bytes"], 552960)

    def test_022_cli_dry_run(self):
        with patch("builtins.print"):
            code = cli.main(["--dry-run", "--project", str(PROJECT),
                             "--binding", str(BINDING)])
        self.assertEqual(code, 0)

    def test_023_source_has_no_pixel_decoder(self):
        source = Path(stage.__file__).read_text()
        for forbidden in (".data", "memmap=", "getdata(", "fits.open(",
                          "imshow(", "jpeg", "cutout"):
            self.assertNotIn(forbidden, source)

    def test_024_psf_band_parameter_is_not_forced(self):
        value = json.loads(PSF_CONTRACT.read_text())
        self.assertTrue(all(row["query_bands_parameter"] is None
                            for row in value["transport_requests"]))
        self.assertTrue(all("bands=" not in row["literal_url"]
                            for row in value["transport_requests"]))

    def test_025_psf_units_and_deployment_stay_unresolved(self):
        provider = json.loads(PSF_CONTRACT.read_text())["provider_contract"]
        self.assertEqual(provider["units"]["state"], "UNRESOLVED")
        self.assertEqual(provider["deployment_version"]["state"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
