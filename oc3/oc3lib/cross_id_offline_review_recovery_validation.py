"""Validator for the prospective zero-network offline review recovery action."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_id_offline_review_recovery import (
    PROJECT, STAGE_ID, SCOPE, file_sha256, load_canonical_json, sha256_bytes,
    validate_sealed,
)

SPEC = PROJECT / "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_FIRST_ACTION_SPEC_001.md"
CANDIDATE = PROJECT / "oc3/INPUTS/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_FIRST_CANDIDATE_001.json"
RECEIPT = PROJECT / "oc3/INPUTS/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_FIRST_CANDIDATE_VALIDATION_001.json"
PERMIT = PROJECT / "oc3/CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_PERMITS/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_PERMIT_001.json"
AUTHORIZATION = PROJECT / "oc3/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_STANDING_AUTHORIZATION_001.json"
STATE = PROJECT / "oc3/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_STATE_001.json"
OUTPUT = PROJECT / "oc3/cross_id_offline_review_recovery/OC3-CROSS-ID-OFFLINE-SEMANTIC-REVIEW-RECOVERY-001"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
SCRIPT = PROJECT / "oc3/oc3_cross_id_offline_review_recovery.py"
IMPLEMENTATION_FILES = (
    "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_FIRST_ACTION_SPEC_001.md",
    "oc3/oc3_cross_id_offline_review_recovery.py",
    "oc3/oc3lib/cross_id_offline_review_recovery.py",
    "oc3/oc3lib/cross_id_offline_review_recovery_validation.py",
)
EXPECTED_INPUTS = (
    ("oc3/cross_id_formalism_recovery/OC3-CROSS-ID-FORMALISM-PRIMARY-EVIDENCE-ACQUISITION-002/RAW_IMMUTABLE/BUDAVARI_SZALAY_ARXIV_ABSTRACT_V3.body", "c594358824153c3ec6a64273ed852eaf22fdca5c3537f221e9e59bd9d79faec2"),
    ("oc3/cross_id_formalism_recovery/OC3-CROSS-ID-FORMALISM-PRIMARY-EVIDENCE-ACQUISITION-002/RAW_IMMUTABLE/BUDAVARI_SZALAY_ASPC_394_165_DIRECT_PUBLISHER.body", "ff0660168aab46f78221dd2d65f004b5b4b0e2a2139a151a2907203c618c079a"),
    ("oc3/cross_id_formalism_recovery/OC3-CROSS-ID-FORMALISM-PRIMARY-EVIDENCE-ACQUISITION-002/TRANSPORT_EVIDENCE.json", "580a6c635ca55b34f88df7f44da29825aceb28b8d3f5956fdf954d15d7a908d7"),
    ("oc3/cross_id_formalism_recovery/OC3-CROSS-ID-FORMALISM-PRIMARY-EVIDENCE-ACQUISITION-002/TERMINAL.json", "45c51244a8cf63f699464eca7d562cdfee81b401c639246a89f89ad7572a9d59"),
)


class RecoveryValidationError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({p: file_sha256(PROJECT / p) for p in IMPLEMENTATION_FILES}))


def expected_command_argv() -> list[str]:
    return [str(EXECUTABLE), str(SCRIPT), "--review-primary-evidence", "--candidate", str(CANDIDATE),
            "--permit", str(PERMIT), "--standing-authorization", str(AUTHORIZATION),
            "--autonomy-state", str(STATE), "--output-directory", str(OUTPUT)]


def validate_candidate(path: Path = CANDIDATE) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    if (value.get("schema_version") != "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_FIRST_CANDIDATE_001" or
            value.get("stage_id") != STAGE_ID or value.get("scope") != SCOPE or
            value.get("network_requests") != 0 or value.get("application_body_bytes") != 0 or
            value.get("source_rows_read") != 0 or value.get("matching_operations") != 0 or
            value.get("search_bound_selected") is not False or
            value.get("scientific_threshold_selected") is not False or
            value.get("claims_initial_status") != {name: "UNDECIDED" for name in (
                "CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS",
                "BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD")}):
        raise RecoveryValidationError("OFFLINE_RECOVERY_CANDIDATE_INVALID")
    argv = expected_command_argv()
    if value.get("command_argv") != argv or value.get("command_argv_sha256") != sha256_bytes(canonical(argv)):
        raise RecoveryValidationError("COMMAND_BINDING_INVALID")
    if value.get("implementation_aggregate") != implementation_aggregate():
        raise RecoveryValidationError("IMPLEMENTATION_BINDING_INVALID")
    expected = [{"path": path, "sha256": digest} for path, digest in EXPECTED_INPUTS]
    if value.get("input_bindings") != expected:
        raise RecoveryValidationError("OFFLINE_RECOVERY_INPUT_INVALID")
    for binding in expected:
        source = PROJECT / binding["path"]
        if not source.is_file() or file_sha256(source) != binding["sha256"]:
            raise RecoveryValidationError("OFFLINE_RECOVERY_INPUT_MISMATCH")
    return value


def validate_runtime_invocation(candidate: dict[str, object], *, executable: str,
                                script_path: str, argument_vector: Sequence[str]) -> None:
    observed = [executable, script_path, *argument_vector]
    if (observed != candidate["command_argv"] or
            sha256_bytes(canonical(observed)) != candidate["command_argv_sha256"]):
        raise RecoveryValidationError("RUNTIME_COMMAND_MISMATCH")
