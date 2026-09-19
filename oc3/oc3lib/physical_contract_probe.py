"""Bounded provider physical-contract probe.

This module observes HTTP metadata and FITS headers only.  It deliberately has
no table/row API and no dependency on bootstrap, selection, or provider row
decoding code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import contextlib
import gzip
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import sqlite3
import ssl
import threading
import time
from types import MappingProxyType
from typing import Iterable, Mapping, Protocol
from urllib.parse import urlsplit
import zlib

from .core import canonical, digest, file_hash, implementation_hash, immutable_write


PROBE_SPEC_NAME = "OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC.md"
PROBE_SPEC_SHA256 = "9f86e8c685576a8207b4d5befe922f17a7a0bab428b306a8ec8af393ee37c174"
PROBE_CLARIFICATION_001_NAME = "OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC_CLARIFICATION_001.md"
PROBE_CLARIFICATION_001_SHA256 = "bf26b25d7b979e70d433edd42f12a69a36d59a43705f840bc3d9f1f1e4f7e39a"
PRE_PROBE_IMPLEMENTATION = "e374e482cc97c66399025c2bbe0776749dcbd8451998edd441bab165c03fd683"
PRE_CLARIFICATION_001_IMPLEMENTATION = "df8fe72deb876b567e076e05fbd7108bd4734ead4b3b467bc2c7d1f306b836f7"
ENVIRONMENT_FINGERPRINT = "b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf"
AMENDMENT_003_RECEIPT_SHA256 = "09c9676e9f7f3b2ce8f063aa63b34fcc7d40fe3299cb898ecfdb76b95522a38e"

PROBE_AUTHORITIES = MappingProxyType({
    "OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md": "7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd",
    "OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md": "2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66",
    "OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md": "4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe",
    "OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md": "ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c",
    "OC3_DR9_BOOTSTRAP_DOCUMENTARY_EVIDENCE.md": "07f2e20994d52783a84a176113b3f8cdf3d3ba4a0f0e0cf4fc33868e5277769b",
    "OC3_DR9_PROVIDER_SCHEMA_CONTRACT.md": "d02815a66f27df67e60f0cb1dc4d38a977e70c492417d3397946911159bf31c9",
    "OC3_AMENDMENT_003_IMPLEMENTATION_REPORT.md": "a1a02a2cdbb0daa697854c74d9c57cc44697a4486ff3547523271fe7cf90b2eb",
    PROBE_SPEC_NAME: PROBE_SPEC_SHA256,
})


@dataclass(frozen=True)
class ProbeResource:
    role: str
    url: str
    kind: str
    compression: str
    expected_name: str | None = None
    expected_sha256: str | None = None


_RESOURCE_ROWS = (
    ProbeResource("ROOT_SUMMARY", "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz", "fits", "gzip"),
    ProbeResource("NORTH_SUMMARY", "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz", "fits", "gzip"),
    ProbeResource("SOUTH_SUMMARY", "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz", "fits", "gzip"),
    ProbeResource("SOUTH_PATCH_LIST", "https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits", "fits", "identity"),
    ProbeResource("ROOT_CHECKSUM_MANIFEST", "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/legacysurvey_dr9.sha256sum", "manifest", "identity", "survey-bricks.fits.gz", "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f"),
    ProbeResource("NORTH_CHECKSUM_MANIFEST", "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/legacysurvey_dr9_north.sha256sum", "manifest", "identity", "survey-bricks-dr9-north.fits.gz", "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb"),
    ProbeResource("SOUTH_CHECKSUM_MANIFEST", "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/legacysurvey_dr9_south.sha256sum", "manifest", "identity", "survey-bricks-dr9-south.fits.gz", "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f"),
)
RESOURCES = MappingProxyType({r.role: r for r in _RESOURCE_ROWS})
FITS_ROLES = tuple(r.role for r in _RESOURCE_ROWS if r.kind == "fits")
MANIFEST_ROLES = tuple(r.role for r in _RESOURCE_ROWS if r.kind == "manifest")
RANGES = ("bytes=0-65535", "bytes=65536-131071", "bytes=131072-196607", "bytes=196608-262143")

CAPS = MappingProxyType({
    "fits_body_bytes": 1 * 2**20,
    "fits_resource_bytes": 256 * 2**10,
    "manifest_body_bytes": 8 * 2**20,
    "http_body_bytes": 9 * 2**20,
    "requests": 32,
    "concurrency": 1,
    "retries": 1,
    "ram_bytes": 512 * 2**20,
    "disk_bytes": 64 * 2**20,
    "io_bytes": 256 * 2**20,
    "compute_seconds": 300,
    "wall_seconds": 900,
    "threads": 1,
    "gpu": 0,
})

TERMINAL_PRECEDENCE = (
    "PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE",
    "PROBE_TRANSPORT_INTEGRITY_FAILURE",
    "PROBE_PROVIDER_DOCUMENTATION_CONFLICT",
    "PROBE_RANGE_UNAVAILABLE_STOP",
    "PROBE_HEADER_CAP_INSUFFICIENT",
    "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED",
    "PROBE_PHYSICAL_CONTRACTS_RESOLVED",
)


class ProbeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class NeedMoreHeaderData(Exception):
    pass


class InterveningPayload(ProbeError):
    def __init__(self):
        super().__init__("INTERVENING_DATA_PAYLOAD_STOP")


def verify_probe_authorities(project: Path) -> dict[str, str]:
    project = Path(project)
    result: dict[str, str] = {}
    for name, expected in PROBE_AUTHORITIES.items():
        path = project / name
        if not path.is_file() or file_hash(path) != expected:
            raise ProbeError("PROBE_IMPLEMENTATION_AUTHORITY_INTEGRITY_FAILURE")
        result[name] = expected
    clarification = project / PROBE_CLARIFICATION_001_NAME
    if not clarification.is_file() or file_hash(clarification) != PROBE_CLARIFICATION_001_SHA256:
        raise ProbeError("PROBE_CLARIFICATION_AUTHORITY_INTEGRITY_FAILURE")
    receipt = project / "oc3/environment_setup/AMENDMENT_003_REPLAY_RECEIPT.json"
    if not receipt.is_file() or file_hash(receipt) != AMENDMENT_003_RECEIPT_SHA256:
        raise ProbeError("PROBE_IMPLEMENTATION_AUTHORITY_INTEGRITY_FAILURE")
    env_path = project / "oc3/environment_setup/ENVIRONMENT.json"
    try:
        env = json.loads(env_path.read_text(encoding="utf-8"))
        actual = digest(canonical(env["state"]))
    except (OSError, KeyError, ValueError, TypeError):
        raise ProbeError("PROBE_IMPLEMENTATION_AUTHORITY_INTEGRITY_FAILURE") from None
    if actual != ENVIRONMENT_FINGERPRINT:
        raise ProbeError("PROBE_IMPLEMENTATION_AUTHORITY_INTEGRITY_FAILURE")
    return result


def probe_caps(overrides: Mapping[str, int] | None = None) -> dict[str, int]:
    values = dict(CAPS)
    for key, value in (overrides or {}).items():
        if key not in CAPS or isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > CAPS[key]:
            raise ProbeError("PROBE_LIMIT_INCREASE_OR_INVALID")
        if key not in ("retries", "gpu") and value == 0:
            raise ProbeError("PROBE_LIMIT_INCREASE_OR_INVALID")
        values[key] = value
    return values


def _validate_url(resource: ProbeResource, url: str) -> None:
    if url != resource.url:
        raise ProbeError("PROBE_RESOURCE_NOT_ALLOWLISTED")
    parsed = urlsplit(url)
    expected = urlsplit(resource.url)
    if (parsed.scheme != "https" or parsed.hostname != expected.hostname or parsed.query or parsed.fragment
            or parsed.username or parsed.password or parsed.port not in (None, 443)):
        raise ProbeError("PROBE_RESOURCE_NOT_ALLOWLISTED")


@dataclass(frozen=True)
class RequestIdentity:
    role: str
    url: str
    method: str
    byte_range: str | None
    probe_spec_sha256: str = PROBE_SPEC_SHA256
    clarification_001_sha256: str = PROBE_CLARIFICATION_001_SHA256

    def __post_init__(self) -> None:
        if self.role not in RESOURCES:
            raise ProbeError("PROBE_RESOURCE_NOT_ALLOWLISTED")
        resource = RESOURCES[self.role]
        _validate_url(resource, self.url)
        if self.method not in ("HEAD", "GET"):
            raise ProbeError("PROBE_METHOD_NOT_ALLOWED")
        if resource.kind == "fits" and self.method == "GET" and self.byte_range not in RANGES:
            raise ProbeError("PROBE_RANGE_NOT_ALLOWED")
        if self.method == "HEAD" and self.byte_range is not None:
            raise ProbeError("PROBE_RANGE_NOT_ALLOWED")
        if resource.kind == "manifest" and self.byte_range is not None:
            raise ProbeError("PROBE_RANGE_NOT_ALLOWED")
        if self.probe_spec_sha256 != PROBE_SPEC_SHA256:
            raise ProbeError("PROBE_SPEC_BINDING_MISMATCH")
        if self.clarification_001_sha256 != PROBE_CLARIFICATION_001_SHA256:
            raise ProbeError("PROBE_CLARIFICATION_BINDING_MISMATCH")

    @property
    def key(self) -> str:
        return digest(canonical({"role": self.role, "url": self.url, "method": self.method,
                                 "range": self.byte_range, "probe_spec_sha256": self.probe_spec_sha256,
                                 "clarification_001_sha256": self.clarification_001_sha256}))


class Response(Protocol):
    status: int
    headers: Mapping[str, str]
    final_url: str
    def read(self, n: int) -> bytes: ...
    def close(self) -> None: ...


class Transport(Protocol):
    def open(self, identity: RequestIdentity) -> Response: ...


class OfflineTransport:
    def open(self, identity: RequestIdentity) -> Response:
        raise ProbeError("PROBE_OFFLINE_NETWORK_FORBIDDEN")


class HTTPProbeResponse:
    def __init__(self, connection: http.client.HTTPSConnection, response: http.client.HTTPResponse, final_url: str):
        self._connection = connection
        self._response = response
        self.status = response.status
        self.headers = {k.lower(): v for k, v in response.getheaders()}
        self.final_url = final_url

    def read(self, n: int) -> bytes:
        return self._response.read(n)

    def close(self) -> None:
        self._response.close()
        self._connection.close()


class HTTPProbeTransport:
    """Network-capable boundary. Construct only after validated human authorization."""
    def __init__(self, authorized: bool):
        if authorized is not True:
            raise ProbeError("PROBE_HUMAN_AUTHORIZATION_REQUIRED")

    def open(self, identity: RequestIdentity) -> HTTPProbeResponse:
        resource = RESOURCES[identity.role]
        _validate_url(resource, identity.url)
        parsed = urlsplit(identity.url)
        headers = {"Accept-Encoding": "identity"}
        if identity.byte_range is not None:
            headers["Range"] = identity.byte_range
        connection = http.client.HTTPSConnection(parsed.hostname, port=443, timeout=30,
                                                   context=ssl.create_default_context())
        try:
            connection.request(identity.method, parsed.path, headers=headers)
            response = connection.getresponse()
        except BaseException:
            connection.close()
            raise
        return HTTPProbeResponse(connection, response, identity.url)


class MemoryResponse:
    """In-memory response fixture. Never opens a socket."""
    def __init__(self, body: bytes = b"", *, status: int = 200, headers: Mapping[str, str] | None = None,
                 final_url: str = "https://synthetic.invalid/", fail_after: int | None = None):
        self._body = bytes(body)
        self._position = 0
        self.status = status
        self.headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
        self.final_url = final_url
        self.fail_after = fail_after

    @property
    def position(self) -> int:
        return self._position

    def read(self, n: int) -> bytes:
        if self.fail_after is not None and self._position >= self.fail_after:
            raise OSError("SYNTHETIC_PARTIAL_BODY")
        end = min(len(self._body), self._position + n)
        if self.fail_after is not None:
            end = min(end, self.fail_after)
        value = self._body[self._position:end]
        self._position = end
        return value

    def close(self) -> None:
        pass


class MemoryTransport:
    def __init__(self, responses: Iterable[Response]):
        self.responses = list(responses)
        self.calls: list[RequestIdentity] = []

    def open(self, identity: RequestIdentity) -> Response:
        self.calls.append(identity)
        if not self.responses:
            raise AssertionError("SYNTHETIC_RESPONSE_MISSING")
        return self.responses.pop(0)


@dataclass(frozen=True)
class ProbeBinding:
    probe_spec_sha256: str
    implementation_aggregate: str
    environment_fingerprint: str
    human_authorization_sha256: str
    attempt_id: str
    clarification_001_sha256: str = PROBE_CLARIFICATION_001_SHA256

    def __post_init__(self) -> None:
        for value in (self.probe_spec_sha256, self.implementation_aggregate,
                      self.environment_fingerprint, self.human_authorization_sha256):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ProbeError("PROBE_LEDGER_BINDING_INVALID")
        if self.probe_spec_sha256 != PROBE_SPEC_SHA256 or self.environment_fingerprint != ENVIRONMENT_FINGERPRINT:
            raise ProbeError("PROBE_LEDGER_BINDING_INVALID")
        if self.clarification_001_sha256 != PROBE_CLARIFICATION_001_SHA256:
            raise ProbeError("PROBE_LEDGER_BINDING_INVALID")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", self.attempt_id):
            raise ProbeError("PROBE_LEDGER_BINDING_INVALID")

    def as_dict(self) -> dict[str, str]:
        return {"probe_spec_sha256": self.probe_spec_sha256,
                "implementation_aggregate": self.implementation_aggregate,
                "environment_fingerprint": self.environment_fingerprint,
                "human_authorization_sha256": self.human_authorization_sha256,
                "attempt_id": self.attempt_id,
                "clarification_001_sha256": self.clarification_001_sha256}


class ProbeLedger:
    """Separate SQLite probe ledger. It is never used by OC-3 production code."""
    COUNTERS = ("requests", "http_body_bytes", "fits_body_bytes", "manifest_body_bytes", "disk_bytes", "io_bytes")

    def __init__(self, path: Path, binding: ProbeBinding, caps: Mapping[str, int] | None = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.caps = probe_caps(caps)
        self.db = sqlite3.connect(self.path, timeout=0, isolation_level=None)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS counters(key TEXT PRIMARY KEY,value INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY,identity TEXT NOT NULL,role TEXT NOT NULL,
          method TEXT NOT NULL,byte_range TEXT,max_body INTEGER NOT NULL,actual INTEGER NOT NULL DEFAULT 0,
          state TEXT NOT NULL,retry_of INTEGER);
        CREATE TABLE IF NOT EXISTS chunks(role TEXT NOT NULL,byte_range TEXT NOT NULL,sha256 TEXT NOT NULL,
          size INTEGER NOT NULL,verified INTEGER NOT NULL,PRIMARY KEY(role,byte_range));
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT NOT NULL);
        """)
        binding_json = canonical(binding.as_dict()).decode("utf-8")
        cap_json = canonical(self.caps).decode("utf-8")
        with self.transaction():
            old = self.db.execute("SELECT value FROM config WHERE key='binding'").fetchone()
            if old and old[0] != binding_json:
                raise ProbeError("PROBE_LEDGER_BINDING_CONFLICT")
            old_caps = self.db.execute("SELECT value FROM config WHERE key='caps'").fetchone()
            if old_caps:
                previous = json.loads(old_caps[0])
                self.caps = {key: min(self.caps[key], previous[key]) for key in CAPS}
                cap_json = canonical(self.caps).decode("utf-8")
            self.db.execute("INSERT OR IGNORE INTO config VALUES('binding',?)", (binding_json,))
            self.db.execute("INSERT OR REPLACE INTO config VALUES('caps',?)", (cap_json,))
            for key in self.COUNTERS:
                self.db.execute("INSERT OR IGNORE INTO counters VALUES(?,0)", (key,))

    @contextlib.contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def close(self) -> None:
        self.db.close()

    def count(self, key: str) -> int:
        row = self.db.execute("SELECT value FROM counters WHERE key=?", (key,)).fetchone()
        if row is None:
            raise ProbeError("PROBE_LEDGER_COUNTER_UNKNOWN")
        return int(row[0])

    def _increment(self, key: str, amount: int) -> None:
        if amount < 0 or self.count(key) + amount > self.caps[key]:
            raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
        self.db.execute("UPDATE counters SET value=value+? WHERE key=?", (amount, key))

    def reserve(self, identity: RequestIdentity, max_body: int, *, retry_of: int | None = None,
                fault: str | None = None) -> int:
        if not isinstance(max_body, int) or max_body < 0:
            raise ProbeError("PROBE_UNBOUNDED_RESPONSE")
        if max_body > (65536 if RESOURCES[identity.role].kind == "fits" and identity.method == "GET" else 8 * 2**20):
            raise ProbeError("PROBE_UNBOUNDED_RESPONSE")
        request_id = 0
        with self.transaction():
            if fault == "before_commit":
                raise OSError("SYNTHETIC_PRE_COMMIT_CRASH")
            if self.db.execute("SELECT 1 FROM requests WHERE state='RESERVED'").fetchone():
                raise ProbeError("PROBE_CONCURRENCY_LIMIT")
            if self.count("requests") + 1 > self.caps["requests"]:
                raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
            kind = RESOURCES[identity.role].kind
            category = "fits_body_bytes" if kind == "fits" else "manifest_body_bytes"
            if self.count("http_body_bytes") + max_body > self.caps["http_body_bytes"]:
                raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
            if self.count(category) + max_body > self.caps[category]:
                raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
            if kind == "fits":
                consumed = self.db.execute("SELECT COALESCE(SUM(actual),0) FROM requests WHERE role=?", (identity.role,)).fetchone()[0]
                if int(consumed) + max_body > self.caps["fits_resource_bytes"]:
                    raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
            prior = self.db.execute("SELECT id,identity FROM requests WHERE identity=? ORDER BY id", (identity.key,)).fetchall()
            if len(prior) >= 1 + self.caps["retries"]:
                raise ProbeError("PROBE_RETRY_LIMIT_STOP")
            if prior and retry_of is None:
                raise ProbeError("PROBE_RETRY_IDENTITY_REQUIRED")
            if retry_of is not None:
                row = self.db.execute("SELECT identity,state FROM requests WHERE id=?", (retry_of,)).fetchone()
                if not row or row[0] != identity.key or row[1] not in ("FAILED", "CRASH_CHARGED", "COMPLETE"):
                    raise ProbeError("PROBE_RETRY_IDENTITY_MISMATCH")
            self._increment("requests", 1)
            cursor = self.db.execute("INSERT INTO requests(identity,role,method,byte_range,max_body,state,retry_of) VALUES(?,?,?,?,?,'RESERVED',?)",
                                     (identity.key, identity.role, identity.method, identity.byte_range, max_body, retry_of))
            request_id = int(cursor.lastrowid)
        if fault == "after_commit":
            raise OSError("SYNTHETIC_POST_COMMIT_CRASH")
        return request_id

    def charge_response(self, request_id: int, amount: int) -> None:
        if not isinstance(amount, int) or amount < 0:
            raise ProbeError("PROBE_LEDGER_CHARGE_INVALID")
        with self.transaction():
            row = self.db.execute("SELECT role,max_body,actual,state FROM requests WHERE id=?", (request_id,)).fetchone()
            if not row or row[3] != "RESERVED":
                raise ProbeError("PROBE_LEDGER_REQUEST_STATE")
            role, max_body, actual, _ = row
            if actual + amount > max_body:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            kind = RESOURCES[role].kind
            self._increment("http_body_bytes", amount)
            category = "fits_body_bytes" if kind == "fits" else "manifest_body_bytes"
            self._increment(category, amount)
            if kind == "fits":
                consumed = self.db.execute("SELECT COALESCE(SUM(actual),0) FROM requests WHERE role=?", (role,)).fetchone()[0]
                if int(consumed) + amount > self.caps["fits_resource_bytes"]:
                    raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
            self.db.execute("UPDATE requests SET actual=actual+? WHERE id=?", (amount, request_id))

    def charge_local(self, *, disk: int = 0, io: int = 0) -> None:
        with self.transaction():
            self._increment("disk_bytes", disk)
            self._increment("io_bytes", io)

    def finish(self, request_id: int, state: str) -> None:
        if state not in ("COMPLETE", "FAILED"):
            raise ProbeError("PROBE_LEDGER_REQUEST_STATE")
        with self.transaction():
            row = self.db.execute("SELECT state FROM requests WHERE id=?", (request_id,)).fetchone()
            if not row or row[0] != "RESERVED":
                raise ProbeError("PROBE_LEDGER_REQUEST_STATE")
            self.db.execute("UPDATE requests SET state=? WHERE id=?", (state, request_id))

    def recover(self) -> int:
        with self.transaction():
            rows = self.db.execute("SELECT id,role,max_body,actual FROM requests WHERE state='RESERVED'").fetchall()
            for request_id, role, maximum, actual in rows:
                remainder = int(maximum) - int(actual)
                if remainder:
                    self._increment("http_body_bytes", remainder)
                    category = "fits_body_bytes" if RESOURCES[role].kind == "fits" else "manifest_body_bytes"
                    self._increment(category, remainder)
                    self.db.execute("UPDATE requests SET actual=max_body WHERE id=?", (request_id,))
            self.db.execute("UPDATE requests SET state='CRASH_CHARGED' WHERE state='RESERVED'")
            return len(rows)

    def last_attempt(self, identity: RequestIdentity) -> int | None:
        row = self.db.execute("SELECT id FROM requests WHERE identity=? ORDER BY id DESC LIMIT 1", (identity.key,)).fetchone()
        return int(row[0]) if row else None

    def register_chunk(self, role: str, byte_range: str, body: bytes, verified: bool = True) -> None:
        if role not in FITS_ROLES or byte_range not in RANGES:
            raise ProbeError("PROBE_RANGE_NOT_ALLOWED")
        value = (digest(body), len(body), int(bool(verified)))
        with self.transaction():
            old = self.db.execute("SELECT sha256,size,verified FROM chunks WHERE role=? AND byte_range=?", (role, byte_range)).fetchone()
            if old and tuple(old) != value:
                raise ProbeError("PROBE_RESUME_CHUNK_CORRUPT")
            self.db.execute("INSERT OR IGNORE INTO chunks VALUES(?,?,?,?,?)", (role, byte_range, *value))

    def verified_chunks(self, role: str) -> list[tuple[str, str, int]]:
        rows = self.db.execute("SELECT byte_range,sha256,size FROM chunks WHERE role=? AND verified=1", (role,)).fetchall()
        by_range = {row[0]: row for row in rows}
        result = []
        for byte_range in RANGES:
            if byte_range not in by_range:
                break
            result.append(tuple(by_range[byte_range]))
        return result

    def event(self, code: str) -> None:
        with self.transaction():
            self.db.execute("INSERT INTO events(code) VALUES(?)", (code,))

    def summary(self) -> dict:
        return {"counters": {key: self.count(key) for key in self.COUNTERS},
                "requests": [dict(zip(("id", "identity", "role", "method", "range", "max_body", "actual", "state", "retry_of"), row))
                             for row in self.db.execute("SELECT id,identity,role,method,byte_range,max_body,actual,state,retry_of FROM requests ORDER BY id")],
                "events": [row[0] for row in self.db.execute("SELECT code FROM events ORDER BY seq")]}


