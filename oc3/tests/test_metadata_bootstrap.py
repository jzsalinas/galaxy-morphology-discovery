"""Synthetic/offline verification for METADATA_BOOTSTRAP_ONLY + Clarification 001."""
from __future__ import annotations

from dataclasses import replace
import gzip
import hashlib
import inspect
import json
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
from types import MappingProxyType
import unittest

import numpy as np
from astropy.io import fits

from oc3lib.core import file_hash, implementation_hash
from oc3lib.metadata_bootstrap import *
import oc3lib.metadata_bootstrap as bootstrap
from oc3lib.metadata_value_semantics import (
    LocallyComputedFullFileSha256,
    validate_brickname, validate_provider_full_file_integrity,
)
from oc3lib.provider_physical_contracts import (
    ACTIVATION_STATES, PHYSICAL_CONTRACT_HASHES, PRODUCTION_PHYSICAL_CONTRACTS,
    FrozenPhysicalContract, PhysicalRole, ROOT_SUMMARY, NORTH_SUMMARY,
    SOUTH_SUMMARY, SOUTH_PATCH_LIST, validate_fits_structure,
)
from oc3lib.provider_schema import FIELD_BY_ID, FieldClass, FieldId


PROJECT = Path(__file__).resolve().parents[2]
ATTEMPT = PROJECT / ATTEMPT_RELATIVE_DIRECTORY
PROBE = PROJECT / "oc3/provider_contract_probe/OC3-PHYSICAL-CONTRACT-PROBE-001"
PROBE_SNAPSHOT = {
    "PROBE_CHECKSUM_EVIDENCE.json": (1109, "f464983d87ef4ab2776b699a54490874667c7f4a7ca138269180d8467defee3f"),
    "PROBE_EVENTS.json": (145, "d130134b7bb46a612c8213aba80b0d5d613303d04d1870063b5d0a5677e75fd0"),
    "PROBE_LEDGER.sqlite": (40960, "8bd834e3a1fa28d820d7ac81f8fe049749761f518b569cc2d915beb32191b441"),
    "PROBE_PHYSICAL_CONTRACT_CANDIDATES.json": (15421, "eaa8287fab7c4de44dc265239dcf3b9e9e56f5c2adce4334711634cb9e9b7eb1"),
    "PROBE_TERMINAL.json": (257, "27b944d654045c314505e548242eee85416cf9391ffc337d5f4a834fbb3c84e3"),
    "PROBE_TRANSPORT_EVIDENCE.json": (2462, "cd0248193669bb2d303ca55fb24e3ab46f9b0ac2aefc59086c3df2dd49f4975a"),
    "compressed_prefix/NORTH_SUMMARY/0.part": (65536, "7b0cb006d16f193cdcef2120169d039300aa56d9aca863decc3d654c20be4cd6"),
    "compressed_prefix/ROOT_SUMMARY/0.part": (65536, "28c7b004fbbcf9cd02999c6345b6b5f428c901bf8b76fc10d6612aa29d5ded5e"),
    "compressed_prefix/SOUTH_SUMMARY/0.part": (65536, "383aa7a812405560e418efff4109268979c3ad45118e9d00ffbb0ad3c666748b"),
    "transport/NORTH_SUMMARY.head.json": (508, "833b31cdccb786069e07c2bbf0e286ca8a84c410399ab3b9ad1fa28e321e0a9c"),
    "transport/ROOT_SUMMARY.head.json": (490, "bf79a2189fd3ae09863059f4c5bcd5ae6531a4d242d75cd813603f3b8ddc972a"),
    "transport/SOUTH_PATCH_LIST.head.json": (410, "9d8ce43f7bc76529045a80c495d47787c1d7d539cbbd142d2d0889919edc6c3c"),
    "transport/SOUTH_SUMMARY.head.json": (508, "71636341463e738a601cf8aa8c24131e900762bb802ac5d17b12751bf24cb166"),
}


def assert_code(case: unittest.TestCase, code: str, function, *args, **kwargs):
    with case.assertRaises(BootstrapError) as caught:
        function(*args, **kwargs)
    case.assertEqual(caught.exception.code, code)


def resource(role=PhysicalRole.ROOT_SUMMARY, size=4) -> MetadataResource:
    suffix = "patch.fits" if role is PhysicalRole.SOUTH_PATCH_LIST else "summary.fits.gz"
    return MetadataResource(role, f"https://synthetic.invalid/{role.value}/{suffix}", size,
                            f"RAW_IMMUTABLE/{role.value}/{suffix}",
                            "identity" if role is PhysicalRole.SOUTH_PATCH_LIST else "gzip",
                            '"5ffdf047-7bc0"' if role is PhysicalRole.SOUTH_PATCH_LIST else None,
                            "Tue, 12 Jan 2021 18:53:59 GMT" if role is PhysicalRole.SOUTH_PATCH_LIST else None)


def head_response(item: MetadataResource, **changes) -> TransportResponse:
    headers = {"content-length": str(item.expected_length)}
    if item.role is PhysicalRole.SOUTH_PATCH_LIST:
        headers.update(etag=item.expected_etag, **{"last-modified": item.expected_last_modified})
    values = dict(status=200, requested_url=item.url, final_url=item.url,
                  redirect_history=(), headers=headers, body_chunks=())
    values.update(changes)
    return TransportResponse(**values)


