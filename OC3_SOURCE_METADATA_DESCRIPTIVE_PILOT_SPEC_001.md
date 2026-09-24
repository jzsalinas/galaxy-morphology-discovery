# OC3 Source-Metadata Descriptive Pilot Specification 001

Status: **FROZEN PROSPECTIVE DESIGN; INACTIVE**

Mission: `OC3-SOURCE-METADATA-DESCRIPTIVE-PILOT-AUTONOMY-001`

Branch: `autopilot/source-metadata-descriptive-pilot`
Base: `21026ee884669d59328b5e9f2e6cdf4cb353df40`

## Scientific boundary

This pilot asks for the empirical, morphology-independent positional and multiplicity structure of north/south DR9 catalog-source observations in a small prospectively selected set of overlap bricks, before any same-object rule. The observational unit is `(RELEASE, BRICKID, OBJID, processing_domain)`. It is a catalog observation, never an astrophysical-object identity.

The mission may characterize local positional candidate topology. It may never emit `MATCH = TRUE/FALSE`, same-object replication claims, `OBJECT_GROUP_ID`, `SPLIT_GROUP_ID`, a matching radius, a posterior threshold, or a morphology class. Track A `SPLIT_SAFETY_GROUPING` and Track B `OBSERVER_REPLICATION_PAIRING` remain open. Budavári/Szalay Bayes factors are outside scope because extended-source transfer and complete cross-observer covariance remain unresolved.

## Bound predecessor

The following immutable predecessor evidence is bound without reinterpretation:

- `OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_FINAL_REPORT_001.md`, SHA-256 `92cb93731594b044d7005675f44b6656500108cc44850780224baf223d817a72`.
- `oc3/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_FINAL_CLAIM_MATRIX_001.json`, SHA-256 `cee289e6a330cd237be1ae6c2aebfbe8fa321dc60d28ef5c6562ebe13d9376eb`.
- `oc3/OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_AUTONOMY_STATE_001.json`, SHA-256 `4595b322605ad3c16afeac379e7a67d3c0add3c02718c51d406dc28c2f8d9b85`.

Frozen conclusions are: both formalism claims `SUPPORTED`; extended-source transfer `NOT_DEMONSTRATED`; no search bound and no scientific threshold selected.

## Local frame authorities

The root, north, south and development-fixture files are bound respectively by SHA-256 `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f`, `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb`, `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f`, and `147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6` at the paths frozen in the first-action specification.

`GLOBAL_VIEW_BOTH` is reconstructed by exact `(BRICKNAME, BRICKID)` agreement in north and south, with development fixtures excluded. Selection uses no counts, depth, seeing, morphology, photometry, redshift, balance, or future pairing behavior.

For each eligible identity, compute lowercase hexadecimal SHA-256 of the exact ASCII byte string `OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_001|` + decimal `BRICKID` + `|` + `BRICKNAME`, then sort by digest. `GUARD_1(T)` contains each root brick `B` for which `abs(BRICKROW_B-BRICKROW_T)<=1` and the two closed RA intervals overlap or touch under the frozen wrap-aware interval decomposition. The target is included; there is no angular expansion.

Iterate in hash order, accepting a candidate only when its guard is disjoint from all accepted guards. The first two are `PILOT_TARGET`; the next two are `RESERVED_HOLDOUT`. Fewer than four is an integrity failure. Holdout source rows, counts, coordinates, ivars, or pairing structure may not be accessed in this mission.

## Source contract after successful frame

Only `ls_dr9.tractor_n` and `ls_dr9.tractor_s` are allowed. `ls_dr9.tractor`, server cross-match, `q3c_join`, cone search, and radius queries are forbidden. The only source values are `RELEASE, BRICKID, OBJID, BRICKNAME, BRICK_PRIMARY, RA, DEC, RA_IVAR, DEC_IVAR`; `SELECT *` and all TYPE, DCHISQ, SERSIC, SHAPE, flux, magnitude, color, photo-z, REF_CAT, REF_ID, PHOTSYS, label, pixel, and image-measurement values are forbidden. Denied names may appear only in schema metadata.

One exact schema query precedes two exact per-domain count queries. Rows are permitted only after both counts pass `MAX_SOURCE_ROWS_PER_DOMAIN=150000`. A cap failure causes `RESOURCE_BOUND`: no target reduction, substitution, partial query, or truncation. Each row query uses `TOP 150001`, the nine-field projection, `brick_primary=1`, the exact sorted target-guard union, and `ORDER BY release,brickid,objid`; 150001 rows is overflow.

The future envelope is five requests and 67,108,864 response-body bytes, concurrency one, zero retries, no resume. Per-response caps are 524,288 schema; 65,536 for each count; and 32,505,856 for each row response. Only public unauthenticated service use is eligible; authentication causes `STOP_REQUIRES_HUMAN`.

All rows must have exactly the projection, a valid identity, allowed guard membership, true `BRICK_PRIMARY`, finite RA in `[0,360)` and DEC in `[-90,90]`, and no duplicate `(RELEASE,BRICKID,OBJID)` within a domain. Invalid/zero/missing ivars are recorded, never silently deleted.

## Descriptive geometry

For each target and direction, anchors are target-brick rows in one domain and candidates are all opposite-domain rows in that target's guard. Guard rows are context, not anchors. Exact spherical angular separation is computed through unit vectors. Freeze `K=2` only for `LOCAL_NEAREST_WITHIN_GUARD` and `LOCAL_SECOND_NEAREST_WITHIN_GUARD`. `LOCAL_RECIPROCAL_NEAREST` describes graph topology and never a match.

Per-anchor runtime records may contain identities, d1, d2, d2/d1, reciprocity, target/guard relation, and ivar validity. Only compact per-target/direction counts, fractions and quantiles at `(0, .05, .25, .50, .75, .95, 1)` may enter Git. No adaptive histogram, equivalence class, confidence, or threshold is allowed. Source CSVs and per-anchor records remain local and untracked.

## Outcomes and governance

Exactly one terminal outcome is allowed: `SOURCE_METADATA_DESCRIPTIVE_PILOT_COMPLETED`, `SOURCE_METADATA_DESCRIPTIVE_PILOT_RESOURCE_BOUND`, `SOURCE_METADATA_DESCRIPTIVE_PILOT_INCONCLUSIVE`, or `SOURCE_METADATA_DESCRIPTIVE_PILOT_INTEGRITY_FAILED`. No outcome is preferred.

The policy core uses a state-bound first candidate, exact argv, action validators, single-use SHA permits, actual accounting, append-only ledger, separate transitions, scientific terminal, and fail-closed `STOP_REQUIRES_HUMAN`. Permit consumption precedes material access; a crash does not restore it. Policy-core mutation while active, scope/budget/authority expansion, credential need, destructive action, or changed criteria requires human review.

This bootstrap creates no standing authorization, issues no permit, executes no frame, observes no target or holdout identity, makes no network request, and reads no source row.
