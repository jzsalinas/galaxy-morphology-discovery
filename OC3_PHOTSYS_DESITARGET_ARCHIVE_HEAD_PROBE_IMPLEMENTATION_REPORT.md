# OC3 desitarget archive HEAD probe implementation report

## Historical attempt closure

`OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001` remains closed at `PHOTSYS_ZERO_BYTE_RESEARCH_INTEGRITY_STOP` with scientific outcome `null`. Its authorization is consumed, its runtime tree is immutable, and neither resume nor rerun is permitted. The failure occurred on the fifth public resource, the exact commit-pinned desitarget archive. No archive body was published.

Four successful public-source bodies remain reusable offline only by their exact frozen paths, sizes, and SHA-256 values. Their subtotal is 1329429 application body bytes across four requests. The failed implementation did not retain enough response evidence to distinguish a header-only rejection from a cap-plus-one application read. The historical possible total therefore remains the conservative interval 1329429 through 16009494 bytes; it is not an exact wire or TLS byte claim.

## Prospective transport correction

`DocumentaryTransport` now records available resource identity, literal URL, HTTP status, headers, declared `Content-Length`, `Content-Type`, `Content-Encoding`, and UTC observation time before body acceptance. It increments `application_body_bytes_read` as bytes are returned to application code and before enforcing per-resource or cumulative caps. A failed request writes a sealed durable receipt, when an output receipt directory is available, containing the response metadata, failure code, application-read count, and cumulative counters. The receipt explicitly disclaims wire/TLS-byte precision.

Synthetic tests cover rejection from a declared length above the cap with zero body reads, unknown length with cap-plus-one retained, cumulative-cap failure after bytes are counted, and Content-Type failure with response identity retained.

## Separate HEAD-only stage

The new stage is `OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-HEAD-PROBE-001`, scoped to `DESITARGET_COMMIT_ARCHIVE_SIZE_ONLY`. Its transport exposes one exact `HEAD` operation for the commit-pinned codeload URL. It exposes no GET, Range, generic request, redirect, retry, archive decoding, or semantic-research capability. The frozen limits are one request, zero body bytes, zero redirects, zero retries, and concurrency one.

A valid positive `Content-Length` with an HTTP success response, accepted archive content type, identity content encoding, the unchanged literal URL, zero body reads, and a clean no-data firewall produces `DESITARGET_COMMIT_ARCHIVE_SIZE_OBSERVED`. Missing or unusable `Content-Length` produces `DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE` without fallback. Redirects and other contract failures fail closed.

The parent maximum remains 33554432 bytes. Subtracting the historical worst-case 16009494 bytes freezes a remaining conservative body budget of 17544938 bytes. A later, separately reviewed archive acquisition may be designed only when the observed length is at most that threshold. A greater length stops the current 32 MiB specification and requires an amendment or alternate provenance strategy.

## Offline validation

- Focused regression: 67 tests passed, 0 failed.
- Affected regression: 235 tests passed, 0 failed.
- Complete offline regression: 1163 tests passed, 0 failed, 0 skipped; `real_network_requests=0`.
- `--validate-inputs`: `DESITARGET_ARCHIVE_HEAD_PROBE_INPUTS_VALIDATED`, with zero network and zero astronomical access.
- `--dry-run`: `READY_AT_DESITARGET_COMMIT_ARCHIVE_HEAD_BOUNDARY`, with zero network and zero body bytes.
- Astronomical-data GETs, real PHOTSYS bytes, BRICKNAME values, BRICKID values, and ROOT values observed by this implementation task: 0.

The implementation aggregate is `24e9d4176105ce6ec9d3351fc6a5beba624728759d460067dd4553710b38bc83`.

The sealed human-review candidate is `oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_HEAD_PROBE_CANDIDATE_001.json`, SHA-256 `50e957873994c6330577a2b38d3ff3a3a00884ded076b9bd88447edf530b3a95`. Its command argv SHA-256 is `2bccac184f2bd8b617b5d0c9af716eab07a8ce51675383a6d46ca2ed05fad5e1`. The final authorization artifact is absent. No network request was made and the HEAD probe was not executed.
