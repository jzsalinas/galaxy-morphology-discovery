from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import PROJECT, file_sha256, sealed
from oc3lib.source_metadata_path_identity import PathIdentityError, canonical_path_identity
from oc3lib.source_metadata_self_repair import (
    ALLOW, STOP, build_replacement_authorization_binding,
    classify_self_repair, prospective_execution_binding,
    implementation_aggregate, seal_candidate_execution,
    validate_candidate_execution_binding,
)


class PathIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=PROJECT / "oc3")
        self.root = Path(self.temp.name)
        self.candidate = self.root / "nested" / "candidate.json"
        self.candidate.parent.mkdir()
        self.candidate.write_text("{}\n")

    def tearDown(self): self.temp.cleanup()

    def test_absolute_relative_dot_parent_and_lexical_aliases_are_equal(self):
        rel = self.candidate.relative_to(PROJECT)
        forms = [
            canonical_path_identity(self.candidate, project_root=PROJECT, must_exist=True),
            canonical_path_identity(rel, project_root=PROJECT, cwd=PROJECT, must_exist=True),
            canonical_path_identity(Path(".") / rel, project_root=PROJECT, cwd=PROJECT, must_exist=True),
            canonical_path_identity(Path("oc3") / ".." / rel, project_root=PROJECT, cwd=PROJECT, must_exist=True),
            canonical_path_identity(Path("nested") / "candidate.json", project_root=PROJECT,
                cwd=self.root, must_exist=True),
        ]
        self.assertTrue(all(item == forms[0] for item in forms))

    def test_symlink_and_outside_project_fail_closed(self):
        link = self.root / "alias.json"
        link.symlink_to(self.candidate)
        with self.assertRaisesRegex(PathIdentityError, "SYMLINK_PATH_AUTHORITY_AMBIGUITY"):
            canonical_path_identity(link, project_root=PROJECT, must_exist=True)
        with self.assertRaisesRegex(PathIdentityError, "PATH_OUTSIDE_CANONICAL_PROJECT_ROOT"):
            canonical_path_identity(Path("/tmp/outside.json"), project_root=PROJECT)

    def test_creator_and_validator_share_identity_across_different_cwds(self):
        paths = {
            "candidate_path": self.candidate,
            "permit_path": self.root / "permit.json",
            "authorization_path": self.root / "authorization.json",
            "state_path": self.root / "state.json",
            "output_path": self.root / "output",
            "capability_path": self.root / "output" / "capability.json",
        }
        binding = prospective_execution_binding(project_root=PROJECT, cwd=PROJECT, **paths)
        candidate = seal_candidate_execution(payload={"implementation_aggregate":"a"*64},
            binding=binding, supervisor_prefix=["python", "supervisor.py"],
            worker_prefix=["python", "worker.py"])
        os.chdir(self.root)
        try:
            validate_candidate_execution_binding(candidate=candidate,
                actual_candidate_path=Path("nested/candidate.json"), project_root=PROJECT, cwd=self.root)
        finally:
            os.chdir(PROJECT)
        tampered = deepcopy(candidate)
        tampered["canonical_execution_binding"] = deepcopy(binding)
        tampered["canonical_execution_binding"]["argv_paths"]["authorization"] = "/tmp/other.json"
        tampered["command_argv"][tampered["command_argv"].index("--standing-authorization") + 1] = "/tmp/other.json"
        tampered["worker_argv"][tampered["worker_argv"].index("--standing-authorization") + 1] = "/tmp/other.json"
        with self.assertRaisesRegex(ValueError, "CANONICAL_EXECUTION_BINDING_INVALID"):
            validate_candidate_execution_binding(candidate=tampered,
                actual_candidate_path=self.candidate, project_root=PROJECT, cwd=PROJECT)


