from __future__ import annotations

import unittest

from oc3lib.cross_observer_grouping import load_canonical_json
from oc3lib.cross_observer_grouping_datalab_diagnostic_validation import (
    CANDIDATE, expected_command_argv, validate_candidate, validate_manifest, validate_runtime,
)


class DataLabDiagnosticTests(unittest.TestCase):
    def test_candidate_manifest_and_zero_source_rows(self):
        candidate = validate_candidate()
        manifest = validate_manifest()
        self.assertEqual(candidate["source_rows_read"], 0)
        self.assertFalse(candidate["documentary_gate_decided"])
        self.assertEqual((manifest["network_request_cap"], manifest["application_body_byte_cap"]),
                         (1, 65_536))
        self.assertEqual(len(manifest["resources"]), 1)
        self.assertIn("TAP_SCHEMA.columns", manifest["resources"][0]["url"])

    def test_exact_runtime_command_is_closed(self):
        candidate = load_canonical_json(CANDIDATE)
        command = expected_command_argv()
        validate_runtime(candidate, command[0], command[1], command[2:])
        changed = list(command); changed[-1] += "-changed"
        with self.assertRaises(Exception):
            validate_runtime(candidate, changed[0], changed[1], changed[2:])

    def test_no_redirect_retry_or_resume(self):
        candidate = validate_candidate()
        resource = validate_manifest()["resources"][0]
        self.assertEqual((resource["redirects"], resource["retries"]), (0, 0))
        self.assertEqual(candidate["autonomy_policy"]["resume_policy"],
                         {"allowed": False, "prospectively_frozen": True})
