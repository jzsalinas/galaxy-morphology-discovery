#!/usr/bin/env python3
"""Governed offline assessment of the observational-multiplicity grouping gate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from oc3lib.core import canonical
from oc3lib import observational_multiplicity as multiplicity
from oc3lib import observational_multiplicity_governor as governor

PROJECT = multiplicity.PROJECT
STAGE_ID = "OC3-OBSERVATIONAL-MULTIPLICITY-GROUPING-GATE-ASSESSMENT-001"
SCOPE = "OFFLINE_GROUPING_GATE_ASSESSMENT_ONLY"
SPEC = PROJECT / "OC3_OBSERVATIONAL_MULTIPLICITY_GROUPING_GATE_ASSESSMENT_SPEC_001.md"
CANDIDATE_004 = PROJECT / "oc3/INPUTS/OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_004.json"
PRIOR_ROOT = PROJECT / "oc3/observational_multiplicity/OC3-GLOBAL-VIEW-RELATION-AUDIT-001"
PRIOR_TERMINAL = PRIOR_ROOT / "TERMINAL.json"
PRIOR_AGGREGATE = PRIOR_ROOT / "AGGREGATE_EVIDENCE.json"
EXPECTED_PRIOR_TERMINAL_SHA = "dd2ae9647a2e41937e1bf157ca0e34e88530c3fc304b819ebd5c0cad40a68827"
EXPECTED_PRIOR_AGGREGATE_SHA = "21677c5304a975dd16cffd55f9f3a2fa9d4f3fd10f4fa0714e9a7546fc4b5d5c"
EXPECTED_CANDIDATE_004_SHA = "6e3a8c7209630b162e659322ac09ff4a8314255d3739ef1ac3c587b8cd1965df"
GROUPING_GATE = "CROSS_OBSERVER_SOURCE_GROUPING_REQUIRES_PROSPECTIVE_CONTRACT"


class RuntimeCommandBindingError(Exception):
    def __init__(self, code: str = "RUNTIME_COMMAND_BINDING_MISMATCH"):
        self.code = code
        super().__init__(code)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    modes = value.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-candidate", action="store_true")
    modes.add_argument("--assess-grouping-gate", action="store_true")
    value.add_argument("--candidate", type=Path, required=True)
    value.add_argument("--permit", type=Path)
    value.add_argument("--standing-authorization", type=Path)
    value.add_argument("--autonomy-state", type=Path)
    value.add_argument("--output-directory", type=Path)
    return value


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    return parser().parse_args(argv)


def validate_runtime_invocation(candidate: dict[str, object], *, executable: str,
                                script_path: str, argument_vector: list[str]) -> None:
    if [executable, script_path, *argument_vector] != candidate.get("command_argv"):
        raise RuntimeCommandBindingError()


def _load_bound(path: Path, expected_sha: str) -> dict[str, object]:
    if multiplicity.file_sha256(path) != expected_sha:
        raise multiplicity.MultiplicityError("GROUPING_GATE_INPUT_MISMATCH")
    return multiplicity.validate_sealed(multiplicity.load_canonical_json(path))


def _prove_selection_and_split_guards() -> dict[str, bool]:
    first = multiplicity.GlobalBrickIdentity(b"0001p001", 1)
    second = multiplicity.GlobalBrickIdentity(b"0002p001", 2)
    geometry = (1.0, 2.0, 0.9, 1.1, 1.9, 2.1)
    north = multiplicity.RegionalBrickView("north", first, geometry, True)
    south = multiplicity.RegionalBrickView("south", first, geometry, True)
    entries = (
        multiplicity.RelationEntry(first, multiplicity.VIEW_BOTH, (north, south), False),
        multiplicity.RelationEntry(second, multiplicity.VIEW_NONE, (), False),
    )
    multiplicity.validate_selection_contract(("brickname", "brickid"))
    selected = multiplicity.select_global_identities(entries, 1)
    retained = multiplicity.retain_all_valid_views(selected)
    if len(selected) != 1 or selected[0].identity != first or len(retained) != 2:
        raise multiplicity.MultiplicityError("GROUPING_GATE_SELECTION_INVARIANT_FAILED")
    for role in ("PROVENANCE", "CONFOUND_AUDIT", "REPLICATION_AUDIT"):
        multiplicity.validate_observer_domain_role(role)
    try:
        multiplicity.validate_split_assignments([(None, "test")], confirmatory=True)
    except multiplicity.MultiplicityError as exc:
        if exc.code != "UNRESOLVED_GROUPING_BLOCKS_CONFIRMATORY_SPLIT":
            raise
    else:
        raise multiplicity.MultiplicityError("GROUPING_GATE_SPLIT_INVARIANT_FAILED")
    try:
        multiplicity.validate_split_assignments([("g1", "train"), ("g1", "test")], confirmatory=True)
    except multiplicity.MultiplicityError as exc:
        if exc.code != "SPLIT_GROUP_LEAKAGE":
            raise
    else:
        raise multiplicity.MultiplicityError("GROUPING_GATE_SPLIT_INVARIANT_FAILED")
    return {
        "confirmatory_split_blocked_without_group": True,
        "global_identity_selected_once": True,
        "observer_domain_excluded_from_selection": True,
        "observer_domain_roles_closed": True,
        "same_group_cross_split_rejected": True,
        "valid_views_retained_after_selection": True,
    }


def run_assessment(output_directory: Path) -> dict[str, object]:
    prior_terminal = _load_bound(PRIOR_TERMINAL, EXPECTED_PRIOR_TERMINAL_SHA)
    prior_aggregate = _load_bound(PRIOR_AGGREGATE, EXPECTED_PRIOR_AGGREGATE_SHA)
    candidate_004 = _load_bound(CANDIDATE_004, EXPECTED_CANDIDATE_004_SHA)
    if (prior_terminal.get("state") != "GLOBAL_VIEW_RELATION_VALIDATED" or
            prior_terminal.get("aggregate_sha256") != EXPECTED_PRIOR_AGGREGATE_SHA or
            prior_aggregate.get("aggregate", {}).get("identity_conflicts") != 0 or
            prior_aggregate.get("aggregate", {}).get("geometry_conflicts") != 0 or
            any(prior_terminal.get("counters", {}).get(key, 0) != 0 for key in governor.FIREWALL_KEYS) or
            GROUPING_GATE not in candidate_004.get("unresolved_gates", [])):
        raise multiplicity.MultiplicityError("GROUPING_GATE_PRIOR_EVIDENCE_INVALID")
    guards = _prove_selection_and_split_guards()
    counters = {key: 0 for key in governor.FIREWALL_KEYS}
    counters.update({"application_body_bytes_read": 0, "network_requests_started": 0,
                     "retry_requests": 0, "summary_value_reads": 0})
    assessment = multiplicity.sealed({
        "closed_evidence_has_validated_grouping_contract": False,
        "global_view_relation_terminal": {"path": str(PRIOR_TERMINAL.relative_to(PROJECT)),
                                          "sha256": EXPECTED_PRIOR_TERMINAL_SHA},
        "grouping_gate": GROUPING_GATE,
        "guards": guards,
        "result": "GROUPING_EVIDENCE_REQUIRED",
        "scope": SCOPE,
        "stage_id": STAGE_ID,
    })
    terminal = multiplicity.sealed({
        "application_body_bytes_read": 0,
        "assessment_sha256": multiplicity.sha256_bytes(canonical(assessment) + b"\n"),
        "counters": counters,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": "GROUPING_EVIDENCE_REQUIRED",
    })
    output_directory = Path(output_directory)
    multiplicity.write_json_immutable(output_directory / "ASSESSMENT.json", assessment)
    multiplicity.write_json_immutable(output_directory / "TERMINAL.json", terminal)
    return terminal


def main(argv: list[str] | None = None, *, assessment_runner=None, now_utc=None) -> int:
    actual_arguments = list(sys.argv[1:] if argv is None else argv)
    args = parse_arguments(actual_arguments)
    candidate, _ = governor.validate_candidate(args.candidate)
    if args.validate_candidate:
        result = {"candidate_sha256": multiplicity.file_sha256(args.candidate),
                  "network_requests": 0, "stage_id": candidate["stage_id"],
                  "state": "GROUPING_GATE_CANDIDATE_VALIDATED"}
    else:
        if any(item is None for item in (args.permit, args.standing_authorization,
                                         args.autonomy_state, args.output_directory)):
            raise SystemExit("execution bindings required")
        validate_runtime_invocation(candidate, executable=sys.executable,
                                    script_path=sys.argv[0], argument_vector=actual_arguments)
        governor.validate_permit(args.permit, candidate_path=args.candidate,
            state_path=args.autonomy_state, standing_authorization_path=args.standing_authorization)
        consumed_at = (now_utc or (lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")))()
        governor.consume_permit(args.permit, candidate_path=args.candidate,
            state_path=args.autonomy_state, standing_authorization_path=args.standing_authorization,
            consumed_at_utc=consumed_at)
        result = (assessment_runner or run_assessment)(args.output_directory)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
