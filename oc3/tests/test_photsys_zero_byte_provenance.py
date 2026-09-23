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
        self.headers = headers or {"Content-Length": str(len(body)), "Content-Encoding": "identity"}
    def getheaders(self): return list(self.headers.items())
    def read(self, amount): return self.body[:amount]


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
        FakeConnection.response=FakeResponse(b"",headers={"Content-Length":str(5*1024*1024)})
        with patch("oc3lib.photsys_zero_byte_provenance.http.client.HTTPSConnection",FakeConnection):
            self.code("RESOURCE_BODY_CAP_EXCEEDED",lambda:DocumentaryTransport(build_resource_manifest(),FirewallCounters()).get("FITS_STANDARD_4_0"))
    def test_11_request_cap_precedes_connection(self):
        c=FirewallCounters(public_documentary_source_requests=REQUEST_CAP)
        self.code("REQUEST_CAP_EXCEEDED",lambda:DocumentaryTransport(build_resource_manifest(),c).get("FITS_STANDARD_4_0"))

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
    def test_15_archive_traversal_rejected(self):
        data=archive_bytes(source_files(),unsafe=f"{ARCHIVE_PREFIX}/../escape")
        self.code("ARCHIVE_MEMBER_UNSAFE",lambda:extract_archive_safely(data,self.root/"tree"))
    def test_16_archive_wrong_prefix_rejected(self):
        data=archive_bytes(source_files(),unsafe="other/file")
        self.code("ARCHIVE_MEMBER_UNSAFE",lambda:extract_archive_safely(data,self.root/"tree"))
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
    def test_23_fits_distinguishes_nul_space(self):
        text="ASCII NULL is a null string when the first character is zero. ASCII space character is 32 (0x20)."
        result=parse_fits_standard_text(text,title="x",version="4",section="s",page="1",normative=True)
        self.assertTrue(result["x00_distinct_from_x20"])
        self.assertFalse(result["survey_footprint_semantics_assigned"])
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
    def test_30_dry_run_boundary(self): self.assertEqual(dry_run()["state"],READY)
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
    def test_35_candidate_exact(self):
        self.assertEqual(validate_candidate(),build_candidate(implementation_hash(PROJECT)))
    def test_36_completed_matrix_keeps_producer_inference_separate(self):
        legacy={"meanings":{"N":True,"S":True," ":True}}
        fits={"bintable_A_first_character_0x00":True,"x00_distinct_from_x20":True,"x20_ascii_space":True}
        trace={"zero_initialization_before_assignment_proven":False,
               "outside_rows_raw_0x00_proven":False,
               "serialization_preserves_PHOTSYS_proven":False}
        rows=completed_claim_matrix(legacy=legacy,fits=fits,trace=trace,named_generation_proven=False)
        self.assertEqual(rows[2]["status"],"SUPPORTED")
        self.assertEqual(rows[5]["status"],"UNRESOLVED")
        self.assertEqual(rows[9]["status"],"UNRESOLVED")


if __name__ == "__main__": unittest.main()
