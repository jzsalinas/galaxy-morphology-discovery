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
from .galaxy_eligibility_photsys_authority_probe import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)

MISSION_ID = "OC3-PHOTSYS-ZERO-BYTE-PROVENANCE-AUTONOMY-001"
MISSION_SCOPE = "PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_MISSION_ONLY"
AUTONOMY_BRANCH = "autopilot/photsys-zero-byte"
STATE_WAITING = "WAITING_FOR_STANDING_HUMAN_AUTHORIZATION"
STATE_ACTIVE = "ACTIVE"
STATE_AWAITING_ACTION = "AWAITING_NEXT_ACTION_REGISTRATION"
STATE_SCIENTIFIC_TERMINAL = "SCIENTIFIC_TERMINAL"
STOP_REQUIRES_HUMAN = "STOP_REQUIRES_HUMAN"
MANDATE_NOT_ACTIVE = "MANDATE_NOT_ACTIVE"
NO_PERMIT_ISSUED = "NO_PERMIT_ISSUED"
ELIGIBLE = "ELIGIBLE_FOR_AUTONOMOUS_PERMIT"

SCIENTIFIC_SPEC_PATH = PROJECT / "OC3_PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_SPEC.md"
SCIENTIFIC_SPEC_SHA256 = "4b2db6523e9acc3add101199966e6fe372c6105d74edd59089eae1fdc09cc614"
GOVERNANCE_AMENDMENT_PATH = PROJECT / "OC3_AUTONOMOUS_EXECUTION_GOVERNANCE_AMENDMENT_001.md"
GOVERNANCE_AMENDMENT_SHA256 = "f255430eb8b36a7a40b71ee522d81f0664b00ebd16471324cc7f06c61a307b47"
POLICY_CORE_CONTRACT_PATH = PROJECT / "OC3_AUTONOMY_POLICY_CORE_CONTRACT_001.md"
POLICY_CORE_MANIFEST_PATH = PROJECT / "oc3/INPUTS/OC3_AUTONOMY_POLICY_CORE_MANIFEST_001.json"
MANDATE_DOCUMENT_PATH = PROJECT / "OC3_AUTONOMY_MANDATE_001.md"
MANDATE_PATH = PROJECT / "oc3/INPUTS/OC3_AUTONOMY_MANDATE_001.json"
RUNBOOK_PATH = PROJECT / "OC3_AUTONOMOUS_RESEARCH_RUNBOOK_001.md"
STANDING_AUTHORIZATION_PATH = PROJECT / "oc3/OC3_AUTONOMY_STANDING_AUTHORIZATION_001.json"
STATE_PATH = PROJECT / "oc3/OC3_AUTONOMY_STATE_001.json"
LEDGER_ROOT = PROJECT / "oc3/AUTONOMY_LEDGER"
STOP_REPORT_PATH = PROJECT / "AUTOPILOT_STOP_REPORT.md"

TERMINAL_OUTCOMES = (
    "PHOTSYS_0x00_OUTSIDE_SEMANTICS_PROVEN",
    "PHOTSYS_0x00_REPRESENTATION_MISMATCH_BUT_OUTSIDE_MAPPING_SUPPORTED",
    "PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE",
    "PHOTSYS_DOCUMENTATION_PHYSICAL_CONFLICT_UNRESOLVED",
)
ALLOWED_AUTHORITY_CLASSES = (
    "OFFICIAL_LEGACY_SURVEY_DR9_NAMED_PRODUCT_DOCUMENTATION",
    "AUTHORITATIVE_FITS_STANDARD_OR_OFFICIAL_NASA_HEASARC",
    "EXACT_DESITARGET_0_48_0_METADATA_AND_SOURCE",
    "OFFICIAL_DESI_LEGACY_SURVEY_NAMED_PRODUCT_PROVENANCE",
    "PEER_REVIEWED_RANDOM_CATALOG_GENERATION_PROVENANCE",
)
FIREWALL_KEYS = (
    "astronomical_data_GETs", "real_PHOTSYS_bytes_observed",
    "BRICKNAME_values_observed", "BRICKID_values_observed", "ROOT_values_observed",
)
PROHIBITED_SCOPE_KEYS = ("morphological_discovery", "p1", "panel_v2", "resolver")
POLICY_CORE_MEMBERS = (
    "OC3_AUTONOMY_POLICY_CORE_CONTRACT_001.md",
    "oc3/oc3_autonomy_governor.py",
    "oc3/oc3lib/autonomy_governor.py",
)
COMPACT_ARTIFACT_MAX_BYTES = 5 * 1024 * 1024
RUNTIME_TREE_PREFIXES = (
    "oc3/metadata_bootstrap/", "oc3/photsys_archive_head_probe/",
    "oc3/photsys_archive_range_size_probe/", "oc3/photsys_authority_full_acquisition/",
    "oc3/photsys_byte_histogram/", "oc3/photsys_selective_value_validation/",
    "oc3/photsys_zero_byte_provenance/",
)
FORBIDDEN_GIT_SUFFIXES = (".fit", ".fits", ".fits.gz", ".tar", ".tar.gz", ".tgz", ".zip")
SECRET_NAME_PARTS = ("credential", "private_key", "secret", "token")
SECRET_CONTENT_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
)

class AutonomyError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

