# OC3 PHOTSYS out-of-domain raw-byte histogram specification

## 1. Status and scope

This is the frozen prospective specification for:

- stage: `OC3-GALAXY-ELIGIBILITY-PHOTSYS-BYTE-HISTOGRAM-001`;
- scope: `PHOTSYS_SINGLE_BYTE_DISTRIBUTION_ONLY`;
- execution: offline;
- candidate success: `PHOTSYS_RAW_BYTE_HISTOGRAM_OBSERVED`.

This stage is new and separate. It is not a retry, resume, correction, or semantic amendment of `OC3-GALAXY-ELIGIBILITY-PHOTSYS-SELECTIVE-VALUE-VALIDATION-001`. It is not a resolver stage, Panel V2, P1, or morphological discovery.

This specification authorizes no implementation and no real execution. Implementation, a sealed execution candidate, and final human authorization must be reviewed separately.

## 2. Scientific question

The sole scientific question is:

> What raw byte values occur at the already established PHOTSYS byte position across the immutable 662174-row authority, and with what exact frequencies?

The stage observes a raw-byte distribution only. It assigns no astronomical, FITS-null, or provider semantics to any byte.

## 3. Immutable historical boundary

The completed V1 stage is immutable and must not be altered, regenerated, resumed, or rerun.

| Historical evidence | Frozen value |
|---|---|
| Stage | `OC3-GALAXY-ELIGIBILITY-PHOTSYS-SELECTIVE-VALUE-VALIDATION-001` |
| Terminal | `PHOTSYS_SELECTIVE_INVALID_PHOTSYS_FAILED` |
| V1 specification SHA-256 | `c04d1392e3b7bd0e974c6244201566679dae30d479b9b644c8f3abc1b1a7a119` |
| V1 candidate SHA-256 | `11496a57ab65d44f2c743c72b0c6ea88f4942cb2fa4fab716936357357c5770d` |
| V1 terminal SHA-256 | `ad817611054ace2daf395cebaa3a3bf70bfc90dac7f05a0f040366fdd1b241d8` |
| V1 aggregates SHA-256 | `c0a7a0322a9f626e1d215717458b401ed260946211743bcea6f40abc065143af` |
| V1 observability SHA-256 | `977be060d5439908c0a47884ea2fe7c6211e4d1f7195f73ca4a060ef90bd420b` |

The historical terminal name is preserved verbatim. In this stage, any byte outside `{0x4e, 0x53, 0x20}` is called `PHOTSYS_OUTSIDE_FROZEN_V1_DOMAIN`. The term carries no intrinsic semantic judgment.

## 4. Exact input and physical contract

The only future real input is:

`oc3/photsys_authority_full_acquisition/OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001/RAW_IMMUTABLE/survey-bricks-dr9-randoms-0.48.0.fits`

- SHA-256: `804d2caf327e808bb4047cc8792a5b08d01d8875149b7b7eb019ce982f6c3f8c`;
- exact size: `52323840` bytes.

The reviewed physical contract is:

`oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json`

- SHA-256: `30b03a47adfc5cb1cc18b8c930dee2fa1d3f04597768558f84602d6ed2aae56f`.

Frozen target layout:

- HDU: `1`, `BINTABLE`;
- table-data offset: `11520`;
- row count: `662174`;
- row width: `79` bytes;
- PHOTSYS row-relative offset: `70`;
- PHOTSYS width: `1` byte.

No alternate file, mirror, authority, release, inferred layout, or fallback source is permitted.

## 5. Closed real-observation boundary

For each row ordinal `i`, where `0 <= i < 662174`, the only authorized semantic access is exactly one byte at:

```text
11520 + i*79 + 70
```

The production primitive must be equivalent to:

```text
os.pread(fd, 1, 11520 + i*79 + 70)
```

It must occur exactly once per row. Expected real semantic reads: `662174`.

The reader must reject negative, overflowed, out-of-range, expanded, overlapping, whole-row, and unlisted requests before I/O. It must expose no generic semantic `read(offset, length)` API and no whole-row fallback.

## 6. Explicitly forbidden observations

The stage must not read or semantically observe:

- `BRICKNAME`;
- `BRICKID`;
- `AREA_PER_BRICK`;
- any other FITS column;
- ROOT authority values;
- coordinates, regional summaries, identities, or object metadata.

It must not construct an identity or perform a join.

Also prohibited are production semantic mmap, whole-row reads, typed whole-row objects, Astropy table loading, pandas table loading, NumPy structured or record-array loading, generic FITS table readers, read-all-then-filter, and decode-all-then-drop.

