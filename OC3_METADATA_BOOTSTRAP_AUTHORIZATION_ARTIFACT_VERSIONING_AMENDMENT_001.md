# OC3 Metadata Bootstrap Authorization Artifact Versioning Amendment 001

Status: prospective implementation authority; this document does not authorize network execution or create authorization artifacts.

## Frozen correction

Candidate and final authorization identity is determined by the exact canonical file bytes, exact SHA-256, exact absolute path bound in the command argv, and exact candidate/final cross-binding. It is not determined by a permanently hard-coded `001` filename.

For `FIRST_RUN_NETWORK`, the final authorization path SHALL be the actual absolute canonical `--authorization` path. Candidate `final_authorization_path` SHALL equal that path exactly. Final authorization `authorization_candidate_path` SHALL be an explicitly bound absolute canonical regular-file path inside the canonical project, with a versioned candidate filename; its canonical bytes and SHA-256 SHALL match `authorization_candidate_sha256`, and the candidate SHALL pass the unchanged offline validation. Candidate `rights_binding_path` SHALL equal the actual absolute `--rights-binding` argv path exactly.

No relative path, basename-only comparison, symlink path, outside-project path, wildcard, implicit discovery or “latest” resolution is allowed. All existing schema, state, digest, technical-equivalence, command, rights, implementation, environment, resource, cap, patch-model, negative-capability and human-authorization checks remain mandatory before transport construction.

Rights Binding 002, Authorization Candidate 001 and Final Authorization 001 remain immutable historical evidence for the prior implementation aggregate. They SHALL NOT be modified, renamed, deleted or reused as current authorization. Future versioned artifacts require a new reviewed rights binding, candidate and separate human authorization.
