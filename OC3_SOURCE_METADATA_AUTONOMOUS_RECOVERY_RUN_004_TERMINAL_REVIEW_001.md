# OC3 Source-Metadata Autonomous Recovery Run-004 Terminal Review 001

Status: **HISTORICAL TERMINAL — STOP_REQUIRES_HUMAN**.

## Authorization and execution identity

Standing Authorization 004 is
`oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_004.json`,
SHA-256 `d6c9daae4ed052d24f413102e1a14e2428a05992030ba1d3be371a0c2abdc125`.
The execution actor was `AUTHORIZED_AGENT`; the human role was review and
explicit authorization.

The exact executed argv SHA-256 was
`c5812946f6c4d28a6582bec0a333924feec59253deb514b58f9a6e2842a9878a`.
The same runner identity was invoked a second time only to apply its
fail-closed consumed-action rule; that invocation performed no network action.

## Terminal

Run-004 closed at:

- state: `STOP_REQUIRES_HUMAN`;
- reason: `CONSUMED_ACTION_WITHOUT_TERMINAL_REPLAY_FORBIDDEN`;
- final state SHA-256:
  `926c507640e60e4d67e74b130ee3a58b9104ac8a5eaba84dee13a7811abac9b0`;
- mission final report SHA-256:
  `d9ec2e16f594509dbca8c36f4ae4efba258723c4a30829bc9e55149b1916e810`;
- closure SHA-256:
  `43fb06fd192e2ff7b8569ccf162a403964d9d4b74592f071986aa5a18e10357d`.

The first material action consumed its permit and worker capability. The
`schema` request succeeded and preserved 2,124 response bytes. The subsequent
`north_count` request reached a read timeout after 300 seconds. The worker
returned code 2 before publishing `TERMINAL.json`; consequently the runner
could not transition or account the action and forbade replay.

The supervisor retained only the stderr SHA-256. Its exact deterministic
preimage is:

```json
{"error": "The read operation timed out", "network_requests": 0, "state": "RECOVERY_WORKER_BLOCKED"}
```

The preimage hashes to the observed
`044c46a298fe20ed09c5edc4fb4173ca83ccc7045289fa07a16c25fc7545f7c7`.

## Resource accounting

| Class | Requests started | Body bytes observed |
|---|---:|---:|
| Technical | 0 | 0 |
| Material | 2 | 2,124 |

The material figures are evidence-derived transport observations: one
successful schema response and one timed-out `north_count` request. The state
counters remain unchanged because no authoritative action terminal existed.
They must not be interpreted as zero physical use. No retry occurred.

## Scientific evidence boundary

Established:

- the exact schema response is parser-compatible with the frozen 18-row,
  nine-columns-per-table schema gate;
- no source row or source value was accepted;
- no north or south count was established;
- no north or south row acquisition completed;
- no morphological fact was established.

The offline schema check is technical evidence. It is not an authoritative
completed material-action terminal and does not establish source population
counts.

## Self-repair and Git partition

No self-repair episode was consumed and no defect class was accepted. No Git
partition artifact was produced because the action failed before a governed
repair handoff. There are no mutable technical patch changes to classify. The
only tracked runtime mutation is the exact Run-004 state lifecycle; compact
ledger, permit and capability evidence is preserved separately.

The discovered exception-handling gap is deterministic, but recovering this
already-consumed action would require changes outside the frozen mutable
technical surface and a new rule for exact partial-request accounting. An
adapter-only workaround could misclassify a transport timeout as scientific
CSV evidence and is therefore forbidden.

## Open explanations

The evidence does not distinguish among transient provider load, query
execution cost, proxy/service latency or a persistent `north_count` service
behavior. It establishes only the read timeout observed in this attempt.

## Next scientifically permitted step

Prepare a prospective successor-run amendment that catches material transport
exceptions before worker escape, records every started request and preserved
body byte, emits a governed `DATALAB_TRANSPORT_FAILURE` terminal, and routes it
through the existing recovery graph without replaying Run-004. The amendment
must decide explicitly whether this requires expanding the mutable technical
surface. A fresh run, state, authorization, permit and capability are required;
Run-004 must remain immutable terminal evidence. No timeout increase, retry,
provider substitution or query change is implied.
