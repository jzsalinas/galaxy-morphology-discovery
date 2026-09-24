"""Closed provenance and semantic-review boundaries for documentary evidence."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from .cross_observer_grouping import GroupingError

HASHED_RESPONSE_SNAPSHOT = "HASHED_RESPONSE_SNAPSHOT"
REVISION_PINNED_RESOURCE = "REVISION_PINNED_RESOURCE"
CAPTURE_MODES = (HASHED_RESPONSE_SNAPSHOT, REVISION_PINNED_RESOURCE)

ACQUISITION_TERMINAL = "DOCUMENTARY_EVIDENCE_ACQUIRED_PENDING_OFFLINE_SEMANTIC_REVIEW"
DOCUMENTARY_REVIEW_OUTCOMES = (
    "DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE",
    "DOCUMENTARY_SOURCE_METADATA_PILOT_INCONCLUSIVE",
    "DOCUMENTARY_SOURCE_METADATA_CONFLICT",
)
MISSION_TERMINALS = (
    "CROSS_OBSERVER_GROUPING_SUPPORTED_FOR_SPLITS_AND_REPLICATION",
    "CROSS_OBSERVER_SPLIT_SAFETY_SUPPORTED_PAIRING_UNRESOLVED",
    "CROSS_OBSERVER_GROUPING_EVIDENCE_INCONCLUSIVE",
    "CROSS_OBSERVER_GROUPING_STRATEGY_REJECTED",
)
REQUIRED_CLAIMS = (
    "CATALOG_SOURCE_IDENTITY",
    "BRICK_PRIMARY_SEMANTICS",
    "NORTH_SOUTH_PROCESSING_DOMAINS",
    "RESOLVED_CATALOG_NOT_EQUIVALENCE_MAP",
    "ASTROMETRIC_FIELD_SEMANTICS",
    "CALIBRATION_ERROR_OMITTED_FROM_IVARS",
    "GAIA_DR2_ASTROMETRIC_PROVENANCE",
    "REGIONAL_DATALAB_TABLE_AVAILABILITY",
    "CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS",
    "BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD",
)
CLAIM_STATES = ("SUPPORTED", "INCONCLUSIVE", "CONFLICT")


def validate_capture_contract(resource: Mapping[str, object]) -> str:
    """Validate capture semantics without inferring upstream immutability."""
    if "immutable_revision_required" in resource:
        raise GroupingError("BOOLEAN_UPSTREAM_IMMUTABILITY_FORBIDDEN")
    mode = resource.get("evidence_capture_mode")
    revision = resource.get("revision_identity")
    if mode == HASHED_RESPONSE_SNAPSHOT:
        if revision is not None:
            raise GroupingError("SNAPSHOT_REVISION_IDENTITY_FORBIDDEN")
        return mode
    if mode == REVISION_PINNED_RESOURCE:
        if (not isinstance(revision, dict) or set(revision) !=
                {"authority", "identifier", "verification_method"} or
                any(not isinstance(revision[key], str) or not revision[key].strip()
                    for key in revision)):
            raise GroupingError("PINNED_REVISION_IDENTITY_REQUIRED")
        return mode
    raise GroupingError("EVIDENCE_CAPTURE_MODE_INVALID")


def validate_transport_evidence(record: Mapping[str, object]) -> None:
    required = {
        "application_body_bytes", "capture_mode", "content_length",
        "content_type", "etag", "final_url", "last_modified",
        "requested_url", "resource_id", "retrieved_at_utc", "sha256", "status",
    }
    if set(record) != required:
        raise GroupingError("TRANSPORT_EVIDENCE_SCHEMA_INVALID")
    if record["capture_mode"] not in CAPTURE_MODES:
        raise GroupingError("EVIDENCE_CAPTURE_MODE_INVALID")
    if (not isinstance(record["resource_id"], str) or not record["resource_id"] or
            not isinstance(record["requested_url"], str) or
            not isinstance(record["final_url"], str) or
            type(record["status"]) is not int or
            type(record["application_body_bytes"]) is not int or
            record["application_body_bytes"] < 0 or
            not isinstance(record["content_type"], str) or
            not isinstance(record["retrieved_at_utc"], str) or
            not record["retrieved_at_utc"].endswith("Z") or
            not isinstance(record["sha256"], str) or len(record["sha256"]) != 64):
        raise GroupingError("TRANSPORT_EVIDENCE_VALUE_INVALID")
    if record["content_length"] is not None and (
            type(record["content_length"]) is not int or record["content_length"] < 0):
        raise GroupingError("TRANSPORT_EVIDENCE_VALUE_INVALID")
    for key in ("etag", "last_modified"):
        if record[key] is not None and not isinstance(record[key], str):
            raise GroupingError("TRANSPORT_EVIDENCE_VALUE_INVALID")


def validate_local_snapshot(path: Path, expected_sha256: str) -> None:
    from .cross_observer_grouping import file_sha256

    path = Path(path)
    if (not path.is_file() or file_sha256(path) != expected_sha256 or
            path.stat().st_mode & 0o222):
        raise GroupingError("LOCAL_SNAPSHOT_IMMUTABILITY_INVALID")


def validate_documentary_semantic_review(*, claims: Mapping[str, str], outcome: str,
                                         source_rows_read: int,
                                         photsys_scientific_values_read: int,
                                         acquisition_terminal: str) -> str:
    if source_rows_read != 0:
        raise GroupingError("DOCUMENTARY_REVIEW_SOURCE_ROWS_FORBIDDEN")
    if photsys_scientific_values_read != 0:
        raise GroupingError("DOCUMENTARY_REVIEW_PHOTSYS_VALUES_FORBIDDEN")
    if acquisition_terminal != ACQUISITION_TERMINAL:
        raise GroupingError("DOCUMENTARY_ACQUISITION_TERMINAL_INVALID")
    if acquisition_terminal in MISSION_TERMINALS:
        raise GroupingError("DOCUMENTARY_ACQUISITION_MISSION_TERMINAL_FORBIDDEN")
    if tuple(claims) != REQUIRED_CLAIMS or any(value not in CLAIM_STATES for value in claims.values()):
        raise GroupingError("DOCUMENTARY_CLAIM_MATRIX_INCOMPLETE")
    if outcome not in DOCUMENTARY_REVIEW_OUTCOMES:
        raise GroupingError("DOCUMENTARY_REVIEW_OUTCOME_INVALID")
    if outcome == DOCUMENTARY_REVIEW_OUTCOMES[0] and any(value != "SUPPORTED" for value in claims.values()):
        raise GroupingError("DOCUMENTARY_PASS_REQUIRES_ALL_CLAIMS_SUPPORTED")
    return outcome


def assert_acquisition_cannot_finalize_grouping(terminal: str) -> None:
    if terminal != ACQUISITION_TERMINAL or terminal in MISSION_TERMINALS:
        raise GroupingError("DOCUMENTARY_ACQUISITION_MISSION_TERMINAL_FORBIDDEN")
