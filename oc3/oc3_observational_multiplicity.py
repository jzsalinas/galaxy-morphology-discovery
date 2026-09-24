#!/usr/bin/env python3
"""Validate or execute the permitted offline global-view relation audit."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from oc3lib import observational_multiplicity as multiplicity
from oc3lib import observational_multiplicity_governor as governor


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    group = value.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate-candidate", action="store_true")
    group.add_argument("--audit-global-view-relation", action="store_true")
    value.add_argument("--candidate", type=Path, required=True)
    value.add_argument("--permit", type=Path)
    value.add_argument("--output-directory", type=Path)
    return value


def main() -> int:
    args = parser().parse_args()
    candidate, _ = governor.validate_candidate(args.candidate)
    if args.validate_candidate:
        result = {"candidate_sha256": multiplicity.file_sha256(args.candidate),
                  "network_requests": 0, "stage_id": candidate["stage_id"],
                  "state": "GLOBAL_VIEW_RELATION_CANDIDATE_VALIDATED"}
    else:
        if args.permit is None or args.output_directory is None:
            raise SystemExit("--permit and --output-directory are required")
        governor.validate_permit(args.permit, candidate_path=args.candidate)
        consumed_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        governor.consume_permit(
            args.permit, candidate_path=args.candidate,
            consumption_path=args.output_directory / "PERMIT_CONSUMPTION.json",
            consumed_at_utc=consumed_at_utc,
        )
        result = multiplicity.run_local_relation_audit(args.output_directory)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
