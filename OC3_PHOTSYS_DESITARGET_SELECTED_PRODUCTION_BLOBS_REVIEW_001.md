# OC3 selected desitarget production-source review 001

The governed action acquired and searched the three prospectively selected blobs from exact `desitarget` commit `dd30297f9d50fcb7bbba57d79d4b8fc86cb35701`.

- Terminal state: `DESITARGET_SELECTED_PRODUCTION_BLOBS_ACQUIRED`
- Terminal SHA-256: `45fba38afa4ece2a7c5e0273e6a29f8ab238b24571af50da7134b573debdcee6`
- Search-results SHA-256: `a12ad4403e84e520b13c38f479a48a196e82ecad36fad6a93d46d10a27fa324f`
- Resource-receipts SHA-256: `b81f5940c30f119e98f9108471f80673f61c68c093ea991f01cf10b10f41f992`
- Requests consumed: `3`
- Application-body bytes consumed: `73772`
- Retries: `0`
- Remaining requests: `6`
- Remaining application-body bytes: `16998947`

## Findings

`py/desitarget/targets.py` implements `resolve(targets)` for northern/southern imaging overlap. It obtains `PHOTSYS` or derives it from `RELEASE`/`TARGETID`, identifies `N`, and selects northern versus southern photometry by sky position. It does not define an outside-footprint category or construct the named brick-summary product.

`bin/split_randoms` and `bin/alt_split_randoms` read, shuffle, and divide an existing random catalog into numbered FITS files. They neither create the brick-summary product nor add `PHOTSYS` or `AREA_PER_BRICK`.

The frozen search found no occurrence of `survey-bricks`, `survey-bricks-dr9-randoms`, `AREA_PER_BRICK`, `supplement_randoms`, `zeros=True`, or `write_randoms` in these three files. `PHOTSYS` and `resolve` occur only in `targets.resolve`. This provides no trace from the supplemental outside-brick path to physical byte `0x00` in `survey-bricks-dr9-randoms-0.48.0.fits`.

Combined with the complete non-truncated 336-entry commit-tree inventory and the previously evaluated mandatory producer files, every non-test path in the exact tree whose name contains `randoms`, plus the official documentation's explicitly linked resolver, has now been evaluated. No exact named-product generator or aggregation script is present in that deterministically selected production set. This does not prove absence from an external historical production environment.

All astronomical and protected-value firewall counters remain zero.
