"""Offline action-specific validation for global-view audit Candidate 003."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

from .core import canonical
from .observational_multiplicity import (
    PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed,
)

CANDIDATE_002 = PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_002.json"
CANDIDATE_003 = PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_003.json"
PERMIT_003 = PROJECT / "oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_003.json"
AUTHORIZATION = PROJECT / "oc3/OC3_OBSERVATIONAL_MULTIPLICITY_STANDING_AUTHORIZATION_001.json"
STATE = PROJECT / "oc3/OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_STATE_001.json"
OUTPUT = PROJECT / "oc3/observational_multiplicity/OC3-GLOBAL-VIEW-RELATION-AUDIT-001"
SCIENTIFIC_KEYS = frozenset({
    "closed_photsys_terminal", "decoded_fields", "execution", "expected_aggregate_fields",
    "input_authorities", "output_directory", "output_files", "resource_caps", "scientific_question",
    "scope", "specification", "stage_id", "success_terminal", "unresolved_gates",
})

class ExecutorValidationError(Exception):
    def __init__(self, code: str):
        self.code=code
        super().__init__(code)

def expected_command_argv() -> list[str]:
    return [
        str(PROJECT / "oc3/.venv/bin/python"),
        str(PROJECT / "oc3/oc3_observational_multiplicity.py"),
        "--audit-global-view-relation",
        "--candidate", str(CANDIDATE_003),
        "--permit", str(PERMIT_003),
        "--standing-authorization", str(AUTHORIZATION),
        "--autonomy-state", str(STATE),
        "--output-directory", str(OUTPUT),
    ]

def validate_candidate_003(path: Path=CANDIDATE_003) -> dict[str,object]:
    try:
        candidate=validate_sealed(load_canonical_json(path))
        historical=validate_sealed(load_canonical_json(CANDIDATE_002))
    except Exception as exc:
        raise ExecutorValidationError("CANDIDATE_003_CANONICAL_SEAL_INVALID") from exc
    if Path(path).resolve()!=CANDIDATE_003.resolve() or candidate.get("schema_version")!="OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_003":
        raise ExecutorValidationError("CANDIDATE_003_IDENTITY_INVALID")
    if {key:candidate.get(key) for key in SCIENTIFIC_KEYS}!={key:historical.get(key) for key in SCIENTIFIC_KEYS}:
        raise ExecutorValidationError("CANDIDATE_003_SCIENTIFIC_PAYLOAD_CHANGED")
    argv=candidate.get("command_argv")
    if argv!=expected_command_argv() or candidate.get("command_argv_sha256")!=sha256_bytes(canonical(argv)):
        raise ExecutorValidationError("CANDIDATE_003_COMMAND_INVALID")
    forbidden=(str(PROJECT/"oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_001.json"),
               str(CANDIDATE_002),
               str(PROJECT/"oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_001.json"),
               str(PROJECT/"oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_002.json"))
    if any(item in argv for item in forbidden):
        raise ExecutorValidationError("CANDIDATE_003_HISTORICAL_EXECUTION_PATH_PRESENT")
    executor_path = PROJECT / "oc3/oc3_observational_multiplicity.py"
    spec = importlib.util.spec_from_file_location("oc3_observational_multiplicity", executor_path)
    if spec is None or spec.loader is None:
        raise ExecutorValidationError("CANDIDATE_003_EXECUTOR_IMPORT_FAILED")
    executor = importlib.util.module_from_spec(spec)
    executor_root = str(PROJECT / "oc3")
    inserted = executor_root not in sys.path
    if inserted:
        sys.path.insert(0, executor_root)
    try:
        spec.loader.exec_module(executor)
    finally:
        if inserted:
            sys.path.remove(executor_root)
    try:
        parsed=executor.parse_arguments(argv[2:])
    except SystemExit as exc:
        raise ExecutorValidationError("CANDIDATE_003_COMMAND_PARSE_FAILED") from exc
    expected=(True,CANDIDATE_003,PERMIT_003,AUTHORIZATION,STATE,OUTPUT)
    actual=(parsed.audit_global_view_relation,parsed.candidate,parsed.permit,
            parsed.standing_authorization,parsed.autonomy_state,parsed.output_directory)
    if actual!=expected or parsed.validate_candidate:
        raise ExecutorValidationError("CANDIDATE_003_PARSED_BINDING_INVALID")
    return {
        "audit_executions":0,"candidate_sha256":file_sha256(path),"command_argv_sha256":candidate["command_argv_sha256"],
        "local_authority_value_reads":0,"network_requests":0,"parsed":{
            "autonomy_state":str(parsed.autonomy_state),"candidate":str(parsed.candidate),
            "mode":"audit-global-view-relation","output_directory":str(parsed.output_directory),
            "permit":str(parsed.permit),"standing_authorization":str(parsed.standing_authorization)},
        "state":"CANDIDATE_003_EXECUTOR_INTEGRATION_VALIDATED",
    }
