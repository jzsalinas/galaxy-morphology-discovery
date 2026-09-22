# OC3 Galaxy Eligibility PHOTSYS Authority Contract 001

## 0. Status and purpose

**Contract ID:** `OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-CONTRACT-001`

**Status:** FROZEN PROSPECTIVE RESOURCE CONTRACT / NO NETWORK

**Authority stage:** `OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001`

**Scope:** `PHOTSYS_BRICK_AUTHORITY_ONLY`

**Parent amendment:** `OC3_GALAXY_ELIGIBILITY_REGION_RESOLUTION_AMENDMENT_001.md`

This contract defines the smallest staged operation that can bind and acquire the official DR9 brick-level PHOTSYS resolver needed by panel V2. It does not authorize that operation.

## 1. Required resource identity

The target provider product is exactly:

```text
survey-bricks-dr9-randoms-0.48.0.fits
```

It must be an official Legacy Surveys DR9 brick-level resolver whose documented value semantics include `PHOTSYS=N`, `PHOTSYS=S`, and blank PHOTSYS. A similarly named random-point catalog, a different version, a mirror without independently bound provenance, a generated substitute, or any collection of twenty random catalogs is out of scope.

Current offline resolution state:

```text
literal_official_url = UNRESOLVED_PENDING_AUTHORIZED_AUTHORITY_PROBE
final_url = UNRESOLVED
Content-Length = UNRESOLVED
ETag = UNRESOLVED
Last-Modified = UNRESOLVED
provider_checksum = UNRESOLVED
FITS_HDU = UNRESOLVED
row_count = UNRESOLVED
row_width = UNRESOLVED
ordered_schema = UNRESOLVED
rights_local_preservation = UNRESOLVED
```

No local document or artifact currently binds the literal official URL. It must not be guessed from a filename or directory convention.

## 2. Closed value projection

The required semantic projection is exactly:

```text
BRICKNAME
BRICKID
PHOTSYS
```

Before any cell decode, the probe must bind exact case, HDU, ordered column inventory, `TFORM`, dtype, vector shape, null/scaling cards, units, string padding behavior, and value semantics. Aliases are prohibited.

An additional identity or geometry field requires a prospective clarification demonstrating that the three-field projection cannot establish an exact root join. Such a field remains technical-only and cannot affect eligibility or hash ordering.

## 3. Firewall and representation gate

The probe may inspect FITS header names and structural metadata. It must not decode values from:

```text
AREA_PER_BRICK
random-point coordinates or rows
random counts
observer quantities
source or model counts
depth, seeing, or color fields
morphology fields
```

Every field outside the approved projection is nonprojectable. The reader must expose zero-valued counters for forbidden decode, materialization, serialization, logging, and morphology access.

If the product is not a brick-level table with one resolver row per represented global brick identity, the stage stops with:

```text
PHOTSYS_AUTHORITY_NOT_BRICK_LEVEL_STOP
```

It may not decode a random-point catalog or derive PHOTSYS statistically.

## 4. Stage A — documentary and resource probe

The first future human-authorized operation is header/documentary only. It must:

1. resolve the exact official DR9 documentation resource for the filename and PHOTSYS semantics;
2. resolve the literal official provider URL without search crawling or mirrors;
3. issue HEAD to that one literal resource;
4. record redirects, final URL, status, `Content-Length`, `Accept-Ranges`, ETag, Last-Modified, and timestamp UTC;
5. use exact bounded FITS-header Range requests ending at header-block boundaries;
6. bind the complete HDU inventory and exhaustive table schema without reading table cells;
7. determine whether the product is brick-level and whether the three fields can be selectively decoded; and
8. record rights and local-preservation evidence.

The maximum prospective envelope is:

```text
documentary_resources <= 2
data_resources = 1
HEAD_data_requests = 1
full_FITS_GETs = 0
table_cell_values_decoded = 0
network_requests_started <= 72, including redirects
response_body_bytes <= 2 MiB
per_resource_header_range_bytes <= 512 KiB
concurrency = 1
automatic_retries = 0
redirects_per_request <= 3
```

