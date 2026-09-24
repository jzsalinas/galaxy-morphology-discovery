# OC3 Galaxy Eligibility Panel Strategy Reassessment 001

## Status

**Decision type:** prospective methodological reassessment.
**Execution authorized:** none.
**Panel materialized:** none.

The reassessment uses no learned representation, morphology outcome, source row, pixel, or PHOTSYS reinterpretation.

## Compared strategies

| Strategy | Current status | Methodological effect |
|---|---|---|
| `PHOTSYS_CANONICAL_REGION` | Blocked by the closed semantic terminal. | Would choose one regional view, but the required interpretation of observed `0x00` was not established. |
| `EXCLUDE_ALL_OVERLAPS` | Technically simple but scientifically lossy. | Removes replicated observer information and changes the effective footprint; overlap alone is not a defect. |
| `GLOBAL_IDENTITY_WITH_ALL_VALID_VIEWS` | Prospectively selected strategy, conditional on its gates. | Selects each global brick once, preserves every independently valid regional view, and turns overlap into an observer audit opportunity. It requires source/object grouping before independent confirmatory splits. |

## Prospective decision

`GLOBAL_IDENTITY_WITH_ALL_VALID_VIEWS` is the preferred strategy because the choice follows from observation-first methodology and sampling independence, without consulting an embedding or downstream result.

The decision is conditional. It becomes operational only if an offline audit demonstrates a deterministic root-bound global-identity to available-view relation with zero identity or geometry conflicts. Later source-level use remains gated by a prospective cross-observer grouping contract and by independently frozen technical and galaxy-eligibility rules.

## Discovery panel

The main `DISCOVERY_FEASIBILITY_PANEL` uses `GLOBAL_BRICK_IDENTITY` as its selection unit. Region is excluded from hash bytes, ordering, quotas, and replacement. A global identity enters at most once. Region composition is reported after selection.

No fixed 8 north + 8 south quota survives into this strategy. A future bounded panel size must be justified prospectively from the feasibility question and resource limits.

## Replication audit

`OBSERVER_REPLICATION_AUDIT` is separate. After morphology-independent object grouping, it may compare representations of the same object observed through north and south. Such observations are audit cases, not default positive pairs or a training objective. Pass thresholds remain unfrozen.

## Blocking conditions

- The global-view relation is not demonstrated.
- A regional summary has internal duplicates.
- A regional identity or geometry conflicts with the root authority.
- A proposed selection hash contains observer domain or an observer-balancing term.
- Confirmatory splitting is attempted before object/split grouping is resolved.
- “All views” bypasses any independent technical or galaxy-eligibility rule.

No Panel V3 identity, membership, or materialized artifact is created here.
