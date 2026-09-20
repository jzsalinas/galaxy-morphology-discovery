"""Bounded METADATA_BOOTSTRAP_ONLY infrastructure.

Imports are offline and side-effect free.  Generic provider production decode
remains disabled; this module owns a separately gated selective bootstrap path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import struct
import time
from types import MappingProxyType
from typing import Callable, Iterable, Iterator, Mapping, Protocol

from .core import canonical, file_hash, hash_object, implementation_hash
from .metadata_value_semantics import (
    AcquisitionBoundLocalSha256, EXPECTED_PATCH_REPRESENTATION,
    LocallyComputedFullFileSha256, PatchRepresentationIdentity,
    ValidatedBrickname, validate_brickname, validate_patch_representation,
    validate_provider_full_file_integrity,
)
from .provider_physical_contracts import (
    ACTIVATION_STATES, PHYSICAL_CONTRACT_HASHES, PRODUCTION_PHYSICAL_CONTRACTS,
    FrozenPhysicalContract, PhysicalRole, validate_fits_structure,
)
from .provider_schema import (
    FIELD_BY_ID, GRZ_PREDICATE_VERSION, REGIONAL_LOGICAL_FIELDS,
    ROOT_LOGICAL_FIELDS, FieldClass, FieldId, grz_median_present_v1,
)


BASE_SPEC_SHA256 = "e42ecef50f2a4dd01dbd2d1c8acbcb24e48f30d4692d3bae19c73011fa265dbd"
CLARIFICATION_001_SHA256 = "97c42b873b2700ea2155d9107217e296db441d98a24159efe173732dd4bcca4d"
VALUE_SEMANTICS_SPEC_SHA256 = "c72f2ff7d3032b1ed38a22cc7f002781e3e1266c8b9aa45c2af08822164d6348"
VALUE_SEMANTICS_REPORT_SHA256 = "bb84fd3992d9f2a52572bea1676234d188553078cade1229be9fedeada5d07e3"
PHYSICAL_CONTRACT_DOCUMENT_SHA256 = "bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b"
AMENDMENT_004_SHA256 = "842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48"
POST_PROBE_001_SHA256 = "930909ebdfffff58bc0c88cbbab9c619128cb4ab7adb8df9ec6a88e82324e155"
PRE_METADATA_BOOTSTRAP_INFRASTRUCTURE = "f3f64a05c581e2c74d2cb80c2a2e499ab7c76cbd8eba7ad7f9e5f40a49e48581"
PRE_METADATA_BOOTSTRAP_GATE_ACTIVATION = "084706171e4b74a13a8d2ed57ee5d61b73953d746e6aab23081ef77d78673407"
ENVIRONMENT_FINGERPRINT = "b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf"
EXECUTION_PLAN_SHA256 = "0e246d5fce5d71c2aa109cba913f1eb9bd397259e492e279870c6d4ccf163b20"
PLAN_POST_ACTIVATION_REVIEW_SHA256 = "a232a58f91705215d5322945460549b7b53789bf630503d505552f8f5fb460a0"
RIGHTS_REVIEW_SHA256 = "81dc0a0ec485b7f8d9007781e9845735ec057483b45421442d112c3ad5e38d2e"
CANDIDATE_SPEC_SHA256 = "b340a3d4a9123da0eb5cd54426eca2d6aced8089fb90f905b91f966852a250fa"
CANDIDATE_BINDING_AMENDMENT_SHA256 = "dc457220b80cf3e061224fcdeaf720a0be1b6fce8f1dff72c4ec247665a6712c"
CANONICAL_PROJECT_DIRECTORY = "/home/jzsalinas/Documents/galaxy-morphology-discovery"
CANONICAL_SCRIPT_RELATIVE_PATH = "oc3/oc3_metadata_bootstrap.py"
AUTHORIZATION_CANDIDATE_RELATIVE_PATH = "oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE_001.json"
FINAL_AUTHORIZATION_RELATIVE_PATH = "oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_001.json"
CANDIDATE_TYPE = "METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE"
CANDIDATE_STATE = "PENDING_HUMAN_REVIEW"
VALID_CANDIDATE_STATE = "AUTHORIZATION_CANDIDATE_VALID_FOR_HUMAN_REVIEW"
RIGHTS_BINDING_TYPE = "METADATA_BOOTSTRAP_RIGHTS_BINDING"
FIRST_AUTHORIZATION_TYPE = "METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION"
RESUME_AUTHORIZATION_TYPE = "METADATA_BOOTSTRAP_RESUME_AUTHORIZATION"
FIRST_EXECUTION_MODE = "FIRST_RUN_NETWORK"
RESUME_EXECUTION_MODE = "NETWORK_RESUME"
CANONICALIZATION_VERSION = "CANONICAL_JSON_SORTED_KEYS_COMPACT_UTF8_LF_V1"

AUTHORITY_BINDINGS = MappingProxyType({
    "OC3_METADATA_BOOTSTRAP_EXECUTION_PLAN_001.md": EXECUTION_PLAN_SHA256,
    "OC3_METADATA_BOOTSTRAP_EXECUTION_PLAN_001_POST_ACTIVATION_REVIEW.md": PLAN_POST_ACTIVATION_REVIEW_SHA256,
    "OC3_METADATA_BOOTSTRAP_RIGHTS_REVIEW_001.md": RIGHTS_REVIEW_SHA256,
    "OC3_METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE_SPEC.md": CANDIDATE_SPEC_SHA256,
    "OC3_METADATA_BOOTSTRAP_FINAL_AUTHORIZATION_CANDIDATE_BINDING_AMENDMENT_001.md": CANDIDATE_BINDING_AMENDMENT_SHA256,
    "OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC.md": BASE_SPEC_SHA256,
    "OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC_CLARIFICATION_001.md": CLARIFICATION_001_SHA256,
    "OC3_METADATA_VALUE_SEMANTICS_AND_INTEGRITY_SPEC.md": VALUE_SEMANTICS_SPEC_SHA256,
    "OC3_METADATA_VALUE_SEMANTICS_IMPLEMENTATION_REPORT.md": VALUE_SEMANTICS_REPORT_SHA256,
    "OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md": PHYSICAL_CONTRACT_DOCUMENT_SHA256,
    "OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md": AMENDMENT_004_SHA256,
    "OC3_POST_PROBE_001_REGRESSION_STATE_CLARIFICATION_001.md": POST_PROBE_001_SHA256,
})

BOOTSTRAP_SCOPE = "METADATA_BOOTSTRAP_ONLY"
ATTEMPT_ID = "OC3-METADATA-BOOTSTRAP-001"
ATTEMPT_RELATIVE_DIRECTORY = f"oc3/metadata_bootstrap/{ATTEMPT_ID}"
PATCH_MODEL = "MODEL_B_TWO_STAGE"
BOOTSTRAP_ALLOWED_SELECTIVE_DECODE = True
PRODUCTION_PROVIDER_DECODE_ENABLED = False
EXPECTED_AGGREGATE_BYTES = 89_461_646


class BootstrapError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MetadataResource:
    role: PhysicalRole
    url: str
    expected_length: int
    raw_relative_path: str
    compression: str
    expected_etag: str | None = None
    expected_last_modified: str | None = None

    def __post_init__(self) -> None:
        if (not self.url.startswith("https://") or "?" in self.url or "#" in self.url or
                type(self.expected_length) is not int or self.expected_length <= 0 or
                self.compression not in ("gzip", "identity")):
            raise BootstrapError("METADATA_RESOURCE_IDENTITY_INVALID")


RESOURCES = MappingProxyType({resource.role: resource for resource in (
    MetadataResource(PhysicalRole.ROOT_SUMMARY,
        "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz",
        13_147_987, "RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz", "gzip"),
    MetadataResource(PhysicalRole.NORTH_SUMMARY,
        "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz",
        20_882_100, "RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz", "gzip"),
    MetadataResource(PhysicalRole.SOUTH_SUMMARY,
        "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz",
        55_399_879, "RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz", "gzip"),
    MetadataResource(PhysicalRole.SOUTH_PATCH_LIST,
        "https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits",
        31_680, "RAW_IMMUTABLE/SOUTH_PATCH_LIST/dr9-south-patched-bricks.fits", "identity",
        '"5ffdf047-7bc0"', "Tue, 12 Jan 2021 18:53:59 GMT"),
)})
RESOURCE_ORDER = tuple(RESOURCES)


@dataclass(frozen=True)
class ResourceCaps:
    version: str = "METADATA_BOOTSTRAP_ONLY_RESOURCE_CAPS_V1"
    requests: int = 12
    concurrency: int = 1
    retry_additional_per_exact_identity: int = 1
    http_body_bytes: int = 134_217_728
    single_resource_body_bytes: int = 67_108_864
    disk_bytes: int = 268_435_456
    io_bytes: int = 536_870_912
    ram_bytes: int = 1_073_741_824
    compute_seconds: int = 300
    wall_seconds: int = 900
    threads: int = 1
    gpu: int = 0
    timeout_seconds: int = 30
    retry_backoff_seconds: int = 2
    retry_after_max_seconds: int = 60


RESOURCE_CAPS = ResourceCaps()


FINAL_EVIDENCE_ARTIFACTS = (
    "BOOTSTRAP_AUTHORIZATION_BINDING.json",
    "BOOTSTRAP_TRANSPORT_EVIDENCE.json",
    "BOOTSTRAP_RAW_FILE_MANIFEST.json",
    "BOOTSTRAP_INTEGRITY_EVIDENCE.json",
    "BOOTSTRAP_PHYSICAL_CONTRACT_EVIDENCE.json",
    "BOOTSTRAP_SEMANTIC_SUMMARY.json",
    "PATCH_ACQUISITION_BOUND_EVIDENCE.json",
    "BOOTSTRAP_EVENTS.json",
    "BOOTSTRAP_TERMINAL.json",
    "BOOTSTRAP_LEDGER.sqlite",
    "BOOTSTRAP_RUN.log",
)

TERMINAL_PRECEDENCE = (
    "METADATA_ROW_OBSERVATION_INTEGRITY_FAILURE",
    "METADATA_FORBIDDEN_FIELD_BOUNDARY_FAILURE",
    "METADATA_BOOTSTRAP_AUTHORITY_FAILURE",
    "METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",
    "METADATA_LOCAL_STATE_CONFLICT",
    "METADATA_RESOURCE_LIMIT_STOP",
    "PATCH_LIST_REPRESENTATION_DRIFT_STOP",
    "METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP",
    "METADATA_TRANSPORT_INTEGRITY_FAILURE",
    "METADATA_FULL_FILE_INTEGRITY_FAILURE",
    "METADATA_PHYSICAL_CONTRACT_FAILURE",
    "METADATA_VALUE_SEMANTICS_FAILURE",
    "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED",
    "METADATA_BOOTSTRAP_RESOLVED",
)


def terminal_outcome(events: Iterable[str], *, model: str = PATCH_MODEL) -> str:
    seen = set(events)
    if model == PATCH_MODEL:
        seen.discard("METADATA_BOOTSTRAP_RESOLVED")
    for outcome in TERMINAL_PRECEDENCE:
        if outcome in seen:
            return outcome
    raise BootstrapError("METADATA_TERMINAL_OUTCOME_MISSING")


def command_sha256(argv: Iterable[str]) -> str:
    values = tuple(argv)
    if not values or any(type(value) is not str or not value for value in values):
        raise BootstrapError("METADATA_COMMAND_INVALID")
    return hashlib.sha256(canonical(list(values))).hexdigest()


def _sha256_text(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def resource_binding_values() -> list[dict[str, object]]:
    return [
        {
            "accept_encoding": "identity",
            "allowed_methods": ["HEAD", "GET"],
            "compression": resource.compression,
            "expected_etag": resource.expected_etag,
            "expected_length": resource.expected_length,
            "expected_last_modified": resource.expected_last_modified,
            "expected_provider_full_file_sha256":
                PRODUCTION_PHYSICAL_CONTRACTS[role].expected_provider_full_file_sha256,
            "provider_checksum_status": PRODUCTION_PHYSICAL_CONTRACTS[role].checksum_status,
            "range_allowed": False,
            "redirects_allowed": False,
            "role": role.value,
            "url": resource.url,
        }
        for role, resource in RESOURCES.items()
    ]


def resource_cap_values() -> dict[str, object]:
    return dict(vars(RESOURCE_CAPS))


NEGATIVE_CAPABILITIES = MappingProxyType({
    "automatic_resume": False,
    "background_execution": False,
    "forbidden_field_observation": False,
    "mirror_or_fallback": False,
    "oc3_start": False,
    "patch_row_decode": False,
    "range_requests": False,
    "redirects": False,
    "release_substitution": False,
    "redistribution": False,
    "row_persistence": False,
    "selection": False,
})


RIGHTS_FIELDS = frozenset({
    "binding_type", "schema_version", "canonicalization", "attempt_id", "scope",
    "local_scientific_acquisition", "local_preservation", "redistribution",
    "FITS_OR_DERIVED_REDISTRIBUTION", "execution_plan_sha256",
    "base_spec_sha256", "clarification_sha256", "implementation_aggregate",
    "environment_fingerprint", "resources", "reviewed_evidence", "reviewed",
    "synthetic_only",
})
EVIDENCE_REFERENCE_FIELDS = frozenset({"path", "sha256"})


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _load_canonical_json(path: Path, error_code: str) -> tuple[dict, str]:
    try:
        raw = Path(path).read_bytes()
        if len(raw) > 1024 * 1024:
            raise ValueError("governance input too large")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
        if not isinstance(value, dict) or raw != canonical(value) + b"\n":
            raise ValueError("non-canonical JSON")
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise BootstrapError(error_code) from exc
    return value, hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class RightsBinding:
    value: MappingProxyType
    sha256: str
    synthetic_only: bool

    def __post_init__(self) -> None:
        if (not isinstance(self.value, MappingProxyType) or
                self.sha256 != hashlib.sha256(canonical(dict(self.value)) + b"\n").hexdigest()):
            raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")

    def object(self) -> dict:
        return dict(self.value)

    @property
    def redistribution(self) -> bool:
        return self.value["redistribution"]


def load_rights_binding(path: Path) -> RightsBinding:
    value, source_sha256 = _load_canonical_json(path, "METADATA_RIGHTS_BINDING_INVALID")
    synthetic = value.get("synthetic_only")
    if type(synthetic) is not bool:
        raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")
    return RightsBinding(MappingProxyType(value), source_sha256, synthetic)


def validate_rights(binding: RightsBinding, *, implementation_aggregate: str,
                    allow_synthetic: bool, project: Path | None = None) -> RightsBinding:
    if not isinstance(binding, RightsBinding):
        raise BootstrapError("METADATA_RIGHTS_BINDING_REQUIRED")
    value = binding.value
    if set(value) != RIGHTS_FIELDS:
        raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")
    if (
        value["binding_type"] != RIGHTS_BINDING_TYPE or
        value["schema_version"] != 1 or
        value["canonicalization"] != CANONICALIZATION_VERSION or
        value["attempt_id"] != ATTEMPT_ID or
        value["scope"] != BOOTSTRAP_SCOPE or
        value["local_scientific_acquisition"] != "ALLOWED_FOR_THIS_PROTOCOL" or
        value["local_preservation"] != "ALLOWED_FOR_THIS_PROTOCOL" or
        value["redistribution"] is not False or
        value["FITS_OR_DERIVED_REDISTRIBUTION"] != "DISABLED_UNRESOLVED" or
        value["execution_plan_sha256"] != EXECUTION_PLAN_SHA256 or
        value["base_spec_sha256"] != BASE_SPEC_SHA256 or
        value["clarification_sha256"] != CLARIFICATION_001_SHA256 or
        value["implementation_aggregate"] != implementation_aggregate or
        value["environment_fingerprint"] != ENVIRONMENT_FINGERPRINT or
        value["resources"] != resource_binding_values() or
        value["reviewed"] is not True or
        type(value["synthetic_only"]) is not bool or
        not _sha256_text(binding.sha256)
    ):
        raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")
    if binding.synthetic_only and not allow_synthetic:
        raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")
    evidence = value["reviewed_evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")
    project = Path(project or CANONICAL_PROJECT_DIRECTORY).resolve()
    for reference in evidence:
        if not isinstance(reference, dict) or set(reference) != EVIDENCE_REFERENCE_FIELDS:
            raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")
        relative = reference["path"]
        expected_sha = reference["sha256"]
        if not isinstance(relative, str) or not relative or not _sha256_text(expected_sha):
            raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")
        candidate = (project / relative).resolve()
        if not candidate.is_relative_to(project) or not candidate.is_file() or file_hash(candidate) != expected_sha:
            raise BootstrapError("METADATA_RIGHTS_BINDING_INVALID")
    return binding


FINAL_AUTH_COMMON_FIELDS = frozenset({
    "authorization_type", "authorization_state", "schema_version", "canonicalization",
    "authorized", "authorized_by", "authorized_at_utc", "scope", "attempt_id",
    "attempt_directory", "execution_mode", "execution_plan_sha256",
    "base_spec_sha256", "clarification_sha256", "implementation_aggregate",
    "environment_fingerprint", "patch_model", "resources", "resource_caps",
    "command_argv", "command_sha256", "rights_binding_sha256",
    "negative_capabilities", "synthetic_only",
})
FIRST_AUTH_FIELDS = FINAL_AUTH_COMMON_FIELDS | frozenset({
    "authorization_candidate_path", "authorization_candidate_sha256",
})
RESUME_AUTH_FIELDS = FINAL_AUTH_COMMON_FIELDS | frozenset({
    "first_run_authorization_sha256", "ledger_identity", "ledger_watermark",
    "consumed_counters", "remaining_caps", "completed_raw_resources",
    "pending_resources", "existing_staging_state",
})
CANDIDATE_FIELDS = frozenset({
    "schema_version", "canonicalization", "candidate_type", "candidate_state",
    "attempt_id", "scope", "execution_mode", "patch_model",
    "execution_plan_sha256", "plan_post_activation_review_sha256",
    "rights_binding_path", "rights_binding_sha256", "rights_review_sha256",
    "base_spec_sha256", "clarification_sha256", "implementation_aggregate",
    "environment_fingerprint", "resources", "resource_caps", "command_vector",
    "command_sha256", "negative_capabilities", "final_authorization_path",
    "candidate_created_at_utc",
})


@dataclass(frozen=True)
class AuthorizationCandidate:
    value: MappingProxyType
    sha256: str
    validation_state: str = VALID_CANDIDATE_STATE

    def __post_init__(self) -> None:
        if (not isinstance(self.value, MappingProxyType) or
                self.sha256 != hashlib.sha256(canonical(dict(self.value)) + b"\n").hexdigest() or
                self.validation_state != VALID_CANDIDATE_STATE):
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")


def load_authorization_candidate(path: Path) -> AuthorizationCandidate:
    value, source_sha256 = _load_canonical_json(
        Path(path), "METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    return AuthorizationCandidate(MappingProxyType(value), source_sha256)


def _valid_utc(value: object, *, require_z: bool = False) -> bool:
    if not isinstance(value, str) or not value or (require_z and not value.endswith("Z")):
        return False
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (timestamp.tzinfo is not None and
            timestamp.utcoffset() == timezone.utc.utcoffset(timestamp))


def validate_authorization_candidate(
        candidate: AuthorizationCandidate, *, argv: Iterable[str],
        implementation_aggregate: str, rights_sha256: str,
        authorization_path: Path, rights_path: Path,
        project: Path | None = None, allow_synthetic_paths: bool = False,
) -> AuthorizationCandidate:
    """Validate a review candidate without creating any transport capability."""
    if not isinstance(candidate, AuthorizationCandidate):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    value = candidate.value
    if set(value) != CANDIDATE_FIELDS:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    project = Path(project or CANONICAL_PROJECT_DIRECTORY).resolve()
    authorization_path = Path(authorization_path)
    rights_path = Path(rights_path)
    argv = tuple(argv)
    expected_final = (project / FINAL_AUTHORIZATION_RELATIVE_PATH).resolve()
    if not allow_synthetic_paths:
        if (authorization_path.resolve() != expected_final or
                str(authorization_path) != str(expected_final)):
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    if (
        value["schema_version"] != 1 or type(value["schema_version"]) is not int or
        value["canonicalization"] != CANONICALIZATION_VERSION or
        value["candidate_type"] != CANDIDATE_TYPE or
        value["candidate_state"] != CANDIDATE_STATE or
        value["attempt_id"] != ATTEMPT_ID or
        value["scope"] != BOOTSTRAP_SCOPE or
        value["execution_mode"] != FIRST_EXECUTION_MODE or
        value["patch_model"] != PATCH_MODEL or
        value["execution_plan_sha256"] != EXECUTION_PLAN_SHA256 or
        value["plan_post_activation_review_sha256"] != PLAN_POST_ACTIVATION_REVIEW_SHA256 or
        value["rights_review_sha256"] != RIGHTS_REVIEW_SHA256 or
        value["base_spec_sha256"] != BASE_SPEC_SHA256 or
        value["clarification_sha256"] != CLARIFICATION_001_SHA256 or
        value["implementation_aggregate"] != implementation_aggregate or
        value["environment_fingerprint"] != ENVIRONMENT_FINGERPRINT or
        value["resources"] != resource_binding_values() or
        value["resource_caps"] != resource_cap_values() or
        value["negative_capabilities"] != dict(NEGATIVE_CAPABILITIES) or
        value["rights_binding_path"] != str(rights_path) or
        value["rights_binding_sha256"] != rights_sha256 or
        value["final_authorization_path"] != str(authorization_path) or
        tuple(value["command_vector"]) != argv or
        value["command_sha256"] != command_sha256(argv) or
        not _valid_utc(value["candidate_created_at_utc"], require_z=True)
    ):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    if (not allow_synthetic_paths and
            (not rights_path.is_absolute() or
             not rights_path.resolve().is_relative_to(project))):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    for relative, expected in (
        ("OC3_METADATA_BOOTSTRAP_EXECUTION_PLAN_001_POST_ACTIVATION_REVIEW.md",
         PLAN_POST_ACTIVATION_REVIEW_SHA256),
        ("OC3_METADATA_BOOTSTRAP_RIGHTS_REVIEW_001.md", RIGHTS_REVIEW_SHA256),
    ):
        path = project / relative
        if not path.is_file() or file_hash(path) != expected:
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    return candidate


@dataclass(frozen=True)
class ValidatedAuthorization:
    kind: str
    value: MappingProxyType
    sha256: str
    synthetic_only: bool


def validate_authorization(value: object, *, argv: Iterable[str], resume: bool,
                           implementation_aggregate: str, rights_sha256: str,
                           require_authorized: bool = True,
                           allow_synthetic: bool = False,
                           candidate: AuthorizationCandidate | None = None,
                           candidate_path: Path | None = None) -> ValidatedAuthorization:
    if not isinstance(value, dict):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    expected_fields = RESUME_AUTH_FIELDS if resume else FIRST_AUTH_FIELDS
    if set(value) != expected_fields:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    argv = tuple(argv)
    expected_kind = RESUME_AUTHORIZATION_TYPE if resume else FIRST_AUTHORIZATION_TYPE
    expected_mode = RESUME_EXECUTION_MODE if resume else FIRST_EXECUTION_MODE
    expected_schema = 1 if resume else 2
    if (value["authorization_type"] != expected_kind or
            value["authorization_state"] != "FINAL_HUMAN_AUTHORIZATION" or
            value["schema_version"] != expected_schema or type(value["schema_version"]) is not int or
            value["canonicalization"] != CANONICALIZATION_VERSION or
            value["scope"] != BOOTSTRAP_SCOPE or
            value["attempt_id"] != ATTEMPT_ID or
            value["attempt_directory"] != ATTEMPT_RELATIVE_DIRECTORY or
            value["execution_mode"] != expected_mode or
            value["execution_plan_sha256"] != EXECUTION_PLAN_SHA256 or
            value["base_spec_sha256"] != BASE_SPEC_SHA256 or
            value["clarification_sha256"] != CLARIFICATION_001_SHA256 or
            value["implementation_aggregate"] != implementation_aggregate or
            value["environment_fingerprint"] != ENVIRONMENT_FINGERPRINT or
            value["patch_model"] != PATCH_MODEL or
            value["resources"] != resource_binding_values() or
            value["resource_caps"] != resource_cap_values() or
            value["negative_capabilities"] != dict(NEGATIVE_CAPABILITIES) or
            tuple(value["command_argv"]) != argv or
            value["command_sha256"] != command_sha256(argv) or
            value["rights_binding_sha256"] != rights_sha256 or
            type(value["authorized"]) is not bool or
            type(value["synthetic_only"]) is not bool):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    if (not isinstance(value["authorized_by"], str) or not value["authorized_by"].strip() or
            not _valid_utc(value["authorized_at_utc"])):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    has_resume = "--resume" in argv
    if has_resume != resume:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    if require_authorized and value["authorized"] is not True:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    if value["synthetic_only"] and not allow_synthetic:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    if not resume:
        if (not isinstance(candidate, AuthorizationCandidate) or candidate_path is None or
                value["authorization_candidate_path"] != str(Path(candidate_path)) or
                value["authorization_candidate_sha256"] != candidate.sha256):
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
        correspondence = {
            "attempt_id": "attempt_id", "scope": "scope",
            "execution_mode": "execution_mode", "patch_model": "patch_model",
            "execution_plan_sha256": "execution_plan_sha256",
            "rights_binding_sha256": "rights_binding_sha256",
            "base_spec_sha256": "base_spec_sha256",
            "clarification_sha256": "clarification_sha256",
            "implementation_aggregate": "implementation_aggregate",
            "environment_fingerprint": "environment_fingerprint",
            "resources": "resources", "resource_caps": "resource_caps",
            "command_vector": "command_argv", "command_sha256": "command_sha256",
            "negative_capabilities": "negative_capabilities",
        }
        if any(candidate.value[source] != value[target]
               for source, target in correspondence.items()):
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    else:
        if (not _sha256_text(value["first_run_authorization_sha256"]) or
                not isinstance(value["ledger_identity"], str) or not value["ledger_identity"] or
                type(value["ledger_watermark"]) is not int or value["ledger_watermark"] < 0 or
                not isinstance(value["consumed_counters"], dict) or
                not isinstance(value["remaining_caps"], dict) or
                not isinstance(value["completed_raw_resources"], list) or
                not isinstance(value["pending_resources"], list) or
                not isinstance(value["existing_staging_state"], list)):
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
        completed = set(value["completed_raw_resources"])
        pending = set(value["pending_resources"])
        roles = {role.value for role in RESOURCE_ORDER}
        if completed & pending or completed | pending != roles:
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    raw = canonical(value) + b"\n"
    validated_kind = "RESUME_NETWORK_AUTHORIZATION" if resume else "FIRST_RUN_NETWORK_AUTHORIZATION"
    return ValidatedAuthorization(validated_kind, MappingProxyType(dict(value)),
                                  hashlib.sha256(raw).hexdigest(), value["synthetic_only"])


@dataclass(frozen=True)
class TransportResponse:
    status: int
    requested_url: str
    final_url: str
    redirect_history: tuple[str, ...]
    headers: Mapping[str, str]
    body_chunks: tuple[bytes, ...] = ()


class BootstrapTransport(Protocol):
    def head(self, resource: MetadataResource) -> TransportResponse: ...
    def get(self, resource: MetadataResource) -> TransportResponse: ...


class OfflineTransport:
    def head(self, resource: MetadataResource) -> TransportResponse:
        raise BootstrapError("METADATA_OFFLINE_NETWORK_FORBIDDEN")
    def get(self, resource: MetadataResource) -> TransportResponse:
        raise BootstrapError("METADATA_OFFLINE_NETWORK_FORBIDDEN")


class SyntheticTransport:
    synthetic_only = True

    def __init__(self, responses: Iterable[TransportResponse]):
        self._responses = iter(tuple(responses))
        self.calls: list[tuple[str, PhysicalRole]] = []

    def _next(self, method: str, resource: MetadataResource) -> TransportResponse:
        self.calls.append((method, resource.role))
        try:
            response = next(self._responses)
        except StopIteration as exc:
            raise BootstrapError("METADATA_SYNTHETIC_RESPONSE_MISSING") from exc
        return response

    def head(self, resource: MetadataResource) -> TransportResponse:
        return self._next("HEAD", resource)

    def get(self, resource: MetadataResource) -> TransportResponse:
        return self._next("GET", resource)


_REAL_TRANSPORT_TOKEN = object()
_ACTIVATION_GATE_TOKEN = object()


class RealHttpTransport:
    """Real HTTP capability; construct only through the fully gated factory."""

    def __init__(self, token: object):
        if token is not _REAL_TRANSPORT_TOKEN:
            raise BootstrapError("METADATA_REAL_TRANSPORT_GATE_REQUIRED")

    @staticmethod
    def _request(resource: MetadataResource, method: str) -> TransportResponse:
        import urllib.request

        class RejectRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")

        opener = urllib.request.build_opener(RejectRedirect)
        request = urllib.request.Request(resource.url, method=method,
                                         headers={"Accept-Encoding": "identity"})
        with opener.open(request, timeout=RESOURCE_CAPS.timeout_seconds) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
            if method == "GET":
                encoding = headers.get("content-encoding")
                length = headers.get("content-length", "")
                if (response.status != 200 or response.geturl() != resource.url or
                        encoding not in (None, "identity") or "content-range" in headers or
                        re.fullmatch(r"[0-9]+", length) is None or
                        int(length) != resource.expected_length):
                    raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")
                received = 0; parts = []
                while received <= resource.expected_length:
                    chunk = response.read(min(1024 * 1024,
                                              resource.expected_length + 1 - received))
                    if not chunk:
                        break
                    parts.append(chunk); received += len(chunk)
                chunks = tuple(parts)
            else:
                chunks = ()
            return TransportResponse(response.status, resource.url, response.geturl(), (), headers, chunks)

    def head(self, resource: MetadataResource) -> TransportResponse:
        return self._request(resource, "HEAD")

    def get(self, resource: MetadataResource) -> TransportResponse:
        return self._request(resource, "GET")


def construct_real_transport(*, execute_network: bool, offline: bool,
                             rights: RightsBinding | None,
                             authorization: ValidatedAuthorization | None,
                             implementation_aggregate: str,
                             gate_token: object | None = None) -> RealHttpTransport:
    if (gate_token is not _ACTIVATION_GATE_TOKEN or offline or not execute_network or
            rights is None or authorization is None):
        raise BootstrapError("METADATA_REAL_TRANSPORT_GATE_REQUIRED")
    validate_rights(rights, implementation_aggregate=implementation_aggregate,
                    allow_synthetic=False, project=Path(CANONICAL_PROJECT_DIRECTORY))
    if authorization.synthetic_only:
        raise BootstrapError("METADATA_REAL_TRANSPORT_GATE_REQUIRED")
    return RealHttpTransport(_REAL_TRANSPORT_TOKEN)


def _validate_command_vector(command: Iterable[str], *, authorization_path: Path,
                             rights_path: Path, resume: bool) -> tuple[str, ...]:
    values = tuple(command)
    script = str((Path(CANONICAL_PROJECT_DIRECTORY) / CANONICAL_SCRIPT_RELATIVE_PATH).resolve())
    expected = (
        script,
        "--execute-network",
        "--authorization", str(Path(authorization_path)),
        "--rights-binding", str(Path(rights_path)),
    ) + (("--resume",) if resume else ())
    if (values != expected or not Path(authorization_path).is_absolute() or
            not Path(rights_path).is_absolute()):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    return values


def _verify_gate_authorities(project: Path, trace: list[str]) -> str:
    project = Path(project).resolve()
    if project != Path(CANONICAL_PROJECT_DIRECTORY).resolve():
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE")
    trace.append("01_project_identity")
    plan = project / "OC3_METADATA_BOOTSTRAP_EXECUTION_PLAN_001.md"
    if not plan.is_file() or file_hash(plan) != EXECUTION_PLAN_SHA256:
        raise BootstrapError("METADATA_BOOTSTRAP_EXECUTION_PLAN_AUTHORITY_FAILURE")
    trace.append("02_execution_plan_authority")
    for name, expected in AUTHORITY_BINDINGS.items():
        path = project / name
        if not path.is_file() or file_hash(path) != expected:
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE")
    trace.append("03_spec_and_clarification")
    aggregate = implementation_hash(project)
    if not _sha256_text(aggregate):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE")
    trace.append("04_implementation_aggregate")
    try:
        environment = json.loads((project / "oc3/environment_setup/ENVIRONMENT.json").read_text())
    except (OSError, ValueError) as exc:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE") from exc
    if environment.get("environment_sha256") != ENVIRONMENT_FINGERPRINT:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE")
    trace.append("05_environment_fingerprint")
    if ATTEMPT_ID != "OC3-METADATA-BOOTSTRAP-001":
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE")
    trace.append("06_attempt_identity")
    return aggregate


def activate_network_transport(*, project: Path, command: Iterable[str],
                               authorization_path: Path | None,
                               rights_path: Path | None, resume: bool,
                               allow_synthetic: bool = False,
                               transport_factory: Callable[..., object] | None = None,
                               gate_trace: list[str] | None = None) -> object:
    """Validate every local authority before creating any network capability.

    ``allow_synthetic`` and ``transport_factory`` exist for the offline regression
    harness only and are not exposed by the CLI.
    """
    trace = gate_trace if gate_trace is not None else []
    project = Path(project).resolve()
    aggregate = _verify_gate_authorities(project, trace)
    attempt = project / ATTEMPT_RELATIVE_DIRECTORY
    if resume:
        if not attempt.is_dir():
            raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT")
    elif attempt.exists():
        raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT")
    trace.append("07_attempt_state")
    if rights_path is None or not Path(rights_path).is_file():
        raise BootstrapError("PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS")
    rights = load_rights_binding(Path(rights_path))
    validate_rights(rights, implementation_aggregate=aggregate,
                    allow_synthetic=allow_synthetic, project=project)
    trace.append("08_rights_binding")
    if authorization_path is None or not Path(authorization_path).is_file():
        raise BootstrapError("PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS")
    authorization_value, _ = _load_canonical_json(
        Path(authorization_path), "METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    if set(authorization_value) != (RESUME_AUTH_FIELDS if resume else FIRST_AUTH_FIELDS):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("09_human_authorization")
    if authorization_value["rights_binding_sha256"] != rights.sha256:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("10_authorization_rights_binding")
    if (rights.value["execution_plan_sha256"] != EXECUTION_PLAN_SHA256 or
            authorization_value["execution_plan_sha256"] != EXECUTION_PLAN_SHA256):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("11_plan_bindings")
    if (rights.value["resources"] != resource_binding_values() or
            authorization_value["resources"] != resource_binding_values() or
            authorization_value["resource_caps"] != resource_cap_values()):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("12_resources_and_caps")
    if authorization_value["patch_model"] != PATCH_MODEL:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("13_patch_model")
    command = _validate_command_vector(command, authorization_path=Path(authorization_path),
                                       rights_path=Path(rights_path), resume=resume)
    if tuple(authorization_value["command_argv"]) != command:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("14_command_vector")
    if authorization_value["command_sha256"] != command_sha256(command):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("15_command_sha256")
    if authorization_value["authorized"] is not True:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("16_authorized_true")
    expected_mode = RESUME_EXECUTION_MODE if resume else FIRST_EXECUTION_MODE
    if authorization_value["execution_mode"] != expected_mode:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("17_execution_mode")
    if (("--resume" in command) is not resume):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("18_resume_mode")
    if authorization_value["negative_capabilities"] != dict(NEGATIVE_CAPABILITIES):
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
    trace.append("19_negative_capabilities")
    candidate = None
    candidate_path = None
    if not resume:
        raw_candidate_path = authorization_value["authorization_candidate_path"]
        if not isinstance(raw_candidate_path, str) or not raw_candidate_path:
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
        candidate_path = Path(raw_candidate_path)
        expected_candidate_path = (project / AUTHORIZATION_CANDIDATE_RELATIVE_PATH).resolve()
        if (not candidate_path.is_absolute() or not candidate_path.is_file() or
                (not allow_synthetic and
                 (str(candidate_path) != str(expected_candidate_path) or
                  candidate_path.resolve() != expected_candidate_path or
                  not candidate_path.resolve().is_relative_to(project)))):
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
        trace.append("20_authorization_candidate_path")
        candidate = load_authorization_candidate(candidate_path)
        if (not _sha256_text(authorization_value["authorization_candidate_sha256"]) or
                authorization_value["authorization_candidate_sha256"] != candidate.sha256):
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE")
        trace.append("21_authorization_candidate_sha256")
        validate_authorization_candidate(
            candidate, argv=command, implementation_aggregate=aggregate,
            rights_sha256=rights.sha256, authorization_path=Path(authorization_path),
            rights_path=Path(rights_path), project=project,
            allow_synthetic_paths=allow_synthetic,
        )
        trace.append("22_authorization_candidate_validation")
    authorization = validate_authorization(
        authorization_value, argv=command, resume=resume,
        implementation_aggregate=aggregate, rights_sha256=rights.sha256,
        require_authorized=True, allow_synthetic=allow_synthetic,
        candidate=candidate, candidate_path=candidate_path,
    )
    if not resume:
        trace.append("23_candidate_final_equivalence")
    factory = transport_factory or construct_real_transport
    result = factory(
        execute_network=True, offline=False, rights=rights,
        authorization=authorization, implementation_aggregate=aggregate,
        gate_token=_ACTIVATION_GATE_TOKEN,
    )
    trace.append("24_real_transport_construction" if not resume else
                 "20_real_transport_construction")
    return result


def _headers(response: TransportResponse) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in response.headers.items()}


@dataclass(frozen=True)
class PretransferEvidence:
    role: PhysicalRole
    requested_url: str
    final_url: str
    content_length: int
    etag: str | None
    last_modified: str | None


def validate_head(resource: MetadataResource, response: TransportResponse) -> PretransferEvidence:
    headers = _headers(response)
    code = ("PATCH_LIST_REPRESENTATION_DRIFT_STOP" if resource.role is PhysicalRole.SOUTH_PATCH_LIST
            else "METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP")
    encoding = headers.get("content-encoding")
    length = headers.get("content-length", "")
    if (response.status != 200 or response.requested_url != resource.url or
            response.final_url != resource.url or response.redirect_history or
            encoding not in (None, "identity") or re.fullmatch(r"[0-9]+", length) is None or
            int(length) != resource.expected_length):
        raise BootstrapError(code)
    if resource.role is PhysicalRole.SOUTH_PATCH_LIST:
        identity = PatchRepresentationIdentity(int(length), headers.get("etag", ""),
            headers.get("last-modified", ""), response.final_url, False)
        try:
            validate_patch_representation(identity)
        except Exception as exc:
            raise BootstrapError(code) from exc
    return PretransferEvidence(resource.role, resource.url, response.final_url,
        int(length), headers.get("etag"), headers.get("last-modified"))


def validate_all_heads(responses: Mapping[PhysicalRole, TransportResponse],
                       resources: Mapping[PhysicalRole, MetadataResource] = RESOURCES
                       ) -> MappingProxyType:
    if set(responses) != set(resources):
        raise BootstrapError("METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP")
    return MappingProxyType({role: validate_head(resources[role], responses[role])
                             for role in resources})


def validate_get_headers(resource: MetadataResource, head: PretransferEvidence,
                         response: TransportResponse) -> None:
    headers = _headers(response)
    encoding = headers.get("content-encoding")
    length = headers.get("content-length", "")
    if (response.status != 200 or response.requested_url != resource.url or
            response.final_url != resource.url or response.redirect_history or
            encoding not in (None, "identity") or "content-range" in headers or
            re.fullmatch(r"[0-9]+", length) is None or
            int(length) != resource.expected_length or head.content_length != resource.expected_length):
        raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")
    if resource.role is PhysicalRole.SOUTH_PATCH_LIST:
        if (headers.get("etag") != head.etag or
                headers.get("last-modified") != head.last_modified):
            raise BootstrapError("PATCH_LIST_REPRESENTATION_DRIFT_STOP")


def validate_complete_body(resource: MetadataResource, response: TransportResponse) -> int:
    """Validate an injected complete-body response without interpreting bytes."""
    total = 0
    for chunk in response.body_chunks:
        if type(chunk) is not bytes:
            raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")
        total += len(chunk)
        if total > resource.expected_length:
            raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")
    if total != resource.expected_length:
        raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")
    return total


def collect_pretransfer_evidence(transport: BootstrapTransport,
                                 ledger: "BootstrapLedger",
                                 resources: Mapping[PhysicalRole, MetadataResource] = RESOURCES
                                 ) -> MappingProxyType:
    """Issue every allowed HEAD and validate the closed set before any GET."""
    responses: dict[PhysicalRole, TransportResponse] = {}
    for ordinal, (role, item) in enumerate(resources.items(), 1):
        request_id = ledger.begin_request("HEAD", item, ordinal=ordinal)
        try:
            responses[role] = transport.head(item)
        except Exception:
            ledger.finish_request(request_id, "FAILED", 0, uncertain=True)
            raise
        ledger.finish_request(request_id, "COMPLETE", 0)
    return validate_all_heads(responses, resources)


def acquire_complete_resource(transport: BootstrapTransport,
                              ledger: "BootstrapLedger",
                              storage: "AttemptStorage",
                              resource: MetadataResource,
                              head: PretransferEvidence, *, ordinal: int,
                              authorization_sha256: str,
                              implementation_aggregate: str,
                              retry_of: str | None = None,
                              timestamp: str | None = None
                              ) -> "BootstrapRawDigest":
    """Acquire one complete body after the four-resource HEAD barrier passed."""
    request_id = ledger.begin_request("GET", resource, ordinal=ordinal, retry_of=retry_of)
    try:
        response = transport.get(resource)
    except Exception:
        ledger.finish_request(request_id, "UNCERTAIN", 0, uncertain=True)
        raise
    actual = sum(len(chunk) for chunk in response.body_chunks if type(chunk) is bytes)
    try:
        validate_get_headers(resource, head, response)
        validate_complete_body(resource, response)
    except Exception:
        ledger.finish_request(request_id, "FAILED", actual)
        raise
    ledger.finish_request(request_id, "COMPLETE", actual)
    staging_id, staging_path, size = storage.write_staging(
        resource, ordinal, response.body_chunks)
    artifact = storage.publish_raw(resource, staging_id, staging_path, size, request_id)
    receipt = {
        "actual_body_bytes": actual, "final_url": response.final_url,
        "headers": dict(sorted(_headers(response).items())), "method": "GET",
        "request_id": request_id, "requested_url": response.requested_url,
        "role": resource.role.value, "status": response.status,
    }
    return derive_raw_digest(
        artifact, resource, authorization_sha256=authorization_sha256,
        implementation_aggregate=implementation_aggregate,
        transport_receipt_sha256=hash_object(receipt), ledger=ledger,
        timestamp=timestamp,
    )


class BootstrapLedger:
    """One SQLite ledger.  It contains counters/evidence, never provider rows."""

    def __init__(self, path: Path, binding: Mapping[str, object], caps: ResourceCaps = RESOURCE_CAPS):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fresh = not self.path.exists()
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS counters(key TEXT PRIMARY KEY,value INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,method TEXT,url TEXT,role TEXT,
          retry_of TEXT,status TEXT,reserved_body INTEGER,actual_body INTEGER);
        CREATE TABLE IF NOT EXISTS staging(id TEXT PRIMARY KEY,role TEXT,path TEXT,status TEXT,bytes INTEGER);
        CREATE TABLE IF NOT EXISTS raw(role TEXT PRIMARY KEY,path TEXT,bytes INTEGER,sha256 TEXT,request_id TEXT);
        CREATE TABLE IF NOT EXISTS events(sequence INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS terminal(outcome TEXT PRIMARY KEY);
        """)
        identity = hash_object(binding)
        if fresh:
            self.db.execute("INSERT INTO config VALUES('binding',?)", (json.dumps(binding, sort_keys=True),))
            self.db.execute("INSERT INTO config VALUES('identity',?)", (identity,))
            for key in ("requests", "body_bytes", "disk_bytes", "io_bytes",
                        "compute_seconds", "wall_seconds", "watermark"):
                self.db.execute("INSERT INTO counters VALUES(?,0)", (key,))
            self.db.commit()
        else:
            old = self.db.execute("SELECT value FROM config WHERE key='identity'").fetchone()
            if not old or old[0] != identity:
                raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT")
        self.identity = identity
        self.caps = caps
        # A process death after reservation is conservatively charged at the
        # full reservation before any resume can issue another request.
        for request_id, reserve in self.db.execute(
                "SELECT id,reserved_body FROM requests WHERE status='RESERVED'").fetchall():
            if self._counter("body_bytes") + int(reserve) > self.caps.http_body_bytes:
                raise BootstrapError("METADATA_RESOURCE_LIMIT_STOP")
            self.db.execute("UPDATE requests SET status='UNCERTAIN',actual_body=? WHERE id=?",
                            (int(reserve), request_id))
            self._add("body_bytes", int(reserve)); self._add("io_bytes", int(reserve))
        self.db.commit()

    def close(self) -> None:
        self.db.commit(); self.db.close()

    def _counter(self, key: str) -> int:
        return int(self.db.execute("SELECT value FROM counters WHERE key=?", (key,)).fetchone()[0])

    @property
    def watermark(self) -> int:
        return self._counter("watermark")

    def _add(self, key: str, amount: int) -> None:
        if type(amount) is not int or amount < 0:
            raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT")
        limit = {
            "body_bytes": self.caps.http_body_bytes,
            "disk_bytes": self.caps.disk_bytes,
            "io_bytes": self.caps.io_bytes,
            "compute_seconds": self.caps.compute_seconds,
            "wall_seconds": self.caps.wall_seconds,
            "requests": self.caps.requests,
        }.get(key)
        if limit is not None and self._counter(key) + amount > limit:
            raise BootstrapError("METADATA_RESOURCE_LIMIT_STOP")
        self.db.execute("UPDATE counters SET value=value+? WHERE key=?", (amount, key))
        self.db.execute("UPDATE counters SET value=value+1 WHERE key='watermark'")

    def counters(self) -> dict[str, int]:
        return {key: int(value) for key, value in self.db.execute("SELECT key,value FROM counters")}

    def begin_request(self, method: str, resource: MetadataResource, *, ordinal: int,
                      retry_of: str | None = None) -> str:
        request_id = hash_object({"method": method, "ordinal": ordinal,
                                  "role": resource.role.value, "url": resource.url})
        used = self._counter("requests")
        reserve = resource.expected_length if method == "GET" else 0
        if (used + 1 > self.caps.requests or reserve > self.caps.single_resource_body_bytes or
                self._counter("body_bytes") + reserve > self.caps.http_body_bytes):
            raise BootstrapError("METADATA_RESOURCE_LIMIT_STOP")
        if retry_of is not None:
            previous = self.db.execute("SELECT method,url,role,retry_of FROM requests WHERE id=?", (retry_of,)).fetchone()
            prior_retries = self.db.execute("SELECT COUNT(*) FROM requests WHERE retry_of=?", (retry_of,)).fetchone()[0]
            if (previous != (method, resource.url, resource.role.value, None) or
                    prior_retries >= self.caps.retry_additional_per_exact_identity):
                raise BootstrapError("METADATA_RESOURCE_LIMIT_STOP")
        try:
            self.db.execute("INSERT INTO requests VALUES(?,?,?,?,?,?,?,0)",
                (request_id, method, resource.url, resource.role.value, retry_of, "RESERVED", reserve))
        except sqlite3.IntegrityError as exc:
            raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT") from exc
        self._add("requests", 1); self.db.commit()
        return request_id

    def finish_request(self, request_id: str, status: str, actual_body: int,
                       *, uncertain: bool = False) -> None:
        row = self.db.execute("SELECT reserved_body,status FROM requests WHERE id=?", (request_id,)).fetchone()
        if not row or row[1] != "RESERVED" or type(actual_body) is not int or actual_body < 0:
            raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT")
        charge = row[0] if uncertain else actual_body
        if self._counter("body_bytes") + charge > self.caps.http_body_bytes:
            raise BootstrapError("METADATA_RESOURCE_LIMIT_STOP")
        self.db.execute("UPDATE requests SET status=?,actual_body=? WHERE id=?", (status, charge, request_id))
        self._add("body_bytes", charge); self._add("io_bytes", charge); self.db.commit()

    def record_staging(self, identity: str, role: PhysicalRole, path: str,
                       status: str, size: int) -> None:
        self.db.execute("INSERT OR REPLACE INTO staging VALUES(?,?,?,?,?)",
                        (identity, role.value, path, status, size))
        self._add("watermark", 0); self.db.commit()

    def record_raw(self, role: PhysicalRole, path: str, size: int, sha256: str,
                   request_id: str) -> None:
        try:
            self.db.execute("INSERT INTO raw VALUES(?,?,?,?,?)",
                            (role.value, path, size, sha256, request_id))
        except sqlite3.IntegrityError as exc:
            raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT") from exc
        # Disk bytes were charged when the staging inode was created.  Atomic
        # hard-link publication does not allocate a second body.
        self._add("watermark", 0); self.db.commit()

    def event(self, code: str) -> None:
        self.db.execute("INSERT INTO events(code) VALUES(?)", (code,))
        self._add("watermark", 0); self.db.commit()

    def set_terminal(self, outcome: str) -> None:
        if outcome == "METADATA_BOOTSTRAP_RESOLVED":
            raise BootstrapError("METADATA_TERMINAL_OUTCOME_INVALID_MODEL_B")
        if self.db.execute("SELECT COUNT(*) FROM terminal").fetchone()[0]:
            raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT")
        self.db.execute("INSERT INTO terminal VALUES(?)", (outcome,)); self.db.commit()


