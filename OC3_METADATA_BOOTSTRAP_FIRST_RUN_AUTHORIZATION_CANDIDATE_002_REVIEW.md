# OC3 Metadata Bootstrap First-Run Authorization Candidate 002 Review

## A. Candidate

| Field | Value |
|---|---|
| Path | `/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE_002.json` |
| SHA-256 | `d7c584b0838a3a11e0fc2fd74df5cdad050dc9381f6f8428a49c6fe4b17f834f` |
| State | `PENDING_HUMAN_REVIEW` |
| Offline validation | `AUTHORIZATION_CANDIDATE_VALID_FOR_HUMAN_REVIEW` |

## B. Current execution identity

| Field | Value |
|---|---|
| Implementation aggregate | `432bcd449673786075938d3a290ad0ea139cc88bf1c2aae758c59d09179ef276` |
| Rights Binding 003 SHA-256 | `da8c0009f654c4ad98b82160b4bab3cabcfb9d093db4fa78fed49218b109c3e0` |
| Command SHA-256 | `84ded4957ab03790f221f56554e6c9dc15c1f5ea3458ce75fb523704ebd09329` |

## C. What will happen if later authorized

The run creates Attempt 001, issues all four HEAD requests before any GET, then GETs `ROOT → NORTH → SOUTH → PATCH` for 89,461,646 expected bytes. It publishes immutable RAW files; validates transport, full-file integrity and physical contracts; selectively decodes ROOT/NORTH/SOUTH; validates frozen semantics and exact joins; and validates PATCH headers only. The only successful terminal is `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED`.

## D. Main caps

| Cap | Value |
|---|---:|
| Requests / concurrency / additional retry | 12 / 1 / 1 per exact identity |
| HTTP bodies / one resource | 134,217,728 / 67,108,864 bytes |
| Disk / I/O / RAM | 268,435,456 / 536,870,912 / 1,073,741,824 bytes |
| Compute / wall | 300 / 900 s |
| Threads / GPU | 1 / 0 |

## E. Negative capabilities

`automatic_resume=false`, `background_execution=false`, `forbidden_field_observation=false`, `mirror_or_fallback=false`, `oc3_start=false`, `patch_row_decode=false`, `range_requests=false`, `redirects=false`, `redistribution=false`, `release_substitution=false`, `row_persistence=false`, `selection=false`.

## F. Scientific boundary

No PATCH row observation, forbidden-field observation, row persistence, selection or OC-3 scientific start is permitted. `redistribution=false` and FITS or derived redistribution remains `DISABLED_UNRESOLVED`.

## G. Exact future manual command

```bash
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_metadata_bootstrap.py --execute-network --authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_002.json --rights-binding /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_RIGHTS_BINDING_003.json
```

## H. Decision state

```text
PENDING_HUMAN_REVIEW
final_authorization=ABSENT
network_execution=NOT_PERFORMED
```
