"""Bounded HEAD and FITS-header-only probe for the frozen PHOTSYS authority.

The stage is inert without a separately sealed candidate and final human
authorization.  It reuses the production HDU walker and cannot issue a full
body GET or decode any table cell.
"""
from __future__ import annotations

from datetime import datetime, timezone
import http.client
import os
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import urljoin, urlsplit

from .core import canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    ALLOWED_FIELDS, AMENDMENT, AMENDMENT_SHA256, Budget, CONTRACT,
    CONTRACT_SHA256, Counters, EXPECTED_ROOT_ROWS, HEADER_BLOCK,
    MAX_HEADER_BLOCKS, PHOTSYSProbeError, PROJECT, PROJECTION_UNAVAILABLE,
    TARGET_FILENAME, canonical_json_bytes, file_sha256, load_canonical_json,
    object_seal, probe_hdu_inventory, sealed, sha256_bytes,
    structural_contract, validate_sealed, write_immutable,
    write_json_immutable,
)
from .galaxy_eligibility_photsys_documentary002 import resolve_directory_href


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PHYSICAL-PROBE-001"
SCOPE = "PHOTSYS_FITS_HEADER_CONTRACT_ONLY"
SUCCESS = "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_RESOLVED"
INCONCLUSIVE = "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_INCONCLUSIVE"
FAILED = "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_FAILED"
NOT_BRICK_LEVEL = "PHOTSYS_AUTHORITY_NOT_BRICK_LEVEL_STOP"

LITERAL_URL = (
    "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/"
    "survey-bricks-dr9-randoms-0.48.0.fits"
)
DOCUMENTARY_STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-DOCUMENTARY-002"
DOCUMENTARY_ROOT = PROJECT / "oc3/photsys_authority_documentary" / DOCUMENTARY_STAGE_ID
DOCUMENTARY_TREE_SEAL = "9ba49a4080fc4501373d3dee5c1c8821f5d2279f833f1e755c3ee562a5043c23"
DIRECTORY_HTML_SHA256 = "09928bee3a1bb5ce114cbae11d6b850c9eb8cffa4a2ee17ac8728924cb55957e"
DOCUMENTARY_FILES = {
    "CHECKPOINTS/0001.json": "f7835a82aa2be3c574eb765e6138d39b83132d468e988fc2e2a0019be283ebce",
    "CHECKPOINTS/CHECKPOINT_INDEX.json": "a849618f5087520c7455295d617dfa78d299775b98a9af7ca3ffe0633099e179",
    "OC3_PHOTSYS_DOCUMENTARY_002_DIRECTORY_INDEX_EVIDENCE.json":
        "3681bb77006ef192833a62e7750118ef3958c49076e9ec0cd70f0b9b3607a4d7",
    "OC3_PHOTSYS_DOCUMENTARY_002_HISTORICAL_PARSE_EVIDENCE.json":
        "d66569e4a2b2647cc33b4a1be4815adfde738d97985ecb927c534cbcd85fe5bf",
    "OC3_PHOTSYS_DOCUMENTARY_002_PROVENANCE_CHAIN.json":
        "9f1fe4de2aa33518b866d29f82c8a33eef3b3bbde1cfb76256e7b384d8fc4a2a",
    "OC3_PHOTSYS_DOCUMENTARY_002_RESOURCE_ACCOUNTING.json":
        "0a942a532b6860db9f5edb2df0eef79e313d2cbe8a38c6df3a3297723e5d406b",
    "OC3_PHOTSYS_DOCUMENTARY_002_RUN.log":
        "600c8d5ef806013500ce2b16a9842106e5cfb339f06df6abe1d81b0427e5ebb9",
    "OC3_PHOTSYS_DOCUMENTARY_002_TERMINAL.json":
        "2713209cded21e54f875dfe34ab167d5028822c4655aeea644cc8a2ccbdd0c42",
    "RAW_IMMUTABLE/official-dr9-randoms-directory-index.body": DIRECTORY_HTML_SHA256,
}

