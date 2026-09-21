# OC3 Representation Branch Readiness Decision 001

## 0. Status, scope, and authority

**Decision ID:** `OC3-REPRESENTATION-BRANCH-READINESS-DECISION-001`

**Status:** FROZEN PROSPECTIVE DECISION

**Evidence stage:** `OC3-PREPROCESSING-INVARIANCE-PERTURBATION-PILOT-001`

**Required evidence state:** `PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_COMPLETED`

**Execution performed by this decision:** NONE

**Network access:** NONE

**Model, encoder, embedding, clustering, morphology, or label access:** NONE

This decision classifies the frozen preprocessing and invariance branches for possible participation in a future representation robustness experiment. It does not authorize that experiment, choose an encoder, define a scientific cohort, or establish morphology preservation or observational equivalence.

Technical admissibility means only that a branch has a sufficiently explicit technical contract for the future role stated here. Scientific equivalence would require separate prospective evidence and is not established by any classification in this document.

The decision uses only these frozen authorities and successful runtime artifacts:

| Evidence ID | Artifact | SHA-256 |
|---|---|---|
| `A1` | `OC3_PREPROCESSING_AND_INVARIANCE_DECISION_001.md` | `de91bb4b25c002b7c4d5ee0744f6fc7e719d43ec6a969885f66d423b2ac80cf9` |
| `A2` | `OC3_PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_SPEC.md` | `4ef5b16a9cc9de25ca194bdbf947bae8491035692fb3499356393093d919f1cd` |
| `E1` | `OC3_PERTURBATION_BRANCH_MANIFEST.json` | `3947b2c2260bf4cfc6ef9770fe6c359b465212234cb9a46d84d31dbee790f089` |
| `E2` | `OC3_PERTURBATION_TECHNICAL_EFFECT_METRICS.csv` | `ed42a4afcf5af2369a22d74b2ee8a3790252f1755c2ff224a921d13b708ad5f4` |
| `E3` | `OC3_PERTURBATION_INFORMATION_LOSS_REGISTER.csv` | `06cf4cc7a2a5872385519a898cc64cd0b98e0e5dfe6ea0a7c82756a5d8dae43d` |
| `E4` | `OC3_NEXP_TECHNICAL_STRATA.csv` | `28919d7ce1d190c584cd3358feff2a5cb33626ff213db6e94f8500049acfe61e` |
| `E5` | `OC3_PERTURBATION_PILOT_SUMMARY.json` | `10f44e724c975957e79e6dc4e322447ceca69efd064df6493667c45a5a855c17` |
| `E6` | `OC3_PERTURBATION_PILOT_TERMINAL.json` | `7183a090f65539e832317652488076bce813e04e9606bd5580987a2017c5ed77` |

`E6` records zero network requests, model operations, encoder operations, embedding operations, clustering operations, morphology operations, label accesses, image displays, plots, input modifications, padding, interpolation, clipping, and provider-PSF transforms. It also records 2 technical development bricks, 6 observational windows, and 0 defined astronomical objects.

## 1. Closed readiness categories

Every branch B00 through B15 has exactly one category:

- `REPRESENTATION_BASELINE`: mandatory unmodified comparator.
- `REPRESENTATION_STRESS_TEST`: controlled sensitivity test with explicit information-change provenance.
- `REPRESENTATION_ABLATION`: deliberate removal of specified input information.
- `REPRESENTATION_STRATIFICATION_ONLY`: descriptive grouping that neither changes IMAGE nor enters an encoder automatically.
- `REPRESENTATION_CONDITIONING_CANDIDATE`: side information reserved for a future separable and ablatable conditioning design.
- `REPRESENTATION_LIMITED_BY_OBSERVER_SYNCHRONIZATION`: technically valid pixel/map operation whose complete observer transformation remains unresolved.
- `DEFERRED`: operation lacks evidence or semantics required for a representation experiment.
- `BLOCKED`: an existing prospective gate or physical contract is absent.

