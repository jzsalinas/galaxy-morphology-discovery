"""Offline action-specific validation for global-view audit Candidate 004."""
from __future__ import annotations

from contextlib import redirect_stderr
import importlib.util
import io
from pathlib import Path
import sys

from .core import canonical
from .observational_multiplicity import (
    PROJECT, audit_implementation_aggregate, file_sha256, load_canonical_json,
    sha256_bytes, validate_sealed,
)

CANDIDATE_003 = PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_003.json"
CANDIDATE_004 = PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_004.json"
PERMIT_004 = PROJECT / "oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_004.json"
AUTHORIZATION = PROJECT / "oc3/OC3_OBSERVATIONAL_MULTIPLICITY_STANDING_AUTHORIZATION_001.json"
STATE = PROJECT / "oc3/OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_STATE_001.json"
OUTPUT = PROJECT / "oc3/observational_multiplicity/OC3-GLOBAL-VIEW-RELATION-AUDIT-001"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
EXECUTOR = PROJECT / "oc3/oc3_observational_multiplicity.py"
SCIENTIFIC_KEYS = frozenset({
    "closed_photsys_terminal", "decoded_fields", "execution", "expected_aggregate_fields",
    "input_authorities", "output_directory", "output_files", "resource_caps", "scientific_question",
    "scope", "specification", "stage_id", "success_terminal", "unresolved_gates",
})


class ExecutorValidationError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def expected_command_argv() -> list[str]:
    return [
        str(EXECUTABLE), str(EXECUTOR), "--audit-global-view-relation",
        "--candidate", str(CANDIDATE_004),
        "--permit", str(PERMIT_004),
        "--standing-authorization", str(AUTHORIZATION),
        "--autonomy-state", str(STATE),
        "--output-directory", str(OUTPUT),
    ]


def _load_executor():
    spec = importlib.util.spec_from_file_location("oc3_observational_multiplicity", EXECUTOR)
    if spec is None or spec.loader is None:
        raise ExecutorValidationError("CANDIDATE_004_EXECUTOR_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    executor_root = str(PROJECT / "oc3")
    inserted = executor_root not in sys.path
    if inserted:
        sys.path.insert(0, executor_root)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(executor_root)
    return module


def _require_runtime_rejection(executor, command: list[str]) -> None:
    try:
        executor.validate_runtime_invocation(
            load_canonical_json(CANDIDATE_004), executable=command[0],
            script_path=command[1], argument_vector=command[2:],
        )
    except executor.RuntimeCommandBindingError as exc:
        if exc.code == "RUNTIME_COMMAND_BINDING_MISMATCH":
            return
    raise ExecutorValidationError("CANDIDATE_004_RUNTIME_MUTATION_ACCEPTED")


def validate_candidate_004(path: Path = CANDIDATE_004) -> dict[str, object]:
    try:
        candidate = validate_sealed(load_canonical_json(path))
        historical = validate_sealed(load_canonical_json(CANDIDATE_003))
    except Exception as exc:
        raise ExecutorValidationError("CANDIDATE_004_CANONICAL_SEAL_INVALID") from exc
    if (Path(path).resolve() != CANDIDATE_004.resolve() or
            candidate.get("schema_version") != "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_004"):
        raise ExecutorValidationError("CANDIDATE_004_IDENTITY_INVALID")
    if ({key: candidate.get(key) for key in SCIENTIFIC_KEYS} !=
            {key: historical.get(key) for key in SCIENTIFIC_KEYS}):
        raise ExecutorValidationError("CANDIDATE_004_SCIENTIFIC_PAYLOAD_CHANGED")
    if candidate.get("implementation_aggregate") != audit_implementation_aggregate():
        raise ExecutorValidationError("CANDIDATE_004_IMPLEMENTATION_AGGREGATE_INVALID")
    argv = candidate.get("command_argv")
    if (argv != expected_command_argv() or
            candidate.get("command_argv_sha256") != sha256_bytes(canonical(argv))):
        raise ExecutorValidationError("CANDIDATE_004_COMMAND_INVALID")
    forbidden = (
        str(PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_001.json"),
        str(PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_002.json"),
        str(CANDIDATE_003),
        str(PROJECT / "oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_001.json"),
        str(PROJECT / "oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_002.json"),
        str(PROJECT / "oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_003.json"),
    )
    if any(item in argv for item in forbidden):
        raise ExecutorValidationError("CANDIDATE_004_HISTORICAL_EXECUTION_PATH_PRESENT")

    executor = _load_executor()
    try:
        parsed = executor.parse_arguments(argv[2:])
    except SystemExit as exc:
        raise ExecutorValidationError("CANDIDATE_004_COMMAND_PARSE_FAILED") from exc
    expected = (True, CANDIDATE_004, PERMIT_004, AUTHORIZATION, STATE, OUTPUT)
    actual = (parsed.audit_global_view_relation, parsed.candidate, parsed.permit,
              parsed.standing_authorization, parsed.autonomy_state, parsed.output_directory)
    if actual != expected or parsed.validate_candidate:
        raise ExecutorValidationError("CANDIDATE_004_PARSED_BINDING_INVALID")
    executor.validate_runtime_invocation(candidate, executable=argv[0],
                                         script_path=argv[1], argument_vector=argv[2:])

    mutation_indexes = (0, 1, 2, 4, 6, 8, 10, 12)
    for index in mutation_indexes:
        mutated = list(argv)
        mutated[index] = mutated[index] + ".mutated"
        _require_runtime_rejection(executor, mutated)
    _require_runtime_rejection(executor, [*argv, "--unknown-extra-argument"])
    with redirect_stderr(io.StringIO()):
        try:
            executor.parse_arguments([*argv[2:], "--unknown-extra-argument"])
        except SystemExit:
            pass
        else:
            raise ExecutorValidationError("CANDIDATE_004_UNKNOWN_ARGUMENT_PARSED")

    return {
        "audit_executions": 0,
        "candidate_sha256": file_sha256(path),
        "command_argv_sha256": candidate["command_argv_sha256"],
        "local_authority_value_reads": 0,
        "network_requests": 0,
        "runtime_command_mutations_rejected": 9,
        "state": "CANDIDATE_004_RUNTIME_COMMAND_BINDING_VALIDATED",
    }
