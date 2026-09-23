"""Closed Range-size probe for the exact commit-pinned desitarget archive.

The production transport issues one internally frozen GET with
``Range: bytes=0-0`` and never calls ``response.read()``.  It has no generic
GET, HEAD, Range, request, URL, method, or body-read interface.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import http.client
from pathlib import Path
import re
from typing import Callable
from urllib.parse import urlsplit

from .core import canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)
from .photsys_zero_byte_provenance import ARCHIVE_URL, EXPECTED_COMMIT


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-RANGE-SIZE-PROBE-001"
SCOPE = "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_ONLY"
SUCCESS = "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_OBSERVED"
INCONCLUSIVE = "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_INCONCLUSIVE"
FAILED = "DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_FAILED"
READY = "READY_AT_DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_BOUNDARY"

SPEC_PATH = PROJECT / "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_SPEC.md"
SPEC_SHA256 = "f4751e6d5aab144b637c313fb6f100df234f8ab78ad2a4186a2036b4e44f5604"
FAILED_REVIEW_PATH = PROJECT / "OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_FAILED_ATTEMPT_REVIEW.md"
FAILED_REVIEW_SHA256 = "55524fc8d32628a9110b9231372d3589eaac87d4f48e823b268dae6e6b1f61a2"

HEAD_STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-HEAD-PROBE-001"
HEAD_ROOT = PROJECT / "oc3/photsys_archive_head_probe" / HEAD_STAGE_ID
HEAD_RESPONSE_PATH = HEAD_ROOT / "HEAD_RESPONSE.json"
HEAD_RESPONSE_SHA256 = "5eefee40091b098435701e4abbf271cb888b29a0353df8e5e7da40242449506b"
HEAD_TERMINAL_PATH = HEAD_ROOT / "TERMINAL.json"
HEAD_TERMINAL_SHA256 = "d70de460a0628b333d73a5b4a70de6fdab53333a971f9c276beb2255a4b82da8"
HEAD_AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_DESITARGET_ARCHIVE_HEAD_PROBE_FINAL_AUTHORIZATION_001.json"
HEAD_AUTHORIZATION_SHA256 = "f33c558bb4b1b51671754571f6911db97611cdb858b1c741fb5956dee902d2bf"
HEAD_ETAG = '"a52cc7025bc235d2b8e2a6f7a4d0b494f2146beb5b02a8d6013819b46a4b2ea1"'

FAILED_ROOT = PROJECT / "oc3/photsys_zero_byte_provenance" / (
    "OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001")
RAW_ROOT = FAILED_ROOT / "RAW_IMMUTABLE_PUBLIC_SOURCES"
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

PARENT_BODY_MAXIMUM = 33_554_432
HISTORICAL_MAXIMUM_BODY_BYTES = 16_009_494
REMAINING_CONSERVATIVE_BODY_BUDGET = 17_544_938
REQUEST_CAP = 1
BODY_CAP = 0
REDIRECT_CAP = 0
RETRY_CAP = 0
CONCURRENCY = 1
RANGE_VALUE = "bytes=0-0"
CONTENT_RANGE_GRAMMAR = "bytes 0-0/TOTAL"
ACCEPTED_CONTENT_TYPES = ("application/gzip", "application/x-gzip", "application/octet-stream")
REDIRECT_STATUSES = (301, 302, 303, 307, 308)

CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_001.json"
CANDIDATE_001_SHA256 = "a277a5e5b4d710650df5e89713dfd23a97c0f79ff273076273eb84835f55fc19"
CANDIDATE_002_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_002.json"
AUTONOMY_AMENDMENT_PATH = PROJECT / "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_AUTONOMY_AMENDMENT_001.md"
AUTONOMY_AMENDMENT_SHA256 = "0e8dfe1bba8f1741385a955d5b47affc5cb468116815789ba2f5d92bf00558a2"
AUTONOMY_MANDATE_PATH = PROJECT / "oc3/INPUTS/OC3_AUTONOMY_MANDATE_001.json"
AUTONOMY_MANDATE_SHA256 = "4364eb22ce95316917b77f4e7dc3dabcd98a8d33fa10c887fb531ae8d49971f8"
AUTONOMY_MANIFEST_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_RESOURCE_MANIFEST_002.json"
AUTONOMY_MANIFEST_SHA256 = "6ca4360ed1b4b59161350933745192d6d2df5bbda877bb0bc0996400cad3eb46"
STANDING_AUTHORIZATION_PATH = PROJECT / "oc3/OC3_AUTONOMY_STANDING_AUTHORIZATION_001.json"
AUTONOMY_STATE_PATH = PROJECT / "oc3/OC3_AUTONOMY_STATE_001.json"
AUTONOMOUS_PERMIT_PATH = PROJECT / "oc3/AUTONOMY_PERMITS/OC3_RANGE_SIZE_PERMIT_001.json"
AUTONOMY_LEDGER_ROOT = PROJECT / "oc3/AUTONOMY_LEDGER"
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_FINAL_AUTHORIZATION_001.json"
OUTPUT_ROOT = PROJECT / "oc3/photsys_archive_range_size_probe" / STAGE_ID


class RangeSizeProbeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass
class RangeSizeCounters:
    network_requests_started: int = 0
    application_body_bytes_read: int = 0
    astronomical_data_GETs: int = 0
    real_PHOTSYS_bytes_observed: int = 0
    BRICKNAME_values_observed: int = 0
    BRICKID_values_observed: int = 0
    ROOT_values_observed: int = 0

    def object(self) -> dict[str, int]:
        return asdict(self)


def _header_values(raw_headers: list[list[str]], name: str) -> list[str]:
    target = name.lower()
    return [value for key, value in raw_headers if key.lower() == target]


def parse_content_range(values: list[str]) -> int:
    """Parse only an exact satisfied one-byte Content-Range field."""
    if not values:
        raise RangeSizeProbeError("CONTENT_RANGE_ABSENT")
    if len(values) != 1 or "," in values[0]:
        raise RangeSizeProbeError("CONTENT_RANGE_MULTIPLE")
    value = values[0]
    if value == "bytes 0-0/*":
        raise RangeSizeProbeError("CONTENT_RANGE_TOTAL_WILDCARD")
    if re.fullmatch(r"bytes \*/[0-9]+", value):
        raise RangeSizeProbeError("CONTENT_RANGE_UNSATISFIED_FORM")
    if not value.startswith("bytes "):
        raise RangeSizeProbeError("CONTENT_RANGE_UNIT_UNEXPECTED")
    match = re.fullmatch(r"bytes ([0-9]+)-([0-9]+)/(.+)", value)
    if match is None:
        raise RangeSizeProbeError("CONTENT_RANGE_MALFORMED")
    start_text, end_text, total_text = match.groups()
    if start_text != "0" or end_text != "0":
        raise RangeSizeProbeError("CONTENT_RANGE_POSITIONS_UNEXPECTED")
    if total_text == "*":
        raise RangeSizeProbeError("CONTENT_RANGE_TOTAL_WILDCARD")
    if re.fullmatch(r"[0-9]+", total_text) is None:
        raise RangeSizeProbeError("CONTENT_RANGE_TOTAL_MALFORMED")
    total = int(total_text, 10)
    if total <= int(end_text, 10):
        raise RangeSizeProbeError("CONTENT_RANGE_TOTAL_INVALID")
    return total


def validate_historical_inputs() -> dict[str, object]:
    expected_files = {
        SPEC_PATH: SPEC_SHA256,
        FAILED_REVIEW_PATH: FAILED_REVIEW_SHA256,
        HEAD_RESPONSE_PATH: HEAD_RESPONSE_SHA256,
        HEAD_TERMINAL_PATH: HEAD_TERMINAL_SHA256,
        HEAD_AUTHORIZATION_PATH: HEAD_AUTHORIZATION_SHA256,
    }
    for path, digest in expected_files.items():
        if not path.is_file() or file_sha256(path) != digest:
            raise RangeSizeProbeError("RANGE_SIZE_FROZEN_INPUT_MISMATCH")
    head_response = validate_sealed(load_canonical_json(HEAD_RESPONSE_PATH))
    head_terminal = validate_sealed(load_canonical_json(HEAD_TERMINAL_PATH))
    observed = head_response.get("response", {})
    counters = head_terminal.get("counters", {})
    if (head_response.get("state") != "DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE" or
            head_terminal.get("state") != "DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE" or
            head_response.get("budget_decision") != "NO_ARCHIVE_GET_CANDIDATE" or
            head_terminal.get("budget_decision") != "NO_ARCHIVE_GET_CANDIDATE" or
            observed.get("status") != 200 or observed.get("method") != "HEAD" or
            observed.get("literal_url") != ARCHIVE_URL or observed.get("final_url") != ARCHIVE_URL or
            observed.get("declared_content_length") is not None or
            observed.get("content_type") != "application/x-gzip" or
            observed.get("content_encoding") != "identity" or observed.get("etag") != HEAD_ETAG or
            observed.get("last_modified") is not None or counters.get("network_requests_started") != 1):
        raise RangeSizeProbeError("RANGE_SIZE_HEAD_EVIDENCE_MISMATCH")
    for key in ("application_body_bytes_read", "astronomical_data_GETs",
                "real_PHOTSYS_bytes_observed", "BRICKNAME_values_observed",
                "BRICKID_values_observed", "ROOT_values_observed"):
        if counters.get(key) != 0:
            raise RangeSizeProbeError("RANGE_SIZE_HEAD_FIREWALL_MISMATCH")
    bodies = []
    for filename, size, digest in PRESERVED_BODIES:
        path = RAW_ROOT / filename
        if not path.is_file() or path.stat().st_size != size or file_sha256(path) != digest:
            raise RangeSizeProbeError("RANGE_SIZE_PRESERVED_BODY_MISMATCH")
        bodies.append({"bytes": size, "path": str(path.relative_to(PROJECT)), "sha256": digest})
    if PARENT_BODY_MAXIMUM - HISTORICAL_MAXIMUM_BODY_BYTES != REMAINING_CONSERVATIVE_BODY_BUDGET:
        raise RangeSizeProbeError("RANGE_SIZE_BUDGET_MISMATCH")
    return {
        "application_body_bytes_read": 0,
        "astronomical_data_GETs": 0,
        "head_terminal": head_terminal["state"],
        "network_requests": 0,
        "preserved_bodies": bodies,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": "DESITARGET_ARCHIVE_RANGE_SIZE_INPUTS_VALIDATED",
    }


def exact_command(project: Path = PROJECT) -> list[str]:
    project = Path(project).resolve()
    return [
        str(project / "oc3/.venv/bin/python"),
        str(project / "oc3/oc3_photsys_archive_range_size_probe.py"),
        "--probe-desitarget-archive-range-size", "--execute-network",
        "--candidate", str(project / CANDIDATE_PATH.relative_to(PROJECT)),
        "--authorization", str(project / AUTHORIZATION_PATH.relative_to(PROJECT)),
        "--output-directory", str(project / OUTPUT_ROOT.relative_to(PROJECT)),
    ]


def exact_autonomous_command(project: Path = PROJECT) -> list[str]:
    project = Path(project).resolve()
    return [
        str(project / "oc3/.venv/bin/python"),
        str(project / "oc3/oc3_photsys_archive_range_size_probe.py"),
        "--probe-desitarget-archive-range-size", "--execute-network",
        "--candidate", str(project / CANDIDATE_002_PATH.relative_to(PROJECT)),
        "--standing-authorization", str(project / STANDING_AUTHORIZATION_PATH.relative_to(PROJECT)),
        "--autonomous-permit", str(project / AUTONOMOUS_PERMIT_PATH.relative_to(PROJECT)),
        "--autonomy-state", str(project / AUTONOMY_STATE_PATH.relative_to(PROJECT)),
        "--output-directory", str(project / OUTPUT_ROOT.relative_to(PROJECT)),
    ]


def build_candidate(implementation_aggregate: str) -> dict[str, object]:
    inputs = validate_historical_inputs()
    command = exact_command()
    return sealed({
        "accepted_content_types": list(ACCEPTED_CONTENT_TYPES),
        "budget": {
            "historical_conservative_maximum": HISTORICAL_MAXIMUM_BODY_BYTES,
            "later_acquisition_may_be_designed_at_most": REMAINING_CONSERVATIVE_BODY_BUDGET,
            "parent_body_maximum": PARENT_BODY_MAXIMUM,
            "stop_current_spec_above": REMAINING_CONSERVATIVE_BODY_BUDGET,
        },
        "candidate_state": "PENDING_HUMAN_REVIEW",
        "command_argv": command,
        "command_argv_sha256": sha256_bytes(canonical(command)),
        "content_range_contract": {
            "authoritative_complete_length_source": "CONTENT_RANGE_TOTAL",
            "content_length_is_complete_size": False,
            "exact_success_grammar": CONTENT_RANGE_GRAMMAR,
            "expected_positions": [0, 0],
            "expected_status": 206,
            "range_unit": "bytes",
        },
        "failed_provenance_review": {
            "path": str(FAILED_REVIEW_PATH.relative_to(PROJECT)),
            "sha256": FAILED_REVIEW_SHA256,
        },
        "final_authorization_path": str(AUTHORIZATION_PATH),
        "final_authorization_present": False,
        "historical_head": {
            "authorization_consumed": True,
            "authorization_path": str(HEAD_AUTHORIZATION_PATH.relative_to(PROJECT)),
            "authorization_sha256": HEAD_AUTHORIZATION_SHA256,
            "etag": HEAD_ETAG,
            "response_path": str(HEAD_RESPONSE_PATH.relative_to(PROJECT)),
            "response_sha256": HEAD_RESPONSE_SHA256,
            "resume": False,
            "terminal_path": str(HEAD_TERMINAL_PATH.relative_to(PROJECT)),
            "terminal_sha256": HEAD_TERMINAL_SHA256,
            "terminal_state": "DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE",
        },
        "implementation_aggregate": implementation_aggregate,
        "negative_capabilities": {
            "archive_acquisition": False, "archive_body_read": False,
            "automatic_resume": False, "generic_get": False, "head": False,
            "redirect": False, "retry": False, "semantic_research": False,
            "synthetic_zero_initialization": False,
        },
        "network_caps": {
            "application_body_bytes": BODY_CAP, "concurrency": CONCURRENCY,
            "redirects": REDIRECT_CAP, "requests": REQUEST_CAP, "retries": RETRY_CAP,
        },
        "preserved_bodies": inputs["preserved_bodies"],
        "request": {
            "headers": {"Accept-Encoding": "identity", "Connection": "close", "Range": RANGE_VALUE},
            "literal_url": ARCHIVE_URL, "method": "GET", "resource_count": 1,
            "resolved_commit": EXPECTED_COMMIT,
        },
        "schema_version": "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_001",
        "scope": SCOPE,
        "specification": {"path": str(SPEC_PATH.relative_to(PROJECT)), "sha256": SPEC_SHA256},
        "stage_id": STAGE_ID,
        "terminal_mapping": {
            "content_range_invalid": INCONCLUSIVE,
            "range_ignored_200": INCONCLUSIVE,
            "range_not_satisfiable_416": INCONCLUSIVE,
            "redirect_or_contract_failure": FAILED,
            "valid_206_content_range": SUCCESS,
        },
    })


def validate_historical_candidate_001(path: Path = CANDIDATE_PATH) -> dict[str, object]:
    try:
        candidate = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise RangeSizeProbeError("RANGE_SIZE_CANDIDATE_INVALID") from exc
    if (Path(path).resolve() != CANDIDATE_PATH.resolve() or
            file_sha256(path) != CANDIDATE_001_SHA256 or
            candidate.get("schema_version") !=
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_001" or
            candidate.get("candidate_state") != "PENDING_HUMAN_REVIEW"):
        raise RangeSizeProbeError("RANGE_SIZE_CANDIDATE_INVALID")
    return candidate


def build_autonomous_candidate(implementation_aggregate: str) -> dict[str, object]:
    base = validate_historical_candidate_001()
    for path, digest in ((AUTONOMY_AMENDMENT_PATH, AUTONOMY_AMENDMENT_SHA256),
                         (AUTONOMY_MANDATE_PATH, AUTONOMY_MANDATE_SHA256),
                         (AUTONOMY_MANIFEST_PATH, AUTONOMY_MANIFEST_SHA256)):
        if not path.is_file() or file_sha256(path) != digest:
            raise RangeSizeProbeError("RANGE_SIZE_AUTONOMY_INPUT_MISMATCH")
    command = exact_autonomous_command()
    preserved_keys = ("accepted_content_types", "budget", "content_range_contract",
                      "failed_provenance_review", "historical_head", "negative_capabilities",
                      "network_caps", "preserved_bodies", "request", "scope",
                      "specification", "stage_id", "terminal_mapping")
    value = {key: base[key] for key in preserved_keys}
    value.update({
        "autonomy_amendment": {"path": str(AUTONOMY_AMENDMENT_PATH.relative_to(PROJECT)),
                               "sha256": AUTONOMY_AMENDMENT_SHA256},
        "candidate_state": "PENDING_STANDING_AUTONOMY",
        "command_argv": command,
        "command_argv_sha256": sha256_bytes(canonical(command)),
        "execution_governance": {
            "authorization_basis": "STANDING_AUTONOMY_MANDATE_001",
            "mandate_path": str(AUTONOMY_MANDATE_PATH.relative_to(PROJECT)),
            "mandate_sha256": AUTONOMY_MANDATE_SHA256,
            "per_stage_human_authorization": False,
            "permit_path": str(AUTONOMOUS_PERMIT_PATH.relative_to(PROJECT)),
            "permit_type": "AUTONOMOUS_EXECUTION_PERMIT",
            "resume": False,
            "standing_authorization_path": str(STANDING_AUTHORIZATION_PATH.relative_to(PROJECT)),
            "state_path": str(AUTONOMY_STATE_PATH.relative_to(PROJECT)),
        },
        "forbidden_scope": {"p1": True, "panel_v2": True, "resolver": True},
        "git_policy": {"branch": "autopilot/photsys-zero-byte", "force_push": False,
                       "merge_main": False},
        "historical_candidate_001": {"path": str(CANDIDATE_PATH.relative_to(PROJECT)),
                                     "sha256": CANDIDATE_001_SHA256},
        "implementation_aggregate": implementation_aggregate,
        "resource_manifest": {"path": str(AUTONOMY_MANIFEST_PATH.relative_to(PROJECT)),
                              "sha256": AUTONOMY_MANIFEST_SHA256},
        "schema_version": "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_002",
        "scientific_firewall": {
            "astronomical_data_GETs": 0, "real_PHOTSYS_bytes_observed": 0,
            "BRICKNAME_values_observed": 0, "BRICKID_values_observed": 0,
            "ROOT_values_observed": 0,
        },
    })
    return sealed(value)


def validate_autonomous_candidate(path: Path = CANDIDATE_002_PATH) -> dict[str, object]:
    try:
        candidate = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise RangeSizeProbeError("RANGE_SIZE_AUTONOMY_CANDIDATE_INVALID") from exc
    if candidate != build_autonomous_candidate(implementation_hash(PROJECT)):
        raise RangeSizeProbeError("RANGE_SIZE_AUTONOMY_CANDIDATE_INVALID")
    if STANDING_AUTHORIZATION_PATH.exists():
        raise RangeSizeProbeError("PREMATURE_STANDING_AUTONOMY_AUTHORIZATION")
    if AUTONOMOUS_PERMIT_PATH.exists():
        raise RangeSizeProbeError("PREMATURE_AUTONOMOUS_PERMIT")
    return candidate


def validate_candidate(path: Path = CANDIDATE_PATH,
                       *, require_authorization_absent: bool = True) -> dict[str, object]:
    if Path(path).resolve() == CANDIDATE_002_PATH.resolve():
        return validate_autonomous_candidate(path)
    candidate = validate_historical_candidate_001(path)
    if require_authorization_absent and AUTHORIZATION_PATH.exists():
        raise RangeSizeProbeError("PREMATURE_RANGE_SIZE_AUTHORIZATION")
    return candidate


def validate_authorization(candidate_path: Path, authorization_path: Path,
                           command_argv_sha256: str) -> dict[str, object]:
    candidate = validate_candidate(candidate_path, require_authorization_absent=False)
    try:
        authorization = validate_sealed(load_canonical_json(authorization_path))
    except Exception as exc:
        raise RangeSizeProbeError("RANGE_SIZE_FINAL_AUTHORIZATION_INVALID") from exc
    required = {"authorization_id", "authorization_state", "authorized", "candidate_sha256",
                "command_argv_sha256", "resume", "scope", "sealed", "stage_id"}
    if (set(authorization) != required or authorization.get("authorized") is not True or
            authorization.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            authorization.get("candidate_sha256") != file_sha256(candidate_path) or
            authorization.get("command_argv_sha256") != command_argv_sha256 or
            authorization.get("command_argv_sha256") != candidate["command_argv_sha256"] or
            authorization.get("resume") is not False or authorization.get("scope") != SCOPE or
            authorization.get("stage_id") != STAGE_ID):
        raise RangeSizeProbeError("RANGE_SIZE_FINAL_AUTHORIZATION_INVALID")
    return authorization


def dry_run() -> dict[str, object]:
    validate_historical_inputs()
    validate_candidate()
    return {
        "application_body_bytes_read": 0,
        "astronomical_data_GETs": 0,
        "method": "GET",
        "network_requests": 0,
        "range": RANGE_VALUE,
        "request_cap": REQUEST_CAP,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": READY,
    }


def autonomous_dry_run() -> dict[str, object]:
    validate_historical_inputs()
    validate_autonomous_candidate()
    return {
        "application_body_bytes_read": 0,
        "astronomical_data_GETs": 0,
        "execution_governance": "AUTONOMOUS_EXECUTION_PERMIT",
        "method": "GET",
        "network_requests": 0,
        "permit_state": "MANDATE_NOT_ACTIVE",
        "range": RANGE_VALUE,
        "request_cap": REQUEST_CAP,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": READY,
    }


class RangeSizeOnlyTransport:
    """One frozen Range GET that captures headers and never reads a body."""
    __slots__ = ("counters", "timeout_seconds", "last_metadata")

    def __init__(self, counters: RangeSizeCounters, timeout_seconds: int = 30):
        self.counters = counters
        self.timeout_seconds = timeout_seconds
        self.last_metadata: dict[str, object] | None = None

    def probe_size(self) -> dict[str, object]:
        parsed = urlsplit(ARCHIVE_URL)
        if (parsed.scheme != "https" or parsed.hostname != "codeload.github.com" or
                parsed.query or parsed.fragment or
                parsed.path != f"/desihub/desitarget/tar.gz/{EXPECTED_COMMIT}"):
            raise RangeSizeProbeError("RANGE_SIZE_RESOURCE_IDENTITY_INVALID")
        if self.counters.network_requests_started >= REQUEST_CAP:
            raise RangeSizeProbeError("RANGE_SIZE_REQUEST_CAP_VIOLATION")
        self.counters.network_requests_started += 1
        connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                  timeout=self.timeout_seconds)
        connection.request("GET", parsed.path, headers={
            "Accept-Encoding": "identity",
            "Connection": "close",
            "Range": RANGE_VALUE,
            "User-Agent": "OC3-PHOTSYS-desitarget-range-size-probe/1",
        })
        response = connection.getresponse()
        raw_headers = [[key, value] for key, value in response.getheaders()]
        content_encoding_values = _header_values(raw_headers, "content-encoding")
        content_type_values = _header_values(raw_headers, "content-type")
        etag_values = _header_values(raw_headers, "etag")
        last_modified_values = _header_values(raw_headers, "last-modified")
        metadata = {
            "application_body_bytes_read": 0,
            "content_encoding_values": content_encoding_values,
            "content_length_values": _header_values(raw_headers, "content-length"),
            "content_range_values": _header_values(raw_headers, "content-range"),
            "content_type_values": content_type_values,
            "etag_values": etag_values,
            "final_url": ARCHIVE_URL,
            "last_modified_values": last_modified_values,
            "literal_url": ARCHIVE_URL,
            "method": "GET",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "range_request": RANGE_VALUE,
            "raw_headers": raw_headers,
            "status": response.status,
        }
        self.last_metadata = metadata
        connection.close()  # Deliberately no response.read() call.
        return metadata


def classify_response(metadata: dict[str, object], counters: RangeSizeCounters) -> dict[str, object]:
    if counters.application_body_bytes_read != 0 or metadata.get("application_body_bytes_read") != 0:
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "RANGE_BODY_READ_FIREWALL_VIOLATION",
                "state": FAILED}
    if counters.network_requests_started != 1:
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "RANGE_SIZE_REQUEST_CAP_VIOLATION",
                "state": FAILED}
    status = metadata.get("status")
    if status == 200:
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "RANGE_IGNORED_200", "state": INCONCLUSIVE}
    if status in REDIRECT_STATUSES:
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "RANGE_REDIRECT_FORBIDDEN", "state": FAILED}
    if status == 416:
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "RANGE_NOT_SATISFIABLE_416",
                "state": INCONCLUSIVE}
    if status != 206:
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "RANGE_HTTP_STATUS_UNEXPECTED", "state": FAILED}

    encoding_values = metadata.get("content_encoding_values")
    if not isinstance(encoding_values, list) or len(encoding_values) > 1 or (
            encoding_values and encoding_values[0].lower() != "identity"):
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "RANGE_CONTENT_ENCODING_MISMATCH", "state": FAILED}
    type_values = metadata.get("content_type_values")
    if not isinstance(type_values, list) or len(type_values) != 1 or (
            type_values[0].split(";", 1)[0].strip().lower() not in ACCEPTED_CONTENT_TYPES):
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "RANGE_CONTENT_TYPE_MISMATCH", "state": FAILED}
    etag_values = metadata.get("etag_values")
    if not isinstance(etag_values, list) or len(etag_values) > 1 or (
            etag_values and etag_values[0] != HEAD_ETAG):
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "REPRESENTATION_IDENTITY_MISMATCH", "state": FAILED}

    try:
        total = parse_content_range(metadata.get("content_range_values", []))
    except RangeSizeProbeError as exc:
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": exc.code, "state": INCONCLUSIVE}
    length_values = metadata.get("content_length_values")
    if not isinstance(length_values, list) or len(length_values) > 1 or (
            length_values and (re.fullmatch(r"[0-9]+", length_values[0]) is None or
                               int(length_values[0], 10) != 1)):
        return {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                "complete_length": None, "reason": "PARTIAL_CONTENT_LENGTH_MISMATCH", "state": FAILED}
    decision = ("LATER_ARCHIVE_ACQUISITION_MAY_BE_DESIGNED"
                if total <= REMAINING_CONSERVATIVE_BODY_BUDGET
                else "STOP_CURRENT_32_MIB_SPEC_CANNOT_ACCOMMODATE")
    return {"budget_decision": decision, "complete_length": total,
            "reason": "VALID_206_CONTENT_RANGE", "state": SUCCESS}


def _execute_after_governance(output_directory: Path, *,
                              transport_factory: Callable[[RangeSizeCounters], RangeSizeOnlyTransport]
                              = RangeSizeOnlyTransport) -> dict[str, object]:
    validate_historical_inputs()
    output = Path(output_directory).resolve()
    if output != OUTPUT_ROOT.resolve() or output.exists():
        raise RangeSizeProbeError("RANGE_SIZE_RERUN_OR_RESUME_FORBIDDEN")
    output.mkdir(parents=True)
    counters = RangeSizeCounters()
    transport = transport_factory(counters)
    metadata: dict[str, object] | None = None
    try:
        metadata = transport.probe_size()
        outcome = classify_response(metadata, counters)
    except RangeSizeProbeError as exc:
        outcome = {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                   "complete_length": None, "reason": exc.code, "state": FAILED}
    except Exception:
        outcome = {"budget_decision": "NO_ARCHIVE_ACQUISITION_CANDIDATE",
                   "complete_length": None, "reason": "RANGE_TRANSPORT_ERROR", "state": FAILED}
    receipt = sealed({"counters": counters.object(), "outcome": outcome,
                      "response": metadata if metadata is not None else transport.last_metadata,
                      "stage_id": STAGE_ID})
    write_json_immutable(output / "RANGE_RESPONSE.json", receipt)
    terminal = sealed({
        "application_body_bytes_read": counters.application_body_bytes_read,
        "budget_decision": outcome["budget_decision"],
        "complete_length": outcome["complete_length"],
        "counters": counters.object(),
        "reason": outcome["reason"],
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": outcome["state"],
    })
    write_json_immutable(output / "TERMINAL.json", terminal)
    return terminal


def execute(candidate_path: Path, authorization_path: Path, command_argv_sha256: str,
            output_directory: Path, *,
            transport_factory: Callable[[RangeSizeCounters], RangeSizeOnlyTransport] = RangeSizeOnlyTransport
            ) -> dict[str, object]:
    """Historical candidate-001 execution path; requires FINAL_HUMAN_AUTHORIZATION."""
    validate_historical_candidate_001(candidate_path)
    validate_authorization(candidate_path, authorization_path, command_argv_sha256)
    return _execute_after_governance(output_directory, transport_factory=transport_factory)


def execute_autonomous(candidate_path: Path, standing_authorization_path: Path,
                       permit_path: Path, state_path: Path, command_argv_sha256: str,
                       output_directory: Path, *, consumed_at_utc: str,
                       transitioned_at_utc: str,
                       transport_factory: Callable[[RangeSizeCounters], RangeSizeOnlyTransport]
                       = RangeSizeOnlyTransport) -> dict[str, object]:
    """Candidate-002 path with standing authorization and a single-use permit."""
    candidate = build_autonomous_candidate(implementation_hash(PROJECT))
    try:
        on_disk = validate_sealed(load_canonical_json(candidate_path))
    except Exception as exc:
        raise RangeSizeProbeError("RANGE_SIZE_AUTONOMY_CANDIDATE_INVALID") from exc
    if on_disk != candidate or on_disk.get("command_argv_sha256") != command_argv_sha256:
        raise RangeSizeProbeError("RANGE_SIZE_AUTONOMY_CANDIDATE_INVALID")
    from .autonomy_governor import (AUTONOMY_LEDGER_ROOT as GOVERNOR_LEDGER_ROOT,
                                    consume_permit, transition_state, validate_permit)
    consumption_directory = GOVERNOR_LEDGER_ROOT / "PERMIT_CONSUMPTION"
    validate_permit(permit_path, candidate_path=candidate_path, state_path=state_path,
                    standing_authorization_path=standing_authorization_path,
                    consumption_directory=consumption_directory)
    # Consumption intent is immutable and precedes the material operation so a
    # crash cannot make a copied permit replayable.
    consume_permit(permit_path, candidate_path=candidate_path, state_path=state_path,
                   standing_authorization_path=standing_authorization_path,
                   consumption_directory=consumption_directory,
                   consumed_at_utc=consumed_at_utc)
    terminal = _execute_after_governance(output_directory, transport_factory=transport_factory)
    transition_state(
        state_path=state_path, candidate_path=candidate_path, permit_path=permit_path,
        terminal_sha256=file_sha256(Path(output_directory) / "TERMINAL.json"),
        terminal_state=str(terminal["state"]),
        request_delta=int(terminal["counters"]["network_requests_started"]),
        body_delta=int(terminal["application_body_bytes_read"]),
        ledger_directory=GOVERNOR_LEDGER_ROOT,
        transitioned_at_utc=transitioned_at_utc,
        reason="AUTONOMOUS_RANGE_SIZE_EXECUTION_COMPLETED")
    return terminal