_INTEGER = re.compile(r"^[+-]?\d+$")
_FLOAT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EDed][+-]?\d+)?$")
_TFORM = re.compile(r"^(?:\d+)?[LXBIJKAEDCMPQ](?:\([^)]*\))?$")
_COLUMN_KEY = re.compile(r"^(TTYPE|TFORM|TUNIT|TNULL|TSCAL|TZERO)(\d+)$")
_NAXIS_KEY = re.compile(r"^NAXIS(\d+)$")
_MAX_STRUCTURAL = 2**63 - 1


def _split_value(text: str) -> str:
    quoted = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == "'":
            if quoted and index + 1 < len(text) and text[index + 1] == "'":
                index += 2
                continue
            quoted = not quoted
        elif char == "/" and not quoted:
            return text[:index].rstrip()
        index += 1
    return text.rstrip()


def _card_value(card: str):
    if len(card) != 80 or card[8:10] != "= ":
        raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
    raw = _split_value(card[10:]).strip()
    if not raw:
        raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
    if raw.startswith("'"):
        if not raw.endswith("'"):
            raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
        return raw[1:-1].replace("''", "'").rstrip()
    if raw in ("T", "F"):
        return raw == "T"
    if _INTEGER.fullmatch(raw):
        return int(raw)
    if _FLOAT.fullmatch(raw):
        return float(raw.replace("D", "E").replace("d", "e"))
    raise ProbeError("PROBE_MALFORMED_FITS_HEADER")


