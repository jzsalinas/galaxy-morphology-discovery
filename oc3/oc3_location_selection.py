#!/usr/bin/env python3
"""Offline-only OC-3 observational location selection entry point."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from oc3lib.location_selection import (FAILURE, STAGE_ID, LocationSelectionError,
                                       dry_run, execute)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="oc3_location_selection.py",
        description="Deterministic OC-3 location selection from 14 immutable auxiliary maps; no network transport exists.")
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="validate frozen bindings without decoding arrays or writing outputs")
    mode.add_argument("--execute", action="store_true",
                      help="decode only the 14 authorized auxiliary arrays and select six locations once")
    result.add_argument("--offline", action="store_true", required=True,
                        help="mandatory declaration; this CLI contains no online mode")
    result.add_argument("--project", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        terminal = dry_run(args.project) if args.dry_run else execute(args.project)
        print(json.dumps(terminal, sort_keys=True, separators=(",", ":")))
        return 0
    except LocationSelectionError as exc:
        terminal = {"stage_id": STAGE_ID, "state": FAILURE, "error": exc.code,
                    "network_requests": 0, "network_body_bytes": 0}
        print(json.dumps(terminal, sort_keys=True, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
