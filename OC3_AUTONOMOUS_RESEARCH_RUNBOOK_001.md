# OC3 autonomous research runbook 001

## Operating loop

1. Read and validate the current sealed autonomy state.
2. Inspect the previous action terminal and its immutable bindings.
3. If one frozen scientific terminal is supported, finalize the provenance report and claim matrix, update state and ledger, commit compact artifacts, and stop.
4. If a human-stop condition applies, write `AUTOPILOT_STOP_REPORT.md`, update state to `STOP_REQUIRES_HUMAN`, commit, and stop.
5. Formulate the smallest next epistemic question.
6. Freeze any required specification or amendment before observation.
7. Implement the bounded action.
8. Run synthetic tests, affected/full offline regression when code changes, and dry-run.
9. Seal the literal resource manifest and candidate.
10. Run deterministic governor evaluation against the current state and active mandate.
11. Issue one single-use autonomous permit only when every check passes.
12. Atomically record permit-consumption intent, then execute once.
13. Audit output seals, identities, counters, and scientific firewall.
14. Update cumulative budgets, state, and append-only transition ledger.
15. Commit only compact control-plane artifacts after staged-size audit.
16. Optionally push only `autopilot/photsys-zero-byte`; record `REMOTE_SYNC_PENDING` if unavailable.
17. Continue without routine human approval while inside the active envelope.

## Selection policy

Always choose the smallest action that resolves the next material uncertainty: metadata before acquisition, preserved bodies before reacquisition, offline exact-tree search before another resource, and immutable blobs or commits before mutable rendered pages. Broad crawling is prohibited. A discovery result is not evidence until a literal admissible identity is frozen in a manifest and candidate.

Synthetic scientific demonstrations require a prospective specification, zero real astronomical data, a permit when their result enters the claim matrix, and output limited to the declared claim. The optional NumPy zero-initialization demonstration remains non-gating by itself.

## Crash and replay

Permits are single-use. Record consumption intent before an epistemically material operation. Preserve partial output and charged counters after interruption. Replay is allowed only when a prospectively frozen restart rule exists and the governor returns `RECOVERABLE_WITHIN_MANDATE`; otherwise enter `STOP_REQUIRES_HUMAN`. Never reset mission counters.

## Mandatory stops

Stop for request/body-budget expansion, protected or astronomical data access, Panel V2, P1, resolver work, post-evidence criterion changes, new authority classes, credentials, destructive evidence handling, force push/history rewrite, integrity conflicts requiring authority changes, sandbox escalation outside the envelope, or a changed scientific question. The stop report names the exact blocker, clause, remaining budgets, and minimum human amendment.

## Runtime and Git profile

Use Codex Local with `workspace-write` sandboxing. Network may be enabled only after the standing authorization is active and only through a permitted action. Approval behavior must allow long-horizon work within workspace and network constraints; danger-full-access is not a requirement. Git is the compact control plane; large runtime evidence, FITS files, archives, and attempt trees remain local. Never merge to `main` autonomously.
