# OC3 Preprocessing / Invariance Perturbation Pilot Specification

## 0. Status, authority, and terminology

**Stage ID:** `OC3-PREPROCESSING-INVARIANCE-PERTURBATION-PILOT-001`

**Status:** FROZEN PROSPECTIVE SPECIFICATION ONLY

**Execution authorized by this document:** NONE

**Network:** PROHIBITED

**Image display and morphology inspection:** PROHIBITED

**Model, encoder, embedding, clustering, anomaly analysis, and training:** PROHIBITED

This specification is governed by:

| Authority | Required SHA-256 or state |
|---|---|
| `OC3_PREPROCESSING_AND_INVARIANCE_DECISION_001.md` | `de91bb4b25c002b7c4d5ee0744f6fc7e719d43ec6a969885f66d423b2ac80cf9` |
| `OC3_PREPROCESSING_AND_INVARIANCE_DECISION_001_TERMINOLOGY_CLARIFICATION_001.md` | `42c13760a18e1c88189a1bf02ac63546eae1d1c85296b4a57e55dfff06e30052` |
| Native extraction terminal | `NATIVE_EXTRACTION_VALIDATED` |
| `oc3/TECHNICAL_INDEX/OC3_NATIVE_EXTRACTION_MANIFEST.json` | `f9002086f90d70eab2e0a9dcf76b6e5099f21847449053a819191b05717fc298` |
| Native extraction manifest seal | `3083c3004419c5bd72eee12aeb5d2c78ad59703fc88f99fb9d7d0d613648fc75` |
| `OC3_NATIVE_EXTRACTION_TERMINAL.json` | `da8abd2b6ab3c072945dab887c85d675ca032ac6c5e44fd46b79575b6ec28248` |
| Frozen locations | `33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1` |
| `OC3_OBSERVER_AUDIT_SLOT_METRICS.csv` | `993d75eca71331e9fc8ea223d24f1ee5335541f0b8cec61817b3f2d2185ecf5e` |
| Observational audit terminal | `OBSERVATIONAL_CONFOUND_AUDIT_COMPLETED` |

The terminology clarification is binding. OC-3 currently contains **2 frozen technical development bricks**, **6 frozen observational windows**, and **0 defined astronomical objects for morphology learning**. The required description is **two-brick / six-window technical pilot**. The windows are technical observational diagnostics, not galaxy examples or object units.

The historical decision document remains byte-for-byte unchanged.

## 1. Purpose and non-purpose

The pilot asks one technical question:

> What exact numerical, support, geometry, provenance, and information-loss effects do the currently justified candidate transformations have on the frozen native observations before any representation model exists?

The pilot measures only:

- exact value and content-hash changes;
- dtype and finite-value behavior;
- zero and support preservation;
- shape and geometry consequences;
- exact or numerical reversibility where applicable;
- information deliberately removed or potentially distorted;
- synchronization of observer maps and provenance; and
- WCS consistency under exact lattice transforms.

The pilot does not measure morphology, visual quality, embedding quality, cluster quality, classification performance, astronomical usefulness, or which preprocessing is “best.” It cannot select a morphology preprocessing pipeline or authorize representation learning.

## 2. Frozen input gate

Execution must fail closed before any array is opened unless every authority in section 0 matches. The native extraction manifest must contain:

```text
stage_id = OC3-OFFLINE-NATIVE-EXTRACTION-001
state = NATIVE_EXTRACTION_VALIDATED
slots = S1,S2,S3,N1,N2,N3 in that order
crops = 78
psf_mappings = 18
manifest seal = 3083c3004419c5bd72eee12aeb5d2c78ad59703fc88f99fb9d7d0d613648fc75
```

Each manifest-bound input must be read-only and must match its recorded artifact SHA-256, array-content SHA-256, shape `(129,129)`, dtype descriptor, slot, product, band, slice bounds, and WCS provenance before use. The sole pixel-map inputs are the existing 78 `.npy` crops. Parent coadds, network resources, acquisition staging, alternate crops, and regenerated arrays are prohibited.

Only the six frozen windows and their linked observer metadata may be used. No crop, recentering, coordinate change, location replacement, source detection, segmentation, or astronomical object definition is permitted.