REDIRECT_CAP = 1
HEAD_LOGICAL_REQUESTS = 1
RANGE_LOGICAL_REQUESTS = MAX_HEADER_BLOCKS
PRIMARY_LOGICAL_REQUESTS = HEAD_LOGICAL_REQUESTS + RANGE_LOGICAL_REQUESTS
MAX_TRANSPORT_REQUESTS = PRIMARY_LOGICAL_REQUESTS * (1 + REDIRECT_CAP)
HEADER_BODY_CAP = MAX_HEADER_BLOCKS * HEADER_BLOCK

CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_PHYSICAL_PROBE_CANDIDATE_001.json"
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_PHYSICAL_PROBE_FINAL_AUTHORIZATION_001.json"
OUTPUT_ROOT = PROJECT / "oc3/photsys_authority_physical_probe" / STAGE_ID


def documentary_tree_rows() -> list[dict[str, object]]:
    return [{"path": str(path.relative_to(DOCUMENTARY_ROOT)), "size": path.stat().st_size,
             "sha256": file_sha256(path)}
            for path in sorted(DOCUMENTARY_ROOT.rglob("*")) if path.is_file()]


def validate_documentary_attempt() -> dict[str, object]:
    if not DOCUMENTARY_ROOT.is_dir():
        raise PHOTSYSProbeError("DOCUMENTARY_002_EVIDENCE_MISSING")
    rows = documentary_tree_rows()
    if ({row["path"]: row["sha256"] for row in rows} != DOCUMENTARY_FILES or
            object_seal(rows) != DOCUMENTARY_TREE_SEAL):
        raise PHOTSYSProbeError("DOCUMENTARY_002_EVIDENCE_MUTATED")
    terminal = validate_sealed(load_canonical_json(
        DOCUMENTARY_ROOT / "OC3_PHOTSYS_DOCUMENTARY_002_TERMINAL.json"))
    accounting = validate_sealed(load_canonical_json(
        DOCUMENTARY_ROOT / "OC3_PHOTSYS_DOCUMENTARY_002_RESOURCE_ACCOUNTING.json"))
    directory = validate_sealed(load_canonical_json(
        DOCUMENTARY_ROOT / "OC3_PHOTSYS_DOCUMENTARY_002_DIRECTORY_INDEX_EVIDENCE.json"))
    parse = validate_sealed(load_canonical_json(
        DOCUMENTARY_ROOT / "OC3_PHOTSYS_DOCUMENTARY_002_HISTORICAL_PARSE_EVIDENCE.json"))
    raw = DOCUMENTARY_ROOT / "RAW_IMMUTABLE/official-dr9-randoms-directory-index.body"
    raw_href, resolved = resolve_directory_href(raw.read_bytes())
    if (terminal.get("state") != "PHOTSYS_LITERAL_RESOURCE_URL_BOUND" or
            terminal.get("literal_target_url") != LITERAL_URL or
            terminal.get("table_cell_values_decoded") != 0 or
            directory.get("literal_target_href") != raw_href or
            directory.get("literal_target_url") != resolved or resolved != LITERAL_URL or
            directory.get("content_sha256") != DIRECTORY_HTML_SHA256 or
            accounting.get("stage_requests") != 1 or
            accounting.get("stage_body_bytes") != 4683 or
            accounting.get("cumulative_requests") != 3 or
            accounting.get("cumulative_body_bytes") != 262366 or
            accounting.get("data_head_requests") != 0 or
            accounting.get("data_range_requests") != 0 or
            accounting.get("full_fits_gets") != 0 or
            any(accounting.get("forbidden_counters", {}).values()) or
            parse.get("facts", {}).get("brick_level_row_model_documented") is not True or
            parse.get("facts", {}).get("photsys_exact_values_documented") is not True):
        raise PHOTSYSProbeError("DOCUMENTARY_002_EVIDENCE_INVALID")
    return {"directory_html_sha256": DIRECTORY_HTML_SHA256,
            "documentary_tree_seal": DOCUMENTARY_TREE_SEAL,
            "facts": parse["facts"], "literal_url": LITERAL_URL,
            "terminal_seal": terminal["sealed"]}


