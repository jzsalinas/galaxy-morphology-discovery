# OC3 PHOTSYS raw-byte histogram implementation report

## Status

The frozen `OC3-GALAXY-ELIGIBILITY-PHOTSYS-BYTE-HISTOGRAM-001` infrastructure is implemented and verified offline. No real PHOTSYS table byte was observed, the observation mode was not executed, the historical V1 validator was not rerun, and no final authorization was created.

The implementation is bound to `OC3_PHOTSYS_OUT_OF_DOMAIN_BYTE_HISTOGRAM_SPEC.md` SHA-256 `127679c83acc9b7dc4e72a559b7b17857c7e53f2e4f63532675eeb13dfa10748` and to `OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_POST_EXECUTION_REVIEW.md` SHA-256 `6b689ba5aff89131d09506ce0827c2aabc59fad3935d3740db3eee019de9d772`.

## Architecture and observation boundary

The production implementation is `oc3/oc3lib/photsys_byte_histogram.py`; its CLI is `oc3/oc3_photsys_byte_histogram.py`.

`ExactPhotsysByteReader` exposes only `read_photsys_byte(row_ordinal)` and iteration over that same operation. It exposes no generic span reader, whole-row reader, identity reader, ROOT adapter, join machinery, or fallback. Its sole production semantic primitive is exactly:

```text
os.pread(fd, 1, 11520 + row_ordinal*79 + 70)
```

The reader validates row type and bounds, the one-byte length, the PHOTSYS-relative offset, checked signed-offset arithmetic, the calculated absolute offset, row boundaries, and file boundaries before I/O. A successful future run requires exactly `662174` such calls.

The implementation does not import or invoke `mmap`, Astropy table loading, pandas, NumPy structured I/O, provider schema adapters, identity objects, or ROOT machinery. Executable synthetic tripwires cover these boundaries.

## Histogram and frozen V1 checks

The only scientific payload is a 256-element list of nonnegative integer counts indexed by raw unsigned byte value. Bytes are binned directly as integers without text decoding. No row ordinal, byte offset, identity, sample, or first-occurrence diagnostic is retained.

The frozen checks are implemented without adjustable parameters:

- bin `0x4e`: `82897`;
- bin `0x53`: `249069`;
- bin `0x20`: `0`;
- frozen V1-domain total: `331966`;
- outside-frozen-V1-domain total: `330208`;
- grand total: `662174`.

The implementation assigns no provider, astronomical, missing-value, padding, corruption, or other semantic meaning to any raw bin.

## Durable evidence and interruption

A separately authorized future run writes deterministic input binding, monotonic progress counters, observability, V1 consistency, terminal, and compact log artifacts. The canonical `OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_001.json` is published only after complete observation, exact totals, frozen V1 agreement, and clean forbidden counters. An existing output directory blocks rerun. An interrupted attempt preserves counters, does not publish a complete histogram, and cannot resume automatically.

The terminal precedence and all frozen terminal identifiers are implemented. The future command requires both the sealed candidate and a separate exact final-human-authorization artifact.

## Verification

All tests installed physical network blockers before discovery/import.

| Verification | Result |
|---|---:|
| New focused synthetic suite | `43/43` passed |
| Affected histogram/V1/firewall suites | `202/202` passed |
| Complete offline regression | `1096/1096` passed |
| Failures | `0` |
| Skips | `0` |
| Real network requests | `0` |

The focused suite covers the frozen histogram cases, all 256 bins, V1 success and each mismatch, first/last offsets, forbidden spans before I/O, negative/overflow/out-of-range rows, identity/ROOT/whole-row attempts, incorrect bindings and layout, deterministic canonicalization and seals, failure publication, no row-linked output, CLI gating, and executable forbidden-library tripwires.

The affected suite also exposed one stale historical assertion that expected the already-used V1 final authorization to be absent. It now verifies that this tracked historical authorization remains present. No V1 execution artifact was altered.

## Real-input preflight

`--validate-inputs` completed with state `PHOTSYS_BYTE_HISTOGRAM_INPUTS_VALIDATED`. It verified immutable paths, hashes, file size, reviewed physical layout, and historical sealed aggregates using opaque hashing and metadata only. All observation and forbidden counters were zero.

`--dry-run` completed with state `READY_AT_REAL_PHOTSYS_BYTE_OBSERVATION_BOUNDARY`. It opened and closed the exact immutable input and stopped immediately before the first possible `pread`. Its counters were:

```json
{"BRICKID_values_observed":0,"BRICKNAME_values_observed":0,"ROOT_values_observed":0,"authorized_PHOTSYS_bytes_observed":0,"forbidden_span_access_count":0,"network_requests":0,"rows_processed":0,"single_byte_pread_count":0,"whole_row_materialization_count":0}
```

Real PHOTSYS table bytes observed during preparation: `0`. Identity observations: `0`. ROOT observations: `0`. Network requests: `0`.

## Sealed candidate

- Implementation aggregate: `389514586d7da2fa7c653be7447d85e55db2ba1100bdb918c7687166593b5208`.
- Candidate: `oc3/INPUTS/OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_CANDIDATE_001.json`.
- Candidate file SHA-256: `28666f5e29a23739c0192509d10d8bddaa11478c93e4ab868b5b0241f13b3c4a`.
- Candidate canonical seal: `5c9f17cfa374620f7dc66fe2991d5b43a72c6c22232951118b5351443e7a18fd`.
- Command argv SHA-256: `f495f0908f66d97213a03515adb2f556efa40ca3f07900be91e5a1cdab70d30d`.
- Final authorization: absent.

The sealed but unauthorized command is:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_photsys_byte_histogram.py --observe-photsys-byte-histogram --execute-real-byte-observation --candidate /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_CANDIDATE_001.json --authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_FINAL_AUTHORIZATION_001.json --output-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/photsys_byte_histogram/OC3-GALAXY-ELIGIBILITY-PHOTSYS-BYTE-HISTOGRAM-001
```

This command was not executed. PHOTSYS V1 semantics remain unchanged. No resolver exists. Panel V2 remains `NOT_STARTED`; P1 remains `BLOCKED`; OC-3 morphological discovery remains not started.
