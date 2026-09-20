# OC-3 metadata-bootstrap first-run authorization candidate specification

## Status and scope

This is a prospective documentary specification for a separate, non-executable first-run authorization candidate. It defines no runtime capability and creates no candidate JSON, final authorization, attempt, ledger, RAW, STAGING, provider-row observation, network request, or OC-3 transition.

The candidate is immutable evidence of the exact technical execution proposal presented for later human review. It is neither an authorization nor an input accepted by the production `--authorization` path.

```text
AUTHORIZATION_CANDIDATE != FINAL_HUMAN_AUTHORIZATION
```

## Verified current state

The specification was prepared locally from a clean canonical repository with no configured remote.

| Item | Verified value |
|---|---|
| Branch | `main` |
| Commit before this specification | `9b14289744e87571cd4887bc6a9ffc4da2a54b6a` |
| Baseline commit and tag | `8e87225dfb895438e5bb73bbadc6ef35dbf6ed1e`, `oc3-pre-metadata-bootstrap-001` |
| Gate-activation commit | `60f937b145f8eb29be4df9352032a092b42a7ddd` |
| Plan post-activation review commit | `bee1460daab76a854a00b0056faf224373950b8e` |
| Rights-binding commit | `9b14289744e87571cd4887bc6a9ffc4da2a54b6a` |
| Execution Plan 001 | SHA-256 `0e246d5fce5d71c2aa109cba913f1eb9bd397259e492e279870c6d4ccf163b20` |
| Plan post-activation review | SHA-256 `a232a58f91705215d5322945460549b7b53789bf630503d505552f8f5fb460a0` |
| Rights review 001 | SHA-256 `81dc0a0ec485b7f8d9007781e9845735ec057483b45421442d112c3ad5e38d2e` |
| Rights binding 001 | SHA-256 `51ab89dfef0cfb34f7ef8614c2dd6e3984d20cf3d2590d6e40d356091d5f10b4` |
| Current implementation aggregate | `d9922ad04a19a9e87b73e85439239a591aae80b1d9528d9e75310b0e88efbec7` |
| Environment fingerprint | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| Canonical replay | 562/562 passed, 0 failed, 0 skipped, `real_network_requests=0` |
| Probe 001 | exact and immutable 13/13 |

The production rights binding exists and validates locally with `synthetic_only=false`. The candidate path, final authorization path, and real attempt path are absent.

## Observed candidate-model gap

The current first-run authorization implementation is final-only. Its closed 24-key schema requires:

```text
authorization_state = FINAL_HUMAN_AUTHORIZATION
authorized_by = nonempty human identity string
authorized_at_utc = valid UTC timestamp
```

Production execution additionally requires `authorized=true`. Passing `require_authorized=false` relaxes only that final boolean check; it does not define a candidate state and does not remove the final-human state, identity, or timestamp requirements. The current regression explicitly rejects `authorized=false` with a candidate state as `METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE` before the transport factory is reached.

The discovered blocker is:

```text
AUTHORIZATION_CANDIDATE_HUMAN_FIELD_GAP
```

A candidate must not reuse `FINAL_HUMAN_AUTHORIZATION`, invent human values, or rely on `authorized=false` alone. This specification resolves the design question by defining a separate candidate artifact and validator while leaving the existing final authorization schema unchanged.

## Candidate purpose and artifact identity

The future candidate artifact path is prospectively frozen as:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE_001.json
```

Its exact type and state are:

```text
candidate_type = METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE
candidate_state = PENDING_HUMAN_REVIEW
```

The candidate exists only to freeze and display the exact plan, rights binding, implementation, environment, resources, caps, Model-B state, negative capabilities, future final-authorization path, command vector, and command SHA-256 for human comparison.

The candidate must never be passed to `--authorization`. It has no network, attempt, transport, selection, decode, or execution authority.

## Future final authorization path

The only prospective first-run artifact eligible for the production `--authorization` argument after explicit human approval is frozen as:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_001.json
```

The candidate path and final path are deliberately distinct. No final file is created by this specification.

