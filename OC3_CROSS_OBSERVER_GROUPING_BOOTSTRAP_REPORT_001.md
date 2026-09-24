# OC3 Cross-Observer Grouping Bootstrap Report 001

## Result

The prospective mission bootstrap is complete on branch
`autopilot/cross-observer-grouping`, created directly from the closed
observational-multiplicity terminal commit
`538a39486c3031fc463a0ddcbd7fdff247c804cf`. The previous mission remains
terminal with outcome `OBSERVATIONAL_MULTIPLICITY_REQUIRES_GROUPING_EVIDENCE`.

The new mission is inactive. No standing authorization exists, no real permit
was issued, and the first documentary action was not executed.

## Closed input binding

| Artifact | SHA-256 |
|---|---|
| `OC3_OBSERVATIONAL_MULTIPLICITY_FINAL_REPORT_001.md` | `35094dc8819ca47fa75fc5b5dc696531e276375e2f3794f2b9dfae4f02361c49` |
| `oc3/OC3_OBSERVATIONAL_MULTIPLICITY_CLAIM_MATRIX_001.json` | `90e649f43b48d5016b9537da154d66b6cbe2a96d4a5d6d00eceeb3e0c19b9b0e` |

The frozen counts and conclusions from that mission were bound without
reinterpretation.

## Scientific architecture

Mission ID: `OC3-CROSS-OBSERVER-GROUPING-AUTONOMY-001`.

The research specification separates two scientific tracks:

1. `SPLIT_SAFETY_GROUPING` investigates conservative, morphology-independent
   leakage control. A `SPLIT_GROUP_ID` may be deliberately coarse and does not
   assert astrophysical identity.
2. `OBSERVER_REPLICATION_PAIRING` investigates evidence-based north/south
   association suitable for a future same-object replication audit. An
   `OBJECT_GROUP_ID` is a stronger claim and remains blocked until a validated
   association contract exists.

The implementation keeps catalog-source observations,
cross-observer associations, split-safety groups, and astrophysical-object
groups as distinct types. It preserves unmatched, ambiguous, invalid,
one-to-many, many-to-one, and many-to-many association states and never selects
the nearest candidate implicitly.

No matching radius or score threshold was selected. `RA_IVAR` and `DEC_IVAR`
are explicitly insufficient as a complete cross-observer covariance model by
default.

## Frozen bootstrap artifacts

| Artifact | SHA-256 |
|---|---|
| `OC3_CROSS_OBSERVER_SOURCE_GROUPING_RESEARCH_SPEC_001.md` | `a1073b798efc4805d2e11ebb51c5f25b8935474827c7c341c6bfd25047a7b506` |
| `OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_SPEC_001.md` | `96a5155d2ef12218cbc0a7538da41898f09783bd737739db8a95e1e67a4a9eb6` |
| `OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_MANDATE_001.md` | `465a2d68747633daab0bf8f67bcccc286de1774dc075c98cd20deceff02c2f03` |
| `oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_MANDATE_001.json` | `4cf2840a023d8f346e63026f90a0ca76fe5f0a56914766ce4551680b2fe6b4b5` |
| `oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_POLICY_CORE_MANIFEST_001.json` | `2a380d5895e2763e2cead586a09c3b7d94ea3a812e5009917870c7de7b20ddb1` |
| `oc3/OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_STATE_001.json` | `e18dc2eafb2995815485969b1207cff6d1f4074060bc61f6a36942030d29e113` |
| `oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_RESOURCE_MANIFEST_001.json` | `81256914f5c12f97b9c81fd62c9c36a1d1c96672517804a65acbf75631e1ce51` |
| `oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_CANDIDATE_VALIDATION_001.json` | `313d12d00e9c5c6869194144fc5f9d8a442d51c1fae4e7445333f8080d31ad1d` |
| `oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_CANDIDATE_001.json` | `181e254c98a89bea56c30842d76991ad6b042e58a5ffedc4975eca9506a3168f` |

First-action implementation aggregate:
`1d048998ba925c5ce8d010003ffd64b4b0d67351c7d6134ad894ef11b50d1de0`.

First-action command argv SHA-256:
`538bc2422721a2491f52cb2d205e078a69eea32abce5d50030a04e9e95620e17`.

## Prepared first action

The state-bound first candidate is
`OC3-CROSS-OBSERVER-GROUPING-DOCUMENTARY-FEASIBILITY-001`, scope
`PUBLIC_DOCUMENTARY_AND_SCHEMA_METADATA_ONLY`. Its literal manifest contains
six exact resources: three official Legacy Survey DR9 pages, two exact NOIRLab
Data Lab `TAP_SCHEMA` metadata queries, and the Budavári & Szalay (2008)
preprint. The TAP queries expose schema metadata only and cannot return source
rows.

The candidate reserves at most six requests and 12,582,912 response-body bytes,
with concurrency one, zero retries, zero redirects, and no automatic resume.
It is epistemically material and remains non-executable until a separate
standing human authorization activates the mission and the governor issues the
single-use, SHA-derived permit.

The exact prepared command is:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_cross_observer_grouping_documentary.py --research-documentary-feasibility --candidate /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_CANDIDATE_001.json --permit /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/CROSS_OBSERVER_GROUPING_AUTONOMY_PERMITS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_PERMIT_001.json --standing-authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/OC3_CROSS_OBSERVER_GROUPING_STANDING_AUTHORIZATION_001.json --autonomy-state /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_STATE_001.json --output-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/cross_observer_grouping/OC3-CROSS-OBSERVER-GROUPING-DOCUMENTARY-FEASIBILITY-001
```

The command was not executed.

## Validation

- Focused new grouping and governor tests: `19/19` passed.
- Affected grouping, governor, and historical input-tripwire regression:
  `144/144` passed.
- Full synthetic-only offline regression: `1279/1279` passed, zero failures,
  zero skips, `46.437` seconds.
- Full regression log: `/tmp/oc3_cross_observer_grouping_full_regression.log`;
  SHA-256 `c0eb56bc71c0916c5ef1b95f80bd36607adde009acc67a56cd90313fe2dd755f`.
- Governor validation: `AUTONOMY_HARDENING_VALIDATED`, zero network, no permit.
- Documentary preflight: `READY_AT_DOCUMENTARY_RESEARCH_BOUNDARY`, zero
  network and zero source rows.
- Network requests: `0`.
- Source rows and technical source values read: `0`.
- PHOTSYS, morphology fields, photometry, photo-z, pixels, labels, training,
  embeddings, clustering, Panel V3, and P1 operations: `0`.

## Final bootstrap state

```text
state = WAITING_FOR_STANDING_HUMAN_AUTHORIZATION
active = false
standing_authorization = absent
real_permits_issued = 0
first_documentary_candidate = prepared_not_executed
source_rows = 0
matching = not_started
matching_radius = absent
Panel_V3 = not_started
P1 = blocked / not started
morphology_learning = not started
```

No network request, source-row query, Tractor acquisition, matching,
threshold calibration, spatial split execution, panel operation, or morphology
learning occurred during this bootstrap.
