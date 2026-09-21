# OC3 Preprocessing and Invariance Decision 001

## 1. Status, scope, and authority

**Document ID:** `OC3-PREPROCESSING-AND-INVARIANCE-DECISION-001`

**Status:** FROZEN PROSPECTIVE DECISION

**Applies to:** the two-object OC-3 technical pilot and its six frozen native IMAGE windows

**Evidence source stage:** `OC3-OBSERVATIONAL-CONFOUND-AUDIT-001`

**Execution performed by this decision:** NONE

**Network access authorized by this decision:** NONE

**Model, embedding, clustering, anomaly, or morphology analysis authorized:** NONE

This document freezes preprocessing and invariance decisions from the completed OC-3 observational-confound audit. It specifies a native observational baseline, prospective controlled branches, and questions that must remain open. It does not implement or execute any transformation.

The decision is bound to the following frozen evidence:

| Evidence | SHA-256 |
|---|---|
| `OC3_OBSERVATIONAL_CONFOUND_AUDIT_SPEC.md` | `8c997a2eb4a58c50eb72604ab7d1c9a8ece61863ad2af96640bc7569580091c3` |
| `OC3_OBSERVER_AUDIT_SUMMARY.json` | `36e10de7f76c781d6c305157fa927e49a8a241a54fe082bd37fe1f9fe941a3c7` |
| `OC3_OBSERVER_FEATURE_MATRIX.csv` | `f29e1f0f76dc9e018ed52624fe3c7b3a91461b046897c3acbf9079123265c31b` |
| `OC3_OBSERVER_AUDIT_SLOT_METRICS.csv` | `993d75eca71331e9fc8ea223d24f1ee5335541f0b8cec61817b3f2d2185ecf5e` |
| `OC3_OBSERVER_AUDIT_CONTRASTS.csv` | `3864720c14fbe42910697daf1b0a8aab85b778c41cf2384fb2ae7592433cdd79` |
| `OC3_OBSERVER_AUDIT_TERMINAL.json` | `3740cac96ed138e8ab587b62bfcef8ad8222bae1c21de5730f52d61ca2cae3b0` |

The terminal audit state is `OBSERVATIONAL_CONFOUND_AUDIT_COMPLETED`; its descriptive state is `CONFOUND_VARIATION_OBSERVED`. Those states establish that the measurements completed and that observer-condition variation exists. They do not establish that any variable is morphology, nuisance, harmless, or suitable for removal.

The decision categories in this document are exactly:

- `PRESERVE`: retain the quantity or native observational state without transforming it in the baseline.
- `CONDITION_ON`: retain the quantity outside IMAGE and test it as explicit side information; this does not make it an automatic encoder input.
- `TEST_AS_NUISANCE`: compare frozen controlled branches before deciding whether invariance is scientifically appropriate.
- `EXCLUDE_ONLY_UNDER_EXPLICIT_GATE`: exclusion is unavailable by default and requires a later prospective gate with a stated scientific criterion.
- `DEFER`: the evidence or semantics needed to define a defensible operation do not yet exist.
- `PROHIBITED_FOR_NOW`: the operation is incompatible with the present evidence or stage and must not be performed.

Each decision row below has exactly one of these categories. A raw artifact can be preserved for audit while a separate candidate use of that artifact has another decision category.

## 2. Frozen observational evidence

The following table reports observations, not causal interpretations.

