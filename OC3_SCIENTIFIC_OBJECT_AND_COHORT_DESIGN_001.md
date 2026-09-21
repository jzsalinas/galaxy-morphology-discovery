# OC3 Scientific Object and Cohort Design 001

## 0. Status, scope, and authority

**Design ID:** `OC3-SCIENTIFIC-OBJECT-AND-COHORT-DESIGN-001`

**Status:** FROZEN PROSPECTIVE DESIGN / DECISION ONLY

**Design-completion terminal:** `SCIENTIFIC_OBJECT_AND_COHORT_DESIGN_FROZEN`

**Authority:** `OC3_REPRESENTATION_BRANCH_READINESS_DECISION_001.md`

**Authority SHA-256:** `61b3bf73e723876ebd29844cda3d6738f6eb74015a94ab446cb85540e48c16b0`

**Cohort materialization authorized:** NONE

**Tractor catalog acquisition authorized:** NONE

**Object or source selection performed:** NONE

**Network access:** NONE

**Pixel access, cutout creation, model, encoder, embedding, clustering, morphology, and label access:** NONE

This design defines the contracts and unresolved gates that must precede a scientific cohort. It does not create a cohort, declare a Tractor source to be a galaxy, select sources, choose an encoder, or authorize representation learning.

The completion terminal means only that the provisional scientific unit, candidate eligibility policies, cutout policy options, observer-metadata contract, split strategy, label firewall, method families, cohort options, and unresolved gates have been documented prospectively. It is not an execution terminal.

## 1. Evidence classes and decision boundary

The document keeps three evidence classes separate.

### 1.1 OFFICIAL DR9 DOCUMENTATION

The official DR9 documentary findings supplied for this design establish:

1. Tractor catalog-source identity is the tuple `(RELEASE, BRICKID, OBJID)`.
2. Catalog fields include `RELEASE`, `BRICKID`, `OBJID`, `BRICKNAME`, `RA`, `DEC`, `BX`, `BY`, `BRICK_PRIMARY`, `MASKBITS`, `FITBITS`, `TYPE`, and additional photometric/model quantities.
3. `TYPE` is a model-fit/morphological choice with values including `PSF`, `REX`, `EXP`, `DEV`, `SER`, and `DUP`.
4. DR9 source detection uses PSF-matched and SED-matched filtering on stacked imaging, approximately six-sigma detection, detected peaks as Tractor initialization, and subsequent fitting that may move positions or remove low-SNR candidates.
5. Official sweep construction uses `BRICK_PRIMARY` to provide unique primary catalog sources.

These facts support technical identity and provenance. They do not prove that a row is a galaxy, an independent astrophysical object, or a morphology-suitable observation. Before a catalog acquisition stage, the exact official pages, versions, retrieval timestamps, and content hashes supporting these statements must be bound by a separate documentary contract.

### 1.2 LITERATURE

The targeted findings supplied for this design establish method precedents, not project decisions:

- Mohale & Lochner used BYOL-derived representations on Galaxy Zoo DECaLS material followed by unsupervised clustering/anomaly workflows. Their results demonstrate an astronomy-specific SSL path and also motivate explicit control of zoom, companions, artifacts, and other observer/scene shortcuts.
- Wei et al. provide a contrastive unsupervised galaxy-morphology representation precedent. Its exact bibliographic identity, dataset, augmentations, split rules, and scale requirements must be bound before use.
- supervised Zoobot representations may later serve only as a comparator or post-freeze interpretation reference. They are not a training, eligibility, preprocessing, or selection authority for this project.
- BYOL, SimCLR, Barlow Twins, DINO, and MAE represent distinct generic SSL assumptions; PCA and convolutional autoencoders provide simpler baselines.

This design performs no new literature search. The full bibliographic and implementation binding remains a prerequisite for a future method specification.

### 1.3 PROJECT DECISION

The project decisions below are prospective controls derived from the authority and the supplied documentary/literature findings. They are not claims made by the DR9 provider or by the cited literature.

## 2. Ontology: detection, source, object, galaxy, image, and cohort

The following terms are distinct and may not be substituted for one another:

| Term | Prospective definition | What it is not |
|---|---|---|
| `SOURCE_DETECTION` | A pipeline detection/peak candidate produced by the documented DR9 detection process before or during Tractor initialization and fitting. | A catalog identity, stable astrophysical object, or galaxy. |
| `CATALOG_SOURCE_OBSERVATION` | One retained DR9 Tractor catalog row with technical identity `(RELEASE, BRICKID, OBJID)` and its catalog provenance. | A guaranteed independent object or galaxy. |
| `ASTROPHYSICAL_OBJECT` | A real-world source association that may link one or more catalog observations after a separately validated cross-observation/grouping contract. | Automatically identical to one Tractor row. |
| `GALAXY_ELIGIBILITY` | A policy result based on a future morphology-independent extragalactic evidence contract. | Tractor `TYPE`, morphology ground truth, or a visual judgment. |
| `IMAGE_OBSERVATION` | A reproducible catalog-centered native g/r/z image support plus linked observer products, WCS, and immutable provenance for one catalog-source observation. | The astrophysical object itself or proof that the support contains one complete galaxy. |
| `SCIENTIFIC_COHORT_MEMBER` | An observation or grouped object admitted only after all required identity, eligibility, support, metadata, split, sample-size, and firewall gates pass. | Any row that merely exists in a Tractor file. |

The distinctions prevent the invalid implications `catalog row == independent object`, `cutout == object`, and `Tractor model choice == morphology truth`.

## 3. Source-detection provenance and provisional base unit

The frozen provisional base unit is:

```text
DR9_SOURCE_OBSERVATION
```

Its minimum contract is:

```text
source_identity = (release, brickid, objid)
observation_id = canonical DR9 namespace + source_identity
region
brickname
ra
dec
bx
by
brick_primary
survey_and_release_provenance
source_detection_provenance = PIPELINE_DETECTED_SOURCE_OBSERVATION
```

`source_identity` is the official unique catalog-source identity. `observation_id` is a project technical identifier derived deterministically from that tuple; its exact serialization must be frozen before materialization. Region, brick name, sky position, and pixel position are provenance and validation fields rather than replacements for the official tuple.

The unit is described exactly as:

```text
PIPELINE_DETECTED_SOURCE_OBSERVATION
```

It must not be described as `ONTOLOGICALLY_DEFINED_GALAXY`. Its detection and fitting selection function remains attached to every future record, including PSF/SED matching, stacked-image detection, approximate threshold, peak initialization, position evolution, and low-SNR removal provenance.

The direct answer to the central question is therefore provisional and exact:

```text
SCIENTIFIC_OBSERVATIONAL_UNIT_CANDIDATE =
one catalog-centered IMAGE_OBSERVATION anchored to exactly one canonical
BRICK_PRIMARY DR9_SOURCE_OBSERVATION, preserving native g/r/z support,
observer metadata, WCS, resource provenance, detection provenance,
missingness, and a future SPLIT_GROUP_ID
```

This unit is an observation candidate for future morphology discovery. It is not yet a galaxy, an independent astrophysical object, or a cohort member. Those promotions require the eligibility and grouping gates below.

Promotion to an extragalactic/morphology cohort requires a resolved galaxy-eligibility policy based on bounded evidence independent of Tractor morphology fields, plus every technical and grouping gate in this document.

## 4. Tractor firewall

### 4.1 Permitted Tractor roles

Tractor may serve as:

- source-detection provenance;
- technical source identity through `(RELEASE, BRICKID, OBJID)`;
- catalog-center authority through `RA/DEC`, with `BX/BY` used for native-grid validation;
- brick, region, release, primary-status, photometric, and technical provenance metadata; and
- a source of fields retained behind audit or interpretation firewalls.

### 4.2 Prohibited Tractor roles

Tractor must not serve as:

- morphology ground truth;
- galaxy eligibility through `TYPE`;
- object-support or cutout-size authority through model radii;
- preprocessing, augmentation, encoder, or representation selector;
- balancing or split authority through morphology/model fields; or
- cluster/discovery interpretation authority.

`TYPE`, including `PSF`, `REX`, `EXP`, `DEV`, `SER`, and `DUP`, is prohibited for galaxy eligibility, cohort construction, object support, cutout-size choice, split construction, balancing, filtering, encoder selection, and preprocessing. The `DUP` label may not be repurposed as a split-group identifier because it remains inside the `TYPE` firewall.

The same firewall applies to `sersic`, `shape_r`, `shape_e1`, `shape_e2`, and model-goodness quantities that favor morphological families. They may be retained behind an interpretation firewall for a separately authorized post-hoc analysis only. Photometry and colors may be retained as provenance but may not define galaxy eligibility or cohort membership in this design.

`MASKBITS` and `FITBITS` are technical/provider metadata. Their presence does not automatically make a source ineligible, and model-fit flags may not be converted into morphology filters.

## 5. Galaxy-eligibility decision

The frozen decision is:

```text
BOUNDED_COMPARISON_OF_BOTH
GALAXY_ELIGIBILITY_DECISION_REQUIRES_BOUNDED_EVIDENCE
```

“Both” means that a bounded future evidence stage must compare a source-observation-first policy against a policy requiring independent extragalactic evidence before cohort membership. The astrometric star-exclusion alternative must be assessed as a third morphology-independent candidate. The design does not choose a final cohort policy because no bounded evidence currently establishes attainable counts, north/south coverage, depth effects, cross-match completeness, or selection bias for those alternatives.

The alternatives are:

| Option | Definition | Scientific purity | Selection bias | Sample-size effect | North/south and depth risk | Observer-confound risk | External dependency | Reproducibility | Compatibility with unsupervised morphology goal |
|---|---|---|---|---|---|---|---|---|---|
| `A_SOURCE_OBSERVATIONS_NO_GALAXY_PRESELECTION` | Technically valid primary DR9 source observations; galaxy status deferred. | Mixed stars, galaxies, artifacts, and ambiguous sources by construction. | Lowest added semantic prior beyond provider detection. | Potentially broad; must be measured, not assumed. | Tracks DR9 detection/coverage; domain prevalence may vary strongly. | Point-source dominance, artifacts, depth, seeing, and provider selection may dominate structure. | DR9 only. | High if technical gates and manifests are frozen. | Preserves discovery openness but may obscure galaxy morphology. |
| `B_INDEPENDENT_SPECTROSCOPIC_EXTRAGALACTIC_GATE` | DR9 primary sources intersected with an independent spectroscopic class/redshift authority under a frozen match contract. | Extragalactic status can be independent of Tractor morphology. | Strong targeting, magnitude, footprint, success-rate, and population bias. | Reduced and footprint-dependent; must be observed. | May be uneven by region and depth. | Spectroscopic survey identity and target selection become shortcuts. | External spectroscopy and cross-match provenance. | High only if releases, identities, match rules, and failures are immutable. | Provides a clearer extragalactic population while narrowing discovery scope. |
| `C_INDEPENDENT_ASTROMETRIC_STAR_EXCLUSION` | Exclude only independently confident stellar matches under a frozen Gaia-like evidence rule; absence of a match is not galaxy evidence. | Removes some confident stars but leaves ambiguous sources and compact galaxies at risk. | Astrometric detectability, magnitude, crowding, match, and motion-quality bias. | Intermediate and unknown until bounded evidence. | Completeness can vary with depth, crowding, and region. | External astrometric coverage and matching behavior become shortcuts. | External astrometry and cross-match provenance. | High only with a frozen positive-star criterion and explicit unknown state. | Avoids a positive morphology gate but cannot establish galaxy status. |
| `D_PHOTOMETRIC_OR_COLOR_GATE` | Select using colors or photometric star-galaxy criteria. | Potentially higher nominal separation but unverified here. | Directly conditions the cohort on spectral quantities entangled with galaxy populations. | Unknown. | Strong depth, calibration, extinction, and missing-band sensitivity. | Color and photometric survey systematics can dominate representation structure. | Photometric rule and calibration. | Technically reproducible but scientifically high risk. | Not admissible without a later explicit evidence gate; not part of the bounded leading comparison. |

No option is globally ranked. The next evidence stage must report retained/unknown/rejected states, coverage and bias indicators for A/B/C without reading morphology labels or selecting a preferred option from representation outcomes. It must not fall back to Tractor `TYPE` if external evidence is absent.

## 6. Primary status, duplicates, blends, and dependence

### 6.1 BRICK_PRIMARY rule

The provisional catalog-membership rule requires:

```text
BRICK_PRIMARY == true
```

Its sole purpose is provider duplicate prevention and canonical catalog-source identity. It is not a scientific quality filter, morphology criterion, clean-image criterion, pixel mask, or permission to discard nonprimary pixels from a primary source's image support.

Nonprimary catalog occurrences, when available, remain provenance for duplicate/group audits. They may not become separate split members. The S2 mixed-primary six-window fixture remains unchanged technical evidence. This rule does not resolve or authorize `B15_PRIMARY_ONLY_SENSITIVITY`, rewrite S2, crop to a primary footprint, or claim that primary sources have superior morphology.

### 6.2 Observation and object identifiers

The design keeps separate:

- `OBSERVATION_ID`: deterministic technical identifier for one `DR9_SOURCE_OBSERVATION`;
- `OBJECT_ID`: identifier for a validated astrophysical association group, unresolved until a future grouping contract exists; and
- `SPLIT_GROUP_ID`: closed transitive group containing all catalog duplicates, related observations, and shared astrophysical-object associations known under the frozen contract.