def get_response(item: MetadataResource, body=b"DATA", **changes) -> TransportResponse:
    result = head_response(item)
    values = dict(status=result.status, requested_url=result.requested_url,
                  final_url=result.final_url, redirect_history=result.redirect_history,
                  headers=result.headers, body_chunks=(body,))
    values.update(changes)
    return TransportResponse(**values)


def synthetic_rights(aggregate: str) -> RightsBinding:
    value = {
        "binding_type": RIGHTS_BINDING_TYPE,
        "schema_version": 1,
        "canonicalization": CANONICALIZATION_VERSION,
        "attempt_id": ATTEMPT_ID,
        "scope": BOOTSTRAP_SCOPE,
        "local_scientific_acquisition": "ALLOWED_FOR_THIS_PROTOCOL",
        "local_preservation": "ALLOWED_FOR_THIS_PROTOCOL",
        "redistribution": False,
        "FITS_OR_DERIVED_REDISTRIBUTION": "DISABLED_UNRESOLVED",
        "execution_plan_sha256": EXECUTION_PLAN_SHA256,
        "base_spec_sha256": BASE_SPEC_SHA256,
        "clarification_sha256": CLARIFICATION_001_SHA256,
        "implementation_aggregate": aggregate,
        "environment_fingerprint": ENVIRONMENT_FINGERPRINT,
        "resources": resource_binding_values(),
        "reviewed_evidence": [{
            "path": "OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC.md",
            "sha256": BASE_SPEC_SHA256,
        }],
        "reviewed": True,
        "synthetic_only": True,
    }
    raw = canonical(value) + b"\n"
    return RightsBinding(MappingProxyType(value), hashlib.sha256(raw).hexdigest(), True)


def synthetic_candidate(argv, aggregate, rights_sha) -> AuthorizationCandidate:
    value = {
        "schema_version": 1, "canonicalization": CANONICALIZATION_VERSION,
        "candidate_type": CANDIDATE_TYPE, "candidate_state": CANDIDATE_STATE,
        "attempt_id": ATTEMPT_ID, "scope": BOOTSTRAP_SCOPE,
        "execution_mode": FIRST_EXECUTION_MODE, "patch_model": PATCH_MODEL,
        "execution_plan_sha256": EXECUTION_PLAN_SHA256,
        "plan_post_activation_review_sha256": PLAN_POST_ACTIVATION_REVIEW_SHA256,
        "rights_binding_path": str(argv[5]), "rights_binding_sha256": rights_sha,
        "rights_review_sha256": RIGHTS_REVIEW_SHA256,
        "base_spec_sha256": BASE_SPEC_SHA256, "clarification_sha256": CLARIFICATION_001_SHA256,
        "implementation_aggregate": aggregate, "environment_fingerprint": ENVIRONMENT_FINGERPRINT,
        "resources": resource_binding_values(), "resource_caps": resource_cap_values(),
        "command_vector": list(argv), "command_sha256": command_sha256(argv),
        "negative_capabilities": dict(NEGATIVE_CAPABILITIES),
        "final_authorization_path": str(argv[3]),
        "candidate_created_at_utc": "2026-09-19T00:00:00Z",
    }
    raw = canonical(value) + b"\n"
    return AuthorizationCandidate(MappingProxyType(value), hashlib.sha256(raw).hexdigest())


def synthetic_auth(argv, aggregate, rights_sha, *, resume=False, candidate_sha="c" * 64,
                   candidate_path="/synthetic/candidate.json"):
    value = {
        "authorization_type": RESUME_AUTHORIZATION_TYPE if resume else FIRST_AUTHORIZATION_TYPE,
        "authorization_state": "FINAL_HUMAN_AUTHORIZATION",
        "schema_version": 1 if resume else 2,
        "canonicalization": CANONICALIZATION_VERSION,
        "authorized": True, "scope": BOOTSTRAP_SCOPE, "attempt_id": ATTEMPT_ID,
        "authorized_by": "SYNTHETIC_TEST_HARNESS",
        "authorized_at_utc": "2026-09-19T00:00:00Z",
        "attempt_directory": ATTEMPT_RELATIVE_DIRECTORY,
        "execution_mode": RESUME_EXECUTION_MODE if resume else FIRST_EXECUTION_MODE,
        "execution_plan_sha256": EXECUTION_PLAN_SHA256,
        "base_spec_sha256": BASE_SPEC_SHA256,
        "clarification_sha256": CLARIFICATION_001_SHA256,
        "implementation_aggregate": aggregate, "environment_fingerprint": ENVIRONMENT_FINGERPRINT,
        "patch_model": PATCH_MODEL, "resources": resource_binding_values(),
        "resource_caps": resource_cap_values(), "command_argv": list(argv),
        "command_sha256": command_sha256(argv), "rights_binding_sha256": rights_sha,
        "negative_capabilities": dict(NEGATIVE_CAPABILITIES),
        "synthetic_only": True,
    }
    if resume:
        value.update(first_run_authorization_sha256="a" * 64, ledger_identity="ledger",
                     ledger_watermark=7, consumed_counters={"requests": 3},
                     remaining_caps={"requests": 9}, completed_raw_resources=["ROOT_SUMMARY"],
                     pending_resources=["NORTH_SUMMARY", "SOUTH_SUMMARY", "SOUTH_PATCH_LIST"],
                     existing_staging_state=[])
    else:
        value.update(authorization_candidate_path=candidate_path,
                     authorization_candidate_sha256=candidate_sha)
    return value


