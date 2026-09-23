# OC3 PHOTSYS zero-byte semantic provenance implementation report

## Result and boundary

The implementation and offline preflight for `OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001` are complete. The research remains in `PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_RESEARCH_NOT_STARTED` pending separate human review and final authorization.

No network request was made. No astronomical FITS table byte, PHOTSYS byte, BRICKNAME value, BRICKID value, or ROOT value was read. The historical histogram was verified only through its sealed artifact and frozen hashes; its executor was not rerun. PHOTSYS V1 was not amended, no resolver was created, and Panel V2 and P1 were not run.

## Architecture

The implementation consists of:

- `oc3/oc3lib/photsys_zero_byte_provenance.py`: frozen-input validation, exact resource manifest, authorization boundary, bounded transport, archive safety, deterministic source-tree hashing/search, evidence parsers, producer trace, claim matrix, and four-outcome gate;
- `oc3/oc3_photsys_zero_byte_provenance.py`: CLI with `--validate-inputs`, `--dry-run`, `--research-zero-byte-provenance`, and the separately gated optional `--run-synthetic-zero-initialization-check` mode;
- `oc3/tests/test_photsys_zero_byte_provenance.py`: 36 synthetic/offline tests;
- `oc3/INPUTS/OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESOURCE_MANIFEST_001.json`: sealed five-resource allowlist;
- `oc3/INPUTS/OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESEARCH_CANDIDATE_001.json`: sealed human-review candidate.

The future transport accepts resource identifiers rather than arbitrary URLs. It rejects alternate hosts, paths, queries, fragments, redirects, compressed transfer representations, astronomical `.fits` URLs, over-cap bodies, and resources outside the sealed manifest. Source extraction rejects absolute paths, traversal, links, special members, wrong top-level prefixes, excess members, excess expanded bytes, and missing mandatory files.

## Frozen public resources

Resource manifest SHA-256: `e43b5514a81680eb7f602525d76b42aae8bae6ab72a32de02e4b1f7f8a6685e6`.

The exact allowlist is:

1. `https://fits.gsfc.nasa.gov/standard40/fits_standard40aa-le.pdf` — official NASA FITS Standard 4.0 PDF, 4 MiB cap;
2. `https://www.legacysurvey.org/dr9/files/` — official DR9 file documentation, 1 MiB cap;
3. `https://api.github.com/repos/desihub/desitarget/git/ref/tags/0.48.0` — exact tag-ref metadata, 128 KiB cap;
4. `https://api.github.com/repos/desihub/desitarget/git/tags/1957b46481368c3b386a2113dc734538650c492c` — annotated-tag metadata, 128 KiB cap;
5. `https://codeload.github.com/desihub/desitarget/tar.gz/refs/tags/0.48.0` — complete exact-tag source archive, 14 MiB cap.

The future stage must independently verify annotated tag object `1957b46481368c3b386a2113dc734538650c492c` and resolved commit `dd30297f9d50fcb7bbba57d79d4b8fc86cb35701`. These values remain expected candidates, not present authority.

The first research candidate permits exactly five public documentary/source requests, 20 MiB of response bodies, zero retries, and concurrency one. It permits zero astronomical-data GETs.

## Offline evidence processing

The FITS extractor records title, version, normative status, section/page fields, detected pages, documentary text hash, the `0x00` null-string proposition, the `0x20` space proposition, their distinction, and an explicit absence of survey-footprint meaning.

The Legacy Survey parser targets `survey-bricks-dr9-randoms-0.48.0.fits`, records the documented N, S, and outside categories, and preserves outside as a literal single space. It records that the current page has not yet been proven identical to its DR9-production-time form.

After safe extraction, the complete source tree is hashed deterministically. The required files are `py/desitarget/randoms.py`, `bin/select_randoms`, `bin/supplement_randoms`, `py/desitarget/io.py`, and `doc/changes.rst`. Source evidence records file hashes and line hashes. The exact offline search terms are `survey-bricks`, `survey-bricks-dr9-randoms`, `AREA_PER_BRICK`, `PHOTSYS`, `supplement_randoms`, `zeros=True`, `write_randoms`, and `resolve`.

If the named generator is absent, the implementation records `DESITARGET_0_48_0_NAMED_SUMMARY_GENERATOR_NOT_FOUND` and `NAMED_PRODUCT_GENERATION_PROVENANCE_UNRESOLVED`. It does not request newly suggested resources or infer the missing link.

## Claim and outcome gates

The claim matrix uses only the six frozen evidence classes and four frozen statuses. It preserves observation, official documentation, FITS representation, producer source, independent footprint evidence, and inference as separate rows.

The outcome gate implements exactly:

- `PHOTSYS_0x00_OUTSIDE_SEMANTICS_PROVEN`;
- `PHOTSYS_0x00_REPRESENTATION_MISMATCH_BUT_OUTSIDE_MAPPING_SUPPORTED`;
- `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE`;
- `PHOTSYS_DOCUMENTATION_PHYSICAL_CONFLICT_UNRESOLVED`.

Count coincidence, zero initialization, and FITS null-string semantics are explicitly non-gating without the exact producer outside pathway, serialization preservation, and named-product generation provenance.

## Optional synthetic demonstration

The `np.zeros(..., dtype='|S1')` demonstration is implemented behind a distinct CLI mode. It imports NumPy lazily and would emit only the NumPy version, dtype, raw synthetic byte, and result. It was not executed because this task did not include a separate final authorization for that mode.

## Offline verification

- Focused new-stage tests: 36 passed, 0 failed, 0 skipped.
- Affected regression: 204 passed, 0 failed, 0 skipped.
- Complete offline regression: 1132 passed, 0 failed, 0 skipped; `real_network_requests=0`.
- `--validate-inputs`: `PHOTSYS_ZERO_BYTE_PROVENANCE_INPUTS_VALIDATED`, network requests 0 and all no-data counters 0.
- `--dry-run`: `READY_AT_PUBLIC_DOCUMENTARY_RESEARCH_BOUNDARY`, network requests 0 and all no-data counters 0.

The implementation aggregate is `c6af772355af20a5711d42c2e26d0af5c3b541a54ffa31e373ab87b61c880381`.

## Human-review candidate

Candidate path: `oc3/INPUTS/OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESEARCH_CANDIDATE_001.json`

Candidate SHA-256: `ea3052d541e92b375630c4d317a6656b79d02a5713e883f6a5ee387795d6d9c0`

Command argv SHA-256: `a9c756963b6771cbae6c2dc33f4ef6d1327666dadfc1bcaaa8490a8134228ed1`

Exact future command:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_photsys_zero_byte_provenance.py --research-zero-byte-provenance --execute-public-documentary-research --candidate /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESEARCH_CANDIDATE_001.json --authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESEARCH_FINAL_AUTHORIZATION_001.json --output-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/photsys_zero_byte_provenance/OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001
```

The final authorization artifact is absent. The command must not be run until that separate artifact is created after human review.
