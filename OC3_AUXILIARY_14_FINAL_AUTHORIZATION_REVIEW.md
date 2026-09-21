# OC-3 `AUXILIARY_14_ONLY` final authorization review

**Authorization state:** `FINAL_HUMAN_AUTHORIZATION`

**Decision:** `AUTHORIZED`

**Authorized by:** José Salinas

**Authorized at (UTC):** `2026-09-21T12:19:58Z`

**Network performed by authorization and preflight:** zero requests, zero bytes

## Frozen bindings

| Binding | Value |
|---|---|
| Authorization path | `oc3/INPUTS/OC3_AUXILIARY_ACQUISITION_AUTHORIZATION_001.json` |
| Authorization SHA-256 | `43bd2b9f97087a8a67915d3ff41e3a3ea305c0f6ea6603a7cb82b619deb8cbcf` |
| Candidate SHA-256 | `c1b07c6df47dc8144786aa1d5065d0a211033c0be1fc3237b967c986ec819850` |
| Candidate canonical seal | `766a4b014d176373b268c149553c27fa89cabadf3118a7d35c57e80649b3ea69` |
| Resolved-contract SHA-256 | `5afff8fddbcb8a9e86ea3f55cf89288840a21ca705bca121ed1b9204c349616d` |
| Implementation aggregate | `1ca462cff61ea09f93ac23210e1966bbb7e3be37f231b92901f60b65f89d1ec0` |
| Scope | `AUXILIARY_14_ONLY` |
| Resources | 14 |
| Expected primary body bytes | 3,827,520 |
| Primary requests | 14 HEAD + 14 GET = 28 |
| Stage retry pool | 6 requests |
| Stage request cap | 34 requests |
| Starting cumulative requests | 166 |
| Starting cumulative body bytes | 89,836,046 |
| Global body cap | 1,610,612,736 bytes |
| Concurrency | 1 |
| Expected success terminal | `AUXILIARY_PRODUCTS_ACQUIRED` |

The production authorization validator accepted the canonical authorization and its exact candidate binding. The focused result was `FINAL_HUMAN_AUTHORIZATION_VALIDATED`; its local evidence SHA-256 was `6c30f71f0674643a56d4d63f0dbc4c8516774415fb886dadfa4bf8049a61f4d5`.

The offline preflight validated the paths, command, runtime caps, candidate and authorization, then stopped before construction of `LiteralHTTPTransport`. Its result was `READY_AT_REAL_TRANSPORT_BOUNDARY`; its local evidence SHA-256 was `7593b6a2100273e7e67b77c73371438bf6dc0e41fd75c846002aecb8e08bf68d`.

This authorization covers only the ordered 14-resource auxiliary inventory sealed in the candidate. Image/invvar acquisition, location selection, morphology, automatic retry and automatic resume remain unauthorized.

## Authorized human-executable command

```bash
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python \
  /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_resource_contract.py \
  --acquire-auxiliary \
  --execute-network \
  --project /home/jzsalinas/Documents/galaxy-morphology-discovery \
  --contract-manifest /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/RESOURCE_CONTRACT_RESOLVED.json \
  --candidate /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_AUXILIARY_14_ACQUISITION_CANDIDATE_001.json \
  --authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_AUXILIARY_ACQUISITION_AUTHORIZATION_001.json \
  --audit-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/auxiliary_acquisition/OC3-RESOURCE-CONTRACT-AUXILIARY-ACQUISITION-001 \
  --log /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/auxiliary_acquisition/OC3-RESOURCE-CONTRACT-AUXILIARY-ACQUISITION-001/AUXILIARY_RUN.log \
  --stage-request-cap 34 \
  --stage-retry-request-pool 6 \
  --expected-body-bytes 3827520
```

**AUXILIARY_14_ONLY FINAL AUTHORIZATION READY.**

**NEXT ACTION: HUMAN EXECUTES THE AUTHORIZED AUXILIARY ACQUISITION.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
