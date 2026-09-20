"""Offline regression for the metadata-bootstrap runtime activation gate."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import socket
import tempfile
from types import MappingProxyType
import unittest
from unittest.mock import patch

import oc3_metadata_bootstrap as cli
from oc3lib.core import canonical, file_hash, implementation_hash
from oc3lib.metadata_bootstrap import *
import oc3lib.metadata_bootstrap as bootstrap


PROJECT = Path(__file__).resolve().parents[2]
ATTEMPT = PROJECT / ATTEMPT_RELATIVE_DIRECTORY
SCRIPT = (PROJECT / CANONICAL_SCRIPT_RELATIVE_PATH).resolve()
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


def raises_code(case, code, function, *args, **kwargs):
    with case.assertRaises(BootstrapError) as caught:
        function(*args, **kwargs)
    case.assertEqual(caught.exception.code, code)


class GateActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="oc3_gate_activation_")
        root = Path(self.temp.name)
        self.rights_path = (root / "rights.json").resolve()
        self.auth_path = (root / "authorization.json").resolve()
        self.candidate_path = (root / "candidate.json").resolve()
        self.aggregate = implementation_hash(PROJECT)
        self.command = (
            str(SCRIPT), "--execute-network", "--authorization", str(self.auth_path),
            "--rights-binding", str(self.rights_path),
        )
        self.factory_calls = []

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path: Path, value: dict):
        path.write_bytes(canonical(value) + b"\n")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def rights(self, **changes):
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
            "implementation_aggregate": self.aggregate,
            "environment_fingerprint": ENVIRONMENT_FINGERPRINT,
            "resources": resource_binding_values(),
            "reviewed_evidence": [{
                "path": "OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC.md",
                "sha256": BASE_SPEC_SHA256,
            }],
            "reviewed": True,
            "synthetic_only": True,
        }
        value.update(changes)
        return value

    def candidate(self, rights_sha: str, **changes):
        value = {
            "schema_version": 1,
            "canonicalization": CANONICALIZATION_VERSION,
            "candidate_type": CANDIDATE_TYPE,
            "candidate_state": CANDIDATE_STATE,
            "attempt_id": ATTEMPT_ID,
            "scope": BOOTSTRAP_SCOPE,
            "execution_mode": FIRST_EXECUTION_MODE,
            "patch_model": PATCH_MODEL,
            "execution_plan_sha256": EXECUTION_PLAN_SHA256,
            "plan_post_activation_review_sha256": PLAN_POST_ACTIVATION_REVIEW_SHA256,
            "rights_binding_path": str(self.rights_path),
            "rights_binding_sha256": rights_sha,
            "rights_review_sha256": RIGHTS_REVIEW_SHA256,
            "base_spec_sha256": BASE_SPEC_SHA256,
            "clarification_sha256": CLARIFICATION_001_SHA256,
            "implementation_aggregate": self.aggregate,
            "environment_fingerprint": ENVIRONMENT_FINGERPRINT,
            "resources": resource_binding_values(),
            "resource_caps": resource_cap_values(),
            "command_vector": list(self.command),
            "command_sha256": command_sha256(self.command),
            "negative_capabilities": dict(NEGATIVE_CAPABILITIES),
            "final_authorization_path": str(self.auth_path),
            "candidate_created_at_utc": "2026-09-19T00:00:00Z",
        }
        value.update(changes)
        return value

    def authorization(self, rights_sha: str, candidate_sha: str = "c" * 64, **changes):
        value = {
            "authorization_type": FIRST_AUTHORIZATION_TYPE,
            "authorization_state": "FINAL_HUMAN_AUTHORIZATION",
            "schema_version": 2,
            "canonicalization": CANONICALIZATION_VERSION,
            "authorized": True,
            "authorized_by": "SYNTHETIC_TEST_HARNESS",
            "authorized_at_utc": "2026-09-19T00:00:00Z",
            "attempt_id": ATTEMPT_ID,
            "attempt_directory": ATTEMPT_RELATIVE_DIRECTORY,
            "scope": BOOTSTRAP_SCOPE,
            "execution_mode": FIRST_EXECUTION_MODE,
            "execution_plan_sha256": EXECUTION_PLAN_SHA256,
            "base_spec_sha256": BASE_SPEC_SHA256,
            "clarification_sha256": CLARIFICATION_001_SHA256,
            "implementation_aggregate": self.aggregate,
            "environment_fingerprint": ENVIRONMENT_FINGERPRINT,
            "patch_model": PATCH_MODEL,
            "resources": resource_binding_values(),
            "resource_caps": resource_cap_values(),
            "command_argv": list(self.command),
            "command_sha256": command_sha256(self.command),
            "rights_binding_sha256": rights_sha,
            "negative_capabilities": dict(NEGATIVE_CAPABILITIES),
            "authorization_candidate_path": str(self.candidate_path),
            "authorization_candidate_sha256": candidate_sha,
            "synthetic_only": True,
        }
        value.update(changes)
        return value

    def resume_authorization(self, rights_sha: str):
        command = self.command + ("--resume",)
        value = self.authorization(
            rights_sha,
            authorization_type=RESUME_AUTHORIZATION_TYPE,
            execution_mode=RESUME_EXECUTION_MODE,
            command_argv=list(command), command_sha256=command_sha256(command),
        )
        value["schema_version"] = 1
        value.pop("authorization_candidate_path")
        value.pop("authorization_candidate_sha256")
        value.update(
            first_run_authorization_sha256="a" * 64,
            ledger_identity="synthetic-ledger", ledger_watermark=0,
            consumed_counters={}, remaining_caps=resource_cap_values(),
            completed_raw_resources=[],
            pending_resources=[role.value for role in RESOURCE_ORDER],
            existing_staging_state=[],
        )
        return value, command

    def prepare(self, rights_changes=None, auth_changes=None, candidate_changes=None,
                write_candidate=True):
        rights_sha = self.write(self.rights_path, self.rights(**(rights_changes or {})))
        candidate_sha = "c" * 64
        if write_candidate:
            candidate_sha = self.write(
                self.candidate_path, self.candidate(rights_sha, **(candidate_changes or {})))
        self.write(self.auth_path, self.authorization(
            rights_sha, candidate_sha, **(auth_changes or {})))
        return rights_sha

    def factory(self, **kwargs):
        self.factory_calls.append(kwargs)
        return "SYNTHETIC_TRANSPORT_FACTORY_REACHED"

    def activate(self, **kwargs):
        return activate_network_transport(
            project=PROJECT, command=self.command,
            authorization_path=self.auth_path, rights_path=self.rights_path,
            resume=False, allow_synthetic=True, transport_factory=self.factory,
            **kwargs,
        )


def c01(t):
    value=t.rights(); value.pop("execution_plan_sha256"); sha=t.write(t.rights_path,value); t.write(t.auth_path,t.authorization(sha)); raises_code(t,"METADATA_RIGHTS_BINDING_INVALID",t.activate)
def c02(t): t.prepare(rights_changes={"execution_plan_sha256":"0"*64}); raises_code(t,"METADATA_RIGHTS_BINDING_INVALID",t.activate)
def c03(t): raises_code(t,"PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS",activate_network_transport,project=PROJECT,command=t.command,authorization_path=t.auth_path,rights_path=None,resume=False,allow_synthetic=True,transport_factory=t.factory)
def c04(t): t.rights_path.write_text("{"); raises_code(t,"METADATA_RIGHTS_BINDING_INVALID",t.activate)
def c05(t):
    value=t.rights(); raw=canonical(value)+b"\n"; b=RightsBinding(MappingProxyType(value),hashlib.sha256(raw).hexdigest(),True); t.assertEqual(validate_rights(b,implementation_aggregate=t.aggregate,allow_synthetic=True,project=PROJECT).value["scope"],BOOTSTRAP_SCOPE)
def c06(t): t.prepare(rights_changes={"redistribution":True}); raises_code(t,"METADATA_RIGHTS_BINDING_INVALID",t.activate)
def c07(t):
    resources=resource_binding_values(); resources[0]={**resources[0],"url":"https://synthetic.invalid/"}; t.prepare(rights_changes={"resources":resources}); raises_code(t,"METADATA_RIGHTS_BINDING_INVALID",t.activate)
def c08(t): t.prepare(rights_changes={"implementation_aggregate":"0"*64}); raises_code(t,"METADATA_RIGHTS_BINDING_INVALID",t.activate)
def c09(t): t.prepare(rights_changes={"environment_fingerprint":"0"*64}); raises_code(t,"METADATA_RIGHTS_BINDING_INVALID",t.activate)
def c10(t):
    sha=t.write(t.rights_path,t.rights()); b=load_rights_binding(t.rights_path); t.assertEqual((b.sha256,sha),(hashlib.sha256(t.rights_path.read_bytes()).hexdigest(),sha))
def c11(t): t.write(t.rights_path,t.rights()); raises_code(t,"PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS",t.activate)
def c12(t): t.prepare(auth_changes={"authorized":False,"authorization_state":"CANDIDATE"}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c13(t): t.prepare(); t.assertEqual(t.activate(),"SYNTHETIC_TRANSPORT_FACTORY_REACHED")
def c14(t): t.prepare(auth_changes={"rights_binding_sha256":"0"*64}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c15(t): t.prepare(auth_changes={"execution_plan_sha256":"0"*64}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c16(t): t.prepare(auth_changes={"implementation_aggregate":"0"*64}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c17(t): t.prepare(auth_changes={"environment_fingerprint":"0"*64}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c18(t): t.prepare(auth_changes={"attempt_id":"WRONG"}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c19(t): t.prepare(auth_changes={"scope":"WRONG"}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c20(t): t.prepare(auth_changes={"execution_mode":"NETWORK_RESUME"}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c21(t): t.prepare(auth_changes={"patch_model":"WRONG"}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c22(t):
    caps=resource_cap_values(); caps["requests"]+=1; t.prepare(auth_changes={"resource_caps":caps}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c23(t): t.prepare(auth_changes={"resources":resource_binding_values()[:-1]}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c24(t):
    negative=dict(NEGATIVE_CAPABILITIES); negative.pop("range_requests"); t.prepare(auth_changes={"negative_capabilities":negative}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c25(t): t.assertEqual(bootstrap._validate_command_vector(t.command,authorization_path=t.auth_path,rights_path=t.rights_path,resume=False),t.command)
def c26(t): raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",bootstrap._validate_command_vector,t.command+("--dry-run",),authorization_path=t.auth_path,rights_path=t.rights_path,resume=False)
def c27(t): t.prepare(auth_changes={"command_sha256":"0"*64}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c28(t):
    sha=t.write(t.rights_path,t.rights()); value=t.authorization(sha); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",validate_authorization,value,argv=t.command+("--resume",),resume=True,implementation_aggregate=t.aggregate,rights_sha256=sha,allow_synthetic=True)
def c29(t):
    sha=t.write(t.rights_path,t.rights()); value,command=t.resume_authorization(sha); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",validate_authorization,value,argv=command,resume=False,implementation_aggregate=t.aggregate,rights_sha256=sha,allow_synthetic=True)
def c30(t): t.prepare(auth_changes={"scope":"WRONG"}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate); t.assertEqual(t.factory_calls,[])
def c31(t): t.prepare(); t.activate(); t.assertEqual(len(t.factory_calls),1)
def c32(t):
    t.prepare(); trace=[]; t.activate(gate_trace=trace); t.assertEqual(trace,[f"{i:02d}_{name}" for i,name in enumerate(("project_identity","execution_plan_authority","spec_and_clarification","implementation_aggregate","environment_fingerprint","attempt_identity","attempt_state","rights_binding","human_authorization","authorization_rights_binding","plan_bindings","resources_and_caps","patch_model","command_vector","command_sha256","authorized_true","execution_mode","resume_mode","negative_capabilities","authorization_candidate_path","authorization_candidate_sha256","authorization_candidate_validation","candidate_final_equivalence","real_transport_construction"),1)])
def c33(t):
    err=io.StringIO()
    with redirect_stderr(err): code=cli.main(["--execute-network"])
    t.assertEqual((code,err.getvalue().strip()),(2,"PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS"))
def c34(t): t.assertFalse(ATTEMPT.exists())
def c35(t): t.assertFalse((ATTEMPT/"BOOTSTRAP_LEDGER.sqlite").exists())
def c36(t):
    with patch.object(socket,"socket",side_effect=AssertionError("socket")),patch.object(socket,"getaddrinfo",side_effect=AssertionError("dns")):
        raises_code(t,"PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS",activate_network_transport,project=PROJECT,command=t.command,authorization_path=t.auth_path,rights_path=None,resume=False,allow_synthetic=True,transport_factory=t.factory)
def c37(t):
    out=io.StringIO()
    with patch.object(cli,"activate_network_transport",side_effect=AssertionError("transport")),redirect_stdout(out): code=cli.main(["--offline"])
    t.assertEqual(code,0)
def c38(t):
    out=io.StringIO()
    with patch.object(cli,"activate_network_transport",side_effect=AssertionError("transport")),redirect_stdout(out): code=cli.main(["--dry-run"])
    t.assertEqual(code,0)
def c39(t): t.assertEqual(PATCH_MODEL,"MODEL_B_TWO_STAGE")
def c40(t): t.assertFalse(PRODUCTION_PROVIDER_DECODE_ENABLED)
def c41(t):
    actual={p.relative_to(PROBE).as_posix() for p in PROBE.rglob("*") if p.is_file()}; t.assertEqual(actual,set(PROBE_SNAPSHOT)); t.assertTrue(all((PROBE/p).stat().st_size==s and file_hash(PROBE/p)==h for p,(s,h) in PROBE_SNAPSHOT.items()))
def c42(t): t.assertTrue(no_selector_api())
def c43(t): t.assertFalse(ATTEMPT.exists())
def c44(t):
    source=(PROJECT/"oc3/tests/run_tests.py").read_text(); t.assertIn("patch.object(socket,'getaddrinfo'",source); t.assertFalse(dry_run_plan(PROJECT,t.command)["network_constructed"])

def validated_candidate(t, rights_sha):
    candidate=load_authorization_candidate(t.candidate_path)
    return validate_authorization_candidate(candidate,argv=t.command,
        implementation_aggregate=t.aggregate,rights_sha256=rights_sha,
        authorization_path=t.auth_path,rights_path=t.rights_path,project=PROJECT,
        allow_synthetic_paths=True)

def rewrite_candidate(t, rights_sha, mutate):
    value=t.candidate(rights_sha); mutate(value); sha=t.write(t.candidate_path,value)
    t.write(t.auth_path,t.authorization(rights_sha,sha)); return sha

def rewrite_authorization(t, mutate):
    value=json.loads(t.auth_path.read_text()); mutate(value); t.write(t.auth_path,value)

def c45(t):
    rights=t.prepare(); candidate=validated_candidate(t,rights); t.assertEqual(candidate.validation_state,VALID_CANDIDATE_STATE); t.assertEqual(t.factory_calls,[])
def c46(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(unknown_key=False)); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c47(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.pop("scope")); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c48(t):
    rights=t.write(t.rights_path,t.rights()); value=t.candidate(rights); t.candidate_path.write_text(json.dumps(value,indent=2)+"\n"); t.write(t.auth_path,t.authorization(rights,"0"*64)); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c49(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(candidate_type="WRONG")); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c50(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(candidate_state="AUTHORIZED")); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c51(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(authorized=False)); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c52(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(authorized_by="SYNTHETIC")); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c53(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(command_sha256="0"*64)); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c54(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(rights_binding_sha256="0"*64)); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c55(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(implementation_aggregate="0"*64)); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c56(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(resources=v["resources"][:-1])); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c57(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v["resource_caps"].update(requests=13)); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c58(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v["negative_capabilities"].update(range_requests=True)); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c59(t):
    rights=t.write(t.rights_path,t.rights()); rewrite_candidate(t,rights,lambda v:v.update(final_authorization_path="/wrong/final.json")); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c60(t):
    rights=t.prepare(); validated_candidate(t,rights); t.assertEqual(t.factory_calls,[])
def c61(t):
    t.prepare(); t.auth_path.write_bytes(t.candidate_path.read_bytes()); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate); t.assertEqual(t.factory_calls,[])
def c62(t):
    t.prepare(auth_changes={"schema_version":1}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c63(t):
    t.prepare(); rewrite_authorization(t,lambda v:v.pop("authorization_candidate_path")); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c64(t):
    t.prepare(); rewrite_authorization(t,lambda v:v.pop("authorization_candidate_sha256")); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c65(t):
    t.prepare(write_candidate=False); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate); t.assertEqual(t.factory_calls,[])
def c66(t):
    t.prepare(auth_changes={"authorization_candidate_sha256":"0"*64}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c67(t):
    t.prepare(auth_changes={"resources":resource_binding_values()[:-1]}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c68(t):
    t.prepare(); t.assertEqual(t.activate(),"SYNTHETIC_TRANSPORT_FACTORY_REACHED")
def c69(t):
    t.prepare(auth_changes={"authorized":False}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c70(t):
    t.prepare(); rewrite_authorization(t,lambda v:v.pop("authorized_by")); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c71(t):
    t.prepare(auth_changes={"authorized_at_utc":"not-utc"}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c72(t):
    t.prepare(auth_changes={"command_argv":list(t.command)+["--dry-run"]}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate)
def c73(t):
    t.prepare(candidate_changes={"candidate_type":"WRONG"}); raises_code(t,"METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE",t.activate); t.assertEqual(t.factory_calls,[])
def c74(t):
    t.assertEqual((EXPECTED_AGGREGATE_BYTES,PATCH_MODEL,PRODUCTION_PROVIDER_DECODE_ENABLED),(89461646,"MODEL_B_TWO_STAGE",False)); t.assertEqual(len(resource_binding_values()),4)
def c75(t):
    t.assertFalse(ATTEMPT.exists()); t.assertFalse((ATTEMPT/"BOOTSTRAP_LEDGER.sqlite").exists())
def c76(t):
    c41(t)
def c77(t):
    t.assertEqual(FIRST_AUTH_FIELDS,FINAL_AUTH_COMMON_FIELDS|{"authorization_candidate_path","authorization_candidate_sha256"}); t.assertFalse({"authorization_candidate_path","authorization_candidate_sha256"}&RESUME_AUTH_FIELDS)


CASES = [
    ("plan_sha_required",c01),("wrong_plan_rights",c02),("missing_rights",c03),("malformed_rights",c04),
    ("rights_exact_values",c05),("rights_redistribution_reject",c06),("rights_resource_reject",c07),("rights_implementation_reject",c08),("rights_environment_reject",c09),("rights_sha_local",c10),
    ("missing_authorization",c11),("candidate_false_reject",c12),("final_true_accept",c13),("authorization_rights_sha_reject",c14),("authorization_plan_reject",c15),("authorization_implementation_reject",c16),("authorization_environment_reject",c17),("authorization_attempt_reject",c18),("authorization_scope_reject",c19),("authorization_mode_reject",c20),("authorization_patch_model_reject",c21),("authorization_caps_reject",c22),("authorization_resource_reject",c23),("negative_capability_omission",c24),
    ("command_vector_accept",c25),("command_mutation_reject",c26),("command_hash_reject",c27),("first_auth_resume_reject",c28),("resume_auth_first_reject",c29),("transport_before_gates_forbidden",c30),("valid_gates_reach_factory",c31),("factory_gate_order",c32),
    ("canonical_missing_artifacts_blocked",c33),("blocked_no_attempt",c34),("blocked_no_ledger",c35),("blocked_zero_dns_socket",c36),("offline_no_transport",c37),("dry_run_no_transport",c38),("model_b_unchanged",c39),("production_decode_false",c40),("probe_001_exact",c41),("no_selector",c42),("no_real_attempt",c43),("replay_firewall_contract",c44),
    ("candidate_valid_offline",c45),("candidate_unknown_key_reject",c46),("candidate_missing_key_reject",c47),("candidate_noncanonical_reject",c48),("candidate_type_reject",c49),("candidate_state_reject",c50),("candidate_authorized_key_reject",c51),("candidate_human_field_reject",c52),("candidate_command_hash_reject",c53),("candidate_rights_reject",c54),("candidate_implementation_reject",c55),("candidate_resource_reject",c56),("candidate_cap_reject",c57),("candidate_negative_reject",c58),("candidate_final_path_reject",c59),("candidate_no_transport",c60),("candidate_as_authorization_reject",c61),("final_schema_v1_reject",c62),("final_candidate_path_required",c63),("final_candidate_sha_required",c64),("candidate_absent_reject",c65),("candidate_sha_mismatch_reject",c66),("candidate_final_mismatch_reject",c67),("candidate_final_equivalence_pass",c68),("final_authorized_false_reject",c69),("final_human_identity_required",c70),("final_human_time_required",c71),("final_argv_mismatch_reject",c72),("factory_untouched_before_candidate",c73),("scientific_contract_unchanged",c74),("candidate_no_attempt_state",c75),("candidate_probe_001_exact",c76),("first_resume_schema_separation",c77),
]

for index, (label, function) in enumerate(CASES, 1):
    def test(self, _function=function):
        _function(self)
    test.__name__ = f"test_gate_{index:02d}_{label}"
    setattr(GateActivationTests, test.__name__, test)