| Evidence family | Frozen observation | What it establishes | What it does not establish |
|---|---|---|---|
| NEXP support | South windows contain no NEXP=0 pixels. N1 zero-exposure fractions are 3.5334%, 3.2089%, and 1.3641% in g/r/z. N2-z has 0.528814% zero exposure. N3-g/r are constant within their windows; N3-z has two levels. Transition counts vary by slot and band, including 503/326/579 for N1 and 144/0/644 for S3. | Exposure support and discontinuity vary across frozen windows, bands, and survey regions. | That NEXP is pure nuisance; that zero support may be filled; or that discontinuities are unrelated to astrophysical structure. |
| INVVAR | All observed values are finite and nonnegative. Zero INVVAR coincides with zero-support cases in N1-g/r/z and N2-z. Relative dispersion varies, including relative IQR 0.7231856 for N3-z, 0.5166994 for S3-g, and 0.4449151 for S3-z. | Per-pixel uncertainty/support information is heterogeneous and is linked to observed exposure support in the zero cases. | Gaussian errors, calibrated likelihood semantics for a future loss, or permission to convert IMAGE into S/N. |
| MASKBITS | S1 is all zero. S2 has NPRIMARY fraction 0.519379845 and zero fraction 0.480620155. S3 has optical-mask fraction 0.002463794. N1 has optical 0.405684755, WISE 0.344630731, and zero 0.391803377. N2 has optical 0.114476293, WISE 0.016345172, and zero 0.884141578. N3 has WISE 0.545820564 and zero 0.454179436. Unknown-bit fraction is zero in all frozen windows. | The frozen sample contains distinct NPRIMARY, optical, and WISE mask regimes. | That all set bits are fatal, that masked IMAGE pixels should be zeroed or interpolated, or that an empty unknown-bit set generalizes beyond this pilot. |
| PSFSIZE | Spatial constancy and variation differ by slot and band. N3 has exact audit variance `V=0.8293932498304606` with absolute difference zero. Relative ranges include 0.253075439 for N3-z, 0.123886386 for S3-g, 0.10243432 for S2-r, and 0.078182382 for N1-z. | Scalar seeing metadata varies by region, band, and spatial point in the frozen evidence. | A complete PSF operator, a sufficient correction statistic, or a homogenization target. |
| Coadd PSF responses | All decoded samples are finite. Every slot/band has three distinct hashes across P0/P1/P2; raw peaks remain centered with maximum displacement zero. South native shapes are 63x63 in g/r/z; north shapes are 31x31 in g/r and 63x63 in z. Physical normalized PSF shape metrics are deferred. | Native PSF responses vary spatially and retain provider-specific native shapes. | Cross-response physical normalization, flux-preserving PSF matching, or permission to resize north and south kernels to a common array shape. |
| Brick geometry and primary status | S1 and N1 are `ALL_PRIMARY`. S2 is `MIXED_PRIMARY`, with primary fraction 0.480620155, nonprimary fraction 0.519379845, 129 boundary transitions, and center-to-boundary distance 2.5 pixels. S3, N2, and N3 are observed all-primary. | The S2 IMAGE window crosses a real provider primary-boundary condition represented in the native evidence. | That nonprimary pixels are invalid for this task or that a primary-only crop is scientifically preferable. |
| WCS geometry | Local pixel scale is approximately 0.262 arcsec/pixel in all windows. Relative pixel-area variation is small, approximately 5.15e-7 to 1.47e-6. | The frozen windows share a close local angular scale and preserve measurable WCS geometry. | Physical-size equivalence, object-scale equivalence, or permission to discard WCS. |
| IMAGE values | Tier-B IMAGE access found finite mixed scenes and recorded descriptive statistics only. | Native g/r/z arrays exist and can serve as the observational reference. | Morphological content, object extent, centering quality, background semantics, or a preferred contrast transformation. |

The audit did not run background estimation, object segmentation, morphology measurement, image display, plotting, preprocessing, augmentation, representation learning, or optimization. No decision below upgrades absent evidence into an observation.

## 3. Frozen decisions

