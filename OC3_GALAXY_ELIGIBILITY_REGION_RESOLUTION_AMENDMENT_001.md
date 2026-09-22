# OC3 Galaxy Eligibility Region Resolution Amendment 001

## 0. Status and authority

**Amendment ID:** `OC3-GALAXY-ELIGIBILITY-REGION-RESOLUTION-AMENDMENT-001`

**Status:** FROZEN PROSPECTIVE AMENDMENT / NO EXECUTION

**Amends:** `OC3_GALAXY_ELIGIBILITY_BOUNDED_EVIDENCE_SPEC.md`

**Amended specification SHA-256:** `db80f8fefda0aad4a7e1cea4fb3e32bca0f238d33d2a52cbaf72af5da9ec5f17`

**Historical evidence:** `OC3_GALAXY_ELIGIBILITY_RESOURCE_SCHEMA_PROBE_IMPLEMENTATION_REPORT.md`

**Historical evidence SHA-256:** `8905e2c2d4970cfe33bbe295c740d732529ecd2e969f9150c834aa2ea86110ca`

**Historical implementation commit:** `f1585e0c44a7fc3ad87185e398619ba3eee46e51`

**Historical review commit:** `2f5014bbb4320abe5fd8c239e86354c99831153a`

**Network, acquisition, panel selection, Tractor/SDSS/Gaia access, morphology access, and P1 execution authorized by this amendment:** NONE

This amendment changes only the prospective regional-identity ontology and the prerequisites for a new panel version. Every unaffected rule in the amended specification remains binding.

## 1. Immutable historical result

The failed V1 attempt remains immutable evidence:

```text
PANEL_V1 = FAILED_CLOSED
stage_id = OC3-GALAXY-ELIGIBILITY-RESOURCE-SCHEMA-PROBE-001
terminal = GALAXY_ELIGIBILITY_PANEL_BINDING_FAILED
first_error = P0_DUPLICATE_REGIONAL_IDENTITY
execution_attempts = 1
panel_manifest = ABSENT
P1_candidate = ABSENT
network_requests = 0
```

V1 is not resumed, relabeled, overwritten, or deleted. The absence of V1 output does not permit reuse of its stage identity. This amendment does not reinterpret the implementation's behavior: that implementation correctly enforced the then-frozen rule and failed closed.

## 2. Documentary and ontological correction

The official DR9 fact supplied for this amendment is:

> The north BASS/MzLS and south DECaLS imaging footprints overlap, so the same global geometric brick may legitimately appear in both regional DR9 summary views.

Consequently, regional presence is not a globally unique brick identity. The V1 assumption requiring `BRICKNAME` or `BRICKID` to be unique across the union of the north and south regional summaries is invalid.

This correction occurs before any Tractor row, galaxy-eligibility outcome, morphology label, source-level evidence, panel membership, representation, embedding, or discovery result was observed. It introduces no scientific preference based on source population, depth, seeing, morphology, or panel hash.

## 3. Global identity and regional-view overlap

The canonical global identity is:

```text
GLOBAL_BRICK_IDENTITY = (BRICKNAME, BRICKID)
```

Its authority is the immutable global `survey-bricks.fits.gz`. The root table must retain a one-to-one mapping for `BRICKNAME`, `BRICKID`, and their pair. Every regional row must join exactly one global identity and agree exactly with the frozen root geometry.

The same `GLOBAL_BRICK_IDENTITY` appearing once in each regional summary is classified as:

```text
REGIONAL_VIEW_OVERLAP
```

It is not `DUPLICATE_IDENTITY_FAILURE`. The overlap contributes one global brick and at most one V2 candidate.

These remain failures:

- duplicate `BRICKNAME`, duplicate `BRICKID`, or duplicate pair within one regional summary;
- duplicate or conflicting identity within the root authority;
- a regional row with no unique root match;
- regional/root `BRICKID` mismatch; and
- any regional/root geometry disagreement.

## 4. Canonical-region authority

Overlap must not be resolved by input order, north preference, south preference, lexical order, NEXP, PSFSIZE/seeing, area, source counts, panel hash, or convenience.

The preferred official DR9 authority is the single brick-level resolver product:

```text
survey-bricks-dr9-randoms-0.48.0.fits
```

The required field is `PHOTSYS`, with the supplied official semantics:

| `PHOTSYS` exact value | V2 meaning |
|---|---|
| ASCII `N` | `canonical_region=north` |
| ASCII `S` | `canonical_region=south` |
| ASCII space | Outside the resolved imaging footprint; not eligible. |

No trimming, case conversion, truthiness conversion, or inference from regional presence is allowed. Any other value is invalid.