def build_candidate(implementation_aggregate: str,
                    command_argv: Sequence[str]) -> dict[str, object]:
    evidence = validate_documentary_attempt()
    return sealed({
        "authorization_state": "FINAL_HUMAN_AUTHORIZATION_ABSENT",
        "candidate_scope": SCOPE,
        "command_argv": list(command_argv),
        "command_argv_sha256": sha256_bytes(canonical(list(command_argv))),
        "documentary_evidence": {
            "attempt_stage_id": DOCUMENTARY_STAGE_ID,
            "directory_index_evidence_sha256": DOCUMENTARY_FILES[
                "OC3_PHOTSYS_DOCUMENTARY_002_DIRECTORY_INDEX_EVIDENCE.json"],
            "directory_index_html_sha256": evidence["directory_html_sha256"],
            "provenance_chain_sha256": DOCUMENTARY_FILES[
                "OC3_PHOTSYS_DOCUMENTARY_002_PROVENANCE_CHAIN.json"],
            "terminal_sha256": DOCUMENTARY_FILES[
                "OC3_PHOTSYS_DOCUMENTARY_002_TERMINAL.json"],
            "tree_seal": evidence["documentary_tree_seal"],
        },
        "expected_row_count": EXPECTED_ROOT_ROWS,
        "expected_terminals": [SUCCESS, INCONCLUSIVE, FAILED],
        "final_authorization_path": str(AUTHORIZATION_PATH.relative_to(PROJECT)),
        "frozen_authorities": {
            str(CONTRACT.relative_to(PROJECT)): CONTRACT_SHA256,
            str(AMENDMENT.relative_to(PROJECT)): AMENDMENT_SHA256,
        },
        "implementation_aggregate": implementation_aggregate,
        "negative_capabilities": {
            "automatic_resume": False,
            "full_fits_get": False,
            "panel_v2": False,
            "p1": False,
            "stage_b_acquisition": False,
            "table_cell_decode": False,
            "tractor_sdss_gaia_desi": False,
            "whole_row_fallback": False,
        },
        "network_plan": {
            "automatic_retries": 0,
            "concurrency": 1,
            "header_block_bytes": HEADER_BLOCK,
            "header_body_byte_cap": HEADER_BODY_CAP,
            "head_logical_requests": HEAD_LOGICAL_REQUESTS,
            "max_header_blocks": MAX_HEADER_BLOCKS,
            "max_transport_requests_including_redirects": MAX_TRANSPORT_REQUESTS,
            "primary_logical_requests": PRIMARY_LOGICAL_REQUESTS,
            "range_logical_requests": RANGE_LOGICAL_REQUESTS,
            "redirects_per_request": REDIRECT_CAP,
        },
        "projection": {"fields": list(ALLOWED_FIELDS),
                       "status_before_real_probe": "UNOBSERVED_REAL_LAYOUT",
                       "whole_row_fallback": False},
        "resource": {"literal_url": LITERAL_URL, "resource_count": 1,
                     "target_filename": TARGET_FILENAME},
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "zero_value_firewall": Counters().object(),
    })


def validate_candidate(path: Path = CANDIDATE_PATH) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    expected = build_candidate(value.get("implementation_aggregate", ""),
                               value.get("command_argv", []))
    if (value != expected or value.get("implementation_aggregate") != implementation_hash(PROJECT) or
            value.get("command_argv_sha256") !=
            sha256_bytes(canonical(value.get("command_argv", [])))):
        raise PHOTSYSProbeError("PHYSICAL_PROBE_CANDIDATE_INVALID")
    return value


def validate_final_authorization(candidate_path: Path, authorization_path: Path,
                                 argv_sha256: str) -> tuple[dict[str, object], dict[str, object]]:
    candidate = validate_candidate(candidate_path)
    authorization = load_canonical_json(authorization_path)
    required = {"authorization_id", "authorization_state", "authorized", "candidate_sha256",
                "command_argv_sha256", "scope", "stage_id"}
    if (set(authorization) != required or authorization.get("authorized") is not True or
            authorization.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            authorization.get("candidate_sha256") != file_sha256(candidate_path) or
            authorization.get("command_argv_sha256") != argv_sha256 or
            authorization.get("command_argv_sha256") != candidate.get("command_argv_sha256") or
            authorization.get("scope") != SCOPE or authorization.get("stage_id") != STAGE_ID):
        raise PHOTSYSProbeError("PHYSICAL_PROBE_FINAL_AUTHORIZATION_INVALID")
    return candidate, authorization


