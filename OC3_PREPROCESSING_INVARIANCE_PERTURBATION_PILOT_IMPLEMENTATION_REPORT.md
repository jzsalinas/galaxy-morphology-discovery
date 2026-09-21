# OC3 preprocessing / invariance perturbation pilot implementation report

**Stage:** `OC3-PREPROCESSING-INVARIANCE-PERTURBATION-PILOT-001`

**Specification SHA-256:** `4ef5b16a9cc9de25ca194bdbf947bae8491035692fb3499356393093d919f1cd`

**Terminology clarification SHA-256:** `42c13760a18e1c88189a1bf02ac63546eae1d1c85296b4a57e55dfff06e30052`

**Implementation aggregate:** `c4c0a03ebaaf6178c4ebb3151d39f37e705b2007f1b36083f7764d5cc3007514`

## Implementation boundary

The implementation adds:

- `oc3/oc3lib/preprocessing_perturbation_pilot.py`;
- `oc3/oc3_preprocessing_invariance_perturbation_pilot.py`; and
- `oc3/tests/test_preprocessing_invariance_perturbation_pilot.py`.

The OC-3 README records the new offline CLI. `.gitignore` excludes only the prospective runtime publication root. No historical stage, native array, frozen location, decision document, or specification was changed.

Current terminology is enforced as two technical development bricks, six observational windows, and zero astronomical objects defined. Runtime artifacts use no galaxy/object interpretation for the six windows.

## Authority and native-input gate

Both CLI modes bind the exact specification, decision, terminology clarification, native manifest and seal, native terminal, frozen locations, observer-audit metrics, and observer-audit terminal. Production execution cannot start transformations until all 78 read-only native `.npy` artifacts have passed artifact hash, array-content hash, NPY v1.0, shape, dtype, C-order, manifest-order, path, and permission checks.

The production prevalidation completed with state `PERTURBATION_PILOT_INPUTS_VALIDATED`: 78 native artifacts, 18 PSF provenance records, 6 windows, zero decoded array values, zero transformations, zero network requests, zero model operations, and zero morphology operations.

Parent coadds and provider PSF arrays are never opened by this stage. A final input-hash replay detects any native mutation before publication.

## Branch implementation

The closed branch classification is:

- 9 executable entries: B00, B01, B02, B03, B12, B13, B14_G_ONLY,
  B14_R_ONLY, and B14_Z_ONLY, corresponding to 7 decision-document families;
- 1 metadata-only branch: B09;
- 4 representation-stage reservations: B04, B05, B07, and B10; and
- 4 blocked branches: B06, B08, B11, and B15.

B00 publishes exactly 18 native IMAGE references and no array. B14 publishes 18 slot/subbranch reference rows for g-only, r-only, and z-only and no array. B09 regenerates its six technical strata from the frozen audit CSV and never weights, excludes, or changes a window. Reserved and blocked branches create only closed manifest/register entries.

The executable transformed-array inventory is exactly:

```text
B01 = 36
B02 = 36
B03 = 18
B12 = 234
B13 = 156
total = 480
```

## Exact constants and arithmetic

B01 uses the binary32 constants `0x3f000000` (`0.5`) and `0x40000000` (`2.0`). B02 uses the exact signed binary32 development-reference constants:

```text
g = ±0.003173012984916568  (0x3b4ff253 / 0xbb4ff253)
r = ±0.006205183453857899  (0x3bcb54da / 0xbbcb54da)
z = ±0.01568971388041973   (0x3c8087b7 / 0xbc8087b7)
```

B03 divides every slot by the corresponding positive band constant and records `DEVELOPMENT_ONLY_SCALE` plus `NOT_AUTHORIZED_AS_FUTURE_TRAINING_SCALE`. All scalar paths allocate a new array with the exact source float32 dtype descriptor, use a float32 operational scalar and output, perform no clipping, and calculate only the frozen technical metrics and round-trip diagnostics.

## Geometry, WCS, and PSF limitation

B12 implements exact NumPy-equivalent 90°, 180°, and 270° integer-lattice rotations. B13 implements horizontal and vertical exact reflections separately. Each variant permutes all 13 native maps per slot, creates a C-contiguous canonical copy, preserves dtype and the multiset of element bytes, and requires exact inverse bitwise reconstruction. Synthetic tests cover non-native endian arrays, distinct NaN payloads, infinities, and signed zero.

The WCS adapter uses only the frozen old-to-new integer affine `(A,t)` and evaluates the immutable native WCS at inverse-mapped coordinates. It checks center, four corners, and four edge midpoints against the `1e-6` native-pixel residual limit without rewriting or refitting provider cards.

Provider PSF arrays are not transformed. Every geometry variant records:

```text
provider_psf_response_transform = NOT_EXECUTED
psf_provenance_retained = true
known_semantic_limitation = TRANSFORMED_WINDOW_HAS_NO_TRANSFORMED_PROVIDER_PSF_RESPONSE
```

## Outputs and fail-closed behavior

Generated arrays use the native canonical uncompressed NPY v1.0 contract and are independently re-read and rehashed. The stage writes 480 closed technical-metric rows, 23 information-loss rows, 6 NEXP rows, an immutable branch manifest, summary, terminal, and compact run log. Successful publication is atomic and read-only.

There is no resume mode. An existing stage, terminal, publication-ready path, or partial execution refuses a rerun. Failure leaves no successful subset and records `PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_FAILED`. Success records `PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_COMPLETED` but selects no scientific preprocessing and authorizes no representation learning.

## Offline validation

- Focused synthetic suite: **33 passed, 0 failed, 0 skipped**.
- Complete offline regression: **902 passed, 0 failed, 0 skipped**.
- Regression network counter: **`real_network_requests=0`**.
- Complete synthetic publication: exactly 480 transformed arrays, 480 technical rows, 23 information-loss rows, 30 WCS-adapter rows, 18 B00 references, 18 B14 references, and 6 B09 mappings.
- Production input prevalidation: passed with zero array-value decodes.
- Syntax, CLI help, frozen-hash, canonical serialization, source-capability, and diff checks: passed.

The focused and full tests used temporary synthetic arrays only. No production transformation was executed.

## Human execution handoff

Run from `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
oc3/.venv/bin/python oc3/oc3_preprocessing_invariance_perturbation_pilot.py --execute-pilot --project /home/jzsalinas/Documents/galaxy-morphology-discovery
```

Expected input payload is approximately 4.20 MiB across the 78 native `.npy` artifacts. Expected published output is below 64 MiB and contains exactly 480 transformed arrays. Expected wall time is approximately 1–5 minutes on the prepared local environment. Network requests, model operations, and morphology operations must remain zero.

The internal log is:

```text
oc3/PERTURBATION_PILOT/OC3-PREPROCESSING-INVARIANCE-PERTURBATION-PILOT-001/OC3_PERTURBATION_PILOT_RUN.log
```

The success sentinel is the terminal file at the same root with state `PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_COMPLETED`. A failure or interruption is not resumable. Do not delete or repair its stage root; a new prospective decision is required before another attempt.

## Execution declaration

**REAL PRODUCTION PILOT NOT EXECUTED.**

Implementation and validation used zero network requests, zero labels, zero image display, zero plots, zero models, zero encoders, zero embeddings, zero clustering, and zero morphology operations.

**OC-3 MORPHOLOGICAL DISCOVERY PHASE REMAINS NOT STARTED.**