The complete resolver must establish exactly one row for every identity it represents. Required identity values are:

```text
BRICKNAME
BRICKID
PHOTSYS
```

Additional identity or geometry fields may be projected only if a later, prospective physical contract proves they are strictly required for exact binding. They may not enter eligibility or hash ordering.

## 5. Resolver states and failures

For each root `GLOBAL_BRICK_IDENTITY`, the resolver join has exactly one of these states:

```text
PHOTSYS_N
PHOTSYS_S
PHOTSYS_BLANK
PHOTSYS_MISSING
PHOTSYS_INVALID
PHOTSYS_DUPLICATE_OR_CONFLICTING
```

`PHOTSYS_BLANK` is a valid exclusion state. It is counted and does not enter the candidate universe.

`PHOTSYS_MISSING`, `PHOTSYS_INVALID`, and `PHOTSYS_DUPLICATE_OR_CONFLICTING` fail the complete V2 binding. They cannot be converted to an exclusion, guessed from summary membership, or repaired by choosing a region.

The corresponding first-error codes are:

```text
PHOTSYS_GLOBAL_IDENTITY_MISSING
PHOTSYS_VALUE_INVALID
PHOTSYS_IDENTITY_DUPLICATE_OR_CONFLICTING
```

## 6. Revised V2 universe

The V2 universe is built once, in this order:

1. validate the complete hashes and frozen contracts of root, north summary, south summary, development fixtures, and the new PHOTSYS authority;
2. build the unique root map of `GLOBAL_BRICK_IDENTITY`;
3. validate uniqueness separately inside each regional summary;
4. join every regional row exactly to the root identity and geometry;
5. join every root identity exactly to the PHOTSYS resolver;
6. exclude `PHOTSYS_BLANK` identities;
7. map `PHOTSYS_N` only to the north summary and `PHOTSYS_S` only to the south summary;
8. require the canonical regional row to exist exactly once;
9. apply the already frozen geometry/area, `survey_primary=true`, and `GRZ_MEDIAN_PRESENT_V1` gates only to that canonical row;
10. exclude development fixtures globally; and
11. hash the remaining canonically resolved identities under V2.

The existence of the same identity in the noncanonical regional summary is overlap provenance only. No value from that row may affect eligibility, ordering, replacement, or panel membership.

If the canonical row is missing, the complete binding fails with:

```text
PHOTSYS_CANONICAL_REGIONAL_ROW_MISSING
```

It must not fall back to the noncanonical row.

## 7. Global fixture exclusion

The fixture CSV does not itself carry `BRICKID`. Each fixture `BRICKNAME` must therefore join exactly once to the immutable root authority, producing its `GLOBAL_BRICK_IDENTITY`. That identity is excluded globally, regardless of the fixture's recorded regional view or its PHOTSYS value.

A missing, duplicate, or conflicting fixture/root join fails closed. Fixture names must not be hard-coded in selection source code.

## 8. `survey_primary` consistency

`survey_primary=true` remains a technical consistency requirement on the PHOTSYS-selected canonical regional row. It never arbitrates overlap.

If the canonical row exists but its exact logical `survey_primary` value is not true, V2 fails with:

```text
PHOTSYS_SURVEY_PRIMARY_CONFLICT
```

The implementation must not select the noncanonical row, reinterpret PHOTSYS, or convert this conflict into ordinary ineligibility. `survey_primary` values in noncanonical rows do not choose the canonical region.

## 9. V2 hash and selection

The new version is:

```text
PANEL_VERSION = OC3_GALAXY_ELIGIBILITY_PANEL_V2
NORTH_BRICKS = 8
SOUTH_BRICKS = 8
TOTAL_BRICKS = 16
```

For each eligible canonically resolved brick, encode exactly these UTF-8 bytes with LF line endings, no terminal spaces, and one final LF:

```text
OC3-GALAXY-ELIGIBILITY-PANEL-V2
region=<north-or-south>
brickname=<canonical-provider-brickname>
brickid=<base-10-integer-with-no-leading-zeroes>
```

Compute lowercase hexadecimal SHA-256. Sort independently within canonical region by:

```text
(selection_sha256 ascending, brickname ASCII bytes ascending, brickid integer ascending)
```

Select the first eight per canonical region without replacement. A `GLOBAL_BRICK_IDENTITY` may occur at most once in V2. Hash collision, fewer than eight eligible identities in either region, fixture leakage, or repeated selected global identity fails closed.

The V2 domain-separation prefix makes a V1 hash byte sequence and V2 hash byte sequence unequal for the same region and identity. V1 hashes and manifests are never reused.

## 10. Closed aggregate overlap audit

Before selection, the corrected stage records only these aggregate counts:

```text
global_bricks_seen_in_north_summary
global_bricks_seen_in_south_summary
global_identities_appearing_in_both
overlaps_with_PHOTSYS_N
overlaps_with_PHOTSYS_S
overlaps_with_PHOTSYS_BLANK
PHOTSYS_missing
PHOTSYS_invalid
PHOTSYS_duplicate_or_conflicting
canonical_row_missing
PHOTSYS_survey_primary_conflicts
noncanonical_rows_excluded_from_candidates
global_fixtures_excluded
eligible_north
eligible_south
```

The public audit contains no row-level overlap list. If row-level identities are strictly required for reproducibility, they may appear only inside the sealed technical panel manifest or a separately specified immutable technical audit, never in logs or narrative interpretation.

Overlap counts describe survey representation. They are not quality, depth, morphology, population, or preference evidence.

## 11. PHOTSYS firewall

The resolver authority exists only to establish canonical regional identity. The V2 projection allowlist is closed to `BRICKNAME`, `BRICKID`, and `PHOTSYS`, plus a later prospectively approved identity/geometry field only when indispensable for binding.

These values are forbidden for selection and ranking even if present:

```text
AREA_PER_BRICK
random-point rows or coordinates
random counts
observer quantities
source counts
model-family counts
morphology fields
depth
seeing
color
```

Unknown schema, unexpected row type, random-point representation, or inability to isolate the brick-level resolver fails closed. A complete file may be preserved locally only under a separately authorized acquisition contract; its nonprojected columns may not be decoded, materialized, serialized, or logged.

## 12. New execution identities and outputs

The prerequisite authority stage is:

```text
OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001
scope = PHOTSYS_BRICK_AUTHORITY_ONLY
```

The corrected offline binding stage is:

```text
OC3-GALAXY-ELIGIBILITY-PANEL-BINDING-002
panel_version = OC3_GALAXY_ELIGIBILITY_PANEL_V2
```

Its distinct outputs are:

```text
OC3_GALAXY_ELIGIBILITY_PANEL_MANIFEST_V2.json
OC3_GALAXY_ELIGIBILITY_OVERLAP_AUDIT_V2.json
OC3_GALAXY_ELIGIBILITY_PANEL_V2_TERMINAL.json
OC3_GALAXY_ELIGIBILITY_P1_AUTHORIZATION_CANDIDATE_V2.json
```

No V2 output may use a V1 stage ID, V1 panel version, V1 filename, V1 seal, or resume marker.

## 13. Required synthetic regression

Implementation of this amendment must add focused synthetic tests for:

- a global brick present in both regional views becoming `REGIONAL_VIEW_OVERLAP`;
- exact PHOTSYS N and S canonical mapping;
- PHOTSYS blank exclusion;
- missing, invalid, duplicate, and conflicting PHOTSYS failures;
- duplicates within one regional summary remaining fatal;
- root identity or geometry mismatch failure;
- missing canonical regional row failure;
- PHOTSYS/`survey_primary` conflict failure;
- noncanonical row exclusion from candidacy;
- no duplicated panel member from overlap;
- global fixture exclusion through the root identity;
- exact 8+8 V2 selection and insufficient-cardinality stop;
- row-order invariance;
- exact V2 hash bytes and final LF;
- V1/V2 domain separation;
- immutable V1 evidence and distinct V2 outputs;
- zero Tractor cells, forbidden fields, morphology access, and network in synthetic tests.

Any implementation-code change requires the complete offline regression with zero failures, zero skips, and `real_network_requests=0` before an authority probe candidate can be reviewed.

## 14. Dependency and stop rules

The PHOTSYS resolver is not currently local or independently bound. Therefore:

```text
PANEL_V1 = FAILED_CLOSED
PHOTSYS_AUTHORITY = NOT_ACQUIRED
PANEL_V2 = NOT_STARTED
P1 = BLOCKED
```

The next action is to implement and synthetically validate `OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001` against the separate resource contract. No executable human command exists until that implementation and a literal resource candidate have been reviewed and sealed.

The authority probe must remain separate from Tractor, SDSS, Gaia, DESI, image, pixel, panel-selection, and P1 operations. The corrected P0/V2 may run only after the complete resolver authority is acquired, its integrity and physical/value semantics are validated, and a prospective V2 implementation is committed.

## 15. Amendment terminal

```text
GALAXY_ELIGIBILITY_REGION_RESOLUTION_AMENDMENT_FROZEN
```

Creating this amendment performed zero network requests, zero acquisitions, zero panel selection, zero Tractor/SDSS/Gaia/DESI access, zero source-row or image-pixel decode, zero morphology access, and zero changes to the failed V1 evidence.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
