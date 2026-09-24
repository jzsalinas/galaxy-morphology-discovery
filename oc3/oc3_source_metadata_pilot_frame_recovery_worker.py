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
from oc3lib.source_metadata_pilot_frame_recovery import (
    frame_payload, global_view_both, identity_array, read_development_bricknames,
    root_columns, select_frame,
)
from oc3lib.source_metadata_pilot_frame_recovery_validation import (
    CANDIDATE, RecoveryValidationError, implementation_aggregate, validate_candidate, validate_invocation,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Columnar pilot-frame recovery worker")
    result.add_argument("--run-worker", action="store_true", required=True)
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--output", type=Path, required=True)
    return result


def _root(path: Path):
    from astropy.io import fits
    with fits.open(path, memmap=False) as hdus:
        table = hdus[1].data
        required = ("BRICKNAME", "BRICKID", "BRICKROW", "RA", "DEC", "RA1", "RA2", "DEC1", "DEC2")
        if not set(required).issubset(table.names):
            raise RecoveryValidationError("BOUND_ROOT_COLUMNS_MISSING")
        return root_columns(**{name.lower(): table[name].copy() for name in required})


def _identities(path: Path):
    from astropy.io import fits
    with fits.open(path, memmap=False) as hdus:
        table = hdus[1].data
        if not {"BRICKNAME", "BRICKID"}.issubset(table.names):
            raise RecoveryValidationError("BOUND_IDENTITY_COLUMNS_MISSING")
        return identity_array(table["BRICKNAME"].copy(), table["BRICKID"].copy())


def run(candidate: dict[str, object], output: Path) -> None:
    paths = [PROJECT / item["path"] for item in candidate["input_bindings"]]
    root = _root(paths[0])
    north = _identities(paths[1])
    south = _identities(paths[2])
    excluded = read_development_bricknames(paths[3])
    eligible = global_view_both(root["identity"], north, south, excluded)
    selections = select_frame(root, eligible)
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
        print(json.dumps({"frame_path": str(args.output), "state": "PILOT_FRAME_WORKER_COMPLETED"}, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"error": getattr(exc, "code", type(exc).__name__),
                          "state": "PILOT_FRAME_WORKER_FAILED"}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
