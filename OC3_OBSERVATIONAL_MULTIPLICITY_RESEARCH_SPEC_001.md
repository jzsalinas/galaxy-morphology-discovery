# OC3 Observational Multiplicity Research Specification 001

## 0. Frozen prospective status

**Mission:** `OC3-OBSERVATIONAL-MULTIPLICITY-AUTONOMY-001`
**Scope:** `OBSERVATIONAL_MULTIPLICITY_STRATEGY_ONLY`
**Status:** FROZEN PROSPECTIVE SPECIFICATION / INACTIVE
**Network or scientific execution authorized by this document:** none

## 1. Objective

Determine whether a PHOTSYS-independent, global-identity/all-valid-views observational design can replace canonical-region selection while preserving scientific independence, preventing split leakage, and creating a valid observer-replication audit path.

The target remains galaxy morphology. The mission evaluates observational design and grouping feasibility; it does not learn morphology.

## 2. Immutable inputs

The PHOTSYS mission is closed at commit `9a492bd43f804d3b17af7a21875a9e82314375e4` with outcome `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE`. Its report and claim matrix hashes are fixed in the observational-multiplicity amendment. They may be cited but not reopened.

The first evidence source consists only of the already-local, already-bound root, north, and south DR9 brick summaries plus the development-fixture list. No first-stage network, PHOTSYS, Tractor, source-row, pixel, morphology, or label access is allowed.

## 3. Scientific propositions

The mission tests these propositions separately:

1. `GLOBAL_VIEW_RELATION`: exact identity and geometry establish north-only, south-only, or both-view presence without PHOTSYS.
2. `SELECTION_INDEPENDENCE`: selecting each global identity once avoids multiplicity-weighted brick selection and does not use observer domain.
3. `VALID_VIEW_RETENTION`: every selected view must independently pass later technical and galaxy-eligibility contracts.
4. `GROUPING_AND_LEAKAGE`: source-level replication and confirmatory splitting require a prospective morphology-independent grouping contract.
5. `OBSERVER_AUDIT_PATH`: paired views are initially audit evidence, not imposed training invariance.

## 4. First bounded stage

**Stage:** `OC3-GLOBAL-VIEW-RELATION-AUDIT-001`
**Scope:** `OFFLINE_GLOBAL_VIEW_RELATION_ONLY`

It may decode only `BRICKNAME`, `BRICKID`, `RA`, `DEC`, `RA1`, `RA2`, `DEC1`, and `DEC2` from the three frozen summaries. It may read the frozen development-fixture CSV only to derive global fixture exclusions through the root identity.

It reports only aggregate totals: global identities, north present, south present, north-only, south-only, both, identity conflicts, geometry conflicts, fixture exclusions, network requests, PHOTSYS reads, Tractor cells, and morphology accesses. Row identities are not narrative outputs.

Success requires exact input hashes and physical contracts; unique root identity; uniqueness within each regional summary; exact root join and exact geometry; deterministic row-order-independent aggregates; global fixture exclusion; and zero forbidden counters.

Any identity or geometry conflict fails the stage closed. Absence/presence is never mapped to footprint or canonical-region semantics.

## 5. Source grouping gate

`CROSS_OBSERVER_SOURCE_GROUPING_REQUIRES_PROSPECTIVE_CONTRACT` remains open after a successful brick relation audit. A later contract must define morphology-independent evidence, ambiguity handling, transitivity, provenance, and failure states before source pairs can be treated as one object.

No nearest-neighbor default, angular radius, image similarity, Tractor `TYPE`, or morphology evidence is permitted by this specification.

## 6. Split and weighting requirements

All observations in one validated `OBJECT_GROUP_ID` or `SPLIT_GROUP_ID` remain in one split. Unresolved grouping blocks confirmatory split construction.

Every report distinguishes observation count from object/group count. No weighting formula is frozen in this mission bootstrap.

## 7. Terminal decisions

Exactly one terminal decision may close the mission:

- `OBSERVATIONAL_MULTIPLICITY_STRATEGY_SUPPORTED`: the global-view relation is proven; global selection independence and valid-view retention are prospectively enforceable; a morphology-independent grouping contract has been validated sufficiently to prevent leakage; and no unresolved conflict blocks the observer-replication path.
- `OBSERVATIONAL_MULTIPLICITY_REQUIRES_GROUPING_EVIDENCE`: the global-view relation and selection strategy are supported, but source/object grouping evidence remains insufficient for confirmatory splits or same-object replication claims.
- `OBSERVATIONAL_MULTIPLICITY_STRATEGY_INCONCLUSIVE`: required technical or documentary evidence cannot establish or refute one or more mission propositions without expanding the reviewed evidence envelope.
- `OBSERVATIONAL_MULTIPLICITY_STRATEGY_REJECTED`: evidence demonstrates that the strategy violates scientific independence, cannot prevent multiplicity/leakage under an admissible contract, or cannot retain technically valid observations reproducibly.

The first brick-relation stage cannot by itself produce `SUPPORTED`; grouping remains a distinct gate.

## 8. Prohibited work

The mission prohibits PHOTSYS reinterpretation or a V2 resolver; Panel V3 materialization before the strategy gate; P1; uncontracted astronomical value families; Galaxy Zoo/Zoobot or other morphology labels; image pixels; training; encoders; embeddings; clustering; anomaly detection; and selection based on representation outcomes.

## 9. Future observer-replication audit

After representation learning under a separate future authorization, validated same-object north/south pairs may audit cross-domain distance, observer-domain predictability, structure stability under view replacement, and observer-driven anomalies. This specification sets no threshold and creates no positive-pair training rule.

## 10. Negative-result integrity

Observer-domain dominance, infeasible stable morphology under multiplicity, or inability to establish source grouping are legitimate outcomes. The mission must not tune gates to force the all-views strategy to pass.
