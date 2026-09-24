import contextlib
import io
import unittest
from unittest.mock import patch

import oc3_photsys_archive_range_size_probe as cli
from oc3lib.core import canonical
from oc3lib.galaxy_eligibility_photsys_authority_probe import file_sha256
from oc3lib.photsys_archive_range_size_probe import *

class RangeAutonomyCandidateTests(unittest.TestCase):
    def historical_candidate_003(self):
        self.assertEqual(file_sha256(CANDIDATE_003_PATH),
                         "bfd4f6da7fcfd75dff1864541bae6e61e7c01659452dfe7033029a9260051e2a")
        return validate_sealed(load_canonical_json(CANDIDATE_003_PATH))
    def test_01_historical_candidates_unchanged(self):
        self.assertEqual(file_sha256(CANDIDATE_PATH),CANDIDATE_001_SHA256)
        self.assertEqual(file_sha256(CANDIDATE_002_PATH),CANDIDATE_002_SHA256)
        self.assertEqual(validate_historical_candidate_001()["candidate_state"],"PENDING_HUMAN_REVIEW")
        self.assertEqual(validate_historical_candidate_002()["candidate_state"],"PENDING_STANDING_AUTONOMY")
    def test_02_candidate_003_exact(self):
        candidate=self.historical_candidate_003()
        self.assertEqual(candidate["implementation_aggregate"],
                         "a3be89e0c9bf2e0b7b3d50c22e2b3debbcfa2153a2e2439279e4a2fee2e8185f")
    def test_03_semantic_transport_fields_identical_to_002(self):
        old=validate_historical_candidate_002(); new=self.historical_candidate_003()
        for key in ("accepted_content_types","budget","content_range_contract","failed_provenance_review",
                    "historical_head","negative_capabilities","network_caps","preserved_bodies","request",
                    "resource_manifest","scope","specification","stage_id","terminal_mapping","scientific_firewall"):
            self.assertEqual(new[key],old[key],key)
    def test_04_exact_range_contract(self):
        candidate=self.historical_candidate_003()
        self.assertEqual(candidate["request"]["literal_url"],ARCHIVE_URL)
        self.assertEqual(candidate["request"]["headers"]["Range"],"bytes=0-0")
        self.assertEqual(candidate["network_caps"],{"application_body_bytes":0,"concurrency":1,"redirects":0,"requests":1,"retries":0})
        self.assertEqual(candidate["historical_head"]["etag"],HEAD_ETAG)
        self.assertEqual(candidate["specification"]["sha256"],SPEC_SHA256)
    def test_05_generic_contract_reservations(self):
        contract=self.historical_candidate_003()["autonomy_policy"]
        self.assertEqual(contract["schema_version"],"OC3_AUTONOMOUS_ACTION_CONTRACT_001")
        self.assertEqual(contract["network_request_reservation"],1)
        self.assertEqual(contract["application_body_reservation"],0)
        self.assertEqual(contract["authority_classes_used"],["EXACT_DESITARGET_0_48_0_METADATA_AND_SOURCE"])
    def test_06_action_receipt_exact_and_offline(self):
        candidate=self.historical_candidate_003()
        payload={key:value for key,value in candidate.items() if key not in ("autonomy_policy","sealed")}
        self.assertEqual(candidate["autonomy_policy"]["candidate_sha256"],sha256_bytes(canonical(payload)))
        self.assertEqual(file_sha256(ACTION_VALIDATION_RECEIPT_003_PATH),
                         "df86f79c3361171f163f6286d434f0c4bdde9e9f1865e7535a87270cb816f68a")
        receipt=validate_sealed(load_canonical_json(ACTION_VALIDATION_RECEIPT_003_PATH))
        self.assertEqual(receipt["candidate_payload_sha256"],candidate["autonomy_policy"]["candidate_sha256"])
        self.assertEqual(receipt["network_requests"],0)
    def test_07_command_uses_candidate_003_and_permit(self):
        command=exact_autonomous_command()
        self.assertIn(str(CANDIDATE_003_PATH),command); self.assertIn("--autonomous-permit",command)
        self.assertIn("--standing-authorization",command); self.assertNotIn("--authorization",command)
    def test_08_historical_authorization_and_consumed_permit_preserved(self):
        self.assertTrue(STANDING_AUTHORIZATION_PATH.exists()); self.assertTrue(AUTONOMOUS_PERMIT_PATH.exists())
        self.assertEqual(file_sha256(STANDING_AUTHORIZATION_PATH),
                         "e7e906f9d41a72a0176727fe8cf79e43d70ae14a8d62952dcfbe72d09a1f4e0d")
        self.assertEqual(file_sha256(AUTONOMOUS_PERMIT_PATH),
                         "d59baf5c891617e17101682d3973ba62fe324d4aa36065eeb30917845cd3b4c7")
    def test_09_historical_mission_is_terminal_and_inactive(self):
        state=validate_sealed(load_canonical_json(AUTONOMY_STATE_PATH))
        self.assertEqual(state["state"],"SCIENTIFIC_TERMINAL")
        self.assertFalse(state["active"])
        self.assertEqual(state["scientific_outcome"],"PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE")
    def test_10_historical_terminal_check_has_no_network(self):
        with patch("oc3lib.photsys_archive_range_size_probe.http.client.HTTPSConnection",side_effect=AssertionError("network")):
            state=validate_sealed(load_canonical_json(AUTONOMY_STATE_PATH))
        self.assertEqual(state["state"],"SCIENTIFIC_TERMINAL")
    def test_11_real_candidate_003_requires_permit(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code=cli.main(["--probe-desitarget-archive-range-size","--execute-network","--candidate",str(CANDIDATE_003_PATH)])
        self.assertEqual(code,2)
    def test_12_candidate_002_real_execution_closed(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code=cli.main(["--probe-desitarget-archive-range-size","--execute-network","--candidate",str(CANDIDATE_002_PATH),"--authorization",str(AUTHORIZATION_PATH)])
        self.assertEqual(code,2)

if __name__=="__main__": unittest.main()