_RAW_TOKEN = object()


@dataclass(frozen=True)
class RawArtifact:
    role: PhysicalRole
    path: Path
    relative_path: str
    byte_length: int
    request_id: str
    _token: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._token is not _RAW_TOKEN:
            raise BootstrapError("METADATA_RAW_ARTIFACT_UNTRUSTED")


class AttemptStorage:
    def __init__(self, root: Path, ledger: BootstrapLedger, *, synthetic_only: bool):
        self.root = Path(root)
        self.ledger = ledger
        # A future ledger may already have created the attempt root.  Only its
        # SQLite files may pre-exist; provider data and staging may not.
        if self.root.exists():
            allowed = {ledger.path.name, ledger.path.name + "-wal", ledger.path.name + "-shm"}
            if any(path.name not in allowed for path in self.root.iterdir()):
                raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT")
        else:
            self.root.mkdir(parents=True)
        (self.root / "STAGING").mkdir(exist_ok=False)
        (self.root / "RAW_IMMUTABLE").mkdir(exist_ok=False)

    def staging_path(self, role: PhysicalRole, ordinal: int) -> tuple[str, Path]:
        identity = hash_object({"role": role.value, "ordinal": ordinal,
                                "ledger": self.ledger.identity})
        return identity, self.root / "STAGING" / f"{role.value}.{ordinal}.{identity}.partial"

    def write_staging(self, resource: MetadataResource, ordinal: int,
                      chunks: Iterable[bytes]) -> tuple[str, Path, int]:
        identity, path = self.staging_path(resource.role, ordinal)
        size = 0
        if (self.ledger._counter("disk_bytes") + resource.expected_length > self.ledger.caps.disk_bytes or
                self.ledger._counter("io_bytes") + resource.expected_length > self.ledger.caps.io_bytes):
            raise BootstrapError("METADATA_RESOURCE_LIMIT_STOP")
        try:
            with path.open("xb") as stream:
                for chunk in chunks:
                    if type(chunk) is not bytes:
                        raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")
                    stream.write(chunk); size += len(chunk)
                    if size > self.ledger.caps.single_resource_body_bytes:
                        raise BootstrapError("METADATA_RESOURCE_LIMIT_STOP")
                stream.flush(); os.fsync(stream.fileno())
        except Exception:
            self.ledger._add("disk_bytes", size); self.ledger._add("io_bytes", size)
            self.ledger.record_staging(identity, resource.role,
                str(path.relative_to(self.root)), "FAILED", size)
            raise
        self.ledger._add("disk_bytes", size); self.ledger._add("io_bytes", size)
        status = "COMPLETE" if size == resource.expected_length else "PARTIAL"
        self.ledger.record_staging(identity, resource.role,
            str(path.relative_to(self.root)), status, size)
        return identity, path, size

    def publish_raw(self, resource: MetadataResource, staging_identity: str,
                    staging_path: Path, size: int, request_id: str) -> RawArtifact:
        if size != resource.expected_length:
            raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")
        destination = self.root / resource.raw_relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(staging_path, destination)
        except FileExistsError as exc:
            raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT") from exc
        os.chmod(destination, 0o444)
        staging_path.unlink()
        self.ledger.record_staging(staging_identity, resource.role,
            str(staging_path.relative_to(self.root)), "PUBLISHED", size)
        artifact = RawArtifact(resource.role, destination, resource.raw_relative_path,
                               size, request_id, _RAW_TOKEN)
        return artifact

    def incomplete_staging(self) -> tuple[Path, ...]:
        return tuple(path for path in (self.root / "STAGING").iterdir() if path.is_file())


