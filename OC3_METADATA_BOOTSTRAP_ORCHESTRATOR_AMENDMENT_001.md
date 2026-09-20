# OC3 Metadata Bootstrap Orchestrator Amendment 001

Status: prospective implementation authority; this document does not authorize network execution.

## Observed gap

The first authorized manual invocation completed every local authorization gate and constructed `RealHttpTransport`, but returned the fixed state `AUTHORIZED_TRANSPORT_READY`. It made zero requests, created no attempt directory, observed zero provider bytes and did not start or consume a resumable metadata-bootstrap attempt.

## Frozen correction

After successful first-run authorization and transport construction, the CLI SHALL invoke the existing bounded `METADATA_BOOTSTRAP_ONLY` workflow. The order is: create Attempt 001 and its ledger; issue all four HEAD requests and jointly validate them; acquire, publish, digest and validate ROOT, NORTH, SOUTH and PATCH in that order; validate only the PATCH header; selectively decode ROOT, NORTH and SOUTH after every acquisition and physical gate passes; validate frozen semantics and exact regional joins; write aggregate evidence; then select one terminal.

The correction reuses the frozen resources, caps, transport, ledger, immutable publication, provenance, physical contracts, selective decoder, value semantics, join logic and terminal precedence. It adds no fallback, automatic resume, cap reset or broader retry. It does not decode PATCH rows or perform PATCH membership, uniqueness or joins.

For `MODEL_B_TWO_STAGE`, the only successful Attempt 001 terminal is `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED`, with PATCH ending at `PATCH_ACQUISITION_BOUND_PENDING_HUMAN_REVIEW`. `METADATA_BOOTSTRAP_RESOLVED` remains unreachable.

This amendment invalidates the previous implementation aggregate for future execution binding. Existing Rights Binding 002, candidate and final authorization remain immutable historical evidence and SHALL NOT be reused. A later task must review the new aggregate and create fresh rights/candidate authorization artifacts before any real execution.
