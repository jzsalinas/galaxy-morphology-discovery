"""Prospective Run-005 material executor with governed transport failures.

This module is prepared offline.  No Run-005 candidate or authorization exists.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any
import urllib.request

from .cross_observer_grouping import PROJECT, file_sha256, sealed, write_json_immutable
from .autonomous_recovery_envelope import RecoveryEnvelopeError
from .source_metadata_acquisition_pilot import (
    AcquisitionError, AcquisitionSequence, QUERY_LITERALS, REQUEST_ORDER, RESPONSE_CAPS,
    RejectRedirect, frame_support, frozen_headers, parse_counts, parse_schema, query_sha256, query_url,
    validate_source_rows,
)
from .source_metadata_transport_accounting import stream_bounded_response

TIMEOUT_SECONDS = 300


def _terminal(candidate: dict[str, Any], failure: str, *, requests: int, body: int,
        observations: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    return sealed({"schema_version":"OC3_SOURCE_METADATA_RECOVERY_ACTION_TERMINAL_003",
        "run_id":candidate["run_id"],"stage_id":candidate["stage_id"],
        "action_kind":candidate["action_kind"],"request_class":"MATERIAL",
        "failure_class":failure,"network_requests_started":requests,
        "application_body_bytes_read":body,"source_values_accepted":0,
        "complete_responses_obtained":sum(1 for row in observations if row["response_complete"]),
        "partial_response_count":sum(1 for row in observations if row["partial_body_exists"]),
        "transport_observations":observations,**extra})


def material_acquisition(candidate: dict[str, Any], output: Path, invariants: dict[str, Any],
        *, opener: Any | None = None) -> dict[str, Any]:
    """Execute the frozen action while always returning an authoritative terminal."""
    queries={row["id"]:row for row in invariants["queries"]}
    if tuple(queries) != REQUEST_ORDER or any(
            query_sha256(queries[q]["literal_adql"]) != queries[q]["semantic_sha256"] or
            queries[q]["literal_adql"] != QUERY_LITERALS[q] for q in REQUEST_ORDER):
        raise RecoveryEnvelopeError("SCIENTIFIC_QUERY_SEMANTICS_INVALID")
    raw=output/"RAW_IMMUTABLE"; partial=output/"PARTIAL"; staging=output/"STAGING"
    for directory in (raw,partial,staging): directory.mkdir(parents=True,exist_ok=True)
    transport=opener or urllib.request.build_opener(RejectRedirect())
    observations=[]; requests=0; body_bytes=0; sequence=AcquisitionSequence(); counts={}
    frame=invariants["pilot_frame"]; brick_ids,_,_=frame_support(PROJECT/frame["path"],frame["sha256"])
    failure=None; failed_query=None
    for query_id in REQUEST_ORDER:
        write_json_immutable(output/f"REQUEST_INTENT_{len(observations)+1:02d}_{query_id}.json",sealed({
            "schema_version":"OC3_SOURCE_METADATA_RECOVERY_MATERIAL_REQUEST_INTENT_002",
            "run_id":candidate["run_id"],"stage_id":candidate["stage_id"],"query_id":query_id,
            "request_class":"MATERIAL","query_sha256":query_sha256(QUERY_LITERALS[query_id]),
            "timeout_seconds":TIMEOUT_SECONDS,"response_byte_cap":RESPONSE_CAPS[query_id]}))
        observation=stream_bounded_response(query_id=query_id,opener=transport,
            request=urllib.request.Request(query_url(QUERY_LITERALS[query_id]),headers=frozen_headers(),method="GET"),
            timeout_seconds=TIMEOUT_SECONDS,byte_cap=RESPONSE_CAPS[query_id],
            staging_path=staging/f"{query_id}.tmp",complete_path=raw/f"{query_id}.csv",
            partial_path=partial/f"{query_id}.partial")
        row=observation.record(); observations.append(row)
        requests += observation.request_started; body_bytes += observation.body_bytes_preserved
        if not observation.response_complete:
            failure="DATALAB_TRANSPORT_FAILURE"; failed_query=query_id; break
        try:
            data=(raw/f"{query_id}.csv").read_bytes()
            text=io.StringIO(data.decode("utf-8"))
            if query_id == "schema": sequence.accept_schema(parse_schema(text))
            elif query_id.endswith("_count"):
                domain=query_id.split("_")[0]; counts[domain]=parse_counts(text)
                sequence.accept_count(domain,counts[domain])
                if sequence.resource_bound:
                    failure="SOURCE_COUNT_RESOURCE_BOUND"; failed_query=query_id; break
            else:
                domain=query_id.split("_")[0]
                if not sequence.rows_allowed(): raise AcquisitionError("SOURCE_COUNT_ROW_MISMATCH")
                validate_source_rows(text,counts[domain],brick_ids)
        except (AcquisitionError,UnicodeError) as exc:
            failure=exc.code if isinstance(exc,AcquisitionError) else "DATALAB_SCHEMA_MISMATCH"
            failed_query=query_id; break
    if failure is None: failure="SOURCE_METADATA_ACQUISITION_COMPLETED"
    evidence=sealed({"schema_version":"OC3_SOURCE_METADATA_RECOVERY_MATERIAL_TRANSPORT_002",
        "run_id":candidate["run_id"],"stage_id":candidate["stage_id"],"records":observations,
        "network_requests_started":requests,"application_body_bytes_preserved":body_bytes,
        "source_values_accepted":0})
    write_json_immutable(output/"TRANSPORT_EVIDENCE.json",evidence)
    evidence_binding={"path":str((output/"TRANSPORT_EVIDENCE.json").relative_to(PROJECT)),
        "sha256":file_sha256(output/"TRANSPORT_EVIDENCE.json")}
    return _terminal(candidate,failure,requests=requests,body=body_bytes,observations=observations,
        failed_query_id=failed_query,transport_evidence=evidence_binding)
