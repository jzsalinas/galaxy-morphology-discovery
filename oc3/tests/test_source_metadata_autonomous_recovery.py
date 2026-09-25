from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes
from oc3lib.autonomous_recovery_envelope import (
    FINALIZE_SCIENTIFIC, RECOVER_AUTONOMOUSLY, STOP_REQUIRES_HUMAN,
    RecoveryEnvelopeError, validate_patch_manifest,
)
from oc3lib import source_metadata_recovery_governor as gov
from oc3lib.source_metadata_recovery_controller import controller_step, synthetic_replay
from oc3lib.source_metadata_recovery_factory import build_recovery_candidate, validate_parent, _paths
from recovery_adapters.source_metadata.technical_response_diagnostic import classify_representation


class RecoveryFixtures:
    @staticmethod
    def state():
        return {"active":True,"body_budget_material_parent":67_108_864,"code_repair_generation":0,
            "current_stage":"ACTION_REGISTERED","first_candidate":{},"last_action_terminal_sha256":None,
            "last_classification":None,"material_body_bytes_remaining":67_108_864,
            "material_requests_remaining":5,"mission_id":gov.MISSION_ID,"mission_scope":gov.MISSION_SCOPE,
            "next_action_kind":None,"permits_issued":0,"recovery_generation":0,
            "registered_pending_action":{"synthetic":True},"requests_material_parent":5,
            "schema_version":"OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_001","scientific_outcome":None,
            "sequence":1,"standing_authorization":{"synthetic":True},"state":"ACTIVE","stop_reason":None,
            "technical_body_bytes_remaining":2_097_152,"technical_failure_occurrences":{},
            "technical_requests_remaining":8}

    @staticmethod
    def terminal(failure, index=1, request_class="TECHNICAL", requests=0, body=0, **extra):
        return {"application_body_bytes_read":body,"failure_class":failure,
            "network_requests_started":requests,"request_class":request_class,
            "source_values_accepted":0,"terminal_sha256":f"{index:064x}",**extra}


class FrozenRecoveryContractTests(unittest.TestCase):
    def test_closed_predecessor_exact_bindings(self):
        self.assertEqual(file_sha256(PROJECT/"OC3_SOURCE_METADATA_ACQUISITION_PILOT_FINAL_REPORT_001.md"),
            "53e06603f44ac3aaace7ba16b6a4ad94ce3612274a0aaa4f00795a07b425dc71")
        self.assertEqual(file_sha256(PROJECT/"oc3/OC3_SOURCE_METADATA_ACQUISITION_PILOT_AUTONOMY_STATE_001.json"),
            "c066adaeeba21c16a0bc15070c8983c8a7e9d3c9a965c3fa74a9d0a2fbaea8e8")
        closure=load_canonical_json(PROJECT/"oc3/OC3_SOURCE_METADATA_ACQUISITION_PILOT_FINAL_CLOSURE_001.json")
        self.assertEqual(closure["final_ledger_aggregate_sha256"],
            "4618b3a1e739d554d3a8ea38aea3e9718513e4e7a4f11a693591f3af187908ee")
        self.assertEqual(closure["runtime_terminal_sha256"],
            "464a165b3281f5ec5c84617880e98d653bc1171c5eaa4d9b314d5464387b7d0e")

    def test_static_authorities_and_first_candidate_are_inactive(self):
        values=gov.validate_static_authorities(); candidate=gov.validate_first_candidate(); state=gov.validate_state()
        self.assertEqual(candidate["action_kind"],"TECHNICAL_RESPONSE_DIAGNOSTIC")
        self.assertEqual((candidate["network_request_reservation"],candidate["application_body_reservation"]),(1,65536))
        self.assertEqual((state["state"],state["active"],state["permits_issued"]),
            (gov.STATE_WAITING,False,0))
        self.assertFalse(gov.STANDING_AUTHORIZATION.exists())
        self.assertFalse((PROJECT/candidate["permit_path"]).exists())
        self.assertFalse((PROJECT/candidate["worker_capability_path"]).exists())
        self.assertEqual(values["budget"]["MAX_RECOVERY_GENERATIONS"],4)

    def test_scientific_invariant_query_and_holdout_mutations_fail(self):
        original=load_canonical_json(gov.INVARIANTS)
        target=deepcopy(original); target["target_guard_bricknames"].pop()
        with self.assertRaises(RecoveryEnvelopeError): gov.validate_scientific_invariants(target)
        query=deepcopy(original); query["queries"][0]["literal_adql"] += " AND 1=1"
        with self.assertRaisesRegex(RecoveryEnvelopeError,"SCIENTIFIC_QUERY_SEMANTICS_INVALID"):
            gov.validate_scientific_invariants(query)
        holdout=deepcopy(original); holdout["forbidden_holdout_bricknames"][-1]=holdout["target_guard_bricknames"][0]
        with self.assertRaisesRegex(RecoveryEnvelopeError,"SCIENTIFIC_HOLDOUT_FIREWALL_INVALID"):
            gov.validate_scientific_invariants(holdout)

    def test_first_candidate_preserves_exact_schema_semantics_and_material_zero(self):
        candidate=gov.validate_first_candidate(); invariants=load_canonical_json(gov.INVARIANTS)
        schema=next(row for row in invariants["queries"] if row["id"]=="schema")
        self.assertEqual(schema["semantic_sha256"],"d5be2b494f737e047fea77f4002d387fed15c5dbe3ad019f4a0cafe83faf4a0b")
        self.assertEqual(candidate["material_budget_reservation"],{"body_bytes":0,"requests":0})
        self.assertEqual(candidate["trigger_failure_class"],"DATALAB_TRANSPORT_FAILURE")

    def test_synthetic_representation_classifier_never_returns_schema_rows(self):
        self.assertEqual(classify_representation("text/html",b"<html><title>Data Lab</title><body>Query service</body></html>"),
            "HTML_SERVICE_PAGE")
        self.assertEqual(classify_representation("text/html",b"table_name,column_name,datatype\n"),
            "CSV_BODY_WITH_WRONG_CONTENT_TYPE")


class RecoveryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.graph=load_canonical_json(gov.RECOVERY_GRAPH)
        self.budget=load_canonical_json(gov.RECOVERY_BUDGET)

    def test_recoverable_action_does_not_finalize_mission(self):
        step=controller_step(RecoveryFixtures.state(),RecoveryFixtures.terminal("DATALAB_TRANSPORT_FAILURE"),self.graph,self.budget)
        self.assertEqual(step["directive"],"GENERATE_AND_REGISTER_NEXT_ACTION")
        self.assertEqual((step["state"]["active"],step["state"]["state"]),(True,"ACTIVE"))
        self.assertEqual(step["state"]["next_action_kind"],"TECHNICAL_RESPONSE_DIAGNOSTIC")

    def test_resource_bound_action_finalizes(self):
        step=controller_step(RecoveryFixtures.state(),RecoveryFixtures.terminal("SOURCE_COUNT_RESOURCE_BOUND"),self.graph,self.budget)
        self.assertEqual(step["classification"]["decision"],FINALIZE_SCIENTIFIC)
        self.assertEqual(step["directive"],"FINALIZE_SCIENTIFIC_MISSION")

    def test_scientific_integrity_failure_does_not_relax(self):
        step=controller_step(RecoveryFixtures.state(),RecoveryFixtures.terminal("SOURCE_IDENTITY_INTEGRITY_FAILURE"),self.graph,self.budget)
        self.assertEqual(step["classification"]["decision"],FINALIZE_SCIENTIFIC)

    def test_credentials_require_human_stop(self):
        step=controller_step(RecoveryFixtures.state(),RecoveryFixtures.terminal("CREDENTIALS_REQUIRED"),self.graph,self.budget)
        self.assertEqual((step["directive"],step["state"]["active"]),(STOP_REQUIRES_HUMAN,False))

    def test_generation_cap_and_technical_budget_exhaustion_stop(self):
        state=RecoveryFixtures.state(); state["recovery_generation"]=4
        step=controller_step(state,RecoveryFixtures.terminal("DATALAB_TRANSPORT_FAILURE"),self.graph,self.budget)
        self.assertEqual(step["directive"],STOP_REQUIRES_HUMAN)
        state=RecoveryFixtures.state(); state["technical_requests_remaining"]=0
        step=controller_step(state,RecoveryFixtures.terminal("DATALAB_TRANSPORT_FAILURE",requests=1),self.graph,self.budget)
        self.assertEqual(step["directive"],STOP_REQUIRES_HUMAN)

    def test_code_repair_generation_cap_stops(self):
        state=RecoveryFixtures.state(); state["code_repair_generation"]=3
        terminal=RecoveryFixtures.terminal("TECHNICAL_PATCH_VALIDATED",action_kind="OFFLINE_TECHNICAL_REPAIR")
        step=controller_step(state,terminal,self.graph,self.budget)
        self.assertEqual(step["directive"],STOP_REQUIRES_HUMAN)
        self.assertEqual(step["classification"]["reason"],"CODE_REPAIR_GENERATION_LIMIT_REACHED")

    def test_same_failure_class_loop_limit_stops_third_occurrence(self):
        state=RecoveryFixtures.state(); state["technical_failure_occurrences"]={"DATALAB_TRANSPORT_FAILURE":2}
        step=controller_step(state,RecoveryFixtures.terminal("DATALAB_TRANSPORT_FAILURE"),self.graph,self.budget)
        self.assertEqual(step["directive"],STOP_REQUIRES_HUMAN)

    def test_technical_and_material_accounting_are_separate(self):
        state=RecoveryFixtures.state()
        technical=controller_step(state,RecoveryFixtures.terminal("DATALAB_TRANSPORT_FAILURE",requests=1,body=10),self.graph,self.budget)["state"]
        self.assertEqual((technical["technical_requests_remaining"],technical["material_requests_remaining"]),(7,5))
        material_terminal=RecoveryFixtures.terminal("SOURCE_METADATA_ACQUISITION_COMPLETED",2,"MATERIAL",requests=2,body=20)
        material=controller_step(RecoveryFixtures.state(),material_terminal,self.graph,self.budget)["state"]
        self.assertEqual((material["technical_requests_remaining"],material["material_requests_remaining"]),(8,3))

    def test_observed_html_failure_replay_routes_to_diagnostic(self):
        terminal=RecoveryFixtures.terminal("DATALAB_TRANSPORT_FAILURE",requests=1,body=0,
            http_status=200,content_type="text/html",accepted_scientific_bytes=0)
        step=controller_step(RecoveryFixtures.state(),terminal,self.graph,self.budget)
        self.assertEqual(step["classification"],{"decision":RECOVER_AUTONOMOUSLY,
            "failure_class":"DATALAB_TRANSPORT_FAILURE","next_action_kind":"TECHNICAL_RESPONSE_DIAGNOSTIC",
            "reason":"EXPLICIT_RECOVERY_GRAPH_ROUTE"})
        self.assertTrue(step["state"]["active"])

    def test_successful_multi_recovery_replay_finalizes_only_after_success(self):
        failures=["DATALAB_TRANSPORT_FAILURE","TECHNICAL_DIAGNOSTIC_CLASSIFIED",
            "DOCUMENTARY_TRANSPORT_CONTRACT_RESOLVED","TECHNICAL_PATCH_VALIDATED",
            "SOURCE_METADATA_ACQUISITION_COMPLETED"]
        terminals=[RecoveryFixtures.terminal(f,i+1,"MATERIAL" if i==4 else "TECHNICAL") for i,f in enumerate(failures)]
        result=synthetic_replay(RecoveryFixtures.state(),terminals,self.graph,self.budget)
        self.assertEqual([x["directive"] for x in result["trace"][:-1]],
            ["GENERATE_AND_REGISTER_NEXT_ACTION"]*4)
        self.assertEqual(result["terminal_directive"],"FINALIZE_SCIENTIFIC_MISSION")
        self.assertEqual(result["state"]["recovery_generation"],4)

    def test_failure_loop_replay_stops_without_fourth_candidate(self):
        terminals=[RecoveryFixtures.terminal("DATALAB_TRANSPORT_FAILURE",i+1) for i in range(3)]
        result=synthetic_replay(RecoveryFixtures.state(),terminals,self.graph,self.budget)
        self.assertEqual(result["terminal_directive"],STOP_REQUIRES_HUMAN)
        self.assertEqual(len(result["trace"]),3)


