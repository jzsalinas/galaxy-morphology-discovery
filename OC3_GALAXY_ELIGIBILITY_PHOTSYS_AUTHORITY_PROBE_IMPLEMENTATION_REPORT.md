# OC3 Galaxy Eligibility PHOTSYS Authority Probe — Implementation Report

## 1. Frozen authority and implementation aggregate

**Stage:** `OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001`

**Scope:** `PHOTSYS_BRICK_AUTHORITY_ONLY`

**Target:** `survey-bricks-dr9-randoms-0.48.0.fits`

The implementation jointly binds:

- `OC3_GALAXY_ELIGIBILITY_REGION_RESOLUTION_AMENDMENT_001.md`, SHA-256 `1502bd29cab97170a6fa3c4ccddf07b49966ab65b5e0db206a9b8f010ecfbe65`;
- `OC3_GALAXY_ELIGIBILITY_PHOTSYS_AUTHORITY_CONTRACT_001.md`, SHA-256 `5a8691a4f8438914d0a29d72fa1a5c8eec64e3ad82a04c668e44692fbfdd24e1`; and
- immutable failed-V1 report, SHA-256 `8905e2c2d4970cfe33bbe295c740d732529ecd2e969f9150c834aa2ea86110ca`.

**Implementation aggregate:** `ea621f93fef58ab059c7af62737efd02f8a356696d258ec107bb6d92b4abdb92`

The CLI exposes `--help`, `--validate-inputs`, `--dry-run`, and `--probe-resource-contract`. Transport construction occurs only after a canonical candidate and separate final human authorization bind the exact full command argv.

## 2. Files changed

- `oc3/oc3_galaxy_eligibility_photsys_authority_probe.py`
- `oc3/oc3lib/galaxy_eligibility_photsys_authority_probe.py`
- `oc3/tests/test_galaxy_eligibility_photsys_authority_probe.py`
- `oc3/tests/test_physical_contract_probe.py`, limited to admitting the two new closed production inputs
- `oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST.json`
- `oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_RESOURCE_CANDIDATE.json`
- this report

No historical V1 artifact, authority document, scientific product, panel output, or acquired file was changed.

## 3. Closed documentary boundary

The exact documentary allowlist is:

```text
https://www.legacysurvey.org/dr9/files/
https://www.legacysurvey.org/dr9/catalogs/
```

The resolver accepts a data URL only from an explicit HTML link whose final basename is exactly `survey-bricks-dr9-randoms-0.48.0.fits`, whose scheme is HTTPS, whose host is `portal.nersc.gov`, and whose path is inside the official DR9 Legacy Survey tree. Filename convention, plain unlinked text, mirrors, other versions, `randoms-1-*`, `randoms-allsky-*`, and `randoms-outside-*` cannot create a literal resource binding.

Each documentary body, hash, literal and final URL, status, byte count, and UTC timestamp is published immediately under immutable raw evidence and an atomically replaced checkpoint index. The parser separately requires documentary support for the exact product, the brick-level row model, `survey-bricks` fields plus `PHOTSYS` and `AREA_PER_BRICK`, exact N/S/blank semantics, and north/south overlap.

The available offline evidence does not contain a literal official link. Therefore the sealed candidate is documentary-only and leaves both the resource URL and local-preservation rights state unresolved.

## 4. Header-only and representation boundary

The post-documentary implementation supports exactly one data HEAD followed by 2880-byte Range requests. It requires status 206, exact `Content-Range`, identity content encoding, stable literal/final URL, and a complete block ending at FITS `END`. It walks HDUs by header geometry and padded data extents; it skips table payloads and never requests the first table-data byte.

The structural result records the complete HDU inventory, file size, target BINTABLE HDU, row count, row width, exhaustive ordered columns, `TFORM`, row offsets, dtype and shape, null/scaling cards, units, data offset, and table byte extent. A resolved brick-level contract requires:

- exactly one primary HDU and one BINTABLE HDU;
- documented one-row-per-brick semantics;
- the expected global brick-authority cardinality of 662,174 rows;
- exact `BRICKNAME`, `BRICKID`, and `PHOTSYS` fields; and
- structural presence of `AREA_PER_BRICK` without observing its values.