_DIGEST_TOKEN = object()


def _digest_binding(values: tuple[object, ...]) -> str:
    return hashlib.sha256(canonical(list(values)) + str(id(_DIGEST_TOKEN)).encode()).hexdigest()


@dataclass(frozen=True)
class BootstrapRawDigest:
    role: PhysicalRole
    literal_url: str
    authorization_sha256: str
    attempt_id: str
    raw_relative_path: str
    raw_byte_length: int
    raw_sha256: str
    implementation_aggregate: str
    environment_fingerprint: str
    transport_receipt_sha256: str
    request_identity: str
    ledger_watermark: int
    completion_timestamp: str
    _binding_sha256: str = field(repr=False, compare=False)
    _raw_path: Path = field(repr=False, compare=False)
    _token: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        public = (self.role.value, self.literal_url, self.authorization_sha256,
                  self.attempt_id, self.raw_relative_path, self.raw_byte_length,
                  self.raw_sha256, self.implementation_aggregate,
                  self.environment_fingerprint, self.transport_receipt_sha256,
                  self.request_identity, self.ledger_watermark,
                  self.completion_timestamp)
        if (self._token is not _DIGEST_TOKEN or
                self._binding_sha256 != _digest_binding(public)):
            raise BootstrapError("METADATA_COMPLETE_DIGEST_PROVENANCE_REQUIRED")

    def object(self) -> dict:
        return {key: value for key, value in vars(self).items()
                if key not in ("_binding_sha256", "_raw_path", "_token")}


