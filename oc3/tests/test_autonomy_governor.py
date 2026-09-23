import tempfile
import unittest
from pathlib import Path

from oc3lib.autonomy_governor import *
from oc3lib.core import canonical
from oc3lib.galaxy_eligibility_photsys_authority_probe import (
    file_sha256, load_canonical_json, sealed, write_json_immutable,
)


class AutonomyGovernorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="autonomy_SYNTHETIC_ONLY_", dir=PROJECT / "oc3/tests")
        self.root = Path(self.temp.name)
        self.write_counter = 0

    def tearDown(self):
        self.temp.cleanup()

    def code(self, expected, call):
        with self.assertRaises(AutonomyError) as caught:
            call()
        self.assertEqual(caught.exception.code, expected)

    def write(self, name, value):
        self.write_counter += 1
        path = self.root / f"{self.write_counter:03d}_{name}"
        write_json_immutable(path, value)
        return path

    def reseal(self, value):
        return sealed({key: item for key, item in value.items() if key != "sealed"})

    def active_state(self, candidate_path=RANGE_CANDIDATE_PATH):
        state = load_canonical_json(STATE_PATH)
        body = {key: item for key, item in state.items() if key != "sealed"}
        body["active"] = True
        body["state"] = STATE_ACTIVE
        body["registered_pending_action"] = {
            "candidate_path": str(Path(candidate_path).resolve().relative_to(PROJECT)),
            "candidate_sha256": file_sha256(candidate_path),
            "registration_state": "FIRST_PENDING_AUTONOMOUS_ACTION",
            "scope": "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_ONLY",
            "stage_id": "OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-RANGE-SIZE-PROBE-001",
        }
        return self.write("state.json", sealed(body))

    def authorization(self, **updates):
        body = {
            "authorization_state": "STANDING_HUMAN_AUTONOMY_AUTHORIZATION",
            "authorized": True,
            "authorized_at_utc": "2026-09-24T00:00:00Z",
            "authorized_by": "Synthetic Reviewer",
            "continuation_policy": "CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN",
            "mandate_path": str(MANDATE_PATH.relative_to(PROJECT)),
            "mandate_sha256": file_sha256(MANDATE_PATH),
            "mission_id": MISSION_ID,
            "schema_version": "OC3_AUTONOMY_STANDING_AUTHORIZATION_001",
            "scope": MISSION_SCOPE,
        }
        body.update(updates)
        return self.write("standing.json", sealed(body))

    def candidate_mutation(self, mutate):
        candidate = load_canonical_json(RANGE_CANDIDATE_PATH)
        body = {key: item for key, item in candidate.items() if key != "sealed"}
        mutate(body)
        return self.write("candidate.json", sealed(body))

    def policy(self, candidate_path=None, state_path=None, auth_path=None, branch=AUTONOMY_BRANCH):
        return evaluate_policy(candidate_path=candidate_path or RANGE_CANDIDATE_PATH,
                               state_path=state_path or STATE_PATH,
                               standing_authorization_path=auth_path or STANDING_AUTHORIZATION_PATH,
                               current_branch=branch)

    def active_fixture(self, candidate_path=None):
        candidate_path = candidate_path or RANGE_CANDIDATE_PATH
        return self.active_state(candidate_path), self.authorization()

    def test_01_static_authorities_and_pending_mandate(self):
        self.assertIn(str(MANDATE_PATH.relative_to(PROJECT)), validate_static_authorities())
        self.assertFalse(validate_mandate()["active"])

    def test_02_no_standing_authorization_refuses_permit(self):
        result = self.policy()
        self.assertEqual(result, {"decision": MANDATE_NOT_ACTIVE, "permit_state": NO_PERMIT_ISSUED})

    def test_03_wrong_mandate_sha_refused(self):
        state = self.active_state()
        auth = self.authorization(mandate_sha256="0" * 64)
        self.assertEqual(self.policy(state_path=state, auth_path=auth)["decision"],
                         "STANDING_AUTONOMY_AUTHORIZATION_INVALID")

    def test_04_candidate_mutation_refused_by_state_binding(self):
        candidate = self.candidate_mutation(lambda body: body["budget"].update(parent_body_maximum=1))
        state, auth = self.active_fixture()
        self.assertEqual(self.policy(candidate_path=candidate, state_path=state, auth_path=auth)["decision"],
                         "CANDIDATE_STATE_BINDING_MISMATCH")

    def test_05_command_hash_mutation_refused(self):
        candidate = self.candidate_mutation(lambda body: body["command_argv"].append("--mutated"))
        state, auth = self.active_fixture(candidate)
        self.code("COMMAND_ARGV_HASH_MISMATCH",
                  lambda: self.policy(candidate_path=candidate, state_path=state, auth_path=auth))

    def test_06_request_budget_overflow_refused(self):
        candidate = self.candidate_mutation(lambda body: body["network_caps"].update(requests=19))
        state, auth = self.active_fixture(candidate)
        self.assertEqual(self.policy(candidate_path=candidate, state_path=state, auth_path=auth)["decision"],
                         "REQUEST_BUDGET_OVERFLOW")

    def test_07_body_budget_overflow_refused(self):
        candidate = self.candidate_mutation(
            lambda body: body["network_caps"].update(application_body_bytes=17_544_939))
        state, auth = self.active_fixture(candidate)
        self.assertEqual(self.policy(candidate_path=candidate, state_path=state, auth_path=auth)["decision"],
                         "BODY_BUDGET_OVERFLOW")

    def test_08_concurrency_above_one_refused(self):
        candidate = self.candidate_mutation(lambda body: body["network_caps"].update(concurrency=2))
        state, auth = self.active_fixture(candidate)
        self.assertEqual(self.policy(candidate_path=candidate, state_path=state, auth_path=auth)["decision"],
                         "CONCURRENCY_LIMIT_EXCEEDED")

    def test_09_firewall_fields_refused(self):
        cases = {
            "astronomical_data_GETs": "astronomical_data_GETs_FORBIDDEN",
            "real_PHOTSYS_bytes_observed": "real_PHOTSYS_bytes_observed_FORBIDDEN",
            "BRICKNAME_values_observed": "BRICKNAME_values_observed_FORBIDDEN",
            "BRICKID_values_observed": "BRICKID_values_observed_FORBIDDEN",
            "ROOT_values_observed": "ROOT_values_observed_FORBIDDEN",
        }
        for key, expected in cases.items():
            with self.subTest(key=key):
                candidate = self.candidate_mutation(
                    lambda body, key=key: body["scientific_firewall"].update({key: 1}))
                state, auth = self.active_fixture(candidate)
                self.assertEqual(self.policy(candidate_path=candidate, state_path=state,
                                             auth_path=auth)["decision"], expected)

    def test_10_panel_p1_and_resolver_refused(self):
        cases = {"panel_v2": "PANEL_V2_SCOPE_FORBIDDEN",
                 "p1": "P1_SCOPE_FORBIDDEN", "resolver": "RESOLVER_CONSTRUCTION_FORBIDDEN"}
        for key, expected in cases.items():
            with self.subTest(key=key):
                candidate = self.candidate_mutation(
                    lambda body, key=key: body["forbidden_scope"].update({key: False}))
                state, auth = self.active_fixture(candidate)
                self.assertEqual(self.policy(candidate_path=candidate, state_path=state,
                                             auth_path=auth)["decision"], expected)

    def test_11_retry_and_resume_refused(self):
        candidate = self.candidate_mutation(lambda body: body["network_caps"].update(retries=1))
        state, auth = self.active_fixture(candidate)
        self.assertEqual(self.policy(candidate_path=candidate, state_path=state, auth_path=auth)["decision"],
                         "RETRY_NOT_FROZEN_ZERO")
        candidate = self.candidate_mutation(
            lambda body: body["execution_governance"].update(resume=True))
        state, auth = self.active_fixture(candidate)
        self.code("AUTONOMY_CANDIDATE_GOVERNANCE_INVALID",
                  lambda: self.policy(candidate_path=candidate, state_path=state, auth_path=auth))

    def test_12_force_push_and_wrong_branch_refused(self):
        candidate = self.candidate_mutation(lambda body: body["git_policy"].update(force_push=True))
        state, auth = self.active_fixture(candidate)
        self.assertEqual(self.policy(candidate_path=candidate, state_path=state, auth_path=auth)["decision"],
                         "FORCE_PUSH_FORBIDDEN")
        state, auth = self.active_fixture()
        self.assertEqual(self.policy(state_path=state, auth_path=auth, branch="main")["decision"],
                         "UNAUTHORIZED_BRANCH")

    def test_13_authority_class_expansion_refused(self):
        manifest = load_canonical_json(RANGE_MANIFEST_PATH)
        body = {key: item for key, item in manifest.items() if key != "sealed"}
        body["resources"][0]["evidence_class"] = "UNAUTHORIZED_EXTERNAL_AUTHORITY"
        manifest_path = self.write("manifest.json", sealed(body))
        candidate = self.candidate_mutation(lambda value: value.update(resource_manifest={
            "path": str(manifest_path.relative_to(PROJECT)), "sha256": file_sha256(manifest_path)}))
        state, auth = self.active_fixture(candidate)
        self.assertEqual(self.policy(candidate_path=candidate, state_path=state, auth_path=auth)["decision"],
                         "AUTHORITY_CLASS_EXPANSION")

    def test_13b_negative_capability_expansion_refused(self):
        candidate = self.candidate_mutation(
            lambda body: body["negative_capabilities"].update(generic_get=True))
        state, auth = self.active_fixture(candidate)
        self.assertEqual(self.policy(candidate_path=candidate, state_path=state, auth_path=auth)["decision"],
                         "NEGATIVE_CAPABILITY_EXPANSION")

    def test_14_valid_active_fixture_is_eligible(self):
        state, auth = self.active_fixture()
        result = self.policy(state_path=state, auth_path=auth)
        self.assertEqual(result["decision"], ELIGIBLE)

    def test_15_permit_binds_candidate_command_and_state(self):
        state, auth = self.active_fixture()
        permit = build_permit(candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
                              standing_authorization_path=auth,
                              issued_at_utc="2026-09-24T00:01:00Z")
        self.assertEqual(permit["candidate_sha256"], file_sha256(RANGE_CANDIDATE_PATH))
        self.assertEqual(permit["state_before_sha256"], file_sha256(state))
        self.assertEqual(permit["network_budget_reserved"], 1)

    def test_16_wrong_state_hash_invalidates_permit(self):
        state, auth = self.active_fixture()
        permit = self.write("permit.json", build_permit(
            candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
            standing_authorization_path=auth, issued_at_utc="2026-09-24T00:01:00Z"))
        value = load_canonical_json(state)
        body = {key: item for key, item in value.items() if key != "sealed"}
        body["sequence"] += 1
        state.write_bytes(canonical(sealed(body)) + b"\n")
        self.code("AUTONOMOUS_PERMIT_BINDING_MISMATCH", lambda: validate_permit(
            permit, candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
            standing_authorization_path=auth, consumption_directory=self.root / "consumed"))

    def test_17_permit_is_single_use(self):
        state, auth = self.active_fixture()
        permit = self.write("permit.json", build_permit(
            candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
            standing_authorization_path=auth, issued_at_utc="2026-09-24T00:01:00Z"))
        consumed = self.root / "consumed"
        consume_permit(permit, candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
                       standing_authorization_path=auth, consumption_directory=consumed,
                       consumed_at_utc="2026-09-24T00:02:00Z")
        self.code("AUTONOMOUS_PERMIT_ALREADY_CONSUMED", lambda: validate_permit(
            permit, candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
            standing_authorization_path=auth, consumption_directory=consumed))

    def test_18_state_transition_consumes_budget_and_invalidates_reuse(self):
        state, auth = self.active_fixture()
        permit = self.write("permit.json", build_permit(
            candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
            standing_authorization_path=auth, issued_at_utc="2026-09-24T00:01:00Z"))
        updated = transition_state(
            state_path=state, candidate_path=RANGE_CANDIDATE_PATH, permit_path=permit,
            terminal_sha256="a" * 64, terminal_state="SYNTHETIC_COMPLETE",
            request_delta=1, body_delta=0, ledger_directory=self.root / "ledger",
            transitioned_at_utc="2026-09-24T00:03:00Z", reason="SYNTHETIC_TEST")
        self.assertEqual(updated["sequence"], 1)
        self.assertEqual(updated["requests_remaining"], 17)
        self.code("AUTONOMOUS_PERMIT_BINDING_MISMATCH", lambda: validate_permit(
            permit, candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
            standing_authorization_path=auth, consumption_directory=self.root / "consumed"))

    def test_19_inactive_state_cannot_consume_synthetic_permit(self):
        auth = self.authorization()
        body = load_canonical_json(STATE_PATH)
        state = self.write("inactive-state.json", body)
        permit_body = {
            "authorization_basis": "STANDING_AUTONOMY_MANDATE_001",
            "body_budget_reserved": 0,
            "candidate_path": str(RANGE_CANDIDATE_PATH.relative_to(PROJECT)),
            "candidate_sha256": file_sha256(RANGE_CANDIDATE_PATH),
            "command_argv_sha256": load_canonical_json(RANGE_CANDIDATE_PATH)["command_argv_sha256"],
            "issued_at_utc": "2026-09-24T00:01:00Z",
            "mandate_sha256": file_sha256(MANDATE_PATH),
            "network_budget_reserved": 1,
            "permit_id": "OC3-AUTONOMOUS-PERMIT-SYNTHETIC",
            "permit_type": "AUTONOMOUS_EXECUTION_PERMIT",
            "resource_manifest_sha256": file_sha256(RANGE_MANIFEST_PATH),
            "resume": False,
            "retries_reserved": 0,
            "schema_version": "OC3_AUTONOMOUS_EXECUTION_PERMIT_001",
            "scientific_firewall": {key: 0 for key in FIREWALL_KEYS},
            "scope": "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_ONLY",
            "sequence": body["sequence"],
            "stage_id": "OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-RANGE-SIZE-PROBE-001",
            "standing_authorization_sha256": file_sha256(auth),
            "state_before_sha256": file_sha256(state),
        }
        permit = self.write("inactive-permit.json", sealed(permit_body))
        self.code(MANDATE_NOT_ACTIVE, lambda: validate_permit(
            permit, candidate_path=RANGE_CANDIDATE_PATH, state_path=state,
            standing_authorization_path=auth, consumption_directory=self.root / "consumed"))

    def test_20_compact_git_firewall_accepts_control_plane_and_rejects_risky_files(self):
        safe = self.root / "report.md"
        safe.write_text("compact evidence\n")
        result = audit_compact_paths([safe])
        self.assertEqual(result["state"], "GIT_STAGED_SIZE_FIREWALL_PASS")
        fits = self.root / "evidence.fits"
        fits.write_bytes(b"SIMPLE")
        self.code("GIT_SCIENTIFIC_OR_ARCHIVE_BODY_FORBIDDEN",
                  lambda: audit_compact_paths([fits]))
        secret = self.root / "report.txt"
        secret.write_text("gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123456789\n")
        self.code("GIT_SECRET_CONTENT_FORBIDDEN", lambda: audit_compact_paths([secret]))


if __name__ == "__main__":
    unittest.main()
