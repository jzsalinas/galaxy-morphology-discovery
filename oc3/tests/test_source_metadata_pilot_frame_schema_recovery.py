import inspect
import os
import signal
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from astropy.io import fits

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import file_sha256, load_canonical_json, sealed, sha256_bytes
from oc3lib import source_metadata_descriptive_pilot as reference
from oc3lib import source_metadata_pilot_frame_schema_recovery as science
from oc3lib import source_metadata_pilot_frame_schema_recovery_governor as gov
from oc3lib.observational_multiplicity import REGIONAL_FIELDS as HISTORICAL_REGIONAL_FIELDS
from oc3lib.provider_physical_contracts import (
    PRODUCTION_PHYSICAL_CONTRACTS, PhysicalRole,
)
from oc3lib.source_metadata_pilot_frame_schema_recovery_validation import (
    CANDIDATE, EXPECTED_INPUTS, expected_supervisor_argv, expected_worker_command,
    validate_candidate, validate_invocation,
)
from oc3_source_metadata_pilot_frame_schema_recovery_supervisor import run_child_once, supervise


def _value(tform, count=1):
    if tform.endswith("A"):
        return np.asarray([b"0001p001"] * count, dtype="S8")
    if tform == "L": return np.asarray([True] * count, dtype=bool)
    repeat = int(tform[:-1]) if tform[:-1].isdigit() else 1
    code = tform[-1]
    dtype = {"I":np.int16,"J":np.int32,"E":np.float32,"D":np.float64}[code]
    shape = (count, repeat) if repeat > 1 else (count,)
    return np.ones(shape, dtype=dtype)


def physical_fixture(path, contract, *, names=None):
    names = list(names if names is not None else [column.ttype for column in contract.columns])
    formats = [column.tform for column in contract.columns]
    if len(names) != len(formats):
        formats = formats[:len(names)]
    columns = [fits.Column(name=name, format=form, array=_value(form))
               for name,form in zip(names,formats)]
    fits.HDUList([fits.PrimaryHDU(),fits.BinTableHDU.from_columns(columns)]).writeto(path,checksum=False)
    return replace(contract,naxis2=1)


class ProviderCaseContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="oc3_schema_recovery_synthetic_")
        self.root=Path(self.temp.name)

    def tearDown(self): self.temp.cleanup()

    def test_root_uppercase_physical_names_succeed(self):
        contract=PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.ROOT_SUMMARY]
        path=self.root/"root.fits"; adjusted=physical_fixture(path,contract)
        value=science.read_root_physical(path,adjusted)
        self.assertEqual(value["identity"].size,1)

    def test_regional_lowercase_identity_succeeds_and_normalizes(self):
        contract=PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.NORTH_SUMMARY]
        path=self.root/"north.fits"; adjusted=physical_fixture(path,contract)
        value=science.read_regional_identity_physical(path,PhysicalRole.NORTH_SUMMARY,adjusted)
        self.assertEqual(value.dtype.names,("brickname","brickid"))
        self.assertEqual((str(value[0]["brickname"]),int(value[0]["brickid"])),("0001p001",1))

    def assert_schema_failure(self,names):
        contract=PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.NORTH_SUMMARY]
        path=self.root/f"bad-{len(list(self.root.iterdir()))}.fits"
        adjusted=physical_fixture(path,contract,names=names)
        with self.assertRaisesRegex(science.FrameRecoveryError,science.PHYSICAL_SCHEMA_CONTRACT_MISMATCH):
            science.read_regional_identity_physical(path,PhysicalRole.NORTH_SUMMARY,adjusted)

    def test_uppercase_and_mixed_case_aliases_fail(self):
        base=[column.ttype for column in PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.NORTH_SUMMARY].columns]
        for replacement in ("BRICKNAME","BrickName","brickName"):
            with self.subTest(replacement=replacement):
                self.assert_schema_failure([replacement,*base[1:]])

    def test_missing_brickname_and_missing_brickid_fail(self):
        base=[column.ttype for column in PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.NORTH_SUMMARY].columns]
        for missing in ("brickname","brickid"):
            with self.subTest(missing=missing): self.assert_schema_failure([x for x in base if x!=missing])

    def test_reordered_ttype_columns_fail(self):
        base=[column.ttype for column in PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.NORTH_SUMMARY].columns]
        base[0],base[1]=base[1],base[0]
        self.assert_schema_failure(base)

    def test_historical_projection_regression(self):
        self.assertEqual(science.REGIONAL_PHYSICAL_IDENTITY_FIELDS,("brickname","brickid"))
        self.assertEqual(HISTORICAL_REGIONAL_FIELDS,
            ("brickname","brickid","ra","dec","ra1","ra2","dec1","dec2"))
        self.assertEqual(tuple(column.ttype for column in
            PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.NORTH_SUMMARY].columns)[0],"brickname")
        self.assertEqual(tuple(column.ttype for column in
            PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.NORTH_SUMMARY].columns)[43],"brickid")


