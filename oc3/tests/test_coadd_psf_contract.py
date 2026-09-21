"""Synthetic-only tests for the bounded coadd-PSF semantics probe."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oc3_coadd_psf_contract_probe as cli
from oc3lib.core import canonical, file_hash
from oc3lib import coadd_psf_contract as stage


PROJECT = Path(__file__).resolve().parents[2]
IDENTITIES = PROJECT / stage.IDENTITIES_RELATIVE
BINDING = PROJECT / stage.BINDING_RELATIVE
BASE = PROJECT / stage.BASE_CONTRACT_RELATIVE


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


def header(cards):
    values = cards + [card("END")]
    values += [b" " * 80] * ((36 - len(values) % 36) % 36)
    return b"".join(values)


def image_hdu(band, size=7):
    h = header([card("XTENSION", "IMAGE"), card("BITPIX", -32), card("NAXIS", 2),
                card("NAXIS1", size), card("NAXIS2", size), card("PCOUNT", 0),
                card("GCOUNT", 1), card("BAND", band)])
    raw = size * size * 4
    return h + b"\x00" * raw + b"\x00" * ((-raw) % stage.HEADER_BLOCK)


def fits_response(bands=("g", "r", "z")):
    primary = header([card("SIMPLE", True), card("BITPIX", 8), card("NAXIS", 0),
                      card("EXTEND", True), card("BANDS", "".join(bands))] +
                     [card(f"BAND{i}", band) for i, band in enumerate(bands)])
    return primary + b"".join(image_hdu(band) for band in bands)


def production():
    return stage.load_probe_binding(BINDING, PROJECT)


class FakeTransport:
    def __init__(self, binding, bands_by_region=None, fail_region=None):
        self.by_url = {r["literal_url"]: r for r in binding["representative_requests"]}
        self.bands = bands_by_region or {"south": ("g", "r", "z"),
                                         "north": ("g", "r", "z")}
        self.fail_region = fail_region
        self.requests_started = 0
        self.body_bytes_observed = 0
        self.calls = []

    def get(self, url, max_bytes):
        row = self.by_url[url]
        self.requests_started += 1
        self.calls.append((row["region"], url, max_bytes))
        if row["region"] == self.fail_region:
            return 503, {"content-type": "text/plain", "content-length": "4"}, b"fail", url
        body = fits_response(self.bands[row["region"]])
        self.body_bytes_observed += len(body)
        return 200, {"content-type": "image/fits", "content-length": str(len(body)),
                     "etag": '"synthetic"'}, body, url


class CoaddPSFContractTests(unittest.TestCase):
    def test_001_exact_fifty_four_identities_and_eighteen_points(self):
        identities, base = production()[1:]
        self.assertEqual(len(identities["identities"]), 54)
        self.assertEqual(len({(r["slot"], r["point_id"]) for r in identities["identities"]}), 18)
        self.assertEqual(base["counts"]["observational_identities"], 54)

    def test_002_exact_six_immutable_locations(self):
        before = file_hash(PROJECT / stage.LOCATIONS_RELATIVE)
        stage.build_identity_manifest(PROJECT)
        self.assertEqual(before, stage.LOCATIONS_SHA256)
        self.assertEqual(file_hash(PROJECT / stage.LOCATIONS_RELATIVE), before)

    def test_003_p0_p1_p2_coordinates_match_frozen_contract(self):
        identities, base = production()[1:]
        manifest_points = {(r["slot"], r["point_id"]):
                           (r["native_x"], r["native_y"], r["ra"], r["dec"])
                           for r in identities["identities"]}
        for point in base["spatial_points"]:
            self.assertEqual(manifest_points[(point["slot"], point["point_id"])],
                             (*point["native_xy"], *point["ra_dec"]))
        offsets = {(p["point_id"], tuple(p["offset_xy"])) for p in base["spatial_points"]}
        self.assertEqual(offsets, {("P0", (0, 0)), ("P1", (-32, -32)),
                                   ("P2", (32, 32))})

    def test_004_identity_count_is_independent_of_transport_count(self):
        identities = production()[1]
        self.assertEqual(len(identities["identities"]), 54)
        self.assertEqual(len({r["transport_id"] for r in identities["identities"]}), 18)

    def test_005_no_band_parameter_in_representative_urls(self):
        binding = production()[0]
        for row in binding["representative_requests"]:
            self.assertNotIn("bands=", row["literal_url"])
            self.assertIsNone(row["query_bands_parameter"])

    def test_006_region_specific_layers_and_representatives(self):
        binding = production()[0]
        self.assertEqual([(r["region"], r["slot"], r["point_id"], r["layer"])
                          for r in binding["representative_requests"]],
                         [("south", "S1", "P0", "ls-dr9-south"),
                          ("north", "N1", "P0", "ls-dr9-north")])

    def test_007_multiband_response_maps_to_eighteen_transports(self):
        structure = stage.inspect_response(fits_response())
        result = stage.classify_mapping({"south": {"structure": structure},
                                         "north": {"structure": structure}})
        self.assertEqual(result["decision"], "A_ONE_RESPONSE_BUNDLES_G_R_Z")
        self.assertEqual(result["future_http_response_count"], 18)
        self.assertEqual(structure["array_values_decoded"], 0)

    def test_008_single_band_response_maps_to_fifty_four_transports(self):
        structure = stage.inspect_response(fits_response(("g",)))
        result = stage.classify_mapping({"south": {"structure": structure},
                                         "north": {"structure": structure}})
        self.assertEqual(result["decision"], "B_ONE_RESPONSE_REPRESENTS_ONE_BAND")
        self.assertEqual(result["future_http_response_count"], 54)

    def test_008b_region_specific_mapping_is_preserved(self):
        south = stage.inspect_response(fits_response(("g",)))
        north = stage.inspect_response(fits_response(("g", "r", "z")))
        result = stage.classify_mapping({"south": {"structure": south},
                                         "north": {"structure": north}})
        self.assertEqual(result["decision"], "C_ANOTHER_EXPLICITLY_OBSERVED_MAPPING")
        self.assertEqual(result["future_http_response_count"], 36)
        self.assertFalse(result["same_schema_north_south"])

    def test_009_malformed_or_unknown_representation_fails(self):
        with self.assertRaises(stage.CoaddPSFContractError):
            stage.inspect_response(b"not fits")
        malformed = header([card("SIMPLE", True), card("BITPIX", 8), card("NAXIS", 0)])
        with self.assertRaisesRegex(stage.CoaddPSFContractError, "FITS_IMAGE_HDU_MISSING"):
            stage.inspect_response(malformed)

    def test_010_response_byte_cap_is_hard(self):
        with self.assertRaisesRegex(stage.CoaddPSFContractError, "FITS_RESPONSE_SIZE_INVALID"):
            stage.inspect_response(b"x" * (stage.MAX_RESPONSE_BYTES + 1))

    def test_011_cumulative_accounting_starts_at_probe_278(self):
        binding = production()[0]
        with tempfile.TemporaryDirectory() as td:
            store = stage.EvidenceStore(Path(td) / "audit", binding)
            self.assertEqual(store.aggregate["counters"]["cumulative_requests"], 278)
            self.assertEqual(store.aggregate["counters"]["cumulative_body_bytes"], 93870926)
            store.reserve("south", stage.MAX_RESPONSE_BYTES)
            self.assertEqual(store.aggregate["counters"]["cumulative_requests"], 279)

    def test_012_success_persists_two_regional_checkpoints(self):
        binding = production()[0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "audit"
            terminal, success = stage.run_probe(binding, FakeTransport(binding), root)
            self.assertTrue(success)
            self.assertEqual(terminal["state"], stage.SUCCESS)
            self.assertEqual(terminal["future_http_response_count"], 18)
            self.assertEqual(len(list((root / "REQUEST_EVIDENCE").glob("*.json"))), 2)
            self.assertEqual(len(list((root / "REGIONAL_CHECKPOINTS").glob("*.json"))), 2)

    def test_013_later_failure_preserves_south_checkpoint(self):
        binding = production()[0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "audit"
            terminal, success = stage.run_probe(binding,
                                                FakeTransport(binding, fail_region="north"), root)
            self.assertFalse(success)
            self.assertEqual(terminal["state"], stage.PARTIAL)
            self.assertTrue((root / "REGIONAL_CHECKPOINTS" / "south.json").is_file())
            self.assertFalse((root / "REGIONAL_CHECKPOINTS" / "north.json").exists())

    def test_014_binding_has_no_image_invvar_or_morphology_transport(self):
        binding = production()[0]
        self.assertFalse(binding["policy"]["image_invvar_access"])
        self.assertFalse(binding["policy"]["morphology_access"])
        self.assertTrue(all("/viewer/coadd-psf/" in r["literal_url"]
                            for r in binding["representative_requests"]))
        self.assertTrue(all("portal.nersc.gov" not in r["literal_url"]
                            for r in binding["representative_requests"]))

    def test_015_binding_is_canonical_and_sealed(self):
        raw = BINDING.read_bytes()
        value = json.loads(raw)
        self.assertEqual(raw, canonical(value) + b"\n")
        stage.load_probe_binding(BINDING, PROJECT)
        self.assertFalse(value["bulk_psf_acquisition_authorized"])

    def test_016_dry_run_and_cli_use_zero_network(self):
        binding = production()[0]
        plan = stage.dry_run(binding, PROJECT)
        self.assertEqual(plan["network_requests"], 0)
        self.assertEqual(plan["representative_requests"], 2)
        with patch("builtins.print"):
            code = cli.main(["--dry-run", "--project", str(PROJECT),
                             "--binding", str(BINDING)])
        self.assertEqual(code, 0)

    def test_017_runtime_caps_cannot_be_changed(self):
        with patch("builtins.print"):
            code = cli.main(["--dry-run", "--project", str(PROJECT),
                             "--binding", str(BINDING), "--max-new-requests", "3"])
        self.assertEqual(code, 2)

    def test_018_synthetic_probe_never_decodes_arrays(self):
        binding = production()[0]
        with tempfile.TemporaryDirectory() as td:
            terminal, success = stage.run_probe(binding, FakeTransport(binding),
                                                Path(td) / "audit")
        self.assertTrue(success)
        self.assertEqual(terminal["array_values_decoded"], 0)
        self.assertEqual(terminal["image_invvar_requests"], 0)
        self.assertEqual(terminal["morphology_accesses"], 0)


if __name__ == "__main__":
    unittest.main()
