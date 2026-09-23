"""Separate HEAD-only probe for the exact desitarget commit archive.

This module has no GET, Range, body-read, archive-decode, or astronomical-data
capability.  Network transport is constructed only after a sealed candidate
and separate final human authorization validate exactly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import http.client
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

from .core import canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)
from .photsys_zero_byte_provenance import ARCHIVE_URL, EXPECTED_COMMIT


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-HEAD-PROBE-001"
SCOPE = "DESITARGET_COMMIT_ARCHIVE_SIZE_ONLY"
SUCCESS = "DESITARGET_COMMIT_ARCHIVE_SIZE_OBSERVED"
INCONCLUSIVE = "DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE"
FAILED = "DESITARGET_COMMIT_ARCHIVE_HEAD_PROBE_FAILED"
READY = "READY_AT_DESITARGET_COMMIT_ARCHIVE_HEAD_BOUNDARY"

REVIEW_PATH = PROJECT / "OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_FAILED_ATTEMPT_REVIEW.md"
REVIEW_SHA256 = "55524fc8d32628a9110b9231372d3589eaac87d4f48e823b268dae6e6b1f61a2"
FAILED_ROOT = PROJECT / "oc3/photsys_zero_byte_provenance" / (
    "OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001")
FAILED_TERMINAL_PATH = FAILED_ROOT / "TERMINAL.json"
FAILED_TERMINAL_SHA256 = "fef519e21342cea7dee90ec25861ffc086f05b9643370eaa1b34de4785a946a3"

PRESERVED_BODIES = (
    ("FITS_STANDARD_4_0.body", 1_140_821,
     "5624dca15659caf54c56127b4df9af05fd930c8f6d997fcb4bea2b1a5c1bc573"),
    ("LEGACY_SURVEY_DR9_FILES.body", 187_585,
     "d0b51d66529cb4c62db7e8ae1df22d6976879f46dcd62b4e6993729b42674c85"),
    ("DESITARGET_TAG_REF.body", 339,
     "9289a01c82464f9ffe901b907e165c2c9bb7de7c3e17e454d112a3eb6ae2476d"),
    ("DESITARGET_TAG_OBJECT.body", 684,
     "c8a62b156a83788ae395ad2d866bdc114a958f3af93984326594d0c5dabeaef8"),
)
RAW_ROOT = FAILED_ROOT / "RAW_IMMUTABLE_PUBLIC_SOURCES"

HISTORICAL_REQUESTS = 5
HISTORICAL_PRESERVED_BODY_BYTES = 1_329_429
HISTORICAL_MINIMUM_BODY_BYTES = 1_329_429
HISTORICAL_MAXIMUM_BODY_BYTES = 16_009_494
PARENT_BODY_MAXIMUM = 32 * 1024 * 1024
REMAINING_CONSERVATIVE_BODY_BUDGET = 17_544_938

REQUEST_CAP = 1
BODY_CAP = 0
REDIRECT_CAP = 0
RETRY_CAP = 0
CONCURRENCY = 1
ACCEPTED_CONTENT_TYPES = ("application/gzip", "application/x-gzip", "application/octet-stream")

CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_HEAD_PROBE_CANDIDATE_001.json"
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_DESITARGET_ARCHIVE_HEAD_PROBE_FINAL_AUTHORIZATION_001.json"
OUTPUT_ROOT = PROJECT / "oc3/photsys_archive_head_probe" / STAGE_ID


class HeadProbeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass
class HeadCounters:
    network_requests_started: int = 0
    application_body_bytes_read: int = 0
    astronomical_data_GETs: int = 0
    real_PHOTSYS_bytes_observed: int = 0
    BRICKNAME_values_observed: int = 0
    BRICKID_values_observed: int = 0
    ROOT_values_observed: int = 0

    def object(self) -> dict[str, int]:
        return asdict(self)


def validate_historical_inputs() -> dict[str, object]:
    if not REVIEW_PATH.is_file() or file_sha256(REVIEW_PATH) != REVIEW_SHA256:
        raise HeadProbeError("FAILED_ATTEMPT_REVIEW_MISMATCH")
    if (not FAILED_TERMINAL_PATH.is_file() or
            file_sha256(FAILED_TERMINAL_PATH) != FAILED_TERMINAL_SHA256):
        raise HeadProbeError("FAILED_ATTEMPT_TERMINAL_MISMATCH")
    terminal = validate_sealed(load_canonical_json(FAILED_TERMINAL_PATH))
    counters = terminal.get("counters", {})
    if (terminal.get("state") != "PHOTSYS_ZERO_BYTE_RESEARCH_INTEGRITY_STOP" or
            terminal.get("outcome") is not None or
            counters.get("public_documentary_source_requests") != HISTORICAL_REQUESTS or
            counters.get("public_documentary_source_body_bytes") != HISTORICAL_PRESERVED_BODY_BYTES):
        raise HeadProbeError("FAILED_ATTEMPT_TERMINAL_MISMATCH")
    for key in ("astronomical_data_GETs", "real_PHOTSYS_bytes_observed",
                "BRICKNAME_values_observed", "BRICKID_values_observed", "ROOT_values_observed"):
        if counters.get(key) != 0:
            raise HeadProbeError("FAILED_ATTEMPT_FIREWALL_MISMATCH")
    bound = []
    for filename, size, digest in PRESERVED_BODIES:
        path = RAW_ROOT / filename
        if not path.is_file() or path.stat().st_size != size or file_sha256(path) != digest:
            raise HeadProbeError("PRESERVED_BODY_MISMATCH")
        bound.append({"bytes": size, "path": str(path.relative_to(PROJECT)), "sha256": digest})
    if ((RAW_ROOT / "DESITARGET_0_48_0_ARCHIVE.tar.gz").exists() or
            sum(item["bytes"] for item in bound) != HISTORICAL_PRESERVED_BODY_BYTES or
            PARENT_BODY_MAXIMUM - HISTORICAL_MAXIMUM_BODY_BYTES != REMAINING_CONSERVATIVE_BODY_BUDGET):
        raise HeadProbeError("FAILED_ATTEMPT_ACCOUNTING_MISMATCH")
    return {
        "application_body_bytes_read": 0,
        "astronomical_data_GETs": 0,
        "historical_terminal": terminal["state"],
        "network_requests": 0,
        "preserved_bodies": bound,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": "DESITARGET_ARCHIVE_HEAD_PROBE_INPUTS_VALIDATED",
    }


def exact_command(project: Path = PROJECT) -> list[str]:
    project = Path(project).resolve()
    return [
        str(project / "oc3/.venv/bin/python"),
        str(project / "oc3/oc3_photsys_archive_head_probe.py"),
        "--probe-desitarget-archive-head", "--execute-network",
        "--candidate", str(project / CANDIDATE_PATH.relative_to(PROJECT)),
        "--authorization", str(project / AUTHORIZATION_PATH.relative_to(PROJECT)),
        "--output-directory", str(project / OUTPUT_ROOT.relative_to(PROJECT)),
    ]


def build_candidate(implementation_aggregate: str) -> dict[str, object]:
    inputs = validate_historical_inputs()
    command = exact_command()
    return sealed({
        "accepted_content_types": list(ACCEPTED_CONTENT_TYPES),
        "budget_decision": {
            "allow_later_candidate_when_content_length_at_most": REMAINING_CONSERVATIVE_BODY_BUDGET,
            "parent_maximum_body_bytes": PARENT_BODY_MAXIMUM,
            "stop_when_content_length_greater_than": REMAINING_CONSERVATIVE_BODY_BUDGET,
        },
        "candidate_state": "PENDING_HUMAN_REVIEW",
        "command_argv": command,
        "command_argv_sha256": sha256_bytes(canonical(command)),
        "final_authorization_path": str(AUTHORIZATION_PATH),
        "final_authorization_present": False,
        "historical_attempt": {
            "authorization_consumed": True,
            "automatic_resume": False,
            "maximum_possible_total_body_bytes": HISTORICAL_MAXIMUM_BODY_BYTES,
            "minimum_possible_total_body_bytes": HISTORICAL_MINIMUM_BODY_BYTES,
            "preserved_body_bytes": HISTORICAL_PRESERVED_BODY_BYTES,
            "requests_started": HISTORICAL_REQUESTS,
            "review_path": str(REVIEW_PATH.relative_to(PROJECT)),
            "review_sha256": REVIEW_SHA256,
            "runtime_reuse": False,
            "terminal_path": str(FAILED_TERMINAL_PATH.relative_to(PROJECT)),
            "terminal_sha256": FAILED_TERMINAL_SHA256,
        },
        "implementation_aggregate": implementation_aggregate,
        "method": "HEAD",
        "negative_capabilities": {
            "archive_body": False, "automatic_resume": False, "get": False,
            "range": False, "redirect": False, "retry": False,
            "semantic_research": False, "synthetic_zero_initialization": False,
        },
        "network_caps": {
            "body_bytes_authorized": BODY_CAP, "concurrency": CONCURRENCY,
            "redirects": REDIRECT_CAP, "requests": REQUEST_CAP, "retries": RETRY_CAP,
        },
        "preserved_bodies": inputs["preserved_bodies"],
        "resource": {
            "commit": EXPECTED_COMMIT, "literal_url": ARCHIVE_URL,
            "resource_count": 1,
        },
        "schema_version": "OC3_PHOTSYS_DESITARGET_ARCHIVE_HEAD_PROBE_CANDIDATE_001",
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "terminal_rules": {
            "missing_or_invalid_content_length": INCONCLUSIVE,
            "positive_content_length": SUCCESS,
            "transport_or_contract_failure": FAILED,
        },
    })


def validate_candidate(path: Path = CANDIDATE_PATH,
                       *, require_authorization_absent: bool = True) -> dict[str, object]:
    try:
        candidate = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise HeadProbeError("HEAD_PROBE_CANDIDATE_INVALID") from exc
    if candidate != build_candidate(implementation_hash(PROJECT)):
        raise HeadProbeError("HEAD_PROBE_CANDIDATE_INVALID")
    if require_authorization_absent and AUTHORIZATION_PATH.exists():
        raise HeadProbeError("PREMATURE_HEAD_PROBE_AUTHORIZATION")
    return candidate


def validate_authorization(candidate_path: Path, authorization_path: Path,
                           command_argv_sha256: str) -> dict[str, object]:
    candidate = validate_candidate(candidate_path, require_authorization_absent=False)
    try:
        authorization = validate_sealed(load_canonical_json(authorization_path))
    except Exception as exc:
        raise HeadProbeError("HEAD_PROBE_FINAL_AUTHORIZATION_INVALID") from exc
    required = {"authorization_id", "authorization_state", "authorized", "candidate_sha256",
                "command_argv_sha256", "resume", "scope", "sealed", "stage_id"}
    if (set(authorization) != required or authorization.get("authorized") is not True or
            authorization.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            authorization.get("candidate_sha256") != file_sha256(candidate_path) or
            authorization.get("command_argv_sha256") != command_argv_sha256 or
            authorization.get("command_argv_sha256") != candidate["command_argv_sha256"] or
            authorization.get("resume") is not False or authorization.get("scope") != SCOPE or
            authorization.get("stage_id") != STAGE_ID):
        raise HeadProbeError("HEAD_PROBE_FINAL_AUTHORIZATION_INVALID")
    return authorization


def dry_run() -> dict[str, object]:
    validate_historical_inputs()
    validate_candidate()
    return {
        "application_body_bytes_read": 0, "body_bytes_authorized": BODY_CAP,
        "method": "HEAD", "network_requests": 0,
        "request_cap": REQUEST_CAP, "scope": SCOPE, "stage_id": STAGE_ID,
        "state": READY,
    }


class HeadOnlyTransport:
    """One exact HEAD operation.  No body-read or GET entry point exists."""
    __slots__ = ("counters", "timeout_seconds", "last_metadata")

    def __init__(self, counters: HeadCounters, timeout_seconds: int = 30):
        self.counters = counters
        self.timeout_seconds = timeout_seconds
        self.last_metadata: dict[str, object] | None = None

    def head(self) -> dict[str, object]:
        parsed = urlsplit(ARCHIVE_URL)
        if (parsed.scheme != "https" or parsed.hostname != "codeload.github.com" or
                parsed.query or parsed.fragment or
                parsed.path != f"/desihub/desitarget/tar.gz/{EXPECTED_COMMIT}"):
            raise HeadProbeError("HEAD_RESOURCE_IDENTITY_INVALID")
        if self.counters.network_requests_started >= REQUEST_CAP:
            raise HeadProbeError("HEAD_REQUEST_CAP_EXCEEDED")
        self.counters.network_requests_started += 1
        connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                  timeout=self.timeout_seconds)
        connection.request("HEAD", parsed.path, headers={
            "Accept-Encoding": "identity", "User-Agent": "OC3-PHOTSYS-archive-head-probe/1"})
        response = connection.getresponse()
        headers = {key.lower(): value for key, value in response.getheaders()}
        raw_length = headers.get("content-length")
        declared = int(raw_length) if raw_length is not None and raw_length.isdigit() else None
        metadata = {
            "application_body_bytes_read": 0,
            "content_encoding": headers.get("content-encoding", "identity"),
            "content_type": headers.get("content-type"),
            "declared_content_length": declared,
            "etag": headers.get("etag"),
            "final_url": ARCHIVE_URL,
            "headers": headers,
            "last_modified": headers.get("last-modified"),
            "literal_url": ARCHIVE_URL,
            "method": "HEAD",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": response.status,
        }
        self.last_metadata = metadata
        connection.close()  # Deliberately no response.read call.
        if response.status in (301, 302, 303, 307, 308):
            raise HeadProbeError("HEAD_REDIRECT_FORBIDDEN")
        if response.status < 200 or response.status >= 300:
            raise HeadProbeError("HEAD_HTTP_STATUS_INVALID")
        if metadata["content_encoding"].lower() != "identity":
            raise HeadProbeError("HEAD_CONTENT_ENCODING_INVALID")
        content_type = (headers.get("content-type", "").split(";", 1)[0].strip().lower())
        if content_type not in ACCEPTED_CONTENT_TYPES:
            raise HeadProbeError("HEAD_CONTENT_TYPE_INVALID")
        return metadata


def classify_head(metadata: dict[str, object]) -> tuple[str, str]:
    declared = metadata.get("declared_content_length")
    if type(declared) is not int or declared <= 0:
        return INCONCLUSIVE, "NO_ARCHIVE_GET_CANDIDATE"
    if declared <= REMAINING_CONSERVATIVE_BODY_BUDGET:
        return SUCCESS, "LATER_ARCHIVE_ACQUISITION_MAY_BE_DESIGNED"
    return SUCCESS, "STOP_CURRENT_32_MIB_SPEC_CANNOT_ACCOMMODATE"


def execute(candidate_path: Path, authorization_path: Path, command_argv_sha256: str,
            output_directory: Path, *,
            transport_factory: Callable[[HeadCounters], HeadOnlyTransport] = HeadOnlyTransport) -> dict[str, object]:
    validate_candidate(candidate_path, require_authorization_absent=False)
    validate_authorization(candidate_path, authorization_path, command_argv_sha256)
    validate_historical_inputs()
    output = Path(output_directory).resolve()
    if output != OUTPUT_ROOT.resolve() or output.exists():
        raise HeadProbeError("HEAD_PROBE_RERUN_OR_RESUME_FORBIDDEN")
    output.mkdir(parents=True)
    counters = HeadCounters()
    transport = transport_factory(counters)
    metadata: dict[str, object] | None = None
    try:
        metadata = transport.head()
        state, budget_decision = classify_head(metadata)
        receipt = sealed({"budget_decision": budget_decision, "counters": counters.object(),
                          "response": metadata, "stage_id": STAGE_ID, "state": state})
        write_json_immutable(output / "HEAD_RESPONSE.json", receipt)
    except HeadProbeError as exc:
        state = FAILED
        budget_decision = "NO_ARCHIVE_GET_CANDIDATE"
        receipt = sealed({"budget_decision": budget_decision, "counters": counters.object(),
                          "failure_code": exc.code, "response": transport.last_metadata,
                          "stage_id": STAGE_ID, "state": state})
        write_json_immutable(output / "HEAD_RESPONSE.json", receipt)
    terminal = sealed({
        "application_body_bytes_read": counters.application_body_bytes_read,
        "budget_decision": budget_decision,
        "content_length": metadata.get("declared_content_length") if metadata else None,
        "counters": counters.object(), "scope": SCOPE, "stage_id": STAGE_ID,
        "state": state,
    })
    write_json_immutable(output / "TERMINAL.json", terminal)
    return terminal
