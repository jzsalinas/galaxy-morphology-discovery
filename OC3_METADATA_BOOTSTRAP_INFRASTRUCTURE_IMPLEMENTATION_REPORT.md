# OC-3 METADATA_BOOTSTRAP_ONLY infrastructure implementation report

## Scope and terminal state

This change implements and verifies only the future `METADATA_BOOTSTRAP_ONLY` infrastructure governed by `OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC.md` and Clarification 001. The work was entirely synthetic/offline. No provider request, provider byte, real row value, real attempt directory, rights binding, execution plan, authorization candidate, final authorization, resume authorization, production manifest, or brick-selection artifact was created.

The current state remains:

- `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`
- `metadata_bootstrap=NOT_STARTED`
- `production_decode_enabled=false`
- `redistribution=false`
- OC-3 scientific execution not started

## Frozen authorities

The implementation binds and verifies these exact SHA-256 identities before dry-run planning:

| Authority | SHA-256 |
|---|---|
| Base bootstrap specification | `e42ecef50f2a4dd01dbd2d1c8acbcb24e48f30d4692d3bae19c73011fa265dbd` |
| Clarification 001 | `97c42b873b2700ea2155d9107217e296db441d98a24159efe173732dd4bcca4d` |
| Value-semantics specification | `c72f2ff7d3032b1ed38a22cc7f002781e3e1266c8b9aa45c2af08822164d6348` |
| Value-semantics implementation report | `bb84fd3992d9f2a52572bea1676234d188553078cade1229be9fedeada5d07e3` |
| DR9 provider physical contracts | `bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b` |
| Amendment 004 | `842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48` |
| POST_PROBE_001 clarification | `930909ebdfffff58bc0c88cbbab9c619128cb4ab7adb8df9ec6a88e82324e155` |

The historical pre-implementation aggregate remains recorded as `f3f64a05c581e2c74d2cb80c2a2e499ab7c76cbd8eba7ad7f9e5f40a49e48581`. The new Python implementation aggregate is `084706171e4b74a13a8d2ed57ee5d61b73953d746e6aab23081ef77d78673407`.

## Files implemented

- `oc3/oc3lib/metadata_bootstrap.py`: frozen resources and caps, authorization and rights gates, transport interfaces, validation, ledger, storage, provenance, physical-contract integration, selective decoder, semantics, joins, evidence writers, and terminal state machine.
- `oc3/oc3_metadata_bootstrap.py`: fail-closed CLI with `--help`, `--dry-run`, `--offline`, `--execute-network`, `--authorization`, `--rights-binding`, and `--resume`.
- `oc3/tests/test_metadata_bootstrap.py`: 105 synthetic/offline tests covering the required 95-item matrix plus CLI, environment, tamper, and evidence serialization checks.
- `oc3/environment_setup/METADATA_BOOTSTRAP_INFRASTRUCTURE_SYNTHETIC_TESTS.log`: complete canonical replay log.
- `oc3/environment_setup/METADATA_BOOTSTRAP_INFRASTRUCTURE_SYNTHETIC_TESTS.json`: compact replay result.
- `oc3/environment_setup/METADATA_BOOTSTRAP_INFRASTRUCTURE_REPLAY_RECEIPT.json`: immutable replay binding and state receipt.

## Resources and caps

The allowlist contains exactly ROOT_SUMMARY, NORTH_SUMMARY, SOUTH_SUMMARY, and SOUTH_PATCH_LIST with the frozen literal URLs, lengths, PATCH ETag, and PATCH Last-Modified identity. Their exact aggregate is 89,461,646 bytes. Redirects, mirrors, query strings, fragments, Range requests, transparent compression, URL drift, length drift, PATCH identity drift, 206 responses, and Content-Range are rejected.

`METADATA_BOOTSTRAP_ONLY_RESOURCE_CAPS_V1` fixes: 12 requests; concurrency 1; one additional retry per exact identity; 128 MiB HTTP bodies; 64 MiB per resource; 256 MiB disk; 512 MiB I/O; 1 GiB RAM; 300 compute seconds; 900 wall seconds; one thread; zero GPU; 30-second timeout; 2-second retry backoff; and 60-second maximum Retry-After. Historical Probe and metadata caps were not changed.

## CLI, transport, authorization, and rights

Imports are side-effect free. `OfflineTransport` has no network capability. `SyntheticTransport` injects HEAD/GET responses, failures, truncation, overflow, redirects, and identity drift. `RealHttpTransport` can only be constructed through the combined execution, offline, rights, and validated-authorization gate. The current CLI deliberately stops `--execute-network` at `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS` because the separately reviewed execution plan and rights artifact are forbidden in this task.