| ID | Candidate variable or operation | Decision | Frozen rationale and operational consequence |
|---|---|---|---|
| D01 | Native g/r/z IMAGE arrays | `PRESERVE` | The unmodified provider values and band separation are the only observational reference. They remain the baseline encoder input when an encoder stage is later authorized. |
| D02 | NEXP as observer metadata | `TEST_AS_NUISANCE` | Exposure patterns vary substantially. Keep NEXP external to IMAGE and compare hidden, conditioned, stratified, and controlled-perturbation uses before claiming invariance. |
| D03 | Filling, interpolating, or silently rewriting NEXP=0 IMAGE support | `PROHIBITED_FOR_NOW` | Zero-support structure is observed and coincides with zero INVVAR in the relevant windows. At least one branch must retain every observed discontinuity. |
| D04 | INVVAR as explicit side information | `CONDITION_ON` | Retain the unmodified array outside IMAGE and define a conditioning branch. Baseline encoder input remains IMAGE-only. |
| D05 | INVVAR-aware loss or statistical weighting | `TEST_AS_NUISANCE` | A later controlled comparison may test whether uncertainty-aware weighting changes results, but the loss semantics and representation stage must first be frozen. |
| D06 | Multiplying IMAGE by INVVAR, converting to S/N-only input, or assuming Gaussian noise | `PROHIBITED_FOR_NOW` | These operations change the observable, discard flux information, or assert unverified distributional semantics. |
| D07 | MASKBITS split into NPRIMARY, optical, WISE, and unknown-bit channels | `CONDITION_ON` | Preserve raw IMAGE and raw bit values. Any conditioning must use separately documented bit families; unknown bits remain explicit even though none were observed. |
| D08 | Excluding observations or pixels because a MASKBITS family is present | `EXCLUDE_ONLY_UNDER_EXPLICIT_GATE` | Prevalence alone is not a scientific invalidity rule. A later prospective gate must name the bit family, unit of exclusion, and evidence threshold. |
| D09 | PSFSIZE as scalar observer metadata | `CONDITION_ON` | PSFSIZE variation is observed and can be supplied in a separate conditioning branch. It is not a substitute for the spatial PSF response. |
| D10 | Raw coadd PSF responses, native shapes, and provider provenance | `PRESERVE` | Retain the exact acquired responses and their north/south shapes for audit and future controlled use. Do not resize them merely to align tensor shapes. |
| D11 | PSF matching or homogenization | `DEFER` | Physical normalization and flux-preserving matching semantics are unresolved. A perturbation design may be specified, but homogenized science inputs cannot become a baseline until those semantics and a target rule are prospectively frozen. |
| D12 | The S2 mixed-primary boundary in the native window | `PRESERVE` | It is part of the frozen observational evidence and must remain visible in the native baseline and at least one comparative branch. |
| D13 | Primary-only window or cohort rule | `EXCLUDE_ONLY_UNDER_EXPLICIT_GATE` | A future rule requires a separate scientific justification and must be tested without rewriting the current development evidence. |
| D14 | Generic background subtraction | `DEFER` | The audit did not establish background semantics, an estimator, spatial scale, masking policy, or information-loss bound. |
| D15 | Multiplicative intensity scaling, additive offsets, and a robust global scale | `TEST_AS_NUISANCE` | These must be separate, parameter-frozen branches. Each removes or changes different information and must be compared with unscaled IMAGE. |
| D16 | Per-image min-max scaling or histogram equalization | `PROHIBITED_FOR_NOW` | They erase or remap brightness/contrast information without evidence that it is irrelevant and can amplify support or mask discontinuities. |
| D17 | Distinct g/r/z bands and their native order | `PRESERVE` | Color and band-specific structure are observed inputs. Color is neither declared morphology nor declared nuisance. |
| D18 | Grayscale, single-band, false-color, or learned multiband reductions | `TEST_AS_NUISANCE` | Each is an explicit ablation or representation branch with a stated information loss; none may silently replace g/r/z. |
| D19 | Rotation invariance | `TEST_AS_NUISANCE` | Native orientation, controlled rotations, and their effects must be compared. Orientation is not yet shown to be irrelevant. |
| D20 | Reflection invariance | `TEST_AS_NUISANCE` | Reflections must be tested separately from rotations. Chirality is not assumed to be irrelevant. |
| D21 | Translation augmentation, recentering, centroid alignment, or horizontal alignment | `PROHIBITED_FOR_NOW` | Object support, object center, segmentation, and centering semantics have not been established for the current mixed-scene windows. |
| D22 | Scale invariance, resizing, or physical-size normalization | `DEFER` | Angular WCS scale is known locally, but object size and distance are not. Any later scale test must jointly account for PSF, pixel scale, interpolation, and explicit information loss. |
| D23 | WCS and native geometry metadata | `PRESERVE` | Retain WCS externally with each IMAGE window. Small observed pixel-area variation does not authorize discarding it or claiming physical-scale equivalence. |
| D24 | Human/Galaxy Zoo labels, vote fractions, morphological names, or label-derived selection | `PROHIBITED_FOR_NOW` | These remain behind the interpretation firewall and cannot define preprocessing, augmentation, nuisance tests, branch selection, thresholds, or evaluation at this stage. |

### 3.1 Closed variable decision register

This register is the closed decision output for the required observational families. “Allowed next experiment” means a prospectively specified comparison; it is not execution authorization.

