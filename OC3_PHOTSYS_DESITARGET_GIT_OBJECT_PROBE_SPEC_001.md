# OC3 exact desitarget Git-object probe specification 001

## Scope

This prospective stage may retrieve metadata for one exact Git object from the official `desihub/desitarget` GitHub API. It is limited to the commit already bound to tag `0.48.0`, or to a root tree SHA established by a successful commit-object action under this specification. It does not retrieve source blobs, an archive, astronomical data, or survey-table values.

The first action is:

- stage: `OC3-GALAXY-ELIGIBILITY-PHOTSYS-DESITARGET-COMMIT-OBJECT-PROBE-001`;
- scope: `DESITARGET_EXACT_COMMIT_OBJECT_METADATA_ONLY`;
- method: one `GET`;
- literal URL: `https://api.github.com/repos/desihub/desitarget/git/commits/dd30297f9d50fcb7bbba57d79d4b8fc86cb35701`;
- redirects: zero;
- retries: zero;
- concurrency: one;
- accepted body maximum: 131,072 bytes;
- charged/read reservation: 131,073 bytes, including the one-byte over-cap detector.

## Frozen request and response contract

The request sends `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, `Accept-Encoding: identity`, `Connection: close`, and the frozen project user agent. No credential is used.

Success requires HTTP 200, an accepted JSON content type, identity/no content encoding, a body no larger than 131,072 bytes, canonical JSON decoding, exact top-level commit SHA `dd30297f9d50fcb7bbba57d79d4b8fc86cb35701`, and one valid 40-hex root-tree SHA in `tree.sha`. The immutable raw JSON body and a sealed response receipt are retained locally. Only the commit identity, root-tree identity, byte count, and transport metadata enter the compact terminal.

Any redirect, non-200 status, content-type/encoding mismatch, malformed JSON, commit mismatch, missing or malformed tree SHA, declared over-cap body, or observed 131,073rd byte is terminally inconclusive/failed as frozen by the candidate. No fallback resource, retry, body continuation, or archive acquisition is allowed.

## Future tree action

After a successful commit-object terminal, a separate prospective candidate may bind exactly:

`https://api.github.com/repos/desihub/desitarget/git/trees/<OBSERVED_ROOT_TREE_SHA>?recursive=1`

That later action must retain this specification, freeze its own body cap and literal manifest, and require `truncated=false`. The observed tree SHA may not be guessed or taken from an unbound source.

## Scientific and autonomy boundary

This stage uses only `EXACT_DESITARGET_0_48_0_METADATA_AND_SOURCE`. All astronomical-data and protected-value firewall counters remain zero. It cannot determine PHOTSYS semantics, producer behavior, named-product provenance, or a scientific outcome. It cannot start Panel V2, P1, a V2 resolver, or morphological discovery.
