# OC3 desitarget archive Range-size probe implementation report

## Frozen HEAD result

The completed stage `OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-HEAD-PROBE-001` remains immutable and consumed. Its sealed response and terminal hashes are `5eefee40091b098435701e4abbf271cb888b29a0353df8e5e7da40242449506b` and `d70de460a0628b333d73a5b4a70de6fdab53333a971f9c276beb2255a4b82da8`. It observed HTTP 200, the exact URL, `application/x-gzip`, identity encoding, no Content-Length, zero application body bytes, and all scientific-firewall counters zero. Its terminal remains `DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE` with `NO_ARCHIVE_GET_CANDIDATE`.

## Range-size contract

The new independent stage is `OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-ARCHIVE-RANGE-SIZE-PROBE-001`, scoped to `DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_ONLY`. Its dedicated transport internally fixes one `GET` to the exact commit archive with `Range: bytes=0-0`, `Accept-Encoding: identity`, and `Connection: close`. It exposes only `probe_size()` and has no generic GET, HEAD, Range, request, read, URL, method, or header interface.

The transport captures the response status and headers and closes the connection without calling `response.read()`. It neither materializes nor interprets a response-body byte. `application_body_bytes_read` must remain zero; no assertion is made about physical wire, TLS, or server bytes.

## Content-Range and identity rules

Successful evidence requires HTTP 206 and exactly one field matching `bytes 0-0/TOTAL`. The parser follows the HTTP `1*DIGIT` complete-length syntax, requires a positive parsed total greater than position zero, and rejects wildcard totals, unsatisfied form, other units, unexpected positions, duplicate or comma-combined semantics, malformed totals, and nonexact whitespace. `Content-Length` is never treated as complete size; when present it must consistently describe the one-byte partial response.

The historical HEAD ETag is compared only when the Range response also supplies ETag. A mismatch fails closed. Last-Modified is recorded but is not a gate because the HEAD response did not supply it. HTTP 200 and 416 are distinct inconclusive outcomes; redirects and unexpected statuses fail closed. No response path issues a fallback request.

## Budget rule

The parent maximum remains 33554432 bytes, the historical conservative maximum remains 16009494 bytes, and the remaining application-level threshold remains 17544938 bytes. The Range probe authorizes zero application body bytes and does not decrement that threshold based on assumed physical transfer. A valid total at or below the threshold records `LATER_ARCHIVE_ACQUISITION_MAY_BE_DESIGNED`; a larger total records `STOP_CURRENT_32_MIB_SPEC_CANNOT_ACCOMMODATE`. Neither result creates an acquisition candidate.

## Offline validation

- Focused Range-size suite: 30 passed, 0 failed.
- Affected regression: 265 passed, 0 failed.
- Complete offline regression: 1193 passed, 0 failed, 0 skipped; `real_network_requests=0`.
- `--validate-inputs`: `DESITARGET_ARCHIVE_RANGE_SIZE_INPUTS_VALIDATED`, zero network and zero body bytes.
- `--dry-run`: `READY_AT_DESITARGET_COMMIT_ARCHIVE_RANGE_SIZE_BOUNDARY`, zero network, zero body bytes, and zero scientific-firewall counters.

The frozen specification SHA-256 is `f4751e6d5aab144b637c313fb6f100df234f8ab78ad2a4186a2036b4e44f5604`. The implementation aggregate is `e09738b32502b7a234a872b26c3c6e6d1be3a114357de34e2869e2e734a0a36e`.

The sealed human-review candidate is `oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_001.json`, SHA-256 `a277a5e5b4d710650df5e89713dfd23a97c0f79ff273076273eb84835f55fc19`. Its command argv SHA-256 is `6338865c67aa47a72e55e3f7859cc3654eb92c233fb44993a5e6ec7e2b3efa2c`. Final authorization is absent. No network request or real Range probe was executed.