If the initial DR9 scope ultimately contains one canonical `BRICK_PRIMARY` row per source, that is a release-specific catalog scope, not a universal one-observation-per-galaxy ontology.

### 6.3 Blend/source-group status

The currently supplied official field set and semantics do not provide a validated blend-family or source-group identifier suitable for leakage grouping. `TYPE=DUP` is unavailable for this purpose under the TYPE firewall. `MASKBITS`, `FITBITS`, proximity, and model complexity are not substitutes for a documented group relation.

The frozen state is:

```text
BLEND_GROUPING_SEMANTICS_UNRESOLVED
```

Resolution requires:

1. exact official DR9 documentation and schema for any blob, source-group, parent/child, duplicate-link, or cross-brick relation;
2. a bounded metadata inspection of actual field availability, nulls, cardinality, and region/release consistency;
3. a morphology-independent association rule, including any angular/provenance tolerance, frozen before outcomes;
4. transitive-closure behavior and stable group identifiers;
5. treatment of unresolved or ambiguous group membership; and
6. verification that no group crosses a split.

Blend complexity may be recorded as observer/detection provenance when documented. It may not select visually simple or isolated sources, alter cutout support, or define a morphology cohort without a later explicit gate.

## 7. Image-observation center and support

### 7.1 Center authority

The first scientific image-observation contract will be catalog-centered:

```text
center_authority = catalog RA/DEC from the exact source_identity
native_grid_validation = BX/BY in the bound brick/product when available
recenter_operation = NONE
```

RA/DEC is retained with the documented detection/fitting provenance and is not treated as an invariant physical centroid. BX/BY must be reproduced from the exact frozen catalog observation and native coadd/WCS contract; disagreement is a technical failure or documented discrepancy, never an invitation to recenter.

Centroids, segmentation, brightness peaks, Tractor morphology models, `shape_r`, Sérsic parameters, and visual judgments are prohibited as recentering authorities.

### 7.2 Cutout-support options

The existing 129x129 technical windows do not set the future scientific support. The options are:

| Support option | Prospective rule | Strength | Risk and information loss | Status |
|---|---|---|---|---|
| `A_FIXED_SUPPORT` | One prospectively frozen angular/pixel support for every observation. | Does not require morphology fields; simple provenance and model interface. | Can truncate extended objects; small objects may be dominated by sky, neighbors, PSF, masks, and support transitions. | Leading baseline candidate; numerical size unresolved. |
| `B_FINITE_SUPPORT_SET` | Apply a small frozen set of supports consistently as a sensitivity design, without assigning sizes from object appearance. | Makes support sensitivity measurable. | Multiplies storage/compute and creates related views that must stay in one split group; support choice can still expose observer context. | Candidate robustness design; values unresolved. |
| `C_MORPHOLOGY_INDEPENDENT_ADAPTIVE_SUPPORT` | Adapt support only from a separately justified non-morphological authority. | Could reduce truncation and excess field. | No currently validated quantity separates object extent from morphology/model assumptions; may encode distance, brightness, seeing, or selection. | `DEFERRED`. |

The frozen support decision state is:

```text
CUTOUT_SUPPORT_POLICY_RESOLVED = false
```

A future support decision must predeclare support values, angular/pixel interpretation, center convention, edge policy, full-containment or missing-support states, WCS behavior, large-object truncation risk, small-object observer dominance, related-view grouping, and storage/compute cost. It may not choose support from Tractor radius, Sérsic size, morphology model, segmentation, or outcome quality.

### 7.3 Band contract

The baseline candidate preserves distinct native `g`, `r`, and `z`. Technical eligibility requires reproducibly available three-band IMAGE support unless bounded cohort evidence shows that this makes the intended population infeasible and a separate prospective revision is frozen.

Missing-band state must be recorded rather than imputed. Color may not select cohort members. No grayscale, synthetic color, band averaging, or learned mixing is authorized.

## 8. Technical eligibility candidates

Technical eligibility may use only morphology-independent conditions. A future manifest may mark an observation technically eligible only when:

1. the exact `(RELEASE, BRICKID, OBJID)` identity and required provenance fields exist;
2. the provisional `BRICK_PRIMARY` identity rule passes;
3. required g/r/z native products exist and their literal identities are bound;
4. the requested catalog-centered support can be reproduced under the frozen WCS and edge contract;
5. immutable URLs/resource identities, checksums, versions, timestamps, and release/region/brick provenance are available;
6. required artifacts are readable, structurally valid, and uncorrupted;
7. observer products are present or carry an allowed explicit missingness state under the future metadata schema; and
8. grouping and label-firewall checks complete without ambiguity that the future policy forbids.

