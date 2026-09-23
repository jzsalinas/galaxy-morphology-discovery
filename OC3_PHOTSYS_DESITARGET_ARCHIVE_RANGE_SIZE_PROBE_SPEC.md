# OC3 PHOTSYS desitarget archive Range-size probe specification

Status: prospective and frozen before real execution.
Stage: `OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-RANGE-SIZE-PROBE-001`
Scope: `DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_ONLY`

## Scientific and operational question

This stage asks only whether the complete HTTP representation size of the exact commit-pinned desitarget source archive can be established from a valid single-byte Range response without materializing any response-body byte. It is separate from the failed semantic-provenance attempt and from the completed inconclusive HEAD probe. It cannot interpret PHOTSYS, inspect source contents, continue semantic research, or authorize archive acquisition.

## Frozen historical evidence

The completed HEAD stage is `OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-HEAD-PROBE-001`. Its immutable `HEAD_RESPONSE.json` has SHA-256 `5eefee40091b098435701e4abbf271cb888b29a0353df8e5e7da40242449506b`; its immutable `TERMINAL.json` has SHA-256 `d70de460a0628b333d73a5b4a70de6fdab53333a971f9c276beb2255a4b82da8`.

That stage observed HTTP 200, the unchanged literal URL, zero redirects, `Content-Type: application/x-gzip`, identity content encoding, no `Content-Length`, zero application body bytes, one request, and zero scientific-firewall counters. Its terminal is `DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE` with budget decision `NO_ARCHIVE_GET_CANDIDATE`. Its authorization is consumed; it cannot be resumed or rerun.

The historical HEAD response supplied ETag `"a52cc7025bc235d2b8e2a6f7a4d0b494f2146beb5b02a8d6013819b46a4b2ea1"` and no Last-Modified value. A Range response ETag is compared to this value only when the Range response also supplies ETag. Last-Modified is recorded but not required or compared because it was absent from the historical HEAD response.

The failed provenance review is `OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_FAILED_ATTEMPT_REVIEW.md`, SHA-256 `55524fc8d32628a9110b9231372d3589eaac87d4f48e823b268dae6e6b1f61a2`. Its four immutable public-source bodies remain reusable offline only by these exact hashes:

- FITS Standard: `5624dca15659caf54c56127b4df9af05fd930c8f6d997fcb4bea2b1a5c1bc573`
- Legacy Survey DR9: `d0b51d66529cb4c62db7e8ae1df22d6976879f46dcd62b4e6993729b42674c85`
- desitarget tag ref: `9289a01c82464f9ffe901b907e165c2c9bb7de7c3e17e454d112a3eb6ae2476d`
- desitarget annotated tag object: `c8a62b156a83788ae395ad2d866bdc114a958f3af93984326594d0c5dabeaef8`

No historical resource is requested again.

## Exact resource and request

The only resource is:

`https://codeload.github.com/desihub/desitarget/tar.gz/dd30297f9d50fcb7bbba57d79d4b8fc86cb35701`

The bound commit is `dd30297f9d50fcb7bbba57d79d4b8fc86cb35701`. Alternate URLs, tags, mirrors, redirects, HEAD, additional GETs, arbitrary ranges, retries, and fallback requests are prohibited.

The sole future network operation is one HTTP `GET` whose implementation fixes these request headers:

```text
Range: bytes=0-0
Accept-Encoding: identity
Connection: close
```

The caps are one request, zero redirects, zero retries, concurrency one, and zero application body bytes. The dedicated transport exposes only `probe_size()`; it exposes no `get()`, `head()`, `range()`, `read()`, `request()`, URL argument, method argument, or arbitrary header argument.

## No-body and accounting boundary

After obtaining the status line and response headers, the implementation closes the connection without calling `response.read()`. It does not materialize, hash, serialize, or inspect the one-byte range body. Any application body-read attempt is a firewall violation and fails the stage even if only one byte is involved.

`application_body_bytes_read` must remain zero. This is an application-level observation only. The stage makes no claim that wire bytes, TLS bytes, or server bytes sent are zero.

## Accepted response and Content-Range grammar

