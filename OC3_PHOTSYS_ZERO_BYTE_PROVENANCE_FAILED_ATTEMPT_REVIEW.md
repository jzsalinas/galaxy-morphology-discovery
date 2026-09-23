# OC3 PHOTSYS zero-byte provenance failed-attempt review

## Historical closure

The execution of `OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001` is closed with terminal `PHOTSYS_ZERO_BYTE_RESEARCH_INTEGRITY_STOP` and scientific outcome `null`. Its final authorization is consumed. The attempt must not be resumed, rerun, overwritten, or represented as a completed semantic investigation.

The immutable terminal is:

`oc3/photsys_zero_byte_provenance/OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001/TERMINAL.json`

Its SHA-256 is `fef519e21342cea7dee90ec25861ffc086f05b9643370eaa1b34de4785a946a3`.

Five public-source requests were initiated. Four successful bodies are preserved:

| Resource | Relative path | Bytes | SHA-256 |
|---|---|---:|---|
| FITS Standard 4.0 | `RAW_IMMUTABLE_PUBLIC_SOURCES/FITS_STANDARD_4_0.body` | 1140821 | `5624dca15659caf54c56127b4df9af05fd930c8f6d997fcb4bea2b1a5c1bc573` |
| Legacy Survey DR9 documentation | `RAW_IMMUTABLE_PUBLIC_SOURCES/LEGACY_SURVEY_DR9_FILES.body` | 187585 | `d0b51d66529cb4c62db7e8ae1df22d6976879f46dcd62b4e6993729b42674c85` |
| desitarget tag ref | `RAW_IMMUTABLE_PUBLIC_SOURCES/DESITARGET_TAG_REF.body` | 339 | `9289a01c82464f9ffe901b907e165c2c9bb7de7c3e17e454d112a3eb6ae2476d` |
| desitarget annotated tag object | `RAW_IMMUTABLE_PUBLIC_SOURCES/DESITARGET_TAG_OBJECT.body` | 684 | `c8a62b156a83788ae395ad2d866bdc114a958f3af93984326594d0c5dabeaef8` |

The preserved-body subtotal is four requests and 1329429 application body bytes. A later separately reviewed provenance stage may reuse these exact bodies offline after rebinding their paths, sizes, and hashes. Their presence does not authorize a continuation or any network request.

## Failed fifth resource and accounting limitation

The fifth request targeted exactly:

`https://codeload.github.com/desihub/desitarget/tar.gz/dd30297f9d50fcb7bbba57d79d4b8fc86cb35701`

The historical per-resource cap was 14680064 bytes. No archive body was published. The failed implementation did not preserve enough response evidence to distinguish whether it rejected a declared `Content-Length` greater than the cap before reading a body, or read 14680065 application bytes when no usable length was available and then rejected them without charging the historical counter.

The historical terminal counter of 1329429 is retained verbatim and is not redefined as exact total transfer. The conservative possible total application-body interval for the historical attempt is:

```text
minimum_possible_total_body_bytes = 1329429
maximum_possible_total_body_bytes = 16009494
```

These are application-level accounting bounds, not claims about physical wire or TLS bytes.

The parent prospective maximum is 33554432 bytes. Under the conservative historical maximum, the remaining pre-observation body budget is exactly 17544938 bytes.

## No-data firewall

The historical terminal records zero astronomical-data GETs, zero real PHOTSYS bytes observed, zero BRICKNAME values observed, zero BRICKID values observed, and zero ROOT values observed. No semantic outcome was selected. PHOTSYS V1 remains historically failed.

## Separate prospective HEAD-only boundary

The next permissible network operation is a new stage, `OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-HEAD-PROBE-001`, with scope `DESITARGET_COMMIT_ARCHIVE_SIZE_ONLY`. It may issue exactly one HEAD request to the literal commit-pinned archive URL, with zero redirects, zero retries, concurrency one, and zero authorized body bytes. GET, Range, fallback acquisition, archive decoding, and semantic research are prohibited.

Success requires an HTTP success response, the same literal URL, zero application body bytes read, a valid positive `Content-Length`, an accepted archive `Content-Type`, identity content encoding, and no astronomical access. Missing or unusable `Content-Length` produces `DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE` without GET fallback.

If the observed length is at most 17544938 bytes, a later separately reviewed archive-acquisition candidate may be designed. If it is greater, the current 32 MiB prospective specification cannot accommodate the archive under conservative cumulative accounting and the decision is STOP pending a new amendment or alternate provenance strategy.
