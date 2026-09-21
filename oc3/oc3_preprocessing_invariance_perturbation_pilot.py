#!/usr/bin/env python3
"""Offline CLI for the frozen OC-3 technical perturbation pilot."""
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

from oc3lib.preprocessing_perturbation_pilot import (
    FAILURE, STAGE_ID, PilotError, execute, validate_inputs,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="oc3_preprocessing_invariance_perturbation_pilot.py",
        description="Offline technical perturbation pilot for six frozen observational windows.")
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true",
                      help="verify frozen authorities and immutable artifact hashes only")
    mode.add_argument("--execute-pilot", action="store_true",
                      help="execute the single fail-closed offline technical pilot")
    result.add_argument("--project", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        value = (validate_inputs(args.project.resolve()) if args.validate_inputs
                 else execute(args.project.resolve()))
        print(json.dumps(value, sort_keys=True, separators=(",", ":")))
        return 0
    except PilotError as exc:
        value = {"stage_id": STAGE_ID, "state": FAILURE, "error": exc.code,
                 "identity": exc.identity, "network_requests": 0,
                 "model_operations": 0, "morphology_operations": 0}
        print(json.dumps(value, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
