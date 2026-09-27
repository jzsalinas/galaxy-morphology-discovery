"""Human-invoked, restartable acquisition of the five frozen metadata responses."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from typing import Any
import urllib.request
from urllib.error import HTTPError

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, sealed
from .source_metadata_acquisition_pilot import (
    QUERY_LITERALS, REQUEST_ORDER, RESPONSE_CAPS, RejectRedirect, query_sha256,
    query_url, validate_frozen_support,
)
from .source_metadata_transport_accounting import stream_bounded_response

STAGE_ID = "OC3-MANUAL-SOURCE-METADATA-ACQUISITION-001"
ENDPOINT = "https://datalab.noirlab.edu/query/query"
TIMEOUT_SECONDS = 600
RETRIES = 0
SCHEMA_SOURCE = PROJECT / "oc3/source_metadata_autonomous_recovery_run_004/OC3-SOURCE-METADATA-RECOVERY-RUN-004-G01-MATERIAL_SOURCE_METADATA_ACQUISITION/RAW_IMMUTABLE/schema.csv"
SCHEMA_SHA256 = "4605a1303c96cf2156446702e857382cf8365553a2ad5db91b6b2b9b6bb7d3ca"
SCHEMA_BYTES = 2124
ALLOWED_TOP_LEVEL = {"RAW_ACQUIRED", "PARTIAL", "EVIDENCE", "STAGING", "ACQUISITION_MANIFEST.json", "ACQUISITION_LOG.jsonl", "EXECUTION_SUMMARY.json"}


class ManualRejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(req.full_url, code, "DATALAB_REDIRECT_FORBIDDEN", headers, fp)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_canonical(path: Path, value: dict[str, Any], *, exclusive: bool = False) -> None:
    data = canonical(value) + b"\n"
    mode = "xb" if exclusive else "wb"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode) as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())


def binding_payload() -> dict[str, Any]:
    query_manifest = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_QUERY_MANIFEST_001.json"
    closure = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_004_CLOSURE_001.json"
    command=[str(PROJECT/"oc3/.venv/bin/python"),str(PROJECT/"oc3/oc3_manual_source_metadata_acquisition_001.py"),
        "--run-acquisition","--binding",str(PROJECT/"oc3/INPUTS/OC3_MANUAL_SOURCE_METADATA_ACQUISITION_BINDING_001.json"),
        "--output",str(PROJECT/"oc3/manual_source_metadata_acquisition_001")]
    return sealed({
        "schema_version": "OC3_MANUAL_SOURCE_METADATA_ACQUISITION_BINDING_001",
        "stage_id": STAGE_ID, "provider": "NOIRLAB_DATA_LAB_QUERY_MANAGER",
        "endpoint": ENDPOINT, "http_method": "GET", "public_anonymous": True,
        "credentials_authorized": False, "redirects": 0, "timeout_seconds": TIMEOUT_SECONDS,
        "automatic_retries": RETRIES, "concurrency": 1,
        "request_order": list(REQUEST_ORDER),
        "queries": [{"query_id": q, "adql_sha256": query_sha256(QUERY_LITERALS[q]),
            "response_byte_cap": RESPONSE_CAPS[q]} for q in REQUEST_ORDER],
        "query_manifest": {"path": str(query_manifest.relative_to(PROJECT)), "sha256": file_sha256(query_manifest)},
        "schema_reuse": {"authorized": True, "classification": "REUSED_RUN_004_COMPLETE_SCHEMA_RESPONSE",
            "source_path": str(SCHEMA_SOURCE.relative_to(PROJECT)), "source_sha256": SCHEMA_SHA256,
            "source_bytes": SCHEMA_BYTES, "run_004_closure": {"path": str(closure.relative_to(PROJECT)),
                "sha256": file_sha256(closure)}, "scientific_acceptance": False},
        "raw_outputs_git_required": False,
        "command_argv":command,"command_argv_sha256":hashlib.sha256(canonical(command)).hexdigest(),
    })


def validate_binding(binding: dict[str, Any]) -> None:
    if binding != binding_payload():
        raise ValueError("MANUAL_ACQUISITION_BINDING_DRIFT")
    validate_frozen_support()


def _request(query_id: str) -> urllib.request.Request:
    headers = {"Content-Type": "text/ascii", "User-Agent": "OC3-manual-source-metadata-acquisition/1",
        "X-DL-AuthToken": "anonymous.0.0.anon_access", "X-DL-TimeoutRequest": str(TIMEOUT_SECONDS)}
    return urllib.request.Request(query_url(QUERY_LITERALS[query_id]), headers=headers, method="GET")


def _load_manifest(path: Path, binding_sha: str) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "OC3_MANUAL_SOURCE_METADATA_ACQUISITION_MANIFEST_001",
            "stage_id": STAGE_ID, "binding_sha256": binding_sha, "scientific_acceptance": False,
            "queries": {}, "sealed": ""}
    value = json.loads(path.read_text())
    supplied = value.pop("sealed", None)
    if hashlib.sha256(canonical(value)).hexdigest() != supplied:
        raise ValueError("ACQUISITION_MANIFEST_SEAL_INVALID")
    value["sealed"] = supplied
    if value.get("binding_sha256") != binding_sha or value.get("scientific_acceptance") is not False:
        raise ValueError("ACQUISITION_MANIFEST_BINDING_INVALID")
    return value


def _save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    base = {k: v for k, v in manifest.items() if k != "sealed"}
    write_canonical(path, sealed(base))


def _append_log(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical(event) + b"\n"); handle.flush(); os.fsync(handle.fileno())


def _validate_namespace(root: Path) -> None:
    if not root.exists():
        return
    unknown = {p.name for p in root.iterdir()} - ALLOWED_TOP_LEVEL
    if unknown:
        raise ValueError("UNKNOWN_EXISTING_ACQUISITION_ARTIFACT:" + ",".join(sorted(unknown)))


def _validate_completed(root: Path, query_id: str, record: dict[str, Any]) -> None:
    if record.get("terminal_classification") != "MANUAL_ACQUISITION_RESPONSE_COMPLETE" or not record.get("response_complete"):
        raise ValueError("COMPLETED_RECORD_INVALID")
    path = PROJECT / record["raw_path"]
    if path != root / "RAW_ACQUIRED" / f"{query_id}.csv" or not path.is_file():
        raise ValueError("COMPLETED_OUTPUT_MISSING")
    if file_sha256(path) != record["raw_sha256"] or path.stat().st_size != record["bytes_preserved"]:
        raise ValueError("COMPLETED_OUTPUT_HASH_MISMATCH")


class ElapsedReporter:
    def __init__(self, query_id: str, completed: list[str], interval: float = 30.0):
        self.query_id=query_id; self.completed=completed; self.interval=interval
        self.stop=threading.Event(); self.started=time.monotonic(); self.thread=None
    def __enter__(self):
        print(json.dumps({"query_id":self.query_id,"state":"REQUEST_IN_PROGRESS","started_at_utc":utc(),"completed_queries":self.completed},sort_keys=True),flush=True)
        def report():
            while not self.stop.wait(self.interval):
                print(json.dumps({"query_id":self.query_id,"state":"REQUEST_IN_PROGRESS","elapsed_seconds":round(time.monotonic()-self.started,1),"completed_queries":self.completed},sort_keys=True),flush=True)
        self.thread=threading.Thread(target=report, name="oc3-local-elapsed-reporter", daemon=True); self.thread.start(); return self
    def __exit__(self,*_):
        self.stop.set()
        if self.thread: self.thread.join(timeout=1)


def _reuse_schema(root: Path, manifest: dict[str, Any]) -> None:
    if "schema" in manifest["queries"]:
        return
    if not SCHEMA_SOURCE.is_file() or file_sha256(SCHEMA_SOURCE) != SCHEMA_SHA256 or SCHEMA_SOURCE.stat().st_size != SCHEMA_BYTES:
        raise ValueError("RUN_004_SCHEMA_REUSE_EVIDENCE_INVALID")
    raw = root / "RAW_ACQUIRED/schema.csv"
    raw.parent.mkdir(parents=True, exist_ok=True)
    if raw.exists():
        raise ValueError("UNMANIFESTED_COMPLETE_OUTPUT")
    temp = root / "STAGING/schema.reuse.tmp"; temp.parent.mkdir(parents=True, exist_ok=True)
    with SCHEMA_SOURCE.open("rb") as source, temp.open("xb") as sink:
        while chunk := source.read(65536): sink.write(chunk)
        sink.flush(); os.fsync(sink.fileno())
    os.replace(temp, raw)
    now=utc()
    manifest["queries"]["schema"]={"query_id":"schema","adql_sha256":query_sha256(QUERY_LITERALS["schema"]),
        "provider":"NOIRLAB_DATA_LAB_QUERY_MANAGER","endpoint":ENDPOINT,"http_method":"GET",
        "public_anonymous":True,"timeout_seconds":600,"retries":0,"started_at_utc":now,"finished_at_utc":now,
        "terminal_classification":"MANUAL_ACQUISITION_RESPONSE_COMPLETE","requests_started":0,
        "http_status":None,"content_type":None,"bytes_preserved":SCHEMA_BYTES,
        "raw_path":str(raw.relative_to(PROJECT)),"raw_sha256":SCHEMA_SHA256,"response_complete":True,
        "partial":False,"scientific_acceptance":False,"provenance":"REUSED_RUN_004_COMPLETE_SCHEMA_RESPONSE"}


def run_manual_acquisition(*, binding: dict[str, Any], binding_path: Path, root: Path,
        opener: Any | None = None, reporter_interval: float = 30.0) -> int:
    expected_binding=PROJECT/"oc3/INPUTS/OC3_MANUAL_SOURCE_METADATA_ACQUISITION_BINDING_001.json"
    expected_root=PROJECT/"oc3/manual_source_metadata_acquisition_001"
    if opener is None and (binding_path.resolve()!=expected_binding.resolve() or root.resolve()!=expected_root.resolve()):
        raise ValueError("MANUAL_ACQUISITION_PATH_BINDING_INVALID")
    validate_binding(binding); _validate_namespace(root); root.mkdir(parents=True, exist_ok=True)
    binding_sha=file_sha256(binding_path)
    manifest_path=root/"ACQUISITION_MANIFEST.json"; log_path=root/"ACQUISITION_LOG.jsonl"
    manifest=_load_manifest(manifest_path,binding_sha); _reuse_schema(root,manifest); _save_manifest(manifest_path,manifest)
    completed=[]
    for query_id in REQUEST_ORDER:
        existing=manifest["queries"].get(query_id)
        if existing:
            _validate_completed(root,query_id,existing); completed.append(query_id); continue
        attempt=1+len(list((root/"EVIDENCE"/query_id).glob("attempt-*-TERMINAL.json")))
        evidence=root/"EVIDENCE"/query_id; evidence.mkdir(parents=True,exist_ok=True)
        started=utc()
        intent=sealed({"schema_version":"OC3_MANUAL_SOURCE_METADATA_REQUEST_INTENT_001","query_id":query_id,
            "attempt":attempt,"adql_sha256":query_sha256(QUERY_LITERALS[query_id]),"endpoint":ENDPOINT,
            "timeout_seconds":600,"retries":0,"started_at_utc":started})
        write_canonical(evidence/f"attempt-{attempt:04d}-INTENT.json",intent,exclusive=True)
        _append_log(log_path,{"event":"REQUEST_INTENT","query_id":query_id,"attempt":attempt,"at_utc":started})
        transport=opener or urllib.request.build_opener(ManualRejectRedirect())
        with ElapsedReporter(query_id,completed.copy(),reporter_interval):
            observation=stream_bounded_response(query_id=query_id,opener=transport,request=_request(query_id),
                timeout_seconds=600,byte_cap=RESPONSE_CAPS[query_id],
                staging_path=root/f"STAGING/{query_id}.attempt-{attempt:04d}.tmp",
                complete_path=root/f"RAW_ACQUIRED/{query_id}.csv",
                partial_path=root/f"PARTIAL/{query_id}.attempt-{attempt:04d}.partial")
        finished=utc(); terminal_class=("MANUAL_ACQUISITION_RESPONSE_COMPLETE" if observation.response_complete else
            ("MANUAL_ACQUISITION_TRANSPORT_TIMEOUT" if observation.exception_class in {"TimeoutError","timeout"} else "MANUAL_ACQUISITION_TRANSPORT_FAILURE"))
        record={"query_id":query_id,"adql_sha256":query_sha256(QUERY_LITERALS[query_id]),"provider":"NOIRLAB_DATA_LAB_QUERY_MANAGER",
            "endpoint":ENDPOINT,"http_method":"GET","public_anonymous":True,"timeout_seconds":600,"retries":0,
            "started_at_utc":started,"finished_at_utc":finished,"terminal_classification":terminal_class,
            "requests_started":observation.request_started,"http_status":observation.http_status,
            "content_type":observation.content_type,"bytes_preserved":observation.body_bytes_preserved,
            "raw_path":str((root/f"RAW_ACQUIRED/{query_id}.csv").relative_to(PROJECT)) if observation.response_complete else None,
            "raw_sha256":observation.artifact_sha256 if observation.response_complete else None,
            "partial_path":str(Path(observation.artifact_path).relative_to(PROJECT)) if observation.partial_body_exists else None,
            "partial_sha256":observation.artifact_sha256 if observation.partial_body_exists else None,
            "response_complete":observation.response_complete,"partial":observation.partial_body_exists,
            "exception_class":observation.exception_class,"diagnostic_message":observation.diagnostic_message,
            "scientific_acceptance":False,"provenance":"DIRECT_PUBLIC_ANONYMOUS_RESPONSE"}
        terminal=sealed({"schema_version":"OC3_MANUAL_SOURCE_METADATA_QUERY_TERMINAL_001",**record})
        write_canonical(evidence/f"attempt-{attempt:04d}-TERMINAL.json",terminal,exclusive=True)
        _append_log(log_path,{"event":"QUERY_TERMINAL","query_id":query_id,"attempt":attempt,"at_utc":finished,"terminal_classification":terminal_class})
        if not observation.response_complete:
            _save_manifest(manifest_path,manifest)
            print(json.dumps({"state":terminal_class,"query_id":query_id,"evidence":str(evidence),"completed_queries":completed},sort_keys=True),flush=True)
            return 20 if terminal_class.endswith("TIMEOUT") else 21
        manifest["queries"][query_id]=record; _save_manifest(manifest_path,manifest); completed.append(query_id)
    if (root/"EXECUTION_SUMMARY.json").exists():
        prior=json.loads((root/"EXECUTION_SUMMARY.json").read_text())
        if prior.get("state") != "MANUAL_SOURCE_METADATA_ACQUISITION_COMPLETE_RAW_UNAUDITED":
            raise ValueError("EXECUTION_SUMMARY_ALREADY_EXISTS")
        print(json.dumps({"state":prior["state"],"completed_queries":completed,"scientific_acceptance":False},sort_keys=True),flush=True)
        return 0
    summary=sealed({"schema_version":"OC3_MANUAL_SOURCE_METADATA_EXECUTION_SUMMARY_001","stage_id":STAGE_ID,
        "state":"MANUAL_SOURCE_METADATA_ACQUISITION_COMPLETE_RAW_UNAUDITED","completed_queries":completed,
        "scientific_acceptance":False,"network_requests_started":sum(r["requests_started"] for r in manifest["queries"].values()),
        "body_bytes_preserved":sum(r["bytes_preserved"] for r in manifest["queries"].values()),"finished_at_utc":utc()})
    summary_path=root/"EXECUTION_SUMMARY.json"
    write_canonical(summary_path,summary,exclusive=True)
    print(json.dumps({"state":summary["state"],"completed_queries":completed,"scientific_acceptance":False},sort_keys=True),flush=True)
    return 0
