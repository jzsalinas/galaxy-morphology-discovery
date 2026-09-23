import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import oc3_photsys_archive_head_probe as cli
from oc3lib.core import implementation_hash
from oc3lib.photsys_archive_head_probe import *


class HeadResponse:
    def __init__(self, *, status=200, headers=None):
        self.status=status
        self.headers=headers or {"Content-Length":"17000000","Content-Type":"application/x-gzip",
                                 "Content-Encoding":"identity","ETag":"synthetic"}
        self.read_calls=0
    def getheaders(self): return list(self.headers.items())
    def read(self,*args): self.read_calls+=1; raise AssertionError("HEAD_BODY_READ_FORBIDDEN")


class HeadConnection:
    response=HeadResponse()
    method=None
    path=None
    def __init__(self,*args,**kwargs): pass
    def request(self,method,path,headers=None):
        type(self).method=method; type(self).path=path
    def getresponse(self): return type(self).response
    def close(self): pass


class HeadProbeTests(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory(prefix="head_probe_SYNTHETIC_ONLY_")
    def tearDown(self): self.temp.cleanup()
    def code(self,expected,call):
        with self.assertRaises(HeadProbeError) as caught: call()
        self.assertEqual(caught.exception.code,expected)
    def transport(self,response):
        HeadConnection.response=response
        counters=HeadCounters()
        with patch("oc3lib.photsys_archive_head_probe.http.client.HTTPSConnection",HeadConnection):
            result=HeadOnlyTransport(counters).head()
        return counters,result

    def test_01_review_is_frozen(self): self.assertEqual(file_sha256(REVIEW_PATH),REVIEW_SHA256)
    def test_02_historical_terminal_and_four_bodies_validate(self):
        result=validate_historical_inputs()
        self.assertEqual(len(result["preserved_bodies"]),4)
        self.assertEqual(sum(x["bytes"] for x in result["preserved_bodies"]),1329429)
    def test_03_conservative_arithmetic_exact(self):
        self.assertEqual((HISTORICAL_MINIMUM_BODY_BYTES,HISTORICAL_MAXIMUM_BODY_BYTES),(1329429,16009494))
        self.assertEqual(PARENT_BODY_MAXIMUM-HISTORICAL_MAXIMUM_BODY_BYTES,17544938)
    def test_04_head_caps_exact(self):
        self.assertEqual((REQUEST_CAP,BODY_CAP,REDIRECT_CAP,RETRY_CAP,CONCURRENCY),(1,0,0,0,1))
    def test_05_exact_commit_url(self):
        self.assertEqual(ARCHIVE_URL,"https://codeload.github.com/desihub/desitarget/tar.gz/dd30297f9d50fcb7bbba57d79d4b8fc86cb35701")
    def test_06_transport_has_no_get_range_or_generic_request(self):
        transport=HeadOnlyTransport(HeadCounters())
        self.assertFalse(hasattr(transport,"get")); self.assertFalse(hasattr(transport,"range"))
        self.assertFalse(hasattr(transport,"request"))
    def test_07_head_success_reads_no_body(self):
        response=HeadResponse(); counters,result=self.transport(response)
        self.assertEqual((HeadConnection.method,HeadConnection.path),("HEAD",f"/desihub/desitarget/tar.gz/{EXPECTED_COMMIT}"))
        self.assertEqual(result["declared_content_length"],17000000)
        self.assertEqual(response.read_calls,0)
        self.assertEqual(counters.application_body_bytes_read,0)
        self.assertEqual(counters.network_requests_started,1)
    def test_08_missing_content_length_is_inconclusive(self):
        counters,result=self.transport(HeadResponse(headers={"Content-Type":"application/gzip"}))
        self.assertEqual(classify_head(result),(INCONCLUSIVE,"NO_ARCHIVE_GET_CANDIDATE"))
        self.assertEqual(counters.application_body_bytes_read,0)
    def test_09_invalid_content_length_is_inconclusive(self):
        _,result=self.transport(HeadResponse(headers={"Content-Length":"unknown","Content-Type":"application/gzip"}))
        self.assertEqual(classify_head(result)[0],INCONCLUSIVE)
    def test_10_redirect_rejected_without_body(self):
        response=HeadResponse(status=302,headers={"Location":"https://example.test/x"})
        HeadConnection.response=response; counters=HeadCounters(); transport=HeadOnlyTransport(counters)
        with patch("oc3lib.photsys_archive_head_probe.http.client.HTTPSConnection",HeadConnection):
            self.code("HEAD_REDIRECT_FORBIDDEN",transport.head)
        self.assertEqual(response.read_calls,0); self.assertIsNotNone(transport.last_metadata)
    def test_11_wrong_content_type_rejected(self):
        response=HeadResponse(headers={"Content-Length":"10","Content-Type":"text/html"})
        HeadConnection.response=response; transport=HeadOnlyTransport(HeadCounters())
        with patch("oc3lib.photsys_archive_head_probe.http.client.HTTPSConnection",HeadConnection):
            self.code("HEAD_CONTENT_TYPE_INVALID",transport.head)
        self.assertEqual(response.read_calls,0)
    def test_12_threshold_allows_later_design_at_equal(self):
        state,decision=classify_head({"declared_content_length":REMAINING_CONSERVATIVE_BODY_BUDGET})
        self.assertEqual((state,decision),(SUCCESS,"LATER_ARCHIVE_ACQUISITION_MAY_BE_DESIGNED"))
    def test_13_threshold_stops_above(self):
        state,decision=classify_head({"declared_content_length":REMAINING_CONSERVATIVE_BODY_BUDGET+1})
        self.assertEqual((state,decision),(SUCCESS,"STOP_CURRENT_32_MIB_SPEC_CANNOT_ACCOMMODATE"))
    def test_14_exact_command_is_head_only(self):
        command=exact_command(); self.assertIn("--probe-desitarget-archive-head",command)
        self.assertIn("--execute-network",command); self.assertNotIn("GET",command)
    def test_15_historical_candidate_authorization_and_runtime_are_preserved(self):
        self.assertEqual(file_sha256(CANDIDATE_PATH),
                         "50e957873994c6330577a2b38d3ff3a3a00884ded076b9bd88447edf530b3a95")
        self.assertEqual(file_sha256(AUTHORIZATION_PATH),
                         "f33c558bb4b1b51671754571f6911db97611cdb858b1c741fb5956dee902d2bf")
        self.assertEqual(file_sha256(OUTPUT_ROOT/"HEAD_RESPONSE.json"),
                         "5eefee40091b098435701e4abbf271cb888b29a0353df8e5e7da40242449506b")
        self.assertEqual(file_sha256(OUTPUT_ROOT/"TERMINAL.json"),
                         "d70de460a0628b333d73a5b4a70de6fdab53333a971f9c276beb2255a4b82da8")
    def test_16_cli_help(self):
        with self.assertRaises(SystemExit) as caught,contextlib.redirect_stdout(io.StringIO()):cli.main(["--help"])
        self.assertEqual(caught.exception.code,0)
    def test_17_cli_execution_requires_authorization(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["--probe-desitarget-archive-head"]),2)
    def test_18_historical_dry_run_is_closed(self):
        self.code("HEAD_PROBE_CANDIDATE_INVALID",dry_run)
    def test_19_historical_validation_makes_no_network(self):
        with patch("oc3lib.photsys_archive_head_probe.http.client.HTTPSConnection",side_effect=AssertionError("network")):
            self.assertEqual(validate_historical_inputs()["network_requests"],0)


if __name__=="__main__": unittest.main()
