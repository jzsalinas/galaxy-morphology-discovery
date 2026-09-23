import contextlib
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import oc3_photsys_zero_byte_provenance as cli
from oc3lib.core import canonical, implementation_hash
from oc3lib.photsys_zero_byte_provenance import *
from oc3lib.photsys_zero_byte_provenance import _resources


class FakeResponse:
    def __init__(self, body=b"ok", *, status=200, headers=None):
        self.body = body; self.status = status
        self.read_calls = 0
        self.headers = headers or {"Content-Length": str(len(body)), "Content-Encoding": "identity",
                                   "Content-Type": "application/pdf"}
    def getheaders(self): return list(self.headers.items())
    def read(self, amount): self.read_calls += 1; return self.body[:amount]


class FakeConnection:
    response = FakeResponse()
    calls = 0
    def __init__(self, *args, **kwargs): pass
    def request(self, *args, **kwargs): type(self).calls += 1
    def getresponse(self): return type(self).response
    def close(self): pass


def archive_bytes(files, *, unsafe=None):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for name, body in files.items():
            info = tarfile.TarInfo(f"{ARCHIVE_PREFIX}/{name}"); info.size = len(body)
            archive.addfile(info, io.BytesIO(body))
        if unsafe:
            info = tarfile.TarInfo(unsafe); info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
    return stream.getvalue()