Technical ineligibility reasons must remain explicit and must not be collapsed into morphology labels.

The following are not automatic exclusion criteria:

- nonzero `MASKBITS` or any mask-family prevalence;
- low or heterogeneous NEXP;
- zero-support regions unless the frozen support contract makes the required image observation impossible;
- PSFSIZE or PSF variation;
- proximity to brick or primary boundaries;
- neighbors or blend complexity; or
- brightness, color, Tractor type, or model family.

Observer variation should be retained for audit and stratification where the image-observation contract remains technically valid. Any later exclusion requires a named prospective gate, unit of exclusion, rationale, and bias audit.

## 9. Observer-metadata contract

Every future observation record must carry the following metadata outside IMAGE:

| Family | Required content | Default role |
|---|---|---|
| Survey identity | region/survey, release, provider/version | Provenance and domain audit. |
| Catalog identity | RELEASE, BRICKID, OBJID, BRICKNAME, OBSERVATION_ID | Identity and joins. |
| Center/grid | RA, DEC, BX, BY, center provenance | Reproduction and discrepancy checks. |
| Resource identity | literal product/resource identities, hashes, sizes, retrieval provenance | Immutability and reproducibility. |
| Exposure/support | NEXP maps/summaries or explicit missingness, support/transition state | Observer audit and stratification. |
| Uncertainty | INVVAR identity and allowed diagnostics | Observer audit; no automatic S/N conversion. |
| Masks | raw MASKBITS plus NPRIMARY/optical/WISE/unknown family definitions and prevalence | Observer audit; no automatic pixel rewriting. |
| PSF | PSFSIZE and provider-PSF provenance/descriptors permitted by current contracts | Observer audit; no claim that PSFSIZE is complete PSF. |
| Geometry | WCS, cutout bounds, edge/full-support state, pixel scale | Reproduction and geometry audit. |
| Primary/duplicate | BRICK_PRIMARY, duplicate/group identifiers and uncertainty when resolved | Canonical identity and leakage prevention. |
| Missingness/failure | absent band/product/metadata, invalid resource, unsupported geometry, ambiguous group state | Explicit eligibility and bias accounting. |
| Detection provenance | documented source-detection pipeline/release selection function | Population provenance. |

Preservation in this contract does not make a field an encoder input. Any conditioning requires a separately frozen, separable, and ablatable representation specification consistent with the branch-readiness decision.

## 10. Population, related observations, and split contract

Multiple observations of one astrophysical object are allowed conceptually. Until an association contract exists, the project must not claim that technical source identities are unique astrophysical objects.

No `OBJECT_ID`, `OBSERVATION_ID`, nonprimary duplicate, related cutout support, blend/source group, or other member of one transitive `SPLIT_GROUP_ID` may cross development, training, validation, or holdout boundaries.

The prospective split design has four distinct partitions:

- **development:** pipeline construction, schema checks, technical fixtures, and training-only decisions;
- **training:** representation parameter fitting after separate authorization;
- **validation:** prospectively defined method/hyperparameter decisions without holdout access; and
- **holdout:** one-time frozen robustness/generalization evaluation under a later protocol.

Row-wise random splitting is prohibited. The final split contract must evaluate and freeze a morphology-independent spatial grouping policy using brick, larger sky cells, or another documented sky partition. The grouping scale must be justified from product overlap, repeated observations, and observer-condition correlation rather than representation outcomes.

Because north/south is a known observer domain, the split design must report region composition and observer-domain coverage in every partition. It must prospectively define both within-domain coverage and any cross-region stress evaluation. It may not silently randomize away region structure or balance regions using morphology.

The current state is:

```text
SPLIT_GROUPING_POLICY_RESOLVED = false
```

Resolution requires the duplicate/blend grouping contract, candidate spatial-group diagnostics, north/south coverage, observer-regime coverage, and a deterministic assignment algorithm frozen before representation outcomes.

## 11. Observer-domain coverage

Future cohort evidence must characterize, separately by split and region:

- north/south source and group counts;
- NEXP zero-support and transition regimes;
- INVVAR support/missingness diagnostics;
- NPRIMARY, optical, WISE, and unknown MASKBITS-family regimes;
- PSFSIZE and allowed provider-PSF regimes;
- BRICK_PRIMARY, edge, full-support, and ambiguous-group states; and
- product/band missingness and technical failures.

