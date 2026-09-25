# OC3 Source-Metadata Acquisition Pilot Bootstrap Report 002

Status: **READY FOR FIRST REAL SOURCE-METADATA ACQUISITION HUMAN REVIEW; INACTIVE**

This report prospectively supersedes bootstrap report 001 for authorization review. Report 001 remains historical evidence of the earlier bootstrap. Before standing authorization, review found `DIRECT_NETWORK_WORKER_GOVERNANCE_BYPASS`: the standalone worker could reach its network-capable execution path without proving supervisor consumption of a governor permit. No unauthorized execution or material access is known to have occurred. The finding was an implementation and governance defect, not a scientific-design defect.

## Closed execution path

The required causal path is now:

`HUMAN STANDING AUTHORIZATION` → `GOVERNOR ACTIVATION` → `ACTION REGISTRATION` → `SINGLE-USE GOVERNOR PERMIT` → `SUPERVISOR CONSUMES PERMIT` → `START_INTENT` → `SUPERVISOR CREATES SINGLE-USE WORKER EXECUTION CAPABILITY` → `WORKER CONSUMES CAPABILITY` → `REQUEST_INTENT` → network transport.

The worker requires `--execution-capability` at the exact path frozen in the candidate. The supervisor creates the immutable capability only after the policy-defined permit-consumption marker exists and validates. The capability binds the mission, stage, candidate path/SHA, permit path/SHA, standing-authorization path/SHA, autonomy-state path, worker argv SHA, query-manifest path/SHA, output path, five-request reservation, 67,108,864-byte reservation, UTC issuance time, deterministic capability ID, `single_use=true`, and a canonical seal. It contains no credentials.

The worker validates the complete binding before entering `execute()`. It atomically records consumption at `oc3/SOURCE_METADATA_ACQUISITION_PILOT_AUTONOMY_LEDGER/WORKER_CAPABILITY_CONSUMPTION/<capability-sha256>.json` before any request-intent or transport call. A crash does not restore the capability. Missing, invalid, mismatched, or previously consumed capabilities stop with zero network.

## Unchanged scientific and data contract

- Pilot frame SHA-256: `661f4d429f8fe0b6aa0104e093d79568d6f274935a7d9b0e78fb3dd45ae40292`
- Targets: `2255p305/498957`, `1901p342/517112`
- Reserved holdouts: `1075p337/514444`, `0381m012/323320`
- Target guard support: 14 bricks
- Forbidden holdout support: 16 bricks
- Service endpoint: `https://datalab.noirlab.edu/query/query`
- Access contract: `PUBLIC_ANONYMOUS_ONLY`, token identity `anonymous.0.0.anon_access`
- Tables: `ls_dr9.tractor_n`, `ls_dr9.tractor_s`
- Projection: `release,brickid,objid,brickname,brick_primary,ra,dec,ra_ivar,dec_ivar`
- Per-domain source cap: 150,000; transport sentinel: `TOP 150001`
- Parent caps: 5 requests and 67,108,864 application-body bytes
- Concurrency: 1; retries: 0; redirects: 0; resume: false
- Query-manifest SHA-256: `d25c12b9b9a8715aa8e2ae5a9d885ef88b3ece1dc62d327072c3cc305e15abf8`

The five query hashes remain exactly:

- schema: `d5be2b494f737e047fea77f4002d387fed15c5dbe3ad019f4a0cafe83faf4a0b`
- north count: `971078fbd961f2c9ae2f94f13a9ec9d4bb49e7421096cd90fb29c307e597c8f8`
- south count: `7080fb7977071438871c5371255672e5da59e0d2ae0196adbb9c23f4c6c1f685`
- north rows: `ee4b97daf1f7b3d23ccb5b9227200b40c9adb4cc40c6a6c33cff98fe6db0449a`
- south rows: `30f5d1fdc0239c4302a6d6388e0bc25a0cb98b5bff2a8d851c97a9e1b89e7918`

## Corrected documentary provenance

