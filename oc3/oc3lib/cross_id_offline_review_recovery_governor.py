"""Deterministic lifecycle/policy engine for bounded OC3 autonomy.

The governor checks the standing envelope only. Action-specific validators
remain responsible for scientific and transport correctness. No network API
exists in this module.
"""
from __future__ import annotations
from datetime import datetime
import os
from pathlib import Path
import re
import subprocess

from .core import canonical
from .cross_observer_grouping import (
    PROJECT, audit_implementation_aggregate, file_sha256, load_canonical_json,
    sealed, sha256_bytes, validate_sealed, write_json_immutable,
)

MISSION_ID = "OC3-CROSS-ID-OFFLINE-REVIEW-RECOVERY-AUTONOMY-001"
MISSION_SCOPE = "OFFLINE_PRIMARY_EVIDENCE_REVIEW_RECOVERY_ONLY"
AUTONOMY_BRANCH = "autopilot/cross-id-offline-review-recovery"
STATE_WAITING = "WAITING_FOR_STANDING_HUMAN_AUTHORIZATION"
STATE_ACTIVE = "ACTIVE"
STATE_AWAITING = "AWAITING_NEXT_ACTION_REGISTRATION"
STATE_TERMINAL = "SCIENTIFIC_TERMINAL"
STOP_REQUIRES_HUMAN = "STOP_REQUIRES_HUMAN"
MANDATE_NOT_ACTIVE = "MANDATE_NOT_ACTIVE"
NO_PERMIT_ISSUED = "NO_PERMIT_ISSUED"
NO_PERMIT = NO_PERMIT_ISSUED
ELIGIBLE = "ELIGIBLE_FOR_AUTONOMOUS_PERMIT"

SCIENTIFIC_SPEC_PATH = PROJECT / "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_SPEC_001.md"
SCIENTIFIC_SPEC_SHA256 = "dd0a9d4eb03036e06540be6b8173b4703f889df501f6a356d13f60fb9d641ed9"
POLICY_CORE_CONTRACT_PATH = PROJECT / "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_POLICY_CORE_CONTRACT_001.md"
POLICY_CORE_MANIFEST_PATH = PROJECT / "oc3/INPUTS/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_POLICY_CORE_MANIFEST_001.json"
MANDATE_DOCUMENT_PATH = PROJECT / "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_MANDATE_001.md"
MANDATE_PATH = PROJECT / "oc3/INPUTS/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_MANDATE_001.json"
RUNBOOK_PATH = PROJECT / "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMOUS_RESEARCH_RUNBOOK_001.md"
STANDING_AUTHORIZATION_PATH = PROJECT / "oc3/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_STANDING_AUTHORIZATION_001.json"
AUTHORIZATION_PATH = STANDING_AUTHORIZATION_PATH
STATE_PATH = PROJECT / "oc3/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_STATE_001.json"
LEDGER_ROOT = PROJECT / "oc3/CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_LEDGER"
CONSUMPTION_ROOT = LEDGER_ROOT / "PERMIT_CONSUMPTION"
PRIOR_FINAL_REPORT_PATH = PROJECT / "OC3_CROSS_ID_FORMALISM_RECOVERY_AUTHORIZED_EXECUTION_REPORT_001.md"
PRIOR_FINAL_REPORT_SHA256 = "6d1a0f66ce56649ba11eb2bd9796d6b7bdfaba92cdd6e37ca27e0c2720cd842e"
PRIOR_CLAIM_MATRIX_PATH = PROJECT / "OC3_CROSS_ID_FORMALISM_RECOVERY_STOP_REPORT_001.md"
PRIOR_CLAIM_MATRIX_SHA256 = "496b21aacfc894f2f62016741ff86c0780d55be453d3d603a97fe3de398b8d2c"
PRIOR_TERMINAL_STATE_PATH = PROJECT / "oc3/OC3_CROSS_ID_FORMALISM_RECOVERY_AUTONOMY_STATE_001.json"
PRIOR_TERMINAL_STATE_SHA256 = "71bf4d98174f06655e256d5ea09c76743906191740acd250ca798bebd29f994f"
PRIOR_STOP_LEDGER_PATH = PROJECT / "oc3/CROSS_ID_FORMALISM_RECOVERY_AUTONOMY_LEDGER/000005_STOP.json"
PRIOR_STOP_LEDGER_SHA256 = "c6458dacaa066cf97444539c9539d8688fad52f9e2aa623084865c7c5b81b38a"

TERMINAL_OUTCOMES = (
    "CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE",
    "CROSS_ID_FORMALISM_RECOVERED_PILOT_STILL_UNRESOLVED",
    "CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE",
    "CROSS_ID_FORMALISM_CONFLICT",
)
AUTHORITY_CLASSES = (
    "FROZEN_PROJECT_TERMINALS_AND_SPECIFICATIONS",
    "BOUND_LOCAL_PRIMARY_LITERATURE_SNAPSHOTS",
)
FIREWALL_KEYS = (
    "PHOTSYS_reads", "TYPE_values_read", "DCHISQ_values_read", "Sersic_shape_values_read",
    "photometric_values_read", "photoz_values_read", "source_rows_read", "image_pixels_read",
    "morphology_accesses", "label_accesses", "model_operations", "training_operations",
    "embedding_operations", "clustering_operations", "panel_v3_operations", "p1_operations",
    "network_requests", "matching_operations", "search_bound_selections",
    "scientific_threshold_selections",
)
PROHIBITED_SCOPE_KEYS = (
    "photsys_reinterpretation", "source_row_query_without_explicit_contract",
    "tractor_bulk_acquisition", "panel_v3_materialization", "p1", "morphology_learning",
    "training", "embeddings", "clustering", "image_or_pixel_access", "label_access",
    "matching", "search_bound_selection", "scientific_threshold_selection",
)
POLICY_CORE_MEMBERS = (
    "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_POLICY_CORE_CONTRACT_001.md",
    "oc3/oc3_cross_id_offline_review_recovery_governor.py",
    "oc3/oc3lib/cross_id_offline_review_recovery_governor.py",
)
COMPACT_ARTIFACT_MAX_BYTES = 5 * 1024 * 1024
RUNTIME_TREE_PREFIXES = ("oc3/cross_id_formalism_recovery/", "oc3/cross_id_offline_review_recovery/")
FORBIDDEN_GIT_SUFFIXES = (".fit", ".fits", ".fits.gz", ".tar", ".tar.gz", ".tgz", ".zip")
SECRET_NAME_PARTS = ("credential", "private_key", "secret", "token")
SECRET_CONTENT_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
)

class GovernorError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

