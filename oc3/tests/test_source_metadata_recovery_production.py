from contextlib import ExitStack
from copy import deepcopy
from contextlib import redirect_stderr, redirect_stdout
import io
import inspect
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed
from oc3lib.autonomous_recovery_envelope import RecoveryEnvelopeError, STOP_REQUIRES_HUMAN
from oc3lib import source_metadata_recovery_factory as factory
from oc3lib import source_metadata_recovery_governor as gov
from oc3lib import source_metadata_recovery_executors as executors
from oc3_source_metadata_recovery_mission_runner import run_mission
import oc3_source_metadata_recovery_supervisor as supervisor
import oc3_source_metadata_recovery_worker as worker


class ProductionHarness:
    def __init__(self):
        self.temp=tempfile.TemporaryDirectory(dir=PROJECT/"oc3")
        self.root=Path(self.temp.name)
        self.state=self.root/"state.json"; self.auth=self.root/"authorization.json"
        self.first=self.root/"first.json"; self.ledger=self.root/"ledger"
        self.repair_files=[]
        self.old_paths=factory._paths
        self.old_first_candidate_relative=factory.FIRST_CANDIDATE_RELATIVE
        def paths(kind,generation):
            stem=f"G{generation:02d}-{kind}"
            base=self.root.relative_to(PROJECT)
            output=base/f"outputs/{stem}"
            return {"stage_id":f"OC3-SOURCE-METADATA-RECOVERY-{stem}",
                "candidate_path":str(base/f"candidates/{stem}.json"),
                "output_directory":str(output),"permit_path":str(base/f"permits/{stem}.json"),
                "worker_capability_path":str(output/"WORKER_CAPABILITY.json")}
        factory._paths=paths
        factory.FIRST_CANDIDATE_RELATIVE=str(self.first.relative_to(PROJECT))
        self.agentic_root=self.root/"agentic"
        def agentic_paths(generation):
            return {"request":self.agentic_root/f"AGENTIC_REPAIR_REQUEST_{generation:02d}.json",
                "patch":self.agentic_root/f"TECHNICAL_PATCH_MANIFEST_{generation:02d}.json",
                "contract":self.agentic_root/f"TECHNICAL_TRANSPORT_CONTRACT_{generation:02d}.json",
                "receipts":self.agentic_root/f"TECHNICAL_REPAIR_TEST_RECEIPTS_{generation:02d}.json"}
        self.agentic_paths=agentic_paths
        parent=PROJECT/"oc3/source_metadata_acquisition_pilot/OC3-SOURCE-METADATA-ACQUISITION-PILOT-001/TERMINAL.json"
        first=factory.build_first_candidate(parent_terminal_path=parent,action_registry_path=gov.ACTION_REGISTRY,
            technical_authorities_path=gov.TECHNICAL_AUTHORITIES,scientific_invariants_path=gov.INVARIANTS,
            recovery_graph_path=gov.RECOVERY_GRAPH,recovery_budget_path=gov.RECOVERY_BUDGET,
            mutable_surface_path=gov.MUTABLE_SURFACE,state_path=self.state,
            standing_authorization_path=self.auth,implementation_aggregate=gov.implementation_aggregate())
        self.first.write_bytes(canonical(first)+b"\n")
        state={k:v for k,v in gov.validate_state().items() if k!="sealed"}
        state.update({"active":False,"active_adapter":None,"active_adapter_binding":None,
            "adapter_states":{"official_noirlab_tap_public_v1":"AVAILABLE_UNVALIDATED",
                "query_manager_public_anonymous_v1":"AVAILABLE_UNVALIDATED"},
            "agentic_repair_request":None,"code_repair_generation":0,
            "current_stage":"FIRST_ACTION_PREPARED","last_action_terminal":gov.binding(parent),
            "last_action_terminal_sha256":file_sha256(parent),"last_classification":None,
            "material_body_bytes_remaining":67_108_864,"material_requests_remaining":5,
            "next_action_kind":"TECHNICAL_RESPONSE_DIAGNOSTIC","permits_issued":0,
            "recovery_generation":0,"registered_pending_action":None,"scientific_outcome":None,
            "sequence":0,"standing_authorization":None,"state":gov.STATE_WAITING,
            "stop_reason":None,"technical_body_bytes_remaining":2_097_152,
            "technical_failure_occurrences":{},"technical_requests_remaining":8,
            "validated_patch_manifest":None,"validated_test_receipts":None,
            "validated_transport_contract":None})
        state["first_candidate"]={"path":str(self.first.relative_to(PROJECT)),"sha256":file_sha256(self.first)}
        self.state.write_bytes(canonical(sealed(state))+b"\n")
        auth=sealed({"action_registry":gov.binding(gov.ACTION_REGISTRY),"authorized":True,
            "candidate_factory_sha256":file_sha256(PROJECT/"oc3/oc3lib/source_metadata_recovery_factory.py"),
            "first_candidate":gov.binding(self.first),
            "initial_state_sha256":file_sha256(self.state),"mandate":gov.binding(gov.MANDATE),
            "mission_id":gov.MISSION_ID,"mission_runner_sha256":file_sha256(PROJECT/"oc3/oc3_source_metadata_recovery_mission_runner.py"),
            "mutable_technical_surface":gov.binding(gov.MUTABLE_SURFACE),"policy_core_manifest":gov.binding(gov.POLICY_MANIFEST),
            "predecessor_run":gov.binding(gov.RUN_001_CLOSURE),"run_id":gov.RUN_ID,
            "recovery_budget":gov.binding(gov.RECOVERY_BUDGET),"recovery_graph":gov.binding(gov.RECOVERY_GRAPH),
            "schema_version":"OC3_SOURCE_METADATA_RECOVERY_STANDING_AUTHORIZATION_002",
            "scientific_invariants":gov.binding(gov.INVARIANTS),"technical_authorities":gov.binding(gov.TECHNICAL_AUTHORITIES)})
        self.auth.write_bytes(canonical(auth)+b"\n")
        self.stack=ExitStack()
        self.stack.enter_context(patch.object(gov,"FIRST_CANDIDATE",self.first))
        self.stack.enter_context(patch.object(gov,"PERMIT_CONSUMPTION",self.root/"permit_consumption"))
        self.stack.enter_context(patch.object(gov,"CAPABILITY_CONSUMPTION",self.root/"capability_consumption"))
        self.stack.enter_context(patch.object(gov,"agentic_paths",agentic_paths))

    def close(self):
        self.stack.close(); factory._paths=self.old_paths
        factory.FIRST_CANDIDATE_RELATIVE=self.old_first_candidate_relative
        for path in self.repair_files:
            if path.exists(): path.unlink()
        self.temp.cleanup()

    def create_agentic_artifacts(self, *, adapter_id="query_manager_public_anonymous_v1",
                                 changed_path=None,
                                 mutate_queries=False):
        state=gov.validate_state(self.state); generation=state["recovery_generation"]+1
        paths=self.agentic_paths(generation); self.agentic_root.mkdir(parents=True,exist_ok=True)
        request=load_canonical_json(paths["request"])
        authorities=load_canonical_json(gov.TECHNICAL_AUTHORITIES)
        registry_adapter=next((row for row in authorities["adapters"] if row["adapter_id"]==adapter_id),None)
        hashes=request["query_semantic_hashes"]
        after_hashes=dict(hashes)
        if mutate_queries: after_hashes["schema"]="0"*64
        if changed_path is None:
            target=PROJECT/f"oc3/recovery_tests/source_metadata/agentic_{self.root.name}.txt"
            target.parent.mkdir(parents=True,exist_ok=True); target.write_text("synthetic bounded repair\n")
            self.repair_files.append(target); changed_path=str(target.relative_to(PROJECT)); before=None
        else:
            target=PROJECT/changed_path
            registered=next((row for row in authorities["adapters"] if row["implementation_path"]==changed_path),None)
            before=registered["bootstrap_sha256"] if registered else (file_sha256(target) if target.is_file() else None)
        current=file_sha256(target) if target.is_file() else None
        patch_manifest=sealed({"base_commit":request["current_git_head"],
            "changed_paths":[{"after_sha256":current,"before_sha256":before,"path":changed_path}],
            "claimed_repair_scope":"TECHNICAL_ADAPTER_ONLY","firewall_hash_after":file_sha256(gov.MUTABLE_SURFACE),
            "firewall_hash_before":file_sha256(gov.MUTABLE_SURFACE),
            "parent_action_terminal":state["last_action_terminal"],"patch_diff_sha256":"0"*64,
            "query_semantic_hashes_after":after_hashes,"query_semantic_hashes_before":hashes,
            "recovery_generation":generation,"recovery_graph_sha256_after":file_sha256(gov.RECOVERY_GRAPH),
            "recovery_graph_sha256_before":file_sha256(gov.RECOVERY_GRAPH),
            "run_id":gov.RUN_ID,"schema_version":"TECHNICAL_PATCH_MANIFEST_1",
            "scientific_invariants_sha256_after":file_sha256(gov.INVARIANTS),
            "scientific_invariants_sha256_before":file_sha256(gov.INVARIANTS),
            "technical_failure_class":"DOCUMENTARY_EVIDENCE_ACQUIRED",
            "tests_executed":request["required_tests"]})
        paths["patch"].write_bytes(canonical(patch_manifest)+b"\n")
        implementation_path=(registry_adapter or {"implementation_path":"oc3/recovery_adapters/source_metadata/unsupported.py"})["implementation_path"]
        resource_ids=(registry_adapter or {"allowed_authority_resource_ids":["NOIRLAB_DATALAB_USER_MANUAL"]})["allowed_authority_resource_ids"]
        contract=sealed({"adapter_id":adapter_id,"authority_resource_ids":resource_ids,
            "authentication_mode":"ANONYMOUS_PUBLIC",
            "endpoint":"https://example.invalid/query","evidence":[request["diagnostic_and_documentary_evidence"][-1]],
            "http_method":"GET","implementation_path":implementation_path,
            "parameter_serialization":"URL_QUERY_PARAMETERS",
            "query_semantic_hashes":hashes,"query_semantic_preservation_rule":"BYTE_IDENTICAL_FROZEN_ADQL",
            "redirect_policy":"FORBID","response_representation":"CSV","run_id":gov.RUN_ID,
            "schema_version":"OC3_SOURCE_METADATA_TECHNICAL_TRANSPORT_CONTRACT_001"})
        paths["contract"].write_bytes(canonical(contract)+b"\n")
        receipts=sealed({"all_required_passed":True,"real_network_requests":0,"run_id":gov.RUN_ID,
            "schema_version":"OC3_SOURCE_METADATA_TECHNICAL_REPAIR_TEST_RECEIPTS_001",
            "tests_executed":request["required_tests"]})
        paths["receipts"].write_bytes(canonical(receipts)+b"\n")
        return paths

    @staticmethod
    def terminal(candidate,failure,**extra):
        return {"action_kind":candidate["action_kind"],"application_body_bytes_read":0,
            "failure_class":failure,"network_requests_started":0,"request_class":candidate["request_class"],
            "run_id":candidate["run_id"],"schema_version":"SYNTHETIC_ACTION_TERMINAL_001","source_values_accepted":0,
            "stage_id":candidate["stage_id"],**extra}


