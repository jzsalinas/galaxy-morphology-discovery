#!/usr/bin/env python3
"""Offline CLI for deterministic OC3 autonomy policy evaluation."""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.autonomy_governor import (
    MANDATE_NOT_ACTIVE, NO_PERMIT_ISSUED, RANGE_CANDIDATE_PATH, STATE_PATH,
    AutonomyError, audit_staged_compact_artifacts, compact_status, evaluate_policy, validate_mandate,
    validate_state, validate_static_authorities,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Deterministic bounded-autonomy policy governor")
    modes = result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate", action="store_true")
    modes.add_argument("--status", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--audit-staged", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.validate:
            validate_static_authorities(); validate_mandate(); validate_state()
            result = {"network_requests": 0, "permit_issued": False,
                      "state": "AUTONOMY_BOOTSTRAP_VALIDATED"}
        elif args.status:
            result = compact_status()
            result["network_requests"] = 0
        elif args.dry_run:
            result = evaluate_policy(candidate_path=RANGE_CANDIDATE_PATH, state_path=STATE_PATH)
            result["network_requests"] = 0
            if result["decision"] != MANDATE_NOT_ACTIVE or result["permit_state"] != NO_PERMIT_ISSUED:
                raise AutonomyError("AUTONOMY_BOOTSTRAP_PREMATURE_ACTIVATION")
        else:
            result = audit_staged_compact_artifacts()
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except AutonomyError as exc:
        print(json.dumps({"error": exc.code, "state": exc.code},
                         sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
