"""Fail-closed Git change partitioning for source-metadata repair handoffs.

Runtime state is never a repair surface.  This module accounts for every path
in the repair comparison set and admits a runtime state only through an exact,
validated mission binding.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable, Mapping, Sequence

from .autonomous_recovery_envelope import RecoveryEnvelopeError
from .cross_observer_grouping import (
    file_sha256, load_canonical_json, sealed, validate_sealed,
)
from .source_metadata_path_identity import canonical_path_identity


@dataclass(frozen=True)
class RuntimeStateRequirement:
    path: str
    run_id: str
    schema_version: str
    standing_authorization: Mapping[str, str]
    allowed_states: tuple[str, ...] = ("ACTIVE",)
    allowed_stages: tuple[str, ...] = ("AWAITING_AGENTIC_TECHNICAL_REPAIR",)
    pending_action_required: bool = False
    ledger_prefix: str | None = None


def git_comparison_paths(base_commit: str, *, project_root: Path,
        mutable_prefixes: Sequence[str]) -> list[str]:
    """Return every base-tracked change plus new mutable-surface files.

    Existing unrelated untracked runtime evidence is outside Git's tracked
    comparison.  A new untracked repair file is included because it is a
    prospective patch member.
    """
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project_root,
        check=True, capture_output=True, text=True).stdout.strip()
    if head != base_commit:
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_BASE_COMMIT_MISMATCH")
    tracked = subprocess.run(["git", "diff", "--name-only", base_commit, "--"],
        cwd=project_root, check=True, capture_output=True, text=True).stdout.splitlines()
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"],
        cwd=project_root, check=True, capture_output=True, text=True).stdout.splitlines()
    considered = {row for row in tracked if row}
    considered.update(row for row in untracked if row.startswith(tuple(mutable_prefixes)))
    return sorted(considered)


def _binding_valid(project_root: Path, value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != {"path", "sha256"}:
        return False
    try:
        identity = canonical_path_identity(str(value["path"]), project_root=project_root,
            cwd=project_root, must_exist=True)
    except Exception:
        return False
    return file_sha256(Path(identity.absolute)) == value["sha256"]


def validate_runtime_state(path: Path, *, project_root: Path,
        requirement: RuntimeStateRequirement,
        lifecycle_validator: Callable[[Path], Mapping[str, object]] | None = None,
        require_handoff_history: bool = True) -> dict[str, object]:
    """Validate one exact mission-owned state and return compact evidence."""
    identity = canonical_path_identity(path, project_root=project_root, cwd=project_root,
        must_exist=True)
    if identity.project_relative != requirement.path:
        raise RecoveryEnvelopeError("AUTHORIZED_RUNTIME_PATH_MISMATCH")
    try:
        value = validate_sealed(load_canonical_json(Path(identity.absolute)))
    except Exception as exc:
        raise RecoveryEnvelopeError("AUTHORIZED_RUNTIME_STATE_INVALID") from exc
    if (value.get("run_id") != requirement.run_id or
            value.get("schema_version") != requirement.schema_version or
            value.get("standing_authorization") != dict(requirement.standing_authorization) or
            value.get("state") not in requirement.allowed_states or
            value.get("current_stage") not in requirement.allowed_stages or
            value.get("active") is not True or
            not isinstance(value.get("sequence"), int) or value["sequence"] < 1):
        raise RecoveryEnvelopeError("AUTHORIZED_RUNTIME_STATE_INVALID")
    if require_handoff_history:
        if (not _binding_valid(project_root, value.get("last_action_terminal")) or
                not _binding_valid(project_root, value.get("agentic_repair_request"))):
            raise RecoveryEnvelopeError("AUTHORIZED_RUNTIME_LIFECYCLE_INVALID")
        terminal=validate_sealed(load_canonical_json(project_root / value["last_action_terminal"]["path"]))
        request=validate_sealed(load_canonical_json(project_root / value["agentic_repair_request"]["path"]))
        if (terminal.get("run_id") != requirement.run_id or
                request.get("run_id") != requirement.run_id or
                request.get("parent_action_terminal") != value["last_action_terminal"] or
                request.get("recovery_generation") != int(value.get("recovery_generation",-1))+1 or
                (requirement.ledger_prefix is not None and
                 not value["agentic_repair_request"]["path"].startswith(requirement.ledger_prefix))):
            raise RecoveryEnvelopeError("AUTHORIZED_RUNTIME_LIFECYCLE_INVALID")
        pending=value.get("registered_pending_action")
        if requirement.pending_action_required:
            if not _binding_valid(project_root,pending):
                raise RecoveryEnvelopeError("AUTHORIZED_RUNTIME_LIFECYCLE_INVALID")
        elif pending is not None:
            raise RecoveryEnvelopeError("AUTHORIZED_RUNTIME_LIFECYCLE_INVALID")
    if lifecycle_validator is not None:
        validated = lifecycle_validator(Path(identity.absolute))
        if dict(validated) != value:
            raise RecoveryEnvelopeError("AUTHORIZED_RUNTIME_LIFECYCLE_INVALID")
    return {
        "current_stage": value["current_stage"],
        "path": identity.project_relative,
        "run_id": value["run_id"],
        "schema_version": value["schema_version"],
        "sequence": value["sequence"],
        "sha256": file_sha256(Path(identity.absolute)),
        "state": value["state"],
    }


def partition_changed_paths(*, base_commit: str, all_tracked_changes: Sequence[str],
        mutable_prefixes: Sequence[str], project_root: Path,
        runtime_requirement: RuntimeStateRequirement | None = None,
        lifecycle_validator: Callable[[Path], Mapping[str, object]] | None = None,
        require_handoff_history: bool = True) -> dict[str, object]:
    """Partition every supplied path into exactly one fail-closed class."""
    paths = list(all_tracked_changes)
    if paths != sorted(set(paths)) or any(not isinstance(row, str) or not row for row in paths):
        raise RecoveryEnvelopeError("GIT_CHANGE_PARTITION_INPUT_INVALID")
    mutable: list[str] = []
    runtime: list[dict[str, object]] = []
    forbidden: list[str] = []
    runtime_path = runtime_requirement.path if runtime_requirement else None
    for changed in paths:
        in_mutable = changed.startswith(tuple(mutable_prefixes))
        is_runtime = changed == runtime_path
        if in_mutable and is_runtime:
            raise RecoveryEnvelopeError("GIT_CHANGE_PARTITION_OVERLAP")
        if is_runtime:
            runtime.append(validate_runtime_state(project_root / changed,
                project_root=project_root, requirement=runtime_requirement,
                lifecycle_validator=lifecycle_validator,
                require_handoff_history=require_handoff_history))
        elif in_mutable:
            mutable.append(changed)
        else:
            forbidden.append(changed)
    classified = set(mutable) | {row["path"] for row in runtime} | set(forbidden)
    if classified != set(paths) or (set(mutable) & set(forbidden)) or (
            set(mutable) & {row["path"] for row in runtime}) or (
            set(forbidden) & {row["path"] for row in runtime}):
        raise RecoveryEnvelopeError("GIT_CHANGE_PARTITION_NOT_EXHAUSTIVE")
    return sealed({
        "all_tracked_changes": paths,
        "authorized_runtime_changes": runtime,
        "base_commit": base_commit,
        "forbidden_changes": forbidden,
        "mutable_patch_changes": mutable,
        "schema_version": "OC3_SOURCE_METADATA_GIT_CHANGE_PARTITION_001",
    })


def classify_git_changes(*, base_commit: str, mutable_prefixes: Sequence[str],
        project_root: Path, runtime_requirement: RuntimeStateRequirement | None,
        lifecycle_validator: Callable[[Path], Mapping[str, object]] | None = None,
        require_handoff_history: bool = True) -> dict[str, object]:
    paths = git_comparison_paths(base_commit, project_root=project_root,
        mutable_prefixes=mutable_prefixes)
    return partition_changed_paths(base_commit=base_commit,
        all_tracked_changes=paths, mutable_prefixes=mutable_prefixes,
        project_root=project_root, runtime_requirement=runtime_requirement,
        lifecycle_validator=lifecycle_validator,
        require_handoff_history=require_handoff_history)


def validate_partition(partition: Mapping[str, object], *, expected_base: str,
        expected_mutable_paths: Sequence[str]) -> None:
    """Validate the closed evidence schema and its disjoint union invariant."""
    required = {"all_tracked_changes", "authorized_runtime_changes", "base_commit",
        "forbidden_changes", "mutable_patch_changes", "schema_version", "sealed"}
    if set(partition) != required or partition.get("schema_version") != \
            "OC3_SOURCE_METADATA_GIT_CHANGE_PARTITION_001" or partition.get("base_commit") != expected_base:
        raise RecoveryEnvelopeError("GIT_CHANGE_PARTITION_INVALID")
    all_paths = partition.get("all_tracked_changes")
    mutable = partition.get("mutable_patch_changes")
    runtime = partition.get("authorized_runtime_changes")
    forbidden = partition.get("forbidden_changes")
    if not all(isinstance(rows, list) for rows in (all_paths, mutable, runtime, forbidden)):
        raise RecoveryEnvelopeError("GIT_CHANGE_PARTITION_INVALID")
    runtime_paths = [row.get("path") for row in runtime if isinstance(row, Mapping)]
    if len(runtime_paths) != len(runtime):
        raise RecoveryEnvelopeError("GIT_CHANGE_PARTITION_INVALID")
    groups = [set(mutable), set(runtime_paths), set(forbidden)]
    if (list(all_paths) != sorted(set(all_paths)) or
            any(groups[i] & groups[j] for i in range(3) for j in range(i + 1, 3)) or
            set(all_paths) != set().union(*groups) or
            list(mutable) != list(expected_mutable_paths) or forbidden):
        raise RecoveryEnvelopeError("GIT_CHANGE_PARTITION_INVALID")
