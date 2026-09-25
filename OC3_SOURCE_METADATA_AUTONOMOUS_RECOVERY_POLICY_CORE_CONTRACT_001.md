# OC3 Autonomous Recovery Policy Core Contract 001

The Policy Core comprises the generic recovery engine, controller, governor, deterministic factory, production Mission Runner, action executors, single-action supervisor/worker, Action Registry, Technical Authorities Registry and this contract. Once standing authorization is active, any byte change requires `STOP_REQUIRES_HUMAN`.

The control plane derives action kind, trigger, generation, authority classes, reservations, paths and argv. Caller injection is forbidden. It permits control-plane resume only after durable action transition. Material and technical network replay after permit or capability consumption is forbidden.

Technical adapter implementations remain outside the Policy Core and inside the Mutable Technical Surface. The autonomous agent may reason about a repair, but continuation depends only on objective Git-diff, immutable-contract and test evidence.

The Technical Authorities Registry freezes adapter identities, allowed implementation paths and eligible official-evidence resource IDs. Any bootstrap implementation SHA is historical provenance only. A repaired implementation is authorized for material use exclusively through an independently computed runtime SHA persisted with its validated patch, transport contract and test receipts. Material execution rechecks those bytes before network access.
