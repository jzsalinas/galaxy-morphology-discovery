from __future__ import annotations
import inspect
from pathlib import Path
import tempfile
import unittest

from oc3lib.core import canonical
from oc3lib import cross_id_formalism_recovery as science
from oc3lib import cross_id_formalism_recovery_governor as gov
from oc3lib.cross_id_formalism_recovery_acquisition_validation import (
    CANDIDATE, expected_command_argv, validate_candidate, validate_manifest,
    validate_historical_artifacts, validate_runtime_invocation,
)
from oc3lib.cross_id_formalism_recovery_offline_review_validation import (
    CANDIDATE as OFFLINE_CANDIDATE,
    expected_command_argv as offline_expected_command_argv,
    validate_candidate as validate_offline_candidate,
    validate_runtime_invocation as validate_offline_runtime_invocation,
)
from oc3lib.cross_observer_grouping import file_sha256, load_canonical_json, sealed, sha256_bytes


class CrossIdFormalismRecoveryTests(unittest.TestCase):
    def test_primary_resources_are_exact_and_ordered(self):
        resources=validate_manifest()["resources"]
        self.assertEqual([x["url"] for x in resources],[
            "https://arxiv.org/abs/0707.1611v3",
            "https://www.aspbooks.org/publications/394/165.pdf"])
        self.assertEqual([x["evidence_class"] for x in resources],
                         ["PRIMARY_CROSS_IDENTIFICATION_LITERATURE"]*2)

    def test_conference_proceeding_is_not_apj(self):
        proceeding=validate_manifest()["resources"][1]
        self.assertIn("ASP Conference Series",proceeding["bibliographic_identity"])
        self.assertIn("Volume 394",proceeding["bibliographic_identity"])
        self.assertIn("page 165",proceeding["bibliographic_identity"])
        self.assertNotIn("ApJ",str(proceeding))
        self.assertNotIn("679",str(proceeding))

    def test_historical_candidate_and_manifest_are_byte_exact(self):
        validate_historical_artifacts()
        self.assertEqual(file_sha256(gov.PROJECT/"oc3/INPUTS/OC3_CROSS_ID_FORMALISM_RECOVERY_RESOURCE_MANIFEST_001.json"),
                         "27da1978f4b20a18bcfbefbcc4198f84d71739c0d839e432b67209dd152fa7de")
        self.assertEqual(file_sha256(gov.PROJECT/"oc3/INPUTS/OC3_CROSS_ID_FORMALISM_RECOVERY_FIRST_CANDIDATE_001.json"),
                         "03145a5cb0fc18b75c07bcfd1493b358c038dea432f9c9aa1b1133c41e8dd3ea")

    def test_active_candidate_excludes_ads_route_and_uses_permit_002(self):
        candidate=validate_candidate()
        self.assertNotIn("adsabs.harvard.edu",str(candidate))
        self.assertTrue(candidate["autonomy_policy"]["permit_output_path"].endswith(
            "OC3_CROSS_ID_FORMALISM_RECOVERY_PRIMARY_EVIDENCE_PERMIT_002.json"))

    def test_snapshots_have_closed_transport(self):
        manifest=validate_manifest()
        self.assertEqual((manifest["network_request_cap"],manifest["application_body_byte_cap"],
                          manifest["concurrency"],manifest["retries"]),(2,4_718_592,1,0))
        for resource in manifest["resources"]:
            self.assertEqual((resource["evidence_capture_mode"],resource["redirects"],resource["retries"]),
                             ("HASHED_RESPONSE_SNAPSHOT",0,0))

    def test_only_two_claims_reopened_and_eight_preserved(self):
        candidate=validate_candidate()
        self.assertEqual(tuple(candidate["reopened_claims"]),science.REOPENED_CLAIMS)
        self.assertEqual(candidate["supported_prior_claim_count"],8)
        self.assertEqual(candidate["closed_cross_observer_grouping_terminal"]["outcome"],
                         "CROSS_OBSERVER_GROUPING_EVIDENCE_INCONCLUSIVE")

    def test_closed_inputs_are_exact(self):
        candidate=validate_candidate()["closed_cross_observer_grouping_terminal"]
        self.assertEqual(candidate["commit"],"b6667bed7c8271dd582d0b585372d010af4ccc28")
        for key in ("final_report","claim_matrix","terminal_state"):
            binding=candidate[key]
            self.assertEqual(file_sha256(gov.PROJECT/binding["path"]),binding["sha256"])

    def test_point_source_and_known_uncertainty_assumptions_retained(self):
        science.validate_claim_vocabulary()
        self.assertIn("H_POINT_SOURCE_ASSUMPTION",science.FORMALISM_CLAIMS)
        self.assertIn("E_KNOWN_POSITIONAL_UNCERTAINTIES",science.FORMALISM_CLAIMS)

    def test_epistemic_layers_are_separate(self):
        self.assertEqual(science.EPISTEMIC_LAYERS,
            ("FORMALISM_FACT","DR9_DATA_FACT","PROJECT_SUITABILITY_INFERENCE"))
        self.assertEqual(len(set(science.EPISTEMIC_LAYERS)),3)

    def test_search_bound_is_not_scientific_threshold(self):
        self.assertEqual(science.BOUND_TYPES,
            ("CANDIDATE_GENERATION_SEARCH_BOUND","SCIENTIFIC_MATCH_DECISION_THRESHOLD"))
        candidate=validate_candidate()
        self.assertFalse(candidate["search_bound_selected"])
        self.assertFalse(candidate["scientific_threshold_selected"])

    def test_no_radius_constant(self):
        source=inspect.getsource(science)+inspect.getsource(gov)
        self.assertNotIn("MATCH_RADIUS",source)
        self.assertNotIn("ARCSEC_THRESHOLD",source)

    def test_first_candidate_remains_bound_at_governed_stop(self):
        state=load_canonical_json(gov.STATE_PATH)
        self.assertEqual(state["first_candidate"],{
            "path":str(CANDIDATE.relative_to(gov.PROJECT)),"sha256":file_sha256(CANDIDATE)})
        self.assertEqual((state["state"],state["active"],state["permits_issued"]),
            (gov.STOP_REQUIRES_HUMAN,False,1))
        self.assertTrue(gov.STANDING_AUTHORIZATION_PATH.exists())
        self.assertEqual(state["stop_reason"],
            "OFFLINE_REVIEW_CONSUMED_PERMIT_IMPLEMENTATION_MARKER_MISMATCH")

    def test_exact_argv_and_preflight(self):
        candidate=validate_candidate(); command=expected_command_argv()
        validate_runtime_invocation(candidate,executable=command[0],script_path=command[1],argument_vector=command[2:])
        changed=list(command); changed[-1]+="-changed"
        with self.assertRaises(Exception):
            validate_runtime_invocation(candidate,executable=changed[0],script_path=changed[1],argument_vector=changed[2:])

    def test_stopped_mission_refuses_permit(self):
        result=gov.evaluate_candidate(CANDIDATE)
        self.assertEqual(result,{"decision":gov.MANDATE_NOT_ACTIVE,"permit_state":gov.NO_PERMIT_ISSUED})

    def test_policy_core_is_generic_and_has_replay_guards(self):
        source=inspect.getsource(gov)
        self.assertNotIn("arxiv.org",source)
        self.assertNotIn("adsabs.harvard.edu",source)
        self.assertIn("AUTONOMOUS_PERMIT_ALREADY_CONSUMED",source)
        self.assertIn("UNRESOLVED_REGISTERED_ACTION",source)
        self.assertIn("SCIENTIFIC_TERMINAL_PENDING_ACTION",source)

    def test_terminal_outcomes_are_closed(self):
        self.assertEqual(gov.TERMINAL_OUTCOMES,science.TERMINAL_OUTCOMES)
        self.assertEqual(len(gov.TERMINAL_OUTCOMES),4)

    def test_no_source_or_morphology_values_authorized(self):
        state=gov.validate_state()
        self.assertTrue(all(value==0 for value in state["firewall_counters"].values()))
        candidate=validate_candidate()
        self.assertTrue(all(value==0 for value in candidate["autonomy_policy"]["scientific_firewall"].values()))

    def test_offline_review_candidate_is_exact_and_zero_network(self):
        candidate=validate_offline_candidate()
        self.assertEqual((candidate["network_requests"],candidate["source_rows_read"]),(0,0))
        self.assertEqual(candidate["claim_order"],list(science.REOPENED_CLAIMS))
        self.assertFalse(candidate["search_bound_selected"])
        self.assertFalse(candidate["scientific_threshold_selected"])

    def test_offline_review_argv_is_exact(self):
        candidate=validate_offline_candidate(); command=offline_expected_command_argv()
        validate_offline_runtime_invocation(candidate,executable=command[0],script_path=command[1],argument_vector=command[2:])
        changed=list(command); changed[-1]+="-changed"
        with self.assertRaises(Exception):
            validate_offline_runtime_invocation(candidate,executable=changed[0],script_path=changed[1],argument_vector=changed[2:])

    def test_offline_review_uses_only_acquired_primary_evidence(self):
        candidate=validate_offline_candidate()
        paths=[item["path"] for item in candidate["input_bindings"]]
        self.assertEqual(len(paths),4)
        self.assertTrue(all("PRIMARY-EVIDENCE-ACQUISITION-002" in path for path in paths))
        self.assertTrue(all("tractor" not in path.lower() for path in paths))


class CrossIdGovernorLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=gov.PROJECT/"oc3")
        self.root=Path(self.tmp.name); self.counter=0
        self.original_consumption=gov.CONSUMPTION_ROOT
        gov.CONSUMPTION_ROOT=self.root/"ledger"/"PERMIT_CONSUMPTION"

    def tearDown(self):
        gov.CONSUMPTION_ROOT=self.original_consumption; self.tmp.cleanup()

    def write(self,name,value):
        path=self.root/name; path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(canonical(value)+b"\n"); return path

    def binding(self,path):
        return {"path":str(Path(path).resolve().relative_to(gov.PROJECT)),"sha256":file_sha256(path)}

    def candidate(self,name):
        self.counter+=1; stage=f"SYNTHETIC-{name}-{self.counter:03d}"; scope=f"SYNTHETIC_{name}_ONLY"
        argv=["synthetic","--stage",stage]
        payload={"command_argv":argv,"command_argv_sha256":sha256_bytes(canonical(argv)),
            "implementation_aggregate":"a"*64,"schema_version":"SYNTHETIC_RECOVERY_CANDIDATE_001",
            "scope":scope,"specification":self.binding(gov.SCIENTIFIC_SPEC_PATH),"stage_id":stage}
        payload_sha=sha256_bytes(canonical(payload)); impl={"algorithm":"OC3_IMPLEMENTATION_AGGREGATE_V1","sha256":"a"*64}
        receipt=self.write(f"receipt-{self.counter}.json",sealed({"action_kind":name,
            "candidate_payload_sha256":payload_sha,"frozen_specification":payload["specification"],
            "implementation_binding":impl,"network_requests":0,
            "schema_version":"OC3_CROSS_ID_FORMALISM_RECOVERY_ACTION_VALIDATION_RECEIPT_001",
            "scope":scope,"stage_id":stage,"validated":True,
            "validator":self.binding(gov.PROJECT/"oc3/oc3lib/cross_id_formalism_recovery.py")}))
        contract={"action_kind":name,"action_validation_receipt":self.binding(receipt),
            "application_body_reservation":0,"authority_classes_used":[gov.AUTHORITY_CLASSES[0]],
            "candidate_hash_mode":"CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED",
            "candidate_payload_sha256":payload_sha,"command_argv_sha256":payload["command_argv_sha256"],
            "concurrency":1,"frozen_specification":payload["specification"],
            "full_candidate_identity":"FULL_FILE_SHA256_BOUND_BY_STATE_AUTHORIZATION_PERMIT_AND_LEDGER",
            "git_assertions":{"branch":gov.AUTONOMY_BRANCH,"force_push":False,"merge_main":False},
            "implementation_binding":impl,"network_request_reservation":0,
            "permit_output_path":str((self.root/f"permit-{self.counter}.json").relative_to(gov.PROJECT)),
            "requested_prohibited_scopes":[],"resource_manifest":None,
            "resume_policy":{"allowed":False,"prospectively_frozen":True},
            "retry_policy":{"exact_same_resource":True,"prospectively_frozen":True},"retry_reservation":0,
            "schema_version":"OC3_CROSS_ID_FORMALISM_RECOVERY_ACTION_CONTRACT_001",
            "scientific_firewall":{key:0 for key in gov.FIREWALL_KEYS},"scope":scope,"stage_id":stage,
            "standing_mandate_sha256":file_sha256(gov.MANDATE_PATH)}
        return self.write(f"candidate-{self.counter}.json",sealed({**payload,"autonomy_policy":contract}))

    def activate(self,first):
        production=load_canonical_json(gov.STATE_PATH); body={k:v for k,v in production.items() if k!="sealed"}
        body.update({"active":False,"body_budget_remaining":8_388_608,
            "first_candidate":self.binding(first),"current_stage":"FIRST_ACTION_PREPARED",
            "last_completed_stage":None,"last_terminal":None,"permits_issued":0,
            "registered_pending_action":None,"requests_remaining":4,"scientific_outcome":None,
            "sequence":0,"standing_authorization":None,"standing_authorization_initial_state_sha256":None,
            "state":gov.STATE_WAITING,"stop_reason":None})
        state=self.write("state.json",sealed(body))
        auth=self.write("authorization.json",sealed({"authorization_state":"STANDING_HUMAN_AUTONOMY_AUTHORIZATION",
            "authorized":True,"authorized_at_utc":"2026-09-24T00:00:00Z","authorized_by":"Synthetic Reviewer",
            "continuation_policy":"CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN",
            "first_candidate_path":str(first.relative_to(gov.PROJECT)),"first_candidate_sha256":file_sha256(first),
            "initial_state_path":str(state.relative_to(gov.PROJECT)),"initial_state_sha256":file_sha256(state),
            "mandate_path":str(gov.MANDATE_PATH.relative_to(gov.PROJECT)),"mandate_sha256":file_sha256(gov.MANDATE_PATH),
            "mission_id":gov.MISSION_ID,"mission_scope":gov.MISSION_SCOPE,
            "policy_core_manifest_path":str(gov.POLICY_CORE_MANIFEST_PATH.relative_to(gov.PROJECT)),
            "policy_core_manifest_sha256":file_sha256(gov.POLICY_CORE_MANIFEST_PATH),
            "schema_version":"OC3_CROSS_ID_FORMALISM_RECOVERY_STANDING_AUTHORIZATION_001"}))
        ledger=self.root/"ledger"
        gov.activate_standing_autonomy(state_path=state,standing_authorization_path=auth,
            ledger_directory=ledger,activated_at_utc="2026-09-24T00:01:00Z",current_branch=gov.AUTONOMY_BRANCH)
        return state,auth,ledger

    def run_action(self,candidate,state,auth,ledger,index):
        gov.register_pending_action(state_path=state,candidate_path=candidate,standing_authorization_path=auth,
            ledger_directory=ledger,registered_at_utc=f"2026-09-24T00:{index}2:00Z",current_branch=gov.AUTONOMY_BRANCH)
        permit=gov.PROJECT/gov.validate_candidate(candidate)[1]["permit_output_path"]
        gov.issue_permit(candidate_path=candidate,state_path=state,standing_authorization_path=auth,
            output_path=permit,ledger_directory=ledger,issued_at_utc=f"2026-09-24T00:{index}3:00Z")
        gov.consume_permit(permit,candidate_path=candidate,state_path=state,standing_authorization_path=auth,
            consumed_at_utc=f"2026-09-24T00:{index}4:00Z")
        parsed=gov.validate_candidate(candidate)[0]
        terminal=self.write(f"terminal-{index}.json",sealed({"application_body_bytes_read":0,
            "counters":{"network_requests_started":0,"retry_requests":0},"scope":parsed["scope"],
            "stage_id":parsed["stage_id"],"state":"SYNTHETIC_COMPLETE"}))
        gov.transition_completed_action(state_path=state,candidate_path=candidate,permit_path=permit,
            standing_authorization_path=auth,terminal_path=terminal,terminal_sha256=file_sha256(terminal),
            request_delta=0,body_delta=0,retry_delta=0,ledger_directory=ledger,
            transitioned_at_utc=f"2026-09-24T00:{index}5:00Z",reason="SYNTHETIC_COMPLETE")
        return permit

    def test_single_use_multi_action_and_terminal_closure(self):
        first=self.candidate("FIRST"); state,auth,ledger=self.activate(first)
        permit=self.run_action(first,state,auth,ledger,1)
        with self.assertRaises(gov.GovernorError) as caught:
            gov.consume_permit(permit,candidate_path=first,state_path=state,standing_authorization_path=auth,
                consumed_at_utc="2026-09-24T00:16:00Z")
        self.assertEqual(caught.exception.code,"AUTONOMOUS_PERMIT_ALREADY_CONSUMED")
        second=self.candidate("SECOND"); self.run_action(second,state,auth,ledger,2)
        report=self.root/"final.md"; report.write_text("synthetic final\n")
        matrix=self.write("matrix.json",{"claims":[]})
        final=gov.finalize_scientific_terminal(state_path=state,standing_authorization_path=auth,
            outcome="CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE",final_report_path=report,
            claim_matrix_path=matrix,ledger_directory=ledger,finalized_at_utc="2026-09-24T00:30:00Z",
            current_branch=gov.AUTONOMY_BRANCH)
        self.assertEqual((final["state"],final["active"],final["permits_issued"]),
                         (gov.STATE_TERMINAL,False,2))
