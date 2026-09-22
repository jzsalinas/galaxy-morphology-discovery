"""Second, distinct documentary-only PHOTSYS URL-binding attempt.

This stage reuses the immutable bodies from attempt 001 and may retrieve only
the official DR9 randoms directory index.  It has no FITS transport method.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import html
import http.client
import json
import os
from pathlib import Path
import re
from typing import Callable, Sequence
from urllib.parse import urljoin, urlsplit

from .core import canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    Budget, Counters, PHOTSYSProbeError, PROJECT, SCOPE, TARGET_FILENAME,
    canonical_json_bytes, documentary_facts, file_sha256, load_canonical_json,
    object_seal, sealed, sha256_bytes, validate_sealed, write_immutable,
    write_json_immutable,
)


ATTEMPT_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-DOCUMENTARY-002"
HISTORICAL_ATTEMPT_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001"
SUCCESS = "PHOTSYS_LITERAL_RESOURCE_URL_BOUND"
INCONCLUSIVE = "PHOTSYS_LITERAL_RESOURCE_URL_INCONCLUSIVE"
FAILED = "PHOTSYS_DOCUMENTARY_ATTEMPT_002_FAILED"
RESOURCE_ROLE = "OFFICIAL_DR9_RANDOMS_DIRECTORY_INDEX"
DIRECTORY_URL = "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/"
BODY_CAP = 256 * 1024
REDIRECT_CAP = 1
REQUEST_CAP = 2

HISTORICAL_ROOT = PROJECT / "oc3/photsys_authority_probe" / HISTORICAL_ATTEMPT_ID
HISTORICAL_BODY_PATHS = (
    HISTORICAL_ROOT / "RAW_IMMUTABLE/document-01.body",
    HISTORICAL_ROOT / "RAW_IMMUTABLE/document-02.body",
)
HISTORICAL_BODY_HASHES = (
    "d0b51d66529cb4c62db7e8ae1df22d6976879f46dcd62b4e6993729b42674c85",
    "cebd41a5c9c0ec10e91c5956e508ab9cb7ca96d9f46bc413db63ff82c4d18e9a",
)
HISTORICAL_TREE_SEAL = "bd0f6f78828e32261514a7c8a17951be759b3a219e1d232983a82532bacc45d8"
HISTORICAL_REQUESTS = 2
HISTORICAL_BODY_BYTES = 257_683
PARSE_EVIDENCE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_DOCUMENTARY_002_HISTORICAL_PARSE_EVIDENCE.json"
CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_DOCUMENTARY_002_CANDIDATE.json"
OUTPUT_ROOT = PROJECT / "oc3/photsys_authority_documentary" / ATTEMPT_ID
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_DOCUMENTARY_002_FINAL_AUTHORIZATION.json"

HISTORICAL_FILES = {
    "CHECKPOINTS/0001.json": "35ac43cb68fa9a60b54134826b2bbbb359dc1a10dbc6f5662819d3250f762fda",
    "CHECKPOINTS/0002.json": "c41b93bf4202f5c2f95fabe6dbdb1c146a03433a8a6bfeaeea5dbff9103c7bf4",
    "CHECKPOINTS/CHECKPOINT_INDEX.json": "d728b89c8703a087255d4f93856a2dcfd587f846a5b71193f4a96f2df8f10be3",
    "OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST.json": "0f8e1bf4987cb594738c1244fdde7d5ded4b32b4a56b7820b052a67baccb8da9",
    "OC3_PHOTSYS_AUTHORITY_PROBE_RUN.log": "c8c4541fd04f7d77d78c5bba1efe932be2f3ecbb71c7f83e954e884cead4e2df",
    "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json": "cb7119962a971cc4c6a9e6f37f728491cfb9dc218e6f39f873cbf1c1a1e35dfc",
    "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json": "f4061bbeb3b622888dac24c6b2abcaf5c86450d07944aa9558ec55070a8d1ff4",
    "OC3_PHOTSYS_AUTHORITY_TRANSPORT_EVIDENCE.json": "d04fee4c7114153a37d864c5d94ec19230fbc26286930145dc54e7b65c031da4",
    "RAW_IMMUTABLE/document-01.body": HISTORICAL_BODY_HASHES[0],
    "RAW_IMMUTABLE/document-02.body": HISTORICAL_BODY_HASHES[1],
}


def historical_tree_rows() -> list[dict[str, object]]:
    return [{"path": str(path.relative_to(HISTORICAL_ROOT)), "size": path.stat().st_size,
             "sha256": file_sha256(path)}
            for path in sorted(HISTORICAL_ROOT.rglob("*")) if path.is_file()]


def validate_historical_attempt() -> dict[str, object]:
    if not HISTORICAL_ROOT.is_dir():
        raise PHOTSYSProbeError("HISTORICAL_ATTEMPT_MISSING")
    observed = {row["path"]: row["sha256"] for row in historical_tree_rows()}
    if observed != HISTORICAL_FILES or object_seal(historical_tree_rows()) != HISTORICAL_TREE_SEAL:
        raise PHOTSYSProbeError("HISTORICAL_ATTEMPT_MUTATED")
    terminal = validate_sealed(load_canonical_json(
        HISTORICAL_ROOT / "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json"))
    accounting = validate_sealed(load_canonical_json(
        HISTORICAL_ROOT / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json"))
    if (terminal.get("state") != "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_INCONCLUSIVE" or
            terminal.get("network_requests_started") != HISTORICAL_REQUESTS or
            terminal.get("table_cell_values_decoded") != 0 or
            accounting.get("body_bytes") != HISTORICAL_BODY_BYTES or
            accounting.get("network_requests_started") != HISTORICAL_REQUESTS or
            accounting.get("full_fits_gets") != 0 or
            any(accounting.get("forbidden_counters", {}).values())):
        raise PHOTSYSProbeError("HISTORICAL_ATTEMPT_INVALID")
    return {"body_bytes": HISTORICAL_BODY_BYTES, "body_sha256": list(HISTORICAL_BODY_HASHES),
            "requests": HISTORICAL_REQUESTS, "terminal_seal": terminal["sealed"],
            "tree_seal": HISTORICAL_TREE_SEAL}


def corrected_historical_parse() -> dict[str, object]:
    historical = validate_historical_attempt()
    documents = [{"source_url": url, "body": path.read_bytes()}
                 for url, path in zip(("https://www.legacysurvey.org/dr9/files/",
                                       "https://www.legacysurvey.org/dr9/catalogs/"),
                                      HISTORICAL_BODY_PATHS)]
    facts = documentary_facts(documents)
    required_true = ("brick_level_row_model_documented", "north_south_overlap_documented",
                     "photsys_exact_values_documented", "product_identity_documented")
    if facts.get("missing_required_terms") or any(facts.get(key) is not True for key in required_true):
        raise PHOTSYSProbeError("CORRECTED_HISTORICAL_PARSE_FAILED")
    return sealed({
        "facts": facts,
        "historical_attempt_id": HISTORICAL_ATTEMPT_ID,
        "historical_body_sha256": list(HISTORICAL_BODY_HASHES),
        "historical_terminal": "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_INCONCLUSIVE",
        "historical_tree_seal": historical["tree_seal"],
        "network_requests": 0,
        "parser_version": "OC3_PHOTSYS_DOCUMENTARY_PARSER_V2",
        "scope": SCOPE,
        "stage_id": ATTEMPT_ID,
        "table_cell_values_decoded": 0,
    })


_HREF = re.compile(r"href\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)


def is_exact_target_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == "https" and parsed.hostname == "portal.nersc.gov" and
            parsed.username is None and parsed.password is None and
            not parsed.query and not parsed.fragment and
            parsed.path.startswith("/cfs/cosmo/data/legacysurvey/dr9/randoms/") and
            parsed.path.rsplit("/", 1)[-1] == TARGET_FILENAME)


def resolve_directory_href(body: bytes) -> tuple[str, str]:
    try:
        text = body.decode("utf-8")
    except UnicodeError as exc:
        raise PHOTSYSProbeError("DIRECTORY_INDEX_BODY_INVALID") from exc
    matches = set()
    for match in _HREF.finditer(text):
        raw_href = html.unescape(match.group(2).strip())
        resolved = urljoin(DIRECTORY_URL, raw_href)
        if is_exact_target_url(resolved):
            matches.add((raw_href, resolved))
    if len(matches) != 1:
        raise PHOTSYSProbeError("LITERAL_TARGET_HREF_NOT_UNIQUE")
    return matches.pop()


def build_candidate(parse_evidence_sha256: str, implementation_aggregate: str,
                    command_argv: Sequence[str]) -> dict[str, object]:
    return sealed({
        "authorization_state": "FINAL_HUMAN_AUTHORIZATION_ABSENT",
        "candidate_scope": "LITERAL_URL_DOCUMENTARY_BINDING_ONLY",
        "command_argv": list(command_argv),
        "command_argv_sha256": sha256_bytes(canonical(list(command_argv))),
        "expected_terminals": [SUCCESS, INCONCLUSIVE, FAILED],
        "final_authorization_path": str(AUTHORIZATION_PATH.relative_to(PROJECT)),
        "historical_attempt": {
            "body_bytes": HISTORICAL_BODY_BYTES,
            "body_sha256": list(HISTORICAL_BODY_HASHES),
            "requests": HISTORICAL_REQUESTS,
            "tree_seal": HISTORICAL_TREE_SEAL,
        },
        "historical_parse_evidence_sha256": parse_evidence_sha256,
        "implementation_aggregate": implementation_aggregate,
        "negative_capabilities": {
            "data_head_requests": 0,
            "data_range_requests": 0,
            "full_fits_gets": 0,
            "table_cell_values_decoded": 0,
            "tractor_sdss_gaia_desi_access": 0,
        },
        "new_documentary_resource": {
            "literal_url": DIRECTORY_URL,
            "max_body_bytes": BODY_CAP,
            "resource_role": RESOURCE_ROLE,
        },
        "policy": {
            "automatic_retries": 0,
            "body_bytes_cap": BODY_CAP,
            "concurrency": 1,
            "logical_new_documentary_resources": 1,
            "primary_requests": 1,
            "redirects_per_request": REDIRECT_CAP,
            "request_cap_including_redirects": REQUEST_CAP,
        },
        "scope": SCOPE,
        "stage_id": ATTEMPT_ID,
        "target_filename": TARGET_FILENAME,
    })


def validate_candidate(path: Path = CANDIDATE_PATH) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    expected_policy = {"automatic_retries": 0, "body_bytes_cap": BODY_CAP,
                       "concurrency": 1, "logical_new_documentary_resources": 1,
                       "primary_requests": 1, "redirects_per_request": REDIRECT_CAP,
                       "request_cap_including_redirects": REQUEST_CAP}
    expected_negative = {"data_head_requests": 0, "data_range_requests": 0,
                         "full_fits_gets": 0, "table_cell_values_decoded": 0,
                         "tractor_sdss_gaia_desi_access": 0}
    resource = value.get("new_documentary_resource")
    if (value.get("stage_id") != ATTEMPT_ID or value.get("scope") != SCOPE or
            value.get("candidate_scope") != "LITERAL_URL_DOCUMENTARY_BINDING_ONLY" or
            value.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION_ABSENT" or
            value.get("target_filename") != TARGET_FILENAME or
            value.get("policy") != expected_policy or value.get("negative_capabilities") != expected_negative or
            not isinstance(resource, dict) or resource != {"literal_url": DIRECTORY_URL,
                                                            "max_body_bytes": BODY_CAP,
                                                            "resource_role": RESOURCE_ROLE} or
            value.get("historical_parse_evidence_sha256") != file_sha256(PARSE_EVIDENCE_PATH) or
            value.get("implementation_aggregate") != implementation_hash(PROJECT)):
        raise PHOTSYSProbeError("DOCUMENTARY_002_CANDIDATE_INVALID")
    return value


def validate_final_authorization(candidate_path: Path, authorization_path: Path,
                                 command_argv_sha256: str) -> tuple[dict[str, object], dict[str, object]]:
    candidate = validate_candidate(candidate_path)
    authorization = load_canonical_json(authorization_path)
    required = {"authorization_id", "authorization_state", "authorized", "candidate_sha256",
                "command_argv_sha256", "scope", "stage_id"}
    if (set(authorization) != required or authorization.get("authorized") is not True or
            authorization.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            authorization.get("candidate_sha256") != file_sha256(candidate_path) or
            authorization.get("command_argv_sha256") != command_argv_sha256 or
            authorization.get("command_argv_sha256") != candidate.get("command_argv_sha256") or
            authorization.get("stage_id") != ATTEMPT_ID or authorization.get("scope") != SCOPE):
        raise PHOTSYSProbeError("DOCUMENTARY_002_FINAL_AUTHORIZATION_INVALID")
    return candidate, authorization


class DirectoryTransport:
    """GET-only transport whose redirect target must remain the exact allowlist URL."""
    def __init__(self, *, redirect_cap: int, timeout_seconds: int = 30):
        if redirect_cap != REDIRECT_CAP:
            raise PHOTSYSProbeError("DOCUMENTARY_002_REDIRECT_CAP_INVALID")
        self.redirect_cap = redirect_cap
        self.timeout_seconds = timeout_seconds

    def get(self, url: str, *, max_body_bytes: int) -> dict[str, object]:
        if url != DIRECTORY_URL:
            raise PHOTSYSProbeError("DOCUMENTARY_002_RESOURCE_NOT_ALLOWLISTED")
        current = url
        for redirect_count in range(self.redirect_cap + 1):
            if current != DIRECTORY_URL:
                raise PHOTSYSProbeError("DOCUMENTARY_002_REDIRECT_OUTSIDE_ALLOWLIST")
            parsed = urlsplit(current)
            connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                      timeout=self.timeout_seconds)
            connection.request("GET", parsed.path, headers={"Accept-Encoding": "identity",
                                                             "User-Agent": "OC3-PHOTSYS-documentary-002/1"})
            response = connection.getresponse()
            headers = {key.lower(): value for key, value in response.getheaders()}
            if response.status in (301, 302, 303, 307, 308):
                location = headers.get("location")
                connection.close()
                if not location or redirect_count >= self.redirect_cap:
                    raise PHOTSYSProbeError("DOCUMENTARY_002_REDIRECT_CAP")
                current = urljoin(current, location)
                continue
            length = headers.get("content-length")
            if response.status != 200 or length is None or not length.isdigit() or int(length) > max_body_bytes:
                connection.close()
                raise PHOTSYSProbeError("DOCUMENTARY_002_RESPONSE_INVALID")
            body = response.read(max_body_bytes + 1)
            connection.close()
            if len(body) > max_body_bytes:
                raise PHOTSYSProbeError("DOCUMENTARY_002_RESPONSE_INVALID")
            return {"body": body, "final_url": current, "headers": headers,
                    "requests_started": redirect_count + 1, "status": response.status}
        raise PHOTSYSProbeError("DOCUMENTARY_002_REDIRECT_CAP")


def _checkpoint(directory: Path, receipt: dict[str, object]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    value = sealed({"sequence": 1, "stage_id": ATTEMPT_ID, **receipt})
    path = directory / "0001.json"
    write_json_immutable(path, value)
    index = sealed({"completed": [{"name": path.name, "sha256": file_sha256(path)}],
                    "completed_count": 1, "stage_id": ATTEMPT_ID})
    temporary = directory / ".CHECKPOINT_INDEX.tmp"
    with temporary.open("xb") as stream:
        stream.write(canonical_json_bytes(index)); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, directory / "CHECKPOINT_INDEX.json")


def validate_inputs() -> dict[str, object]:
    historical = validate_historical_attempt()
    evidence = validate_sealed(load_canonical_json(PARSE_EVIDENCE_PATH))
    if evidence != corrected_historical_parse():
        raise PHOTSYSProbeError("HISTORICAL_PARSE_EVIDENCE_INVALID")
    return {"historical_body_bytes": historical["body_bytes"],
            "historical_requests": historical["requests"], "network_requests": 0,
            "scope": SCOPE, "stage_id": ATTEMPT_ID,
            "state": "PHOTSYS_DOCUMENTARY_002_INPUTS_VALID"}


def dry_run() -> dict[str, object]:
    validate_inputs()
    return {"body_byte_cap": BODY_CAP, "data_head_requests": 0, "data_range_requests": 0,
            "full_fits_gets": 0, "network_requests": 0, "planned_request_cap": REQUEST_CAP,
            "scope": SCOPE, "stage_id": ATTEMPT_ID,
            "state": "PHOTSYS_DOCUMENTARY_002_DRY_RUN_OK", "table_cell_values_decoded": 0}


def persist_failure_terminal(output_directory: Path, error_code: str) -> None:
    """Seal a failed authorized attempt from any durable receipt already written."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    requests = 0
    body_bytes = 0
    checkpoint = output_directory / "CHECKPOINTS/0001.json"
    if checkpoint.is_file():
        receipt = validate_sealed(load_canonical_json(checkpoint))
        observed_requests = receipt.get("network_requests_started")
        observed_bytes = receipt.get("network_body_bytes")
        if isinstance(observed_requests, int) and observed_requests >= 0:
            requests = observed_requests
        if isinstance(observed_bytes, int) and observed_bytes >= 0:
            body_bytes = observed_bytes
    accounting_path = output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_RESOURCE_ACCOUNTING.json"
    if not accounting_path.exists():
        write_json_immutable(accounting_path, sealed({
            "cumulative_body_bytes": HISTORICAL_BODY_BYTES + body_bytes,
            "cumulative_requests": HISTORICAL_REQUESTS + requests,
            "data_head_requests": 0,
            "data_range_requests": 0,
            "forbidden_counters": Counters().object(),
            "full_fits_gets": 0,
            "historical_body_bytes": HISTORICAL_BODY_BYTES,
            "historical_requests": HISTORICAL_REQUESTS,
            "stage_body_bytes": body_bytes,
            "stage_requests": requests,
            "stage_id": ATTEMPT_ID,
            "state": "PARTIAL_RECONSTRUCTED_FROM_DURABLE_CHECKPOINTS",
        }))
    terminal_path = output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_TERMINAL.json"
    if not terminal_path.exists():
        write_json_immutable(terminal_path, sealed({
            "first_error": error_code,
            "literal_target_url": None,
            "stage_id": ATTEMPT_ID,
            "state": FAILED,
            "table_cell_values_decoded": 0,
        }))
    log_path = output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_RUN.log"
    if not log_path.exists():
        write_immutable(log_path, (
            f"stage_id={ATTEMPT_ID}\nstate={FAILED}\nfirst_error={error_code}\n"
            f"stage_requests={requests}\nstage_body_bytes={body_bytes}\n"
            "data_head_requests=0\ndata_range_requests=0\nfull_fits_gets=0\n"
            "table_cell_values_decoded=0\n"
        ).encode("ascii"))