| Variable or operation | Evidence | Decision category | Allowed next experiment | Prohibited action | Reason | Revisit condition |
|---|---|---|---|---|---|---|
| Native IMAGE | Finite, mixed-scene g/r/z windows exist; Tier-B summaries contain no morphology finding. | `PRESERVE` | `B00` integrity/reference replay only; later branches compare against it. | Mutate, replace, or interpret IMAGE as morphology in this stage. | It is the only validated observational reference. | Only after a frozen branch comparison supports a stated observational-equivalence claim. |
| NEXP | Zero-support and transition structure vary across slots/bands; south has no zeros, while N1 and N2-z contain zeros. | `TEST_AS_NUISANCE` | `B09` stratification, `B10` conditioning, and eventually `B11` physically controlled perturbation. | Alter IMAGE from NEXP, silently fill unsupported pixels, or erase all discontinuity branches. | Coverage is observer information with demonstrated heterogeneous structure. | After predeclared hidden/conditioned/stratified results and a valid joint perturbation model exist. |
| INVVAR | Finite, nonnegative; zeros track observed zero support; dispersion varies strongly. | `CONDITION_ON` | `B04` side-channel conditioning; later separately frozen weighting/loss sensitivity. | Multiply IMAGE by INVVAR, replace IMAGE with S/N, or assume complete Gaussian-noise semantics. | It describes measurement support/uncertainty without proving a noise likelihood. | After uncertainty semantics, objective, and all required comparator branches are frozen and tested. |
| MASKBITS | NPRIMARY, optical, and WISE prevalence differ; no unknown bits were observed. | `CONDITION_ON` | `B05` family-separated conditioning; `B06` only under its explicit gate. | Treat all nonzero bits as unusable; zero, interpolate, inpaint, or discard them in baseline. | Provider flags have distinct meanings and may encode observer context or real-signal overlap. | After family-specific sensitivity evidence and a prospective corruption/exclusion gate. |
| PSFSIZE | Constant and varying band/slot cases coexist; N3-z varies strongly; N3 audit variance reproduced exactly. | `CONDITION_ON` | `B07` scalar conditioning with an ablatable path. | Treat PSFSIZE as the complete PSF or select/drop examples from its value. | It is a useful scalar observer variable but not a full response model. | After conditioning sensitivity is measured against native IMAGE and full PSF provenance. |
| Coadd PSF | P0/P1/P2 hashes differ; peaks stay centered; native north/south shapes differ; normalized metrics are deferred. | `PRESERVE` | Specify `B08` only after physical normalization and matching semantics are validated. | Default homogenization, implicit deconvolution, or silent resizing to a common array shape. | The acquired responses are evidence; a scientifically valid common operator is not yet defined. | After target, normalization, flux, boundary, noise-covariance, and validation rules are frozen. |
| Background | No estimator, background scale, gradient treatment, or low-surface-brightness separation was audited. | `DEFER` | `B02` controlled offset sensitivity; later separate background-estimator comparisons. | Generic local background subtraction or outcome-tuned sky removal. | An additive sensitivity test is not a justified estimate of astronomical background. | After a prospective authority/specification separates sky, gradients, and astronomical structure. |
| Brightness/contrast | Native IMAGE is available, but no flux/contrast transformation was validated. | `TEST_AS_NUISANCE` | `B01`, `B02`, and `B03` as separate frozen branches, each against `B00`. | Per-image min-max, histogram equalization, or default contrast normalization. | Each operation removes different photometric information and can introduce leakage or artifacts. | After the perturbation pilot quantifies value/support effects and states the information removed. |
| Bands | g/r/z are distinct native observational channels with band-specific support and observer metadata. | `PRESERVE` | `B14` explicit single-band, grayscale, false-color, or learned-multiband ablations. | Collapse the baseline to grayscale or assume color is morphology/nuisance. | Band identity and color may contain signal, confounding, or both. | After prospectively frozen band-ablation evidence exists. |
| Rotation | No rotation invariance was tested; WCS, masks, and support would require synchronized handling. | `TEST_AS_NUISANCE` | `B12`, retaining native orientation and freezing interpolation/padding. | Automatic rotation augmentation, outcome-tuned angles, or horizontal alignment. | Orientation relevance and resampling loss are unresolved. | After native-versus-rotation robustness and information-loss evidence is frozen. |
| Reflection | No reflection invariance was tested and handedness relevance is unresolved. | `TEST_AS_NUISANCE` | `B13`, axis-specific and separate from rotation. | Pool reflection with rotation or assume chirality is irrelevant. | Reflection can erase handedness and has a distinct scientific claim. | After native-versus-reflection evidence under consistent geometry exists. |
| Translation/recentering | Object support, centroid, segmentation, and centering semantics were not established. | `PROHIBITED_FOR_NOW` | None in the next pilot; a future scientific-object stage may specify centering. | Move frozen coordinates, recenter, centroid-align, or translate current windows. | A move could change the scene and field of view without a defined object. | After a separate object-definition and extraction protocol is frozen. |
| Scale/resolution | Local angular scale is close across windows, but object size, distance, and physical scale are unknown. | `DEFER` | A later explicit angular/physical rescaling branch with PSF/pixel-scale controls. | Impose scale invariance, resize by convention, or claim physical-size equivalence. | Angular size, redshift, morphology, PSF, and interpolation may be entangled. | After object support and distance semantics exist and information loss can be assessed jointly with PSF. |
| WCS/geometry | Pixel scale is about 0.262 arcsec/pixel and local area variation is small but measurable. | `PRESERVE` | Geometry-consistency checks for any later transformation with defined WCS semantics. | Discard WCS, alter coordinates, or infer physical-scale invariance from the small variation. | WCS is provenance and the basis for validating spatial operations. | Only when a later transformation has an explicit, validated WCS update rule. |
| BRICK_PRIMARY/boundary | S2 is mixed-primary with a boundary 2.5 pixels from center; other observed windows are all-primary. | `PRESERVE` | Keep S2 native in `B00`; `B15` may run only under a separate primary-only gate. | Silently remove the boundary, rewrite S2, or generalize a primary-only rule from this pilot. | The boundary is real provider geometry and part of the frozen development evidence. | After a prospective scientific-cohort gate defines and justifies the unit of exclusion. |

