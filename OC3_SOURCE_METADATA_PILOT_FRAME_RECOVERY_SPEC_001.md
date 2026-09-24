# OC3 Source-Metadata Pilot-Frame Recovery Specification 001

Status: **FROZEN PROSPECTIVE DESIGN; INACTIVE**

Mission: `OC3-SOURCE-METADATA-FRAME-RECOVERY-AUTONOMY-001`

Scope: `OFFLINE_PILOT_FRAME_RECOVERY_ONLY`

Branch: `autopilot/source-metadata-frame-recovery`, based exactly on STOP commit `c4e48be25afc355e82445b1e6efe6f794e55b307`.

## Closed predecessor and epistemic boundary

The predecessor remains immutable at `STOP_REQUIRES_HUMAN` with blocker `CONSUMED_FRAME_PERMIT_NO_TERMINAL`. This mission binds the STOP report `3e108bb586e083b67de5c040a2ae4eb0f94022604b12e781e1798d102392aae9`, stopped state `ba45ad1f3a5f1f3dfa3a821d83dd18b68324f14a9d6270606fb65d1eec6257e1`, historical permit `8e96a042d50e436b9fbd8ee65ccd53be5d9e2ae9a6152968511d7faa001a0f4d`, and consumption marker `70a22ada30ca459c939440750a562eec657dd7b72a6cb83b417d8fb1b2b433ef`. The permit is never replayed.

`TECHNICAL_CAUSE = UNKNOWN`. The governed argv was invoked, the permit was consumed, the process ceased, no output directory, frame or terminal remained, and compact stdout/stderr/return-code evidence was absent. OOM, MemoryError, Astropy, algorithm, data-integrity and timeout explanations are not observations.

Engineering analysis identifies avoidable risk in the historical conversion of complete FITS tables into Python row dictionaries, identity dictionaries and one geometry object per root row. This is not assigned as the crash cause.

## Scientific invariants

The question is whether the exact frozen frame can be reproduced from the same local authorities with a supervised, memory-bounded implementation and unchanged selection semantics. The four authority hashes remain root `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f`, north `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb`, south `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f`, and development fixtures `147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6` at the predecessor paths.

Immutable semantics are `(BRICKNAME,BRICKID)`, `GLOBAL_VIEW_BOTH`, development exclusion, `SHA256_ASCII_GLOBAL_BRICK_IDENTITY_V1`, `WRAP_AWARE_CLOSED_RA_BRICKROW_GUARD_1_V1`, `HASH_ORDER_DISJOINT_GUARD_2_TARGET_2_HOLDOUT_V1`, two targets and two holdouts. Hash literal, sort, closed RA wrap, `abs(BRICKROW difference)<=1`, counts and exclusions cannot change.

Root storage retains only fixed-width/NumPy arrays for `BRICKNAME, BRICKID, BRICKROW, RA, DEC, RA1, RA2, DEC1, DEC2`; north/south retain only identity arrays. Duplicate identities fail. Eligible north/south intersection must exist in root. The full eligible population may be a compact structured array. Hashing retains the exact ASCII literal. Guard scans are vectorized over compact root arrays; Python geometry records are created only for four selections and their guards.

The committed frame contains selected identities, digests, guard memberships, their geometry, input hashes and algorithm/implementation provenance, never the full eligible list or source-derived information. Synthetic tests compare the optimized and historical semantic reference on normal, wrapping, touching, adjacent-row, collision, exclusion and duplicate cases. Real inputs are forbidden during bootstrap.

## Supervised execution

The first and only material stage is `OC3-SOURCE-METADATA-PILOT-FRAME-RECOVERY-001`. A lightweight supervisor validates exact argv and a new single-use permit, consumes it, creates the bound output directory, writes immutable `START_INTENT.json`, launches exactly one frozen worker command, captures bounded child output and resource use, validates `PILOT_FRAME.json`, and writes an action terminal. The worker is implementation-bound and never consumes a permit.

`EXECUTION_DIAGNOSTIC.json` records timestamps, command and implementation hashes, return code, signal, wall seconds, Linux child peak RSS in KiB when available, stdout/stderr total bytes, SHA-256, truncation and at most 262,144 captured bytes per stream, output existence and checkpoint. High RSS does not imply OOM. Worker failure, signal, invalid output and integrity failure remain distinct. There is one launch, no replay and no object-heavy fallback.

## Governance, firewall and outcomes

This recovery ends after frame recovery. Network, Data Lab, source counts/rows, topology, PHOTSYS, denied catalog values, pixels, morphology, labels, matching, radii, thresholds, group IDs, Panel V3, P1, training, embeddings and clustering remain zero. Network/body budgets are zero; concurrency is one; retries and resume are zero.

Exactly one terminal outcome is permitted: `SOURCE_METADATA_PILOT_FRAME_RECOVERED`, `SOURCE_METADATA_PILOT_FRAME_RECOVERY_INTEGRITY_FAILED`, or `SOURCE_METADATA_PILOT_FRAME_RECOVERY_INCONCLUSIVE`. Runtime/implementation failure is inconclusive, never automatically scientific integrity failure.

The new generic Policy Core binds a waiting state and first candidate, exact argv, action validator, SHA-derived single-use permit, append-only ledger, separate transition, scientific terminal and `STOP_REQUIRES_HUMAN`. Bootstrap creates no standing authorization or real permit, executes no worker and reads no real FITS table.