These categories are not rankings and do not imply scientific equivalence, morphology preservation, invariance, or permission to train.

## 2. Frozen technical findings

### 2.1 B00 native baseline

`B00_NATIVE_IMAGE_ONLY` passed integrity validation for exactly 18 native IMAGE references: six windows times g/r/z. It created no transformed baseline. `E3` records mathematical and bitwise reversibility as true, no information removed or distorted, and `TECHNICAL_REFERENCE_ONLY` as the semantic limitation. B00 remains the mandatory comparator for every future branch. No later representation result may replace it as the reference.

### 2.2 B01 multiplicative flux-scale variants

For both `B01_FACTOR_0P5` and `B01_FACTOR_2P0`, all 18 IMAGE rows per variant have:

- input and output dtype `<f4`;
- bitwise round-trip fraction `1.0` and maximum absolute round-trip error `0.0`;
- identical finite and nonfinite counts, with zero newly nonfinite values;
- unchanged exact-zero counts in every row; and
- zero clipping.

The operation remains information-changing: `E3` records `ABSOLUTE_FLUX_SCALE` as intentionally removed and `FLOAT32_RANGE_AND_ROUNDING` as a possible numerical effect. B01 is technically admissible only as a multiplicative flux-scale sensitivity test. This is not a scientific declaration of multiplicative flux invariance.

### 2.3 B02 additive-offset variants

Both B02 variants completed with `<f4` inputs and outputs, preserved finite/nonfinite counts, created no nonfinite values, and had zero clipping. They are mathematically reversible but not bitwise reversible:

| Variant | Round-trip bitwise fraction across rows | Maximum absolute round-trip error | Exact-zero effect |
|---|---:|---:|---|
| `B02_OFFSET_NEGATIVE` | `0.43933657833062917` to `0.6922660897782585` | `3.725290298461914e-09` | Changed in 4/18 rows; output-minus-input zero count ranged from `-203` to `0`. |
| `B02_OFFSET_POSITIVE` | `0.40514392163932456` to `0.5743044288203834` | `2.9802322387695312e-08` | Changed in 4/18 rows; output-minus-input zero count ranged from `-203` to `0`. |

`E3` records `NATIVE_ZERO_LEVEL` as intentionally removed and `FLOAT32_ROUNDING_AND_ZERO_MEMBERSHIP` as potentially distorted. B02 is a `LOSSY_NUMERICAL_STRESS_TEST` candidate within the closed `REPRESENTATION_STRESS_TEST` category. No tolerance is introduced to reinterpret the loss as equivalence. B02 is not background estimation or background correction.

### 2.4 B03 development-scale division

`B03_DIVIDE_BY_DEVELOPMENT_REFERENCE_SCALE_001` completed 18 `<f4` rows, preserved finite/nonfinite and exact-zero counts, created no nonfinite values, and had zero clipping. It is mathematically reversible but not bitwise reversible. Its row-wise bitwise round-trip fraction ranged from `0.8765699176732168` to `0.9970554654167418`; its maximum absolute round-trip error was `9.5367431640625e-07`.

The branch remains bound to:

```text
DEVELOPMENT_ONLY_SCALE
NOT_AUTHORIZED_AS_FUTURE_TRAINING_SCALE
```

`E3` records `NATIVE_UNIT_MAGNITUDE_RELATIVE_TO_DEVELOPMENT_SCALE` as intentionally removed and `FLOAT32_DIVISION_AND_ROUND_TRIP` as potentially distorted. B03 is a `LOSSY_NUMERICAL_STRESS_TEST` candidate within `REPRESENTATION_STRESS_TEST`. Its six-window scale cannot become a future scientific training scale. Any future scale must be defined independently from the future training reference population under a separate prospective protocol.

### 2.5 B12 and B13 lattice geometry

The three B12 rotations and two B13 reflections transformed the 13 aligned maps per window by exact integer lattice permutations. Across all 390 rows, the pilot established:

- exact dtype and multiset-byte preservation;
- exact inverse bitwise reconstruction;
- identical finite, nonfinite, and zero counts;
- zero padding, interpolation, and clipping;
- synchronized IMAGE, INVVAR, NEXP, MASKBITS, PSFSIZE, and affine WCS handling; and
- maximum WCS residual `4.3382897274568677e-10` native pixel against the frozen `1e-6` bound.

This is pixel/map transformation evidence. It is not evidence of a complete observational transformation. Provider PSF responses were not transformed. The binding limitation remains exactly:

```text
TRANSFORMED_WINDOW_HAS_NO_TRANSFORMED_PROVIDER_PSF_RESPONSE
```

B12 and B13 therefore remain `REPRESENTATION_LIMITED_BY_OBSERVER_SYNCHRONIZATION`. They may enter a later experiment only if that experiment explicitly isolates the image/map permutation question and carries this limitation, or after a separate prospective contract provides a physically valid synchronized PSF-response transformation. Neither route may be described as established rotation or reflection invariance.

### 2.6 B14 single-band selections

`B14_G_ONLY`, `B14_R_ONLY`, and `B14_Z_ONLY` each have six manifest rows and created no pixel arrays. Each subbranch retains one native band and makes the other two bands plus their cross-band information intentionally unavailable. The retained band keeps its associated observer metadata.

All three are `REPRESENTATION_ABLATION`. They measure dependence on band information. They are not morphology-equivalent or observationally equivalent to native g/r/z. No grayscale, synthetic color, averaging, or learned mixing branch is introduced.

### 2.7 B09 NEXP stratification

B09 completed as metadata only and exactly records:

```text
S1 -> Z0_TALL
S2 -> Z0_TALL
S3 -> Z0_TSOME
N1 -> ZANY_TALL
N2 -> ZANY_TALL
N3 -> Z0_TSOME
```

It is `REPRESENTATION_STRATIFICATION_ONLY`. It may define descriptive robustness groups. It may not alter IMAGE, become a training target or sample weight, define exclusions, or enter an encoder automatically. The six-window mapping carries `SIX_WINDOW_DEVELOPMENT_MAPPING_NO_STATISTICAL_INFERENCE` and cannot calibrate population thresholds.

## 3. Closed branch decision table

