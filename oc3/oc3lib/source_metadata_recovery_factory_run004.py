"""Deterministic candidate factory for source-metadata recovery RUN-004."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed, validate_sealed
from .autonomous_recovery_envelope import RecoveryEnvelopeError
from .source_metadata_path_identity import canonical_path_identity
from .source_metadata_self_repair import prospective_execution_binding, seal_candidate_execution

RUN_ID = "OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-004"
FIRST_CANDIDATE_RELATIVE = "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_FIRST_CANDIDATE_004.json"
# Replaced by the package-freezing script after all implementation files exist.
SELF_REPAIR_IMPLEMENTATION_AGGREGATE = "2b2fbd0e9b839613c54c9814291073fcdc37fa39872f2a752d04da5e9217bb55"

ACTION_FAMILIES = (
    "TECHNICAL_RESPONSE_DIAGNOSTIC", "OFFICIAL_SERVICE_DOCUMENTARY_PROBE",
    "OFFLINE_TECHNICAL_REPAIR", "MATERIAL_SOURCE_METADATA_ACQUISITION",
    "TECHNICAL_INTEGRITY_TRIAGE",
)


def binding(path: Path) -> dict[str, str]:
    identity = canonical_path_identity(path, project_root=PROJECT, must_exist=True)
    return {"path": identity.project_relative, "sha256": file_sha256(Path(identity.absolute))}


def _load(path: Path) -> dict[str, object]:
    return validate_sealed(load_canonical_json(path))


def _paths(action_kind: str, generation: int) -> dict[str, str]:
    stem = f"OC3-SOURCE-METADATA-RECOVERY-RUN-004-G{generation:02d}-{action_kind}"
    output = f"oc3/source_metadata_autonomous_recovery_run_004/{stem}"
    return {"stage_id": stem,
        "candidate_path": f"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_004_LEDGER/CANDIDATES/{stem}.json",
        "output_directory": output,
        "permit_path": f"oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_004_PERMITS/{stem}.json",
        "worker_capability_path": f"{output}/WORKER_CAPABILITY.json"}


def _build_candidate(*, state: Mapping[str, object], parent_terminal_path: Path,
        action_registry_path: Path, technical_authorities_path: Path,
        scientific_invariants_path: Path, recovery_graph_path: Path,
        recovery_budget_path: Path, mutable_surface_path: Path,
        state_path: Path, standing_authorization_path: Path,
        implementation_aggregate: str, policy_manifest_path: Path,
        self_repair_amendment_path: Path, self_repair_report_path: Path,
        self_repair_replay_path: Path, paths: Mapping[str, str]) -> dict[str, object]:
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
    git_change_partition = None
    if rule["technical_patch_manifest_required"]:
        technical_patch_manifest = state.get("validated_patch_manifest")
        technical_transport_contract = state.get("validated_transport_contract")
        test_receipts = state.get("validated_test_receipts")
        git_change_partition = state.get("validated_change_partition")
        if not all(isinstance(x, Mapping) for x in (technical_patch_manifest,technical_transport_contract,
                test_receipts,git_change_partition)):
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
    candidate_path = PROJECT / paths["candidate_path"]
    permit_path = PROJECT / paths["permit_path"]
    output = PROJECT / paths["output_directory"]
    capability = PROJECT / paths["worker_capability_path"]
    execution_binding = prospective_execution_binding(project_root=PROJECT, cwd=PROJECT,
        candidate_path=candidate_path, permit_path=permit_path,
        authorization_path=standing_authorization_path, state_path=state_path,
        output_path=output, capability_path=capability)
    payload = {"action_kind": action_kind, "active_adapter": adapter,
        "active_adapter_binding": active_adapter_binding,
        "action_registry": binding(action_registry_path), "application_body_reservation": body,
        "authority_classes": list(rule["allowed_authority_classes"]),
        "budget_accounting": {"counter_scope": "MISSION_LOCAL_RUN_004",
            "cross_mission_global_cap": None, "historical_requests_are_provenance_only": True},
        "expected_terminal_classes": ["SCIENTIFIC_TERMINAL", "STOP_REQUIRES_HUMAN",
            "AWAITING_AGENTIC_TECHNICAL_REPAIR"],
        "implementation_aggregate": implementation_aggregate,
        "material_budget_reservation": {"body_bytes": body if request_class == "MATERIAL" else 0,
            "requests": requests if request_class == "MATERIAL" else 0},
        "mission_scope": "SOURCE_METADATA_ACQUISITION_WITH_BOUNDED_TECHNICAL_RECOVERY",
        "mutable_technical_surface": binding(mutable_surface_path),
        "negative_capabilities": ["NO_CREDENTIALS", "NO_HOLDOUT_ACCESS", "NO_PHOTSYS_READ",
            "NO_BRICKNAME_READ", "NO_BRICKID_READ", "NO_ROOT_READ", "NO_IMAGE_PIXEL_ACCESS",
            "NO_LABEL_ACCESS", "NO_MATCHING", "NO_PANEL_V2", "NO_P1", "NO_REDISTRIBUTION"],
        "network_request_reservation": requests, "output_directory": paths["output_directory"],
        "parent_action_terminal": binding(parent_terminal_path), "permit_path": paths["permit_path"],
        "policy_core_manifest": binding(policy_manifest_path),
        "recovery_budget": binding(recovery_budget_path), "recovery_generation": generation,
        "recovery_graph": binding(recovery_graph_path), "remaining_budgets": remaining,
        "rights_constraints": {"access": "PUBLIC_ANONYMOUS_ONLY", "credentials_authorized": False,
            "redistribution_authorized": False},
        "request_class": request_class, "resume": False, "retries": 0, "run_id": RUN_ID,
        "schema_version": "RECOVERY_ACTION_FACTORY_V4", "scientific_invariants": binding(scientific_invariants_path),
        "self_repair_authority": {"amendment": binding(self_repair_amendment_path),
            "implementation_report": binding(self_repair_report_path),
            "replay_receipt": binding(self_repair_replay_path),
            "implementation_aggregate": SELF_REPAIR_IMPLEMENTATION_AGGREGATE,
            "maximum_episodes_per_mission": 2, "maximum_episodes_per_defect_class": 1,
            "post_repair_fresh_artifacts_required": True},
        "stage_id": paths["stage_id"], "technical_authorities": binding(technical_authorities_path),
        "technical_budget_reservation": {"body_bytes": body if request_class == "TECHNICAL" else 0,
            "requests": requests if request_class == "TECHNICAL" else 0},
        "technical_patch_manifest": technical_patch_manifest,
        "technical_transport_contract": technical_transport_contract,
        "test_receipts": test_receipts,
        "git_change_partition": git_change_partition,
        "trigger_failure_class": classification["failure_class"],
        "worker_capability_path": paths["worker_capability_path"]}
    executable = canonical_path_identity("oc3/.venv/bin/python", project_root=PROJECT,
        cwd=PROJECT).absolute
    runner = canonical_path_identity("oc3/oc3_source_metadata_recovery_mission_runner_run004.py",
        project_root=PROJECT, cwd=PROJECT, must_exist=True).absolute
    mission_command = [executable, runner, "--run-mission", "--state",
        execution_binding["argv_paths"]["state"], "--standing-authorization",
        execution_binding["argv_paths"]["authorization"]]
    payload["mission_execution_argv"] = mission_command
    payload["mission_execution_argv_sha256"] = hashlib.sha256(canonical(mission_command)).hexdigest()
    supervisor = canonical_path_identity(rule["supervisor_implementation"]["path"],
        project_root=PROJECT, cwd=PROJECT, must_exist=True).absolute
    worker = canonical_path_identity(rule["worker_implementation"]["path"],
        project_root=PROJECT, cwd=PROJECT, must_exist=True).absolute
    return seal_candidate_execution(payload=payload, binding=execution_binding,
        supervisor_prefix=[executable, supervisor, "--execute-recovery-action"],
        worker_prefix=[executable, worker, "--run-recovery-worker"])


def build_next_candidate(*, state: Mapping[str, object], parent_terminal_path: Path,
        action_registry_path: Path, technical_authorities_path: Path,
        scientific_invariants_path: Path, recovery_graph_path: Path,
        recovery_budget_path: Path, mutable_surface_path: Path,
        state_path: Path, standing_authorization_path: Path,
        implementation_aggregate: str, policy_manifest_path: Path,
        self_repair_amendment_path: Path, self_repair_report_path: Path,
        self_repair_replay_path: Path) -> tuple[Path, dict[str, object]]:
    """Derive a child candidate and its RUN-004 ledger path."""
    generation = int(state.get("recovery_generation", -1)) + 1
    action_kind = str(state.get("next_action_kind", ""))
    paths = _paths(action_kind, generation)
    candidate = _build_candidate(state=state, parent_terminal_path=parent_terminal_path,
        action_registry_path=action_registry_path, technical_authorities_path=technical_authorities_path,
        scientific_invariants_path=scientific_invariants_path, recovery_graph_path=recovery_graph_path,
        recovery_budget_path=recovery_budget_path, mutable_surface_path=mutable_surface_path,
        state_path=state_path, standing_authorization_path=standing_authorization_path,
        implementation_aggregate=implementation_aggregate,
        policy_manifest_path=policy_manifest_path,
        self_repair_amendment_path=self_repair_amendment_path,
        self_repair_report_path=self_repair_report_path,
        self_repair_replay_path=self_repair_replay_path, paths=paths)
    return PROJECT / paths["candidate_path"], candidate


def build_first_candidate(*, parent_terminal_path: Path, action_registry_path: Path,
        technical_authorities_path: Path, scientific_invariants_path: Path,
        recovery_graph_path: Path, recovery_budget_path: Path, mutable_surface_path: Path,
        state_path: Path, standing_authorization_path: Path,
        implementation_aggregate: str, policy_manifest_path: Path,
        self_repair_amendment_path: Path, self_repair_report_path: Path,
        self_repair_replay_path: Path, inherited_adapter_binding: Mapping[str, object]) -> dict[str, object]:
    """Build the sole reviewed first candidate at its fixed INPUTS path."""
    bootstrap_state = {"active": True, "state": "ACTIVE", "registered_pending_action": None,
        "last_classification": {"decision": "RECOVER_AUTONOMOUSLY",
            "failure_class": "TECHNICAL_PATCH_VALIDATED",
            "next_action_kind": "MATERIAL_SOURCE_METADATA_ACQUISITION",
            "reason": "RUN_003_DOCUMENTARY_EVIDENCE_REUSED_READ_ONLY"},
        "next_action_kind": "MATERIAL_SOURCE_METADATA_ACQUISITION",
        "last_action_terminal_sha256": file_sha256(parent_terminal_path), "recovery_generation": 0,
        "technical_requests_remaining": 8, "technical_body_bytes_remaining": 2_097_152,
        "material_requests_remaining": 5, "material_body_bytes_remaining": 67_108_864,
        "active_adapter": "query_manager_public_anonymous_v1",
        "active_adapter_binding": dict(inherited_adapter_binding),
        "adapter_states": {"query_manager_public_anonymous_v1": "ACTIVE"},
        "validated_patch_manifest": None, "validated_transport_contract": None,
        "validated_test_receipts": None, "validated_change_partition": None}
    paths = _paths("MATERIAL_SOURCE_METADATA_ACQUISITION", 1)
    paths = dict(paths); paths["candidate_path"] = FIRST_CANDIDATE_RELATIVE
    return _build_candidate(state=bootstrap_state, parent_terminal_path=parent_terminal_path,
        action_registry_path=action_registry_path, technical_authorities_path=technical_authorities_path,
        scientific_invariants_path=scientific_invariants_path, recovery_graph_path=recovery_graph_path,
        recovery_budget_path=recovery_budget_path, mutable_surface_path=mutable_surface_path,
        state_path=state_path, standing_authorization_path=standing_authorization_path,
        implementation_aggregate=implementation_aggregate,
        policy_manifest_path=policy_manifest_path,
        self_repair_amendment_path=self_repair_amendment_path,
        self_repair_report_path=self_repair_report_path,
        self_repair_replay_path=self_repair_replay_path, paths=paths)


def validate_parent(candidate: dict[str, object], parent_terminal_path: Path) -> None:
    if candidate.get("parent_action_terminal") != binding(parent_terminal_path):
        raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")


def build_recovery_candidate(**_: object) -> dict[str, object]:
    """The unrestricted V1 builder is deliberately unavailable to production."""
    raise RecoveryEnvelopeError("UNRESTRICTED_RECOVERY_FACTORY_DISABLED")
