"""Deterministic policy engine for bounded OC3 research autonomy.

The governor evaluates authorization and budget policy only.  It does not
decide scientific truth and it has no network transport capability.
"""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

from .core import canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)


MISSION_ID = "OC3-PHOTSYS-ZERO-BYTE-PROVENANCE-AUTONOMY-001"
MISSION_SCOPE = "PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_MISSION_ONLY"
AUTONOMY_BRANCH = "autopilot/photsys-zero-byte"
STATE_WAITING = "WAITING_FOR_STANDING_HUMAN_AUTHORIZATION"
STATE_ACTIVE = "ACTIVE"
STOP_REQUIRES_HUMAN = "STOP_REQUIRES_HUMAN"
MANDATE_NOT_ACTIVE = "MANDATE_NOT_ACTIVE"
NO_PERMIT_ISSUED = "NO_PERMIT_ISSUED"
ELIGIBLE = "ELIGIBLE_FOR_AUTONOMOUS_PERMIT"

GOVERNANCE_AMENDMENT_PATH = PROJECT / "OC3_AUTONOMOUS_EXECUTION_GOVERNANCE_AMENDMENT_001.md"
GOVERNANCE_AMENDMENT_SHA256 = "f255430eb8b36a7a40b71ee522d81f0664b00ebd16471324cc7f06c61a307b47"
MANDATE_DOCUMENT_PATH = PROJECT / "OC3_AUTONOMY_MANDATE_001.md"
MANDATE_DOCUMENT_SHA256 = "a3a70c2adf2044d366e2730995b6e6d814582e1e06ba8cafad78bff6a330f24d"
MANDATE_PATH = PROJECT / "oc3/INPUTS/OC3_AUTONOMY_MANDATE_001.json"
MANDATE_SHA256 = "4364eb22ce95316917b77f4e7dc3dabcd98a8d33fa10c887fb531ae8d49971f8"
RUNBOOK_PATH = PROJECT / "OC3_AUTONOMOUS_RESEARCH_RUNBOOK_001.md"
RUNBOOK_SHA256 = "b8884ca9930a3098763b0a945649ab9dca9da792aa8db35e2ec051ed13dff4cd"
RANGE_AMENDMENT_PATH = PROJECT / "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_AUTONOMY_AMENDMENT_001.md"
RANGE_AMENDMENT_SHA256 = "0e8dfe1bba8f1741385a955d5b47affc5cb468116815789ba2f5d92bf00558a2"
SCIENTIFIC_SPEC_PATH = PROJECT / "OC3_PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_SPEC.md"
SCIENTIFIC_SPEC_SHA256 = "4b2db6523e9acc3add101199966e6fe372c6105d74edd59089eae1fdc09cc614"

STANDING_AUTHORIZATION_PATH = PROJECT / "oc3/OC3_AUTONOMY_STANDING_AUTHORIZATION_001.json"
STATE_PATH = PROJECT / "oc3/OC3_AUTONOMY_STATE_001.json"
LEDGER_ROOT = PROJECT / "oc3/AUTONOMY_LEDGER"
STOP_REPORT_PATH = PROJECT / "AUTOPILOT_STOP_REPORT.md"
RANGE_CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_002.json"
RANGE_MANIFEST_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_RESOURCE_MANIFEST_002.json"
RANGE_MANIFEST_SHA256 = "6ca4360ed1b4b59161350933745192d6d2df5bbda877bb0bc0996400cad3eb46"

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
COMPACT_ARTIFACT_MAX_BYTES = 5 * 1024 * 1024
RUNTIME_TREE_PREFIXES = (
    "oc3/metadata_bootstrap/",
    "oc3/photsys_archive_head_probe/",
    "oc3/photsys_archive_range_size_probe/",
    "oc3/photsys_authority_full_acquisition/",
    "oc3/photsys_byte_histogram/",
    "oc3/photsys_selective_value_validation/",
    "oc3/photsys_zero_byte_provenance/",
)
FORBIDDEN_GIT_SUFFIXES = (
    ".fit", ".fits", ".fits.gz", ".tar", ".tar.gz", ".tgz", ".zip",
)
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


