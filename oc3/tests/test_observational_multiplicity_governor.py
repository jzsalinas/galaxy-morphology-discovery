from __future__ import annotations

import inspect
import io
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from oc3lib.core import canonical
from oc3lib.observational_multiplicity import file_sha256, load_canonical_json, sealed, sha256_bytes
from oc3lib import observational_multiplicity_governor as gov
import oc3_observational_multiplicity as executor
from oc3lib.observational_multiplicity_executor_validation import (
    CANDIDATE_002, CANDIDATE_003, expected_command_argv, validate_candidate_003,
)
from oc3lib.observational_multiplicity_executor_validation_004 import (
    CANDIDATE_004, expected_command_argv as expected_command_argv_004,
    validate_candidate_004,
)


class ObservationalMultiplicityGovernorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=gov.PROJECT / "oc3")
        self.root = Path(self.tmp.name)
        self.original_consumption = gov.CONSUMPTION_ROOT
        gov.CONSUMPTION_ROOT = self.root / "LEDGER" / "PERMIT_CONSUMPTION"
        self.counter = 0

    def tearDown(self):
        gov.CONSUMPTION_ROOT = self.original_consumption
        self.tmp.cleanup()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(value) + b"\n")
        return path

    def binding(self, path):
        return {"path": str(Path(path).resolve().relative_to(gov.PROJECT)), "sha256": file_sha256(path)}

    def code(self, expected, fn):
        with self.assertRaises(gov.GovernorError) as caught:
            fn()
        self.assertEqual(caught.exception.code, expected)

    def candidate(self, name, authority, *, requests=0, body=0, retries=0, mutate=None,
                  executor_command=False):
        self.counter += 1
        stage = f"SYNTHETIC-{name}-{self.counter:03d}"
        scope = f"SYNTHETIC_{name}_ONLY"
        if executor_command:
            argv = [str(gov.PROJECT / "oc3/.venv/bin/python"),
                    str(gov.PROJECT / "oc3/oc3_observational_multiplicity.py"),
                    "--audit-global-view-relation",
                    "--candidate", str(self.root / f"candidate_{self.counter}.json"),
                    "--permit", str(self.root / f"permit_{self.counter}.json"),
                    "--standing-authorization", str(self.root / f"authorization_{self.counter}.json"),
                    "--autonomy-state", str(self.root / f"state_{self.counter}.json"),
                    "--output-directory", str(self.root / "OUTPUT")]
        else:
            argv = ["synthetic", "--stage", stage]
        payload = {
            "command_argv": argv,
            "command_argv_sha256": sha256_bytes(canonical(argv)),
            "implementation_aggregate": "a" * 64,
            "schema_version": "SYNTHETIC_OBSERVATIONAL_MULTIPLICITY_CANDIDATE_001",
            "scope": scope,
            "specification": self.binding(gov.SCIENTIFIC_SPEC_PATH),
            "stage_id": stage,
        }
        payload_sha = sha256_bytes(canonical(payload))
        implementation = {"algorithm": "OC3_IMPLEMENTATION_AGGREGATE_V1", "sha256": "a" * 64}
        receipt = self.write(f"receipt_{self.counter}.json", sealed({
            "action_kind": name,
            "candidate_payload_sha256": payload_sha,
            "frozen_specification": payload["specification"],
            "implementation_binding": implementation,
            "network_requests": 0,
            "schema_version": "OC3_OBSERVATIONAL_MULTIPLICITY_ACTION_VALIDATION_RECEIPT_002",
            "scope": scope,
            "stage_id": stage,
            "validated": True,
            "validator": self.binding(gov.PROJECT / "oc3/oc3lib/observational_multiplicity.py"),
        }))
        manifest_binding = None
        if requests:
            manifest = self.write(f"manifest_{self.counter}.json", sealed({
                "broad_crawling": False,
                "mirror_substitution": False,
                "resources": [{
                    "application_body_byte_cap": body,
                    "evidence_class": authority,
                    "expected_representation": "text/plain",
                    "host": "example.invalid",
                    "id": f"RESOURCE-{self.counter}",
                    "immutable_revision_required": True,
                    "method": "GET",
                    "purpose": "synthetic policy replay",
                    "redirects": 0,
                    "retries": retries,
                    "url": f"https://example.invalid/{self.counter}",
                }],
                "schema_version": "SYNTHETIC_LITERAL_RESOURCE_MANIFEST_001",
            }))
            manifest_binding = self.binding(manifest)
        contract = {
            "action_kind": name,
            "action_validation_receipt": self.binding(receipt),
            "application_body_reservation": body,
            "authority_classes_used": [authority],
            "candidate_hash_mode": "CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED",
            "candidate_payload_sha256": payload_sha,
            "command_argv_sha256": payload["command_argv_sha256"],
            "concurrency": 1,
            "frozen_specification": payload["specification"],
            "full_candidate_identity": "FULL_FILE_SHA256_BOUND_BY_STATE_AUTHORIZATION_PERMIT_AND_LEDGER",
            "git_assertions": {"branch": gov.AUTONOMY_BRANCH, "force_push": False, "merge_main": False},
            "implementation_binding": implementation,
            "network_request_reservation": requests,
            "permit_output_path": str((self.root / f"permit_{self.counter}.json").relative_to(gov.PROJECT)),
            "requested_prohibited_scopes": [],
            "resource_manifest": manifest_binding,
            "resume_policy": {"allowed": False, "prospectively_frozen": True},
            "retry_reservation": retries,
            "retry_policy": {"exact_same_resource": True, "prospectively_frozen": True},
            "schema_version": "OC3_OBSERVATIONAL_MULTIPLICITY_ACTION_CONTRACT_002",
            "scientific_firewall": {key: 0 for key in gov.FIREWALL_KEYS},
            "scope": scope,
            "stage_id": stage,
            "standing_mandate_sha256": file_sha256(gov.MANDATE_PATH),
        }
        if mutate:
            mutate(contract)
        value = dict(payload)
        value["autonomy_policy"] = contract
        return self.write(f"candidate_{self.counter}.json", sealed(value))

    def waiting(self, first):
        value = load_canonical_json(gov.STATE_PATH)
        body = {k: v for k, v in value.items() if k != "sealed"}
        body.update({
            "active": False,
            "body_budget_remaining": 16777216,
            "current_stage": "FIRST_ACTION_PREPARED",
            "first_candidate": self.binding(first),
            "last_completed_stage": None,
            "last_terminal": None,
            "permits_issued": 0,
            "registered_pending_action": None,
            "requests_remaining": 12,
            "scientific_outcome": None,
            "sequence": 0,
            "standing_authorization": None,
            "standing_authorization_initial_state_sha256": None,
            "state": gov.STATE_WAITING,
            "stop_reason": None,
        })
        return self.write(f"state_{self.counter}.json", sealed(body))

    def authorization(self, state, first, **updates):
        body = {
            "authorization_state": "STANDING_HUMAN_AUTONOMY_AUTHORIZATION",
            "authorized": True,
            "authorized_at_utc": "2026-09-24T00:00:00Z",
            "authorized_by": "Synthetic Reviewer",
            "continuation_policy": "CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN",
            "first_candidate_path": str(first.relative_to(gov.PROJECT)),
            "first_candidate_sha256": file_sha256(first),
            "initial_state_path": str(state.relative_to(gov.PROJECT)),
            "initial_state_sha256": file_sha256(state),
            "mandate_path": str(gov.MANDATE_PATH.relative_to(gov.PROJECT)),
            "mandate_sha256": file_sha256(gov.MANDATE_PATH),
            "mission_id": gov.MISSION_ID,
            "mission_scope": gov.MISSION_SCOPE,
            "policy_core_manifest_path": str(gov.POLICY_CORE_MANIFEST_PATH.relative_to(gov.PROJECT)),
            "policy_core_manifest_sha256": file_sha256(gov.POLICY_CORE_MANIFEST_PATH),
            "schema_version": "OC3_OBSERVATIONAL_MULTIPLICITY_STANDING_AUTHORIZATION_002",
        }
        body.update(updates)
        return self.write(f"authorization_{self.counter}.json", sealed(body))

    def active(self, first):
        state = self.waiting(first)
        auth = self.authorization(state, first)
        ledger = self.root / f"LEDGER_{self.counter:03d}"
        gov.CONSUMPTION_ROOT = ledger / "PERMIT_CONSUMPTION"
        gov.activate_standing_autonomy(
            state_path=state, standing_authorization_path=auth, ledger_directory=ledger,
            activated_at_utc="2026-09-24T00:01:00Z", current_branch=gov.AUTONOMY_BRANCH)
        return state, auth, ledger

    def register(self, candidate, state, auth, ledger, at="2026-09-24T00:02:00Z"):
        return gov.register_pending_action(
            state_path=state, candidate_path=candidate, standing_authorization_path=auth,
            ledger_directory=ledger, registered_at_utc=at, current_branch=gov.AUTONOMY_BRANCH)

    def issue(self, candidate, state, auth, ledger, at="2026-09-24T00:03:00Z"):
        contract = gov.validate_candidate(candidate)[1]
        path = gov.PROJECT / contract["permit_output_path"]
        gov.issue_permit(candidate_path=candidate, state_path=state, standing_authorization_path=auth,
                         output_path=path, ledger_directory=ledger, issued_at_utc=at)
        return path

    def complete(self, candidate, state, auth, ledger, permit, requests, body, retries=0, index=1):
        gov.consume_permit(permit, candidate_path=candidate, state_path=state,
                           standing_authorization_path=auth, consumed_at_utc=f"2026-09-24T00:0{index+3}:00Z")
        parsed = gov.validate_candidate(candidate)[0]
        terminal = self.write(f"terminal_{index}.json", sealed({
            "application_body_bytes_read": body,
            "counters": {"network_requests_started": requests, "retry_requests": retries},
            "scope": parsed["scope"], "stage_id": parsed["stage_id"], "state": "SYNTHETIC_COMPLETE",
        }))
        return gov.transition_completed_action(
            state_path=state, candidate_path=candidate, permit_path=permit,
            standing_authorization_path=auth, terminal_path=terminal,
            terminal_sha256=file_sha256(terminal), request_delta=requests, body_delta=body,
            retry_delta=retries, ledger_directory=ledger,
            transitioned_at_utc=f"2026-09-24T00:0{index+4}:00Z", reason="SYNTHETIC_COMPLETE")

    def test_01_production_bootstrap_is_inactive_and_candidate_001_immutable(self):
        result = gov.validate_all()
        self.assertFalse(result["active"])
        self.assertEqual(result["permits_issued"], 0)
        self.assertEqual(file_sha256(gov.PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_001.json"),
                         "308dd5af01a4048cd6fb2a796248c324e2d9e6f01b2b44ca68262f98cf070463")
        self.assertFalse(gov.STANDING_AUTHORIZATION_PATH.exists())

    def test_01b_candidate_003_preserves_candidate_002_scientific_payload(self):
        old = load_canonical_json(CANDIDATE_002)
        new = load_canonical_json(CANDIDATE_003)
        scientific = {
            "closed_photsys_terminal", "decoded_fields", "execution", "expected_aggregate_fields",
            "input_authorities", "output_directory", "output_files",
            "resource_caps", "scientific_question", "scope", "specification", "stage_id",
            "success_terminal", "unresolved_gates",
        }
        self.assertEqual({key:old[key] for key in scientific}, {key:new[key] for key in scientific})

    def test_01c_first_action_identity_is_state_data_and_authorization_bound(self):
        source = inspect.getsource(gov)
        self.assertNotIn("FIRST_CANDIDATE_PATH", source)
        first_a = self.candidate("FIRST_A", gov.AUTHORITY_CLASSES[0])
        state_a = self.waiting(first_a)
        auth_a = self.authorization(state_a, first_a)
        gov.validate_standing_authorization(
            auth_a, expected_initial_state_sha256=file_sha256(state_a),
            expected_initial_state_path=state_a,
            expected_first_candidate=gov.validate_state(state_a)["first_candidate"])
        first_b = self.candidate("FIRST_B", gov.AUTHORITY_CLASSES[0])
        state_b = self.waiting(first_b)
        auth_b = self.authorization(state_b, first_b)
        gov.validate_standing_authorization(
            auth_b, expected_initial_state_sha256=file_sha256(state_b),
            expected_initial_state_path=state_b,
            expected_first_candidate=gov.validate_state(state_b)["first_candidate"])
        self.code("STANDING_AUTONOMY_AUTHORIZATION_INVALID", lambda: gov.validate_standing_authorization(
            auth_a, expected_initial_state_sha256=file_sha256(state_b),
            expected_initial_state_path=state_b,
            expected_first_candidate=gov.validate_state(state_b)["first_candidate"]))

    def test_01d_candidate_mutation_after_authorization_fails_closed(self):
        first = self.candidate("MUTABLE", gov.AUTHORITY_CLASSES[0])
        state = self.waiting(first)
        auth = self.authorization(state, first)
        first.write_bytes(first.read_bytes() + b" ")
        self.code("AUTONOMY_FIRST_ACTION_BINDING_INVALID", lambda: gov.activate_standing_autonomy(
            state_path=state, standing_authorization_path=auth, ledger_directory=self.root / "L",
            activated_at_utc="2026-09-24T00:01:00Z", current_branch=gov.AUTONOMY_BRANCH))

    def test_02_activation_exact_one_shot_zero_budget_and_ledger(self):
        first = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0])
        state, auth, ledger = self.active(first)
        active = gov.validate_state(state)
        self.assertTrue(active["active"])
        self.assertEqual((active["requests_remaining"], active["body_budget_remaining"]), (12, 16777216))
        self.assertEqual(len(list(ledger.glob("*_ACTIVATION.json"))), 1)
        self.code("AUTONOMY_ACTIVATION_STATE_INVALID", lambda: gov.activate_standing_autonomy(
            state_path=state, standing_authorization_path=auth, ledger_directory=ledger,
            activated_at_utc="2026-09-24T00:02:00Z", current_branch=gov.AUTONOMY_BRANCH))

    def test_03_activation_binding_and_branch_refusals(self):
        first = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0])
        state = self.waiting(first)
        bad = self.authorization(state, first, mandate_sha256="0" * 64)
        self.code("STANDING_AUTONOMY_AUTHORIZATION_INVALID", lambda: gov.activate_standing_autonomy(
            state_path=state, standing_authorization_path=bad, ledger_directory=self.root / "L1",
            activated_at_utc="2026-09-24T00:01:00Z", current_branch=gov.AUTONOMY_BRANCH))
        state = self.waiting(first); auth = self.authorization(state, first)
        self.code("UNAUTHORIZED_BRANCH", lambda: gov.activate_standing_autonomy(
            state_path=state, standing_authorization_path=auth, ledger_directory=self.root / "L2",
            activated_at_utc="2026-09-24T00:01:00Z", current_branch="main"))

    def test_04_generic_authority_subsets_and_budget_rules(self):
        first = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0])
        state, auth, ledger = self.active(first)
        for authority in gov.AUTHORITY_CLASSES:
            candidate = self.candidate("ACTION", authority, requests=1, body=16)
            result = gov.evaluate_policy(candidate_path=candidate, state_path=state,
                                         standing_authorization_path=auth, require_registered=False)
            self.assertEqual(result["decision"], gov.ELIGIBLE)
        for requests, body, expected in ((13, 1, "REQUEST_BUDGET_OVERFLOW"),
                                         (1, 16777217, "BODY_BUDGET_OVERFLOW")):
            candidate = self.candidate("OVER", gov.AUTHORITY_CLASSES[2], requests=requests, body=body)
            self.assertEqual(gov.evaluate_policy(candidate_path=candidate, state_path=state,
                standing_authorization_path=auth, require_registered=False)["decision"], expected)

    def test_05_multi_action_replay_offline_documentary_grouping_without_policy_change(self):
        policy_before = file_sha256(gov.POLICY_CORE_MANIFEST_PATH)
        first = self.candidate("OFFLINE_LOCAL_AUTHORITY_RELATION_AUDIT", gov.AUTHORITY_CLASSES[0])
        state, auth, ledger = self.active(first)
        self.register(first, state, auth, ledger)
        permit1 = self.issue(first, state, auth, ledger)
        self.complete(first, state, auth, ledger, permit1, 0, 0, index=1)

        documentary = self.candidate("BOUNDED_DOCUMENTARY_LOOKUP", gov.AUTHORITY_CLASSES[2], requests=1, body=64)
        self.register(documentary, state, auth, ledger, at="2026-09-24T00:06:00Z")
        self.assertEqual(gov.evaluate_policy(candidate_path=documentary, state_path=state,
            standing_authorization_path=auth)["decision"], gov.ELIGIBLE)
        permit2 = self.issue(documentary, state, auth, ledger, at="2026-09-24T00:07:00Z")
        self.complete(documentary, state, auth, ledger, permit2, 1, 64, index=4)

        grouping = self.candidate("PROSPECTIVE_GROUPING_METADATA", gov.AUTHORITY_CLASSES[3], requests=1, body=32)
        self.register(grouping, state, auth, ledger, at="2026-09-24T00:09:00Z")
        self.assertEqual(gov.evaluate_policy(candidate_path=grouping, state_path=state,
            standing_authorization_path=auth)["decision"], gov.ELIGIBLE)
        self.issue(grouping, state, auth, ledger, at="2026-09-24T00:10:00Z")
        self.assertEqual(file_sha256(gov.POLICY_CORE_MANIFEST_PATH), policy_before)

    def test_06_authority_concurrency_retry_and_manifest_refusals(self):
        mutations = [
            ("AUTHORITY_CLASS_EXPANSION", lambda c: c.update(authority_classes_used=["OUTSIDE"])),
            ("CONCURRENCY_LIMIT_EXCEEDED", lambda c: c.update(concurrency=2)),
            ("RETRY_NOT_PROSPECTIVELY_FROZEN", lambda c: c["retry_policy"].update(prospectively_frozen=False)),
            ("LITERAL_RESOURCE_MANIFEST_REQUIRED", lambda c: c.update(resource_manifest=None)),
        ]
        first = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0]); state, auth, _ = self.active(first)
        for expected, mutate in mutations:
            candidate = self.candidate("REFUSE", gov.AUTHORITY_CLASSES[2], requests=1, body=1,
                retries=1 if "RETRY" in expected else 0, mutate=mutate)
            try:
                result = gov.evaluate_policy(candidate_path=candidate, state_path=state,
                    standing_authorization_path=auth, require_registered=False)
                self.assertEqual(result["decision"], expected)
            except gov.GovernorError as exc:
                self.assertIn(expected, (exc.code, "RETRY_NOT_PROSPECTIVELY_FROZEN"))

    def test_07_all_firewalls_and_prohibited_scopes_refused(self):
        for key in gov.FIREWALL_KEYS:
            candidate = self.candidate("FIREWALL", gov.AUTHORITY_CLASSES[0],
                mutate=lambda c, k=key: c["scientific_firewall"].update({k: 1}))
            self.code("AUTONOMOUS_ACTION_FIREWALL_INVALID", lambda c=candidate: gov.validate_candidate(c))
        for scope in gov.PROHIBITED_SCOPE_KEYS:
            candidate = self.candidate("PROHIBITED", gov.AUTHORITY_CLASSES[0],
                mutate=lambda c, s=scope: c.update(requested_prohibited_scopes=[s]))
            self.code("AUTONOMOUS_ACTION_PROHIBITED_SCOPE_INVALID", lambda c=candidate: gov.validate_candidate(c))

    def test_08_git_candidate_command_state_and_policy_mutations_refused(self):
        for mutate in (
            lambda c: c["git_assertions"].update(branch="main"),
            lambda c: c["git_assertions"].update(force_push=True),
            lambda c: c["git_assertions"].update(merge_main=True),
        ):
            candidate = self.candidate("GIT", gov.AUTHORITY_CLASSES[0], mutate=mutate)
            self.code("AUTONOMOUS_ACTION_GIT_ASSERTIONS_INVALID", lambda c=candidate: gov.validate_candidate(c))
        candidate = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0])
        value = load_canonical_json(candidate); value["stage_id"] = "MUTATED"; candidate.write_bytes(canonical(value)+b"\n")
        self.code("AUTONOMOUS_ACTION_CANDIDATE_INVALID", lambda: gov.validate_candidate(candidate))
        candidate = self.candidate("COMMAND", gov.AUTHORITY_CLASSES[0])
        value = load_canonical_json(candidate); body = {k:v for k,v in value.items() if k != "sealed"}
        body["command_argv"] = ["synthetic", "--mutated"]
        body["autonomy_policy"]["candidate_payload_sha256"] = sha256_bytes(canonical(
            {k:v for k,v in body.items() if k != "autonomy_policy"}))
        candidate.write_bytes(canonical(sealed(body))+b"\n")
        self.code("COMMAND_ARGV_HASH_MISMATCH", lambda: gov.validate_candidate(candidate))

        first = self.candidate("FIRST", gov.AUTHORITY_CLASSES[0]); state, auth, ledger = self.active(first)
        self.register(first, state, auth, ledger); permit = self.issue(first, state, auth, ledger)
        value = load_canonical_json(state); body = {k:v for k,v in value.items() if k != "sealed"}; body["sequence"] += 1
        state.write_bytes(canonical(sealed(body))+b"\n")
        self.code("AUTONOMOUS_PERMIT_BINDING_MISMATCH", lambda: gov.validate_permit(
            permit,candidate_path=first,state_path=state,standing_authorization_path=auth))
        original = gov.file_sha256
        def altered(path):
            if Path(path).resolve() == (gov.PROJECT / "oc3/oc3lib/observational_multiplicity_governor.py").resolve():
                return "0" * 64
            return original(path)
        with patch.object(gov, "file_sha256", side_effect=altered):
            self.code("POLICY_CORE_MISMATCH", gov.validate_policy_core_manifest)

    def test_09_permit_single_use_canonical_marker_and_no_alternate_path(self):
        first = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0]); state, auth, ledger = self.active(first)
        self.register(first, state, auth, ledger); permit = self.issue(first, state, auth, ledger)
        self.assertNotIn("consumption_directory", inspect.signature(gov.consume_permit).parameters)
        alternate = self.root / "alternate" / f"{file_sha256(permit)}.json"
        alternate.parent.mkdir(); alternate.write_text("{}\n")
        marker = gov.consume_permit(permit, candidate_path=first, state_path=state,
                                    standing_authorization_path=auth, consumed_at_utc="2026-09-24T00:04:00Z")
        self.assertEqual(marker, gov.CONSUMPTION_ROOT / f"{file_sha256(permit)}.json")
        self.code("AUTONOMOUS_PERMIT_ALREADY_CONSUMED", lambda: gov.consume_permit(
            permit, candidate_path=first, state_path=state, standing_authorization_path=auth,
            consumed_at_utc="2026-09-24T00:05:00Z"))

    def test_10_transition_requires_marker_sha_and_counter_reservations(self):
        first = self.candidate("DOC", gov.AUTHORITY_CLASSES[2], requests=1, body=8)
        state, auth, ledger = self.active(first); self.register(first, state, auth, ledger)
        permit = self.issue(first, state, auth, ledger)
        terminal = self.write("terminal.json", sealed({"application_body_bytes_read":8,
            "counters":{"network_requests_started":1,"retry_requests":0},
            "scope":gov.validate_candidate(first)[0]["scope"],"stage_id":gov.validate_candidate(first)[0]["stage_id"],
            "state":"COMPLETE"}))
        kwargs = dict(state_path=state,candidate_path=first,permit_path=permit,
            standing_authorization_path=auth,terminal_path=terminal,terminal_sha256=file_sha256(terminal),
            request_delta=1,body_delta=8,retry_delta=0,ledger_directory=ledger,
            transitioned_at_utc="2026-09-24T00:05:00Z",reason="SYNTHETIC")
        self.code("AUTONOMOUS_PERMIT_CONSUMPTION_MISSING", lambda: gov.transition_completed_action(**kwargs))
        gov.consume_permit(permit,candidate_path=first,state_path=state,standing_authorization_path=auth,
                           consumed_at_utc="2026-09-24T00:04:00Z")
        bad = dict(kwargs); bad["terminal_sha256"] = "0"*64
        self.code("AUTONOMY_TERMINAL_SHA_MISMATCH", lambda: gov.transition_completed_action(**bad))
        bad = dict(kwargs); bad["request_delta"] = 0
        self.code("AUTONOMY_TERMINAL_COUNTER_MISMATCH", lambda: gov.transition_completed_action(**bad))
        bad = dict(kwargs); bad["body_delta"] = 9
        self.code("PERMIT_RESERVATION_EXCEEDED_REQUIRES_STOP", lambda: gov.transition_completed_action(**bad))

    def test_11_stop_and_scientific_terminal_are_closed(self):
        first = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0]); state, auth, ledger = self.active(first)
        report = self.root / "STOP.md"; report.write_text("# Stop\nExact synthetic blocker.\n")
        stopped = gov.enter_stop_requires_human(state_path=state,standing_authorization_path=auth,
            stop_report_path=report,blocker_code="SYNTHETIC_BLOCKER",ledger_directory=ledger,
            stopped_at_utc="2026-09-24T00:02:00Z",current_branch=gov.AUTONOMY_BRANCH)
        self.assertFalse(stopped["active"])
        self.code(gov.MANDATE_NOT_ACTIVE, lambda: gov.build_permit(candidate_path=first,state_path=state,
            standing_authorization_path=auth,issued_at_utc="2026-09-24T00:03:00Z"))

        first = self.candidate("SECOND", gov.AUTHORITY_CLASSES[0]); state, auth, ledger = self.active(first)
        final = self.root / "FINAL.md"; final.write_text("# Final\nSynthetic evidence.\n")
        matrix = self.root / "MATRIX.json"; matrix.write_text("{}\n")
        terminal = gov.finalize_scientific_terminal(state_path=state,standing_authorization_path=auth,
            outcome=gov.TERMINAL_OUTCOMES[2],final_report_path=final,claim_matrix_path=matrix,
            ledger_directory=ledger,finalized_at_utc="2026-09-24T00:02:00Z",current_branch=gov.AUTONOMY_BRANCH)
        self.assertFalse(terminal["active"]); self.assertEqual(terminal["state"],gov.STATE_TERMINAL)

    def test_12_only_state_bound_candidate_can_register_first(self):
        first = self.candidate("BOUND_FIRST", gov.AUTHORITY_CLASSES[0])
        other = self.candidate("UNBOUND_FIRST", gov.AUTHORITY_CLASSES[0])
        state, auth, ledger = self.active(first)
        self.code("AUTONOMY_FIRST_ACTION_BINDING_INVALID", lambda: self.register(other, state, auth, ledger))
        registered = self.register(first, state, auth, ledger)
        self.assertEqual(registered["registered_pending_action"]["registration_state"],
                         "FIRST_PENDING_AUTONOMOUS_ACTION")

    def test_13_candidate_003_exact_argv_and_historical_argv_refused(self):
        result = validate_candidate_003()
        self.assertEqual(result["state"], "CANDIDATE_003_EXECUTOR_INTEGRATION_VALIDATED")
        self.assertEqual((result["audit_executions"], result["network_requests"]), (0, 0))
        parsed = executor.parse_arguments(expected_command_argv()[2:])
        self.assertEqual(parsed.candidate, CANDIDATE_003)
        historical = load_canonical_json(CANDIDATE_002)["command_argv"]
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                executor.parse_arguments(historical[2:])
            with self.assertRaises(SystemExit):
                executor.parse_arguments(expected_command_argv()[2:] + ["--consumption-path", str(self.root)])

    def test_13b_candidate_004_exact_runtime_command_and_mutations(self):
        result = validate_candidate_004()
        self.assertEqual(result["state"], "CANDIDATE_004_RUNTIME_COMMAND_BINDING_VALIDATED")
        self.assertEqual(result["runtime_command_mutations_rejected"], 9)
        self.assertEqual((result["audit_executions"], result["network_requests"]), (0, 0))
        command = expected_command_argv_004()
        parsed = executor.parse_arguments(command[2:])
        self.assertEqual(parsed.candidate, CANDIDATE_004)
        executor.validate_runtime_invocation(load_canonical_json(CANDIDATE_004),
                                             executable=command[0], script_path=command[1],
                                             argument_vector=command[2:])
        governed = {0:"python", 1:"script", 2:"mode", 4:"candidate", 6:"permit",
                    8:"standing_authorization", 10:"state", 12:"output_directory"}
        for index, name in governed.items():
            with self.subTest(runtime_element=name):
                mutated = list(command)
                mutated[index] += ".changed"
                with self.assertRaises(executor.RuntimeCommandBindingError):
                    executor.validate_runtime_invocation(load_canonical_json(CANDIDATE_004),
                        executable=mutated[0], script_path=mutated[1], argument_vector=mutated[2:])
        with self.assertRaises(executor.RuntimeCommandBindingError):
            executor.validate_runtime_invocation(load_canonical_json(CANDIDATE_004),
                executable=command[0], script_path=command[1],
                argument_vector=[*command[2:], "--unknown-extra-argument"])

    def test_14_executor_consumes_canonical_permit_before_runner_and_replay_fails(self):
        first = self.candidate("EXECUTOR", gov.AUTHORITY_CLASSES[0], executor_command=True)
        state, auth, ledger = self.active(first)
        self.register(first, state, auth, ledger)
        permit = self.issue(first, state, auth, ledger)
        state_before = file_sha256(state)
        called = []

        def runner(output_directory):
            marker = gov.CONSUMPTION_ROOT / f"{file_sha256(permit)}.json"
            self.assertTrue(marker.is_file())
            self.assertEqual(output_directory, self.root / "OUTPUT")
            called.append(True)
            return {"state": "SYNTHETIC_AUDIT_COMPLETE"}

        command = load_canonical_json(first)["command_argv"]
        argv = command[2:]
        invalid_runtime_argv = list(argv)
        invalid_runtime_argv[invalid_runtime_argv.index("--output-directory") + 1] = str(self.root / "OTHER")
        with patch.object(executor.sys, "argv", [command[1], *invalid_runtime_argv]):
            with self.assertRaises(executor.RuntimeCommandBindingError):
                executor.main(audit_runner=lambda _: called.append(False),
                              now_utc=lambda: "2026-09-24T00:03:30Z")
        self.assertEqual(called, [])
        self.assertFalse((gov.CONSUMPTION_ROOT / f"{file_sha256(permit)}.json").exists())
        with patch.object(executor.sys, "argv", [command[1], *argv]):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(executor.main(audit_runner=runner,
                                               now_utc=lambda: "2026-09-24T00:04:00Z"), 0)
        self.assertEqual(called, [True])
        self.assertEqual(file_sha256(state), state_before)
        with patch.object(executor.sys, "argv", [command[1], *argv]):
            with self.assertRaises(gov.GovernorError) as caught:
                executor.main(audit_runner=lambda _: called.append(False),
                              now_utc=lambda: "2026-09-24T00:05:00Z")
        self.assertEqual(caught.exception.code, "AUTONOMOUS_PERMIT_ALREADY_CONSUMED")
        self.assertEqual(called, [True])

    def test_15_historical_v1_policy_core_is_byte_immutable(self):
        self.assertEqual(file_sha256(gov.HISTORICAL_POLICY_MANIFEST_PATH),
                         gov.HISTORICAL_POLICY_MANIFEST_SHA256)

    def test_16_policy_core_v2_mutation_blocks_permit(self):
        first = self.candidate("POLICY_V2", gov.AUTHORITY_CLASSES[0])
        state, auth, ledger = self.active(first)
        self.register(first, state, auth, ledger)
        member = (gov.PROJECT / "oc3/oc3lib/observational_multiplicity_governor.py").resolve()
        original = gov.file_sha256

        def altered(path):
            return "0" * 64 if Path(path).resolve() == member else original(path)

        with patch.object(gov, "file_sha256", side_effect=altered):
            self.code("POLICY_CORE_MISMATCH", lambda: gov.build_permit(
                candidate_path=first, state_path=state, standing_authorization_path=auth,
                issued_at_utc="2026-09-24T00:03:00Z"))
        permit_path = gov.PROJECT / gov.validate_candidate(first)[1]["permit_output_path"]
        self.assertFalse(permit_path.exists())


if __name__ == "__main__":
    unittest.main()
