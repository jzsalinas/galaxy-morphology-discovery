"""Offline validator for the grouping-gate assessment action."""
from __future__ import annotations

from contextlib import redirect_stderr
import importlib.util
import io
from pathlib import Path
import sys

from .core import canonical
from .observational_multiplicity import (
    PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed,
)

CANDIDATE = PROJECT / "oc3/INPUTS/OC3_GROUPING_GATE_ASSESSMENT_CANDIDATE_001.json"
PERMIT = PROJECT / "oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GROUPING_GATE_ASSESSMENT_PERMIT_001.json"
AUTHORIZATION = PROJECT / "oc3/OC3_OBSERVATIONAL_MULTIPLICITY_STANDING_AUTHORIZATION_001.json"
STATE = PROJECT / "oc3/OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_STATE_001.json"
OUTPUT = PROJECT / "oc3/observational_multiplicity/OC3-OBSERVATIONAL-MULTIPLICITY-GROUPING-GATE-ASSESSMENT-001"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
EXECUTOR = PROJECT / "oc3/oc3_observational_multiplicity_grouping_gate.py"
SPECIFICATION = PROJECT / "OC3_OBSERVATIONAL_MULTIPLICITY_GROUPING_GATE_ASSESSMENT_SPEC_001.md"
IMPLEMENTATION_FILES = (
    "OC3_OBSERVATIONAL_MULTIPLICITY_GROUPING_GATE_ASSESSMENT_SPEC_001.md",
    "oc3/oc3_observational_multiplicity_grouping_gate.py",
    "oc3/oc3lib/observational_multiplicity.py",
)


class GroupingValidationError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({path: file_sha256(PROJECT / path) for path in IMPLEMENTATION_FILES}))


def expected_command_argv() -> list[str]:
    return [str(EXECUTABLE), str(EXECUTOR), "--assess-grouping-gate",
            "--candidate", str(CANDIDATE), "--permit", str(PERMIT),
            "--standing-authorization", str(AUTHORIZATION),
            "--autonomy-state", str(STATE), "--output-directory", str(OUTPUT)]


def _load_executor():
    spec = importlib.util.spec_from_file_location("oc3_observational_multiplicity_grouping_gate", EXECUTOR)
    if spec is None or spec.loader is None:
        raise GroupingValidationError("GROUPING_EXECUTOR_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    root = str(PROJECT / "oc3")
    inserted = root not in sys.path
    if inserted:
        sys.path.insert(0, root)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(root)
    return module


def validate_candidate(path: Path = CANDIDATE) -> dict[str, object]:
    candidate = validate_sealed(load_canonical_json(path))
    if (Path(path).resolve() != CANDIDATE.resolve() or
            candidate.get("schema_version") != "OC3_GROUPING_GATE_ASSESSMENT_CANDIDATE_001" or
            candidate.get("implementation_aggregate") != implementation_aggregate()):
        raise GroupingValidationError("GROUPING_CANDIDATE_IDENTITY_INVALID")
    argv = candidate.get("command_argv")
    if argv != expected_command_argv() or candidate.get("command_argv_sha256") != sha256_bytes(canonical(argv)):
        raise GroupingValidationError("GROUPING_CANDIDATE_COMMAND_INVALID")
    executor = _load_executor()
    parsed = executor.parse_arguments(argv[2:])
    expected = (True, CANDIDATE, PERMIT, AUTHORIZATION, STATE, OUTPUT)
    actual = (parsed.assess_grouping_gate, parsed.candidate, parsed.permit,
              parsed.standing_authorization, parsed.autonomy_state, parsed.output_directory)
    if actual != expected or parsed.validate_candidate:
        raise GroupingValidationError("GROUPING_CANDIDATE_PARSE_INVALID")
    executor.validate_runtime_invocation(candidate, executable=argv[0],
                                         script_path=argv[1], argument_vector=argv[2:])
    mutated = list(argv)
    mutated[-1] += ".changed"
    try:
        executor.validate_runtime_invocation(candidate, executable=mutated[0],
                                             script_path=mutated[1], argument_vector=mutated[2:])
    except executor.RuntimeCommandBindingError:
        pass
    else:
        raise GroupingValidationError("GROUPING_RUNTIME_MUTATION_ACCEPTED")
    with redirect_stderr(io.StringIO()):
        try:
            executor.parse_arguments([*argv[2:], "--unknown"])
        except SystemExit:
            pass
        else:
            raise GroupingValidationError("GROUPING_UNKNOWN_ARGUMENT_ACCEPTED")
    return {"assessment_executions": 0, "candidate_sha256": file_sha256(path),
            "command_argv_sha256": candidate["command_argv_sha256"],
            "network_requests": 0, "summary_value_reads": 0,
            "state": "GROUPING_GATE_CANDIDATE_VALIDATED"}
