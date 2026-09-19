# OC-3 metadata-bootstrap prospective execution plan 001

## Status and authority of this document

This document is the exact prospective plan for the first real OC-3 metadata-bootstrap attempt. It is a local planning artifact only. It is not an execution authorization, rights binding, authorization candidate, final authorization, resume authorization, or scientific-stage transition.

Conceptual authorization state: `authorized=false`.

Creation of this plan does not permit network access, attempt creation, provider-row observation, selection, Probe 001 execution, or OC-3 execution.

## Verified authority state

Verification was performed locally from the canonical repository working directory. All required identities matched exactly.

| Authority or invariant | Verified value |
|---|---|
| `OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC.md` | SHA-256 `e42ecef50f2a4dd01dbd2d1c8acbcb24e48f30d4692d3bae19c73011fa265dbd` |
| `OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC_CLARIFICATION_001.md` | SHA-256 `97c42b873b2700ea2155d9107217e296db441d98a24159efe173732dd4bcca4d` |
| `OC3_METADATA_BOOTSTRAP_INFRASTRUCTURE_IMPLEMENTATION_REPORT.md` | SHA-256 `4809e002fe9e78242001b6910ec93350a3761f32281a27902c5cbbb71b4afa50` |
| `oc3/environment_setup/METADATA_BOOTSTRAP_INFRASTRUCTURE_REPLAY_RECEIPT.json` | SHA-256 `6f3d13350829b121d6a6579df89dc377505b6cf180d1325a9199687b45278ad0` |
| `OC3_METADATA_VALUE_SEMANTICS_AND_INTEGRITY_SPEC.md` | SHA-256 `c72f2ff7d3032b1ed38a22cc7f002781e3e1266c8b9aa45c2af08822164d6348` |
| `OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md` | SHA-256 `bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b` |
| Current implementation aggregate | `084706171e4b74a13a8d2ed57ee5d61b73953d746e6aab23081ef77d78673407` |
| Environment fingerprint | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| Canonical regression | 518 total, 518 passed, 0 failed, 0 skipped, `real_network_requests=0` |
| Probe 001 | 13/13 files present with frozen sizes and SHA-256 identities |
| Real metadata-bootstrap attempt directory | Absent |
| Metadata-bootstrap rights binding | Absent |
| Metadata-bootstrap authorization | Absent |

The exact canonical working directory observed locally is:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery
```

Any mismatch in these bindings during a later preflight must terminate as `METADATA_BOOTSTRAP_EXECUTION_PLAN_AUTHORITY_FAILURE` before attempt state or transport construction.

## Plan identity

```text
plan_id = OC3-METADATA-BOOTSTRAP-EXECUTION-PLAN-001
attempt_id = OC3-METADATA-BOOTSTRAP-001
scope = METADATA_BOOTSTRAP_ONLY
execution_mode = FIRST_RUN_NETWORK
patch_model = MODEL_B_TWO_STAGE
authorized = false
```

This plan is not authorization.

## Exact resource plan

No mirror, redirect, query string, fragment, dynamic discovery, release substitution, or alternate resource is permitted.

| Role | Literal URL | Expected length | Expected provider SHA-256 or integrity state |
|---|---|---:|---|
| `ROOT_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` | 13,147,987 | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| `NORTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` | 20,882,100 | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| `SOUTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` | 55,399,879 | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |
| `SOUTH_PATCH_LIST` | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` | 31,680 | `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`; use an attempt-bound local acquisition digest under Model B |
| **Total** | — | **89,461,646** | — |

The PATCH pretransfer representation must additionally match exactly:

```text
ETag = "5ffdf047-7bc0"
Last-Modified = Tue, 12 Jan 2021 18:53:59 GMT
final URL = https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits
redirected = false
```

## Nominal request schedule

The nominal successful first invocation has exactly this order:

1. `HEAD ROOT_SUMMARY`
2. `HEAD NORTH_SUMMARY`
3. `HEAD SOUTH_SUMMARY`
4. `HEAD SOUTH_PATCH_LIST`

Joint pretransfer validation of all four representations occurs locally after request 4 and before request 5.

5. `GET ROOT_SUMMARY`
6. `GET NORTH_SUMMARY`
7. `GET SOUTH_SUMMARY`
8. `GET SOUTH_PATCH_LIST`

