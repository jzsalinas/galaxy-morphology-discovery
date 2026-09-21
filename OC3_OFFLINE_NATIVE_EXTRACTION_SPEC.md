# OC-3 offline native extraction specification

**Stage:** `OC3-OFFLINE-NATIVE-EXTRACTION-001`

**Status:** prospective specification only

**Network:** prohibited

**Scientific interpretation:** prohibited

## 1. Purpose and authority

This stage defines the first authorized OC-3 science-pixel boundary. It asks
only whether the six frozen 129×129 native windows can be reproduced exactly
from the acquired DR9 products while preserving values, dtype, geometry and
provenance. It does not ask or answer a morphological question.

Execution must validate these frozen inputs before decoding any array:

| Authority | Required state or SHA-256 |
|---|---|
| `MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md` | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| Location selection | `LOCATION_SELECTION_VALIDATED` |
| Selection SHA-256 | `2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860` |
| `OC3_LOCATIONS.json` | `33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1` |
| Auxiliary resolved contract | `5afff8fddbcb8a9e86ea3f55cf89288840a21ca705bca121ed1b9204c349616d` |
| Auxiliary acquisition terminal | `0f39b8f24d2dd2b13590a153f30f7050d5c6f44b3d1d39bc38725b0353eda75b` |
| Auxiliary acquisition ledger | `2fa6121a5ee08f8150c723d2069bcf357f25b67f6a02d14375d84c4265e94ee6` |
| Fixed-native/PSF candidate | `961a763e5732b38c5193764a785a3799b0a74e9e42de111fa1de08c8d4cc2951` |
| Fixed-native/PSF terminal | `ca55cd8cd4009b2e5af2466abf6cd08ac3e6b1c2811f3d41fbe7bea495eda875` |
| Fixed-native/PSF ledger | `fac57a450cb263799e0940c430f730e92835d308c537a8323c3ac4e129b5476c` |
| `OC3_PSF_IDENTITIES.json` | `8c8ec5a14169154fce82f6b7a6de147d08e749ba5b410974fd920411b8fe9036` |
| Acquired-product terminal | `BOUNDED_NATIVE_PRODUCTS_ACQUIRED` |

Only bodies under the two acquisition `RAW_IMMUTABLE` roots are input
authorities. `STAGING`, provider URLs and network responses are not inputs.
Every source body must match the SHA-256 recorded in its acquisition ledger
before any pixel decode. No location, brick, band, source identity or PSF point
may be replaced.

## 2. Exact extraction unit

Slots are ordered `S1,S2,S3,N1,N2,N3`. For the already frozen 0-based integer
center `(x,y)`, the exact bounds are:

```text
x0 = x - 64    x1 = x + 65
y0 = y - 64    y1 = y + 65
FITS-array slice = parent[y0:y1, x0:x1]
slice_bounds_xy = [x0,y0,x1,y1]
```

The output shape is exactly `(129,129)`, with the frozen center at output index
`[64,64]`. `requested == obtained`, `offset_in_requested == [0,0]`,
`padding=false` and `resampling=false` are mandatory. Sky coordinates and WCS
metadata may validate provenance but can never modify these bounds.

The implementation must use a bounded FITS section accessor or equivalent. It
must not expose or decode parent pixels outside the six authorized windows and
must not load a complete 3600×3600 science plane merely for convenience.

## 3. Closed crop inventory

For each slot, extract exactly these thirteen arrays in this order:

```text
image-g.npy       image-r.npy       image-z.npy
invvar-g.npy      invvar-r.npy      invvar-z.npy
nexp-g.npy        nexp-r.npy        nexp-z.npy
psfsize-g.npy     psfsize-r.npy     psfsize-z.npy
maskbits-optical.npy
```

Across six slots this is exactly 78 arrays. Observed source dtypes are binding:

| Product | Count per slot | Required decoded/output dtype |
|---|---:|---|
| image | 3 | `float32` |
| invvar | 3 | `float32` |
| nexp | 3 | `int16` |
| psfsize | 3 | `float32` |
| maskbits | 1 | `int16` |

