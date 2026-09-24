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
    value.add_argument("--standing-authorization", type=Path)
    value.add_argument("--autonomy-state", type=Path)
    value.add_argument("--output-directory", type=Path)
    return value


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    return parser().parse_args(argv)


def main(argv: list[str] | None = None, *, audit_runner=None, now_utc=None) -> int:
    args = parse_arguments(argv)
    candidate, _ = governor.validate_candidate(args.candidate)
    if args.validate_candidate:
        result = {"candidate_sha256": multiplicity.file_sha256(args.candidate),
                  "network_requests": 0, "stage_id": candidate["stage_id"],
                  "state": "GLOBAL_VIEW_RELATION_CANDIDATE_VALIDATED"}
    else:
        if any(value is None for value in (args.permit,args.standing_authorization,
                                            args.autonomy_state,args.output_directory)):
            raise SystemExit("--permit, --standing-authorization, --autonomy-state and --output-directory are required")
        governor.validate_permit(args.permit, candidate_path=args.candidate,
            state_path=args.autonomy_state,standing_authorization_path=args.standing_authorization)
        consumed_at_utc = (now_utc or (lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")))()
        governor.consume_permit(
            args.permit, candidate_path=args.candidate,
            state_path=args.autonomy_state,standing_authorization_path=args.standing_authorization,
            consumed_at_utc=consumed_at_utc,
        )
        result = (audit_runner or multiplicity.run_local_relation_audit)(args.output_directory)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