def make_fits(path: Path, contract: FrozenPhysicalContract, rows=2, *, gzip_output=False):
    columns = []
    for index, column in enumerate(contract.columns):
        form = column.tform
        names = [f"{index % 10000:04d}{'p' if index % 2 == 0 else 'm'}{index % 1000:03d}".encode("ascii")
                 for index in range(1, rows + 1)]
        if form == "8A": values = np.asarray(names, dtype="S8")
        elif form == "I": values = np.asarray([1 + i for i in range(rows)], dtype=np.int16)
        elif form == "J":
            base = 101 if column.ttype.lower() == "brickid" else 2_000_000_001 + index
            values = np.asarray([base + i for i in range(rows)], dtype=np.int32)
        elif form == "6J": values = np.asarray([[0, 1, 0, 0, 0, 0]] * rows, dtype=np.int32)
        elif form == "4I": values = np.asarray([[30001, 30002, 30003, 30004]] * rows, dtype=np.int16)
        elif form == "4E": values = np.asarray([[12345.25, 12346.25, 12347.25, 12348.25]] * rows, dtype=np.float32)
        elif form == "E": values = np.asarray([12345.5 + i for i in range(rows)], dtype=np.float32)
        elif form == "D": values = np.asarray([10.25 + i for i in range(rows)], dtype=np.float64)
        elif form == "L": values = np.asarray([True] * rows, dtype=bool)
        else: raise AssertionError(form)
        columns.append(fits.Column(name=column.ttype, format=form, array=values))
    plain = path.with_suffix(".fits") if gzip_output else path
    fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns(columns)]).writeto(plain, checksum=False)
    if gzip_output:
        path.write_bytes(gzip.compress(plain.read_bytes(), mtime=0)); plain.unlink()
    return path, replace(contract, naxis2=rows)


def probe_exact(case):
    observed = {str(p.relative_to(PROBE)): p for p in PROBE.rglob("*") if p.is_file()}
    case.assertEqual(set(observed), set(PROBE_SNAPSHOT))
    for name, (size, sha) in PROBE_SNAPSHOT.items():
        case.assertEqual((observed[name].stat().st_size, file_hash(observed[name])), (size, sha))


class MetadataBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="oc3_metadata_bootstrap_synthetic_")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def ledger(self, caps=RESOURCE_CAPS):
        return BootstrapLedger(self.root / f"ledger-{len(list(self.root.glob('ledger-*')))}.sqlite",
                               {"synthetic": True}, caps)

    def fixture(self, contract=ROOT_SUMMARY, rows=2):
        path = self.root / f"{contract.role.value}-{len(list(self.root.iterdir()))}.fits.gz"
        return make_fits(path, contract, rows, gzip_output=contract.compression == "gzip")


def c01(t): t.assertEqual(file_hash(PROJECT / "OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC.md"), BASE_SPEC_SHA256)
def c02(t): t.assertEqual(file_hash(PROJECT / "OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC_CLARIFICATION_001.md"), CLARIFICATION_001_SHA256)
def c03(t): t.assertEqual(json.loads((PROJECT / "oc3/environment_setup/ENVIRONMENT.json").read_text())["environment_sha256"], ENVIRONMENT_FINGERPRINT)
def c04(t): t.assertEqual(PRE_METADATA_BOOTSTRAP_INFRASTRUCTURE, "f3f64a05c581e2c74d2cb80c2a2e499ab7c76cbd8eba7ad7f9e5f40a49e48581")
def c05(t): probe_exact(t)
def c06(t): t.assertEqual(RESOURCE_CAPS.http_body_bytes, 128 * 2**20)
def c07(t): t.assertEqual((EXPECTED_AGGREGATE_BYTES, sum(x.expected_length for x in RESOURCES.values())), (89461646, 89461646))
def c08(t): t.assertEqual(RESOURCE_CAPS.single_resource_body_bytes, 64 * 2**20)
def c09(t): t.assertEqual(RESOURCE_CAPS.requests, 12)
def c10(t): t.assertEqual(RESOURCE_CAPS.concurrency, 1)
def c11(t): t.assertEqual(RESOURCE_CAPS.retry_additional_per_exact_identity, 1)
def c12(t): t.assertEqual((RESOURCE_CAPS.disk_bytes, RESOURCE_CAPS.io_bytes, RESOURCE_CAPS.ram_bytes, RESOURCE_CAPS.compute_seconds, RESOURCE_CAPS.wall_seconds), (268435456,536870912,1073741824,300,900))
def c13(t):
    items = RESOURCES; transport = SyntheticTransport([head_response(x) for x in items.values()])
    ledger = t.ledger(); evidence = collect_pretransfer_evidence(transport, ledger, items)
    t.assertEqual(set(evidence), set(PhysicalRole)); t.assertTrue(all(x[0] == "HEAD" for x in transport.calls)); ledger.close()
def c14(t):
    x=resource(); assert_code(t,"METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP",validate_head,x,head_response(x,headers={"content-length":"3"}))
def c15(t):
    x=resource(PhysicalRole.NORTH_SUMMARY); assert_code(t,"METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP",validate_head,x,head_response(x,status=404))
def c16(t):
    x=resource(PhysicalRole.SOUTH_SUMMARY); assert_code(t,"METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP",validate_head,x,head_response(x,final_url=x.url+"/"))
