#!/usr/bin/env python3
"""CLI for the closed offline OC-3 observational/confound audit."""
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

from oc3lib.observational_confound_audit import (
    FAILURE, STAGE_ID, AuditError, execute, validate_inputs,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="oc3_observational_confound_audit.py",
        description="Offline two-tier technical audit of frozen OC-3 crops.")
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true",
                      help="validate immutable bindings without opening crop arrays")
    mode.add_argument("--audit", action="store_true",
                      help="execute the single offline two-tier audit")
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
    except AuditError as exc:
        value = {"stage_id": STAGE_ID, "state": FAILURE, "error": exc.code,
                 "identity": exc.identity, "network_requests": 0}
        print(json.dumps(value, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
