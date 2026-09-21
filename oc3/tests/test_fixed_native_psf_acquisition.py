"""Offline synthetic tests for fixed native + bundled PSF acquisition."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oc3_fixed_native_psf_acquisition as cli
from oc3lib.core import canonical, file_hash
from oc3lib import fixed_native_psf_acquisition as stage


PROJECT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = PROJECT / stage.CANDIDATE_RELATIVE


def production_candidate():
    return stage._canonical_load(CANDIDATE_PATH)


def synthetic_authorization(candidate):
    return stage._seal({
        "schema_version": "OC3_FIXED_NATIVE_PSF_ACQUISITION_FINAL_HUMAN_AUTHORIZATION_001",
        "stage_id": stage.STAGE_ID,
        "scope": "FIXED_NATIVE_PRODUCTS_AND_PSF_ACQUISITION",
        "authorization_state": "FINAL_HUMAN_AUTHORIZATION",
        "authorized": True, "authorized_by": "synthetic-test",
        "authorized_at_utc": "2026-09-21T00:00:00Z", "resume": False,
        "candidate_path": str(CANDIDATE_PATH.resolve()),
        "candidate_sha256": hashlib.sha256(canonical(candidate) + b"\n").hexdigest(),
    })


def small_candidate():
    value = copy.deepcopy(production_candidate())
    for row in value["fixed_native_resources"]:
        row["expected_content_length"] = 4
    for row in value["psf_transport_resources"]:
        row["max_response_bytes"] = 4
    return stage._seal(value)


class FakeTransport:
    def __init__(self, candidate, fail_url=None):
        self.fixed = {row["literal_url"]: row for row in candidate["fixed_native_resources"]}
        self.psf = {row["literal_url"]: row for row in candidate["psf_transport_resources"]}
        self.fail_url = fail_url
        self.calls = []

    def head(self, url):
        row = self.fixed[url]
        self.calls.append(("HEAD", row["resource_id"]))
        return 200, {"content-length": str(row["expected_content_length"]),
                     "content-encoding": "identity", "etag": row["expected_etag"]}, b"", url

    def get(self, url, max_bytes):
        self.calls.append(("GET", url))
        if url == self.fail_url:
            return 503, {"content-type": "text/plain", "content-length": "4"}, b"fail", url
        if url in self.fixed:
            body = b"F" * self.fixed[url]["expected_content_length"]
            return 200, {"content-length": str(len(body)),
                         "content-encoding": "identity"}, body, url
        body = b"PSF!"
        return 200, {"content-length": str(len(body)), "content-type": "image/fits",
                     "content-encoding": "identity"}, body, url


def fixed_ok(row, body):
    return {"resource_id": row["resource_id"], "synthetic": True,
            "science_pixel_values_observed": 0}


def psf_ok(row, body):
    return {"resource_id": row["resource_id"], "synthetic": True,
            "bands": ["g", "r", "z"], "array_values_decoded": 0}


class FixedNativePSFAcquisitionTests(unittest.TestCase):
    def test_001_exact_twelve_fixed_inventory_and_bytes(self):
        candidate = production_candidate()
        rows = candidate["fixed_native_resources"]
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(r["expected_content_length"] for r in rows), 144766080)
        self.assertEqual([(r["region"], r["product"], r["band"]) for r in rows],
                         [(region, product, band) for region in ("south", "north")
                          for product in ("image", "invvar") for band in ("g", "r", "z")])

    def test_002_exact_eighteen_psf_transports_and_fifty_four_identities(self):
        candidate = production_candidate()
        rows = candidate["psf_transport_resources"]
        self.assertEqual(len(rows), 18)
        self.assertEqual([(r["slot"], r["point_id"]) for r in rows],
                         [(slot, point) for slot in stage.SLOTS for point in stage.PSF_POINTS])
        ids = [identity for row in rows for identity in row["observational_identity_ids"]]
        self.assertEqual(len(ids), 54)
        self.assertEqual(len(set(ids)), 54)

    def test_003_region_specific_shapes_are_frozen_without_homogenization(self):
        candidate = production_candidate()
        self.assertEqual(candidate["psf_contract"]["region_specific_shapes"],
                         {"south": {"g": [63, 63], "r": [63, 63], "z": [63, 63]},
                          "north": {"g": [31, 31], "r": [31, 31], "z": [63, 63]}})
        self.assertFalse(candidate["psf_contract"]["same_schema_north_south"])
        self.assertFalse(candidate["psf_contract"]["homogenize_shapes"])

    def test_004_historical_psf_reservation_is_total_envelope(self):
        budget = production_candidate()["body_budget"]
        self.assertEqual(budget["psf_total_cap_bytes"], 56623104)
        self.assertEqual(budget["psf_per_response_cap_bytes"], 3145728)
        self.assertEqual(budget["stage_primary_body_reservation"], 201389184)

    def test_005_request_plan_and_cumulative_counters(self):
        candidate = production_candidate()
        plan = candidate["request_plan"]
        self.assertEqual((plan["fixed_head"], plan["fixed_get"], plan["psf_head"],
                          plan["psf_get"], plan["primary_request_count"]),
                         (12, 12, 0, 18, 42))
        self.assertEqual((plan["retry_pool"], plan["stage_request_cap"]), (6, 48))
        self.assertEqual(candidate["starting_cumulative"],
                         {"requests": 280, "body_bytes": 93968846})

    def test_006_download_order_is_deterministic(self):
        candidate = production_candidate()
        expected = [r["resource_id"] for r in
                    candidate["fixed_native_resources"] + candidate["psf_transport_resources"]]
        self.assertEqual(candidate["acquisition_order"], expected)

    def test_007_fixed_representation_drift_fails(self):
        row = production_candidate()["fixed_native_resources"][0]
        observed = copy.deepcopy(row["expected_structure"])
        observed["science_pixel_values_observed"] = 0
        stage._assert_fixed_structure(row["expected_structure"], observed, row["resource_id"])
        observed["dtype"] = "float64"
        with self.assertRaisesRegex(stage.NativePSFAcquisitionError,
                                    "FIXED_NATIVE_REPRESENTATION_DRIFT"):
            stage._assert_fixed_structure(row["expected_structure"], observed, row["resource_id"])

    def test_008_psf_malformed_missing_order_and_shape_fail(self):
        row = production_candidate()["psf_transport_resources"][0]
        base = {"representation_format": "FITS", "image_hdu_count": 3,
                "bands": ["g", "r", "z"], "array_values_decoded": 0,
                "hdus": [{"is_image": True, "band": band, "dtype": "float32",
                          "shape": [63, 63]} for band in ("g", "r", "z")]}
        stage._assert_psf_structure(row, base)
        for mutation in ("missing", "order", "shape", "malformed"):
            value = copy.deepcopy(base)
            if mutation == "missing": value["bands"] = ["g", "r"]
            elif mutation == "order": value["bands"] = ["r", "g", "z"]
            elif mutation == "shape": value["hdus"][0]["shape"] = [31, 31]
            else: value["representation_format"] = "PNG"
            with self.assertRaises(stage.NativePSFAcquisitionError):
                stage._assert_psf_structure(row, value)

    def test_009_immutable_publication_never_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "STAGING" / "x"; destination = root / "RAW" / "x"
            digest = stage._stage(source, b"exact-provider-body")
            stage._publish(source, destination, digest)
            self.assertEqual(file_hash(destination), digest)
            replacement = root / "STAGING" / "replacement"
            stage._stage(replacement, b"different")
            with self.assertRaisesRegex(stage.NativePSFAcquisitionError,
                                        "IMMUTABLE_PUBLICATION_CONFLICT"):
                stage._publish(replacement, destination, file_hash(replacement))

    def test_010_no_automatic_resume(self):
        candidate = production_candidate()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "attempt"
            stage.AcquisitionState(root, candidate)
            with self.assertRaisesRegex(stage.NativePSFAcquisitionError,
                                        "SEPARATE_RESUME_AUTHORIZATION_REQUIRED"):
                stage.AcquisitionState(root, candidate)

    def test_011_locations_are_not_mutated(self):
        path = PROJECT / stage.LOCATIONS_RELATIVE
        before = file_hash(path)
        stage.build_candidate(PROJECT)
        self.assertEqual(before, stage.LOCATIONS_SHA256)
        self.assertEqual(file_hash(path), before)

    def test_012_candidate_has_zero_extraction_preprocessing_morphology(self):
        negative = production_candidate()["negative_capabilities"]
        self.assertFalse(negative["cutout_extraction"])
        self.assertFalse(negative["preprocessing"])
        self.assertFalse(negative["morphology_inspection"])
        self.assertFalse(negative["location_change"])

    def test_013_candidate_was_prospective_and_completed_authorization_is_sealed(self):
        candidate = production_candidate()
        self.assertFalse(candidate["final_authorization_present"])
        authorization_path = PROJECT / stage.AUTHORIZATION_RELATIVE
        self.assertEqual(file_hash(authorization_path),
                         "e493fa0acdeb0f70ebce2a51f04d1d41f18c5a5a81a6e745d0d1b8cc5afc3d0d")
        authorization = stage._canonical_load(authorization_path)
        stage._verify_seal(authorization)
        self.assertTrue(authorization["authorized"])
        self.assertEqual(authorization["candidate_sha256"], file_hash(CANDIDATE_PATH))

    def test_014_offline_candidate_validation(self):
        result = stage.validate_candidate_offline(CANDIDATE_PATH, PROJECT)
        self.assertEqual(result["state"], stage.CANDIDATE_READY)
        self.assertEqual(result["network_requests"], 0)
        with patch("builtins.print"):
            code = cli.main(["--validate-candidate", "--project", str(PROJECT),
                             "--candidate", str(CANDIDATE_PATH)])
        self.assertEqual(code, 0)

    def test_014b_missing_final_authorization_blocks_transport(self):
        with patch.object(cli, "ClosedAcquisitionTransport") as transport:
            with patch("builtins.print"):
                code = cli.main(["--acquire", "--execute-network",
                                 "--project", str(PROJECT),
                                 "--candidate", str(CANDIDATE_PATH)])
        self.assertEqual(code, 2)
        transport.assert_not_called()

    def test_014c_transport_preserves_dynamic_psf_url_and_enforces_cap(self):
        fixed_url = "https://portal.example/static.fits.fz"
        psf_url = "https://viewer.example/coadd-psf/?ra=1&dec=2&layer=ls-dr9-south"
        with (patch.object(stage, "LiteralHTTPTransport") as fixed_class,
              patch.object(stage, "LiteralPSFTransport") as psf_class):
            fixed = fixed_class.return_value
            psf = psf_class.return_value
            fixed.requests_started = 0; fixed.body_bytes_observed = 0
            psf.requests_started = 1; psf.body_bytes_observed = 4
            psf.get.return_value = (200, {"content-type": "image/fits"}, b"PSF!", psf_url)
            transport = stage.ClosedAcquisitionTransport([fixed_url], [psf_url])
            self.assertEqual(transport.get(psf_url, 4)[2], b"PSF!")
            psf.get.assert_called_once_with(psf_url, 4)
            fixed.get.assert_not_called()
            self.assertEqual((transport.requests_started, transport.body_bytes_observed), (1, 4))
            psf.get.return_value = (200, {}, b"TOO-LONG", psf_url)
            with self.assertRaisesRegex(stage.NativePSFAcquisitionError,
                                        "HTTP_BODY_EXCEEDS_BOUND"):
                transport.get(psf_url, 4)

    def test_015_runtime_caps_cannot_change(self):
        with patch("builtins.print"):
            code = cli.main(["--validate-candidate", "--project", str(PROJECT),
                             "--candidate", str(CANDIDATE_PATH),
                             "--stage-request-cap", "49"])
        self.assertEqual(code, 2)

    def test_016_full_synthetic_acquisition_and_identity_mapping(self):
        candidate = small_candidate(); authorization = synthetic_authorization(candidate)
        transport = FakeTransport(candidate)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "attempt"
            terminal = stage.run_acquisition(candidate, authorization, transport, root,
                                             candidate_path=CANDIDATE_PATH,
                                             fixed_validator=fixed_ok,
                                             psf_validator=psf_ok)
            self.assertEqual(terminal["state"], stage.SUCCESS)
            self.assertEqual(terminal["fixed_native_published"], 12)
            self.assertEqual(terminal["psf_responses_published"], 18)
            self.assertEqual(terminal["psf_observational_identities_mapped"], 54)
            self.assertEqual(terminal["stage_requests"], 42)
            self.assertEqual(len(list((root / "RAW_IMMUTABLE").rglob("*.fits*"))), 30)

    def test_017_partial_failure_preserves_completed_publication(self):
        candidate = small_candidate(); authorization = synthetic_authorization(candidate)
        fail_url = candidate["fixed_native_resources"][1]["literal_url"]
        transport = FakeTransport(candidate, fail_url=fail_url)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "attempt"
            with self.assertRaises(stage.NativePSFAcquisitionError):
                stage.run_acquisition(candidate, authorization, transport, root,
                                      candidate_path=CANDIDATE_PATH,
                                      fixed_validator=fixed_ok,
                                      psf_validator=psf_ok)
            ledger = json.loads((root / "ACQUISITION_LEDGER.json").read_text())
            self.assertEqual(ledger["state"], "PARTIAL")
            self.assertEqual(len(ledger["published"]), 1)
            self.assertTrue((root / "ACQUISITION_TERMINAL.json").is_file())

    def test_018_candidate_is_canonical_and_sealed(self):
        raw = CANDIDATE_PATH.read_bytes(); value = json.loads(raw)
        self.assertEqual(raw, canonical(value) + b"\n")
        stage.validate_candidate(value, PROJECT)


if __name__ == "__main__":
    unittest.main()
