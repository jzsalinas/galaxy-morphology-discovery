#!/usr/bin/env python3
"""Offline CLI for the frozen OC3 supervised pilot-frame schema recovery governor."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode=True
for _key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[_key]="1"

from oc3lib.source_metadata_pilot_frame_schema_recovery_governor import (
    AUTONOMY_BRANCH, LEDGER_ROOT, MANDATE_NOT_ACTIVE, NO_PERMIT_ISSUED, STATE_PATH,
    STANDING_AUTHORIZATION_PATH, GovernorError, activate_standing_autonomy,
    audit_staged_compact_artifacts, compact_status, consume_permit, enter_stop_requires_human,
    evaluate_policy, finalize_scientific_terminal, issue_permit, register_pending_action,
    transition_completed_action, validate_mandate, validate_state, validate_static_authorities,
)

def parser() -> argparse.ArgumentParser:
    result=argparse.ArgumentParser(description="Deterministic offline OC3 pilot-frame schema recovery autonomy governor")
    modes=result.add_mutually_exclusive_group(required=True)
    for name in ("validate","status","dry-run","activate-standing-authorization","register-action",
                 "evaluate","issue-permit","consume-permit","transition-completed-action","audit-staged","enter-stop",
                 "finalize-scientific-terminal"):
        modes.add_argument("--"+name,action="store_true")
    result.add_argument("--candidate",type=Path)
    result.add_argument("--state",type=Path,default=STATE_PATH)
    result.add_argument("--standing-authorization",type=Path,default=STANDING_AUTHORIZATION_PATH)
    result.add_argument("--permit",type=Path)
    result.add_argument("--permit-output",type=Path)
    result.add_argument("--ledger-directory",type=Path,default=LEDGER_ROOT)
    result.add_argument("--terminal",type=Path)
    result.add_argument("--terminal-sha256")
    result.add_argument("--request-delta",type=int,default=0)
    result.add_argument("--body-delta",type=int,default=0)
    result.add_argument("--retry-delta",type=int,default=0)
    result.add_argument("--stop-report",type=Path)
    result.add_argument("--blocker-code")
    result.add_argument("--outcome")
    result.add_argument("--final-report",type=Path)
    result.add_argument("--claim-matrix",type=Path)
    result.add_argument("--branch")
    result.add_argument("--at-utc")
    return result

def _now(value: str|None) -> str:
    return value or datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def _branch(value: str|None) -> str:
    if value is not None: return value
    return subprocess.run(["git","branch","--show-current"],cwd=Path(__file__).resolve().parents[1],
                          check=True,capture_output=True,text=True).stdout.strip()

def _candidate(args) -> Path:
    if args.candidate is not None: return args.candidate
    state=validate_state(args.state); registered=state.get("registered_pending_action")
    if not isinstance(registered,dict): return Path(__file__).resolve().parents[1]/str(state["first_candidate"]["path"])
    return Path(__file__).resolve().parents[1]/str(registered["candidate_path"])

def main(argv: list[str]|None=None) -> int:
    args=parser().parse_args(argv)
    try:
        if args.validate:
            validate_static_authorities(); validate_mandate(); validate_state(args.state)
            output={"network_requests":0,"permit_issued":False,"state":"AUTONOMY_HARDENING_VALIDATED"}
        elif args.status:
            output=compact_status(args.state); output["network_requests"]=0
        elif args.audit_staged:
            output=audit_staged_compact_artifacts()
        elif args.dry_run or args.evaluate:
            output=evaluate_policy(candidate_path=_candidate(args),state_path=args.state,
                standing_authorization_path=args.standing_authorization,current_branch=_branch(args.branch))
            output["network_requests"]=0
            if args.dry_run and (output["decision"]!=MANDATE_NOT_ACTIVE or output["permit_state"]!=NO_PERMIT_ISSUED):
                raise GovernorError("AUTONOMY_BOOTSTRAP_PREMATURE_ACTIVATION")
        elif args.activate_standing_authorization:
            output=activate_standing_autonomy(state_path=args.state,
                standing_authorization_path=args.standing_authorization,ledger_directory=args.ledger_directory,
                activated_at_utc=_now(args.at_utc),current_branch=_branch(args.branch))
        elif args.register_action:
            output=register_pending_action(state_path=args.state,candidate_path=_candidate(args),
                standing_authorization_path=args.standing_authorization,ledger_directory=args.ledger_directory,
                registered_at_utc=_now(args.at_utc),current_branch=_branch(args.branch))
        elif args.issue_permit:
            if args.permit_output is None: raise GovernorError("AUTONOMOUS_PERMIT_OUTPUT_REQUIRED")
            output=issue_permit(candidate_path=_candidate(args),state_path=args.state,
                standing_authorization_path=args.standing_authorization,output_path=args.permit_output,
                ledger_directory=args.ledger_directory,issued_at_utc=_now(args.at_utc),
                current_branch=_branch(args.branch))
        elif args.consume_permit:
            if args.permit is None: raise GovernorError("AUTONOMOUS_PERMIT_REQUIRED")
            marker=consume_permit(args.permit,candidate_path=_candidate(args),state_path=args.state,
                standing_authorization_path=args.standing_authorization,consumed_at_utc=_now(args.at_utc))
            output={"consumption_marker":str(marker),"network_requests":0,"state":"PERMIT_CONSUMED"}
        elif args.transition_completed_action:
            if args.permit is None or args.terminal is None or args.terminal_sha256 is None:
                raise GovernorError("AUTONOMY_TRANSITION_ARGUMENT_REQUIRED")
            output=transition_completed_action(state_path=args.state,candidate_path=_candidate(args),
                permit_path=args.permit,standing_authorization_path=args.standing_authorization,
                terminal_path=args.terminal,
                terminal_sha256=args.terminal_sha256,
                request_delta=args.request_delta,body_delta=args.body_delta,retry_delta=args.retry_delta,
                ledger_directory=args.ledger_directory,transitioned_at_utc=_now(args.at_utc),
                reason="GOVERNED_ACTION_COMPLETED")
        elif args.enter_stop:
            if args.stop_report is None or args.blocker_code is None:
                raise GovernorError("AUTONOMY_STOP_ARGUMENT_REQUIRED")
            output=enter_stop_requires_human(state_path=args.state,
                standing_authorization_path=args.standing_authorization,stop_report_path=args.stop_report,
                blocker_code=args.blocker_code,ledger_directory=args.ledger_directory,
                stopped_at_utc=_now(args.at_utc),current_branch=_branch(args.branch))
        else:
            if args.outcome is None or args.final_report is None:
                raise GovernorError("SCIENTIFIC_TERMINAL_ARGUMENT_REQUIRED")
            output=finalize_scientific_terminal(state_path=args.state,
                standing_authorization_path=args.standing_authorization,outcome=args.outcome,
                final_report_path=args.final_report,claim_matrix_path=args.claim_matrix,
                ledger_directory=args.ledger_directory,finalized_at_utc=_now(args.at_utc),
                current_branch=_branch(args.branch))
        print(json.dumps(output,sort_keys=True,separators=(",",":")))
        return 0
    except GovernorError as exc:
        print(json.dumps({"error":exc.code,"state":exc.code},sort_keys=True,separators=(",",":")),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