class PhysicalTransport:
    """Exact-resource transport supporting one HEAD and aligned Range GETs only."""
    def __init__(self, *, redirect_cap: int, timeout_seconds: int = 30):
        if redirect_cap != REDIRECT_CAP:
            raise PHOTSYSProbeError("PHYSICAL_PROBE_REDIRECT_CAP_INVALID")
        self.redirect_cap = redirect_cap
        self.timeout_seconds = timeout_seconds
        self.head_requests = 0
        self.range_requests = 0
        self.max_requested_byte = -1
        self.representation: dict[str, str | None] | None = None

    def request(self, method: str, url: str, *, byte_range: tuple[int, int] | None,
                max_body_bytes: int) -> dict[str, object]:
        if url != LITERAL_URL:
            raise PHOTSYSProbeError("PHYSICAL_PROBE_RESOURCE_NOT_ALLOWLISTED")
        if method == "HEAD":
            if byte_range is not None or max_body_bytes != 0 or self.head_requests != 0:
                raise PHOTSYSProbeError("PHYSICAL_PROBE_HEAD_PLAN_INVALID")
            self.head_requests += 1
        elif method == "GET":
            if (self.head_requests != 1 or byte_range is None or max_body_bytes != HEADER_BLOCK or
                    byte_range[0] % HEADER_BLOCK or
                    byte_range[1] != byte_range[0] + HEADER_BLOCK - 1):
                raise PHOTSYSProbeError("PHYSICAL_PROBE_RANGE_PLAN_INVALID")
            self.range_requests += 1
            self.max_requested_byte = max(self.max_requested_byte, byte_range[1])
        else:
            raise PHOTSYSProbeError("PHYSICAL_PROBE_METHOD_FORBIDDEN")
        current = url
        for redirects in range(self.redirect_cap + 1):
            if current != LITERAL_URL:
                raise PHOTSYSProbeError("PHYSICAL_PROBE_REDIRECT_OUTSIDE_LITERAL")
            parsed = urlsplit(current)
            connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                      timeout=self.timeout_seconds)
            headers = {"Accept-Encoding": "identity",
                       "User-Agent": "OC3-PHOTSYS-physical-probe/1"}
            if byte_range is not None:
                headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
            connection.request(method, parsed.path, headers=headers)
            response = connection.getresponse()
            response_headers = {key.lower(): value for key, value in response.getheaders()}
            if response.status in (301, 302, 303, 307, 308):
                location = response_headers.get("location")
                connection.close()
                if not location or redirects >= self.redirect_cap:
                    raise PHOTSYSProbeError("PHYSICAL_PROBE_REDIRECT_CAP")
                current = urljoin(current, location)
                continue
            if current != LITERAL_URL:
                connection.close()
                raise PHOTSYSProbeError("PHYSICAL_PROBE_FINAL_URL_MISMATCH")
            encoding = response_headers.get("content-encoding", "identity").lower()
            if encoding != "identity":
                connection.close()
                raise PHOTSYSProbeError("PHYSICAL_PROBE_REPRESENTATION_ENCODING")
            if method == "HEAD":
                if (response.status != 200 or
                        response_headers.get("accept-ranges", "").lower() != "bytes" or
                        not response_headers.get("content-length", "").isdigit() or
                        int(response_headers["content-length"]) <= 0):
                    connection.close()
                    raise PHOTSYSProbeError("PHYSICAL_PROBE_HEAD_CONTRACT_INVALID")
                body = b""
                self.representation = {
                    "content_length": response_headers["content-length"],
                    "etag": response_headers.get("etag"),
                    "last_modified": response_headers.get("last-modified"),
                }
            else:
                if response.status != 206 or response_headers.get("content-length") != str(HEADER_BLOCK):
                    connection.close()
                    raise PHOTSYSProbeError("EXACT_RANGE_REQUIRED")
                if self.representation is None:
                    connection.close()
                    raise PHOTSYSProbeError("PHYSICAL_PROBE_HEAD_REQUIRED")
                for key in ("etag", "last_modified"):
                    header = key.replace("_", "-")
                    observed = response_headers.get(header)
                    if observed is not None and self.representation[key] is not None and \
                            observed != self.representation[key]:
                        connection.close()
                        raise PHOTSYSProbeError("PHYSICAL_PROBE_REPRESENTATION_DRIFT")
                body = response.read(HEADER_BLOCK + 1)
                if len(body) != HEADER_BLOCK:
                    connection.close()
                    raise PHOTSYSProbeError("EXACT_RANGE_REQUIRED")
            connection.close()
            return {"body": body, "final_url": current, "headers": response_headers,
                    "redirects": redirects, "requests_started": redirects + 1,
                    "status": response.status}
        raise PHOTSYSProbeError("PHYSICAL_PROBE_REDIRECT_CAP")


