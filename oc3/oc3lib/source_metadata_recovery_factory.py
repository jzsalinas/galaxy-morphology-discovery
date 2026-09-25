"""Immutable domain factory for bounded source-metadata recovery candidates."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, sealed, sha256_bytes
from .autonomous_recovery_envelope import RecoveryEnvelopeError

ACTION_FAMILIES = (
    "TECHNICAL_RESPONSE_DIAGNOSTIC",
    "OFFICIAL_SERVICE_DOCUMENTARY_PROBE",
    "OFFLINE_TECHNICAL_REPAIR",
    "MATERIAL_SOURCE_METADATA_ACQUISITION",
    "TECHNICAL_INTEGRITY_TRIAGE",
)


def binding(path: Path) -> dict[str, str]:
    return {"path": str(Path(path).resolve().relative_to(PROJECT)), "sha256": file_sha256(path)}


def build_recovery_candidate(*, action_kind: str, stage_id: str, parent_terminal: Mapping[str, str],
        recovery_generation: int, trigger_failure_class: str, recovery_graph: Path,
        scientific_invariants: Path, recovery_budget: Path, mutable_surface: Path,
        remaining_budgets: dict[str, int], implementation_aggregate: str,
        command_argv: list[str], worker_argv: list[str], permit_path: str,
        worker_capability_path: str, output_directory: str, authority_classes: list[str],
        network_request_reservation: int, application_body_reservation: int,
        request_class: str, technical_patch_manifest: dict[str, str] | None = None) -> dict[str, object]:
    if action_kind not in ACTION_FAMILIES:
        raise RecoveryEnvelopeError("RECOVERY_ACTION_KIND_NOT_ALLOWED")
    if set(parent_terminal) != {"path", "sha256"}:
        raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_INVALID")
    candidate = {
        "action_kind": action_kind,
        "application_body_reservation": application_body_reservation,
        "authority_classes": authority_classes,
        "command_argv": command_argv,
        "command_argv_sha256": sha256_bytes(canonical(command_argv)),
        "implementation_aggregate": implementation_aggregate,
        "material_budget_reservation": {"body_bytes": application_body_reservation if request_class == "MATERIAL" else 0,
            "requests": network_request_reservation if request_class == "MATERIAL" else 0},
        "mutable_technical_surface": binding(mutable_surface),
        "network_request_reservation": network_request_reservation,
        "output_directory": output_directory,
        "parent_action_terminal": dict(parent_terminal),
        "permit_path": permit_path,
        "recovery_budget": binding(recovery_budget),
        "recovery_generation": recovery_generation,
        "recovery_graph": binding(recovery_graph),
        "remaining_budgets": remaining_budgets,
        "request_class": request_class,
        "resume": False,
        "retries": 0,
        "schema_version": "RECOVERY_ACTION_FACTORY_V1",
        "scientific_invariants": binding(scientific_invariants),
        "stage_id": stage_id,
        "technical_budget_reservation": {"body_bytes": application_body_reservation if request_class == "TECHNICAL" else 0,
            "requests": network_request_reservation if request_class == "TECHNICAL" else 0},
        "technical_patch_manifest": technical_patch_manifest,
        "trigger_failure_class": trigger_failure_class,
        "worker_argv": worker_argv,
        "worker_argv_sha256": sha256_bytes(canonical(worker_argv)),
        "worker_capability_path": worker_capability_path,
    }
    return sealed(candidate)


def validate_parent(candidate: dict[str, object], parent_terminal_path: Path) -> None:
    expected = candidate.get("parent_action_terminal")
    if not isinstance(expected, dict) or expected != binding(parent_terminal_path):
        raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")