def _checked_product(values: Iterable[int]) -> int:
    result = 1
    for value in values:
        if not isinstance(value, int) or value < 0:
            raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
        if value and result > _MAX_STRUCTURAL // value:
            raise ProbeError("PROBE_FITS_ARITHMETIC_OVERFLOW")
        result *= value
    return result


@dataclass(frozen=True)
class ColumnContract:
    index: int
    ttype: str
    tform: str
    tunit: object | None = None
    tnull: object | None = None
    tscal: object | None = None
    tzero: object | None = None

    def as_dict(self) -> dict:
        return {"index": self.index, "ttype": self.ttype, "tform": self.tform,
                "tunit": self.tunit, "tnull": self.tnull, "tscal": self.tscal, "tzero": self.tzero}


@dataclass(frozen=True)
class FITSHeaderContract:
    hdu_index: int
    header_start: int
    header_end: int
    xtension: str
    extname: str | None
    bitpix: int
    naxis: int
    naxis1: int
    naxis2: int
    pcount: int
    gcount: int
    tfields: int
    columns: tuple[ColumnContract, ...]
    checksum: str | None
    datasum: str | None
    header_sha256: str

    def as_dict(self) -> dict:
        return {"hdu_index": self.hdu_index, "header_start": self.header_start, "header_end": self.header_end,
                "xtension": self.xtension, "extname": self.extname, "bitpix": self.bitpix,
                "naxis": self.naxis, "naxis1": self.naxis1, "naxis2": self.naxis2,
                "pcount": self.pcount, "gcount": self.gcount, "tfields": self.tfields,
                "columns": [column.as_dict() for column in self.columns],
                "checksum": {"value": self.checksum, "verified": False} if self.checksum is not None else None,
                "datasum": {"value": self.datasum, "verified": False} if self.datasum is not None else None,
                "header_sha256": self.header_sha256}


