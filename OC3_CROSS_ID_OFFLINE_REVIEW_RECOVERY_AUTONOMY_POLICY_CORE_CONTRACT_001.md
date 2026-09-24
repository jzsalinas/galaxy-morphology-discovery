# OC3 Cross-ID Offline Review Recovery Policy Core Contract 001

This generic Policy Core governs the inactive mission
`OC3-CROSS-ID-OFFLINE-REVIEW-RECOVERY-AUTONOMY-001`. Its sealed members are this
contract and the two governor modules listed by its manifest. It validates mission
identity, standing authorization, immutable state, registered candidate identity,
zero network/body reservations, authority classes, firewalls, single-use permits,
ledger continuity, Git branch, terminal vocabulary and stop transitions.

The Policy Core contains no evidence markers, resource-specific filenames,
candidate identity, first-action stage identity, or preferred scientific outcome.
Action-specific code owns those facts. Before activation it may be reviewed;
after activation any mutation is `STOP_REQUIRES_HUMAN`. Permits are deterministic,
single-use and cannot be replayed. The governor never performs network I/O.
