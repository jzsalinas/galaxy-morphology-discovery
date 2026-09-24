#!/usr/bin/env python3
"""Bounded exact GitHub Git-object metadata probe.

The .sh suffix keeps this action-specific implementation outside the frozen
Python implementation aggregate while its exact bytes remain bound by the
action-validation receipt and candidate.  Invoke it with the OC3 venv Python.
"""
from __future__ import annotations

import argparse
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

COMMIT = "dd30297f9d50fcb7bbba57d79d4b8fc86cb35701"
COMMIT_URL = f"https://api.github.com/repos/desihub/desitarget/git/commits/{COMMIT}"
TREE_PREFIX = "https://api.github.com/repos/desihub/desitarget/git/trees/"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Accept-Encoding": "identity",
    "Connection": "close",
    "User-Agent": "galaxy-morphology-discovery-oc3",
    "X-GitHub-Api-Version": "2022-11-28",
}
ACCEPTED_CONTENT_TYPES = ("application/json", "application/vnd.github+json")
FIREWALL = {
    "astronomical_data_GETs": 0,
    "real_PHOTSYS_bytes_observed": 0,
    "BRICKNAME_values_observed": 0,
    "BRICKID_values_observed": 0,
    "ROOT_values_observed": 0,
}


class ProbeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _headers(response: http.client.HTTPResponse) -> list[list[str]]:
    return [[str(k), str(v)] for k, v in response.getheaders()]


def _values(headers: list[list[str]], name: str) -> list[str]:
    target = name.lower()
    return [value for key, value in headers if key.lower() == target]


def validate_body(kind: str, body: bytes, expected_sha: str) -> dict[str, object]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError("GIT_OBJECT_JSON_INVALID") from exc
    if not isinstance(value, dict) or value.get("sha") != expected_sha:
        raise ProbeError("GIT_OBJECT_SHA_MISMATCH")
    if kind == "COMMIT_OBJECT":
        tree = value.get("tree")
        tree_sha = tree.get("sha") if isinstance(tree, dict) else None
        if not isinstance(tree_sha, str) or re.fullmatch(r"[0-9a-f]{40}", tree_sha) is None:
            raise ProbeError("GIT_COMMIT_TREE_SHA_INVALID")
        return {"commit_sha": expected_sha, "root_tree_sha": tree_sha}
    if kind == "RECURSIVE_TREE":
        if value.get("truncated") is not False or not isinstance(value.get("tree"), list) or not value["tree"]:
            raise ProbeError("GIT_RECURSIVE_TREE_INCOMPLETE")
        for item in value["tree"]:
            if (not isinstance(item, dict) or not isinstance(item.get("path"), str) or
                    item.get("type") not in ("blob", "tree", "commit") or
                    not isinstance(item.get("sha"), str) or
                    re.fullmatch(r"[0-9a-f]{40}", item["sha"]) is None):
                raise ProbeError("GIT_RECURSIVE_TREE_ENTRY_INVALID")
        return {"entry_count": len(value["tree"]), "root_tree_sha": expected_sha, "truncated": False}
    raise ProbeError("GIT_OBJECT_KIND_INVALID")


def exact_command(candidate: dict[str, object], candidate_path: Path) -> list[str]:
    paths = candidate["execution_paths"]
    return [
        str(PROJECT / "oc3/.venv/bin/python"), str(Path(__file__).resolve()),
        "--execute-network", "--candidate", str(Path(candidate_path).resolve()),
        "--standing-authorization", str(PROJECT / paths["standing_authorization"]),
        "--autonomous-permit", str(PROJECT / paths["permit"]),
        "--autonomy-state", str(PROJECT / paths["state"]),
        "--output-directory", str(PROJECT / paths["output_directory"]),
    ]