Nominal HTTP requests are 8. The maximum is 12. Conditional retries are excluded from the nominal count, are limited to one additional attempt per exact identity, consume the same cumulative caps, and cannot change method, URL, headers, or representation identity.

All HTTP operations are sequential with concurrency 1. Every request uses `Accept-Encoding: identity`. Only HEAD and complete GET are allowed. Range, redirect following, transparent HTTP decompression, fallback resources, and parallel transfers are prohibited.

No GET may occur unless all four HEAD responses and their joint representation validation pass. A failure during a later resource sequence stops all subsequent network operations.

## Transfer and storage caps

| Cap | Frozen value |
|---|---:|
| Nominal complete GET body bytes | 89,461,646 |
| Cumulative HTTP body bytes | 134,217,728 |
| Single-resource body bytes | 67,108,864 |
| Attempt disk bytes | 268,435,456 |
| Local I/O bytes | 536,870,912 |
| RAM bytes | 1,073,741,824 |
| Active compute | 300 seconds |
| Wall time | 900 seconds |
| Threads | 1 |
| GPU | 0 |
| Timeout | 30 seconds |
| Retry backoff | 2 seconds |
| Maximum accepted `Retry-After` | 60 seconds |

Deterministic capacity margins are:

| Calculation | Exact margin |
|---|---:|
| HTTP body cap − nominal complete bodies | 134,217,728 − 89,461,646 = **44,756,082 bytes** (42.682726 MiB) |
| Single-resource cap − largest resource (`SOUTH_SUMMARY`) | 67,108,864 − 55,399,879 = **11,708,985 bytes** (11.166558 MiB) |
| Disk cap − expected four-file RAW set | 268,435,456 − 89,461,646 = **178,973,810 bytes** (170.682726 MiB) |

These margins are capacity, not permission to widen another cap. Error bodies, partial bodies, abandoned bodies, staging state, retries, hashing, parsing, and other local I/O consume the applicable remaining budgets. No retry or later resume resets a counter. This plan does not predict an exact runtime.

## Prospective attempt paths

The future attempt root is exactly:

```text
oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/
```

Relative to the canonical repository, the prospective paths are:

```text
oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/STAGING/
oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz
oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz
oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz
oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/SOUTH_PATCH_LIST/dr9-south-patched-bricks.fits
```

The exact final evidence artifacts under that future attempt root are:

```text
BOOTSTRAP_AUTHORIZATION_BINDING.json
BOOTSTRAP_TRANSPORT_EVIDENCE.json
BOOTSTRAP_RAW_FILE_MANIFEST.json
BOOTSTRAP_INTEGRITY_EVIDENCE.json
BOOTSTRAP_PHYSICAL_CONTRACT_EVIDENCE.json
BOOTSTRAP_SEMANTIC_SUMMARY.json
PATCH_ACQUISITION_BOUND_EVIDENCE.json
BOOTSTRAP_EVENTS.json
BOOTSTRAP_TERMINAL.json
BOOTSTRAP_LEDGER.sqlite
BOOTSTRAP_RUN.log
```

`STAGING/` is execution state and is not a final evidence artifact. None of these paths is created by this plan.

## Exact causal plan

The only permitted causal sequence is:

```text
local authority verification
→ rights binding verification
→ human authorization verification
→ attempt/ledger conflict check
→ four HEAD requests
→ joint representation validation
→ ROOT GET
→ ROOT raw publication
→ ROOT local digest
→ ROOT provider digest comparison
→ ROOT physical contract
→ NORTH GET
→ NORTH raw publication
→ NORTH local digest
→ NORTH provider digest comparison
→ NORTH physical contract
→ SOUTH GET
→ SOUTH raw publication
→ SOUTH local digest
→ SOUTH provider digest comparison
→ SOUTH physical contract
→ PATCH GET
→ PATCH raw publication
→ PATCH acquisition-bound local digest
→ PATCH header-only physical validation
→ root/north/south selective decode
→ frozen semantic validation
→ root↔north and root↔south joins
→ aggregate evidence
→ METADATA_BOOTSTRAP_PARTIALLY_RESOLVED
```

No PATCH row or cell decoder, record parser, membership validator, uniqueness validator, RELEASE observation, BRICKID observation, BRICKNAME observation, or PATCH join may occur anywhere in this sequence.