## 3. Mandatory baseline

`B00_NATIVE_IMAGE_ONLY` is immutable and mandatory. It consists of references to the 18 native IMAGE arrays in slot order and band order `g,r,z`, with all observer metadata retained externally. It performs no copy, cast, transformation, concatenation, or metadata injection.

The execution of B00 means integrity verification and publication of reference identities only. It never creates a transformed baseline. Every numerical branch compares directly with the corresponding B00 array; every geometry branch compares with the corresponding B00 array and native WCS.

No observer metadata is supplied to a model because no model exists in this stage.

## 4. Closed branch execution classes

Every decision-document branch has exactly one class for this pilot:

| Branch | Execution class | Exact scope in this pilot |
|---|---|---|
| `B00_NATIVE_IMAGE_ONLY` | `EXECUTE_TRANSFORMATION_NOW` | Verify and reference the native baseline; transform nothing. |
| `B01_MULTIPLICATIVE_FLUX_SCALE` | `EXECUTE_TRANSFORMATION_NOW` | Two frozen positive scalar variants on IMAGE only. |
| `B02_ADDITIVE_OFFSET` | `EXECUTE_TRANSFORMATION_NOW` | Two frozen symmetric per-band offset variants on IMAGE only. |
| `B03_ROBUST_GLOBAL_SCALE` | `EXECUTE_TRANSFORMATION_NOW` | One frozen per-band development-scale division on IMAGE only. |
| `B04_INVVAR_CONDITIONING` | `RESERVED_FOR_REPRESENTATION_STAGE` | Verify INVVAR remains canonically addressable; create no conditioned input. |
| `B05_MASK_FAMILY_CONDITIONING` | `RESERVED_FOR_REPRESENTATION_STAGE` | Verify raw MASKBITS and family definitions remain addressable; create no conditioned input. |
| `B06_CONTROLLED_MASK_REMOVAL` | `BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE` | No explicit mask-removal gate exists. |
| `B07_PSFSIZE_CONDITIONING` | `RESERVED_FOR_REPRESENTATION_STAGE` | Verify PSFSIZE maps and PSF provenance remain addressable; create no conditioned input. |
| `B08_PSF_PERTURBATION_OR_MATCHING` | `BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE` | Physical PSF normalization and matching semantics remain unresolved. |
| `B09_NEXP_STRATIFICATION` | `METADATA_ONLY_NOW` | Publish the six-row frozen technical-stratum mapping; do not transform IMAGE. |
| `B10_NEXP_CONDITIONING` | `RESERVED_FOR_REPRESENTATION_STAGE` | Verify NEXP remains canonically addressable; create no conditioned input. |
| `B11_NEXP_CONTROLLED_PERTURBATION` | `BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE` | No physically valid joint IMAGE/INVVAR/NEXP perturbation exists. |
| `B12_ROTATION` | `EXECUTE_TRANSFORMATION_NOW` | Three exact right-angle lattice permutations. |
| `B13_REFLECTION` | `EXECUTE_TRANSFORMATION_NOW` | Horizontal and vertical exact lattice permutations, kept separate. |
| `B14_BAND_ABLATION` | `EXECUTE_TRANSFORMATION_NOW` | Channel-selection manifests for g-only, r-only, and z-only; no synthetic pixels. |
| `B15_PRIMARY_ONLY_SENSITIVITY` | `BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE` | No prospective primary-only scientific gate exists. |

The only B14 variants are `B14_G_ONLY`, `B14_R_ONLY`, and `B14_Z_ONLY`. Grayscale, false-color, arbitrary color combination, and learned multiband mappings remain unexecuted because their mapping semantics are not frozen.

A blocked branch is not a failed branch. A reserved branch is not an executed branch. Implementations must not represent either state as a successful transformation.

## 5. Shared numerical and serialization contract

The execution environment and implementation version must be recorded. Numerical behavior is frozen to NumPy 2.5.3 semantics. All calculations are deterministic and seedless.

For B01, B02, and B03:

