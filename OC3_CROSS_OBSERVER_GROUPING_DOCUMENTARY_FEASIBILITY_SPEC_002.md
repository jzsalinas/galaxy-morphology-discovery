# OC3 Cross-Observer Grouping Documentary Feasibility Specification 002

Scope: `PUBLIC_DOCUMENTARY_AND_SCHEMA_METADATA_ONLY`.

This prospective correction preserves the scientific question, two-track
architecture, metadata firewall, no-radius rule, no-nearest rule, authority
classes, mission budgets, and four mission terminals. It supersedes the
preauthorization execution binding in Candidate 001 without changing the
scientific design.

## Stage A: DOCUMENTARY_EVIDENCE_ACQUISITION

Stage A may acquire only the six literal resources in Resource Manifest 002.
All are `HASHED_RESPONSE_SNAPSHOT` resources. Successful acquisition records
requested and final URL, HTTP status, UTC retrieval timestamp, content type,
optional content length, optional ETag, optional Last-Modified, exact body byte
count, exact body SHA-256, and capture mode. Each body is published locally as
a read-only immutable snapshot. No upstream revision immutability is asserted.

Its only successful terminal is
`DOCUMENTARY_EVIDENCE_ACQUIRED_PENDING_OFFLINE_SEMANTIC_REVIEW`. This terminal
does not pass the documentary Gate and cannot produce a mission grouping
terminal.

## Stage B: OFFLINE_DOCUMENTARY_SEMANTIC_REVIEW

Stage B is a later, separately contracted offline action. It may read only the
captured snapshots and their transport evidence. It may not access source rows,
scientific PHOTSYS values, pixels, morphology, labels, matching, or thresholds.
Documentary text containing the token `PHOTSYS` is not a PHOTSYS value read and
must not be used to recover a canonical north/south assignment.

The review must classify every required claim:

1. `CATALOG_SOURCE_IDENTITY`
2. `BRICK_PRIMARY_SEMANTICS`
3. `NORTH_SOUTH_PROCESSING_DOMAINS`
4. `RESOLVED_CATALOG_NOT_EQUIVALENCE_MAP`
5. `ASTROMETRIC_FIELD_SEMANTICS`
6. `CALIBRATION_ERROR_OMITTED_FROM_IVARS`
7. `GAIA_DR2_ASTROMETRIC_PROVENANCE`
8. `REGIONAL_DATALAB_TABLE_AVAILABILITY`
9. `CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS`
10. `BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD`

The closed documentary review outcomes are:

- `DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE`
- `DOCUMENTARY_SOURCE_METADATA_PILOT_INCONCLUSIVE`
- `DOCUMENTARY_SOURCE_METADATA_CONFLICT`

`DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE` means only that a bounded
source-metadata pilot can be designed prospectively without selecting a radius
or score threshold. It does not support a grouping strategy or authorize a
source-row query.
