"""Policy governor for the finite OC3 source-metadata recovery envelope."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Mapping

from .core import canonical
from .cross_observer_grouping import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)
from .autonomous_recovery_envelope import (
    FINALIZE_SCIENTIFIC, RECOVER_AUTONOMOUSLY, STOP_REQUIRES_HUMAN,
    RecoveryEnvelopeError, account_action, classify_action_terminal, validate_recovery_graph,
)
from .source_metadata_recovery_factory import ACTION_FAMILIES, binding

MISSION_ID = "OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-ENVELOPE-001"
MISSION_SCOPE = "SOURCE_METADATA_ACQUISITION_WITH_BOUNDED_TECHNICAL_RECOVERY"
AUTONOMY_BRANCH = "autopilot/source-metadata-autonomous-recovery"
STATE_WAITING = "WAITING_FOR_STANDING_HUMAN_AUTHORIZATION"
STATE_ACTIVE = "ACTIVE"
STATE_TERMINAL = "SCIENTIFIC_TERMINAL"

SPEC = PROJECT / "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_ENVELOPE_SPEC_001.md"
POLICY_CONTRACT = PROJECT / "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_POLICY_CORE_CONTRACT_001.md"
RUNBOOK = PROJECT / "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUNBOOK_001.md"
INVARIANTS = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_SCIENTIFIC_INVARIANTS_001.json"
RECOVERY_GRAPH = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_GRAPH_001.json"
MUTABLE_SURFACE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_MUTABLE_TECHNICAL_SURFACE_001.json"
RECOVERY_BUDGET = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_BUDGET_001.json"
POLICY_MANIFEST = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_POLICY_CORE_MANIFEST_001.json"
MANDATE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_MANDATE_001.json"
FIRST_CANDIDATE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_FIRST_CANDIDATE_001.json"
STATE = PROJECT / "oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_001.json"
STANDING_AUTHORIZATION = PROJECT / "oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_001.json"
LEDGER_ROOT = PROJECT / "oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_LEDGER"
PERMIT_ROOT = PROJECT / "oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_PERMITS"
PERMIT_CONSUMPTION = LEDGER_ROOT / "PERMIT_CONSUMPTION"
CAPABILITY_CONSUMPTION = LEDGER_ROOT / "WORKER_CAPABILITY_CONSUMPTION"
IMPLEMENTATION_FILES = (
    "oc3/oc3lib/autonomous_recovery_envelope.py",
    "oc3/oc3lib/source_metadata_recovery_controller.py",
    "oc3/oc3lib/source_metadata_recovery_factory.py",
    "oc3/oc3lib/source_metadata_recovery_governor.py",
    "oc3/oc3_source_metadata_recovery_supervisor.py",
    "oc3/oc3_source_metadata_recovery_worker.py",
    "oc3/recovery_adapters/source_metadata/technical_response_diagnostic.py",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({name: file_sha256(PROJECT / name) for name in IMPLEMENTATION_FILES}))


def _load(path: Path, code: str) -> dict[str, object]:
    try:
        return validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise RecoveryEnvelopeError(code) from exc


def _atomic_state(path: Path, value: dict[str, object]) -> None:
    data = canonical(value) + b"\n"
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def validate_scientific_invariants(invariants: dict[str, object]) -> dict[str, object]:
    if (invariants.get("max_source_rows_per_domain") != 150_000 or invariants.get("top_hard_cap") != 150_001 or
            len(invariants.get("target_guard_bricknames", [])) != 14 or
            len(invariants.get("forbidden_holdout_bricknames", [])) != 16 or
            len(invariants.get("projection", [])) != 9 or len(invariants.get("queries", [])) != 5):
        raise RecoveryEnvelopeError("SCIENTIFIC_INVARIANTS_INVALID")
    from .source_metadata_acquisition_pilot import query_sha256
    if any(query_sha256(row.get("literal_adql", "")) != row.get("semantic_sha256") for row in invariants["queries"]):
        raise RecoveryEnvelopeError("SCIENTIFIC_QUERY_SEMANTICS_INVALID")
    if set(invariants["target_guard_bricknames"]) & set(invariants["forbidden_holdout_bricknames"]):
        raise RecoveryEnvelopeError("SCIENTIFIC_HOLDOUT_FIREWALL_INVALID")
    return invariants


def validate_recovery_budget(budget: dict[str, object]) -> dict[str, object]:
    expected = {"MAX_CODE_REPAIR_GENERATIONS": 3, "MAX_MATERIAL_BODY_BYTES": 67_108_864,
        "MAX_MATERIAL_REQUESTS": 5, "MAX_OCCURRENCES_SAME_TECHNICAL_FAILURE_CLASS": 2,
        "MAX_RECOVERY_GENERATIONS": 4, "MAX_TECHNICAL_BODY_BYTES": 2_097_152,
        "MAX_TECHNICAL_BODY_BYTES_PER_REQUEST": 262_144, "MAX_TECHNICAL_NETWORK_REQUESTS": 8,
        "MATERIAL_CONCURRENCY": 1, "MATERIAL_RETRIES_PER_ACTION": 0,
        "TECHNICAL_CONCURRENCY": 1, "TECHNICAL_RETRIES_PER_ACTION": 0}
    if any(budget.get(key) != value for key, value in expected.items()):
        raise RecoveryEnvelopeError("RECOVERY_BUDGET_INVALID")
    return budget


def validate_static_authorities() -> dict[str, dict[str, object]]:
    values = {"invariants": _load(INVARIANTS, "SCIENTIFIC_INVARIANTS_INVALID"),
        "graph": _load(RECOVERY_GRAPH, "RECOVERY_GRAPH_INVALID"),
        "surface": _load(MUTABLE_SURFACE, "MUTABLE_TECHNICAL_SURFACE_INVALID"),
        "budget": _load(RECOVERY_BUDGET, "RECOVERY_BUDGET_INVALID"),
        "policy": _load(POLICY_MANIFEST, "RECOVERY_POLICY_CORE_INVALID"),
        "mandate": _load(MANDATE, "RECOVERY_MANDATE_INVALID")}
    validate_recovery_graph(values["graph"])
    validate_recovery_budget(values["budget"])
    validate_scientific_invariants(values["invariants"])
    policy = values["policy"]
    if (policy.get("generic_policy_core") is not True or
            policy.get("active_mutation_result") != STOP_REQUIRES_HUMAN or
            not isinstance(policy.get("files"), list)):
        raise RecoveryEnvelopeError("RECOVERY_POLICY_CORE_INVALID")
    for item in policy["files"]:
        path = PROJECT / str(item.get("path", ""))
        if not path.is_file() or item.get("sha256") != file_sha256(path):
            raise RecoveryEnvelopeError("RECOVERY_POLICY_CORE_CHANGED")
    mandate = values["mandate"]
    if (mandate.get("active") is not False or mandate.get("mission_id") != MISSION_ID or
            mandate.get("mission_scope") != MISSION_SCOPE or mandate.get("autonomy_branch") != AUTONOMY_BRANCH or
            mandate.get("allowed_action_families") != list(ACTION_FAMILIES) or
            mandate.get("scientific_invariants") != binding(INVARIANTS) or
            mandate.get("recovery_graph") != binding(RECOVERY_GRAPH) or
            mandate.get("mutable_technical_surface") != binding(MUTABLE_SURFACE) or
            mandate.get("recovery_budget") != binding(RECOVERY_BUDGET) or
            mandate.get("policy_core_manifest") != binding(POLICY_MANIFEST)):
        raise RecoveryEnvelopeError("RECOVERY_MANDATE_PREMATURELY_ACTIVE")
    return values


def validate_candidate(path: Path) -> dict[str, object]:
    value = _load(path, "RECOVERY_CANDIDATE_INVALID")
    required = {"action_kind", "application_body_reservation", "authority_classes", "command_argv",
        "command_argv_sha256", "implementation_aggregate", "material_budget_reservation",
        "mutable_technical_surface", "network_request_reservation", "output_directory",
        "parent_action_terminal", "permit_path", "recovery_budget", "recovery_generation",
        "recovery_graph", "remaining_budgets", "request_class", "resume", "retries",
        "schema_version", "scientific_invariants", "sealed", "stage_id",
        "technical_budget_reservation", "technical_patch_manifest", "trigger_failure_class",
        "worker_argv", "worker_argv_sha256", "worker_capability_path"}
    if (set(value) != required or value.get("schema_version") != "RECOVERY_ACTION_FACTORY_V1" or
            value.get("action_kind") not in ACTION_FAMILIES or value.get("request_class") not in ("TECHNICAL", "MATERIAL", "OFFLINE") or
            value.get("resume") is not False or value.get("retries") != 0 or
            value.get("implementation_aggregate") != implementation_aggregate()):
        raise RecoveryEnvelopeError("RECOVERY_CANDIDATE_INVALID")
    expected = (("scientific_invariants", INVARIANTS), ("recovery_graph", RECOVERY_GRAPH),
        ("mutable_technical_surface", MUTABLE_SURFACE), ("recovery_budget", RECOVERY_BUDGET))
    if any(value[key] != binding(path_) for key, path_ in expected):
        raise RecoveryEnvelopeError("RECOVERY_CANDIDATE_AUTHORITY_MISMATCH")
    if (sha256_bytes(canonical(value["command_argv"])) != value["command_argv_sha256"] or
            sha256_bytes(canonical(value["worker_argv"])) != value["worker_argv_sha256"]):
        raise RecoveryEnvelopeError("RECOVERY_CANDIDATE_ARGV_MISMATCH")
    budget = _load(RECOVERY_BUDGET, "RECOVERY_BUDGET_INVALID")
    if (type(value["recovery_generation"]) is not int or value["recovery_generation"] < 1 or
            value["recovery_generation"] > budget["MAX_RECOVERY_GENERATIONS"]):
        raise RecoveryEnvelopeError("RECOVERY_GENERATION_LIMIT")
    if value["request_class"] == "TECHNICAL" and (
            value["network_request_reservation"] > budget["MAX_TECHNICAL_NETWORK_REQUESTS"] or
            value["application_body_reservation"] > budget["MAX_TECHNICAL_BODY_BYTES"] or
            value["application_body_reservation"] > budget["MAX_TECHNICAL_BODY_BYTES_PER_REQUEST"]):
        raise RecoveryEnvelopeError("TECHNICAL_BUDGET_OVERFLOW")
    return value


def validate_first_candidate(path: Path = FIRST_CANDIDATE) -> dict[str, object]:
    value = validate_candidate(path)
    if (value["action_kind"] != "TECHNICAL_RESPONSE_DIAGNOSTIC" or value["request_class"] != "TECHNICAL" or
            value["network_request_reservation"] != 1 or value["application_body_reservation"] != 65_536 or
            value["material_budget_reservation"] != {"body_bytes": 0, "requests": 0} or
            value["technical_budget_reservation"] != {"body_bytes": 65_536, "requests": 1}):
        raise RecoveryEnvelopeError("FIRST_RECOVERY_CANDIDATE_INVALID")
    return value


def validate_state(path: Path = STATE) -> dict[str, object]:
    value = _load(path, "RECOVERY_STATE_INVALID")
    required = {"active", "body_budget_material_parent", "code_repair_generation", "current_stage",
        "first_candidate", "last_action_terminal_sha256", "last_classification", "material_body_bytes_remaining",
        "material_requests_remaining", "mission_id", "mission_scope", "next_action_kind", "permits_issued",
        "recovery_generation", "registered_pending_action", "requests_material_parent", "schema_version", "sealed",
        "sequence", "scientific_outcome", "standing_authorization", "state", "stop_reason",
        "technical_body_bytes_remaining", "technical_failure_occurrences", "technical_requests_remaining"}
    if (set(value) != required or value.get("schema_version") != "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_001" or
            value.get("mission_id") != MISSION_ID or value.get("mission_scope") != MISSION_SCOPE):
        raise RecoveryEnvelopeError("RECOVERY_STATE_INVALID")
    if value["state"] == STATE_WAITING and (value["active"] is not False or value["standing_authorization"] is not None):
        raise RecoveryEnvelopeError("RECOVERY_WAITING_STATE_INVALID")
    if value["state"] == STATE_ACTIVE and value["active"] is not True:
        raise RecoveryEnvelopeError("RECOVERY_ACTIVE_STATE_INVALID")
    if value["state"] in (STATE_TERMINAL, STOP_REQUIRES_HUMAN) and value["active"] is not False:
        raise RecoveryEnvelopeError("RECOVERY_TERMINAL_STATE_INVALID")
    return value


def activate(*, state_path: Path, authorization_path: Path, activated_at_utc: str) -> dict[str, object]:
    state = validate_state(state_path); auth = _load(authorization_path, "RECOVERY_STANDING_AUTHORIZATION_INVALID")
    if state["state"] != STATE_WAITING or auth.get("authorized") is not True or auth.get("initial_state_sha256") != file_sha256(state_path):
        raise RecoveryEnvelopeError("RECOVERY_ACTIVATION_INVALID")
    body = {k: v for k, v in state.items() if k != "sealed"}
    body.update({"active": True, "current_stage": "AWAITING_NEXT_ACTION_REGISTRATION",
        "standing_authorization": binding(authorization_path), "state": STATE_ACTIVE,
        "sequence": state["sequence"] + 1})
    updated = sealed(body); _atomic_state(state_path, updated)
    return updated


def register_action(*, state_path: Path, candidate_path: Path) -> dict[str, object]:
    state = validate_state(state_path); candidate = validate_candidate(candidate_path)
    if state["state"] != STATE_ACTIVE or state["registered_pending_action"] is not None:
        raise RecoveryEnvelopeError("RECOVERY_ACTION_REGISTRATION_INVALID")
    expected_parent = state["last_action_terminal_sha256"]
    if expected_parent is not None and candidate["parent_action_terminal"]["sha256"] != expected_parent:
        raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")
    body = {k: v for k, v in state.items() if k != "sealed"}
    body.update({"current_stage": "ACTION_REGISTERED", "registered_pending_action": binding(candidate_path),
        "sequence": state["sequence"] + 1})
    updated = sealed(body); _atomic_state(state_path, updated)
    return updated


def issue_permit(*, state_path: Path, candidate_path: Path, output_path: Path,
                 issued_at_utc: str) -> dict[str, object]:
    state = validate_state(state_path); candidate = validate_candidate(candidate_path)
    if (state["registered_pending_action"] != binding(candidate_path) or
            output_path.resolve() != (PROJECT / candidate["permit_path"]).resolve() or output_path.exists()):
        raise RecoveryEnvelopeError("RECOVERY_PERMIT_ISSUANCE_INVALID")
    permit = sealed({"application_body_reservation": candidate["application_body_reservation"],
        "candidate_path": str(candidate_path.resolve().relative_to(PROJECT)),
        "candidate_sha256": file_sha256(candidate_path), "issued_at_utc": issued_at_utc,
        "network_request_reservation": candidate["network_request_reservation"],
        "permit_id": f"RECOVERY-PERMIT-{state['sequence']:06d}-{file_sha256(candidate_path)[:12]}",
        "request_class": candidate["request_class"],
        "schema_version": "OC3_AUTONOMOUS_RECOVERY_EXECUTION_PERMIT_001", "single_use": True,
        "stage_id": candidate["stage_id"], "state_before_sha256": file_sha256(state_path),
        "worker_argv_sha256": candidate["worker_argv_sha256"]})
    write_json_immutable(output_path, permit)
    return permit


def permit_consumption_path(permit_path: Path) -> Path:
    return PERMIT_CONSUMPTION / f"{file_sha256(permit_path)}.json"


def validate_permit(*, permit_path: Path, candidate_path: Path,
                    allow_consumed: bool = False) -> dict[str, object]:
    permit = _load(permit_path, "RECOVERY_PERMIT_INVALID")
    candidate = validate_candidate(candidate_path)
    required = {"application_body_reservation", "candidate_path", "candidate_sha256", "issued_at_utc",
        "network_request_reservation", "permit_id", "request_class", "schema_version", "sealed",
        "single_use", "stage_id", "state_before_sha256", "worker_argv_sha256"}
    if (set(permit) != required or permit.get("schema_version") != "OC3_AUTONOMOUS_RECOVERY_EXECUTION_PERMIT_001" or
            permit.get("candidate_sha256") != file_sha256(candidate_path) or
            permit.get("network_request_reservation") != candidate["network_request_reservation"] or
            permit.get("application_body_reservation") != candidate["application_body_reservation"] or
            permit.get("request_class") != candidate["request_class"] or
            permit.get("worker_argv_sha256") != candidate["worker_argv_sha256"] or permit.get("single_use") is not True):
        raise RecoveryEnvelopeError("RECOVERY_PERMIT_INVALID")
    if permit_consumption_path(permit_path).exists() and not allow_consumed:
        raise RecoveryEnvelopeError("RECOVERY_PERMIT_ALREADY_CONSUMED")
    return permit


def consume_permit(*, permit_path: Path, candidate_path: Path, consumed_at_utc: str) -> Path:
    permit = validate_permit(permit_path=permit_path, candidate_path=candidate_path)
    marker = permit_consumption_path(permit_path)
    if marker.exists():
        raise RecoveryEnvelopeError("RECOVERY_PERMIT_ALREADY_CONSUMED")
    write_json_immutable(marker, sealed({"candidate_sha256": file_sha256(candidate_path),
        "consumed_at_utc": consumed_at_utc, "permit_sha256": file_sha256(permit_path),
        "schema_version": "OC3_AUTONOMOUS_RECOVERY_PERMIT_CONSUMPTION_001"}))
    return marker


def capability_consumption_path(capability_path: Path) -> Path:
    return CAPABILITY_CONSUMPTION / f"{file_sha256(capability_path)}.json"


def create_worker_capability(*, candidate_path: Path, permit_path: Path,
        permit_marker: Path, authorization_path: Path, state_path: Path,
        capability_path: Path, issued_at_utc: str) -> dict[str, object]:
    candidate = validate_candidate(candidate_path)
    if (capability_path.resolve() != (PROJECT / candidate["worker_capability_path"]).resolve() or
            permit_marker.resolve() != permit_consumption_path(permit_path).resolve() or
            not permit_marker.is_file() or capability_path.exists()):
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_INVALID")
    capability = sealed({"application_body_reservation": candidate["application_body_reservation"],
        "authorization_sha256": file_sha256(authorization_path),
        "candidate_sha256": file_sha256(candidate_path), "issued_at_utc": issued_at_utc,
        "mission_id": MISSION_ID, "network_request_reservation": candidate["network_request_reservation"],
        "output_directory": candidate["output_directory"], "permit_sha256": file_sha256(permit_path),
        "request_class": candidate["request_class"],
        "schema_version": "OC3_AUTONOMOUS_RECOVERY_WORKER_CAPABILITY_001", "single_use": True,
        "stage_id": candidate["stage_id"], "state_sha256": file_sha256(state_path),
        "worker_argv_sha256": candidate["worker_argv_sha256"]})
    write_json_immutable(capability_path, capability)
    return capability


def validate_worker_capability(*, capability_path: Path, candidate_path: Path,
        permit_path: Path, authorization_path: Path, state_path: Path) -> dict[str, object]:
    capability = _load(capability_path, "RECOVERY_WORKER_CAPABILITY_INVALID")
    candidate = validate_candidate(candidate_path)
    required = {"application_body_reservation", "authorization_sha256", "candidate_sha256", "issued_at_utc",
        "mission_id", "network_request_reservation", "output_directory", "permit_sha256", "request_class",
        "schema_version", "sealed", "single_use", "stage_id", "state_sha256", "worker_argv_sha256"}
    if (set(capability) != required or capability.get("schema_version") != "OC3_AUTONOMOUS_RECOVERY_WORKER_CAPABILITY_001" or
            capability.get("candidate_sha256") != file_sha256(candidate_path) or
            capability.get("permit_sha256") != file_sha256(permit_path) or
            capability.get("authorization_sha256") != file_sha256(authorization_path) or
            capability.get("state_sha256") != file_sha256(state_path) or capability.get("mission_id") != MISSION_ID or
            capability.get("stage_id") != candidate["stage_id"] or
            capability.get("worker_argv_sha256") != candidate["worker_argv_sha256"] or
            capability.get("network_request_reservation") != candidate["network_request_reservation"] or
            capability.get("application_body_reservation") != candidate["application_body_reservation"] or
            capability.get("output_directory") != candidate["output_directory"] or capability.get("single_use") is not True):
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_INVALID")
    validate_permit(permit_path=permit_path, candidate_path=candidate_path, allow_consumed=True)
    if not permit_consumption_path(permit_path).is_file():
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_INVALID")
    if capability_consumption_path(capability_path).exists():
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_ALREADY_CONSUMED")
    return capability


def consume_worker_capability(*, capability_path: Path, candidate_path: Path,
                              consumed_at_utc: str) -> Path:
    capability = _load(capability_path, "RECOVERY_WORKER_CAPABILITY_INVALID")
    if capability.get("candidate_sha256") != file_sha256(candidate_path):
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_INVALID")
    marker = capability_consumption_path(capability_path)
    if marker.exists():
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_ALREADY_CONSUMED")
    write_json_immutable(marker, sealed({"candidate_sha256": file_sha256(candidate_path),
        "capability_sha256": file_sha256(capability_path), "consumed_at_utc": consumed_at_utc,
        "schema_version": "OC3_AUTONOMOUS_RECOVERY_CAPABILITY_CONSUMPTION_001"}))
    return marker


def transition_action(*, state_path: Path, candidate_path: Path, terminal_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    state = validate_state(state_path); candidate = validate_candidate(candidate_path)
    if state["registered_pending_action"] != binding(candidate_path):
        raise RecoveryEnvelopeError("RECOVERY_ACTION_TRANSITION_INVALID")
    terminal = _load(terminal_path, "RECOVERY_ACTION_TERMINAL_INVALID")
    terminal = dict(terminal); terminal["terminal_sha256"] = file_sha256(terminal_path)
    graph = _load(RECOVERY_GRAPH, "RECOVERY_GRAPH_INVALID")
    budget = _load(RECOVERY_BUDGET, "RECOVERY_BUDGET_INVALID")
    classification = classify_action_terminal(terminal, graph)
    updated = account_action(state, terminal, classification, budget)
    updated["permits_issued"] = state["permits_issued"] + 1
    sealed_state = sealed(updated); _atomic_state(state_path, sealed_state)
    return sealed_state, sealed(classification)


def finalize_mission(*, state_path: Path, outcome: str) -> dict[str, object]:
    state = validate_state(state_path)
    if state.get("current_stage") != "AWAITING_SCIENTIFIC_FINALIZATION":
        raise RecoveryEnvelopeError("RECOVERY_MISSION_FINALIZATION_INVALID")
    body = {k: v for k, v in state.items() if k != "sealed"}
    body.update({"active": False, "current_stage": STATE_TERMINAL, "scientific_outcome": outcome,
        "state": STATE_TERMINAL, "sequence": state["sequence"] + 1})
    updated = sealed(body); _atomic_state(state_path, updated)
    return updated
