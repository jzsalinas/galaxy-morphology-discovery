from __future__ import annotations

from pathlib import Path
import io
import inspect
import tempfile
import unittest

import oc3_cross_observer_grouping_documentary as documentary
from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import file_sha256, load_canonical_json, sealed, sha256_bytes
from oc3lib import cross_observer_grouping_governor as gov
from oc3lib.cross_observer_grouping_documentary_validation import (
    CANDIDATE, expected_command_argv, validate_candidate as validate_documentary_candidate,
    validate_runtime_invocation,
)


class CrossObserverGroupingGovernorTests(unittest.TestCase):
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

    def candidate(self, name, authority, *, requests=0, body=0, retries=0, mutate=None):
        self.counter += 1
        stage, scope = f"SYNTHETIC-{name}-{self.counter:03d}", f"SYNTHETIC_{name}_ONLY"
        argv = ["synthetic", "--stage", stage]
        payload = {"command_argv": argv, "command_argv_sha256": sha256_bytes(canonical(argv)),
            "implementation_aggregate": "a" * 64,
            "schema_version": "SYNTHETIC_CROSS_OBSERVER_GROUPING_CANDIDATE_001",
            "scope": scope, "specification": self.binding(gov.SCIENTIFIC_SPEC_PATH), "stage_id": stage}
        payload_sha = sha256_bytes(canonical(payload))
        implementation = {"algorithm": "OC3_IMPLEMENTATION_AGGREGATE_V1", "sha256": "a" * 64}
        receipt = self.write(f"receipt_{self.counter}.json", sealed({
            "action_kind": name, "candidate_payload_sha256": payload_sha,
            "frozen_specification": payload["specification"], "implementation_binding": implementation,
            "network_requests": 0, "schema_version": "OC3_CROSS_OBSERVER_GROUPING_ACTION_VALIDATION_RECEIPT_002",
            "scope": scope, "stage_id": stage, "validated": True,
            "validator": self.binding(gov.PROJECT / "oc3/oc3lib/cross_observer_grouping.py")}))
        manifest_binding = None
        if requests:
            manifest = self.write(f"manifest_{self.counter}.json", sealed({"broad_crawling": False,
                "mirror_substitution": False, "resources": [{"application_body_byte_cap": body,
                    "accepted_content_types": ["text/plain"],
                    "evidence_capture_mode": "HASHED_RESPONSE_SNAPSHOT",
                    "evidence_class": authority, "expected_representation": "text/plain",
                    "host": "example.invalid", "id": f"RESOURCE-{self.counter}",
                    "method": "GET", "purpose": "synthetic replay", "revision_identity": None,
                    "redirects": 0, "retries": retries, "url": f"https://example.invalid/{self.counter}"}],
                "schema_version": "SYNTHETIC_LITERAL_RESOURCE_MANIFEST_001"}))
            manifest_binding = self.binding(manifest)
        contract = {"action_kind": name, "action_validation_receipt": self.binding(receipt),
            "application_body_reservation": body, "authority_classes_used": [authority],
            "candidate_hash_mode": "CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED",
            "candidate_payload_sha256": payload_sha, "command_argv_sha256": payload["command_argv_sha256"],
            "concurrency": 1, "frozen_specification": payload["specification"],
            "full_candidate_identity": "FULL_FILE_SHA256_BOUND_BY_STATE_AUTHORIZATION_PERMIT_AND_LEDGER",
            "git_assertions": {"branch": gov.AUTONOMY_BRANCH, "force_push": False, "merge_main": False},
            "implementation_binding": implementation, "network_request_reservation": requests,
            "permit_output_path": str((self.root / f"permit_{self.counter}.json").relative_to(gov.PROJECT)),
            "requested_prohibited_scopes": [], "resource_manifest": manifest_binding,
            "resume_policy": {"allowed": False, "prospectively_frozen": True},
            "retry_reservation": retries,
            "retry_policy": {"exact_same_resource": True, "prospectively_frozen": True},
            "schema_version": "OC3_CROSS_OBSERVER_GROUPING_ACTION_CONTRACT_002",
            "scientific_firewall": {key: 0 for key in gov.FIREWALL_KEYS}, "scope": scope,
            "stage_id": stage, "standing_mandate_sha256": file_sha256(gov.MANDATE_PATH)}
        if mutate:
            mutate(contract)
        return self.write(f"candidate_{self.counter}.json", sealed({**payload, "autonomy_policy": contract}))

    def waiting(self, first):
        production = load_canonical_json(gov.STATE_PATH)
        body = {k: v for k, v in production.items() if k != "sealed"}
        body.update({"active": False, "body_budget_remaining": 16_777_216,
            "current_stage": "FIRST_ACTION_PREPARED", "first_candidate": self.binding(first),
            "last_completed_stage": None, "last_terminal": None, "permits_issued": 0,
            "registered_pending_action": None, "requests_remaining": 12, "scientific_outcome": None,
            "sequence": 0, "standing_authorization": None,
            "standing_authorization_initial_state_sha256": None, "state": gov.STATE_WAITING,
            "stop_reason": None})
        return self.write(f"state_{self.counter}.json", sealed(body))

    def authorization(self, state, first):
        return self.write(f"authorization_{self.counter}.json", sealed({
            "authorization_state": "STANDING_HUMAN_AUTONOMY_AUTHORIZATION", "authorized": True,
            "authorized_at_utc": "2026-09-24T00:00:00Z", "authorized_by": "Synthetic Reviewer",
            "continuation_policy": "CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN",
            "first_candidate_path": str(first.relative_to(gov.PROJECT)), "first_candidate_sha256": file_sha256(first),
            "initial_state_path": str(state.relative_to(gov.PROJECT)), "initial_state_sha256": file_sha256(state),
            "mandate_path": str(gov.MANDATE_PATH.relative_to(gov.PROJECT)), "mandate_sha256": file_sha256(gov.MANDATE_PATH),
            "mission_id": gov.MISSION_ID, "mission_scope": gov.MISSION_SCOPE,
            "policy_core_manifest_path": str(gov.POLICY_CORE_MANIFEST_PATH.relative_to(gov.PROJECT)),
            "policy_core_manifest_sha256": file_sha256(gov.POLICY_CORE_MANIFEST_PATH),
            "schema_version": "OC3_CROSS_OBSERVER_GROUPING_STANDING_AUTHORIZATION_002"}))

    def active(self, first):
        state = self.waiting(first); auth = self.authorization(state, first)
        ledger = self.root / f"LEDGER_{self.counter:03d}"
        gov.CONSUMPTION_ROOT = ledger / "PERMIT_CONSUMPTION"
        gov.activate_standing_autonomy(state_path=state, standing_authorization_path=auth,
            ledger_directory=ledger, activated_at_utc="2026-09-24T00:01:00Z",
            current_branch=gov.AUTONOMY_BRANCH)
        return state, auth, ledger

    def run_action(self, candidate, state, auth, ledger, *, index, requests=0, body=0):
        gov.register_pending_action(state_path=state, candidate_path=candidate,
            standing_authorization_path=auth, ledger_directory=ledger,
            registered_at_utc=f"2026-09-24T00:{index*10+2:02d}:00Z", current_branch=gov.AUTONOMY_BRANCH)
        permit = gov.PROJECT / gov.validate_candidate(candidate)[1]["permit_output_path"]
        gov.issue_permit(candidate_path=candidate, state_path=state, standing_authorization_path=auth,
            output_path=permit, ledger_directory=ledger, issued_at_utc=f"2026-09-24T00:{index*10+3:02d}:00Z")
        gov.consume_permit(permit, candidate_path=candidate, state_path=state,
            standing_authorization_path=auth, consumed_at_utc=f"2026-09-24T00:{index*10+4:02d}:00Z")
        parsed = gov.validate_candidate(candidate)[0]
        terminal = self.write(f"terminal_{index}.json", sealed({"application_body_bytes_read": body,
            "counters": {"network_requests_started": requests, "retry_requests": 0},
            "scope": parsed["scope"], "stage_id": parsed["stage_id"], "state": "SYNTHETIC_COMPLETE"}))
        gov.transition_completed_action(state_path=state, candidate_path=candidate, permit_path=permit,
            standing_authorization_path=auth, terminal_path=terminal, terminal_sha256=file_sha256(terminal),
            request_delta=requests, body_delta=body, retry_delta=0, ledger_directory=ledger,
            transitioned_at_utc=f"2026-09-24T00:{index*10+5:02d}:00Z", reason="SYNTHETIC_COMPLETE")
        return permit

    def test_production_state_is_terminal_and_first_candidate_remains_bound(self):
        result = gov.validate_all(); state = load_canonical_json(gov.STATE_PATH)
        self.assertEqual((result["active"], result["permits_issued"], result["state"]),
                         (False, 6, gov.STATE_TERMINAL))
        self.assertTrue(gov.STANDING_AUTHORIZATION_PATH.exists())
        self.assertEqual(state["first_candidate"], self.binding(CANDIDATE))

    def test_policy_core_is_generic(self):
        source = inspect.getsource(gov)
        self.assertNotIn("DOCUMENTARY_FEASIBILITY_CANDIDATE", source)
        self.assertNotIn("OC3-CROSS-OBSERVER-GROUPING-DOCUMENTARY-FEASIBILITY-001", source)
        self.assertNotIn("legacysurvey.org", source)
        self.assertNotIn("datalab.noirlab.edu", source)
        self.assertNotIn("arxiv.org", source)

    def test_documentary_candidate_and_command_are_exact(self):
        candidate = validate_documentary_candidate()
        command = expected_command_argv()
        validate_runtime_invocation(candidate, executable=command[0], script_path=command[1], argument_vector=command[2:])
        changed = list(command); changed[-1] += "-changed"
        with self.assertRaises(Exception):
            validate_runtime_invocation(candidate, executable=changed[0], script_path=changed[1], argument_vector=changed[2:])

    def test_partial_body_bytes_are_charged_before_cap_failure(self):
        response = io.BytesIO(b"12345")
        response.headers = {}
        counters = {"application_body_bytes": 0, "network_requests_started": 1}
        with self.assertRaises(Exception):
            documentary._read_bounded(response, 4, 10, counters)
        self.assertEqual(counters, {"application_body_bytes": 5, "network_requests_started": 1})

    def test_request_is_charged_before_transport_construction(self):
        candidate = load_canonical_json(CANDIDATE)
        counters = {"application_body_bytes": 0, "network_requests_started": 0}

        class BrokenOpener:
            def open(self, request, timeout):
                raise OSError("synthetic transport refusal")

        original = documentary.urllib.request.build_opener
        documentary.urllib.request.build_opener = lambda handler: BrokenOpener()
        try:
            with self.assertRaises(OSError):
                documentary._acquire(candidate, self.root / "partial", counters)
        finally:
            documentary.urllib.request.build_opener = original
        self.assertEqual(counters, {"application_body_bytes": 0, "network_requests_started": 1})

    def test_terminal_mission_cannot_issue_permit(self):
        result = gov.evaluate_candidate(CANDIDATE)
        self.assertEqual((result["decision"], result["permit_state"]),
                         (gov.MANDATE_NOT_ACTIVE, gov.NO_PERMIT_ISSUED))

    def test_authority_budget_and_firewall_refusals(self):
        first = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0])
        state, auth, ledger = self.active(first)
        for mutation, code in (
            (lambda c: c.update(authority_classes_used=["UNREVIEWED_WEB"]), "AUTHORITY_CLASS_EXPANSION"),
            (lambda c: c.update(network_request_reservation=13), "REQUEST_BUDGET_OVERFLOW"),
            (lambda c: c["scientific_firewall"].update(source_rows_read=1), "AUTONOMOUS_ACTION_FIREWALL_INVALID"),
            (lambda c: c["requested_prohibited_scopes"].append("training"), "AUTONOMOUS_ACTION_PROHIBITED_SCOPE_INVALID"),
        ):
            candidate = self.candidate("BAD", gov.AUTHORITY_CLASSES[0], mutate=mutation)
            if code.startswith("AUTONOMOUS_ACTION"):
                self.code(code, lambda c=candidate: gov.validate_candidate(c))
            else:
                result = gov.evaluate_policy(candidate_path=candidate, state_path=state,
                    standing_authorization_path=auth, current_branch=gov.AUTONOMY_BRANCH, require_registered=False)
                self.assertEqual(result["decision"], code)

    def test_single_use_permit_and_multi_action_replay(self):
        first = self.candidate("OFFLINE", gov.AUTHORITY_CLASSES[0])
        state, auth, ledger = self.active(first)
        permit = self.run_action(first, state, auth, ledger, index=1)
        self.code("AUTONOMOUS_PERMIT_ALREADY_CONSUMED", lambda: gov.consume_permit(
            permit, candidate_path=first, state_path=state, standing_authorization_path=auth,
            consumed_at_utc="2026-09-24T00:16:00Z"))
        second = self.candidate("DOCUMENTARY", gov.AUTHORITY_CLASSES[1], requests=1, body=1024)
        self.run_action(second, state, auth, ledger, index=2, requests=1, body=1024)
        final = load_canonical_json(state)
        self.assertEqual((final["permits_issued"], final["requests_remaining"], final["body_budget_remaining"]),
                         (2, 11, 16_776_192))