## 4. Native observational baseline

The mandatory reference branch is `B00_NATIVE_IMAGE_ONLY`:

1. IMAGE consists of the unchanged native provider g/r/z values in the frozen native windows.
2. No intensity normalization, background subtraction, masking, filling, interpolation, PSF matching, resizing, recentering, rotation, or reflection is applied.
3. Band order and native pixel geometry are preserved.
4. INVVAR, NEXP, MASKBITS, PSFSIZE, coadd-PSF provenance/responses, WCS, survey region, brick identity, and primary geometry remain linked externally.
5. These observer variables are **PRESERVED FOR AUDIT**. They are **not automatically supplied as ENCODER INPUT**.
6. The baseline encoder input, if a later encoder stage is authorized, is IMAGE g/r/z only. The existence of metadata does not silently enlarge that input.

| Quantity | Preserved for audit | Baseline encoder input | Baseline role |
|---|---:|---:|---|
| Native IMAGE g/r/z | Yes | Yes | Unchanged observational reference. |
| INVVAR | Yes | No | Linked uncertainty/support record. |
| NEXP | Yes | No | Linked exposure/support record. |
| MASKBITS and decoded families | Yes | No | Linked quality/provenance record. |
| PSFSIZE | Yes | No | Linked scalar observer metadata. |
| Raw coadd PSF response and provenance | Yes | No | Linked spatial response evidence in native shape. |
| WCS and pixel geometry | Yes | No | Linked coordinate and scale evidence. |
| Brick and BRICK_PRIMARY geometry | Yes | No | Linked provider ownership/boundary evidence. |
| Human or morphology labels | No access in this stage | No | Interpretation firewall. |

No transformed branch may become the implicit reference because its embeddings appear visually cleaner, more compact, or easier to cluster. Any replacement of `B00_NATIVE_IMAGE_ONLY` requires a later prospective decision grounded in a frozen comparison.

A preprocessing operation is justified only if it states its observational-equivalence claim in advance and survives the corresponding frozen robustness test.

## 5. Prospective experiment branch matrix

The matrix defines questions and controls; it does not authorize execution. Parameters, seeds, sampling, interpolation, padding, and evaluation measures must be frozen in the next applicable specification before any branch runs. In every branch, the original arrays and observer metadata remain immutable and addressable.

