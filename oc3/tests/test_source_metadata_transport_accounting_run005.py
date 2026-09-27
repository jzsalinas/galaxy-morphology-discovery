from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from oc3lib.cross_observer_grouping import PROJECT, load_canonical_json
from oc3lib.autonomous_recovery_envelope import RecoveryEnvelopeError
from oc3lib.source_metadata_acquisition_pilot import QUERY_LITERALS
from oc3lib.source_metadata_recovery_executors_run005 import material_acquisition
from test_manual_source_metadata_acquisition import Opener, PartialResponse, Response, success_responses

INVARIANTS=PROJECT/"oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_SCIENTIFIC_INVARIANTS_001.json"
SCHEMA=PROJECT/"oc3/source_metadata_autonomous_recovery_run_004/OC3-SOURCE-METADATA-RECOVERY-RUN-004-G01-MATERIAL_SOURCE_METADATA_ACQUISITION/RAW_IMMUTABLE/schema.csv"


class Run005TransportAccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=PROJECT/"oc3")
        self.output=Path(self.temp.name)/"out"; self.output.mkdir()
        self.invariants=load_canonical_json(INVARIANTS)
        self.candidate={"run_id":"OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-005",
            "stage_id":"OC3-SOURCE-METADATA-RECOVERY-RUN-005-G01-MATERIAL_SOURCE_METADATA_ACQUISITION",
            "action_kind":"MATERIAL_SOURCE_METADATA_ACQUISITION"}
    def tearDown(self): self.temp.cleanup()
    def responses(self): return [Response(SCHEMA.read_bytes()),*success_responses()]

    def test_failure_before_request_start_is_not_charged(self):
        inv=deepcopy(self.invariants); inv["queries"][0]["literal_adql"] += " "
        opener=Opener([])
        with self.assertRaisesRegex(RecoveryEnvelopeError,"SCIENTIFIC_QUERY_SEMANTICS_INVALID"):
            material_acquisition(self.candidate,self.output,inv,opener=opener)
        self.assertEqual(opener.calls,[])

    def test_timeout_after_start_zero_bytes_has_governed_terminal(self):
        terminal=material_acquisition(self.candidate,self.output,self.invariants,opener=Opener([TimeoutError("read timed out")]))
        self.assertEqual(terminal["failure_class"],"DATALAB_TRANSPORT_FAILURE")
        self.assertEqual(terminal["network_requests_started"],1); self.assertEqual(terminal["application_body_bytes_read"],0)
        self.assertEqual(terminal["transport_observations"][0]["exception_class"],"TimeoutError")

    def test_partial_bytes_are_accounted_and_never_parsed(self):
        terminal=material_acquisition(self.candidate,self.output,self.invariants,opener=Opener([PartialResponse(b"partial")]))
        self.assertEqual(terminal["application_body_bytes_read"],3)
        self.assertEqual(terminal["partial_response_count"],1); self.assertEqual(terminal["source_values_accepted"],0)
        self.assertFalse((self.output/"RAW_IMMUTABLE/schema.csv").exists())

    def test_complete_response_before_parser_failure_is_accounted(self):
        body=b"not,a,schema\n"
        terminal=material_acquisition(self.candidate,self.output,self.invariants,opener=Opener([Response(body)]))
        self.assertEqual(terminal["failure_class"],"SOURCE_RESPONSE_HEADER_MISMATCH")
        self.assertEqual(terminal["network_requests_started"],1); self.assertEqual(terminal["application_body_bytes_read"],len(body))
        self.assertEqual(terminal["complete_responses_obtained"],1)

    def test_timeout_after_previous_query_complete_preserves_exact_totals(self):
        schema=SCHEMA.read_bytes()
        terminal=material_acquisition(self.candidate,self.output,self.invariants,opener=Opener([Response(schema),PartialResponse(b"abcd")]))
        self.assertEqual(terminal["failure_class"],"DATALAB_TRANSPORT_FAILURE")
        self.assertEqual(terminal["network_requests_started"],2)
        self.assertEqual(terminal["application_body_bytes_read"],len(schema)+3)
        self.assertEqual(terminal["complete_responses_obtained"],1)
        self.assertEqual(terminal["failed_query_id"],"north_count")

    def test_premature_eof_is_transport_failure(self):
        response=Response(b"abc",declared=7)
        terminal=material_acquisition(self.candidate,self.output,self.invariants,opener=Opener([response]))
        obs=terminal["transport_observations"][0]
        self.assertEqual(terminal["failure_class"],"DATALAB_TRANSPORT_FAILURE")
        self.assertIn("PREMATURE_EOF",obs["diagnostic_message"]); self.assertTrue(obs["partial_body_exists"])


if __name__=="__main__": unittest.main()
