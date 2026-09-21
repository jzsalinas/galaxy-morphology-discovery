# OC3 Galaxy Eligibility Bounded Evidence Specification

## 0. Status, authority, and non-execution boundary

**Stage ID:** `OC3-GALAXY-ELIGIBILITY-BOUNDED-EVIDENCE-001`

**Status:** FROZEN PROSPECTIVE SPECIFICATION / RESOURCE DESIGN ONLY

**Specification terminal:** `GALAXY_ELIGIBILITY_BOUNDED_EVIDENCE_SPEC_FROZEN`

**Authority:** `OC3_SCIENTIFIC_OBJECT_AND_COHORT_DESIGN_001.md`

**Authority SHA-256:** `8ee40ca3d4ab3ab22a2898aeb48bfd03dd39ca0a124f5b449e5d4d8f6a735ab4`

**Execution, acquisition, or selection authorized by this specification:** NONE

**Network, Tractor/SDSS/Gaia download, source-row decode, image/pixel access, cohort materialization, label access, and model operations:** NONE

This specification designs a bounded metadata experiment. It does not execute that experiment, select galaxies, create a membership list, choose an eligibility policy, or close any cohort-materialization gate.

The central question is:

> What morphology-independent evidence is practically available for distinguishing (A) technically valid DR9 source observations, (B) observations with independent spectroscopic extragalactic evidence, and (C) observations with positive stellar astrometric evidence, while never treating absent stellar evidence as galaxy evidence?

The three leading policies are exactly:

```text
A_SOURCE_OBSERVATIONS_NO_GALAXY_PRESELECTION
B_INDEPENDENT_SPECTROSCOPIC_EXTRAGALACTIC_GATE
C_INDEPENDENT_ASTROMETRIC_STAR_EXCLUSION
```

The photometric/color gate remains high-risk and unavailable. No policy is ranked prospectively.

## 1. Evidence-source classes

The stage keeps these paths independent:

| Path | Evidence source | Independence status | First-attempt status |
|---|---|---|---|
| `A` | DR9 Tractor technical source identity and catalog center | Provider source ecosystem | Required after schema/resource probe. |
| `C1_PROVIDER_EMBEDDED_GAIA_DR2_ASTROMETRY` | Gaia DR2 reference fields embedded by the DR9 provider | Not fully independent of DR9 source construction | Required feasibility path if exact semantics and projection are bound. |
| `C2_EXTERNAL_GAIA_DR3_ASTROMETRY` | Official Gaia DR3 source data joined under a new match contract | External authority | Designed here; not automatic in first network attempt. |
| `B1_DR9_SDSS_DR16_PREMATCHED_SPECTROSCOPY` | Official DR9 regional external SDSS DR16 match products | External spectroscopy prematched by the DR9 provider | Primary bounded spectroscopy candidate; access feasibility must be probed first. |
| `B2_DESI_DR1_SPECTROSCOPY` | Public DESI DR1 classifications/redshifts | External replication/fallback authority | Optional; unavailable in first attempt unless B1 is unusable and a separate bounded contract is frozen. |

`C1` may test availability and positive stellar evidence once a threshold contract exists, but it is not fully independent. `REF_CAT != G2`, no Gaia match, missing parallax, missing proper motion, or a nonsignificant measurement is never galaxy evidence.

The supplied documentary finding that public DESI DR1 contains more than 18 million unique targets establishes potential scope only. The global 20+ GB zcatalog is prohibited for this bounded stage.

## 2. Frozen morphology-blind brick panel

### 2.1 Local authority bindings

The future panel selector may read only the already local, immutable DR9 brick-summary authorities and fixture register below:

