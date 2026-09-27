# OC3 Source-Metadata Transport Exception Accounting Amendment 001

Status: **PROSPECTIVE; OFFLINE; NO RUN-005 EXECUTION AUTHORITY**.

## Historical boundary

Run-004 remains immutable at `STOP_REQUIRES_HUMAN / CONSUMED_ACTION_WITHOUT_TERMINAL_REPLAY_FORBIDDEN`.
Its authorization, permit, capability, state, 2,124-byte schema response, timeout evidence and closure are historical evidence. This amendment does not resume, replay or reinterpret that action.

## Corrected boundary

For a future Run-005 action, control passes to transport accounting immediately before the request is handed to the HTTP opener. From that point every outcome produces an observation containing the query ID, request class, request-start count, bytes actually preserved, status and Content-Type when known, timeout, completion state, partial-state flag, normalized exception class/message and artifact hash when bytes exist.

Timeout, connection failure/reset, HTTP failure, detectable premature EOF and supported local transport exceptions terminate as `DATALAB_TRANSPORT_FAILURE`. A request handed to the opener counts even when no response headers or bytes arrive. A failure before that handoff consumes zero requests. A partial body remains under `PARTIAL`, is never promoted to `RAW_IMMUTABLE`, and is never parsed. A complete response may still fail the frozen parser; its request and bytes remain charged while accepted source values remain zero.

The worker must publish `TRANSPORT_EVIDENCE.json` and a governed action terminal for these outcomes. The terminal is sufficient for the existing controller to reconcile the reserved action against actual requests and bytes. Permit and worker capability consumption remain single-use and unchanged.

## Scope and drift

This changes control-plane failure accounting only. Frozen ADQL, projections, bricks, predicates, ordering, row caps, provider, public-anonymous rights, redirects, budgets, scientific acceptance rules, recovery limits and historical evidence have drift zero. It grants no network authority and creates no Run-005 authorization.

