# OC3 Observational Multiplicity Autonomous Research Runbook 001

All commands run from the repository root with `oc3/.venv/bin/python`. Bootstrap validation is offline.

## Before activation

1. Validate the policy core, mandate, waiting state, and candidate 002:
   `oc3/.venv/bin/python oc3/oc3_observational_multiplicity_governor.py --validate`
2. Inspect compact status:
   `oc3/.venv/bin/python oc3/oc3_observational_multiplicity_governor.py --status`
3. Stop. A separate reviewed standing authorization is required.

## Governed lifecycle

After authorization, activation binds the exact waiting state and first candidate but does not register or execute it. Each action then follows: action-specific validation receipt; registration; generic evaluation; permit issuance at the candidate-declared path; canonical permit consumption; material execution; immutable terminal; completion transition.

The canonical marker is derived only from the permit SHA under `oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_LEDGER/PERMIT_CONSUMPTION/`. A consumed permit is never replayed. Registration and permit issuance do not consume network/body budgets; verified terminal counters drive completion accounting.

The first action remains the offline global-view relation audit and reads only the frozen identity/geometry columns. Later official-documentation or grouping-metadata actions need new prospective specifications, validators, receipts, candidates, and literal manifests when networked. They do not require policy-core modification.

## Failure and terminal handling

Policy mutation, authority expansion, exhausted reservation/budget, dirty firewall, altered Git assertions, missing canonical consumption, or invalid terminal evidence fails closed. A compact bound report enters `STOP_REQUIRES_HUMAN`. Finalization accepts only the four mandate outcomes, no pending action, a clean firewall, a bound final report, and the decision/evidence matrix when the mission specification requires one.

Compact governance artifacts may enter Git. Heavy runtime evidence stays local. Do not push, merge main, rewrite history, or modify the closed PHOTSYS mission.
