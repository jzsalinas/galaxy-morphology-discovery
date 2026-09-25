#!/usr/bin/env python3
"""Production loop for the bounded source-metadata recovery mission."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable

sys.dont_write_bytecode=True

from oc3lib.cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed, write_json_immutable
from oc3lib.autonomous_recovery_envelope import FINALIZE_SCIENTIFIC, RECOVER_AUTONOMOUSLY, STOP_REQUIRES_HUMAN, RecoveryEnvelopeError
from oc3lib import source_metadata_recovery_governor_run003 as gov


def _record(ledger: Path, name: str, value: dict[str, object]):
    if value.get("run_id", gov.RUN_ID) != gov.RUN_ID:
        raise RecoveryEnvelopeError("RECOVERY_RUN_ID_MISMATCH")
    value={**value,"run_id":gov.RUN_ID}
    ledger.mkdir(parents=True,exist_ok=True)
    write_json_immutable(ledger/name,sealed(value))


def _synthetic_action(candidate_path: Path, candidate: dict[str, object], permit_path: Path,
        authorization_path: Path, state_path: Path, output: Path,
        executor: Callable[[dict[str, object]], dict[str, object]]):
    marker=gov.consume_permit(permit_path=permit_path,candidate_path=candidate_path,consumed_at_utc=gov.utc_now())
    output.mkdir(parents=True,exist_ok=False)
    capability=PROJECT/candidate["worker_capability_path"]
    gov.create_worker_capability(candidate_path=candidate_path,permit_path=permit_path,
        permit_marker=marker,authorization_path=authorization_path,state_path=state_path,
        capability_path=capability,issued_at_utc=gov.utc_now())
    gov.consume_worker_capability(capability_path=capability,candidate_path=candidate_path,consumed_at_utc=gov.utc_now())
    result=executor(candidate)
    if result.get("run_id") != candidate["run_id"]:
        raise RecoveryEnvelopeError("RECOVERY_RUN_ID_MISMATCH")
    terminal=sealed(result)
    write_json_immutable(output/"TERMINAL.json",terminal)


def _execute(candidate_path: Path, candidate: dict[str, object], permit_path: Path,
        authorization_path: Path, state_path: Path, output: Path, executor):
    if executor is not None:
        return _synthetic_action(candidate_path,candidate,permit_path,authorization_path,state_path,output,executor)
    result=subprocess.run(candidate["command_argv"],cwd=PROJECT,check=False,text=True,capture_output=True)
    if result.returncode != 0:
        raise RecoveryEnvelopeError("RECOVERY_SUPERVISOR_RUNTIME_FAILURE")


def _final_report(ledger: Path, state: dict[str, object], reason: str):
    trace=[]
    for path in sorted(ledger.glob("*_ACTION_TRANSITION.json")):
        row=load_canonical_json(path)
        trace.append({"classification":row["classification"],"terminal":row["terminal"]})
    write_json_immutable(ledger/"MISSION_FINAL_REPORT.json",sealed({"action_trace":trace,
        "active_adapter":state.get("active_adapter"),"material_body_bytes_remaining":state["material_body_bytes_remaining"],
        "material_requests_remaining":state["material_requests_remaining"],"mission_terminal_reason":reason,
        "permits_issued":state["permits_issued"],"recovery_graph_sha256":file_sha256(gov.RECOVERY_GRAPH),
        "recovery_generation":state["recovery_generation"],"run_id":gov.RUN_ID,
        "schema_version":"OC3_SOURCE_METADATA_RECOVERY_MISSION_FINAL_REPORT_003",
        "scientific_invariants_sha256":file_sha256(gov.INVARIANTS),"state":state["state"],
        "technical_body_bytes_remaining":state["technical_body_bytes_remaining"],
        "technical_requests_remaining":state["technical_requests_remaining"]}))


def _handoff_evidence(state: dict[str, object], terminal_path: Path) -> list[dict[str, str]]:
    paths=[]
    prior=state.get("last_action_terminal")
    if isinstance(prior,dict):
        prior_path=PROJECT/prior["path"]
        if prior_path.is_file(): paths.append(gov.binding(prior_path))
    documentary=terminal_path.parent/"DOCUMENTARY_EVIDENCE.json"
    if documentary.is_file(): paths.append(gov.binding(documentary))
    paths.append(gov.binding(terminal_path))
    return paths


def _run_mission(*, state_path: Path=gov.STATE, authorization_path: Path=gov.STANDING_AUTHORIZATION,
        first_candidate_path: Path=gov.FIRST_CANDIDATE, ledger: Path=gov.LEDGER_ROOT,
        executor: Callable[[dict[str, object]],dict[str, object]]|None=None) -> dict[str, object]:
    """Run until scientific terminal or governed STOP; executor is test injection only."""
    gov.validate_static_authorities()
    state=gov.validate_state(state_path)
    if state["state"] == gov.STATE_WAITING:
        gov.validate_standing_authorization(authorization_path,state_path=state_path)
        state=gov.activate(state_path=state_path,authorization_path=authorization_path,activated_at_utc=gov.utc_now())
        _record(ledger,"000_ACTIVATION.json",{"authorization_sha256":file_sha256(authorization_path),
            "event":"MISSION_ACTIVATED","state_sha256":file_sha256(state_path)})
    else:
        gov.validate_standing_authorization(authorization_path,state_path=state_path,require_initial_state=False)
        if state.get("standing_authorization") != gov.binding(authorization_path):
            raise RecoveryEnvelopeError("RECOVERY_STANDING_AUTHORIZATION_INVALID")
    while True:
        state=gov.validate_state(state_path)
        if state["state"] in (gov.STATE_TERMINAL,STOP_REQUIRES_HUMAN): return state
        if state["current_stage"] == "AWAITING_AGENTIC_TECHNICAL_REPAIR":
            try:
                resumed=gov.complete_agentic_handoff(state_path=state_path)
            except RecoveryEnvelopeError as exc:
                stopped=gov.stop_mission(state_path=state_path,reason=exc.code)
                _record(ledger,f"{stopped['sequence']:03d}_STOP.json",{
                    "event":"STOP_REQUIRES_HUMAN","reason":stopped["stop_reason"]})
                _final_report(ledger,stopped,str(stopped["stop_reason"])); return stopped
            if resumed["current_stage"] == "AWAITING_AGENTIC_TECHNICAL_REPAIR":
                return resumed
            _record(ledger,f"{resumed['sequence']:03d}_AGENTIC_REPAIR_ARTIFACTS_VALIDATED.json",{
                "event":"AGENTIC_REPAIR_ARTIFACTS_VALIDATED",
                "patch_manifest":resumed["validated_patch_manifest"],
                "test_receipts":resumed["validated_test_receipts"],
                "transport_contract":resumed["validated_transport_contract"]})
            state=resumed
        if state["current_stage"] == "AWAITING_NEXT_ACTION_REGISTRATION":
            if state["recovery_generation"] == 0:
                candidate_path=first_candidate_path; candidate=gov.validate_first_candidate(candidate_path)
            else:
                parent=state.get("last_action_terminal")
                if not isinstance(parent,dict): raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")
                candidate_path,candidate=gov.expected_child(state,PROJECT/parent["path"],state_path=state_path,
                    authorization_path=authorization_path)
                gov.write_candidate_idempotent(candidate_path,candidate)
                _record(ledger,f"{state['sequence']:03d}_CANDIDATE_GENERATED.json",{
                    "candidate":gov.binding(candidate_path),"event":"CANDIDATE_GENERATED",
                    "parent_action_terminal_sha256":state["last_action_terminal_sha256"]})
            state=gov.register_action(state_path=state_path,candidate_path=candidate_path)
            _record(ledger,f"{state['sequence']:03d}_ACTION_REGISTERED.json",{
                "candidate":gov.binding(candidate_path),"event":"ACTION_REGISTERED"})
        else:
            registered=state.get("registered_pending_action")
            if not isinstance(registered,dict): raise RecoveryEnvelopeError("RECOVERY_ACTION_REGISTRATION_INVALID")
            candidate_path=PROJECT/registered["path"]; candidate=gov.validate_candidate(candidate_path)
        permit_path=PROJECT/candidate["permit_path"]; output=PROJECT/candidate["output_directory"]
        terminal_path=output/"TERMINAL.json"
        if not terminal_path.exists():
            if permit_path.exists() and gov.permit_consumption_path(permit_path).exists():
                state=gov.stop_mission(state_path=state_path,reason="CONSUMED_ACTION_WITHOUT_TERMINAL_REPLAY_FORBIDDEN")
                _record(ledger,f"{state['sequence']:03d}_STOP.json",{"event":"STOP_REQUIRES_HUMAN",
                    "reason":state["stop_reason"]}); _final_report(ledger,state,str(state["stop_reason"])); return state
            if not permit_path.exists():
                gov.issue_permit(state_path=state_path,candidate_path=candidate_path,output_path=permit_path,
                    issued_at_utc=gov.utc_now())
                _record(ledger,f"{state['sequence']:03d}_PERMIT_ISSUED.json",{
                    "event":"PERMIT_ISSUED","permit":gov.binding(permit_path)})
            _execute(candidate_path,candidate,permit_path,authorization_path,state_path,output,executor)
        if not terminal_path.is_file(): raise RecoveryEnvelopeError("RECOVERY_ACTION_TERMINAL_MISSING")
        permit_marker=gov.permit_consumption_path(permit_path)
        capability=PROJECT/candidate["worker_capability_path"]
        capability_marker=gov.capability_consumption_path(capability)
        if not (permit_marker.is_file() and capability.is_file() and capability_marker.is_file()):
            raise RecoveryEnvelopeError("RECOVERY_ACTION_GATE_EVIDENCE_MISSING")
        _record(ledger,f"{state['sequence']:03d}_{candidate['stage_id']}_GATES_CONSUMED.json",{
            "capability":gov.binding(capability),"capability_consumption":gov.binding(capability_marker),
            "event":"ACTION_GATES_CONSUMED","permit_consumption":gov.binding(permit_marker)})
        _record(ledger,f"{state['sequence']:03d}_{candidate['stage_id']}_ACTION_COMPLETED.json",{
            "event":"ACTION_COMPLETED","terminal":gov.binding(terminal_path)})
        terminal=load_canonical_json(terminal_path)
        if (candidate["action_kind"] == "OFFICIAL_SERVICE_DOCUMENTARY_PROBE" and
                terminal.get("failure_class") == "DOCUMENTARY_EVIDENCE_ACQUIRED"):
            state=gov.begin_agentic_handoff(state_path=state_path,candidate_path=candidate_path,
                terminal_path=terminal_path,evidence=_handoff_evidence(state,terminal_path))
            if state["current_stage"] != "AWAITING_AGENTIC_TECHNICAL_REPAIR":
                _record(ledger,f"{state['sequence']:03d}_ACTION_TRANSITION.json",{
                    "classification":state["last_classification"],"event":"ACTION_TRANSITION",
                    "terminal":gov.binding(terminal_path)})
                _final_report(ledger,state,str(state["stop_reason"])); return state
            _record(ledger,f"{state['sequence']:03d}_AGENTIC_REPAIR_HANDOFF.json",{
                "agentic_repair_request":state["agentic_repair_request"],
                "event":"AGENTIC_REPAIR_REQUIRED","standing_authorization":state["standing_authorization"]})
            return state
        state,classification=gov.transition_action(state_path=state_path,candidate_path=candidate_path,
            terminal_path=terminal_path)
        _record(ledger,f"{state['sequence']:03d}_ACTION_TRANSITION.json",{
            "classification":classification,"event":"ACTION_TRANSITION",
            "terminal":gov.binding(terminal_path)})
        decision=classification["decision"]
        if decision == RECOVER_AUTONOMOUSLY: continue
        if decision == FINALIZE_SCIENTIFIC:
            terminal=load_canonical_json(terminal_path)
            final=gov.finalize_mission(state_path=state_path,outcome=terminal["failure_class"])
            _record(ledger,f"{final['sequence']:03d}_MISSION_FINALIZED.json",{
                "event":"MISSION_FINALIZED","scientific_invariants_sha256":file_sha256(gov.INVARIANTS),
                "recovery_graph_sha256":file_sha256(gov.RECOVERY_GRAPH),"state_sha256":file_sha256(state_path)})
            _final_report(ledger,final,terminal["failure_class"])
            return final
        stopped=gov.validate_state(state_path); _final_report(ledger,stopped,str(stopped["stop_reason"])); return stopped


def run_mission(*, state_path: Path=gov.STATE, authorization_path: Path=gov.STANDING_AUTHORIZATION,
        first_candidate_path: Path=gov.FIRST_CANDIDATE, ledger: Path=gov.LEDGER_ROOT,
        executor: Callable[[dict[str, object]],dict[str, object]]|None=None) -> dict[str, object]:
    try:
        return _run_mission(state_path=state_path,authorization_path=authorization_path,
            first_candidate_path=first_candidate_path,ledger=ledger,executor=executor)
    except Exception as exc:
        _record(ledger,"RUNNER_CRASH.json",{"error":getattr(exc,"code",type(exc).__name__),
            "event":"UNCONTRACTED_RUNNER_CRASH","state_sha256":file_sha256(state_path) if state_path.exists() else None})
        raise


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-mission",action="store_true",required=True)
    parser.add_argument("--state",type=Path,default=gov.STATE)
    parser.add_argument("--standing-authorization",type=Path,default=gov.STANDING_AUTHORIZATION)
    parser.add_argument("--resume",action="store_true")
    args=parser.parse_args(argv)
    try:
        state=run_mission(state_path=args.state,authorization_path=args.standing_authorization)
        result="AGENTIC_REPAIR_REQUIRED" if state["current_stage"]=="AWAITING_AGENTIC_TECHNICAL_REPAIR" else state["state"]
        print(json.dumps({"mission_state":state["state"],"network_mode":"AUTHORIZED_PRODUCTION",
            "runner_result":result},sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"error":getattr(exc,"code",str(exc)),"state":"RUNNER_BLOCKED"},sort_keys=True),file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
