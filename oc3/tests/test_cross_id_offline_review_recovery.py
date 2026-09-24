import inspect
import tempfile
import unittest
from pathlib import Path

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import file_sha256, load_canonical_json, sealed, sha256_bytes
from oc3lib import cross_id_offline_review_recovery as science
from oc3lib import cross_id_offline_review_recovery_governor as gov
from oc3lib.cross_id_offline_review_recovery_validation import (
    CANDIDATE, EXPECTED_INPUTS, expected_command_argv, validate_candidate,
    validate_runtime_invocation,
)


class CrossIdOfflineRecoveryBootstrapTests(unittest.TestCase):
    def test_predecessor_stop_is_immutable_and_permit_consumed(self):
        self.assertEqual(file_sha256(gov.PRIOR_TERMINAL_STATE_PATH), gov.PRIOR_TERMINAL_STATE_SHA256)
        state = load_canonical_json(gov.PRIOR_TERMINAL_STATE_PATH)
        self.assertEqual((state["state"], state["active"], state["stop_reason"]),
                         (gov.STOP_REQUIRES_HUMAN, False,
                          "OFFLINE_REVIEW_CONSUMED_PERMIT_IMPLEMENTATION_MARKER_MISMATCH"))
        permit_sha = "2807fefd6b6e93be45aa6377fdd65ab4dbf0be26a5ab6551e23b1a9dc0e3c7df"
        marker = gov.PROJECT / "oc3/CROSS_ID_FORMALISM_RECOVERY_AUTONOMY_LEDGER/PERMIT_CONSUMPTION" / f"{permit_sha}.json"
        self.assertTrue(marker.is_file())

    def test_closed_local_input_hashes_are_exact(self):
        for relative, digest in EXPECTED_INPUTS:
            self.assertEqual(file_sha256(gov.PROJECT / relative), digest)

    def test_whitespace_normalization_exact(self):
        self.assertEqual(science.normalize_whitespace("  alpha\t\n beta\u2003gamma  "),
                         "alpha beta gamma")

    def test_known_layout_break_passes(self):
        text = "prefix inverse of the\n covariance matrix suffix"
        self.assertEqual(science.marker_occurrences(text, "inverse of the covariance matrix"), (1,))

    def test_arbitrary_whitespace_between_every_token_passes(self):
        marker = "inverse of the covariance matrix"
        for separator in (" ", "\t", "\n", " \t\n\u2003 "):
            self.assertEqual(science.marker_occurrences(separator.join(marker.split()), marker), (0,))

    def test_required_negative_phrases_fail(self):
        marker = "inverse of the covariance matrix"
        negatives = ("inverse of a covariance matrix", "inverse covariance matrix",
                     "inverse of the variance matrix", "matrix covariance the of inverse")
        for value in negatives:
            self.assertEqual(science.marker_occurrences(value, marker), (), value)

    def test_no_silent_dehyphenation(self):
        self.assertEqual(science.marker_occurrences("inverse of the covari-\nance matrix",
                                                    "inverse of the covariance matrix"), ())

    def test_all_markers_use_one_matcher(self):
        source = inspect.getsource(science.evaluate_all_markers)
        self.assertIn("marker_occurrences(text, literal)", source)
        self.assertNotIn("if marker_id", source)
        rows = science.evaluate_all_markers("irrelevant")
        self.assertEqual([r["marker_id"] for r in rows], [m[0] for m in science.MARKERS])

    def test_vocabulary_and_terminal_mapping_are_frozen(self):
        science.validate_claim_vocabulary()
        self.assertEqual(science.TERMINAL_OUTCOMES, gov.TERMINAL_OUTCOMES)
        self.assertEqual(science.terminal_outcome("SUPPORTED", "SUPPORTED"),
                         "CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE")
        self.assertEqual(science.terminal_outcome("INCONCLUSIVE", "INCONCLUSIVE"),
                         "CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE")

    def test_candidate_and_exact_runtime_command(self):
        candidate = validate_candidate()
        command = expected_command_argv()
        validate_runtime_invocation(candidate, executable=command[0], script_path=command[1],
                                    argument_vector=command[2:])
        changed = list(command); changed[-1] += "-changed"
        with self.assertRaises(Exception):
            validate_runtime_invocation(candidate, executable=changed[0], script_path=changed[1],
                                        argument_vector=changed[2:])

    def test_candidate_has_five_outputs_and_zero_observation(self):
        value = validate_candidate()
        self.assertEqual(value["output_files"], ["EXTRACTION_PROVENANCE.json", "MARKER_EVIDENCE.json",
            "CLAIM_MATRIX.json", "REVIEW_REPORT.md", "TERMINAL.json"])
        self.assertEqual((value["network_requests"], value["application_body_bytes"],
                          value["source_rows_read"], value["matching_operations"]), (0, 0, 0, 0))
        self.assertFalse(value["search_bound_selected"])
        self.assertFalse(value["scientific_threshold_selected"])

    def test_mission_closed_at_scientific_terminal_with_single_consumed_permit(self):
        state = gov.validate_state()
        self.assertEqual((state["state"], state["active"], state["permits_issued"]),
                         (gov.STATE_TERMINAL, False, 1))
        self.assertEqual(state["scientific_outcome"],
                         "CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE")
        self.assertTrue(gov.STANDING_AUTHORIZATION_PATH.exists())
        permit = gov.PROJECT / validate_candidate()["autonomy_policy"]["permit_output_path"]
        self.assertTrue(permit.exists())
        self.assertTrue(gov._consumption_marker_path(permit).exists())
        self.assertEqual(gov.evaluate_candidate(CANDIDATE),
                         {"decision": gov.MANDATE_NOT_ACTIVE, "permit_state": gov.NO_PERMIT_ISSUED})

    def test_budget_authorities_and_firewall_are_closed(self):
        mandate = gov.validate_mandate()
        self.assertEqual(mandate["budgets"], {"application_body_bytes_parent": 0,
            "application_body_bytes_remaining": 0, "concurrency": 1,
            "network_requests_parent": 0, "network_requests_remaining": 0,
            "retries_default": 0, "retries_max_per_exact_resource": 0})
        self.assertEqual(tuple(mandate["allowed_authority_classes"]), gov.AUTHORITY_CLASSES)
        self.assertTrue(all(v == 0 for v in mandate["firewall"].values()))

    def test_static_authorities_and_policy_core_validate(self):
        authorities = gov.validate_static_authorities()
        self.assertIn("OC3_CROSS_ID_FORMALISM_RECOVERY_STOP_REPORT_001.md", authorities)
        gov.validate_policy_core_manifest()

    def test_governor_is_generic(self):
        source = inspect.getsource(gov)
        for forbidden in ("inverse of the covariance matrix", "BUDAVARI_SZALAY",
                          "OC3-CROSS-ID-OFFLINE-SEMANTIC-REVIEW-RECOVERY-001"):
            self.assertNotIn(forbidden, source)
        self.assertIn("AUTONOMOUS_PERMIT_ALREADY_CONSUMED", source)
        self.assertIn("UNRESOLVED_REGISTERED_ACTION", source)


class CrossIdOfflineRecoveryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=gov.PROJECT / "oc3")
        self.root = Path(self.tmp.name)
        self.counter = 0
        self.original_consumption = gov.CONSUMPTION_ROOT
        gov.CONSUMPTION_ROOT = self.root / "ledger/PERMIT_CONSUMPTION"

    def tearDown(self):
        gov.CONSUMPTION_ROOT = self.original_consumption
        self.tmp.cleanup()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(value) + b"\n")
        return path

    def binding(self, path):
        return {"path": str(Path(path).resolve().relative_to(gov.PROJECT)),
                "sha256": file_sha256(path)}

    def candidate(self, name):
        self.counter += 1
        stage = f"SYNTHETIC-{name}-{self.counter:03d}"
        scope = f"SYNTHETIC_{name}_ONLY"
        argv = ["synthetic", "--stage", stage]
        payload = {"command_argv": argv, "command_argv_sha256": sha256_bytes(canonical(argv)),
                   "implementation_aggregate": "a" * 64, "schema_version": "SYNTHETIC_RECOVERY_001",
                   "scope": scope, "specification": self.binding(gov.SCIENTIFIC_SPEC_PATH),
                   "stage_id": stage}
        payload_sha = sha256_bytes(canonical(payload))
        implementation = {"algorithm": "OC3_IMPLEMENTATION_AGGREGATE_V1", "sha256": "a" * 64}
        receipt = self.write(f"receipt-{self.counter}.json", sealed({
            "action_kind": name, "candidate_payload_sha256": payload_sha,
            "frozen_specification": payload["specification"], "implementation_binding": implementation,
            "network_requests": 0,
            "schema_version": "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_ACTION_VALIDATION_RECEIPT_001",
            "scope": scope, "stage_id": stage, "validated": True,
            "validator": self.binding(gov.PROJECT / "oc3/oc3lib/cross_id_offline_review_recovery.py")}))
        contract = {"action_kind": name, "action_validation_receipt": self.binding(receipt),
            "application_body_reservation": 0, "authority_classes_used": [gov.AUTHORITY_CLASSES[0]],
            "candidate_hash_mode": "CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED",
            "candidate_payload_sha256": payload_sha, "command_argv_sha256": payload["command_argv_sha256"],
            "concurrency": 1, "frozen_specification": payload["specification"],
            "full_candidate_identity": "FULL_FILE_SHA256_BOUND_BY_STATE_AUTHORIZATION_PERMIT_AND_LEDGER",
            "git_assertions": {"branch": gov.AUTONOMY_BRANCH, "force_push": False, "merge_main": False},
            "implementation_binding": implementation, "network_request_reservation": 0,
            "permit_output_path": str((self.root / f"permit-{self.counter}.json").relative_to(gov.PROJECT)),
            "requested_prohibited_scopes": [], "resource_manifest": None,
            "resume_policy": {"allowed": False, "prospectively_frozen": True},
            "retry_policy": {"exact_same_resource": True, "prospectively_frozen": True},
            "retry_reservation": 0, "schema_version": "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_ACTION_CONTRACT_001",
            "scientific_firewall": {key: 0 for key in gov.FIREWALL_KEYS}, "scope": scope,
            "stage_id": stage, "standing_mandate_sha256": file_sha256(gov.MANDATE_PATH)}
        return self.write(f"candidate-{self.counter}.json", sealed({**payload, "autonomy_policy": contract}))

    def activate(self, first):
        production = load_canonical_json(gov.STATE_PATH)
        body = {k: v for k, v in production.items() if k != "sealed"}
        body.update({"active": False, "first_candidate": self.binding(first),
            "current_stage": "FIRST_ACTION_PREPARED", "last_completed_stage": None,
            "last_terminal": None, "permits_issued": 0, "registered_pending_action": None,
            "scientific_outcome": None, "sequence": 0, "standing_authorization": None,
            "standing_authorization_initial_state_sha256": None,
            "state": gov.STATE_WAITING, "stop_reason": None})
        state = self.write("state.json", sealed(body))
        auth = self.write("authorization.json", sealed({
            "authorization_state": "STANDING_HUMAN_AUTONOMY_AUTHORIZATION", "authorized": True,
            "authorized_at_utc": "2026-09-24T18:00:00Z", "authorized_by": "Synthetic Reviewer",
            "continuation_policy": "CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN",
            "first_candidate_path": str(first.relative_to(gov.PROJECT)),
            "first_candidate_sha256": file_sha256(first), "initial_state_path": str(state.relative_to(gov.PROJECT)),
            "initial_state_sha256": file_sha256(state), "mandate_path": str(gov.MANDATE_PATH.relative_to(gov.PROJECT)),
            "mandate_sha256": file_sha256(gov.MANDATE_PATH), "mission_id": gov.MISSION_ID,
            "mission_scope": gov.MISSION_SCOPE,
            "policy_core_manifest_path": str(gov.POLICY_CORE_MANIFEST_PATH.relative_to(gov.PROJECT)),
            "policy_core_manifest_sha256": file_sha256(gov.POLICY_CORE_MANIFEST_PATH),
            "schema_version": "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_STANDING_AUTHORIZATION_001"}))
        ledger = self.root / "ledger"
        gov.activate_standing_autonomy(state_path=state, standing_authorization_path=auth,
            ledger_directory=ledger, activated_at_utc="2026-09-24T18:01:00Z",
            current_branch=gov.AUTONOMY_BRANCH)
        return state, auth, ledger

    def run_action(self, candidate, state, auth, ledger, index):
        gov.register_pending_action(state_path=state, candidate_path=candidate,
            standing_authorization_path=auth, ledger_directory=ledger,
            registered_at_utc=f"2026-09-24T18:{index}2:00Z", current_branch=gov.AUTONOMY_BRANCH)
        permit = gov.PROJECT / gov.validate_candidate(candidate)[1]["permit_output_path"]
        gov.issue_permit(candidate_path=candidate, state_path=state, standing_authorization_path=auth,
            output_path=permit, ledger_directory=ledger, issued_at_utc=f"2026-09-24T18:{index}3:00Z")
        gov.consume_permit(permit, candidate_path=candidate, state_path=state,
            standing_authorization_path=auth, consumed_at_utc=f"2026-09-24T18:{index}4:00Z")
        parsed = gov.validate_candidate(candidate)[0]
        terminal = self.write(f"terminal-{index}.json", sealed({"application_body_bytes_read": 0,
            "counters": {**{key: 0 for key in gov.FIREWALL_KEYS}, "network_requests_started": 0,
                         "retry_requests": 0}, "scope": parsed["scope"], "stage_id": parsed["stage_id"],
            "state": "SYNTHETIC_COMPLETE"}))
        gov.transition_completed_action(state_path=state, candidate_path=candidate, permit_path=permit,
            standing_authorization_path=auth, terminal_path=terminal, terminal_sha256=file_sha256(terminal),
            request_delta=0, body_delta=0, retry_delta=0, ledger_directory=ledger,
            transitioned_at_utc=f"2026-09-24T18:{index}5:00Z", reason="SYNTHETIC_COMPLETE")
        return permit

    def test_single_use_multi_action_and_terminal_closure(self):
        first = self.candidate("FIRST")
        state, auth, ledger = self.activate(first)
        permit = self.run_action(first, state, auth, ledger, 1)
        with self.assertRaises(gov.GovernorError) as caught:
            gov.consume_permit(permit, candidate_path=first, state_path=state,
                               standing_authorization_path=auth,
                               consumed_at_utc="2026-09-24T18:16:00Z")
        self.assertEqual(caught.exception.code, "AUTONOMOUS_PERMIT_ALREADY_CONSUMED")
        second = self.candidate("SECOND")
        self.run_action(second, state, auth, ledger, 2)
        report = self.root / "final.md"; report.write_text("synthetic final\n")
        matrix = self.write("matrix.json", {"claims": []})
        final = gov.finalize_scientific_terminal(state_path=state, standing_authorization_path=auth,
            outcome="CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE", final_report_path=report,
            claim_matrix_path=matrix, ledger_directory=ledger, finalized_at_utc="2026-09-24T18:30:00Z",
            current_branch=gov.AUTONOMY_BRANCH)
        self.assertEqual((final["state"], final["active"], final["permits_issued"]),
                         (gov.STATE_TERMINAL, False, 2))


if __name__ == "__main__":
    unittest.main()