def _sha(value: object, code: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise GovernorError(code)
    return value

def _utc(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise GovernorError("AUTONOMY_TIMESTAMP_INVALID")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise GovernorError("AUTONOMY_TIMESTAMP_INVALID") from exc
    return value

def _load_sealed(path: Path, code: str) -> dict[str, object]:
    try:
        return validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise GovernorError(code) from exc

def _relative(path: Path, code: str = "AUTONOMY_PATH_OUTSIDE_PROJECT") -> str:
    try:
        return str(Path(path).resolve().relative_to(PROJECT))
    except ValueError as exc:
        raise GovernorError(code) from exc

def _binding(path: Path) -> dict[str, str]:
    return {"path": _relative(path), "sha256": file_sha256(path)}

def _refusal(code: str) -> dict[str, object]:
    return {"decision": code, "permit_state": NO_PERMIT_ISSUED}

def validate_policy_core_manifest(path: Path = POLICY_CORE_MANIFEST_PATH) -> dict[str, object]:
    value = _load_sealed(path, "POLICY_CORE_MANIFEST_INVALID")
    if (set(value) != {"active_mutation_result", "contract", "files", "schema_version", "sealed"} or
            value.get("schema_version") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_POLICY_CORE_MANIFEST_001" or
            value.get("active_mutation_result") != STOP_REQUIRES_HUMAN):
        raise GovernorError("POLICY_CORE_MANIFEST_INVALID")
    contract = value.get("contract", {})
    if (contract.get("path") != _relative(POLICY_CORE_CONTRACT_PATH) or
            contract.get("sha256") != file_sha256(POLICY_CORE_CONTRACT_PATH)):
        raise GovernorError("POLICY_CORE_MISMATCH")
    files = value.get("files")
    if not isinstance(files, list) or {i.get("path") for i in files if isinstance(i, dict)} != set(POLICY_CORE_MEMBERS):
        raise GovernorError("POLICY_CORE_MANIFEST_INVALID")
    for item in files:
        if set(item) != {"path", "sha256"}:
            raise GovernorError("POLICY_CORE_MANIFEST_INVALID")
        member = PROJECT / str(item["path"])
        if not member.is_file() or item["sha256"] != file_sha256(member):
            raise GovernorError("POLICY_CORE_MISMATCH")
    return value

def validate_mandate(path: Path = MANDATE_PATH) -> dict[str, object]:
    value = _load_sealed(path, "AUTONOMY_MANDATE_INVALID")
    required = {"active", "allowed_authority_classes", "allowed_scientific_outcomes",
        "authorization_state", "autonomous_action_contract", "autonomy_branch", "budgets",
        "firewall", "governing_specification", "mandate_document", "mission_id", "mission_scope",
        "policy_core_manifest", "prohibited_scopes", "runbook", "schema_version", "sealed",
        "standing_authorization_path", "stop_state"}
    if (set(value) != required or value.get("schema_version") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_MANDATE_001" or
            value.get("authorization_state") != "PENDING_HUMAN_AUTHORIZATION" or value.get("active") is not False or
            value.get("mission_id") != MISSION_ID or value.get("mission_scope") != MISSION_SCOPE or
            value.get("autonomy_branch") != AUTONOMY_BRANCH or
            tuple(value.get("allowed_scientific_outcomes", [])) != TERMINAL_OUTCOMES or
            tuple(value.get("allowed_authority_classes", [])) != AUTHORITY_CLASSES or
            tuple(value.get("prohibited_scopes", [])) != PROHIBITED_SCOPE_KEYS or
            value.get("autonomous_action_contract") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_ACTION_CONTRACT_001" or
            value.get("stop_state") != STOP_REQUIRES_HUMAN):
        raise GovernorError("AUTONOMY_MANDATE_INVALID")
    if value.get("budgets") != {"application_body_bytes_parent":0,
        "application_body_bytes_remaining":0,"concurrency":1,
        "network_requests_parent":0,"network_requests_remaining":0,
        "retries_default":0,"retries_max_per_exact_resource":0}:
        raise GovernorError("AUTONOMY_MANDATE_BUDGET_INVALID")
    if value.get("firewall") != {key: 0 for key in FIREWALL_KEYS}:
        raise GovernorError("AUTONOMY_MANDATE_FIREWALL_INVALID")
    manifest = value.get("policy_core_manifest", {})
    if manifest.get("path") != _relative(POLICY_CORE_MANIFEST_PATH) or manifest.get("sha256") != file_sha256(POLICY_CORE_MANIFEST_PATH):
        raise GovernorError("AUTONOMY_MANDATE_POLICY_CORE_MISMATCH")
    validate_policy_core_manifest()
    for key, actual in (("governing_specification", SCIENTIFIC_SPEC_PATH),
                        ("mandate_document", MANDATE_DOCUMENT_PATH), ("runbook", RUNBOOK_PATH)):
        binding = value.get(key, {})
        if binding.get("path") != _relative(actual) or binding.get("sha256") != file_sha256(actual):
            raise GovernorError("AUTONOMY_MANDATE_AUTHORITY_MISMATCH")
    return value

def validate_static_authorities() -> dict[str, str]:
    for path, digest in (
            (SCIENTIFIC_SPEC_PATH, SCIENTIFIC_SPEC_SHA256),
            (PRIOR_FINAL_REPORT_PATH, PRIOR_FINAL_REPORT_SHA256),
            (PRIOR_CLAIM_MATRIX_PATH, PRIOR_CLAIM_MATRIX_SHA256),
            (PRIOR_TERMINAL_STATE_PATH, PRIOR_TERMINAL_STATE_SHA256),
            (PRIOR_STOP_LEDGER_PATH, PRIOR_STOP_LEDGER_SHA256)):
        if not path.is_file() or file_sha256(path) != digest:
            raise GovernorError("AUTONOMY_STATIC_AUTHORITY_MISMATCH")
    validate_policy_core_manifest(); validate_mandate()
    return {_relative(SCIENTIFIC_SPEC_PATH):SCIENTIFIC_SPEC_SHA256,
            _relative(PRIOR_FINAL_REPORT_PATH):PRIOR_FINAL_REPORT_SHA256,
            _relative(PRIOR_CLAIM_MATRIX_PATH):PRIOR_CLAIM_MATRIX_SHA256,
            _relative(PRIOR_TERMINAL_STATE_PATH):PRIOR_TERMINAL_STATE_SHA256,
            _relative(PRIOR_STOP_LEDGER_PATH):PRIOR_STOP_LEDGER_SHA256,
            _relative(POLICY_CORE_MANIFEST_PATH):file_sha256(POLICY_CORE_MANIFEST_PATH),
            _relative(MANDATE_PATH):file_sha256(MANDATE_PATH)}

def _validate_first_candidate_binding(binding: object) -> tuple[Path, dict[str,object], dict[str,object]]:
    if not isinstance(binding,dict) or set(binding) != {"path","sha256"}:
        raise GovernorError("AUTONOMY_FIRST_ACTION_BINDING_INVALID")
    if not isinstance(binding["path"],str) or not isinstance(binding["sha256"],str):
        raise GovernorError("AUTONOMY_FIRST_ACTION_BINDING_INVALID")
    path=PROJECT/binding["path"]
    try:
        relative=_relative(path)
    except GovernorError as exc:
        raise GovernorError("AUTONOMY_FIRST_ACTION_BINDING_INVALID") from exc
    if binding["path"] != relative:
        raise GovernorError("AUTONOMY_FIRST_ACTION_BINDING_INVALID")
    if not path.is_file() or binding["sha256"] != file_sha256(path):
        raise GovernorError("AUTONOMY_FIRST_ACTION_BINDING_INVALID")
    try:
        candidate,contract=validate_autonomous_action_candidate(path)
    except Exception as exc:
        raise GovernorError("AUTONOMY_FIRST_ACTION_BINDING_INVALID") from exc
    return path,candidate,contract

def validate_state(path: Path = STATE_PATH) -> dict[str, object]:
    value = _load_sealed(path, "AUTONOMY_STATE_INVALID")
    required = {"active", "autonomy_branch", "body_budget_parent", "body_budget_remaining",
        "current_stage", "firewall_counters", "first_candidate", "governing_specification",
        "last_completed_stage", "last_terminal", "mandate", "mission_id", "permits_issued",
        "policy_core_manifest", "registered_pending_action", "request_budget_parent", "requests_remaining",
        "schema_version", "scientific_outcome", "scientific_question", "sealed", "sequence",
        "standing_authorization", "standing_authorization_initial_state_contract",
        "standing_authorization_initial_state_sha256", "standing_authorization_path", "state",
        "stop_reason", "terminal_outcomes"}
    if (set(value) != required or value.get("schema_version") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_STATE_001" or
            value.get("mission_id") != MISSION_ID or value.get("autonomy_branch") != AUTONOMY_BRANCH or
            type(value.get("sequence")) is not int or value["sequence"] < 0 or
            type(value.get("permits_issued")) is not int or value["permits_issued"] < 0 or
            tuple(value.get("terminal_outcomes", [])) != TERMINAL_OUTCOMES or
            value.get("governing_specification") != _binding(SCIENTIFIC_SPEC_PATH) or
            value.get("mandate") != _binding(MANDATE_PATH) or
            value.get("policy_core_manifest") != _binding(POLICY_CORE_MANIFEST_PATH) or
            value.get("standing_authorization_path") != _relative(STANDING_AUTHORIZATION_PATH) or
            value.get("request_budget_parent") != 0 or value.get("body_budget_parent") != 0):
        raise GovernorError("AUTONOMY_STATE_INVALID")
    if value.get("firewall_counters") != {key: 0 for key in FIREWALL_KEYS}:
        raise GovernorError("AUTONOMY_STATE_FIREWALL_INVALID")
    if (type(value.get("requests_remaining")) is not int or value["requests_remaining"] != 0 or
            type(value.get("body_budget_remaining")) is not int or value["body_budget_remaining"] != 0):
        raise GovernorError("AUTONOMY_STATE_BUDGET_INVALID")
    state_name = value.get("state")
    if state_name == STATE_WAITING:
        if (value.get("active") is not False or value.get("standing_authorization") is not None or
                value.get("standing_authorization_initial_state_sha256") is not None or
                value.get("standing_authorization_initial_state_contract") != "CURRENT_WAITING_STATE_FILE_SHA256"):
            raise GovernorError("AUTONOMY_WAITING_STATE_INVALID")
    elif state_name in (STATE_ACTIVE, STATE_AWAITING):
        if value.get("active") is not True:
            raise GovernorError("AUTONOMY_ACTIVE_STATE_INVALID")
        _sha(value.get("standing_authorization_initial_state_sha256"), "AUTONOMY_INITIAL_STATE_SHA_INVALID")
        if not isinstance(value.get("standing_authorization"), dict) or set(value["standing_authorization"]) != {"path","sha256"}:
            raise GovernorError("AUTONOMY_ACTIVE_STATE_INVALID")
    elif state_name in (STOP_REQUIRES_HUMAN, STATE_TERMINAL):
        if value.get("active") is not False:
            raise GovernorError("AUTONOMY_TERMINAL_STATE_INVALID")
    else:
        raise GovernorError("AUTONOMY_STATE_INVALID")
    _validate_first_candidate_binding(value.get("first_candidate"))
    return value

def validate_standing_authorization(path: Path, *, expected_initial_state_sha256: str,
                                    expected_initial_state_path: Path = STATE_PATH,
                                    expected_first_candidate: dict[str,str]) -> dict[str, object]:
    value = _load_sealed(path, "STANDING_AUTONOMY_AUTHORIZATION_INVALID")
    _validate_first_candidate_binding(expected_first_candidate)
    required = {"authorization_state", "authorized", "authorized_at_utc", "authorized_by",
        "continuation_policy", "first_candidate_path", "first_candidate_sha256",
        "initial_state_path", "initial_state_sha256", "mandate_path",
        "mandate_sha256", "mission_id", "mission_scope", "policy_core_manifest_path",
        "policy_core_manifest_sha256", "schema_version", "sealed"}
    if (set(value) != required or value.get("schema_version") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_STANDING_AUTHORIZATION_001" or
            value.get("authorization_state") != "STANDING_HUMAN_AUTONOMY_AUTHORIZATION" or
            value.get("authorized") is not True or not isinstance(value.get("authorized_by"), str) or
            not value["authorized_by"].strip() or value.get("continuation_policy") !=
            "CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN" or
            value.get("mission_id") != MISSION_ID or value.get("mission_scope") != MISSION_SCOPE or
            value.get("mandate_path") != _relative(MANDATE_PATH) or value.get("mandate_sha256") != file_sha256(MANDATE_PATH) or
            value.get("policy_core_manifest_path") != _relative(POLICY_CORE_MANIFEST_PATH) or
            value.get("policy_core_manifest_sha256") != file_sha256(POLICY_CORE_MANIFEST_PATH) or
            value.get("first_candidate_path") != expected_first_candidate["path"] or
            value.get("first_candidate_sha256") != expected_first_candidate["sha256"] or
            value.get("initial_state_path") != _relative(expected_initial_state_path) or
            value.get("initial_state_sha256") != expected_initial_state_sha256):
        raise GovernorError("STANDING_AUTONOMY_AUTHORIZATION_INVALID")
    _utc(value.get("authorized_at_utc")); validate_policy_core_manifest()
    return value

def candidate_payload(candidate: dict[str, object]) -> dict[str, object]:
    return {key: item for key, item in candidate.items() if key not in ("autonomy_policy", "sealed")}

def _validate_artifact_binding(binding: object, code: str) -> Path:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise GovernorError(code)
    path = PROJECT / str(binding["path"])
    if not path.is_file() or binding["sha256"] != file_sha256(path):
        raise GovernorError(code)
    return path

def validate_action_validation_receipt(binding: object, contract: dict[str, object]) -> dict[str, object]:
    path = _validate_artifact_binding(binding, "ACTION_VALIDATION_RECEIPT_INVALID")
    receipt = _load_sealed(path, "ACTION_VALIDATION_RECEIPT_INVALID")
    required = {"action_kind", "candidate_payload_sha256", "frozen_specification", "implementation_binding",
                "network_requests", "schema_version", "scope", "sealed", "stage_id", "validated", "validator"}
    if (set(receipt) != required or receipt.get("schema_version") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_ACTION_VALIDATION_RECEIPT_001" or
            receipt.get("validated") is not True or receipt.get("network_requests") != 0 or
            receipt.get("action_kind") != contract["action_kind"] or
            receipt.get("candidate_payload_sha256") != contract["candidate_payload_sha256"] or
            receipt.get("stage_id") != contract["stage_id"] or receipt.get("scope") != contract["scope"] or
            receipt.get("implementation_binding") != contract["implementation_binding"] or
            receipt.get("frozen_specification") != contract["frozen_specification"]):
        raise GovernorError("ACTION_VALIDATION_RECEIPT_INVALID")
    _validate_artifact_binding(receipt.get("validator"), "ACTION_VALIDATOR_IDENTITY_MISMATCH")
    return receipt

def validate_literal_resource_manifest(binding: object) -> dict[str, object]:
    path = _validate_artifact_binding(binding, "AUTONOMY_RESOURCE_MANIFEST_INVALID")
    manifest = _load_sealed(path, "AUTONOMY_RESOURCE_MANIFEST_INVALID")
    resources = manifest.get("resources")
    if (manifest.get("broad_crawling") is not False or manifest.get("mirror_substitution") is not False or
            not isinstance(resources, list) or not resources):
        raise GovernorError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
    required = {"accepted_content_types", "application_body_byte_cap", "bibliographic_identity", "evidence_capture_mode",
                "evidence_class", "expected_representation", "host", "id", "method", "purpose",
                "redirects", "retries", "revision_identity", "url"}
    for resource in resources:
        if (not isinstance(resource, dict) or set(resource) != required or
                not isinstance(resource.get("url"), str) or not resource["url"].startswith("https://") or
                not isinstance(resource.get("host"), str) or not resource["host"] or
                resource.get("method") not in ("GET", "HEAD") or
                type(resource.get("application_body_byte_cap")) is not int or resource["application_body_byte_cap"] < 0 or
                type(resource.get("redirects")) is not int or resource["redirects"] < 0 or
                type(resource.get("retries")) is not int or resource["retries"] < 0):
            raise GovernorError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
        mode = resource.get("evidence_capture_mode")
        revision = resource.get("revision_identity")
        if mode == "HASHED_RESPONSE_SNAPSHOT":
            if revision is not None:
                raise GovernorError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
        elif mode == "REVISION_PINNED_RESOURCE":
            if (not isinstance(revision, dict) or set(revision) !=
                    {"authority", "identifier", "verification_method"} or
                    any(not isinstance(revision[key], str) or not revision[key].strip()
                        for key in revision)):
                raise GovernorError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
        else:
            raise GovernorError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
    return manifest

def validate_autonomous_action_candidate(path: Path) -> tuple[dict[str, object], dict[str, object]]:
    candidate = _load_sealed(path, "AUTONOMOUS_ACTION_CANDIDATE_INVALID")
    contract = candidate.get("autonomy_policy")
    required = {"action_kind", "action_validation_receipt", "application_body_reservation",
        "authority_classes_used", "candidate_hash_mode", "candidate_payload_sha256",
        "command_argv_sha256", "concurrency", "frozen_specification", "full_candidate_identity",
        "git_assertions", "implementation_binding", "network_request_reservation", "permit_output_path",
        "requested_prohibited_scopes", "resource_manifest", "resume_policy", "retry_reservation",
        "retry_policy", "schema_version",
        "scientific_firewall", "scope", "stage_id", "standing_mandate_sha256"}
    if (not isinstance(contract, dict) or set(contract) != required or
            contract.get("schema_version") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_ACTION_CONTRACT_001" or
            contract.get("candidate_hash_mode") != "CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED" or
            contract.get("full_candidate_identity") != "FULL_FILE_SHA256_BOUND_BY_STATE_AUTHORIZATION_PERMIT_AND_LEDGER" or
            contract.get("stage_id") != candidate.get("stage_id") or contract.get("scope") != candidate.get("scope") or
            contract.get("command_argv_sha256") != candidate.get("command_argv_sha256") or
            contract.get("standing_mandate_sha256") != file_sha256(MANDATE_PATH)):
        raise GovernorError("AUTONOMOUS_ACTION_CONTRACT_INVALID")
    payload_sha = sha256_bytes(canonical(candidate_payload(candidate)))
    if contract.get("candidate_payload_sha256") != payload_sha:
        raise GovernorError("AUTONOMOUS_ACTION_PAYLOAD_MISMATCH")
    argv = candidate.get("command_argv")
    if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv) or sha256_bytes(canonical(argv)) != contract["command_argv_sha256"]:
        raise GovernorError("COMMAND_ARGV_HASH_MISMATCH")
    implementation = contract.get("implementation_binding")
    if (not isinstance(implementation, dict) or set(implementation) != {"algorithm","sha256"} or
            implementation.get("algorithm") != "OC3_IMPLEMENTATION_AGGREGATE_V1" or
            implementation.get("sha256") != candidate.get("implementation_aggregate")):
        raise GovernorError("IMPLEMENTATION_BINDING_INVALID")
    _sha(implementation.get("sha256"), "IMPLEMENTATION_BINDING_INVALID")
    _validate_artifact_binding(contract.get("frozen_specification"), "FROZEN_SPECIFICATION_MISMATCH")
    validate_action_validation_receipt(contract.get("action_validation_receipt"), contract)
    if contract.get("resource_manifest") is not None:
        validate_literal_resource_manifest(contract["resource_manifest"])
    for key in ("network_request_reservation", "application_body_reservation", "retry_reservation", "concurrency"):
        if type(contract.get(key)) is not int or contract[key] < 0:
            raise GovernorError("AUTONOMOUS_ACTION_RESERVATION_INVALID")
    authorities = contract.get("authority_classes_used")
    if not isinstance(authorities, list) or not authorities or len(authorities) != len(set(authorities)):
        raise GovernorError("AUTONOMOUS_ACTION_AUTHORITY_CLASSES_INVALID")
    if contract.get("scientific_firewall") != {key:0 for key in FIREWALL_KEYS}:
        raise GovernorError("AUTONOMOUS_ACTION_FIREWALL_INVALID")
    if contract.get("requested_prohibited_scopes") != []:
        raise GovernorError("AUTONOMOUS_ACTION_PROHIBITED_SCOPE_INVALID")
    if contract.get("git_assertions") != {"branch":AUTONOMY_BRANCH,"force_push":False,"merge_main":False}:
        raise GovernorError("AUTONOMOUS_ACTION_GIT_ASSERTIONS_INVALID")
    if contract.get("resume_policy") != {"allowed":False,"prospectively_frozen":True}:
        raise GovernorError("AUTONOMOUS_ACTION_RESUME_INVALID")
    retry_rule = contract.get("retry_policy")
    if not isinstance(retry_rule, dict) or set(retry_rule) != {"exact_same_resource","prospectively_frozen"}:
        raise GovernorError("AUTONOMOUS_ACTION_RETRY_INVALID")
    _relative(PROJECT / str(contract.get("permit_output_path", "")), "AUTONOMOUS_PERMIT_PATH_INVALID")
    return candidate, contract

def _registered_binding(candidate_path: Path, candidate: dict[str, object], contract: dict[str, object], *, first=False) -> dict[str, object]:
    return {"action_contract_schema":"OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_ACTION_CONTRACT_001","action_kind":contract["action_kind"],
        "candidate_path":_relative(candidate_path),"candidate_sha256":file_sha256(candidate_path),
        "candidate_payload_sha256":contract["candidate_payload_sha256"],
        "registration_state":"FIRST_PENDING_AUTONOMOUS_ACTION" if first else "PENDING_AUTONOMOUS_ACTION",
        "scope":contract["scope"],"stage_id":contract["stage_id"]}

def _validate_active_context(state: dict[str, object], authorization_path: Path,
                             state_path: Path = STATE_PATH) -> dict[str, object]:
    if state.get("active") is not True or state.get("state") != STATE_ACTIVE:
        raise GovernorError(MANDATE_NOT_ACTIVE)
    initial_sha = _sha(state.get("standing_authorization_initial_state_sha256"), "AUTONOMY_INITIAL_STATE_SHA_INVALID")
    authorization = validate_standing_authorization(
        authorization_path, expected_initial_state_sha256=initial_sha,
        expected_initial_state_path=state_path,expected_first_candidate=state["first_candidate"])
    if state.get("standing_authorization") != _binding(authorization_path):
        raise GovernorError("STANDING_AUTHORIZATION_STATE_BINDING_MISMATCH")
    validate_policy_core_manifest()
    return authorization

def evaluate_policy(*, candidate_path: Path, state_path: Path = STATE_PATH,
                    standing_authorization_path: Path = STANDING_AUTHORIZATION_PATH,
                    current_branch: str = AUTONOMY_BRANCH, require_registered: bool = True) -> dict[str, object]:
    validate_static_authorities(); mandate = validate_mandate(); state = validate_state(state_path)
    candidate, contract = validate_autonomous_action_candidate(candidate_path)
    if not Path(standing_authorization_path).is_file() or state.get("active") is not True:
        return _refusal(MANDATE_NOT_ACTIVE)
    if require_registered:
        registered = state.get("registered_pending_action")
        if not isinstance(registered, dict):
            return _refusal("NO_REGISTERED_PENDING_ACTION")
        expected = _registered_binding(candidate_path, candidate, contract,
                                       first=registered.get("registration_state") == "FIRST_PENDING_AUTONOMOUS_ACTION")
        if registered != expected or registered.get("registration_state") not in ("FIRST_PENDING_AUTONOMOUS_ACTION","PENDING_AUTONOMOUS_ACTION"):
            return _refusal("CANDIDATE_STATE_BINDING_MISMATCH")
    try:
        _validate_active_context(state, standing_authorization_path, state_path)
    except GovernorError as exc:
        return _refusal(exc.code)
    if current_branch != AUTONOMY_BRANCH:
        return _refusal("UNAUTHORIZED_BRANCH")
    if contract["standing_mandate_sha256"] != file_sha256(MANDATE_PATH):
        return _refusal("MANDATE_BINDING_MISMATCH")
    if not set(contract["authority_classes_used"]).issubset(set(mandate["allowed_authority_classes"])):
        return _refusal("AUTHORITY_CLASS_EXPANSION")
    if contract["network_request_reservation"] > state["requests_remaining"]:
        return _refusal("REQUEST_BUDGET_OVERFLOW")
    if contract["application_body_reservation"] > state["body_budget_remaining"]:
        return _refusal("BODY_BUDGET_OVERFLOW")
    if contract["concurrency"] > mandate["budgets"]["concurrency"]:
        return _refusal("CONCURRENCY_LIMIT_EXCEEDED")
    retry_rule = contract["retry_policy"]; retries = contract["retry_reservation"]
    if retries > mandate["budgets"]["retries_max_per_exact_resource"] or (
            retries and (retry_rule["prospectively_frozen"] is not True or retry_rule["exact_same_resource"] is not True)):
        return _refusal("RETRY_NOT_PROSPECTIVELY_FROZEN")
    if contract["resume_policy"] != {"allowed":False,"prospectively_frozen":True}:
        return _refusal("RESUME_NOT_FROZEN")
    if contract["scientific_firewall"] != {key:0 for key in FIREWALL_KEYS}:
        return _refusal("SCIENTIFIC_FIREWALL_VIOLATION")
    if contract["requested_prohibited_scopes"] != []:
        return _refusal("PROHIBITED_SCOPE_EXPANSION")
    git_policy = contract["git_assertions"]
    if git_policy["force_push"] is not False: return _refusal("FORCE_PUSH_FORBIDDEN")
    if git_policy["merge_main"] is not False: return _refusal("MAIN_MERGE_FORBIDDEN")
    if git_policy["branch"] != AUTONOMY_BRANCH: return _refusal("UNAUTHORIZED_BRANCH")
    manifest_binding = contract["resource_manifest"]
    if contract["network_request_reservation"] > 0 and manifest_binding is None:
        return _refusal("LITERAL_RESOURCE_MANIFEST_REQUIRED")
    if manifest_binding is not None:
        manifest = validate_literal_resource_manifest(manifest_binding); resources = manifest["resources"]
        if len(resources) > contract["network_request_reservation"]:
            return _refusal("RESOURCE_COUNT_EXCEEDS_REQUEST_RESERVATION")
        if sum(i["application_body_byte_cap"] for i in resources) > contract["application_body_reservation"]:
            return _refusal("RESOURCE_BODY_CAP_EXCEEDS_RESERVATION")
        if any(i["evidence_class"] not in contract["authority_classes_used"] for i in resources):
            return _refusal("RESOURCE_AUTHORITY_CLASS_MISMATCH")
    return {"candidate_sha256":file_sha256(candidate_path),"decision":ELIGIBLE,
        "permit_state":"PERMIT_MAY_BE_ISSUED","policy_core_manifest_sha256":file_sha256(POLICY_CORE_MANIFEST_PATH),
        "standing_authorization_sha256":file_sha256(standing_authorization_path),
        "state_before_sha256":file_sha256(state_path)}

def build_permit(*, candidate_path: Path, state_path: Path, standing_authorization_path: Path,
                 issued_at_utc: str, current_branch: str = AUTONOMY_BRANCH) -> dict[str, object]:
    evaluation = evaluate_policy(candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path,current_branch=current_branch)
    if evaluation["decision"] != ELIGIBLE: raise GovernorError(str(evaluation["decision"]))
    _utc(issued_at_utc); _, contract = validate_autonomous_action_candidate(candidate_path); state = validate_state(state_path)
    candidate_sha = file_sha256(candidate_path)
    return sealed({"action_kind":contract["action_kind"],"authorization_basis":"STANDING_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_MANDATE_001",
        "body_budget_reserved":contract["application_body_reservation"],"candidate_path":_relative(candidate_path),
        "authority_classes":contract["authority_classes_used"],
        "candidate_payload_sha256":contract["candidate_payload_sha256"],"candidate_sha256":candidate_sha,
        "command_argv_sha256":contract["command_argv_sha256"],"concurrency_reserved":contract["concurrency"],
        "initial_state_sha256":state["standing_authorization_initial_state_sha256"],"issued_at_utc":issued_at_utc,
        "mandate_sha256":file_sha256(MANDATE_PATH),"network_budget_reserved":contract["network_request_reservation"],
        "permit_id":f"OC3-AUTONOMOUS-PERMIT-{state['sequence']+1:06d}-{candidate_sha[:12]}",
        "permit_type":"AUTONOMOUS_EXECUTION_PERMIT","policy_core_manifest_sha256":file_sha256(POLICY_CORE_MANIFEST_PATH),
        "resource_manifest_sha256":None if contract["resource_manifest"] is None else contract["resource_manifest"]["sha256"],
        "resume_policy":contract["resume_policy"],"retries_reserved":contract["retry_reservation"],
        "schema_version":"OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_EXECUTION_PERMIT_001","scientific_firewall":contract["scientific_firewall"],
        "scope":contract["scope"],"sequence":state["sequence"],"stage_id":contract["stage_id"],
        "standing_authorization_sha256":file_sha256(standing_authorization_path),
        "state_before_sha256":file_sha256(state_path)})

def issue_permit(*, candidate_path: Path, state_path: Path, standing_authorization_path: Path,
                 output_path: Path, ledger_directory: Path, issued_at_utc: str,
                 current_branch: str = AUTONOMY_BRANCH) -> dict[str, object]:
    _, contract = validate_autonomous_action_candidate(candidate_path)
    expected = (PROJECT / str(contract["permit_output_path"])).resolve()
    if Path(output_path).resolve() != expected: raise GovernorError("AUTONOMOUS_PERMIT_OUTPUT_PATH_MISMATCH")
    if expected.exists(): raise GovernorError("AUTONOMOUS_PERMIT_ALREADY_EXISTS")
    permit = build_permit(candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path,issued_at_utc=issued_at_utc,current_branch=current_branch)
    write_json_immutable(expected, permit); permit_sha = file_sha256(expected)
    issuance = sealed({"body_budget_delta":0,"candidate_sha256":file_sha256(candidate_path),
        "issued_at_utc":issued_at_utc,"new_state_sha256":permit["state_before_sha256"],
        "permit_id":permit["permit_id"],"permit_sha256":permit_sha,
        "previous_state_sha256":permit["state_before_sha256"],"reason":"AUTONOMOUS_PERMIT_ISSUED",
        "request_budget_delta":0,"sequence":permit["sequence"],
        "state_before_sha256":permit["state_before_sha256"],"state":"AUTONOMOUS_PERMIT_ISSUED"})
    write_json_immutable(Path(ledger_directory)/"PERMIT_ISSUANCE"/f"{permit_sha}.json", issuance)
    return permit

def _consumption_marker_path(permit_path: Path) -> Path:
    """Return the sole policy-defined marker identity derived from the permit SHA."""
    return CONSUMPTION_ROOT / f"{file_sha256(permit_path)}.json"

def validate_permit(permit_path: Path, *, candidate_path: Path, state_path: Path,
                    standing_authorization_path: Path,
                    allow_consumed: bool = False) -> dict[str, object]:
    permit = _load_sealed(permit_path,"AUTONOMOUS_PERMIT_INVALID")
    marker = _consumption_marker_path(permit_path)
    if marker.exists() and not allow_consumed: raise GovernorError("AUTONOMOUS_PERMIT_ALREADY_CONSUMED")
    _, contract = validate_autonomous_action_candidate(candidate_path)
    state = validate_state(state_path)
    evaluation = evaluate_policy(candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path)
    if evaluation["decision"] != ELIGIBLE: raise GovernorError(str(evaluation["decision"]))
    required = {"action_kind","authority_classes","authorization_basis","body_budget_reserved","candidate_path",
        "candidate_payload_sha256","candidate_sha256","command_argv_sha256","concurrency_reserved",
        "initial_state_sha256","issued_at_utc","mandate_sha256","network_budget_reserved","permit_id",
        "permit_type","policy_core_manifest_sha256","resource_manifest_sha256","resume_policy","retries_reserved",
        "schema_version","scientific_firewall","scope","sealed","sequence","stage_id",
        "standing_authorization_sha256","state_before_sha256"}
    if (set(permit) != required or permit.get("schema_version") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_EXECUTION_PERMIT_001" or
            permit.get("permit_type") != "AUTONOMOUS_EXECUTION_PERMIT" or
            permit.get("authorization_basis") != "STANDING_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_MANDATE_001" or
            permit.get("mandate_sha256") != file_sha256(MANDATE_PATH) or
            permit.get("policy_core_manifest_sha256") != file_sha256(POLICY_CORE_MANIFEST_PATH) or
            permit.get("standing_authorization_sha256") != file_sha256(standing_authorization_path) or
            permit.get("initial_state_sha256") != state["standing_authorization_initial_state_sha256"] or
            permit.get("state_before_sha256") != file_sha256(state_path) or permit.get("sequence") != state["sequence"] or
            permit.get("candidate_sha256") != file_sha256(candidate_path) or
            permit.get("candidate_payload_sha256") != contract["candidate_payload_sha256"] or
            permit.get("candidate_path") != _relative(candidate_path) or
            permit.get("command_argv_sha256") != contract["command_argv_sha256"] or
            permit.get("action_kind") != contract["action_kind"] or
            permit.get("authority_classes") != contract["authority_classes_used"] or
            permit.get("network_budget_reserved") != contract["network_request_reservation"] or
            permit.get("body_budget_reserved") != contract["application_body_reservation"] or
            permit.get("retries_reserved") != contract["retry_reservation"] or
            permit.get("concurrency_reserved") != contract["concurrency"] or
            permit.get("resume_policy") != contract["resume_policy"] or
            permit.get("scientific_firewall") != {key:0 for key in FIREWALL_KEYS}):
        raise GovernorError("AUTONOMOUS_PERMIT_BINDING_MISMATCH")
    _utc(permit.get("issued_at_utc"))
    return permit

def consume_permit(permit_path: Path, *, candidate_path: Path, state_path: Path,
                   standing_authorization_path: Path,
                   consumed_at_utc: str) -> Path:
    permit = validate_permit(permit_path,candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path)
    _utc(consumed_at_utc); marker = _consumption_marker_path(permit_path)
    write_json_immutable(marker,sealed({"candidate_sha256":permit["candidate_sha256"],
        "consumed_at_utc":consumed_at_utc,"permit_id":permit["permit_id"],"permit_sha256":file_sha256(permit_path),
        "body_budget_delta":0,"new_state_sha256":permit["state_before_sha256"],
        "previous_state_sha256":permit["state_before_sha256"],"reason":"PERMIT_CONSUMPTION_INTENT_RECORDED",
        "request_budget_delta":0,"sequence":permit["sequence"],
        "state_before_sha256":permit["state_before_sha256"],"state":"PERMIT_CONSUMPTION_INTENT_RECORDED"}))
    return marker

def validate_consumption_marker(permit_path: Path, *, candidate_path: Path) -> dict[str, object]:
    marker = _load_sealed(_consumption_marker_path(permit_path),"AUTONOMOUS_PERMIT_CONSUMPTION_MISSING")
    permit = _load_sealed(permit_path,"AUTONOMOUS_PERMIT_INVALID")
    if (set(marker) != {"body_budget_delta","candidate_sha256","consumed_at_utc","new_state_sha256",
            "permit_id","permit_sha256","previous_state_sha256","reason","request_budget_delta",
            "sealed","sequence","state","state_before_sha256"} or
            marker.get("state") != "PERMIT_CONSUMPTION_INTENT_RECORDED" or
            marker.get("permit_sha256") != file_sha256(permit_path) or marker.get("permit_id") != permit.get("permit_id") or
            marker.get("state_before_sha256") != permit.get("state_before_sha256") or
            marker.get("candidate_sha256") != file_sha256(candidate_path)):
        raise GovernorError("AUTONOMOUS_PERMIT_CONSUMPTION_INVALID")
    _utc(marker.get("consumed_at_utc")); return marker

def atomic_replace_state(path: Path, value: dict[str, object]) -> None:
    path=Path(path); data=canonical(value)+b"\n"; path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(f".{path.name}.tmp-{os.getpid()}")
    if temporary.exists(): raise GovernorError("AUTONOMY_STATE_TEMP_CONFLICT")
    with temporary.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary,path)

