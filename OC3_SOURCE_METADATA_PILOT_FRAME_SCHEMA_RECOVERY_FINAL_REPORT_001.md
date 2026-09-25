# OC3 Source-Metadata Pilot-Frame Schema Recovery Final Report 001

## Scientific outcome

`SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERED`

The exact frozen pilot frame was derived offline from the four bound local authorities through the audited case-sensitive provider physical contracts and the supervised memory-bounded implementation. The recovered frame passed its frozen sealed-payload validation. No retry, fallback worker or historical implementation was used.

The immediately preceding supervised failure remains classified as `IMPLEMENTATION_SCHEMA_CASE_MISMATCH`. The earlier opaque predecessor remains `TECHNICAL_CAUSE = UNKNOWN`; this successful recovery does not retrospectively reclassify it.

## Execution evidence

- Worker return code: `0`.
- Terminating signal: `null`.
- Worker error taxonomy code: `null`.
- Phase checkpoint: `FRAME_VALIDATED`.
- Wall time: `11.089861497` seconds.
- Peak RSS diagnostic: `321680` KiB on Linux. This is `ru_maxrss`, the maximum over completed child processes; it is not an OOM inference.
- Worker stdout: 237 bytes, SHA-256 `d89bf71d2aee75ae27220fced30473f1871287c2af3a6e3ccd9c62df3be16574`, not truncated.
- Worker stderr: 0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, not truncated.
- Complete physical-contract validation before allowed cell access: `PASS` for `ROOT_SUMMARY`, `NORTH_SUMMARY` and `SOUTH_SUMMARY`.
- Sealed `PILOT_FRAME.json` validation: `PASS`.
- `PILOT_FRAME.json` SHA-256: `661f4d429f8fe0b6aa0104e093d79568d6f274935a7d9b0e78fb3dd45ae40292`.
- `EXECUTION_DIAGNOSTIC.json` SHA-256: `fec38b96c99c04f7542a0d440798b1ac1c59382c2185fe7a250c0ea4388da76d`.
- `TERMINAL.json` SHA-256: `8c56ae813fa8c9c562b6fe2861471799f981d112efd8b90a2ddead5f50dfe6d3`.

## Frozen selections

### PILOT_TARGET_1

- Global identity: `2255p305`, `BRICKID=498957`.
- Selection digest: `000bb3f372e5becee5491b0fcded81202ab31b1e80149421af44bcdd089d5b21`.
- Guard count: 7.
- Guard memberships: `2255p302/497712`, `2257p302/497713`, `2252p305/498956`, `2255p305/498957`, `2258p305/498958`, `2254p307/500198`, `2257p307/500199`.

### PILOT_TARGET_2

- Global identity: `1901p342`, `BRICKID=517112`.
- Selection digest: `000c375787a443ec667d617843b7e340b4d8f2e98790f21b404420fcb9255c0b`.
- Guard count: 7.
- Guard memberships: `1900p340/515917`, `1903p340/515918`, `1897p342/517111`, `1901p342/517112`, `1904p342/517113`, `1898p345/518303`, `1901p345/518304`.

### RESERVED_HOLDOUT_1

- Global identity: `1075p337`, `BRICKID=514444`.
- Selection digest: `000e3602b1bbe15099e1f2af412ab03088e7c04f62ba0aa69bfdbcccb3657e8f`.
- Guard count: 7.
- Guard memberships: `1074p335/513241`, `1077p335/513242`, `1072p337/514443`, `1075p337/514444`, `1078p337/514445`, `1073p340/515642`, `1076p340/515643`.

### RESERVED_HOLDOUT_2

- Global identity: `0381m012`, `BRICKID=323320`.
- Selection digest: `0010377310b7f7197ce835fd2ad7050c40e1bf8dfcd6f95248b55036b9e01d42`.
- Guard count: 9.
- Guard memberships: `0378m015/321879`, `0381m015/321880`, `0383m015/321881`, `0378m012/323319`, `0381m012/323320`, `0383m012/323321`, `0378m010/324759`, `0381m010/324760`, `0383m010/324761`.

The four guards are pairwise disjoint, and each selected identity belongs to its own guard. The selection algorithms, counts, hash literals and guard topology are exactly those frozen before execution.

## Firewall and interpretation boundary

Network requests, response-body bytes, retries, Data Lab accesses, source rows, source counts, PHOTSYS, TYPE, DCHISQ, Sersic/shape, photometry, photo-z, pixels, morphology, labels, models, training, embeddings, clustering, matching, radius operations, search-bound selections, scientific-threshold selections, object-group IDs, split-group IDs, Panel V3 and P1 were all zero.

No source-derived information was observed. The recovered identities and guards come solely from the already-bound local brick identity and geometry authorities. No holdout source data was inspected.