Coverage is an observer-domain requirement, not morphology balancing. The design sets no equal-count target. Any minimum coverage must be justified for the chosen method and planned shortcut probes before selection.

## 12. Six-window fixture firewall

The existing 2 technical development bricks and 6 observational windows remain `DEVELOPMENT_FIXTURES_ONLY`. They may validate pipeline plumbing, transformations, observer metrics, shortcut probes, and deterministic reproduction.

They do not automatically become cohort members. Any future source whose center or image support intersects a fixture window must be assigned to a fixture-overlap exclusion/group flag. The entire related `SPLIT_GROUP_ID` and prospectively defined surrounding spatial group must be barred from final holdout use. It may enter a development-only technical set only under an explicit future rule.

This prevents repeated fixture inspection and pipeline tuning from contaminating holdout evaluation. The rule does not reinterpret the windows as galaxies and does not modify S2 or any native fixture.

## 13. External-label firewall

The following are prohibited during cohort design, evidence gathering, materialization, preprocessing, split assignment, representation selection, and discovery analysis:

- Galaxy Zoo votes, vote fractions, classes, and subject-derived morphology fields;
- Hubble/T types and human morphology annotations;
- Zoobot morphology predictions or representations used as selection authority;
- Tractor `TYPE` and morphology/model-fit fields as eligibility or filtering inputs; and
- any morphology-derived catalog filter, support choice, balancing rule, threshold, or stopping rule.

External labels may be joined only after the cohort, splits, preprocessing, representations, and discovery analyses required by a separate interpretation protocol are frozen. The join must occur in an interpretation lockbox and cannot retroactively change any upstream decision.

The label-firewall design state is:

```text
LABEL_FIREWALL_RESOLVED = true
```

Implementation enforcement and audit evidence remain required before materialization.

## 14. Sample-size decision framework

The frozen state is:

```text
SAMPLE_SIZE_REQUIRES_METHOD_SPECIFICATION
```

No universal sample count is defined. A future method specification must justify counts from independent grouping units, trainable complexity, learning/stability curves, observer-domain coverage, split requirements, and uncertainty targets.

| Method/evaluation family | Evidence required to set minimum counts | Scale implication that must be measured |
|---|---|---|
| PCA/classical baseline | Frozen feature dimensionality, retained-component rule, covariance/spectrum stability across grouped resamples and observer domains. | Independent samples must support stable covariance/components; no number is inferred here. |
| Convolutional autoencoder | Architecture capacity, reconstruction objective, learning curves, seed stability, holdout reconstruction behavior, shortcut probes. | Count depends on capacity and scene diversity; reconstruction alone is not morphology validity. |
| BYOL-like SSL | Backbone/projector/teacher contract, view count, augmentation validity, batch behavior, collapse controls, seed and learning-curve stability. | No negative pairs, but data diversity and stable teacher/student training remain method-dependent. |
| Contrastive SSL/SimCLR-like | Positive-view semantics, negative sampling unit, false-negative risk, batch/queue design, domain balance, grouped splits. | Negative diversity and batch/queue scale can set strong count requirements. |
| Non-contrastive SSL/Barlow/DINO-like | Objective-specific batch statistics or teacher/student dynamics, collapse controls, multi-view policy, seed stability. | Data and batch dependence varies by objective and architecture. |
| MAE-like SSL | Patch/mask policy, reconstruction target, masking rate, image support, capacity, learning curves, observer-artifact reconstruction audit. | Requires enough observations to separate reusable structure from pixel/observer reconstruction shortcuts. |
| Observer-shortcut probes | Frozen target definitions, independent group counts per observer regime, class prevalence/range, null controls, uncertainty precision. | Rare domains and grouped effective sample size, not raw rows, determine feasibility. |
| Clustering/manifold analysis | Frozen representation, distance/normalization, method parameters, stability across seeds/resamples, null baselines, domain-confound audit. | Counts must support stable local/global structure without using labels to tune. |
| Holdout robustness | Independent object/spatial groups, observer-domain coverage, predeclared effect/uncertainty target, one-time evaluation policy. | Holdout size follows precision and domain coverage, not computational convenience. |

No count may be chosen merely to fit current compute. The future decision must also account for data-transfer, storage, and human-execution governance after scientific requirements are set.

## 15. Compact methods review

This review records candidate assumptions and risks. It does not select a method.