## Frozen future command vector and hash

The current pure runtime command-vector validator was called locally with `resume=false`. It accepted exactly this future final execution vector:

```json
["/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_metadata_bootstrap.py","--execute-network","--authorization","/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_001.json","--rights-binding","/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_RIGHTS_BINDING_001.json"]
```

The vector excludes the Python interpreter and shell `cd`. It contains no `--resume`, `--offline`, `--dry-run`, override, alternate path, limit mutation, resource mutation, or background flag.

The existing production `command_sha256` rule computes SHA-256 over the canonical UTF-8 JSON serialization of the complete string array, using compact separators, `ensure_ascii=false`, `allow_nan=false`, and no trailing LF. Applying that exact production function gives:

```text
command_sha256 = 4985668400a14bab02675f203712f0909a9e09f084f9222e994e6d10f5a3eab8
command_status = COMMAND_HASH_FROZEN_FOR_PROSPECTIVE_CANDIDATE
```

The hash describes the future final execution command. It is not permission to invoke it.

## Closed candidate schema

The future candidate JSON SHALL be a closed object with exactly these 24 keys:

```text
schema_version
canonicalization
candidate_type
candidate_state
attempt_id
scope
execution_mode
patch_model
execution_plan_sha256
plan_post_activation_review_sha256
rights_binding_path
rights_binding_sha256
rights_review_sha256
base_spec_sha256
clarification_sha256
implementation_aggregate
environment_fingerprint
resources
resource_caps
command_vector
command_sha256
negative_capabilities
final_authorization_path
candidate_created_at_utc
```

The candidate SHALL NOT contain an `authorized` key. Absence is chosen instead of `authorized=false` because candidate authority is determined by its separate type, state, schema, path, and validator. This prevents the candidate from resembling a nearly-final authorization, prevents mechanical boolean promotion, and avoids repeating the rejected assumption that `authorized=false` alone defines a valid candidate model.

The candidate SHALL NOT contain `authorized_by`, `authorized_at_utc`, `authorization_state`, human signature, approval token, approval statement, or human decision. `candidate_created_at_utc` is machine-generated provenance for the immutable candidate bytes; it is not approval and is semantically distinct from final `authorized_at_utc`.

### Exact field values and types

| Field | Required candidate value or type |
|---|---|
| `schema_version` | integer `1` |
| `canonicalization` | `CANONICAL_JSON_SORTED_KEYS_COMPACT_UTF8_LF_V1` |
| `candidate_type` | `METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE` |
| `candidate_state` | `PENDING_HUMAN_REVIEW` |
| `attempt_id` | `OC3-METADATA-BOOTSTRAP-001` |
| `scope` | `METADATA_BOOTSTRAP_ONLY` |
| `execution_mode` | `FIRST_RUN_NETWORK` |
| `patch_model` | `MODEL_B_TWO_STAGE` |
| `execution_plan_sha256` | `0e246d5fce5d71c2aa109cba913f1eb9bd397259e492e279870c6d4ccf163b20` |
| `plan_post_activation_review_sha256` | `a232a58f91705215d5322945460549b7b53789bf630503d505552f8f5fb460a0` |
| `rights_binding_path` | exact absolute frozen rights path |
| `rights_binding_sha256` | `51ab89dfef0cfb34f7ef8614c2dd6e3984d20cf3d2590d6e40d356091d5f10b4` |
| `rights_review_sha256` | `81dc0a0ec485b7f8d9007781e9845735ec057483b45421442d112c3ad5e38d2e` |
| `base_spec_sha256` | `e42ecef50f2a4dd01dbd2d1c8acbcb24e48f30d4692d3bae19c73011fa265dbd` |
| `clarification_sha256` | `97c42b873b2700ea2155d9107217e296db441d98a24159efe173732dd4bcca4d` |
| `implementation_aggregate` | `d9922ad04a19a9e87b73e85439239a591aae80b1d9528d9e75310b0e88efbec7` |
| `environment_fingerprint` | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| `resources` | exact ordered production resource-binding array |
| `resource_caps` | exact production `METADATA_BOOTSTRAP_ONLY_RESOURCE_CAPS_V1` object |
| `command_vector` | exact six-element string array frozen above |
| `command_sha256` | `4985668400a14bab02675f203712f0909a9e09f084f9222e994e6d10f5a3eab8` |
| `negative_capabilities` | exact production negative-capability object |
| `final_authorization_path` | exact absolute frozen final path |
| `candidate_created_at_utc` | nonempty RFC 3339/ISO 8601 string with explicit UTC `Z`; artifact provenance only |

