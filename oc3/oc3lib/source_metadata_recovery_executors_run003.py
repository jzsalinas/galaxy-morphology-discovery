"""Production action executors behind the recovery worker capability boundary."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import urllib.request

from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed, write_json_immutable
from .autonomous_recovery_envelope import RecoveryEnvelopeError, validate_patch_manifest
from .source_metadata_acquisition_pilot import (
    AcquisitionError, AcquisitionSequence, QUERY_LITERALS, REQUEST_ORDER, RESPONSE_CAPS,
    frame_support, parse_counts, parse_schema, query_sha256, validate_source_rows,
)
from recovery_adapters.source_metadata.transport_registry import get_adapter


def _terminal(candidate, failure, *, request_class=None, requests=0, body=0, **extra):
    return sealed({"action_kind": candidate["action_kind"], "application_body_bytes_read": body,
        "failure_class": failure, "network_requests_started": requests,
        "request_class": request_class or candidate["request_class"], "run_id": candidate["run_id"], "schema_version":
        "OC3_SOURCE_METADATA_RECOVERY_ACTION_TERMINAL_002", "source_values_accepted": 0,
        "stage_id": candidate["stage_id"], **extra})


def documentary_probe(candidate, output: Path, authorities: dict[str, object]):
    resources = [r for r in authorities["resources"] if r["authority_class"] in candidate["authority_classes"]]
    cap = candidate["application_body_reservation"]; used = 0; records = []
    raw = output / "RAW_TECHNICAL"; raw.mkdir(exist_ok=True)
    for index, resource in enumerate(resources[:candidate["network_request_reservation"]], 1):
        intent = sealed({"resource_id": resource["id"], "schema_version":
            "OC3_RECOVERY_DOCUMENTARY_REQUEST_INTENT_001", "url": resource["url"]})
        intent = sealed({**{k:v for k,v in intent.items() if k != "sealed"}, "run_id":candidate["run_id"]})
        write_json_immutable(output / f"REQUEST_INTENT_{index:02d}.json", intent)
        request = urllib.request.Request(resource["url"], method="GET", headers={"Accept-Encoding":"identity"})
        response = urllib.request.urlopen(request, timeout=300)
        data = response.read(cap - used + 1)
        if used + len(data) > cap:
            raise RecoveryEnvelopeError("TECHNICAL_DOCUMENTARY_BODY_CAP_EXCEEDED")
        path = raw / f"{resource['id']}.body"; path.write_bytes(data); used += len(data)
        records.append({"body_sha256":hashlib.sha256(data).hexdigest(),"content_type":response.headers.get("Content-Type", ""),
            "http_status":response.getcode(),"resource_id":resource["id"]})
    write_json_immutable(output / "DOCUMENTARY_EVIDENCE.json", sealed({"records":records,"run_id":candidate["run_id"],
        "schema_version":"OC3_SOURCE_METADATA_DOCUMENTARY_EVIDENCE_001"}))
    return _terminal(candidate, "DOCUMENTARY_EVIDENCE_ACQUIRED", requests=len(records), body=used)


def integrity_triage(candidate, output: Path):
    parent = load_canonical_json(PROJECT / candidate["parent_action_terminal"]["path"])
    proven = bool(parent.get("response_content_type") or parent.get("diagnostic_class")) and parent.get("source_values_accepted",0) == 0
    failure = "DATALAB_SCHEMA_MISMATCH" if proven else "AUTHORITY_CLASS_EXPANSION"
    write_json_immutable(output / "TRIAGE.json", sealed({"representation_level_proven":proven,"run_id":candidate["run_id"],
        "schema_version":"OC3_SOURCE_METADATA_TECHNICAL_TRIAGE_001"}))
    return _terminal(candidate, failure, request_class="OFFLINE", representation_level_proven=proven)


def _git_changed_paths(base_commit: str, allowed_prefixes: tuple[str, ...]) -> list[str]:
    head = subprocess.run(["git","rev-parse","HEAD"],cwd=PROJECT,check=True,
        capture_output=True,text=True).stdout.strip()
    if head != base_commit:
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_BASE_COMMIT_MISMATCH")
    result = subprocess.run(["git","diff","--name-only",base_commit,"--"],cwd=PROJECT,
        check=True,capture_output=True,text=True)
    untracked = subprocess.run(["git","ls-files","--others","--exclude-standard"],cwd=PROJECT,
        check=True,capture_output=True,text=True).stdout.splitlines()
    paths=set(row for row in result.stdout.splitlines() if row)
    paths.update(row for row in untracked if row.startswith(allowed_prefixes))
    return sorted(paths)


def _git_blob_sha256(base_commit: str, path: str) -> str | None:
    result = subprocess.run(["git","show",f"{base_commit}:{path}"],cwd=PROJECT,
        check=False,capture_output=True)
    return hashlib.sha256(result.stdout).hexdigest() if result.returncode == 0 else None


def offline_repair(candidate, output: Path):
    patch_binding = candidate.get("technical_patch_manifest")
    contract_binding = candidate.get("technical_transport_contract")
    receipt_binding = candidate.get("test_receipts")
    if not all(isinstance(item, dict) for item in (patch_binding, contract_binding, receipt_binding)):
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_MANIFEST_REQUIRED")
    path = PROJECT / patch_binding["path"]
    if file_sha256(path) != patch_binding["sha256"]:
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_MANIFEST_INVALID")
    contract_path = PROJECT / contract_binding["path"]
    receipts_path = PROJECT / receipt_binding["path"]
    if (file_sha256(contract_path) != contract_binding["sha256"] or
            file_sha256(receipts_path) != receipt_binding["sha256"]):
        raise RecoveryEnvelopeError("TECHNICAL_REPAIR_ARTIFACT_BINDING_INVALID")
    manifest = load_canonical_json(path)
    contract = load_canonical_json(contract_path)
    receipts = load_canonical_json(receipts_path)
    if any(value.get("run_id") != candidate.get("run_id") for value in (manifest, contract, receipts)):
        raise RecoveryEnvelopeError("RECOVERY_RUN_ID_MISMATCH")
    authorities = load_canonical_json(PROJECT / candidate["technical_authorities"]["path"])
    registry_adapter=next((row for row in authorities["adapters"]
        if row["adapter_id"]==contract.get("adapter_id")),None)
    if (registry_adapter is None or contract.get("implementation_path") != registry_adapter["implementation_path"]):
        raise RecoveryEnvelopeError("TECHNICAL_TRANSPORT_CONTRACT_INVALID")
    surface = load_canonical_json(PROJECT / candidate["mutable_technical_surface"]["path"])
    validate_patch_manifest(manifest, surface)
    actual = _git_changed_paths(manifest["base_commit"],tuple(surface["allowed_path_prefixes"]))
    declared = sorted(row["path"] for row in manifest["changed_paths"])
    if actual != declared:
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_GIT_DIFF_MISMATCH")
    rows={row["path"]:row for row in manifest["changed_paths"]}
    for changed_path in actual:
        current=PROJECT/changed_path
        after=file_sha256(current) if current.is_file() else None
        if (rows[changed_path]["before_sha256"] != _git_blob_sha256(manifest["base_commit"],changed_path) or
                rows[changed_path]["after_sha256"] != after):
            raise RecoveryEnvelopeError("TECHNICAL_PATCH_GIT_DIFF_MISMATCH")
    adapter_id = contract.get("adapter_id")
    implementation_path=PROJECT/registry_adapter["implementation_path"]
    if not isinstance(adapter_id, str) or not adapter_id or not implementation_path.is_file():
        raise RecoveryEnvelopeError("TECHNICAL_TRANSPORT_CONTRACT_INVALID")
    implementation_sha=file_sha256(implementation_path)
    if implementation_sha != registry_adapter["bootstrap_sha256"]:
        row=next((item for item in manifest["changed_paths"]
            if item["path"]==registry_adapter["implementation_path"]),None)
        if row is None or row["after_sha256"] != implementation_sha:
            raise RecoveryEnvelopeError("TECHNICAL_PATCH_GIT_DIFF_MISMATCH")
    return _terminal(candidate, "TECHNICAL_PATCH_VALIDATED", request_class="OFFLINE",
        adapter_activated=adapter_id, patch_manifest=patch_binding,
        adapter_implementation_binding={"adapter_id":adapter_id,
            "implementation_path":registry_adapter["implementation_path"],
            "implementation_sha256":implementation_sha},
        technical_transport_contract=contract_binding, test_receipts=receipt_binding)


def validate_material_adapter_binding(candidate: dict[str, object]) -> None:
    active=candidate.get("active_adapter_binding")
    if (not isinstance(active,dict) or active.get("adapter_id") != candidate.get("active_adapter") or
            not isinstance(active.get("implementation_path"),str)):
        raise RecoveryEnvelopeError("ADAPTER_IMPLEMENTATION_DRIFT")
    implementation=PROJECT/active["implementation_path"]
    if not implementation.is_file() or file_sha256(implementation) != active.get("implementation_sha256"):
        raise RecoveryEnvelopeError("ADAPTER_IMPLEMENTATION_DRIFT")


def material_acquisition(candidate, output: Path, invariants: dict[str, object]):
    try:
        validate_material_adapter_binding(candidate)
    except RecoveryEnvelopeError:
        return _terminal(candidate,"ADAPTER_IMPLEMENTATION_DRIFT",request_class="MATERIAL")
    queries = {row["id"]: row for row in invariants["queries"]}
    if tuple(queries) != REQUEST_ORDER or any(query_sha256(queries[q]["literal_adql"]) != queries[q]["semantic_sha256"] for q in REQUEST_ORDER):
        raise RecoveryEnvelopeError("SCIENTIFIC_QUERY_SEMANTICS_INVALID")
    adapter = get_adapter(candidate["active_adapter"])
    raw = output / "RAW_IMMUTABLE"; raw.mkdir(exist_ok=True)
    bodies={}; records=[]; total=0
    sequence=AcquisitionSequence(); counts={}
    frame=invariants["pilot_frame"]
    brick_ids,_,_=frame_support(PROJECT/frame["path"],frame["sha256"])
    try:
        for query_id in REQUEST_ORDER:
            body, record = adapter.execute(query_id, queries[query_id]["literal_adql"], RESPONSE_CAPS[query_id],
                {"adapter_validated":True,"stage_id":candidate["stage_id"]})
            total += len(body); bodies[query_id]=body; records.append(record)
            (raw/f"{query_id}.csv").write_bytes(body)
            if query_id == "schema": sequence.accept_schema(parse_schema(io.StringIO(body.decode("utf-8"))))
            elif query_id.endswith("_count"):
                domain=query_id.split("_")[0]; counts[domain]=parse_counts(io.StringIO(body.decode("utf-8")))
                sequence.accept_count(domain,counts[domain])
                if sequence.resource_bound:
                    return _terminal(candidate,"SOURCE_COUNT_RESOURCE_BOUND",request_class="MATERIAL",requests=len(records),body=total)
            elif query_id.endswith("_rows"):
                domain=query_id.split("_")[0]
                if not sequence.rows_allowed(): raise AcquisitionError("SOURCE_COUNT_ROW_MISMATCH")
                validate_source_rows(io.StringIO(body.decode("utf-8")),counts[domain],brick_ids)
        failure="SOURCE_METADATA_ACQUISITION_COMPLETED"
    except AcquisitionError as exc:
        failure=exc.code
    write_json_immutable(output/"TRANSPORT_EVIDENCE.json",sealed({"adapter":candidate["active_adapter"],"run_id":candidate["run_id"],
        "records":records,"schema_version":"OC3_SOURCE_METADATA_RECOVERY_MATERIAL_TRANSPORT_001"}))
    return _terminal(candidate,failure,request_class="MATERIAL",requests=len(records),body=total)


def execute_action(candidate: dict[str, object], output: Path, authorities: dict[str, object],
                   invariants: dict[str, object]):
    kind=candidate["action_kind"]
    if kind == "TECHNICAL_RESPONSE_DIAGNOSTIC":
        from oc3_source_metadata_recovery_worker_run003 import execute_diagnostic
        return execute_diagnostic(candidate, output)
    if kind == "OFFICIAL_SERVICE_DOCUMENTARY_PROBE": return documentary_probe(candidate,output,authorities)
    if kind == "TECHNICAL_INTEGRITY_TRIAGE": return integrity_triage(candidate,output)
    if kind == "OFFLINE_TECHNICAL_REPAIR": return offline_repair(candidate,output)
    if kind == "MATERIAL_SOURCE_METADATA_ACQUISITION": return material_acquisition(candidate,output,invariants)
    raise RecoveryEnvelopeError("RECOVERY_ACTION_KIND_NOT_ALLOWED")
