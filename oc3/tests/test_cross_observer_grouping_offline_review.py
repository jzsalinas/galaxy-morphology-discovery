from __future__ import annotations
import unittest
from oc3lib.cross_observer_grouping_offline_review_validation import (
 OfflineReviewValidationError,expected_command_argv,validate_candidate,validate_runtime)

class OfflineDocumentaryReviewTests(unittest.TestCase):
 def test_candidate_is_offline_and_binds_seven_inputs(self):
  value=validate_candidate(); self.assertEqual(len(value["input_bindings"]),7)
  self.assertEqual(value["resource_caps"]["network_requests"],0); self.assertEqual(value["source_rows_read"],0)
 def test_runtime_is_exact(self):
  value=validate_candidate(); command=expected_command_argv(); validate_runtime(value,command[0],command[1],command[2:])
  with self.assertRaises(OfflineReviewValidationError): validate_runtime(value,command[0],command[1],command[2:]+["extra"])

if __name__=="__main__": unittest.main()
