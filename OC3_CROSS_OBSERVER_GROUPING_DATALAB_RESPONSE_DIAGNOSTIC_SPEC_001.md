# OC3 Cross-Observer Grouping Data Lab Response Diagnostic 001

Stage: `OC3-CROSS-OBSERVER-GROUPING-DATALAB-COLUMN-METADATA-RESPONSE-DIAGNOSTIC-001`.

This prospective action diagnoses only the representation returned by the
exact Data Lab `TAP_SCHEMA.columns` URL already frozen in Resource Manifest
002. Candidate 002 failed closed before reading its fifth response body because
the observed Content-Type was outside that candidate's allowlist.

The action permits one sequential GET, 65,536 body bytes, zero redirects, zero
retries, and no resume. It accepts only CSV, plain text, XML, or VOTable error
representations. It records exact transport metadata, preserves the exact body
read-only, and may classify only whether the response is usable schema metadata
or a provider diagnostic/error representation.

It cannot read source rows, change the original query, inspect any other URL,
pass the documentary Gate, select a matching threshold, or emit a mission
terminal. A failure remains closed and consumes its permit.