def columns(rows):
    return science.root_columns(
        brickname=[r[0] for r in rows], brickid=[r[1] for r in rows], brickrow=[r[2] for r in rows],
        ra=[r[3] for r in rows], dec=[r[4] for r in rows], ra1=[r[5] for r in rows],
        ra2=[r[6] for r in rows], dec1=[r[7] for r in rows], dec2=[r[8] for r in rows])


def reference_rows(rows):
    return [{"BRICKNAME":r[0], "BRICKID":r[1], "BRICKROW":r[2], "RA":r[3], "DEC":r[4],
             "RA1":r[5], "RA2":r[6], "DEC1":r[7], "DEC2":r[8]} for r in rows]


class ColumnarSemanticTests(unittest.TestCase):
    def dataset(self):
        return [
            ("a",1,0,359.5,0,359,1,-1,1), ("b",2,1,0.5,0,0,2,-1,1),
            ("c",3,0,10,0,9,11,-1,1), ("d",4,1,11,0,11,12,-1,1),
            ("e",5,4,50,0,49,51,-1,1), ("f",6,7,90,0,89,91,-1,1),
            ("g",7,10,130,0,129,131,-1,1), ("h",8,13,170,0,169,171,-1,1),
            ("i",9,16,210,0,209,211,-1,1), ("j",10,19,250,0,249,251,-1,1)]

    def test_reference_and_columnar_global_view_equivalent(self):
        rows = self.dataset(); root = columns(rows)
        ids = science.identity_array([r[0] for r in rows], [r[1] for r in rows])
        optimized = science.global_view_both(root["identity"], ids, ids, ["j"])
        _, old = reference.reconstruct_global_view_both(reference_rows(rows),
            [{"BRICKNAME":r[0],"BRICKID":r[1]} for r in rows],
            [{"BRICKNAME":r[0],"BRICKID":r[1]} for r in rows], ["j"])
        self.assertEqual(tuple((str(x["brickname"]),int(x["brickid"])) for x in optimized),
                         tuple((x.brickname,x.brickid) for x in old))

    def test_digest_order_exact(self):
        ids = science.identity_array(["x","y","z"],[2,1,3])
        observed = [(str(ids[i]["brickname"]), int(ids[i]["brickid"])) for i in science.digest_order(ids)]
        expected = sorted(((str(x["brickname"]),int(x["brickid"])) for x in ids),
                          key=lambda x:(reference.target_digest(reference.GlobalBrickIdentity(x[0],x[1])),x))
        self.assertEqual(observed, expected)

    def test_wrap_touch_same_and_adjacent_row_guard_equivalence(self):
        rows = self.dataset(); root = columns(rows)
        old_geometry, _ = reference.reconstruct_global_view_both(reference_rows(rows),
            [{"BRICKNAME":r[0],"BRICKID":r[1]} for r in rows],
            [{"BRICKNAME":r[0],"BRICKID":r[1]} for r in rows], [])
        for identity in (("a",1),("c",3),("d",4)):
            new = {(str(root["brickname"][i]),int(root["brickid"][i])) for i in science.guard_indices(root,identity)}
            old = {(x.brickname,x.brickid) for x in reference.guard_one(reference.GlobalBrickIdentity(*identity),old_geometry)}
            self.assertEqual(new,old)

    def test_selection_target_holdout_and_geometry_equivalence(self):
        rows = self.dataset(); root = columns(rows)
        ids = science.identity_array([r[0] for r in rows], [r[1] for r in rows])
        selected = science.select_frame(root,ids)
        old_geometry, old_eligible = reference.reconstruct_global_view_both(reference_rows(rows),
            [{"BRICKNAME":r[0],"BRICKID":r[1]} for r in rows],
            [{"BRICKNAME":r[0],"BRICKID":r[1]} for r in rows], [])
        old = reference.select_frame(old_eligible,old_geometry)
        self.assertEqual([(x["identity"],x["role"],x["digest"]) for x in selected],
                         [((x.identity.brickname,x.identity.brickid),x.role,x.digest) for x in old])
        for new_item,old_item in zip(selected,old):
            new_geometry=[science._geometry(root,int(i)) for i in new_item["guard_indices"]]
            old_geometry_rows=[old_geometry[x] for x in old_item.guard]
            self.assertEqual([(x["brickname"],x["brickid"],x["brickrow"],x["ra1"],x["ra2"]) for x in new_geometry],
                             [(x.identity.brickname,x.identity.brickid,x.brickrow,x.ra1,x.ra2) for x in old_geometry_rows])

    def test_guard_collision_and_insufficient_disjoint_fail(self):
        rows=[(chr(97+i),i,0,10,0,9,11,-1,1) for i in range(5)]
        root=columns(rows); ids=science.identity_array([r[0] for r in rows],[r[1] for r in rows])
        with self.assertRaises(science.FrameRecoveryError): science.select_frame(root,ids)

    def test_duplicate_rejection_all_authorities(self):
        ids=science.identity_array(["a","a"],[1,1])
        for authority in ("ROOT","NORTH","SOUTH"):
            with self.assertRaises(science.FrameRecoveryError): science.require_unique_identities(ids,authority)

    def test_missing_root_and_development_exclusion(self):
        root=science.identity_array(["a"],[1]); both=science.identity_array(["a","b"],[1,2])
        with self.assertRaises(science.FrameRecoveryError): science.global_view_both(root,both,both,[])
        self.assertEqual(science.global_view_both(root,root,root,["a"]).size,0)

    def test_large_scale_is_compact_array_engineering_regression(self):
        count=200_000
        names=np.asarray([f"{i:08d}" for i in range(count)],dtype="U8")
        ids=np.arange(count,dtype=np.int64)
        root=science.root_columns(brickname=names,brickid=ids,brickrow=ids,ra=np.zeros(count),dec=np.zeros(count),
            ra1=np.zeros(count),ra2=np.ones(count),dec1=-np.ones(count),dec2=np.ones(count))
        north=science.identity_array(names,ids); south=science.identity_array(names,ids)
        self.assertLess(science.compact_array_bytes(root,north,south),50_000_000)
        self.assertTrue(all(isinstance(value,np.ndarray) for value in root.values()))

    def test_frame_validation_rejects_guard_collision(self):
        rows=self.dataset(); root=columns(rows); ids=science.identity_array([r[0] for r in rows],[r[1] for r in rows])
        selected=science.select_frame(root,ids); hashes={"a":"0"*64}
        payload=science.frame_payload(root,selected,hashes,"f"*64)
        science.validate_frame_payload(payload,hashes,"f"*64)
        payload["selections"][1]["guard"]=payload["selections"][0]["guard"]
        with self.assertRaises(science.FrameRecoveryError): science.validate_frame_payload(payload,hashes,"f"*64)