Opaque filesystem and page-cache behavior below the exact `pread` boundary is transport, not semantic observation.

## 7. Canonical histogram

The primary scientific result is a canonical array named `histogram_counts` with exactly `256` nonnegative integer elements.

- Array index: unsigned byte value `0..255`.
- Array value: exact number of rows whose PHOTSYS source byte equals that index.
- Required length: `256`.
- Required sum: `662174`.

The array index is the authoritative byte identity. Printable ASCII or hexadecimal labels are nonauthoritative derived review aids and must not replace the numeric index.

The canonical artifact is `OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_001.json`, serialized as compact UTF-8 canonical JSON with sorted object keys and one terminal LF. It contains the 256-bin array plus only the allowed metadata in section 9 and a deterministic seal. No row-level resolver or binary identity map is produced.

## 8. Frozen V1 consistency cross-check

Before any semantic interpretation, the observed histogram must satisfy all of these frozen expectations:

```text
histogram_counts[0x4e] = 82897
histogram_counts[0x53] = 249069
histogram_counts[0x20] = 0
histogram_counts[0x4e] + histogram_counts[0x53] + histogram_counts[0x20] = 331966
sum(histogram_counts[j] for j not in {0x4e, 0x53, 0x20}) = 330208
sum(histogram_counts) = 662174
```

These numbers come from immutable historical evidence and are frozen before the histogram is observed. A mismatch is a new discrepancy and must terminate for review. It must not cause a parameter change, a semantic expansion, or an automatic retry.

## 9. Output privacy and allowed evidence

No row-level output is permitted. The implementation must not record, serialize, log, or expose:

- row ordinal to byte;
- identity to byte;
- byte offset to byte;
- sample rows;
- first offending row;
- example identity;
- any equivalent row-linked diagnostic.

The only allowed scientific value output is the 256 aggregate counts. Additional allowed metadata is limited to:

- stage and schema identifiers;
- input path, size, and hashes;
- reviewed physical-contract path and hash;
- historical V1 evidence hashes and frozen cross-check counts;
- implementation aggregate;
- observability counters;
- terminal state;
- histogram SHA-256 and canonical seal.

No per-row temporary artifact may survive process memory or be written to disk. Logs and error messages must contain counters and terminal codes only.

## 10. Mandatory observability

The future implementation must maintain monotonic counters for at least:

- `rows_processed`;
- `authorized_PHOTSYS_bytes_observed`;
- `single_byte_pread_count`;
- `forbidden_span_access_count`;
- `whole_row_materialization_count`;
- `BRICKNAME_values_observed`;
- `BRICKID_values_observed`;
- `ROOT_values_observed`;
- `network_requests`.

Success requires exactly:

```text
rows_processed = 662174
authorized_PHOTSYS_bytes_observed = 662174
single_byte_pread_count = 662174
BRICKNAME_values_observed = 0
BRICKID_values_observed = 0
ROOT_values_observed = 0
forbidden_span_access_count = 0
whole_row_materialization_count = 0
network_requests = 0
```

An error, interruption, or later review must not reset counters within an attempt.

## 11. Success boundary

The sole success terminal is:

`PHOTSYS_RAW_BYTE_HISTOGRAM_OBSERVED`

It requires:

- every frozen input hash, size, and physical-layout fact matches;
- exactly `662174` rows processed;
- exactly one authorized PHOTSYS byte observation per row;
- a canonical 256-bin histogram whose sum is `662174`;
- exact agreement with every frozen V1 cross-check count;
- all forbidden, whole-row, identity, ROOT, and network counters equal zero;
- deterministic canonical histogram serialization, SHA-256, and seal;
- no row-linked output and no resolver.

Success means only that the raw-byte histogram was observed reproducibly. It does not validate PHOTSYS authority, amend or expand V1 semantics, interpret or accept an unexpected byte, select Panel V2, unblock P1, or authorize morphological discovery.

## 12. Closed terminal states and precedence

