# OC3 Source-Metadata Acquisition Pilot Final Report 001

Scientific outcome: **`SOURCE_METADATA_ACQUISITION_INCONCLUSIVE`**

Error code: **`DATALAB_TRANSPORT_FAILURE`**

## Governed execution

- Mission: `OC3-SOURCE-METADATA-ACQUISITION-PILOT-AUTONOMY-001`
- Stage: `OC3-SOURCE-METADATA-ACQUISITION-PILOT-001`
- Scope: `PROSPECTIVE_DR9_SOURCE_METADATA_ACQUISITION_ONLY`
- Requests actually started: 1
- Application-body bytes actually read: 0
- Retry requests: 0
- Worker return code: 0
- Worker terminating signal: `None`
- Worker launches: 1

The single schema request returned HTTP 200 with observed content type `text/html`. The response was rejected before body decoding, recorded `body_bytes_read=0`, empty-body SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, and completion state `FAILED_CLOSED`. No redirect occurred.

## Gate results

- Schema result: `NOT_OBSERVED_TRANSPORT_FAILED_CLOSED`
- Schema rows observed: 0
- North per-brick counts: `NOT_REQUESTED`
- South per-brick counts: `NOT_REQUESTED`
- North total: `NOT_OBSERVED`
- South total: `NOT_OBSERVED`
- Count cap: `NOT_EVALUATED`
- North source rows acquired: 0
- South source rows acquired: 0
- RA_IVAR state counts: `NOT_OBSERVED`
- DEC_IVAR state counts: `NOT_OBSERVED`
- Row-integrity result: `NOT_EVALUATED`
- Count/row consistency result: `NOT_EVALUATED`

The result is inconclusive because the schema transport failed closed before any application-body byte or schema row was observed. The frozen protocol prohibits retry and worker replay.

## Firewalls

- Holdout count requests: 0
- Holdout row requests: 0
- Holdout source-derived cells observed: 0
- Combined Tractor, crossmatch, q3c and cone-search operations: 0
- Matching, angular-separation and radius operations: 0
- Search-bound and scientific-threshold selections: 0
- Object/split group IDs created: 0
- PHOTSYS, TYPE, DCHISQ, Sersic/shape, photometry, photo-z and pixels read: 0
- Morphology, labels, models, training, embeddings, clustering, Panel V3 and P1: 0

No positional topology analysis was performed.

## Immutable bindings

- Query-manifest SHA-256: `d25c12b9b9a8715aa8e2ae5a9d885ef88b3ece1dc62d327072c3cc305e15abf8`
- Permit SHA-256: `4285995e1b1f83c45c0b4166048f13232844900b24e97ea3e39c4d2d0b66cd3b`
- Permit-consumption marker SHA-256: `da422862b4bf241e2d5ebb10d6548f9906202e441ae301a3663d9e33ba384572`
- Worker capability SHA-256: `b29baeb0d21dffa3a94e600e3bf285bc8090ba9869c4767658d45712fee1af6e`
- Capability-consumption marker SHA-256: `9464f8fa8051474321f6e4bd554e8843e0d69f2d4fd303e38d3f6b4abc96ee31`
- Terminal SHA-256: `464a165b3281f5ec5c84617880e98d653bc1171c5eaa4d9b314d5464387b7d0e`
- Transport-evidence SHA-256: `18d37ad0f017e94c0e4030c836212fb5a361e8588059846899f49bfe769218e8`
- Execution-diagnostic SHA-256: `5b3a1a6e16036c02a6d9f8df8ce6117de40034674a0063dd08707f76715e5bcd`
- Final claim-matrix SHA-256: `10240b96327fe2af4b467abfeaf5971d8f5a15391becdbb5b17127f02f493695`
- Predicted finalized-state SHA-256: `c066adaeeba21c16a0bc15070c8983c8a7e9d3c9a965c3fa74a9d0a2fbaea8e8`

The governor's finalization ledger record binds the byte-exact SHA-256 of this report after the report exists. The post-finalization closure artifact records that report SHA, the realized final-state SHA and the final ledger aggregate. The local Git commit is created after finalization and is reported externally because a commit cannot contain its own identity.