class PhysicalCheckpoints:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.last_sequence = 0

    def record(self, sequence: int, value: dict[str, object]) -> dict[str, object]:
        if sequence != self.last_sequence + 1:
            raise PHOTSYSProbeError("PHYSICAL_CHECKPOINT_SEQUENCE_INVALID")
        receipt = sealed({"sequence": sequence, "stage_id": STAGE_ID, **value})
        path = self.directory / f"{sequence:04d}.json"
        write_json_immutable(path, receipt)
        self.last_sequence = sequence
        entries = [{"name": item.name, "sha256": file_sha256(item)}
                   for item in sorted(self.directory.glob("[0-9][0-9][0-9][0-9].json"))]
        index = sealed({"completed": entries, "completed_count": len(entries),
                        "stage_id": STAGE_ID})
        temporary = self.directory / ".CHECKPOINT_INDEX.tmp"
        with temporary.open("xb") as stream:
            stream.write(canonical_json_bytes(index)); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, self.directory / "CHECKPOINT_INDEX.json")
        return receipt


def validate_inputs() -> dict[str, object]:
    evidence = validate_documentary_attempt()
    if file_sha256(CONTRACT) != CONTRACT_SHA256 or file_sha256(AMENDMENT) != AMENDMENT_SHA256:
        raise PHOTSYSProbeError("PHYSICAL_PROBE_FROZEN_AUTHORITY_MISMATCH")
    return {"documentary_tree_seal": evidence["documentary_tree_seal"],
            "literal_url": evidence["literal_url"], "network_requests": 0,
            "scope": SCOPE, "stage_id": STAGE_ID,
            "state": "PHOTSYS_PHYSICAL_PROBE_INPUTS_VALID"}


def dry_run() -> dict[str, object]:
    validate_inputs()
    return {"full_fits_gets": 0, "header_body_byte_cap": HEADER_BODY_CAP,
            "max_header_blocks": MAX_HEADER_BLOCKS,
            "max_transport_requests_including_redirects": MAX_TRANSPORT_REQUESTS,
            "network_requests": 0, "primary_logical_requests": PRIMARY_LOGICAL_REQUESTS,
            "projection_status": "UNOBSERVED_REAL_LAYOUT", "scope": SCOPE,
            "stage_id": STAGE_ID, "state": "READY_AT_REAL_TRANSPORT_BOUNDARY",
            "table_cell_values_decoded": 0}


def _hdu_public(item: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in item.items() if key != "header"}