| branch_id | question | IMAGE transformation | observer metadata available | observer metadata supplied to encoder | augmentation/invariance | expected information removed | confound addressed | new confound potentially introduced | comparison baseline | failure criterion |
|---|---|---|---|---|---|---|---|---|---|---|
| `B00_NATIVE_IMAGE_ONLY` | What does the unchanged observational record provide? | None; native g/r/z values and geometry. | All frozen observer metadata. | None. | None. | None by design. | None removed; this is the reference. | Observer shortcuts remain possible. | Self/integrity replay. | Any byte/value/shape/WCS mutation, unsupported pixel rewrite, or metadata leakage into IMAGE. |
| `B01_MULTIPLICATIVE_FLUX_SCALE` | How sensitive are later results to a prospectively fixed multiplicative intensity factor? | Multiply all bands by a frozen factor rule without per-image fitting. | All. | None. | Brightness perturbation, not declared invariance. | Absolute flux scale if the factor is hidden downstream. | Multiplicative photometric sensitivity. | Unrealistic flux distribution or coupling to clipping/dtype. | `B00`. | Factor depends on labels/results; clipping/nonfinite values appear; or operation cannot be exactly recorded/reversed where promised. |
| `B02_ADDITIVE_OFFSET` | How sensitive are later results to a controlled additive level? | Add a frozen bandwise or common offset; no estimated background subtraction. | All. | None. | Offset perturbation, not background correction. | Absolute zero level if hidden downstream. | Additive background sensitivity. | Nonphysical negative/positive regimes or support-edge amplification. | `B00`. | Offset is fitted after viewing outcomes; it changes support semantics; or creates nonfinite/clipped values. |
| `B03_ROBUST_GLOBAL_SCALE` | Does one training-reference-derived global scale improve numerical conditioning without per-object contrast normalization? | Divide by a single prospectively frozen scale per band or one common scale; never per image. | All. | None. | Numerical scaling only. | Absolute unit magnitude; relative within-image and cross-object values remain only if one shared rule is used. | Dynamic range and optimizer conditioning in a later model stage. | Dataset-level leakage or regional/band imbalance encoded by the scale estimate. | `B00`. | Scale uses evaluation objects, labels, per-image statistics, or outcome-based tuning; zeros/nonfinite behavior changes. |
| `B04_INVVAR_CONDITIONING` | Does explicit uncertainty/support context reduce reliance on unobserved noise differences while preserving flux? | None. | All, with INVVAR explicit. | INVVAR through a separately specified conditioning path; IMAGE remains g/r/z. | No geometric invariance. | None from IMAGE; the model may learn to discount uncertain regions. | Heteroscedasticity and zero-support awareness. | Direct survey/coverage shortcut through INVVAR. | `B00`. | INVVAR is multiplied into IMAGE, treated as a label, assumed Gaussian without validation, or conditioning path cannot be ablated. |
| `B05_MASK_FAMILY_CONDITIONING` | Can explicit mask-family context separate provider flags from IMAGE structure? | None. | Raw MASKBITS plus separate NPRIMARY, optical, WISE, and unknown channels. | Separate frozen mask-family conditioning path. | No masking invariant is presumed. | None from IMAGE. | Provider-mask shortcut made measurable/explicit. | Mask prevalence can itself reveal region, brick, or location. | `B00`. | Families are conflated; unknown bits are dropped; IMAGE is zeroed/interpolated; or branch cannot be ablated by family. |
| `B06_CONTROLLED_MASK_REMOVAL` | Under an explicit later gate, what is lost when one named mask family is removed or inpainted by a predeclared rule? | One prospectively named family only, using a frozen operation and retaining an untouched comparator. | All raw masks and original IMAGE. | None by default. | Candidate robustness test only. | Pixel values/support in the named mask family; possibly real signal. | Sensitivity to one provider flag family. | Inpainting artifacts, edge cues, unequal removal by region, and morphology erasure. | `B00` and `B05`. | No explicit gate; more than one family changes; S2 boundary is silently removed; or information loss cannot be quantified. |
| `B07_PSFSIZE_CONDITIONING` | Is scalar seeing information useful as explicit observer context? | None. | PSFSIZE and full PSF provenance available. | PSFSIZE only through a separate conditioning path. | No PSF invariance presumed. | None from IMAGE. | Scalar seeing variation. | Region/band/location shortcut; false belief that PSFSIZE fully specifies the PSF. | `B00`. | PSFSIZE replaces full provenance, is used to choose/drop objects, or branch lacks a no-PSFSIZE ablation. |
| `B08_PSF_PERTURBATION_OR_MATCHING` | After PSF normalization semantics are frozen, how sensitive are results to a controlled PSF change? | Prospectively specified convolution/matching only; native branch retained. | Raw PSF responses, PSFSIZE, WCS, provenance. | None unless separately frozen. | Candidate PSF robustness; not default homogenization. | High-frequency spatial information and possibly photometric information. | PSF-dependent representation. | Correlated noise, boundary artifacts, north/south shape normalization artifacts, flux bias. | `B00` and `B07`. | Physical normalization/target/flux rule unresolved; deconvolution is implied; native shapes are silently resized; or validation cannot bound information loss. |
| `B09_NEXP_STRATIFICATION` | Do results differ across predeclared exposure-support strata while IMAGE remains unchanged? | None. | NEXP plus all metadata. | None. | Stratified comparison; no invariance claim. | None. | Exposure-depth/support association. | Small-stratum instability and region leakage. | `B00`. | Strata are chosen from outcomes; unsupported pixels are filled; discontinuities disappear; or membership uses labels. |
| `B10_NEXP_CONDITIONING` | Does explicit NEXP context alter reliance on exposure discontinuities? | None. | NEXP plus all metadata. | NEXP through a separate conditioning path. | No invariance presumed. | None from IMAGE. | Exposure/support awareness. | Strong survey/brick shortcut through the NEXP pattern. | `B00` and `B09`. | NEXP changes IMAGE, is conflated with INVVAR, or lacks a hidden-NEXP comparator. |
| `B11_NEXP_CONTROLLED_PERTURBATION` | How sensitive are later outputs to a prospectively valid simulated exposure/support change? | No operation is allowed until a physically meaningful joint IMAGE/INVVAR/NEXP rule is specified; zero-support discontinuity remains in a comparator. | All. | None by default. | Candidate support perturbation. | Depends on the later physical rule and must be stated then. | Reliance on coverage patterns. | Fabricated noise/support semantics and synthetic edge cues. | `B00`, `B09`, and `B10`. | Perturbation changes NEXP alone while pretending IMAGE is physically corresponding; fills zero support; or lacks a preserved-discontinuity branch. |
| `B12_ROTATION` | Is a later representation stable under predeclared rotations? | Frozen rotations with explicitly specified resampling, padding, and valid region; native orientation retained. | All metadata transformed consistently where defined. | None by default. | Rotation tested as nuisance. | Edge/corner content under non-right-angle crops; orientation information if invariance is enforced. | Orientation sensitivity. | Interpolation, padding, WCS inconsistency, and repeated-resampling cues. | `B00`. | Native orientation omitted; transformation is outcome-tuned; WCS/masks/support are inconsistent; or interpolation loss is unreported. |
| `B13_REFLECTION` | Is a later representation stable under reflection independently of rotation? | Frozen axis-specific reflection with metadata geometry updated consistently. | All. | None by default. | Reflection tested separately; chirality retained in baseline. | Handedness if invariance is enforced. | Reflection sensitivity. | Artificial chirality erasure or coordinate/provenance inconsistency. | `B00` and `B12`. | Reflection and rotation are pooled; chirality is declared irrelevant without evidence; or WCS/masks are inconsistent. |
| `B14_BAND_ABLATION` | What information and shortcuts depend on g, r, z jointly or individually? | Predeclared single-band, grayscale, false-color, or multiband mapping; each mapping is explicit. | Band-specific metadata remains available. | None by default. | Band/color sensitivity, not presumed invariance. | Color and/or band-specific spatial information according to branch. | Spectral/band dependence and possible band-specific observer effects. | Unequal S/N, arbitrary color mapping, or learned mixing shortcut. | `B00`. | Mapping is implicit or outcome-tuned; g/r/z identity is lost from provenance; or the branch is presented as morphology-equivalent. |
| `B15_PRIMARY_ONLY_SENSITIVITY` | Under a later explicit gate, how much does a primary-only rule change evidence relative to S2 native geometry? | No current operation; a later rule must define pixel/window/object handling without rewriting originals. | BRICK_PRIMARY, WCS, masks, and native IMAGE. | None by default. | Boundary sensitivity only. | Nonprimary regions and potentially real scene content. | Provider ownership/boundary effects. | Selection bias, altered field of view, and S2-specific geometry. | `B00` with S2 boundary retained. | No prospective gate; S2 evidence is overwritten; rule is selected from outcomes; or changed field of view is unreported. |

