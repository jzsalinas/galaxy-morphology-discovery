import contextlib
import io
import unittest
from unittest.mock import patch

import oc3_photsys_archive_range_size_probe as cli
from oc3lib.core import implementation_hash
from oc3lib.galaxy_eligibility_photsys_authority_probe import file_sha256
from oc3lib.photsys_archive_range_size_probe import *

class RangeAutonomyCandidateTests(unittest.TestCase):
    def test_01_historical_candidates_unchanged(self):
        self.assertEqual(file_sha256(CANDIDATE_PATH),CANDIDATE_001_SHA256)
        self.assertEqual(file_sha256(CANDIDATE_002_PATH),CANDIDATE_002_SHA256)
        self.assertEqual(validate_historical_candidate_001()["candidate_state"],"PENDING_HUMAN_REVIEW")
        self.assertEqual(validate_historical_candidate_002()["candidate_state"],"PENDING_STANDING_AUTONOMY")
    def test_02_candidate_003_exact(self):
        self.assertEqual(validate_autonomous_candidate_003(),build_autonomous_candidate_003(implementation_hash(PROJECT)))
    def test_03_semantic_transport_fields_identical_to_002(self):
        old=validate_historical_candidate_002(); new=validate_autonomous_candidate_003()
        for key in ("accepted_content_types","budget","content_range_contract","failed_provenance_review",
                    "historical_head","negative_capabilities","network_caps","preserved_bodies","request",
                    "resource_manifest","scope","specification","stage_id","terminal_mapping","scientific_firewall"):
            self.assertEqual(new[key],old[key],key)
    def test_04_exact_range_contract(self):
        candidate=validate_autonomous_candidate_003()
        self.assertEqual(candidate["request"]["literal_url"],ARCHIVE_URL)
        self.assertEqual(candidate["request"]["headers"]["Range"],"bytes=0-0")
        self.assertEqual(candidate["network_caps"],{"application_body_bytes":0,"concurrency":1,"redirects":0,"requests":1,"retries":0})
        self.assertEqual(candidate["historical_head"]["etag"],HEAD_ETAG)
        self.assertEqual(candidate["specification"]["sha256"],SPEC_SHA256)
    def test_05_generic_contract_reservations(self):
        contract=validate_autonomous_candidate_003()["autonomy_policy"]
        self.assertEqual(contract["schema_version"],"OC3_AUTONOMOUS_ACTION_CONTRACT_001")
        self.assertEqual(contract["network_request_reservation"],1)
        self.assertEqual(contract["application_body_reservation"],0)
        self.assertEqual(contract["authority_classes_used"],["EXACT_DESITARGET_0_48_0_METADATA_AND_SOURCE"])
    def test_06_action_receipt_exact_and_offline(self):
        candidate=validate_autonomous_candidate_003(); payload=build_candidate_003_payload(implementation_hash(PROJECT))
        self.assertEqual(candidate["autonomy_policy"]["candidate_sha256"],sha256_bytes(canonical(payload)))
        self.assertEqual(build_action_validation_receipt_003(payload),validate_sealed(load_canonical_json(ACTION_VALIDATION_RECEIPT_003_PATH)))
    def test_07_command_uses_candidate_003_and_permit(self):
        command=exact_autonomous_command()
        self.assertIn(str(CANDIDATE_003_PATH),command); self.assertIn("--autonomous-permit",command)
        self.assertIn("--standing-authorization",command); self.assertNotIn("--authorization",command)
    def test_08_no_real_authorization_or_permit(self):
        self.assertFalse(STANDING_AUTHORIZATION_PATH.exists()); self.assertFalse(AUTONOMOUS_PERMIT_PATH.exists())
    def test_09_autonomous_dry_run_is_inactive(self):
        result=autonomous_dry_run(); self.assertEqual(result["permit_state"],"MANDATE_NOT_ACTIVE")
        self.assertEqual(result["network_requests"],0)
    def test_10_cli_candidate_003_dry_run_has_no_network(self):
        output=io.StringIO()
        with patch("oc3lib.photsys_archive_range_size_probe.http.client.HTTPSConnection",side_effect=AssertionError("network")),contextlib.redirect_stdout(output):
            code=cli.main(["--dry-run","--candidate",str(CANDIDATE_003_PATH)])
        self.assertEqual(code,0); self.assertIn("MANDATE_NOT_ACTIVE",output.getvalue())
    def test_11_real_candidate_003_requires_permit(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code=cli.main(["--probe-desitarget-archive-range-size","--execute-network","--candidate",str(CANDIDATE_003_PATH)])
        self.assertEqual(code,2)
    def test_12_candidate_002_real_execution_closed(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code=cli.main(["--probe-desitarget-archive-range-size","--execute-network","--candidate",str(CANDIDATE_002_PATH),"--authorization",str(AUTHORIZATION_PATH)])
        self.assertEqual(code,2)

if __name__=="__main__": unittest.main()
