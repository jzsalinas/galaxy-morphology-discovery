"""Frozen acquisition/integrity logic for the OC3 DR9 source-metadata pilot.

No positional topology or cross-observer identity operation exists here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import csv
from datetime import datetime, timezone
import hashlib
import io
import math
import os
from pathlib import Path
import re
from typing import Callable, Iterable, Mapping, TextIO
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .cross_observer_grouping import file_sha256, load_canonical_json, sealed, validate_sealed, write_json_immutable

MISSION_ID = "OC3-SOURCE-METADATA-ACQUISITION-PILOT-AUTONOMY-001"
MISSION_SCOPE = "PROSPECTIVE_DR9_SOURCE_METADATA_ACQUISITION_ONLY"
STAGE_ID = "OC3-SOURCE-METADATA-ACQUISITION-PILOT-001"
SERVICE_ENDPOINT = "https://datalab.noirlab.edu/query/query"
PUBLIC_ANONYMOUS_TOKEN = "anonymous.0.0.anon_access"
USER_AGENT = "OC3-source-metadata-acquisition-pilot/1"
TIMEOUT_SECONDS = 300
REQUEST_CAP = 5
BODY_CAP = 67_108_864
MAX_SOURCE_ROWS_PER_DOMAIN = 150_000
ROW_QUERY_HARD_CAP = 150_001
CONCURRENCY = 1
RETRIES = 0
REDIRECTS = 0
RESUME = False

TABLES = ("ls_dr9.tractor_n", "ls_dr9.tractor_s")
PROJECTION = ("release", "brickid", "objid", "brickname", "brick_primary",
              "ra", "dec", "ra_ivar", "dec_ivar")
SCHEMA_PROJECTION = ("table_name", "column_name", "datatype", "description")
COUNT_PROJECTION = ("brickname", "source_count")
ORDER_BY = ("release", "brickid", "objid")
TARGET_IDENTITIES = (("2255p305", 498957), ("1901p342", 517112))
HOLDOUT_IDENTITIES = (("1075p337", 514444), ("0381m012", 323320))
TARGET_GUARD_UNION = (
    "1897p342", "1898p345", "1900p340", "1901p342", "1901p345", "1903p340", "1904p342",
    "2252p305", "2254p307", "2255p302", "2255p305", "2257p302", "2257p307", "2258p305",
)
HOLDOUT_GUARD_UNION = (
    "0378m010", "0378m012", "0378m015", "0381m010", "0381m012", "0381m015", "0383m010",
    "0383m012", "0383m015", "1072p337", "1073p340", "1074p335", "1075p337", "1076p340",
    "1077p335", "1078p337",
)
RESPONSE_CAPS = {
    "schema": 524_288,
    "north_count": 65_536,
    "south_count": 65_536,
    "north_rows": 32_505_856,
    "south_rows": 32_505_856,
}
REQUEST_ORDER = ("schema", "north_count", "south_count", "north_rows", "south_rows")
TRUE_SERIALIZATIONS = frozenset(("1", "true", "TRUE", "t", "T"))
MISSING_IVAR_SERIALIZATIONS = frozenset(("", "NULL", "null"))

DATATYPE_CLASSES = {
    "integer-compatible": frozenset((
        "adql:smallint", "adql:integer", "adql:bigint", "smallint", "integer", "bigint",
        "short", "int", "long",
    )),
    "string-compatible": frozenset((
        "adql:varchar", "varchar", "char", "character varying", "text", "unicodechar",
    )),
    "boolean/integer-boolean-compatible": frozenset((
        "adql:boolean", "boolean", "bool", "adql:smallint", "smallint", "adql:integer", "integer",
    )),
    "floating-compatible": frozenset((
        "adql:real", "adql:double", "real", "double", "double precision", "float", "float4", "float8",
    )),
}
COLUMN_SEMANTIC_CLASS = {
    "release": "integer-compatible", "brickid": "integer-compatible", "objid": "integer-compatible",
    "brickname": "string-compatible", "brick_primary": "boolean/integer-boolean-compatible",
    "ra": "floating-compatible", "dec": "floating-compatible",
    "ra_ivar": "floating-compatible", "dec_ivar": "floating-compatible",
}

FAILURE_TAXONOMY = (
    "DATALAB_SCHEMA_MISMATCH", "DATALAB_TRANSPORT_FAILURE", "DATALAB_REDIRECT_FORBIDDEN",
    "DATALAB_AUTHENTICATION_REQUIRED", "DATALAB_BODY_CAP_EXCEEDED", "SOURCE_COUNT_RESOURCE_BOUND",
    "SOURCE_RESPONSE_HEADER_MISMATCH", "SOURCE_IDENTITY_INTEGRITY_FAILURE", "SOURCE_COUNT_ROW_MISMATCH",
    "SOURCE_ORDERING_INTEGRITY_FAILURE", "SOURCE_HOLDOUT_FIREWALL_VIOLATION",
    "SOURCE_UNEXPECTED_BRICK_FAILURE", "WORKER_RUNTIME_FAILURE",
)
OUTCOMES = (
    "SOURCE_METADATA_ACQUISITION_COMPLETED", "SOURCE_METADATA_ACQUISITION_RESOURCE_BOUND",
    "SOURCE_METADATA_ACQUISITION_INCONCLUSIVE", "SOURCE_METADATA_ACQUISITION_INTEGRITY_FAILED",
)


class AcquisitionError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass
class AcquisitionSequence:
    """Small fail-closed gate used by the worker and synthetic tests."""
    schema_accepted: bool = False
    counts: dict[str, int] = field(default_factory=dict)
    resource_bound: bool = False

    def accept_schema(self, schema: Mapping[str, Mapping[str, str]]) -> None:
        if self.schema_accepted or self.counts or set(schema) != set(TABLES):
            raise AcquisitionError("DATALAB_SCHEMA_MISMATCH")
        if any(set(columns) != set(PROJECTION) for columns in schema.values()):
            raise AcquisitionError("DATALAB_SCHEMA_MISMATCH")
        self.schema_accepted = True

    def accept_count(self, domain: str, values: Mapping[str, int]) -> None:
        if not self.schema_accepted or domain not in ("north", "south") or domain in self.counts:
            raise AcquisitionError("SOURCE_COUNT_ROW_MISMATCH")
        total = sum(int(value) for value in values.values())
        if total < 0:
            raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
        self.counts[domain] = total
        self.resource_bound = self.resource_bound or total > MAX_SOURCE_ROWS_PER_DOMAIN

    def rows_allowed(self) -> bool:
        return self.schema_accepted and set(self.counts) == {"north", "south"} and not self.resource_bound


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonicalize_adql(value: str) -> str:
    return " ".join(value.split())


def query_sha256(value: str) -> str:
    return hashlib.sha256(canonicalize_adql(value).encode("utf-8")).hexdigest()


def _brick_literal() -> str:
    return "('" + "','".join(TARGET_GUARD_UNION) + "')"


SCHEMA_QUERY = """SELECT table_name,column_name,datatype,description
FROM TAP_SCHEMA.columns
WHERE table_name IN ('ls_dr9.tractor_n','ls_dr9.tractor_s')
AND column_name IN
('release','brickid','objid','brickname','brick_primary',
'ra','dec','ra_ivar','dec_ivar')
ORDER BY table_name,column_name"""


def validate_table(table: str) -> None:
    if table not in TABLES:
        raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")


def count_query(table: str) -> str:
    validate_table(table)
    return f"""SELECT brickname,COUNT(*) AS source_count