| Condition | Terminal |
|---|---|
| Input path, size, hash, immutable publication, or historical-evidence mismatch | `PHOTSYS_BYTE_HISTOGRAM_INPUT_MISMATCH_FAILED` |
| Physical layout or reviewed-contract mismatch | `PHOTSYS_BYTE_HISTOGRAM_PHYSICAL_LAYOUT_MISMATCH_FAILED` |
| Forbidden or expanded span requested, whether or not I/O occurs | `PHOTSYS_BYTE_HISTOGRAM_FORBIDDEN_SPAN_ACCESS_FAILED` |
| Whole-row materialization or fallback attempted | `PHOTSYS_BYTE_HISTOGRAM_WHOLE_ROW_MATERIALIZATION_FAILED` |
| `BRICKNAME`, `BRICKID`, ROOT, identity, or other column access attempted | `PHOTSYS_BYTE_HISTOGRAM_IDENTITY_OR_ROOT_ACCESS_FAILED` |
| Processed or observed row count differs from `662174` | `PHOTSYS_BYTE_HISTOGRAM_ROW_COUNT_MISMATCH_FAILED` |
| Observation stops before complete sealed evidence is available | `PHOTSYS_BYTE_HISTOGRAM_INCOMPLETE` |
| Histogram length or grand total is wrong | `PHOTSYS_BYTE_HISTOGRAM_TOTAL_MISMATCH_FAILED` |
| Any frozen N, S, space, V1-domain, or outside-V1 count differs | `PHOTSYS_BYTE_HISTOGRAM_V1_CONSISTENCY_MISMATCH_FAILED` |
| Complete evidence cannot distinguish a required condition | `PHOTSYS_BYTE_HISTOGRAM_INCONCLUSIVE` |

Terminal precedence is frozen as follows: forbidden-span access; whole-row materialization; identity or ROOT access; input mismatch; physical-layout mismatch; row-count mismatch; incomplete observation; histogram total mismatch; V1 consistency mismatch; success. A more specific observed failure must never be converted to success or to a weaker condition.

No terminal authorizes automatic semantic expansion, retry, resume, reinterpretation, or publication of row-level data.

## 13. Durable evidence and interruption

A future real attempt must write deterministic durable artifacts for:

- exact input binding;
- progress and monotonic counters;
- observability;
- canonical 256-bin histogram;
- V1 consistency result;
- terminal;
- compact append-only log without row-linked values.

The histogram may be published only after complete observation and all firewall checks. An interrupted attempt must preserve its evidence and stop closed. It must not silently resume. Any restart or resume requires later review and a separately sealed authorization.

## 14. Synthetic test design frozen before implementation

Synthetic fixtures only must cover:

1. a histogram containing `N`, `S`, and ASCII space;
2. one byte outside the V1 domain;
3. multiple bytes outside the V1 domain;
4. counts across all 256 bins;
5. exact histogram length and sum;
6. exact V1 cross-check success;
7. mismatch against historical `N` count;
8. mismatch against historical `S` count;
9. mismatch against historical ASCII-space count;
10. mismatch against historical outside-domain count;
11. forbidden-span access rejected before I/O;
12. `BRICKNAME` access attempt;
13. `BRICKID` access attempt;
14. ROOT access attempt;
15. whole-row fallback attempt;
16. first-row exact offset;
17. last-row exact offset;
18. negative, overflowed, and out-of-range row access;
19. wrong input hash, size, offset, row width, or row count;
20. deterministic histogram serialization, SHA-256, and seal;
21. failure and interruption paths emit no semantic amendment, identity, or row-level output.

Tripwires must prove that the production path cannot invoke mmap, Astropy, pandas, NumPy structured I/O, a generic semantic reader, or a whole-row fallback.

## 15. Future CLI and authorization boundary

A future implementation must provide at least:

- `--help`;
- `--validate-inputs`;
- `--dry-run`;
- `--observe-photsys-byte-histogram`.

All modes are offline. `--validate-inputs` may hash opaque bytes and validate frozen metadata without observing a table byte. `--dry-run` must reach the exact first-byte observation boundary and stop with all real-value counters equal to zero.

`--observe-photsys-byte-histogram` is the only future mode permitted to observe real PHOTSYS bytes. It must require an exact sealed implementation candidate and a separate final human authorization. This specification does not create either artifact.

## 16. Interpretation lock and next step

This stage must not decide whether a byte means blank, missing, outside footprint, NUL padding, provider sentinel, corruption, or any other interpretation. That prohibition remains even if one byte accounts for all `330208` outside-V1 observations.

After successful histogram observation, stop. Human review must inspect the nonzero aggregate bins. Only then may a separate prospective semantic or documentary investigation be designed using appropriate format or provider evidence. Nothing in this specification pre-authorizes that investigation or a change to V1.

PHOTSYS V1 semantics remain unchanged. No resolver exists. Panel V2 remains `NOT_STARTED`; P1 remains `BLOCKED`; OC-3 morphological discovery remains not started.