def derive_raw_digest(artifact: RawArtifact, resource: MetadataResource, *,
                      authorization_sha256: str, implementation_aggregate: str,
                      transport_receipt_sha256: str, ledger: BootstrapLedger,
                      timestamp: str | None = None) -> BootstrapRawDigest:
    if not isinstance(artifact, RawArtifact) or artifact._token is not _RAW_TOKEN:
        raise BootstrapError("METADATA_COMPLETE_DIGEST_PROVENANCE_REQUIRED")
    if artifact.role is not resource.role or artifact.byte_length != resource.expected_length:
        raise BootstrapError("METADATA_COMPLETE_DIGEST_PROVENANCE_REQUIRED")
    digest = hashlib.sha256(); count = 0
    with artifact.path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk); count += len(chunk)
    if count != artifact.byte_length:
        raise BootstrapError("METADATA_COMPLETE_DIGEST_PROVENANCE_REQUIRED")
    ledger._add("io_bytes", count); ledger.db.commit()
    completed = timestamp or datetime.now(timezone.utc).isoformat()
    public = (resource.role.value, resource.url, authorization_sha256,
              ATTEMPT_ID, artifact.relative_path, count, digest.hexdigest(),
              implementation_aggregate, ENVIRONMENT_FINGERPRINT,
              transport_receipt_sha256, artifact.request_id, ledger.watermark,
              completed)
    value = BootstrapRawDigest(resource.role, resource.url, authorization_sha256,
        ATTEMPT_ID, artifact.relative_path, count, digest.hexdigest(),
        implementation_aggregate, ENVIRONMENT_FINGERPRINT,
        transport_receipt_sha256, artifact.request_id, ledger.watermark,
        completed, _digest_binding(public), artifact.path, _DIGEST_TOKEN)
    ledger.record_raw(artifact.role, artifact.relative_path, count,
                      value.raw_sha256, artifact.request_id)
    return value