def _write_snapshot(state_path: Path, state: dict[str, object], ledger_directory: Path) -> str:
    previous_sha=file_sha256(state_path)
    write_json_immutable(Path(ledger_directory)/"STATE_SNAPSHOTS"/f"{state['sequence']:06d}_{previous_sha}.json",state)
    return previous_sha

def activate_standing_autonomy(*, state_path: Path, standing_authorization_path: Path,
                               ledger_directory: Path, activated_at_utc: str, current_branch: str) -> dict[str, object]:
    validate_static_authorities(); _utc(activated_at_utc); state=validate_state(state_path)
    if state.get("active") is not False or state.get("state") != STATE_WAITING:
        raise GovernorError("AUTONOMY_ACTIVATION_STATE_INVALID")
    if current_branch != AUTONOMY_BRANCH: raise GovernorError("UNAUTHORIZED_BRANCH")
    if any(Path(ledger_directory).glob("*_ACTIVATION.json")): raise GovernorError("AUTONOMY_ALREADY_ACTIVATED")
    candidate_path,_,_ = _validate_first_candidate_binding(state.get("first_candidate"))
    if state.get("registered_pending_action") is not None:
        raise GovernorError("AUTONOMY_FIRST_ACTION_BINDING_INVALID")
    initial_state_sha=file_sha256(state_path)
    validate_standing_authorization(standing_authorization_path,
        expected_initial_state_sha256=initial_state_sha,expected_initial_state_path=state_path,
        expected_first_candidate=state["first_candidate"])
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({"active":True,
        "current_stage":STATE_AWAITING,"sequence":state["sequence"]+1,
        "standing_authorization":_binding(standing_authorization_path),
        "standing_authorization_initial_state_sha256":initial_state_sha,"state":STATE_ACTIVE})
    updated=sealed(body); new_sha=sha256_bytes(canonical(updated)+b"\n")
    record=sealed({"activated_at_utc":activated_at_utc,"branch":current_branch,"body_budget_delta":0,
        "mandate_sha256":file_sha256(MANDATE_PATH),"new_state_sha256":new_sha,
        "policy_core_manifest_sha256":file_sha256(POLICY_CORE_MANIFEST_PATH),"previous_state_sha256":previous_sha,
        "reason":"STANDING_AUTONOMY_ACTIVATED","request_budget_delta":0,"sequence":updated["sequence"],
        "standing_authorization_sha256":file_sha256(standing_authorization_path)})
    write_json_immutable(Path(ledger_directory)/f"{updated['sequence']:06d}_ACTIVATION.json",record)
    atomic_replace_state(state_path,updated); return updated