All source maps have shape `(3600,3600)`. The output retains the decoded dtype
descriptor, including byte order. No cast, scaling, normalization, background
subtraction, clipping, thresholding, masking, NaN/Inf replacement,
interpolation, rotation, recentering, resizing or derived channel is permitted.
`MASKBITS` and `INVVAR` accompany image pixels but never modify them.

## 4. Canonical array artifact and content hash

Each crop is an uncompressed NumPy `.npy` v1.0 file written with
`numpy.lib.format.write_array(..., version=(1,0), allow_pickle=False)` from a
C-contiguous 2D numeric array. The writer must freeze `fortran_order=false`,
shape `(129,129)` and the exact source `numpy.dtype.str`. Object or structured
dtypes are rejected. The implementation records its NumPy version; the frozen
environment currently provides NumPy 2.5.3.

Two hashes have distinct meanings:

1. `artifact_sha256` is SHA-256 over every byte of the `.npy` file.
2. `array_content_sha256` is SHA-256 over this exact byte sequence:

```text
UTF-8("OC3_ARRAY_CONTENT_V1\n")
+ canonical_json({"dtype": dtype.str, "order": "C", "shape": [129,129]})
+ LF
+ array.tobytes(order="C")
```

`canonical_json` uses sorted keys, compact separators, UTF-8,
`ensure_ascii=false` and `allow_nan=false`; this restriction applies to the
metadata JSON, not to numeric array bytes. The source slice and the reloaded
output must have identical dtype descriptors, shapes and C-order bytes. This
bitwise gate preserves NaN payloads and signed zero and is stronger than a
numeric tolerance comparison.

## 5. WCS and geometry provenance

Every crop retains both representations already required by the frozen OC-3
design:

- the exact parent WCS card/value model and its canonical SHA-256;
- the parent source identity, body SHA-256, logical/physical HDU and native
  shape;
- the integer origin `[x0,y0]` and half-open bounds `[x0,y0,x1,y1]`;
- a translated cutout WCS derived mechanically from the parent.

For the translated FITS WCS, all supported WCS terms remain identical except:

```text
CRPIX1_crop = CRPIX1_parent - x0
CRPIX2_crop = CRPIX2_parent - y0
```

No distortion term, CD/PC matrix, CDELT, CRVAL, CTYPE, unit or projection may
be dropped or refitted. The translated WCS must reproduce the parent sky
mapping at output center and four corners with a round-trip residual no larger
than the already frozen bookkeeping tolerance of `1e-6` native pixel. An
unsupported parent WCS fails the stage; it is not simplified. WCS never affects
pixel selection after the frozen integer bounds are loaded.

## 6. PSF reference model

PSF arrays are not cropped, decoded, normalized, padded, resized, split or
rewritten. The extraction manifest contains exactly eighteen immutable
references in slot order and point order `P0,P1,P2`. Each reference binds:

```text
slot, region, brick, point_id, transport_id,
source_response_path, source_response_sha256,
plane_mapping = {g: physical_hdu 0, r: physical_hdu 1, z: physical_hdu 2},
observational_identity_ids, native_provider_shapes
```

South shapes remain `g/r/z = 63×63/63×63/63×63`; north shapes remain
`31×31/31×31/63×63`. The eighteen bodies must map to exactly 54 unique
observational identities. Band-level entries may reference the same provider
body; they must not create new PSF files.

## 7. Publication and manifest

The stage root is:

```text
oc3/NATIVE_EXTRACTION/OC3-OFFLINE-NATIVE-EXTRACTION-001/
```

Arrays are first written beneath `STAGING/<slot>/`. Nothing is promoted until
all 78 source-equality gates and all 18 PSF mappings pass. Successful arrays are
atomically moved without rewriting to read-only paths:

```text
RAW_IMMUTABLE/<slot>/<exact filename from section 3>
```

The sole row-level index is canonical JSON at:

```text
oc3/TECHNICAL_INDEX/OC3_NATIVE_EXTRACTION_MANIFEST.json
```

Its exact top-level keys are:

```text
schema_version,stage_id,state,authority_bindings,format_contract,
crops,psf_mappings,aggregate,sealed
```

