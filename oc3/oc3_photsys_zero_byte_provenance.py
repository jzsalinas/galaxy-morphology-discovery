#!/usr/bin/env python3
"""CLI for bounded PHOTSYS zero-byte public-source research."""
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
from oc3lib.photsys_zero_byte_provenance import (
    AUTHORIZATION_PATH, CANDIDATE_PATH, OUTPUT_ROOT, STAGE_ID, ProvenanceError,
    dry_run, run_research, synthetic_zero_initialization_check, validate_frozen_inputs,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Bounded public-document/source PHOTSYS provenance research")
    modes = result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-inputs", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--research-zero-byte-provenance", action="store_true")
    modes.add_argument("--run-synthetic-zero-initialization-check", action="store_true")
    result.add_argument("--execute-public-documentary-research", action="store_true")
    result.add_argument("--execute-synthetic-check", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE_PATH)
    result.add_argument("--authorization", type=Path)
    result.add_argument("--output-directory", type=Path, default=OUTPUT_ROOT)
    return result


def command_hash(argv: list[str]) -> str:
    complete = [str(Path(__file__).resolve().parent / ".venv/bin/python"),
                str(Path(__file__).resolve()), *argv]
    return hashlib.sha256(canonical(complete)).hexdigest()


def main(argv: list[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if argv is None else argv)
    args = parser().parse_args(supplied)
    try:
        if args.validate_inputs:
            if args.authorization or args.execute_public_documentary_research or args.execute_synthetic_check:
                raise ProvenanceError("OFFLINE_PREFLIGHT_ARGUMENT_INVALID")
            value = validate_frozen_inputs()
        elif args.dry_run:
            if args.authorization or args.execute_public_documentary_research or args.execute_synthetic_check:
                raise ProvenanceError("OFFLINE_PREFLIGHT_ARGUMENT_INVALID")
            value = dry_run()
        elif args.run_synthetic_zero_initialization_check:
            if not args.execute_synthetic_check or args.authorization is None:
                raise ProvenanceError("SYNTHETIC_CHECK_FINAL_AUTHORIZATION_REQUIRED")
            raise ProvenanceError("SYNTHETIC_CHECK_SEPARATE_AUTHORIZATION_NOT_IMPLEMENTED")
        else:
            if not args.execute_public_documentary_research or args.authorization is None:
                raise ProvenanceError("FINAL_AUTHORIZATION_REQUIRED")
            value = run_research(args.candidate, args.authorization, command_hash(supplied),
                                 args.output_directory)
        print(json.dumps(value, sort_keys=True, separators=(",", ":")))
        return 0
    except ProvenanceError as exc:
        print(json.dumps({"error": exc.code, "stage_id": STAGE_ID, "state": exc.code},
                         sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
