"""Prospective bounded autonomous technical self-repair policy primitives.

This module is offline and has no transport dependency.  It does not grant a
standing authorization; a future mandate must explicitly opt into the policy.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from pathlib import PurePosixPath
from typing import Mapping, Sequence

from .core import canonical
from .cross_observer_grouping import file_sha256, sealed
from .source_metadata_path_identity import canonical_path_identity


ALLOW = "AUTONOMOUS_TECHNICAL_SELF_REPAIR"
STOP = "STOP_REQUIRES_HUMAN"
MAX_SELF_REPAIR_EPISODES = 2
MAX_SAME_DEFECT_CLASS = 1
_SELF_REPAIR_POLICY_PATHS = {
    "OC3_SOURCE_METADATA_AUTONOMOUS_TECHNICAL_SELF_REPAIR_AMENDMENT_001.md",
    "oc3/oc3lib/source_metadata_self_repair.py",
}

_DRIFT_FIELDS = (
    "scientific_semantic_drift",
    "observational_contract_drift",
    "provider_resource_drift",
    "rights_drift",
    "resource_scope_drift",
    "permission_drift",
    "acceptance_criteria_drift",
)
_REQUIRED = {
    "acceptance_criteria_drift", "changed_paths", "defect_class",
    "deterministic_diagnosis", "historical_evidence_mutation",
    "intended_behavior_unambiguous", "local_implementation_only",
    "multiple_material_fixes_plausible", "non_scientific", "offline_testable",
    "observational_contract_drift", "permission_drift",
    "prospective_artifacts_only", "provider_resource_drift", "resource_scope_drift",
    "rights_drift", "schema_version", "scientific_semantic_drift",
    "standing_mandate_allows_self_repair", "standing_mandate_allows_rebinding",
}


def classify_self_repair(
    proposal: Mapping[str, object],
    *,
    prior_defect_classes: Sequence[str],
    authorized_implementation_prefixes: Sequence[str],
) -> dict[str, object]:
    """Apply the closed eligibility and finite-loop policy."""
    if set(proposal) != _REQUIRED or proposal.get("schema_version") != "OC3_AUTONOMOUS_TECHNICAL_SELF_REPAIR_PROPOSAL_001":
        return {"decision": STOP, "reason": "SELF_REPAIR_PROPOSAL_SCHEMA_INVALID"}
    defect = proposal.get("defect_class")
    changed = proposal.get("changed_paths")
    if not isinstance(defect, str) or not defect or not isinstance(changed, list) or not changed:
        return {"decision": STOP, "reason": "SELF_REPAIR_PROPOSAL_SCHEMA_INVALID"}
    if len(prior_defect_classes) >= MAX_SELF_REPAIR_EPISODES:
        return {"decision": STOP, "reason": "SELF_REPAIR_EPISODE_LIMIT_REACHED"}
    if prior_defect_classes.count(defect) >= MAX_SAME_DEFECT_CLASS:
        return {"decision": STOP, "reason": "SELF_REPAIR_DEFECT_CLASS_REPEATED"}
    def canonical_changed_path(path: object) -> bool:
        if not isinstance(path, str) or not path or Path(path).is_absolute():
            return False
        pure = PurePosixPath(path)
        return (pure.as_posix() == path and "." not in pure.parts and ".." not in pure.parts and
            any(path.startswith(prefix) for prefix in authorized_implementation_prefixes))
    if not authorized_implementation_prefixes or any(not canonical_changed_path(path) for path in changed):
        return {"decision": STOP, "reason": "SELF_REPAIR_OUTSIDE_AUTHORIZED_IMPLEMENTATION_SURFACE"}
    if any(path in _SELF_REPAIR_POLICY_PATHS for path in changed):
        return {"decision": STOP, "reason": "RECURSIVE_SELF_REPAIR_POLICY_MUTATION_FORBIDDEN"}
    required_true = (
        "local_implementation_only", "deterministic_diagnosis",
        "intended_behavior_unambiguous", "non_scientific", "offline_testable",
        "prospective_artifacts_only", "standing_mandate_allows_self_repair",
        "standing_mandate_allows_rebinding",
    )
    if any(proposal.get(field) is not True for field in required_true):
        return {"decision": STOP, "reason": "SELF_REPAIR_ELIGIBILITY_NOT_PROVEN"}
    if proposal.get("multiple_material_fixes_plausible") is not False:
        return {"decision": STOP, "reason": "SELF_REPAIR_MATERIALLY_AMBIGUOUS"}
    if proposal.get("historical_evidence_mutation") is not False:
        return {"decision": STOP, "reason": "HISTORICAL_EVIDENCE_MUTATION_FORBIDDEN"}
    for field in _DRIFT_FIELDS:
        if proposal.get(field) != 0:
            return {"decision": STOP, "reason": f"{field.upper()}_FORBIDDEN"}
    return {
        "decision": ALLOW,
        "defect_class": defect,
        "episode_number": len(prior_defect_classes) + 1,
        "reason": "ALL_CLOSED_SELF_REPAIR_ELIGIBILITY_GATES_PASSED",
    }


def prospective_execution_binding(
    *,
    project_root: Path,
    cwd: Path,
    candidate_path: Path,
    permit_path: Path,
    authorization_path: Path,
    state_path: Path,
    output_path: Path,
    capability_path: Path,
) -> dict[str, object]:
    """Build candidate/sealing/authorization/runner paths from one primitive."""
    identities = {
        name: canonical_path_identity(path, project_root=project_root, cwd=cwd)
        for name, path in {
            "candidate": candidate_path,
            "permit": permit_path,
            "authorization": authorization_path,
            "state": state_path,
            "output": output_path,
            "capability": capability_path,
        }.items()
    }
    return {
        "artifact_paths": {name: identity.project_relative for name, identity in identities.items()},
        "argv_paths": {name: identity.absolute for name, identity in identities.items()},
        "schema_version": "OC3_SOURCE_METADATA_CANONICAL_EXECUTION_BINDING_001",
    }


def seal_candidate_execution(
    *, payload: Mapping[str, object], binding: Mapping[str, object],
    supervisor_prefix: Sequence[str], worker_prefix: Sequence[str],
) -> dict[str, object]:
    """Seal a candidate using only canonical paths produced by the primitive."""
    artifact_paths = binding.get("artifact_paths")
    argv_paths = binding.get("argv_paths")
    if not isinstance(artifact_paths, Mapping) or not isinstance(argv_paths, Mapping):
        raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")
    common = [
        "--candidate", argv_paths["candidate"], "--permit", argv_paths["permit"],
        "--standing-authorization", argv_paths["authorization"],
        "--state", argv_paths["state"], "--output", argv_paths["output"],
    ]
    command = [*supervisor_prefix, *common]
    worker = [*worker_prefix, *common, "--execution-capability", argv_paths["capability"]]
    return sealed({**payload,
        "candidate_path": artifact_paths["candidate"],
        "canonical_execution_binding": dict(binding),
        "command_argv": command,
        "command_argv_sha256": hashlib.sha256(canonical(command)).hexdigest(),
        "worker_argv": worker,
        "worker_argv_sha256": hashlib.sha256(canonical(worker)).hexdigest(),
    })


def validate_candidate_execution_binding(
    *, candidate: Mapping[str, object], actual_candidate_path: Path,
    project_root: Path, cwd: Path,
) -> None:
    """Validate candidate identity and every bound argv path consistently."""
    identity = canonical_path_identity(actual_candidate_path, project_root=project_root, cwd=cwd, must_exist=True)
    if candidate.get("candidate_path") != identity.project_relative:
        raise ValueError("RECOVERY_CANDIDATE_SELF_PATH_MISMATCH")
    expected_flags = {
        "--candidate": "candidate", "--permit": "permit",
        "--standing-authorization": "authorization", "--state": "state",
        "--output": "output",
    }
    stored = candidate.get("canonical_execution_binding")
    if not isinstance(stored, Mapping) or stored.get("schema_version") != "OC3_SOURCE_METADATA_CANONICAL_EXECUTION_BINDING_001":
        raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")
    artifact_paths = stored.get("artifact_paths")
    argv_paths = stored.get("argv_paths")
    if not isinstance(artifact_paths, Mapping) or not isinstance(argv_paths, Mapping):
        raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")
    for name in ("candidate", "permit", "authorization", "state", "output", "capability"):
        if not isinstance(artifact_paths.get(name), str):
            raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")
        expected = canonical_path_identity(
            artifact_paths[name], project_root=project_root, cwd=project_root,
            must_exist=name == "candidate",
        )
        if argv_paths.get(name) != expected.absolute:
            raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")
    if artifact_paths["candidate"] != identity.project_relative or argv_paths["candidate"] != identity.absolute:
        raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")
    for argv_name in ("command_argv", "worker_argv"):
        argv = candidate.get(argv_name)
        if not isinstance(argv, list):
            raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")
        expected_hash = hashlib.sha256(canonical(argv)).hexdigest()
        if candidate.get(f"{argv_name}_sha256") != expected_hash:
            raise ValueError("CANONICAL_EXECUTION_ARGV_HASH_INVALID")
        for flag, name in expected_flags.items():
            if argv.count(flag) != 1 or argv[argv.index(flag) + 1] != argv_paths.get(name):
                raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")
    worker = candidate.get("worker_argv")
    if worker.count("--execution-capability") != 1 or worker[worker.index("--execution-capability") + 1] != argv_paths.get("capability"):
        raise ValueError("CANONICAL_EXECUTION_BINDING_INVALID")


def build_replacement_authorization_binding(
    *, old_authorization_sha256: str, old_candidate_sha256: str,
    new_candidate_path: Path, new_implementation_aggregate: str,
    prior_implementation_aggregate: str, mandate_sha256: str,
    project_root: Path, cwd: Path,
) -> dict[str, object]:
    """Build a fresh derived binding; old authorization/candidate are never reused."""
    hashes = (old_authorization_sha256, old_candidate_sha256, new_implementation_aggregate,
        prior_implementation_aggregate, mandate_sha256)
    if any(not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
           for value in hashes):
        raise ValueError("SELF_REPAIR_BINDING_SHA256_INVALID")
    if new_implementation_aggregate == prior_implementation_aggregate:
        raise ValueError("SELF_REPAIR_IMPLEMENTATION_IDENTITY_UNCHANGED")
    identity = canonical_path_identity(new_candidate_path, project_root=project_root, cwd=cwd, must_exist=True)
    candidate_sha = file_sha256(Path(identity.absolute))
    if candidate_sha == old_candidate_sha256:
        raise ValueError("INVALIDATED_PENDING_CANDIDATE_REUSE_FORBIDDEN")
    from .cross_observer_grouping import load_canonical_json, validate_sealed
    candidate = validate_sealed(load_canonical_json(Path(identity.absolute)))
    if candidate.get("implementation_aggregate") != new_implementation_aggregate:
        raise ValueError("REPLACEMENT_CANDIDATE_IMPLEMENTATION_BINDING_INVALID")
    return sealed({
        "authorization_basis_mandate_sha256": mandate_sha256,
        "new_candidate": {"path": identity.project_relative, "sha256": candidate_sha},
        "new_implementation_aggregate": new_implementation_aggregate,
        "parent_authorization_sha256": old_authorization_sha256,
        "prior_candidate_sha256": old_candidate_sha256,
        "prior_implementation_aggregate": prior_implementation_aggregate,
        "replacement_reason": "AUTONOMOUS_TECHNICAL_SELF_REPAIR",
        "schema_version": "OC3_SOURCE_METADATA_SELF_REPAIR_REPLACEMENT_AUTHORIZATION_BINDING_001",
    })


def implementation_aggregate(paths: Sequence[Path], *, project_root: Path) -> str:
    rows = {
        canonical_path_identity(path, project_root=project_root, must_exist=True).project_relative: file_sha256(path)
        for path in paths
    }
    return hashlib.sha256(canonical(rows)).hexdigest()
