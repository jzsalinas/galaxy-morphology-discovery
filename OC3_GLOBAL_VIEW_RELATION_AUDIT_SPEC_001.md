# OC3 Global View Relation Audit Specification 001

## Status

Prospective executable specification. No execution or permit is authorized by this file.

## Contract

- Stage: `OC3-GLOBAL-VIEW-RELATION-AUDIT-001`
- Scope: `OFFLINE_GLOBAL_VIEW_RELATION_ONLY`
- Network requests/body bytes: `0 / 0`
- Concurrency: `1`
- Automatic retries/resume: `0 / false`
- Source rows, PHOTSYS, Tractor cells, pixels, morphology, and labels: `0`

The exact root, north, south, and fixture resources are bound by the action candidate. Summary-table decoding is restricted to identity and geometry fields listed by the mission specification. Provider bytes outside those spans may transit decompression as opaque bytes but may not be decoded or serialized.

## Deterministic algorithm

1. Verify each exact file hash, byte size, and frozen physical contract.
2. Decode the closed identity/geometry projection.
3. Require one-to-one root `BRICKNAME`, `BRICKID`, and pair identities.
4. Require uniqueness independently within north and south.
5. Join every regional row to exactly one root pair and compare geometry exactly.
6. Classify every root identity as north-only, south-only, both, or no regional view.
7. Join fixture names to one root identity and mark that identity globally excluded.
8. Publish aggregates and instrumentation only; do not publish row identities.

`GLOBAL_VIEW_BOTH` is a valid relation, never an inter-summary duplicate failure. Internal regional duplicates remain fatal.

## Success and failure

Success terminal: `GLOBAL_VIEW_RELATION_VALIDATED`.

Fail-closed codes include `ROOT_IDENTITY_DUPLICATE`, `REGIONAL_IDENTITY_DUPLICATE`, `REGIONAL_ROOT_IDENTITY_MISMATCH`, `REGIONAL_ROOT_GEOMETRY_MISMATCH`, `FIXTURE_ROOT_BINDING_FAILURE`, `INPUT_AUTHORITY_MISMATCH`, `FIELD_FIREWALL_VIOLATION`, and `RESOURCE_LIMIT_EXCEEDED`.

Success proves only a deterministic global-brick to available-provider-view relation for the frozen files. It does not prove source pairing, object identity, galaxy eligibility, outside-footprint status, canonical region, or Panel V3 feasibility.

## Resource cap

The eventual human or autonomously permitted run is offline and bounded to one pass over the four bound local files, at most 1 GiB local I/O, 2 GiB RAM, one thread, 300 CPU seconds, 900 wall seconds, and 4 MiB outputs. It is epistemically material and therefore requires a mission permit even though network and body-byte reservations are zero.
