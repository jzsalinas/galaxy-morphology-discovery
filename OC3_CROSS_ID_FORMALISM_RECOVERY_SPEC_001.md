# OC3 Cross-ID Formalism Recovery Specification 001

## Status and scientific question

**Mission:** `OC3-CROSS-ID-FORMALISM-RECOVERY-AUTONOMY-001`  
**Scope:** `CROSS_ID_FORMALISM_RECOVERY_ONLY`  
**Status:** prospective, frozen, inactive  
**Authorization created:** none

Can accessible primary literature establish the assumptions and limits of the
Budavári–Szalay probabilistic cross-identification formalism well enough to
decide whether a threshold-free, bounded DR9 source-metadata pilot can be
specified?

The closed cross-observer-grouping mission remains immutable at commit
`b6667bed7c8271dd582d0b585372d010af4ccc28`, outcome
`CROSS_OBSERVER_GROUPING_EVIDENCE_INCONCLUSIVE`. Its final report, final claim
matrix, and terminal state are closed inputs. The eight claims previously
classified `SUPPORTED` remain closed. Only
`CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS` and
`BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD` are reopened.

## Evidence boundary

The initial material action may retrieve exactly two primary resources:

1. arXiv abstract HTML `https://arxiv.org/abs/0707.1611` as a hashed response
   snapshot;
2. conference proceeding PDF
   `https://adsabs.harvard.edu/pdf/2008ASPC..394..165B` as a hashed response
   snapshot, after verifying authorship, bibliographic identity, and primary
   source status.

The conference proceeding must never be represented as the ApJ article.
Earlier arXiv/export/ADS failures were transport failures with no acquired
body and imply neither scientific support nor rejection. No broad crawl,
redirect, mirror substitution, retry, or automatic resume is allowed.

## Required formalism claims

The offline review must address, without post-observation criteria changes:

- A: the method is Bayesian/probabilistic;
- B: it compares same-source and separate-source hypotheses;
- C: the formal construction is symmetric where claimed by the source;
- D: the positional uncertainty model and its domain;
- E: the requirement for known positional uncertainties;
- F: circular, Gaussian, tangent-plane, or spherical approximations and limits;
- G: prior-probability requirements;
- H: any point-source assumption;
- I: optional use of physical properties;
- J: limits on transfer to extended DR9 galaxies;
- K: whether the formalism itself requires an arbitrary angular
  match-decision radius.

Claim J remains open unless primary evidence and a separately justified DR9
inference support it. Known positional errors and point-source assumptions may
not be omitted from the matrix.

## Epistemic layers

Every material statement is exactly one of `FORMALISM_FACT`, `DR9_DATA_FACT`,
or `PROJECT_SUITABILITY_INFERENCE`. A formalism fact cannot establish DR9
suitability. This mission acquires no new DR9 data fact.

`CANDIDATE_GENERATION_SEARCH_BOUND` and
`SCIENTIFIC_MATCH_DECISION_THRESHOLD` are distinct concepts. Bootstrap chooses
neither and contains no numeric radius constant. A finite computational search
bound, if ever proposed, is not evidence for a scientific association.

## Claim decisions and sequence

The review first decides
`CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS`, then reevaluates
`BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD`. A descriptive pilot may be
specifiable while any scientific match-decision threshold remains unchosen;
bootstrap does not authorize such a pilot.

## Terminal outcomes

Exactly one outcome may close the mission:

- `CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE`
- `CROSS_ID_FORMALISM_RECOVERED_PILOT_STILL_UNRESOLVED`
- `CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE`
- `CROSS_ID_FORMALISM_CONFLICT`

## Firewalls and stop rules

Source rows, technical source values, PHOTSYS, pixels, morphology, labels,
models, training, embeddings, clustering, Panel V3, and P1 remain at zero.
No matching, source acquisition, pilot materialization, threshold selection,
or radius selection is authorized. New authority classes, extra resources,
credentials, budget expansion, policy-core mutation after activation, or any
astronomical observation requires `STOP_REQUIRES_HUMAN`.

