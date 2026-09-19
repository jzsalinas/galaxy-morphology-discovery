#!/usr/bin/env python3
"""CLI for the bounded physical-contract probe. Offline and non-mutating by default."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.core import canonical, implementation_hash
from oc3lib.physical_contract_probe import (ENVIRONMENT_FINGERPRINT, HTTPProbeTransport,
    PRE_PROBE_IMPLEMENTATION, PROBE_SPEC_SHA256, ProbeBinding, ProbeError, ProbeLedger,
    execute_probe, load_authorization, probe_plan, verify_probe_authorities)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Bounded OC-3 provider physical-contract probe; default OFFLINE.")
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("plan", "run"):
        command = commands.add_parser(name)
        command.add_argument("--project", type=Path, default=Path(__file__).resolve().parent.parent)
        command.add_argument("--offline", action="store_true")
        command.add_argument("--dry-run", action="store_true")
        command.add_argument("--execute-network", action="store_true")
        command.add_argument("--authorization", type=Path)
        command.add_argument("--resume", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        plan = probe_plan(args.project)
        if args.command == "plan" or args.offline or args.dry_run:
            print(canonical(plan).decode("utf-8"))
            return 0
        if not args.execute_network or args.authorization is None:
            raise ProbeError("PROBE_HUMAN_AUTHORIZATION_REQUIRED")
        command_bytes = canonical({"argv": list(argv if argv is not None else sys.argv[1:])}) + b"\n"
        authorization, authorization_sha = load_authorization(args.authorization, args.project, command_bytes)
        verify_probe_authorities(args.project)
        aggregate = implementation_hash(args.project)
        binding = ProbeBinding(PROBE_SPEC_SHA256, aggregate, ENVIRONMENT_FINGERPRINT,
                               authorization_sha, authorization["attempt_id"])
        attempt = Path(authorization["execution_directory"])
        if args.resume:
            if not attempt.is_dir():
                raise ProbeError("PROBE_RESUME_ATTEMPT_MISSING")
        else:
            attempt.mkdir(parents=True, exist_ok=False)
        ledger = ProbeLedger(attempt / "PROBE_LEDGER.sqlite", binding)
        try:
            if args.resume:
                ledger.recover()
            outcome = execute_probe(HTTPProbeTransport(authorized=True), ledger, attempt)
        finally:
            ledger.close()
        print(outcome)
        return 0 if outcome == "PROBE_PHYSICAL_CONTRACTS_RESOLVED" else 24
    except ProbeError as error:
        print(error.code, file=sys.stderr)
        return 23


if __name__ == "__main__":
    raise SystemExit(main())
