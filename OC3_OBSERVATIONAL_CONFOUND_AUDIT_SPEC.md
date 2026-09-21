# OC-3 observational confound audit specification

**Stage:** `OC3-OBSERVATIONAL-CONFOUND-AUDIT-001`

**Status:** prospective specification only

**Network:** prohibited

**Image display and scientific morphology:** prohibited

## 1. Question and boundary

This stage asks: **what observational variation is present across the six
frozen OC-3 development windows, and which of that variation could later act as
a confound for a morphological representation?** Its mandatory framing is:
are we observing potential scene structure, or structure introduced by the
observing process?

The audit characterizes the observer. It does not decide whether morphology is
present, preserved, recoverable or scientifically usable. It performs no
selection, rejection, replacement, preprocessing, normalization, masking,
source detection, segmentation, representation learning or training. It uses
no human label, Galaxy Zoo product, rendered image, plot, thumbnail or RGB
composite.

## 2. Frozen authorities and input gate

Execution is permitted only after all of these exact checks pass:

| Authority | Required binding |
|---|---|
| Native extraction terminal | `NATIVE_EXTRACTION_VALIDATED` |
| `oc3/TECHNICAL_INDEX/OC3_NATIVE_EXTRACTION_MANIFEST.json` | SHA-256 `f9002086f90d70eab2e0a9dcf76b6e5099f21847449053a819191b05717fc298` |
| Manifest seal | `3083c3004419c5bd72eee12aeb5d2c78ad59703fc88f99fb9d7d0d613648fc75` |
| Extraction specification | SHA-256 `e5a86e69b97ca1daff42e44e9abfd823a5bb37ccf181f1aec4650dd88264c6d2` |
| Morphological information preservation specification | SHA-256 `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| Frozen locations | SHA-256 `33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1` |
| Selection identity | `2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860` |

The manifest must contain exactly six slots in order
`S1,S2,S3,N1,N2,N3`, 78 crop records in its frozen product order, 18 PSF
response mappings and 54 unique PSF observational identities. Every crop path,
artifact SHA-256, array-content SHA-256, shape and dtype descriptor is verified
before analysis. Existing crops are read-only inputs and are never regenerated
or modified.

The 78 extracted `.npy` files are the sole pixel-map authority. A native coadd
body must not be reopened to recompute a crop. Two narrow exceptions are
allowed: the 18 immutable provider PSF bodies because extraction deliberately
published references rather than decoded PSF planes, and header-only reads of
one manifest-bound NEXP body per region to recover the already validated
`RAMIN,RAMAX,DECMIN,DECMAX` BRICK_PRIMARY provenance. A header-only read must
not touch its compressed image section. Each exceptional body may be opened
only through its manifest path after its recorded body SHA-256 matches. Frozen
location and selection metadata may be read only to verify slot intent and
BRICK_PRIMARY provenance; they may not change a location or pixel bound.

No network-capable transport may be imported or constructed. A missing,
changed, writable or structurally inconsistent input yields
`OBSERVER_AUDIT_INCOMPLETE` before publication.

## 3. Two-tier execution order

The implementation must enforce two sequential analytical tiers:

1. **Tier A — `OBSERVER_ONLY`.** It may read only INVVAR, NEXP, MASKBITS,
   PSFSIZE, the referenced coadd-PSF responses, WCS/geometry provenance and
   frozen slot-design metadata. It must complete all Tier-A rows in staging
   before the first IMAGE array is opened.
2. **Tier B — `SCENE_MIXED_OBSERVATION`.** It may then read IMAGE only for the
   fixed signal-sanity metrics in section 11.

Technical counters must record 60 Tier-A crop-array reads, 18 Tier-B IMAGE
array reads, 18 PSF response-body reads and 54 PSF plane decodes. They may not
record pixel values. If Tier A is incomplete, Tier B is not started.

All calculations operate on the unchanged 129×129 arrays. Flattening, when
needed for a scalar reduction, uses C order and does not create a published
array. No computed value can feed back into a crop, a location, a mask or the
set of metrics.

## 4. Frozen slot intent

The audit retains these roles regardless of observed values:

| Slot | Prospective role |
|---|---|
| S1 | south interior observational reference |
| S2 | south BRICK_PRIMARY boundary condition |
| S3 | south optical MASKBITS condition |
| N1 | north interior observational reference |
| N2 | north exposure-support transition |
| N3 | north spatial PSFSIZE variation |

`S1` and `N1` retain their selection-provenance interior status. `S2` retains
its validated BRICK_PRIMARY boundary-crossing status as an observational fact;
NPRIMARY is not a substitute for that geometry. For every slot, the audit also
computes an observed geometry status from WCS and the frozen primary bounds.
For slots whose selection rule did not constrain BRICK_PRIMARY, the prospective
role remains `NOT_CONSTRAINED_BY_SLOT_DESIGN` even though their measured status
is reported. An observed status never retroactively redefines the slot role.

## 5. Shared numerical conventions

Counts are exact integers. Fractions are `count / 16641` for crop maps and
`count / plane.size` for PSF planes. Empty denominators are invalid. Unless a
family states otherwise, extrema and quantiles use finite values only. The
fixed quantile probabilities are:

```text
Q = [0.05, 0.25, 0.50, 0.75, 0.95]
```

They are computed with NumPy 2.5.3
`numpy.quantile(values, Q, method="linear")`. `IQR = Q0.75 - Q0.25`.
Nonfinite counts are always separate; JSON never serializes NaN or infinity.
An undefined scalar is null with an explicit `validity_state`, never zero.

Reductions that require float64 use the stored values promoted to float64 but
never rewrite inputs. CSV floating values use the shortest round-trip decimal
representation produced by canonical JSON; negative zero is retained when it
is the computed result. CSV is UTF-8, comma-delimited, RFC 4180 quoted where
needed, with LF terminators and one header row.

## 6. Tier A — NEXP coverage

For every slot and band, NEXP must remain a 129×129 nonnegative integer array.
The audit records:

- pixel count;
- one count and fraction for every observed integer level, ordered ascending;
- zero and positive counts/fractions;
- exact minimum and maximum;
- number of distinct levels;
- horizontal, vertical and total transition counts;
- transition fraction.

The prospective adjacency rule uses each undirected four-neighbour edge once:

```text
horizontal = sum(A[y,x] != A[y,x+1]) for y=0..128, x=0..127
vertical   = sum(A[y,x] != A[y+1,x]) for y=0..127, x=0..128
total      = horizontal + vertical
transition_fraction = total / 33024
```

There is no diagonal adjacency, wrapping or thresholding. NEXP is not converted
into a mask and never modifies IMAGE.

For N2, the frozen class-0 condition is expressed if at least one band has both
`zero_count > 0` and `positive_count > 0`. The boolean and the bands satisfying
it are recorded. If false, the evidence state is `STRATUM_NOT_EXPRESSED`; no
fallback location is selected.

## 7. Tier A — INVVAR and diagnostic sigma

For every slot and band, the audit records pixel count, finite/nonfinite counts
and fractions, exact-zero count/fraction, positive count/fraction,
negative-value count/fraction, finite minimum/maximum, Q05/Q25/Q50/Q75/Q95,
median, IQR and:

```text
relative_iqr = IQR / abs(median)
```

`relative_iqr` is null with `UNDEFINED_ZERO_MEDIAN` when the finite median is
zero and null with `NO_FINITE_VALUES` when appropriate. It is a delivered
weight-field dispersion descriptor, not a noise-model fit.

For values strictly greater than zero, compute in float64 only:

```text
diagnostic_sigma = 1 / sqrt(invvar)
```

Record its contributing count/fraction, finite minimum/maximum,
Q05/Q25/Q50/Q75/Q95, median and IQR. No sigma value is produced at zero,
negative or nonfinite INVVAR. This diagnostic does not assert independent
Gaussian noise, and INVVAR or sigma never modifies IMAGE.

## 8. Tier A — MASKBITS

MASKBITS must remain the raw nonnegative integer field. The frozen DR9 bit
partition is:

| Partition | Bits |
|---|---|
| NPRIMARY | 0 |
| optical S3 groups | 1–7 and 10–13 |
| WISE | 8–9 |
| known DR9 mask | 0–13 |

For each slot, record the pixel count and count/fraction for raw value zero,
each known bit 0 through 13, any optical S3 bit, any WISE bit and any unknown
bit. Also record ascending unknown bit positions and their individual
counts/fractions. The known mask is `(1 << 14) - 1`; an unknown pixel satisfies
`raw & ~known_mask != 0`.

Raw integer semantics and per-bit overlap are preserved. Counts are not
exclusive and all nonzero values are never collapsed into “bad pixels.” The
absence of a bit does not establish the absence of the documented phenomenon.
No bit is applied to IMAGE.

For S3, the frozen optical condition is expressed exactly when:

```text
count((MASKBITS & sum(1 << b for b in [1,2,3,4,5,6,7,10,11,12,13])) != 0) > 0
```

The boolean is recorded. A false result is `STRATUM_NOT_EXPRESSED` and does not
trigger replacement.

## 9. Tier A — PSFSIZE

For every slot and band, record pixel count, finite/nonfinite counts and
fractions, nonpositive count/fraction, finite minimum/maximum, Q25/Q50/Q75,
median, IQR and:

```text
relative_range = (finite_max - finite_min) / median
```

The relative range is defined only for a finite strictly positive median.
PSFSIZE remains a survey-provided FWHM map in angular units, not a PSF kernel.

For N3, recompute the original statistic without changing its arithmetic:

```text
median_b = numpy.median(PSFSIZE_b), promoted to float64
within_b = (max(PSFSIZE_b) - min(PSFSIZE_b)) / median_b
across   = max_b(median_b) / min_b(median_b) - 1
V        = max(within_g, within_r, within_z, across)
```

All three windows must be finite and strictly positive. Require
`abs(V - 0.8293932498304606) <= 1e-12`, with no relative tolerance. This is an
extraction/selection consistency check and never a new ranking criterion. A
mismatch makes the audit incomplete; it does not select another location.

## 10. Tier A — immutable coadd PSF responses

The 18 referenced response bodies are analyzed in manifest slot order and
point order `P0,P1,P2`; their g/r/z plane mappings yield exactly 54
observational identities. Stored arrays are never rewritten, cropped,
centered, normalized, padded, resized or homogenized.

### 10.1 Representation-safe diagnostics

For each plane, record body and plane identity, body SHA-256, physical HDU,
shape, dtype descriptor, element count, finite/nonfinite counts and fractions,
finite minimum/maximum, raw sum, raw integral in sample-pixel units, raw peak
location and plane-content SHA-256.

The raw sum is `math.fsum` over C-order values promoted exactly to Python
float and is defined only if all samples are finite. “Raw integral” is the same
unscaled sum explicitly labeled `sample_pixel_units`; it is not a physical
integral. The raw peak is the finite maximum with a tie broken by lowest
`(y,x)` in row-major order. Plane content hash is:

```text
SHA256(
  UTF-8("OC3_PSF_PLANE_V1\n") +
  canonical_json({"dtype": dtype.str, "order": "C", "shape": [h,w]}) +
  LF + plane.tobytes(order="C")
)
```

Across P0/P1/P2, per slot and band, record whether shape/dtype agree, the
minimum/maximum/range of raw sums when all three are defined, the minimum
finite fraction, the number of distinct plane hashes, and the maximum pairwise
Euclidean displacement between raw peak coordinates. These are representation
descriptors only.

### 10.2 Normalization decision

The existing evidence leaves units unresolved and normalization
`SOURCE_VERIFIED_NOT_DIRECTLY_OBSERVED`. It does not justify silent unit-sum,
unit-peak or physical normalization. Therefore no normalized moment, FWHM,
ellipticity, width or physical PSF-shape metric is allowed in this stage. Every
one of the 54 identities receives:

```text
PHYSICAL_PSF_SHAPE_METRICS_DEFERRED
```

This decision is prospective and may change only through a separate evidence
and specification amendment.

## 11. Tier A — WCS and geometry

For each slot, record region, brick, frozen slot role,
`primary_geometry_role`, native bounds, center index `[64,64]`, absence of
padding/resampling, and the maximum stored parent/crop WCS consistency residual
across its thirteen crop records. All thirteen WCS/bounds representations must
agree for the slot.

Using only the header-recovered frozen BRICK_PRIMARY sky rectangle and the
translated crop WCS, classify all 16641 output pixel centers with the original
half-open rule: RA inside `[RAMIN,RAMAX)` with wrap, and DEC inside
`[DECMIN,DECMAX)`. Record primary/nonprimary counts and fractions, horizontal,
vertical and total four-neighbour primary-boundary transitions, and
`observed_primary_geometry_status` as `ALL_PRIMARY`, `MIXED_PRIMARY` or
`NO_PRIMARY`. For a mixed crop, record the same discrete center-to-boundary
distance used by frozen selection: boundaries lie halfway between adjacent
pixel centers with different membership, and distance is the minimum Euclidean
distance from `[64,64]` to those boundary-segment midpoints. The value is null
for a non-mixed crop.

Local geometry is measured at output center `(64,64)` and corners
`(0,0),(128,0),(0,128),(128,128)`. At each point, construct a numerical
Jacobian with symmetric offsets of 0.5 pixel. Wrapped RA differences are mapped
to `[-180,180)` and multiplied by `cos(dec_at_point)`; east/north derivatives
are expressed in arcsec per pixel. Record the two singular values, absolute
determinant in arcsec²/pixel² and axis ratio `s_max/s_min`. Per slot record:

- center geometric-mean pixel scale `sqrt(abs(det(J_center)))`;
- minimum, maximum and relative range of pixel area across the five points;
- maximum axis ratio across the five points;
- maximum parent/crop round-trip residual in native pixels.

Area relative range is `(max-min)/median` over the five values. Singular or
nonfinite Jacobians are `OBSERVER_AUDIT_INCOMPLETE`. WCS is never used to
reproject, recenter or alter a crop. S2 remains
`FROZEN_BOUNDARY_CROSSING` and must independently yield `MIXED_PRIMARY` with
both counts positive and at least one transition. S1 and N1 must independently
yield `ALL_PRIMARY`. A mismatch is `STRATUM_NOT_EXPRESSED`; this stage does not
replace geometry with NPRIMARY or choose another location.

## 12. Tier B — IMAGE signal sanity

Only after Tier A has completed may each IMAGE g/r/z crop be read. For every
slot and band, record only:

- pixel count;
- finite and nonfinite counts/fractions;
- exact-zero count/fraction;
- finite minimum and maximum;
- Q05/Q25/Q50/Q75/Q95;
- median and IQR.

Every row has `interpretation_scope=SCENE_MIXED_OBSERVATION`. Differences may
come from the astronomical scene, the observer or both. The metrics are not
morphological descriptors. No source count, centroid, shape, concentration,
asymmetry, Sérsic quantity, source-tied moment, segmentation, edge/texture
feature, embedding or visualization is computed.

With only six slots, this stage computes no p-values, fitted relationship,
causal model or correlation coefficient. Tier-A and Tier-B rows may be read
side by side later, but this audit publishes no claim that an observer variable
caused an IMAGE summary.

## 13. Observer feature matrix

`OC3_OBSERVER_FEATURE_MATRIX.csv` is required. It has six rows in frozen slot
order and contains Tier-A quantities only. The first columns are
`slot,region,brick,primary_geometry_role,observed_primary_geometry_status`.
Remaining columns expand in the
following exact group and band order (`g,r,z`):

1. **coverage**, per band:
   `nexp_zero_fraction`, `nexp_positive_fraction`, `nexp_distinct_levels`,
   `nexp_transition_count`, `nexp_transition_fraction`, `nexp_range`;
2. **weight/noise proxy**, per band:
   `invvar_finite_fraction`, `invvar_zero_fraction`,
   `invvar_positive_fraction`, `invvar_negative_fraction`, `invvar_median`,
   `invvar_iqr`, `invvar_relative_iqr`, `diagnostic_sigma_median`;
3. **masking**, once per slot:
   `maskbits_zero_fraction`, `maskbits_nprimary_fraction`,
   `maskbits_optical_any_fraction`, `maskbits_wise_any_fraction`, individual
   `maskbits_bit01_fraction` through `maskbits_bit07_fraction`, individual
   `maskbits_bit10_fraction` through `maskbits_bit13_fraction`, and
   `maskbits_unknown_fraction`;
4. **PSFSIZE**, per band:
   `psfsize_finite_fraction`, `psfsize_nonpositive_fraction`,
   `psfsize_median`, `psfsize_iqr`, `psfsize_relative_range`;
5. **PSF representation**, per band:
   `psf_height`, `psf_width`, `psf_finite_fraction_min`,
   `psf_raw_sum_min`, `psf_raw_sum_max`, `psf_raw_sum_range`,
   `psf_distinct_plane_hashes`, `psf_peak_displacement_max_pixels`;
6. **geometry**, once per slot:
   `primary_fraction`, `primary_boundary_transition_count`,
   `primary_center_boundary_distance_pixels`, `pixel_scale_center_arcsec`,
   `pixel_area_min_arcsec2`,
   `pixel_area_max_arcsec2`, `pixel_area_relative_range_5point`,
   `axis_ratio_max_5point`, `wcs_roundtrip_residual_max_pixel`.

Template names become `<metric>_<band>` for banded groups. No IMAGE-derived
column is permitted. Null remains empty with its reason available in the slot
metrics table. The matrix is descriptive observer structure; row distances are
not computed and must not be called morphological similarity.

## 14. Frozen observer contrasts

The required contrasts, in order, are:

```text
C01: S1 - S2
C02: S1 - S3
C03: N1 - N2
C04: N1 - N3
C05: S1 - N1   (south interior - north interior)
```

For every feature-matrix column, publish left and right values. For a numeric
feature, `signed_difference = left - right`. For categorical values the
difference is null and `comparison_state` is `EQUAL`, `DIFFERENT` or
`UNDEFINED`. No ratio, standardization, significance test, causal statement,
ranking or better/worse label is produced.

## 15. Prospective questions

The summary preserves these questions verbatim and answers them only from the
frozen outputs:

1. Did all six intended observational strata survive exact extraction?
2. How heterogeneous is exposure support within and between slots?
3. How heterogeneous is the inverse-variance/noise proxy?
4. Which optical mask conditions are present and how spatially prevalent are they?
5. How much PSFSIZE variation exists within and across windows?
6. Does provider coadd-PSF representation vary across P0/P1/P2 and bands?
7. Are south and north observational conditions different in ways a future encoder could potentially learn?
8. Does S2 expose its frozen boundary condition?
9. Does N2 expose a coverage discontinuity under its frozen class-0 rule?
10. Does N3 reproduce the deliberately selected PSFSIZE-variation condition?
11. Which observer variables, if any, warrant later prospective invariance or robustness experiments?

Question 7 and question 11 remain descriptive. This stage defines no threshold
for “material,” performs no encoder experiment and approves no preprocessing.

## 16. Interpretation states

These are evidence descriptions, not scientific PASS/FAIL gates:

- `OBSERVER_AUDIT_INCOMPLETE`: an authority, integrity, schema, inventory,
  numerical-definition or required-output gate did not complete.
- `STRATUM_NOT_EXPRESSED`: an exact intended predicate is false for S3 or N2,
  the N3 consistency value fails its frozen tolerance, S2 does not independently
  reproduce `MIXED_PRIMARY`, or S1/N1 do not reproduce `ALL_PRIMARY`. It never
  triggers replacement.
- `CONFOUND_VARIATION_OBSERVED`: the audit is complete and at least one
  prospectively defined witness is nonconstant: nonzero NEXP transitions,
  nonzero INVVAR IQR, nonzero optical/unknown mask prevalence, nonzero PSFSIZE
  range, more than one PSF plane hash across P0/P1/P2, or nonzero five-point WCS
  area range.
- `LIMITED_VARIATION_OBSERVED`: the audit is complete, all intended predicates
  are expressed, and none of those witnesses is nonconstant.

The summary may retain per-slot states. Its single overall descriptive state
uses precedence `OBSERVER_AUDIT_INCOMPLETE`, `STRATUM_NOT_EXPRESSED`,
`CONFOUND_VARIATION_OBSERVED`, `LIMITED_VARIATION_OBSERVED`. No state asserts
that confounds are absent or that morphology is valid.

## 17. Closed outputs and schemas

All outputs are staged beneath:

```text
oc3/CONFOUND_AUDIT/OC3-OBSERVATIONAL-CONFOUND-AUDIT-001/STAGING/
```

and promoted once to the stage root only after every required row and integrity
gate passes. Existing stage paths cause a fail-closed stop. No output contains
an image, array, thumbnail, plot, pixel coordinate list or label.

### 17.1 Slot metrics

`OC3_OBSERVER_AUDIT_SLOT_METRICS.csv` uses this exact header:

```text
slot,region,brick,tier,family,band,point_id,metric_id,level,value_int,value_float,value_text,unit,interpretation_scope,validity_state
```

Rows are ordered by slot; Tier A before B; families
`NEXP,INVVAR,MASKBITS,PSFSIZE,COADD_PSF,WCS_GEOMETRY,IMAGE`; then g/r/z,
P0/P1/P2 and the metric order in this specification. Exactly one value column
is populated. Dynamic NEXP levels and unknown MASKBITS positions use `level`.

### 17.2 Feature matrix and contrasts

`OC3_OBSERVER_FEATURE_MATRIX.csv` follows section 13 and has exactly six rows.

`OC3_OBSERVER_AUDIT_CONTRASTS.csv` uses:

```text
contrast_id,left_slot,right_slot,feature_id,left_value,right_value,signed_difference,unit,interpretation_scope,comparison_state
```

All contrast rows are `OBSERVER_ONLY` and follow C01–C05, then feature-matrix
column order.

### 17.3 Summary, terminal and log

`OC3_OBSERVER_AUDIT_SUMMARY.json` is canonical JSON plus LF with exact
top-level keys:

```text
schema_version,stage_id,state,input_bindings,method_bindings,slot_intents,
psf_normalization_decision,prospective_questions,question_evidence,
interpretation_states,output_hashes,aggregate,sealed
```

`sealed` is SHA-256 of the canonical object with `sealed` omitted.
`question_evidence` contains technical metric identifiers and descriptive
states, not free-form scientific interpretation.

`OC3_OBSERVER_AUDIT_TERMINAL.json` and `OC3_OBSERVER_AUDIT_RUN.log` are compact
canonical technical records. The log contains no metric values. Their
aggregate records slot/row/identity counts, tier-completion flags, read counts,
input modifications, images displayed, plots produced, morphology operations,
preprocessing operations and network requests.

Every successful artifact is read-only. SHA-256 is recorded for both CSVs, the
feature matrix and summary. Input hashes are rechecked after computation and
must be unchanged.

## 18. Success and failure

The sole success terminal is:

```text
OBSERVATIONAL_CONFOUND_AUDIT_COMPLETED
```

It requires all six slots, every frozen Tier-A and Tier-B metric, 18 PSF
responses, 54 plane identities, the five contrasts, sealed canonical outputs,
unchanged inputs, zero network, zero display, zero plot, zero preprocessing and
zero morphology operations. Success means only that the technical audit was
completed reproducibly.

An incomplete execution publishes no successful subset and uses
`OBSERVER_AUDIT_INCOMPLETE`. Natural observational variation never causes a
technical failure.

Completion does not mean confounds are absent, IMAGE is suitable,
preprocessing is approved, morphology is preserved or scientific discovery has
started.

## 19. Next decision boundary

After successful audit completion, a separate prospective decision must use
the frozen evidence to decide whether masks are inputs, exclusions or neither;
whether uncertainty is modeled explicitly; whether PSF variation is preserved,
conditioned on, matched or tested as a nuisance; whether coverage transitions
are represented; what information must not be normalized away; and which
augmentations would erase observationally relevant signal. This specification
answers none of those questions in advance.

**NEXT STEP: IMPLEMENT AND EXECUTE OBSERVATIONAL / CONFOUND AUDIT.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
