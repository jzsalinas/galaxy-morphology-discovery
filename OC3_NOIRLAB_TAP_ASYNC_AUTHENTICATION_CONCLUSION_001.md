# OC3 NOIRLab TAP Async Authentication Conclusion 001

Status: **CURRENTLY UNRESOLVED — ANONYMOUS DIRECT-TAP ASYNC NOT ESTABLISHED**.

The preserved official Data Lab manual page is an index. It links separately to Catalog Data Access (TAP/SCS), Query Manager and Job Manager documentation, but contains no operational or authentication contract for those interfaces. The preserved official capabilities representation advertises a TAP base access URL but contains no anonymous-access declaration and no async security method.

Existing project evidence that Query Manager synchronous public-dataset queries can use anonymous access does not establish that direct TAP/UWS job creation, phase transition, polling, result retrieval, error retrieval or destruction is anonymous. No credentials, account or authenticated pathway is authorized or implied.

Conclusion: `anonymous_direct_tap_async_supported = NOT_ESTABLISHED`. This evidence supports neither `ANONYMOUS_TAP_ASYNC_PROBE_JUSTIFIED` nor `AUTHENTICATED_ASYNC_DECISION_REQUIRED`; the authentication requirement itself remains undocumented in the available offline corpus.