FROM {table}
WHERE brick_primary = 1
AND brickname IN
{_brick_literal()}
GROUP BY brickname
ORDER BY brickname"""


def row_query(table: str) -> str:
    validate_table(table)
    return f"""SELECT TOP 150001
release,brickid,objid,brickname,brick_primary,ra,dec,ra_ivar,dec_ivar
FROM {table}
WHERE brick_primary = 1
AND brickname IN
{_brick_literal()}
ORDER BY release,brickid,objid"""


QUERY_LITERALS = {
    "schema": SCHEMA_QUERY,
    "north_count": count_query("ls_dr9.tractor_n"),
    "south_count": count_query("ls_dr9.tractor_s"),
    "north_rows": row_query("ls_dr9.tractor_n"),
    "south_rows": row_query("ls_dr9.tractor_s"),
}


def query_url(query: str) -> str:
    parameters = (
        ("adql", query), ("ofmt", "csv"), ("out", "None"),
        ("async", "False"), ("drop", "False"), ("profile", "default"),
    )
    return SERVICE_ENDPOINT + "?" + urlencode(parameters, quote_via=quote)


def frozen_headers() -> dict[str, str]:
    return {"Content-Type": "text/ascii", "User-Agent": USER_AGENT,
            "X-DL-AuthToken": PUBLIC_ANONYMOUS_TOKEN, "X-DL-TimeoutRequest": "300"}


def validate_query_boundary(query: str) -> None:
    normalized = canonicalize_adql(query).lower()
    forbidden = (r"\bls_dr9\.tractor\b", r"\bls_dr10\b", r"\bls_dr11\b", r"\bsweep", r"\bmydb\b",
                 r"\bq3c", r"\bcone", r"\bcrossmatch", r"select\s+\*")
    if any(re.search(pattern, normalized) for pattern in forbidden):
        raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
    if any(name in normalized for name in HOLDOUT_GUARD_UNION):
        raise AcquisitionError("SOURCE_HOLDOUT_FIREWALL_VIOLATION")


def validate_frozen_support() -> None:
    if (TARGET_GUARD_UNION != tuple(sorted(TARGET_GUARD_UNION)) or
            HOLDOUT_GUARD_UNION != tuple(sorted(HOLDOUT_GUARD_UNION)) or
            len(TARGET_GUARD_UNION) != 14 or len(HOLDOUT_GUARD_UNION) != 16 or
            set(TARGET_GUARD_UNION) & set(HOLDOUT_GUARD_UNION)):
        raise AcquisitionError("SOURCE_HOLDOUT_FIREWALL_VIOLATION")
    for query in QUERY_LITERALS.values():
        validate_query_boundary(query)


def frame_support(frame_path: Path, expected_sha256: str) -> tuple[dict[str, int], tuple[tuple[str, int], ...], tuple[tuple[str, int], ...]]:
    if file_sha256(frame_path) != expected_sha256:
        raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
    frame = validate_sealed(load_canonical_json(frame_path))
    rows = frame.get("selections")
    if not isinstance(rows, list) or len(rows) != 4:
        raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
    targets = tuple((row["global_identity"]["brickname"], int(row["global_identity"]["brickid"]))
                    for row in rows if row.get("role") == "PILOT_TARGET")
    holdouts = tuple((row["global_identity"]["brickname"], int(row["global_identity"]["brickid"]))
                     for row in rows if row.get("role") == "RESERVED_HOLDOUT")
    mapping: dict[str, int] = {}
    target_bricks: set[str] = set()
    holdout_bricks: set[str] = set()
    for row in rows:
        names = target_bricks if row["role"] == "PILOT_TARGET" else holdout_bricks
        for member in row["guard"]:
            name, brickid = str(member["brickname"]), int(member["brickid"])
            names.add(name)
            if name in mapping and mapping[name] != brickid:
                raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
            mapping[name] = brickid
    if (targets != TARGET_IDENTITIES or holdouts != HOLDOUT_IDENTITIES or
            tuple(sorted(target_bricks)) != TARGET_GUARD_UNION or
            tuple(sorted(holdout_bricks)) != HOLDOUT_GUARD_UNION):
        raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
    return {name: mapping[name] for name in TARGET_GUARD_UNION}, targets, holdouts


def _reader(source: TextIO, expected: tuple[str, ...]) -> csv.DictReader:
    reader = csv.DictReader(source)
    if tuple(reader.fieldnames or ()) != expected:
        raise AcquisitionError("SOURCE_RESPONSE_HEADER_MISMATCH")
    return reader


def parse_schema(source: TextIO) -> dict[str, dict[str, str]]:
    reader = _reader(source, SCHEMA_PROJECTION)
    observed: dict[str, dict[str, str]] = {table: {} for table in TABLES}
    count = 0
    for row in reader:
        count += 1
        table, column = row["table_name"], row["column_name"]
        if table not in observed or column not in PROJECTION or column in observed[table]:
            raise AcquisitionError("DATALAB_SCHEMA_MISMATCH")
        datatype = row["datatype"].strip().lower()
        semantic = COLUMN_SEMANTIC_CLASS[column]
        if datatype not in DATATYPE_CLASSES[semantic]:
            raise AcquisitionError("DATALAB_SCHEMA_MISMATCH")
        observed[table][column] = datatype
    if count != 18 or any(set(columns) != set(PROJECTION) for columns in observed.values()):
        raise AcquisitionError("DATALAB_SCHEMA_MISMATCH")
    return observed


def _strict_nonnegative_int(value: str, code: str) -> int:
    if re.fullmatch(r"[0-9]+", value.strip()) is None:
        raise AcquisitionError(code)
    return int(value)


def parse_counts(source: TextIO) -> dict[str, int]:
    reader = _reader(source, COUNT_PROJECTION)
    observed: dict[str, int] = {}
    for row in reader:
        name = row["brickname"]
        if name in HOLDOUT_GUARD_UNION:
            raise AcquisitionError("SOURCE_HOLDOUT_FIREWALL_VIOLATION")
        if name not in TARGET_GUARD_UNION:
            raise AcquisitionError("SOURCE_UNEXPECTED_BRICK_FAILURE")
        if name in observed:
            raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
        observed[name] = _strict_nonnegative_int(row["source_count"], "SOURCE_IDENTITY_INTEGRITY_FAILURE")
    return {name: observed.get(name, 0) for name in TARGET_GUARD_UNION}


def classify_ivar(value: str) -> str:
    stripped = value.strip()
    if stripped in MISSING_IVAR_SERIALIZATIONS:
        return "MISSING"
    try:
        number = float(stripped)
    except ValueError:
        return "INVALID"
    if not math.isfinite(number) or number < 0:
        return "INVALID"
    return "ZERO" if number == 0 else "POSITIVE_FINITE"


def validate_source_rows(source: TextIO, expected_counts: Mapping[str, int],
                         brick_ids: Mapping[str, int]) -> dict[str, object]:
    reader = _reader(source, PROJECTION)
    previous: tuple[int, int, int] | None = None
    per_brick = {name: 0 for name in TARGET_GUARD_UNION}
    ivars = {axis: {state: 0 for state in ("POSITIVE_FINITE", "ZERO", "MISSING", "INVALID")}
             for axis in ("ra_ivar", "dec_ivar")}
    rows = 0
    for row in reader:
        rows += 1
        if rows >= ROW_QUERY_HARD_CAP:
            raise AcquisitionError("SOURCE_COUNT_ROW_MISMATCH")
        name = row["brickname"]
        if name in HOLDOUT_GUARD_UNION:
            raise AcquisitionError("SOURCE_HOLDOUT_FIREWALL_VIOLATION")
        if name not in TARGET_GUARD_UNION:
            raise AcquisitionError("SOURCE_UNEXPECTED_BRICK_FAILURE")
        release = _strict_nonnegative_int(row["release"], "SOURCE_IDENTITY_INTEGRITY_FAILURE")
        brickid = _strict_nonnegative_int(row["brickid"], "SOURCE_IDENTITY_INTEGRITY_FAILURE")
        objid = _strict_nonnegative_int(row["objid"], "SOURCE_IDENTITY_INTEGRITY_FAILURE")
        identity = (release, brickid, objid)
        if previous is not None and identity <= previous:
            raise AcquisitionError("SOURCE_ORDERING_INTEGRITY_FAILURE")
        previous = identity
        if brickid != brick_ids.get(name):
            raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
        if row["brick_primary"] not in TRUE_SERIALIZATIONS:
            raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
        try:
            ra, dec = float(row["ra"]), float(row["dec"])
        except ValueError as exc:
            raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE") from exc
        if not (math.isfinite(ra) and 0 <= ra < 360 and math.isfinite(dec) and -90 <= dec <= 90):
            raise AcquisitionError("SOURCE_IDENTITY_INTEGRITY_FAILURE")
        per_brick[name] += 1
        for axis in ivars:
            ivars[axis][classify_ivar(row[axis])] += 1
    expected = {name: int(expected_counts.get(name, 0)) for name in TARGET_GUARD_UNION}
    if per_brick != expected or rows != sum(expected.values()):
        raise AcquisitionError("SOURCE_COUNT_ROW_MISMATCH")
    return {"accepted_row_count": rows, "ivar_states": ivars, "per_brick_counts": per_brick}


class RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AcquisitionError("DATALAB_REDIRECT_FORBIDDEN")


@dataclass
class Accounting:
    requests_started: int = 0
    body_bytes_read: int = 0
    records: list[dict[str, object]] = field(default_factory=list)


def bounded_get(query_id: str, literal_url: str, cap: int, target: Path, accounting: Accounting,
                opener_factory: Callable[[], object] | None = None,
                ledger_directory: Path | None = None) -> dict[str, object]:
    if query_id not in REQUEST_ORDER or cap != RESPONSE_CAPS[query_id]:
        raise AcquisitionError("DATALAB_TRANSPORT_FAILURE")
    if literal_url != query_url(QUERY_LITERALS[query_id]) or accounting.requests_started >= REQUEST_CAP:
        raise AcquisitionError("DATALAB_TRANSPORT_FAILURE")
    accounting.requests_started += 1
    if opener_factory is None:
        opener_factory = lambda: build_opener(RejectRedirect)
    request = Request(literal_url, method="GET", headers=frozen_headers())
    started = _utc(); target.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, object] = {"body_bytes_read": 0, "body_sha256": None,
        "completion_state": "REQUEST_INTENT_RECORDED", "content_type": None,
        "ended_at_utc": None, "final_url": None, "http_status": None,
        "query_id": query_id, "redirect_count": 0,
        "query_sha256": query_sha256(QUERY_LITERALS[query_id]),
        "request_number": accounting.requests_started, "started_at_utc": started}
    accounting.records.append(record)
    if ledger_directory is not None:
        write_json_immutable(Path(ledger_directory) / f"{accounting.requests_started:02d}_{query_id}_INTENT.json",
            sealed({"literal_url": literal_url, "query_id": query_id,
                "query_sha256": record["query_sha256"], "request_number": accounting.requests_started,
                "schema_version": "OC3_SOURCE_METADATA_ACQUISITION_REQUEST_INTENT_001",
                "started_at_utc": started}))
    response = None; digest = hashlib.sha256(); body_bytes = 0
    try:
        response = opener_factory().open(request, timeout=TIMEOUT_SECONDS)
        status = int(getattr(response, "status", response.getcode()))
        record["http_status"] = status; record["final_url"] = response.geturl()
        if status in (401, 403):
            raise AcquisitionError("DATALAB_AUTHENTICATION_REQUIRED")
        if 300 <= status < 400 or response.geturl() != literal_url:
            raise AcquisitionError("DATALAB_REDIRECT_FORBIDDEN")
        if status != 200:
            raise AcquisitionError("DATALAB_TRANSPORT_FAILURE")
        content_type = response.headers.get_content_type()
        record["content_type"] = content_type
        if content_type not in ("text/csv", "text/plain", "application/x-csv"):
            raise AcquisitionError("DATALAB_TRANSPORT_FAILURE")
        with target.open("xb") as stream:
            while True:
                chunk = response.read(min(65_536, cap + 1 - body_bytes))
                if not chunk:
                    break
                stream.write(chunk); stream.flush()
                body_bytes += len(chunk); accounting.body_bytes_read += len(chunk); digest.update(chunk)
                record["body_bytes_read"] = body_bytes
                if accounting.body_bytes_read > BODY_CAP or body_bytes > cap:
                    raise AcquisitionError("DATALAB_BODY_CAP_EXCEEDED")
            os.fsync(stream.fileno())
        target.chmod(0o444)
        record.update({"body_sha256": digest.hexdigest(),
                "completion_state": "COMPLETE", "content_type": content_type,
                "ended_at_utc": _utc(), "final_url": response.geturl(), "http_status": status,
                "redirect_count": 0})
        return dict(record)
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise AcquisitionError("DATALAB_AUTHENTICATION_REQUIRED") from exc
        if 300 <= exc.code < 400:
            raise AcquisitionError("DATALAB_REDIRECT_FORBIDDEN") from exc
        raise AcquisitionError("DATALAB_TRANSPORT_FAILURE") from exc
    except AcquisitionError:
        raise
    except (URLError, TimeoutError, ConnectionError) as exc:
        raise AcquisitionError("DATALAB_TRANSPORT_FAILURE") from exc
    finally:
        if record["completion_state"] != "COMPLETE":
            record["body_sha256"] = digest.hexdigest()
            record["ended_at_utc"] = _utc()
            record["completion_state"] = "FAILED_CLOSED"
        if response is not None:
            response.close()
        if target.exists():
            target.chmod(0o444)
        if ledger_directory is not None:
            write_json_immutable(Path(ledger_directory) / f"{accounting.requests_started:02d}_{query_id}_RESULT.json",
                sealed({"record": dict(record),
                    "schema_version": "OC3_SOURCE_METADATA_ACQUISITION_REQUEST_RESULT_001"}))


def terminal_outcome_for(code: str) -> str:
    if code == "SOURCE_COUNT_RESOURCE_BOUND":
        return "SOURCE_METADATA_ACQUISITION_RESOURCE_BOUND"
    if code in ("DATALAB_TRANSPORT_FAILURE", "DATALAB_REDIRECT_FORBIDDEN",
                "DATALAB_AUTHENTICATION_REQUIRED", "DATALAB_BODY_CAP_EXCEEDED", "DATALAB_SCHEMA_MISMATCH"):
        return "SOURCE_METADATA_ACQUISITION_INCONCLUSIVE"
    if code in FAILURE_TAXONOMY:
        return "SOURCE_METADATA_ACQUISITION_INTEGRITY_FAILED"
    return "SOURCE_METADATA_ACQUISITION_INCONCLUSIVE"


def load_text(path: Path) -> TextIO:
    return path.open("r", encoding="utf-8", newline="")