def validate_regional_provider_integrity(digest: BootstrapRawDigest) -> bool:
    if digest.role is PhysicalRole.SOUTH_PATCH_LIST:
        raise BootstrapError("PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND")
    try:
        validate_provider_full_file_integrity(
            digest.role, LocallyComputedFullFileSha256(digest.raw_sha256))
    except Exception as exc:
        raise BootstrapError("METADATA_FULL_FILE_INTEGRITY_FAILURE") from exc
    return True


def patch_acquisition_evidence(digest: BootstrapRawDigest,
                               resource: MetadataResource, *,
                               synthetic_only: bool) -> AcquisitionBoundLocalSha256:
    if digest.role is not PhysicalRole.SOUTH_PATCH_LIST:
        raise BootstrapError("PATCH_ACQUISITION_BINDING_INVALID")
    return AcquisitionBoundLocalSha256(
        role=digest.role, resource_url=resource.url,
        physical_contract_sha256=PHYSICAL_CONTRACT_HASHES[digest.role],
        authorization_sha256=digest.authorization_sha256,
        implementation_aggregate=digest.implementation_aggregate,
        environment_fingerprint=digest.environment_fingerprint,
        representation_identity=EXPECTED_PATCH_REPRESENTATION,
        acquired_byte_count=digest.raw_byte_length,
        local_sha256=digest.raw_sha256, synthetic_only=synthetic_only,
    )


