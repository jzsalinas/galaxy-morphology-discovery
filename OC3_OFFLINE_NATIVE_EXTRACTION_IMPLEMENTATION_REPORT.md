# OC-3 offline native extraction implementation report

**Stage:** `OC3-OFFLINE-NATIVE-EXTRACTION-001`

**Specification SHA-256:** `e5a86e69b97ca1daff42e44e9abfd823a5bb37ccf181f1aec4650dd88264c6d2`

**Implementation aggregate:** `68ccc701690300445399f417903779c8be6c8648aaabb4818bb423aeaf6af7fb`

## Implementation boundary

The implementation adds `oc3/oc3lib/native_extraction.py`, the offline CLI
`oc3/oc3_offline_native_extraction.py`, and focused synthetic tests in
`oc3/tests/test_native_extraction.py`. It updates the OC-3 README and ignore
rules for runtime extraction artifacts. Historical acquisition hashing is
anchored to its already frozen implementation aggregate, and two historical
test tripwires now recognize the completed fixed-native authorization and the
future extraction manifest without broadening either inventory.

The CLI has only `--validate-inputs` and `--extract`. It contains no network
transport or network mode. Input validation binds the exact frozen authorities,
states, seals, source paths, body hashes, shapes, dtypes, HDUs, locations and PSF
identities before a section can be decoded.

## Bounded FITS section access

The production accessor opens each local tiled-compressed FITS body read-only
and obtains exactly `hdu.section[y0:y1, x0:x1]`. It rejects a non-compressed
image HDU, invalid bounds, a preloaded HDU, any post-section `_data_loaded`
state, a shape other than 129×129, or a dtype-descriptor change. It records only
section-call, authorized-element, full-plane-materialization and unauthorized-
pixel counters.

The focused suite exercises a real tiled-compressed FITS image with explicit
50×50 tiles and a 129×129 section crossing tile boundaries. It also uses an
instrumented compressed-HDU double whose `.data` property raises immediately;
the accessor succeeds through `.section`, returns exactly the requested slice,
and exposes no adjacent pixels. A source scan rejects the full-plane access
patterns `hdu.data` and `.getdata(` in the implementation.

## Preservation and publication gates

Every source section is serialized with NumPy NPY v1.0, reloaded, and compared
for exact dtype descriptor, shape and C-order bytes. The array-content hash and
artifact hash are independently recomputed. The tests cover non-native byte
order, NaN payload bytes, infinities, signed zero, exact canonical hashing, WCS
translation, immutable atomic promotion, companion-array non-mutation of IMAGE,
failure without manifest publication and refusal of a second publication.

The synthetic publication test produces exactly 78 arrays, 18 PSF references
and 54 unique PSF observational identities. It verifies the manifest seal,
exact top-level schema, artifact hashes and read-only files. Recursive
anti-interpretation tripwires reject every frozen scientific-summary field.

## Validation results before real extraction

- Focused suite: **17 passed, 0 failed, 0 skipped**.
- Complete offline regression: **845 passed, 0 failed, 0 skipped**.
- Regression network counter: **`real_network_requests=0`**.
- Frozen-input prevalidation: **`NATIVE_EXTRACTION_INPUTS_VALIDATED`** with
  78 planned crops, 18 PSF mappings, zero network requests and zero science
  pixels accessed.
- Syntax and diff checks: passed.

No real science pixel was accessed while creating this report. No image was
displayed and no scientific statistic, morphology operation, preprocessing,
normalization, mask application or PSF array decode was performed.
