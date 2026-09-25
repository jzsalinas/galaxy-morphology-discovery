from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed
from oc3lib.autonomous_recovery_envelope import RecoveryEnvelopeError, STOP_REQUIRES_HUMAN
from oc3lib import source_metadata_recovery_factory as factory
from oc3lib import source_metadata_recovery_governor as gov
from oc3_source_metadata_recovery_mission_runner import run_mission


class ProductionHarness:
    def __init__(self):
        self.temp=tempfile.TemporaryDirectory(dir=PROJECT/"oc3")
        self.root=Path(self.temp.name)
        self.state=self.root/"state.json"; self.auth=self.root/"authorization.json"
        self.first=self.root/"first.json"; self.ledger=self.root/"ledger"
        self.old_paths=factory._paths
        def paths(kind,generation):
            stem=f"G{generation:02d}-{kind}"
            base=self.root.relative_to(PROJECT)
            output=base/f"outputs/{stem}"
            return {"stage_id":f"OC3-SOURCE-METADATA-RECOVERY-{stem}",
                "candidate_path":str(base/f"candidates/{stem}.json"),
                "output_directory":str(output),"permit_path":str(base/f"permits/{stem}.json"),
                "worker_capability_path":str(output/"WORKER_CAPABILITY.json")}
        factory._paths=paths
        parent=PROJECT/"oc3/source_metadata_acquisition_pilot/OC3-SOURCE-METADATA-ACQUISITION-PILOT-001/TERMINAL.json"
        first=factory.build_first_candidate(parent_terminal_path=parent,action_registry_path=gov.ACTION_REGISTRY,
            technical_authorities_path=gov.TECHNICAL_AUTHORITIES,scientific_invariants_path=gov.INVARIANTS,
            recovery_graph_path=gov.RECOVERY_GRAPH,recovery_budget_path=gov.RECOVERY_BUDGET,
            mutable_surface_path=gov.MUTABLE_SURFACE,state_path=self.state,
            standing_authorization_path=self.auth,implementation_aggregate=gov.implementation_aggregate())
        self.first.write_bytes(canonical(first)+b"\n")
        state={k:v for k,v in gov.validate_state().items() if k!="sealed"}
        state["first_candidate"]={"path":str(self.first.relative_to(PROJECT)),"sha256":file_sha256(self.first)}
        self.state.write_bytes(canonical(sealed(state))+b"\n")
        auth=sealed({"action_registry":gov.binding(gov.ACTION_REGISTRY),"authorized":True,
            "candidate_factory_sha256":file_sha256(PROJECT/"oc3/oc3lib/source_metadata_recovery_factory.py"),
            "initial_state_sha256":file_sha256(self.state),"mandate":gov.binding(gov.MANDATE),
            "mission_id":gov.MISSION_ID,"mission_runner_sha256":file_sha256(PROJECT/"oc3/oc3_source_metadata_recovery_mission_runner.py"),
            "mutable_technical_surface":gov.binding(gov.MUTABLE_SURFACE),"policy_core_manifest":gov.binding(gov.POLICY_MANIFEST),
            "recovery_budget":gov.binding(gov.RECOVERY_BUDGET),"recovery_graph":gov.binding(gov.RECOVERY_GRAPH),
            "schema_version":"OC3_SOURCE_METADATA_RECOVERY_STANDING_AUTHORIZATION_001",
            "scientific_invariants":gov.binding(gov.INVARIANTS),"technical_authorities":gov.binding(gov.TECHNICAL_AUTHORITIES)})
        self.auth.write_bytes(canonical(auth)+b"\n")
        self.stack=ExitStack()
        self.stack.enter_context(patch.object(gov,"FIRST_CANDIDATE",self.first))
        self.stack.enter_context(patch.object(gov,"PERMIT_CONSUMPTION",self.root/"permit_consumption"))
        self.stack.enter_context(patch.object(gov,"CAPABILITY_CONSUMPTION",self.root/"capability_consumption"))

    def close(self):
        self.stack.close(); factory._paths=self.old_paths; self.temp.cleanup()

    @staticmethod
    def terminal(candidate,failure,**extra):
        return {"action_kind":candidate["action_kind"],"application_body_bytes_read":0,
            "failure_class":failure,"network_requests_started":0,"request_class":candidate["request_class"],
            "schema_version":"SYNTHETIC_ACTION_TERMINAL_001","source_values_accepted":0,
            "stage_id":candidate["stage_id"],**extra}