| Method/family | Required input | Augmentation assumptions | Negative pairs | Batch/data-scale dependence | Complexity | Natural observer-shortcut risks | Compatibility with current invariance decisions | Sample-size implication | Later disposition |
|---|---|---|---|---|---|---|---|---|---|
| Mohale & Lochner astronomy BYOL precedent | Survey galaxy images under their published preprocessing; exact replication contract still required. | BYOL views; astronomy-specific validity of each augmentation must be reviewed. | No explicit negatives. | Data diversity, batch, teacher/student dynamics, and seeds matter. | Moderate/high deep SSL plus downstream clustering/anomaly tools. | Zoom, companions, artifacts, survey/acquisition cues. | Candidate precedent; project B00/B01 first wave and observer probes must replace assumed invariances. | Requires method-specific learning/stability evidence. | Include in full literature/replication review; no authority over cohort selection. |
| Wei et al. contrastive astronomy precedent | Galaxy images; exact bands/support/preprocessing require bibliographic binding. | Positive-pair transformations define intended invariances and must be scientifically audited. | Yes or contrastive equivalents, subject to the cited method. | Negative diversity, batch/queue design, and false negatives may be material. | Moderate/high. | Survey domain, brightness, orientation, neighbors, artifacts, false negatives between related sources. | Candidate comparison after exact method binding; no unfrozen augmentation. | Requires bounded method-specific evidence. | Include after exact paper/code/dataset contract is frozen. |
| Supervised Zoobot representation | Inputs/preprocessing defined by its supervised training provenance. | Supervised pipeline-specific. | Method-dependent. | Depends on pretrained artifact. | Low for inference, high upstream. | Label ontology, training-survey, morphology, and acquisition-domain leakage. | Incompatible as training or selection authority; possible post-freeze comparator only. | Does not set this project's training count. | Interpretation/comparator lockbox only. |
| BYOL | Multiview images and online/target networks. | Strongly dependent on valid paired views. | No. | Batch, EMA, capacity, data diversity, seeds. | High relative to PCA/AE. | Any stable observer cue shared across views; invalid invariance can be learned. | Candidate only after branch and augmentation specification. | Learning/collapse/stability curves required. | Candidate, not selected. |
| SimCLR | Paired augmented views and encoder/projector. | Positive views must preserve the intended scientific relation. | Yes, in-batch negatives. | Often strongly batch/negative/data dependent. | High. | False negatives, survey-domain separation, augmentation fingerprints. | Candidate only with grouped negatives and frozen transformations. | Negative diversity and batch evidence required. | Candidate, not selected. |
| Barlow Twins | Paired views and cross-correlation objective. | Same paired-view scientific burden as other SSL. | No explicit negatives. | Batch statistics and feature dimensionality matter. | High. | Observer variables may become decorrelated or retained without being detected absent probes. | Candidate with explicit observer probes and frozen views. | Batch/statistical stability evidence required. | Candidate, not selected. |
| DINO | Multi-view images with student/teacher self-distillation. | Crop/scale/multi-view rules can change object support and are currently unresolved. | No explicit negatives. | Teacher dynamics, crops, data scale, and architecture matter. | High. | Crop/scale, survey domain, background, artifacts, and attention shortcuts. | Currently limited by unresolved object support and scale/crop semantics. | Large-model/data feasibility must be justified. | Deferred until support and augmentation contracts exist. |
| MAE | Patchified images with masked reconstruction. | Masking is not geometric invariance but changes visible support. | No. | Capacity, mask ratio, patch size, image diversity. | High. | Reconstruction of noise, PSF, masks, backgrounds, and survey texture. | Candidate only with B00 provenance and observer reconstruction probes. | Learning/stability and shortcut evidence required. | Candidate, not selected. |
| PCA | Frozen vectorization/features and scaling. | None unless preprocessing is added explicitly. | No. | Covariance estimation depends on effective independent count. | Low. | Brightness, background, edge, PSF, mask, and survey variance can dominate components. | Required simple baseline once representation input is frozen. | Component/covariance stability determines count. | Include later as baseline. |
| Convolutional autoencoder | Images and reconstruction objective. | None required; optional transforms need separate authority. | No. | Capacity and scene diversity matter. | Moderate. | Pixel fidelity can prioritize background, PSF, artifacts, and high-flux structures. | Candidate simple learned baseline with observer probes. | Learning/seed/reconstruction stability determines count. | Include later as baseline. |
| Raw/global technical summaries | Prospectively legitimate non-morphological summaries only. | None. | No. | Low. | May directly encode survey, depth, masks, PSF, or brightness. | Useful as shortcut/null baselines, never as morphology truth. | Observer-domain coverage sets count. | Include only with closed feature schema. |