class SupervisorTests(unittest.TestCase):
    def test_nonzero_exit_and_bounded_stream_hashes(self):
        result=run_child_once([sys.executable,"-c","import sys;print('out');print('err',file=sys.stderr);raise SystemExit(7)"],cap=16)
        self.assertEqual(result["return_code"],7); self.assertIsNone(result["terminating_signal"])
        self.assertGreater(result["stdout"]["byte_count"],0); self.assertGreater(result["stderr"]["byte_count"],0)

    def test_signal_termination_is_exact(self):
        result=run_child_once([sys.executable,"-c","import os,signal;os.kill(os.getpid(),signal.SIGTERM)"],cap=16)
        self.assertEqual(result["return_code"],-signal.SIGTERM)
        self.assertEqual(result["terminating_signal"],signal.SIGTERM)

    def test_capture_cap_records_total_and_truncation(self):
        result=run_child_once([sys.executable,"-c","print('x'*1000)"],cap=32)
        self.assertTrue(result["stdout"]["truncated"]); self.assertEqual(result["stdout"]["captured_byte_count"],32)
        self.assertGreater(result["stdout"]["byte_count"],32)

    def test_permit_consumption_precedes_worker_launch(self):
        import oc3_source_metadata_pilot_frame_schema_recovery_supervisor as supervisor
        source=inspect.getsource(supervisor.main)
        self.assertLess(source.index("consume_permit("),source.index("supervise(candidate"))
        self.assertEqual(inspect.getsource(supervisor.supervise).count("run_child_once("),1)

    def test_diagnostic_contract_fields_are_frozen(self):
        self.assertEqual(science.DIAGNOSTIC_SCHEMA,"OC3_FRAME_SCHEMA_RECOVERY_EXECUTION_DIAGNOSTIC_001")
        self.assertEqual(science.STREAM_CAPTURE_CAP,262144)
        source=inspect.getsource(__import__("oc3_source_metadata_pilot_frame_schema_recovery_supervisor"))
        for field in ("terminating_signal","max_rss_kib_linux","stdout","stderr","pilot_frame_exists","phase_checkpoint_reached"):
            self.assertIn(field,source)

    def test_failed_worker_writes_diagnostic_and_cannot_claim_recovery(self):
        candidate=validate_candidate().copy()
        candidate["worker_command"]=[sys.executable,"-c","import sys;print('bounded failure',file=sys.stderr);raise SystemExit(9)"]
        with tempfile.TemporaryDirectory(dir=gov.PROJECT/"oc3") as temporary:
            output=Path(temporary)/"synthetic-output"
            terminal=supervise(candidate,output)
            self.assertEqual(terminal["state"],"PILOT_FRAME_SCHEMA_WORKER_FAILED")
            self.assertEqual(terminal["failure_class"],science.WORKER_RUNTIME_FAILURE)
            self.assertTrue((output/"START_INTENT.json").is_file())
            self.assertTrue((output/"EXECUTION_DIAGNOSTIC.json").is_file())
            self.assertTrue((output/"TERMINAL.json").is_file())
            self.assertFalse((output/"PILOT_FRAME.json").exists())
            diagnostic=load_canonical_json(output/"EXECUTION_DIAGNOSTIC.json")
            self.assertEqual(diagnostic["child"]["return_code"],9)