Unexpected HDUs, random-point representation, row-count disagreement, malformed or unknown required layout, or missing documentary support stops closed with the frozen representation failures.

## 5. Selective projection and firewall

The BINTABLE layout calculator derives exact widths and row-relative offsets before any cell access. It emits the minimal disjoint byte spans covering only:

```text
BRICKNAME
BRICKID
PHOTSYS
```

Intervening fields split spans. Variable descriptors, absent required fields, byte overlap, or any need for a whole-row fallback produces `PHOTSYS_AUTHORITY_SELECTIVE_PROJECTION_UNAVAILABLE`.

The following counters remain zero in every terminal and partial-failure reconstruction:

```text
forbidden_value_decode_count
forbidden_value_materialization_count
forbidden_value_serialization_count
forbidden_value_log_count
random_point_row_decode_count
morphology_access_count
table_cell_values_decoded
```

No probe mode contains a table-cell decoder. `AREA_PER_BRICK` is structurally observable by name and schema only.

## 6. Checkpoints and tightened envelopes

Requests undergo worst-case preflight against redirects and body limits before transport. There are no retries and no automatic rerun or resume. A partial attempt retains immutable document bodies, HEAD evidence, each header block, cumulative accounting in receipts, an atomic checkpoint index, and a failure terminal reconstructed from durable receipts.

The complete header-capable implementation maximum is tighter than the frozen contract:

```text
requests including redirects <= 62
response bodies <= 1,129,216 bytes
data header Range bodies <= 80,640 bytes
FITS header blocks <= 28
redirects per request <= 1
concurrency = 1
automatic retries = 0
full FITS GETs = 0
table cells decoded = 0
```

The first sealed candidate is smaller because the literal data URL is not yet bound:

```text
candidate_scope = MINIMUM_DOCUMENTARY_BINDING_ONLY
documentary resources = 2
data HEAD requests = 0
data Range requests = 0
requests including redirects <= 4
response bodies <= 1,048,576 bytes
per-document body <= 524,288 bytes
redirects per request <= 1
concurrency = 1
automatic retries = 0
```

## 7. Offline validation

New focused suite:

```text
30 passed
0 failures
0 skips
real_network_requests = 0
```

Combined new suite and affected production-directory/physical-contract tripwires:

```text
155 passed
0 failures
0 skips
real_network_requests = 0
```

Complete offline regression, with socket and DNS blockers installed before discovery and imports:

```json
{"synthetic_only":true,"real_network_requests":0,"tests":967,"passed":967,"failed":0,"skipped":0,"seconds":58.822}
```

The tests cover the closed documentary allowlist, exact filename/version, explicit-link requirement, redirect and cap behavior, documentary hashes, exact FITS block boundaries, `END`, table-data avoidance, HDU inventory, exhaustive schema, structural-only `AREA_PER_BRICK`, random-point and malformed representation stops, Range mismatch, minimal interleaved projection spans, no whole-row fallback, zero forbidden values, authorization gating, durable partial failures, immutable V1 evidence, and the blocked Panel V2/P1 boundary.

## 8. Sealed first real-probe candidate

**Candidate:** `oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_RESOURCE_CANDIDATE.json`

**Candidate SHA-256:** `ce44b89346b1f281f587ddf654dab562b753f09dd140c0791ce475af401e0fc0`

**Command argv SHA-256:** `2f6a1fffd7e0ac6a9b559dfc57705e59a39a65bca964487798991433a4d60403`

The candidate contains the exact eventual command, but `authorization_state=FINAL_HUMAN_AUTHORIZATION_ABSENT`. Its only possible successful operational result is documentary resolution followed by `PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_INCONCLUSIVE`; it cannot issue data HEAD or Range requests and cannot resolve the complete resource contract.

A separate human review and final authorization is the next action. After that documentary attempt is reviewed, a distinct post-documentary candidate may bind the observed literal URL and authorize the one-HEAD/header-only contract probe. No terminal from either Stage A attempt authorizes Stage B acquisition.

## 9. Preserved stage state

```text
PANEL_V1 = FAILED_CLOSED
PHOTSYS_AUTHORITY = NOT_ACQUIRED
PANEL_V2 = NOT_STARTED
P1 = BLOCKED
final_human_authorization = ABSENT
network_requests_executed_by_implementation = 0
```

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
