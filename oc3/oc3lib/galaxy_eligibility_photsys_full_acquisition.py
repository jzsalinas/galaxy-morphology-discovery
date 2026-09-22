"""Prospective, separately authorized PHOTSYS full-file byte acquisition.

Candidate construction and validation are offline.  A network transport is
constructed only after an exact final authorization has been validated.  This
stage preserves provider bytes; it contains no FITS table-value decoder.
"""
from __future__ import annotations

import hashlib
import http.client
import os
from pathlib import Path
from urllib.parse import urlsplit

from .core import canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    PHOTSYSProbeError, PROJECT, file_sha256, load_canonical_json, sealed,
    sha256_bytes, validate_sealed, write_json_immutable,
)
from .galaxy_eligibility_photsys_physical_correction import (
    REVIEWED_CONTRACT_PATH, validate_reviewed_contract,
)


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001"
SCOPE = "PHOTSYS_FULL_FILE_BYTE_PRESERVATION_ONLY"
CANDIDATE_STATE = "PENDING_HUMAN_REVIEW"
READY = "PHOTSYS_FULL_ACQUISITION_CANDIDATE_VALID_FOR_HUMAN_REVIEW"
SUCCESS = "PHOTSYS_FULL_FILE_BYTES_ACQUIRED"
PARTIAL = "PHOTSYS_FULL_FILE_ACQUISITION_PARTIAL"
TARGET_FILENAME = "survey-bricks-dr9-randoms-0.48.0.fits"
EXPECTED_BODY_BYTES = 52_323_840
STARTING_REQUESTS = 8
STARTING_BODY_BYTES = 273_886
PRIMARY_GETS = 1
AUTOMATIC_RETRIES = 0
CONCURRENCY = 1

CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_FULL_ACQUISITION_CANDIDATE_001.json"
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_FULL_ACQUISITION_FINAL_AUTHORIZATION_001.json"
OUTPUT_ROOT = PROJECT / "oc3/photsys_authority_full_acquisition" / STAGE_ID
PUBLISHED_PATH = OUTPUT_ROOT / "RAW_IMMUTABLE" / TARGET_FILENAME
STAGING_PATH = OUTPUT_ROOT / "STAGING" / (TARGET_FILENAME + ".partial")
TERMINAL_PATH = OUTPUT_ROOT / "OC3_PHOTSYS_FULL_ACQUISITION_TERMINAL.json"
CHECKPOINT_PATH = OUTPUT_ROOT / "OC3_PHOTSYS_FULL_ACQUISITION_CHECKPOINT.json"
LOG_PATH = OUTPUT_ROOT / "OC3_PHOTSYS_FULL_ACQUISITION_RUN.log"


def exact_command(project: Path = PROJECT) -> list[str]:
    project = Path(project).resolve()
    return [
        str(project / "oc3/.venv/bin/python"),
        str(project / "oc3/oc3_galaxy_eligibility_photsys_full_acquisition.py"),
        "--acquire", "--execute-network",
        "--candidate", str(project / CANDIDATE_PATH.relative_to(PROJECT)),
        "--authorization", str(project / AUTHORIZATION_PATH.relative_to(PROJECT)),
        "--output-directory", str(project / OUTPUT_ROOT.relative_to(PROJECT)),
        "--expected-body-bytes", str(EXPECTED_BODY_BYTES),
        "--primary-get-count", str(PRIMARY_GETS),
        "--automatic-retries", str(AUTOMATIC_RETRIES),
        "--concurrency", str(CONCURRENCY),
    ]