def _require_sha(value: object, code: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
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


def validate_static_authorities() -> dict[str, str]:
    expected = {
        GOVERNANCE_AMENDMENT_PATH: GOVERNANCE_AMENDMENT_SHA256,
        MANDATE_DOCUMENT_PATH: MANDATE_DOCUMENT_SHA256,
        MANDATE_PATH: MANDATE_SHA256,
        RUNBOOK_PATH: RUNBOOK_SHA256,
        RANGE_AMENDMENT_PATH: RANGE_AMENDMENT_SHA256,
        SCIENTIFIC_SPEC_PATH: SCIENTIFIC_SPEC_SHA256,
        RANGE_MANIFEST_PATH: RANGE_MANIFEST_SHA256,
    }
    for path, digest in expected.items():
        if not path.is_file() or file_sha256(path) != digest:
            raise AutonomyError("AUTONOMY_STATIC_AUTHORITY_MISMATCH")
    return {str(path.relative_to(PROJECT)): digest for path, digest in expected.items()}


def validate_mandate(path: Path = MANDATE_PATH) -> dict[str, object]:
    if Path(path).resolve() == MANDATE_PATH.resolve() and file_sha256(path) != MANDATE_SHA256:
        raise AutonomyError("AUTONOMY_MANDATE_MISMATCH")
    value = _load_sealed(path, "AUTONOMY_MANDATE_INVALID")
    if (value.get("schema_version") != "OC3_AUTONOMY_MANDATE_001" or
            value.get("authorization_state") != "PENDING_HUMAN_AUTHORIZATION" or
            value.get("active") is not False or value.get("mission_id") != MISSION_ID or
            value.get("mission_scope") != MISSION_SCOPE or
            value.get("autonomy_branch") != AUTONOMY_BRANCH or
            tuple(value.get("allowed_scientific_outcomes", [])) != TERMINAL_OUTCOMES or
            tuple(value.get("allowed_evidence_classes", [])) != ALLOWED_AUTHORITY_CLASSES):
        raise AutonomyError("AUTONOMY_MANDATE_INVALID")
    budgets = value.get("budgets", {})
    if budgets != {"application_body_bytes_parent": 33_554_432,
                    "application_body_bytes_remaining": 17_544_938,
                    "concurrency": 1,
                    "historical_conservative_body_maximum": 16_009_494,
                    "public_source_requests_historical": 6,
                    "public_source_requests_parent": 24,
                    "public_source_requests_remaining": 18,
                    "retries_default": 0}:
        raise AutonomyError("AUTONOMY_MANDATE_BUDGET_INVALID")
    if value.get("firewall") != {key: 0 for key in FIREWALL_KEYS}:
        raise AutonomyError("AUTONOMY_MANDATE_FIREWALL_INVALID")
    return value


def validate_standing_authorization(path: Path = STANDING_AUTHORIZATION_PATH,
                                    mandate_path: Path = MANDATE_PATH) -> dict[str, object]:
    value = _load_sealed(path, "STANDING_AUTONOMY_AUTHORIZATION_INVALID")
    required = {"authorization_state", "authorized", "authorized_at_utc", "authorized_by",
                "continuation_policy", "mandate_path", "mandate_sha256", "mission_id",
                "schema_version", "scope", "sealed"}
    if (set(value) != required or
            value.get("schema_version") != "OC3_AUTONOMY_STANDING_AUTHORIZATION_001" or
            value.get("authorization_state") != "STANDING_HUMAN_AUTONOMY_AUTHORIZATION" or
            value.get("authorized") is not True or
            not isinstance(value.get("authorized_by"), str) or not value["authorized_by"].strip() or
            value.get("continuation_policy") !=
            "CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN" or
            value.get("mandate_path") != str(Path(mandate_path).resolve().relative_to(PROJECT)) or
            value.get("mandate_sha256") != file_sha256(mandate_path) or
            value.get("mission_id") != MISSION_ID or value.get("scope") != MISSION_SCOPE):
        raise AutonomyError("STANDING_AUTONOMY_AUTHORIZATION_INVALID")
    _utc(value.get("authorized_at_utc"))
    return value


def validate_state(path: Path = STATE_PATH) -> dict[str, object]:
    value = _load_sealed(path, "AUTONOMY_STATE_INVALID")
    required = {"active", "autonomy_branch", "body_budget_parent", "body_budget_remaining",
                "current_stage", "firewall_counters", "governance_amendment",
                "governing_specification", "historical_conservative_body_maximum",
                "last_completed_stage", "mandate", "mission_id", "prohibited_next_phases",
                "registered_pending_action", "request_budget_parent", "requests_historical_consumed",
                "requests_remaining", "schema_version", "scientific_outcome", "scientific_question",
                "sealed", "sequence", "standing_authorization_path", "state", "stop_reason",
                "terminal_outcomes"}
    if (set(value) != required or value.get("schema_version") != "OC3_AUTONOMY_STATE_001" or
            value.get("mission_id") != MISSION_ID or value.get("autonomy_branch") != AUTONOMY_BRANCH or
            type(value.get("sequence")) is not int or value["sequence"] < 0 or
            tuple(value.get("terminal_outcomes", [])) != TERMINAL_OUTCOMES or
            value.get("governing_specification", {}).get("sha256") != SCIENTIFIC_SPEC_SHA256 or
            value.get("governance_amendment", {}).get("sha256") != GOVERNANCE_AMENDMENT_SHA256 or
            value.get("mandate", {}).get("sha256") != file_sha256(MANDATE_PATH) or
            value.get("standing_authorization_path") != str(STANDING_AUTHORIZATION_PATH.relative_to(PROJECT))):
        raise AutonomyError("AUTONOMY_STATE_INVALID")
    if value.get("firewall_counters") != {key: 0 for key in FIREWALL_KEYS}:
        raise AutonomyError("AUTONOMY_STATE_FIREWALL_INVALID")
    return value


def validate_resource_manifest(path: Path) -> dict[str, object]:
    value = _load_sealed(path, "AUTONOMY_RESOURCE_MANIFEST_INVALID")
    resources = value.get("resources")
    if (value.get("schema_version") !=
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_RESOURCE_MANIFEST_002" or
            value.get("stage_id") !=
            "OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-RANGE-SIZE-PROBE-001" or
            value.get("scope") != "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_ONLY" or
            value.get("broad_crawling") is not False or value.get("mirror_substitution") is not False or
            not isinstance(resources, list) or len(resources) != 1):
        raise AutonomyError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
    resource = resources[0]
    if (resource.get("id") != "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE" or
            resource.get("commit") != "dd30297f9d50fcb7bbba57d79d4b8fc86cb35701" or
            not isinstance(resource.get("evidence_class"), str) or not resource["evidence_class"] or
            resource.get("url") != "https://codeload.github.com/desihub/desitarget/tar.gz/"
            "dd30297f9d50fcb7bbba57d79d4b8fc86cb35701" or
            resource.get("host") != "codeload.github.com" or resource.get("method") != "GET" or
            resource.get("range") != "bytes=0-0" or resource.get("application_body_byte_cap") != 0 or
            resource.get("redirects") != 0 or resource.get("retries") != 0 or
            resource.get("immutable_revision_required") is not True or
            resource.get("expected_representation") != "HTTP_206_HEADERS_ONLY_NO_BODY_MATERIALIZATION" or
            resource.get("accepted_content_types") !=
            ["application/gzip", "application/x-gzip", "application/octet-stream"]):
        raise AutonomyError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
    return value


def validate_candidate_structure(path: Path) -> dict[str, object]:
    value = _load_sealed(path, "AUTONOMY_CANDIDATE_INVALID")
    if (value.get("schema_version") !=
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_002" or
            value.get("candidate_state") != "PENDING_STANDING_AUTONOMY" or
            value.get("stage_id") !=
            "OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-RANGE-SIZE-PROBE-001" or
            value.get("scope") != "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_ONLY" or
            value.get("implementation_aggregate") != implementation_hash(PROJECT)):
        raise AutonomyError("AUTONOMY_CANDIDATE_INVALID")
    argv = value.get("command_argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv) or (
            value.get("command_argv_sha256") != sha256_bytes(canonical(argv))):
        raise AutonomyError("COMMAND_ARGV_HASH_MISMATCH")
    from .photsys_archive_range_size_probe import exact_autonomous_command
    if argv != exact_autonomous_command(PROJECT):
        raise AutonomyError("COMMAND_ARGV_NOT_FROZEN")
    governance = value.get("execution_governance", {})
    if (governance.get("permit_type") != "AUTONOMOUS_EXECUTION_PERMIT" or
            governance.get("authorization_basis") != "STANDING_AUTONOMY_MANDATE_001" or
            governance.get("mandate_sha256") != file_sha256(MANDATE_PATH) or
            governance.get("resume") is not False or governance.get("per_stage_human_authorization") is not False):
        raise AutonomyError("AUTONOMY_CANDIDATE_GOVERNANCE_INVALID")
    manifest_binding = value.get("resource_manifest", {})
    manifest_path = PROJECT / str(manifest_binding.get("path", ""))
    if (not manifest_path.is_file() or manifest_binding.get("sha256") != file_sha256(manifest_path)):
        raise AutonomyError("AUTONOMY_RESOURCE_MANIFEST_INVALID")
    validate_resource_manifest(manifest_path)
    return value


def _refusal(code: str) -> dict[str, object]:
    return {"decision": code, "permit_state": NO_PERMIT_ISSUED}


def evaluate_policy(*, candidate_path: Path = RANGE_CANDIDATE_PATH,
                    state_path: Path = STATE_PATH,
                    standing_authorization_path: Path = STANDING_AUTHORIZATION_PATH,
                    current_branch: str = AUTONOMY_BRANCH) -> dict[str, object]:
    validate_static_authorities()
    validate_mandate()
    state = validate_state(state_path)
    candidate = validate_candidate_structure(candidate_path)
    registered = state.get("registered_pending_action", {})
    if (registered.get("candidate_path") != str(Path(candidate_path).resolve().relative_to(PROJECT)) or
            registered.get("candidate_sha256") != file_sha256(candidate_path) or
            registered.get("registration_state") != "FIRST_PENDING_AUTONOMOUS_ACTION"):
        return _refusal("CANDIDATE_STATE_BINDING_MISMATCH")
    if not Path(standing_authorization_path).is_file():
        return _refusal(MANDATE_NOT_ACTIVE)
    try:
        authorization = validate_standing_authorization(standing_authorization_path)
    except AutonomyError as exc:
        return _refusal(exc.code)
    if state.get("active") is not True or state.get("state") != STATE_ACTIVE:
        return _refusal(MANDATE_NOT_ACTIVE)
    if current_branch != AUTONOMY_BRANCH or candidate.get("git_policy", {}).get("branch") != AUTONOMY_BRANCH:
        return _refusal("UNAUTHORIZED_BRANCH")
    if candidate.get("git_policy", {}).get("force_push") is not False:
        return _refusal("FORCE_PUSH_FORBIDDEN")
    network = candidate.get("network_caps", {})
    if type(network.get("requests")) is not int or network["requests"] > state["requests_remaining"]:
        return _refusal("REQUEST_BUDGET_OVERFLOW")
    if network["requests"] < 0:
        return _refusal("REQUEST_BUDGET_INVALID")
    if type(network.get("application_body_bytes")) is not int or (
            network["application_body_bytes"] > state["body_budget_remaining"]):
        return _refusal("BODY_BUDGET_OVERFLOW")
    if network["application_body_bytes"] < 0:
        return _refusal("BODY_BUDGET_INVALID")
    if network.get("concurrency") != 1:
        return _refusal("CONCURRENCY_LIMIT_EXCEEDED")
    if network.get("retries") != 0:
        return _refusal("RETRY_NOT_FROZEN_ZERO")
    if candidate.get("execution_governance", {}).get("resume") is not False:
        return _refusal("RESUME_NOT_FROZEN")
    expected_negative_capabilities = {
        "archive_acquisition": False, "archive_body_read": False,
        "automatic_resume": False, "generic_get": False, "head": False,
        "redirect": False, "retry": False, "semantic_research": False,
        "synthetic_zero_initialization": False,
    }
    if candidate.get("negative_capabilities") != expected_negative_capabilities:
        return _refusal("NEGATIVE_CAPABILITY_EXPANSION")
    firewall = candidate.get("scientific_firewall", {})
    for key in FIREWALL_KEYS:
        if firewall.get(key) != 0:
            return _refusal(f"{key}_FORBIDDEN")
    forbidden = candidate.get("forbidden_scope", {})
    if forbidden.get("panel_v2") is not True:
        return _refusal("PANEL_V2_SCOPE_FORBIDDEN")
    if forbidden.get("p1") is not True:
        return _refusal("P1_SCOPE_FORBIDDEN")
    if forbidden.get("resolver") is not True:
        return _refusal("RESOLVER_CONSTRUCTION_FORBIDDEN")
    manifest = validate_resource_manifest(PROJECT / candidate["resource_manifest"]["path"])
    if manifest["resources"][0]["evidence_class"] not in ALLOWED_AUTHORITY_CLASSES:
        return _refusal("AUTHORITY_CLASS_EXPANSION")
    return {
        "candidate_sha256": file_sha256(candidate_path),
        "decision": ELIGIBLE,
        "permit_state": "PERMIT_MAY_BE_ISSUED",
        "standing_authorization_sha256": file_sha256(standing_authorization_path),
        "state_before_sha256": file_sha256(state_path),
    }


def build_permit(*, candidate_path: Path, state_path: Path,
                 standing_authorization_path: Path, issued_at_utc: str,
                 current_branch: str = AUTONOMY_BRANCH) -> dict[str, object]:
    evaluation = evaluate_policy(candidate_path=candidate_path, state_path=state_path,
                                 standing_authorization_path=standing_authorization_path,
                                 current_branch=current_branch)
    if evaluation["decision"] != ELIGIBLE:
        raise AutonomyError(str(evaluation["decision"]))
    _utc(issued_at_utc)
    candidate = validate_candidate_structure(candidate_path)
    state = validate_state(state_path)
    authorization = validate_standing_authorization(standing_authorization_path)
    candidate_sha = file_sha256(candidate_path)
    return sealed({
        "authorization_basis": "STANDING_AUTONOMY_MANDATE_001",
        "body_budget_reserved": candidate["network_caps"]["application_body_bytes"],
        "candidate_path": str(Path(candidate_path).resolve().relative_to(PROJECT)),
        "candidate_sha256": candidate_sha,
        "command_argv_sha256": candidate["command_argv_sha256"],
        "issued_at_utc": issued_at_utc,
        "mandate_sha256": file_sha256(MANDATE_PATH),
        "network_budget_reserved": candidate["network_caps"]["requests"],
        "permit_id": f"OC3-AUTONOMOUS-PERMIT-{state['sequence'] + 1:06d}-{candidate_sha[:12]}",
        "permit_type": "AUTONOMOUS_EXECUTION_PERMIT",
        "resource_manifest_sha256": candidate["resource_manifest"]["sha256"],
        "resume": False,
        "retries_reserved": candidate["network_caps"]["retries"],
        "schema_version": "OC3_AUTONOMOUS_EXECUTION_PERMIT_001",
        "scientific_firewall": candidate["scientific_firewall"],
        "scope": candidate["scope"],
        "sequence": state["sequence"],
        "stage_id": candidate["stage_id"],
        "standing_authorization_sha256": file_sha256(standing_authorization_path),
        "state_before_sha256": file_sha256(state_path),
    })


def validate_permit(permit_path: Path, *, candidate_path: Path, state_path: Path,
                    standing_authorization_path: Path, consumption_directory: Path) -> dict[str, object]:
    permit = _load_sealed(permit_path, "AUTONOMOUS_PERMIT_INVALID")
    candidate = validate_candidate_structure(candidate_path)
    state = validate_state(state_path)
    validate_standing_authorization(standing_authorization_path)
    if state.get("active") is not True or state.get("state") != STATE_ACTIVE:
        raise AutonomyError(MANDATE_NOT_ACTIVE)
    required = {"authorization_basis", "body_budget_reserved", "candidate_path", "candidate_sha256",
                "command_argv_sha256", "issued_at_utc", "mandate_sha256", "network_budget_reserved",
                "permit_id", "permit_type", "resource_manifest_sha256", "resume", "retries_reserved",
                "schema_version", "scientific_firewall", "scope", "sealed", "sequence", "stage_id",
                "standing_authorization_sha256", "state_before_sha256"}
    if (set(permit) != required or permit.get("permit_type") != "AUTONOMOUS_EXECUTION_PERMIT" or
            permit.get("authorization_basis") != "STANDING_AUTONOMY_MANDATE_001" or
            permit.get("mandate_sha256") != file_sha256(MANDATE_PATH) or
            permit.get("standing_authorization_sha256") != file_sha256(standing_authorization_path) or
            permit.get("state_before_sha256") != file_sha256(state_path) or
            permit.get("sequence") != state["sequence"] or permit.get("candidate_sha256") != file_sha256(candidate_path) or
            permit.get("candidate_path") != str(Path(candidate_path).resolve().relative_to(PROJECT)) or
            permit.get("command_argv_sha256") != candidate["command_argv_sha256"] or
            permit.get("resource_manifest_sha256") != candidate["resource_manifest"]["sha256"] or
            permit.get("resume") is not False or permit.get("network_budget_reserved") != 1 or
            permit.get("body_budget_reserved") != 0 or permit.get("retries_reserved") != 0 or
            permit.get("scientific_firewall") != {key: 0 for key in FIREWALL_KEYS}):
        raise AutonomyError("AUTONOMOUS_PERMIT_BINDING_MISMATCH")
    _utc(permit.get("issued_at_utc"))
    marker = Path(consumption_directory) / f"{file_sha256(permit_path)}.json"
    if marker.exists():
        raise AutonomyError("AUTONOMOUS_PERMIT_ALREADY_CONSUMED")
    return permit


def audit_compact_paths(paths: list[Path], *, project: Path = PROJECT) -> dict[str, object]:
    """Fail closed if a proposed Git commit contains non-compact or sensitive material."""
    project = Path(project).resolve()
    total = 0
    largest = 0
    normalized: list[str] = []
    for item in paths:
        path = Path(item)
        absolute = path.resolve() if path.is_absolute() else (project / path).resolve()
        try:
            relative = absolute.relative_to(project).as_posix()
        except ValueError as exc:
            raise AutonomyError("GIT_PATH_OUTSIDE_PROJECT") from exc
        lowered = relative.lower()
        if any(lowered.startswith(prefix.lower()) for prefix in RUNTIME_TREE_PREFIXES):
            raise AutonomyError("GIT_RUNTIME_EVIDENCE_FORBIDDEN")
        if any(lowered.endswith(suffix) for suffix in FORBIDDEN_GIT_SUFFIXES):
            raise AutonomyError("GIT_SCIENTIFIC_OR_ARCHIVE_BODY_FORBIDDEN")
        basename = absolute.name.lower()
        if basename == ".env" or any(part in basename for part in SECRET_NAME_PARTS):
            raise AutonomyError("GIT_CREDENTIAL_PATH_FORBIDDEN")
        if absolute.is_symlink() or not absolute.is_file():
            raise AutonomyError("GIT_NONREGULAR_PATH_FORBIDDEN")
        size = absolute.stat().st_size
        if size > COMPACT_ARTIFACT_MAX_BYTES:
            raise AutonomyError("GIT_COMPACT_ARTIFACT_SIZE_EXCEEDED")
        payload = absolute.read_bytes()
        if any(pattern.search(payload) for pattern in SECRET_CONTENT_PATTERNS):
            raise AutonomyError("GIT_SECRET_CONTENT_FORBIDDEN")
        total += size
        largest = max(largest, size)
        normalized.append(relative)
    return {
        "file_count": len(normalized),
        "files": sorted(normalized),
        "largest_file_bytes": largest,
        "network_requests": 0,
        "per_file_limit_bytes": COMPACT_ARTIFACT_MAX_BYTES,
        "state": "GIT_STAGED_SIZE_FIREWALL_PASS",
        "total_bytes": total,
    }


def audit_staged_compact_artifacts(*, project: Path = PROJECT) -> dict[str, object]:
    """Read the Git index and apply the compact-control-plane firewall."""
    project = Path(project).resolve()
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
        cwd=project, check=True, capture_output=True,
    )
    names = [name.decode("utf-8") for name in result.stdout.split(b"\0") if name]
    if not names:
        raise AutonomyError("GIT_NO_STAGED_ARTIFACTS")
    return audit_compact_paths([Path(name) for name in names], project=project)


