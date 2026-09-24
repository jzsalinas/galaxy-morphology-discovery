import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import oc3lib.autonomy_governor as ag
from oc3lib.core import canonical
from oc3lib.galaxy_eligibility_photsys_authority_probe import (
    file_sha256, load_canonical_json, sealed, sha256_bytes, write_json_immutable,
)

class AutonomyLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="autonomy_hardening_SYNTHETIC_ONLY_",dir=ag.PROJECT/"oc3/tests")
        self.root=Path(self.temp.name); self.count=0
    def tearDown(self): self.temp.cleanup()
    def write(self,name,value):
        self.count+=1; path=self.root/f"{self.count:03d}_{name}"; write_json_immutable(path,value); return path
    def code(self,expected,call):
        with self.assertRaises(ag.AutonomyError) as caught: call()
        self.assertEqual(caught.exception.code,expected)
    def candidate(self,name,authority,*,requests=0,body=0,mutate=None):
        stage=f"SYNTHETIC-{name}"; scope=f"SYNTHETIC_{name}_ONLY"
        validator=self.root/f"validator_{name}.py"; validator.write_text("# synthetic offline validator\n")
        argv=["synthetic-offline-action",name]
        payload={"command_argv":argv,"command_argv_sha256":sha256_bytes(canonical(argv)),
            "implementation_aggregate":"a"*64,"schema_version":f"SYNTHETIC_{name}_CANDIDATE_001",
            "scope":scope,"specification":{"path":str(ag.SCIENTIFIC_SPEC_PATH.relative_to(ag.PROJECT)),
            "sha256":file_sha256(ag.SCIENTIFIC_SPEC_PATH)},"stage_id":stage}
        payload_sha=sha256_bytes(canonical(payload))
        receipt=self.write(f"receipt_{name}.json",sealed({"action_kind":name,
            "candidate_payload_sha256":payload_sha,"frozen_specification":payload["specification"],
            "network_requests":0,"schema_version":"OC3_ACTION_VALIDATION_RECEIPT_001","scope":scope,
            "stage_id":stage,"validated":True,"validator":{"path":str(validator.relative_to(ag.PROJECT)),
            "sha256":file_sha256(validator)}}))
        manifest_binding=None
        if requests:
            manifest=self.write(f"manifest_{name}.json",sealed({"broad_crawling":False,"mirror_substitution":False,
                "resources":[{"application_body_byte_cap":body,"evidence_class":authority,
                "expected_representation":"SYNTHETIC_HEADERS_ONLY","host":"example.invalid","id":name,
                "immutable_revision_required":True,"method":"GET","purpose":"synthetic policy test",
                "redirects":0,"retries":0,"url":f"https://example.invalid/{name}"}],
                "schema_version":"SYNTHETIC_LITERAL_RESOURCE_MANIFEST_001"}))
            manifest_binding={"path":str(manifest.relative_to(ag.PROJECT)),"sha256":file_sha256(manifest)}
        contract={"action_kind":name,"action_validation_receipt":{"path":str(receipt.relative_to(ag.PROJECT)),
            "sha256":file_sha256(receipt)},"application_body_reservation":body,
            "authority_classes_used":[authority],"candidate_hash_mode":"CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED",
            "candidate_sha256":payload_sha,"command_argv_sha256":payload["command_argv_sha256"],"concurrency":1,
            "frozen_specification":payload["specification"],"git_assertions":{"branch":ag.AUTONOMY_BRANCH,
            "force_push":False,"merge_main":False},"implementation_binding":{"algorithm":"OC3_IMPLEMENTATION_AGGREGATE_V1",
            "sha256":"a"*64},"network_request_reservation":requests,
            "permit_output_path":str((self.root/f"permit_{name}.json").relative_to(ag.PROJECT)),
            "prohibited_scope_assertions":{key:True for key in ag.PROHIBITED_SCOPE_KEYS},
            "resource_manifest":manifest_binding,"resume_rule":{"allowed":False,"prospectively_frozen":True},
            "retry_reservation":0,"retry_rule":{"exact_same_resource":True,"prospectively_frozen":True},
            "schema_version":"OC3_AUTONOMOUS_ACTION_CONTRACT_001",
            "scientific_firewall":{key:0 for key in ag.FIREWALL_KEYS},"scope":scope,"stage_id":stage,
            "standing_mandate_sha256":file_sha256(ag.MANDATE_PATH)}
        if mutate: mutate(contract)
        value=dict(payload); value["autonomy_policy"]=contract
        return self.write(f"candidate_{name}.json",sealed(value))
    def waiting(self,candidate):
        value=load_canonical_json(ag.STATE_PATH); body={k:v for k,v in value.items() if k!="sealed"}
        parsed,contract=ag.validate_autonomous_action_candidate(candidate)
        body.update({"active":False,"current_stage":ag.STATE_WAITING,"registered_pending_action":
            ag._registered_binding(candidate,parsed,contract,first=True),"standing_authorization":None,
            "standing_authorization_initial_state_sha256":None,"state":ag.STATE_WAITING,
            "requests_remaining":18,"body_budget_remaining":17544938,
            "scientific_outcome":None,"stop_reason":None})
        return self.write("state.json",sealed(body))
    def authorization(self,state,**updates):
        body={"authorization_state":"STANDING_HUMAN_AUTONOMY_AUTHORIZATION","authorized":True,
            "authorized_at_utc":"2026-09-24T00:00:00Z","authorized_by":"Synthetic Reviewer",
            "continuation_policy":"CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN",
            "initial_state_path":str(state.relative_to(ag.PROJECT)),"initial_state_sha256":file_sha256(state),
            "mandate_path":str(ag.MANDATE_PATH.relative_to(ag.PROJECT)),"mandate_sha256":file_sha256(ag.MANDATE_PATH),
            "mission_id":ag.MISSION_ID,"mission_scope":ag.MISSION_SCOPE,
            "policy_core_manifest_path":str(ag.POLICY_CORE_MANIFEST_PATH.relative_to(ag.PROJECT)),
            "policy_core_manifest_sha256":file_sha256(ag.POLICY_CORE_MANIFEST_PATH),
            "schema_version":"OC3_AUTONOMY_STANDING_AUTHORIZATION_001"}
        body.update(updates); return self.write("authorization.json",sealed(body))
    def active(self,candidate):
        state=self.waiting(candidate); auth=self.authorization(state); self.count+=1; ledger=self.root/f"ledger_{self.count:03d}"
        ag.activate_standing_autonomy(state_path=state,standing_authorization_path=auth,
            ledger_directory=ledger,activated_at_utc="2026-09-24T00:01:00Z",current_branch=ag.AUTONOMY_BRANCH)
        return state,auth,ledger

    def test_01_static_policy_core_and_closed_production_state(self):
        self.assertEqual(ag.validate_policy_core_manifest()["active_mutation_result"],ag.STOP_REQUIRES_HUMAN)
        state=ag.validate_state()
        self.assertEqual(state["state"],ag.STATE_SCIENTIFIC_TERMINAL)
        self.assertEqual(state["scientific_outcome"],"PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE")
    def test_02_closed_production_mission_refuses(self):
        result=ag.evaluate_policy(candidate_path=ag.PROJECT/"oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_003.json")
        self.assertEqual(result,{"decision":"NO_REGISTERED_PENDING_ACTION","permit_state":ag.NO_PERMIT_ISSUED})
    def test_03_activation_positive_zero_budget(self):
        candidate=self.candidate("DOC",ag.ALLOWED_AUTHORITY_CLASSES[0]); state=self.waiting(candidate); auth=self.authorization(state)
        before=load_canonical_json(state); updated=ag.activate_standing_autonomy(state_path=state,
            standing_authorization_path=auth,ledger_directory=self.root/"ledger",activated_at_utc="2026-09-24T00:01:00Z",
            current_branch=ag.AUTONOMY_BRANCH)
        self.assertTrue(updated["active"]); self.assertEqual(updated["sequence"],before["sequence"]+1)
        self.assertEqual(updated["requests_remaining"],before["requests_remaining"])
        record=load_canonical_json(next((self.root/"ledger").glob("*_ACTIVATION.json")))
        self.assertEqual(record["request_budget_delta"],0)
    def test_04_activation_absent_and_wrong_bindings_refused(self):
        candidate=self.candidate("DOC",ag.ALLOWED_AUTHORITY_CLASSES[0]); state=self.waiting(candidate)
        self.code("STANDING_AUTONOMY_AUTHORIZATION_INVALID",lambda:ag.activate_standing_autonomy(
            state_path=state,standing_authorization_path=self.root/"absent.json",ledger_directory=self.root/"l0",
            activated_at_utc="2026-09-24T00:01:00Z",current_branch=ag.AUTONOMY_BRANCH))
        for field,value in (("mandate_sha256","0"*64),("policy_core_manifest_sha256","0"*64),
                            ("initial_state_sha256","0"*64),("mission_id","WRONG"),("mission_scope","WRONG")):
            with self.subTest(field=field):
                state=self.waiting(candidate); auth=self.authorization(state,**{field:value})
                self.code("STANDING_AUTONOMY_AUTHORIZATION_INVALID",lambda s=state,a=auth:ag.activate_standing_autonomy(
                    state_path=s,standing_authorization_path=a,ledger_directory=self.root/("l"+field),
                    activated_at_utc="2026-09-24T00:01:00Z",current_branch=ag.AUTONOMY_BRANCH))
    def test_05_activation_branch_registration_and_second_attempt_refused(self):
        candidate=self.candidate("DOC",ag.ALLOWED_AUTHORITY_CLASSES[0]); state=self.waiting(candidate); auth=self.authorization(state)
        self.code("UNAUTHORIZED_BRANCH",lambda:ag.activate_standing_autonomy(state_path=state,
            standing_authorization_path=auth,ledger_directory=self.root/"branch",activated_at_utc="2026-09-24T00:01:00Z",current_branch="main"))
        state=self.waiting(candidate); value=load_canonical_json(state); body={k:v for k,v in value.items() if k!="sealed"}; body["registered_pending_action"]["candidate_sha256"]="0"*64; state.write_bytes(canonical(sealed(body))+b"\n"); auth=self.authorization(state)
        self.code("AUTONOMY_FIRST_ACTION_BINDING_INVALID",lambda:ag.activate_standing_autonomy(state_path=state,
            standing_authorization_path=auth,ledger_directory=self.root/"badreg",activated_at_utc="2026-09-24T00:01:00Z",current_branch=ag.AUTONOMY_BRANCH))
        state,auth,ledger=self.active(candidate)
        self.code("AUTONOMY_ACTIVATION_STATE_INVALID",lambda:ag.activate_standing_autonomy(state_path=state,
            standing_authorization_path=auth,ledger_directory=ledger,activated_at_utc="2026-09-24T00:02:00Z",current_branch=ag.AUTONOMY_BRANCH))
    def test_06_two_generic_action_classes_eligible(self):
        for name,authority in (("OFFICIAL_DOC",ag.ALLOWED_AUTHORITY_CLASSES[0]),("EXACT_SOURCE",ag.ALLOWED_AUTHORITY_CLASSES[2])):
            with self.subTest(name=name):
                candidate=self.candidate(name,authority,requests=1,body=16); state,auth,_=self.active(candidate)
                self.assertEqual(ag.evaluate_policy(candidate_path=candidate,state_path=state,
                    standing_authorization_path=auth)["decision"],ag.ELIGIBLE)
    def test_07_generic_refusals(self):
        cases=[("AUTH",lambda c:c.update(authority_classes_used=["UNAUTHORIZED"])),
               ("ASTRO",lambda c:c["scientific_firewall"].update(astronomical_data_GETs=1)),
               ("PANEL",lambda c:c["prohibited_scope_assertions"].update(panel_v2=False)),
               ("P1",lambda c:c["prohibited_scope_assertions"].update(p1=False)),
               ("RESOLVER",lambda c:c["prohibited_scope_assertions"].update(resolver=False)),
               ("MORPH",lambda c:c["prohibited_scope_assertions"].update(morphological_discovery=False)),
               ("CONCURRENCY",lambda c:c.update(concurrency=2)),
               ("RETRY",lambda c:(c.update(retry_reservation=1),c["retry_rule"].update(prospectively_frozen=False))),
               ("BRANCH",lambda c:c["git_assertions"].update(branch="main")),
               ("FORCE",lambda c:c["git_assertions"].update(force_push=True)),
               ("MERGE",lambda c:c["git_assertions"].update(merge_main=True)),
               ("NO_MANIFEST",lambda c:c.update(resource_manifest=None))]
        for name,mutate in cases:
            with self.subTest(name=name):
                candidate=self.candidate(name,ag.ALLOWED_AUTHORITY_CLASSES[0],requests=1,body=1,mutate=mutate)
                try:
                    ag.validate_autonomous_action_candidate(candidate)
                except ag.AutonomyError as exc:
                    self.assertNotEqual(exc.code,ag.ELIGIBLE)
                    continue
                state=self.waiting(candidate); auth=self.authorization(state)
                ag.activate_standing_autonomy(state_path=state,standing_authorization_path=auth,
                    ledger_directory=self.root/("ledger"+name),activated_at_utc="2026-09-24T00:01:00Z",current_branch=ag.AUTONOMY_BRANCH)
                try: decision=ag.evaluate_policy(candidate_path=candidate,state_path=state,standing_authorization_path=auth)["decision"]
                except ag.AutonomyError as exc: decision=exc.code
                self.assertNotEqual(decision,ag.ELIGIBLE)
    def test_08_budget_overflow_refused(self):
        candidate=self.candidate("OVER",ag.ALLOWED_AUTHORITY_CLASSES[0],requests=19,body=17544939)
        state,auth,_=self.active(candidate)
        self.assertIn(ag.evaluate_policy(candidate_path=candidate,state_path=state,standing_authorization_path=auth)["decision"],
                      ("REQUEST_BUDGET_OVERFLOW","BODY_BUDGET_OVERFLOW"))
    def test_09_policy_core_mutation_fails_closed(self):
        candidate=self.candidate("DOC",ag.ALLOWED_AUTHORITY_CLASSES[0]); state,auth,_=self.active(candidate)
        original=ag.file_sha256
        def altered(path):
            if Path(path).resolve()==(ag.PROJECT/"oc3/oc3lib/autonomy_governor.py").resolve(): return "0"*64
            return original(path)
        with patch.object(ag,"file_sha256",side_effect=altered):
            self.code("POLICY_CORE_MISMATCH",lambda:ag.build_permit(candidate_path=candidate,state_path=state,
                standing_authorization_path=auth,issued_at_utc="2026-09-24T00:02:00Z"))

    def test_10_issue_consume_single_use_and_transition_guards(self):
        candidate=self.candidate("DOC",ag.ALLOWED_AUTHORITY_CLASSES[0],requests=1,body=0); state,auth,ledger=self.active(candidate)
        permit_path=self.root/"permit_DOC.json"
        permit=ag.issue_permit(candidate_path=candidate,state_path=state,standing_authorization_path=auth,
            output_path=permit_path,ledger_directory=ledger,issued_at_utc="2026-09-24T00:02:00Z")
        self.assertEqual(permit["network_budget_reserved"],1)
        consumed=self.root/"consumed"
        ag.consume_permit(permit_path,candidate_path=candidate,state_path=state,standing_authorization_path=auth,
            consumption_directory=consumed,consumed_at_utc="2026-09-24T00:03:00Z")
        self.code("AUTONOMOUS_PERMIT_ALREADY_CONSUMED",lambda:ag.consume_permit(permit_path,
            candidate_path=candidate,state_path=state,standing_authorization_path=auth,
            consumption_directory=consumed,consumed_at_utc="2026-09-24T00:04:00Z"))
        terminal=self.write("terminal.json",sealed({"application_body_bytes_read":0,
            "counters":{"network_requests_started":1,"retry_requests":0},"scope":"SYNTHETIC_DOC_ONLY",
            "stage_id":"SYNTHETIC-DOC","state":"SYNTHETIC_COMPLETE"}))
        self.code("PERMIT_RESERVATION_EXCEEDED_REQUIRES_STOP",lambda:ag.transition_completed_action(
            state_path=state,candidate_path=candidate,permit_path=permit_path,standing_authorization_path=auth,
            consumption_directory=consumed,terminal_path=terminal,terminal_sha256=file_sha256(terminal),
            request_delta=2,body_delta=0,retry_delta=0,
            ledger_directory=ledger,transitioned_at_utc="2026-09-24T00:05:00Z",reason="SYNTHETIC"))
    def test_11_transition_requires_consumption_and_real_terminal(self):
        candidate=self.candidate("DOC",ag.ALLOWED_AUTHORITY_CLASSES[0]); state,auth,ledger=self.active(candidate)
        permit_path=self.root/"permit_DOC.json"; ag.issue_permit(candidate_path=candidate,state_path=state,
            standing_authorization_path=auth,output_path=permit_path,ledger_directory=ledger,
            issued_at_utc="2026-09-24T00:02:00Z")
        terminal=self.write("terminal.json",sealed({"application_body_bytes_read":0,
            "counters":{"network_requests_started":0,"retry_requests":0},"scope":"SYNTHETIC_DOC_ONLY",
            "stage_id":"SYNTHETIC-DOC","state":"COMPLETE"}))
        self.code("AUTONOMOUS_PERMIT_CONSUMPTION_MISSING",lambda:ag.transition_completed_action(
            state_path=state,candidate_path=candidate,permit_path=permit_path,standing_authorization_path=auth,
            consumption_directory=self.root/"consumed",terminal_path=terminal,terminal_sha256=file_sha256(terminal),
            request_delta=0,body_delta=0,
            retry_delta=0,ledger_directory=ledger,transitioned_at_utc="2026-09-24T00:03:00Z",reason="SYNTHETIC"))
        ag.consume_permit(permit_path,candidate_path=candidate,state_path=state,standing_authorization_path=auth,
            consumption_directory=self.root/"consumed",consumed_at_utc="2026-09-24T00:03:00Z")
        self.code("AUTONOMY_TERMINAL_ARTIFACT_MISSING",lambda:ag.transition_completed_action(
            state_path=state,candidate_path=candidate,permit_path=permit_path,standing_authorization_path=auth,
            consumption_directory=self.root/"consumed",terminal_path=self.root/"absent.json",terminal_sha256="0"*64,request_delta=0,
            body_delta=0,retry_delta=0,ledger_directory=ledger,transitioned_at_utc="2026-09-24T00:04:00Z",reason="SYNTHETIC"))
    def test_12_full_two_action_replay(self):
        first=self.candidate("FIRST",ag.ALLOWED_AUTHORITY_CLASSES[0],requests=1,body=0); state,auth,ledger=self.active(first)
        permit1=self.root/"permit_FIRST.json"; ag.issue_permit(candidate_path=first,state_path=state,
            standing_authorization_path=auth,output_path=permit1,ledger_directory=ledger,issued_at_utc="2026-09-24T00:02:00Z")
        consumed=ledger/"PERMIT_CONSUMPTION"; ag.consume_permit(permit1,candidate_path=first,state_path=state,
            standing_authorization_path=auth,consumption_directory=consumed,consumed_at_utc="2026-09-24T00:03:00Z")
        terminal=self.write("terminal_first.json",sealed({"application_body_bytes_read":0,
            "counters":{"network_requests_started":1,"retry_requests":0},"scope":"SYNTHETIC_FIRST_ONLY",
            "stage_id":"SYNTHETIC-FIRST","state":"COMPLETE"}))
        updated=ag.transition_completed_action(state_path=state,candidate_path=first,permit_path=permit1,
            standing_authorization_path=auth,consumption_directory=consumed,terminal_path=terminal,
            terminal_sha256=file_sha256(terminal),request_delta=1,body_delta=0,retry_delta=0,ledger_directory=ledger,
            transitioned_at_utc="2026-09-24T00:04:00Z",reason="SYNTHETIC_FIRST_COMPLETE")
        self.assertIsNone(updated["registered_pending_action"]); self.assertEqual(updated["requests_remaining"],17)
        self.code("AUTONOMOUS_PERMIT_ALREADY_CONSUMED",lambda:ag.validate_permit(permit1,
            candidate_path=first,state_path=state,standing_authorization_path=auth,
            consumption_directory=consumed))
        second=self.candidate("SECOND",ag.ALLOWED_AUTHORITY_CLASSES[2])
        registered=ag.register_pending_action(state_path=state,candidate_path=second,standing_authorization_path=auth,
            ledger_directory=ledger,registered_at_utc="2026-09-24T00:05:00Z",current_branch=ag.AUTONOMY_BRANCH)
        self.assertEqual(registered["registered_pending_action"]["action_kind"],"SECOND")
        permit2=self.root/"permit_SECOND.json"; ag.issue_permit(candidate_path=second,state_path=state,
            standing_authorization_path=auth,output_path=permit2,ledger_directory=ledger,
            issued_at_utc="2026-09-24T00:06:00Z")
        self.assertTrue(permit2.is_file())
    def test_13_stop_transition(self):
        candidate=self.candidate("DOC",ag.ALLOWED_AUTHORITY_CLASSES[0]); state,auth,ledger=self.active(candidate)
        report=self.root/"STOP.md"; report.write_text("# STOP\nExact blocker and minimum human amendment.\n")
        updated=ag.enter_stop_requires_human(state_path=state,standing_authorization_path=auth,
            stop_report_path=report,blocker_code="SYNTHETIC_BLOCKER",ledger_directory=ledger,
            stopped_at_utc="2026-09-24T00:02:00Z",current_branch=ag.AUTONOMY_BRANCH)
        self.assertFalse(updated["active"]); self.assertEqual(updated["state"],ag.STOP_REQUIRES_HUMAN)
        self.assertEqual(updated["requests_remaining"],18)
    def test_14_scientific_terminal_transition(self):
        candidate=self.candidate("DOC",ag.ALLOWED_AUTHORITY_CLASSES[0]); state,auth,ledger=self.active(candidate)
        value=load_canonical_json(state); body={k:v for k,v in value.items() if k!="sealed"}; body["registered_pending_action"]=None; state.write_bytes(canonical(sealed(body))+b"\n")
        report=self.root/"FINAL.md"; report.write_text("# Final semantic report\n")
        matrix=self.root/"CLAIMS.json"; matrix.write_text("{}\n")
        outcome=ag.TERMINAL_OUTCOMES[2]
        updated=ag.finalize_scientific_terminal(state_path=state,standing_authorization_path=auth,outcome=outcome,
            final_report_path=report,claim_matrix_path=matrix,ledger_directory=ledger,
            finalized_at_utc="2026-09-24T00:02:00Z",current_branch=ag.AUTONOMY_BRANCH)
        self.assertEqual(updated["scientific_outcome"],outcome); self.assertFalse(updated["active"])
    def test_15_git_firewall(self):
        safe=self.root/"report.md"; safe.write_text("compact\n")
        self.assertEqual(ag.audit_compact_paths([safe])["state"],"GIT_STAGED_SIZE_FIREWALL_PASS")
        bad=self.root/"evidence.fits"; bad.write_bytes(b"SIMPLE")
        self.code("GIT_SCIENTIFIC_OR_ARCHIVE_BODY_FORBIDDEN",lambda:ag.audit_compact_paths([bad]))

if __name__=="__main__": unittest.main()