| branch_id | pilot_execution_status | readiness_category | technical_reversibility | information_removed | observer_synchronization | allowed_future_role | prohibited_claim | required_future_condition | evidence_reference |
|---|---|---|---|---|---|---|---|---|---|
| `B00_NATIVE_IMAGE_ONLY` | `REFERENCE_VALIDATED` | `REPRESENTATION_BASELINE` | Mathematical=true; bitwise=true; no transform. | None. | Native observer metadata retained externally. | Mandatory comparator for every branch. | That any transformed result can replace B00 as reference. | Frozen input integrity must continue to pass. | `E1:b00_references`; `E3:B00_NATIVE_IMAGE_ONLY`; `E6` |
| `B01_MULTIPLICATIVE_FLUX_SCALE` | `EXECUTED` | `REPRESENTATION_STRESS_TEST` | Mathematical=true; bitwise=true for both variants; max error `0.0`. | Absolute flux scale. | IMAGE g/r/z changed by one shared rule; observer variables unchanged externally. | Test sensitivity to factors 0.5 and 2.0 against B00. | Multiplicative flux invariance or observational equivalence. | Future protocol must retain both frozen variants and B00 without outcome-based selection. | `E2:B01_*`; `E3:B01_*` |
| `B02_ADDITIVE_OFFSET` | `EXECUTED` | `REPRESENTATION_STRESS_TEST` | Mathematical=true; bitwise=false; max errors `3.725290298461914e-09` and `2.9802322387695312e-08`. | Native zero level; exact-zero membership changed. | IMAGE g/r/z changed by rule; observer variables unchanged externally. | Deliberately lossy numerical stress test against B00. | Observational equivalence, background estimate, or background correction. | Future protocol must label it `LOSSY_NUMERICAL_STRESS_TEST` and retain frozen numerical-loss provenance. | `E2:B02_*`; `E3:B02_*` |
| `B03_ROBUST_GLOBAL_SCALE` | `EXECUTED` | `REPRESENTATION_STRESS_TEST` | Mathematical=true; bitwise=false; max error `9.5367431640625e-07`. | Native unit magnitude relative to development scale. | IMAGE g/r/z changed by rule; observer variables unchanged externally. | Deliberately lossy scale-sensitivity test against B00. | Scientific normalization, future training scale, or observational equivalence. | Future training-reference scale must be defined independently; carry both development-only labels. | `E1:method_bindings`; `E2:B03_*`; `E3:B03_*` |
| `B04_INVVAR_CONDITIONING` | `RESERVED_FOR_REPRESENTATION_STAGE` | `REPRESENTATION_CONDITIONING_CANDIDATE` | Not applicable; no operation executed. | None. | Architecture undefined. | Separable, ablatable uncertainty/support conditioning candidate. | Gaussian likelihood semantics, S/N replacement, or automatic IMAGE multiplication. | Freeze conditioning architecture and IMAGE-only comparator prospectively. | `E1:reserved_side_information`; `E3:B04_*`; `A1:D04-D06` |
| `B05_MASK_FAMILY_CONDITIONING` | `RESERVED_FOR_REPRESENTATION_STAGE` | `REPRESENTATION_CONDITIONING_CANDIDATE` | Not applicable; no operation executed. | None. | Architecture undefined. | Separable, family-specific conditioning candidate. | All nonzero bits are invalid, or masked pixels may be rewritten. | Freeze ablatable NPRIMARY/optical/WISE/unknown paths without altering IMAGE. | `E1:reserved_side_information`; `E3:B05_*`; `A1:D07-D08` |
| `B06_CONTROLLED_MASK_REMOVAL` | `BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE` | `BLOCKED` | Not applicable; no operation executed. | None in pilot. | No removal contract. | None. | Permission to remove, inpaint, zero, or exclude masked evidence. | Resolve `NO_EXPLICIT_MASK_REMOVAL_GATE` prospectively. | `E1:branch_classes`; `E3:B06_*`; `A1:D08` |
| `B07_PSFSIZE_CONDITIONING` | `RESERVED_FOR_REPRESENTATION_STAGE` | `REPRESENTATION_CONDITIONING_CANDIDATE` | Not applicable; no operation executed. | None. | Architecture undefined; full PSF provenance remains external. | Separable, ablatable scalar seeing-context candidate. | PSFSIZE fully specifies the PSF. | Freeze conditioning architecture and retain full PSF provenance plus no-PSFSIZE comparator. | `E1:reserved_side_information`; `E3:B07_*`; `A1:D09-D10` |
| `B08_PSF_PERTURBATION_OR_MATCHING` | `BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE` | `BLOCKED` | Not applicable; no operation executed. | None in pilot. | Physical PSF transformation unresolved. | None. | PSF homogenization, matching, deconvolution, or common response is validated. | Resolve `PHYSICAL_PSF_NORMALIZATION_AND_MATCHING_SEMANTICS_UNRESOLVED`. | `E1:branch_classes`; `E3:B08_*`; `A1:D11` |
| `B09_NEXP_STRATIFICATION` | `METADATA_ONLY_COMPLETED` | `REPRESENTATION_STRATIFICATION_ONLY` | Not applicable; no pixel operation. | None. | Uses frozen NEXP audit rows; IMAGE unchanged. | Descriptive robustness grouping and observer-shortcut analysis. | Training target, weight, exclusion, automatic encoder input, or statistical population inference. | Future population must define strata prospectively and validate coverage; current mapping remains development-only. | `E4`; `E3:B09_*` |
| `B10_NEXP_CONDITIONING` | `RESERVED_FOR_REPRESENTATION_STAGE` | `REPRESENTATION_CONDITIONING_CANDIDATE` | Not applicable; no operation executed. | None. | Architecture undefined. | Separable, ablatable exposure/support conditioning candidate. | NEXP may change IMAGE or be conflated with INVVAR. | Freeze conditioning architecture, hidden-NEXP comparator, and observer-shortcut probes. | `E1:reserved_side_information`; `E3:B10_*`; `A1:D02-D03` |
| `B11_NEXP_CONTROLLED_PERTURBATION` | `BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE` | `BLOCKED` | Not applicable; no operation executed. | None in pilot. | Joint physical transformation unresolved. | None. | Changing NEXP alone creates a corresponding observation. | Resolve `NO_PHYSICALLY_VALID_JOINT_IMAGE_INVVAR_NEXP_PERTURBATION`. | `E1:branch_classes`; `E3:B11_*`; `A1:D02-D03` |
| `B12_ROTATION` | `EXECUTED` | `REPRESENTATION_LIMITED_BY_OBSERVER_SYNCHRONIZATION` | Mathematical=true; bitwise=true for 13 maps; exact lattice permutations. | None from synchronized maps. | IMAGE/INVVAR/NEXP/MASKBITS/PSFSIZE/WCS synchronized; provider PSF response unsynchronized. | Explicitly limited image/map permutation robustness test. | Complete observational transformation, morphology invariance, or rotation invariance. | Either freeze a PSF-response transform or prospectively isolate the map-only question and retain the exact limitation. | `E1:wcs_adapters`; `E2:B12_*`; `E3:B12_*` |
| `B13_REFLECTION` | `EXECUTED` | `REPRESENTATION_LIMITED_BY_OBSERVER_SYNCHRONIZATION` | Mathematical=true; bitwise=true for 13 maps; exact lattice permutations. | None from synchronized maps. | IMAGE/INVVAR/NEXP/MASKBITS/PSFSIZE/WCS synchronized; provider PSF response unsynchronized. | Explicitly limited image/map reflection robustness test, separate from rotation. | Complete observational transformation, morphology invariance, reflection invariance, or irrelevant chirality. | Same PSF/isolation condition as B12; keep reflection separate from rotation. | `E1:wcs_adapters`; `E2:B13_*`; `E3:B13_*` |
| `B14_BAND_ABLATION` | `EXECUTED` | `REPRESENTATION_ABLATION` | Mathematical=false; bitwise=false as a multiband representation; no new pixels. | Two bands and their cross-band information per subbranch. | Retained-band observer metadata synchronized; omitted bands unavailable to subbranch. | Measure dependence on g, r, or z information. | Morphology equivalence or observational equivalence to native g/r/z. | Freeze input-interface handling for g-only/r-only/z-only and keep all three plus B00. | `E1:band_selections`; `E3:B14_*` |
| `B15_PRIMARY_ONLY_SENSITIVITY` | `BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE` | `BLOCKED` | Not applicable; no operation executed. | None in pilot. | No primary-only object/window contract. | None. | Permission to discard nonprimary evidence or rewrite S2. | Resolve `NO_PROSPECTIVE_PRIMARY_ONLY_SCIENTIFIC_GATE`. | `E1:branch_classes`; `E3:B15_*`; `A1:D12-D13` |

