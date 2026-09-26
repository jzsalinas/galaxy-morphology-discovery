from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, validate_sealed
from oc3lib import source_metadata_recovery_governor_run004 as gov


class Run004PreparationTests(unittest.TestCase):
    def test_001_static_authorities_validate(self):
        gov.validate_static_authorities()

    def test_002_first_candidate_is_material_and_offline_prepared(self):
        candidate=gov.validate_first_candidate()
        self.assertEqual(candidate["action_kind"],"MATERIAL_SOURCE_METADATA_ACQUISITION")
        self.assertEqual(candidate["network_request_reservation"],5)
        self.assertEqual(candidate["active_adapter"],"query_manager_public_anonymous_v1")

    def test_003_waiting_state_is_inactive_and_fresh(self):
        state=gov.validate_state()
        self.assertEqual(state["state"],gov.STATE_WAITING)
        self.assertFalse(state["active"])
        self.assertEqual(state["execution_status"],"NOT_STARTED")
        self.assertEqual(state["self_repair_episodes"],0)
        self.assertEqual(state["permits_issued"],0)

    def test_004_no_final_authorization_exists(self):
        self.assertFalse(gov.STANDING_AUTHORIZATION.exists())

    def test_005_no_run004_runtime_namespace_exists(self):
        self.assertFalse(gov.LEDGER_ROOT.exists())
        self.assertFalse(gov.PERMIT_ROOT.exists())
        self.assertFalse((PROJECT/"oc3/source_metadata_autonomous_recovery_run_004").exists())

    def test_006_budgets_are_frozen_and_unspent(self):
        state=gov.validate_state()
        self.assertEqual((state["technical_requests_remaining"],state["technical_body_bytes_remaining"]),(8,2_097_152))
        self.assertEqual((state["material_requests_remaining"],state["material_body_bytes_remaining"]),(5,67_108_864))
        self.assertEqual(state["network_requests_attributable"],0)
        self.assertEqual(state["material_actions_attributable"],0)

    def test_007_run003_runtime_identity_is_not_reused(self):
        candidate=gov.validate_first_candidate()
        joined="\n".join(candidate["command_argv"]+candidate["worker_argv"]+candidate["mission_execution_argv"])
        self.assertNotIn("RUN-003",joined)
        self.assertNotIn("run_003",joined)
        self.assertNotIn("STATE_003",joined)

    def test_008_inherited_evidence_is_read_only_and_zero_science(self):
        authority=validate_sealed(load_canonical_json(gov.INHERITED_TRANSPORT_AUTHORITY))
        self.assertEqual(authority["source_run_id"],"OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-003")
        self.assertEqual(authority["network_requests_charged_to_run_004"],0)
        self.assertEqual(authority["scientific_rows_accepted"],0)
        self.assertEqual(authority["material_actions"],0)
        for item in authority["evidence"]:
            self.assertEqual(file_sha256(PROJECT/item["path"]),item["sha256"])

    def test_009_exact_agentic_command_identity(self):
        candidate=gov.validate_first_candidate()
        self.assertEqual(candidate["mission_execution_argv_sha256"],
            hashlib.sha256(canonical(candidate["mission_execution_argv"])).hexdigest())
        self.assertIn("oc3_source_metadata_recovery_mission_runner_run004.py",candidate["mission_execution_argv"][1])

    def test_010_drift_matrix_is_all_zero(self):
        drift=validate_sealed(load_canonical_json(gov.DRIFT_MATRIX))
        for field in ("scientific_semantic_drift","observational_contract_drift",
                "provider_resource_drift","rights_drift","resource_scope_drift",
                "budget_drift","acceptance_criteria_drift"):
            self.assertEqual(drift[field],0)

    def test_011_run003_terminal_state_remains_exact(self):
        closure=validate_sealed(load_canonical_json(gov.RUN_003_CLOSURE))
        self.assertEqual(closure["terminal_state"]["sha256"],
            "d53674b9199546c016e28440a997de854d8f66b2ba4b8df63ac29d39a51d6a88")
        self.assertEqual(closure["stop_reason"],"TECHNICAL_PATCH_GIT_DIFF_STATE_PATH_BINDING_CONFLICT")

    def test_012_mutable_surface_was_not_broadened(self):
        surface=validate_sealed(load_canonical_json(gov.MUTABLE_SURFACE))
        self.assertEqual(surface["allowed_path_prefixes"],[
            "oc3/recovery_adapters/source_metadata/","oc3/recovery_tests/source_metadata/"])


if __name__ == "__main__":
    unittest.main()
