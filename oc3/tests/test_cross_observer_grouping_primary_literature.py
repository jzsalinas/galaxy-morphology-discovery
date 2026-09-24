from __future__ import annotations
import unittest
from oc3lib.cross_observer_grouping_primary_literature_validation import (
    FROZEN_USER_AGENT, LiteratureValidationError, expected_command_argv, validate_candidate, validate_manifest, validate_runtime,
)

class PrimaryLiteratureRecoveryTests(unittest.TestCase):
    def test_candidate_is_single_official_arxiv_export_resource(self):
        candidate=validate_candidate(); resource=validate_manifest()["resources"][0]
        self.assertEqual(resource["url"],"https://export.arxiv.org/pdf/0707.1611")
        self.assertEqual(candidate["request_headers"],{"User-Agent":FROZEN_USER_AGENT})
        self.assertEqual(candidate["source_rows_read"],0)
    def test_runtime_is_exact(self):
        candidate=validate_candidate(); command=expected_command_argv()
        validate_runtime(candidate,command[0],command[1],command[2:])
        with self.assertRaises(LiteratureValidationError):
            validate_runtime(candidate,command[0],command[1],command[2:]+["extra"])

if __name__=="__main__": unittest.main()
