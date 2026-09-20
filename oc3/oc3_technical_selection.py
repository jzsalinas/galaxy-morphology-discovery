#!/usr/bin/env python3
"""Offline-only entry point for deterministic OC-3 technical-brick selection."""
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

from oc3lib.technical_selection import (
    FAILURE_TERMINAL, SelectionError, dry_run, run_production,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="oc3_technical_selection.py")
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute-offline", action="store_true",
                      help="run the closed local technical selection")
    mode.add_argument("--dry-run", action="store_true",
                      help="validate the exact closed paths without reading rows")
    result.add_argument("--attempt-directory", required=True, type=Path)
    result.add_argument("--patch-evidence-directory", required=True, type=Path)
    result.add_argument("--output-csv", required=True, type=Path)
    result.add_argument("--audit-directory", required=True, type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.dry_run:
            result = dry_run(args.attempt_directory, args.patch_evidence_directory,
                             args.output_csv, args.audit_directory)
        else:
            evidence = run_production(args.attempt_directory, args.patch_evidence_directory,
                                      args.output_csv, args.audit_directory)
            result = {
                "network_requests": evidence["aggregate"]["metrics"]["network_requests"],
                "selected_count": evidence["aggregate"]["metrics"]["selected_count"],
                "stage_id": evidence["terminal"]["stage_id"],
                "state": evidence["terminal"]["terminal"],
            }
            if result["state"] == FAILURE_TERMINAL:
                print(json.dumps(result, sort_keys=True, separators=(",", ":")))
                return 2
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except SelectionError as exc:
        print(json.dumps({"error": exc.code, "state": FAILURE_TERMINAL},
                         sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
