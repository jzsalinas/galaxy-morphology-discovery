"""Closed validator for the prospective offline pilot-frame action."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed
from .source_metadata_descriptive_pilot import FRAME_SCOPE, FRAME_STAGE_ID

SPEC = PROJECT / "OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_FIRST_ACTION_SPEC_001.md"
CANDIDATE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_FIRST_CANDIDATE_001.json"
RECEIPT = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_FIRST_CANDIDATE_VALIDATION_001.json"
PERMIT = PROJECT / "oc3/SOURCE_METADATA_DESCRIPTIVE_PILOT_AUTONOMY_PERMITS/OC3_SOURCE_METADATA_PILOT_FRAME_PERMIT_001.json"
AUTHORIZATION = PROJECT / "oc3/OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_STANDING_AUTHORIZATION_001.json"
STATE = PROJECT / "oc3/OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_AUTONOMY_STATE_001.json"
OUTPUT = PROJECT / "oc3/source_metadata_descriptive_pilot/OC3-SOURCE-METADATA-PILOT-FRAME-DERIVATION-001"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
SCRIPT = PROJECT / "oc3/oc3_source_metadata_pilot_frame.py"
IMPLEMENTATION_FILES = (
    "OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_FIRST_ACTION_SPEC_001.md",
    "oc3/oc3_source_metadata_pilot_frame.py",
    "oc3/oc3lib/source_metadata_descriptive_pilot.py",
    "oc3/oc3lib/source_metadata_descriptive_pilot_validation.py",
)
EXPECTED_INPUTS = (
    ("oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz", "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f"),
    ("oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz", "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb"),
    ("oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz", "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f"),
    ("oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv", "147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6"),
)


class FrameValidationError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({path: file_sha256(PROJECT / path) for path in IMPLEMENTATION_FILES}))


def expected_command_argv() -> list[str]:
    return [str(EXECUTABLE), str(SCRIPT), "--derive-pilot-frame", "--candidate", str(CANDIDATE),
            "--permit", str(PERMIT), "--standing-authorization", str(AUTHORIZATION),
            "--autonomy-state", str(STATE), "--output-directory", str(OUTPUT)]


def validate_candidate(path: Path = CANDIDATE) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    exact_zero = ("network_requests", "application_body_bytes", "source_rows_read",
                  "matching_operations", "PHOTSYS_reads", "morphology_accesses",
                  "object_group_ids_created", "split_group_ids_created")
    if (value.get("schema_version") != "OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_FIRST_CANDIDATE_001" or
            value.get("stage_id") != FRAME_STAGE_ID or value.get("scope") != FRAME_SCOPE or
            any(value.get(key) != 0 for key in exact_zero) or
            value.get("target_count") != 2 or value.get("reserved_holdout_count") != 2 or
            value.get("search_bound_selected") is not False or
            value.get("scientific_threshold_selected") is not False or
            value.get("frame_materialized") is not False):
        raise FrameValidationError("PILOT_FRAME_CANDIDATE_INVALID")
    argv = expected_command_argv()
    if value.get("command_argv") != argv or value.get("command_argv_sha256") != sha256_bytes(canonical(argv)):
        raise FrameValidationError("COMMAND_BINDING_INVALID")
    if value.get("implementation_aggregate") != implementation_aggregate():
        raise FrameValidationError("IMPLEMENTATION_BINDING_INVALID")
    expected = [{"path": path, "sha256": digest} for path, digest in EXPECTED_INPUTS]
    if value.get("input_bindings") != expected:
        raise FrameValidationError("PILOT_FRAME_INPUT_BINDING_INVALID")
    for binding in expected:
        source = PROJECT / binding["path"]
        if not source.is_file() or file_sha256(source) != binding["sha256"]:
            raise FrameValidationError("PILOT_FRAME_INPUT_MISMATCH")
    return value


def validate_runtime_invocation(candidate: dict[str, object], *, executable: str,
                                script_path: str, argument_vector: Sequence[str]) -> None:
    observed = [executable, script_path, *argument_vector]
    if observed != candidate["command_argv"] or sha256_bytes(canonical(observed)) != candidate["command_argv_sha256"]:
        raise FrameValidationError("RUNTIME_COMMAND_MISMATCH")