class ProductionRunnerTests(unittest.TestCase):
    def setUp(self): self.h=ProductionHarness()
    def tearDown(self): self.h.close()

    def test_actual_runner_multi_action_to_scientific_terminal(self):
        outcomes={"TECHNICAL_RESPONSE_DIAGNOSTIC":"TECHNICAL_DIAGNOSTIC_CLASSIFIED",
            "OFFICIAL_SERVICE_DOCUMENTARY_PROBE":"DOCUMENTARY_TRANSPORT_CONTRACT_RESOLVED",
            "OFFLINE_TECHNICAL_REPAIR":"TECHNICAL_PATCH_VALIDATED",
            "MATERIAL_SOURCE_METADATA_ACQUISITION":"SOURCE_METADATA_ACQUISITION_COMPLETED"}
        seen=[]
        def executor(c):
            seen.append(c["action_kind"]); extra={}
            if c["action_kind"]=="OFFLINE_TECHNICAL_REPAIR": extra["adapter_activated"]="query_manager_public_anonymous_v1"
            return self.h.terminal(c,outcomes[c["action_kind"]],**extra)
        state=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(seen,["TECHNICAL_RESPONSE_DIAGNOSTIC","OFFICIAL_SERVICE_DOCUMENTARY_PROBE",
            "OFFLINE_TECHNICAL_REPAIR","MATERIAL_SOURCE_METADATA_ACQUISITION"])
        self.assertEqual(state["state"],gov.STATE_TERMINAL)
        self.assertEqual(len(list((self.h.root/"permits").glob("*.json"))),4)
        self.assertEqual(len(list((self.h.root/"capability_consumption").glob("*.json"))),4)

    def test_actual_runner_failure_loop_stops_without_fourth_candidate(self):
        calls=[]
        def executor(c): calls.append(c["stage_id"]); return self.h.terminal(c,"DATALAB_TRANSPORT_FAILURE")
        state=run_mission(state_path=self.h.state,authorization_path=self.h.auth,
            first_candidate_path=self.h.first,ledger=self.h.ledger,executor=executor)
        self.assertEqual(state["state"],STOP_REQUIRES_HUMAN); self.assertEqual(len(calls),3)
        self.assertEqual(len(list((self.h.root/"candidates").glob("*.json"))),2)

    def test_resource_bound_finalizes_and_credentials_stop(self):
        def resource(c):
            if c["action_kind"]=="TECHNICAL_RESPONSE_DIAGNOSTIC":
                return self.h.terminal(c,"TECHNICAL_PATCH_VALIDATED",adapter_activated="query_manager_public_anonymous_v1")
            return self.h.terminal(c,"SOURCE_COUNT_RESOURCE_BOUND")
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
            if c["action_kind"] == "TECHNICAL_RESPONSE_DIAGNOSTIC":
                return self.h.terminal(c,"TECHNICAL_PATCH_VALIDATED",adapter_activated="query_manager_public_anonymous_v1")
            return self.h.terminal(c,"SOURCE_METADATA_ACQUISITION_COMPLETED")
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
        self.assertEqual(state["state"],gov.STATE_TERMINAL)

    def test_registry_and_frozen_science(self):
        values=gov.validate_static_authorities()
        self.assertEqual([x["action_kind"] for x in values["action_registry"]["actions"]],list(factory.ACTION_FAMILIES))
        self.assertEqual(file_sha256(gov.INVARIANTS),"0d2b304e815a949cf7f69d44cd43148eb663fadb68afb47a7e9f767635a329f3")
        self.assertEqual(file_sha256(gov.RECOVERY_GRAPH),"19e7d6226d6550efbd32c62a4268d682e448f15fb3c490550471286943587fb7")

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
