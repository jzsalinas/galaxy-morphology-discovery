# OC3 Galaxy Eligibility Observational Multiplicity Amendment 001

## 0. Status and authority

**Amendment ID:** `OC3-GALAXY-ELIGIBILITY-OBSERVATIONAL-MULTIPLICITY-AMENDMENT-001`

**Status:** FROZEN PROSPECTIVE AMENDMENT / NO SCIENTIFIC EXECUTION

**Prospectively amends:** only the future canonical-region requirement in `OC3_GALAXY_ELIGIBILITY_REGION_RESOLUTION_AMENDMENT_001.md`.

The historical V1 failure, the region-resolution amendment, every PHOTSYS artifact, and the terminal result `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE` remain immutable evidence. This amendment neither repairs nor reinterprets PHOTSYS and does not create a V2 resolver.

## 1. Closed PHOTSYS input

The new strategy binds the prior result only as a closed limitation:

- terminal commit: `9a492bd43f804d3b17af7a21875a9e82314375e4`;
- final report SHA-256: `e80d7caeb57f3c05dd66986e801c46a78d6a8abb454aea678332a6e29639dc24`;
- claim matrix SHA-256: `72d9b26c5be5e03acb9bc41f88421ce087705fabfb1ee0421eb533f971c635c5`;
- outcome: `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE`.

No future conclusion in this mission may assign a meaning to byte `0x00`, infer an outside-footprint state, or choose a canonical region from PHOTSYS.

## 2. Prospective correction

North/south overlap is evidence that one global geometric brick has multiple provider views. It is not evidence of duplicate astrophysical objects. North/south is neither morphology nor automatically a scientific class.

For future work governed by this amendment, PHOTSYS is not required to choose one canonical regional view. A technically valid north view and a technically valid south view may both be preserved as distinct `IMAGE_OBSERVATION` records.

The amendment supersedes only these future rules from the historical region-resolution amendment:

- canonical regional view selection by PHOTSYS;
- fixed selection of eight canonical north plus eight canonical south bricks;
- exclusion of a noncanonical regional row solely because a canonical row was chosen.

All historical claims and executions remain unchanged.

## 3. Ontology

The following levels are distinct:

1. `GLOBAL_BRICK_IDENTITY = (BRICKNAME, BRICKID)`. One identity may be present only in north, only in south, or in both summaries.
2. `CATALOG_SOURCE_OBSERVATION = (RELEASE, BRICKID, OBJID)`. This is a provider observation record, not proof of an independent astrophysical object.
3. `ASTROPHYSICAL_OBJECT / OBJECT_GROUP_ID`. This remains unresolved and requires a prospective, morphology-independent association contract.

`IMAGE_OBSERVATION` remains the base observational unit, anchored in future work to one canonical `BRICK_PRIMARY` DR9 source observation. Multiple image observations do not imply multiple galaxies, and one image observation does not prove an ontologically unique galaxy.

## 4. Observer domain

Each regional view carries exactly one `observer_domain` value: `north` or `south`. It is restricted to provenance, confound audit, and replication audit.

It is forbidden as a morphology label, eligibility class, cluster target, training label, scientific taxonomy, automatic balancing target, or canonical-object selector. Region may not enter the discovery-feasibility selection hash.

Correlations with region or related instrumental variables indicate observer-domain dependence. They do not establish causality.

## 5. PHOTSYS-independent technical universe

The already-bound root and regional summaries may establish only these presence categories:

- `GLOBAL_VIEW_NORTH_ONLY`;
- `GLOBAL_VIEW_SOUTH_ONLY`;
- `GLOBAL_VIEW_BOTH`.

The relation must use exact root identity and exact root/regional geometry. Presence or absence must never be translated into outside-footprint, canonical north, or canonical south semantics.

Duplicates within one regional summary, root identity conflicts, missing root joins, and geometry disagreements remain failures.

## 6. Global selection and retained views

A future discovery-feasibility panel selects `GLOBAL_BRICK_IDENTITY` at most once. Its selection hash contains no observer-domain value and provides no multiplicity advantage to an identity with two regional views.

After a global identity is selected, every independently technically valid available regional view is retained. “Every” remains bounded by exact resource identity, schema validity, `BRICK_PRIMARY`, required g/r/z support, valid WCS/center, firewall compliance, and the future galaxy-eligibility contract. Invalid or unsupported records are not admitted to increase multiplicity.

Development-fixture exclusion applies to the global identity and therefore excludes all its regional views.

## 7. Two panel roles

`DISCOVERY_FEASIBILITY_PANEL` samples global identities without observer-domain balancing. Its north/south composition is measured after selection.

`OBSERVER_REPLICATION_AUDIT` is a separate future audit that may intentionally seek validated same-object observations across observer domains. Its pairs do not define the discovery selection universe and are not positive training pairs by default.

No Panel V3 is created by this amendment. A new panel specification may be frozen only after the global-view relation gate passes.

## 8. Grouping and split gate

The unresolved gate is:

```text
CROSS_OBSERVER_SOURCE_GROUPING_REQUIRES_PROSPECTIVE_CONTRACT
```

Same brick, proximity alone, image similarity, similar morphology, and Tractor `TYPE` cannot establish `OBJECT_GROUP_ID`. No nearest-neighbor convention or angular radius is chosen here.

Once an `OBJECT_GROUP_ID` or `SPLIT_GROUP_ID` is validated, every associated `IMAGE_OBSERVATION` must remain in the same split. While grouping is unresolved, confirmatory split construction is blocked. Separately specified, non-training exploratory observer audits may proceed.

## 9. Multiplicity and inferential weight

Every future analysis must distinguish `observation_count` from `object/group_count`. No loss, sampling, or aggregate weighting formula is selected here. Once grouping exists, total inferential weight must be auditable at `OBJECT_GROUP_ID` level.

## 10. Separation from galaxy eligibility

This amendment resolves no galaxy/star question, spectroscopic or Gaia evidence, source validity, blend grouping, cutout support, or object grouping. The bounded A/B/C galaxy-eligibility comparison remains intact. Regional multiplicity cannot establish galaxy status.

## 11. Negative outcomes

The strategy remains compatible with findings that observer multiplicity makes stable representation infeasible, observer domain dominates discovered structure, or cross-observer grouping cannot be established robustly.

## 12. Zero-execution declaration

Creating this amendment performs no network access, FITS row read, PHOTSYS read, Tractor access, panel materialization, P1 operation, pixel read, training, representation learning, embedding, clustering, morphology access, or label access.
