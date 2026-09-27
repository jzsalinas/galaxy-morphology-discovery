# OC3 Run-005 and Manual Acquisition Implementation Report 001

Status: **OFFLINE PREPARATION COMPLETE; NO NETWORK; NO EXECUTION AUTHORITY**.

Run-004 remains closed at `STOP_REQUIRES_HUMAN / CONSUMED_ACTION_WITHOUT_TERMINAL_REPLAY_FORBIDDEN`. The prospective Run-005 streaming boundary now records a request immediately before opener handoff, preserves partial bytes separately, detects declared-length premature EOF, and returns a governed `DATALAB_TRANSPORT_FAILURE` terminal with exact per-query and action accounting. Complete responses are charged even if the frozen parser subsequently rejects them. Single-use permit/capability rules are unchanged.

The separate manual instrument freezes the five existing queries and reuses the exact complete Run-004 schema response under explicit provenance. It uses a 600-second timeout, zero retries, one request at a time, immutable per-attempt intents/terminals, streamed temporary writes, fsync, atomic promotion, sealed manifest, append-only log and hash-validated restart. Every acquired response remains RAW and scientifically unaccepted pending the separate offline audit contract.

Focused validation passed 23 synthetic tests: 17 manual acquisition cases and six Run-005 accounting cases. The complete socket/DNS-firewalled regression passed 1,574 tests with zero failures, zero skips and zero real network requests. The regression replaces seven historical lifecycle assertions with the current closed Run-004 and inactive Run-005 expectations.

Run-005 has no first candidate, standing authorization, permit or capability. Its preparation state is `TRANSPORT_FAILURE_ACCOUNTING_REPAIRED / WAITING_FOR_MANUAL_ACQUISITION_AUDIT`, with execution `NOT_STARTED`. A future zero-network evidence-ingestion candidate is permitted only after a distinct offline audit accepts the manual evidence.
