from __future__ import annotations

import unittest
from unittest.mock import patch

from oc3lib.source_metadata_acquisition_pilot import RejectRedirect, frozen_headers, query_url
from recovery_adapters.source_metadata.transport_registry import AdapterError, get_adapter


class _Response:
    def __init__(self, body: bytes, content_type: str = "text/html; charset=utf-8"):
        self.body = body
        self.headers = {"Content-Type": content_type}
        self.requested_size = None

    def read(self, size: int) -> bytes:
        self.requested_size = size
        return self.body

    @staticmethod
    def getcode() -> int:
        return 200


class _Opener:
    def __init__(self, response: _Response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout: int):
        self.request = request
        self.timeout = timeout
        return self.response


class QueryManagerPublicAnonymousRun003Tests(unittest.TestCase):
    def test_validated_adapter_preserves_query_and_accepts_csv_bytes_with_wrong_content_type(self):
        literal_adql = "SELECT table_name FROM TAP_SCHEMA.tables ORDER BY table_name"
        body = b"table_name\nls_dr9.tractor_n\n"
        response = _Response(body)
        opener = _Opener(response)

        with patch("recovery_adapters.source_metadata.transport_registry.urllib.request.build_opener",
                   return_value=opener) as build_opener:
            observed, record = get_adapter("query_manager_public_anonymous_v1").execute(
                "schema", literal_adql, 1024, {"adapter_validated": True})

        self.assertEqual(observed, body)
        self.assertEqual(record["content_type"], "text/html; charset=utf-8")
        self.assertEqual(record["http_status"], 200)
        self.assertEqual(record["query_id"], "schema")
        self.assertEqual(record["url"], query_url(literal_adql))
        self.assertEqual(opener.request.full_url, query_url(literal_adql))
        self.assertEqual(opener.request.method, "GET")
        self.assertEqual(opener.timeout, 300)
        self.assertEqual(response.requested_size, 1025)
        self.assertEqual(opener.request.headers["X-dl-authtoken"], frozen_headers()["X-DL-AuthToken"])
        self.assertEqual(len(build_opener.call_args.args), 1)
        self.assertIsInstance(build_opener.call_args.args[0], RejectRedirect)

    def test_body_cap_is_enforced_before_csv_parsing(self):
        response = _Response(b"x" * 5, content_type="text/csv")
        opener = _Opener(response)
        with patch("recovery_adapters.source_metadata.transport_registry.urllib.request.build_opener",
                   return_value=opener):
            with self.assertRaisesRegex(AdapterError, "DATALAB_BODY_CAP_EXCEEDED"):
                get_adapter("query_manager_public_anonymous_v1").execute(
                    "schema", "SELECT 1", 4, {"adapter_validated": True})

    def test_unvalidated_or_unknown_adapter_fails_closed(self):
        with self.assertRaisesRegex(AdapterError, "TECHNICAL_ADAPTER_NOT_VALIDATED"):
            get_adapter("query_manager_public_anonymous_v1").execute(
                "schema", "SELECT 1", 32, {"adapter_validated": False})
        with self.assertRaisesRegex(AdapterError, "TECHNICAL_ADAPTER_NOT_VALIDATED"):
            get_adapter("not_registered")


if __name__ == "__main__":
    unittest.main()