def register_pending_action(*, state_path: Path, candidate_path: Path, standing_authorization_path: Path,
                            ledger_directory: Path, registered_at_utc: str, current_branch: str) -> dict[str, object]:
    validate_static_authorities(); _utc(registered_at_utc); state=validate_state(state_path)
    _validate_active_context(state,standing_authorization_path,state_path)
    if current_branch != AUTONOMY_BRANCH: raise GovernorError("UNAUTHORIZED_BRANCH")
    if state.get("registered_pending_action") is not None: raise GovernorError("UNRESOLVED_REGISTERED_ACTION")
    if state.get("last_completed_stage") is None and _binding(candidate_path) != state.get("first_candidate"):
        raise GovernorError("AUTONOMY_FIRST_ACTION_BINDING_INVALID")
    candidate,contract=validate_autonomous_action_candidate(candidate_path)
    evaluation=evaluate_policy(candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path,current_branch=current_branch,require_registered=False)
    if evaluation["decision"] != ELIGIBLE: raise GovernorError(str(evaluation["decision"]))
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    first = state.get("last_completed_stage") is None and _binding(candidate_path) == state.get("first_candidate")
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({
        "registered_pending_action":_registered_binding(candidate_path,candidate,contract,first=first),
        "current_stage":"AUTONOMOUS_POLICY_EVALUATION","sequence":state["sequence"]+1})
    updated=sealed(body); new_sha=sha256_bytes(canonical(updated)+b"\n")
    record=sealed({"action_kind":contract["action_kind"],"body_budget_delta":0,
        "candidate_sha256":file_sha256(candidate_path),"new_state_sha256":new_sha,
        "previous_state_sha256":previous_sha,"reason":"PENDING_ACTION_REGISTERED",
        "registered_at_utc":registered_at_utc,"request_budget_delta":0,"sequence":updated["sequence"],
        "stage_id":contract["stage_id"]})
    write_json_immutable(Path(ledger_directory)/f"{updated['sequence']:06d}_ACTION_REGISTRATION.json",record)
    atomic_replace_state(state_path,updated); return updated

