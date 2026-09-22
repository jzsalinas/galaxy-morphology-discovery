"""Offline regression for the PHOTSYS HDU-label correction and Stage-B candidate."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from oc3lib.core import implementation_hash
from oc3lib.galaxy_eligibility_photsys_authority_probe import (
    PHOTSYSProbeError, PROJECT, load_canonical_json, validate_sealed,
)
from oc3lib import galaxy_eligibility_photsys_physical_correction as correction
from oc3lib import galaxy_eligibility_photsys_full_acquisition as acquisition


class CorrectionTests(unittest.TestCase):
    def test_001_exact_primary_and_bintable_classification(self):
        self.assertEqual(correction.classify_hdu_type(0, {"SIMPLE": True}), "PRIMARY")
        self.assertEqual(correction.classify_hdu_type(1, {"XTENSION": "BINTABLE"}),
                         "BINTABLE")
        with self.assertRaises(PHOTSYSProbeError):
            correction.classify_hdu_type(0, {"XTENSION": "BINTABLE"})
        with self.assertRaises(PHOTSYSProbeError):
            correction.classify_hdu_type(1, {"SIMPLE": True})

    def test_002_immutable_headers_reconstruct_exact_contract(self):
        rebuilt = correction.reconstruct_from_immutable_headers()
        original = validate_sealed(load_canonical_json(correction.ORIGINAL_CONTRACT_PATH))
        self.assertEqual(rebuilt["corrected_hdu_types"], ["PRIMARY", "BINTABLE"])
        self.assertEqual(rebuilt["schema"], original["structural_contract"]["column_schema"])
        self.assertEqual(rebuilt["projection"],
                         original["structural_contract"]["selective_projection"])
        self.assertEqual(rebuilt["primary_header_bytes"] + rebuilt["table_header_bytes"],
                         original["first_table_data_byte"])

    def test_003_correction_is_derived_label_only(self):
        value = correction.build_correction()
        self.assertEqual(value["original_derived_hdu_type"], [None, "PRIMARY"])
        self.assertEqual(value["corrected_derived_hdu_type"], ["PRIMARY", "BINTABLE"])
        self.assertTrue(value["physical_conclusions_unchanged"])
        self.assertTrue(all(value["impact_assessment"].values()))
        self.assertEqual((value["network_requests"], value["table_cell_values_decoded"]),
                         (0, 0))

    def test_004_reviewed_contract_binds_every_physical_finding(self):
        value = correction.validate_reviewed_contract()
        self.assertEqual([row["hdu_type"] for row in value["hdu_inventory"]],
                         ["PRIMARY", "BINTABLE"])
        self.assertEqual((value["first_table_data_byte"], value["maximum_probe_byte"]),
                         (11520, 11519))
        self.assertEqual((value["physical_contract"]["row_count"],
                          value["physical_contract"]["row_width"]), (662174, 79))
        self.assertEqual(len(value["physical_contract"]["column_schema"]), 13)
        self.assertEqual(value["full_fits_gets"], 0)
        self.assertFalse(any(value["firewall"].values()))


class StageBCandidateTests(unittest.TestCase):
    def test_010_candidate_is_exact_and_authorization_absent(self):
        value = acquisition.validate_candidate()
        self.assertEqual(value, acquisition.build_candidate(implementation_hash(PROJECT)))
        self.assertFalse(value["final_authorization_present"])
        self.assertFalse(acquisition.AUTHORIZATION_PATH.exists())
        self.assertEqual(value["resource"]["expected_content_length"], 52323840)
        self.assertEqual(value["request_plan"], {
            "automatic_retries": 0, "concurrency": 1, "identity_head": 0,
            "primary_gets": 1, "separate_resume_authorization_required": True,
            "stage_body_cap": 52323840, "stage_request_cap": 1,
        })

    def test_011_byte_preservation_does_not_authorize_values(self):
        value = acquisition.validate_candidate()
        boundary = value["acquisition_value_boundary"]
        self.assertEqual(boundary["statement"],
                         "FULL_FILE_BYTE_PRESERVATION != ALL_COLUMN_VALUE_OBSERVATION")
        self.assertFalse(boundary["all_column_value_observation_authorized"])
        design = value["offline_selective_validator_design"]
        self.assertEqual(design["allowed_value_fields"],
                         ["BRICKNAME", "BRICKID", "PHOTSYS"])
        self.assertIn("AREA_PER_BRICK", design["forbidden_value_fields"])
        self.assertFalse(design["panel_selection"])

    def test_012_offline_validation_constructs_no_transport(self):
        with patch.object(acquisition, "FullFileTransport",
                          side_effect=AssertionError("network transport")):
            result = acquisition.validate_candidate_offline()
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(result["state"], acquisition.READY)

    def test_013_missing_authorization_blocks_before_transport(self):
        with patch.object(acquisition, "FullFileTransport") as transport:
            with self.assertRaises(PHOTSYSProbeError):
                acquisition.execute(acquisition.CANDIDATE_PATH,
                                    Path("/definitely/missing/authorization.json"),
                                    "0" * 64, acquisition.OUTPUT_ROOT)
        transport.assert_not_called()

    def test_014_transport_streams_exact_bytes_with_no_decode(self):
        payload = b"provider-bytes"
        class Response:
            status = 200
            def getheaders(self):
                return [("Content-Length", str(len(payload))), ("Content-Encoding", "identity"),
                        ("ETag", '"e"'), ("Last-Modified", "Mon")]
            def read(self, size):
                value, self.body = self.body[:size], self.body[size:]
                return value
            body = payload
        class Connection:
            response = Response()
            def request(self, *args, **kwargs): pass
            def getresponse(self): return self.response
            def close(self): pass
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(acquisition, "EXPECTED_BODY_BYTES", len(payload)), \
                patch.object(acquisition.http.client, "HTTPSConnection", return_value=Connection()):
            target = Path(temp) / "body.partial"
            transport = acquisition.FullFileTransport(
                "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/x.fits")
            observed = transport.download(target, {"etag": '"e"', "last_modified": "Mon"})
        self.assertEqual(observed["body_bytes"], len(payload))
        self.assertEqual(transport.requests_started, 1)


if __name__ == "__main__":
    unittest.main()