def c17(t):
    x=resource(PhysicalRole.SOUTH_PATCH_LIST); h=dict(head_response(x).headers); h["content-length"]="3"; assert_code(t,"PATCH_LIST_REPRESENTATION_DRIFT_STOP",validate_head,x,head_response(x,headers=h))
def c18(t):
    x=resource(PhysicalRole.SOUTH_PATCH_LIST); h=dict(head_response(x).headers); h["etag"]='"bad"'; assert_code(t,"PATCH_LIST_REPRESENTATION_DRIFT_STOP",validate_head,x,head_response(x,headers=h))
def c19(t):
    x=resource(PhysicalRole.SOUTH_PATCH_LIST); h=dict(head_response(x).headers); h["last-modified"]="bad"; assert_code(t,"PATCH_LIST_REPRESENTATION_DRIFT_STOP",validate_head,x,head_response(x,headers=h))
def c20(t):
    x=resource(); assert_code(t,"METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP",validate_head,x,head_response(x,redirect_history=(x.url,)))
def c21(t):
    x=resource(); h=dict(head_response(x).headers); h["content-encoding"]="gzip"; assert_code(t,"METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP",validate_head,x,head_response(x,headers=h))
def c22(t):
    x=resource(); h=validate_head(x,head_response(x)); r=get_response(x); validate_get_headers(x,h,r); t.assertEqual(validate_complete_body(x,r),4)
def c23(t):
    x=resource(); h=validate_head(x,head_response(x)); assert_code(t,"METADATA_TRANSPORT_INTEGRITY_FAILURE",validate_get_headers,x,h,get_response(x,status=206))
def c24(t):
    x=resource(); h=validate_head(x,head_response(x)); headers=dict(head_response(x).headers); headers["content-range"]="bytes 0-3/4"; assert_code(t,"METADATA_TRANSPORT_INTEGRITY_FAILURE",validate_get_headers,x,h,get_response(x,headers=headers))
def c25(t): assert_code(t,"METADATA_TRANSPORT_INTEGRITY_FAILURE",validate_complete_body,resource(),get_response(resource(),b"DAT"))
def c26(t): assert_code(t,"METADATA_TRANSPORT_INTEGRITY_FAILURE",validate_complete_body,resource(),get_response(resource(),b"DATAX"))
def c27(t):
    l=t.ledger(); x=resource(); q=l.begin_request("GET",x,ordinal=1); l.finish_request(q,"FAILED",2); t.assertEqual(l.counters()["body_bytes"],2); l.close()
def c28(t):
    l=t.ledger(); x=resource(); q=l.begin_request("GET",x,ordinal=1); l.finish_request(q,"FAILED",1); t.assertTrue(l.begin_request("GET",x,ordinal=2,retry_of=q)); l.close()
def c29(t):
    l=t.ledger(); s=AttemptStorage(t.root/"attempt",l,synthetic_only=True); x=resource(); i,p,n=s.write_staging(x,1,[b"x"]); assert_code(t,"METADATA_TRANSPORT_INTEGRITY_FAILURE",s.publish_raw,x,i,p,n,"q"); l.close()
def c30(t):
    l=t.ledger(); s=AttemptStorage(t.root/"attempt",l,synthetic_only=True); x=resource(); i,p,n=s.write_staging(x,1,[b"DATA"]); s.publish_raw(x,i,p,n,"q"); i2,p2,n2=s.write_staging(x,2,[b"DATA"]); assert_code(t,"METADATA_LOCAL_STATE_CONFLICT",s.publish_raw,x,i2,p2,n2,"q2"); l.close()
def c31(t):
    l=t.ledger(); s=AttemptStorage(t.root/"attempt",l,synthetic_only=True); x=resource(); i,p,n=s.write_staging(x,1,[b"DATA"]); a=s.publish_raw(x,i,p,n,"q"); t.assertEqual(a.path.read_bytes(),b"DATA"); t.assertFalse(p.exists()); l.close()
def c32(t):
    l=t.ledger(); s=AttemptStorage(t.root/"attempt",l,synthetic_only=True); x=resource(); i,p,n=s.write_staging(x,1,[b"DATA"]); s.publish_raw(x,i,p,n,"q"); t.assertEqual(s.incomplete_staging(),()); l.close()
def c33(t):
    l=t.ledger(); s=AttemptStorage(t.root/"attempt",l,synthetic_only=True); s.write_staging(resource(),1,[b"x"]); t.assertEqual(len(s.incomplete_staging()),1); l.close()
def c34(t):
    l=t.ledger(); s=AttemptStorage(t.root/"attempt",l,synthetic_only=True); t.assertNotEqual(s.staging_path(PhysicalRole.ROOT_SUMMARY,1)[0],s.staging_path(PhysicalRole.ROOT_SUMMARY,2)[0]); l.close()
def c35(t):
    values=[PhysicalRole.ROOT_SUMMARY,"u","a"*64,ATTEMPT_ID,"p",1,"b"*64,"c"*64,ENVIRONMENT_FINGERPRINT,"d"*64,"r",1,"now","0"*64,Path("x"),object()]
    assert_code(t,"METADATA_COMPLETE_DIGEST_PROVENANCE_REQUIRED",BootstrapRawDigest,*values)
