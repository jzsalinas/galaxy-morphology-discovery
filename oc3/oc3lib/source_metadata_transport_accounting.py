"""Fail-closed streaming transport accounting for prospective source-metadata work.

The caller owns query semantics.  This module only records transport facts and never
parses, accepts, or interprets CSV content.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import socket
from typing import Any
from urllib.error import HTTPError, URLError


SUPPORTED_TRANSPORT_EXCEPTIONS = (TimeoutError, socket.timeout, ConnectionError, HTTPError, URLError, OSError)


def normalized_diagnostic(exc: BaseException) -> str:
    value = " ".join(str(exc).split()) or exc.__class__.__name__
    return value[:512]


@dataclass(frozen=True)
class TransportObservation:
    query_id: str
    request_started: int
    body_bytes_preserved: int
    response_complete: bool
    partial_body_exists: bool
    http_status: int | None
    content_type: str | None
    exception_class: str | None
    diagnostic_message: str | None
    timeout_seconds: int
    artifact_path: str | None
    artifact_sha256: str | None
    failure_class: str | None

    def record(self) -> dict[str, Any]:
        return asdict(self)


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stream_bounded_response(*, query_id: str, opener: Any, request: Any,
        timeout_seconds: int, byte_cap: int, staging_path: Path,
        complete_path: Path, partial_path: Path, chunk_size: int = 65_536) -> TransportObservation:
    """Perform one request and preserve exact observable accounting.

    ``request_started`` becomes one immediately before handing the request to the
    opener.  A partial body is never promoted to ``complete_path``.  A response with
    a declared Content-Length is complete only when that exact length was received.
    """
    for path in (staging_path, complete_path, partial_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    if complete_path.exists() or staging_path.exists() or partial_path.exists():
        raise FileExistsError("TRANSPORT_OUTPUT_ALREADY_EXISTS")
    request_started = 0
    bytes_read = 0
    response = None
    status = None
    content_type = None
    expected_length = None
    try:
        request_started = 1
        response = opener.open(request, timeout=timeout_seconds)
        status = response.getcode()
        content_type = response.headers.get("Content-Type")
        if status != 200:
            raise OSError(f"HTTP_STATUS_{status}")
        final_url = response.geturl() if hasattr(response, "geturl") else request.full_url
        if final_url != request.full_url:
            raise OSError("DATALAB_REDIRECT_FORBIDDEN")
        raw_length = response.headers.get("Content-Length")
        if raw_length is not None:
            try:
                expected_length = int(raw_length)
            except ValueError as exc:
                raise OSError("INVALID_CONTENT_LENGTH") from exc
            if expected_length < 0 or expected_length > byte_cap:
                raise OSError("DATALAB_BODY_CAP_EXCEEDED")
        with staging_path.open("xb") as sink:
            while True:
                chunk = response.read(min(chunk_size, byte_cap - bytes_read + 1))
                if not chunk:
                    break
                sink.write(chunk)
                bytes_read += len(chunk)
                if bytes_read > byte_cap:
                    raise OSError("DATALAB_BODY_CAP_EXCEEDED")
            sink.flush()
            os.fsync(sink.fileno())
        if expected_length is not None and bytes_read != expected_length:
            raise OSError(f"PREMATURE_EOF expected={expected_length} observed={bytes_read}")
        os.replace(staging_path, complete_path)
        _fsync_directory(complete_path.parent)
        return TransportObservation(query_id, request_started, bytes_read, True, False,
            status, content_type, None, None, timeout_seconds, str(complete_path),
            _hash(complete_path), None)
    except SUPPORTED_TRANSPORT_EXCEPTIONS as exc:
        if staging_path.exists():
            os.replace(staging_path, partial_path)
            with partial_path.open("rb") as preserved:
                os.fsync(preserved.fileno())
            _fsync_directory(partial_path.parent)
        exists = partial_path.exists()
        size = partial_path.stat().st_size if exists else bytes_read
        return TransportObservation(query_id, request_started, size, False, exists,
            status, content_type, exc.__class__.__name__, normalized_diagnostic(exc),
            timeout_seconds, str(partial_path) if exists else None,
            _hash(partial_path) if exists else None, "DATALAB_TRANSPORT_FAILURE")
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
