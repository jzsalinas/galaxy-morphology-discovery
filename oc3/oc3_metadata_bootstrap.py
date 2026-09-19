#!/usr/bin/env python3
"""Fail-closed CLI for the frozen OC-3 metadata bootstrap stage.

Real transport capability is constructed only after the frozen plan, rights,
human authorization, exact command, implementation, and environment gates pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from oc3lib.metadata_bootstrap import (
    ATTEMPT_ID, BOOTSTRAP_SCOPE, BootstrapError, activate_network_transport,
    dry_run_plan,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="oc3_metadata_bootstrap.py")
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true",
                      help="inspect frozen bindings without constructing network transport")
    mode.add_argument("--execute-network", action="store_true",
                      help="request the separately authorized future network mode")
    result.add_argument("--dry-run", action="store_true",
                        help="emit a deterministic prospective plan without creating attempt state")
    result.add_argument("--authorization", type=Path,
                        help="future exact first-run or resume authorization JSON")
    result.add_argument("--rights-binding", type=Path,
                        help="future exact reviewed rights binding JSON")
    result.add_argument("--resume", action="store_true",
                        help="future resume mode; requires RESUME_NETWORK_AUTHORIZATION")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    command = [str(Path(__file__).resolve())] + list(argv if argv is not None else sys.argv[1:])
    project = Path(__file__).resolve().parents[1]
    try:
        if args.execute_network:
            activate_network_transport(
                project=project,
                command=command,
                authorization_path=args.authorization,
                rights_path=args.rights_binding,
                resume=args.resume,
            )
            print(json.dumps({
                "attempt_id": ATTEMPT_ID,
                "network_requests_started": 0,
                "network_transport_constructed": True,
                "scope": BOOTSTRAP_SCOPE,
                "state": "AUTHORIZED_TRANSPORT_READY",
            }, sort_keys=True, separators=(",", ":")))
            return 0
        plan = dry_run_plan(project, command)
        plan.update({
            "attempt_id": ATTEMPT_ID,
            "metadata_bootstrap": "NOT_STARTED",
            "mode": "DRY_RUN" if args.dry_run else "OFFLINE_INSPECTION",
            "production_decode_enabled": False,
            "real_attempt_created": False,
            "real_network_requests": 0,
            "redistribution": False,
            "scope": BOOTSTRAP_SCOPE,
        })
        print(json.dumps(plan, sort_keys=True, separators=(",", ":")))
        return 0
    except BootstrapError as exc:
        print(exc.code, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