| Role | Local path | SHA-256 |
|---|---|---|
| Root geometry | `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| North summary | `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz` | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| South summary | `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz` | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |
| Existing fixture bricks | `oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv` | `147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6` |

The selector must validate complete hashes and the already frozen physical/value contracts before reading allowed cells. The south patch list is not a panel-selection input: restricting this eligibility panel to patched bricks would introduce a patch-specific coverage condition unrelated to the central question.

### 2.2 Panel size and regional balance

The exact panel is:

```text
PANEL_VERSION = OC3_GALAXY_ELIGIBILITY_PANEL_V1
NORTH_BRICKS = 8
SOUTH_BRICKS = 8
TOTAL_BRICKS = 16
```

The size is frozen before any Tractor, spectroscopy, Gaia, source-count, match, or eligibility outcome is observed. It bounds resource identities and permits region-separated feasibility reporting. It is not a power calculation and must not be described as statistically representative of DR9.

### 2.3 Technical eligibility before hashing

A brick enters the hash universe only if all of the following pass using the local summary contracts:

1. regional provenance is exactly `north` or `south` from the immutable input role;
2. `brickname` is a valid canonical eight-character provider identity;
3. `brickid` is valid and joins exactly one-to-one with the root row of the same `brickname` and geometry;
4. `ra`, `dec`, `ra1`, `ra2`, `dec1`, `dec2`, and `area` pass the frozen finite/range semantics;
5. `survey_primary == true`;
6. `nexp_g`, `nexp_r`, and `nexp_z` are valid integers and each is at least 1 under `GRZ_MEDIAN_PRESENT_V1`;
7. no duplicate `brickname` or `brickid` exists within or across the candidate region views; and
8. `(region, brickname)` is absent from the exact fixture set in `OC3_DEVELOPMENT_BRICKS.csv`.

The fixture exclusion currently binds south `3443m052` and north `2478p325`, but implementations must derive the exclusion set from the hash-bound file rather than hard-code those names.

The eligibility step must not read or use source/model counts (`nobjs`, `npsf`, `nsimp`, `nrex`, `nexp`, `ndev`, `ncomp`, `nser`, `ndup`), PSFSIZE, depth, extinction, transmissions, sky, WISE, colors, Tractor rows, morphology, SGA, Galaxy Zoo, or any eligibility outcome.

### 2.4 Canonical hash selection

For each eligible brick, encode exactly this UTF-8 byte sequence with LF line endings and no terminal spaces:

```text
OC3-GALAXY-ELIGIBILITY-PANEL-V1
region=<north-or-south>
brickname=<canonical-provider-brickname>
brickid=<base-10-integer-with-no-leading-zeroes>
```

The sequence has one final LF. Compute lowercase hexadecimal SHA-256, sort independently within each region by:

```text
(selection_sha256 ascending, brickname ASCII bytes ascending, brickid integer ascending)
```

Select the first eight per region without replacement. A hash collision, duplicate identity, fewer than eight eligible bricks in either region, authority mismatch, join discrepancy, or fixture leak fails closed. Input row order must not affect the panel or its seal.

The future panel manifest records input hashes, eligibility rule version, all 16 identities, each selection hash, exclusion counts by technical reason, tie count, order hash, and a canonical JSON seal. This stage specification does not run the selector or name the selected bricks.

## 3. Tractor resource contract

For every sealed panel brick, the exact candidate resource is:

```text
https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/
<region>/tractor/<AAA>/tractor-<brickname>.fits
```

with:

```text
AAA = brickname[:3]
```

Literal URLs must be materialized from the sealed panel manifest, never from source-code brick constants. Before any row acquisition, a resource/schema probe must record final URL, redirects, HTTP status, `Content-Length`, `Accept-Ranges`, ETag if present, Last-Modified if present, retrieval timestamp UTC, bounded header bytes, FITS HDU inventory, BINTABLE layout, row count/width, ordered columns, TFORM/dtype/shape, null/scaling/unit cards, compression/layout, and schema/header hashes.

Full Tractor GETs are prohibited until selective access is proven. The FITS schema may recognize denied column names for validation, but no denied cell bytes may be decoded, materialized, serialized, or logged.

If a provider-supported projection or a validated bounded byte-range plan cannot guarantee that only allowlisted cell values cross the reader boundary, the stage must stop with:

```text
TRACTOR_SELECTIVE_COLUMN_FIREWALL_UNAVAILABLE
```

Downloading a complete Tractor table and ignoring forbidden columns afterward does not satisfy the firewall.

## 4. Tractor column firewall

### 4.1 Closed allowlist

The bounded reader has two explicit projections. `A_CORE` contains exactly nine fields:

```text
RELEASE
BRICKID
OBJID
BRICKNAME
BRICK_PRIMARY
RA
DEC
BX
BY
```

`C1_EXTENSION` may add exactly these ten provider-embedded external-reference fields only after their exact DR9 schema and semantics are bound:

```text
REF_CAT
REF_ID
REF_EPOCH
PARALLAX
PARALLAX_IVAR
PMRA
PMRA_IVAR
PMDEC
PMDEC_IVAR
GAIA_ASTROMETRIC_PARAMS_SOLVED
```

The full projected union is therefore at most 19 columns. Case, HDU, order within the provider schema, TFORM/dtype, vector shape, null/scaling, units, and value semantics must match a versioned contract. Missing `C1_EXTENSION` semantics makes C1 unavailable; it does not weaken `A_CORE` or permit aliases.

### 4.2 Denylist and nonprojectable fields

The following are explicitly denied:

```text
TYPE
DCHISQ
SERSIC
SHAPE_R
SHAPE_E1
SHAPE_E2
```

All model-family goodness quantities, morphology-derived fields, photometric/color galaxy cuts, and every provider column outside the 19-field union are nonprojectable in this stage. This includes `MASKBITS` and `FITBITS`: they remain relevant to later observer audits but are not required for this eligibility evidence reader.

Schema validation may compare denied names and structural metadata against an exhaustive provider contract. It must never access denied values. Unknown columns or structural discrepancies fail before any row iteration unless a prior prospective amendment classifies them.

### 4.3 Mandatory tripwires

Every reader and terminal must expose these counters:

```text
forbidden_field_observations = 0
forbidden_value_decode_count = 0
forbidden_value_materialization_count = 0
forbidden_value_serialization_count = 0
forbidden_value_log_count = 0
morphology_label_accesses = 0
```

Here `forbidden_field_observations` means observation of a denied cell value; recognizing a denied column name in header-only schema validation is not a value observation. Any nonzero counter is an integrity failure and prevents evidence publication.

## 5. Policy A evidence contract

`A_SOURCE_OBSERVATIONS_NO_GALAXY_PRESELECTION` measures technical source-observation availability only. For each panel brick it reports:

- total Tractor rows from table structure/accounting;
- rows whose `A_CORE` projection decodes validly;
- `BRICK_PRIMARY == true` rows;
- unique valid `(RELEASE, BRICKID, OBJID)` identities;
- valid `BRICKNAME`, RA/DEC, and BX/BY center fields;
- release and region consistency;
- missing/invalid technical fields; and
- duplicate/conflicting technical identities.

It does not separate stars from galaxies, inspect `TYPE`, or infer astrophysical independence. Its row-level state is one of:

```text
A_TECHNICAL_SOURCE_VALID
A_TECHNICAL_SOURCE_INVALID
A_TECHNICAL_SOURCE_AMBIGUOUS
```

The bounded panel establishes feasibility and source-population size only within the selected bricks.

## 6. C1 provider-embedded Gaia DR2 contract

`C1_PROVIDER_EMBEDDED_GAIA_DR2_ASTROMETRY` uses only `C1_EXTENSION` values whose exact provider semantics have been bound. The evidence is embedded in the DR9 source ecosystem and may not be represented as a fully independent cross-match.

The first bounded attempt may measure:

- `REF_CAT=G2` availability only if `G2` is confirmed by the official DR9 contract;
- valid/invalid/missing `REF_ID` and `REF_EPOCH` states;
- availability states for parallax, PMRA, PMDEC, their inverse variances, and `GAIA_ASTROMETRIC_PARAMS_SOLVED`;
- consistency of missing/null/sentinel behavior; and
- the fraction in each evidence state by region and brick.

It must preserve exactly these evidence outcomes:

```text
STAR_EVIDENCE_POSITIVE
STAR_EVIDENCE_NOT_ESTABLISHED
ASTROMETRY_UNAVAILABLE_OR_AMBIGUOUS
```

`STAR_EVIDENCE_POSITIVE` is unavailable until a separate prospective contract defines a justified positive-star criterion. Until then, a valid Gaia-linked measurement remains `STAR_EVIDENCE_NOT_ESTABLISHED`; absent, invalid, or ambiguous astrometry remains `ASTROMETRY_UNAVAILABLE_OR_AMBIGUOUS`.

The unresolved threshold state is:

```text
STELLAR_ASTROMETRIC_THRESHOLD_REQUIRES_PROSPECTIVE_EVIDENCE
```

No significance threshold, inverse-variance conversion rule, or logical combination of parallax/proper motion is frozen here. No-Gaia, `REF_CAT != G2`, missing astrometry, zero inverse variance, or evidence below a future positive threshold is never converted to galaxy or extragalactic evidence.

## 7. C2 external Gaia DR3 design

`C2_EXTERNAL_GAIA_DR3_ASTROMETRY` remains a separate optional path. A future official Gaia DR3 contract must bind at least:

```text
source_id
reference_epoch
ra
dec
parallax
parallax_error
parallax_over_error
pmra
pmra_error
pmdec
pmdec_error
astrometric_params_solved
```

Before any query, the match specification must freeze:

1. source and target coordinate frames/units;
2. epoch handling and proper-motion propagation direction;
3. angular match radius justified prospectively;
4. uncertainty use, if any;
5. multiple-match and tie handling;
6. missing/invalid-source states;
7. positive stellar-evidence criterion and its provenance; and
8. query service, exact query text, returned schema, row/byte caps, retries, and deterministic ordering.

The purpose is to measure whether independent Gaia DR3 changes or strengthens C1 evidence. C1 and C2 identities, values, derived states, counts, and provenance remain separate. C2 is not automatically executed with the first Tractor attempt.

No angular radius or stellar threshold is chosen by convention in this specification.

## 8. B1 DR9–SDSS DR16 prematched spectroscopy contract

The primary bounded spectroscopy candidate is:

```text
B1_DR9_SDSS_DR16_PREMATCHED_SPECTROSCOPY
survey-dr9-<region>-specObj-dr16.fits
```

The supplied official DR9 semantics state that each regional file contains Tractor photometry matched row-by-row to SDSS DR16 spectroscopy using the nearest Legacy Surveys `BRICK_PRIMARY` photometric object within 1.5 arcsec. DR9 retains all duplicate SDSS spectroscopic rows. These are provider match semantics, not a new project nearest-neighbor rule.

Before data-row access, the documentary/resource probe must bind:

- exact north/south literal URLs, final URLs, sizes, checksums when published, and rights/provenance;
- exact HDU and exhaustive schema;
- Tractor identity fields sufficient to join `(RELEASE, BRICKID, OBJID)` without morphology fields;
- unique SDSS spectroscopic-observation identity fields;
- documented spectroscopic class, redshift, warning/quality/failure fields and null semantics;
- the provider's 1.5-arcsec prematch semantics and duplicate-row policy; and
- selective column/row access feasibility for the 16-brick panel.

The evidence categories are:

```text
SPECTRO_EXTRAGALACTIC_EVIDENCE
SPECTRO_STELLAR_EVIDENCE
SPECTRO_AMBIGUOUS_OR_BAD
```

Exact class values, redshift validity, warning masks, confidence/quality rules, and conflicts are not invented here. They must be frozen from the SDSS data model before classification. Photometric `TYPE`, DCHISQ, model family, color, or shape may not interpret spectroscopy.

Each spectroscopic observation remains individually identified. Duplicate rows are not silently collapsed. A per-source aggregate must retain observation count, consistency/conflict state, and all match ambiguity states without allowing duplicate spectra to inflate the number of unique DR9 sources.

## 9. B1 size/access gate and B2 fallback

The B1 regional files may be much larger than the Tractor panel. The first network probe may issue only HEAD and bounded header/schema Range requests. Before a full GET, it must determine whether panel-brick rows and allowlisted columns can be obtained without downloading a disproportionate regional catalog or decoding unrelated rows/fields.

If safe bounded access is not proven, the result is:

```text
B1_BOUNDED_ACCESS_REQUIRES_ALTERNATE_STRATEGY
```

The stage then compares prospectively:

- provider-supported bounded access;
- a separately justified query service with immutable query/output contracts;
- a spatially scoped or bounded DESI DR1 product/query; or
- another reproducible spectroscopy authority.

It must not widen the resource envelope or download the complete regional file automatically.

`B2_DESI_DR1_SPECTROSCOPY` is optional for the first evidence attempt. It may become a bounded fallback or later replication only after exact DESI release/product, target identity, spectral class/redshift, quality fields, match semantics, target-selection provenance, query/subset mechanism, caps, and rights are frozen. The global zcatalog is prohibited.

## 10. Cross-match ambiguity contract

Every external path B1, B2, or C2 must preserve exactly one of these match states:

```text
NO_MATCH
UNIQUE_MATCH
MULTIPLE_MATCH
AMBIGUOUS_MATCH
INVALID_MATCH
```

Their meanings are:

| State | Meaning | Evidence consequence |
|---|---|---|
| `NO_MATCH` | No candidate satisfies the frozen match contract. | External evidence absent; never galaxy evidence. |
| `UNIQUE_MATCH` | Exactly one valid candidate satisfies every frozen rule. | Evidence may be classified by the source-specific contract. |
| `MULTIPLE_MATCH` | More than one valid candidate remains and multiplicity is scientifically retained, such as duplicate spectra. | Retain all identities; do not choose nearest automatically. |
| `AMBIGUOUS_MATCH` | Candidates or conflicting evidence cannot be resolved by the frozen contract. | Evidence remains unknown/ambiguous. |
| `INVALID_MATCH` | Required fields, frames, quality, identity, or provenance fail validation. | Evidence rejected with an explicit technical reason. |

No implementation may convert `NO_MATCH` to galaxy, choose a nearest candidate in `MULTIPLE_MATCH`, or erase conflicts without a separately frozen rule. C1 uses its provider link and availability states rather than pretending it was independently rematched.

## 11. Coverage and selection-function metrics

The closed aggregate metric families are calculated independently for A, B1, C1, and any separately authorized B2/C2 path:

### 11.1 Population and evidence states

- panel bricks expected/available/failed;
- total technical rows and unique technical source identities;
- primary, invalid, conflicting, and missing-identity counts;
- positive, not-established, unavailable, ambiguous, bad, and no-match counts as applicable;
- north/south and per-brick counts;
- match availability and ambiguity-state counts;
- duplicate spectroscopic-observation counts without duplicate source inflation; and
- effective retained fraction with numerator, denominator, and state definition explicit.

### 11.2 Observer-domain evidence

After the panel seal is frozen, a separate summary-only projection may read from the already local regional brick summaries:

```text
region
brickname
brickid
nexp_g
nexp_r
nexp_z
nexphist_g
nexphist_r
nexphist_z
psfsize_g
psfsize_r
psfsize_z
area
survey_primary
```

NEXP, PSFSIZE, and area do not participate in hash ordering beyond the pre-hash minimum g/r/z availability rule and `survey_primary`. PSFSIZE and detailed NEXP values are read only after selection for bias reporting. Source/model counts, depth, colors, extinction, `TYPE`, and model families remain forbidden.

The aggregate report records missingness and exact predefined summaries by region and evidence state for:

- NEXP median/transition-support metadata already defined by the provider summary contract;
- PSFSIZE g/r/z availability and distribution summaries;
- regional/survey coverage and brick area; and
- panel resource availability.

Before implementation, the exact statistic schema must freeze count, missing count, finite minimum/maximum, median, and predefined categorical support states; no post-outcome bin or threshold may be added. These metrics reveal potential eligibility-induced observer bias. They do not establish causality or morphology balance.

Higher retained fraction, higher match rate, or lower missingness must not be labeled superior and cannot alone select a policy.

## 12. Closed outputs

No output is a scientific cohort membership list. The future stage may publish only:

| Output | Content boundary |
|---|---|
| `OC3_GALAXY_ELIGIBILITY_PANEL_MANIFEST.json` | Sixteen brick identities, selection hashes, authority bindings, technical exclusion counts, order hash, and seal. No source rows. |
| `OC3_GALAXY_ELIGIBILITY_RESOURCE_MANIFEST.csv` | Literal URLs, roles, final URLs, status, Content-Length, range behavior, versions/timestamps, schema/header hashes, request/byte accounting. |
| `OC3_TRACTOR_ELIGIBILITY_SCHEMA_CONTRACT.json` | Exhaustive provider schema structure and classification; no cell values. |
| `OC3_B1_SPECTROSCOPY_SCHEMA_ACCESS_REPORT.md` | B1 official semantics, exact schemas, sizes, bounded-access feasibility, and alternate-strategy status. |
| `OC3_GALAXY_ELIGIBILITY_TECHNICAL_EVIDENCE.parquet` | Allowlisted source identities and A/B/C evidence/match states only, if a later acquisition is authorized. |
| `OC3_GALAXY_ELIGIBILITY_POLICY_COVERAGE.csv` | Aggregate policy/state/region/brick counts and retained fractions. |
| `OC3_GALAXY_ELIGIBILITY_OBSERVER_BIAS.csv` | Closed NEXP/PSFSIZE/coverage summaries by evidence state, without morphology fields. |
| `OC3_GALAXY_ELIGIBILITY_AMBIGUITY.csv` | Match-state, duplicate, conflict, invalid, missing, and unknown aggregates. |
| `OC3_GALAXY_ELIGIBILITY_RESOURCE_ACCOUNTING.json` | Per-substage and cumulative requests, bytes, retries, resources, stops, and caps. |
| `OC3_GALAXY_ELIGIBILITY_DECISION.md` | One allowed policy outcome with evidence references; no object list. |
| `OC3_GALAXY_ELIGIBILITY_TERMINAL.json` | Acquisition state, policy-decision state, tripwires, hashes, and counters kept separate. |

The row-level evidence schema is closed to:

```text
stage_id
panel_version
panel_brick_id
region
release
brickid
objid
brickname
brick_primary
ra
dec
bx
by
observation_id
a_evidence_state
c1_link_state
c1_astrometry_availability_state
c1_stellar_evidence_state
b1_match_state
b1_spectro_evidence_state
b1_spectroscopic_observation_count
b1_duplicate_consistency_state
c2_execution_state
c2_match_state
c2_stellar_evidence_state
technical_missingness_code
evidence_provenance_ids
```

No `TYPE`, DCHISQ, Sérsic, shape, photometric color cut, Galaxy Zoo, Zoobot, Hubble/T type, SGA galaxy identity, morphology prediction, or scientific cohort membership flag may appear.

## 13. Label and field firewall

The stage uses a strict allowlist. Forbidden access includes:

- `TYPE` and all `DCHISQ` morphology-model values;
- `SERSIC`, `SHAPE_R`, `SHAPE_E1`, and `SHAPE_E2`;
- Galaxy Zoo votes/classes and subject-derived morphology fields;
- Zoobot morphology predictions or embeddings;
- Hubble/T types and human morphology annotations;
- SGA identity used as positive galaxy truth;
- photometric/color galaxy cuts; and
- any morphology-derived filter, parameter, threshold, balancing rule, or outcome.

The required successful terminal value is:

```text
forbidden_field_observations = 0
```

The firewall must be enforced before row decode through schema classification, projection allowlists, nonprojectable column handles, logs without denied names/values where applicable, output-schema assertions, and synthetic tripwires. A post-decode column drop is insufficient.

## 14. Staged resource and human-execution model

Network work is split into independently authorized, resumable human CLI stages. No stage resets cumulative accounting.

### 14.1 Stage P0 — offline panel binding

- validate four local authority hashes;
- decode only allowed brick-summary fields;
- apply technical eligibility, fixture exclusion, and hash selection;
- write and seal the 16-brick panel manifest;
- network requests: 0;
- Tractor/SDSS/Gaia rows decoded: 0.

### 14.2 Stage P1 — documentary/resource/schema probe

This is the first network-capable stage and the next executable step. It may:

- retrieve/bind the exact official DR9 Tractor/C1 and B1 documentation under a closed documentary allowlist;
- issue HEAD requests for the 16 Tractor resources and exact north/south B1 resources;
- use bounded Range GETs only to recover FITS headers/schema blocks;
- compute whether a cell-level projection plan could avoid forbidden values; and
- publish resource, schema, size, rights/provenance, and access-feasibility evidence.

It may not decode a single table cell.

Its maximum envelope is:

```text
panel_bricks = 16
tractor_resources = 16
b1_resources = 2
gaia_resources_or_queries = 0
desi_resources_or_queries = 0
science_pixels = 0
table_cell_values_decoded = 0
full_fits_gets = 0
network_requests_started <= 96, including retries
response_body_bytes <= 16 MiB
per_resource_range_body_bytes <= 512 KiB
concurrency_per_service <= 4
retry_requests_per_resource <= 1
redirects_per_request <= 3
```

The implementation must tighten these caps when exact header sizes/documentary resources are known; it may never increase them without a prospective amendment. Extensive output goes to a log and receipts. Human execution is mandatory because the stage uses network resources and retry/throttling behavior.

### 14.3 Stage P2 — bounded Tractor A/C1 acquisition

Unavailable until P1 proves selective projection and a separate acquisition specification freezes exact bytes/requests. It may acquire only A_CORE/C1_EXTENSION values for the 16 bricks. If projection cannot exclude every other cell value, P2 remains blocked.

### 14.4 Stage P3 — optional B1 spectroscopy access

Unavailable until P1 resolves exact schema, quality semantics, panel-row access, and an independent cap. It must not download a disproportionate regional file merely because it is the published product.

### 14.5 Stage P4 — optional C2 or B2

Unavailable until a separate query/resource contract freezes external match semantics and caps. C2 and B2 must not be combined automatically with P2 or P3.

## 15. Failure, inconclusive, and decision states

Acquisition completion and eligibility-policy resolution are independent.

The later execution terminal must carry one acquisition state:

```text
GALAXY_ELIGIBILITY_EVIDENCE_ACQUISITION_COMPLETED
GALAXY_ELIGIBILITY_EVIDENCE_ACQUISITION_PARTIAL
GALAXY_ELIGIBILITY_EVIDENCE_ACQUISITION_FAILED
```

and exactly one policy-decision state:

```text
GALAXY_ELIGIBILITY_POLICY_RESOLVED
GALAXY_ELIGIBILITY_POLICY_REMAINS_UNRESOLVED
ADDITIONAL_BOUNDED_EVIDENCE_REQUIRED
```

`GALAXY_ELIGIBILITY_POLICY_RESOLVED` requires a prospectively valid path with bound semantics, reproducible identities, explicit positive/unknown/ambiguous states, quantified regional/observer availability, documented selection function, closed firewall, and sufficient evidence to freeze one policy without using source count alone. If C is selected, the stellar threshold contract must already be resolved. If B is selected, the spectroscopic class/redshift/quality and duplicate rules must already be resolved. If A is selected, the decision must explicitly accept its mixed source population and observer risks.

`ADDITIONAL_BOUNDED_EVIDENCE_REQUIRED` applies when the current bounded attempt is valid but a named, resource-bounded follow-up can resolve a specific remaining question. `GALAXY_ELIGIBILITY_POLICY_REMAINS_UNRESOLVED` applies when semantics, access, ambiguity, bias, or representativeness remain insufficient without a new prospective design choice.

Negative and inconclusive outcomes are valid. No result forces a galaxy gate or permits fallback to Tractor `TYPE`, color, SGA, or morphology labels.

## 16. Next executable stage

The exact next executable stage is:

**Stage ID:** `OC3-GALAXY-ELIGIBILITY-RESOURCE-SCHEMA-PROBE-001`

**Scope:** `DOCUMENTARY_RESOURCE_SCHEMA_PROBE_ONLY`

It consists of P0 followed, only after offline review and separate human authorization, by P1. Its implementation must be deterministic, idempotent, fail-closed, and resumable only within the frozen caps. It must expose `--help`, `--validate-inputs`, `--dry-run`, the offline panel-binding mode, and a separately gated probe mode.

Before handoff, implementation must pass synthetic tests for:

- panel invariance to row order;
- exact 8+8 selection and fixture exclusion;
- authority mismatch and low-cardinality stops;
- literal Tractor URL and `AAA=brickname[:3]` construction;
- allowlist-only schema projection;
- denied/unknown column tripwires before cells;
- zero-cell header probing;
- request/byte/concurrency/retry caps;
- redirect and final-URL binding;
- B1 size/access stop;
- zero Gaia/DESI construction;
- canonical manifests, logs, terminals, and restart behavior; and
- zero morphology labels, pixels, models, or cohort outputs.

No implementation or execution is authorized by this specification task.

## 17. Specification success declaration

Creating this specification performed:

- zero panel selection;
- zero Tractor, SDSS, Gaia, or DESI acquisition;
- zero network requests;
- zero table-cell or image-pixel reads;
- zero source, galaxy, or cohort selection;
- zero scientific cohort materialization;
- zero morphology-label or forbidden-field value access;
- zero model, encoder, embedding, clustering, anomaly, or morphology operations; and
- zero changes to existing technical fixtures.

The specification terminal is:

```text
GALAXY_ELIGIBILITY_BOUNDED_EVIDENCE_SPEC_FROZEN
```

This terminal freezes resource design and decision semantics only. It does not mean evidence was acquired or an eligibility policy was resolved.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