def digest_fixture(t, data=b"DATA"):
    x=resource(size=len(data)); l=t.ledger(); s=AttemptStorage(t.root/"attempt",l,synthetic_only=True); i,p,n=s.write_staging(x,1,[data]); a=s.publish_raw(x,i,p,n,"q"); d=derive_raw_digest(a,x,authorization_sha256="a"*64,implementation_aggregate="b"*64,transport_receipt_sha256="c"*64,ledger=l,timestamp="2026-01-01T00:00:00+00:00"); return x,l,s,a,d
def c36(t):
    _,l,_,_,d=digest_fixture(t); t.assertEqual(d.raw_sha256,hashlib.sha256(b"DATA").hexdigest()); l.close()
def c37(t):
    _,l,_,_,d=digest_fixture(t); t.assertEqual(d.raw_byte_length,4); l.close()
def c38(t): t.assertTrue(validate_provider_full_file_integrity(PhysicalRole.ROOT_SUMMARY,LocallyComputedFullFileSha256(ROOT_SUMMARY.expected_provider_full_file_sha256)))
def c39(t):
    _,l,_,_,d=digest_fixture(t); assert_code(t,"METADATA_FULL_FILE_INTEGRITY_FAILURE",validate_regional_provider_integrity,d); l.close()
def c40(t): t.assertTrue(validate_provider_full_file_integrity(PhysicalRole.NORTH_SUMMARY,LocallyComputedFullFileSha256(NORTH_SUMMARY.expected_provider_full_file_sha256)))
def c41(t): t.assertTrue(validate_provider_full_file_integrity(PhysicalRole.SOUTH_SUMMARY,LocallyComputedFullFileSha256(SOUTH_SUMMARY.expected_provider_full_file_sha256)))
def c42(t):
    p,c=t.fixture(ROOT_SUMMARY); t.assertEqual(validate_fits_structure(p,c),c.sha256)
def c43(t):
    p,c=t.fixture(NORTH_SUMMARY); t.assertEqual(validate_fits_structure(p,c),c.sha256)
def c44(t):
    p,c=t.fixture(SOUTH_SUMMARY); t.assertEqual(validate_fits_structure(p,c),c.sha256)
def c45(t):
    p,c=make_fits(t.root/"patch.fits",SOUTH_PATCH_LIST,SOUTH_PATCH_LIST.naxis2)
    e=validate_patch_header_only(p,c); t.assertEqual((p.stat().st_size,e.physical_contract_sha256,e.payload_bytes_observed),(31680,c.sha256,0))
def c46(t):
    p,c=t.fixture(ROOT_SUMMARY); _,l,_,_,d=digest_fixture(t,p.read_bytes())
    assert_code(t,"METADATA_PHYSICAL_CONTRACT_FAILURE",validate_bootstrap_physical,d,replace(c,naxis1=71)); l.close()
def decoded_regional(t):
    p,c=t.fixture(NORTH_SUMMARY); s=SelectiveFitsDecoder().decode(p,c); rows=list(s.rows); return rows,s.instrumentation,c
def c47(t):
    rows,m,c=decoded_regional(t); t.assertEqual(m.opaque_bytes_transited,c.naxis1*c.naxis2); t.assertEqual(m.cell_values_decoded,16*c.naxis2)
def c48(t): t.assertEqual(decoded_regional(t)[1].forbidden_cell_decode_count,0)
def c49(t): t.assertEqual(decoded_regional(t)[1].forbidden_value_materialization_count,0)
def c50(t): t.assertEqual(decoded_regional(t)[1].forbidden_value_log_count,0)
def c51(t): t.assertEqual(decoded_regional(t)[1].forbidden_value_serialization_count,0)
def c52(t):
    p,c=t.fixture(ROOT_SUMMARY); rows=list(SelectiveFitsDecoder().decode(p,c).rows); t.assertEqual(set(rows[0]),{x for x in FieldId if x.value.startswith("root.")})
def c53(t):
    rows,_,_=decoded_regional(t); t.assertEqual(len(rows[0]),16); t.assertTrue(all(FIELD_BY_ID[x].classification is FieldClass.TECHNICAL_ALLOWED for x in rows[0]))
def c54(t):
    rows,_,_=decoded_regional(t); t.assertEqual((rows[0][FieldId.REG_NEXPHIST_Z],rows[0][FieldId.REG_BRICKID],rows[0][FieldId.REG_AREA]),((0,1,0,0,0,0),101,10.25))
def c55(t):
    rows,m,_=decoded_regional(t); t.assertNotIn("30001",str(rows)); t.assertEqual(m.forbidden_cell_decode_count,0)
def c56(t): t.assertIn("hdu.data",SelectiveFitsDecoder.prohibited_real_apis)
def c57(t): t.assertIn("Table.read",SelectiveFitsDecoder.prohibited_real_apis)
def c58(t): t.assertIn("FITS_rec",SelectiveFitsDecoder.prohibited_real_apis)
def c59(t):
    _,l,_,_,d=digest_fixture(t); t.assertRegex(d.raw_sha256,r"^[0-9a-f]{64}$"); l.close()
def c60(t):
    f=PatchPayloadFirewall(); t.assertEqual(f.payload_decoder_calls,0)
