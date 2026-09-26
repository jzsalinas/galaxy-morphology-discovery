# OC3 Source-Metadata Autonomous Recovery Production Specification 005

Status: **PROSPECTIVE; OFFLINE PACKAGE ONLY; RUN-004 NOT AUTHORIZED**.

Run-004 uses fresh `*_004` candidate, state, authorization, ledger, permit, capability,
output and execution identities. Its first candidate is
`MATERIAL_SOURCE_METADATA_ACQUISITION`, justified by the read-only inherited transport
authority. No Run-003 execution capability is reusable.

The frozen scientific queries, target/holdout guards, projection, row caps, recovery
graph, provider endpoints and material budget remain unchanged. Run-004 begins with
8 technical requests / 2,097,152 technical bytes and 5 material requests / 67,108,864
material bytes. Concurrency remains one and retries remain zero.

Future technical repair handoffs must publish a sealed Git partition. The partition is
recomputed independently by both handoff validation and the offline repair executor.
Its mutable class must equal the patch manifest paths; its authorized runtime class
must contain only an exact validated Run-004 state when changed; and its forbidden
class must be empty. The union must be disjoint and exhaustive.

The inherited transport authority records only that the frozen ADQL is byte-identical,
public anonymous GET is compatible, redirects are forbidden, the body cap is enforced,
and CSV bytes can be accepted while an observed `text/html` header is retained as
provenance. It cannot establish scientific counts or rows.

No network operation, permit, capability, final standing authorization, material
output or scientific result is created by freezing this package.