def _terminal_counters(terminal: dict[str, object]) -> tuple[int|None,int|None,int|None]:
    counters=terminal.get("counters",{}); counters=counters if isinstance(counters,dict) else {}
    requests=counters.get("network_requests_started",counters.get("network_requests",terminal.get("network_requests_started")))
    body=terminal.get("application_body_bytes_read",counters.get("application_body_bytes_read",
        counters.get("network_body_bytes",terminal.get("network_body_bytes"))))
    retries=counters.get("retry_requests",terminal.get("retry_requests"))
    if retries is None and requests == 0: retries=0
    return requests,body,retries

def transition_completed_action(*, state_path: Path, candidate_path: Path, permit_path: Path,
                                standing_authorization_path: Path,
                                terminal_path: Path, terminal_sha256: str,
                                request_delta: int, body_delta: int, retry_delta: int,
                                ledger_directory: Path, transitioned_at_utc: str, reason: str) -> dict[str, object]:
    _utc(transitioned_at_utc); state=validate_state(state_path)
    permit=validate_permit(permit_path,candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path,
        allow_consumed=True)
    validate_consumption_marker(permit_path,candidate_path=candidate_path)
    terminal_path=Path(terminal_path)
    if not terminal_path.is_file(): raise GovernorError("AUTONOMY_TERMINAL_ARTIFACT_MISSING")
    terminal=_load_sealed(terminal_path,"AUTONOMY_TERMINAL_ARTIFACT_INVALID"); terminal_sha=file_sha256(terminal_path)
    if _sha(terminal_sha256,"AUTONOMY_TERMINAL_SHA_INVALID") != terminal_sha:
        raise GovernorError("AUTONOMY_TERMINAL_SHA_MISMATCH")
    if terminal.get("stage_id") is not None and terminal.get("stage_id") != permit["stage_id"]:
        raise GovernorError("AUTONOMY_TERMINAL_STAGE_MISMATCH")
    if terminal.get("scope") is not None and terminal.get("scope") != permit["scope"]:
        raise GovernorError("AUTONOMY_TERMINAL_SCOPE_MISMATCH")
    terminal_counter_map=terminal.get("counters",{}) if isinstance(terminal.get("counters"),dict) else {}
    if any(terminal_counter_map.get(key,0) != 0 for key in FIREWALL_KEYS):
        raise GovernorError("AUTONOMY_TERMINAL_FIREWALL_VIOLATION")
    if any(type(x) is not int or x<0 for x in (request_delta,body_delta,retry_delta)):
        raise GovernorError("AUTONOMY_TRANSITION_DELTA_INVALID")
    if (request_delta>permit["network_budget_reserved"] or body_delta>permit["body_budget_reserved"] or
            retry_delta>permit["retries_reserved"]):
        raise GovernorError("PERMIT_RESERVATION_EXCEEDED_REQUIRES_STOP")
    if request_delta>state["requests_remaining"] or body_delta>state["body_budget_remaining"]:
        raise GovernorError("AUTONOMY_TRANSITION_BUDGET_INVALID")
    observed=_terminal_counters(terminal)
    if any(type(actual) is not int or actual < 0 for actual in observed):
        raise GovernorError("AUTONOMY_TERMINAL_COUNTERS_REQUIRED")
    for actual,expected in zip(observed,(request_delta,body_delta,retry_delta)):
        if actual is not None and actual!=expected: raise GovernorError("AUTONOMY_TERMINAL_COUNTER_MISMATCH")
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({
        "body_budget_remaining":state["body_budget_remaining"]-body_delta,"current_stage":STATE_AWAITING,
        "last_completed_stage":permit["stage_id"],"last_terminal":_binding(terminal_path),
        "permits_issued":state["permits_issued"]+1,
        "registered_pending_action":None,"requests_remaining":state["requests_remaining"]-request_delta,
        "sequence":state["sequence"]+1})
    updated=sealed(body); new_sha=sha256_bytes(canonical(updated)+b"\n")
    record=sealed({"action_stage":permit["stage_id"],"body_budget_delta":body_delta,
        "candidate_sha256":file_sha256(candidate_path),"new_state_sha256":new_sha,
        "permit_sha256":file_sha256(permit_path),"previous_state_sha256":previous_sha,"reason":reason,
        "request_budget_delta":request_delta,"retry_delta":retry_delta,"sequence":updated["sequence"],
        "terminal_path":_relative(terminal_path),"terminal_sha256":terminal_sha,
        "terminal_state":terminal.get("state"),"transitioned_at_utc":transitioned_at_utc})
    write_json_immutable(Path(ledger_directory)/f"{updated['sequence']:06d}_ACTION_COMPLETE.json",record)
    atomic_replace_state(state_path,updated); return updated