No B00-B15 branch is assigned `DEFERRED`: the four unresolved executable proposals have explicit `BLOCKED` gates, while the conditioning proposals are reserved candidates. The following broader operations retain the separate `DEFER` decisions from `A1` and are outside the executed branch inventory:

| Operation | Readiness | Required future evidence |
|---|---|---|
| Background estimation/subtraction | `DEFERRED` | Background definition, estimator, spatial scale, mask interaction, and information-loss bound. |
| Scale/resolution normalization | `DEFERRED` | Scientific object support, distance/physical-scale semantics, PSF and pixel-scale controls, interpolation and loss contract. |
| PSF homogenization | `DEFERRED` | Physical normalization, target response, flux, boundary, noise-covariance, and validation rules; B08 remains blocked. |

No blocker or deferral is removed by successful pilot execution.

## 4. Minimal future representation experiment

Branch readiness is conditional and is not execution authorization. After the scientific-object/cohort bridge in section 7 and a separate frozen representation-experiment specification exist, the minimal first wave is:

1. `B00_NATIVE_IMAGE_ONLY` as the mandatory comparator;
2. `B01_FACTOR_0P5`; and
3. `B01_FACTOR_2P0`.

This set preserves shape, dtype, band interface, support, and external observer metadata while isolating one frozen multiplicative-scale question with exact bitwise round trips. Both B01 directions are required; neither may be selected from outcomes. B09 may accompany the first wave only as descriptive stratification and observer-shortcut auditing, never as an encoder input, weight, target, or exclusion rule.

