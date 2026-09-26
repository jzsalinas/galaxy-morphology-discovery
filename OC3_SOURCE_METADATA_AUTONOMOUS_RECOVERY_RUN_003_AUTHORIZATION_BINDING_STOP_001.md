# OC3 Source-Metadata Autonomous Recovery Run-003 Authorization-Binding STOP 001

Status: **STOP_REQUIRES_HUMAN; PRE-EXECUTION GOVERNANCE STOP**.

Recorded at UTC: `2026-09-26T12:17:06Z`.

## Exact classification

`AGENTIC_EXECUTION_ALIGNMENT_NOT_BINDABLE_TO_FINAL_AUTHORIZATION`

Run-003 was not authorized, activated or executed. The final standing
authorization was not created.

## Human decision received

The human owner explicitly approved Run-003 subject to a mandatory prior
condition: the distinct final standing authorization must bind or otherwise
cryptographically include
`OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_003_AGENTIC_EXECUTION_ALIGNMENT_001.md`
at SHA-256
`28abdc2741853fc7e415cba078b58c4b991717e88990bbab89cd23a86aa61736`.

The reviewed human instruction has SHA-256
`4d538cd22d5bb2ac68b693342757444b3f6b5a55ef0be926382568d3a8edffe8`.
It explicitly requires this STOP if the existing final-authorization schema
cannot represent that binding without changing Candidate 003, Policy Core 003,
implementation semantics or another frozen technical authority.

## Closed-schema finding

The production function `validate_standing_authorization` in
`oc3/oc3lib/source_metadata_recovery_governor_run003.py`, SHA-256
`dd7ac8a2b3a8efee2bc0fc02ab9f132fbdfe29b55c1f6f4f0b66d5a058834c5f`,
requires exact set equality for the authorization object. Its closed field set
is:

```text
action_registry
authorized
candidate_factory_sha256
control_plane_aggregate
first_candidate
implementation_aggregate
initial_state_sha256
mandate
mission_id
mission_runner_sha256
mutable_technical_surface
policy_core_manifest
predecessor_run
recovery_budget
recovery_graph
run_id
schema_version
scientific_invariants
sealed
self_repair_authority
technical_authorities
```

There is no field for an agentic-execution alignment, reviewed execution-actor
authority or additional documentary authority. An added field is rejected by
`set(value) != required`. Every existing binding field is also compared with a
specific frozen artifact or identity; none can be repurposed to carry the
alignment without failing validation.

The alignment is not a member of Policy Core Manifest 003 and is not referenced
by Candidate 003 or Waiting State 003. Therefore the existing authorization's
`sealed` value cannot cryptographically include the alignment: the sealed hash
covers only the authorization fields, and none of those fields transitively
binds the alignment.

## Prohibited resolution paths

The binding could be added only by at least one change that this human decision
does not authorize:

1. extend the closed authorization schema and validator, changing the frozen
   Run-003 governor and the control-plane aggregate; or
2. add the alignment to Policy Core Manifest 003 or another currently bound
   authority, changing that authority's bytes and its downstream bindings; or
3. reinterpret an existing closed-schema field, which would fail the current
   validator and would not constitute an honest cryptographic binding.

No such change was made. No implicit binding from the human message, Git commit
or filesystem adjacency was invented.

## Frozen identities preserved

- Policy Core 003:
  `6d19ae1732b12863cb8e9d83b174d90ae114e72f0e10133568e48f28161cbfdd`
- Policy Core Manifest 003:
  `c9a10c82ac019bd14c9a0f925c28411ede638b0f1eca686e5dd55b98af9839cb`
- Inactive Mandate 003:
  `6fdf0088326a5b8cd66672f51f0daceabaa6b752b8e14223a3382ca96aba402d`
- Candidate 003:
  `b1c270b5a490400e35f509563b214cb56ee9780ed4cbcdeb058c6f1c4aff8eb3`
- Waiting State 003:
  `60e5c95601e2968e1024a0fda896a7918be528f02b90eae61b6b9c408a9a5a5e`
- implementation aggregate:
  `d6c4680b7e861baffce27dee14a4270c1304b1e3c841eb6c9977502b2f7d0348`
- control-plane aggregate:
  `8fc7628e4aaf07c0cf3c9ccb420abd3ffd672243f2eb20aac0b61ef8d329ccf3`
- mission argv SHA-256:
  `8a9e1fdc617cce8f6c5a3544279425335e67371c9f15f4c312b164cc7eb7f2b8`

Waiting State 003 remains `WAITING_FOR_STANDING_HUMAN_AUTHORIZATION`, inactive,
with `execution_status = NOT_STARTED`. It was not mutated into a runtime STOP
because Run-003 never obtained a valid standing authorization and never began.

## Resource and execution accounting

- final standing authorization created: `NO`
- mission command invoked: `NO`
- Run-003 network requests: `0`
- Run-003 response-body bytes: `0`
- Run-003 material requests: `0`
- Run-003 material bytes: `0`
- permits issued: `0`
- self-repair episodes: `0`
- scientific rows or values observed: `0`
- historical Run-001/Run-002 evidence modified: `NO`

## Minimum prospective resolution

A new human decision is required to authorize a narrow, prospective
pre-execution governance revision that adds an exact path-and-SHA binding for
the agentic-execution alignment to the final standing-authorization contract,
updates only the authority and downstream artifacts whose hashes necessarily
change, and preserves the exact command argv, mission scope, scientific
semantics, resources, rights, budgets, self-repair limits and terminal
semantics.

Until such a revision is prepared, reviewed and separately authorized, the
governed result is:

`STOP_REQUIRES_HUMAN`

`AGENTIC_EXECUTION_ALIGNMENT_NOT_BINDABLE_TO_FINAL_AUTHORIZATION`