class ProductionRunnerTests(unittest.TestCase):
    def setUp(self): self.h=ProductionHarness()
    def tearDown(self):
        if self.h is not None: self.h.close()

    def reach_handoff(self):
        def executor(c):
            failure="TECHNICAL_DIAGNOSTIC_CLASSIFIED" if c["action_kind"]=="TECHNICAL_RESPONSE_DIAGNOSTIC" else "DOCUMENTARY_EVIDENCE_ACQUIRED"
            return self.h.terminal(c,failure)
        return run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor),executor

    def run_real_adapter_repair(self, *, drift=False):
        self.reach_handoff()
        adapter_path="oc3/recovery_adapters/source_metadata/transport_registry.py"
        target=PROJECT/adapter_path; original=target.read_bytes()
        bootstrap_sha=file_sha256(target); material_candidates=[]
        try:
            target.write_bytes(original+b"\n# bounded synthetic repaired adapter bytes\n")
            repaired_sha=file_sha256(target)
            self.assertNotEqual(repaired_sha,bootstrap_sha)
            self.assertEqual(gov.validate_static_authorities()["technical_authorities"]["adapters"][0]["bootstrap_sha256"],bootstrap_sha)
            artifacts=self.h.create_agentic_artifacts(changed_path=adapter_path)
            def executor(candidate):
                if candidate["action_kind"]=="OFFLINE_TECHNICAL_REPAIR":
                    result=executors.offline_repair(candidate,PROJECT/candidate["output_directory"])
                    return {k:v for k,v in result.items() if k!="sealed"}
                if candidate["action_kind"]=="MATERIAL_SOURCE_METADATA_ACQUISITION":
                    material_candidates.append(candidate)
                    if drift: target.write_bytes(target.read_bytes()+b"# post-validation drift\n")
                    if drift:
                        result=executors.material_acquisition(candidate,PROJECT/candidate["output_directory"],
                            load_canonical_json(gov.INVARIANTS))
                        return {k:v for k,v in result.items() if k!="sealed"}
                    executors.validate_material_adapter_binding(candidate)
                    return self.h.terminal(candidate,"SOURCE_METADATA_ACQUISITION_COMPLETED")
                raise AssertionError(candidate["action_kind"])
            with patch.object(executors,"_git_changed_paths",return_value=[adapter_path]), \
                    patch.object(executors,"_git_blob_sha256",return_value=bootstrap_sha):
                state=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
                    first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
            return state,material_candidates,repaired_sha
        finally:
            target.write_bytes(original)

    def test_actual_runner_multi_action_to_scientific_terminal(self):
        outcomes={"TECHNICAL_RESPONSE_DIAGNOSTIC":"TECHNICAL_DIAGNOSTIC_CLASSIFIED",
            "OFFICIAL_SERVICE_DOCUMENTARY_PROBE":"DOCUMENTARY_EVIDENCE_ACQUIRED",
            "OFFLINE_TECHNICAL_REPAIR":"TECHNICAL_PATCH_VALIDATED",
            "MATERIAL_SOURCE_METADATA_ACQUISITION":"SOURCE_METADATA_ACQUISITION_COMPLETED"}
        seen=[]
        def executor(c):
            seen.append(c["action_kind"]); extra={}
            if c["action_kind"]=="OFFLINE_TECHNICAL_REPAIR":
                return {k:v for k,v in executors.offline_repair(c,PROJECT/c["output_directory"]).items() if k!="sealed"}
            return self.h.terminal(c,outcomes[c["action_kind"]],**extra)
        authorization_sha=file_sha256(self.h.auth)
        handoff=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(handoff["current_stage"],"AWAITING_AGENTIC_TECHNICAL_REPAIR")
        self.assertTrue(handoff["active"]); self.assertIsNone(handoff["registered_pending_action"])
        self.assertEqual(len(list((self.h.root/"permits").glob("*.json"))),2)
        artifacts=self.h.create_agentic_artifacts()
        changed=load_canonical_json(artifacts["patch"])["changed_paths"][0]["path"]
        with patch.object(executors,"_git_changed_paths",return_value=[changed]), \
                patch.object(executors,"_git_blob_sha256",return_value=None):
            state=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
                first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(seen,["TECHNICAL_RESPONSE_DIAGNOSTIC","OFFICIAL_SERVICE_DOCUMENTARY_PROBE",
            "OFFLINE_TECHNICAL_REPAIR","MATERIAL_SOURCE_METADATA_ACQUISITION"])
        self.assertEqual(state["state"],gov.STATE_TERMINAL)
        self.assertEqual(file_sha256(self.h.auth),authorization_sha)
        self.assertEqual(len(list((self.h.root/"permits").glob("*.json"))),4)
        self.assertEqual(len(list((self.h.root/"capability_consumption").glob("*.json"))),4)

    def test_first_candidate_crosses_real_supervisor_and_worker_path_gates_offline(self):
        state=gov.activate(state_path=self.h.state,authorization_path=self.h.auth,
            activated_at_utc="2026-01-01T00:00:00Z")
        self.assertEqual(state["run_id"],gov.RUN_ID)
        gov.register_action(state_path=self.h.state,candidate_path=self.h.first)
        candidate=gov.validate_first_candidate(self.h.first)
        permit=PROJECT/candidate["permit_path"]
        gov.issue_permit(state_path=self.h.state,candidate_path=self.h.first,
            output_path=permit,issued_at_utc="2026-01-01T00:00:01Z")

        def fake_action(c, output, authorities, invariants):
            return {"action_kind":c["action_kind"],"application_body_bytes_read":0,
                "failure_class":"CREDENTIALS_REQUIRED","network_requests_started":0,
                "request_class":c["request_class"],"run_id":c["run_id"],
                "schema_version":"SYNTHETIC_PATH_GATE_TERMINAL_001",
                "source_values_accepted":0,"stage_id":c["stage_id"]}

        def invoke_worker(command, **kwargs):
            out=io.StringIO(); err=io.StringIO()
            with patch.object(sys,"argv",command[1:]), patch.object(worker,"execute_action",side_effect=fake_action), \
                    redirect_stdout(out), redirect_stderr(err):
                return_code=worker.main(command[2:])
            return subprocess.CompletedProcess(command,return_code,out.getvalue(),err.getvalue())

        out=io.StringIO(); err=io.StringIO()
        with patch.object(sys,"argv",candidate["command_argv"][1:]), \
                patch.object(supervisor.subprocess,"run",side_effect=invoke_worker), \
                redirect_stdout(out), redirect_stderr(err):
            return_code=supervisor.main(candidate["command_argv"][2:])
        self.assertEqual(return_code,0,err.getvalue())
        self.assertTrue(gov.permit_consumption_path(permit).is_file())
        capability=PROJECT/candidate["worker_capability_path"]
        self.assertTrue(capability.is_file())
        self.assertTrue(gov.capability_consumption_path(capability).is_file())
        self.assertTrue((PROJECT/candidate["output_directory"]/"TERMINAL.json").is_file())
        self.assertEqual(load_canonical_json(capability)["candidate_path"],candidate["candidate_path"])
        self.assertEqual(load_canonical_json(capability)["run_id"],gov.RUN_ID)

    def test_run_001_permit_and_authorization_cannot_cross_into_run_002(self):
        run_001_permit=PROJECT/"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_PERMITS/OC3-SOURCE-METADATA-RECOVERY-G01-TECHNICAL_RESPONSE_DIAGNOSTIC.json"
        run_001_auth=PROJECT/"oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_001.json"
        self.assertTrue(run_001_permit.is_file()); self.assertTrue(run_001_auth.is_file())
        with self.assertRaises(RecoveryEnvelopeError):
            gov.validate_permit(permit_path=run_001_permit,candidate_path=self.h.first)
        with self.assertRaises(RecoveryEnvelopeError):
            gov.validate_standing_authorization(run_001_auth,state_path=self.h.state)
        historical_marker=PROJECT/"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_LEDGER/PERMIT_CONSUMPTION"/f"{file_sha256(run_001_permit)}.json"
        self.assertFalse(historical_marker.exists())
        self.assertFalse((PROJECT/gov.validate_first_candidate(self.h.first)["worker_capability_path"]).exists())

    def test_permit_and_capability_alternate_candidate_paths_fail_closed(self):
        gov.activate(state_path=self.h.state,authorization_path=self.h.auth,
            activated_at_utc="2026-01-01T00:00:00Z")
        gov.register_action(state_path=self.h.state,candidate_path=self.h.first)
        candidate=gov.validate_first_candidate(self.h.first); permit=PROJECT/candidate["permit_path"]
        gov.issue_permit(state_path=self.h.state,candidate_path=self.h.first,
            output_path=permit,issued_at_utc="2026-01-01T00:00:01Z")
        original=permit.read_bytes(); value={k:v for k,v in load_canonical_json(permit).items() if k!="sealed"}
        value["candidate_path"]="oc3/alternate-candidate.json"
        permit.write_bytes(canonical(sealed(value))+b"\n")
        with self.assertRaisesRegex(RecoveryEnvelopeError,"RECOVERY_PERMIT_INVALID"):
            gov.validate_permit(permit_path=permit,candidate_path=self.h.first)
        permit.write_bytes(original)
        marker=gov.consume_permit(permit_path=permit,candidate_path=self.h.first,
            consumed_at_utc="2026-01-01T00:00:02Z")
        output=PROJECT/candidate["output_directory"]; output.mkdir(parents=True)
        capability=PROJECT/candidate["worker_capability_path"]
        gov.create_worker_capability(candidate_path=self.h.first,permit_path=permit,
            permit_marker=marker,authorization_path=self.h.auth,state_path=self.h.state,
            capability_path=capability,issued_at_utc="2026-01-01T00:00:03Z")
        value={k:v for k,v in load_canonical_json(capability).items() if k!="sealed"}
        value["candidate_path"]="oc3/alternate-candidate.json"
        capability.write_bytes(canonical(sealed(value))+b"\n")
        with self.assertRaisesRegex(RecoveryEnvelopeError,"RECOVERY_WORKER_CAPABILITY_INVALID"):
            gov.validate_worker_capability(capability_path=capability,candidate_path=self.h.first,
                permit_path=permit,authorization_path=self.h.auth,state_path=self.h.state)

    def test_actual_runner_failure_loop_stops_without_fourth_candidate(self):
        calls=[]
        def executor(c): calls.append(c["stage_id"]); return self.h.terminal(c,"DATALAB_TRANSPORT_FAILURE")
        state=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(state["state"],STOP_REQUIRES_HUMAN); self.assertEqual(len(calls),3)
        self.assertEqual(len(list((self.h.root/"candidates").glob("*.json"))),2)

    def test_resource_bound_finalizes_and_credentials_stop(self):
        def resource(c): return self.h.terminal(c,"SOURCE_COUNT_RESOURCE_BOUND")
        state=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=resource)
        self.assertEqual((state["state"],state["scientific_outcome"]),(gov.STATE_TERMINAL,"SOURCE_COUNT_RESOURCE_BOUND"))

    def test_credentials_stop_without_second_action(self):
        calls=[]
        def executor(c): calls.append(1); return self.h.terminal(c,"CREDENTIALS_REQUIRED")
        state=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(state["state"],STOP_REQUIRES_HUMAN); self.assertEqual(len(calls),1)

    def test_control_plane_resume_after_transition(self):
        calls=[]
        def executor(c):
            calls.append(c["action_kind"])
            return self.h.terminal(c,"TECHNICAL_DIAGNOSTIC_CLASSIFIED" if
                c["action_kind"] == "TECHNICAL_RESPONSE_DIAGNOSTIC" else "CREDENTIALS_REQUIRED")
        original=gov.expected_child
        with patch.object(gov,"expected_child",side_effect=RuntimeError("synthetic crash after durable transition")):
            with self.assertRaises(RuntimeError):
                run_mission(state_path=self.h.state,authorization_path=self.h.auth,
                    first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        interrupted=gov.validate_state(self.h.state)
        self.assertEqual((interrupted["state"],interrupted["current_stage"],interrupted["registered_pending_action"]),
            ("ACTIVE","AWAITING_NEXT_ACTION_REGISTRATION",None))
        (self.h.ledger/"RUNNER_CRASH.json").unlink()
        state=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(state["state"],STOP_REQUIRES_HUMAN)

    def test_missing_patch_keeps_handoff_and_invalid_or_unsupported_artifacts_stop(self):
        handoff,executor=self.reach_handoff()
        permits=handoff["permits_issued"]
        unchanged=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual((unchanged["current_stage"],unchanged["permits_issued"]),
            ("AWAITING_AGENTIC_TECHNICAL_REPAIR",permits))
        self.h.create_agentic_artifacts(adapter_id="unsupported_adapter")
        stopped=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual((stopped["state"],stopped["stop_reason"]),
            (STOP_REQUIRES_HUMAN,"TECHNICAL_TRANSPORT_CONTRACT_INVALID"))

    def test_patch_outside_surface_and_query_hash_change_stop(self):
        _,executor=self.reach_handoff()
        self.h.create_agentic_artifacts(changed_path="oc3/oc3lib/source_metadata_recovery_governor.py")
        stopped=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(stopped["stop_reason"],"TECHNICAL_PATCH_OUTSIDE_MUTABLE_SURFACE")

        self.h.close(); self.h=ProductionHarness(); _,executor=self.reach_handoff()
        self.h.create_agentic_artifacts(mutate_queries=True)
        stopped=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(stopped["stop_reason"],"TECHNICAL_PATCH_IMMUTABLE_CONTRACT_CHANGED")

    def test_material_candidate_requires_validated_active_adapter(self):
        state={k:v for k,v in gov.validate_state(self.h.state).items() if k!="sealed"}
        state.update({"active":True,"state":"ACTIVE","registered_pending_action":None,
            "last_classification":{"decision":"RECOVER_AUTONOMOUSLY","failure_class":"TECHNICAL_PATCH_VALIDATED",
                "next_action_kind":"MATERIAL_SOURCE_METADATA_ACQUISITION"},
            "next_action_kind":"MATERIAL_SOURCE_METADATA_ACQUISITION","active_adapter":"query_manager_public_anonymous_v1",
            "adapter_states":{"query_manager_public_anonymous_v1":"AVAILABLE_UNVALIDATED"}})
        parent=PROJECT/state["last_action_terminal"]["path"]
        with self.assertRaisesRegex(RecoveryEnvelopeError,"TECHNICAL_ADAPTER_NOT_VALIDATED"):
            factory.build_next_candidate(state=state,parent_terminal_path=parent,
                action_registry_path=gov.ACTION_REGISTRY,technical_authorities_path=gov.TECHNICAL_AUTHORITIES,
                scientific_invariants_path=gov.INVARIANTS,recovery_graph_path=gov.RECOVERY_GRAPH,
                recovery_budget_path=gov.RECOVERY_BUDGET,mutable_surface_path=gov.MUTABLE_SURFACE,
                state_path=self.h.state,standing_authorization_path=self.h.auth,
                implementation_aggregate=gov.implementation_aggregate())

    def test_documentary_and_adapter_executor_semantics_are_not_hard_coded(self):
        documentary=inspect.getsource(executors.documentary_probe)
        repair=inspect.getsource(executors.offline_repair)
        self.assertIn('"DOCUMENTARY_EVIDENCE_ACQUIRED"',documentary)
        self.assertNotIn('"DOCUMENTARY_TRANSPORT_CONTRACT_RESOLVED"',documentary)
        self.assertNotIn("query_manager_public_anonymous_v1",repair)
        self.assertIn('contract.get("adapter_id")',repair)

    def test_real_adapter_repair_binds_new_runtime_sha_without_bootstrap_rejection(self):
        state,candidates,repaired_sha=self.run_real_adapter_repair()
        self.assertEqual(state["state"],gov.STATE_TERMINAL)
        self.assertEqual(len(candidates),1)
        binding=candidates[0]["active_adapter_binding"]
        self.assertEqual(binding["implementation_sha256"],repaired_sha)
        self.assertEqual(binding["implementation_path"],"oc3/recovery_adapters/source_metadata/transport_registry.py")
        self.assertEqual(state["active_adapter_binding"],binding)

    def test_post_validation_adapter_drift_stops_before_material_network(self):
        state,candidates,_=self.run_real_adapter_repair(drift=True)
        self.assertEqual(len(candidates),1)
        self.assertEqual((state["state"],state["stop_reason"]),(STOP_REQUIRES_HUMAN,"ADAPTER_IMPLEMENTATION_DRIFT"))
        terminal=load_canonical_json(PROJECT/state["last_action_terminal"]["path"])
        self.assertEqual(terminal["failure_class"],"ADAPTER_IMPLEMENTATION_DRIFT")
        self.assertEqual(terminal["network_requests_started"],0)
        output=PROJECT/candidates[0]["output_directory"]
        self.assertFalse((output/"REQUEST_INTENT.json").exists())
        self.assertFalse((output/"RAW_IMMUTABLE").exists())

    def test_git_derived_real_adapter_change_is_exact_in_isolated_repository(self):
        with tempfile.TemporaryDirectory(dir=PROJECT/"oc3") as directory:
            root=Path(directory); relative="oc3/recovery_adapters/source_metadata/adapter.py"
            target=root/relative; target.parent.mkdir(parents=True); target.write_text("bootstrap\n")
            subprocess.run(["git","init","-q"],cwd=root,check=True)
            subprocess.run(["git","config","user.email","synthetic@example.invalid"],cwd=root,check=True)
            subprocess.run(["git","config","user.name","Synthetic Test"],cwd=root,check=True)
            subprocess.run(["git","add",relative],cwd=root,check=True)
            subprocess.run(["git","commit","-qm","bootstrap"],cwd=root,check=True)
            base=subprocess.run(["git","rev-parse","HEAD"],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
            before=file_sha256(target); target.write_text("repaired\n")
            with patch.object(executors,"PROJECT",root):
                self.assertEqual(executors._git_changed_paths(base,("oc3/recovery_adapters/source_metadata/",)),[relative])
                self.assertEqual(executors._git_blob_sha256(base,relative),before)

    def test_tap_identity_is_prospective_and_cannot_materialize_unvalidated(self):
        authorities=gov.validate_static_authorities()["technical_authorities"]
        tap=next(row for row in authorities["adapters"] if row["adapter_id"]=="official_noirlab_tap_public_v1")
        self.assertEqual(tap["initial_state"],"AVAILABLE_UNVALIDATED")
        self.assertIsNone(tap["bootstrap_sha256"])
        self.assertFalse((PROJECT/tap["implementation_path"]).exists())
        state={k:v for k,v in gov.validate_state(self.h.state).items() if k!="sealed"}
        state.update({"active":True,"state":"ACTIVE","registered_pending_action":None,
            "last_classification":{"decision":"RECOVER_AUTONOMOUSLY","failure_class":"TECHNICAL_PATCH_VALIDATED",
                "next_action_kind":"MATERIAL_SOURCE_METADATA_ACQUISITION"},
            "next_action_kind":"MATERIAL_SOURCE_METADATA_ACQUISITION","active_adapter":"official_noirlab_tap_public_v1",
            "active_adapter_binding":None})
        parent=PROJECT/state["last_action_terminal"]["path"]
        with self.assertRaisesRegex(RecoveryEnvelopeError,"TECHNICAL_ADAPTER_NOT_VALIDATED"):
            factory.build_next_candidate(state=state,parent_terminal_path=parent,
                action_registry_path=gov.ACTION_REGISTRY,technical_authorities_path=gov.TECHNICAL_AUTHORITIES,
                scientific_invariants_path=gov.INVARIANTS,recovery_graph_path=gov.RECOVERY_GRAPH,
                recovery_budget_path=gov.RECOVERY_BUDGET,mutable_surface_path=gov.MUTABLE_SURFACE,
                state_path=self.h.state,standing_authorization_path=self.h.auth,
                implementation_aggregate=gov.implementation_aggregate())

    def test_registry_and_frozen_science(self):
        values=gov.validate_static_authorities()
        self.assertEqual([x["action_kind"] for x in values["action_registry"]["actions"]],list(factory.ACTION_FAMILIES))
        self.assertEqual(file_sha256(gov.INVARIANTS),"0d2b304e815a949cf7f69d44cd43148eb663fadb68afb47a7e9f767635a329f3")
        self.assertEqual(file_sha256(gov.RECOVERY_GRAPH),"19e7d6226d6550efbd32c62a4268d682e448f15fb3c490550471286943587fb7")

    def test_production_first_candidate_is_byte_recomputed_and_self_bound(self):
        self.h.close(); self.h=None
        candidate=gov.validate_first_candidate(gov.FIRST_CANDIDATE)
        parent=PROJECT/candidate["parent_action_terminal"]["path"]
        expected=factory.build_first_candidate(parent_terminal_path=parent,
            action_registry_path=gov.ACTION_REGISTRY,technical_authorities_path=gov.TECHNICAL_AUTHORITIES,
            scientific_invariants_path=gov.INVARIANTS,recovery_graph_path=gov.RECOVERY_GRAPH,
            recovery_budget_path=gov.RECOVERY_BUDGET,mutable_surface_path=gov.MUTABLE_SURFACE,
            state_path=gov.STATE,standing_authorization_path=gov.STANDING_AUTHORIZATION,
            implementation_aggregate=gov.implementation_aggregate())
        self.assertEqual(gov.FIRST_CANDIDATE.read_bytes(),canonical(expected)+b"\n")
        canonical_path=str(gov.FIRST_CANDIDATE.relative_to(PROJECT))
        self.assertEqual(candidate["candidate_path"],canonical_path)
        for argv in (candidate["command_argv"],candidate["worker_argv"]):
            self.assertEqual(argv[argv.index("--candidate")+1],str(gov.FIRST_CANDIDATE))

    def test_candidate_path_tampering_and_same_byte_copy_fail_closed(self):
        candidate=gov.validate_first_candidate(self.h.first)
        with tempfile.TemporaryDirectory(dir=PROJECT/"oc3") as directory:
            root=Path(directory); base_path=root/"candidate.json"
            base={k:v for k,v in candidate.items() if k!="sealed"}
            base["candidate_path"]=str(base_path.relative_to(PROJECT))
            for key in ("command_argv","worker_argv"):
                argv=list(base[key]); argv[argv.index("--candidate")+1]=str(base_path); base[key]=argv
            from oc3lib.cross_observer_grouping import sha256_bytes
            base["command_argv_sha256"]=sha256_bytes(canonical(base["command_argv"]))
            base["worker_argv_sha256"]=sha256_bytes(canonical(base["worker_argv"]))

            def write(value): base_path.write_bytes(canonical(sealed(value))+b"\n")
            write(base); gov.validate_candidate(base_path)
            copied=root/"copied.json"; copied.write_bytes(base_path.read_bytes())
            with self.assertRaisesRegex(RecoveryEnvelopeError,"RECOVERY_CANDIDATE_SELF_PATH_MISMATCH"):
                gov.validate_candidate(copied)
            linked=root/"linked.json"; linked.symlink_to(base_path)
            with self.assertRaisesRegex(RecoveryEnvelopeError,"RECOVERY_CANDIDATE_SELF_PATH_MISMATCH"):
                gov.validate_candidate(linked)
            moved=root/"moved.json"; base_path.rename(moved)
            with self.assertRaisesRegex(RecoveryEnvelopeError,"RECOVERY_CANDIDATE_SELF_PATH_MISMATCH"):
                gov.validate_candidate(moved)
            moved.rename(base_path)
            for name,mutate in {
                "self":lambda v:v.__setitem__("candidate_path","oc3/alternate.json"),
                "supervisor":lambda v:v["command_argv"].__setitem__(v["command_argv"].index("--candidate")+1,"/tmp/alternate.json"),
                "worker":lambda v:v["worker_argv"].__setitem__(v["worker_argv"].index("--candidate")+1,"/tmp/alternate.json"),
            }.items():
                with self.subTest(name=name):
                    changed=deepcopy(base); mutate(changed)
                    changed["command_argv_sha256"]=sha256_bytes(canonical(changed["command_argv"]))
                    changed["worker_argv_sha256"]=sha256_bytes(canonical(changed["worker_argv"]))
                    write(changed)
                    with self.assertRaisesRegex(RecoveryEnvelopeError,"RECOVERY_CANDIDATE_SELF_PATH_MISMATCH"):
                        gov.validate_candidate(base_path)

    def test_first_and_child_candidates_use_distinct_factory_derived_namespaces(self):
        self.h.close(); self.h=None
        first=gov.validate_first_candidate()
        self.assertEqual(first["candidate_path"],factory.FIRST_CANDIDATE_RELATIVE)
        child=factory._paths("OFFICIAL_SERVICE_DOCUMENTARY_PROBE",2)
        self.assertTrue(child["candidate_path"].startswith(
            "oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_LEDGER/CANDIDATES/"))
        self.assertNotEqual(first["candidate_path"],child["candidate_path"])

    def test_generated_child_tampering_matrix_fails_recomputation(self):
        def executor(c): return self.h.terminal(c,"TECHNICAL_DIAGNOSTIC_CLASSIFIED")
        with patch.object(gov,"expected_child",side_effect=RuntimeError("pause after transition")):
            with self.assertRaises(RuntimeError):
                run_mission(state_path=self.h.state,authorization_path=self.h.auth,
                    first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        (self.h.ledger/"RUNNER_CRASH.json").unlink()
        state=gov.validate_state(self.h.state); parent=PROJECT/state["last_action_terminal"]["path"]
        path,expected=gov.expected_child(state,parent,state_path=self.h.state,authorization_path=self.h.auth)
        path.parent.mkdir(parents=True,exist_ok=True)
        mutations={"action_kind":lambda x:x.__setitem__("action_kind","TECHNICAL_INTEGRITY_TRIAGE"),
            "trigger":lambda x:x.__setitem__("trigger_failure_class","OTHER"),
            "parent":lambda x:x["parent_action_terminal"].__setitem__("sha256","0"*64),
            "generation":lambda x:x.__setitem__("recovery_generation",4),
            "authority":lambda x:x.__setitem__("authority_classes",["PINNED_ASTRO_DATALAB_SOURCE"]),
            "request_class":lambda x:x.__setitem__("request_class","MATERIAL"),
            "requests":lambda x:x.__setitem__("network_request_reservation",1),
            "body":lambda x:x.__setitem__("application_body_reservation",1),
            "worker":lambda x:x["worker_argv"].__setitem__(1,"/tmp/evil.py"),
            "supervisor":lambda x:x["command_argv"].__setitem__(1,"/tmp/evil.py"),
            "output":lambda x:x.__setitem__("output_directory","oc3/evil"),
            "permit":lambda x:x.__setitem__("permit_path","oc3/evil.json"),
            "capability":lambda x:x.__setitem__("worker_capability_path","oc3/evil-cap.json"),
            "adapter_binding":lambda x:x.__setitem__("active_adapter_binding",{"adapter_id":"forged"}),
            "budgets":lambda x:x["remaining_budgets"].__setitem__("technical_requests",999)}
        from oc3lib.cross_observer_grouping import sha256_bytes
        for name,mutate in mutations.items():
            with self.subTest(name=name):
                value=deepcopy({k:v for k,v in expected.items() if k!="sealed"}); mutate(value)
                value["command_argv_sha256"]=sha256_bytes(canonical(value["command_argv"]))
                value["worker_argv_sha256"]=sha256_bytes(canonical(value["worker_argv"]))
                path.write_bytes(canonical(sealed(value))+b"\n")
                with self.assertRaises(RecoveryEnvelopeError):
                    gov.validate_generated_candidate(path,state_path=self.h.state,parent_terminal_path=parent)


if __name__ == "__main__": unittest.main()