class PatchPayloadFirewall:
    def __init__(self) -> None:
        self.payload_decoder_calls = 0

    def decode_row_payload(self, *args, **kwargs):
        self.payload_decoder_calls += 1
        raise BootstrapError("METADATA_ROW_OBSERVATION_INTEGRITY_FAILURE")

    decode_release = decode_row_payload
    decode_brickid = decode_row_payload
    decode_brickname = decode_row_payload
    validate_membership = decode_row_payload


@dataclass(frozen=True)
class PatchHeaderEvidence:
    physical_contract_sha256: str
    header_bytes_consumed: int
    payload_bytes_observed: int = 0


def validate_patch_header_only(path: Path,
                               contract: FrozenPhysicalContract) -> PatchHeaderEvidence:
    """Validate PATCH FITS headers while stopping before the first table byte."""
    if contract.role is not PhysicalRole.SOUTH_PATCH_LIST or contract.compression != "identity":
        raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
    consumed = 0
    headers: list[dict[str, object]] = []
    try:
        with Path(path).open("rb") as stream:
            for _ in range(contract.target_hdu_index + 1):
                blocks = bytearray()
                while True:
                    block = stream.read(2880)
                    if len(block) != 2880:
                        raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
                    blocks.extend(block); consumed += len(block)
                    if any(block[offset:offset + 8] == b"END     "
                           for offset in range(0, 2880, 80)):
                        break
                header, _ = _header(bytes(blocks), 0)
                headers.append(header)
            observed = headers[contract.target_hdu_index]
            expected = {
                "XTENSION": contract.xtension, "BITPIX": contract.bitpix,
                "NAXIS": contract.naxis, "NAXIS1": contract.naxis1,
                "NAXIS2": contract.naxis2, "PCOUNT": contract.pcount,
                "GCOUNT": contract.gcount, "TFIELDS": contract.tfields,
            }
            if any(observed.get(key) != value for key, value in expected.items()):
                raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
            for key, absent in (("EXTNAME", contract.extname_absent),
                                ("CHECKSUM", contract.checksum_absent),
                                ("DATASUM", contract.datasum_absent)):
                if absent and key in observed:
                    raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
            for index, column in enumerate(contract.columns, 1):
                if (observed.get(f"TTYPE{index}") != column.ttype or
                        observed.get(f"TFORM{index}") != column.tform):
                    raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
                for prefix, absent in (("TUNIT", column.tunit_absent),
                                       ("TNULL", column.tnull_absent),
                                       ("TSCAL", column.tscal_absent),
                                       ("TZERO", column.tzero_absent)):
                    if absent and f"{prefix}{index}" in observed:
                        raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
    except BootstrapError:
        raise
    except Exception as exc:
        raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE") from exc
    return PatchHeaderEvidence(contract.sha256, consumed, 0)