An implementation must tighten these caps after its exact documentary allowlist and request plan are sealed. Any retry requires separate authorization. Every response and header block receives an immediate durable checkpoint.

Stage A may terminate only as:

```text
PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_RESOLVED
PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_INCONCLUSIVE
PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_FAILED
```

No resolved terminal authorizes full acquisition.

## 5. Stage B — complete authority acquisition

Stage B requires a separate prospective acquisition candidate and final human authorization created after Stage A review. It must bind:

- exact literal and final URL;
- exact observed `Content-Length` and a byte cap no larger than that reviewed size plus protocol overhead explicitly accounted outside body bytes;
- immutable header/schema contract;
- checksum/ETag/Last-Modified evidence;
- rights/local-preservation state;
- expected request count, concurrency one, and zero automatic retries;
- staging and immutable-publication paths;
- complete-file SHA-256 computed locally; and
- restart behavior that never overwrites a published identity.

The complete body must first enter staging. It may be published under `RAW_IMMUTABLE` only after length, full-file hash, and physical-contract checks pass. A later offline decode may project only the approved cells.

Stage B is blocked if the observed file exceeds the reviewed local/resource envelope, its rights are unresolved, its representation is not brick-level, or its full-body integrity cannot be bound.

## 6. Offline semantic validation after acquisition

Before V2 selection, an offline validator must require:

- canonical `BRICKNAME` bytes under `OC3_BRICKNAME_SEMANTICS_V1`;
- signed FITS integer `BRICKID` with no coercion;
- exact one-byte PHOTSYS semantics `N`, `S`, or ASCII space as documented;
- unique `BRICKNAME`, unique `BRICKID`, and unique pair inside the resolver;
- exact join to the root `GLOBAL_BRICK_IDENTITY`;
- explicit missing, blank, invalid, and conflict states; and
- zero use of nonprojected values.

The validator publishes aggregate value-state counts and a sealed identity-to-PHOTSYS technical authority required by V2. It publishes no panel and performs no hash selection.

## 7. Closed artifacts

The future implementation may publish only:

```text
OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST.json
OC3_PHOTSYS_AUTHORITY_RESOURCE_CANDIDATE.json
OC3_PHOTSYS_AUTHORITY_TRANSPORT_EVIDENCE.json
OC3_PHOTSYS_AUTHORITY_HEADER_SCHEMA_CONTRACT.json
OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json
OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json
```

After separately authorized complete acquisition and offline validation, it may additionally publish:

```text
RAW_IMMUTABLE/PHOTSYS_AUTHORITY/survey-bricks-dr9-randoms-0.48.0.fits
OC3_PHOTSYS_AUTHORITY_FILE_MANIFEST.json
OC3_PHOTSYS_AUTHORITY_VALUE_CONTRACT.json
OC3_PHOTSYS_AUTHORITY_AGGREGATE_AUDIT.json
OC3_PHOTSYS_AUTHORITY_VALIDATION_TERMINAL.json
```

No artifact may contain random-point rows, morphology fields, Tractor cells, panel membership, or a P1 authorization.

## 8. Authorization boundary and next action

No candidate or final authorization is created by this contract because the literal URL, exact size, schema, and rights are unresolved. Consequently, there is no safe exact human network command yet.

The next task is offline implementation and synthetic validation of the authority probe. Only after it creates a sealed literal candidate may a human command be reviewed. That command must run from the repository root, write an extensive log and compact terminal, preserve checkpoints, and remain within the tightened Stage A caps.

Tractor, SDSS, Gaia, DESI, panel V2, and the existing P1 remain blocked throughout both authority substages.

## 9. Contract terminal

```text
GALAXY_ELIGIBILITY_PHOTSYS_AUTHORITY_CONTRACT_FROZEN
```

Creating this contract performed zero network requests, zero downloads, zero FITS-header or table-cell access, zero panel selection, and zero changes to historical V1 evidence.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
