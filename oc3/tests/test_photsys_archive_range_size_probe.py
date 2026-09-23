import contextlib
import io
import unittest
from unittest.mock import patch

import oc3_photsys_archive_range_size_probe as cli
from oc3lib.core import implementation_hash
from oc3lib.photsys_archive_range_size_probe import *


class RangeResponse:
    def __init__(self, *, status=206, headers=None):
        self.status = status
        self.headers = headers if headers is not None else [
            ("Content-Range", "bytes 0-0/100"),
            ("Content-Length", "1"),
            ("Content-Type", "application/x-gzip"),
            ("Content-Encoding", "identity"),
            ("ETag", HEAD_ETAG),
        ]
        self.read_calls = 0

    def getheaders(self):
        return list(self.headers)

    def read(self, *args):
        self.read_calls += 1
        raise AssertionError("RANGE_BODY_READ_FIREWALL_VIOLATION")


class RangeConnection:
    response = RangeResponse()
    requests = []

    def __init__(self, *args, **kwargs):
        pass

    def request(self, method, path, headers=None):
        type(self).requests.append((method, path, dict(headers or {})))

    def getresponse(self):
        return type(self).response

    def close(self):
        pass


class RangeSizeProbeTests(unittest.TestCase):
    def setUp(self):
        RangeConnection.requests = []

    def code(self, expected, call):
        with self.assertRaises(RangeSizeProbeError) as caught:
            call()
        self.assertEqual(caught.exception.code, expected)

    def transport(self, response):
        RangeConnection.response = response
        counters = RangeSizeCounters()
        with patch("oc3lib.photsys_archive_range_size_probe.http.client.HTTPSConnection",
                   RangeConnection):
            metadata = RangeSizeOnlyTransport(counters).probe_size()
        self.assertEqual(response.read_calls, 0)
        return counters, metadata

    def classify(self, response):
        counters, metadata = self.transport(response)
        return classify_response(metadata, counters)

    def test_01_specification_is_frozen(self):
        self.assertEqual(file_sha256(SPEC_PATH), SPEC_SHA256)

    def test_02_head_and_preserved_inputs_validate(self):
        result = validate_historical_inputs()
        self.assertEqual(result["head_terminal"], "DESITARGET_COMMIT_ARCHIVE_SIZE_INCONCLUSIVE")
        self.assertEqual(len(result["preserved_bodies"]), 4)

    def test_03_exact_resource_range_and_caps(self):
        self.assertEqual(ARCHIVE_URL, "https://codeload.github.com/desihub/desitarget/tar.gz/"
                         "dd30297f9d50fcb7bbba57d79d4b8fc86cb35701")
        self.assertEqual(RANGE_VALUE, "bytes=0-0")
        self.assertEqual((REQUEST_CAP, BODY_CAP, REDIRECT_CAP, RETRY_CAP, CONCURRENCY),
                         (1, 0, 0, 0, 1))

    def test_04_transport_exposes_only_probe_operation(self):
        transport = RangeSizeOnlyTransport(RangeSizeCounters())
        self.assertTrue(hasattr(transport, "probe_size"))
        for name in ("get", "head", "range", "read", "request"):
            self.assertFalse(hasattr(transport, name))

    def test_05_exact_get_headers_and_no_body_read(self):
        response = RangeResponse()
        counters, metadata = self.transport(response)
        self.assertEqual(len(RangeConnection.requests), 1)
        method, path, headers = RangeConnection.requests[0]
        self.assertEqual((method, path),
                         ("GET", f"/desihub/desitarget/tar.gz/{EXPECTED_COMMIT}"))
        self.assertEqual(headers["Range"], "bytes=0-0")
        self.assertEqual(headers["Accept-Encoding"], "identity")
        self.assertEqual(headers["Connection"], "close")
        self.assertEqual(counters.application_body_bytes_read, 0)
        self.assertEqual(metadata["application_body_bytes_read"], 0)

    def test_06_valid_content_range_values(self):
        for value, expected in (("bytes 0-0/1", 1),
                                ("bytes 0-0/17544938", 17_544_938),
                                ("bytes 0-0/17544939", 17_544_939),
                                ("bytes 0-0/0001", 1)):
            with self.subTest(value=value):
                self.assertEqual(parse_content_range([value]), expected)

    def test_07_invalid_content_range_values(self):
        cases = {
            "bytes 0-0/*": "CONTENT_RANGE_TOTAL_WILDCARD",
            "bytes 0-1/100": "CONTENT_RANGE_POSITIONS_UNEXPECTED",
            "bytes 1-1/100": "CONTENT_RANGE_POSITIONS_UNEXPECTED",
            "items 0-0/100": "CONTENT_RANGE_UNIT_UNEXPECTED",
            "bytes */100": "CONTENT_RANGE_UNSATISFIED_FORM",
            "bytes 0-0/0": "CONTENT_RANGE_TOTAL_INVALID",
            "bytes 0-0/-1": "CONTENT_RANGE_TOTAL_MALFORMED",
            "bytes 0-0/notanumber": "CONTENT_RANGE_TOTAL_MALFORMED",
            " bytes 0-0/100": "CONTENT_RANGE_UNIT_UNEXPECTED",
            "bytes  0-0/100": "CONTENT_RANGE_MALFORMED",
            "bytes 0 -0/100": "CONTENT_RANGE_MALFORMED",
            "bytes 0-0/100 ": "CONTENT_RANGE_TOTAL_MALFORMED",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.code(expected, lambda value=value: parse_content_range([value]))

    def test_08_absent_and_multiple_content_range_rejected(self):
        self.code("CONTENT_RANGE_ABSENT", lambda: parse_content_range([]))
        self.code("CONTENT_RANGE_MULTIPLE",
                  lambda: parse_content_range(["bytes 0-0/10", "bytes 0-0/10"]))
        self.code("CONTENT_RANGE_MULTIPLE",
                  lambda: parse_content_range(["bytes 0-0/10, bytes 0-0/10"]))

    def test_09_valid_206_below_budget(self):
        outcome = self.classify(RangeResponse(headers=[
            ("Content-Range", "bytes 0-0/17544938"), ("Content-Length", "1"),
            ("Content-Type", "application/gzip"), ("ETag", HEAD_ETAG)]))
        self.assertEqual(outcome, {"budget_decision": "LATER_ARCHIVE_ACQUISITION_MAY_BE_DESIGNED",
                                   "complete_length": 17_544_938,
                                   "reason": "VALID_206_CONTENT_RANGE", "state": SUCCESS})

    def test_10_valid_206_above_budget_stops_current_spec(self):
        outcome = self.classify(RangeResponse(headers=[
            ("Content-Range", "bytes 0-0/17544939"),
            ("Content-Type", "application/octet-stream")]))
        self.assertEqual(outcome["state"], SUCCESS)
        self.assertEqual(outcome["budget_decision"],
                         "STOP_CURRENT_32_MIB_SPEC_CANNOT_ACCOMMODATE")

    def test_11_http_200_is_inconclusive_and_reads_nothing(self):
        response = RangeResponse(status=200, headers=[("Content-Type", "application/x-gzip")])
        outcome = self.classify(response)
        self.assertEqual((outcome["state"], outcome["reason"]),
                         (INCONCLUSIVE, "RANGE_IGNORED_200"))
        self.assertEqual(response.read_calls, 0)

    def test_12_redirects_fail_without_body_read(self):
        for status in REDIRECT_STATUSES:
            response = RangeResponse(status=status, headers=[("Location", "https://example.test/")])
            outcome = self.classify(response)
            self.assertEqual((outcome["state"], outcome["reason"]),
                             (FAILED, "RANGE_REDIRECT_FORBIDDEN"))
            self.assertEqual(response.read_calls, 0)

    def test_13_416_is_inconclusive_and_does_not_parse_total(self):
        response = RangeResponse(status=416, headers=[("Content-Range", "bytes */999")])
        outcome = self.classify(response)
        self.assertEqual((outcome["state"], outcome["reason"], outcome["complete_length"]),
                         (INCONCLUSIVE, "RANGE_NOT_SATISFIABLE_416", None))
        self.assertEqual(response.read_calls, 0)

    def test_14_500_fails_without_second_request(self):
        response = RangeResponse(status=500, headers=[])
        outcome = self.classify(response)
        self.assertEqual((outcome["state"], outcome["reason"]),
                         (FAILED, "RANGE_HTTP_STATUS_UNEXPECTED"))
        self.assertEqual(len(RangeConnection.requests), 1)

    def test_15_content_type_failure_reads_nothing(self):
        response = RangeResponse(headers=[("Content-Range", "bytes 0-0/100"),
                                          ("Content-Type", "text/plain")])
        outcome = self.classify(response)
        self.assertEqual(outcome["reason"], "RANGE_CONTENT_TYPE_MISMATCH")
        self.assertEqual(response.read_calls, 0)

    def test_16_content_encoding_failure(self):
        outcome = self.classify(RangeResponse(headers=[
            ("Content-Range", "bytes 0-0/100"), ("Content-Type", "application/gzip"),
            ("Content-Encoding", "gzip")]))
        self.assertEqual(outcome["reason"], "RANGE_CONTENT_ENCODING_MISMATCH")

    def test_17_etag_mismatch_fails_identity(self):
        outcome = self.classify(RangeResponse(headers=[
            ("Content-Range", "bytes 0-0/100"), ("Content-Type", "application/gzip"),
            ("ETag", '"different"')]))
        self.assertEqual(outcome["reason"], "REPRESENTATION_IDENTITY_MISMATCH")

    def test_18_absent_range_etag_is_allowed(self):
        outcome = self.classify(RangeResponse(headers=[
            ("Content-Range", "bytes 0-0/100"), ("Content-Type", "application/gzip")]))
        self.assertEqual(outcome["state"], SUCCESS)

    def test_19_content_length_is_partial_not_complete(self):
        outcome = self.classify(RangeResponse(headers=[
            ("Content-Range", "bytes 0-0/100"), ("Content-Length", "1"),
            ("Content-Type", "application/gzip")]))
        self.assertEqual(outcome["complete_length"], 100)

    def test_20_bad_partial_content_length_fails(self):
        for values in (["2"], ["invalid"], ["1", "1"]):
            headers = [("Content-Range", "bytes 0-0/100"),
                       ("Content-Type", "application/gzip")]
            headers.extend(("Content-Length", value) for value in values)
            with self.subTest(values=values):
                self.assertEqual(self.classify(RangeResponse(headers=headers))["reason"],
                                 "PARTIAL_CONTENT_LENGTH_MISMATCH")

    def test_21_missing_and_malformed_content_range_never_read(self):
        for headers in ([('Content-Type', 'application/gzip')],
                        [('Content-Range', 'bytes 0-1/100'),
                         ('Content-Type', 'application/gzip')]):
            response = RangeResponse(headers=headers)
            outcome = self.classify(response)
            self.assertEqual(outcome["state"], INCONCLUSIVE)
            self.assertEqual(response.read_calls, 0)

    def test_22_request_cap_prevents_second_request(self):
        counters = RangeSizeCounters(network_requests_started=1)
        transport = RangeSizeOnlyTransport(counters)
        with patch("oc3lib.photsys_archive_range_size_probe.http.client.HTTPSConnection",
                   side_effect=AssertionError("connection forbidden")):
            self.code("RANGE_SIZE_REQUEST_CAP_VIOLATION", transport.probe_size)

    def test_23_candidate_exact_and_authorization_absent(self):
        self.assertEqual(validate_candidate(), build_candidate(implementation_hash(PROJECT)))
        self.assertFalse(AUTHORIZATION_PATH.exists())

    def test_24_exact_command_is_range_size_only(self):
        command = exact_command()
        self.assertIn("--probe-desitarget-archive-range-size", command)
        self.assertIn("--execute-network", command)
        self.assertNotIn("--probe-desitarget-archive-head", command)

    def test_25_cli_help(self):
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stdout(io.StringIO()):
            cli.main(["--help"])
        self.assertEqual(caught.exception.code, 0)

    def test_26_execution_requires_authorization(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["--probe-desitarget-archive-range-size"]), 2)

    def test_27_dry_run_boundary(self):
        result = dry_run()
        self.assertEqual(result["state"], READY)
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(result["application_body_bytes_read"], 0)

    def test_28_validate_and_dry_run_make_no_network(self):
        with patch("oc3lib.photsys_archive_range_size_probe.http.client.HTTPSConnection",
                   side_effect=AssertionError("network")):
            self.assertEqual(validate_historical_inputs()["network_requests"], 0)
            self.assertEqual(dry_run()["network_requests"], 0)

    def test_29_firewall_counters_start_at_zero(self):
        counters = RangeSizeCounters().object()
        self.assertEqual(sum(counters.values()), 0)

    def test_30_any_body_read_count_is_a_firewall_failure(self):
        counters, metadata = self.transport(RangeResponse())
        counters.application_body_bytes_read = 1
        outcome = classify_response(metadata, counters)
        self.assertEqual((outcome["state"], outcome["reason"]),
                         (FAILED, "RANGE_BODY_READ_FIREWALL_VIOLATION"))


if __name__ == "__main__":
    unittest.main()