def execute(candidate_path: Path, authorization_path: Path, command_argv_sha256: str,
            output_directory: Path, *,
            transport_factory: Callable[..., object] = DirectoryTransport) -> dict[str, object]:
    candidate, authorization = validate_final_authorization(
        candidate_path, authorization_path, command_argv_sha256)
    output_directory = Path(output_directory)
    if output_directory.exists():
        raise PHOTSYSProbeError("DOCUMENTARY_002_RERUN_OR_RESUME_FORBIDDEN")
    historical = validate_historical_attempt()
    parse_evidence = validate_sealed(load_canonical_json(PARSE_EVIDENCE_PATH))
    if parse_evidence != corrected_historical_parse():
        raise PHOTSYSProbeError("HISTORICAL_PARSE_EVIDENCE_INVALID")
    policy = candidate["policy"]
    transport = transport_factory(redirect_cap=policy["redirects_per_request"])
    budget = Budget(policy["request_cap_including_redirects"], policy["body_bytes_cap"], 0)
    budget.preflight(maximum=BODY_CAP, is_range=False,
                     request_envelope=1 + policy["redirects_per_request"])
    response = transport.get(DIRECTORY_URL, max_body_bytes=BODY_CAP)
    budget.charge(response, maximum=BODY_CAP, is_range=False)
    if response.get("status") != 200 or response.get("final_url") != DIRECTORY_URL:
        raise PHOTSYSProbeError("DOCUMENTARY_002_RESPONSE_INVALID")
    body = response["body"]
    raw = output_directory / "RAW_IMMUTABLE"
    write_immutable(raw / "official-dr9-randoms-directory-index.body", body)
    receipt = {"body_bytes": len(body), "content_sha256": sha256_bytes(body),
               "final_url": response["final_url"], "kind": "DOCUMENTARY_DIRECTORY_INDEX",
               "literal_url": DIRECTORY_URL,
               "network_body_bytes": budget.body_bytes,
               "network_requests_started": budget.requests,
               "observed_at_utc": datetime.now(timezone.utc).isoformat(),
               "resource_role": RESOURCE_ROLE, "status": response["status"]}
    _checkpoint(output_directory / "CHECKPOINTS", receipt)
    try:
        raw_href, literal_url = resolve_directory_href(body)
        state = SUCCESS; first_error = None
    except PHOTSYSProbeError as exc:
        if exc.code != "LITERAL_TARGET_HREF_NOT_UNIQUE":
            raise
        raw_href = None; literal_url = None; state = INCONCLUSIVE; first_error = exc.code
    write_json_immutable(output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_HISTORICAL_PARSE_EVIDENCE.json",
                         parse_evidence)
    index_evidence = sealed({"body_bytes": len(body), "content_sha256": sha256_bytes(body),
                             "literal_target_href": raw_href, "literal_target_url": literal_url,
                             "observed_at_utc": receipt["observed_at_utc"],
                             "resource_role": RESOURCE_ROLE, "source_url": DIRECTORY_URL,
                             "stage_id": ATTEMPT_ID})
    write_json_immutable(output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_DIRECTORY_INDEX_EVIDENCE.json",
                         index_evidence)
    provenance = sealed({"directory_index_sha256": sha256_bytes(body),
                         "historical_body_sha256": list(HISTORICAL_BODY_HASHES),
                         "historical_tree_seal": HISTORICAL_TREE_SEAL,
                         "literal_target_url": literal_url,
                         "parse_evidence_sha256": file_sha256(PARSE_EVIDENCE_PATH),
                         "stage_id": ATTEMPT_ID})
    write_json_immutable(output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_PROVENANCE_CHAIN.json",
                         provenance)
    counters = Counters(); counters.require_zero()
    accounting = sealed({"cumulative_body_bytes": historical["body_bytes"] + budget.body_bytes,
                         "cumulative_requests": historical["requests"] + budget.requests,
                         "data_head_requests": 0, "data_range_requests": 0,
                         "forbidden_counters": counters.object(), "full_fits_gets": 0,
                         "historical_body_bytes": historical["body_bytes"],
                         "historical_requests": historical["requests"],
                         "stage_body_bytes": budget.body_bytes, "stage_requests": budget.requests,
                         "stage_id": ATTEMPT_ID})
    write_json_immutable(output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_RESOURCE_ACCOUNTING.json",
                         accounting)
    terminal = sealed({"authorization_id": authorization["authorization_id"],
                       "first_error": first_error, "literal_target_url": literal_url,
                       "stage_id": ATTEMPT_ID, "state": state,
                       "table_cell_values_decoded": 0})
    write_json_immutable(output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_TERMINAL.json", terminal)
    write_immutable(output_directory / "OC3_PHOTSYS_DOCUMENTARY_002_RUN.log",
                    (f"stage_id={ATTEMPT_ID}\nstate={state}\nstage_requests={budget.requests}\n"
                     f"stage_body_bytes={budget.body_bytes}\ndata_head_requests=0\n"
                     "data_range_requests=0\nfull_fits_gets=0\ntable_cell_values_decoded=0\n").encode("ascii"))
    return {"body_bytes": budget.body_bytes, "literal_official_url": literal_url,
            "network_requests_started": budget.requests, "scope": SCOPE,
            "stage_id": ATTEMPT_ID, "state": state, "table_cell_values_decoded": 0}
