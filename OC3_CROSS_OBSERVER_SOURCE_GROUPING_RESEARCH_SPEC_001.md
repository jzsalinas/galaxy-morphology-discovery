# OC3 Cross-Observer Source Grouping Research Specification 001

## 0. Frozen prospective status

**Mission:** `OC3-CROSS-OBSERVER-GROUPING-AUTONOMY-001`
**Scope:** `CROSS_OBSERVER_GROUPING_RESEARCH_ONLY`
**Status:** FROZEN PROSPECTIVE SPECIFICATION / INACTIVE
**Authorization created by this document:** none

## 1. Scientific question

What morphology-independent evidence is sufficient to relate north and south DR9 source observations while preserving ambiguity, preventing leakage, and avoiding false claims of astrophysical object identity?

The closed observational-multiplicity mission is immutable at commit `538a39486c3031fc463a0ddcbd7fdff247c804cf`, outcome `OBSERVATIONAL_MULTIPLICITY_REQUIRES_GROUPING_EVIDENCE`. Its final report (`35094dc8819ca47fa75fc5b5dc696531e276375e2f3794f2b9dfae4f02361c49`) and claim matrix (`90e649f43b48d5016b9537da154d66b6cbe2a96d4a5d6d00eceeb3e0c19b9b0e`) are closed inputs and their counts are not reinterpreted.

## 2. Terminology and two-track architecture

`CATALOG_SOURCE_OBSERVATION` is exactly `(RELEASE, BRICKID, OBJID)` in one processing domain. It is not an astrophysical-object identity. `CROSS_OBSERVER_ASSOCIATION` preserves `NO_MATCH`, `UNIQUE_MATCH`, `MULTIPLE_MATCH`, `AMBIGUOUS_MATCH`, and `INVALID_MATCH`, with explicit one-to-many, many-to-one, or many-to-many states when required. `ASTROPHYSICAL_OBJECT_GROUP` requires a validated association, ambiguity, transitivity, provenance, and failure contract.

Track A, `SPLIT_SAFETY_GROUPING`, tests conservative leakage control without claiming object identity. Its `SPLIT_GROUP_ID` may be coarse and contain multiple objects. Track B, `OBSERVER_REPLICATION_PAIRING`, tests the stronger same-object association needed for replication. Its `OBJECT_GROUP_ID` must be evidence-based. Track B failure does not force Track A failure, and Track A success never claims replication.

## 3. Evidence hierarchy and authority classes

Material claims may use only: frozen project specifications and terminals; exact official Legacy Survey DR9 documentation; exact official NOIRLab Data Lab documentation or `TAP_SCHEMA` metadata; primary cross-identification literature; bound local global-view evidence; prospectively contracted source metadata; and prospectively contracted validation anchors. Discovery is not material evidence until an exact resource is prospectively bound.

Provider documentation outranks project inference for data semantics. Primary literature defines formalism assumptions but does not establish DR9-specific suitability. File or service evidence must confirm operational claims. Unresolved conflicts remain `UNRESOLVED`.

## 4. First documentary stage

`OC3-CROSS-OBSERVER-GROUPING-DOCUMENTARY-FEASIBILITY-001` asks whether official documentation and established cross-identification literature can support a bounded source-metadata pilot without choosing a matching radius or score threshold. It may retrieve only the literal resource manifest and may inspect only public documentation, primary literature, and Data Lab schema metadata. It reads zero source rows.

The claim matrix separates `OFFICIAL_PROVIDER_FACT`, `DATA_ACCESS_FACT`, `PRIMARY_LITERATURE_FORMALISM`, `PROJECT_INFERENCE`, and `UNRESOLVED`. It must address source identity; `BRICK_PRIMARY`; north/south processing domains; resolved-catalog limitations; allowed astrometric fields; the omission of calibration error from RA/DEC inverse variance; Gaia DR2 astrometric provenance; Data Lab regional tables; Budavári–Szalay assumptions; validation-anchor limitations; and whether a pilot is specifiable without an arbitrary threshold.