@dataclass(frozen=True)
class _ParsedHeader:
    start: int
    end: int
    values: Mapping[str, object]
    raw: bytes


def _parse_header(data: bytes, start: int) -> _ParsedHeader:
    if start < 0 or start % 2880:
        raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
    if len(data) < start + 2880:
        raise NeedMoreHeaderData()
    values: dict[str, object] = {}
    end_card: int | None = None
    position = start
    while position + 80 <= len(data):
        raw = data[position:position + 80]
        try:
            card = raw.decode("ascii")
        except UnicodeDecodeError:
            raise ProbeError("PROBE_MALFORMED_FITS_HEADER") from None
        key = card[:8].strip()
        if key == "END":
            if card[8:].strip():
                raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
            end_card = position + 80
            break
        if key:
            structural = (key in {"SIMPLE", "XTENSION", "BITPIX", "NAXIS", "PCOUNT", "GCOUNT", "TFIELDS",
                                      "EXTNAME", "CHECKSUM", "DATASUM"}
                          or _NAXIS_KEY.fullmatch(key) is not None or _COLUMN_KEY.fullmatch(key) is not None)
            if structural:
                if key in values:
                    raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
                values[key] = _card_value(card)
        position += 80
    if end_card is None:
        if len(data) - start >= 256 * 2**10:
            raise ProbeError("PROBE_MISSING_FITS_END")
        raise NeedMoreHeaderData()
    end = ((end_card + 2879) // 2880) * 2880
    if len(data) < end:
        raise NeedMoreHeaderData()
    if any(byte != 32 for byte in data[end_card:end]):
        raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
    return _ParsedHeader(start, end, MappingProxyType(values), data[start:end])


def _require_int(values: Mapping[str, object], key: str, *, minimum: int | None = None) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or (minimum is not None and value < minimum):
        raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
    return value


def _payload_size(header: _ParsedHeader) -> int:
    values = header.values
    bitpix = abs(_require_int(values, "BITPIX"))
    if bitpix not in (8, 16, 32, 64):
        raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
    naxis = _require_int(values, "NAXIS", minimum=0)
    if naxis > 999:
        raise ProbeError("PROBE_FITS_ARITHMETIC_OVERFLOW")
    xtension = values.get("XTENSION")
    pcount = _require_int(values, "PCOUNT", minimum=0) if "PCOUNT" in values else 0
    gcount = _require_int(values, "GCOUNT", minimum=1) if "GCOUNT" in values else 1
    if xtension == "BINTABLE":
        row = _require_int(values, "NAXIS1", minimum=0)
        rows = _require_int(values, "NAXIS2", minimum=0)
        base = _checked_product((row, rows))
        if pcount > _MAX_STRUCTURAL - base:
            raise ProbeError("PROBE_FITS_ARITHMETIC_OVERFLOW")
        return _checked_product((base + pcount, gcount))
    axes = [_require_int(values, f"NAXIS{index}", minimum=0) for index in range(1, naxis + 1)]
    pixels = 0 if naxis == 0 else _checked_product(axes)
    if pcount > _MAX_STRUCTURAL - pixels:
        raise ProbeError("PROBE_FITS_ARITHMETIC_OVERFLOW")
    return _checked_product((pixels + pcount, gcount, bitpix // 8))


def parse_target_bintable(data: bytes) -> FITSHeaderContract:
    primary = _parse_header(data, 0)
    if primary.values.get("SIMPLE") is not True:
        raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
    if _payload_size(primary) != 0:
        raise InterveningPayload()
    table = _parse_header(data, primary.end)
    values = table.values
    if values.get("XTENSION") != "BINTABLE":
        raise ProbeError("PROBE_TARGET_NOT_BINTABLE")
    bitpix = _require_int(values, "BITPIX")
    naxis = _require_int(values, "NAXIS", minimum=0)
    naxis1 = _require_int(values, "NAXIS1", minimum=0)
    naxis2 = _require_int(values, "NAXIS2", minimum=0)
    pcount = _require_int(values, "PCOUNT", minimum=0)
    gcount = _require_int(values, "GCOUNT", minimum=1)
    tfields = _require_int(values, "TFIELDS", minimum=0)
    if tfields > 999:
        raise ProbeError("PROBE_FITS_ARITHMETIC_OVERFLOW")
    _payload_size(table)
    columns = []
    for index in range(1, tfields + 1):
        ttype = values.get(f"TTYPE{index}")
        tform = values.get(f"TFORM{index}")
        if not isinstance(ttype, str) or not ttype or not isinstance(tform, str) or not _TFORM.fullmatch(tform):
            raise ProbeError("PROBE_MALFORMED_FITS_HEADER")
        columns.append(ColumnContract(index, ttype, tform, values.get(f"TUNIT{index}"),
                                      values.get(f"TNULL{index}"), values.get(f"TSCAL{index}"), values.get(f"TZERO{index}")))
    return FITSHeaderContract(1, table.start, table.end, "BINTABLE",
                              values.get("EXTNAME") if isinstance(values.get("EXTNAME"), str) else None,
                              bitpix, naxis, naxis1, naxis2, pcount, gcount, tfields,
                              tuple(columns),
                              values.get("CHECKSUM") if isinstance(values.get("CHECKSUM"), str) else None,
                              values.get("DATASUM") if isinstance(values.get("DATASUM"), str) else None,
                              digest(table.raw))


class UncompressedHeaderExtractor:
    def __init__(self):
        self._header = bytearray()
        self.contract: FITSHeaderContract | None = None
        self.wire_bytes_received = 0

    @property
    def header_bytes(self) -> bytes:
        return bytes(self._header)

    def feed(self, chunk: bytes) -> bool:
        self.wire_bytes_received += len(chunk)
        if self.contract is not None:
            return True
        position = 0
        while position < len(chunk) and self.contract is None:
            needed = 2880 - (len(self._header) % 2880)
            take = min(needed, len(chunk) - position)
            self._header.extend(chunk[position:position + take])
            position += take
            if len(self._header) % 2880 == 0:
                try:
                    self.contract = parse_target_bintable(bytes(self._header))
                except NeedMoreHeaderData:
                    pass
        return self.contract is not None


class GzipHeaderExtractor:
    def __init__(self):
        self._decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        self._pending = b""
        self._header = bytearray()
        self.contract: FITSHeaderContract | None = None
        self.wire_bytes_received = 0
        self.compressed_bytes_consumed = 0
        self.uncompressed_header_bytes_emitted = 0

    @property
    def header_bytes(self) -> bytes:
        return bytes(self._header)

    def feed(self, chunk: bytes) -> bool:
        if self.contract is not None:
            raise ProbeError("PROBE_ROW_OBSERVATION_FORBIDDEN")
        self.wire_bytes_received += len(chunk)
        self._pending += bytes(chunk)
        while self._pending and self.contract is None:
            needed = 2880 - (len(self._header) % 2880)
            before = len(self._pending)
            try:
                output = self._decoder.decompress(self._pending, needed)
            except zlib.error:
                raise ProbeError("PROBE_MALFORMED_FITS_HEADER") from None
            self._pending = self._decoder.unconsumed_tail
            consumed = before - len(self._pending)
            self.compressed_bytes_consumed += consumed
            if output:
                if len(output) > needed:
                    raise ProbeError("PROBE_ROW_OBSERVATION_FORBIDDEN")
                self._header.extend(output)
                self.uncompressed_header_bytes_emitted += len(output)
            if len(self._header) % 2880 == 0 and self._header:
                try:
                    self.contract = parse_target_bintable(bytes(self._header))
                except NeedMoreHeaderData:
                    pass
            if not output and consumed == 0:
                break
            if self._decoder.eof and self.contract is None and not self._pending:
                # A structurally valid gzip representation may end before the
                # required FITS BINTABLE header is complete.  Transport EOF is
                # classified by ProbeEngine once the known representation
                # length has been exhausted; it is not evidence that gzip or
                # the bytes already emitted are malformed.
                break
        return self.contract is not None


def reconstruct_gzip_header(chunks: Iterable[bytes]) -> GzipHeaderExtractor:
    extractor = GzipHeaderExtractor()
    for chunk in chunks:
        if extractor.feed(chunk):
            break
    return extractor


@dataclass(frozen=True)
class TransportEvidence:
    schema_version: int
    role: str
    requested_url: str
    final_url: str
    status: int
    content_length: int | None
    content_type: str | None
    etag: str | None
    last_modified: str | None
    accept_ranges: str | None
    compression: str
    wire_bytes_received: int
    compressed_bytes_consumed: int | None
    uncompressed_header_bytes_emitted: int
    observed_utc: str

    def as_dict(self) -> dict:
        return {field.name: getattr(self, field.name) for field in self.__dataclass_fields__.values()}


@dataclass(frozen=True)
class PhysicalContractCandidate:
    schema_version: int
    role: str
    requested_url: str
    final_url: str
    compression: str
    content_length: int | None
    content_type: str | None
    etag: str | None
    last_modified: str | None
    header: FITSHeaderContract
    provider_manifest_sha256: str | None
    evidence_sha256: tuple[str, ...]

    def as_dict(self) -> dict:
        return {"schema_version": self.schema_version, "role": self.role,
                "requested_url": self.requested_url, "final_url": self.final_url,
                "compression": self.compression, "content_length": self.content_length,
                "content_type": self.content_type, "etag": self.etag,
                "last_modified": self.last_modified, "header": self.header.as_dict(),
                "provider_manifest_sha256": self.provider_manifest_sha256,
                "evidence_sha256": list(self.evidence_sha256)}

    def canonical_bytes(self) -> bytes:
        return canonical(self.as_dict()) + b"\n"

    def sha256(self) -> str:
        return digest(self.canonical_bytes())


def parse_checksum_manifest(body: bytes, resource: ProbeResource) -> str:
    if resource.kind != "manifest" or not resource.expected_name or not resource.expected_sha256:
        raise ProbeError("PROBE_MANIFEST_ROLE_INVALID")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        raise ProbeError("PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP") from None
    matches: list[str] = []
    same_basename = 0
    for raw in text.splitlines():
        if not raw.strip():
            continue
        match = re.fullmatch(r"([0-9A-Fa-f]{64})[ \t]+\*?([^\r\n]+)", raw)
        if not match:
            raise ProbeError("PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP")
        value, path = match.group(1).lower(), match.group(2)
        if Path(path).name == resource.expected_name:
            same_basename += 1
        if path == resource.expected_name:
            matches.append(value)
    if same_basename != 1 or len(matches) != 1 or matches[0] != resource.expected_sha256:
        raise ProbeError("PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP")
    return matches[0]


def patch_checksum_status() -> str:
    return "PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND"


def brickid_outcome(contracts: Mapping[str, FITSHeaderContract]) -> str:
    expected = {"ROOT_SUMMARY": "J", "NORTH_SUMMARY": "I", "SOUTH_SUMMARY": "I"}
    if set(expected) - set(contracts):
        return "BRICKID_PHYSICAL_LAYOUT_UNRESOLVED"
    for role, required in expected.items():
        matches = [column for column in contracts[role].columns if column.ttype.casefold() == "brickid"]
        if len(matches) != 1:
            return "BRICKID_PHYSICAL_LAYOUT_UNRESOLVED"
        if matches[0].tform != required:
            return "BRICKID_PHYSICAL_LAYOUT_CONFLICTS_WITH_DOCUMENTATION"
    return "BRICKID_PHYSICAL_LAYOUT_SUPPORTS_DOCUMENTATION"


class RowObservationTripwire:
    @staticmethod
    def _forbidden(*args, **kwargs):
        raise ProbeError("PROBE_ROW_OBSERVATION_FORBIDDEN")

    hdu_data = _forbidden
    table_read = _forbidden
    provider_schema_decode = _forbidden
    resolve_bootstrap_bricks = _forbidden
    decode_row = _forbidden
    decode_cell = _forbidden
    selection_helper = _forbidden


def terminal_outcome(events: Iterable[str]) -> str:
    values = set(events)
    mapping = {
        "PROBE_ROW_OBSERVATION_FORBIDDEN": "PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE",
        "PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE": "PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE",
        "PROBE_TRANSPORT_INTEGRITY_FAILURE": "PROBE_TRANSPORT_INTEGRITY_FAILURE",
        "PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP": "PROBE_PROVIDER_DOCUMENTATION_CONFLICT",
        "PROBE_PROVIDER_DOCUMENTATION_CONFLICT": "PROBE_PROVIDER_DOCUMENTATION_CONFLICT",
        "PROBE_RANGE_UNAVAILABLE_STOP": "PROBE_RANGE_UNAVAILABLE_STOP",
        "PHYSICAL_CONTRACT_HEADER_CAP_INSUFFICIENT": "PROBE_HEADER_CAP_INSUFFICIENT",
        "PROBE_HEADER_CAP_INSUFFICIENT": "PROBE_HEADER_CAP_INSUFFICIENT",
        "INTERVENING_DATA_PAYLOAD_STOP": "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED",
        "PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE": "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED",
        "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED": "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED",
        "PROBE_PHYSICAL_CONTRACTS_RESOLVED": "PROBE_PHYSICAL_CONTRACTS_RESOLVED",
    }
    terminals = {mapping[value] for value in values if value in mapping}
    if not terminals:
        return "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED"
    return min(terminals, key=TERMINAL_PRECEDENCE.index)


class ProbeEngine:
    def __init__(self, transport: Transport, ledger: ProbeLedger, evidence_root: Path | None = None,
                 guard: "ProbeRuntimeGuard | None" = None):
        self.transport = transport
        self.ledger = ledger
        self.evidence_root = Path(evidence_root) if evidence_root is not None else None
        self.guard = guard
        self._next_range = {role: 0 for role in FITS_ROLES}
        self._total_length: dict[str, int] = {}
        self._head: dict[str, dict[str, str]] = {}
        self._range_identity: dict[str, dict[str, str]] = {}

    @staticmethod
    def _headers(response: Response) -> dict[str, str]:
        return {str(k).lower(): str(v) for k, v in response.headers.items()}

    @staticmethod
    def _transport_identity(identity: RequestIdentity, response: Response, headers: Mapping[str, str]) -> None:
        if response.final_url != identity.url:
            raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
        if headers.get("content-encoding", "identity").lower() != "identity":
            raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")

    def head(self, role: str) -> dict[str, str]:
        resource = RESOURCES[role]
        cache = self.evidence_root / "transport" / f"{role}.head.json" if self.evidence_root else None
        if cache is not None and cache.is_file():
            raw = cache.read_bytes()
            self.ledger.charge_local(io=len(raw))
            try:
                saved = json.loads(raw)
            except (UnicodeDecodeError, ValueError):
                raise ProbeError("PROBE_RESUME_CHUNK_CORRUPT") from None
            if raw != canonical(saved) + b"\n" or saved.get("role") != role or saved.get("url") != resource.url or not isinstance(saved.get("headers"), dict):
                raise ProbeError("PROBE_RESUME_CHUNK_CORRUPT")
            self._head[role] = {str(k): str(v) for k, v in saved["headers"].items()}
            return self._head[role]
        identity = RequestIdentity(role, resource.url, "HEAD", None)
        attempt = self.ledger.reserve(identity, 0, retry_of=self.ledger.last_attempt(identity))
        response = None
        try:
            if self.guard: self.guard.check()
            response = self.transport.open(identity)
            headers = self._headers(response)
            self._transport_identity(identity, response, headers)
            if response.status != 200:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            self._head[role] = headers
            if cache is not None:
                _write_evidence(cache, {"role": role, "url": resource.url, "headers": headers}, self.ledger)
            self.ledger.finish(attempt, "COMPLETE")
            return headers
        except BaseException:
            try:
                self.ledger.finish(attempt, "FAILED")
            except ProbeError:
                pass
            raise
        finally:
            if response is not None:
                response.close()

    def range_get(self, role: str, index: int) -> bytes:
        resource = RESOURCES[role]
        if resource.kind != "fits" or index != self._next_range[role] or index >= len(RANGES):
            raise ProbeError("PROBE_RANGE_NOT_ALLOWED")
        start = index * 65536
        requested_end = start + 65535
        if role in self._total_length and start >= self._total_length[role]:
            raise ProbeError("PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE")
        byte_range = RANGES[index]
        identity = RequestIdentity(role, resource.url, "GET", byte_range)
        attempt = self.ledger.reserve(identity, 65536, retry_of=self.ledger.last_attempt(identity))
        response = None
        try:
            if self.guard: self.guard.check()
            response = self.transport.open(identity)
            headers = self._headers(response)
            self._transport_identity(identity, response, headers)
            if response.status in (200, 416):
                raise ProbeError("PROBE_RANGE_UNAVAILABLE_STOP")
            if response.status != 206:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", headers.get("content-range", ""))
            if not match:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            actual_start, actual_end, total = map(int, match.groups())
            if total <= 0 or total > 2**63 - 1 or start >= total:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            expected_end = min(requested_end, total - 1)
            if (actual_start, actual_end) != (start, expected_end):
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            if role in self._total_length and self._total_length[role] != total:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            expected_length = expected_end - start + 1
            if "content-length" not in headers or not headers["content-length"].isdigit() or int(headers["content-length"]) != expected_length:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            head_length = self._head.get(role, {}).get("content-length")
            if head_length is not None and (not head_length.isdigit() or int(head_length) != total):
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            for identity_header in ("etag", "last-modified"):
                expected_identity = self._head.get(role, {}).get(identity_header)
                if expected_identity is not None and headers.get(identity_header) != expected_identity:
                    raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
                prior_identity = self._range_identity.get(role, {}).get(identity_header)
                if prior_identity is not None and headers.get(identity_header) != prior_identity:
                    raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            body = bytearray()
            while len(body) < expected_length:
                chunk = response.read(min(expected_length - len(body), 16384))
                if not chunk:
                    break
                self.ledger.charge_response(attempt, len(chunk))
                body.extend(chunk)
            if len(body) != expected_length:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            extra = response.read(1)
            if extra:
                self.ledger.charge_response(attempt, len(extra))
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            self._total_length[role] = total
            observed_identity = {key: headers[key] for key in ("etag", "last-modified") if key in headers}
            self._range_identity.setdefault(role, {}).update(observed_identity)
            self._next_range[role] += 1
            value = bytes(body)
            self.ledger.register_chunk(role, byte_range, value)
            if self.evidence_root is not None and resource.compression == "gzip":
                _write_bytes(self.evidence_root / "compressed_prefix" / role / f"{index}.part", value, self.ledger)
            self.ledger.finish(attempt, "COMPLETE")
            return value
        except BaseException:
            try:
                self.ledger.finish(attempt, "FAILED")
            except ProbeError:
                pass
            raise
        finally:
            if response is not None:
                response.close()

    def manifest_get(self, role: str) -> bytes:
        resource = RESOURCES[role]
        if resource.kind != "manifest":
            raise ProbeError("PROBE_MANIFEST_ROLE_INVALID")
        identity = RequestIdentity(role, resource.url, "GET", None)
        remaining = self.ledger.caps["manifest_body_bytes"] - self.ledger.count("manifest_body_bytes")
        attempt = self.ledger.reserve(identity, remaining, retry_of=self.ledger.last_attempt(identity))
        response = None
        try:
            if self.guard: self.guard.check()
            response = self.transport.open(identity)
            headers = self._headers(response)
            self._transport_identity(identity, response, headers)
            if response.status != 200:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            declared = headers.get("content-length")
            if declared is None or not declared.isdigit() or int(declared) > remaining:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            expected = int(declared)
            body = bytearray()
            while len(body) < expected:
                chunk = response.read(min(65536, expected - len(body)))
                if not chunk:
                    break
                self.ledger.charge_response(attempt, len(chunk))
                body.extend(chunk)
            if len(body) != expected:
                raise ProbeError("PROBE_TRANSPORT_INTEGRITY_FAILURE")
            self.ledger.finish(attempt, "COMPLETE")
            return bytes(body)
        except BaseException:
            try:
                self.ledger.finish(attempt, "FAILED")
            except ProbeError:
                pass
            raise
        finally:
            if response is not None:
                response.close()

    def fits_contract(self, role: str) -> tuple[FITSHeaderContract, TransportEvidence]:
        resource = RESOURCES[role]
        headers = self.head(role)
        if headers.get("accept-ranges", "").lower() == "none":
            raise ProbeError("PROBE_RANGE_UNAVAILABLE_STOP")
        if headers.get("content-length", "").isdigit():
            self._total_length[role] = int(headers["content-length"])
        extractor = GzipHeaderExtractor() if resource.compression == "gzip" else UncompressedHeaderExtractor()
        if isinstance(extractor, GzipHeaderExtractor) and self.evidence_root is not None:
            for index, (byte_range, expected_sha, expected_size) in enumerate(self.ledger.verified_chunks(role)):
                path = self.evidence_root / "compressed_prefix" / role / f"{index}.part"
                if not path.is_file():
                    break
                body = path.read_bytes()
                self.ledger.charge_local(io=len(body))
                if byte_range != RANGES[index] or len(body) != expected_size or digest(body) != expected_sha:
                    raise ProbeError("PROBE_RESUME_CHUNK_CORRUPT")
                self._next_range[role] = index + 1
                if extractor.feed(body):
                    break
        for index in range(self._next_range[role], 4):
            if extractor.contract is not None:
                break
            body = self.range_get(role, index)
            if extractor.feed(body):
                break
        if extractor.contract is None:
            if role in self._total_length and self._total_length[role] <= 4 * 65536:
                raise ProbeError("PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE")
            raise ProbeError("PHYSICAL_CONTRACT_HEADER_CAP_INSUFFICIENT")
        evidence = TransportEvidence(1, role, resource.url, resource.url, 206,
                                     int(headers["content-length"]) if headers.get("content-length", "").isdigit() else None,
                                     headers.get("content-type"), headers.get("etag"), headers.get("last-modified"),
                                     headers.get("accept-ranges"), resource.compression,
                                     extractor.wire_bytes_received,
                                     extractor.compressed_bytes_consumed if isinstance(extractor, GzipHeaderExtractor) else None,
                                     len(extractor.header_bytes), datetime.now(timezone.utc).isoformat())
        return extractor.contract, evidence


class ProbeRuntimeGuard:
    def __init__(self, caps: Mapping[str, int] | None = None):
        self.caps = probe_caps(caps)
        self.wall_start = time.monotonic()
        self.cpu_start = time.process_time()

    def check(self) -> None:
        if time.monotonic() - self.wall_start > self.caps["wall_seconds"]:
            raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
        if time.process_time() - self.cpu_start > self.caps["compute_seconds"]:
            raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
        if threading.active_count() > self.caps["threads"]:
            raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
        try:
            import resource
            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            peak_bytes = peak * 1024 if peak < 2**40 else peak
            if peak_bytes > self.caps["ram_bytes"]:
                raise ProbeError("PROBE_RESOURCE_LIMIT_STOP")
        except ImportError:
            pass


def _write_bytes(path: Path, data: bytes, ledger: ProbeLedger) -> None:
    path = Path(path)
    existed = path.exists()
    if existed:
        ledger.charge_local(io=len(data))
    else:
        ledger.charge_local(disk=len(data), io=len(data))
    immutable_write(path, data)


def _write_evidence(path: Path, value, ledger: ProbeLedger) -> None:
    _write_bytes(path, canonical(value) + b"\n", ledger)


def execute_probe(transport: Transport, ledger: ProbeLedger, attempt_root: Path,
                  caps: Mapping[str, int] | None = None) -> str:
    """Execute only after the caller has validated the human authorization."""
    attempt_root = Path(attempt_root)
    guard = ProbeRuntimeGuard(caps)
    engine = ProbeEngine(transport, ledger, attempt_root, guard)
    contracts: dict[str, FITSHeaderContract] = {}
    transport_records: dict[str, dict] = {}
    manifest_records: dict[str, dict] = {}
    provider_hashes: dict[str, str] = {}
    candidates: dict[str, dict] = {}
    events: list[str] = []
    terminal = "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED"
    try:
        for role in FITS_ROLES:
            guard.check()
            contract, evidence = engine.fits_contract(role)
            contracts[role] = contract
            transport_records[role] = evidence.as_dict()
        for role in MANIFEST_ROLES:
            guard.check()
            body = engine.manifest_get(role)
            value = parse_checksum_manifest(body, RESOURCES[role])
            provider_hashes[role] = value
            manifest_records[role] = {"role": role, "url": RESOURCES[role].url,
                                      "entry": RESOURCES[role].expected_name,
                                      "provider_sha256": value, "evidence_sha256": digest(body)}
        role_to_manifest = {"ROOT_SUMMARY": "ROOT_CHECKSUM_MANIFEST",
                            "NORTH_SUMMARY": "NORTH_CHECKSUM_MANIFEST",
                            "SOUTH_SUMMARY": "SOUTH_CHECKSUM_MANIFEST"}
        for role, contract in contracts.items():
            evidence = transport_records[role]
            manifest_role = role_to_manifest.get(role)
            evidence_hashes = [digest(canonical(evidence)), contract.header_sha256]
            if manifest_role:
                evidence_hashes.append(manifest_records[manifest_role]["evidence_sha256"])
            candidate = PhysicalContractCandidate(
                1, role, RESOURCES[role].url, evidence["final_url"], RESOURCES[role].compression,
                evidence["content_length"], evidence["content_type"], evidence["etag"], evidence["last_modified"],
                contract, provider_hashes.get(manifest_role), tuple(evidence_hashes))
            candidates[role] = {"candidate": candidate.as_dict(), "candidate_sha256": candidate.sha256()}
        events.extend((patch_checksum_status(), brickid_outcome(contracts), "PROBE_PHYSICAL_CONTRACTS_RESOLVED"))
        terminal = terminal_outcome(events)
    except ProbeError as error:
        events.append(error.code)
        terminal = terminal_outcome(events)
    except (OSError, TimeoutError):
        events.append("PROBE_TRANSPORT_INTEGRITY_FAILURE")
        terminal = terminal_outcome(events)
    finally:
        guard.check()
        _write_evidence(attempt_root / "PROBE_TRANSPORT_EVIDENCE.json", transport_records, ledger)
        _write_evidence(attempt_root / "PROBE_CHECKSUM_EVIDENCE.json", manifest_records, ledger)
        _write_evidence(attempt_root / "PROBE_PHYSICAL_CONTRACT_CANDIDATES.json", candidates, ledger)
        _write_evidence(attempt_root / "PROBE_EVENTS.json", {"events": events}, ledger)
        _write_evidence(attempt_root / "PROBE_TERMINAL.json",
                        {"outcome": terminal, "probe_execution": "COMPLETE",
                         "scientific_execution": "NOT_STARTED", "events": events}, ledger)
    return terminal


AUTHORIZATION_FIELDS = frozenset({"authorized", "scope", "probe_spec_sha256", "clarification_001_sha256", "implementation_aggregate",
                                  "environment_fingerprint", "resources", "methods", "ranges", "caps",
                                  "execution_directory", "zero_row_observation", "command_sha256", "attempt_id"})


def load_authorization(path: Path, project: Path, command_bytes: bytes) -> tuple[dict, str]:
    path = Path(path)
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, ValueError):
        raise ProbeError("PROBE_HUMAN_AUTHORIZATION_REQUIRED") from None
    if raw != canonical(value) + b"\n" or not isinstance(value, dict) or set(value) != AUTHORIZATION_FIELDS:
        raise ProbeError("PROBE_HUMAN_AUTHORIZATION_REQUIRED")
    current = implementation_hash(Path(project))
    expected_resources = [{"role": resource.role, "url": resource.url} for resource in _RESOURCE_ROWS]
    expected_methods = {role: ["HEAD", "GET"] for role in FITS_ROLES} | {role: ["HEAD", "GET"] for role in MANIFEST_ROLES}
    execution = Path(value["execution_directory"]).resolve()
    root = (Path(project) / "oc3/provider_contract_probe").resolve()
    valid = (value["authorized"] is True and value["scope"] == "PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY"
             and value["probe_spec_sha256"] == PROBE_SPEC_SHA256
             and value["clarification_001_sha256"] == PROBE_CLARIFICATION_001_SHA256
             and value["implementation_aggregate"] == current
             and value["environment_fingerprint"] == ENVIRONMENT_FINGERPRINT
             and value["resources"] == expected_resources and value["methods"] == expected_methods
             and value["ranges"] == list(RANGES) and value["caps"] == dict(CAPS)
             and value["zero_row_observation"] is True
             and value["command_sha256"] == digest(command_bytes)
             and execution.parent == root
             and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value["attempt_id"] or "")
             and execution.name == value["attempt_id"])
    if not valid:
        raise ProbeError("PROBE_HUMAN_AUTHORIZATION_REQUIRED")
    return value, digest(raw)


def probe_plan(project: Path) -> dict:
    verify_probe_authorities(project)
    return {"scope": "PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY",
            "spec_sha256": PROBE_SPEC_SHA256, "clarification_001_sha256": PROBE_CLARIFICATION_001_SHA256,
            "resources": [{"role": r.role, "url": r.url, "kind": r.kind, "compression": r.compression} for r in _RESOURCE_ROWS],
            "methods": {role: ["HEAD", "GET"] for role in RESOURCES},
            "ranges": list(RANGES), "caps": dict(CAPS), "network": False,
            "evidence_mutation": False, "row_observation": False,
            "probe_execution": "NOT_STARTED", "scientific_execution": "NOT_STARTED"}
