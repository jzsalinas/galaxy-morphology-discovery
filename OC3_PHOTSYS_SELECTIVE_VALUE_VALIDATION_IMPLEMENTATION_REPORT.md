# OC3 PHOTSYS selective value validation — implementation report

## Result

The offline implementation for `OC3-GALAXY-ELIGIBILITY-PHOTSYS-SELECTIVE-VALUE-VALIDATION-001` is complete and bound to `OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_SPEC.md` SHA-256 `c04d1392e3b7bd0e974c6244201566679dae30d479b9b644c8f3abc1b1a7a119`.

No real PHOTSYS table cell or global-authority row value was decoded during implementation, testing, candidate construction, `--validate-inputs`, or `--dry-run`. Network requests were zero. The real validation was not executed, no projected authority was published, and no final authorization was created.

## Architecture and semantic boundary

The production PHOTSYS reader uses `os.pread` and admits only the row-relative spans `(0, 12)` and `(70, 1)`. It validates the requested row and span before I/O, has no public generic `read` or whole-row method, and exposes only a closed `ProjectedPhotsysRecord` containing `BRICKNAME`, `BRICKID`, and `PHOTSYS`.

The ROOT adapter binds the existing frozen `ROOT_SUMMARY` physical contract. It streams the gzip member and treats each 70-byte decompressor result as opaque transport. Only bytes `0..11` cross the semantic boundary, producing a closed `ProjectedGlobalBrickIdentity`; no other root field becomes a typed value.

The semantic boundary is crossed only when the explicitly authorized byte spans are assigned field meaning. Filesystem hashing, size and mode checks, canonical metadata checks, opaque compressed transport, and path readiness do not cross it.

Before any real value observation, the implementation fixed this consistency interpretation: trailing FITS spaces may be removed by the PHOTSYS lexical decoder exactly as specified, but the canonical result must independently pass `OC3_BRICKNAME_SEMANTICS_V1` before it can enter the exact global identity join. No repair, case conversion, alias, coordinate fallback, or value-dependent rule exists.

## Validation, accounting, and interruption behavior

The join key is exactly canonical `BRICKNAME` plus signed big-endian `BRICKID`. The validator records raw and canonical name uniqueness independently, ID and pair uniqueness, all frozen join aggregates, per-field valid/invalid counts, the `N`/`S`/ASCII-space distribution, and bounded diagnostic hashes without publishing identity lists.

The implementation maintains the four required authorized-value counters, all four forbidden-value counters, the whole-row counter, exact-span read counts, global projection counts, and opaque gzip transit bytes. Success requires exact row and field counts and every forbidden counter equal to zero.

Future real execution writes sealed input binding, periodic monotonic progress/accounting, observability, validation aggregates, and a terminal. An existing output directory blocks execution. An interruption preserves the available evidence and cannot silently resume. The fixed-width 13-byte resolver and its sealed sidecar are published only after the success terminal is established.

## Synthetic tripwires and regression

The new focused suite contains 34 synthetic tests. It covers all frozen decoding cases, signed integer boundaries, all uniqueness and join classes, physical-layout drift, wrong size/hash, exact first/last offsets, overflow, rejection before I/O, opaque gzip projection, deterministic resolver bytes and SHA-256, and failure-path non-publication. Executable and structural tripwires confirm the production path has no generic reader, whole-row access, NumPy structured load, pandas load, Astropy table load, or production mmap fallback.

The affected offline suite completed with 199/199 passing, zero failures, zero skips, and zero real network requests. The final complete offline regression completed with 1053/1053 passing, zero failures, zero skips, zero real network requests, in 67.388 seconds.

The affected historical PHOTSYS validators were corrected to compare immutable prior artifacts with their recorded implementation aggregate `800f413ee53ac2fecad66386a49ecaff04989d3ffce6b232cb52916a3c9dbbe6`, rather than reinterpret them against the current Python tree. Their tests now also recognize that the earlier full-byte acquisition authorization exists because that historical stage was completed. No historical evidence was modified.

## Real-input offline preflight

`--validate-inputs` returned `PHOTSYS_SELECTIVE_INPUTS_VALIDATED`. It verified the frozen files, hashes, sizes, mode, physical contract, acquisition receipts, root manifest, root integrity evidence, and root semantic summary. Its counters were:

- authorized PHOTSYS values decoded: `0`;
- authorized ROOT values decoded: `0`;
- forbidden counters: all `0`;
- whole-row materialization count: `0`;
- network requests: `0`.

`--dry-run` returned `READY_AT_REAL_VALUE_OBSERVATION_BOUNDARY` with every authorized, forbidden, whole-row, exact-span, and global-projection counter equal to `0`; network requests were `0`.

## Frozen candidate

- Implementation aggregate: `8a2321e33912886c96ba94c63b2552cf0c74a70447fbbda855d54ba752363813`
- Candidate: `oc3/INPUTS/OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_CANDIDATE_001.json`
- Candidate SHA-256: `11496a57ab65d44f2c743c72b0c6ea88f4942cb2fa4fab716936357357c5770d`
- Command argv SHA-256: `0707c7b3745bf0b8556ec28dac84495f5a0e7842ebeb9216ebecab080865ccf3`
- Candidate state: `PENDING_HUMAN_REVIEW`
- Final authorization: absent

The candidate binds the complete frozen specification and input evidence, the three authorized fields, exact PHOTSYS spans, frozen ROOT projection, success and closed terminal criteria, zero-forbidden firewall, success-only output, and no-resume boundary. Its command invokes `--validate-photsys-authority`, but that command was not executed.

Panel V2 remains `NOT_STARTED`. P1 remains `BLOCKED`. OC-3 morphological discovery remains not started.
