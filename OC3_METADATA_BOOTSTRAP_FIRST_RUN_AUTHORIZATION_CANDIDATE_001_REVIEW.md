# OC-3 metadata-bootstrap first-run authorization candidate 001 review

## A. Candidate identity

| Field | Value |
|---|---|
| Candidate path | `/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE_001.json` |
| Candidate SHA-256 | `4c377cde700c390bc2272c93d2bc6246f642719ddaa455890c14c0ecdea34c7e` |
| Candidate state | `PENDING_HUMAN_REVIEW` |
| Offline validation | `AUTHORIZATION_CANDIDATE_VALID_FOR_HUMAN_REVIEW` |

## B. Execution identity

| Field | Value |
|---|---|
| Implementation aggregate | `4676a6e85e98c4a4fe6464a2ec7c63c4f7c0ca959f7bc05b547b0de3467347c1` |
| Execution Plan 001 SHA-256 | `0e246d5fce5d71c2aa109cba913f1eb9bd397259e492e279870c6d4ccf163b20` |
| Rights Binding 002 SHA-256 | `372279185e4cfb73882f2acebcb9faf051e74294728f950b082563693b898d54` |
| Environment fingerprint | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |

The immutable candidate specification remains applicable through its implemented 24-key schema. Its execution identities are refreshed by this candidate to the current implementation aggregate, Rights Binding 002 path/SHA, and final command vector/SHA. The implemented validator retains the already frozen plan post-activation review and rights-review identities. The new narrow Plan review records `operational_drift_count=0`.

## C. What would be fetched

| Role | Exact URL | Bytes |
|---|---|---:|
| `ROOT_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` | 13,147,987 |
| `NORTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` | 20,882,100 |
| `SOUTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` | 55,399,879 |
| `SOUTH_PATCH_LIST` | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` | 31,680 |
| **Total** |  | **89,461,646** |

## D. Limits

| Limit | Value |
|---|---:|
| Requests | 12 |
| Concurrency | 1 |
| HTTP body bytes | 134,217,728 (128 MiB) |
| Per-resource body bytes | 67,108,864 (64 MiB) |
| Disk bytes | 268,435,456 (256 MiB) |
| I/O bytes | 536,870,912 (512 MiB) |
| RAM bytes | 1,073,741,824 (1 GiB) |
| Compute | 300 s |
| Wall | 900 s |
| Threads | 1 |
| GPU | 0 |

## E. Scientific and observational boundaries

- Patch model: `MODEL_B_TWO_STAGE`.
- PATCH rows are not observed.
- Forbidden fields are not decoded.
- No provider row is persisted.
- `redistribution=false`; FITS or derived redistribution remains `DISABLED_UNRESOLVED`.
- `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED` is the only successful terminal outcome reachable under the frozen PATCH boundary.

## F. Negative capabilities

```json
{"automatic_resume":false,"background_execution":false,"forbidden_field_observation":false,"mirror_or_fallback":false,"oc3_start":false,"patch_row_decode":false,"range_requests":false,"redirects":false,"redistribution":false,"release_substitution":false,"row_persistence":false,"selection":false}
```

## G. Future command

Exact command vector:

```json
["/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_metadata_bootstrap.py","--execute-network","--authorization","/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_001.json","--rights-binding","/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_RIGHTS_BINDING_002.json"]
```

Command SHA-256:

`7bd267dedd973157ee3727ae305453c058369573d3127c1df1a973647b06565f`

## H. Human decision boundary

The candidate is valid for human review. Final authorization is absent. Network execution remains prohibited. Candidate validity does not imply authorization, and the candidate cannot be used as the final `--authorization` artifact.

```text
metadata_bootstrap=NOT_STARTED
real_network_requests=0
real_attempt_created=false
```