def build_candidate(implementation_aggregate: str) -> dict[str, object]:
    reviewed = validate_reviewed_contract()
    if (reviewed.get("file_size") != EXPECTED_BODY_BYTES or
            reviewed.get("first_table_data_byte") != 11520 or
            reviewed.get("maximum_probe_byte") != 11519 or
            reviewed.get("full_fits_gets") != 0):
        raise PHOTSYSProbeError("REVIEWED_PHYSICAL_CONTRACT_NOT_ACQUISITION_READY")
    structural = reviewed["physical_contract"]
    projection = structural["selective_projection"]
    return sealed({
        "acquisition_purpose": "LOCAL_IMMUTABLE_AUTHORITY_PRESERVATION",
        "acquisition_value_boundary": {
            "all_column_value_observation_authorized": False,
            "full_file_byte_preservation_authorized_by_candidate": False,
            "statement": "FULL_FILE_BYTE_PRESERVATION != ALL_COLUMN_VALUE_OBSERVATION",
        },
        "candidate_state": CANDIDATE_STATE,
        "command_argv": exact_command(),
        "expected_representation": reviewed["http"],
        "final_authorization_path": str(AUTHORIZATION_PATH),
        "final_authorization_present": False,
        "implementation_aggregate": implementation_aggregate,
        "offline_selective_validator_design": {
            "aggregate_counts": ["N", "S", "blank", "missing", "invalid", "conflict"],
            "allowed_value_fields": ["BRICKNAME", "BRICKID", "PHOTSYS"],
            "forbidden_value_fields": [
                row["name"] for row in structural["column_schema"]
                if row["name"] not in ("BRICKNAME", "BRICKID", "PHOTSYS")
            ],
            "full_file_integrity_required": True,
            "global_brick_identity_join": "EXACT",
            "panel_selection": False,
            "publish_identity_to_photsys_authority": True,
            "required_projection": projection,
            "row_count": structural["row_count"],
            "unique_constraints": ["BRICKNAME", "BRICKID", "BRICKNAME_BRICKID_PAIR"],
            "valid_photsys_bytes": ["N", "S", " "],
        },
        "publication": {
            "immutable": True, "mode": "0444", "overwrite": False,
            "sha256": True, "staging_first": True,
        },
        "request_plan": {
            "automatic_retries": AUTOMATIC_RETRIES,
            "concurrency": CONCURRENCY,
            "identity_head": 0,
            "primary_gets": PRIMARY_GETS,
            "separate_resume_authorization_required": True,
            "stage_body_cap": EXPECTED_BODY_BYTES,
            "stage_request_cap": PRIMARY_GETS,
        },
        "resource": {
            "expected_content_length": EXPECTED_BODY_BYTES,
            "expected_row_count": 662174,
            "expected_row_width": 79,
            "filename": TARGET_FILENAME,
            "literal_url": reviewed["literal_url"],
            "required_projection": ["BRICKNAME", "BRICKID", "PHOTSYS"],
        },
        "reviewed_physical_contract": {
            "path": str(REVIEWED_CONTRACT_PATH.relative_to(PROJECT)),
            "sha256": file_sha256(REVIEWED_CONTRACT_PATH),
        },
        "schema_version": "OC3_PHOTSYS_FULL_ACQUISITION_CANDIDATE_001",
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "starting_cumulative": {
            "body_bytes": STARTING_BODY_BYTES, "network_requests": STARTING_REQUESTS,
        },
        "success_terminal": SUCCESS,
    })


def validate_candidate(path: Path = CANDIDATE_PATH, *,
                       require_authorization_absent: bool = True) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    expected = build_candidate(implementation_hash(PROJECT))
    if value != expected:
        raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_CANDIDATE_INVALID")
    if require_authorization_absent and AUTHORIZATION_PATH.exists():
        raise PHOTSYSProbeError("PREMATURE_FINAL_AUTHORIZATION_PRESENT")
    return value


def validate_candidate_offline(path: Path = CANDIDATE_PATH) -> dict[str, object]:
    value = validate_candidate(path)
    return {
        "expected_body_bytes": value["resource"]["expected_content_length"],
        "final_authorization_present": False,
        "network_requests": 0,
        "stage_id": STAGE_ID,
        "state": READY,
    }


def validate_authorization(path: Path, candidate_path: Path,
                           command_argv_sha256: str) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    allowed = {
        "authorization_id", "authorization_state", "authorized", "candidate_sha256",
        "command_argv_sha256", "resume", "scope", "sealed", "stage_id",
    }
    if (set(value) != allowed or value.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            value.get("authorized") is not True or value.get("resume") is not False or
            value.get("scope") != SCOPE or value.get("stage_id") != STAGE_ID or
            value.get("candidate_sha256") != file_sha256(candidate_path) or
            value.get("command_argv_sha256") != command_argv_sha256):
        raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_AUTHORIZATION_INVALID")
    return value


