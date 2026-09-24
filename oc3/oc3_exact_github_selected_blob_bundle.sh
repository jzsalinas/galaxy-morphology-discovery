#!/usr/bin/env python3
"""Acquire and search a frozen selected bundle of exact Git blobs."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "oc3"))

from oc3lib.autonomy_governor import (  # noqa: E402
    LEDGER_ROOT, consume_permit, transition_completed_action,
    validate_autonomous_action_candidate, validate_permit,
)
from oc3lib.core import canonical, implementation_hash  # noqa: E402
from oc3lib.galaxy_eligibility_photsys_authority_probe import (  # noqa: E402
    file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)
from oc3lib.photsys_zero_byte_provenance import (  # noqa: E402
    SEARCH_TERMS, search_source_tree,
)

COMMIT = "dd30297f9d50fcb7bbba57d79d4b8fc86cb35701"
TARGET_PATHS = ("py/desitarget/targets.py", "bin/split_randoms", "bin/alt_split_randoms")
BLOB_PREFIX = "https://api.github.com/repos/desihub/desitarget/git/blobs/"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Accept-Encoding": "identity",
    "Connection": "close",
    "User-Agent": "galaxy-morphology-discovery-oc3",
    "X-GitHub-Api-Version": "2022-11-28",
}
ACCEPTED_CONTENT_TYPES = ("application/json", "application/vnd.github+json")
FIREWALL = {
    "astronomical_data_GETs": 0, "real_PHOTSYS_bytes_observed": 0,
    "BRICKNAME_values_observed": 0, "BRICKID_values_observed": 0,
    "ROOT_values_observed": 0,
}


class ProbeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def validate_blob_body(body: bytes, expected_sha: str, expected_size: int) -> bytes:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError("GIT_BLOB_JSON_INVALID") from exc
    if (not isinstance(value, dict) or value.get("sha") != expected_sha or
            value.get("encoding") != "base64" or value.get("size") != expected_size or
            not isinstance(value.get("content"), str)):
        raise ProbeError("GIT_BLOB_CONTRACT_INVALID")
    try:
        decoded = base64.b64decode(value["content"], validate=False)
    except Exception as exc:
        raise ProbeError("GIT_BLOB_BASE64_INVALID") from exc
    if len(decoded) != expected_size:
        raise ProbeError("GIT_BLOB_SIZE_MISMATCH")
    identity = hashlib.sha1(f"blob {len(decoded)}\0".encode() + decoded).hexdigest()
    if identity != expected_sha:
        raise ProbeError("GIT_BLOB_SHA_MISMATCH")
    return decoded


def exact_command(candidate: dict[str, object], candidate_path: Path) -> list[str]:
    paths = candidate["execution_paths"]
    return [str(PROJECT / "oc3/.venv/bin/python"), str(Path(__file__).resolve()),
            "--execute-network", "--candidate", str(Path(candidate_path).resolve()),
            "--standing-authorization", str(PROJECT / paths["standing_authorization"]),
            "--autonomous-permit", str(PROJECT / paths["permit"]),
            "--autonomy-state", str(PROJECT / paths["state"]),
            "--output-directory", str(PROJECT / paths["output_directory"])]


def _tree_entries(path: Path) -> dict[str, dict[str, object]]:
    try:
        value = json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise ProbeError("GIT_TREE_INVENTORY_INVALID") from exc
    if (value.get("sha") != "514756ea86baa049a05394dbc01fdde008a87288" or
            value.get("truncated") is not False or not isinstance(value.get("tree"), list)):
        raise ProbeError("GIT_TREE_INVENTORY_INVALID")
    return {item["path"]: item for item in value["tree"] if isinstance(item, dict) and isinstance(item.get("path"), str)}


def validate_candidate(path: Path) -> tuple[dict[str, object], dict[str, object]]:
    try:
        candidate = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise ProbeError("GIT_BLOB_BUNDLE_CANDIDATE_INVALID") from exc
    required = {"accepted_content_types", "action_implementation", "autonomy_policy", "candidate_state",
                "command_argv", "command_argv_sha256", "execution_paths", "implementation_aggregate",
                "network_caps", "resources", "schema_version", "scope", "sealed", "search_terms",
                "specification", "stage_id", "terminal_mapping", "tree_inventory"}
    if (set(candidate) != required or
            candidate.get("schema_version") != "OC3_EXACT_GITHUB_BLOB_BUNDLE_CANDIDATE_001" or
            candidate.get("candidate_state") != "PENDING_STANDING_AUTONOMY" or
            candidate.get("implementation_aggregate") != implementation_hash(PROJECT) or
            candidate.get("accepted_content_types") != list(ACCEPTED_CONTENT_TYPES) or
            candidate.get("search_terms") != list(SEARCH_TERMS)):
        raise ProbeError("GIT_BLOB_BUNDLE_CANDIDATE_INVALID")
    implementation = {"path": str(Path(__file__).resolve().relative_to(PROJECT)),
                      "sha256": file_sha256(Path(__file__))}
    if candidate.get("action_implementation") != implementation:
        raise ProbeError("GIT_BLOB_BUNDLE_IMPLEMENTATION_MISMATCH")
    spec = candidate.get("specification", {}); spec_path = PROJECT / str(spec.get("path", ""))
    if not spec_path.is_file() or spec.get("sha256") != file_sha256(spec_path):
        raise ProbeError("GIT_BLOB_BUNDLE_SPECIFICATION_MISMATCH")
    tree_binding = candidate.get("tree_inventory", {}); tree_path = PROJECT / str(tree_binding.get("path", ""))
    if not tree_path.is_file() or tree_binding.get("sha256") != file_sha256(tree_path):
        raise ProbeError("GIT_TREE_INVENTORY_MISMATCH")
    tree = _tree_entries(tree_path)
    resources = candidate.get("resources")
    if (not isinstance(resources, list) or len(resources) != len(TARGET_PATHS) or
            [item.get("path") for item in resources] != list(TARGET_PATHS)):
        raise ProbeError("GIT_BLOB_BUNDLE_RESOURCE_SET_INVALID")
    total = 0
    for item in resources:
        if (set(item) != {"accepted_body_bytes", "blob_sha", "decoded_size", "literal_url", "path", "read_reservation_bytes"} or
                item["literal_url"] != BLOB_PREFIX + item["blob_sha"] or
                type(item["decoded_size"]) is not int or item["decoded_size"] < 0 or
                type(item["accepted_body_bytes"]) is not int or item["accepted_body_bytes"] <= 0 or
                item["read_reservation_bytes"] != item["accepted_body_bytes"] + 1):
            raise ProbeError("GIT_BLOB_BUNDLE_RESOURCE_INVALID")
        observed = tree.get(item["path"], {})
        if (observed.get("type") != "blob" or observed.get("sha") != item["blob_sha"] or
                observed.get("size") != item["decoded_size"]):
            raise ProbeError("GIT_BLOB_TREE_BINDING_MISMATCH")
        total += item["read_reservation_bytes"]
    caps = candidate.get("network_caps", {})
    if caps != {"application_body_reservation": total, "concurrency": 1,
                "redirects": 0, "requests": len(resources), "retries": 0}:
        raise ProbeError("GIT_BLOB_BUNDLE_CAPS_INVALID")
    paths = candidate.get("execution_paths", {})
    if set(paths) != {"output_directory", "permit", "standing_authorization", "state"}:
        raise ProbeError("GIT_BLOB_BUNDLE_PATHS_INVALID")
    command = exact_command(candidate, path)
    if candidate.get("command_argv") != command or candidate.get("command_argv_sha256") != sha256_bytes(canonical(command)):
        raise ProbeError("GIT_BLOB_BUNDLE_COMMAND_INVALID")
    try:
        _, contract = validate_autonomous_action_candidate(path)
    except Exception as exc:
        raise ProbeError("GIT_BLOB_BUNDLE_AUTONOMY_CONTRACT_INVALID") from exc
    if (contract["network_request_reservation"] != len(resources) or
            contract["application_body_reservation"] != total or contract["retry_reservation"] != 0 or
            contract["concurrency"] != 1 or contract["scientific_firewall"] != FIREWALL):
        raise ProbeError("GIT_BLOB_BUNDLE_AUTONOMY_RESERVATION_INVALID")
    return candidate, contract


def _header_values(headers: list[list[str]], name: str) -> list[str]:
    return [value for key, value in headers if key.lower() == name.lower()]


def execute(candidate_path: Path, standing_authorization: Path, permit: Path,
            state_path: Path, output_directory: Path) -> dict[str, object]:
    candidate, _ = validate_candidate(candidate_path)
    consumption = LEDGER_ROOT / "PERMIT_CONSUMPTION"
    validate_permit(permit, candidate_path=candidate_path, state_path=state_path,
                    standing_authorization_path=standing_authorization,
                    consumption_directory=consumption)
    output = Path(output_directory).resolve()
    if output != (PROJECT / candidate["execution_paths"]["output_directory"]).resolve() or output.exists():
        raise ProbeError("GIT_BLOB_BUNDLE_OUTPUT_CONFLICT")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    consume_permit(permit, candidate_path=candidate_path, state_path=state_path,
                   standing_authorization_path=standing_authorization,
                   consumption_directory=consumption, consumed_at_utc=now)
    output.mkdir(parents=True)
    source_root = output / "SOURCE_TREE"
    raw_root = output / "RAW_IMMUTABLE_RESPONSES"
    raw_root.mkdir(); source_root.mkdir()
    counters = dict(FIREWALL)
    counters.update({"application_body_bytes_read": 0, "network_requests_started": 0, "retry_requests": 0})
    receipts = []
    state = candidate["terminal_mapping"]["failure"]
    reason = "GIT_BLOB_BUNDLE_TRANSPORT_ERROR"
    try:
        for index, resource in enumerate(candidate["resources"], 1):
            parsed = urlsplit(resource["literal_url"])
            if parsed.scheme != "https" or parsed.hostname != "api.github.com" or parsed.port is not None or parsed.query:
                raise ProbeError("GIT_BLOB_URL_INVALID")
            connection = http.client.HTTPSConnection(parsed.hostname, timeout=30)
            counters["network_requests_started"] += 1
            try:
                connection.request("GET", parsed.path, headers=HEADERS)
                response = connection.getresponse()
                headers = [[str(k), str(v)] for k, v in response.getheaders()]
                if 300 <= response.status < 400:
                    raise ProbeError("GIT_BLOB_REDIRECT_FORBIDDEN")
                if response.status != 200:
                    raise ProbeError("GIT_BLOB_HTTP_STATUS_UNEXPECTED")
                types = _header_values(headers, "Content-Type")
                media = types[0].split(";", 1)[0].strip().lower() if len(types) == 1 else ""
                encodings = _header_values(headers, "Content-Encoding")
                lengths = _header_values(headers, "Content-Length")
                if media not in ACCEPTED_CONTENT_TYPES:
                    raise ProbeError("GIT_BLOB_CONTENT_TYPE_INVALID")
                if len(encodings) > 1 or (encodings and encodings[0].strip().lower() != "identity"):
                    raise ProbeError("GIT_BLOB_CONTENT_ENCODING_INVALID")
                if len(lengths) > 1 or (lengths and (not lengths[0].isdigit() or int(lengths[0]) > resource["accepted_body_bytes"])):
                    raise ProbeError("GIT_BLOB_DECLARED_BODY_CAP_EXCEEDED")
                body = response.read(resource["read_reservation_bytes"])
                counters["application_body_bytes_read"] += len(body)
                if len(body) > resource["accepted_body_bytes"]:
                    raise ProbeError("GIT_BLOB_BODY_CAP_EXCEEDED")
                decoded = validate_blob_body(body, resource["blob_sha"], resource["decoded_size"])
                raw_path = raw_root / f"{index:02d}.json"
                with raw_path.open("xb") as stream:
                    stream.write(body); stream.flush(); os.fsync(stream.fileno())
                source_path = source_root / resource["path"]
                source_path.parent.mkdir(parents=True, exist_ok=True)
                with source_path.open("xb") as stream:
                    stream.write(decoded); stream.flush(); os.fsync(stream.fileno())
                receipts.append({"blob_sha": resource["blob_sha"], "body_bytes": len(body),
                                 "body_sha256": hashlib.sha256(body).hexdigest(),
                                 "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
                                 "decoded_size": len(decoded), "path": resource["path"], "status": response.status})
            finally:
                connection.close()
        search = search_source_tree(source_root)
        write_json_immutable(output / "SEARCH_RESULTS.json", sealed(search))
        write_json_immutable(output / "RESOURCE_RECEIPTS.json", sealed({"resources": receipts}))
        state = candidate["terminal_mapping"]["success"]
        reason = "EXACT_SELECTED_SOURCE_BLOBS_VALIDATED"
        observed = {"named_product_generator_status": search["named_product_generator_status"],
                    "selected_paths": list(TARGET_PATHS),
                    "term_hit_counts": {term: len(search["results"][term]) for term in SEARCH_TERMS}}
    except ProbeError as exc:
        reason = exc.code
        observed = None
    except Exception:
        reason = "GIT_BLOB_BUNDLE_TRANSPORT_ERROR"
        observed = None
    terminal = sealed({"application_body_bytes_read": counters["application_body_bytes_read"],
                       "counters": counters, "observed": observed, "reason": reason,
                       "resource_receipts_count": len(receipts), "scope": candidate["scope"],
                       "stage_id": candidate["stage_id"], "state": state})
    write_json_immutable(output / "TERMINAL.json", terminal)
    transition_completed_action(state_path=state_path, candidate_path=candidate_path, permit_path=permit,
        standing_authorization_path=standing_authorization, consumption_directory=consumption,
        terminal_path=output / "TERMINAL.json", terminal_sha256=file_sha256(output / "TERMINAL.json"),
        request_delta=counters["network_requests_started"], body_delta=counters["application_body_bytes_read"],
        retry_delta=0, ledger_directory=LEDGER_ROOT, transitioned_at_utc=now,
        reason="AUTONOMOUS_EXACT_SELECTED_GIT_BLOB_BUNDLE_COMPLETED")
    return terminal


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Bounded exact GitHub blob bundle")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-candidate", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute-network", action="store_true")
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--standing-authorization", type=Path)
    p.add_argument("--autonomous-permit", type=Path)
    p.add_argument("--autonomy-state", type=Path)
    p.add_argument("--output-directory", type=Path)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        candidate, _ = validate_candidate(args.candidate)
        if args.validate_candidate or args.dry_run:
            if any(x is not None for x in (args.standing_authorization, args.autonomous_permit,
                                           args.autonomy_state, args.output_directory)):
                raise ProbeError("GIT_BLOB_BUNDLE_OFFLINE_ARGUMENT_INVALID")
            result = {"application_body_bytes_read": 0, "network_requests": 0,
                      "resource_count": len(candidate["resources"]), "scope": candidate["scope"],
                      "stage_id": candidate["stage_id"],
                      "state": "GIT_BLOB_BUNDLE_CANDIDATE_VALIDATED" if args.validate_candidate else
                               "READY_AT_EXACT_GIT_BLOB_BUNDLE_BOUNDARY"}
        else:
            if None in (args.standing_authorization, args.autonomous_permit,
                        args.autonomy_state, args.output_directory):
                raise ProbeError("GIT_BLOB_BUNDLE_EXECUTION_ARGUMENT_REQUIRED")
            result = execute(args.candidate, args.standing_authorization, args.autonomous_permit,
                             args.autonomy_state, args.output_directory)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except ProbeError as exc:
        print(json.dumps({"error": exc.code, "state": exc.code},
                         sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