### 5.1 NEXP alternatives are separate questions

The required alternatives are:

- **Hidden:** `B00`, where NEXP is preserved for audit and not supplied to a future encoder.
- **Conditioned:** `B10`, where NEXP enters only through a separable, ablatable path.
- **Stratified:** `B09`, where unchanged IMAGE results are compared across frozen NEXP regimes.
- **Controlled perturbation:** `B11`, only after a physically consistent joint perturbation rule is frozen.

None of these alternatives permits silent filling or rewriting of unsupported IMAGE pixels. `B00` and at least one later comparative branch must preserve the observed NEXP discontinuities exactly.

### 5.2 INVVAR alternatives are separate questions

INVVAR must remain side information in the baseline. `B04` tests conditioning without modifying IMAGE. A future loss-weighting branch may be specified only after the representation objective and uncertainty semantics are prospectively frozen. Before any normalization is adopted, the comparison set must include native IMAGE-only, explicit conditioning, a separately specified uncertainty-aware loss or weighting branch, and a sensitivity analysis that can reveal direct survey/support shortcuts.

Multiplication of IMAGE by INVVAR, S/N-only replacement, and an unverified Gaussian likelihood remain prohibited.

### 5.3 MASKBITS families remain separate

NPRIMARY, optical, WISE, and unknown-bit behavior must be recorded separately. The baseline retains raw IMAGE and raw masks without zeroing, interpolation, inpainting, or discarding. `B05` conditions on named families. `B06` and any observation exclusion require their own explicit gate; neither can be inferred from mask prevalence.

### 5.4 PSF evidence does not authorize homogenization

The baseline retains native PSF provenance and native north/south response shapes. `B07` tests scalar PSFSIZE conditioning. `B08` remains deferred until physical response normalization, target choice, convolution, boundary, noise-covariance, and flux behavior have verified semantics. PSF homogenization is not a default preprocessing step.

### 5.5 Geometry, background, intensity, and bands

The S2 mixed-primary boundary stays in `B00`. Any primary-only rule is a separately gated sensitivity study and cannot rewrite the frozen development evidence.

Background treatment remains deferred. A generic subtraction is not equivalent to the controlled additive-offset branch: `B02` probes sensitivity and does not claim to estimate a sky background.

Brightness and contrast candidates must state their lost information. Multiplicative scaling changes absolute flux scale; additive offsets change the zero level; a shared robust global scale changes units and can introduce dataset leakage. Per-image min-max scaling and histogram equalization remain prohibited. No transform is justified by producing visually cleaner data.