class FullFileTransport:
    """One literal GET, streamed directly into a private staging file."""

    def __init__(self, literal_url: str):
        self.literal_url = literal_url
        self.requests_started = 0
        self.body_bytes = 0

    def download(self, destination: Path, expected: dict[str, object]) -> dict[str, object]:
        if self.requests_started != 0:
            raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_REQUEST_CAP")
        parsed = urlsplit(self.literal_url)
        if parsed.scheme != "https" or parsed.hostname != "portal.nersc.gov":
            raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_URL_INVALID")
        connection = http.client.HTTPSConnection(parsed.hostname, timeout=60)
        self.requests_started = 1
        try:
            connection.request("GET", parsed.path, headers={"Accept-Encoding": "identity"})
            response = connection.getresponse()
            headers = {key.lower(): value.strip() for key, value in response.getheaders()}
            if (response.status != 200 or headers.get("content-encoding", "identity") != "identity" or
                    int(headers.get("content-length", "-1")) != EXPECTED_BODY_BYTES or
                    headers.get("etag") != expected.get("etag") or
                    headers.get("last-modified") != expected.get("last_modified")):
                raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_REPRESENTATION_DRIFT")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_STAGING_CONFLICT")
            digest = hashlib.sha256()
            with destination.open("xb") as stream:
                while True:
                    chunk = response.read(min(1024 * 1024, EXPECTED_BODY_BYTES - self.body_bytes + 1))
                    if not chunk:
                        break
                    self.body_bytes += len(chunk)
                    if self.body_bytes > EXPECTED_BODY_BYTES:
                        raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_BODY_CAP")
                    digest.update(chunk)
                    stream.write(chunk)
                stream.flush(); os.fsync(stream.fileno())
            if self.body_bytes != EXPECTED_BODY_BYTES:
                raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_LENGTH_MISMATCH")
            return {"body_bytes": self.body_bytes, "etag": headers.get("etag"),
                    "last_modified": headers.get("last-modified"),
                    "sha256": digest.hexdigest(), "status": response.status}
        finally:
            connection.close()


def execute(candidate_path: Path, authorization_path: Path, command_argv_sha256: str,
            output_directory: Path, transport_factory=FullFileTransport) -> dict[str, object]:
    candidate = validate_candidate(candidate_path, require_authorization_absent=False)
    validate_authorization(authorization_path, candidate_path, command_argv_sha256)
    if Path(output_directory).resolve() != OUTPUT_ROOT.resolve():
        raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_OUTPUT_PATH_INVALID")
    if OUTPUT_ROOT.exists() and any(OUTPUT_ROOT.iterdir()):
        raise PHOTSYSProbeError("SEPARATE_RESUME_AUTHORIZATION_REQUIRED")
    transport = transport_factory(candidate["resource"]["literal_url"])
    evidence = transport.download(STAGING_PATH, candidate["expected_representation"])
    write_json_immutable(CHECKPOINT_PATH, sealed({
        "candidate_sha256": file_sha256(candidate_path), "evidence": evidence,
        "stage_id": STAGE_ID, "table_cell_values_decoded": 0,
    }))
    PUBLISHED_PATH.parent.mkdir(parents=True, exist_ok=True)
    os.replace(STAGING_PATH, PUBLISHED_PATH)
    os.chmod(PUBLISHED_PATH, 0o444)
    terminal = sealed({
        "body_bytes": evidence["body_bytes"], "file_sha256": evidence["sha256"],
        "full_file_byte_preserved": True, "network_requests_started": transport.requests_started,
        "published_path": str(PUBLISHED_PATH), "stage_id": STAGE_ID, "state": SUCCESS,
        "table_cell_values_decoded": 0,
    })
    write_json_immutable(TERMINAL_PATH, terminal)
    return terminal