def validate_bootstrap_physical(digest: BootstrapRawDigest,
                                contract: FrozenPhysicalContract | None = None) -> str:
    if not isinstance(digest, BootstrapRawDigest) or digest._token is not _DIGEST_TOKEN:
        raise BootstrapError("METADATA_COMPLETE_DIGEST_PROVENANCE_REQUIRED")
    contract = contract or PRODUCTION_PHYSICAL_CONTRACTS[digest.role]
    if (digest._raw_path.stat().st_size != digest.raw_byte_length or
            file_hash(digest._raw_path) != digest.raw_sha256):
        raise BootstrapError("METADATA_FULL_FILE_INTEGRITY_FAILURE")
    try:
        if digest.role is PhysicalRole.SOUTH_PATCH_LIST:
            return validate_patch_header_only(digest._raw_path, contract).physical_contract_sha256
        return validate_fits_structure(digest._raw_path, contract)
    except Exception as exc:
        raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE") from exc


_TFORM = re.compile(r"^(\d*)([AIJEDL])$")
_WIDTH = {"A": 1, "I": 2, "J": 4, "E": 4, "D": 8, "L": 1}


def _tform(tform: str) -> tuple[int, str, int]:
    match = _TFORM.fullmatch(tform)
    if not match:
        raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
    repeat = int(match.group(1) or "1"); code = match.group(2)
    return repeat, code, repeat * _WIDTH[code]


def _parse_value(raw: str):
    raw = raw.split("/", 1)[0].strip()
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].strip()
    if raw == "T": return True
    if raw == "F": return False
    try: return int(raw)
    except ValueError:
        try: return float(raw.replace("D", "E"))
        except ValueError: return raw