`crops` contains 78 entries in slot/product/band order. Each entry binds:

```text
slot,region,brick,product,band,source_resource_id,source_path,
source_body_sha256,source_shape,source_dtype,source_hdu,
slice_bounds_xy,output_shape,output_dtype,artifact_path,
array_content_sha256,artifact_sha256,wcs_provenance
```

For `maskbits`, `band=null`. `psf_mappings` contains the eighteen entries from
section 6. `aggregate` contains only the permitted technical counts. `sealed`
is SHA-256 of the canonical object with `sealed` omitted. The file itself is
canonical JSON plus one LF.

The stage also emits canonical, compact, non-scientific:

```text
OC3_NATIVE_EXTRACTION_AUDIT.json
OC3_NATIVE_EXTRACTION_TERMINAL.json
OC3_NATIVE_EXTRACTION_RUN.log
```

Successful artifacts are read-only. Existing stage or manifest paths cause a
fail-closed stop; there is no overwrite, partial promotion or automatic resume.
RAW inputs and acquisition evidence are never modified or deleted.

## 8. Source-slice gate and terminals

For every crop, the implementation must hash the authorized source section,
serialize it, reload the `.npy`, and require exact equality of dtype descriptor,
shape and C-order bytes. It then recomputes both hashes independently. A wrong
source hash, bounds, HDU, shape, dtype, WCS, value byte, filename or inventory
fails the entire stage. Outputs are never repaired.

Success terminal:

```text
NATIVE_EXTRACTION_VALIDATED
```

It requires all of the following:

```text
slots=6
crop_arrays=78
psf_response_mappings=18
psf_observational_identities=54
padding_count=0
resampling_count=0
shape_failures=0
dtype_failures=0
source_equality_failures=0
unauthorized_product_observations=0
network_requests=0
```

The single failure terminal is `NATIVE_EXTRACTION_FAILED`. A failure may retain
staging, log and technical failure evidence, but publishes no manifest and no
successful subset.

## 9. Pixel-access and anti-interpretation boundary

Science arrays may be decoded only for the exact bounded slice, shape/dtype
validation, bytewise source/output equality, serialization and integrity
hashing. The stage must not calculate or emit flux summaries, extrema, moments,
histograms, finite-value fractions, detections, centroids, segmentation,
morphology, thumbnails, composites, plots, quality scores or any statistic for
scientific interpretation. Aggregate evidence is limited to the counts in
section 8 plus elapsed/resource bookkeeping.

No output may trigger display, rejection, replacement, preprocessing, encoder
work or training. Empty, contaminated or visually inconvenient crops remain
authoritative if their technical gates pass. The next stage is a separately
prospective observational/confound audit.

## 10. Future implementation and tests

The future CLI is `oc3/oc3_offline_native_extraction.py`. It provides
`--validate-inputs` and `--extract`, accepts only local canonical paths, imports
no HTTP client and has no network mode. It validates every frozen binding and
the complete output plan before first pixel access, restricts decoding through
the bounded-section accessor, and refuses a pre-existing publication.

Expected work is small: 148,593,600 bytes (about 141.7 MiB) of local source
bodies are integrity-scanned, 78 bounded sections are decoded, and raw crop
payload is 4,393,224 bytes plus deterministic `.npy` headers and JSON. No bulk
acquisition or long-running handoff is expected.

Focused synthetic tests must cover exact half-open slicing and center
conventions; all six edge layouts; dtype and byte-order preservation; NaN/Inf
and signed-zero preservation; no MASKBITS/INVVAR modification of image;
canonical `.npy` and array-content hashes; bytewise source/output equality;
parent and translated WCS reproducibility; exact 78/18/54 inventories; wrong
source hash/HDU failure; unauthorized-product and full-plane-decode tripwires;
zero network; no scientific-summary leakage; atomic immutable publication; and
refusal of a second publication.

This specification authorizes no implementation and reads no science pixel.

**NEXT STEP: IMPLEMENT AND EXECUTE OFFLINE NATIVE EXTRACTION.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
