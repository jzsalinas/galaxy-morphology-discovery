from __future__ import annotations

import io
import unittest

import oc3_cross_observer_grouping_documentary_completion as completion
from oc3lib.cross_observer_grouping_documentary_completion_validation import (
    CompletionValidationError, expected_command_argv, validate_candidate, validate_manifest, validate_runtime,
)


class DocumentaryCompletionTests(unittest.TestCase):
    def test_frozen_candidate_and_manifest_validate_offline(self):
        candidate = validate_candidate(); manifest = validate_manifest()
        self.assertEqual(len(manifest["resources"]), 3)
        self.assertEqual(candidate["source_rows_read"], 0)

    def test_query_correction_is_literal(self):
        resources = validate_manifest()["resources"]
        self.assertIn("schema_name", resources[0]["url"])
        self.assertNotIn("schema_name", resources[1]["url"])
        self.assertIn("%27ls_dr9.tractor_n%27", resources[1]["url"])

    def test_runtime_command_is_exact(self):
        candidate = validate_candidate(); command = expected_command_argv()
        validate_runtime(candidate,command[0],command[1],command[2:])
        with self.assertRaises(CompletionValidationError):
            validate_runtime(candidate,command[0],command[1],command[2:]+["unexpected"])

    def test_partial_bytes_are_charged_before_cap_failure(self):
        response = io.BytesIO(b"12345"); response.headers = {}
        counters = {"application_body_bytes":0,"network_requests_started":1}
        with self.assertRaises(CompletionValidationError):
            completion._read_bounded(response,4,10,counters)
        self.assertEqual(counters["application_body_bytes"],5)


if __name__ == "__main__":
    unittest.main()