The current official client-source reference is `astro-datalab/datalab`, file `dl/queryClient.py`, recorded in `OC3_SOURCE_METADATA_ACQUISITION_DOCUMENTARY_PROVENANCE_002.json` with SHA-256 `0d238c47e0aa6ac47641deb6054ef332839d6fc4d3af1fd2ed0f1cc908814725`. The exact reviewed commit was not available in local review evidence, so it is explicitly unresolved rather than inferred. This correction came from human-reviewed external evidence and was recorded without network replay. Provenance 001 remains historical.

## Resealed bootstrap identities

- Scientific specification SHA-256: `6388bdb5d6fa3f4451d0e4317ccc5ec902a4214360c818edeeeab993e20865aa`
- First-action specification SHA-256: `b0424038c9f7489d3b33eb36688517fe49eac7c64223ef73e2a1aa8070363299`
- Governance-bypass review SHA-256: `36400e1765627a4f5053e95af4dad5d404c6d351c4b3e1b783e1359c66e86a50`
- Policy Core contract SHA-256: `6ffe84394e8adf3897c3a8d27d9a39cce0cd6b995155409f2641c4b632ab167c`
- Policy Core manifest SHA-256: `332c9be0c1e942d40153f9be00474cf28d0991126295004a45120ba077c3635e`
- Mandate document SHA-256: `2da163fc4817fdf9420d7e63430171a2d463ede63c5effa07a975ca9f775e9c5`
- Machine mandate SHA-256: `016f60625c5f7e0dce30ad3a033515c0b9e148d1605687119918a0f736a6794d`
- Candidate-validation receipt SHA-256: `c1ecfc4b909e6a0ee19dc8d00905cc18dc826eaef3ea9e11f71de0d5a053bfdd`
- Candidate SHA-256: `da653cf2086621e2b6f45737eabc89a5ebc3744cd680159d872420fd6966dc36`
- Waiting-state SHA-256: `bcd664435297803cbaa0f1e78a86cb0116f711d332115f7175e3f775abaf374d`
- Implementation aggregate: `4584c973a471fc4e73eac253cabdb227369cea513281fe4648477dfb5cd7e3fc`
- Supervisor argv SHA-256: `0acb5cd5fa480e3e323cf7ce2792cbfb6272c1a66cf28e9a724612fcd62f05bd`
- Worker argv SHA-256: `9f56a00f0d470d500829d206c6ea06dce6d3c5663834ab60e92acc2a90ebea90`

## Offline verification

- Focused acquisition and governance tests: 34 passed
- Mandatory direct-worker test: missing capability returns `WORKER_EXECUTION_CAPABILITY_REQUIRED`, nonzero, with `network_requests=0`
- Invalid-capability matrix: bad seal; wrong candidate, permit, authorization, query-manifest, worker-command, output, and stage bindings; already-consumed capability; all fail before any mock opener call
- Synthetic governed lifecycle: activation, action registration, permit issuance, permit consumption, supervisor capability creation, worker capability consumption, then simulated request intent
- Structural ordering checks: permit validation precedes permit consumption; permit consumption precedes supervisor launch; `START_INTENT` precedes capability creation; capability creation precedes child launch; capability validation and consumption precede worker `execute()`
- Official socket-firewalled full regression: 1,450 passed, 0 failed, 0 skipped
- Real network requests during bootstrap and tests: 0
- Governor state: `WAITING_FOR_STANDING_HUMAN_AUTHORIZATION`
- Policy evaluation: `MANDATE_NOT_ACTIVE`; `NO_PERMIT_ISSUED`

## Observation firewall

- Schema response rows observed: 0
- Source counts observed: 0
- Source rows observed: 0
- Holdout source access: 0
- Combined Tractor access: 0
- Crossmatch, q3c, cone search, matching, angular separation, radius, and scientific-threshold operations: 0
- `OBJECT_GROUP_ID` and `SPLIT_GROUP_ID` creation: 0
- PHOTSYS, TYPE, DCHISQ, Sersic/shape, photometry, photo-z, and pixel access: 0
- Morphology, model, training, embedding, clustering, Panel V3, and P1 operations: 0
- Standing authorization: absent
- Governor permit: absent
- Bootstrap-generated worker capability: absent

The mission remains inactive. Human review must bind this resealed waiting state and candidate before activation or any material access.