1. input IMAGE shape remains `(129,129)`;
2. input and output dtype descriptors are identical and must be float32;
3. the operational scalar is an IEEE-754 binary32 constant;
4. an output array of the exact input `dtype.str` is allocated;
5. the NumPy ufunc operates with a float32 scalar and float32 output; no float64 working array or in-place mutation is allowed;
6. no clipping, thresholding, masking, replacement, or saturation is allowed;
7. output remains C-contiguous; and
8. each output is serialized as uncompressed `.npy` v1.0 with `allow_pickle=False`, using the native extraction canonical writer rules.

All source inputs are opened read-only. A transform always writes a new development artifact. The implementation must independently re-read each output and verify shape, dtype descriptor, content hash, and artifact hash.

The canonical array-content hash is the native extraction `OC3_ARRAY_CONTENT_V1` hash. The branch manifest additionally hashes the transform identity, operational scalar or affine transform, source array-content hash, and output array-content hash.

## 6. B01 — multiplicative flux-scale stress test

The exact variants are:

| Variant | Operational factor | IEEE-754 binary32 bits | Inverse factor |
|---|---:|---|---:|
| `B01_FACTOR_0P5` | `0.5` | `0x3f000000` | `2.0` |
| `B01_FACTOR_2P0` | `2.0` | `0x40000000` | `0.5` |

For a variant, the same scalar is applied to g, r, and z within every slot. No factor is fitted by slot, band, region, value range, or outcome. The transform is:

```text
output = float32(input * factor)
round_trip = float32(output * inverse_factor)
```

The branch measures per array: source/output hashes, dtype, finite/nonfinite counts, exact-zero counts, changed-element count/fraction, clipping count, and round-trip bitwise equality plus maximum absolute difference. It does not interpret brightness. INVVAR, NEXP, MASKBITS, PSFSIZE, PSF references, and WCS are unchanged external references.

## 7. Frozen development reference scale

The only permitted reference scale for B02 and B03 is `DEVELOPMENT_REFERENCE_SCALE_001`. It is derived entirely from the already frozen Tier-B `IMAGE/iqr` rows in `OC3_OBSERVER_AUDIT_SLOT_METRICS.csv`; no IMAGE array is reopened to estimate it.

For each band `b`:

```text
I_b = the six published float64 IMAGE IQR values in slot order
      S1,S2,S3,N1,N2,N3
R_b = numpy.quantile(I_b, 0.5, method="linear")
    = arithmetic mean of the third and fourth values after ascending sort
S_b = nearest IEEE-754 binary32 value to R_b, round-to-nearest ties-to-even
```

The binding values are:

| Band | Six frozen IQR values in slot order S1,S2,S3,N1,N2,N3 | `R_b` float64 | Operational `S_b` float32 | binary32 bits |
|---|---|---:|---:|---|
| g | `0.0032734537962824106, 0.003072572057135403, 0.0034723838325589895, 0.004288292402634397, 0.002467454585712403, 0.00217011955101043` | `0.003173012926708907` | `0.003173012984916568` | `0x3b4ff253` |
| r | `0.0075814733281731606, 0.006517183966934681, 0.005468357820063829, 0.008290610538097098, 0.005893183057196438, 0.005317323841154575` | `0.00620518351206556` | `0.006205183453857899` | `0x3bcb54da` |
| z | `0.013848434668034315, 0.011527255643159151, 0.014200177974998951, 0.019013932440429926, 0.017179248854517937, 0.022952701896429062` | `0.015689713414758444` | `0.01568971388041973` | `0x3c8087b7` |

This scale is labeled exactly:

```text
DEVELOPMENT_ONLY_SCALE
NOT_AUTHORIZED_AS_FUTURE_TRAINING_SCALE
```

It is a technical stress-test reference derived from six development windows. It is not an astronomical background, noise estimate, calibration, scientific normalization, or future preprocessing default. A future representation experiment must estimate any scale from its own training reference set under a separately frozen protocol and without evaluation or holdout evidence.

## 8. B02 — additive-offset stress test

The exact offset multiplier set is `{-1.0,+1.0}`. For band `b`, the operational offset is the signed float32 value `±S_b` from section 7. Every slot uses the same per-band constants.