class SelfRepairPolicyTests(unittest.TestCase):
    prefixes = ("oc3/oc3lib/", "oc3/tests/")

    @staticmethod
    def proposal(**updates):
        value = {
            "acceptance_criteria_drift":0,
            "changed_paths":["oc3/oc3lib/source_metadata_path_identity.py"],
            "defect_class":"PATH_CANONICALIZATION_MISMATCH",
            "deterministic_diagnosis":True,
            "historical_evidence_mutation":False,
            "intended_behavior_unambiguous":True,
            "local_implementation_only":True,
            "multiple_material_fixes_plausible":False,
            "non_scientific":True,
            "offline_testable":True,
            "observational_contract_drift":0,
            "permission_drift":0,
            "prospective_artifacts_only":True,
            "provider_resource_drift":0,
            "resource_scope_drift":0,
            "rights_drift":0,
            "schema_version":"OC3_AUTONOMOUS_TECHNICAL_SELF_REPAIR_PROPOSAL_001",
            "scientific_semantic_drift":0,
            "standing_mandate_allows_rebinding":True,
            "standing_mandate_allows_self_repair":True,
        }
        value.update(updates); return value

    def classify(self, proposal=None, history=()):
        return classify_self_repair(proposal or self.proposal(), prior_defect_classes=history,
            authorized_implementation_prefixes=self.prefixes)

    def test_deterministic_local_defect_is_eligible(self):
        self.assertEqual(self.classify()["decision"], ALLOW)

    def test_scientific_semantics_caps_provider_rights_and_ambiguity_are_rejected(self):
        cases = {
            "science":{"scientific_semantic_drift":1},
            "cap":{"resource_scope_drift":1},
            "provider":{"provider_resource_drift":1},
            "rights":{"rights_drift":1},
            "ambiguity":{"multiple_material_fixes_plausible":True},
        }
        for name, update in cases.items():
            with self.subTest(name=name):
                self.assertEqual(self.classify(self.proposal(**update))["decision"], STOP)

    def test_repeat_and_episode_limits_fail_closed(self):
        self.assertEqual(self.classify(history=("PATH_CANONICALIZATION_MISMATCH",))["reason"],
            "SELF_REPAIR_DEFECT_CLASS_REPEATED")
        self.assertEqual(self.classify(history=("A", "B"))["reason"],
            "SELF_REPAIR_EPISODE_LIMIT_REACHED")

    def test_lexical_alias_and_governance_path_are_outside_repair_surface(self):
        for path in ("oc3/oc3lib/../INPUTS/authority.json",
                     "OC3_SOURCE_METADATA_AUTONOMOUS_TECHNICAL_SELF_REPAIR_AMENDMENT_001.md"):
            with self.subTest(path=path):
                result=self.classify(self.proposal(changed_paths=[path]))
                self.assertEqual(result["reason"],"SELF_REPAIR_OUTSIDE_AUTHORIZED_IMPLEMENTATION_SURFACE")
        recursive=self.classify(self.proposal(changed_paths=["oc3/oc3lib/source_metadata_self_repair.py"]))
        self.assertEqual(recursive["reason"],"RECURSIVE_SELF_REPAIR_POLICY_MUTATION_FORBIDDEN")

    def test_pending_candidate_and_old_authorization_cannot_be_reused(self):
        with tempfile.TemporaryDirectory(dir=PROJECT / "oc3") as directory:
            root = Path(directory); candidate = root / "candidate.json"
            candidate.write_bytes(canonical(sealed({"implementation_aggregate":"b" * 64}))+b"\n")
            binding = build_replacement_authorization_binding(
                old_authorization_sha256="a"*64, old_candidate_sha256="c"*64,
                new_candidate_path=candidate, new_implementation_aggregate="b"*64,
                prior_implementation_aggregate="d"*64, mandate_sha256="e"*64,
                project_root=PROJECT, cwd=PROJECT)
            self.assertEqual(binding["new_candidate"]["sha256"], file_sha256(candidate))
            self.assertEqual(binding["new_implementation_aggregate"], "b"*64)
            with self.assertRaisesRegex(ValueError, "IDENTITY_UNCHANGED"):
                build_replacement_authorization_binding(
                    old_authorization_sha256="a"*64, old_candidate_sha256="c"*64,
                    new_candidate_path=candidate, new_implementation_aggregate="d"*64,
                    prior_implementation_aggregate="d"*64, mandate_sha256="e"*64,
                    project_root=PROJECT, cwd=PROJECT)
            with self.assertRaisesRegex(ValueError, "CANDIDATE_REUSE_FORBIDDEN"):
                build_replacement_authorization_binding(
                    old_authorization_sha256="a"*64, old_candidate_sha256=file_sha256(candidate),
                    new_candidate_path=candidate, new_implementation_aggregate="b"*64,
                    prior_implementation_aggregate="d"*64, mandate_sha256="e"*64,
                    project_root=PROJECT, cwd=PROJECT)

    def test_new_aggregate_changes_and_run_002_evidence_remains_exact(self):
        historical = {
            PROJECT/"oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_002.json":
                "0b727b876091fa9508b50f651457308e22c6fd1024a9c248328e0ed6f0bb3250",
            PROJECT/"oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_002.json":
                "1c8d54fe366dbbce8af22bfa0b684d9e014c5f052fae7f307005ccbce7587bd4",
            PROJECT/"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_LEDGER/CONTROL_PLANE_CONTRADICTION.json":
                "a5cdaa5d7fd24534ef7a30d661253cf1bb92eba954347d49b8a4fa92db915e87",
            PROJECT/"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_LEDGER/MISSION_FINAL_REPORT.json":
                "6d9abc269c8d080262a2e40271c067766a5dc848474edcdbf4e54ac30a08854b",
        }
        self.assertEqual({path:file_sha256(path) for path in historical},historical)
        with tempfile.TemporaryDirectory(dir=PROJECT/"oc3") as directory:
            target=Path(directory)/"implementation.py"; target.write_text("before\n")
            before=implementation_aggregate([target],project_root=PROJECT)
            target.write_text("after\n")
            after=implementation_aggregate([target],project_root=PROJECT)
            self.assertNotEqual(before,after)


if __name__ == "__main__": unittest.main()