Successful size evidence requires HTTP `206 Partial Content` and exactly one `Content-Range` field whose value matches the case-sensitive, whitespace-sensitive grammar:

```text
bytes 0-0/TOTAL
```

`TOTAL` follows HTTP complete-length syntax `1*DIGIT`, parses as a base-10 integer, is positive, and is greater than the last position zero. Leading zeroes are syntactically accepted because `1*DIGIT` permits them; the parsed integer is the recorded `complete_length`.

The parser rejects field absence, duplicate or multiple Content-Range semantics, another range unit, unsatisfied-range form, wildcard total, unexpected start or end, embedded or surrounding whitespace outside the exact grammar, signed totals, non-decimal totals, zero total, and malformed syntax. It performs no repair or normalization.

`Content-Length` is never used as the complete representation size. When present on a successful `bytes=0-0` response, exactly one decimal Content-Length field must describe one partial-response body byte. Missing Content-Length is allowed because complete size comes from Content-Range. Duplicate, malformed, or non-one partial Content-Length is a contract failure.

Accepted base Content-Type values are exactly `application/gzip`, `application/x-gzip`, and `application/octet-stream`; parameters are ignored only after extracting the base type. Content encoding must be absent or `identity`.

## Identity comparison

Response ETag and Last-Modified are recorded when present. If the Range response supplies ETag, it must exactly equal the historical HEAD ETag. Absence on the Range response is allowed. A mismatch is `REPRESENTATION_IDENTITY_MISMATCH` and fails closed. Last-Modified is not a gate because the historical HEAD supplied none.

## Closed terminal mapping

Success is `DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_OBSERVED`. It requires HTTP 206, exact valid Content-Range, accepted type and encoding, identity consistency, one request, no body read, and a clean scientific firewall.

HTTP 200 is `DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_INCONCLUSIVE` with reason `RANGE_IGNORED_200`. HTTP 416 is the same terminal class with reason `RANGE_NOT_SATISFIABLE_416`; a 416 Content-Range is not parsed for size. For HTTP 206, absent, wildcard, duplicate, malformed, unexpected-unit, unsatisfied-form, or unexpected-position Content-Range evidence is inconclusive with a distinct recorded reason.

Redirects 301, 302, 303, 307, and 308 fail closed as `DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_FAILED` with reason `RANGE_REDIRECT_FORBIDDEN`. Other unexpected HTTP statuses fail with `RANGE_HTTP_STATUS_UNEXPECTED`. Content-Type mismatch, content-encoding mismatch, partial Content-Length inconsistency, representation-identity mismatch, request-cap violation, and any body-read attempt also fail closed with distinct reasons. No terminal causes another request.

## Conservative budget decision

The parent body maximum is 33554432 bytes. The historical conservative possible maximum is 16009494 bytes. The remaining conservative budget is therefore 17544938 bytes. This Range-size probe authorizes zero application body bytes, so it does not decrement that application-level threshold and does not assert zero physical transfer.

After successful size observation only:

- `complete_length <= 17544938` records `LATER_ARCHIVE_ACQUISITION_MAY_BE_DESIGNED`.
- `complete_length > 17544938` records `STOP_CURRENT_32_MIB_SPEC_CANNOT_ACCOMMODATE`.

Neither result authorizes or automatically prepares archive acquisition.

## Scientific firewall

The terminal requires at most one public-source metadata request and exactly zero for `application_body_bytes_read`, `astronomical_data_GETs`, `real_PHOTSYS_bytes_observed`, `BRICKNAME_values_observed`, `BRICKID_values_observed`, and `ROOT_values_observed`. This Range GET is not an astronomical-data GET.

## Execution governance

Offline modes are `--help`, `--validate-inputs`, and `--dry-run`. The network mode is `--probe-desitarget-archive-range-size` plus an explicit execution flag, the exact sealed candidate, a separate final human authorization, and the exact output directory. Offline dry-run must return `READY_AT_DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_BOUNDARY` with all counters zero.

The real stage has no automatic resume and no overwrite. An interruption or partial tree is preserved and requires review and a new authorization. The human-review candidate is prospective and cannot serve as authorization. Final authorization is absent when the candidate is sealed.