def c61(t): t.assertFalse(hasattr(PatchHeaderEvidence,"release"))
def c62(t): t.assertFalse(hasattr(PatchHeaderEvidence,"brickid"))
def c63(t): t.assertFalse(hasattr(PatchHeaderEvidence,"brickname"))
def c64(t): t.assertNotIn("patch",inspect.getsource(validate_regional_semantics).lower())
def c65(t):
    item=RESOURCES[PhysicalRole.SOUTH_PATCH_LIST]; data=b"P"*item.expected_length
    ledger=t.ledger(); storage=AttemptStorage(t.root/"patch-attempt",ledger,synthetic_only=True)
    identity,path,size=storage.write_staging(item,1,[data]); artifact=storage.publish_raw(item,identity,path,size,"patch-request")
    digest=derive_raw_digest(artifact,item,authorization_sha256="a"*64,
        implementation_aggregate="b"*64,transport_receipt_sha256="c"*64,
        ledger=ledger,timestamp="2026-01-01T00:00:00+00:00")
    evidence=patch_acquisition_evidence(digest,item,synthetic_only=True)
    t.assertTrue(evidence.synthetic_only); t.assertEqual(terminal_outcome(["METADATA_BOOTSTRAP_PARTIALLY_RESOLVED"]),"METADATA_BOOTSTRAP_PARTIALLY_RESOLVED"); ledger.close()
def c66(t):
    t.assertFalse(ACTIVATION_STATES[PhysicalRole.SOUTH_PATCH_LIST].full_file_integrity_bound)
def c67(t): assert_code(t,"METADATA_TERMINAL_OUTCOME_MISSING",terminal_outcome,["METADATA_BOOTSTRAP_RESOLVED"])
def root_rows():
    return [{FieldId.ROOT_BRICKNAME:validate_brickname(b"0001p001"),FieldId.ROOT_BRICKID:101,FieldId.ROOT_RA:1.,FieldId.ROOT_DEC:2.,FieldId.ROOT_RA1:0.,FieldId.ROOT_RA2:2.,FieldId.ROOT_DEC1:1.,FieldId.ROOT_DEC2:3.}]
def regional_rows(name=b"0001p001",bid=101):
    return [{FieldId.REG_BRICKNAME:validate_brickname(name),FieldId.REG_BRICKID:bid,FieldId.REG_RA:1.,FieldId.REG_DEC:2.,FieldId.REG_RA1:0.,FieldId.REG_RA2:2.,FieldId.REG_DEC1:1.,FieldId.REG_DEC2:3.,FieldId.REG_AREA:1.,FieldId.REG_SURVEY_PRIMARY:True,FieldId.REG_NEXP_G:1,FieldId.REG_NEXP_R:1,FieldId.REG_NEXP_Z:1}]
def c68(t): t.assertEqual(validate_brickname(b"0001p001").semantics_version,"OC3_BRICKNAME_SEMANTICS_V1")
def c69(t): t.assertEqual(GRZ_PREDICATE_VERSION,"GRZ_MEDIAN_PRESENT_V1")
def c70(t):
    rows=root_rows()*2; assert_code(t,"METADATA_VALUE_SEMANTICS_FAILURE",validate_root_semantics,rows)
def c71(t): t.assertEqual(validate_regional_semantics(PhysicalRole.NORTH_SUMMARY,regional_rows(),validate_root_semantics(root_rows())).exact_root_matches,1)
def c72(t): t.assertEqual(validate_regional_semantics(PhysicalRole.SOUTH_SUMMARY,regional_rows(),validate_root_semantics(root_rows())).exact_root_matches,1)
def c73(t): assert_code(t,"METADATA_VALUE_SEMANTICS_FAILURE",validate_regional_semantics,PhysicalRole.NORTH_SUMMARY,regional_rows(b"9999m999"),validate_root_semantics(root_rows()))
def c74(t):
    rows=root_rows()+[{**root_rows()[0],FieldId.ROOT_BRICKID:102}]; assert_code(t,"METADATA_VALUE_SEMANTICS_FAILURE",validate_root_semantics,rows)
def c75(t): assert_code(t,"METADATA_VALUE_SEMANTICS_FAILURE",validate_regional_semantics,PhysicalRole.SOUTH_SUMMARY,regional_rows(bid=999),validate_root_semantics(root_rows()))
def c76(t): t.assertFalse(validate_regional_semantics(PhysicalRole.NORTH_SUMMARY,regional_rows(),validate_root_semantics(root_rows())).row_values_persisted)
def c77(t):
    a="b"*64; rights=synthetic_rights(a); argv=("tool","--execute-network","--authorization","/synthetic/final.json","--rights-binding","/synthetic/rights.json"); candidate=synthetic_candidate(argv,a,rights.sha256); value=synthetic_auth(argv,a,rights.sha256,candidate_sha=candidate.sha256); t.assertEqual(validate_authorization(value,argv=argv,resume=False,implementation_aggregate=a,rights_sha256=rights.sha256,allow_synthetic=True,candidate=candidate,candidate_path=Path(value["authorization_candidate_path"])).kind,"FIRST_RUN_NETWORK_AUTHORIZATION")
def c78(t):
    a="b"*64; r=synthetic_rights(a); argv=("tool","--resume"); value=synthetic_auth(argv,a,r.sha256); assert_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",validate_authorization,value,argv=argv,resume=True,implementation_aggregate=a,rights_sha256=r.sha256,allow_synthetic=True)
def c79(t):
    a="b"*64; r=synthetic_rights(a); argv=("tool",); value=synthetic_auth(("tool","--resume"),a,r.sha256,resume=True); assert_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",validate_authorization,value,argv=argv,resume=False,implementation_aggregate=a,rights_sha256=r.sha256,allow_synthetic=True)