The first wave does not establish a preferred preprocessing or scientific flux invariance. It asks whether a future representation changes under the two frozen scale stresses relative to B00.

The second wave is ordered by experimental isolation, not expected performance:

- B02 and B03 may test deliberate numerical loss, each separately and with its frozen provenance;
- B14 may test one-band ablations after the representation interface defines comparable g-only/r-only/z-only inputs without synthetic color;
- B12 and B13 may run only under their observer-synchronization limitation or after a valid PSF-response contract;
- B04, B05, B07, and B10 require a separable, ablatable conditioning architecture and matching hidden-observer comparators; and
- B06, B08, B11, and B15 remain unavailable until their exact blockers are resolved prospectively.

No experiment is required to combine all technically admissible branches. Combining scale, additive loss, band removal, geometry, and conditioning in one first experiment would prevent attribution of an observed effect to one controlled question.

## 5. Mandatory observer-shortcut audit

Before any representation experiment starts, its prospective specification must freeze a probe plan for observer information retained by every encoder candidate and relevant branch. At minimum the plan must cover:

1. north/south survey region;
2. NEXP strata and predeclared support/transition summaries;
3. INVVAR zero-support and predeclared dispersion diagnostics;
4. NPRIMARY, optical, WISE, and unknown MASKBITS family prevalence separately;
5. PSFSIZE and only prospectively allowed PSF descriptors, with full PSF provenance retained; and
6. BRICK_PRIMARY or mixed-primary status.

The future experiment must compare observer predictability across relevant branches against B00. It must freeze probe family, leakage-controlled split/grouping unit, metrics, null or permutation controls, uncertainty reporting, and decision rules before results are observed. No numerical threshold is set here because none was prospectively frozen and six windows cannot calibrate one.

Observer predictability measures retained observer information. It is not by itself proof of an invalid representation and does not authorize information removal. The analysis must distinguish observer metadata, sampling, measurement quality, and potentially entangled astrophysical information.

Human annotations, Galaxy Zoo votes or vote fractions, morphology names, morphology-derived selections, and predictions derived from them remain outside preprocessing, branch, encoder, hyperparameter, threshold, and stopping decisions.

## 6. Critical population limitation

The completed pilot contains exactly:

```text
2 technical development bricks
6 observational windows
0 defined astronomical objects
```

No morphology representation can be scientifically trained or evaluated from these six windows. They do not define galaxies, independent sampling units, a morphology-learning population, or leakage-controlled development and holdout sets.

The six windows may be used only to validate:

- representation plumbing;
- observer-shortcut probe plumbing;
- transformation and invariance mechanics; and
- deterministic experiment reproducibility.

They are not sufficient to estimate morphology structure, tune a representation, compare scientific generalization, set robustness thresholds, choose an encoder, or define a future training scale.

## 7. Required bridge before representation learning

Before any real representation learning, a prospective scientific-object and cohort design must define all of the following without materializing the cohort in this decision:

### A. Scientific observational unit

Define what constitutes one galaxy/object observation, including identity, coordinate authority, centering semantics, angular support, band completeness, duplicate handling, survey-region identity, and the distinction among object, observation, brick, and cutout.

