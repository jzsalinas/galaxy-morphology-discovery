#!/usr/bin/env python3
"""Retrieve one frozen public documentary resource under an autonomy permit."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import http.client
import json
import os
from pathlib import Path
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

LITERAL_URL = "https://ui.adsabs.harvard.edu/abs/2023AJ....165...50M/abstract"
ACCEPTED_CONTENT_TYPES = ("text/html", "application/xhtml+xml")
HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Encoding": "identity",
    "Connection": "close",
    "User-Agent": "galaxy-morphology-discovery-oc3",
}
FIREWALL = {
    "astronomical_data_GETs": 0, "real_PHOTSYS_bytes_observed": 0,
    "BRICKNAME_values_observed": 0, "BRICKID_values_observed": 0,
    "ROOT_values_observed": 0,
}
TERMS = (
    "survey-bricks-dr9-randoms-0.48.0.fits", "survey-bricks", "photsys",
    "outside of the footprint", "outside-the-footprint", "desitarget",
    "supplement_randoms", "supplemental", "aggregation", "generated",
)


class ProbeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class PageInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.meta: dict[str, list[str]] = {}
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k.lower(): v for k, v in attrs if v is not None}
        if tag.lower() == "a" and "href" in values:
            self.links.append(values["href"])
        if tag.lower() == "meta" and "content" in values:
            key = values.get("name") or values.get("property")
            if key:
                self.meta.setdefault(key.lower(), []).append(values["content"])

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text.append(data)


def analyze_html(body: bytes) -> dict[str, object]:
    try:
        decoded = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProbeError("DOCUMENT_UTF8_INVALID") from exc
    parser = PageInventory()
    try:
        parser.feed(decoded)
    except Exception as exc:
        raise ProbeError("DOCUMENT_HTML_INVALID") from exc
    haystack = decoded.lower()
    discovered = sorted({
        link for link in parser.links
        if link.startswith(("https://doi.org/", "https://arxiv.org/", "https://iopscience.iop.org/"))
    })
    titles = parser.meta.get("citation_title", []) + parser.meta.get("dc.title", [])
    dois = parser.meta.get("citation_doi", []) + parser.meta.get("dc.identifier", [])
    return {
        "discovered_candidate_links": discovered,
        "document_title_values": titles[:4],
        "doi_values": dois[:4],
        "term_counts": {term: haystack.count(term.lower()) for term in TERMS},
    }


def exact_command(candidate: dict[str, object], candidate_path: Path) -> list[str]:
    paths = candidate["execution_paths"]
    return [str(PROJECT / "oc3/.venv/bin/python"), str(Path(__file__).resolve()),
            "--execute-network", "--candidate", str(Path(candidate_path).resolve()),
            "--standing-authorization", str(PROJECT / paths["standing_authorization"]),
            "--autonomous-permit", str(PROJECT / paths["permit"]),
            "--autonomy-state", str(PROJECT / paths["state"]),
            "--output-directory", str(PROJECT / paths["output_directory"])]


def validate_candidate(path: Path) -> tuple[dict[str, object], dict[str, object]]:
    try:
        candidate = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise ProbeError("PUBLIC_DOCUMENT_CANDIDATE_INVALID") from exc
    required = {"accepted_content_types", "action_implementation", "autonomy_policy",
                "candidate_state", "command_argv", "command_argv_sha256", "execution_paths",
                "implementation_aggregate", "network_caps", "resource", "schema_version",
                "scope", "sealed", "specification", "stage_id", "terminal_mapping"}
    if (set(candidate) != required or
            candidate.get("schema_version") != "OC3_EXACT_PUBLIC_DOCUMENT_CANDIDATE_001" or
            candidate.get("candidate_state") != "PENDING_STANDING_AUTONOMY" or
            candidate.get("implementation_aggregate") != implementation_hash(PROJECT) or
            candidate.get("accepted_content_types") != list(ACCEPTED_CONTENT_TYPES)):
        raise ProbeError("PUBLIC_DOCUMENT_CANDIDATE_INVALID")
    implementation = {"path": str(Path(__file__).resolve().relative_to(PROJECT)),
                      "sha256": file_sha256(Path(__file__))}
    if candidate.get("action_implementation") != implementation:
        raise ProbeError("PUBLIC_DOCUMENT_IMPLEMENTATION_MISMATCH")
    spec = candidate.get("specification", {})
    spec_path = PROJECT / str(spec.get("path", ""))
    if not spec_path.is_file() or spec.get("sha256") != file_sha256(spec_path):
        raise ProbeError("PUBLIC_DOCUMENT_SPECIFICATION_MISMATCH")
    resource = candidate.get("resource")
    if (not isinstance(resource, dict) or
            set(resource) != {"accepted_body_bytes", "literal_url", "read_reservation_bytes"} or
            resource.get("literal_url") != LITERAL_URL or
            type(resource.get("accepted_body_bytes")) is not int or
            resource["accepted_body_bytes"] <= 0 or
            resource.get("read_reservation_bytes") != resource["accepted_body_bytes"] + 1):
        raise ProbeError("PUBLIC_DOCUMENT_RESOURCE_INVALID")
    caps = candidate.get("network_caps")
    if caps != {"application_body_reservation": resource["read_reservation_bytes"],
                "concurrency": 1, "redirects": 0, "requests": 1, "retries": 0}:
        raise ProbeError("PUBLIC_DOCUMENT_CAPS_INVALID")
    paths = candidate.get("execution_paths", {})
    if set(paths) != {"output_directory", "permit", "standing_authorization", "state"}:
        raise ProbeError("PUBLIC_DOCUMENT_PATHS_INVALID")
    command = exact_command(candidate, path)
    if (candidate.get("command_argv") != command or
            candidate.get("command_argv_sha256") != sha256_bytes(canonical(command))):
        raise ProbeError("PUBLIC_DOCUMENT_COMMAND_INVALID")
    try:
        _, contract = validate_autonomous_action_candidate(path)
    except Exception as exc:
        raise ProbeError("PUBLIC_DOCUMENT_AUTONOMY_CONTRACT_INVALID") from exc
    if (contract["network_request_reservation"] != 1 or
            contract["application_body_reservation"] != resource["read_reservation_bytes"] or
            contract["retry_reservation"] != 0 or contract["concurrency"] != 1 or
            contract["scientific_firewall"] != FIREWALL):
        raise ProbeError("PUBLIC_DOCUMENT_AUTONOMY_RESERVATION_INVALID")
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
        raise ProbeError("PUBLIC_DOCUMENT_OUTPUT_CONFLICT")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    consume_permit(permit, candidate_path=candidate_path, state_path=state_path,
                   standing_authorization_path=standing_authorization,
                   consumption_directory=consumption, consumed_at_utc=now)
    output.mkdir(parents=True)
    counters = dict(FIREWALL)
    counters.update({"application_body_bytes_read": 0, "network_requests_started": 0,
                     "retry_requests": 0})
    state = candidate["terminal_mapping"]["failure"]
    reason = "PUBLIC_DOCUMENT_TRANSPORT_ERROR"
    evidence = None
    headers: list[list[str]] = []
    status = None
    try:
        parsed = urlsplit(candidate["resource"]["literal_url"])
        if (parsed.scheme != "https" or parsed.hostname != "ui.adsabs.harvard.edu" or
                parsed.port is not None or parsed.query or parsed.fragment):
            raise ProbeError("PUBLIC_DOCUMENT_URL_INVALID")
        connection = http.client.HTTPSConnection(parsed.hostname, timeout=30)
        counters["network_requests_started"] += 1
        try:
            connection.request("GET", parsed.path, headers=HEADERS)
            response = connection.getresponse()
            status = response.status
            headers = [[str(k), str(v)] for k, v in response.getheaders()]
            if 300 <= status < 400:
                raise ProbeError("PUBLIC_DOCUMENT_REDIRECT_FORBIDDEN")
            if status != 200:
                raise ProbeError("PUBLIC_DOCUMENT_HTTP_STATUS_UNEXPECTED")
            types = _header_values(headers, "Content-Type")
            media = types[0].split(";", 1)[0].strip().lower() if len(types) == 1 else ""
            encodings = _header_values(headers, "Content-Encoding")
            lengths = _header_values(headers, "Content-Length")
            if media not in ACCEPTED_CONTENT_TYPES:
                raise ProbeError("PUBLIC_DOCUMENT_CONTENT_TYPE_INVALID")
            if len(encodings) > 1 or (encodings and encodings[0].strip().lower() != "identity"):
                raise ProbeError("PUBLIC_DOCUMENT_CONTENT_ENCODING_INVALID")
            if len(lengths) > 1 or (lengths and (not lengths[0].isdigit() or
                    int(lengths[0]) > candidate["resource"]["accepted_body_bytes"])):
                raise ProbeError("PUBLIC_DOCUMENT_DECLARED_BODY_CAP_EXCEEDED")
            body = response.read(candidate["resource"]["read_reservation_bytes"])
            counters["application_body_bytes_read"] += len(body)
            if len(body) > candidate["resource"]["accepted_body_bytes"]:
                raise ProbeError("PUBLIC_DOCUMENT_BODY_CAP_EXCEEDED")
            raw = output / "RAW_IMMUTABLE_DOCUMENT.body"
            with raw.open("xb") as stream:
                stream.write(body); stream.flush(); os.fsync(stream.fileno())
            evidence = analyze_html(body)
            write_json_immutable(output / "DOCUMENT_ANALYSIS.json", sealed(evidence))
            reason = "EXACT_PUBLIC_DOCUMENT_VALIDATED"
            state = candidate["terminal_mapping"]["success"]
        finally:
            connection.close()
    except ProbeError as exc:
        reason = exc.code
    except Exception:
        reason = "PUBLIC_DOCUMENT_TRANSPORT_ERROR"
    receipt = sealed({"body_bytes": counters["application_body_bytes_read"],
                      "body_sha256": file_sha256(output / "RAW_IMMUTABLE_DOCUMENT.body")
                      if (output / "RAW_IMMUTABLE_DOCUMENT.body").is_file() else None,
                      "headers": headers, "literal_url": LITERAL_URL, "status": status})
    write_json_immutable(output / "RESPONSE_RECEIPT.json", receipt)
    terminal = sealed({"application_body_bytes_read": counters["application_body_bytes_read"],
                       "counters": counters, "evidence": evidence, "reason": reason,
                       "scope": candidate["scope"], "stage_id": candidate["stage_id"],
                       "state": state})
    terminal_path = output / "TERMINAL.json"
    write_json_immutable(terminal_path, terminal)
    transition_completed_action(
        state_path=state_path, standing_authorization_path=standing_authorization,
        permit_path=permit, terminal_path=terminal_path,
        terminal_sha256=file_sha256(terminal_path),
        request_delta=counters["network_requests_started"],
        body_delta=counters["application_body_bytes_read"],
        retry_delta=counters["retry_requests"],
        reason="AUTONOMOUS_EXACT_PUBLIC_DOCUMENT_ACTION_COMPLETED",
        at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    return terminal


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-candidate", action="store_true")
    mode.add_argument("--execute-network", action="store_true")
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--standing-authorization", type=Path)
    p.add_argument("--autonomous-permit", type=Path)
    p.add_argument("--autonomy-state", type=Path)
    p.add_argument("--output-directory", type=Path)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.validate_candidate:
            validate_candidate(args.candidate)
            result = {"network_requests": 0, "state": "PUBLIC_DOCUMENT_CANDIDATE_VALIDATED"}
        else:
            if any(x is None for x in (args.standing_authorization, args.autonomous_permit,
                                       args.autonomy_state, args.output_directory)):
                raise ProbeError("PUBLIC_DOCUMENT_EXECUTION_ARGUMENTS_INVALID")
            result = execute(args.candidate, args.standing_authorization, args.autonomous_permit,
                             args.autonomy_state, args.output_directory)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except ProbeError as exc:
        print(json.dumps({"error": exc.code, "state": "PUBLIC_DOCUMENT_ACTION_REJECTED"},
                         sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