def _sha(value: object, code: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise AutonomyError(code)
    return value

def _utc(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise AutonomyError("AUTONOMY_TIMESTAMP_INVALID")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise AutonomyError("AUTONOMY_TIMESTAMP_INVALID") from exc
    return value

def _load_sealed(path: Path, code: str) -> dict[str, object]:
    try:
        return validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise AutonomyError(code) from exc

def _relative(path: Path, code: str = "AUTONOMY_PATH_OUTSIDE_PROJECT") -> str:
    try:
        return str(Path(path).resolve().relative_to(PROJECT))
    except ValueError as exc:
        raise AutonomyError(code) from exc

def _binding(path: Path) -> dict[str, str]:
    return {"path": _relative(path), "sha256": file_sha256(path)}

def _refusal(code: str) -> dict[str, object]:
    return {"decision": code, "permit_state": NO_PERMIT_ISSUED}

def validate_policy_core_manifest(path: Path = POLICY_CORE_MANIFEST_PATH) -> dict[str, object]:
    value = _load_sealed(path, "POLICY_CORE_MANIFEST_INVALID")
    if (set(value) != {"active_mutation_result", "contract", "files", "schema_version", "sealed"} or
            value.get("schema_version") != "OC3_AUTONOMY_POLICY_CORE_MANIFEST_001" or
            value.get("active_mutation_result") != STOP_REQUIRES_HUMAN):
        raise AutonomyError("POLICY_CORE_MANIFEST_INVALID")
    contract = value.get("contract", {})
    if (contract.get("path") != _relative(POLICY_CORE_CONTRACT_PATH) or
            contract.get("sha256") != file_sha256(POLICY_CORE_CONTRACT_PATH)):
        raise AutonomyError("POLICY_CORE_MISMATCH")
    files = value.get("files")
    if not isinstance(files, list) or {i.get("path") for i in files if isinstance(i, dict)} != set(POLICY_CORE_MEMBERS):
        raise AutonomyError("POLICY_CORE_MANIFEST_INVALID")
    for item in files:
        if set(item) != {"path", "sha256"}:
            raise AutonomyError("POLICY_CORE_MANIFEST_INVALID")
        member = PROJECT / str(item["path"])
        if not member.is_file() or item["sha256"] != file_sha256(member):
            raise AutonomyError("POLICY_CORE_MISMATCH")
    return value

def validate_mandate(path: Path = MANDATE_PATH) -> dict[str, object]:
    value = _load_sealed(path, "AUTONOMY_MANDATE_INVALID")
    required = {"active", "allowed_evidence_classes", "allowed_scientific_outcomes",
        "authorization_state", "autonomous_action_contract", "autonomy_branch", "budgets",
        "firewall", "governance_amendment", "governing_scientific_specification",
        "mandate_document", "mission_id", "mission_scope", "policy_core_manifest",
        "prohibited_next_phases", "range_autonomy_amendment", "runbook", "schema_version",
        "sealed", "standing_authorization_path", "stop_state"}
    if (set(value) != required or value.get("schema_version") != "OC3_AUTONOMY_MANDATE_002" or
            value.get("authorization_state") != "PENDING_HUMAN_AUTHORIZATION" or value.get("active") is not False or
            value.get("mission_id") != MISSION_ID or value.get("mission_scope") != MISSION_SCOPE or
            value.get("autonomy_branch") != AUTONOMY_BRANCH or
            tuple(value.get("allowed_scientific_outcomes", [])) != TERMINAL_OUTCOMES or
            tuple(value.get("allowed_evidence_classes", [])) != ALLOWED_AUTHORITY_CLASSES or
            value.get("autonomous_action_contract") != "OC3_AUTONOMOUS_ACTION_CONTRACT_001" or
            value.get("stop_state") != STOP_REQUIRES_HUMAN):
        raise AutonomyError("AUTONOMY_MANDATE_INVALID")
    if value.get("budgets") != {"application_body_bytes_parent":33554432,
        "application_body_bytes_remaining":17544938,"concurrency":1,
        "historical_conservative_body_maximum":16009494,"public_source_requests_historical":6,
        "public_source_requests_parent":24,"public_source_requests_remaining":18,
        "retries_default":0,"retries_max_per_exact_resource":1}:
        raise AutonomyError("AUTONOMY_MANDATE_BUDGET_INVALID")
    if value.get("firewall") != {key: 0 for key in FIREWALL_KEYS}:
        raise AutonomyError("AUTONOMY_MANDATE_FIREWALL_INVALID")
    manifest = value.get("policy_core_manifest", {})
    if manifest.get("path") != _relative(POLICY_CORE_MANIFEST_PATH) or manifest.get("sha256") != file_sha256(POLICY_CORE_MANIFEST_PATH):
        raise AutonomyError("AUTONOMY_MANDATE_POLICY_CORE_MISMATCH")
    validate_policy_core_manifest()
    for key, actual in (("governing_scientific_specification", SCIENTIFIC_SPEC_PATH),
                        ("governance_amendment", GOVERNANCE_AMENDMENT_PATH),
                        ("mandate_document", MANDATE_DOCUMENT_PATH), ("runbook", RUNBOOK_PATH)):
        binding = value.get(key, {})
        if binding.get("path") != _relative(actual) or binding.get("sha256") != file_sha256(actual):
            raise AutonomyError("AUTONOMY_MANDATE_AUTHORITY_MISMATCH")
    return value

def validate_static_authorities() -> dict[str, str]:
    for path, digest in ((SCIENTIFIC_SPEC_PATH, SCIENTIFIC_SPEC_SHA256),
                         (GOVERNANCE_AMENDMENT_PATH, GOVERNANCE_AMENDMENT_SHA256)):
        if not path.is_file() or file_sha256(path) != digest:
            raise AutonomyError("AUTONOMY_STATIC_AUTHORITY_MISMATCH")
    validate_policy_core_manifest(); validate_mandate()
    return {_relative(SCIENTIFIC_SPEC_PATH):SCIENTIFIC_SPEC_SHA256,
            _relative(GOVERNANCE_AMENDMENT_PATH):GOVERNANCE_AMENDMENT_SHA256,
            _relative(POLICY_CORE_MANIFEST_PATH):file_sha256(POLICY_CORE_MANIFEST_PATH),
            _relative(MANDATE_PATH):file_sha256(MANDATE_PATH)}

def validate_state(path: Path = STATE_PATH) -> dict[str, object]:
    value = _load_sealed(path, "AUTONOMY_STATE_INVALID")
    required = {"active", "autonomy_branch", "body_budget_parent", "body_budget_remaining",
        "current_stage", "firewall_counters", "governance_amendment", "governing_specification",
        "historical_conservative_body_maximum", "last_completed_stage", "last_terminal", "mandate",
        "mission_id", "policy_core_manifest", "prohibited_next_phases", "registered_pending_action",
        "request_budget_parent", "requests_historical_consumed", "requests_remaining", "schema_version",
        "scientific_outcome", "scientific_question", "sealed", "sequence", "standing_authorization",
        "standing_authorization_initial_state_contract", "standing_authorization_initial_state_sha256",
        "standing_authorization_path", "state", "stop_reason", "terminal_outcomes"}
    if (set(value) != required or value.get("schema_version") != "OC3_AUTONOMY_STATE_002" or
            value.get("mission_id") != MISSION_ID or value.get("autonomy_branch") != AUTONOMY_BRANCH or
            type(value.get("sequence")) is not int or value["sequence"] < 0 or
            tuple(value.get("terminal_outcomes", [])) != TERMINAL_OUTCOMES or
            value.get("governing_specification", {}).get("sha256") != SCIENTIFIC_SPEC_SHA256 or
            value.get("governance_amendment", {}).get("sha256") != GOVERNANCE_AMENDMENT_SHA256 or
            value.get("mandate", {}).get("sha256") != file_sha256(MANDATE_PATH) or
            value.get("policy_core_manifest", {}).get("sha256") != file_sha256(POLICY_CORE_MANIFEST_PATH) or
            value.get("standing_authorization_path") != _relative(STANDING_AUTHORIZATION_PATH) or
            value.get("request_budget_parent") != 24 or value.get("requests_historical_consumed") != 6 or
            value.get("body_budget_parent") != 33554432 or
            value.get("historical_conservative_body_maximum") != 16009494):
        raise AutonomyError("AUTONOMY_STATE_INVALID")
    if value.get("firewall_counters") != {key: 0 for key in FIREWALL_KEYS}:
        raise AutonomyError("AUTONOMY_STATE_FIREWALL_INVALID")
    if (type(value.get("requests_remaining")) is not int or not 0 <= value["requests_remaining"] <= 18 or
            type(value.get("body_budget_remaining")) is not int or not 0 <= value["body_budget_remaining"] <= 17544938):
        raise AutonomyError("AUTONOMY_STATE_BUDGET_INVALID")
    state_name = value.get("state")
    if state_name == STATE_WAITING:
        if (value.get("active") is not False or value.get("standing_authorization") is not None or
                value.get("standing_authorization_initial_state_sha256") is not None or
                value.get("standing_authorization_initial_state_contract") != "CURRENT_WAITING_STATE_FILE_SHA256"):
            raise AutonomyError("AUTONOMY_WAITING_STATE_INVALID")
    elif state_name == STATE_ACTIVE:
        if value.get("active") is not True:
            raise AutonomyError("AUTONOMY_ACTIVE_STATE_INVALID")
        _sha(value.get("standing_authorization_initial_state_sha256"), "AUTONOMY_INITIAL_STATE_SHA_INVALID")
        if not isinstance(value.get("standing_authorization"), dict) or set(value["standing_authorization"]) != {"path","sha256"}:
            raise AutonomyError("AUTONOMY_ACTIVE_STATE_INVALID")
    elif state_name in (STOP_REQUIRES_HUMAN, STATE_SCIENTIFIC_TERMINAL):
        if value.get("active") is not False:
            raise AutonomyError("AUTONOMY_TERMINAL_STATE_INVALID")
    else:
        raise AutonomyError("AUTONOMY_STATE_INVALID")
    return value

def validate_standing_authorization(path: Path, *, expected_initial_state_sha256: str,
                                    expected_initial_state_path: Path = STATE_PATH) -> dict[str, object]:
    value = _load_sealed(path, "STANDING_AUTONOMY_AUTHORIZATION_INVALID")
    required = {"authorization_state", "authorized", "authorized_at_utc", "authorized_by",
        "continuation_policy", "initial_state_path", "initial_state_sha256", "mandate_path",
        "mandate_sha256", "mission_id", "mission_scope", "policy_core_manifest_path",
        "policy_core_manifest_sha256", "schema_version", "sealed"}
    if (set(value) != required or value.get("schema_version") != "OC3_AUTONOMY_STANDING_AUTHORIZATION_001" or
            value.get("authorization_state") != "STANDING_HUMAN_AUTONOMY_AUTHORIZATION" or
            value.get("authorized") is not True or not isinstance(value.get("authorized_by"), str) or
            not value["authorized_by"].strip() or value.get("continuation_policy") !=
            "CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN" or
            value.get("mission_id") != MISSION_ID or value.get("mission_scope") != MISSION_SCOPE or
            value.get("mandate_path") != _relative(MANDATE_PATH) or value.get("mandate_sha256") != file_sha256(MANDATE_PATH) or
            value.get("policy_core_manifest_path") != _relative(POLICY_CORE_MANIFEST_PATH) or
            value.get("policy_core_manifest_sha256") != file_sha256(POLICY_CORE_MANIFEST_PATH) or
            value.get("initial_state_path") != _relative(expected_initial_state_path) or
            value.get("initial_state_sha256") != expected_initial_state_sha256):
        raise AutonomyError("STANDING_AUTONOMY_AUTHORIZATION_INVALID")
    _utc(value.get("authorized_at_utc")); validate_policy_core_manifest()
    return value

def candidate_payload(candidate: dict[str, object]) -> dict[str, object]:
    return {key: item for key, item in candidate.items() if key not in ("autonomy_policy", "sealed")}

def _validate_artifact_binding(binding: object, code: str) -> Path:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise AutonomyError(code)
    path = PROJECT / str(binding["path"])
    if not path.is_file() or binding["sha256"] != file_sha256(path):
        raise AutonomyError(code)
    return path

def validate_action_validation_receipt(binding: object, contract: dict[str, object]) -> dict[str, object]:
    path = _validate_artifact_binding(binding, "ACTION_VALIDATION_RECEIPT_INVALID")
    receipt = _load_sealed(path, "ACTION_VALIDATION_RECEIPT_INVALID")
    required = {"action_kind", "candidate_payload_sha256", "frozen_specification", "network_requests",
                "schema_version", "scope", "sealed", "stage_id", "validated", "validator"}
    if (set(receipt) != required or receipt.get("schema_version") != "OC3_ACTION_VALIDATION_RECEIPT_001" or
            receipt.get("validated") is not True or receipt.get("network_requests") != 0 or
            receipt.get("action_kind") != contract["action_kind"] or
            receipt.get("candidate_payload_sha256") != contract["candidate_sha256"] or
            receipt.get("stage_id") != contract["stage_id"] or receipt.get("scope") != contract["scope"] or
            receipt.get("frozen_specification") != contract["frozen_specification"]):
        raise AutonomyError("ACTION_VALIDATION_RECEIPT_INVALID")
    _validate_artifact_binding(receipt.get("validator"), "ACTION_VALIDATOR_IDENTITY_MISMATCH")
    return receipt

def validate_literal_resource_manifest(binding: object) -> dict[str, object]:
    path = _validate_artifact_binding(binding, "AUTONOMY_RESOURCE_MANIFEST_INVALID")
    manifest = _load_sealed(path, "AUTONOMY_RESOURCE_MANIFEST_INVALID")
    resources = manifest.get("resources")
    if (manifest.get("broad_crawling") is not False or manifest.get("mirror_substitution") is not False or
            not isinstance(resources, list) or not resources):
        raise AutonomyError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
    required = {"application_body_byte_cap", "evidence_class", "expected_representation", "host", "id",
                "immutable_revision_required", "method", "purpose", "redirects", "retries", "url"}
    for resource in resources:
        if (not isinstance(resource, dict) or not required.issubset(resource) or
                not isinstance(resource.get("url"), str) or not resource["url"].startswith("https://") or
                not isinstance(resource.get("host"), str) or not resource["host"] or
                resource.get("method") not in ("GET", "HEAD") or
                type(resource.get("application_body_byte_cap")) is not int or resource["application_body_byte_cap"] < 0 or
                type(resource.get("redirects")) is not int or resource["redirects"] < 0 or
                type(resource.get("retries")) is not int or resource["retries"] < 0 or
                resource.get("immutable_revision_required") is not True):
            raise AutonomyError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
    return manifest

def validate_autonomous_action_candidate(path: Path) -> tuple[dict[str, object], dict[str, object]]:
    candidate = _load_sealed(path, "AUTONOMOUS_ACTION_CANDIDATE_INVALID")
    contract = candidate.get("autonomy_policy")
    required = {"action_kind", "action_validation_receipt", "application_body_reservation",
        "authority_classes_used", "candidate_hash_mode", "candidate_sha256", "command_argv_sha256",
        "concurrency", "frozen_specification", "git_assertions", "implementation_binding",
        "network_request_reservation", "permit_output_path", "prohibited_scope_assertions",
        "resource_manifest", "resume_rule", "retry_reservation", "retry_rule", "schema_version",
        "scientific_firewall", "scope", "stage_id", "standing_mandate_sha256"}
    if (not isinstance(contract, dict) or set(contract) != required or
            contract.get("schema_version") != "OC3_AUTONOMOUS_ACTION_CONTRACT_001" or
            contract.get("candidate_hash_mode") != "CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED" or
            contract.get("stage_id") != candidate.get("stage_id") or contract.get("scope") != candidate.get("scope") or
            contract.get("command_argv_sha256") != candidate.get("command_argv_sha256") or
            contract.get("standing_mandate_sha256") != file_sha256(MANDATE_PATH)):
        raise AutonomyError("AUTONOMOUS_ACTION_CONTRACT_INVALID")
    payload_sha = sha256_bytes(canonical(candidate_payload(candidate)))
    if contract.get("candidate_sha256") != payload_sha:
        raise AutonomyError("AUTONOMOUS_ACTION_PAYLOAD_MISMATCH")
    argv = candidate.get("command_argv")
    if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv) or sha256_bytes(canonical(argv)) != contract["command_argv_sha256"]:
        raise AutonomyError("COMMAND_ARGV_HASH_MISMATCH")
    implementation = contract.get("implementation_binding")
    if (not isinstance(implementation, dict) or set(implementation) != {"algorithm","sha256"} or
            implementation.get("algorithm") != "OC3_IMPLEMENTATION_AGGREGATE_V1" or
            implementation.get("sha256") != candidate.get("implementation_aggregate")):
        raise AutonomyError("IMPLEMENTATION_BINDING_INVALID")
    _sha(implementation.get("sha256"), "IMPLEMENTATION_BINDING_INVALID")
    _validate_artifact_binding(contract.get("frozen_specification"), "FROZEN_SPECIFICATION_MISMATCH")
    validate_action_validation_receipt(contract.get("action_validation_receipt"), contract)
    if contract.get("resource_manifest") is not None:
        validate_literal_resource_manifest(contract["resource_manifest"])
    for key in ("network_request_reservation", "application_body_reservation", "retry_reservation", "concurrency"):
        if type(contract.get(key)) is not int or contract[key] < 0:
            raise AutonomyError("AUTONOMOUS_ACTION_RESERVATION_INVALID")
    authorities = contract.get("authority_classes_used")
    if not isinstance(authorities, list) or not authorities or len(authorities) != len(set(authorities)):
        raise AutonomyError("AUTONOMOUS_ACTION_AUTHORITY_CLASSES_INVALID")
    if contract.get("scientific_firewall") != {key:0 for key in FIREWALL_KEYS}:
        raise AutonomyError("AUTONOMOUS_ACTION_FIREWALL_INVALID")
    if contract.get("prohibited_scope_assertions") != {key:True for key in PROHIBITED_SCOPE_KEYS}:
        raise AutonomyError("AUTONOMOUS_ACTION_PROHIBITED_SCOPE_INVALID")
    if contract.get("git_assertions") != {"branch":AUTONOMY_BRANCH,"force_push":False,"merge_main":False}:
        raise AutonomyError("AUTONOMOUS_ACTION_GIT_ASSERTIONS_INVALID")
    if contract.get("resume_rule") != {"allowed":False,"prospectively_frozen":True}:
        raise AutonomyError("AUTONOMOUS_ACTION_RESUME_INVALID")
    retry_rule = contract.get("retry_rule")
    if not isinstance(retry_rule, dict) or set(retry_rule) != {"exact_same_resource","prospectively_frozen"}:
        raise AutonomyError("AUTONOMOUS_ACTION_RETRY_INVALID")
    _relative(PROJECT / str(contract.get("permit_output_path", "")), "AUTONOMOUS_PERMIT_PATH_INVALID")
    return candidate, contract

def _registered_binding(candidate_path: Path, candidate: dict[str, object], contract: dict[str, object], *, first=False) -> dict[str, object]:
    return {"action_contract_schema":"OC3_AUTONOMOUS_ACTION_CONTRACT_001","action_kind":contract["action_kind"],
        "candidate_path":_relative(candidate_path),"candidate_sha256":file_sha256(candidate_path),
        "candidate_payload_sha256":contract["candidate_sha256"],
        "registration_state":"FIRST_PENDING_AUTONOMOUS_ACTION" if first else "PENDING_AUTONOMOUS_ACTION",
        "scope":contract["scope"],"stage_id":contract["stage_id"]}

def _validate_active_context(state: dict[str, object], authorization_path: Path,
                             state_path: Path = STATE_PATH) -> dict[str, object]:
    if state.get("active") is not True or state.get("state") != STATE_ACTIVE:
        raise AutonomyError(MANDATE_NOT_ACTIVE)
    initial_sha = _sha(state.get("standing_authorization_initial_state_sha256"), "AUTONOMY_INITIAL_STATE_SHA_INVALID")
    authorization = validate_standing_authorization(
        authorization_path, expected_initial_state_sha256=initial_sha,
        expected_initial_state_path=state_path)
    if state.get("standing_authorization") != _binding(authorization_path):
        raise AutonomyError("STANDING_AUTHORIZATION_STATE_BINDING_MISMATCH")
    validate_policy_core_manifest()
    return authorization

def evaluate_policy(*, candidate_path: Path, state_path: Path = STATE_PATH,
                    standing_authorization_path: Path = STANDING_AUTHORIZATION_PATH,
                    current_branch: str = AUTONOMY_BRANCH, require_registered: bool = True) -> dict[str, object]:
    validate_static_authorities(); mandate = validate_mandate(); state = validate_state(state_path)
    candidate, contract = validate_autonomous_action_candidate(candidate_path)
    if require_registered:
        registered = state.get("registered_pending_action")
        if not isinstance(registered, dict):
            return _refusal("NO_REGISTERED_PENDING_ACTION")
        expected = _registered_binding(candidate_path, candidate, contract,
                                       first=registered.get("registration_state") == "FIRST_PENDING_AUTONOMOUS_ACTION")
        if registered != expected or registered.get("registration_state") not in ("FIRST_PENDING_AUTONOMOUS_ACTION","PENDING_AUTONOMOUS_ACTION"):
            return _refusal("CANDIDATE_STATE_BINDING_MISMATCH")
    if not Path(standing_authorization_path).is_file():
        return _refusal(MANDATE_NOT_ACTIVE)
    try:
        _validate_active_context(state, standing_authorization_path, state_path)
    except AutonomyError as exc:
        return _refusal(exc.code)
    if current_branch != AUTONOMY_BRANCH:
        return _refusal("UNAUTHORIZED_BRANCH")
    if contract["standing_mandate_sha256"] != file_sha256(MANDATE_PATH):
        return _refusal("MANDATE_BINDING_MISMATCH")
    if not set(contract["authority_classes_used"]).issubset(set(mandate["allowed_evidence_classes"])):
        return _refusal("AUTHORITY_CLASS_EXPANSION")
    if contract["network_request_reservation"] > state["requests_remaining"]:
        return _refusal("REQUEST_BUDGET_OVERFLOW")
    if contract["application_body_reservation"] > state["body_budget_remaining"]:
        return _refusal("BODY_BUDGET_OVERFLOW")
    if contract["concurrency"] > mandate["budgets"]["concurrency"]:
        return _refusal("CONCURRENCY_LIMIT_EXCEEDED")
    retry_rule = contract["retry_rule"]; retries = contract["retry_reservation"]
    if retries > mandate["budgets"]["retries_max_per_exact_resource"] or (
            retries and (retry_rule["prospectively_frozen"] is not True or retry_rule["exact_same_resource"] is not True)):
        return _refusal("RETRY_NOT_PROSPECTIVELY_FROZEN")
    if contract["resume_rule"] != {"allowed":False,"prospectively_frozen":True}:
        return _refusal("RESUME_NOT_FROZEN")
    if contract["scientific_firewall"] != {key:0 for key in FIREWALL_KEYS}:
        return _refusal("SCIENTIFIC_FIREWALL_VIOLATION")
    if contract["prohibited_scope_assertions"] != {key:True for key in PROHIBITED_SCOPE_KEYS}:
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
    if evaluation["decision"] != ELIGIBLE: raise AutonomyError(str(evaluation["decision"]))
    _utc(issued_at_utc); _, contract = validate_autonomous_action_candidate(candidate_path); state = validate_state(state_path)
    candidate_sha = file_sha256(candidate_path)
    return sealed({"action_kind":contract["action_kind"],"authorization_basis":"STANDING_AUTONOMY_MANDATE_001",
        "body_budget_reserved":contract["application_body_reservation"],"candidate_path":_relative(candidate_path),
        "candidate_payload_sha256":contract["candidate_sha256"],"candidate_sha256":candidate_sha,
        "command_argv_sha256":contract["command_argv_sha256"],"concurrency_reserved":contract["concurrency"],
        "initial_state_sha256":state["standing_authorization_initial_state_sha256"],"issued_at_utc":issued_at_utc,
        "mandate_sha256":file_sha256(MANDATE_PATH),"network_budget_reserved":contract["network_request_reservation"],
        "permit_id":f"OC3-AUTONOMOUS-PERMIT-{state['sequence']+1:06d}-{candidate_sha[:12]}",
        "permit_type":"AUTONOMOUS_EXECUTION_PERMIT","policy_core_manifest_sha256":file_sha256(POLICY_CORE_MANIFEST_PATH),
        "resource_manifest_sha256":None if contract["resource_manifest"] is None else contract["resource_manifest"]["sha256"],
        "resume":contract["resume_rule"]["allowed"],"retries_reserved":contract["retry_reservation"],
        "schema_version":"OC3_AUTONOMOUS_EXECUTION_PERMIT_002","scientific_firewall":contract["scientific_firewall"],
        "scope":contract["scope"],"sequence":state["sequence"],"stage_id":contract["stage_id"],
        "standing_authorization_sha256":file_sha256(standing_authorization_path),
        "state_before_sha256":file_sha256(state_path)})

def issue_permit(*, candidate_path: Path, state_path: Path, standing_authorization_path: Path,
                 output_path: Path, ledger_directory: Path, issued_at_utc: str,
                 current_branch: str = AUTONOMY_BRANCH) -> dict[str, object]:
    _, contract = validate_autonomous_action_candidate(candidate_path)
    expected = (PROJECT / str(contract["permit_output_path"])).resolve()
    if Path(output_path).resolve() != expected: raise AutonomyError("AUTONOMOUS_PERMIT_OUTPUT_PATH_MISMATCH")
    if expected.exists(): raise AutonomyError("AUTONOMOUS_PERMIT_ALREADY_EXISTS")
    permit = build_permit(candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path,issued_at_utc=issued_at_utc,current_branch=current_branch)
    write_json_immutable(expected, permit); permit_sha = file_sha256(expected)
    issuance = sealed({"candidate_sha256":file_sha256(candidate_path),"issued_at_utc":issued_at_utc,
        "permit_id":permit["permit_id"],"permit_sha256":permit_sha,"sequence":permit["sequence"],
        "state_before_sha256":permit["state_before_sha256"],"state":"AUTONOMOUS_PERMIT_ISSUED"})
    write_json_immutable(Path(ledger_directory)/"PERMIT_ISSUANCE"/f"{permit_sha}.json", issuance)
    return permit

def _consumption_marker_path(permit_path: Path, consumption_directory: Path) -> Path:
    return Path(consumption_directory) / f"{file_sha256(permit_path)}.json"

def validate_permit(permit_path: Path, *, candidate_path: Path, state_path: Path,
                    standing_authorization_path: Path, consumption_directory: Path,
                    allow_consumed: bool = False) -> dict[str, object]:
    permit = _load_sealed(permit_path,"AUTONOMOUS_PERMIT_INVALID")
    marker = _consumption_marker_path(permit_path,consumption_directory)
    if marker.exists() and not allow_consumed: raise AutonomyError("AUTONOMOUS_PERMIT_ALREADY_CONSUMED")
    _, contract = validate_autonomous_action_candidate(candidate_path)
    state = validate_state(state_path)
    evaluation = evaluate_policy(candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path)
    if evaluation["decision"] != ELIGIBLE: raise AutonomyError(str(evaluation["decision"]))
    required = {"action_kind","authorization_basis","body_budget_reserved","candidate_path",
        "candidate_payload_sha256","candidate_sha256","command_argv_sha256","concurrency_reserved",
        "initial_state_sha256","issued_at_utc","mandate_sha256","network_budget_reserved","permit_id",
        "permit_type","policy_core_manifest_sha256","resource_manifest_sha256","resume","retries_reserved",
        "schema_version","scientific_firewall","scope","sealed","sequence","stage_id",
        "standing_authorization_sha256","state_before_sha256"}
    if (set(permit) != required or permit.get("schema_version") != "OC3_AUTONOMOUS_EXECUTION_PERMIT_002" or
            permit.get("permit_type") != "AUTONOMOUS_EXECUTION_PERMIT" or
            permit.get("authorization_basis") != "STANDING_AUTONOMY_MANDATE_001" or
            permit.get("mandate_sha256") != file_sha256(MANDATE_PATH) or
            permit.get("policy_core_manifest_sha256") != file_sha256(POLICY_CORE_MANIFEST_PATH) or
            permit.get("standing_authorization_sha256") != file_sha256(standing_authorization_path) or
            permit.get("initial_state_sha256") != state["standing_authorization_initial_state_sha256"] or
            permit.get("state_before_sha256") != file_sha256(state_path) or permit.get("sequence") != state["sequence"] or
            permit.get("candidate_sha256") != file_sha256(candidate_path) or
            permit.get("candidate_payload_sha256") != contract["candidate_sha256"] or
            permit.get("candidate_path") != _relative(candidate_path) or
            permit.get("command_argv_sha256") != contract["command_argv_sha256"] or
            permit.get("action_kind") != contract["action_kind"] or
            permit.get("network_budget_reserved") != contract["network_request_reservation"] or
            permit.get("body_budget_reserved") != contract["application_body_reservation"] or
            permit.get("retries_reserved") != contract["retry_reservation"] or
            permit.get("concurrency_reserved") != contract["concurrency"] or permit.get("resume") is not False or
            permit.get("scientific_firewall") != {key:0 for key in FIREWALL_KEYS}):
        raise AutonomyError("AUTONOMOUS_PERMIT_BINDING_MISMATCH")
    _utc(permit.get("issued_at_utc"))
    return permit

def consume_permit(permit_path: Path, *, candidate_path: Path, state_path: Path,
                   standing_authorization_path: Path, consumption_directory: Path,
                   consumed_at_utc: str) -> Path:
    permit = validate_permit(permit_path,candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path,consumption_directory=consumption_directory)
    _utc(consumed_at_utc); marker = _consumption_marker_path(permit_path,consumption_directory)
    write_json_immutable(marker,sealed({"candidate_sha256":permit["candidate_sha256"],
        "consumed_at_utc":consumed_at_utc,"permit_id":permit["permit_id"],"permit_sha256":file_sha256(permit_path),
        "state_before_sha256":permit["state_before_sha256"],"state":"PERMIT_CONSUMPTION_INTENT_RECORDED"}))
    return marker

def validate_consumption_marker(permit_path: Path, *, candidate_path: Path, consumption_directory: Path) -> dict[str, object]:
    marker = _load_sealed(_consumption_marker_path(permit_path,consumption_directory),"AUTONOMOUS_PERMIT_CONSUMPTION_MISSING")
    permit = _load_sealed(permit_path,"AUTONOMOUS_PERMIT_INVALID")
    if (set(marker) != {"candidate_sha256","consumed_at_utc","permit_id","permit_sha256","sealed","state","state_before_sha256"} or
            marker.get("state") != "PERMIT_CONSUMPTION_INTENT_RECORDED" or
            marker.get("permit_sha256") != file_sha256(permit_path) or marker.get("permit_id") != permit.get("permit_id") or
            marker.get("state_before_sha256") != permit.get("state_before_sha256") or
            marker.get("candidate_sha256") != file_sha256(candidate_path)):
        raise AutonomyError("AUTONOMOUS_PERMIT_CONSUMPTION_INVALID")
    _utc(marker.get("consumed_at_utc")); return marker

def atomic_replace_state(path: Path, value: dict[str, object]) -> None:
    path=Path(path); data=canonical(value)+b"\n"; path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(f".{path.name}.tmp-{os.getpid()}")
    if temporary.exists(): raise AutonomyError("AUTONOMY_STATE_TEMP_CONFLICT")
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
        raise AutonomyError("AUTONOMY_ACTIVATION_STATE_INVALID")
    if current_branch != AUTONOMY_BRANCH: raise AutonomyError("UNAUTHORIZED_BRANCH")
    if any(Path(ledger_directory).glob("*_ACTIVATION.json")): raise AutonomyError("AUTONOMY_ALREADY_ACTIVATED")
    registered=state.get("registered_pending_action")
    if not isinstance(registered,dict) or registered.get("registration_state") != "FIRST_PENDING_AUTONOMOUS_ACTION":
        raise AutonomyError("AUTONOMY_FIRST_ACTION_BINDING_INVALID")
    candidate_path=PROJECT/str(registered.get("candidate_path","")); candidate,contract=validate_autonomous_action_candidate(candidate_path)
    if registered != _registered_binding(candidate_path,candidate,contract,first=True):
        raise AutonomyError("AUTONOMY_FIRST_ACTION_BINDING_INVALID")
    initial_state_sha=file_sha256(state_path)
    validate_standing_authorization(standing_authorization_path,
        expected_initial_state_sha256=initial_state_sha,expected_initial_state_path=state_path)
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({"active":True,
        "current_stage":"AUTONOMOUS_POLICY_EVALUATION","sequence":state["sequence"]+1,
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
    if current_branch != AUTONOMY_BRANCH: raise AutonomyError("UNAUTHORIZED_BRANCH")
    if state.get("registered_pending_action") is not None: raise AutonomyError("UNRESOLVED_REGISTERED_ACTION")
    candidate,contract=validate_autonomous_action_candidate(candidate_path)
    evaluation=evaluate_policy(candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path,current_branch=current_branch,require_registered=False)
    if evaluation["decision"] != ELIGIBLE: raise AutonomyError(str(evaluation["decision"]))
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({
        "registered_pending_action":_registered_binding(candidate_path,candidate,contract),
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
    return (counters.get("network_requests_started",terminal.get("network_requests_started")),
            terminal.get("application_body_bytes_read",counters.get("application_body_bytes_read")),
            counters.get("retry_requests",terminal.get("retry_requests")))

def transition_completed_action(*, state_path: Path, candidate_path: Path, permit_path: Path,
                                standing_authorization_path: Path, consumption_directory: Path,
                                terminal_path: Path, terminal_sha256: str,
                                request_delta: int, body_delta: int, retry_delta: int,
                                ledger_directory: Path, transitioned_at_utc: str, reason: str) -> dict[str, object]:
    _utc(transitioned_at_utc); state=validate_state(state_path)
    permit=validate_permit(permit_path,candidate_path=candidate_path,state_path=state_path,
        standing_authorization_path=standing_authorization_path,consumption_directory=consumption_directory,
        allow_consumed=True)
    validate_consumption_marker(permit_path,candidate_path=candidate_path,consumption_directory=consumption_directory)
    terminal_path=Path(terminal_path)
    if not terminal_path.is_file(): raise AutonomyError("AUTONOMY_TERMINAL_ARTIFACT_MISSING")
    terminal=_load_sealed(terminal_path,"AUTONOMY_TERMINAL_ARTIFACT_INVALID"); terminal_sha=file_sha256(terminal_path)
    if _sha(terminal_sha256,"AUTONOMY_TERMINAL_SHA_INVALID") != terminal_sha:
        raise AutonomyError("AUTONOMY_TERMINAL_SHA_MISMATCH")
    if terminal.get("stage_id") is not None and terminal.get("stage_id") != permit["stage_id"]:
        raise AutonomyError("AUTONOMY_TERMINAL_STAGE_MISMATCH")
    if terminal.get("scope") is not None and terminal.get("scope") != permit["scope"]:
        raise AutonomyError("AUTONOMY_TERMINAL_SCOPE_MISMATCH")
    if any(type(x) is not int or x<0 for x in (request_delta,body_delta,retry_delta)):
        raise AutonomyError("AUTONOMY_TRANSITION_DELTA_INVALID")
    if (request_delta>permit["network_budget_reserved"] or body_delta>permit["body_budget_reserved"] or
            retry_delta>permit["retries_reserved"]):
        raise AutonomyError("PERMIT_RESERVATION_EXCEEDED_REQUIRES_STOP")
    if request_delta>state["requests_remaining"] or body_delta>state["body_budget_remaining"]:
        raise AutonomyError("AUTONOMY_TRANSITION_BUDGET_INVALID")
    observed=_terminal_counters(terminal)
    for actual,expected in zip(observed,(request_delta,body_delta,retry_delta)):
        if actual is not None and actual!=expected: raise AutonomyError("AUTONOMY_TERMINAL_COUNTER_MISMATCH")
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({
        "body_budget_remaining":state["body_budget_remaining"]-body_delta,"current_stage":STATE_AWAITING_ACTION,
        "last_completed_stage":permit["stage_id"],"last_terminal":_binding(terminal_path),
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
    if re.fullmatch(r"[A-Z0-9_]+",blocker_code) is None: raise AutonomyError("AUTONOMY_STOP_BLOCKER_INVALID")
    state=validate_state(state_path); _validate_active_context(state,standing_authorization_path,state_path)
    if current_branch!=AUTONOMY_BRANCH: raise AutonomyError("UNAUTHORIZED_BRANCH")
    report=Path(stop_report_path)
    if not report.is_file() or report.stat().st_size==0 or report.stat().st_size>COMPACT_ARTIFACT_MAX_BYTES:
        raise AutonomyError("AUTONOMY_STOP_REPORT_INVALID")
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
    if outcome not in TERMINAL_OUTCOMES: raise AutonomyError("SCIENTIFIC_OUTCOME_NOT_FROZEN")
    state=validate_state(state_path); _validate_active_context(state,standing_authorization_path,state_path)
    if current_branch!=AUTONOMY_BRANCH: raise AutonomyError("UNAUTHORIZED_BRANCH")
    if state.get("registered_pending_action") is not None: raise AutonomyError("SCIENTIFIC_TERMINAL_PENDING_ACTION")
    if state.get("firewall_counters")!={key:0 for key in FIREWALL_KEYS}:
        raise AutonomyError("SCIENTIFIC_TERMINAL_FIREWALL_DIRTY")
    report=Path(final_report_path)
    if not report.is_file() or report.stat().st_size==0: raise AutonomyError("SCIENTIFIC_TERMINAL_REPORT_INVALID")
    matrix_binding=None
    if claim_matrix_path is not None:
        matrix=Path(claim_matrix_path)
        if not matrix.is_file() or matrix.stat().st_size==0: raise AutonomyError("SCIENTIFIC_TERMINAL_CLAIM_MATRIX_INVALID")
        matrix_binding=_binding(matrix)
    previous_sha=_write_snapshot(state_path,state,ledger_directory)
    body={k:v for k,v in state.items() if k!="sealed"}; body.update({"active":False,
        "current_stage":STATE_SCIENTIFIC_TERMINAL,"scientific_outcome":outcome,
        "sequence":state["sequence"]+1,"state":STATE_SCIENTIFIC_TERMINAL})
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
        except ValueError as exc: raise AutonomyError("GIT_PATH_OUTSIDE_PROJECT") from exc
        lowered=relative.lower()
        if any(lowered.startswith(p.lower()) for p in RUNTIME_TREE_PREFIXES): raise AutonomyError("GIT_RUNTIME_EVIDENCE_FORBIDDEN")
        if any(lowered.endswith(s) for s in FORBIDDEN_GIT_SUFFIXES): raise AutonomyError("GIT_SCIENTIFIC_OR_ARCHIVE_BODY_FORBIDDEN")
        basename=absolute.name.lower()
        if basename==".env" or any(p in basename for p in SECRET_NAME_PARTS): raise AutonomyError("GIT_CREDENTIAL_PATH_FORBIDDEN")
        if absolute.is_symlink() or not absolute.is_file(): raise AutonomyError("GIT_NONREGULAR_PATH_FORBIDDEN")
        size=absolute.stat().st_size
        if size>COMPACT_ARTIFACT_MAX_BYTES: raise AutonomyError("GIT_COMPACT_ARTIFACT_SIZE_EXCEEDED")
        payload=absolute.read_bytes()
        if any(pattern.search(payload) for pattern in SECRET_CONTENT_PATTERNS): raise AutonomyError("GIT_SECRET_CONTENT_FORBIDDEN")
        total+=size; largest=max(largest,size); normalized.append(relative)
    return {"file_count":len(normalized),"files":sorted(normalized),"largest_file_bytes":largest,
        "network_requests":0,"per_file_limit_bytes":COMPACT_ARTIFACT_MAX_BYTES,
        "state":"GIT_STAGED_SIZE_FIREWALL_PASS","total_bytes":total}

def audit_staged_compact_artifacts(*, project: Path=PROJECT) -> dict[str,object]:
    project=Path(project).resolve()
    result=subprocess.run(["git","diff","--cached","--name-only","--diff-filter=ACMR","-z"],
                          cwd=project,check=True,capture_output=True)
    names=[n.decode("utf-8") for n in result.stdout.split(b"\0") if n]
    if not names: raise AutonomyError("GIT_NO_STAGED_ARTIFACTS")
    return audit_compact_paths([Path(n) for n in names],project=project)

def compact_status(state_path: Path=STATE_PATH) -> dict[str,object]:
    state=validate_state(state_path)
    return {"active":state["active"],"mission_id":state["mission_id"],
        "permit_state":MANDATE_NOT_ACTIVE if not state["active"] else "ACTIVE_POLICY_EVALUATION",
        "requests_remaining":state["requests_remaining"],"sequence":state["sequence"],"state":state["state"]}