## 5. Initial metadata firewall

Before a separate source-pilot authorization, source technical values remain unread. A future primary projection is limited to `RELEASE`, `BRICKID`, `OBJID`, `BRICKNAME`, `BRICK_PRIMARY`, `RA`, `DEC`, `RA_IVAR`, and `DEC_IVAR`, after exact schema validation. `REF_CAT` and `REF_ID` are validation-only candidates under a separate contract.

Cell values for TYPE, DCHISQ, SERSIC, shapes, fluxes, colors, magnitudes, photo-z, reference identifiers, morphology, Galaxy Zoo, and Zoobot are denied. Images, pixels, labels, training, models, embeddings, clustering, Panel V3, P1, and PHOTSYS reinterpretation are prohibited.

## 6. Positional and association discipline

No angular radius or score threshold is frozen in bootstrap. RA_IVAR and DEC_IVAR are statistical centroid information and are not treated as complete cross-observer covariance. Calibration uncertainty, systematic offsets, extended-source centroid instability, deblending, segmentation, epoch assumptions, missing values, multiplicity, deterministic ordering, and failure behavior require explicit prospective contracts.

Close position or a shared brick never silently means the same object. The combined resolved `tractor` catalog is not ground truth for independent north/south pairing. Nearest candidates are never selected automatically. A valid result may retain secure, ambiguous, unmatched, multiple, and invalid observations.

## 7. Split-safety candidates

Future Track A work may compare global-brick groups, connected brick/supertile groups, spatial cells with guards, and established spatial leakage-control methods. No strategy or size is selected here. Boundary crossing, positional differences, guard loss, spatial bias, deterministic construction, and morphology independence must be evaluated prospectively.

## 8. Pilot and holdout prerequisites

A source pilot requires a passed documentary gate, exact provider schema, endpoint and authentication contract, literal query text and hash, exact allowlisted projection, deterministic identity-only ordering, frozen request/byte/time caps, and deterministic overlap-brick selection from previously proven `GLOBAL_VIEW_BOTH` identities. Development fixtures remain excluded. Development and holdout sets and all threshold criteria must be frozen before pairing outcomes are observed.

No `SELECT *`, combined resolved population, morphology column, source count, seeing, depth, regional population, or future outcome may select pilot bricks. If safe selective access cannot be demonstrated, there is no automatic fallback to bulk Tractor FITS.

## 9. Validation anchors

Gaia DR2, Tycho-2, SGA, spectroscopic identities, and DR9 external SDSS matches are only prospective validation anchors. Each requires a coverage, selection-function, independence, matching-mechanism, and allowed-use assessment. Absence is not negative evidence. The provider's 1.5-arcsec SDSS rule is not this project's north/south matching radius.

## 10. Terminal outcomes

Exactly one of these closes the mission:

- `CROSS_OBSERVER_GROUPING_SUPPORTED_FOR_SPLITS_AND_REPLICATION`
- `CROSS_OBSERVER_SPLIT_SAFETY_SUPPORTED_PAIRING_UNRESOLVED`
- `CROSS_OBSERVER_GROUPING_EVIDENCE_INCONCLUSIVE`
- `CROSS_OBSERVER_GROUPING_STRATEGY_REJECTED`

No outcome is preferred. Negative evidence is retained without threshold tuning. Split-safety support may later unblock a separately authorized representation-learning design while replication remains blocked; this mission itself authorizes neither.

## 11. Failure rules

Fail closed on authority drift, uncontracted source values, incomplete uncertainty represented as complete, forced nearest or one-to-one association, unknown grouping used for replication, unresolved grouping used for confirmatory splits, holdout-informed criteria, arbitrary thresholds, resource-limit violation, or a need to expand authority classes. Expansion, new credentials, material source observation, Policy Core mutation after activation, Panel V3, P1, or morphology learning requires `STOP_REQUIRES_HUMAN`.
