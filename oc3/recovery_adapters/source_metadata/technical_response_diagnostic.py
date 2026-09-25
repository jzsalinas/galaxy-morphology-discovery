"""Bounded representation diagnostic for one exact schema-query response."""
from __future__ import annotations

from html.parser import HTMLParser

BODY_CAP = 65_536
TECHNICAL_CLASSES = (
    "HTML_SERVICE_PAGE", "HTML_ERROR_PAGE", "HTML_AUTH_PAGE", "HTML_PROXY_PAGE",
    "CSV_BODY_WITH_WRONG_CONTENT_TYPE", "UNKNOWN_HTML_RESPONSE",
)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def classify_representation(content_type: str, body: bytes) -> str:
    """Classify technical representation only; never parse rows as science."""
    if len(body) > BODY_CAP:
        raise ValueError("TECHNICAL_DIAGNOSTIC_BODY_CAP_EXCEEDED")
    lowered = content_type.split(";", 1)[0].strip().lower()
    prefix = body[:4096].lstrip().lower()
    if lowered in ("text/csv", "application/x-csv") or prefix.startswith(b"table_name,column_name,"):
        return "CSV_BODY_WITH_WRONG_CONTENT_TYPE" if lowered not in ("text/csv", "application/x-csv") else "CSV_REPRESENTATION"
    if b"<html" not in prefix and b"<!doctype html" not in prefix:
        return "UNKNOWN_HTML_RESPONSE"
    parser = _Text(); parser.feed(body.decode("utf-8", errors="replace")); text = " ".join(parser.parts).lower()
    if any(token in text for token in ("sign in", "login", "authentication", "unauthorized")):
        return "HTML_AUTH_PAGE"
    if any(token in text for token in ("proxy error", "gateway", "upstream")):
        return "HTML_PROXY_PAGE"
    if any(token in text for token in ("error", "exception", "failed")):
        return "HTML_ERROR_PAGE"
    if any(token in text for token in ("data lab", "query", "service")):
        return "HTML_SERVICE_PAGE"
    return "UNKNOWN_HTML_RESPONSE"
