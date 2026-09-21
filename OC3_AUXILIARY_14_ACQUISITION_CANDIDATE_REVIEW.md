# OC-3 `AUXILIARY_14_ONLY` acquisition candidate review

**Review state:** `READY_FOR_AUXILIARY_ACQUISITION_HUMAN_REVIEW`

**Candidate state:** `PENDING_HUMAN_REVIEW`

**Final human authorization:** absent

**Network performed by this preparation:** zero requests, zero bytes

## Frozen bindings

| Binding | Value |
|---|---|
| Implementation aggregate | `1ca462cff61ea09f93ac23210e1966bbb7e3be37f231b92901f60b65f89d1ec0` |
| Resolved-contract SHA-256 | `5afff8fddbcb8a9e86ea3f55cf89288840a21ca705bca121ed1b9204c349616d` |
| Candidate SHA-256 | `c1b07c6df47dc8144786aa1d5065d0a211033c0be1fc3237b967c986ec819850` |
| Candidate canonical seal | `766a4b014d176373b268c149553c27fa89cabadf3118a7d35c57e80649b3ea69` |
| Scope | `AUXILIARY_14_ONLY` |
| Resources | 14 |
| Expected primary body bytes | 3,827,520 |
| Primary requests | 14 HEAD + 14 GET = 28 |
| Stage retry pool | 6 requests |
| Stage request cap | 34 requests |
| Starting cumulative requests | 166 |
| Starting cumulative body bytes | 89,836,046 |
| Unchanged global body cap | 1,610,612,736 bytes |
| Concurrency | 1 |
| Expected success terminal | `AUXILIARY_PRODUCTS_ACQUIRED` |

The original 200-request value remains frozen as the historical planning estimate and cap used through Probe 002. It is not reset or edited. Future request safety is enforced by this candidate's closed stage-local cap while every request continues to increment the cumulative counter.

## Exact acquisition order

1. south NEXP g
2. south NEXP r
3. south NEXP z
4. south PSFSIZE g
5. south PSFSIZE r
6. south PSFSIZE z
7. south MASKBITS
8. north NEXP g
9. north NEXP r
10. north NEXP z
11. north PSFSIZE g
12. north PSFSIZE r
13. north PSFSIZE z
14. north MASKBITS

All URLs, Content-Length values, ETags, representations and resource identities are inherited directly from the immutable resolved contract. Any HEAD discrepancy is representation drift and stops before GET. The implementation does not re-probe or choose an alternate URL.

## Offline validation

- Focused accounting/acquisition suite: **49/49 PASS**, 0 failures, 0 skips; SHA-256 `4bb558995dada648d88c150ddcbf2d51756064352edff56e8023c99f10df434b`.
- Full offline regression: **732/732 PASS**, 0 failures, 0 skips, `real_network_requests=0`; SHA-256 `9f856038b41070776e5e8fdad97adb29aae033c3d2d952c2ea4bd5c99dcae3fb`.
- Production candidate validation: `AUXILIARY_ACQUISITION_CANDIDATE_VALID_FOR_HUMAN_REVIEW`, `network_requests=0`; SHA-256 `45edde451925387425cd3efe77657757585c7c3b5ab5392e6fa8c446a6aea056`.

The candidate is a technical proposal and contains no authorization or human-approval fields. Location selection, image/invvar acquisition, automatic resume and science-pixel interpretation remain disabled.

**READY FOR AUXILIARY ACQUISITION HUMAN REVIEW.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
