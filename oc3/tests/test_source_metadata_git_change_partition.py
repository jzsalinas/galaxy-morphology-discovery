from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from oc3lib.autonomous_recovery_envelope import RecoveryEnvelopeError
from oc3lib.cross_observer_grouping import file_sha256, sealed
from oc3lib.source_metadata_git_change_partition import (
    RuntimeStateRequirement, partition_changed_paths, validate_partition,
)


class GitChangePartitionTests(unittest.TestCase):
    RUN_ID = "OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-004"
    STATE = "oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_004.json"
    PREFIXES = ("oc3/recovery_adapters/source_metadata/",
        "oc3/recovery_tests/source_metadata/")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.auth = self._write("oc3/AUTH.json", sealed({"authorized": True}))
        self.terminal = self._write("oc3/runtime/TERMINAL.json", sealed({"run_id": self.RUN_ID}))
        self.request = self._write("oc3/ledger/REQUEST.json", sealed({"run_id": self.RUN_ID,
            "parent_action_terminal":self._binding(self.terminal),"recovery_generation":1}))
        self.state_path = self.root / self.STATE
        self._write_state()
        self.requirement = RuntimeStateRequirement(path=self.STATE, run_id=self.RUN_ID,
            schema_version="OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_004",
            standing_authorization=self._binding(self.auth))

    def tearDown(self):
        self.temp.cleanup()

    def _write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        return path

    def _binding(self, path):
        return {"path": path.relative_to(self.root).as_posix(), "sha256": file_sha256(path)}

    def _write_state(self, **changes):
        value = {
            "active": True,
            "agentic_repair_request": self._binding(self.request),
            "current_stage": "AWAITING_AGENTIC_TECHNICAL_REPAIR",
            "registered_pending_action": None,
            "recovery_generation": 0,
            "run_id": self.RUN_ID,
            "schema_version": "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_004",
            "sequence": 3,
            "standing_authorization": self._binding(self.auth),
            "state": "ACTIVE",
            "last_action_terminal": self._binding(self.terminal),
        }
        value.update(changes)
        self._write(self.STATE, sealed(value))

    def _partition(self, paths, *, prefixes=None, requirement=None):
        return partition_changed_paths(base_commit="a" * 40,
            all_tracked_changes=sorted(paths), mutable_prefixes=prefixes or self.PREFIXES,
            project_root=self.root,
            runtime_requirement=self.requirement if requirement is None else requirement)

    def test_01_allowed_patch_and_legitimate_state_pass(self):
        patch = self.PREFIXES[0] + "adapter.py"
        result = self._partition([patch, self.STATE])
        self.assertEqual(result["mutable_patch_changes"], [patch])
        self.assertEqual([r["path"] for r in result["authorized_runtime_changes"]], [self.STATE])
        self.assertEqual(result["forbidden_changes"], [])

    def test_02_state_is_not_inserted_into_patch_manifest(self):
        result = self._partition([self.STATE])
        self.assertEqual(result["mutable_patch_changes"], [])
        self.assertEqual(len(result["authorized_runtime_changes"]), 1)

    def test_03_state_manually_inserted_into_patch_manifest_fails(self):
        result = dict(self._partition([self.STATE])); result.pop("sealed")
        result["authorized_runtime_changes"] = []
        result["mutable_patch_changes"] = [self.STATE]
        result = sealed(result)
        with self.assertRaises(RecoveryEnvelopeError):
            validate_partition(result, expected_base="a" * 40, expected_mutable_paths=[])

    def test_04_tampered_state_fails(self):
        self.state_path.write_text(self.state_path.read_text().replace('"sequence":3', '"sequence":4'))
        with self.assertRaisesRegex(RecoveryEnvelopeError, "AUTHORIZED_RUNTIME_STATE_INVALID"):
            self._partition([self.STATE])

    def test_05_wrong_run_id_fails(self):
        self._write_state(run_id="OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-003")
        with self.assertRaisesRegex(RecoveryEnvelopeError, "AUTHORIZED_RUNTIME_STATE_INVALID"):
            self._partition([self.STATE])

    def test_06_predecessor_state_is_forbidden(self):
        predecessor = "oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_003.json"
        result = self._partition([predecessor])
        self.assertEqual(result["forbidden_changes"], [predecessor])

    def test_07_arbitrary_tracked_file_is_forbidden(self):
        result = self._partition(["README.md"])
        self.assertEqual(result["forbidden_changes"], ["README.md"])

    def test_08_policy_core_change_is_forbidden(self):
        result = self._partition(["OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_POLICY_CORE_004.md"])
        self.assertTrue(result["forbidden_changes"])

    def test_09_scientific_invariant_change_is_forbidden(self):
        path = "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_SCIENTIFIC_INVARIANTS_001.json"
        self.assertEqual(self._partition([path])["forbidden_changes"], [path])

    def test_10_recovery_graph_change_is_forbidden(self):
        path = "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_GRAPH_001.json"
        self.assertEqual(self._partition([path])["forbidden_changes"], [path])

    def test_11_control_plane_change_is_forbidden(self):
        path = "oc3/oc3lib/source_metadata_recovery_governor_run004.py"
        self.assertEqual(self._partition([path])["forbidden_changes"], [path])

    def test_12_allowed_patch_plus_hidden_forbidden_change_fails_validation(self):
        patch = self.PREFIXES[1] + "test_adapter.py"
        result = self._partition([patch, "secret.txt"])
        with self.assertRaises(RecoveryEnvelopeError):
            validate_partition(result, expected_base="a" * 40, expected_mutable_paths=[patch])

    def test_13_no_path_disappears_from_partition(self):
        patch = self.PREFIXES[0] + "adapter.py"
        forbidden = "arbitrary.txt"
        result = self._partition([patch, self.STATE, forbidden])
        union = (set(result["mutable_patch_changes"]) |
            {r["path"] for r in result["authorized_runtime_changes"]} |
            set(result["forbidden_changes"]))
        self.assertEqual(union, set(result["all_tracked_changes"]))

    def test_14_same_path_cannot_belong_to_two_classes(self):
        overlapping = RuntimeStateRequirement(path=self.PREFIXES[0] + "state.json",
            run_id=self.RUN_ID, schema_version="X", standing_authorization=self._binding(self.auth))
        with self.assertRaisesRegex(RecoveryEnvelopeError, "GIT_CHANGE_PARTITION_OVERLAP"):
            self._partition([overlapping.path], requirement=overlapping)

    def test_15_clean_mutable_patch_without_runtime_passes(self):
        patch = self.PREFIXES[1] + "test_only.py"
        result = self._partition([patch])
        validate_partition(result, expected_base="a" * 40, expected_mutable_paths=[patch])

    def test_runtime_wrong_authorization_binding_fails(self):
        self._write_state(standing_authorization={"path": "x", "sha256": "0" * 64})
        with self.assertRaisesRegex(RecoveryEnvelopeError, "AUTHORIZED_RUNTIME_STATE_INVALID"):
            self._partition([self.STATE])

    def test_runtime_broken_history_binding_fails(self):
        self._write_state(agentic_repair_request={"path": "missing", "sha256": "0" * 64})
        with self.assertRaisesRegex(RecoveryEnvelopeError, "AUTHORIZED_RUNTIME_LIFECYCLE_INVALID"):
            self._partition([self.STATE])

    def test_registered_action_runtime_transition_passes_at_execution_boundary(self):
        candidate=self._write("oc3/ledger/CANDIDATE.json",sealed({"run_id":self.RUN_ID}))
        self._write_state(current_stage="AWAITING_NEXT_ACTION_REGISTRATION",
            registered_pending_action=self._binding(candidate))
        requirement=RuntimeStateRequirement(path=self.STATE,run_id=self.RUN_ID,
            schema_version="OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_004",
            standing_authorization=self._binding(self.auth),
            allowed_stages=("AWAITING_NEXT_ACTION_REGISTRATION",),pending_action_required=True)
        result=self._partition([self.STATE],requirement=requirement)
        self.assertEqual(result["authorized_runtime_changes"][0]["path"],self.STATE)


if __name__ == "__main__":
    unittest.main()