Bands remain distinct g/r/z in `B00`. Grayscale, single-band, false-color, and learned multiband mappings are explicit ablations. Color is neither assumed to encode morphology nor assumed to be nuisance.

Rotation and reflection are tested separately. No horizontal alignment, recentering, or translation augmentation is allowed for the current windows. Scale invariance remains deferred until object support and physical-scale semantics exist and PSF plus pixel scale can be treated jointly.

## 6. Anti-shortcut evaluation plan for a later representation stage

This plan is frozen prospectively but cannot run before a representation stage is separately specified and authorized. Its purpose is to measure observer information retained by a representation, not to declare observer variables intrinsically invalid.

Future probes must attempt to predict, from a frozen representation and under leakage-controlled splits:

1. survey region or north/south identity;
2. NEXP summaries and support/discontinuity strata;
3. INVVAR summaries, zero-support status, and dispersion diagnostics;
4. prevalence of NPRIMARY, optical, WISE, and unknown MASKBITS families separately;
5. PSFSIZE and predeclared PSF-response diagnostics;
6. BRICK_PRIMARY or mixed-primary status.

The later protocol must freeze the probe family, train/validation grouping unit, metrics, null or permutation control, uncertainty reporting, and decision thresholds before results are observed. This document deliberately sets no thresholds because two objects and six windows cannot calibrate them.

High predictability of observer metadata is evidence that the representation retains observer information. It is not by itself proof that the representation is invalid, nor permission to remove information. The interpretation must consider whether the observer property is entangled with sampling, signal quality, or astrophysical content and must compare the controlled branches above.

## 7. Information firewall

Human annotations, Galaxy Zoo votes, vote fractions, morphology labels or names, and predictions derived from them remain inaccessible to every preprocessing and invariance decision in this document. They must not be used to:

- select transformations, parameters, windows, objects, bands, or masks;
- define nuisance variables or invariances;
- tune thresholds, branch order, or stopping criteria;
- choose a preferred embedding or representation;
- interpret the Tier-B IMAGE measurements as morphology.

Any later interpretation stage requires its own authorization and must consume frozen outputs without retroactively changing this decision.

## 8. Unresolved assumptions and mandatory deferrals

The following remain unresolved and may not be filled by convention:

- physical normalization and common-grid semantics for the acquired coadd PSF responses;
- a flux-preserving, noise-aware PSF-matching target and validation rule;
- background definition, estimator, scale, mask interaction, and information-loss bound;
- object support, centering, orientation, and field-of-view sufficiency in the current mixed scenes;
- physical scale or distance semantics needed for resizing or scale invariance;
- whether any MASKBITS family is fatal for a pixel, window, or object;
- the statistical distribution and likelihood semantics represented by INVVAR;
- a physically valid joint perturbation of IMAGE, INVVAR, and NEXP;
- whether color, absolute brightness, orientation, handedness, or primary-boundary context is morphology-relevant, nuisance, or both;
- leakage-controlled split units and calibrated thresholds for future anti-shortcut probes.

These deferrals are active controls. They cannot be treated as implementation choices.

## 9. Exact next stage

The next permissible development stage is:

**Stage ID:** `OC3-PREPROCESSING-INVARIANCE-PERTURBATION-PILOT-001`

**Stage name:** PREPROCESSING / INVARIANCE PERTURBATION PILOT

Its prospective specification may use only the frozen native windows and observer metadata to define and validate controlled transformations. It must:

1. keep `B00_NATIVE_IMAGE_ONLY` immutable and mandatory;
2. freeze branch parameters before execution;
3. measure value, support, geometry, dtype, finite-value, provenance, and reversibility/information-loss effects without using morphology labels;
4. keep NEXP, INVVAR, MASKBITS, PSF, WCS, and primary geometry synchronized where a transformation has defined semantics;
5. stop branches whose required semantics are listed as deferred;
6. avoid an encoder, embeddings, clustering, anomaly detection, model training, or morphology inspection;
7. produce only prospective technical evidence needed to decide which branches are safe to carry into a later representation experiment.

The next stage must not skip directly to encoder selection, representation learning, or clustering. A separate prospective specification and authorization are required before any of those activities.

## 10. Completion declaration

This document was created from frozen tabular and summary evidence. It performed:

- zero IMAGE preprocessing operations;
- zero augmentations;
- zero pixel-array reads for new analysis;
- zero morphology accesses or interpretations;
- zero label accesses;
- zero model or representation operations;
- zero network requests;
- zero acquisition operations.

The baseline remains the unchanged native g/r/z IMAGE data with observer metadata preserved externally. This decision freezes comparison questions and safeguards; it does not select a transformed scientific input.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