def consume_permit(permit_path: Path, *, candidate_path: Path, state_path: Path,
                   standing_authorization_path: Path, consumption_directory: Path,
                   consumed_at_utc: str) -> Path:
    permit = validate_permit(permit_path, candidate_path=candidate_path, state_path=state_path,
                             standing_authorization_path=standing_authorization_path,
                             consumption_directory=consumption_directory)
    _utc(consumed_at_utc)
    marker = Path(consumption_directory) / f"{file_sha256(permit_path)}.json"
    write_json_immutable(marker, sealed({
        "consumed_at_utc": consumed_at_utc,
        "permit_id": permit["permit_id"],
        "permit_sha256": file_sha256(permit_path),
        "state_before_sha256": permit["state_before_sha256"],
        "state": "PERMIT_CONSUMPTION_INTENT_RECORDED",
    }))
    return marker


def atomic_replace_state(path: Path, value: dict[str, object]) -> None:
    path = Path(path)
    data = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    if temporary.exists():
        raise AutonomyError("AUTONOMY_STATE_TEMP_CONFLICT")
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def transition_state(*, state_path: Path, candidate_path: Path, permit_path: Path,
                     terminal_sha256: str, terminal_state: str, request_delta: int,
                     body_delta: int, ledger_directory: Path, transitioned_at_utc: str,
                     reason: str) -> dict[str, object]:
    state = validate_state(state_path)
    permit = _load_sealed(permit_path, "AUTONOMOUS_PERMIT_INVALID")
    _require_sha(terminal_sha256, "AUTONOMY_TERMINAL_SHA_INVALID")
    _utc(transitioned_at_utc)
    if permit.get("state_before_sha256") != file_sha256(state_path):
        raise AutonomyError("PERMIT_STATE_MISMATCH")
    if request_delta < 0 or body_delta < 0 or request_delta > state["requests_remaining"] or body_delta > state["body_budget_remaining"]:
        raise AutonomyError("AUTONOMY_TRANSITION_BUDGET_INVALID")
    previous_sha = file_sha256(state_path)
    body = {key: item for key, item in state.items() if key != "sealed"}
    body["sequence"] = state["sequence"] + 1
    body["requests_remaining"] = state["requests_remaining"] - request_delta
    body["body_budget_remaining"] = state["body_budget_remaining"] - body_delta
    body["last_completed_stage"] = permit["stage_id"]
    body["current_stage"] = "AUTONOMOUS_POLICY_EVALUATION"
    body["registered_pending_action"] = None
    new_state = sealed(body)
    new_sha = sha256_bytes(canonical(new_state) + b"\n")
    ledger_directory = Path(ledger_directory)
    snapshot = ledger_directory / "STATE_SNAPSHOTS" / f"{state['sequence']:06d}_{previous_sha}.json"
    write_json_immutable(snapshot, state)
    transition = sealed({
        "action_stage": permit["stage_id"], "body_budget_delta": body_delta,
        "candidate_sha256": file_sha256(candidate_path), "new_state_sha256": new_sha,
        "permit_sha256": file_sha256(permit_path), "previous_state_sha256": previous_sha,
        "reason": reason, "request_budget_delta": request_delta,
        "sequence": new_state["sequence"], "terminal_sha256": terminal_sha256,
        "terminal_state": terminal_state, "transitioned_at_utc": transitioned_at_utc,
    })
    write_json_immutable(ledger_directory / f"{new_state['sequence']:06d}_TRANSITION.json", transition)
    atomic_replace_state(state_path, new_state)
    return new_state


def compact_status(state_path: Path = STATE_PATH) -> dict[str, object]:
    state = validate_state(state_path)
    return {"active": state["active"], "mission_id": state["mission_id"],
            "permit_state": MANDATE_NOT_ACTIVE if not state["active"] else "ACTIVE_POLICY_EVALUATION",
            "requests_remaining": state["requests_remaining"], "sequence": state["sequence"],
            "state": state["state"]}