| Variant | g offset | r offset | z offset |
|---|---:|---:|---:|
| `B02_OFFSET_NEGATIVE` | `-0.003173012984916568` | `-0.006205183453857899` | `-0.01568971388041973` |
| `B02_OFFSET_POSITIVE` | `+0.003173012984916568` | `+0.006205183453857899` | `+0.01568971388041973` |

The negative binary32 words are `0xbb4ff253`, `0xbbcb54da`, and `0xbc8087b7`; the positive words are those in section 7. The transform is:

```text
output_b = float32(input_b + offset_b)
round_trip_b = float32(output_b - offset_b)
```

These offsets deliberately probe sensitivity at one shared, robust development spread per band. They do not estimate or subtract sky/background. No per-slot value is fitted. INVVAR, NEXP, MASKBITS, PSFSIZE, PSF references, and WCS remain unchanged because this is a numerical sensitivity test, not a simulated observation.

The branch records the metrics from section 15, including exact-zero changes and round-trip error. It may not be described as background correction.

## 9. B03 — robust global development scale

The sole variant is `B03_DIVIDE_BY_DEVELOPMENT_REFERENCE_SCALE_001`. For every slot and band:

```text
output_b = float32(input_b / S_b)
round_trip_b = float32(output_b * S_b)
```

The same band-specific `S_b` in section 7 is used for all six slots. The transform is not per-window, label-derived, outcome-tuned, or evaluated against morphology. Output values are dimensionless relative to the development reference scale, while the manifest retains the original nanomaggy unit and the exact transformation.

The branch must carry both labels `DEVELOPMENT_ONLY_SCALE` and `NOT_AUTHORIZED_AS_FUTURE_TRAINING_SCALE`. It records numerical and reversibility effects only.

## 10. B12 and B13 — exact lattice geometry

Let the input/output shape be `n=129`, let `m=n-1=128`, and use zero-based pixel coordinates `p=[x,y]^T`. Every geometry variant is an exact old-to-new integer affine transform:

```text
p_out = A * p_in + t
```

| Variant | NumPy-equivalent transform | `A` | `t` |
|---|---|---|---|
| `B12_ROT90_CCW` | `rot90(array,k=1)` | `[[0,1],[-1,0]]` | `[0,128]` |
| `B12_ROT180` | `rot90(array,k=2)` | `[[-1,0],[0,-1]]` | `[128,128]` |
| `B12_ROT270_CCW` | `rot90(array,k=3)` | `[[0,-1],[1,0]]` | `[128,0]` |
| `B13_REFLECT_HORIZONTAL` | `fliplr(array)` | `[[-1,0],[0,1]]` | `[128,0]` |
| `B13_REFLECT_VERTICAL` | `flipud(array)` | `[[1,0],[0,-1]]` | `[0,128]` |

Each transform must be implemented as the corresponding integer-index permutation, followed by a C-contiguous copy for canonical serialization. It performs zero interpolation, zero padding, zero clipping, and invents zero pixels. Its inverse is exact: ROT90 and ROT270 are mutual inverses; ROT180, horizontal reflection, and vertical reflection are self-inverse.

For each geometry variant, all 13 native maps per slot are permuted identically:

```text
IMAGE g,r,z
INVVAR g,r,z
NEXP g,r,z
PSFSIZE g,r,z
MASKBITS optical
```

This preserves pixel alignment among IMAGE and observer maps. Array dtype descriptors and per-element byte values must remain unchanged under permutation. Exact inverse reconstruction must be bitwise equal to B00 for every map.

### 10.1 WCS rule

The immutable native WCS model remains the authority. The transformed branch stores the exact affine adapter `(A,t)` and defines:

```text
p_in = inverse(A) * (p_out - t)
world_out(p_out, origin=0) = world_native(p_in, origin=0)
```

No provider WCS card is dropped, fitted, or silently rewritten. At output center, four corners, and four edge midpoints, the implementation must verify that branch world coordinates equal the native-world evaluation at the inverse-mapped integer coordinate. World-to-pixel round trip, mapped back through the affine adapter, must have maximum residual no larger than `1e-6` native pixel. The manifest records the affine, WCS source hash, test points, maximum residual, padding count, and interpolation count.

