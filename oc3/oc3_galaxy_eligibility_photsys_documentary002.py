#!/usr/bin/env python3
"""CLI for the second bounded PHOTSYS documentary-only attempt."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.core import canonical
from oc3lib.galaxy_eligibility_photsys_authority_probe import PHOTSYSProbeError
from oc3lib.galaxy_eligibility_photsys_documentary002 import (
    ATTEMPT_ID, FAILED, dry_run, execute, persist_failure_terminal, validate_inputs,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="oc3_galaxy_eligibility_photsys_documentary002.py",
        description="Second, separately authorized PHOTSYS documentary-only URL-binding attempt.",
    )
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--probe-documentary-002", action="store_true")
    result.add_argument("--candidate", type=Path)
    result.add_argument("--authorization", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result


def command_argv_sha256(argv: list[str]) -> str:
    complete = ["oc3/.venv/bin/python",
                "oc3/oc3_galaxy_eligibility_photsys_documentary002.py", *argv]
    return hashlib.sha256(canonical(complete)).hexdigest()


def main(argv: list[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if argv is None else argv)
    args = parser().parse_args(supplied)
    try:
        if args.validate_inputs:
            if args.candidate or args.authorization or args.output_directory:
                raise PHOTSYSProbeError("DOCUMENTARY_002_OFFLINE_ARGUMENT_SCOPE")
            result = validate_inputs()
        elif args.dry_run:
            if args.candidate or args.authorization or args.output_directory:
                raise PHOTSYSProbeError("DOCUMENTARY_002_OFFLINE_ARGUMENT_SCOPE")
            result = dry_run()
        else:
            if not args.candidate or not args.authorization or not args.output_directory:
                raise PHOTSYSProbeError("DOCUMENTARY_002_FINAL_AUTHORIZATION_REQUIRED")
            result = execute(args.candidate, args.authorization, command_argv_sha256(supplied),
                             args.output_directory)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except PHOTSYSProbeError as exc:
        if args.probe_documentary_002 and args.output_directory:
            try:
                persist_failure_terminal(args.output_directory, exc.code)
            except PHOTSYSProbeError:
                pass
        print(json.dumps({"error": exc.code, "stage_id": ATTEMPT_ID, "state": FAILED},
                         sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