def enter_stop_requires_human(*, state_path: Path, standing_authorization_path: Path,
                              stop_report_path: Path, blocker_code: str, ledger_directory: Path,
                              stopped_at_utc: str, current_branch: str) -> dict[str, object]:
    _utc(stopped_at_utc)
    if re.fullmatch(r"[A-Z0-9_]+",blocker_code) is None: raise GovernorError("AUTONOMY_STOP_BLOCKER_INVALID")
    state=validate_state(state_path); _validate_active_context(state,standing_authorization_path,state_path)
    if current_branch!=AUTONOMY_BRANCH: raise GovernorError("UNAUTHORIZED_BRANCH")
    report=Path(stop_report_path)
    if not report.is_file() or report.stat().st_size==0 or report.stat().st_size>COMPACT_ARTIFACT_MAX_BYTES:
        raise GovernorError("AUTONOMY_STOP_REPORT_INVALID")
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({"active":False,
        "current_stage":STOP_REQUIRES_HUMAN,"sequence":state["sequence"]+1,
        "state":STOP_REQUIRES_HUMAN,"stop_reason":blocker_code})
    updated=sealed(body); new_sha=sha256_bytes(canonical(updated)+b"\n")
    record=sealed({"blocker_code":blocker_code,"body_budget_delta":0,"new_state_sha256":new_sha,
        "previous_state_sha256":previous_sha,"reason":STOP_REQUIRES_HUMAN,"report_path":_relative(report),
        "report_sha256":file_sha256(report),"request_budget_delta":0,"sequence":updated["sequence"],
        "stopped_at_utc":stopped_at_utc})
    write_json_immutable(Path(ledger_directory)/f"{updated['sequence']:06d}_STOP.json",record)
    atomic_replace_state(state_path,updated); return updated