First-run and resume authorizations use distinct exact schemas. A first-run authorization rejects `--resume`; a resume authorization binds the first authorization, ledger identity and watermark, counters, remaining caps, completed/pending resources, staging state, implementation/environment, and exact resume argv/hash. A retry inside the same invocation remains ledger-bound and does not impersonate a resume.

The rights interface requires local scientific acquisition and preservation to be explicitly allowed for this protocol, redistribution false, FITS/derived redistribution unresolved and disabled, reviewed evidence references, and exact implementation/environment bindings. No real rights object was created.

## Ledger, staging, RAW, and provenance

The SQLite ledger stores only technical identities, counters, reservations, request/retry relations, staging and RAW state, bindings, events, watermark, and terminal state. It has no provider-row table. Reservations occur before transport. An outstanding request recovered after process death becomes `UNCERTAIN` and charges the full reserved body conservatively.

Each retry receives a new staging identity and file. Partial or failed staging cannot become RAW or feed parsing/integrity checks. Publication uses exclusive creation through a hard link, removes the staging name, and makes the RAW inode read-only. Existing RAW files are never overwritten. No decompressed copy is persisted.

The bootstrap digest factory accepts only an internally issued, atomically published `RawArtifact`; reads that exact path to EOF; verifies its byte count; computes SHA-256 locally; binds the complete frozen provenance tuple; and seals the tuple against mutation. The physical validator rechecks the RAW size and digest before reading headers.

## Physical contracts and selective decoding

ROOT/NORTH/SOUTH use the frozen complete-file SHA identities before physical validation. PATCH follows Model B only: complete local bytes, acquisition-bound local SHA-256, header-only physical validation, and `PATCH_ACQUISITION_BOUND_PENDING_HUMAN_REVIEW`. It retains `PROVIDER_PUBLISHED_SHA256=ABSENT`, `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`, and `full_file_integrity_bound=false`.

PATCH header validation reads complete 2880-byte header blocks only through the target BINTABLE `END` card and stops before payload. The payload firewall exposes tripwires for row, RELEASE, BRICKID, BRICKNAME, membership, and uniqueness access. No PATCH payload decode or join path exists.

The ROOT/NORTH/SOUTH decoder manually computes FITS row stride and every physical column byte span. It maps physical provider names to the frozen logical contract, which correctly handles allowed columns before, between, and after forbidden spans. It decodes only the exact TECHNICAL_ALLOWED set and never constructs a whole provider record. `hdu.data`, `Table.read`, `FITS_rec`, whole-table NumPy records, Pandas, and Astropy Table materialization are absent from the decoder path.

Opaque row bytes and decoded values are counted separately. Synthetic regional fixtures place distinctive scalar and vector canaries in forbidden spans. Final replay counters were:

- `forbidden_cell_decode_count=0`
- `forbidden_value_materialization_count=0`
- `forbidden_value_log_count=0`
- `forbidden_value_serialization_count=0`

## Semantics, joins, persistence, and outcomes

The implementation reuses `OC3_BRICKNAME_SEMANTICS_V1`, `GRZ_MEDIAN_PRESENT_V1`, frozen finite-value rules, strict FITS logical values, and exact int32 BRICKID semantics. It does not clean, coerce, normalize, or adapt thresholds.

Bootstrap-local validation enforces unique root BRICKNAME/BRICKID identities and exactly one equal-BRICKID root match for each north or south row. There is no north-to-south requirement and no PATCH join. Only aggregate regional counters are serializable. No CSV, Parquet, row-bearing SQLite table, BRICKNAME list, candidate list, index artifact, or selector API is produced.

The exact 14-outcome precedence is implemented. Under `MODEL_B_TWO_STAGE`, `METADATA_BOOTSTRAP_RESOLVED` is unreachable; the only successful complete future attempt-001 outcome is `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED`, while higher-priority failures remain dominant.

## Synthetic replay and environment

The canonical runner installed socket and DNS blockers before test discovery/import. Result: 518 total, 518 passed, 0 failed, 0 skipped, `real_network_requests=0`, in 30.934 seconds. The previous 413-test regression is retained and all 105 new tests pass.

Environment fingerprint: `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`; Python 3.12.14; NumPy 2.5.3; Astropy 8.0.1; PyArrow 25.0.1. No dependency was installed or changed.

Probe 001 remains exactly 13/13 immutable. It was not rerun or resumed. The canonical real metadata-bootstrap attempt directory is absent. Network requests, new DR9 bytes, and real provider row observations are all zero.

## Remaining blockers

The next stage requires separate prospective review of rights evidence and a frozen human execution plan. Only after those artifacts exist can an exact first-run authorization candidate be prepared. This implementation does not grant authority to execute a real bootstrap, decode production provider rows, perform selection, or start OC-3.

DO NOT RE-RUN OR RESUME PROBE 001.

OC-3 REMAINS NOT STARTED.
