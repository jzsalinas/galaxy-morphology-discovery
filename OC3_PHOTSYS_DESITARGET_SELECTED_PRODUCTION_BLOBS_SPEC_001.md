# OC3 selected desitarget production-blob specification 001

## Prospective selection

The complete non-truncated tree for exact `desitarget` commit `dd30297f9d50fcb7bbba57d79d4b8fc86cb35701` identifies three relevant production files not present in the previously acquired mandatory bundle:

1. `py/desitarget/targets.py`, which the official DR9 files page links at tag 0.48.0 when describing random-catalog north/south resolution;
2. `bin/split_randoms`;
3. `bin/alt_split_randoms`.

Together with the already acquired `randoms.py`, `io.py`, `select_randoms`, and `supplement_randoms`, the two executables complete the set of non-test paths in the exact tree whose names contain `randoms`. Their exact path, blob SHA, and decoded size must match the immutable tree inventory. No other blob is authorized.

## Transport and analysis

Each blob is retrieved once, sequentially, through its exact official GitHub Git Data API URL. The same HTTP, content-type, base64, decoded-size, Git-blob identity, redirect, retry, and firewall rules used by the mandatory bundle apply. After validation, the frozen eight search terms are evaluated offline across these three files. A missing named-product literal is negative evidence only for this selected set.

## Scientific boundary

The stage uses only `EXACT_DESITARGET_0_48_0_METADATA_AND_SOURCE`. It may characterize random-catalog resolution and splitting, but cannot infer the producer of `survey-bricks-dr9-randoms-0.48.0.fits` without an explicit trace. It reads no astronomical product or protected value and cannot create a resolver or start Panel V2, P1, or morphological discovery.