## Row-observation boundary

The first attempt may transiently observe only these values through the reviewed selective decoder:

- ROOT, exactly 11 `TECHNICAL_ALLOWED` fields: `BRICKNAME`, `BRICKID`, `BRICKQ`, `BRICKROW`, `BRICKCOL`, `RA`, `DEC`, `RA1`, `RA2`, `DEC1`, `DEC2`.
- NORTH, exactly 16 `TECHNICAL_ALLOWED` fields: `brickname`, `ra`, `dec`, `nexp_g`, `nexp_r`, `nexp_z`, `nexphist_g`, `nexphist_r`, `nexphist_z`, `brickid`, `ra1`, `ra2`, `dec1`, `dec2`, `area`, `survey_primary`.
- SOUTH, the same exact 16 `TECHNICAL_ALLOWED` fields.
- PATCH, zero cell fields.
- `KNOWN_BUT_FORBIDDEN`, zero decoded values.
- Persisted row values, zero.

Opaque transit of decompressed FITS row bytes is not cell-value observation. The required terminal values for the four tripwires are:

```text
forbidden_cell_decode_count = 0
forbidden_value_materialization_count = 0
forbidden_value_log_count = 0
forbidden_value_serialization_count = 0
```

Any nonzero value is a terminal boundary failure. Aggregate counters and closed reason codes may persist; row-bearing values may not.

## Expected successful state

The only successful terminal for Attempt 001 is:

```text
METADATA_BOOTSTRAP_PARTIALLY_RESOLVED
```

The corresponding PATCH state is:

```text
PATCH_ACQUISITION_BOUND_PENDING_HUMAN_REVIEW
provider_published_checksum_known = false
acquisition_bound_local_sha256_known = true
full_file_integrity_bound = false
patch_row_semantics = NOT_OBSERVED
patch_membership = NOT_OBSERVED
```

`METADATA_BOOTSTRAP_RESOLVED` remains unreachable under `MODEL_B_TWO_STAGE` in Attempt 001.

## Terminal outcomes and precedence

Exactly one terminal outcome is emitted. The following order is strict from highest to lowest precedence. After any terminal is emitted, additional automatic network is prohibited and existing ledger-bound evidence is preserved. “Resume possible” below means only a theoretically applicable, separately reviewed and human-authorized `--resume`; it never means automatic permission.

| Priority | Exact outcome | Trigger class | Additional network after terminal | Existing evidence | Later separately authorized resume theoretically applicable? |
|---:|---|---|---|---|---|
| 1 | `METADATA_ROW_OBSERVATION_INTEGRITY_FAILURE` | Any PATCH payload/cell access or other unauthorized cell observation | Prohibited | Preserve | No under the current implementation/specification; requires prospective correction and replay |
| 2 | `METADATA_FORBIDDEN_FIELD_BOUNDARY_FAILURE` | Materialization, logging, serialization, or leakage of a forbidden value | Prohibited | Preserve | No under the current implementation/specification; requires prospective correction and replay |
| 3 | `METADATA_BOOTSTRAP_AUTHORITY_FAILURE` | Spec, authority, implementation, environment, or frozen binding mismatch | Prohibited | Preserve | No; authority must be resolved prospectively before a new first-run decision |
| 4 | `METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE` | Invalid scope, command, human authorization, or binding | Prohibited | Preserve | No; a corrected first-run authorization is a new reviewed intent, not implied resume authority |
| 5 | `METADATA_LOCAL_STATE_CONFLICT` | Conflicting attempt, RAW, ledger, staging, or output state | Prohibited | Preserve without overwrite or repair | No unless a later prospective specification explicitly resolves the conflict |
| 6 | `METADATA_RESOURCE_LIMIT_STOP` | Reservation or any request/body/disk/I/O/RAM/compute/wall/thread/GPU cap fails | Prohibited | Preserve and retain consumed counters | No if the pending operation cannot fit the unchanged remaining caps; caps never reset or expand |
| 7 | `PATCH_LIST_REPRESENTATION_DRIFT_STOP` | PATCH identity differs before or during transfer | Prohibited | Preserve | No; a new representation requires prospective scientific/governance review |
| 8 | `METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP` | ROOT/NORTH/SOUTH size or representation identity differs | Prohibited | Preserve | No; a new representation requires prospective review |
| 9 | `METADATA_TRANSPORT_INTEGRITY_FAILURE` | Invalid method, status, headers, complete-body length, content encoding, redirect, or transport continuity | Prohibited | Preserve partial/failed evidence and charge bytes conservatively | Conditional only if the exact pending operation, retry entitlement, and all remaining caps permit it; requires a separate resume candidate and human authorization |
| 10 | `METADATA_FULL_FILE_INTEGRITY_FAILURE` | ROOT/NORTH/SOUTH complete local digest differs from the frozen provider digest | Prohibited | Preserve | No for the same frozen representation |
| 11 | `METADATA_PHYSICAL_CONTRACT_FAILURE` | Exact frozen FITS physical contract differs | Prohibited | Preserve | No under the current contract; requires prospective revision |
| 12 | `METADATA_VALUE_SEMANTICS_FAILURE` | Allowed-value semantics, uniqueness, or exact root↔regional join fails | Prohibited | Preserve aggregate failure evidence | No; the negative scientific result is final for this attempt and does not permit cleaning or threshold changes |
| 13 | `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED` | Every authorized step passed and PATCH remains pending human review | Prohibited | Preserve final evidence | No resume; the next action is local audit and later separately specified PATCH review |
| 14 | `METADATA_BOOTSTRAP_RESOLVED` | Reserved future state | Prohibited | Preserve | Not applicable; unreachable in Attempt 001 |