The candidate file SHALL use UTF-8 canonical JSON with sorted keys, compact separators, finite JSON values, duplicate-key rejection, and exactly one trailing LF. Its SHA-256 SHALL be calculated over its exact file bytes after serialization. Unknown, duplicate, absent, or extra keys invalidate the candidate.

## Exact resources

The candidate SHALL copy the exact ordered result of the existing production `resource_binding_values()` function. No weaker or alternate representation is permitted.

| Role | URL | Bytes | Compression | Provider checksum state |
|---|---|---:|---|---|
| `ROOT_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` | 13,147,987 | `gzip` | `EXPECTED_PROVIDER_CHECKSUM_KNOWN` |
| `NORTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` | 20,882,100 | `gzip` | `EXPECTED_PROVIDER_CHECKSUM_KNOWN` |
| `SOUTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` | 55,399,879 | `gzip` | `EXPECTED_PROVIDER_CHECKSUM_KNOWN` |
| `SOUTH_PATCH_LIST` | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` | 31,680 | `identity` | `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND` |

The aggregate is exactly 89,461,646 bytes. Each item also retains the exact provider digest or null, PATCH ETag and Last-Modified or null, `allowed_methods=["HEAD","GET"]`, `accept_encoding="identity"`, `range_allowed=false`, and `redirects_allowed=false` from production. No other role, URL, mirror, fallback, redirect, Range, or release substitution is allowed.

## Exact resource caps

The candidate SHALL copy the exact production `resource_cap_values()` object:

| Key | Value |
|---|---:|
| `version` | `METADATA_BOOTSTRAP_ONLY_RESOURCE_CAPS_V1` |
| `requests` | 12 |
| `concurrency` | 1 |
| `retry_additional_per_exact_identity` | 1 |
| `http_body_bytes` | 134,217,728 |
| `single_resource_body_bytes` | 67,108,864 |
| `disk_bytes` | 268,435,456 |
| `io_bytes` | 536,870,912 |
| `ram_bytes` | 1,073,741,824 |
| `compute_seconds` | 300 |
| `wall_seconds` | 900 |
| `threads` | 1 |
| `gpu` | 0 |
| `timeout_seconds` | 30 |
| `retry_backoff_seconds` | 2 |
| `retry_after_max_seconds` | 60 |

No candidate field may widen, reinterpret, reset, or omit a cap.

## Exact negative capabilities

The candidate SHALL bind the same exact object required by final authorization:

```json
{"automatic_resume":false,"background_execution":false,"forbidden_field_observation":false,"mirror_or_fallback":false,"oc3_start":false,"patch_row_decode":false,"range_requests":false,"redirects":false,"release_substitution":false,"redistribution":false,"row_persistence":false,"selection":false}
```

This object is a closed set. The candidate cannot use a weaker policy or add a compensating capability.

## Model-B freeze

The candidate SHALL bind `MODEL_B_TWO_STAGE`. For `SOUTH_PATCH_LIST`, the provider SHA remains absent; PATCH row values, `RELEASE`, `BRICKID`, `BRICKNAME`, membership and joins remain `NOT_OBSERVED`; and full-file integrity remains false after the bounded first acquisition pending separate review. `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED` is the only reachable successful terminal in Attempt 001. `METADATA_BOOTSTRAP_RESOLVED` remains unreachable.

## Separate offline candidate validator

A later implementation SHALL provide separate, offline-only operations conceptually named:

```text
load_authorization_candidate()
validate_authorization_candidate()
```

They SHALL:

1. read only the prospective candidate path;
2. enforce size, UTF-8, strict JSON, duplicate-key rejection, canonical bytes and the exact closed key set;
3. verify every exact identity and value in this specification against local authorities and current production constants;
4. recompute the rights-file SHA, implementation aggregate, command vector and command SHA locally;
5. verify the absence of the real attempt and final authorization at candidate creation time;
6. produce only `AUTHORIZATION_CANDIDATE_VALID_FOR_HUMAN_REVIEW` on success; and
7. remain incapable of constructing, receiving, returning, or invoking `RealHttpTransport`.

Candidate validation success must never mean `AUTHORIZED`, `EXECUTION_READY`, or `TRANSPORT_ALLOWED`. The candidate loader/validator must be distinct from the final authorization validator and activation path.

## Runtime firewall

The production `--authorization` loader and validator must continue accepting only the existing final closed schema. The candidate's distinct type, state, absent final-human fields, absent `authorized`, and extra candidate-only bindings make it structurally incompatible with that schema. Supplying the candidate path to `--authorization` must fail with `METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE` before real transport construction.

No candidate code path may issue DNS, open a socket, construct transport, create attempt state, read provider bytes, or delegate to activation.

## Final authorization binding gap

The current final authorization closed schema has no `candidate_sha256`, equivalent candidate-identity field, or reviewed-evidence structure. Its exact key set cannot bind the future candidate identity directly. Therefore the required classification is:

```text
FINAL_AUTHORIZATION_CANDIDATE_BINDING_GAP
```

A subsequent narrowly scoped prospective amendment is required before final authorization creation. That amendment must define an exact candidate-SHA binding in the final authorization model, update runtime validation and focused offline regression prospectively, and preserve the existing execution gates. This specification does not choose or implement that amendment and does not modify the final schema.

Final authorization must not silently omit candidate provenance.

## Promotion prohibition

Final authorization is not created by copying the candidate, flipping a boolean, and adding a name or timestamp. The candidate remains immutable evidence of what was reviewed.

A later final authorization is a distinct artifact constructed only after explicit human approval. It must independently validate against the then-applicable final closed schema and bind the exact candidate SHA under the separately reviewed amendment.

There is no automatic promotion, derivation, rename, overwrite, or in-place mutation.

## Human review contract

Before any final artifact may be created, the human review must compare at least:

- candidate SHA-256 and exact bytes;
- plan and plan-review SHA-256 identities;
- rights binding and rights-review SHA-256 identities;
- implementation aggregate and environment fingerprint;
- all four resources, representation constraints and 89,461,646-byte aggregate;
- every resource cap;
- `MODEL_B_TWO_STAGE` and its PATCH limitations;
- the exact negative-capability object;
- frozen final authorization and rights paths;
- the six-element command vector and `4985668400a14bab02675f203712f0909a9e09f084f9222e994e6d10f5a3eab8` command hash;
- current Git commit/state and authority identities; and
- absence of any existing attempt, ledger, RAW, STAGING, or conflicting final authorization.

Only an explicit human decision after that comparison may authorize creation of a distinct final authorization artifact. Even that creation step is separate from manual network execution.

## State after this specification

This specification changes no execution capability:

```text
rights_component=RESOLVED
authorization_candidate=ABSENT
final_authorization=ABSENT
metadata_bootstrap=NOT_STARTED
production_decode_enabled=false
redistribution=false
real_network_requests=0
real_provider_row_values=0
real_attempt_created=false
```

Probe 001 remains immutable 13/13.

THIS SPECIFICATION DOES NOT CREATE AN AUTHORIZATION CANDIDATE.

THIS SPECIFICATION DOES NOT AUTHORIZE EXECUTION.

DO NOT CREATE FINAL AUTHORIZATION WITHOUT EXPLICIT HUMAN APPROVAL.

DO NOT RE-RUN OR RESUME PROBE 001.

OC-3 REMAINS NOT STARTED.
