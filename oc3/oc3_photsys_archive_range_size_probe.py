#!/usr/bin/env python3
"""CLI for the separately authorized desitarget archive Range-size probe."""
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
from oc3lib.photsys_archive_range_size_probe import (
    AUTHORIZATION_PATH, AUTONOMY_STATE_PATH, AUTONOMOUS_PERMIT_PATH,
    CANDIDATE_002_PATH, CANDIDATE_003_PATH, CANDIDATE_PATH, OUTPUT_ROOT, STAGE_ID,
    STANDING_AUTHORIZATION_PATH, RangeSizeProbeError, autonomous_dry_run,
    dry_run, execute, execute_autonomous, validate_historical_inputs,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="One exact bytes=0-0 GET with header-only observation for archive size")
    modes = result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-inputs", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--probe-desitarget-archive-range-size", action="store_true")
    result.add_argument("--execute-network", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE_PATH)
    result.add_argument("--authorization", type=Path)
    result.add_argument("--standing-authorization", type=Path)
    result.add_argument("--autonomous-permit", type=Path)
    result.add_argument("--autonomy-state", type=Path)
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
            if (args.execute_network or args.authorization or args.standing_authorization or
                    args.autonomous_permit or args.autonomy_state):
                raise RangeSizeProbeError("RANGE_SIZE_PREFLIGHT_ARGUMENT_INVALID")
            result = validate_historical_inputs()
        elif args.dry_run:
            if (args.execute_network or args.authorization or args.standing_authorization or
                    args.autonomous_permit or args.autonomy_state):
                raise RangeSizeProbeError("RANGE_SIZE_PREFLIGHT_ARGUMENT_INVALID")
            result = autonomous_dry_run() if args.candidate.resolve() == CANDIDATE_003_PATH.resolve() else dry_run(args.candidate)
        else:
            if not args.execute_network:
                raise RangeSizeProbeError("RANGE_SIZE_FINAL_AUTHORIZATION_REQUIRED")
            if args.candidate.resolve() == CANDIDATE_003_PATH.resolve():
                if (args.authorization is not None or args.standing_authorization is None or
                        args.autonomous_permit is None or args.autonomy_state is None):
                    raise RangeSizeProbeError("RANGE_SIZE_AUTONOMOUS_PERMIT_REQUIRED")
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                result = execute_autonomous(
                    args.candidate, args.standing_authorization, args.autonomous_permit,
                    args.autonomy_state, command_hash(supplied), args.output_directory,
                    consumed_at_utc=now, transitioned_at_utc=now)
            elif args.candidate.resolve() == CANDIDATE_002_PATH.resolve():
                raise RangeSizeProbeError("RANGE_SIZE_HISTORICAL_CANDIDATE_NOT_EXECUTABLE")
            else:
                if (args.authorization is None or args.standing_authorization is not None or
                        args.autonomous_permit is not None or args.autonomy_state is not None):
                    raise RangeSizeProbeError("RANGE_SIZE_FINAL_AUTHORIZATION_REQUIRED")
                result = execute(args.candidate, args.authorization, command_hash(supplied),
                                 args.output_directory)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except RangeSizeProbeError as exc:
        print(json.dumps({"error": exc.code, "stage_id": STAGE_ID, "state": exc.code},
                         sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