Before architecture selection, the full review must bind exact papers, code/artifact versions where used, datasets, preprocessing, augmentations, splits, objectives, scale, and reported failure modes. Existing methods must be compared against project requirements before any project-specific encoder is proposed.

## 16. Gate ledger before materialization

| Gate | Current state | Closure evidence required |
|---|---|---|
| `OBJECT_IDENTITY_CONTRACT_RESOLVED` | `OPEN` | Canonical OBSERVATION_ID serialization, official duplicate semantics, OBJECT_ID/SPLIT_GROUP_ID association contract, and bounded schema validation. |
| `GALAXY_ELIGIBILITY_POLICY_RESOLVED` | `OPEN` | Bounded A/B/C comparison with availability, unknowns, cross-match semantics, north/south/depth coverage, and selection-bias audit. |
| `BLEND_GROUPING_SEMANTICS_RESOLVED` | `OPEN` | Official field semantics plus bounded actual-schema/cardinality inspection and transitive grouping rule. |
| `CUTOUT_SUPPORT_POLICY_RESOLVED` | `OPEN` | Frozen support option/value(s), edge/full-support rules, WCS/center contract, truncation and observer-dominance analysis. |
| `SPLIT_GROUPING_POLICY_RESOLVED` | `OPEN` | Duplicate/object/spatial grouping, deterministic assignment, fixture exclusion, region/domain coverage, and leakage tests. |
| `OBSERVER_METADATA_CONTRACT_RESOLVED` | `OPEN` | Versioned schema, missingness states, product bindings, allowed diagnostics, integrity rules, and bounded validation. |
| `TECHNICAL_ELIGIBILITY_CONTRACT_RESOLVED` | `OPEN` | Closed eligibility fields, failure reasons, no forbidden field access, and deterministic validation. |
| `LABEL_FIREWALL_RESOLVED` | `DESIGN_RESOLVED_IMPLEMENTATION_PENDING` | Enforced allowlist/denylist, audit log, lockbox boundary, and synthetic tripwire tests. |
| `SAMPLE_SIZE_POLICY_RESOLVED` | `OPEN` | Method-specific effective group counts, learning/stability evidence, observer-domain coverage, split and uncertainty requirements. |
| `METHODS_REVIEW_COMPLETE` | `PARTIAL` | Exact bibliography/code/data binding and cohort-specific comparison of astronomy precedents, generic SSL, shortcut methods, and simple baselines. |
| `OFFICIAL_DR9_DOCUMENTARY_BINDING_RESOLVED` | `OPEN` | Exact official URLs/pages, versions, timestamps, archived content hashes, and reconciled field semantics. |

Materialization is blocked while any required gate is `OPEN` or `PARTIAL`. Closing the design document does not close these execution gates.

## 17. Exact next stage

Because galaxy eligibility remains unresolved, the sole immediate next stage is:

**Stage ID:** `OC3-GALAXY-ELIGIBILITY-BOUNDED-EVIDENCE-001`

**Stage name:** GALAXY ELIGIBILITY BOUNDED EVIDENCE

Its prospective purpose is to:

1. bind the exact official DR9 catalog/detection/primary/field documentation;
2. bind the exact independent spectroscopic and astrometric authorities eligible for options B and C;
3. define morphology-independent cross-match identities, positive/negative/unknown states, ambiguity handling, and failure rules;
4. inspect only the minimum bounded metadata needed to estimate option availability, north/south/depth coverage, and selection-function differences;
5. determine whether A, B, C, or a prospectively justified combination can become the cohort eligibility policy; and
6. report unresolved duplicate/blend and split-group implications without reading pixels or morphology labels.

This stage must first receive its own frozen specification, resource caps, allowlists, label firewall, exact outputs, and human authorization for any network or catalog access. It is not a large cohort materialization stage and may not download Tractor catalogs under this design.

`COHORT_METADATA_BOUNDED_PILOT` remains downstream and unauthorized until the galaxy-eligibility decision and the other required gates are resolved.

## 18. Zero-execution declaration

Creating this design performed:

- zero cohort materialization;
- zero Tractor catalog downloads;
- zero source or object selection;
- zero cutout creation or pixel reads;
- zero changes to the six technical fixtures;
- zero model or encoder operations;
- zero embeddings, clustering, anomaly, or morphology operations;
- zero label or morphology-prediction access;
- zero image displays or plots; and
- zero network requests.

The design-completion state is:

```text
SCIENTIFIC_OBJECT_AND_COHORT_DESIGN_FROZEN
```

It documents the scientific unit and unresolved gates. It does not authorize objects, cohort materialization, representation learning, or scientific morphology claims.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
