# OC3 autonomous research runbook 001 — lifecycle revision 002

All commands run from the repository root with `oc3/.venv/bin/python`. They are offline except an action executor whose sealed candidate and permit explicitly authorize network.

## Start and activation

1. `oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --validate`
2. `oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --status`
3. After the reviewed standing authorization exists, activate once:
   `oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --activate-standing-authorization`

Activation verifies the exact mandate, policy core, waiting state, branch, and first candidate; records zero budget delta; and atomically enters `ACTIVE`. Never edit state JSON manually.

## Per-action loop

1. Read sealed state and prior terminal.
2. If a scientific terminal is justified, finalize and stop. If a mandate stop applies, create the compact STOP report, enter STOP, and stop.
3. Choose the smallest operation resolving the next material uncertainty. Reuse preserved evidence and prefer offline source search or metadata before acquisition.
4. Freeze the action specification, literal resources, implementation, action-validation receipt, and candidate with `OC3_AUTONOMOUS_ACTION_CONTRACT_001`.
5. Run action-specific offline validation and focused tests.
6. When no pending action exists, register it:
   `oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --register-action --candidate <candidate>`
7. Evaluate:
   `oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --evaluate --candidate <candidate>`
8. Issue exactly one immutable permit at the candidate-declared path:
   `oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --issue-permit --candidate <candidate> --permit-output <permit>`
9. Execute once through the action-specific executor. It must consume the permit before material work.
10. Audit the terminal and transition:
    `oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --transition-completed-action --candidate <candidate> --permit <permit> --consumption-directory <dir> --terminal <terminal> --terminal-sha256 <sha256> --request-delta N --body-delta N --retry-delta N`
11. Confirm budgets/state/ledger, commit compact artifacts after `--audit-staged`, optionally push only `autopilot/photsys-zero-byte`, and continue.

## STOP and scientific terminal

Enter STOP only with an exact compact report and blocker:
`oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --enter-stop --stop-report AUTOPILOT_STOP_REPORT.md --blocker-code <CODE>`.

Finalize only with one frozen outcome, no pending action, clean firewall, and bound report/claim matrix:
`oc3/.venv/bin/python oc3/oc3_autonomy_governor.py --finalize-scientific-terminal --outcome <OUTCOME> --final-report <report> --claim-matrix <matrix>`.

Both transitions set `active=false`; do not continue. A consumed permit without a valid terminal is never replayed automatically. Without a frozen restart rule, enter STOP.

## Runtime profile

Use `workspace-write`; enable network only for a permitted executor; allow long-horizon execution without routine approval inside the sandbox. The project governor remains the scientific authorization mechanism. `danger-full-access` is not required.
