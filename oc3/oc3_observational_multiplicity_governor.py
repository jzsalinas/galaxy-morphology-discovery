#!/usr/bin/env python3
"""Offline CLI for the observational-multiplicity mission governor."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from oc3lib import observational_multiplicity_governor as governor


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    group = value.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate", action="store_true")
    group.add_argument("--status", action="store_true")
    group.add_argument("--evaluate", action="store_true")
    group.add_argument("--activate-standing-authorization", action="store_true")
    value.add_argument("--candidate", type=Path, default=governor.FIRST_CANDIDATE_PATH)
    value.add_argument("--authorization", type=Path, default=governor.AUTHORIZATION_PATH)
    value.add_argument("--activated-at-utc")
    return value


def main() -> int:
    args = parser().parse_args()
    if args.validate:
        result = governor.validate_all()
    elif args.status:
        state = governor.validate_state()
        result = {"active": state["active"], "mission_id": state["mission_id"],
                  "network_requests": 0, "permits_issued": state["permits_issued"],
                  "state": state["state"]}
    elif args.evaluate:
        result = governor.evaluate_candidate(args.candidate)
    else:
        if not args.activated_at_utc:
            raise SystemExit("--activated-at-utc is required")
        result = governor.activate(activated_at_utc=args.activated_at_utc,
                                   authorization_path=args.authorization)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
