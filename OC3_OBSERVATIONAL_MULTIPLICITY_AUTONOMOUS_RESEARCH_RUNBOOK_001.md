# OC3 Observational Multiplicity Autonomous Research Runbook 001

All commands run from the repository root with `oc3/.venv/bin/python`. Bootstrap validation is offline.

## Before activation

1. Validate the policy core, mandate, state, and first candidate:
   `oc3/.venv/bin/python oc3/oc3_observational_multiplicity_governor.py --validate`
2. Inspect status:
   `oc3/.venv/bin/python oc3/oc3_observational_multiplicity_governor.py --status`
3. Stop. A separate human-reviewed standing authorization is required.

## Activation and actions

After a valid standing authorization exists, activation binds the current waiting state and first candidate and enters `ACTIVE`. Each material action is then validated, registered, evaluated, issued one immutable permit, consumed before material access, and transitioned from an immutable terminal artifact.

The first candidate is `OC3-GLOBAL-VIEW-RELATION-AUDIT-001`. Although offline, it reads real local identity/geometry values and therefore requires a permit. Bootstrap tests use synthetic rows only and do not execute it.

## STOP and terminals

Policy mismatch, evidence-envelope expansion, protected-value access, altered criteria, or exhausted budget enters `STOP_REQUIRES_HUMAN`. Scientific finalization accepts only the four mandate outcomes and requires no pending action.

## Git and runtime evidence

Compact specifications, code, tests, state, ledger records, and reports belong in Git. Heavy runtime evidence remains local. Do not push, merge main, rewrite history, or modify the closed PHOTSYS mission.