A higher-precedence outcome cannot be replaced by a later one. No terminal authorizes selection or changes any frozen specification.

## First-run command shape

Local `--help` inspection confirmed the implemented flags `--execute-network`, `--authorization`, `--rights-binding`, and `--resume`. The future first-run shell invocation shape is:

```bash
cd /home/jzsalinas/Documents/galaxy-morphology-discovery
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python \
  /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_metadata_bootstrap.py \
  --execute-network \
  --authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_001.json \
  --rights-binding /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_RIGHTS_BINDING_001.json
```

The two prospective filenames are plan-local proposals only:

```text
oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_001.json = PROPOSED_PENDING_SEPARATE_FREEZE
oc3/METADATA_BOOTSTRAP_RIGHTS_BINDING_001.json = PROPOSED_PENDING_SEPARATE_FREEZE
```

The command must not include `--resume`, `--offline`, `--dry-run`, limit overrides, alternate URLs, Range settings, or background-execution wrappers.

For clarity, the shell invocation uses the frozen Python interpreter. The command vector internally bound by the current CLI’s established `command_sha256` rule begins with the absolute script path and then the exact option/value strings; the interpreter and `cd` shell built-in are not included by the current implementation’s command-vector construction.

This command is not executable yet. Both proposed input artifacts are absent, neither filename/identity is separately frozen, and the current CLI implementation deliberately returns `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS` for `--execute-network` before reading either input or constructing transport. Any later implementation change changes the implementation aggregate and requires this plan and all dependent bindings to be reviewed again.

## Command-hash status

```text
COMMAND_HASH_PENDING_RIGHTS_AND_AUTHORIZATION_FREEZE
```

No command hash is calculated in this plan. The unresolved literal paths for the authorization and rights binding are only `PROPOSED_PENDING_SEPARATE_FREEZE`, and the current network CLI gate is intentionally inactive. Calculating a binding hash now would silently promote proposed artifact names into frozen runtime identities and would not describe an executable command under the current aggregate.

The eventual command hash must use the implementation’s canonical rule: SHA-256 over compact, sorted-key JSON encoding of the complete exact command-vector string list. It may be calculated only after all literal argv elements and their governing artifact identities are prospectively frozen.

## Rights dependency

Before this plan can become authorizable, a separately reviewed rights binding must prove and bind at least:

```text
local_scientific_acquisition = ALLOWED_FOR_THIS_PROTOCOL
local_preservation = ALLOWED_FOR_THIS_PROTOCOL
redistribution = false
FITS_OR_DERIVED_REDISTRIBUTION = DISABLED_UNRESOLVED
```

It must additionally bind:

- reviewed documentary evidence references and exact snapshot/file hashes;
- bootstrap specification SHA-256 `e42ecef50f2a4dd01dbd2d1c8acbcb24e48f30d4692d3bae19c73011fa265dbd`;
- Clarification 001 SHA-256 `97c42b873b2700ea2155d9107217e296db441d98a24159efe173732dd4bcca4d`;
- the implementation aggregate applicable when execution is proposed;
- environment fingerprint `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`;
- all four literal resource URLs and their representation constraints;
- attempt ID `OC3-METADATA-BOOTSTRAP-001`;
- this plan’s externally computed SHA-256;
- scope limited to local acquisition, local preservation, local technical validation, and the zero-redistribution rule.

This plan does not create or approve that binding.

## First-run authorization dependency

A later first-run authorization candidate must bind, without omission:

- `attempt_id=OC3-METADATA-BOOTSTRAP-001`;
- `scope=METADATA_BOOTSTRAP_ONLY`;
- `execution_mode=FIRST_RUN_NETWORK`;
- `patch_model=MODEL_B_TWO_STAGE`;
- this plan’s externally computed SHA-256;
- the exact future rights-binding SHA-256;
- base specification and Clarification 001 SHA-256 identities;
- the applicable implementation aggregate and environment fingerprint;
- all four exact resources, expected lengths, representation constraints, and provider-integrity states;
- `METADATA_BOOTSTRAP_ONLY_RESOURCE_CAPS_V1` in full;
- the exact command vector and canonical command SHA-256;
- `authorized=false` while it remains a candidate;
- the negative capabilities: no Range, mirrors, redirects, release substitution, PATCH row decode, forbidden-field observation, row persistence, selection, automatic resume, background execution, redistribution, or OC-3 start;
- absence of `--resume` in the exact first-run command.

The candidate is not authorization. Human approval must later produce a distinct exact final authorization. This plan creates neither artifact.

## Manual execution boundary

Codex must not execute the future network run. After all dependencies are separately frozen and the human issues final authorization, the responsible human manually invokes the exact CLI from the canonical working directory.

There is no `nohup`, background execution, polling workaround, or automatic resume. The success sentinel is the exact `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED` outcome recorded in the future `BOOTSTRAP_TERMINAL.json` and compact process result, with exit status zero and no orphan/incomplete staging. Any other terminal or nonzero exit is failure or stop evidence, not permission to continue.

If interruption or partial failure makes resume potentially applicable, execution stops. A later task must inspect local state and prepare a distinct resume candidate under Clarification 001, binding the existing attempt directory, first-run authorization SHA, ledger identity and watermark, consumed counters, remaining caps, completed RAW resources, pending resources, staging state, implementation/environment, and exact `--resume` command/hash. This plan does not authorize resume.

## Post-execution audit boundary

Immediately after a future manual invocation, no follow-on network request or automatic stage transition is allowed. The next task is a local, read-only audit of:

- the single ledger, its bindings, watermark, requests, retries, and cumulative counters;
- all four RAW paths, sizes, locally computed hashes, provider comparisons, and transport receipts;
- transport and joint pretransfer evidence;
- ROOT/NORTH/SOUTH full-file integrity evidence;
- all four physical-contract results;
- selective-decoder aggregate instrumentation and the four zero-valued forbidden-field tripwires;
- frozen semantic aggregate counters and root↔north/root↔south join aggregates;
- PATCH acquisition-bound evidence and unchanged Model-B limitations;
- the exact terminal outcome and complete final-artifact inventory.

Selection, candidate creation, brick ranking, PATCH payload decode, and scientific execution are not automatic audit follow-ups.

## Current state after plan creation

Creating this plan changes no execution state:

```text
PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS
metadata_bootstrap = NOT_STARTED
production_decode_enabled = false
redistribution = false
real_network_requests = 0
real_provider_row_values = 0
real_attempt_created = false
rights_binding_created = false
authorization_created = false
```

Probe 001 remains immutable 13/13 and is not rerun or resumed. The implementation aggregate remains `084706171e4b74a13a8d2ed57ee5d61b73953d746e6aab23081ef77d78673407` because this Markdown plan is outside the implementation aggregate’s Python-file set.

THIS PLAN IS NOT AUTHORIZATION.

DO NOT RE-RUN OR RESUME PROBE 001.

OC-3 REMAINS NOT STARTED.
