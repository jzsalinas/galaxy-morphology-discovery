# OC3 Cross-ID Formalism Recovery Offline Semantic Review Specification 001

## Frozen action

**Stage:** `OC3-CROSS-ID-FORMALISM-OFFLINE-SEMANTIC-REVIEW-001`  
**Scope:** `OFFLINE_PRIMARY_LITERATURE_SEMANTIC_REVIEW_ONLY`  
**Network reservation:** zero  
**Source rows and astronomical values:** zero

The action reads only the two immutable snapshots acquired by the completed
primary-evidence action, its transport evidence and terminal, the closed
predecessor artifacts, and the frozen scientific specification. The input
files and SHA-256 identities are fixed in Candidate 001 for this action.

## Evidence rules

The review records each A-K subclaim as `SUPPORTED`, `INCONCLUSIVE`, or
`CONFLICT`, with one epistemic layer: `FORMALISM_FACT`, `DR9_DATA_FACT`, or
`PROJECT_SUITABILITY_INFERENCE`. No model memory or uncaptured web content is
evidence.

Claim 9, `CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS`, is `SUPPORTED` only if
the captured primary evidence establishes A-I and K, identifies its
point-source scope, and the review retains the absence of a demonstrated
direct transfer to extended DR9 galaxies. Claim J may remain `INCONCLUSIVE`
without making Claim 9 inconclusive when that limitation is itself explicitly
preserved rather than silently bridged. A material contradiction produces
`CONFLICT`; missing mandatory primary support produces `INCONCLUSIVE`.

Claim 10, `BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD`, is evaluated only
after Claim 9. It is `SUPPORTED` only if:

1. Claim 9 is supported;
2. candidate-generation search support is kept distinct from a scientific
   same-object decision threshold;
3. the proposed future pilot is descriptive and does not declare pair
   equivalence;
4. extended-source suitability remains an explicit project inference;
5. no source access or pilot execution occurs in this mission.

Otherwise Claim 10 is `INCONCLUSIVE`, unless admitted evidence materially
conflicts, in which case it is `CONFLICT`.

## Frozen terminal mapping

- Claim 9 `SUPPORTED` and Claim 10 `SUPPORTED`:
  `CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE`.
- Claim 9 `SUPPORTED` and Claim 10 `INCONCLUSIVE`:
  `CROSS_ID_FORMALISM_RECOVERED_PILOT_STILL_UNRESOLVED`.
- either claim `CONFLICT`: `CROSS_ID_FORMALISM_CONFLICT`.
- every other allowed combination:
  `CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE`.

No threshold, radius, source-row query, matching, Panel V3, P1, morphology,
training, embedding, clustering, or model operation is authorized.

