from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from oc3lib.autonomous_recovery_envelope import RecoveryEnvelopeError
from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import PROJECT, file_sha256, load_canonical_json
from oc3lib import source_metadata_recovery_governor_run003 as gov
from oc3lib.source_metadata_path_identity import PathIdentityError, canonical_path_identity
from oc3lib.source_metadata_self_repair import validate_candidate_execution_binding


class Run003PreparationTests(unittest.TestCase):
    def test_001_static_policy_core_validates(self):
        values = gov.validate_static_authorities()
        self.assertEqual(values["policy"]["run_id"], gov.RUN_ID)

    def test_002_first_candidate_validates(self):
        value = gov.validate_first_candidate()
        self.assertEqual(value["action_kind"], "OFFICIAL_SERVICE_DOCUMENTARY_PROBE")
        self.assertEqual(value["trigger_failure_class"], "TECHNICAL_DIAGNOSTIC_CLASSIFIED")

    def test_003_waiting_state_validates_and_is_inactive(self):
        state = gov.validate_state()
        self.assertEqual(state["state"], gov.STATE_WAITING)
        self.assertFalse(state["active"])
        self.assertIsNone(state["standing_authorization"])
        self.assertEqual(state["execution_status"], "NOT_STARTED")

    def test_004_validated_self_repair_aggregate_is_exact(self):
        self.assertEqual(gov.implementation_aggregate(),
            "d6c4680b7e861baffce27dee14a4270c1304b1e3c841eb6c9977502b2f7d0348")

    def test_005_self_repair_evidence_hashes_are_exact(self):
        expected = {
            gov.SELF_REPAIR_AMENDMENT: "5935c68cdd215f4460175210dbd145aae2105fbd46d5d744c776f46ba75cf271",
            gov.SELF_REPAIR_REPORT: "12ecc6c0e8cc1848451b638967880fb5fa0c6bab3a0864ed8f362a0025f86281",
            gov.SELF_REPAIR_REPLAY: "3ec61759be14e44b7827207d13976074172ccd7907d5fa2210bf2fb5b9299002",
        }
        for path, digest in expected.items():
            self.assertEqual(file_sha256(path), digest)

    def test_006_run002_closure_preserves_exact_history(self):
        closure = load_canonical_json(gov.RUN_002_CLOSURE)
        self.assertEqual(closure["authorization_sha256"],
            "0b727b876091fa9508b50f651457308e22c6fd1024a9c248328e0ed6f0bb3250")
        self.assertEqual(closure["terminal_state_sha256"],
            "1c8d54fe366dbbce8af22bfa0b684d9e014c5f052fae7f307005ccbce7587bd4")
        self.assertEqual(closure["g01_classification"], "CSV_BODY_WITH_WRONG_CONTENT_TYPE")
        self.assertEqual((closure["network_requests"], closure["body_bytes"]), (1, 2124))
        self.assertEqual((closure["scientific_rows_accepted"], closure["source_values_accepted"]), (0, 0))

    def test_007_candidate_uses_only_run003_operational_namespace(self):
        candidate = load_canonical_json(gov.FIRST_CANDIDATE)
        serialized = canonical(candidate).decode()
        self.assertIn("RUN-003", serialized)
        for forbidden in ("RUN_001_PERMITS", "RUN_002_PERMITS",
                "source_metadata_autonomous_recovery_run_002/OC3-SOURCE-METADATA-RECOVERY-RUN-003"):
            self.assertNotIn(forbidden, serialized)

    def test_008_canonical_candidate_identity_is_cwd_independent(self):
        candidate = load_canonical_json(gov.FIRST_CANDIDATE)
        for cwd in (PROJECT, PROJECT / "oc3", PROJECT / "oc3/tests"):
            validate_candidate_execution_binding(candidate=candidate,
                actual_candidate_path=gov.FIRST_CANDIDATE, project_root=PROJECT, cwd=cwd)

    def test_009_repository_escape_fails_closed(self):
        with self.assertRaisesRegex(PathIdentityError, "PATH_OUTSIDE_CANONICAL_PROJECT_ROOT"):
            canonical_path_identity("../../outside", project_root=PROJECT, cwd=PROJECT)

    def test_010_symlink_alias_fails_closed(self):
        with tempfile.TemporaryDirectory(dir=PROJECT / "oc3") as directory:
            root = Path(directory); target = root / "target"; target.write_text("x")
            alias = root / "alias"; alias.symlink_to(target)
            with self.assertRaisesRegex(PathIdentityError, "SYMLINK_PATH_AUTHORITY_AMBIGUITY"):
                canonical_path_identity(alias, project_root=PROJECT)

    def test_011_candidate_binds_mission_local_budget(self):
        value = load_canonical_json(gov.FIRST_CANDIDATE)
        self.assertEqual(value["remaining_budgets"], {"technical_requests": 8,
            "technical_body_bytes": 2_097_152, "material_requests": 5,
            "material_body_bytes": 67_108_864})
        self.assertEqual(value["budget_accounting"]["counter_scope"], "MISSION_LOCAL_RUN_003")
        self.assertIsNone(value["budget_accounting"]["cross_mission_global_cap"])

    def test_012_candidate_binds_self_repair_limits(self):
        policy = load_canonical_json(gov.FIRST_CANDIDATE)["self_repair_authority"]
        self.assertEqual(policy["maximum_episodes_per_mission"], 2)
        self.assertEqual(policy["maximum_episodes_per_defect_class"], 1)
        self.assertTrue(policy["post_repair_fresh_artifacts_required"])

    def test_013_candidate_has_no_human_authorization_field(self):
        candidate = load_canonical_json(gov.FIRST_CANDIDATE)
        self.assertNotIn("authorized", candidate)
        self.assertNotIn("authorized_by", candidate)
        self.assertNotIn("authorized_at_utc", candidate)

    def test_014_exact_proposed_runner_identity_is_bound(self):
        candidate = load_canonical_json(gov.FIRST_CANDIDATE)
        argv = candidate["mission_execution_argv"]
        self.assertEqual(argv, [str(PROJECT / "oc3/.venv/bin/python"),
            str(PROJECT / "oc3/oc3_source_metadata_recovery_mission_runner_run003.py"),
            "--run-mission", "--state", str(gov.STATE),
            "--standing-authorization", str(gov.STANDING_AUTHORIZATION)])
        self.assertEqual(hashlib.sha256(canonical(argv)).hexdigest(),
            candidate["mission_execution_argv_sha256"])

    def test_015_transport_is_unreachable_without_authorization(self):
        self.assertFalse(gov.STANDING_AUTHORIZATION.exists())
        with self.assertRaisesRegex(RecoveryEnvelopeError, "RECOVERY_STANDING_AUTHORIZATION_INVALID"):
            gov.validate_standing_authorization(gov.STANDING_AUTHORIZATION, state_path=gov.STATE)

    def test_016_no_run003_execution_namespaces_exist(self):
        for path in (gov.LEDGER_ROOT, gov.PERMIT_ROOT,
                PROJECT / "oc3/source_metadata_autonomous_recovery_run_003"):
            self.assertFalse(path.exists())

    def test_017_candidate_validation_records_zero_execution(self):
        receipt = load_canonical_json(gov.CANDIDATE_VALIDATION)
        self.assertEqual(receipt["validation_result"], "PASS")
        self.assertEqual(receipt["network_requests"], 0)
        self.assertEqual(receipt["material_actions"], 0)
        self.assertEqual(receipt["run_003_execution"], "NOT_STARTED")

    def test_018_waiting_state_binds_candidate_validation(self):
        state = load_canonical_json(gov.STATE)
        self.assertEqual(state["candidate_validation"], gov.binding(gov.CANDIDATE_VALIDATION))
        self.assertEqual(state["network_requests_attributable"], 0)
        self.assertEqual(state["material_actions_attributable"], 0)

    def test_019_policy_manifest_binds_control_plane(self):
        manifest = load_canonical_json(gov.POLICY_MANIFEST)
        self.assertEqual(manifest["control_plane_aggregate"], gov.control_plane_aggregate())
        self.assertEqual(manifest["implementation_aggregate"], gov.implementation_aggregate())

    def test_020_run002_operational_hashes_remain_exact(self):
        expected = {
            PROJECT / "oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_002.json":
                "0b727b876091fa9508b50f651457308e22c6fd1024a9c248328e0ed6f0bb3250",
            PROJECT / "oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_002.json":
                "1c8d54fe366dbbce8af22bfa0b684d9e014c5f052fae7f307005ccbce7587bd4",
            PROJECT / "oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_LEDGER/CONTROL_PLANE_CONTRADICTION.json":
                "a5cdaa5d7fd24534ef7a30d661253cf1bb92eba954347d49b8a4fa92db915e87",
            PROJECT / "oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_LEDGER/MISSION_FINAL_REPORT.json":
                "6d9abc269c8d080262a2e40271c067766a5dc848474edcdbf4e54ac30a08854b",
        }
        for path, digest in expected.items():
            self.assertEqual(file_sha256(path), digest)


if __name__ == "__main__":
    unittest.main()