def validate_candidate(path: Path) -> tuple[dict[str, object], dict[str, object]]:
    try:
        candidate = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise ProbeError("GIT_OBJECT_CANDIDATE_INVALID") from exc
    required = {
        "accepted_content_types", "action_implementation", "autonomy_policy", "candidate_state",
        "command_argv", "command_argv_sha256", "execution_paths", "expected",
        "implementation_aggregate", "network_caps", "request", "schema_version", "scope",
        "sealed", "specification", "stage_id", "terminal_mapping",
    }
    if (set(candidate) != required or
            candidate.get("schema_version") != "OC3_EXACT_GITHUB_GIT_OBJECT_PROBE_CANDIDATE_001" or
            candidate.get("candidate_state") != "PENDING_STANDING_AUTONOMY" or
            candidate.get("implementation_aggregate") != implementation_hash(PROJECT) or
            candidate.get("accepted_content_types") != list(ACCEPTED_CONTENT_TYPES)):
        raise ProbeError("GIT_OBJECT_CANDIDATE_INVALID")
    implementation = candidate.get("action_implementation", {})
    if (implementation != {"path": str(Path(__file__).resolve().relative_to(PROJECT)),
                            "sha256": file_sha256(Path(__file__))}):
        raise ProbeError("GIT_OBJECT_IMPLEMENTATION_MISMATCH")
    spec = candidate.get("specification", {})
    spec_path = PROJECT / str(spec.get("path", ""))
    if not spec_path.is_file() or spec.get("sha256") != file_sha256(spec_path):
        raise ProbeError("GIT_OBJECT_SPECIFICATION_MISMATCH")
    caps = candidate.get("network_caps", {})
    if (set(caps) != {"accepted_body_bytes", "concurrency", "read_reservation_bytes", "redirects", "requests", "retries"} or
            caps.get("requests") != 1 or caps.get("redirects") != 0 or caps.get("retries") != 0 or
            caps.get("concurrency") != 1 or type(caps.get("accepted_body_bytes")) is not int or
            type(caps.get("read_reservation_bytes")) is not int or
            caps["accepted_body_bytes"] <= 0 or caps["read_reservation_bytes"] != caps["accepted_body_bytes"] + 1):
        raise ProbeError("GIT_OBJECT_CAPS_INVALID")
    request = candidate.get("request", {})
    expected = candidate.get("expected", {})
    kind = expected.get("object_kind")
    object_sha = expected.get("object_sha")
    if (request.get("method") != "GET" or request.get("headers") != HEADERS or
            request.get("literal_url") not in (COMMIT_URL, f"{TREE_PREFIX}{object_sha}?recursive=1") or
            not isinstance(object_sha, str) or re.fullmatch(r"[0-9a-f]{40}", object_sha) is None or
            expected.get("resolved_commit") != COMMIT or kind not in ("COMMIT_OBJECT", "RECURSIVE_TREE")):
        raise ProbeError("GIT_OBJECT_REQUEST_INVALID")
    if (kind == "COMMIT_OBJECT" and (object_sha != COMMIT or request["literal_url"] != COMMIT_URL)):
        raise ProbeError("GIT_COMMIT_OBJECT_IDENTITY_INVALID")
    paths = candidate.get("execution_paths", {})
    if set(paths) != {"output_directory", "permit", "standing_authorization", "state"}:
        raise ProbeError("GIT_OBJECT_EXECUTION_PATHS_INVALID")
    command = exact_command(candidate, path)
    if candidate.get("command_argv") != command or candidate.get("command_argv_sha256") != sha256_bytes(canonical(command)):
        raise ProbeError("GIT_OBJECT_COMMAND_INVALID")
    try:
        _, contract = validate_autonomous_action_candidate(path)
    except Exception as exc:
        raise ProbeError("GIT_OBJECT_AUTONOMY_CONTRACT_INVALID") from exc
    if (contract["network_request_reservation"] != 1 or
            contract["application_body_reservation"] != caps["read_reservation_bytes"] or
            contract["retry_reservation"] != 0 or contract["concurrency"] != 1 or
            contract["scientific_firewall"] != FIREWALL):
        raise ProbeError("GIT_OBJECT_AUTONOMY_RESERVATION_INVALID")
    return candidate, contract


def _terminal(candidate: dict[str, object], *, state: str, reason: str,
              counters: dict[str, int], response: dict[str, object] | None,
              observed: dict[str, object] | None) -> dict[str, object]:
    return sealed({
        "application_body_bytes_read": counters["application_body_bytes_read"],
        "counters": counters,
        "observed": observed,
        "reason": reason,
        "response": response,
        "scope": candidate["scope"],
        "stage_id": candidate["stage_id"],
        "state": state,
    })


