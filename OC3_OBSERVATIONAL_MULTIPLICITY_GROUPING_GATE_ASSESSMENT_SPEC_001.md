# OC3 Observational Multiplicity Grouping Gate Assessment Specification 001

## Status and question

Prospective offline action under the active observational-multiplicity mandate. It asks whether the evidence frozen after `GLOBAL_VIEW_RELATION_VALIDATED` is sufficient to close the source/object grouping gate required for confirmatory splitting and same-object observer-replication claims.

Stage: `OC3-OBSERVATIONAL-MULTIPLICITY-GROUPING-GATE-ASSESSMENT-001`  
Scope: `OFFLINE_GROUPING_GATE_ASSESSMENT_ONLY`

## Closed evidence

The action may read only the frozen mission specification, Candidate 004, and Candidate 004's sealed terminal and aggregate evidence. It may invoke the already-reviewed pure selection, view-retention, observer-role, and split-assignment guards with synthetic identities. It may not reopen root/north/south values or inspect any source, PHOTSYS, Tractor, pixel, morphology, or label value.

The evidence universe is closed. A grouping contract is available only if an input bound by this action supplies a prospectively validated `OBJECT_GROUP_ID` or `SPLIT_GROUP_ID` with ambiguity, transitivity, provenance, and failure semantics. Absence from this closed evidence is recorded as insufficient evidence, never as proof that no grouping authority could exist in a broader mandate.

## Deterministic assessment

1. Verify exact hashes and canonical seals of the prior terminal, aggregate evidence, and Candidate 004.
2. Require the prior terminal state `GLOBAL_VIEW_RELATION_VALIDATED`, matching aggregate SHA, zero identity/geometry conflicts, and zero scientific-firewall counters.
3. Prove synthetically that global selection uses only `BRICKNAME` and `BRICKID`, gives one selection opportunity per global identity, and excludes observer domain.
4. Prove synthetically that all independently valid views are retained after selection and that observer domain is accepted only for provenance, confound audit, or replication audit.
5. Prove that unresolved grouping blocks confirmatory splitting and that a known shared group cannot cross splits.
6. Inspect only the closed evidence bindings for a validated grouping contract. Do not invent nearest-neighbor, angular-radius, image, morphology, PHOTSYS, or Tractor criteria.

## Outcomes

- `GROUPING_CONTRACT_AVAILABLE`: every required grouping semantic is bound and validated.
- `GROUPING_EVIDENCE_REQUIRED`: global selection/view-retention controls are enforceable, but the closed evidence has no validated grouping contract.
- `GROUPING_GATE_ASSESSMENT_FAILED`: an integrity, relation, selection, view-retention, observer-role, split, or firewall invariant fails.

The expected result is not prespecified. `GROUPING_EVIDENCE_REQUIRED` supports the frozen mission terminal `OBSERVATIONAL_MULTIPLICITY_REQUIRES_GROUPING_EVIDENCE`; it does not authorize acquiring a new metadata family.

## Limits

Network requests/body bytes, retries, PHOTSYS, Tractor/source rows, summary-value reads, pixels, morphology, labels, models, embeddings, and clustering are all zero. Concurrency is one. Output is limited to sealed `ASSESSMENT.json` and `TERMINAL.json` under the action runtime directory.
