import contextlib
import io
import unittest
from unittest.mock import patch

import oc3_photsys_archive_range_size_probe as cli
from oc3lib.core import implementation_hash
from oc3lib.galaxy_eligibility_photsys_authority_probe import file_sha256
from oc3lib.photsys_archive_range_size_probe import *


class RangeAutonomyCandidateTests(unittest.TestCase):
    def test_01_candidate_001_unchanged(self):
        self.assertEqual(file_sha256(CANDIDATE_PATH), CANDIDATE_001_SHA256)
        self.assertEqual(validate_historical_candidate_001()["candidate_state"], "PENDING_HUMAN_REVIEW")

    def test_02_candidate_002_exact(self):
        self.assertEqual(validate_autonomous_candidate(),
                         build_autonomous_candidate(implementation_hash(PROJECT)))

    def test_03_scientific_and_transport_contract_unchanged(self):
        first = validate_historical_candidate_001()
        second = validate_autonomous_candidate()
        for key in ("accepted_content_types", "budget", "content_range_contract",
                    "failed_provenance_review", "historical_head", "negative_capabilities",
                    "network_caps", "preserved_bodies", "request", "scope",
                    "specification", "stage_id", "terminal_mapping"):
            self.assertEqual(second[key], first[key], key)

    def test_04_governance_is_autonomous_only(self):
        candidate = validate_autonomous_candidate()
        governance = candidate["execution_governance"]
        self.assertEqual(governance["permit_type"], "AUTONOMOUS_EXECUTION_PERMIT")
        self.assertFalse(governance["per_stage_human_authorization"])
        self.assertFalse(governance["resume"])

    def test_05_command_uses_permit_not_final_human_authorization(self):
        command = exact_autonomous_command()
        self.assertIn("--autonomous-permit", command)
        self.assertIn("--standing-authorization", command)
        self.assertIn("--autonomy-state", command)
        self.assertNotIn("--authorization", command)

    def test_06_manifest_exact(self):
        candidate = validate_autonomous_candidate()
        self.assertEqual(candidate["resource_manifest"]["sha256"], AUTONOMY_MANIFEST_SHA256)
        self.assertEqual(file_sha256(AUTONOMY_MANIFEST_PATH), AUTONOMY_MANIFEST_SHA256)

    def test_07_no_real_authorization_or_permit(self):
        self.assertFalse(STANDING_AUTHORIZATION_PATH.exists())
        self.assertFalse(AUTONOMOUS_PERMIT_PATH.exists())

    def test_08_autonomous_dry_run_is_not_active(self):
        result = autonomous_dry_run()
        self.assertEqual(result["state"], READY)
        self.assertEqual(result["permit_state"], "MANDATE_NOT_ACTIVE")
        self.assertEqual(result["network_requests"], 0)

    def test_09_cli_candidate_002_dry_run_has_no_network(self):
        output = io.StringIO()
        with patch("oc3lib.photsys_archive_range_size_probe.http.client.HTTPSConnection",
                   side_effect=AssertionError("network")), contextlib.redirect_stdout(output):
            code = cli.main(["--dry-run", "--candidate", str(CANDIDATE_002_PATH)])
        self.assertEqual(code, 0)
        self.assertIn("MANDATE_NOT_ACTIVE", output.getvalue())

    def test_10_real_candidate_002_execution_requires_permit(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["--probe-desitarget-archive-range-size", "--execute-network",
                             "--candidate", str(CANDIDATE_002_PATH)])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
