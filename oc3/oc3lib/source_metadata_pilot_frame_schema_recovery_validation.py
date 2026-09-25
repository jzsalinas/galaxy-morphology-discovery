"""Closed validator for supervised, offline pilot-frame schema recovery."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed
from .source_metadata_pilot_frame_schema_recovery import (
    ACTION_KIND, ALLOWED_COLUMN_ACCESS_MISMATCH, DIAGNOSTIC_SCHEMA,
    FRAME_SELECTION_INTEGRITY_FAILURE, GLOBAL_IDENTITY_INTEGRITY_FAILURE,
    IDENTITY_DECODE_FAILURE, PHYSICAL_SCHEMA_CONTRACT_MISMATCH, SCOPE, STAGE_ID,
    STREAM_CAPTURE_CAP, WORKER_RUNTIME_FAILURE,
)
from .provider_physical_contracts import PHYSICAL_CONTRACT_HASHES, PhysicalRole

SPEC = PROJECT / "OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_FIRST_ACTION_SPEC_001.md"
CANDIDATE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_CANDIDATE_001.json"
RECEIPT = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_CANDIDATE_VALIDATION_001.json"
PERMIT = PROJECT / "oc3/SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_AUTONOMY_PERMITS/OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_PERMIT_001.json"
AUTHORIZATION = PROJECT / "oc3/OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_STANDING_AUTHORIZATION_001.json"
STATE = PROJECT / "oc3/OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_AUTONOMY_STATE_001.json"
OUTPUT = PROJECT / "oc3/source_metadata_pilot_frame_schema_recovery/OC3-SOURCE-METADATA-PILOT-FRAME-SCHEMA-RECOVERY-001"
FRAME = OUTPUT / "PILOT_FRAME.json"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
SUPERVISOR = PROJECT / "oc3/oc3_source_metadata_pilot_frame_schema_recovery_supervisor.py"
WORKER = PROJECT / "oc3/oc3_source_metadata_pilot_frame_schema_recovery_worker.py"
IMPLEMENTATION_FILES = (
    "OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_FIRST_ACTION_SPEC_001.md",
    "oc3/oc3_source_metadata_pilot_frame_schema_recovery_supervisor.py",
    "oc3/oc3_source_metadata_pilot_frame_schema_recovery_worker.py",
    "oc3/oc3lib/source_metadata_pilot_frame_schema_recovery.py",
    "oc3/oc3lib/source_metadata_pilot_frame_schema_recovery_validation.py",
    "oc3/oc3lib/provider_physical_contracts.py",
)
EXPECTED_INPUTS = (
    ("oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz", "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f"),
    ("oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz", "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb"),
    ("oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz", "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f"),
    ("oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv", "147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6"),
)


class RecoveryValidationError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({path: file_sha256(PROJECT / path) for path in IMPLEMENTATION_FILES}))


def expected_worker_command() -> list[str]:
    return [str(EXECUTABLE), str(WORKER), "--run-schema-correct-worker", "--candidate", str(CANDIDATE),
            "--output", str(FRAME)]


def expected_supervisor_argv() -> list[str]:
    return [str(EXECUTABLE), str(SUPERVISOR), "--recover-schema-correct-pilot-frame", "--candidate", str(CANDIDATE),
            "--permit", str(PERMIT), "--standing-authorization", str(AUTHORIZATION),
            "--autonomy-state", str(STATE), "--output-directory", str(OUTPUT)]


def validate_candidate(path: Path = CANDIDATE) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    zero = ("network_requests", "application_body_bytes", "source_rows_read", "datalab_accesses",
            "matching_operations", "PHOTSYS_reads", "morphology_accesses", "object_group_ids_created",
            "split_group_ids_created", "targets_materialized", "holdouts_materialized")
    if (value.get("schema_version") != "OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_CANDIDATE_001" or
            value.get("stage_id") != STAGE_ID or value.get("scope") != SCOPE or
            value.get("action_kind") != ACTION_KIND or any(value.get(key) != 0 for key in zero) or
            value.get("preceding_failure_class") != "IMPLEMENTATION_SCHEMA_CASE_MISMATCH" or
            value.get("historical_predecessor_technical_cause") != "UNKNOWN" or
            value.get("worker_launches") != 1 or
            value.get("stream_capture_cap_bytes") != STREAM_CAPTURE_CAP or
            value.get("diagnostic_schema") != DIAGNOSTIC_SCHEMA or
            value.get("resume") is not False):
        raise RecoveryValidationError("FRAME_RECOVERY_CANDIDATE_INVALID")
    expected_contracts = [
        {"role": role.value, "sha256": PHYSICAL_CONTRACT_HASHES[role]}
        for role in (PhysicalRole.ROOT_SUMMARY, PhysicalRole.NORTH_SUMMARY, PhysicalRole.SOUTH_SUMMARY)
    ]
    if value.get("physical_contract_bindings") != expected_contracts:
        raise RecoveryValidationError("PHYSICAL_CONTRACT_BINDING_INVALID")
    expected_taxonomy = [PHYSICAL_SCHEMA_CONTRACT_MISMATCH, ALLOWED_COLUMN_ACCESS_MISMATCH,
        IDENTITY_DECODE_FAILURE, GLOBAL_IDENTITY_INTEGRITY_FAILURE,
        FRAME_SELECTION_INTEGRITY_FAILURE, WORKER_RUNTIME_FAILURE]
    if value.get("worker_error_taxonomy") != expected_taxonomy:
        raise RecoveryValidationError("WORKER_ERROR_TAXONOMY_INVALID")
    supervisor, worker = expected_supervisor_argv(), expected_worker_command()
    if (value.get("command_argv") != supervisor or value.get("command_argv_sha256") != sha256_bytes(canonical(supervisor)) or
            value.get("worker_command") != worker or value.get("worker_command_sha256") != sha256_bytes(canonical(worker))):
        raise RecoveryValidationError("COMMAND_BINDING_INVALID")
    if value.get("implementation_aggregate") != implementation_aggregate():
        raise RecoveryValidationError("IMPLEMENTATION_BINDING_INVALID")
    expected = [{"path": path, "sha256": digest} for path, digest in EXPECTED_INPUTS]
    if value.get("input_bindings") != expected:
        raise RecoveryValidationError("FRAME_RECOVERY_INPUT_BINDING_INVALID")
    for binding in expected:
        source = PROJECT / binding["path"]
        if not source.is_file() or file_sha256(source) != binding["sha256"]:
            raise RecoveryValidationError("FRAME_RECOVERY_INPUT_MISMATCH")
    return value


def validate_invocation(candidate: dict[str, object], observed: Sequence[str], *, worker: bool = False) -> None:
    expected = candidate["worker_command"] if worker else candidate["command_argv"]
    expected_sha = candidate["worker_command_sha256"] if worker else candidate["command_argv_sha256"]
    if list(observed) != expected or sha256_bytes(canonical(list(observed))) != expected_sha:
        raise RecoveryValidationError("WORKER_COMMAND_MISMATCH" if worker else "SUPERVISOR_COMMAND_MISMATCH")
