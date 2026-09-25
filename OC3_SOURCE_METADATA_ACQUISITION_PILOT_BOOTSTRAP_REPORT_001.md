# OC3 Source-Metadata Acquisition Pilot Bootstrap Report 001

Status: **READY FOR FIRST REAL SOURCE-METADATA ACQUISITION HUMAN REVIEW; INACTIVE**

## Frozen basis

- Base terminal commit: `cf34a0efae274a198ac924f99da6135597a7d451`
- Closed predecessor outcome: `SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERED`
- Predecessor final report SHA-256: `6002a9f901d39dabbd1c5a77255df1286ddb177981db627f4c0093cc9c698764`
- Predecessor final claim matrix SHA-256: `8b4fe975730f24174436cc21cf27c8c1ea280b0f14b6452714a9ce35a0cff65d`
- `PILOT_FRAME.json` SHA-256: `661f4d429f8fe0b6aa0104e093d79568d6f274935a7d9b0e78fb3dd45ae40292`
- Frozen targets: `2255p305/498957`, `1901p342/517112`
- Reserved holdouts: `1075p337/514444`, `0381m012/323320`
- Allowed target-query support: 14 lexicographically ordered bricks
- Forbidden holdout support: 16 lexicographically ordered bricks
- Target/holdout intersection: empty

The predecessor frame is used as immutable identity/geometry evidence. No frame selection was repeated or reinterpreted.

## Frozen Data Lab action

- Service endpoint: `https://datalab.noirlab.edu/query/query`
- Transport: synchronous HTTPS GET, ADQL, CSV, public anonymous token identity `anonymous.0.0.anon_access`
- Credentials read: 0
- Source tables: exactly `ls_dr9.tractor_n` and `ls_dr9.tractor_s`
- Projection: `release,brickid,objid,brickname,brick_primary,ra,dec,ra_ivar,dec_ivar`
- Per-domain count cap: 150,000
- Row transport hard cap: `TOP 150001`
- Request cap: 5
- Parent application-body cap: 67,108,864 bytes
- Per-response caps: schema 524,288; each count 65,536; each rows response 32,505,856 bytes
- Concurrency: 1
- Retries: 0
- Redirects: 0
- Resume: false

The exact query hashes under `ADQL_WHITESPACE_CANONICAL_SHA256_V1` are:

- schema: `d5be2b494f737e047fea77f4002d387fed15c5dbe3ad019f4a0cafe83faf4a0b`
- north count: `971078fbd961f2c9ae2f94f13a9ec9d4bb49e7421096cd90fb29c307e597c8f8`
- south count: `7080fb7977071438871c5371255672e5da59e0d2ae0196adbb9c23f4c6c1f685`
- north rows: `ee4b97daf1f7b3d23ccb5b9227200b40c9adb4cc40c6a6c33cff98fe6db0449a`
- south rows: `30f5d1fdc0239c4302a6d6388e0bc25a0cb98b5bff2a8d851c97a9e1b89e7918`

The documentary provenance record identifies six current official references. Bootstrap did not retrieve them: it records the frozen pre-bootstrap review basis honestly, and therefore supplies transport/schema expectations rather than source-row evidence.

## Immutable bootstrap identities

- Scientific specification SHA-256: `8b34d426c1cfbd671c9fe1d13a874c2c2dd2233c0164ea12bb1708a9445886c4`
- Policy Core contract SHA-256: `f689f0b6a05ab026042a5b4fe78b1fe412334262ff5f3c0befada06cb0ef5585`
- Policy Core manifest SHA-256: `2db82a9e229343607f51c04949b7843d5765c2d5e5a9b5e574e4e785be8c90a1`
- Mandate SHA-256: `224801cc4cea1ecc744808b8daaefbe372db22aeb319c58f3a4a385f21963d97`
- Waiting-state SHA-256: `28b93c0dd7807313f258cb3382e8d4623e823eec8f1db262b815b741d2843c0e`
- First candidate SHA-256: `17e696eda7323558c4e2fa56336522f581afd0d526bda8d7fb47c21b2ddf0198`
- Implementation aggregate: `003b2a867f6d05d65c9bdaba86e56a9050cab647a38971647fb7fd64d416ca65`
- Command argv SHA-256: `0acb5cd5fa480e3e323cf7ce2792cbfb6272c1a66cf28e9a724612fcd62f05bd`

## Offline validation

- New acquisition tests: 28 passed
- Affected predecessor/inventory tests: 153 passed
- Official socket-firewalled full regression: 1,444 passed, 0 failed, 0 skipped
- Candidate preflight: `READY_AT_PUBLIC_ANONYMOUS_DATALAB_ACQUISITION_BOUNDARY`
- Governor validation: `AUTONOMY_HARDENING_VALIDATED`
- Governor state: `WAITING_FOR_STANDING_HUMAN_AUTHORIZATION`
- Policy evaluation: `MANDATE_NOT_ACTIVE`; `NO_PERMIT_ISSUED`

## Bootstrap observation counters

- Real network requests: 0
- Schema response rows observed: 0
- Source counts observed: 0
- Source rows observed: 0
- Holdout count requests: 0
- Holdout row requests: 0
- Holdout source-derived cells observed: 0
- Matching, angular-separation, radius and threshold operations: 0
- Object/split group IDs created: 0
- Morphology, Panel V3 and P1 operations: 0
- Standing authorization: absent
- Execution permit: absent

The five exact Data Lab requests are frozen but unexecuted. The mission cannot activate or issue a permit until a later human authorization binds this exact waiting state and first candidate.
