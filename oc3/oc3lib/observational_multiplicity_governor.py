"""Deterministic lifecycle governor for the observational-multiplicity mission."""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import re
import subprocess

from .core import canonical
from .observational_multiplicity import (
    PROJECT, MultiplicityError, audit_implementation_aggregate, file_sha256, load_canonical_json, sealed,
    sha256_bytes, validate_sealed, write_json_immutable,
)


MISSION_ID = "OC3-OBSERVATIONAL-MULTIPLICITY-AUTONOMY-001"
MISSION_SCOPE = "OBSERVATIONAL_MULTIPLICITY_STRATEGY_ONLY"
AUTONOMY_BRANCH = "autopilot/observational-multiplicity"
STATE_WAITING = "WAITING_FOR_STANDING_HUMAN_AUTHORIZATION"
STATE_ACTIVE = "ACTIVE"
STATE_AWAITING = "AWAITING_NEXT_ACTION_REGISTRATION"
STATE_TERMINAL = "SCIENTIFIC_TERMINAL"
STOP_REQUIRES_HUMAN = "STOP_REQUIRES_HUMAN"
MANDATE_NOT_ACTIVE = "MANDATE_NOT_ACTIVE"
ELIGIBLE = "ELIGIBLE_FOR_AUTONOMOUS_PERMIT"
NO_PERMIT = "NO_PERMIT_ISSUED"

TERMINAL_OUTCOMES = (
    "OBSERVATIONAL_MULTIPLICITY_STRATEGY_SUPPORTED",
    "OBSERVATIONAL_MULTIPLICITY_REQUIRES_GROUPING_EVIDENCE",
    "OBSERVATIONAL_MULTIPLICITY_STRATEGY_INCONCLUSIVE",
    "OBSERVATIONAL_MULTIPLICITY_STRATEGY_REJECTED",
)
AUTHORITY_CLASSES = (
    "FROZEN_PROJECT_SPECIFICATIONS_AND_TERMINALS",
    "BOUND_LOCAL_DR9_BRICK_SUMMARY_IDENTITY_GEOMETRY",
    "BOUNDED_OFFICIAL_DR9_DOCUMENTATION",
    "PROSPECTIVELY_CONTRACTED_GROUPING_METADATA",
)
FIREWALL_KEYS = (
    "PHOTSYS_reads", "Tractor_cells_read", "source_rows_read", "image_pixels_read",
    "morphology_accesses", "label_accesses", "model_operations", "embedding_operations",
    "clustering_operations",
)
PROHIBITED_SCOPE_KEYS = (
    "photsys_reinterpretation", "photsys_v2_resolver", "panel_v3_materialization",
    "p1", "morphology_learning", "training", "embeddings", "clustering",
)

SPEC_PATH = PROJECT / "OC3_OBSERVATIONAL_MULTIPLICITY_RESEARCH_SPEC_001.md"
SPEC_SHA256 = "60d91adf66c7f5e84139021a5664de7058ef9e91f4daf23e8df429800eee1fe5"
MANDATE_DOCUMENT_PATH = PROJECT / "OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_MANDATE_001.md"
MANDATE_DOCUMENT_SHA256 = "c27440620a96df7d40d1a6dcd21a578e97f9c9ebe38885d9890ba3ac98f4bf7a"
RUNBOOK_PATH = PROJECT / "OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMOUS_RESEARCH_RUNBOOK_001.md"
RUNBOOK_SHA256 = "a2c068f75ee4f835b365b53e2c6a84e7a2ee6d6d1cbfc82d228f019187abb1ae"
POLICY_CONTRACT_PATH = PROJECT / "OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_POLICY_CORE_CONTRACT_001.md"
POLICY_CONTRACT_SHA256 = "62370b023a7f03d8505193c9d6eb98a5804ea3ab7d418378761a0e5e830a1d43"
POLICY_MANIFEST_PATH = PROJECT / "oc3/INPUTS/OC3_OBSERVATIONAL_MULTIPLICITY_POLICY_CORE_MANIFEST_001.json"
MANDATE_PATH = PROJECT / "oc3/INPUTS/OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_MANDATE_001.json"
STATE_PATH = PROJECT / "oc3/OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_STATE_001.json"
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_OBSERVATIONAL_MULTIPLICITY_STANDING_AUTHORIZATION_001.json"
FIRST_CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_001.json"
LEDGER_ROOT = PROJECT / "oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_LEDGER"
POLICY_MEMBERS = (
    "OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_POLICY_CORE_CONTRACT_001.md",
    "oc3/oc3_observational_multiplicity_governor.py",
    "oc3/oc3lib/observational_multiplicity_governor.py",
)


