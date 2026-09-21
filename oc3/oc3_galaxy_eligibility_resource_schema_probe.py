#!/usr/bin/env python3
"""CLI for the bounded galaxy-eligibility resource/schema probe."""
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
from oc3lib.galaxy_eligibility_resource_schema_probe import (
    EligibilityProbeError,
    P0_FAILURE_TERMINAL,
    STAGE_ID,
    dry_run,
    execute_p0,
    probe_resource_schema,
    validate_inputs,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="oc3_galaxy_eligibility_resource_schema_probe.py",
        description="Offline P0 panel binding and separately authorized bounded P1 schema probe.",
    )
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--bind-panel", action="store_true")
    mode.add_argument("--probe-resource-schema", action="store_true")
    result.add_argument("--candidate", type=Path)
    result.add_argument("--authorization", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result


def argv_sha256(argv: list[str]) -> str:
    return hashlib.sha256(canonical(argv)).hexdigest()


def main(argv: list[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if argv is None else argv)
    args = parser().parse_args(supplied)
    try:
        if args.validate_inputs:
            result = validate_inputs()
        elif args.dry_run:
            result = dry_run()
        elif args.bind_panel:
            if args.candidate or args.authorization or args.output_directory:
                raise EligibilityProbeError("P0_ARGUMENT_SCOPE_VIOLATION")
            evidence = execute_p0()
            panel = evidence["panel"]
            result = {
                "fixture_leak_count": 0,
                "network_requests": 0,
                "north_count": panel["regional_counts"]["north"],
                "panel_manifest_seal": panel["sealed"],
                "panel_size": panel["panel_size"],
                "south_count": panel["regional_counts"]["south"],
                "stage_id": STAGE_ID,
                "state": evidence["terminal"]["terminal"],
            }
        else:
            if not args.candidate or not args.authorization or not args.output_directory:
                raise EligibilityProbeError("P1_FINAL_AUTHORIZATION_REQUIRED")
            result = probe_resource_schema(
                args.candidate, args.authorization, argv_sha256(supplied), args.output_directory)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except EligibilityProbeError as exc:
        print(json.dumps({"error": exc.code, "stage_id": STAGE_ID,
                          "state": P0_FAILURE_TERMINAL},
                         sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