### B. Extraction and materialization

Freeze the native product, release, cutout dimensions, WCS rule, edge/support behavior, immutable provenance, checksum contract, failure states, and observer-map/PSF associations for each observational unit.

### C. Split and grouping unit

Define development, training, validation, and holdout boundaries before representation outcomes exist. Group all duplicate or related observations so no object, shared observation, acquisition unit, or other prospectively identified dependency can cross a forbidden boundary.

### D. Relation of the six windows to the population

Keep the six current windows as technical fixtures for plumbing and reproducibility. They cannot become scientific examples merely because the future cohort overlaps their sky positions. Any future relationship must be explicit and prevent fixture-driven tuning from contaminating evaluation.

### E. Observer variables per object

Bind region, NEXP, INVVAR, MASKBITS families, PSFSIZE, allowed full-PSF provenance/descriptors, BRICK_PRIMARY status, WCS, release, brick/resource identities, and any missingness/support state to each object observation without automatically injecting them into IMAGE or an encoder.

### F. Label-free cohort formation

Define selection using technical and observational eligibility only. Morphology labels, Galaxy Zoo votes, vote fractions, morphology predictions, and morphology-derived filtering or threshold choices must remain inaccessible.

### G. Sample size and coverage

Prospectively justify minimum counts, independent grouping units, north/south coverage, observer-condition coverage, band/support completeness, and development/validation/holdout adequacy for the intended unsupervised or self-supervised method and observer probes. This decision sets no numerical minimum because no method, scientific unit, power criterion, or target population is yet frozen.

### H. External-label firewall

Specify access controls and stage boundaries that prevent external morphology labels or label-derived predictions from influencing cohort construction, preprocessing, augmentations, encoder selection, hyperparameters, representation selection, clustering, or stopping. Any later interpretation must consume frozen representations and analyses without retroactive tuning.

## 8. Existing methods before architecture selection

Before an encoder architecture is frozen, a targeted literature and methods review must cover at least:

- self-supervised learning for astronomical images;
- contrastive and non-contrastive representation learning;
- astronomy-specific augmentation and invariance assumptions;
- unsupervised galaxy-morphology methods;
- survey/domain shortcut detection;
- nuisance-aware and conditional representation methods; and
- simple baselines including PCA, autoencoders, and existing embeddings.

The review must map each method's observational assumptions, required sample size and split unit, augmentations, nuisance handling, observer-shortcut controls, reproducibility requirements, and information-loss claims to the future cohort contract. A new project-specific encoder may be proposed only after existing methods are shown insufficient for a stated requirement. This document performs no literature search and selects no architecture.

## 9. Exact next stage

The sole immediate next stage is:

**Stage ID:** `OC3-SCIENTIFIC-OBJECT-AND-COHORT-DESIGN-001`

**Stage name:** SCIENTIFIC OBJECT AND COHORT DESIGN

Its purpose is to freeze prospectively:

- the scientific galaxy/object observational unit;
- label-free identity and eligibility rules;
- extraction and immutable materialization protocol;
- observer metadata and provenance attached to each unit;
- development, training, validation, and holdout grouping boundaries;
- sample-size and observer-coverage requirements; and
- transfer of the six-window observer-audit safeguards to the future population.

This next stage must not materialize the cohort, train an encoder, create embeddings, cluster observations, access morphology labels, or choose a representation architecture. A later implementation/acquisition authorization is required after its specification is frozen.

## 10. Decision boundary and zero-execution declaration

This decision establishes branch readiness for future controlled comparisons only. It does not authorize any branch execution, scientific cohort construction, representation learning, encoder construction, embedding calculation, clustering, morphology analysis, image display, or label access.

Creating this document performed:

- zero new transformations;
- zero new pixel reads;
- zero input modifications;
- zero network requests;
- zero model or encoder operations;
- zero embeddings or clustering operations;
- zero morphology operations;
- zero image displays or plots; and
- zero label accesses.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