### 10.2 PSF limitation

Provider coadd-PSF response arrays are not decoded, rotated, normalized, resized, or rewritten in this pilot. Their immutable provenance and native north/south shapes remain linked externally. Every B12/B13 row must record:

```text
provider_psf_response_transform = NOT_EXECUTED
psf_provenance_retained = true
known_semantic_limitation = TRANSFORMED_WINDOW_HAS_NO_TRANSFORMED_PROVIDER_PSF_RESPONSE
```

Consequently B12/B13 can establish exact window/map permutation behavior but cannot yet establish a complete PSF-synchronized representation input or rotational/reflection invariance.

## 11. B14 — deterministic single-band selections

The exact subbranches are:

| Subbranch | Bands retained | Bands omitted | Pixel artifact policy |
|---|---|---|---|
| `B14_G_ONLY` | g | r,z | Reference native g; create no new array. |
| `B14_R_ONLY` | r | g,z | Reference native r; create no new array. |
| `B14_Z_ONLY` | z | g,r | Reference native z; create no new array. |

Each is a channel-selection manifest, not a pixel transformation. It retains observer metadata for the selected band and preserves canonical references for omitted bands for audit only. The intentionally unavailable information is the two omitted bands and all cross-band/color relationships involving them.

No grayscale, average, weighted sum, color composite, false-color array, or learned mixing is created. No subbranch is described as equivalent to g/r/z.

## 12. B09 — development-only NEXP stratification

B09 reads only the already frozen NEXP metrics; it does not reopen NEXP or IMAGE arrays. For each slot:

```text
zero_support_bands = ordered bands whose frozen NEXP zero_count > 0
transition_bands = ordered bands whose frozen total_transition_count > 0
zero_class = ZANY if zero_support_bands is nonempty, otherwise Z0
transition_class = TALL if all g,r,z transition,
                   TSOME if a proper nonempty subset transitions,
                   T0 if no band transitions
technical_stratum = zero_class + "_" + transition_class
```

The binding mapping is:

| Slot | zero-support bands | transition bands | frozen transition counts g/r/z | Technical stratum |
|---|---|---|---|---|
| S1 | none | g,r,z | `388/100/113` | `Z0_TALL` |
| S2 | none | g,r,z | `95/129/40` | `Z0_TALL` |
| S3 | none | g,z | `144/0/644` | `Z0_TSOME` |
| N1 | g,r,z | g,r,z | `503/326/579` | `ZANY_TALL` |
| N2 | z | g,r,z | `174/207/138` | `ZANY_TALL` |
| N3 | none | z | `0/0/247` | `Z0_TSOME` |

This is a deterministic technical mapping, not a statistically powered comparison. No thresholds beyond exact zero and exact transition presence are introduced. It cannot select, reject, weight, or change a window.

## 13. Reserved and blocked branches

For B04, B05, B07, and B10, this pilot may check only that the manifest-bound side information exists, is read-only, has the expected identity/hash/shape/dtype, and can be addressed by slot and band or mask family. It must not concatenate channels, create “conditioned” tensors, design a conditioning architecture, or modify IMAGE. Their recorded status is `RESERVED_FOR_REPRESENTATION_STAGE`.

The exact blockers are:

| Branch | Required recorded blocker |
|---|---|
| B06 | `NO_EXPLICIT_MASK_REMOVAL_GATE` |
| B08 | `PHYSICAL_PSF_NORMALIZATION_AND_MATCHING_SEMANTICS_UNRESOLVED` |
| B11 | `NO_PHYSICALLY_VALID_JOINT_IMAGE_INVVAR_NEXP_PERTURBATION` |
| B15 | `NO_PROSPECTIVE_PRIMARY_ONLY_SCIENTIFIC_GATE` |

Blocked branches must create no transformed array, selection, exclusion, simulated value, or alternative window.

## 14. Development-only parameter principle and anti-cherry-picking

Every amplitude and mapping in this specification is frozen before execution and is a development stress-test parameter. After implementation begins:

- no factor, offset, scale, angle, axis, band, stratum, or tolerance may be adjusted because an effect appears too small, too large, ugly, convenient, or clean;
- no branch may be removed because its technical output is unexpected;
- no transformation may be added from visual inspection or model behavior;
- no output may be displayed to tune a choice;
- no holdout, evaluation, human, Galaxy Zoo, Hubble, morphology, or label-derived evidence may be accessed; and
- no pilot parameter becomes a scientific or training default from this execution.

Unexpected technical effects are pilot results. They do not authorize parameter revision within the same attempt.

## 15. Frozen technical effect metrics

Metrics are computed per output array where applicable and then summarized by branch/variant without ranking. The closed array metric set is:

```text
stage_id
branch_id
variant_id
slot
product
band
source_artifact_sha256
source_array_content_sha256
output_artifact_sha256
output_array_content_sha256
input_shape
output_shape
input_dtype
output_dtype
input_finite_count
output_finite_count
input_nonfinite_count
output_nonfinite_count
input_exact_zero_count
output_exact_zero_count
changed_element_count
changed_element_fraction
input_finite_minimum
input_finite_maximum
output_finite_minimum
output_finite_maximum
inverse_applicable
inverse_variant
round_trip_bitwise_equal_count
round_trip_bitwise_equal_fraction
round_trip_max_absolute_difference
support_alignment_pass
wcs_consistency_applicable
wcs_max_residual_native_pixels
padding_count
interpolation_count
clipping_count
```

`changed_element_count` compares each element’s exact dtype-width byte group, so signed zero and NaN payload changes cannot be hidden. Exact-zero counts use numerical equality to zero and include either sign. Extrema use finite values only and exist solely to detect clipping or nonfinite generation; they are not scene summaries. An undefined field is null with a reason, never fabricated as zero.

For B12/B13, changed-element position counts are descriptive of permutation and are never treated as value distortion; multiset byte equality and inverse bitwise equality are mandatory. For B14 and B09, array metrics are not emitted because no output array exists.

The pilot must not calculate centroids, moments, profiles, gradients, textures, segmentation, source counts, morphology statistics, image similarity intended as visual quality, embeddings, or branch rankings.

## 16. Information-loss register

Every branch and variant receives exactly one row with this schema:

```text
branch_id
variant_id
execution_class
operation
mathematically_reversible
bitwise_reversible
information_intentionally_removed
information_potentially_distorted
new_artifacts_possible
observer_variables_synchronized
observer_variables_unchanged
observer_variables_not_synchronized
known_semantic_limitation
comparison_baseline
execution_status
```

Binding expectations include:

- B00 removes and distorts nothing.
- B01 changes absolute flux scale but leaves spatial layout unchanged; float32 range/rounding are possible numerical effects.
- B02 changes the zero level; float32 rounding and changes to exact-zero membership are expected technical effects.
- B03 removes native unit magnitude relative to the development scale; float32 division/round-trip error is possible.
- B12/B13 are exact pixel permutations and must be bitwise reversible for all synchronized maps; provider PSF responses remain unsynchronized.
- B14 intentionally makes two bands and their cross-band information unavailable to the subbranch.
- B09 removes nothing and creates no pixel product.
- reserved and blocked branches report no executed operation.

No row may label a branch scientifically superior.

## 17. Output and immutability contract

If separately implemented and authorized, the stage root is:

```text
oc3/PERTURBATION_PILOT/
  OC3-PREPROCESSING-INVARIANCE-PERTURBATION-PILOT-001/
```

The required logical outputs are:

```text
STAGING/
TRANSFORMED/<variant_id>/<slot>/<product-band filename>
OC3_PERTURBATION_BRANCH_MANIFEST.json
OC3_PERTURBATION_TECHNICAL_EFFECT_METRICS.csv
OC3_PERTURBATION_INFORMATION_LOSS_REGISTER.csv
OC3_NEXP_TECHNICAL_STRATA.csv
OC3_PERTURBATION_PILOT_SUMMARY.json
OC3_PERTURBATION_PILOT_TERMINAL.json
OC3_PERTURBATION_PILOT_RUN.log
```

B00 and B14 contain immutable references only and must not duplicate native arrays. B09 creates only its six-row CSV mapping. No giant combined tensor, RGB composite, thumbnail, plot, gallery, or visualization is permitted. g/r/z identity remains explicit in every path and row.

