"""Deterministic candidate factory for source-metadata recovery RUN-002."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes, validate_sealed
from .autonomous_recovery_envelope import RecoveryEnvelopeError

RUN_ID = "OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-002"
FIRST_CANDIDATE_RELATIVE = "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_FIRST_CANDIDATE_002.json"

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
    stem = f"OC3-SOURCE-METADATA-RECOVERY-RUN-002-G{generation:02d}-{action_kind}"
    output = f"oc3/source_metadata_autonomous_recovery_run_002/{stem}"
    return {"stage_id": stem,
        "candidate_path": f"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_LEDGER/CANDIDATES/{stem}.json",
        "output_directory": output,
        "permit_path": f"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_PERMITS/{stem}.json",
        "worker_capability_path": f"{output}/WORKER_CAPABILITY.json"}


def _build_candidate(*, state: Mapping[str, object], parent_terminal_path: Path,
        action_registry_path: Path, technical_authorities_path: Path,
        scientific_invariants_path: Path, recovery_graph_path: Path,
        recovery_budget_path: Path, mutable_surface_path: Path,
        state_path: Path, standing_authorization_path: Path,
        implementation_aggregate: str, paths: Mapping[str, str]) -> dict[str, object]:
    """Build one candidate from a factory-derived canonical path."""
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
    technical_patch_manifest = None; technical_transport_contract = None; test_receipts = None
    if rule["technical_patch_manifest_required"]:
        technical_patch_manifest = state.get("validated_patch_manifest")
        technical_transport_contract = state.get("validated_transport_contract")
        test_receipts = state.get("validated_test_receipts")
        if not all(isinstance(x, Mapping) for x in (technical_patch_manifest,technical_transport_contract,test_receipts)):
            raise RecoveryEnvelopeError("AGENTIC_REPAIR_ARTIFACTS_NOT_VALIDATED")
    adapter = None; active_adapter_binding = None
    if rule.get("active_adapter_required"):
        adapter = state.get("active_adapter")
        authorities = _load(technical_authorities_path)
        active_adapter_binding=state.get("active_adapter_binding")
        registry_adapter=next((row for row in authorities["adapters"] if row["adapter_id"]==adapter),None)
        if (adapter not in authorities["adapter_ids"] or
                state.get("adapter_states",{}).get(adapter) != "ACTIVE" or
                not isinstance(active_adapter_binding,Mapping) or registry_adapter is None or
                active_adapter_binding.get("adapter_id") != adapter or
                active_adapter_binding.get("implementation_path") != registry_adapter["implementation_path"]):
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
    return sealed({"action_kind": action_kind, "active_adapter": adapter,
        "active_adapter_binding": active_adapter_binding,
        "action_registry": binding(action_registry_path), "application_body_reservation": body,
        "authority_classes": list(rule["allowed_authority_classes"]),
        "candidate_path": str(candidate_path.resolve().relative_to(PROJECT)),
        "command_argv": command, "command_argv_sha256": sha256_bytes(canonical(command)),
        "implementation_aggregate": implementation_aggregate,
        "material_budget_reservation": {"body_bytes": body if request_class == "MATERIAL" else 0,
            "requests": requests if request_class == "MATERIAL" else 0},
        "mutable_technical_surface": binding(mutable_surface_path),
        "network_request_reservation": requests, "output_directory": paths["output_directory"],
        "parent_action_terminal": binding(parent_terminal_path), "permit_path": paths["permit_path"],
        "recovery_budget": binding(recovery_budget_path), "recovery_generation": generation,
        "recovery_graph": binding(recovery_graph_path), "remaining_budgets": remaining,
        "request_class": request_class, "resume": False, "retries": 0, "run_id": RUN_ID,
        "schema_version": "RECOVERY_ACTION_FACTORY_V3", "scientific_invariants": binding(scientific_invariants_path),
        "stage_id": paths["stage_id"], "technical_authorities": binding(technical_authorities_path),
        "technical_budget_reservation": {"body_bytes": body if request_class == "TECHNICAL" else 0,
            "requests": requests if request_class == "TECHNICAL" else 0},
        "technical_patch_manifest": technical_patch_manifest,
        "technical_transport_contract": technical_transport_contract,
        "test_receipts": test_receipts,
        "trigger_failure_class": classification["failure_class"],
        "worker_argv": worker_command, "worker_argv_sha256": sha256_bytes(canonical(worker_command)),
        "worker_capability_path": paths["worker_capability_path"]})


def build_next_candidate(*, state: Mapping[str, object], parent_terminal_path: Path,
        action_registry_path: Path, technical_authorities_path: Path,
        scientific_invariants_path: Path, recovery_graph_path: Path,
        recovery_budget_path: Path, mutable_surface_path: Path,
        state_path: Path, standing_authorization_path: Path,
        implementation_aggregate: str) -> tuple[Path, dict[str, object]]:
    """Derive a child candidate and its RUN-002 ledger path."""
    generation = int(state.get("recovery_generation", -1)) + 1
    action_kind = str(state.get("next_action_kind", ""))
    paths = _paths(action_kind, generation)
    candidate = _build_candidate(state=state, parent_terminal_path=parent_terminal_path,
        action_registry_path=action_registry_path, technical_authorities_path=technical_authorities_path,
        scientific_invariants_path=scientific_invariants_path, recovery_graph_path=recovery_graph_path,
        recovery_budget_path=recovery_budget_path, mutable_surface_path=mutable_surface_path,
        state_path=state_path, standing_authorization_path=standing_authorization_path,
        implementation_aggregate=implementation_aggregate, paths=paths)
    return PROJECT / paths["candidate_path"], candidate


def build_first_candidate(*, parent_terminal_path: Path, action_registry_path: Path,
        technical_authorities_path: Path, scientific_invariants_path: Path,
        recovery_graph_path: Path, recovery_budget_path: Path, mutable_surface_path: Path,
        state_path: Path, standing_authorization_path: Path,
        implementation_aggregate: str) -> dict[str, object]:
    """Build the sole reviewed first candidate at its fixed INPUTS path."""
    bootstrap_state = {"active": True, "state": "ACTIVE", "registered_pending_action": None,
        "last_classification": {"decision": "RECOVER_AUTONOMOUSLY",
            "failure_class": "DATALAB_TRANSPORT_FAILURE",
            "next_action_kind": "TECHNICAL_RESPONSE_DIAGNOSTIC"},
        "next_action_kind": "TECHNICAL_RESPONSE_DIAGNOSTIC",
        "last_action_terminal_sha256": file_sha256(parent_terminal_path), "recovery_generation": 0,
        "technical_requests_remaining": 8, "technical_body_bytes_remaining": 2_097_152,
        "material_requests_remaining": 5, "material_body_bytes_remaining": 67_108_864,
        "active_adapter": None, "active_adapter_binding": None, "adapter_states": {},
        "validated_patch_manifest": None, "validated_transport_contract": None,
        "validated_test_receipts": None}
    paths = _paths("TECHNICAL_RESPONSE_DIAGNOSTIC", 1)
    paths = dict(paths); paths["candidate_path"] = FIRST_CANDIDATE_RELATIVE
    return _build_candidate(state=bootstrap_state, parent_terminal_path=parent_terminal_path,
        action_registry_path=action_registry_path, technical_authorities_path=technical_authorities_path,
        scientific_invariants_path=scientific_invariants_path, recovery_graph_path=recovery_graph_path,
        recovery_budget_path=recovery_budget_path, mutable_surface_path=mutable_surface_path,
        state_path=state_path, standing_authorization_path=standing_authorization_path,
        implementation_aggregate=implementation_aggregate, paths=paths)


def validate_parent(candidate: dict[str, object], parent_terminal_path: Path) -> None:
    if candidate.get("parent_action_terminal") != binding(parent_terminal_path):
        raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")


def build_recovery_candidate(**_: object) -> dict[str, object]:
    """The unrestricted V1 builder is deliberately unavailable to production."""
    raise RecoveryEnvelopeError("UNRESTRICTED_RECOVERY_FACTORY_DISABLED")