def execute(candidate_path: Path, authorization_path: Path, argv_sha256: str,
            output_directory: Path, *,
            transport_factory: Callable[..., object] = PhysicalTransport) -> dict[str, object]:
    candidate, authorization = validate_final_authorization(
        candidate_path, authorization_path, argv_sha256)
    output_directory = Path(output_directory)
    if output_directory.exists():
        raise PHOTSYSProbeError("PHYSICAL_PROBE_RERUN_OR_RESUME_FORBIDDEN")
    evidence = validate_documentary_attempt()
    policy = candidate["network_plan"]
    transport = transport_factory(redirect_cap=policy["redirects_per_request"])
    budget = Budget(policy["max_transport_requests_including_redirects"],
                    policy["header_body_byte_cap"], policy["header_body_byte_cap"])
    checkpoints = PhysicalCheckpoints(output_directory / "CHECKPOINTS")
    raw = output_directory / "RAW_IMMUTABLE_HEADERS"; raw.mkdir(parents=True, exist_ok=True)

    budget.preflight(maximum=0, is_range=False, request_envelope=1 + REDIRECT_CAP)
    head = transport.request("HEAD", LITERAL_URL, byte_range=None, max_body_bytes=0)
    budget.charge(head, maximum=0, is_range=False)
    headers = head["headers"]
    file_size = int(headers["content-length"])
    observed_at = datetime.now(timezone.utc).isoformat()
    head_evidence = {
        "accept_ranges": headers.get("accept-ranges"),
        "content_encoding": headers.get("content-encoding", "identity"),
        "content_length": file_size,
        "etag": headers.get("etag"),
        "final_url": head["final_url"],
        "kind": "FITS_HEAD_EVIDENCE",
        "last_modified": headers.get("last-modified"),
        "network_body_bytes": budget.body_bytes,
        "network_requests_started": budget.requests,
        "observed_at_utc": observed_at,
        "status": head["status"],
    }
    checkpoints.record(1, head_evidence)

    def hdu_checkpoint(item: dict[str, object], sequence: int) -> int:
        sequence += 1
        checkpoints.record(sequence, {"data_bytes": item["data_bytes"],
                                      "data_offset": item["data_offset"],
                                      "hdu_end": item["hdu_end"],
                                      "hdu_index": item["hdu_index"],
                                      "hdu_type": item["hdu_type"],
                                      "header_bytes": item["header_bytes"],
                                      "header_sha256": item["header_sha256"],
                                      "header_start": item["header_start"],
                                      "kind": "HDU_STRUCTURAL_CHECKPOINT",
                                      "padded_data_bytes": item["padded_data_bytes"]})
        return sequence

    inventory, blocks_used = probe_hdu_inventory(
        transport, budget, checkpoints, raw, url=LITERAL_URL, file_size=file_size,
        header_block_cap=policy["max_header_blocks"], sequence_start=1,
        hdu_checkpoint=hdu_checkpoint)
    contract = structural_contract(inventory, evidence["facts"])
    table = inventory[contract["target_hdu_index"]]
    first_table_data_byte = contract["data_offset"]
    max_requested_byte = getattr(transport, "max_requested_byte", -1)
    if max_requested_byte >= first_table_data_byte:
        raise PHOTSYSProbeError("PHYSICAL_PROBE_TABLE_DATA_BOUNDARY_CROSSED")
    checkpoints.record(checkpoints.last_sequence + 1, {
        "column_schema": contract["column_schema"], "kind": "SCHEMA_CHECKPOINT",
        "row_count": contract["row_count"], "row_width": contract["row_width"],
        "target_hdu_index": contract["target_hdu_index"]})
    checkpoints.record(checkpoints.last_sequence + 1, {
        "first_table_data_byte": first_table_data_byte,
        "kind": "PROJECTION_PLAN_CHECKPOINT",
        "maximum_requested_byte": max_requested_byte,
        "proof_maximum_requested_byte_before_table_data": True,
        "selective_projection": contract["selective_projection"]})
    counters = Counters(); counters.require_zero()
    header_contract = sealed({
        "documentary_provenance": {"directory_html_sha256": DIRECTORY_HTML_SHA256,
                                   "documentary_tree_seal": DOCUMENTARY_TREE_SEAL},
        "first_table_data_byte": first_table_data_byte,
        "hdu_inventory": [{**_hdu_public(item), "header_cards": item["header"]}
                          for item in inventory],
        "http": head_evidence,
        "maximum_requested_byte": max_requested_byte,
        "proof_maximum_requested_byte_before_table_data": True,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "structural_contract": contract,
        "target_table_header_sha256": table["header_sha256"],
    })
    transport_evidence = sealed({
        "accept_ranges": head_evidence["accept_ranges"],
        "content_encoding": head_evidence["content_encoding"],
        "content_length": file_size,
        "etag": head_evidence["etag"],
        "final_url": head_evidence["final_url"],
        "first_table_data_byte": first_table_data_byte,
        "header_blocks": blocks_used,
        "last_modified": head_evidence["last_modified"],
        "maximum_requested_byte": max_requested_byte,
        "representation_stability": "NO_CONFLICT_OBSERVED_ACROSS_HEAD_AND_RANGES",
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "status": head_evidence["status"],
    })
    write_json_immutable(
        output_directory / "OC3_PHOTSYS_AUTHORITY_TRANSPORT_EVIDENCE.json",
        transport_evidence)
    write_json_immutable(
        output_directory / "OC3_PHOTSYS_AUTHORITY_HEADER_SCHEMA_CONTRACT.json",
        header_contract)
    accounting = sealed({
        "forbidden_counters": counters.object(), "full_fits_gets": 0,
        "header_blocks": blocks_used, "network_body_bytes": budget.body_bytes,
        "network_requests_started": budget.requests,
        "primary_head_requests": getattr(transport, "head_requests", 1),
        "primary_range_requests": getattr(transport, "range_requests", blocks_used),
        "scope": SCOPE, "stage_id": STAGE_ID, "table_cell_values_decoded": 0,
    })
    write_json_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json",
                         accounting)
    terminal = sealed({
        "authorization_id": authorization["authorization_id"], "first_error": None,
        "full_acquisition_authorized": False, "projection_state":
            "PHOTSYS_THREE_FIELD_PROJECTION_PROVEN",
        "scope": SCOPE, "stage_id": STAGE_ID, "state": SUCCESS,
        "table_cell_values_decoded": 0,
    })
    write_json_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json",
                         terminal)
    write_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_PHYSICAL_PROBE_RUN.log",
                    (f"stage_id={STAGE_ID}\nstate={SUCCESS}\n"
                     f"network_requests_started={budget.requests}\n"
                     f"header_body_bytes={budget.body_bytes}\nheader_blocks={blocks_used}\n"
                     f"first_table_data_byte={first_table_data_byte}\n"
                     f"maximum_requested_byte={max_requested_byte}\n"
                     "full_fits_gets=0\ntable_cell_values_decoded=0\n").encode("ascii"))
    return {"first_table_data_byte": first_table_data_byte,
            "header_body_bytes": budget.body_bytes, "header_blocks": blocks_used,
            "maximum_requested_byte": max_requested_byte,
            "network_requests_started": budget.requests,
            "projection_state": "PHOTSYS_THREE_FIELD_PROJECTION_PROVEN",
            "scope": SCOPE, "stage_id": STAGE_ID, "state": SUCCESS,
            "table_cell_values_decoded": 0}