class PatchAndFactoryTests(unittest.TestCase):
    def patch(self,path="oc3/recovery_adapters/source_metadata/adapter.py"):
        fixed="a"*64
        return {"base_commit":"b356b448f170d49a03727722324ed0d6e6913c34",
            "changed_paths":[{"after_sha256":"b"*64,"before_sha256":"a"*64,"path":path}],
            "claimed_repair_scope":"TECHNICAL_ADAPTER_ONLY","firewall_hash_after":fixed,"firewall_hash_before":fixed,
            "parent_action_terminal":{"path":"terminal.json","sha256":fixed},"patch_diff_sha256":"b"*64,
            "query_semantic_hashes_after":{"schema":fixed},"query_semantic_hashes_before":{"schema":fixed},
            "recovery_generation":1,"recovery_graph_sha256_after":fixed,"recovery_graph_sha256_before":fixed,
            "schema_version":"TECHNICAL_PATCH_MANIFEST_1","scientific_invariants_sha256_after":fixed,
            "scientific_invariants_sha256_before":fixed,"technical_failure_class":"LOCAL_PARSER_FAILURE",
            "tests_executed":["synthetic"]}

    def test_technical_adapter_only_patch_passes(self):
        validate_patch_manifest(self.patch(),load_canonical_json(gov.MUTABLE_SURFACE))

    def test_policy_core_and_immutable_mutations_fail_patch(self):
        with self.assertRaisesRegex(RecoveryEnvelopeError,"OUTSIDE_MUTABLE_SURFACE"):
            validate_patch_manifest(self.patch("oc3/oc3lib/autonomous_recovery_envelope.py"),load_canonical_json(gov.MUTABLE_SURFACE))
        for after in ("scientific_invariants_sha256_after","recovery_graph_sha256_after",
                      "query_semantic_hashes_after","firewall_hash_after"):
            manifest=self.patch(); manifest[after]="c"*64 if "hashes" not in after else {"schema":"c"*64}
            with self.assertRaisesRegex(RecoveryEnvelopeError,"IMMUTABLE_CONTRACT_CHANGED"):
                validate_patch_manifest(manifest,load_canonical_json(gov.MUTABLE_SURFACE))

    def test_candidate_factory_binds_parent_and_mismatch_fails(self):
        first=gov.validate_first_candidate()
        parent=PROJECT/first["parent_action_terminal"]["path"]
        candidate=first
        validate_parent(candidate,parent)
        with self.assertRaisesRegex(RecoveryEnvelopeError,"UNRESTRICTED_RECOVERY_FACTORY_DISABLED"):
            build_recovery_candidate(action_kind="CALLER_CHOSEN")
        with tempfile.NamedTemporaryFile(dir=PROJECT/"oc3",delete=False) as stream:
            wrong=Path(stream.name); stream.write(b"different")
        try:
            with self.assertRaisesRegex(RecoveryEnvelopeError,"PARENT_ACTION_TERMINAL_MISMATCH"):
                validate_parent(candidate,wrong)
        finally: wrong.unlink()

    def test_each_network_action_has_distinct_permit_and_capability_paths(self):
        one=_paths("TECHNICAL_RESPONSE_DIAGNOSTIC",1)
        two=_paths("TECHNICAL_RESPONSE_DIAGNOSTIC",2)
        self.assertNotEqual(one["permit_path"],two["permit_path"])
        self.assertNotEqual(one["worker_capability_path"],two["worker_capability_path"])
        self.assertNotEqual(one["output_directory"],two["output_directory"])

    def test_generation_cap_rejected_by_candidate_validator(self):
        candidate={k:v for k,v in gov.validate_first_candidate().items() if k!="sealed"}; candidate["recovery_generation"]=5
        with tempfile.NamedTemporaryFile(dir=PROJECT/"oc3",delete=False) as stream:
            path=Path(stream.name); stream.write(canonical(sealed(candidate))+b"\n")
        try:
            with self.assertRaisesRegex(RecoveryEnvelopeError,"RECOVERY_GENERATION_LIMIT"):
                gov.validate_candidate(path)
        finally: path.unlink()

    def test_permit_and_capability_are_single_use(self):
        self.assertTrue(gov.validate_first_candidate()["resume"] is False)


if __name__ == "__main__":
    unittest.main()