class GovernanceBootstrapTests(unittest.TestCase):
    def test_predecessor_bindings_and_unknown_cause(self):
        self.assertEqual(file_sha256(gov.PRIOR_FINAL_REPORT_PATH),gov.PRIOR_FINAL_REPORT_SHA256)
        self.assertEqual(file_sha256(gov.PRIOR_CLAIM_MATRIX_PATH),gov.PRIOR_CLAIM_MATRIX_SHA256)
        self.assertEqual(file_sha256(gov.PRIOR_TERMINAL_STATE_PATH),gov.PRIOR_TERMINAL_STATE_SHA256)
        self.assertEqual(file_sha256(gov.PRIOR_CONSUMPTION_MARKER_PATH),gov.PRIOR_CONSUMPTION_MARKER_SHA256)

    def test_bound_inputs_exact(self):
        for path,digest in EXPECTED_INPUTS: self.assertEqual(file_sha256(gov.PROJECT/path),digest)

    def test_candidate_exact_commands_and_zero_access(self):
        candidate=validate_candidate()
        validate_invocation(candidate,expected_supervisor_argv())
        validate_invocation(candidate,expected_worker_command(),worker=True)
        self.assertEqual((candidate["network_requests"],candidate["source_rows_read"],candidate["targets_materialized"],candidate["holdouts_materialized"]),(0,0,0,0))
        self.assertEqual(candidate["preceding_failure_class"],"IMPLEMENTATION_SCHEMA_CASE_MISMATCH")
        self.assertEqual(candidate["historical_predecessor_technical_cause"],"UNKNOWN")

    def test_closed_terminal_state_preserves_authorization_and_consumed_permit(self):
        gov.validate_static_authorities(); gov.validate_mandate(); state=gov.validate_state()
        self.assertEqual((state["state"],state["active"],state["permits_issued"]),(gov.STATE_TERMINAL,False,1))
        self.assertTrue(gov.STANDING_AUTHORIZATION_PATH.exists())
        self.assertTrue((gov.PROJECT/validate_candidate()["autonomy_policy"]["permit_output_path"]).exists())
        self.assertEqual(gov.evaluate_candidate(CANDIDATE),{"decision":gov.MANDATE_NOT_ACTIVE,"permit_state":gov.NO_PERMIT_ISSUED})

    def test_zero_budget_firewall_and_terminal_vocabulary(self):
        mandate=gov.validate_mandate()
        self.assertEqual(mandate["budgets"],{"application_body_bytes_parent":0,"application_body_bytes_remaining":0,
            "concurrency":1,"network_requests_parent":0,"network_requests_remaining":0,
            "retries_default":0,"retries_max_per_exact_resource":0})
        self.assertTrue(all(value==0 for value in mandate["firewall"].values()))
        self.assertEqual(gov.TERMINAL_OUTCOMES,("SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERED",
            "SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_INTEGRITY_FAILED","SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_INCONCLUSIVE"))

    def test_policy_core_contains_single_use_and_terminal_closure(self):
        source=inspect.getsource(gov)
        self.assertIn("AUTONOMOUS_PERMIT_ALREADY_CONSUMED",source)
        self.assertIn("finalize_scientific_terminal",source)
        self.assertNotIn("MAX_SOURCE_ROWS_PER_DOMAIN",source)

    def test_worker_has_no_permit_or_network_api(self):
        source=(gov.PROJECT/"oc3/oc3_source_metadata_pilot_frame_schema_recovery_worker.py").read_text()
        for forbidden in ("consume_permit","validate_permit","requests.","urllib","httpx"):
            self.assertNotIn(forbidden,source)


if __name__ == "__main__":
    unittest.main()
