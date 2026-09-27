from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from oc3lib.cross_observer_grouping import PROJECT, load_canonical_json
from oc3lib.manual_source_metadata_acquisition import (
    TIMEOUT_SECONDS, binding_payload, run_manual_acquisition,
)

BINDING=PROJECT/"oc3/INPUTS/OC3_MANUAL_SOURCE_METADATA_ACQUISITION_BINDING_001.json"


class Headers(dict):
    pass


class Response:
    def __init__(self, body: bytes, content_type="text/csv", status=200, declared=None):
        self.body=body; self.offset=0; self.status=status
        self.headers=Headers({"Content-Type":content_type,"Content-Length":str(len(body) if declared is None else declared)})
    def read(self,n):
        value=self.body[self.offset:self.offset+n]; self.offset+=len(value); return value
    def getcode(self): return self.status
    def close(self): pass


class PartialResponse(Response):
    def __init__(self, body: bytes): super().__init__(body,declared=len(body)+10); self.calls=0
    def read(self,n):
        self.calls+=1
        if self.calls==1: return super().read(min(n,3))
        raise TimeoutError(" synthetic read   timed out ")

class RedirectResponse(Response):
    def geturl(self): return "https://example.invalid/redirected"


class Opener:
    def __init__(self,responses): self.responses=list(responses); self.calls=[]
    def open(self,request,timeout):
        self.calls.append((request,timeout))
        item=self.responses.pop(0)
        if isinstance(item,BaseException): raise item
        return item


def success_responses(content_type="text/csv"):
    return [Response(b"brickname,source_count\n",content_type),Response(b"brickname,source_count\n",content_type),
        Response(b"release,brickid,objid,brickname,brick_primary,ra,dec,ra_ivar,dec_ivar\n",content_type),
        Response(b"release,brickid,objid,brickname,brick_primary,ra,dec,ra_ivar,dec_ivar\n",content_type)]


class ManualAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=PROJECT/"oc3")
        self.root=Path(self.temp.name)/"manual"
        self.binding=load_canonical_json(BINDING)
    def tearDown(self): self.temp.cleanup()

    def execute(self,opener):
        return run_manual_acquisition(binding=self.binding,binding_path=BINDING,root=self.root,opener=opener,reporter_interval=0.01)

    def test_all_five_logical_queries_complete_with_schema_reuse(self):
        opener=Opener(success_responses())
        self.assertEqual(self.execute(opener),0)
        manifest=json.loads((self.root/"ACQUISITION_MANIFEST.json").read_text())
        self.assertEqual(set(manifest["queries"]),{"schema","north_count","south_count","north_rows","south_rows"})
        self.assertEqual(manifest["queries"]["schema"]["requests_started"],0)
        self.assertEqual(len(opener.calls),4)
        self.assertTrue(all(timeout==TIMEOUT_SECONDS for _,timeout in opener.calls))
        self.assertTrue(all(not row["scientific_acceptance"] for row in manifest["queries"].values()))

    def test_wrong_content_type_is_recorded_without_acceptance(self):
        self.assertEqual(self.execute(Opener(success_responses("text/html"))),0)
        manifest=json.loads((self.root/"ACQUISITION_MANIFEST.json").read_text())
        self.assertEqual(manifest["queries"]["north_count"]["content_type"],"text/html")
        self.assertFalse(manifest["scientific_acceptance"])

    def test_timeout_zero_bytes_writes_terminal_and_nonzero_exit(self):
        opener=Opener([TimeoutError("read timed out")])
        self.assertEqual(self.execute(opener),20)
        terminal=next((self.root/"EVIDENCE/north_count").glob("*TERMINAL.json"))
        data=json.loads(terminal.read_text())
        self.assertEqual(data["requests_started"],1); self.assertEqual(data["bytes_preserved"],0)
        self.assertFalse(data["response_complete"]); self.assertFalse(data["scientific_acceptance"])

    def test_partial_bytes_remain_partial_and_unaccepted(self):
        self.assertEqual(self.execute(Opener([PartialResponse(b"abcdef")])),20)
        terminal=json.loads(next((self.root/"EVIDENCE/north_count").glob("*TERMINAL.json")).read_text())
        self.assertEqual(terminal["bytes_preserved"],3); self.assertTrue(terminal["partial"])
        self.assertTrue((self.root/terminal["partial_path"].split(self.root.name+"/",1)[-1]).exists())
        self.assertFalse((self.root/"RAW_ACQUIRED/north_count.csv").exists())

    def test_completed_query_survives_later_failure_and_restart_skips_it(self):
        first=Opener([success_responses()[0],TimeoutError("read timed out")])
        self.assertEqual(self.execute(first),20)
        digest=hashlib.sha256((self.root/"RAW_ACQUIRED/north_count.csv").read_bytes()).hexdigest()
        second=Opener(success_responses()[1:])
        self.assertEqual(self.execute(second),0)
        self.assertEqual(len(second.calls),3)
        self.assertEqual(hashlib.sha256((self.root/"RAW_ACQUIRED/north_count.csv").read_bytes()).hexdigest(),digest)

    def test_hash_mismatch_prevents_skip(self):
        self.assertEqual(self.execute(Opener([success_responses()[0],TimeoutError("x")])),20)
        (self.root/"RAW_ACQUIRED/north_count.csv").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"COMPLETED_OUTPUT_HASH_MISMATCH"):
            self.execute(Opener([]))

    def test_unmanifested_complete_and_unknown_files_fail_closed(self):
        self.root.mkdir(); (self.root/"mystery").write_text("x")
        with self.assertRaisesRegex(ValueError,"UNKNOWN_EXISTING"):
            self.execute(Opener([]))

    def test_binding_query_or_provider_drift_fails_before_network(self):
        for mutation in ("query","provider"):
            with self.subTest(mutation=mutation):
                value=deepcopy(self.binding)
                if mutation=="query": value["queries"][0]["adql_sha256"]="0"*64
                else: value["endpoint"]="https://example.invalid"
                opener=Opener([])
                with self.assertRaisesRegex(ValueError,"BINDING_DRIFT"):
                    run_manual_acquisition(binding=value,binding_path=BINDING,root=self.root,opener=opener)
                self.assertEqual(opener.calls,[])

    def test_binding_freezes_no_credentials_redirects_retries_and_seal(self):
        expected=binding_payload(); self.assertEqual(self.binding,expected)
        self.assertFalse(expected["credentials_authorized"]); self.assertEqual(expected["redirects"],0)
        self.assertEqual(expected["automatic_retries"],0); self.assertEqual(expected["timeout_seconds"],600)
        self.assertEqual(expected["command_argv_sha256"],hashlib.sha256(__import__('oc3lib.core',fromlist=['canonical']).canonical(expected["command_argv"])).hexdigest())

    def test_no_automatic_retry_after_timeout(self):
        opener=Opener([TimeoutError("timeout"),success_responses()[0]])
        self.assertEqual(self.execute(opener),20); self.assertEqual(len(opener.calls),1)

    def test_detectable_premature_eof_is_partial(self):
        self.assertEqual(self.execute(Opener([Response(b"abc",declared=8)])),21)
        terminal=json.loads(next((self.root/"EVIDENCE/north_count").glob("*TERMINAL.json")).read_text())
        self.assertTrue(terminal["partial"]); self.assertIn("PREMATURE_EOF",terminal["diagnostic_message"])

    def test_http_failure_is_governed_transport_failure(self):
        self.assertEqual(self.execute(Opener([Response(b"error",status=500)])),21)
        terminal=json.loads(next((self.root/"EVIDENCE/north_count").glob("*TERMINAL.json")).read_text())
        self.assertIn("HTTP_STATUS_500",terminal["diagnostic_message"])

    def test_redirect_is_forbidden_and_not_complete(self):
        self.assertEqual(self.execute(Opener([RedirectResponse(b"data")])),21)
        self.assertFalse((self.root/"RAW_ACQUIRED/north_count.csv").exists())

    def test_existing_unmanifested_complete_output_is_not_overwritten(self):
        (self.root/"RAW_ACQUIRED").mkdir(parents=True)
        target=self.root/"RAW_ACQUIRED/north_count.csv"; target.write_bytes(b"preserve")
        with self.assertRaisesRegex(FileExistsError,"TRANSPORT_OUTPUT_ALREADY_EXISTS"):
            self.execute(Opener(success_responses()))
        self.assertEqual(target.read_bytes(),b"preserve")

    def test_incomplete_staging_file_is_never_complete(self):
        (self.root/"STAGING").mkdir(parents=True)
        (self.root/"STAGING/north_count.attempt-0001.tmp").write_bytes(b"incomplete")
        with self.assertRaisesRegex(FileExistsError,"TRANSPORT_OUTPUT_ALREADY_EXISTS"):
            self.execute(Opener(success_responses()))
        self.assertFalse((self.root/"RAW_ACQUIRED/north_count.csv").exists())

    def test_manifest_tamper_fails_before_network(self):
        self.assertEqual(self.execute(Opener([success_responses()[0],TimeoutError("stop")])),20)
        manifest=json.loads((self.root/"ACQUISITION_MANIFEST.json").read_text()); manifest["scientific_acceptance"]=True
        (self.root/"ACQUISITION_MANIFEST.json").write_text(json.dumps(manifest))
        opener=Opener([])
        with self.assertRaisesRegex(ValueError,"MANIFEST_SEAL_INVALID"):
            self.execute(opener)
        self.assertEqual(opener.calls,[])

    def test_completed_execution_rerun_is_zero_network(self):
        self.assertEqual(self.execute(Opener(success_responses())),0)
        opener=Opener([]); self.assertEqual(self.execute(opener),0); self.assertEqual(opener.calls,[])


if __name__=="__main__": unittest.main()
