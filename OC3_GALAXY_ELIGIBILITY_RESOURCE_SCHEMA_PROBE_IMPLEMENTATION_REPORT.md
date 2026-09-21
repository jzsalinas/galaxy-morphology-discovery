# OC3 Galaxy Eligibility Resource/Schema Probe — Implementation Report

## 1. Binding and scope

**Stage:** `OC3-GALAXY-ELIGIBILITY-RESOURCE-SCHEMA-PROBE-001`

**Scope:** `DOCUMENTARY_RESOURCE_SCHEMA_PROBE_ONLY`

**Frozen specification:** `OC3_GALAXY_ELIGIBILITY_BOUNDED_EVIDENCE_SPEC.md`

**Specification SHA-256:** `db80f8fefda0aad4a7e1cea4fb3e32bca0f238d33d2a52cbaf72af5da9ec5f17`

**Implementation aggregate:** `6f1335b28d8fb56d15ee04e64e9d82ff8c10d65ade5d643c7929b4ae6eee9d8d`

The implementation supplies `--help`, `--validate-inputs`, `--dry-run`, `--bind-panel`, and `--probe-resource-schema`. Only the first four modes can operate without a separately bound final authorization. This implementation and its validation made zero network requests.

## 2. Files changed by the implementation

- `oc3/oc3_galaxy_eligibility_resource_schema_probe.py`
- `oc3/oc3lib/galaxy_eligibility_resource_schema_probe.py`
- `oc3/tests/test_galaxy_eligibility_resource_schema_probe.py`
- `oc3/INPUTS/OC3_GALAXY_ELIGIBILITY_DOCUMENTARY_MANIFEST_001.json`
- `oc3/tests/test_physical_contract_probe.py`, limited to extending its closed production-input inventory for the new documentary manifest and the prospective P0 outputs.
- `OC3_GALAXY_ELIGIBILITY_RESOURCE_SCHEMA_PROBE_IMPLEMENTATION_REPORT.md`

## 3. Offline panel selector

P0 binds the three immutable local DR9 brick-summary files and the development-fixture CSV by their frozen complete-file SHA-256 values. It validates the frozen FITS physical contracts before selectively decoding only:

```text
ROOT: BRICKNAME BRICKID RA DEC RA1 RA2 DEC1 DEC2
REGIONAL: brickname brickid ra dec ra1 ra2 dec1 dec2 area
          survey_primary nexp_g nexp_r nexp_z
```

All other summary cells remain opaque. The selector requires exact brick-name semantics, unique names and IDs, exact root/regional identity and geometry joins, finite/range-valid geometry and area, `survey_primary=true`, `GRZ_MEDIAN_PRESENT_V1`, and fixture exclusion derived from the bound CSV. It applies the exact frozen hash bytes with a final LF, orders independently by selection hash/name/ID, and selects eight north plus eight south. Hash collision, insufficient cardinality, duplicate identity, join mismatch, fixture leakage, authority mismatch, or output conflict fails closed.

The panel manifest contains only the 16 technical brick identities, selection hashes, authority hashes, eligibility version, technical exclusion counts, tie count, order hash, accounting, zeroed tripwires, and a canonical seal. It contains no source rows, model fields, or morphology information.

## 4. Tractor firewall and selective-byte capability

The closed projections are exactly `A_CORE` with nine fields and `C1_EXTENSION` with ten fields. The explicit denylist is `TYPE`, `DCHISQ`, `SERSIC`, `SHAPE_R`, `SHAPE_E1`, and `SHAPE_E2`; every field outside the 19-field union is nonprojectable.

The FITS capability validates an exhaustive ordered schema, calculates every BINTABLE column offset from `TFORM`, and emits row-relative byte spans containing only requested allowlisted fields. Adjacent allowed cells may share a span. Intervening denied or nonprojectable bytes split spans. Whole-row retrieval followed by a column drop is rejected. If neither provider projection nor exact byte ranges can exclude all other cell bytes, the result is `TRACTOR_SELECTIVE_COLUMN_FIREWALL_UNAVAILABLE`.

Schema inspection observes names and structural metadata only. Every projection-plan result records zero decoded cell values and successful plans record zero forbidden cell bytes.

## 5. B1 and P1 capability

The closed documentary manifest binds only the official DR9 catalog and file documentation pages needed to resolve Tractor/C1 schema semantics and B1 filenames, paths, schema, provider match semantics, duplicate policy, and bounded-access feasibility. Hashes and retrieval timestamps remain unresolved placeholders until authorized retrieval.