def source_files(named=False):
    randoms = b'''def get_quantities_in_a_brick(zeros=False):
    if zeros:
        dt = [("RELEASE", "i2")]
    else:
        dt = [("PHOTSYS", "|S1")]
    x["PHOTSYS"] = b"S"
    x["PHOTSYS"] = b"N"
def supplement_randoms():
    return select_randoms_bricks(zeros=True)
'''
    files = {
        "py/desitarget/randoms.py": randoms,
        "bin/select_randoms": b"select_randoms_bricks\n",
        "bin/supplement_randoms": b"supplement_randoms zeros=True\n",
        "py/desitarget/io.py": b"def write_randoms(): fitsio.write()\n",
        "doc/changes.rst": b"0.48.0\n",
    }
    if named:
        files["bin/make_summary"] = b"write('survey-bricks-dr9-randoms-0.48.0.fits')\n"
    return files


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="zero_provenance_SYNTHETIC_ONLY_")
        self.root = Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def code(self, expected, call):
        with self.assertRaises(ProvenanceError) as caught: call()
        self.assertEqual(caught.exception.code, expected)

    def test_01_spec_hash(self): self.assertEqual(file_sha256(SPEC_PATH), SPEC_SHA256)
    def test_02_manifest_exact(self): self.assertEqual(validate_resource_manifest(), build_resource_manifest())
    def test_03_allowlist_exact_five(self):
        resources = _resources(); self.assertEqual(len(resources), 5)
        self.assertEqual({r["host"] for r in resources}, {"fits.gsfc.nasa.gov", "www.legacysurvey.org", "api.github.com", "codeload.github.com"})
    def test_04_no_astronomical_urls(self):
        self.assertTrue(all(not str(r["url"]).lower().endswith(".fits") for r in _resources()))
        self.assertNotIn("portal.nersc.gov", canonical(_resources()).decode())
    def test_05_caps_tighter_than_spec(self):
        self.assertLessEqual(REQUEST_CAP, 24); self.assertLessEqual(BODY_CAP, 32*1024*1024)
        self.assertEqual((CONCURRENCY, RETRIES_PER_RESOURCE), (1, 0))
    def test_05a_archive_is_commit_pinned_not_tag_pinned(self):
        archive=[r for r in _resources() if r["id"]=="DESITARGET_0_48_0_ARCHIVE"][0]
        self.assertEqual(archive["url"],ARCHIVE_URL)
        self.assertIn(EXPECTED_COMMIT,archive["url"])
        self.assertNotIn("refs/tags",archive["url"])
        self.assertEqual(archive["archive_identity"]["top_level_prefix"],ARCHIVE_PREFIX)
    def test_06_wrong_host_rejected_before_connection(self):
        manifest=build_resource_manifest(); manifest["resources"][0]["host"]="evil.example"
        t=DocumentaryTransport(manifest, FirewallCounters())
        self.code("RESOURCE_NOT_ALLOWLISTED", lambda:t.get("FITS_STANDARD_4_0"))
    def test_07_query_rejected_before_connection(self):
        manifest=build_resource_manifest(); manifest["resources"][0]["url"] += "?x=1"
        t=DocumentaryTransport(manifest, FirewallCounters())
        self.code("RESOURCE_NOT_ALLOWLISTED", lambda:t.get("FITS_STANDARD_4_0"))
    def test_08_unknown_identity_rejected(self):
        self.code("RESOURCE_NOT_ALLOWLISTED", lambda:DocumentaryTransport(build_resource_manifest(),FirewallCounters()).get("X"))
    def test_09_redirect_rejected(self):
        FakeConnection.response=FakeResponse(b"",status=302,headers={"Location":"https://example/x"})
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",FakeConnection):
            self.code("DOCUMENTARY_HTTP_RESPONSE_INVALID",lambda:DocumentaryTransport(build_resource_manifest(),FirewallCounters()).get("FITS_STANDARD_4_0"))
    def test_10_content_length_cap(self):
        FakeConnection.response=FakeResponse(b"",headers={"Content-Length":str(5*1024*1024),
                                                           "Content-Type":"application/pdf"})
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",FakeConnection):
            counters=FirewallCounters(); transport=DocumentaryTransport(
                build_resource_manifest(),counters,receipt_directory=self.root/"receipts")
            self.code("RESOURCE_BODY_CAP_EXCEEDED",lambda:transport.get("FITS_STANDARD_4_0"))
        self.assertEqual(counters.application_body_bytes_read,0)
        self.assertEqual(FakeConnection.response.read_calls,0)
        receipt=validate_sealed(load_canonical_json(next((self.root/"receipts").iterdir())))
        self.assertEqual(receipt["declared_content_length"],5*1024*1024)
        self.assertEqual(receipt["application_body_bytes_read"],0)
        self.assertEqual(receipt["failure_code"],"RESOURCE_BODY_CAP_EXCEEDED")
    def test_10a_unknown_length_cap_plus_one_is_counted_before_failure(self):
        manifest=build_resource_manifest(); manifest["resources"][0]["byte_cap"]=10
        FakeConnection.response=FakeResponse(b"x"*11,headers={"Content-Type":"application/pdf"})
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",FakeConnection):
            counters=FirewallCounters(); transport=DocumentaryTransport(
                manifest,counters,receipt_directory=self.root/"receipts")
            self.code("RESOURCE_BODY_CAP_EXCEEDED",lambda:transport.get("FITS_STANDARD_4_0"))
        self.assertEqual(counters.application_body_bytes_read,11)
        self.assertEqual(counters.public_documentary_source_body_bytes,11)
        receipt=validate_sealed(load_canonical_json(next((self.root/"receipts").iterdir())))
        self.assertEqual(receipt["application_body_bytes_read"],11)
        self.assertFalse(receipt["wire_or_tls_bytes_claimed"])
    def test_10b_cumulative_excess_remains_counted(self):
        FakeConnection.response=FakeResponse(b"abcdef",headers={"Content-Type":"application/pdf"})
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",FakeConnection):
            counters=FirewallCounters(); transport=DocumentaryTransport(
                build_resource_manifest(),counters,receipt_directory=self.root/"receipts",
                global_body_cap=5)
            self.code("RESOURCE_BODY_CAP_EXCEEDED",lambda:transport.get("FITS_STANDARD_4_0"))
        self.assertEqual(counters.application_body_bytes_read,6)
        self.assertEqual(counters.public_documentary_source_body_bytes,6)
        receipt=validate_sealed(load_canonical_json(next((self.root/"receipts").iterdir())))
        self.assertEqual(receipt["counters"]["application_body_bytes_read"],6)
    def test_11_request_cap_precedes_connection(self):
        c=FirewallCounters(public_documentary_source_requests=REQUEST_CAP)
        self.code("REQUEST_CAP_EXCEEDED",lambda:DocumentaryTransport(build_resource_manifest(),c).get("FITS_STANDARD_4_0"))
    def test_11a_content_type_closed_per_resource(self):
        FakeConnection.response=FakeResponse(b"not pdf",headers={"Content-Length":"7","Content-Type":"text/plain"})
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",FakeConnection):
            transport=DocumentaryTransport(build_resource_manifest(),FirewallCounters(),
                                           receipt_directory=self.root/"receipts")
            self.code("DOCUMENTARY_CONTENT_TYPE_INVALID",lambda:transport.get("FITS_STANDARD_4_0"))
        receipt=validate_sealed(load_canonical_json(next((self.root/"receipts").iterdir())))
        self.assertEqual(receipt["resource_id"],"FITS_STANDARD_4_0")
        self.assertEqual(receipt["content_type"],"text/plain")
        self.assertEqual(receipt["application_body_bytes_read"],0)
    def test_11aa_http_failure_retains_headers_and_resource_identity(self):
        FakeConnection.response=FakeResponse(b"",status=503,headers={
            "Content-Length":"0","Content-Type":"application/pdf","X-Request-Id":"synthetic"})
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",FakeConnection):
            transport=DocumentaryTransport(build_resource_manifest(),FirewallCounters(),
                                           receipt_directory=self.root/"receipts")
            self.code("DOCUMENTARY_HTTP_RESPONSE_INVALID",lambda:transport.get("FITS_STANDARD_4_0"))
        receipt=validate_sealed(load_canonical_json(next((self.root/"receipts").iterdir())))
        self.assertEqual(receipt["status"],503)
        self.assertEqual(receipt["resource_id"],"FITS_STANDARD_4_0")
        self.assertEqual(receipt["headers"]["x-request-id"],"synthetic")
        self.assertEqual(receipt["application_body_bytes_read"],0)
    def test_11b_content_type_parameters_are_accepted(self):
        FakeConnection.response=FakeResponse(b"ok",headers={"Content-Length":"2","Content-Type":"application/pdf; charset=binary"})
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",FakeConnection):
            result=DocumentaryTransport(build_resource_manifest(),FirewallCounters()).get("FITS_STANDARD_4_0")
        self.assertEqual(result["body"],b"ok")

    def test_12_revision_binding_accepts_exact(self):
        ref=canonical({"object":{"type":"tag","sha":EXPECTED_TAG_OBJECT}})
        tag=canonical({"sha":EXPECTED_TAG_OBJECT,"object":{"type":"commit","sha":EXPECTED_COMMIT}})
        self.assertTrue(verify_revision_metadata(ref,tag)["verified"])
    def test_13_revision_mismatch_rejected(self):
        ref=canonical({"object":{"type":"tag","sha":"0"*40}}); tag=b"{}"
        self.code("DESITARGET_REVISION_MISMATCH",lambda:verify_revision_metadata(ref,tag))
    def test_14_safe_archive_extracts_complete_tree(self):
        target=self.root/"tree"; manifest=extract_archive_safely(archive_bytes(source_files()),target)
        self.assertEqual(len(manifest["entries"]),5)
        self.assertEqual(ARCHIVE_PREFIX,f"desitarget-{EXPECTED_COMMIT}")
    def test_15_archive_traversal_rejected(self):
        data=archive_bytes(source_files(),unsafe=f"{ARCHIVE_PREFIX}/../escape")
        self.code("ARCHIVE_MEMBER_UNSAFE",lambda:extract_archive_safely(data,self.root/"tree"))
    def test_16_archive_wrong_prefix_rejected(self):
        data=archive_bytes(source_files(),unsafe="other/file")
        self.code("ARCHIVE_MEMBER_UNSAFE",lambda:extract_archive_safely(data,self.root/"tree"))
    def test_16a_wrong_commit_archive_prefix_rejected(self):
        wrong=f"desitarget-{'0'*40}"
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode="w:gz") as archive:
            info=tarfile.TarInfo(f"{wrong}/py/desitarget/randoms.py"); info.size=1
            archive.addfile(info,io.BytesIO(b"x"))
        self.code("ARCHIVE_MEMBER_UNSAFE",lambda:extract_archive_safely(stream.getvalue(),self.root/"tree"))
    def test_17_missing_mandatory_file_rejected(self):
        files=source_files(); del files["doc/changes.rst"]
        self.code("MANDATORY_SOURCE_PATH_MISSING",lambda:extract_archive_safely(archive_bytes(files),self.root/"tree"))
    def test_18_tree_hash_deterministic(self):
        target=self.root/"tree"; extract_archive_safely(archive_bytes(source_files()),target)
        self.assertEqual(deterministic_tree_manifest(target),deterministic_tree_manifest(target))
    def test_19_search_negative_named_generator(self):
        target=self.root/"tree"; extract_archive_safely(archive_bytes(source_files()),target)
        self.assertEqual(search_source_tree(target)["named_product_generator_status"],NAMED_GENERATOR_NOT_FOUND)
    def test_20_search_terms_complete(self):
        target=self.root/"tree"; extract_archive_safely(archive_bytes(source_files()),target)
        self.assertEqual(tuple(search_source_tree(target)["search_terms"]),SEARCH_TERMS)
    def test_21_producer_trace_required_facts(self):
        target=self.root/"tree"; extract_archive_safely(archive_bytes(source_files()),target)
        trace=analyze_producer_source(target)
        self.assertTrue(trace["normal_PHOTSYS_S1_dtype_detected"])
        self.assertTrue(trace["normal_N_assignment_detected"]); self.assertTrue(trace["normal_S_assignment_detected"])
        self.assertTrue(trace["supplement_randoms_detected"]); self.assertTrue(trace["zeros_true_path_detected"])
        self.assertFalse(trace["zeros_true_output_dtype_contains_PHOTSYS"])
    def test_22_legacy_space_preserved(self):
        body=b"<p>survey-bricks-dr9-randoms-0.48.0.fits PHOTSYS: 'N' north, 'S' south, ' ' outside of footprint</p>"
        result=parse_legacy_document(body)
        self.assertEqual(result["outside_representation_literal"]," ")
        self.assertTrue(all(result["meanings"].values()))
    def test_23_generic_ascii_null_does_not_prove_bintable_A(self):
        text="A generic appendix mentions ASCII NULL and a null string with its first character elsewhere."
        result=parse_fits_standard_text(text,title="x",version="4",normative=True)
        self.assertFalse(result["BINTABLE_A_NULL_RULE"])
        self.assertFalse(result["representation_complete"])
    def test_23a_bintable_A_context_proves_only_its_rule(self):
        text=("7.3.2 Binary Table Data\nTFORMn Data Type 'A' Character string\n"
              "A character string may be terminated by ASCII NULL (hexadecimal 00). "
              "A null string has ASCII NULL as its first character.")
        result=parse_fits_standard_text(text,title="x",version="4",normative=True)
        self.assertTrue(result["BINTABLE_A_NULL_RULE"])
        self.assertTrue(result["ASCII_NULL_0x00"])
        self.assertFalse(result["ASCII_SPACE_0x20"])
        self.assertFalse(result["representation_complete"])
        record=result["evidence_records"][0]
        self.assertEqual(record["claim"],"BINTABLE_A_NULL_RULE")
        self.assertEqual(record["page"],1)
        self.assertIsNotNone(record["context_sha256"])
    def test_23b_ascii_null_definition_independent(self):
        result=parse_fits_standard_text("ASCII NULL is hexadecimal 00 and has all bits zero.",title="x",version="4",normative=True)
        self.assertTrue(result["ASCII_NULL_0x00"])
        self.assertFalse(result["BINTABLE_A_NULL_RULE"])
    def test_23c_ascii_space_definition_independent(self):
        result=parse_fits_standard_text("ASCII space is decimal 32, hexadecimal 20 (0x20).",title="x",version="4",normative=True)
        self.assertTrue(result["ASCII_SPACE_0x20"])
        self.assertFalse(result["BINTABLE_A_NULL_RULE"])
    def test_23d_all_three_required_for_complete_representation(self):
        text=("7.3.2 Binary Table Data\nTFORMn Data Type 'A' Character string\n"
              "A character string may be terminated by ASCII NULL (hexadecimal 00). "
              "A null string has ASCII NULL as its first character.\n"
              "ASCII NULL has all bits zero, hexadecimal 00.\n"
              "ASCII space is decimal 32, hexadecimal 20 (0x20).")
        result=parse_fits_standard_text(text,title="x",version="4",normative=True)
        self.assertTrue(result["representation_complete"])
        self.assertTrue(result["x00_distinct_from_x20"])
        self.assertFalse(result["survey_footprint_semantics_assigned"])
    def test_23e_ambiguous_context_stays_unresolved(self):
        text="Binary Table and TFORMn Data Type A occur here.\fASCII NULL hexadecimal 00; null string first character."
        result=parse_fits_standard_text(text,title="x",version="4",normative=True)
        self.assertFalse(result["BINTABLE_A_NULL_RULE"])
        self.assertFalse(result["representation_complete"])
    def test_24_claim_matrix_closed(self):
        self.assertEqual(validate_claim_matrix(initial_claim_matrix()),initial_claim_matrix())
    def test_25_claim_matrix_bad_status_rejected(self):
        rows=initial_claim_matrix(); rows[0]["status"]="PASS"
        self.code("CLAIM_MATRIX_INVALID",lambda:validate_claim_matrix(rows))
    def test_26_counts_alone_inconclusive(self):
        self.assertEqual(outcome_gate(official_categories=False,fits_representation=False,exact_producer=False,exact_outside_path=False,serialization_preserves=False,named_product_generation=False,documentary_physical_mismatch=True,unresolved_conflict=False,count_coincidence=True),INCONCLUSIVE)
    def test_27_zero_init_alone_inconclusive(self):
        self.assertEqual(outcome_gate(official_categories=False,fits_representation=True,exact_producer=False,exact_outside_path=False,serialization_preserves=False,named_product_generation=False,documentary_physical_mismatch=True,unresolved_conflict=False,zero_initialization=True),INCONCLUSIVE)
    def test_28_missing_named_generation_inconclusive(self):
        self.assertEqual(outcome_gate(official_categories=True,fits_representation=True,exact_producer=True,exact_outside_path=True,serialization_preserves=True,named_product_generation=False,documentary_physical_mismatch=True,unresolved_conflict=False),INCONCLUSIVE)
    def test_29_validate_inputs_no_network(self):
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",side_effect=AssertionError("network")):
            self.assertEqual(validate_frozen_inputs()["network_requests"],0)
    def test_30_historical_attempt_is_closed_and_not_dry_runnable(self):
        self.assertTrue(AUTHORIZATION_PATH.exists())
        self.assertTrue(OUTPUT_ROOT.exists())
        self.code("RESEARCH_CANDIDATE_INVALID",dry_run)
    def test_31_cli_help(self):
        with self.assertRaises(SystemExit) as caught,contextlib.redirect_stdout(io.StringIO()):cli.main(["--help"])
        self.assertEqual(caught.exception.code,0)
    def test_32_cli_research_without_authorization_blocked(self):
        with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(cli.main(["--research-zero-byte-provenance"]),2)
    def test_33_synthetic_mode_unexecuted_without_authorization(self):
        with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(cli.main(["--run-synthetic-zero-initialization-check"]),2)
    def test_34_firewall_has_no_data_capability(self):
        counters=FirewallCounters(); self.assertTrue(counters.data_clean())
        self.assertEqual(sum(counters.object().values()),0)
    def test_35_historical_candidate_and_authorization_are_preserved(self):
        self.assertEqual(file_sha256(CANDIDATE_PATH),
                         "6ef3d2283c50b72393f184caf3f4ba0ba1ce8d4abf996437c9bd046b3930cebc")
        self.assertEqual(file_sha256(AUTHORIZATION_PATH),
                         "26f971c7024dce61ee17a28456c77c30ab35dcb9b13fb9b6b94df2b55720d7bd")
        self.code("RESEARCH_CANDIDATE_INVALID",
                  lambda:validate_candidate(CANDIDATE_PATH,authorization_absent=False))
    def test_36_completed_matrix_keeps_producer_inference_separate(self):
        legacy={"meanings":{"N":True,"S":True," ":True}}
        fits={"BINTABLE_A_NULL_RULE":True,"ASCII_NULL_0x00":True,
              "ASCII_SPACE_0x20":True,"x00_distinct_from_x20":True}
        trace={"zero_initialization_before_assignment_proven":False,
               "outside_rows_raw_0x00_proven":False,
               "serialization_preserves_PHOTSYS_proven":False}
        rows=completed_claim_matrix(legacy=legacy,fits=fits,trace=trace,named_generation_proven=False)
        self.assertEqual(rows[2]["status"],"SUPPORTED")
        self.assertEqual(rows[5]["status"],"UNRESOLVED")
        self.assertEqual(rows[9]["status"],"UNRESOLVED")


if __name__ == "__main__": unittest.main()