The branch manifest is canonical JSON with sorted keys, compact separators, UTF-8, `ensure_ascii=false`, `allow_nan=false`, and one terminal LF. It binds authority hashes, implementation identity, environment versions, every branch class, exact constants/affines, input and output identities, metric/register hashes, counts, and a canonical seal computed with `sealed` omitted.

Publication is atomic after all gates pass. Successful outputs become read-only. Existing stage or terminal paths cause fail-closed refusal; native extraction is never overwritten, repaired, deleted, or made writable.

The expected authorized inventory is:

```text
baseline reference variants = 1
B01 variants = 2
B02 variants = 2
B03 variants = 1
B12 variants = 3
B13 variants = 2
B14 selection variants = 3
total named executable variants including B00 = 14
B09 metadata mappings = 6 rows
reserved branches = 4
blocked branches = 4
transformed arrays = 480
network requests = 0
```

The 480 transformed arrays comprise 90 IMAGE outputs from B01/B02/B03 and 390 synchronized map outputs from B12/B13. B00, B09, and B14 create no pixel arrays. A mismatch fails the attempt.

Because future execution is a bulk operation over scientific image/map arrays, project governance requires a reproducible CLI handoff for human execution after implementation and focused validation. This specification itself authorizes neither implementation nor execution.

## 18. Validation and failure rules

Before publication, an implementation must require:

1. all authority hashes/states and manifest seal match;
2. all 78 native input identities pass their existing integrity gates;
3. B00 references exactly 18 native IMAGE arrays and copies none;
4. all B01/B02/B03 constants match their decimal and binary32 bindings;
5. every transformed output preserves required shape/dtype and creates no nonfinite value from a finite input;
6. clipping, padding, and interpolation counts are zero for every authorized branch;
7. B12/B13 synchronize all 13 maps per slot and inverse-reconstruct them bitwise;
8. all WCS adapters pass the `1e-6` native-pixel residual bound;
9. B12/B13 preserve PSF provenance and record the unsynchronized-response limitation;
10. B14 creates exactly three selection manifests and no pixel array;
11. B09 exactly matches the six frozen rows in section 12;
12. reserved and blocked branches create no transformed or conditioned input;
13. native inputs remain byte-identical and read-only;
14. no human/morphology label is opened or logged;
15. no image display, plot, model, embedding, clustering, morphology operation, or network transport is constructed; and
16. all output hashes, manifest seal, counters, and information-loss rows reconcile.

Any mismatch produces `PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_FAILED`. There is no partial-success terminal, silent retry with changed parameters, branch substitution, or repair of a native input. Staging and a compact technical failure record may remain, but no successful subset is published.

## 19. Success terminal and meaning

The sole success terminal is:

```text
PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_COMPLETED
```

It means only that all authorized technical perturbation variants completed and all metadata-only, reserved, and blocked branches were represented exactly according to this frozen specification, with their technical and information-loss properties recorded.

Success does not:

- choose preprocessing for morphology;
- establish invariance;
- establish observational equivalence;
- define an astronomical object;
- authorize an encoder, model, training, embeddings, clustering, or interpretation; or
- promote any development stress-test parameter to a future training default.

## 20. Boundary after completion

After a successful pilot, the project may decide which transformations are technically safe enough to include as comparison branches in a later representation robustness experiment. It may not decide which branch produces the best morphology.

Before any training, a separate prospective representation-experiment specification must freeze at least encoder baselines, representation inputs, observer-shortcut probes, seeds, split/grouping rules, metrics, robustness comparisons, decision thresholds, and failure criteria. Human and Galaxy Zoo labels remain unavailable for preprocessing, branch, encoder, and hyperparameter selection.

## 21. Zero-execution declaration

Creating this specification and its terminology clarification performs:

- zero transformations;
- zero new pixel-array reads;
- zero changes to native IMAGE or observer maps;
- zero changes to the six frozen locations;
- zero model, encoder, embedding, clustering, or morphology operations;
- zero image displays or plots;
- zero label accesses;
- zero network requests; and
- zero pilot output publication.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