def finalize_scientific_terminal(*, state_path: Path, standing_authorization_path: Path,
                                 outcome: str, final_report_path: Path, claim_matrix_path: Path|None,
                                 ledger_directory: Path, finalized_at_utc: str, current_branch: str) -> dict[str, object]:
    _utc(finalized_at_utc)
    if outcome not in TERMINAL_OUTCOMES: raise GovernorError("SCIENTIFIC_OUTCOME_NOT_FROZEN")
    state=validate_state(state_path); _validate_active_context(state,standing_authorization_path,state_path)
    if current_branch!=AUTONOMY_BRANCH: raise GovernorError("UNAUTHORIZED_BRANCH")
    if state.get("registered_pending_action") is not None: raise GovernorError("SCIENTIFIC_TERMINAL_PENDING_ACTION")
    if state.get("firewall_counters")!={key:0 for key in FIREWALL_KEYS}:
        raise GovernorError("SCIENTIFIC_TERMINAL_FIREWALL_DIRTY")
    report=Path(final_report_path)
    if not report.is_file() or report.stat().st_size==0: raise GovernorError("SCIENTIFIC_TERMINAL_REPORT_INVALID")
    matrix_binding=None
    if claim_matrix_path is not None:
        matrix=Path(claim_matrix_path)
        if not matrix.is_file() or matrix.stat().st_size==0: raise GovernorError("SCIENTIFIC_TERMINAL_CLAIM_MATRIX_INVALID")
        matrix_binding=_binding(matrix)
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({"active":False,
        "current_stage":STATE_TERMINAL,"scientific_outcome":outcome,
        "sequence":state["sequence"]+1,"state":STATE_TERMINAL})
    updated=sealed(body); new_sha=sha256_bytes(canonical(updated)+b"\n")
    record=sealed({"body_budget_delta":0,"claim_matrix":matrix_binding,"final_report":_binding(report),
        "finalized_at_utc":finalized_at_utc,"new_state_sha256":new_sha,"outcome":outcome,
        "previous_state_sha256":previous_sha,"reason":"SCIENTIFIC_TERMINAL_FINALIZED",
        "request_budget_delta":0,"sequence":updated["sequence"]})
    write_json_immutable(Path(ledger_directory)/f"{updated['sequence']:06d}_SCIENTIFIC_TERMINAL.json",record)
    atomic_replace_state(state_path,updated); return updated