def c80(t):
    a="b"*64; r=synthetic_rights(a); argv=("tool","--resume"); value=synthetic_auth(argv,a,r.sha256,resume=True); out=validate_authorization(value,argv=argv,resume=True,implementation_aggregate=a,rights_sha256=r.sha256,allow_synthetic=True); t.assertEqual(out.value["ledger_watermark"],7)
def c81(t): c28(t)
def c82(t): assert_code(t,"METADATA_REAL_TRANSPORT_GATE_REQUIRED",construct_real_transport,execute_network=True,offline=True,rights=None,authorization=None,implementation_aggregate="a"*64)
def c83(t): assert_code(t,"METADATA_REAL_TRANSPORT_GATE_REQUIRED",construct_real_transport,execute_network=True,offline=False,rights=None,authorization=None,implementation_aggregate="a"*64)
def c84(t): t.assertFalse(synthetic_rights("a"*64).redistribution)
def c85(t): t.assertEqual(TERMINAL_PRECEDENCE,("METADATA_ROW_OBSERVATION_INTEGRITY_FAILURE","METADATA_FORBIDDEN_FIELD_BOUNDARY_FAILURE","METADATA_BOOTSTRAP_AUTHORITY_FAILURE","METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE","METADATA_LOCAL_STATE_CONFLICT","METADATA_RESOURCE_LIMIT_STOP","PATCH_LIST_REPRESENTATION_DRIFT_STOP","METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP","METADATA_TRANSPORT_INTEGRITY_FAILURE","METADATA_FULL_FILE_INTEGRITY_FAILURE","METADATA_PHYSICAL_CONTRACT_FAILURE","METADATA_VALUE_SEMANTICS_FAILURE","METADATA_BOOTSTRAP_PARTIALLY_RESOLVED","METADATA_BOOTSTRAP_RESOLVED"))
def c86(t): t.assertEqual(terminal_outcome(["METADATA_BOOTSTRAP_PARTIALLY_RESOLVED"]),"METADATA_BOOTSTRAP_PARTIALLY_RESOLVED")
def c87(t): c67(t)
def c88(t):
    before=ATTEMPT.exists(); plan=dry_run_plan(PROJECT,("tool","--dry-run")); t.assertFalse(plan["network_constructed"]); t.assertEqual(ATTEMPT.exists(),before)
def c89(t): assert_code(t,"METADATA_OFFLINE_NETWORK_FORBIDDEN",OfflineTransport().head,resource())
def c90(t):
    x=resource(); transport=SyntheticTransport([get_response(x)]); h=validate_head(x,head_response(x))
    ledger=t.ledger(); storage=AttemptStorage(t.root/"replay",ledger,synthetic_only=True)
    digest=acquire_complete_resource(transport,ledger,storage,x,h,ordinal=1,
        authorization_sha256="a"*64,implementation_aggregate="b"*64,
        timestamp="2026-01-01T00:00:00+00:00")
    t.assertEqual((digest.raw_byte_length,storage.incomplete_staging(),transport.calls),
                  (4,(),[("GET",PhysicalRole.ROOT_SUMMARY)])); ledger.close()
def c91(t): t.assertFalse(ATTEMPT.exists())
def c92(t): t.assertFalse(PRODUCTION_PROVIDER_DECODE_ENABLED); t.assertTrue(BOOTSTRAP_ALLOWED_SELECTIVE_DECODE)
def c93(t):
    public=[n for n,v in vars(bootstrap).items() if callable(v) and not n.startswith("_")]
    t.assertFalse(any(n in public for n in ("select_bricks","select_candidates","rank_coverage","create_candidates")))
def c94(t): t.assertEqual(json.loads((PROJECT/"oc3/environment_setup/METADATA_VALUE_SEMANTICS_REPLAY_RECEIPT.json").read_text())["metadata_bootstrap"],"NOT_STARTED")
def c95(t): probe_exact(t)