def execute(candidate_path: Path, standing_authorization: Path, permit: Path,
            state_path: Path, output_directory: Path) -> dict[str, object]:
    candidate, _ = validate_candidate(candidate_path)
    consumption = LEDGER_ROOT / "PERMIT_CONSUMPTION"
    validate_permit(permit, candidate_path=candidate_path, state_path=state_path,
                    standing_authorization_path=standing_authorization,
                    consumption_directory=consumption)
    output = Path(output_directory).resolve()
    if output != (PROJECT / candidate["execution_paths"]["output_directory"]).resolve() or output.exists():
        raise ProbeError("GIT_OBJECT_OUTPUT_CONFLICT")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    consume_permit(permit, candidate_path=candidate_path, state_path=state_path,
                   standing_authorization_path=standing_authorization,
                   consumption_directory=consumption, consumed_at_utc=now)
    output.mkdir(parents=True)
    counters = dict(FIREWALL)
    counters.update({"application_body_bytes_read": 0, "network_requests_started": 0, "retry_requests": 0})
    response_meta = None
    observed = None
    success = candidate["terminal_mapping"]["success"]
    failure = candidate["terminal_mapping"]["failure"]
    inconclusive = candidate["terminal_mapping"]["inconclusive"]
    state = failure
    reason = "GIT_OBJECT_TRANSPORT_ERROR"
    connection = None
    try:
        parsed = urlsplit(candidate["request"]["literal_url"])
        if parsed.scheme != "https" or parsed.hostname != "api.github.com" or parsed.port is not None:
            raise ProbeError("GIT_OBJECT_URL_INVALID")
        connection = http.client.HTTPSConnection(parsed.hostname, timeout=30)
        counters["network_requests_started"] = 1
        target = parsed.path + ("?" + parsed.query if parsed.query else "")
        connection.request("GET", target, headers=HEADERS)
        response = connection.getresponse()
        raw_headers = _headers(response)
        response_meta = {"final_url": candidate["request"]["literal_url"],
                         "raw_headers": raw_headers, "status": response.status}
        if 300 <= response.status < 400:
            raise ProbeError("GIT_OBJECT_REDIRECT_FORBIDDEN")
        if response.status != 200:
            state, reason = inconclusive, "GIT_OBJECT_HTTP_STATUS_UNEXPECTED"
        else:
            content_types = _values(raw_headers, "Content-Type")
            encodings = _values(raw_headers, "Content-Encoding")
            lengths = _values(raw_headers, "Content-Length")
            media = content_types[0].split(";", 1)[0].strip().lower() if len(content_types) == 1 else ""
            if media not in ACCEPTED_CONTENT_TYPES:
                raise ProbeError("GIT_OBJECT_CONTENT_TYPE_INVALID")
            if len(encodings) > 1 or (encodings and encodings[0].strip().lower() != "identity"):
                raise ProbeError("GIT_OBJECT_CONTENT_ENCODING_INVALID")
            accepted = candidate["network_caps"]["accepted_body_bytes"]
            if len(lengths) > 1 or (lengths and (not lengths[0].isdigit() or int(lengths[0]) > accepted)):
                state, reason = inconclusive, "GIT_OBJECT_DECLARED_BODY_CAP_EXCEEDED"
            else:
                body = response.read(candidate["network_caps"]["read_reservation_bytes"])
                counters["application_body_bytes_read"] = len(body)
                if len(body) > accepted:
                    state, reason = inconclusive, "GIT_OBJECT_BODY_CAP_EXCEEDED"
                else:
                    observed = validate_body(candidate["expected"]["object_kind"], body,
                                             candidate["expected"]["object_sha"])
                    write_json_immutable(output / "BODY_IDENTITY.json", sealed({
                        "body_bytes": len(body), "body_sha256": hashlib.sha256(body).hexdigest(),
                        "literal_url": candidate["request"]["literal_url"],
                        "object_kind": candidate["expected"]["object_kind"],
                    }))
                    with (output / "RAW_IMMUTABLE_RESPONSE.body").open("xb") as stream:
                        stream.write(body); stream.flush(); os.fsync(stream.fileno())
                    state, reason = success, "EXACT_GIT_OBJECT_METADATA_VALIDATED"
    except ProbeError as exc:
        state, reason = failure, exc.code
    except Exception:
        state, reason = failure, "GIT_OBJECT_TRANSPORT_ERROR"
    finally:
        if connection is not None:
            connection.close()
    terminal = _terminal(candidate, state=state, reason=reason, counters=counters,
                         response=response_meta, observed=observed)
    write_json_immutable(output / "TERMINAL.json", terminal)
    write_json_immutable(output / "RESPONSE_RECEIPT.json", sealed({
        "application_body_bytes_read": counters["application_body_bytes_read"],
        "response": response_meta, "stage_id": candidate["stage_id"],
    }))
    transition_completed_action(
        state_path=state_path, candidate_path=candidate_path, permit_path=permit,
        standing_authorization_path=standing_authorization, consumption_directory=consumption,
        terminal_path=output / "TERMINAL.json", terminal_sha256=file_sha256(output / "TERMINAL.json"),
        request_delta=counters["network_requests_started"],
        body_delta=counters["application_body_bytes_read"], retry_delta=0,
        ledger_directory=LEDGER_ROOT, transitioned_at_utc=now,
        reason="AUTONOMOUS_EXACT_GIT_OBJECT_PROBE_COMPLETED")
    return terminal


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Bounded exact GitHub Git-object metadata probe")
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
                raise ProbeError("GIT_OBJECT_OFFLINE_ARGUMENT_INVALID")
            result = {"application_body_bytes_read": 0, "network_requests": 0,
                      "scope": candidate["scope"], "stage_id": candidate["stage_id"],
                      "state": "GIT_OBJECT_CANDIDATE_VALIDATED" if args.validate_candidate else
                               "READY_AT_EXACT_GIT_OBJECT_BOUNDARY"}
        else:
            if None in (args.standing_authorization, args.autonomous_permit,
                        args.autonomy_state, args.output_directory):
                raise ProbeError("GIT_OBJECT_EXECUTION_ARGUMENT_REQUIRED")
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
