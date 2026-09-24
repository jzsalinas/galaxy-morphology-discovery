# OC3 Source-Metadata Pilot-Frame Recovery Bootstrap Report 001

## Result

Mission `OC3-SOURCE-METADATA-FRAME-RECOVERY-AUTONOMY-001` was bootstrapped on `autopilot/source-metadata-frame-recovery` from exact predecessor STOP commit `c4e48be25afc355e82445b1e6efe6f794e55b307`. It is inactive. No standing authorization or real permit exists and no real FITS authority was opened by the recovery implementation.

The predecessor STOP report remains SHA-256 `3e108bb586e083b67de5c040a2ae4eb0f94022604b12e781e1798d102392aae9`; the historical consumed permit remains `8e96a042d50e436b9fbd8ee65ccd53be5d9e2ae9a6152968511d7faa001a0f4d`. `TECHNICAL_CAUSE = UNKNOWN`.

Engineering analysis, without causal attribution, identified object-heavy amplification in the historical full-table lists of dictionaries, identity dictionaries and per-row geometry objects. The recovery retains only fixed-width/NumPy column arrays and materializes geometry dictionaries solely for the selected identities and guard members.

## Frozen identities

- Scientific specification: `2c56345ec5cb8e254fbd916a1fc5296d4b3ba1b282e683f11f536d2df3d5d13c`.
- Policy Core contract: `aa5285125109a8699f5651370e393835a409a92f162c83938af266af96cad98f`.
- Policy Core manifest: `6434887411650a97a816bdd49b952f2a6d71ca133136ccff64b200627407330c`.
- Pending mandate: `10de73943f01b70219975e01931e096ff5d64e31b9f621779bc88ad60695f6c9`.
- Waiting state: `65595ef648fa8b671cf1278b21503093a83c1da3d0fa4a8e0d3ac843bf0ca1f8`.
- First candidate: `96e717653be65eaf75b27a21c6b0e5a603b4afbb815e5f5e9a06c2b21add3c3f`.
- Supervisor/worker implementation aggregate: `3dfb6e1d47701b2fba2d8d90daf3228e5fb1fc361a72f1edfd350cbd40c8ae48`.
- Supervisor command argv SHA-256: `1999e3d16713e4c550eda2637e4dab2d5ce460ba6352e2e34b875a458147483c`.
- Worker command SHA-256: `d65d95952361a30073a017de4c57cd1bbd99c06fbad4b3d4f6f03f3239add847`.

## Diagnostic contract

The supervisor consumes the new permit before worker launch, creates the output and immutable `START_INTENT.json`, launches one exact worker, bounds each captured stream to 262,144 stored bytes while hashing and counting the complete stream, records return code, signal, wall time and Linux `ru_maxrss` in KiB, validates the compact frame and writes `EXECUTION_DIAGNOSTIC.json` plus `TERMINAL.json`. Nonzero exit and signal tests demonstrate retained failure evidence. No automatic retry or object-heavy fallback exists.

## Verification

- Focused recovery suite: 22 passed, 0 failed, 0 skipped.
- Recovery plus affected predecessor and INPUTS-integrity suites: 175 passed, 0 failed, 0 skipped.
- Full guarded offline regression: 1,388 passed, 0 failed, 0 skipped, `real_network_requests=0`.
- Candidate preflight: `READY_AT_SUPERVISED_FRAME_RECOVERY_BOUNDARY`, network 0, real frame reads 0.
- Governor validation: `AUTONOMY_HARDENING_VALIDATED`, permit issued false.
- Governor dry run: `MANDATE_NOT_ACTIVE`, `NO_PERMIT_ISSUED`.

Synthetic coverage includes reference/optimized eligible identities, exact digest order, wrap/touch/row guard membership, collisions, development exclusion, duplicate rejection, disjoint 2+2 selection, output geometry, a 200,000-row compact-array engineering regression, exact supervisor and worker commands, permit-before-worker ordering, bounded streams, nonzero exit, signal capture, diagnostic creation, invalid-output rejection, single-use architecture and scientific terminal closure.

Observed during bootstrap: network 0, real frame reads 0, targets materialized 0, holdouts materialized 0, source rows 0, matching 0, radius 0, threshold 0, morphology 0, Panel V3 0 and P1 0.