The future full P1 order is fixed as documents, HEAD for 16 Tractor resources, HEAD for B1 north then south, bounded Tractor headers in panel order, and bounded B1 headers north then south. FITS probing requests exact 2880-byte header blocks and stops at `END`; it never requests a full FITS body or decodes a table cell. An exhaustive post-documentary schema contract is required before the full resource plan can run.

Every document body, HEAD receipt, header block, resource-level schema result, request/byte counter, and checkpoint seal is persisted. The checkpoint index is replaced atomically. Reattempt or resumption requires separate authorization.

Transport construction occurs only after a canonical final authorization binds the candidate file SHA-256, command argv SHA-256, stage, and scope. Gaia and DESI transports are absent.

## 6. First P1 implementation envelope

The first candidate is stricter than the frozen maximum:

```text
candidate_scope = MINIMUM_DOCUMENTARY_BINDING_ONLY
logical_document_resources = 2
network_requests_started <= 8, including redirects
response_body_bytes <= 1 MiB
per_resource_body_bytes <= 512 KiB
concurrency = 1
automatic_retries = 0
redirects_per_request <= 3
```

The two B1 filenames are recorded, but their literal URLs remain empty because no local authority resolves them. The candidate therefore cannot authorize Tractor/B1 HEAD or Range operations. A documentary-only attempt terminates inconclusive until a reviewed post-documentary candidate binds literal paths and exhaustive schemas.

## 7. Validation

Focused validation:

```text
36 tests passed
0 failures
0 skips
real_network_requests = 0
```

This includes 35 new tests plus the affected closed production-directory tripwire. It covers authority bindings, exact field boundaries, fixture derivation, 8+8 selection, low cardinality, duplicates, joins, row-order invariance, hash bytes, seals, URLs, projection sets, denied/unknown fields, BINTABLE offsets, contiguous and interleaved layouts, unavailable-firewall behavior, authorization gating, tightened caps, request order, checkpoints, header-only Range behavior, immutable publication, and replay prevention.

Full offline regression:

```json
{"synthetic_only":true,"real_network_requests":0,"tests":937,"passed":937,"failed":0,"skipped":0,"seconds":48.677}
```

The real input validation bound four authorities, two fixture rows, two documentary resources, and read `89430131` local bytes for checksums with zero network requests.

## 8. P0 execution state at implementation commit

```text
P0 execution = NOT YET STARTED
panel manifest = ABSENT
P1 candidate = ABSENT
final P1 authorization = ABSENT
network requests = 0
Tractor rows decoded = 0
spectroscopy rows decoded = 0
Gaia rows decoded = 0
forbidden field observations = 0
```

P0 will be executed exactly once offline only after this implementation is committed. This report will then receive a post-P0 section binding the immutable output hashes and terminal without changing the implementation aggregate.

## 9. Post-commit real P0 execution review

The implementation was committed as:

```text
f1585e0c44a7fc3ad87185e398619ba3eee46e51
feat: implement bounded galaxy eligibility resource probe
```

P0 was then invoked exactly once offline:

```text
oc3/.venv/bin/python oc3/oc3_galaxy_eligibility_resource_schema_probe.py --bind-panel
```

The observed compact result was:

```json
{"error":"P0_DUPLICATE_REGIONAL_IDENTITY","stage_id":"OC3-GALAXY-ELIGIBILITY-RESOURCE-SCHEMA-PROBE-001","state":"GALAXY_ELIGIBILITY_PANEL_BINDING_FAILED"}
```

The frozen pre-hash rule requires unique `BRICKNAME` and `BRICKID` values within and across the north/south candidate region views. The real regional authorities did not satisfy that rule. The implementation stopped before hash selection and publication. It did not remove overlaps, assign one region, change the identity key, or adapt the panel after observing this result.

Post-attempt filesystem review confirmed:

```text
P0 execution attempts = 1
P0 terminal = GALAXY_ELIGIBILITY_PANEL_BINDING_FAILED
first error = P0_DUPLICATE_REGIONAL_IDENTITY
panel manifest = ABSENT
P1 authorization candidate = ABSENT
P0 run directory = ABSENT
network requests = 0
Tractor rows decoded = 0
spectroscopy rows decoded = 0
Gaia rows decoded = 0
forbidden field observations = 0
final P1 authorization = ABSENT
```

P1 cannot proceed because no sealed 16-brick panel exists. A new execution would require a prospective clarification or amendment that decides how regional overlap affects the frozen panel identity and balance rules. No such rule is inferred here, and P0 must not be rerun under the current specification.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