def persist_failure_terminal(output_directory: Path, error_code: str) -> None:
    output_directory = Path(output_directory); output_directory.mkdir(parents=True, exist_ok=True)
    requests = 0; body_bytes = 0; header_blocks = 0
    directory = output_directory / "CHECKPOINTS"
    if directory.is_dir():
        for path in sorted(directory.glob("[0-9][0-9][0-9][0-9].json")):
            try:
                item = validate_sealed(load_canonical_json(path))
            except PHOTSYSProbeError:
                continue
            if isinstance(item.get("network_requests_started"), int):
                requests = max(requests, item["network_requests_started"])
            if isinstance(item.get("network_body_bytes"), int):
                body_bytes = max(body_bytes, item["network_body_bytes"])
            if item.get("kind") == "FITS_HEADER_BLOCK":
                header_blocks += 1
    accounting_path = output_directory / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json"
    if not accounting_path.exists():
        write_json_immutable(accounting_path, sealed({
            "forbidden_counters": Counters().object(), "full_fits_gets": 0,
            "header_blocks": header_blocks, "network_body_bytes": body_bytes,
            "network_requests_started": requests, "scope": SCOPE, "stage_id": STAGE_ID,
            "state": "PARTIAL_RECONSTRUCTED_FROM_DURABLE_CHECKPOINTS",
            "table_cell_values_decoded": 0}))
    terminal_path = output_directory / "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json"
    if not terminal_path.exists():
        write_json_immutable(terminal_path, sealed({
            "first_error": error_code, "full_acquisition_authorized": False,
            "projection_state": (PROJECTION_UNAVAILABLE if error_code == PROJECTION_UNAVAILABLE
                                 else "UNRESOLVED"),
            "scope": SCOPE, "stage_id": STAGE_ID, "state": FAILED,
            "table_cell_values_decoded": 0}))