def audit_compact_paths(paths: list[Path], *, project: Path=PROJECT) -> dict[str,object]:
    project=Path(project).resolve(); total=0; largest=0; normalized=[]
    for item in paths:
        path=Path(item); absolute=path.resolve() if path.is_absolute() else (project/path).resolve()
        try: relative=absolute.relative_to(project).as_posix()
        except ValueError as exc: raise GovernorError("GIT_PATH_OUTSIDE_PROJECT") from exc
        lowered=relative.lower()
        if any(lowered.startswith(p.lower()) for p in RUNTIME_TREE_PREFIXES): raise GovernorError("GIT_RUNTIME_EVIDENCE_FORBIDDEN")
        if any(lowered.endswith(s) for s in FORBIDDEN_GIT_SUFFIXES): raise GovernorError("GIT_SCIENTIFIC_OR_ARCHIVE_BODY_FORBIDDEN")
        basename=absolute.name.lower()
        if basename==".env" or any(p in basename for p in SECRET_NAME_PARTS): raise GovernorError("GIT_CREDENTIAL_PATH_FORBIDDEN")
        if absolute.is_symlink() or not absolute.is_file(): raise GovernorError("GIT_NONREGULAR_PATH_FORBIDDEN")
        size=absolute.stat().st_size
        if size>COMPACT_ARTIFACT_MAX_BYTES: raise GovernorError("GIT_COMPACT_ARTIFACT_SIZE_EXCEEDED")
        payload=absolute.read_bytes()
        if any(pattern.search(payload) for pattern in SECRET_CONTENT_PATTERNS): raise GovernorError("GIT_SECRET_CONTENT_FORBIDDEN")
        total+=size; largest=max(largest,size); normalized.append(relative)
    return {"file_count":len(normalized),"files":sorted(normalized),"largest_file_bytes":largest,
        "network_requests":0,"per_file_limit_bytes":COMPACT_ARTIFACT_MAX_BYTES,
        "state":"GIT_STAGED_SIZE_FIREWALL_PASS","total_bytes":total}

def audit_staged_compact_artifacts(*, project: Path=PROJECT) -> dict[str,object]:
    project=Path(project).resolve()
    result=subprocess.run(["git","diff","--cached","--name-only","--diff-filter=ACMR","-z"],
                          cwd=project,check=True,capture_output=True)
    names=[n.decode("utf-8") for n in result.stdout.split(b"\0") if n]
    if not names: raise GovernorError("GIT_NO_STAGED_ARTIFACTS")
    return audit_compact_paths([Path(n) for n in names],project=project)

def compact_status(state_path: Path=STATE_PATH) -> dict[str,object]:
    state=validate_state(state_path)
    return {"active":state["active"],"mission_id":state["mission_id"],
        "permit_state":MANDATE_NOT_ACTIVE if not state["active"] else "ACTIVE_POLICY_EVALUATION",
        "requests_remaining":state["requests_remaining"],"sequence":state["sequence"],"state":state["state"]}

def first_candidate_path(state_path: Path=STATE_PATH) -> Path:
    state=validate_state(state_path)
    return PROJECT/str(state["first_candidate"]["path"])

def validate_candidate(path: Path|None=None) -> tuple[dict[str,object],dict[str,object]]:
    path=first_candidate_path() if path is None else path
    return validate_autonomous_action_candidate(path)

def validate_all() -> dict[str,object]:
    validate_static_authorities(); validate_mandate(); state=validate_state(); validate_candidate()
    return {"active":state["active"],"network_requests":0,"permits_issued":state["permits_issued"],
            "state":state["state"],"validated":True}

def evaluate_candidate(candidate_path: Path|None=None,
                       state_path: Path=STATE_PATH) -> dict[str,object]:
    candidate_path=first_candidate_path(state_path) if candidate_path is None else candidate_path
    return evaluate_policy(candidate_path=candidate_path,state_path=state_path)