class GovernorError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _relative(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(PROJECT))
    except ValueError as exc:
        raise GovernorError("PATH_OUTSIDE_PROJECT") from exc


def _binding(path: Path) -> dict[str, str]:
    return {"path": _relative(path), "sha256": file_sha256(path)}


def _utc(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise GovernorError("TIMESTAMP_INVALID")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise GovernorError("TIMESTAMP_INVALID") from exc
    return value


def _load(path: Path, code: str) -> dict[str, object]:
    try:
        return validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise GovernorError(code) from exc


def _current_branch() -> str:
    result = subprocess.run(["git", "branch", "--show-current"], cwd=PROJECT,
                            text=True, capture_output=True, check=True)
    return result.stdout.strip()


def _replace_state(path: Path, value: dict[str, object]) -> None:
    """Atomically replace only the governed mutable state artifact."""
    data = canonical(value) + b"\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def candidate_payload(candidate: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in candidate.items() if key not in ("autonomy_policy", "sealed")}


def validate_policy_manifest(path: Path = POLICY_MANIFEST_PATH) -> dict[str, object]:
    value = _load(path, "POLICY_CORE_MANIFEST_INVALID")
    if (set(value) != {"active_mutation_result", "contract", "files", "schema_version", "sealed"} or
            value.get("schema_version") != "OC3_OBSERVATIONAL_MULTIPLICITY_POLICY_CORE_MANIFEST_001" or
            value.get("active_mutation_result") != STOP_REQUIRES_HUMAN):
        raise GovernorError("POLICY_CORE_MANIFEST_INVALID")
    if value.get("contract") != _binding(POLICY_CONTRACT_PATH):
        raise GovernorError("POLICY_CORE_MISMATCH")
    files = value.get("files")
    if not isinstance(files, list) or {item.get("path") for item in files if isinstance(item, dict)} != set(POLICY_MEMBERS):
        raise GovernorError("POLICY_CORE_MANIFEST_INVALID")
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise GovernorError("POLICY_CORE_MANIFEST_INVALID")
        path = PROJECT / item["path"]
        if not path.is_file() or file_sha256(path) != item["sha256"]:
            raise GovernorError("POLICY_CORE_MISMATCH")
    return value


def validate_mandate(path: Path = MANDATE_PATH) -> dict[str, object]:
    value = _load(path, "AUTONOMY_MANDATE_INVALID")
    required = {
        "active", "allowed_authority_classes", "allowed_scientific_outcomes",
        "authorization_state", "autonomy_branch", "budgets", "firewall",
        "governing_specification", "mandate_document", "mission_id", "mission_scope",
        "policy_core_manifest", "prohibited_scopes", "runbook", "schema_version",
        "sealed", "standing_authorization_path", "stop_state",
    }
    if (set(value) != required or value.get("schema_version") != "OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_MANDATE_001" or
            value.get("active") is not False or value.get("authorization_state") != "PENDING_HUMAN_AUTHORIZATION" or
            value.get("mission_id") != MISSION_ID or value.get("mission_scope") != MISSION_SCOPE or
            value.get("autonomy_branch") != AUTONOMY_BRANCH or
            tuple(value.get("allowed_authority_classes", ())) != AUTHORITY_CLASSES or
            tuple(value.get("allowed_scientific_outcomes", ())) != TERMINAL_OUTCOMES or
            tuple(value.get("prohibited_scopes", ())) != PROHIBITED_SCOPE_KEYS or
            value.get("stop_state") != STOP_REQUIRES_HUMAN or
            value.get("standing_authorization_path") != _relative(AUTHORIZATION_PATH)):
        raise GovernorError("AUTONOMY_MANDATE_INVALID")
    if value.get("budgets") != {
        "application_body_bytes_parent": 16_777_216,
        "application_body_bytes_remaining": 16_777_216,
        "concurrency": 1,
        "network_requests_parent": 12,
        "network_requests_remaining": 12,
        "retries_default": 0,
        "retries_max_per_exact_resource": 1,
    } or value.get("firewall") != {key: 0 for key in FIREWALL_KEYS}:
        raise GovernorError("AUTONOMY_MANDATE_INVALID")
    expected = {
        "governing_specification": _binding(SPEC_PATH), "mandate_document": _binding(MANDATE_DOCUMENT_PATH),
        "policy_core_manifest": _binding(POLICY_MANIFEST_PATH), "runbook": _binding(RUNBOOK_PATH),
    }
    for key, binding in expected.items():
        if value.get(key) != binding:
            raise GovernorError("AUTONOMY_MANDATE_AUTHORITY_MISMATCH")
    validate_policy_manifest()
    return value


def validate_state(path: Path = STATE_PATH) -> dict[str, object]:
    value = _load(path, "AUTONOMY_STATE_INVALID")
    required = {
        "active", "autonomy_branch", "body_budget_parent", "body_budget_remaining",
        "current_stage", "firewall_counters", "last_completed_stage", "last_terminal",
        "mandate", "mission_id", "permits_issued", "policy_core_manifest",
        "registered_pending_action", "request_budget_parent", "requests_remaining",
        "schema_version", "scientific_outcome", "scientific_question", "sealed",
        "sequence", "standing_authorization", "standing_authorization_path", "state",
        "stop_reason", "terminal_outcomes",
    }
    if (set(value) != required or value.get("schema_version") != "OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_STATE_001" or
            value.get("mission_id") != MISSION_ID or value.get("autonomy_branch") != AUTONOMY_BRANCH or
            tuple(value.get("terminal_outcomes", ())) != TERMINAL_OUTCOMES or
            value.get("mandate") != _binding(MANDATE_PATH) or
            value.get("policy_core_manifest") != _binding(POLICY_MANIFEST_PATH) or
            value.get("standing_authorization_path") != _relative(AUTHORIZATION_PATH) or
            type(value.get("sequence")) is not int or value["sequence"] < 0 or
            type(value.get("permits_issued")) is not int or value["permits_issued"] < 0 or
            value.get("request_budget_parent") != 12 or value.get("body_budget_parent") != 16_777_216 or
            type(value.get("requests_remaining")) is not int or not 0 <= value["requests_remaining"] <= 12 or
            type(value.get("body_budget_remaining")) is not int or not 0 <= value["body_budget_remaining"] <= 16_777_216 or
            value.get("firewall_counters") != {key: 0 for key in FIREWALL_KEYS}):
        raise GovernorError("AUTONOMY_STATE_INVALID")
    state = value.get("state")
    if state == STATE_WAITING:
        if value.get("active") is not False or value.get("standing_authorization") is not None or value.get("permits_issued") != 0:
            raise GovernorError("AUTONOMY_WAITING_STATE_INVALID")
    elif state in (STATE_ACTIVE, STATE_AWAITING):
        if value.get("active") is not True or not isinstance(value.get("standing_authorization"), dict):
            raise GovernorError("AUTONOMY_ACTIVE_STATE_INVALID")
    elif state in (STOP_REQUIRES_HUMAN, STATE_TERMINAL):
        if value.get("active") is not False:
            raise GovernorError("AUTONOMY_TERMINAL_STATE_INVALID")
    else:
        raise GovernorError("AUTONOMY_STATE_INVALID")
    return value


def validate_action_receipt(binding: object, contract: dict[str, object]) -> dict[str, object]:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise GovernorError("ACTION_VALIDATION_RECEIPT_INVALID")
    path = PROJECT / str(binding["path"])
    if not path.is_file() or file_sha256(path) != binding["sha256"]:
        raise GovernorError("ACTION_VALIDATION_RECEIPT_INVALID")
    receipt = _load(path, "ACTION_VALIDATION_RECEIPT_INVALID")
    validator = receipt.get("validator")
    if (not isinstance(validator, dict) or set(validator) != {"path", "sha256"} or
            not (PROJECT / str(validator["path"])).is_file() or
            file_sha256(PROJECT / str(validator["path"])) != validator["sha256"] or
            receipt.get("implementation_aggregate") != audit_implementation_aggregate() or
            receipt.get("validated") is not True or receipt.get("network_requests") != 0 or
            receipt.get("candidate_payload_sha256") != contract.get("candidate_payload_sha256") or
            receipt.get("stage_id") != contract.get("stage_id") or receipt.get("scope") != contract.get("scope")):
        raise GovernorError("ACTION_VALIDATION_RECEIPT_INVALID")
    return receipt


def validate_candidate(path: Path = FIRST_CANDIDATE_PATH) -> tuple[dict[str, object], dict[str, object]]:
    candidate = _load(path, "AUTONOMOUS_ACTION_CANDIDATE_INVALID")
    contract = candidate.get("autonomy_policy")
    required = {
        "action_kind", "action_validation_receipt", "application_body_reservation",
        "authority_classes_used", "candidate_hash_mode", "candidate_payload_sha256",
        "command_argv_sha256", "concurrency", "git_branch", "implementation_aggregate",
        "mission_id", "network_request_reservation", "permit_output_path", "permit_required",
        "prohibited_scope_assertions", "resume", "retry_reservation", "schema_version",
        "scientific_firewall", "scope", "stage_id", "standing_mandate_sha256",
    }
    if (not isinstance(contract, dict) or set(contract) != required or
            contract.get("schema_version") != "OC3_OBSERVATIONAL_MULTIPLICITY_ACTION_CONTRACT_001" or
            contract.get("mission_id") != MISSION_ID or contract.get("git_branch") != AUTONOMY_BRANCH or
            contract.get("candidate_hash_mode") != "CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED" or
            contract.get("candidate_payload_sha256") != sha256_bytes(canonical(candidate_payload(candidate))) or
            contract.get("command_argv_sha256") != candidate.get("command_argv_sha256") or
            contract.get("implementation_aggregate") != candidate.get("implementation_aggregate") or
            contract.get("implementation_aggregate") != audit_implementation_aggregate() or
            contract.get("stage_id") != candidate.get("stage_id") or contract.get("scope") != candidate.get("scope") or
            contract.get("standing_mandate_sha256") != file_sha256(MANDATE_PATH) or
            contract.get("permit_required") is not True or contract.get("resume") is not False or
            contract.get("network_request_reservation") != 0 or contract.get("application_body_reservation") != 0 or
            contract.get("retry_reservation") != 0 or contract.get("concurrency") != 1 or
            tuple(contract.get("authority_classes_used", ())) != AUTHORITY_CLASSES[:2] or
            contract.get("scientific_firewall") != {key: 0 for key in FIREWALL_KEYS} or
            contract.get("prohibited_scope_assertions") != {key: False for key in PROHIBITED_SCOPE_KEYS}):
        raise GovernorError("AUTONOMOUS_ACTION_CONTRACT_INVALID")
    validate_action_receipt(contract.get("action_validation_receipt"), contract)
    return candidate, contract


def validate_standing_authorization(path: Path, expected_state_sha256: str,
                                    expected_candidate_sha256: str) -> dict[str, object]:
    value = _load(path, "STANDING_AUTHORIZATION_INVALID")
    required = {
        "authorization_state", "authorized", "authorized_at_utc", "authorized_by",
        "branch", "first_candidate_path", "first_candidate_sha256", "initial_state_path",
        "initial_state_sha256", "mandate_path", "mandate_sha256", "mission_id",
        "policy_core_manifest_path", "policy_core_manifest_sha256", "schema_version", "sealed",
    }
    if (set(value) != required or value.get("schema_version") != "OC3_OBSERVATIONAL_MULTIPLICITY_STANDING_AUTHORIZATION_001" or
            value.get("authorization_state") != "STANDING_HUMAN_AUTONOMY_AUTHORIZATION" or
            value.get("authorized") is not True or not str(value.get("authorized_by", "")).strip() or
            value.get("branch") != AUTONOMY_BRANCH or value.get("mission_id") != MISSION_ID or
            value.get("mandate_path") != _relative(MANDATE_PATH) or value.get("mandate_sha256") != file_sha256(MANDATE_PATH) or
            value.get("policy_core_manifest_path") != _relative(POLICY_MANIFEST_PATH) or
            value.get("policy_core_manifest_sha256") != file_sha256(POLICY_MANIFEST_PATH) or
            value.get("initial_state_path") != _relative(STATE_PATH) or value.get("initial_state_sha256") != expected_state_sha256 or
            value.get("first_candidate_path") != _relative(FIRST_CANDIDATE_PATH) or
            value.get("first_candidate_sha256") != expected_candidate_sha256):
        raise GovernorError("STANDING_AUTHORIZATION_INVALID")
    _utc(value.get("authorized_at_utc"))
    return value


def validate_all() -> dict[str, object]:
    validate_policy_manifest(); validate_mandate(); state = validate_state(); validate_candidate()
    return {"active": state["active"], "network_requests": 0, "permits_issued": state["permits_issued"],
            "state": state["state"], "validated": True}


def evaluate_candidate(candidate_path: Path = FIRST_CANDIDATE_PATH,
                       state_path: Path = STATE_PATH) -> dict[str, object]:
    validate_policy_manifest(); validate_mandate(); candidate, contract = validate_candidate(candidate_path)
    state = validate_state(state_path)
    if not state["active"]:
        return {"decision": MANDATE_NOT_ACTIVE, "permit_state": NO_PERMIT}
    if state["registered_pending_action"] is None or state["registered_pending_action"].get("sha256") != file_sha256(candidate_path):
        return {"decision": "ACTION_NOT_REGISTERED", "permit_state": NO_PERMIT}
    if contract["network_request_reservation"] > state["requests_remaining"] or contract["application_body_reservation"] > state["body_budget_remaining"]:
        return {"decision": "MISSION_BUDGET_EXCEEDED", "permit_state": NO_PERMIT}
    return {"decision": ELIGIBLE, "permit_state": NO_PERMIT, "stage_id": candidate["stage_id"]}


def activate(*, activated_at_utc: str, authorization_path: Path = AUTHORIZATION_PATH,
             state_path: Path = STATE_PATH) -> dict[str, object]:
    validate_policy_manifest(); validate_mandate(); validate_candidate()
    state = validate_state(state_path)
    if state["state"] != STATE_WAITING:
        raise GovernorError("ACTIVATION_STATE_INVALID")
    authorization = validate_standing_authorization(authorization_path, file_sha256(state_path),
                                                     file_sha256(FIRST_CANDIDATE_PATH))
    if _current_branch() != AUTONOMY_BRANCH:
        raise GovernorError("AUTONOMY_BRANCH_MISMATCH")
    body = {key: value for key, value in state.items() if key != "sealed"}
    body.update({"active": True, "current_stage": "AWAITING_FIRST_ACTION_REGISTRATION",
                 "sequence": state["sequence"] + 1, "standing_authorization": _binding(authorization_path),
                 "state": STATE_AWAITING})
    _utc(activated_at_utc)
    _replace_state(state_path, sealed(body))
    return body


def register_action(*, candidate_path: Path, registered_at_utc: str,
                    state_path: Path = STATE_PATH) -> dict[str, object]:
    candidate, _ = validate_candidate(candidate_path); state = validate_state(state_path)
    if not state["active"] or state["registered_pending_action"] is not None:
        raise GovernorError("ACTION_REGISTRATION_STATE_INVALID")
    if _current_branch() != AUTONOMY_BRANCH:
        raise GovernorError("AUTONOMY_BRANCH_MISMATCH")
    _utc(registered_at_utc)
    body = {key: value for key, value in state.items() if key != "sealed"}
    body.update({"current_stage": candidate["stage_id"], "registered_pending_action": {
        "path": _relative(candidate_path), "sha256": file_sha256(candidate_path),
        "stage_id": candidate["stage_id"], "scope": candidate["scope"],
    }, "sequence": state["sequence"] + 1, "state": STATE_ACTIVE})
    _replace_state(state_path, sealed(body)); return body


def issue_permit(*, candidate_path: Path, output_path: Path, issued_at_utc: str,
                 state_path: Path = STATE_PATH) -> dict[str, object]:
    candidate, contract = validate_candidate(candidate_path); state = validate_state(state_path)
    decision = evaluate_candidate(candidate_path, state_path)
    if decision["decision"] != ELIGIBLE or _relative(output_path) != contract["permit_output_path"]:
        raise GovernorError("PERMIT_NOT_ELIGIBLE")
    _utc(issued_at_utc)
    permit = sealed({
        "application_body_reservation": 0, "candidate_path": _relative(candidate_path),
        "candidate_sha256": file_sha256(candidate_path), "consumed": False,
        "issued_at_utc": issued_at_utc, "mandate_sha256": file_sha256(MANDATE_PATH),
        "mission_id": MISSION_ID, "network_request_reservation": 0,
        "schema_version": "OC3_OBSERVATIONAL_MULTIPLICITY_EXECUTION_PERMIT_001",
        "scope": candidate["scope"], "stage_id": candidate["stage_id"],
        "state_sha256": file_sha256(state_path),
    })
    write_json_immutable(output_path, permit)
    return permit


def validate_permit(permit_path: Path, *, candidate_path: Path,
                    state_path: Path = STATE_PATH) -> dict[str, object]:
    permit = _load(permit_path, "PERMIT_INVALID")
    state = validate_state(state_path); candidate, _ = validate_candidate(candidate_path)
    if (permit.get("schema_version") != "OC3_OBSERVATIONAL_MULTIPLICITY_EXECUTION_PERMIT_001" or
            permit.get("mission_id") != MISSION_ID or permit.get("consumed") is not False or
            permit.get("candidate_path") != _relative(candidate_path) or
            permit.get("candidate_sha256") != file_sha256(candidate_path) or
            permit.get("state_sha256") != file_sha256(state_path) or
            permit.get("stage_id") != candidate["stage_id"] or permit.get("scope") != candidate["scope"] or
            state["registered_pending_action"].get("sha256") != file_sha256(candidate_path)):
        raise GovernorError("PERMIT_INVALID")
    return permit


def consume_permit(permit_path: Path, *, candidate_path: Path, consumption_path: Path,
                   consumed_at_utc: str, state_path: Path = STATE_PATH) -> dict[str, object]:
    permit = validate_permit(permit_path, candidate_path=candidate_path, state_path=state_path)
    _utc(consumed_at_utc)
    receipt = sealed({"candidate_sha256": permit["candidate_sha256"],
                      "consumed_at_utc": consumed_at_utc, "permit_sha256": file_sha256(permit_path),
                      "schema_version": "OC3_OBSERVATIONAL_MULTIPLICITY_PERMIT_CONSUMPTION_001",
                      "stage_id": permit["stage_id"]})
    write_json_immutable(consumption_path, receipt); return receipt


def transition_completed(*, candidate_path: Path, permit_path: Path, consumption_path: Path,
                         terminal_path: Path, request_delta: int, body_delta: int,
                         transitioned_at_utc: str, state_path: Path = STATE_PATH) -> dict[str, object]:
    state = validate_state(state_path); candidate, contract = validate_candidate(candidate_path)
    permit = _load(permit_path, "PERMIT_INVALID"); receipt = _load(consumption_path, "PERMIT_CONSUMPTION_MISSING")
    terminal = _load(terminal_path, "TERMINAL_INVALID"); _utc(transitioned_at_utc)
    if (receipt.get("permit_sha256") != file_sha256(permit_path) or
            terminal.get("stage_id") != candidate["stage_id"] or terminal.get("scope") != candidate["scope"] or
            request_delta != 0 or body_delta != 0 or request_delta > contract["network_request_reservation"] or
            body_delta > contract["application_body_reservation"]):
        raise GovernorError("COMPLETION_TRANSITION_INVALID")
    body = {key: value for key, value in state.items() if key != "sealed"}
    body.update({"body_budget_remaining": state["body_budget_remaining"] - body_delta,
                 "current_stage": "AWAITING_NEXT_ACTION_REGISTRATION",
                 "last_completed_stage": candidate["stage_id"], "last_terminal": _binding(terminal_path),
                 "permits_issued": state["permits_issued"] + 1, "registered_pending_action": None,
                 "requests_remaining": state["requests_remaining"] - request_delta,
                 "sequence": state["sequence"] + 1, "state": STATE_AWAITING})
    _replace_state(state_path, sealed(body)); return body


def enter_stop(*, blocker_code: str, report_path: Path, stopped_at_utc: str,
               state_path: Path = STATE_PATH) -> dict[str, object]:
    state = validate_state(state_path); _utc(stopped_at_utc)
    if not blocker_code or not report_path.is_file():
        raise GovernorError("STOP_EVIDENCE_INVALID")
    body = {key: value for key, value in state.items() if key != "sealed"}
    body.update({"active": False, "current_stage": STOP_REQUIRES_HUMAN,
                 "sequence": state["sequence"] + 1, "state": STOP_REQUIRES_HUMAN,
                 "stop_reason": {"blocker_code": blocker_code, "report": _binding(report_path)}})
    _replace_state(state_path, sealed(body)); return body


def finalize(*, outcome: str, report_path: Path, finalized_at_utc: str,
             state_path: Path = STATE_PATH) -> dict[str, object]:
    state = validate_state(state_path); _utc(finalized_at_utc)
    if outcome not in TERMINAL_OUTCOMES or state["registered_pending_action"] is not None or not report_path.is_file():
        raise GovernorError("SCIENTIFIC_TERMINAL_INVALID")
    body = {key: value for key, value in state.items() if key != "sealed"}
    body.update({"active": False, "current_stage": STATE_TERMINAL,
                 "last_terminal": _binding(report_path), "scientific_outcome": outcome,
                 "sequence": state["sequence"] + 1, "state": STATE_TERMINAL})
    _replace_state(state_path, sealed(body)); return body
