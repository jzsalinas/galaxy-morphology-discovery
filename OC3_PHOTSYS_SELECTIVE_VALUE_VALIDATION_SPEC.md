# OC3 PHOTSYS selective value validation specification

## 1. Status and scope

This is the frozen prospective specification for:

- stage: `OC3-GALAXY-ELIGIBILITY-PHOTSYS-SELECTIVE-VALUE-VALIDATION-001`;
- scope: `PHOTSYS_THREE_FIELD_VALUE_OBSERVATION_ONLY`;
- execution: offline;
- candidate success: `PHOTSYS_THREE_FIELD_AUTHORITY_VALIDATED`.

It introduces the first authorized value observation from the acquired PHOTSYS authority. It does not implement a decoder, authorize execution, select Panel V2, unblock P1, or begin morphological discovery. Implementation and any real execution require later human review.

## 2. Frozen authorities and exact inputs

The future implementation must fail closed unless every path, length, and SHA-256 below matches exactly.

### 2.1 PHOTSYS authority

| Role | Path | SHA-256 / value |
|---|---|---|
| Immutable acquired FITS | `oc3/photsys_authority_full_acquisition/OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001/RAW_IMMUTABLE/survey-bricks-dr9-randoms-0.48.0.fits` | `804d2caf327e808bb4047cc8792a5b08d01d8875149b7b7eb019ce982f6c3f8c` |
| Exact byte length | same file | `52323840` |
| Acquisition checkpoint | `oc3/photsys_authority_full_acquisition/OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001/OC3_PHOTSYS_FULL_ACQUISITION_CHECKPOINT.json` | `289da27a13789682546757f74767d50dcb94c62904d668bb7c4d108758e7c51a` |
| Acquisition terminal | `oc3/photsys_authority_full_acquisition/OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001/OC3_PHOTSYS_FULL_ACQUISITION_TERMINAL.json` | `a3d2a0cabc8387cffcf2f59efb81393d5aad5a802bfea26716ffa4b9914e830b` |
| Reviewed physical contract | `oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json` | `30b03a47adfc5cb1cc18b8c930dee2fa1d3f04597768558f84602d6ed2aae56f` |
| Physical correction | `OC3_PHOTSYS_PHYSICAL_CONTRACT_CORRECTION_001.json` | `3a7838e89f93b309439470848bcfd932c6e758b003723dbf946de90c3c93c5dc` |
| Physical post-execution review | `OC3_PHOTSYS_PHYSICAL_PROBE_POST_EXECUTION_REVIEW.md` | `9da0020660377e7ef9825b77e0ef465f4018a1716272727ccc578a439e3583cf` |

The literal provider URL remains exactly:

`https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/survey-bricks-dr9-randoms-0.48.0.fits`

### 2.2 Global brick identity authority

The existing global authority is bound rather than recreated:

