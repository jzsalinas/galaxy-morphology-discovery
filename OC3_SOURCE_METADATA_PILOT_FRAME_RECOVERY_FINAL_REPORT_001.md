# OC3 Source-Metadata Pilot-Frame Recovery Final Report 001

## Scientific terminal

`SOURCE_METADATA_PILOT_FRAME_RECOVERY_INTEGRITY_FAILED`

The authorized supervisor was executed exactly once. It consumed the new
single-use permit before launching the frozen worker, created the immutable
start intent, captured bounded child-process evidence, and wrote a sealed
terminal. The worker returned code 2 with the explicit error
`BOUND_IDENTITY_COLUMNS_MISSING`; no `PILOT_FRAME.json` was produced.

This is an input-contract violation under the frozen recovery runbook. The
worker had already accepted the bound root table and then failed the explicit
`BRICKNAME`/`BRICKID` presence check on the first regional identity table
(`NORTH_SUMMARY`). The observation establishes only that at least one required
identity column was absent from that table. This execution did not inspect or
record the complete column list, so it does not identify which required column
was absent.

## Frame result

- Pilot target 1: not materialized.
- Pilot target 2: not materialized.
- Reserved holdout 1: not materialized.
- Reserved holdout 2: not materialized.
- Guard memberships and counts: unavailable because selection never began.
- Frozen selection semantics: unchanged and unexecuted beyond the failed input
  invariant.

The missing frame means the mission did not demonstrate that the exact frozen
pilot frame can be recovered from the four bound local authorities. It also
does not authorize a schema substitution, a relaxed identity, or another
execution.

## Execution evidence

- Candidate SHA-256:
  `96e717653be65eaf75b27a21c6b0e5a603b4afbb815e5f5e9a06c2b21add3c3f`.
- Standing authorization SHA-256:
  `5a2af9bd9fca3a336c094d06821bfb83c63f572e24eb8f589206bd4f2cea6ab0`.
- Permit SHA-256:
  `8160d22f84a5f441338a985101311e071d69c2372b5a0f65267736ff9e859514`.
- Permit consumption marker SHA-256:
  `59bba0256e676ffef5ecfb897644f1d7ee6adbe1c6531946440bb52b1be85688`.
- Start intent SHA-256:
  `6aefa031fd9cb63e6d332ef8da5d98e56277ad140c1d5e09b7fa02cc02dc484c`.
- Execution diagnostic SHA-256:
  `37ee3d96c266f76a6542a71e263cb0f035f957eb1d6353a9bff1d3f586bb75eb`.
- Action terminal SHA-256:
  `a2eb33ba99e3701820100500209ba4222becfceb105994d6a9206a7ad4175c53`.
- Worker command SHA-256:
  `d65d95952361a30073a017de4c57cd1bbd99c06fbad4b3d4f6f03f3239add847`.
- Implementation aggregate:
  `3dfb6e1d47701b2fba2d8d90daf3228e5fb1fc361a72f1edfd350cbd40c8ae48`.
- Child return code: 2; terminating signal: none.
- Wall-clock duration: 3.148651571 seconds.
- Linux completed-child peak RSS: 291448 KiB. This measurement is not an
  OOM inference.
- Standard output: 0 bytes, SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Standard error: 82 bytes, SHA-256
  `b8b0e3129cb5524be7950edcbab4827df4c059d84bea590a39b8bb2828cf22b2`.
- Both streams were captured below the frozen 262144-byte per-stream cap and
  neither was truncated.

## Firewall and provenance boundary

Network requests, application body bytes, retries, source rows, PHOTSYS,
denied catalog values, pixels, morphology, labels, matching, group IDs, Panel
V3, P1, model operations, training, embeddings, and clustering all remained
zero. No astronomical object, target, holdout, or guard was materialized.

The predecessor remains immutable at `STOP_REQUIRES_HUMAN`. Its technical
cause remains `UNKNOWN`. The present `BOUND_IDENTITY_COLUMNS_MISSING` result is
evidence from this separate authorized recovery attempt and is not a
retrospective explanation of the predecessor interruption.

No replay, fallback, schema repair, new candidate, or downstream stage is
authorized by this terminal.
