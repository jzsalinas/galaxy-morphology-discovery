# OC-3 coadd-PSF contract probe implementation report

## Result

`OC3-COADD-PSF-CONTRACT-PROBE-001` is implemented and ready for a separate
human execution. No real probe request was issued during implementation,
testing or review.

The offline evidence closes the expected source model but not the deployed
transport contract. A two-response probe remains scientifically necessary to
observe the public south and north schemas, returned bands, headers, units and
failure behavior without extrapolating source code into deployment evidence.

## Frozen products

- `oc3/TECHNICAL_INDEX/OC3_PSF_IDENTITIES.json`: 54 observational identities,
  18 immutable spatial points; file SHA-256
  `8c8ec5a14169154fce82f6b7a6de147d08e749ba5b410974fd920411b8fe9036`.
- `oc3/INPUTS/OC3_COADD_PSF_CONTRACT_PROBE_BINDING_001.json`: two literal
  representative requests; file SHA-256
  `cb85f224cd0e378e3d4d2d648841d3922162c500236f4b0e3cc818c4ae65407c`;
  internal seal
  `2f0d66258846780ab8c755dc8ada8266e88bb45c3c89680bd9eb6644e79f5195`.
- Entry point SHA-256:
  `dfe07211ba5673e1861e560286cdb9c41e9fe78f3f40b0909e4fc9c216d7fbc7`.
- Implementation module SHA-256:
  `b7f3a9ca27bababed74ae27e736715aead8170a8c290346927abb51f697d5e61`.
- Implementation aggregate:
  `ea17bdcd84b14ea669969d56de1beede0ea01ec9b13ef246e58d3ea13d889974`.

## Network and safety envelope

The binding permits exactly two GET requests in fixed order: S1/P0 south and
N1/P0 north. Each response is capped at 1,048,576 bytes; the stage is capped
at 2,097,152 bytes. Concurrency is one and retries are zero. Counters start at
278 requests and 93,870,926 body bytes. A one-byte read sentinel detects and
fails a streamed response that exceeds its cap; every observed byte is charged.

The transport accepts only the two literal HTTPS URLs in the binding, rejects
redirects and content encoding changes, and never constructs a band query.
Request metadata is persisted before response-format validation. Each completed
regional FITS structure is then sealed independently, so a north failure cannot
erase a successful south result.

FITS inspection reads headers and advances over array byte ranges by offsets.
It records HDUs, shapes, dtypes, explicit bands, units and normalization-related
header fields without converting any array bytes to numerical values. The code
has no image/invvar resource URL or morphology-selection path and does not retain
raw PSF science products.

## Verification

- Focused synthetic tests: 19/19 passed; zero skips; log SHA-256
  `b6e4d86c7e9ac57c0f547508440f3b3b95e14e043101c5abb6b5135a73ebcde1`.
- Full offline regression: 808/808 passed; zero failures; zero skips;
  `real_network_requests=0`; log SHA-256
  `9caf360938e5b5b7cb6d1a8b309aa0dfe5b5e8603bab8f801e0aff7c51c413fa`.
- Production dry-run: `READY_FOR_HUMAN_COADD_PSF_CONTRACT_PROBE`, two
  representative requests, zero network; output SHA-256
  `15ea2dd0c7d760661757e97abe20b6546b8df07d51165ce675137961b468b372`.

No image/invvar access, PSF bulk acquisition, location mutation, morphology
inspection or array-value decode occurred.

## Execution and restart rule

The exact command is embedded in the sealed binding and emitted by `--dry-run`.
A success terminal is `COADD_PSF_CONTRACT_RESOLVED`. A bounded failure is
`COADD_PSF_CONTRACT_PARTIALLY_RESOLVED`. Do not delete, overwrite or rerun the
same audit directory after a partial result; preserve its checkpoints for a
reviewed continuation. Cumulative counters never reset.

**FIXED IMAGE/INVVAR CONTRACT REMAINS RESOLVED.**

**IMAGE/INVVAR BULK ACQUISITION REMAINS NOT AUTHORIZED.**

**PSF BULK ACQUISITION REMAINS NOT AUTHORIZED.**

**LOCATIONS REMAIN IMMUTABLE.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