| Role | Path | SHA-256 |
|---|---|---|
| Immutable root authority | `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| Raw-file manifest | `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/BOOTSTRAP_RAW_FILE_MANIFEST.json` | `021c31736ee19af4d137f35404a266140b2aac90349607f58bb0815df719ea2a` |
| Integrity evidence | `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/BOOTSTRAP_INTEGRITY_EVIDENCE.json` | `460b50eefe6ff71aa94e8c88782565fc0e487fd817e40430c11c14432810607b` |
| Semantic summary | `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/BOOTSTRAP_SEMANTIC_SUMMARY.json` | `a0dd0c9bfa684a811c8033ade346d28381d6739a1991840bb23dacd00e7c9a7e` |

The root authority has `662174` validated rows and supplies `GLOBAL_BRICK_IDENTITY = (BRICKNAME, BRICKID)` under `OC3_BRICKNAME_SEMANTICS_V1`. The governing amendment is `OC3_GALAXY_ELIGIBILITY_REGION_RESOLUTION_AMENDMENT_001.md`, SHA-256 `1502bd29cab97170a6fa3c4ccddf07b49966ab65b5e0db206a9b8f010ecfbe65`.

No new global identity authority may be inferred or substituted. If an implementation cannot construct the exact join from this frozen authority while preserving the value firewall, it must terminate `PHOTSYS_GLOBAL_AUTHORITY_ACCESS_INCONCLUSIVE`; it may not use regional summaries, coordinates, aliases, fuzzy matching, or derived IDs as fallback.

## 3. Frozen physical layout

The only target table is HDU 1, `BINTABLE`:

- table-data offset: `11520`;
- row count: `662174`;
- row width: `79` bytes;
- table byte extent: `52311746` bytes.

The authorized fields and spans are:

| Field | FITS form | Row-relative span | Width |
|---|---|---:|---:|
| `BRICKNAME` | `8A` | `0..7` | 8 |
| `BRICKID` | `J` | `8..11` | 4 |
| `PHOTSYS` | `1A` | `70` | 1 |

The only authorized projection is the two exact spans `0..11` and `70`. All other row-relative bytes are forbidden at the value layer. No physical-contract fact may be adapted after value observation begins.

## 4. Value firewall

The future stage may decode, materialize, compare, aggregate, serialize, or publish values only from `BRICKNAME`, `BRICKID`, and `PHOTSYS`.

Every other FITS column value is forbidden, including `BRICKQ`, `BRICKROW`, `BRICKCOL`, `RA`, `DEC`, `RA1`, `RA2`, `DEC1`, `DEC2`, and `AREA_PER_BRICK`. The ban also applies categorically to `TYPE`, `DCHISQ`, `SERSIC`, `SHAPE_R`, `SHAPE_E1`, `SHAPE_E2`, and every other nonprojected field whether or not it occurs in this file.

Forbidden operations include:

- constructing a full-row typed view or structured ndarray;
- reading a complete row and discarding forbidden columns afterward;
- loading the complete table with Astropy, pandas, NumPy structured I/O, or equivalent convenience conversion;
- serializing, logging, hashing as semantic values, aggregating, or exposing a forbidden column;
- using a whole-row fallback after a projection error.

Any attempted forbidden-span access is terminal even if no forbidden value reaches an output.

## 5. Raw-byte reader boundary

### 5.1 PHOTSYS FITS

The production reader must use an exact-span raw-byte primitive such as `os.pread`. For row ordinal `i` in `0 <= i < 662174`, it may request only:

```text
11520 + i*79 + 0  through  11520 + i*79 + 11
11520 + i*79 + 70 through  11520 + i*79 + 70
```

Each application-visible projection buffer must therefore contain exactly 12 or 1 authorized bytes. A production mmap of the PHOTSYS table is disallowed because it would make enforcement of the closed application access surface harder to audit. OS page-cache activity beneath `pread` is transport of opaque immutable bytes and is not semantic observation.

The reader must reject negative, overflowed, unaligned, out-of-row, overlapping-expanded, or unlisted spans before file access. It must expose no generic `read(offset, length)` method to the semantic layer. The semantic layer receives a closed three-field projection object only.

### 5.2 Compressed global authority

The global authority is gzip-compressed. An implementation may reuse the already audited root projection semantics, but decompressor output must remain an opaque transport buffer. Only the frozen root `BRICKNAME` and `BRICKID` spans may cross into decoded/projected application buffers. No full-row typed object may be constructed. If this separation cannot be demonstrated by synthetic tripwires and counters, the stage is inconclusive rather than weakened.

An OS virtual mapping, an opaque compressed input buffer, or an opaque decompressor buffer is not by itself value observation. Crossing the boundary occurs when bytes are assigned field meaning, converted to a typed field, copied into a projected semantic buffer, compared as a field, aggregated, serialized, logged, or exposed to another component.

## 6. Frozen decoding rules

### 6.1 `BRICKNAME`

- The source is exactly 8 bytes.
- Every byte must be 7-bit ASCII; malformed or non-ASCII input fails without repair.
- The raw 8-byte value must remain available to validation logic.
- Canonical string conversion may remove only trailing FITS ASCII-space padding (`0x20`).
- Leading spaces, embedded repair, case conversion, Unicode normalization, replacement decoding, NUL termination, and any other normalization are forbidden.
- Identity comparison against the root authority uses the exact canonical result and must also satisfy the frozen global authority semantics. A padded value that cannot map exactly to one root identity is reported, never repaired.

### 6.2 `BRICKID`

- `TFORM=J` is decoded as a FITS signed 32-bit big-endian integer.
- Text coercion, unsigned reinterpretation, saturation, null substitution, and value-dependent reinterpretation are forbidden.

### 6.3 `PHOTSYS`

- The source is exactly one raw byte and must never be stripped.
- Valid bytes are exactly `0x4e` (`N`), `0x53` (`S`), and `0x20` (ASCII space).
- ASCII space is a valid documented exclusion, not missing data.
- Any other byte is `INVALID_PHOTSYS`.

These rules are frozen before observing the real value distribution.

## 7. Required validation

The implementation must process exactly `662174` rows and report:

- valid and invalid counts for each of `BRICKNAME`, `BRICKID`, and `PHOTSYS`;
- PHOTSYS counts for `N`, `S`, ASCII space, and invalid;
- uniqueness of raw/canonical `BRICKNAME`;
- uniqueness of signed `BRICKID`;
- uniqueness of `(BRICKNAME, BRICKID)`;
- exact join to the frozen global authority.

The join report must include these mutually explicit aggregates:

- `matched`;
- `missing_from_PHOTSYS_authority`;
- `missing_from_global_authority`;
- `BRICKNAME_conflict`;
- `BRICKID_conflict`;
- `identity_pair_conflict`;
- `invalid_PHOTSYS`.

No mismatch may be dropped, filtered, coerced, reassigned, or converted into a valid exclusion.

## 8. Output boundary

Primary outputs are canonical sealed JSON containing counts, uniqueness results, join aggregates, input hashes, implementation binding, observability counters, terminal state, and the projected-authority hash. They must contain no identity values or forbidden source values.

Only after all success criteria pass may the stage publish a row-level resolver. Its canonical representation is:

- filename: `OC3_PHOTSYS_PROJECTED_AUTHORITY_001.bin`;
- exactly `662174` fixed-width 13-byte records;
- record bytes: raw 8-byte `BRICKNAME`, 4-byte signed big-endian `BRICKID`, 1 raw-byte `PHOTSYS`;
- ordering: ascending raw `BRICKNAME` bytes, then ascending signed `BRICKID`;
- no header, padding, delimiter, metadata, or additional field in the binary file;
- SHA-256 over the exact complete byte stream;
- a separate canonical sealed JSON sidecar binds schema, record count, order rule, source hashes, and binary SHA-256.

The resolver semantics are `N -> north`, `S -> south`, and ASCII space -> valid exclusion. It establishes only `GLOBAL_BRICK_IDENTITY -> PHOTSYS`; it does not select the 8 north plus 8 south Panel V2 cohort.

On any non-success terminal, no row-level resolver may be published.

## 9. Success, failure, and inconclusive states

`PHOTSYS_THREE_FIELD_AUTHORITY_VALIDATED` requires all of the following:

- every frozen input hash and physical-contract fact matches;
- exactly `662174` rows processed;
- exactly `662174` authorized values decoded for each of the three fields;
- zero malformed `BRICKNAME` representations;
- zero malformed `BRICKID` representations;
- zero invalid PHOTSYS bytes;
- unique `BRICKNAME`, unique `BRICKID`, and unique identity pair;
- `matched = 662174` and every missing/conflict aggregate equals zero;
- all forbidden-value and whole-row counters equal zero;
- the canonical projected resolver is reproducible and its SHA-256 is sealed.

Closed terminal outcomes include:

| Condition | Terminal |
|---|---|
| Input hash or immutable publication mismatch | `PHOTSYS_SELECTIVE_INPUT_MISMATCH_FAILED` |
| Physical layout or contract mismatch | `PHOTSYS_SELECTIVE_PHYSICAL_CONTRACT_MISMATCH_FAILED` |
| Row-count mismatch | `PHOTSYS_SELECTIVE_ROW_COUNT_MISMATCH_FAILED` |
| Duplicate name, ID, or pair | `PHOTSYS_SELECTIVE_IDENTITY_DUPLICATE_FAILED` |
| Join missing or conflict | `PHOTSYS_SELECTIVE_GLOBAL_JOIN_CONFLICT_FAILED` |
| Invalid PHOTSYS byte | `PHOTSYS_SELECTIVE_INVALID_PHOTSYS_FAILED` |
| Malformed authorized field | `PHOTSYS_SELECTIVE_AUTHORIZED_VALUE_INVALID_FAILED` |
| Forbidden span/value or whole-row access | `PHOTSYS_SELECTIVE_READER_FIREWALL_VIOLATION_FAILED` |
| Frozen global authority cannot be projected under the firewall | `PHOTSYS_GLOBAL_AUTHORITY_ACCESS_INCONCLUSIVE` |
| Complete evidence cannot distinguish a contract or join condition | `PHOTSYS_SELECTIVE_VALUE_VALIDATION_INCONCLUSIVE` |

No criterion or terminal mapping may be weakened after real values are observed.

## 10. Mandatory observability

The eventual terminal and accounting artifacts must include at least:

- `authorized_rows_processed`;
- `authorized_BRICKNAME_values_decoded`;
- `authorized_BRICKID_values_decoded`;
- `authorized_PHOTSYS_values_decoded`;
- `forbidden_value_decode_count`;
- `forbidden_value_materialization_count`;
- `forbidden_value_serialization_count`;
- `forbidden_value_log_count`;
- `whole_row_materialization_count`.

All forbidden and whole-row counters must equal zero for success. Counts are cumulative within an attempt and may never be reset by resume or error handling.

## 11. Synthetic test design frozen before implementation

The implementation suite must cover independently of real values:

1. valid `N`, `S`, and ASCII-space rows;
2. an 8-byte BRICKNAME with permitted right-space padding and exact canonicalization;
3. leading/embedded space and malformed or non-ASCII BRICKNAME rejection;
4. signed big-endian BRICKID boundary decoding, including negative values;
5. duplicate BRICKNAME, duplicate BRICKID, and duplicate pair;
6. name, ID, and pair join conflicts plus both missing directions;
7. invalid PHOTSYS bytes, including NUL and lowercase letters;
8. wrong row width, data offset, row count, file size, or input hash;
9. forbidden-span access rejected before I/O;
10. whole-row read, structured-array, Astropy-table, pandas, and generic-reader fallback tripwires;
11. exact-span offset arithmetic at first and last rows, including overflow controls;
12. opaque-buffer versus semantic-boundary tests for the root gzip adapter;
13. deterministic sorting, binary serialization, and projected-authority hash;
14. failure-path proof that no projected resolver is published.

No test may use the real PHOTSYS value distribution to choose parameters or relax a criterion.

## 12. Future execution model

Implementation must provide at least:

- `--help`;
- `--validate-inputs`;
- `--dry-run`;
- `--validate-photsys-authority`.

All modes are offline. A future real validation may be delegated as a deterministic human CLI if its cost crosses project thresholds. It must write detailed output to a log, emit a compact terminal, support fail-closed restart rules, and require a separately reviewed candidate/authorization before observing real cells.

This specification authorizes no implementation or execution. Panel V2 remains `NOT_STARTED`; P1 remains `BLOCKED`; OC-3 morphological discovery remains not started.
