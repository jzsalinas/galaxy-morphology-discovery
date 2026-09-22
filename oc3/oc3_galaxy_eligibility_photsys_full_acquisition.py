#!/usr/bin/env python3
"""Validate or separately execute the PHOTSYS full-file preservation stage."""
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
from oc3lib.galaxy_eligibility_photsys_full_acquisition import (
    AUTOMATIC_RETRIES, CANDIDATE_PATH, CONCURRENCY, EXPECTED_BODY_BYTES, OUTPUT_ROOT,
    PARTIAL, PRIMARY_GETS, STAGE_ID, execute, validate_candidate_offline,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=(
        "Prospective PHOTSYS full-file byte preservation; no table-value decoding."))
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-candidate", action="store_true")
    mode.add_argument("--acquire", action="store_true")
    result.add_argument("--execute-network", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE_PATH)
    result.add_argument("--authorization", type=Path)
    result.add_argument("--output-directory", type=Path, default=OUTPUT_ROOT)
    result.add_argument("--expected-body-bytes", type=int, default=EXPECTED_BODY_BYTES)
    result.add_argument("--primary-get-count", type=int, default=PRIMARY_GETS)
    result.add_argument("--automatic-retries", type=int, default=AUTOMATIC_RETRIES)
    result.add_argument("--concurrency", type=int, default=CONCURRENCY)
    result.add_argument("--resume", action="store_true")
    return result


def command_hash(argv: list[str]) -> str:
    complete = [str(Path(__file__).resolve().parent / ".venv/bin/python"),
                str(Path(__file__).resolve()), *argv]
    return hashlib.sha256(canonical(complete)).hexdigest()


def main(argv: list[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if argv is None else argv)
    args = parser().parse_args(supplied)
    try:
        caps = (args.expected_body_bytes, args.primary_get_count,
                args.automatic_retries, args.concurrency)
        if caps != (EXPECTED_BODY_BYTES, PRIMARY_GETS, AUTOMATIC_RETRIES, CONCURRENCY):
            raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_RUNTIME_CAP_MISMATCH")
        if args.validate_candidate:
            if args.execute_network or args.authorization or args.resume:
                raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_OFFLINE_ARGUMENT_SCOPE")
            result = validate_candidate_offline(args.candidate)
        else:
            if args.resume:
                raise PHOTSYSProbeError("SEPARATE_RESUME_AUTHORIZATION_REQUIRED")
            if not args.execute_network or args.authorization is None:
                raise PHOTSYSProbeError("PHOTSYS_FULL_ACQUISITION_FINAL_AUTHORIZATION_REQUIRED")
            result = execute(args.candidate, args.authorization, command_hash(supplied),
                             args.output_directory)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except PHOTSYSProbeError as exc:
        print(json.dumps({"error": exc.code, "stage_id": STAGE_ID, "state": PARTIAL},
                         sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