def _header(data: bytes, start: int) -> tuple[dict[str, object], int]:
    values: dict[str, object] = {}
    offset = start
    while offset + 80 <= len(data):
        card = data[offset:offset + 80]; offset += 80
        try: key = card[:8].decode("ascii").strip()
        except UnicodeDecodeError as exc: raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE") from exc
        if key == "END":
            end = ((offset + 2879) // 2880) * 2880
            return values, end
        if card[8:10] == b"= ":
            values[key] = _parse_value(card[10:80].decode("ascii"))
    raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")


def _table_location(data: bytes, contract: FrozenPhysicalContract) -> tuple[dict[str, object], int]:
    start = 0
    for index in range(contract.target_hdu_index + 1):
        header, data_start = _header(data, start)
        if index == contract.target_hdu_index:
            return header, data_start
        naxis = int(header.get("NAXIS", 0))
        size = 0 if naxis == 0 else abs(int(header.get("BITPIX", 8))) // 8
        for axis in range(1, naxis + 1): size *= int(header.get(f"NAXIS{axis}", 0))
        size += int(header.get("PCOUNT", 0))
        start = data_start + ((size + 2879) // 2880) * 2880
    raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")


def _decode_allowed_cell(raw: bytes, tform: str, field_id: FieldId):
    repeat, code, width = _tform(tform)
    if len(raw) != width:
        raise BootstrapError("METADATA_VALUE_SEMANTICS_FAILURE")
    if code == "A":
        if field_id in (FieldId.ROOT_BRICKNAME, FieldId.REG_BRICKNAME):
            return validate_brickname(raw)
        return raw.decode("ascii", errors="strict")
    if code == "L":
        values = []
        for item in raw:
            if item == ord("T"): values.append(True)
            elif item == ord("F"): values.append(False)
            else: raise BootstrapError("METADATA_VALUE_SEMANTICS_FAILURE")
    else:
        fmt = {"I": "h", "J": "i", "E": "f", "D": "d"}[code]
        values = list(struct.unpack(">" + fmt * repeat, raw))
    return values[0] if repeat == 1 else tuple(values)


@dataclass
class DecodeInstrumentation:
    opaque_bytes_transited: int = 0
    cell_values_decoded: int = 0
    forbidden_cell_decode_count: int = 0
    forbidden_value_materialization_count: int = 0
    forbidden_value_log_count: int = 0
    forbidden_value_serialization_count: int = 0

    def assert_clean(self) -> None:
        if any((self.forbidden_cell_decode_count,
                self.forbidden_value_materialization_count,
                self.forbidden_value_log_count,
                self.forbidden_value_serialization_count)):
            raise BootstrapError("METADATA_FORBIDDEN_FIELD_BOUNDARY_FAILURE")


@dataclass
class SelectiveDecodeSession:
    rows: Iterator[MappingProxyType]
    instrumentation: DecodeInstrumentation


class SelectiveFitsDecoder:
    """Manual row-stride decoder; never creates a complete provider record."""

    prohibited_real_apis = (
        "hdu.data", "Table.read", "FITS_rec", "np.asarray(full_table)",
        "pandas", "Astropy Table",
    )

    def decode(self, path: Path, contract: FrozenPhysicalContract) -> SelectiveDecodeSession:
        if contract.role is PhysicalRole.SOUTH_PATCH_LIST:
            raise BootstrapError("METADATA_ROW_OBSERVATION_INTEGRITY_FAILURE")
        raw = Path(path).read_bytes()
        try:
            data = gzip.decompress(raw) if contract.compression == "gzip" else raw
        except Exception as exc:
            raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE") from exc
        header, data_start = _table_location(data, contract)
        logical = ROOT_LOGICAL_FIELDS if contract.role is PhysicalRole.ROOT_SUMMARY else REGIONAL_LOGICAL_FIELDS
        logical_by_provider_name = {field.provider_name: field for field in logical}
        if (len(logical_by_provider_name) != len(contract.columns) or
                {column.ttype for column in contract.columns} != set(logical_by_provider_name)):
            raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
        offsets = []; offset = 0
        for column in contract.columns:
            spec = logical_by_provider_name[column.ttype]
            _, _, width = _tform(column.tform)
            offsets.append((offset, width, column.tform, spec.field_id, spec.classification))
            offset += width
        nrows = header.get("NAXIS2"); row_size = header.get("NAXIS1")
        if type(nrows) is not int or type(row_size) is not int or row_size != offset:
            raise BootstrapError("METADATA_PHYSICAL_CONTRACT_FAILURE")
        needed = data_start + row_size * nrows
        if needed > len(data):
            raise BootstrapError("METADATA_TRANSPORT_INTEGRITY_FAILURE")
        metrics = DecodeInstrumentation(opaque_bytes_transited=row_size * nrows)

        def rows() -> Iterator[MappingProxyType]:
            for row_index in range(nrows):
                base = data_start + row_index * row_size
                selected = {}
                for col_offset, width, tform, field_id, classification in offsets:
                    if classification is not FieldClass.TECHNICAL_ALLOWED:
                        continue
                    selected[field_id] = _decode_allowed_cell(
                        data[base + col_offset:base + col_offset + width], tform, field_id)
                    metrics.cell_values_decoded += 1
                yield MappingProxyType(selected)
            metrics.assert_clean()

        return SelectiveDecodeSession(rows(), metrics)


@dataclass(frozen=True)
class RootSemanticIndex:
    by_name: MappingProxyType
    total_rows: int
    valid_rows: int
    invalid_by_reason: MappingProxyType


def _finite(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_root_semantics(rows: Iterable[Mapping[FieldId, object]]) -> RootSemanticIndex:
    by_name: dict[bytes, int] = {}; ids: set[int] = set(); invalid: dict[str, int] = {}
    total = 0
    for row in rows:
        total += 1
        try:
            name = row[FieldId.ROOT_BRICKNAME]; brickid = row[FieldId.ROOT_BRICKID]
            if not isinstance(name, ValidatedBrickname): raise ValueError("BRICKNAME_INVALID")
            if type(brickid) is not int: raise ValueError("BRICKID_INVALID")
            for key in (FieldId.ROOT_RA, FieldId.ROOT_DEC, FieldId.ROOT_RA1,
                        FieldId.ROOT_RA2, FieldId.ROOT_DEC1, FieldId.ROOT_DEC2):
                if not _finite(row[key]): raise ValueError("FINITE_VALUE_INVALID")
            if name.raw in by_name: raise ValueError("DUPLICATE_BRICKNAME")
            if brickid in ids: raise ValueError("DUPLICATE_BRICKID")
            by_name[name.raw] = brickid; ids.add(brickid)
        except (KeyError, ValueError) as exc:
            reason = str(exc).strip("'") if str(exc) else "FINITE_VALUE_INVALID"
            invalid[reason] = invalid.get(reason, 0) + 1
    if invalid:
        raise BootstrapError("METADATA_VALUE_SEMANTICS_FAILURE")
    return RootSemanticIndex(MappingProxyType(by_name), total, total, MappingProxyType({}))


@dataclass(frozen=True)
class RegionalSemanticSummary:
    role: PhysicalRole
    total_rows: int
    valid_rows: int
    invalid_by_reason: MappingProxyType
    exact_root_matches: int
    grz_true: int
    row_values_persisted: bool = False


def validate_regional_semantics(role: PhysicalRole,
                                rows: Iterable[Mapping[FieldId, object]],
                                root: RootSemanticIndex) -> RegionalSemanticSummary:
    if role not in (PhysicalRole.NORTH_SUMMARY, PhysicalRole.SOUTH_SUMMARY):
        raise BootstrapError("METADATA_VALUE_SEMANTICS_FAILURE")
    total = matches = grz_true = 0; names: set[bytes] = set(); ids: set[int] = set(); invalid: dict[str, int] = {}
    for row in rows:
        total += 1
        try:
            name = row[FieldId.REG_BRICKNAME]; brickid = row[FieldId.REG_BRICKID]
            if not isinstance(name, ValidatedBrickname): raise ValueError("BRICKNAME_INVALID")
            if type(brickid) is not int: raise ValueError("BRICKID_INVALID")
            if name.raw in names: raise ValueError("DUPLICATE_BRICKNAME")
            if brickid in ids: raise ValueError("DUPLICATE_BRICKID")
            for key in (FieldId.REG_RA, FieldId.REG_DEC, FieldId.REG_RA1,
                        FieldId.REG_RA2, FieldId.REG_DEC1, FieldId.REG_DEC2,
                        FieldId.REG_AREA):
                if not _finite(row[key]): raise ValueError("FINITE_VALUE_INVALID")
            if type(row[FieldId.REG_SURVEY_PRIMARY]) is not bool:
                raise ValueError("SURVEY_PRIMARY_INVALID")
            try: present = grz_median_present_v1(row[FieldId.REG_NEXP_G], row[FieldId.REG_NEXP_R], row[FieldId.REG_NEXP_Z])
            except Exception: raise ValueError("GRZ_INPUT_INVALID")
            if name.raw not in root.by_name: raise ValueError("ROOT_MATCH_ZERO")
            if root.by_name[name.raw] != brickid: raise ValueError("ROOT_BRICKID_MISMATCH")
            names.add(name.raw); ids.add(brickid); matches += 1; grz_true += int(present)
        except (KeyError, ValueError) as exc:
            reason = str(exc).strip("'") if str(exc) else "FINITE_VALUE_INVALID"
            invalid[reason] = invalid.get(reason, 0) + 1
    if invalid:
        raise BootstrapError("METADATA_VALUE_SEMANTICS_FAILURE")
    return RegionalSemanticSummary(role, total, total, MappingProxyType({}), matches, grz_true, False)


def canonical_json_bytes(value: object) -> bytes:
    return canonical(value) + b"\n"


def write_final_json(root: Path, name: str, value: Mapping[str, object]) -> Path:
    if name not in FINAL_EVIDENCE_ARTIFACTS or not name.endswith(".json"):
        raise BootstrapError("METADATA_FINAL_ARTIFACT_NOT_ALLOWED")
    path = Path(root) / name
    try:
        with path.open("xb") as stream:
            stream.write(canonical_json_bytes(dict(value))); stream.flush(); os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise BootstrapError("METADATA_LOCAL_STATE_CONFLICT") from exc
    return path


def dry_run_plan(project: Path, argv: Iterable[str]) -> dict:
    project = Path(project).resolve()
    for name, expected in AUTHORITY_BINDINGS.items():
        path = project / name
        if not path.is_file() or file_hash(path) != expected:
            raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE")
    try:
        environment = json.loads((project / "oc3/environment_setup/ENVIRONMENT.json").read_text())
    except (OSError, ValueError) as exc:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE") from exc
    if environment.get("environment_sha256") != ENVIRONMENT_FINGERPRINT:
        raise BootstrapError("METADATA_BOOTSTRAP_AUTHORITY_FAILURE")
    aggregate = implementation_hash(project)
    return {
        "attempt_directory": ATTEMPT_RELATIVE_DIRECTORY,
        "authorization_required": True,
        "caps": vars(RESOURCE_CAPS),
        "command_argv": list(argv),
        "command_sha256": command_sha256(argv),
        "expected_aggregate_bytes": EXPECTED_AGGREGATE_BYTES,
        "implementation_aggregate": aggregate,
        "environment_fingerprint": ENVIRONMENT_FINGERPRINT,
        "authorities": dict(AUTHORITY_BINDINGS),
        "model": PATCH_MODEL,
        "network_constructed": False,
        "output_artifacts": list(FINAL_EVIDENCE_ARTIFACTS),
        "physical_contract_hashes": {role.value: value for role, value in PHYSICAL_CONTRACT_HASHES.items()},
        "resources": [{"role": role.value, "url": resource.url, "expected_length": resource.expected_length}
                      for role, resource in RESOURCES.items()],
        "rights_binding_required": True,
        "scope": BOOTSTRAP_SCOPE,
    }


def no_selector_api() -> bool:
    return True
