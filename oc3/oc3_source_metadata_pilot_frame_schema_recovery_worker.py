#!/usr/bin/env python3
"""Material worker for memory-bounded local FITS frame recovery; no permit logic."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.cross_observer_grouping import PROJECT, sealed, write_json_immutable
from oc3lib.source_metadata_pilot_frame_schema_recovery import (
    FRAME_SELECTION_INTEGRITY_FAILURE, GLOBAL_IDENTITY_INTEGRITY_FAILURE,
    WORKER_RUNTIME_FAILURE, FrameRecoveryError, frame_payload, global_view_both,
    read_development_bricknames, read_regional_identity_physical,
    read_root_physical, select_frame,
)
from oc3lib.provider_physical_contracts import PhysicalRole
from oc3lib.source_metadata_pilot_frame_schema_recovery_validation import (
    CANDIDATE, RecoveryValidationError, implementation_aggregate, validate_candidate, validate_invocation,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Columnar pilot-frame schema recovery worker")
    result.add_argument("--run-schema-correct-worker", action="store_true", required=True)
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--output", type=Path, required=True)
    return result


def run(candidate: dict[str, object], output: Path) -> None:
    paths = [PROJECT / item["path"] for item in candidate["input_bindings"]]
    root = read_root_physical(paths[0])
    north = read_regional_identity_physical(paths[1], PhysicalRole.NORTH_SUMMARY)
    south = read_regional_identity_physical(paths[2], PhysicalRole.SOUTH_SUMMARY)
    excluded = read_development_bricknames(paths[3])
    try:
        eligible = global_view_both(root["identity"], north, south, excluded)
    except Exception as exc:
        raise FrameRecoveryError(GLOBAL_IDENTITY_INTEGRITY_FAILURE) from exc
    try:
        selections = select_frame(root, eligible)
    except Exception as exc:
        raise FrameRecoveryError(FRAME_SELECTION_INTEGRITY_FAILURE) from exc
    value = frame_payload(root, selections,
        {item["path"]: item["sha256"] for item in candidate["input_bindings"]},
        candidate["implementation_aggregate"])
    write_json_immutable(output, sealed(value))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        candidate = validate_candidate(args.candidate)
        validate_invocation(candidate, [sys.executable, sys.argv[0], *sys.argv[1:]], worker=True)
        run(candidate, args.output)
        print(json.dumps({"frame_path": str(args.output), "state": "PILOT_FRAME_SCHEMA_WORKER_COMPLETED"}, sort_keys=True))
        return 0
    except Exception as exc:
        code = getattr(exc, "code", WORKER_RUNTIME_FAILURE)
        print(json.dumps({"error": code,
                          "state": "PILOT_FRAME_SCHEMA_WORKER_FAILED"}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
