# OC3 Source-Metadata Autonomous Recovery Bootstrap Report 004

Status: **READY FOR FINAL AUTONOMOUS RECOVERY HUMAN REVIEW; INACTIVE**.

## Closed finding

`MUTABLE_ADAPTER_STATIC_SHA_CONTRADICTION` was confirmed at reviewed base commit `c92270ecb0746da6ee1a3711e7bc36f7184566d2`. Registry V1 bound the mutable Query Manager implementation by its current SHA and static validation required those bytes forever. A legitimate agentic repair would therefore have failed before its patch could be evaluated.

Technical Authorities Registry V2 separates prospective authority from runtime evidence. It freezes adapter ID, allowed mutable implementation path and allowed official-evidence resource IDs. Query Manager's bootstrap SHA is verified against its historical blob at `c92270e` and is provenance only. TAP has a prospectively allowed absent path and no bootstrap SHA, implementation, contract or validated state.

## Adapter implementation binding model

Successful offline repair independently hashes the implementation at the V2-registered path and verifies any changed implementation against the Git-derived patch manifest. The governor independently rehashes that path during transition and persists:

`active_adapter_binding = {adapter_id, implementation_path, implementation_sha256, technical_patch_manifest, technical_transport_contract, test_receipts}`.

The material candidate derives this object from durable state. The material executor rehashes the registered implementation before creating a request intent or invoking transport. A mismatch produces `ADAPTER_IMPLEMENTATION_DRIFT` and `STOP_REQUIRES_HUMAN` with zero material network requests.

Prospectively allowed adapter IDs are:

- `query_manager_public_anonymous_v1` — `AVAILABLE_UNVALIDATED`; bootstrap provenance exists.
- `official_noirlab_tap_public_v1` — `AVAILABLE_UNVALIDATED`; implementation absent and no validity implied.

## Frozen identities

- Technical Authorities Registry V2: `187ba6da5a85caf38a72988e1b95f2184903913ff923ba6611dacf60ebbcda36`
- Production Mission Runner: `4c476aef0c57f12e08dd57de5ec2b9837b4bdfdf545c8a402f5889f29baeb8be`
- Governor: `5316361cbdf423910f767d4e96a835dd28ff5d6e0b04ff0dbc2d846ea4729f0d`
- Deterministic Candidate Factory: `bef93745baa51dd4cfc1871830b7682b85a189e3df843f775312c9536ad87547`
- Policy Core manifest: `964c6b799c57d2251d88beec12626f98336aec34d08e5a26f6184667cd439c52`
- Pending mandate: `080771efabd6e2856bd9066195f7da1a62a11aec66f9b2a1410d9c615e21087d`
- Waiting state: `3dc1055da46efab368239b22229605ad3aab9d749fa2d72a12294ff373feddd7`
- Resealed first candidate: `85768ae364773c67ae1ff458ead767db5f6ff4b789afcc28a61a185ef348dfd7`
- Control-plane implementation aggregate: `b016cb1da3600444999682e6bfca50224e0563e10c163dd00d434ac5807f6898`
- Scientific Invariants Manifest: `0d2b304e815a949cf7f69d44cd43148eb663fadb68afb47a7e9f767635a329f3` (byte-identical)
- Recovery Graph: `19e7d6226d6550efbd32c62a4268d682e448f15fb3c490550471286943587fb7` (byte-identical)

All five scientific query semantic hashes remain byte-identical.

## Regression evidence

The real-adapter regression entered the durable agentic handoff, modified the actual registered Query Manager implementation bytes under a controlled fixture, created the exact patch/contract/test artifacts, resumed under the same authorization, validated the repair, activated the newly computed SHA and generated a material candidate containing that runtime binding. Static authority validation continued to verify the bootstrap SHA historically and did not reject the repaired bytes.

The drift regression changed the implementation again after activation. Material execution returned `ADAPTER_IMPLEMENTATION_DRIFT`, created no material request intent or raw directory, initiated zero network requests and stopped the mission. An isolated temporary Git repository separately proved exact Git-derived adapter path and pre-repair blob hashing.

- Focused runner, recovery and acquisition tests: 71 passed.
- Full socket-firewalled regression: 1,487 passed, 0 failed, 0 skipped.
- Full regression log SHA-256: `9617a3d81861feb9f6fedd59766503ea890345cdf21c2f659600d26352b6d959`.
- Real network requests: 0.
- Source counts observed: 0.
- Source rows observed: 0.
- Standing authorization: absent.
- Real permits and worker capabilities: absent.
- Real recovery mission execution: absent.

The mission remains inactive pending later human standing authorization of the revised Registry V2 and resealed control-plane identities.
