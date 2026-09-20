#!/usr/bin/env python3
"""Offline-only entry point for the bounded PATCH metadata decode stage."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.patch_metadata_decode import (
    FAILURE_TERMINAL, PatchDecodeError, dry_run, run_production,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="oc3_patch_metadata_decode.py")
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute-offline", action="store_true",
                      help="run the exact closed local decode stage")
    mode.add_argument("--dry-run", action="store_true",
                      help="validate the closed argv without reading PATCH rows")
    result.add_argument("--attempt-directory", required=True, type=Path)
    result.add_argument("--output-directory", required=True, type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.dry_run:
            result = dry_run(args.attempt_directory, args.output_directory)
        else:
            result = run_production(args.attempt_directory, args.output_directory)
            result = {
                "network_requests": result["aggregate"]["metrics"]["network_requests"],
                "row_count": result["aggregate"]["metrics"]["row_count"],
                "stage_id": result["terminal"]["stage_id"],
                "state": result["terminal"]["terminal"],
            }
            if result["state"] == FAILURE_TERMINAL:
                print(json.dumps(result, sort_keys=True, separators=(",", ":")))
                return 2
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except PatchDecodeError as exc:
        print(json.dumps({"error": exc.code, "state": FAILURE_TERMINAL},
                         sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
