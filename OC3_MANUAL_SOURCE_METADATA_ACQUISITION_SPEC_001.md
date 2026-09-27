# OC3 Manual Source-Metadata Acquisition Specification 001

Status: **PROSPECTIVE HUMAN-INVOKED ACQUISITION INSTRUMENT**.

## Frozen acquisition

The instrument requests exactly `schema`, `north_count`, `south_count`, `north_rows`, `south_rows` using the existing literal ADQL, provider endpoint, projections, brick guards, predicates, row caps and ordering. Access is public-anonymous, redirects are forbidden, concurrency is one, automatic retries are zero, and the human-approved timeout is 600 seconds. No credentials, asynchronous jobs, mirrors, query decomposition or alternate provider are permitted.

The complete Run-004 `schema.csv` is reusable because its exact 2,124 bytes and SHA-256 are preserved, its query/provider identity is bound by the Run-004 closure, and it passed the frozen schema parser offline. Reuse copies it into the fresh manual RAW namespace with `requests_started=0`, provenance `REUSED_RUN_004_COMPLETE_SCHEMA_RESPONSE`, and `scientific_acceptance=false`. This does not convert the historical material action into a completed action. The first future request is `north_count`.

## Durability and restart

Before each request the runner writes and fsyncs an immutable intent. It streams to `STAGING`, enforces the existing per-response byte cap, fsyncs, and atomically promotes to `RAW_ACQUIRED` only after successful EOF and detectable completeness checks. Failures preserve any bytes under `PARTIAL` with a hash and immutable terminal. Completed earlier queries remain untouched.

On restart the runner recomputes every completed RAW hash and byte count from the sealed manifest. Exact completions are skipped; mismatch, unmanifested output, unknown top-level artifacts, binding drift or provider/query drift stops before network. One invocation stops at the first failed query and never retries automatically. A later human invocation may start the next attempt.

The acquisition manifest and log distinguish RAW acquisition from scientific acceptance. The instrument never validates or accepts source counts/rows and always records `scientific_acceptance=false`. Content-Type is provenance, not a scientific acceptance decision.

Local elapsed-time messages identify the active query and completed predecessors without provider polling. The process stays in the foreground and is suitable for `tmux`.

Exit codes: `0` means all five RAW responses are complete but unaudited; `20` means transport timeout; `21` means another transport failure; `22` means local binding/integrity failure. None means scientific acceptance.

