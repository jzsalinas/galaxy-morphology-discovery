# OC3 Source-Metadata Pilot-Frame Schema Recovery Bootstrap Report 001

## Result

Mission `OC3-SOURCE-METADATA-FRAME-SCHEMA-RECOVERY-AUTONOMY-001` was bootstrapped on `autopilot/source-metadata-frame-schema-recovery` from exact preceding terminal commit `507f6896dc93f5a3e3ec93b98c4a86e5a915d071`. It remains inactive. No standing authorization or real permit exists, and the schema-correct pilot-frame recovery was not executed.

The closed preceding mission remains terminal as `SOURCE_METADATA_PILOT_FRAME_RECOVERY_INTEGRITY_FAILED`. Its observed worker error was `BOUND_IDENTITY_COLUMNS_MISSING`, the first failing regional authority was `NORTH_SUMMARY`, the worker return code was 2, and no `PILOT_FRAME.json`, target identity or holdout identity was materialized.

## Frozen review conclusion

The frozen provider physical contract records uppercase `BRICKNAME` and `BRICKID` for `ROOT_SUMMARY`, and lowercase `brickname` and `brickid` for regional `NORTH_SUMMARY` and `SOUTH_SUMMARY`. The regional contract is case-sensitive, with `TTYPE1 = brickname` and `TTYPE44 = brickid`. The frozen historical regional technical projection is `("brickname","brickid","ra","dec","ra1","ra2","dec1","dec2")`.

Therefore the immediately preceding supervised failure is classified as:

`CURRENT_RECOVERY_FAILURE_CLASS = IMPLEMENTATION_SCHEMA_CASE_MISMATCH`

This classification applies only to that observed supervised attempt. The earlier opaque predecessor remains `TECHNICAL_CAUSE = UNKNOWN`: the compatible uppercase access in its implementation does not prove the cause of an execution for which return-code and stderr evidence were not preserved.

## Corrected prospective implementation

The new worker validates each complete FITS physical schema through `oc3/oc3lib/provider_physical_contracts.py` before allowed cell access. Root access uses the exact uppercase physical names; regional identity access uses the exact lowercase physical names. Canonical project identities are constructed only after successful validation and decode. There is no case-insensitive lookup, alternate-spelling probe, or adaptive fallback.

The supervised fixed-width/NumPy architecture and all scientific frame semantics remain unchanged: `GLOBAL_VIEW_BOTH`, development-fixture exclusion, `SHA256_ASCII_GLOBAL_BRICK_IDENTITY_V1`, `WRAP_AWARE_CLOSED_RA_BRICKROW_GUARD_1_V1`, `HASH_ORDER_DISJOINT_GUARD_2_TARGET_2_HOLDOUT_V1`, two targets and two holdouts.

Prospective worker failures are separated into exactly `PHYSICAL_SCHEMA_CONTRACT_MISMATCH`, `ALLOWED_COLUMN_ACCESS_MISMATCH`, `IDENTITY_DECODE_FAILURE`, `GLOBAL_IDENTITY_INTEGRITY_FAILURE`, `FRAME_SELECTION_INTEGRITY_FAILURE`, and `WORKER_RUNTIME_FAILURE`.

## Frozen identities

- Scientific specification SHA-256: `350af50ce508c49a612dfc97191529159d9ae10e8151260ed751b19e3b2e0df7`.
- Policy Core contract SHA-256: `452c6039f3b37bf6585da27b73685f5be2c8fd2fc2756fbcbddcfe016810149f`.
- Policy Core manifest SHA-256: `7da94259ab6b3de59c2dc42c93bb9dd3a0f63205328491695d9a8acd553c90b1`.
- Pending mandate SHA-256: `8cc3e2b0f22b1563ad9444c6f1efc41d70e62bb24ef227c3622a1cb1bf137d8d`.
- Waiting-state SHA-256: `796d87fa825f8a6565b167bc21ce5b2c4949450014096ab3aefe6586a3303a30`.
- First candidate SHA-256: `5e25afe2592b05c3d3abfdaabfd65f8a4064dadb276ca37d4bc446435880b1e8`.
- Candidate validation receipt SHA-256: `6d3a5ae76ba9dd5677395d378eae5451409ee3dc2279cabcb9be00a303d4f710`.
- Supervisor/worker implementation aggregate: `cb6ba4341f38f871dd8d7d5d8248906b706f7f43a1f6646102a724bd4afe9607`.
- Supervisor command argv SHA-256: `cf1d41256d1ce906dde420d6884ca20be4c3817a80e02ce8f8d3af34ce7ff9be`.
- Worker command argv SHA-256: `6d4dad856f49d5a8059efca790a5154886448cfdbbd344a6ed01fabaef77957a`.

The candidate binds the same four frozen local authority hashes, the frozen provider physical contracts, zero network/body/source-row access, one future worker launch and a new single-use permit path. That permit and the standing authorization are absent.

## Verification

- Focused schema-recovery suite: 28 passed, 0 failed, 0 skipped.
- Affected frame, pilot and provider-schema suites: 175 passed, 0 failed, 0 skipped.
- Full guarded offline regression through `oc3/tests/run_tests.py`: 1,416 passed, 0 failed, 0 skipped; `real_network_requests=0`.
- Candidate preflight: `READY_AT_SCHEMA_CORRECT_SUPERVISED_FRAME_RECOVERY_BOUNDARY`; network requests 0; response-body bytes 0; real FITS material frame reads 0.
- Governor validation: `AUTONOMY_HARDENING_VALIDATED`; permit issued false.
- Governor dry run: `MANDATE_NOT_ACTIVE`; `NO_PERMIT_ISSUED`.

Synthetic coverage includes the exact uppercase root case, exact lowercase regional case, rejection of uppercase and mixed-case regional aliases, missing identity columns, reordered `TTYPE` columns, historical projection regression, and all prior reference-versus-columnar selection equivalence cases.

## Bootstrap firewall

Observed during this work: network 0, Data Lab 0, real FITS material frame reads 0, source rows 0, targets materialized 0, holdouts materialized 0, matching 0, radius operations 0, threshold selections 0, morphology 0, Panel V3 0 and P1 0. No real frame derivation occurred.
