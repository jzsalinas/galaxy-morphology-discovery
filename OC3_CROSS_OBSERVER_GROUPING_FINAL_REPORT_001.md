# OC3 Cross-Observer Grouping Final Report 001

## Decision

`CROSS_OBSERVER_GROUPING_EVIDENCE_INCONCLUSIVE`

## Evidence obtained

The mission preserved exact snapshots of the three official DR9 documentation pages and corrected the Data Lab metadata query after a governed diagnostic showed that `TAP_SCHEMA.columns` has no `schema_name` column. The corrected responses confirm `ls_dr9.tractor`, `ls_dr9.tractor_n`, and `ls_dr9.tractor_s`, and all eleven prospectively allowlisted metadata fields in each table.

The offline review classified eight documentary claims as `SUPPORTED`: catalog source identity, `BRICK_PRIMARY` semantics, north/south processing domains, the resolved catalog's selection role rather than an equivalence-map role, astrometric field semantics, omission of calibration error from RA/DEC inverse variance, Gaia DR2 astrometric provenance, and regional Data Lab table availability.

## Unresolved evidence

The primary Budavári–Szalay cross-identification article could not be acquired through three separately contracted exact transports: the original arXiv URL returned HTTP 406, the official arXiv export URL returned HTTP 406, and the exact ADS bibcode URL returned HTTP 403. All failed before a response body was read. No mirror, redirect, familiar matching radius, or undocumented substitute was accepted.

Consequently `CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS` and `BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD` remain `INCONCLUSIVE`. The frozen Stage B rule requires all ten claims to be supported, so the documentary Gate is `DOCUMENTARY_SOURCE_METADATA_PILOT_INCONCLUSIVE`.

## Track decisions

- Track A, `SPLIT_SAFETY_GROUPING`: `INCONCLUSIVE`. No `SPLIT_GROUP_ID` was materialized or validated.
- Track B, `OBSERVER_REPLICATION_PAIRING`: `INCONCLUSIVE`. No `OBJECT_GROUP_ID`, match, nearest-neighbor choice, radius, or score threshold was materialized.

The inconclusive Track B result is not reinterpreted as Track A evidence. A shared brick was never treated as same-object identity.

## Resource and firewall accounting

The mission used 11 of 12 network requests and 330,391 of 16,777,216 allowed application-body bytes. One request and 16,446,825 bytes remain unused. Six single-use permits were issued. All denied scientific counters remained zero, including source rows, PHOTSYS, TYPE, DCHISQ, shapes, photometry, photo-z, pixels, morphology, labels, models, training, embeddings, clustering, Panel V3, and P1.

The remaining request cannot satisfy the unresolved primary-literature requirement and also execute a valid two-domain source pilot under the frozen prerequisites. Spending it on another unproven transport would not close the scientific question. The mission therefore terminates inconclusively without source-row acquisition.

## Reproducibility bindings

- Offline documentary claim matrix: `e929e9517504a3da14f046722b01719c88888e6c8781a50c3404e95bec555a84`
- Final claim matrix: `c483939ad407281beeecac818bf767763a7301920b064c0e10ddd4f5b2b4d37f`
- Primary article failure terminal: `73192479028d882feda07491370048dddfd896506044f8b68b48d671350f85c3`
- Final state is produced only by the frozen Policy Core V2 governor.