CASES = [
    ("base_spec_binding",c01),("clarification_binding",c02),("environment_binding",c03),("implementation_predecessor_binding",c04),("probe_13_immutable",c05),
    ("body_cap",c06),("aggregate_bytes",c07),("single_resource_cap",c08),("request_cap",c09),("concurrency",c10),("retry_max",c11),("other_caps",c12),
    ("all_heads_before_get",c13),("root_length_drift",c14),("north_length_drift",c15),("south_length_drift",c16),("patch_length_drift",c17),("patch_etag_drift",c18),("patch_modified_drift",c19),("redirect_rejected",c20),("encoding_rejected",c21),
    ("complete_get",c22),("status_206",c23),("content_range",c24),("truncated",c25),("excess",c26),("failed_bytes_charged",c27),("retry_identity",c28),
    ("partial_not_raw",c29),("raw_exclusive",c30),("atomic_publication",c31),("success_no_staging",c32),("failure_retains_staging",c33),("retry_new_staging",c34),
    ("digest_constructor_guard",c35),("digest_exact_raw",c36),("digest_byte_count",c37),("root_digest",c38),("digest_mismatch",c39),("north_digest",c40),("south_digest",c41),
    ("root_physical",c42),("north_physical",c43),("south_physical",c44),("patch_header",c45),("physical_drift",c46),
    ("opaque_transit",c47),("forbidden_decode_zero",c48),("forbidden_materialization_zero",c49),("forbidden_log_zero",c50),("forbidden_serialization_zero",c51),("root_allowed",c52),("regional_allowed",c53),("spans_around_forbidden",c54),("vector_canary",c55),("no_hdu_data",c56),("no_table_read",c57),("no_whole_record",c58),
    ("patch_hash",c59),("patch_tripwire",c60),("patch_release_unobserved",c61),("patch_brickid_unobserved",c62),("patch_brickname_unobserved",c63),("no_patch_join",c64),("patch_pending",c65),("patch_integrity_false",c66),("resolved_impossible",c67),
    ("brickname_reused",c68),("grz_reused",c69),("root_unique",c70),("north_join",c71),("south_join",c72),("zero_join",c73),("multiple_join",c74),("brickid_mismatch",c75),("no_row_persistence",c76),
    ("first_auth",c77),("first_reject_resume",c78),("resume_reject_first",c79),("resume_ledger_binding",c80),("same_invocation_retry",c81),("offline_transport",c82),
    ("rights_required",c83),("redistribution_false",c84),("precedence",c85),("partial_success",c86),("full_unreachable",c87),("dry_run_zero_network",c88),("offline_zero_network",c89),("synthetic_replay",c90),("no_real_attempt",c91),("production_decode_false",c92),("no_selector",c93),("bootstrap_not_started",c94),("probe_exact_after",c95),
]

def c96(t):
    result=subprocess.run([str(PROJECT/"oc3/.venv/bin/python"),str(PROJECT/"oc3/oc3_metadata_bootstrap.py"),"--help"],capture_output=True,text=True,check=False); t.assertEqual(result.returncode,0); t.assertIn("--execute-network",result.stdout)
def c97(t):
    result=subprocess.run([str(PROJECT/"oc3/.venv/bin/python"),str(PROJECT/"oc3/oc3_metadata_bootstrap.py"),"--dry-run","--offline"],capture_output=True,text=True,check=False); t.assertEqual(result.returncode,0); t.assertEqual(json.loads(result.stdout)["real_network_requests"],0)
def c98(t):
    result=subprocess.run([str(PROJECT/"oc3/.venv/bin/python"),str(PROJECT/"oc3/oc3_metadata_bootstrap.py"),"--execute-network"],capture_output=True,text=True,check=False); t.assertEqual((result.returncode,result.stderr.strip()),(2,"PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS"))
def c99(t): t.assertEqual((RESOURCE_CAPS.timeout_seconds,RESOURCE_CAPS.retry_backoff_seconds,RESOURCE_CAPS.retry_after_max_seconds,RESOURCE_CAPS.threads,RESOURCE_CAPS.gpu),(30,2,60,1,0))
def c100(t):
    import sys as _sys, astropy, numpy, pyarrow
    t.assertEqual((_sys.version_info[:3],numpy.__version__,astropy.__version__,pyarrow.__version__),((3,12,14),"2.5.3","8.0.1","25.0.1"))
def c101(t):
    a="b"*64; r=synthetic_rights(a); argv=("tool",); value=synthetic_auth(argv,a,r.sha256); value["authorized"]=False
    assert_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",validate_authorization,value,argv=argv,resume=False,implementation_aggregate=a,rights_sha256=r.sha256,allow_synthetic=True)
def c102(t):
    a="b"*64; r=synthetic_rights(a); argv=("tool",); value=synthetic_auth(argv,a,r.sha256); value["scope"]="WRONG"
    assert_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",validate_authorization,value,argv=argv,resume=False,implementation_aggregate=a,rights_sha256=r.sha256,allow_synthetic=True)
def c103(t):
    _,l,_,_,d=digest_fixture(t)
    with t.assertRaises(BootstrapError): replace(d,raw_sha256="0"*64)
    l.close()
def c104(t):
    path=write_final_json(t.root,"BOOTSTRAP_EVENTS.json",{"z":1,"a":2}); t.assertEqual(path.read_bytes(),b'{"a":2,"z":1}\n')
def c105(t):
    t.assertEqual(set(FINAL_EVIDENCE_ARTIFACTS),{"BOOTSTRAP_AUTHORIZATION_BINDING.json","BOOTSTRAP_TRANSPORT_EVIDENCE.json","BOOTSTRAP_RAW_FILE_MANIFEST.json","BOOTSTRAP_INTEGRITY_EVIDENCE.json","BOOTSTRAP_PHYSICAL_CONTRACT_EVIDENCE.json","BOOTSTRAP_SEMANTIC_SUMMARY.json","PATCH_ACQUISITION_BOUND_EVIDENCE.json","BOOTSTRAP_EVENTS.json","BOOTSTRAP_TERMINAL.json","BOOTSTRAP_LEDGER.sqlite","BOOTSTRAP_RUN.log"})

CASES.extend([
    ("cli_help",c96),("cli_dry_run",c97),("network_plan_gate",c98),
    ("timeouts_threads_gpu",c99),("environment_versions",c100),
    ("authorized_false",c101),("wrong_scope",c102),("digest_tamper",c103),
    ("canonical_final_json",c104),("final_artifact_set",c105),
])

for index, (label, function) in enumerate(CASES, 1):
    def test(self, _function=function):
        _function(self)
    test.__name__ = f"test_{index:03d}_{label}"
    setattr(MetadataBootstrapTests, test.__name__, test)
