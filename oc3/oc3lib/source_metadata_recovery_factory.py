"""Deterministic candidate factory for the source-metadata recovery mission."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes, validate_sealed
from .autonomous_recovery_envelope import RecoveryEnvelopeError

ACTION_FAMILIES = (
    "TECHNICAL_RESPONSE_DIAGNOSTIC", "OFFICIAL_SERVICE_DOCUMENTARY_PROBE",
    "OFFLINE_TECHNICAL_REPAIR", "MATERIAL_SOURCE_METADATA_ACQUISITION",
    "TECHNICAL_INTEGRITY_TRIAGE",
)


def binding(path: Path) -> dict[str, str]:
    return {"path": str(Path(path).resolve().relative_to(PROJECT)), "sha256": file_sha256(path)}


def _load(path: Path) -> dict[str, object]:
    return validate_sealed(load_canonical_json(path))


def _paths(action_kind: str, generation: int) -> dict[str, str]:
    stem = f"OC3-SOURCE-METADATA-RECOVERY-G{generation:02d}-{action_kind}"
    output = f"oc3/source_metadata_autonomous_recovery/{stem}"
    return {"stage_id": stem,
        "candidate_path": f"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_LEDGER/CANDIDATES/{stem}.json",
        "output_directory": output,
        "permit_path": f"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_PERMITS/{stem}.json",
        "worker_capability_path": f"{output}/WORKER_CAPABILITY.json"}


def build_next_candidate(*, state: Mapping[str, object], parent_terminal_path: Path,
        action_registry_path: Path, technical_authorities_path: Path,
        scientific_invariants_path: Path, recovery_graph_path: Path,
        recovery_budget_path: Path, mutable_surface_path: Path,
        state_path: Path, standing_authorization_path: Path,
        implementation_aggregate: str) -> tuple[Path, dict[str, object]]:
    """Derive every security-relevant child field from frozen authorities/state."""
    if (state.get("active") is not True or state.get("state") != "ACTIVE" or
            state.get("registered_pending_action") is not None or not state.get("last_classification") or
            not state.get("next_action_kind")):
        raise RecoveryEnvelopeError("RECOVERY_CHILD_ACTION_STATE_MISMATCH")
    action_kind = str(state["next_action_kind"])
    classification = state["last_classification"]
    if not isinstance(classification, Mapping) or classification.get("next_action_kind") != action_kind:
        raise RecoveryEnvelopeError("RECOVERY_CHILD_ACTION_STATE_MISMATCH")
    if state.get("last_action_terminal_sha256") != file_sha256(parent_terminal_path):
        raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")
    registry = _load(action_registry_path)
    entries = {row["action_kind"]: row for row in registry["actions"]}
    if action_kind not in entries:
        raise RecoveryEnvelopeError("RECOVERY_ACTION_KIND_NOT_ALLOWED")
    rule = entries[action_kind]
    if classification.get("failure_class") not in rule["eligible_trigger_failure_classes"]:
        raise RecoveryEnvelopeError("RECOVERY_CHILD_ACTION_STATE_MISMATCH")
    generation = int(state["recovery_generation"]) + 1
    paths = _paths(action_kind, generation)
    remaining = {"technical_requests": int(state["technical_requests_remaining"]),
        "technical_body_bytes": int(state["technical_body_bytes_remaining"]),
        "material_requests": int(state["material_requests_remaining"]),
        "material_body_bytes": int(state["material_body_bytes_remaining"])}
    request_class = rule["request_class"]
    requests = int(rule["maximum_requests_per_action"])
    body = int(rule["maximum_body_bytes_per_action"])
    if request_class != "OFFLINE":
        prefix = request_class.lower()
        if requests > remaining[f"{prefix}_requests"] or body > remaining[f"{prefix}_body_bytes"]:
            raise RecoveryEnvelopeError("RECOVERY_BUDGET_EXHAUSTED")
    technical_patch_manifest = None
    if rule["technical_patch_manifest_required"]:
        technical_patch_manifest = {"path":
            f"oc3/INPUTS/TECHNICAL_PATCH_MANIFEST_{generation:02d}.json", "sha256": None}
    adapter = None
    if rule.get("active_adapter_required"):
        adapter = state.get("active_adapter")
        authorities = _load(technical_authorities_path)
        if adapter not in authorities["adapter_ids"]:
            raise RecoveryEnvelopeError("TECHNICAL_ADAPTER_NOT_VALIDATED")
    executable = str(PROJECT / "oc3/.venv/bin/python")
    supervisor = str(PROJECT / rule["supervisor_implementation"]["path"])
    worker = str(PROJECT / rule["worker_implementation"]["path"])
    candidate_path = PROJECT / paths["candidate_path"]
    permit_path = PROJECT / paths["permit_path"]
    output = PROJECT / paths["output_directory"]
    capability = PROJECT / paths["worker_capability_path"]
    command = [executable, supervisor, "--execute-recovery-action", "--candidate", str(candidate_path),
        "--permit", str(permit_path), "--standing-authorization", str(standing_authorization_path),
        "--state", str(state_path), "--output", str(output)]
    worker_command = [executable, worker, "--run-recovery-worker", "--candidate", str(candidate_path),
        "--permit", str(permit_path), "--standing-authorization", str(standing_authorization_path),
        "--state", str(state_path), "--output", str(output), "--execution-capability", str(capability)]
    candidate = sealed({"action_kind": action_kind, "active_adapter": adapter,
        "action_registry": binding(action_registry_path), "application_body_reservation": body,
        "authority_classes": list(rule["allowed_authority_classes"]),
        "command_argv": command, "command_argv_sha256": sha256_bytes(canonical(command)),
        "implementation_aggregate": implementation_aggregate,
        "material_budget_reservation": {"body_bytes": body if request_class == "MATERIAL" else 0,
            "requests": requests if request_class == "MATERIAL" else 0},
        "mutable_technical_surface": binding(mutable_surface_path),
        "network_request_reservation": requests, "output_directory": paths["output_directory"],
        "parent_action_terminal": binding(parent_terminal_path), "permit_path": paths["permit_path"],
        "recovery_budget": binding(recovery_budget_path), "recovery_generation": generation,
        "recovery_graph": binding(recovery_graph_path), "remaining_budgets": remaining,
        "request_class": request_class, "resume": False, "retries": 0,
        "schema_version": "RECOVERY_ACTION_FACTORY_V2", "scientific_invariants": binding(scientific_invariants_path),
        "stage_id": paths["stage_id"], "technical_authorities": binding(technical_authorities_path),
        "technical_budget_reservation": {"body_bytes": body if request_class == "TECHNICAL" else 0,
            "requests": requests if request_class == "TECHNICAL" else 0},
        "technical_patch_manifest": technical_patch_manifest,
        "trigger_failure_class": classification["failure_class"],
        "worker_argv": worker_command, "worker_argv_sha256": sha256_bytes(canonical(worker_command)),
        "worker_capability_path": paths["worker_capability_path"]})
    return candidate_path, candidate


def build_first_candidate(*, parent_terminal_path: Path, action_registry_path: Path,
        technical_authorities_path: Path, scientific_invariants_path: Path,
        recovery_graph_path: Path, recovery_budget_path: Path, mutable_surface_path: Path,
        state_path: Path, standing_authorization_path: Path,
        implementation_aggregate: str) -> dict[str, object]:
    """Build the sole prospective first candidate from the closed predecessor."""
    bootstrap_state = {"active": True, "state": "ACTIVE", "registered_pending_action": None,
        "last_classification": {"decision": "RECOVER_AUTONOMOUSLY",
            "failure_class": "DATALAB_TRANSPORT_FAILURE",
            "next_action_kind": "TECHNICAL_RESPONSE_DIAGNOSTIC"},
        "next_action_kind": "TECHNICAL_RESPONSE_DIAGNOSTIC",
        "last_action_terminal_sha256": file_sha256(parent_terminal_path), "recovery_generation": 0,
        "technical_requests_remaining": 8, "technical_body_bytes_remaining": 2_097_152,
        "material_requests_remaining": 5, "material_body_bytes_remaining": 67_108_864,
        "active_adapter": None}
    _, candidate = build_next_candidate(state=bootstrap_state,
        parent_terminal_path=parent_terminal_path, action_registry_path=action_registry_path,
        technical_authorities_path=technical_authorities_path,
        scientific_invariants_path=scientific_invariants_path,
        recovery_graph_path=recovery_graph_path, recovery_budget_path=recovery_budget_path,
        mutable_surface_path=mutable_surface_path, state_path=state_path,
        standing_authorization_path=standing_authorization_path,
        implementation_aggregate=implementation_aggregate)
    return candidate


def validate_parent(candidate: dict[str, object], parent_terminal_path: Path) -> None:
    if candidate.get("parent_action_terminal") != binding(parent_terminal_path):
        raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")


def build_recovery_candidate(**_: object) -> dict[str, object]:
    """The unrestricted V1 builder is deliberately unavailable to production."""
    raise RecoveryEnvelopeError("UNRESTRICTED_RECOVERY_FACTORY_DISABLED")
