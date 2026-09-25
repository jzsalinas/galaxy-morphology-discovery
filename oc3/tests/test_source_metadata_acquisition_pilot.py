import io
import inspect
import json
from email.message import Message
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import file_sha256, load_canonical_json, sealed, sha256_bytes
from oc3lib import source_metadata_acquisition_pilot as science
from oc3lib import source_metadata_acquisition_pilot_governor as gov
from oc3lib import source_metadata_acquisition_pilot_validation as validation
from oc3lib.source_metadata_acquisition_pilot_validation import (
    CANDIDATE, DOCUMENTARY_PROVENANCE, FRAME, FRAME_SHA256, QUERY_MANIFEST,
    AcquisitionValidationError, consume_worker_capability, create_worker_capability,
    expected_command_argv, expected_worker_command, implementation_aggregate,
    validate_candidate, validate_documentary_provenance, validate_query_manifest,
    validate_worker_capability, worker_capability_consumption_path,
)
import oc3_source_metadata_acquisition_pilot_supervisor as supervisor
import oc3_source_metadata_acquisition_pilot_worker as worker


def schema_csv(datatype_overrides=None):
    overrides=datatype_overrides or {}
    values={"release":"integer","brickid":"bigint","objid":"bigint","brickname":"varchar",
            "brick_primary":"boolean","ra":"double","dec":"double","ra_ivar":"double","dec_ivar":"double"}
    values.update(datatype_overrides or {})
    rows=["table_name,column_name,datatype,description"]
    for table in science.TABLES:
        for column in science.PROJECTION:
            rows.append(f"{table},{column},{values[column]},synthetic")
    return "\n".join(rows)+"\n"


def source_header():
    return ",".join(science.PROJECTION)+"\n"


class Headers(Message):
    pass


class FakeResponse:
    def __init__(self, body, url, status=200, content_type="text/csv"):
        self._source=io.BytesIO(body); self._url=url; self.status=status; self.closed=False
        self.headers=Headers(); self.headers["Content-Type"]=content_type
    def read(self, size=-1): return self._source.read(size)
    def getcode(self): return self.status
    def geturl(self): return self._url
    def close(self): self.closed=True


class FakeOpener:
    def __init__(self, response, before=None): self.response=response; self.before=before; self.calls=0
    def open(self, request, timeout):
        self.calls+=1
        if self.before: self.before(request,timeout)
        return self.response


class FrozenContractTests(unittest.TestCase):
    def test_exact_endpoint_token_transport_and_caps(self):
        self.assertEqual(science.SERVICE_ENDPOINT,"https://datalab.noirlab.edu/query/query")
        self.assertEqual(science.PUBLIC_ANONYMOUS_TOKEN,"anonymous.0.0.anon_access")
        self.assertEqual((science.REQUEST_CAP,science.BODY_CAP,science.CONCURRENCY,science.RETRIES,science.REDIRECTS,science.RESUME),(5,67108864,1,0,0,False))
        self.assertEqual(science.frozen_headers()["X-DL-AuthToken"],science.PUBLIC_ANONYMOUS_TOKEN)

    def test_target_holdout_literals_are_exact_disjoint_and_sorted(self):
        self.assertEqual(len(science.TARGET_GUARD_UNION),14); self.assertEqual(len(science.HOLDOUT_GUARD_UNION),16)
        self.assertEqual(science.TARGET_GUARD_UNION,tuple(sorted(science.TARGET_GUARD_UNION)))
        self.assertEqual(science.HOLDOUT_GUARD_UNION,tuple(sorted(science.HOLDOUT_GUARD_UNION)))
        self.assertFalse(set(science.TARGET_GUARD_UNION)&set(science.HOLDOUT_GUARD_UNION))
        science.validate_frozen_support()

    def test_frame_binding_targets_holdouts_and_brick_map(self):
        mapping,targets,holdouts=science.frame_support(FRAME,FRAME_SHA256)
        self.assertEqual(targets,science.TARGET_IDENTITIES); self.assertEqual(holdouts,science.HOLDOUT_IDENTITIES)
        self.assertEqual(tuple(mapping),science.TARGET_GUARD_UNION)

    def test_exact_five_queries_hashes_and_urls(self):
        manifest=validate_query_manifest()
        self.assertEqual(tuple(row["id"] for row in manifest["queries"]),science.REQUEST_ORDER)
        for row in manifest["queries"]:
            literal=science.QUERY_LITERALS[row["id"]]
            self.assertEqual(row["canonical_sha256"],science.query_sha256(literal))
            self.assertEqual(row["literal_url"],science.query_url(literal))
            self.assertIn("adql=",row["literal_url"]); self.assertIn("%20",row["literal_url"])

    def test_forbidden_query_families_and_holdout_fail_closed(self):
        for query in ("SELECT * FROM ls_dr9.tractor","SELECT x FROM ls_dr9.tractor_n WHERE q3c_radial_query(x)",
                      "SELECT x FROM mydb.t","SELECT x FROM ls_dr9.tractor_n WHERE brickname='1075p337'"):
            with self.assertRaises(science.AcquisitionError): science.validate_query_boundary(query)
        for table in ("ls_dr9.tractor","ls_dr10.tractor_n"):
            with self.assertRaises(science.AcquisitionError): science.count_query(table)

    def test_projection_and_top_are_literal(self):
        self.assertEqual(science.PROJECTION,("release","brickid","objid","brickname","brick_primary","ra","dec","ra_ivar","dec_ivar"))
        self.assertIn("SELECT TOP 150001",science.QUERY_LITERALS["north_rows"])
        self.assertNotIn("SELECT *",science.QUERY_LITERALS["north_rows"].upper())

    def test_documentary_record_is_offline_and_transport_only(self):
        value=validate_documentary_provenance()
        self.assertEqual(value["network_requests"],0); self.assertTrue(value["transport_semantics_only"])
        self.assertEqual(len(value["sources"]),6)
        source=next(row for row in value["sources"] if row["id"]=="ASTRO_DATALAB_QUERY_CLIENT_SOURCE")
        self.assertEqual((source["repository"],source["file"]),("astro-datalab/datalab","dl/queryClient.py"))
        self.assertIsNone(source["exact_commit"])


class GateAndCsvTests(unittest.TestCase):
    def test_schema_18_row_gate_and_datatype_allowlists(self):
        observed=science.parse_schema(io.StringIO(schema_csv()))
        self.assertEqual(set(observed),set(science.TABLES)); self.assertTrue(all(len(x)==9 for x in observed.values()))
        with self.assertRaisesRegex(science.AcquisitionError,"DATALAB_SCHEMA_MISMATCH"):
            science.parse_schema(io.StringIO(schema_csv({"ra":"opaque"})))

    def test_schema_header_duplicate_and_missing_fail(self):
        with self.assertRaisesRegex(science.AcquisitionError,"SOURCE_RESPONSE_HEADER_MISMATCH"):
            science.parse_schema(io.StringIO("column_name,table_name,datatype,description\n"))
        text=schema_csv(); duplicated=text+text.splitlines()[1]+"\n"
        with self.assertRaisesRegex(science.AcquisitionError,"DATALAB_SCHEMA_MISMATCH"):
            science.parse_schema(io.StringIO(duplicated))
        with self.assertRaisesRegex(science.AcquisitionError,"DATALAB_SCHEMA_MISMATCH"):
            science.parse_schema(io.StringIO("\n".join(text.splitlines()[:-1])+"\n"))

    def test_schema_before_counts_and_both_counts_before_rows(self):
        flow=science.AcquisitionSequence()
        with self.assertRaises(science.AcquisitionError): flow.accept_count("north",{})
        schema={table:{column:"x" for column in science.PROJECTION} for table in science.TABLES}
        flow.accept_schema(schema); flow.accept_count("north",{})
        self.assertFalse(flow.rows_allowed()); flow.accept_count("south",{})
        self.assertTrue(flow.rows_allowed())

    def test_resource_bound_stops_rows_without_substitution(self):
        flow=science.AcquisitionSequence(); schema={t:{c:"x" for c in science.PROJECTION} for t in science.TABLES}
        flow.accept_schema(schema); flow.accept_count("north",{science.TARGET_GUARD_UNION[0]:150001}); flow.accept_count("south",{})
        self.assertTrue(flow.resource_bound); self.assertFalse(flow.rows_allowed())
        self.assertEqual(flow.counts["north"],150001)

    def test_count_parsing_zero_fill_duplicates_holdout_and_unexpected(self):
        first=science.TARGET_GUARD_UNION[0]
        parsed=science.parse_counts(io.StringIO(f"brickname,source_count\n{first},2\n"))
        self.assertEqual(parsed[first],2); self.assertEqual(sum(parsed.values()),2)
        for body in (f"brickname,source_count\n{first},1\n{first},2\n",
                     "brickname,source_count\n1075p337,1\n","brickname,source_count\nnot-a-brick,1\n"):
            with self.assertRaises(science.AcquisitionError): science.parse_counts(io.StringIO(body))

    def test_valid_rows_brick_crosscheck_counts_order_coordinates_and_ivars(self):
        name=science.TARGET_GUARD_UNION[0]; brick_ids,_,_=science.frame_support(FRAME,FRAME_SHA256)
        counts={item:0 for item in science.TARGET_GUARD_UNION}; counts[name]=2
        body=source_header()+f"9010,{brick_ids[name]},1,{name},1,10,-1,2,0\n9010,{brick_ids[name]},2,{name},true,11,0,,nan\n"
        result=science.validate_source_rows(io.StringIO(body),counts,brick_ids)
        self.assertEqual(result["accepted_row_count"],2)
        self.assertEqual(result["ivar_states"]["ra_ivar"],{"POSITIVE_FINITE":1,"ZERO":0,"MISSING":1,"INVALID":0})
        self.assertEqual(result["ivar_states"]["dec_ivar"],{"POSITIVE_FINITE":0,"ZERO":1,"MISSING":0,"INVALID":1})

    def _row_case(self,row,counts=None):
        name=science.TARGET_GUARD_UNION[0]; ids,_,_=science.frame_support(FRAME,FRAME_SHA256)
        expected={item:0 for item in science.TARGET_GUARD_UNION}; expected[name]=1 if counts is None else counts
        return lambda: science.validate_source_rows(io.StringIO(source_header()+row+"\n"),expected,ids)

    def test_row_header_identity_brick_primary_and_coordinate_failures(self):
        name=science.TARGET_GUARD_UNION[0]; ids,_,_=science.frame_support(FRAME,FRAME_SHA256); brick=ids[name]
        cases=(f"9010,{brick+1},1,{name},1,1,1,1,1",f"9010,{brick},1,{name},0,1,1,1,1",
               f"9010,{brick},1,{name},1,360,1,1,1",f"9010,{brick},1,{name},1,1,-91,1,1")
        for row in cases:
            with self.subTest(row=row), self.assertRaises(science.AcquisitionError): self._row_case(row)()
        with self.assertRaisesRegex(science.AcquisitionError,"SOURCE_RESPONSE_HEADER_MISMATCH"):
            science.validate_source_rows(io.StringIO("objid,release\n"),{},ids)

    def test_duplicate_decreasing_count_mismatch_and_top_overflow(self):
        name=science.TARGET_GUARD_UNION[0]; ids,_,_=science.frame_support(FRAME,FRAME_SHA256); brick=ids[name]
        counts={item:0 for item in science.TARGET_GUARD_UNION}; counts[name]=2
        same=f"9010,{brick},1,{name},1,1,1,1,1"
        with self.assertRaisesRegex(science.AcquisitionError,"SOURCE_ORDERING_INTEGRITY_FAILURE"):
            science.validate_source_rows(io.StringIO(source_header()+same+"\n"+same+"\n"),counts,ids)
        with self.assertRaisesRegex(science.AcquisitionError,"SOURCE_COUNT_ROW_MISMATCH"):
            science.validate_source_rows(io.StringIO(source_header()+same+"\n"),counts,ids)
        many=source_header()+"".join(f"9010,{brick},{i},{name},1,1,1,1,1\n" for i in range(150001))
        over={item:0 for item in science.TARGET_GUARD_UNION}; over[name]=150001
        with self.assertRaisesRegex(science.AcquisitionError,"SOURCE_COUNT_ROW_MISMATCH"):
            science.validate_source_rows(io.StringIO(many),over,ids)

    def test_ivar_classification_exact(self):
        self.assertEqual([science.classify_ivar(x) for x in ("1","0","","-1","nan","bad")],
                         ["POSITIVE_FINITE","ZERO","MISSING","INVALID","INVALID","INVALID"])


class TransportAndWorkerTests(unittest.TestCase):
    def test_direct_worker_without_capability_fails_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            command=[sys.executable,str(worker.__file__),"--run-acquisition-worker",
                "--candidate",str(CANDIDATE),"--output",str(Path(tmp)/"output")]
            result=subprocess.run(command,capture_output=True,text=True,check=False)
        self.assertNotEqual(result.returncode,0)
        failure=json.loads(result.stderr)
        self.assertEqual(failure,{"error":"WORKER_EXECUTION_CAPABILITY_REQUIRED",
            "network_requests":0,"state":"WORKER_BLOCKED"})

    def test_request_intent_is_durable_before_transport(self):
        url=science.query_url(science.SCHEMA_QUERY); accounting=science.Accounting()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); ledger=root/"ledger"; target=root/"schema.csv"
            opener=FakeOpener(FakeResponse(b"x\n",url),before=lambda req,timeout:self.assertTrue((ledger/"01_schema_INTENT.json").is_file()))
            result=science.bounded_get("schema",url,science.RESPONSE_CAPS["schema"],target,accounting,lambda:opener,ledger)
            self.assertEqual((accounting.requests_started,accounting.body_bytes_read),(1,2))
            self.assertEqual(result["query_sha256"],science.query_sha256(science.SCHEMA_QUERY))
            self.assertTrue((ledger/"01_schema_RESULT.json").is_file())

    def test_body_cap_failure_charges_all_bytes_read(self):
        url=science.query_url(science.SCHEMA_QUERY); cap=science.RESPONSE_CAPS["schema"]
        accounting=science.Accounting(); response=FakeResponse(b"x"*(cap+1),url)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(science.AcquisitionError,"DATALAB_BODY_CAP_EXCEEDED"):
                science.bounded_get("schema",url,cap,Path(tmp)/"body",accounting,lambda:FakeOpener(response))
        self.assertEqual(accounting.requests_started,1); self.assertEqual(accounting.body_bytes_read,cap+1)

    def test_redirect_auth_final_url_and_retry_zero(self):
        with self.assertRaisesRegex(science.AcquisitionError,"DATALAB_REDIRECT_FORBIDDEN"):
            science.RejectRedirect().redirect_request(None,None,302,"x",{},"https://elsewhere")
        self.assertEqual(science.RETRIES,0)
        url=science.query_url(science.SCHEMA_QUERY)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(science.AcquisitionError,"DATALAB_REDIRECT_FORBIDDEN"):
            science.bounded_get("schema",url,science.RESPONSE_CAPS["schema"],Path(tmp)/"x",science.Accounting(),
                                lambda:FakeOpener(FakeResponse(b"x",url+"/redirected")))

    def test_worker_full_empty_populations_uses_exact_five_request_order(self):
        candidate=validate_candidate(); bodies={"schema":schema_csv(),"north_count":"brickname,source_count\n",
            "south_count":"brickname,source_count\n","north_rows":source_header(),"south_rows":source_header()}
        observed=[]
        def fake_get(qid,url,cap,target,accounting,opener_factory=None,ledger_directory=None):
            observed.append(qid); accounting.requests_started+=1; data=bodies[qid].encode(); accounting.body_bytes_read+=len(data)
            target.write_bytes(data); return {"query_id":qid}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(worker,"bounded_get",side_effect=fake_get):
            output=Path(tmp)/"run"; output.mkdir(); terminal=worker.execute(candidate,output)
            self.assertEqual(terminal["state"],"SOURCE_METADATA_ACQUISITION_COMPLETED")
            self.assertEqual(tuple(observed),science.REQUEST_ORDER); self.assertTrue((output/"FINAL_REPORT.md").is_file())

    def test_worker_count_resource_bound_stops_after_three_requests(self):
        candidate=validate_candidate(); name=science.TARGET_GUARD_UNION[0]
        bodies={"schema":schema_csv(),"north_count":f"brickname,source_count\n{name},150001\n",
                "south_count":"brickname,source_count\n"}; observed=[]
        def fake_get(qid,url,cap,target,accounting,opener_factory=None,ledger_directory=None):
            observed.append(qid); accounting.requests_started+=1; data=bodies[qid].encode(); accounting.body_bytes_read+=len(data); target.write_bytes(data); return {}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(worker,"bounded_get",side_effect=fake_get):
            output=Path(tmp)/"run"; output.mkdir(); terminal=worker.execute(candidate,output)
            self.assertEqual(terminal["state"],"SOURCE_METADATA_ACQUISITION_RESOURCE_BOUND")
            self.assertEqual(observed,["schema","north_count","south_count"])

    def test_supervisor_preserves_worker_failure_evidence(self):
        candidate=validate_candidate().copy(); candidate["worker_command"]=["/bin/sh","-c","exit 9"]
        with tempfile.TemporaryDirectory(dir=gov.PROJECT/"oc3") as tmp:
            output=Path(tmp)/"failure"
            with mock.patch.object(supervisor,"create_worker_capability"), self.assertRaisesRegex(ValueError,"WORKER_RUNTIME_FAILURE"):
                supervisor.run_worker(candidate,output,candidate_path=CANDIDATE,permit_path=CANDIDATE,
                    standing_authorization_path=CANDIDATE,autonomy_state_path=CANDIDATE,
                    permit_consumption_marker=CANDIDATE)
            self.assertTrue((output/"START_INTENT.json").is_file()); self.assertTrue((output/"SUPERVISOR_FAILURE.json").is_file())
            self.assertFalse((output/"TERMINAL.json").exists())

    def test_terminal_taxonomy_is_separate(self):
        self.assertEqual(science.terminal_outcome_for("SOURCE_COUNT_RESOURCE_BOUND"),"SOURCE_METADATA_ACQUISITION_RESOURCE_BOUND")
        self.assertEqual(science.terminal_outcome_for("DATALAB_TRANSPORT_FAILURE"),"SOURCE_METADATA_ACQUISITION_INCONCLUSIVE")
        self.assertEqual(science.terminal_outcome_for("SOURCE_ORDERING_INTEGRITY_FAILURE"),"SOURCE_METADATA_ACQUISITION_INTEGRITY_FAILED")


class WorkerCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=gov.PROJECT/"oc3")
        self.root=Path(self.tmp.name); self.output=self.root/"output"; self.output.mkdir()
        self.candidate_path=self.root/"candidate.json"; self.permit=self.root/"permit.json"
        self.authorization=self.root/"authorization.json"; self.state=self.root/"state.json"
        self.capability=self.output/"OC3_SOURCE_METADATA_ACQUISITION_WORKER_CAPABILITY_001.json"
        self.old_state,self.old_auth=validation.STATE,validation.AUTHORIZATION
        self.old_consumption=validation.WORKER_CAPABILITY_CONSUMPTION_ROOT
        self.old_governor_consumption=gov.CONSUMPTION_ROOT
        validation.STATE=self.state; validation.AUTHORIZATION=self.authorization
        validation.WORKER_CAPABILITY_CONSUMPTION_ROOT=self.root/"capability-consumption"
        gov.CONSUMPTION_ROOT=self.root/"permit-consumption"
        self._write(self.permit,sealed({"kind":"synthetic-permit"}))
        self._write(self.authorization,sealed({"kind":"synthetic-authorization"}))
        self._write(self.state,sealed({"kind":"synthetic-state"}))
        candidate={k:v for k,v in load_canonical_json(CANDIDATE).items() if k!="sealed"}
        candidate["output_directory"]=str(self.output.relative_to(gov.PROJECT))
        candidate["worker_capability_path"]=str(self.capability.relative_to(gov.PROJECT))
        candidate["autonomy_policy"]=dict(candidate["autonomy_policy"])
        candidate["autonomy_policy"]["permit_output_path"]=str(self.permit.relative_to(gov.PROJECT))
        candidate["worker_command"]=[sys.executable,str(worker.__file__),"--run-acquisition-worker",
            "--candidate",str(self.candidate_path),"--output",str(self.output),
            "--execution-capability",str(self.capability)]
        candidate["worker_command_sha256"]=sha256_bytes(canonical(candidate["worker_command"]))
        self.candidate=sealed(candidate); self._write(self.candidate_path,self.candidate)
        self.permit_marker=gov._consumption_marker_path(self.permit)
        marker=sealed({"candidate_sha256":file_sha256(self.candidate_path),
            "permit_sha256":file_sha256(self.permit),"state":"PERMIT_CONSUMPTION_INTENT_RECORDED"})
        self._write(self.permit_marker,marker)
        with mock.patch.object(gov,"validate_consumption_marker",return_value=marker):
            create_worker_capability(candidate=self.candidate,candidate_path=self.candidate_path,
                permit_path=self.permit,standing_authorization_path=self.authorization,
                autonomy_state_path=self.state,output_directory=self.output,
                permit_consumption_marker=self.permit_marker,issued_at_utc="2026-09-25T12:00:00Z")
        self.valid_bytes=self.capability.read_bytes()

    def tearDown(self):
        validation.STATE=self.old_state; validation.AUTHORIZATION=self.old_auth
        validation.WORKER_CAPABILITY_CONSUMPTION_ROOT=self.old_consumption
        gov.CONSUMPTION_ROOT=self.old_governor_consumption
        self.tmp.cleanup()

    @staticmethod
    def _write(path, value):
        path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(canonical(value)+b"\n")

    def _replace_capability(self, mutator, reseal=True):
        value=load_canonical_json(self.capability)
        body={k:v for k,v in value.items() if k!="sealed"}; mutator(body)
        replacement=sealed(body) if reseal else {**body,"sealed":"0"*64}
        self.capability.unlink(); self._write(self.capability,replacement)

    def _validate(self):
        with mock.patch.object(gov,"validate_permit"), mock.patch.object(gov,"validate_consumption_marker"), \
                mock.patch.object(worker,"bounded_get") as network:
            result=validate_worker_capability(self.capability,candidate=self.candidate,
                candidate_path=self.candidate_path,output_directory=self.output)
            self.assertEqual(network.call_count,0)
            return result

    def test_valid_capability_consumes_once_before_any_transport(self):
        self._validate()
        with mock.patch.object(gov,"validate_permit"), mock.patch.object(gov,"validate_consumption_marker"), \
                mock.patch.object(worker,"bounded_get") as network:
            marker=consume_worker_capability(self.capability,candidate=self.candidate,
                candidate_path=self.candidate_path,output_directory=self.output,
                consumed_at_utc="2026-09-25T12:01:00Z")
            self.assertTrue(marker.is_file()); self.assertEqual(network.call_count,0)
            observed=load_canonical_json(marker)
            self.assertEqual(observed["capability_sha256"],file_sha256(self.capability))
            with self.assertRaisesRegex(AcquisitionValidationError,"WORKER_EXECUTION_CAPABILITY_ALREADY_CONSUMED"):
                consume_worker_capability(self.capability,candidate=self.candidate,
                    candidate_path=self.candidate_path,output_directory=self.output)
            self.assertEqual(network.call_count,0)

    def test_invalid_capability_matrix_fails_without_network(self):
        mutations=(
            ("bad seal",lambda body: body.update({"candidate_sha256":"1"*64}),False),
            ("wrong candidate SHA",lambda body: body.update({"candidate_sha256":"1"*64}),True),
            ("wrong permit SHA",lambda body: body.update({"permit_sha256":"2"*64}),True),
            ("wrong authorization SHA",lambda body: body.update({"standing_authorization_sha256":"3"*64}),True),
            ("wrong query manifest SHA",lambda body: body.update({"query_manifest_sha256":"4"*64}),True),
            ("wrong worker argv SHA",lambda body: body.update({"worker_command_sha256":"5"*64}),True),
            ("wrong output",lambda body: body.update({"output_directory":"oc3/wrong-output"}),True),
            ("wrong stage",lambda body: body.update({"stage_id":"WRONG-STAGE"}),True),
        )
        for label,mutation,reseal in mutations:
            with self.subTest(label=label):
                self.capability.unlink(); self.capability.write_bytes(self.valid_bytes)
                self._replace_capability(mutation,reseal=reseal)
                with mock.patch.object(gov,"validate_permit"), mock.patch.object(gov,"validate_consumption_marker"), \
                        mock.patch.object(worker,"bounded_get") as network, \
                        self.assertRaisesRegex(AcquisitionValidationError,"WORKER_EXECUTION_CAPABILITY_INVALID"):
                    validate_worker_capability(self.capability,candidate=self.candidate,
                        candidate_path=self.candidate_path,output_directory=self.output)
                self.assertEqual(network.call_count,0)

    def test_already_consumed_capability_fails_without_network(self):
        marker=worker_capability_consumption_path(self.capability)
        self._write(marker,sealed({"already":True}))
        with mock.patch.object(worker,"bounded_get") as network, \
                self.assertRaisesRegex(AcquisitionValidationError,"WORKER_EXECUTION_CAPABILITY_ALREADY_CONSUMED"):
            validate_worker_capability(self.capability,candidate=self.candidate,
                candidate_path=self.candidate_path,output_directory=self.output)
        self.assertEqual(network.call_count,0)

    def test_structural_order_has_no_transport_before_capability_consumption(self):
        worker_source=inspect.getsource(worker.main)
        self.assertLess(worker_source.index("validate_worker_capability("),
            worker_source.index("consume_worker_capability("))
        self.assertLess(worker_source.index("consume_worker_capability("),worker_source.index("execute("))
        supervisor_source=inspect.getsource(supervisor.main)
        self.assertLess(supervisor_source.index("validate_permit("),supervisor_source.index("consume_permit("))
        self.assertLess(supervisor_source.index("consume_permit("),supervisor_source.index("run_worker("))
        launch_source=inspect.getsource(supervisor.run_worker)
        self.assertLess(launch_source.index("START_INTENT.json"),launch_source.index("create_worker_capability("))
        self.assertLess(launch_source.index("create_worker_capability("),launch_source.index("run_child("))


class BootstrapGovernanceTests(unittest.TestCase):
    def test_synthetic_governed_lifecycle_consumes_capability_before_transport(self):
        with tempfile.TemporaryDirectory(dir=gov.PROJECT/"oc3") as tmp:
            root=Path(tmp); output=root/"output"; capability=output/"OC3_SOURCE_METADATA_ACQUISITION_WORKER_CAPABILITY_001.json"
            candidate_path=root/"candidate.json"; receipt_path=root/"receipt.json"; permit=root/"permit.json"
            state_path=root/"state.json"; authorization=root/"authorization.json"; ledger=root/"ledger"
            def write(path,value):
                path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(canonical(value)+b"\n"); return path
            def binding(path):
                return {"path":str(Path(path).relative_to(gov.PROJECT)),"sha256":file_sha256(path)}

            candidate={k:v for k,v in load_canonical_json(CANDIDATE).items() if k!="sealed"}
            candidate["output_directory"]=str(output.relative_to(gov.PROJECT))
            candidate["worker_capability_path"]=str(capability.relative_to(gov.PROJECT))
            candidate["worker_command"]=["synthetic-worker","--execution-capability",str(capability)]
            candidate["worker_command_sha256"]=sha256_bytes(canonical(candidate["worker_command"]))
            payload={k:v for k,v in candidate.items() if k!="autonomy_policy"}
            payload_sha=sha256_bytes(canonical(payload))
            receipt={k:v for k,v in load_canonical_json(validation.RECEIPT).items() if k!="sealed"}
            receipt["candidate_payload_sha256"]=payload_sha
            write(receipt_path,sealed(receipt))
            contract=dict(candidate["autonomy_policy"])
            contract["action_validation_receipt"]=binding(receipt_path)
            contract["candidate_payload_sha256"]=payload_sha
            contract["permit_output_path"]=str(permit.relative_to(gov.PROJECT))
            candidate["autonomy_policy"]=contract
            write(candidate_path,sealed(candidate)); candidate=load_canonical_json(candidate_path)

            state={k:v for k,v in load_canonical_json(gov.STATE_PATH).items() if k!="sealed"}
            state.update({"active":False,"current_stage":"FIRST_ACTION_PREPARED",
                "first_candidate":binding(candidate_path),"last_completed_stage":None,"last_terminal":None,
                "body_budget_remaining":science.BODY_CAP,"permits_issued":0,"registered_pending_action":None,
                "requests_remaining":science.REQUEST_CAP,"scientific_outcome":None,"sequence":0,
                "standing_authorization":None,"standing_authorization_initial_state_sha256":None,
                "state":gov.STATE_WAITING,"stop_reason":None})
            write(state_path,sealed(state))
            write(authorization,sealed({"authorization_state":"STANDING_HUMAN_AUTONOMY_AUTHORIZATION",
                "authorized":True,"authorized_at_utc":"2026-09-25T12:00:00Z","authorized_by":"Synthetic Reviewer",
                "continuation_policy":"CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN",
                "first_candidate_path":str(candidate_path.relative_to(gov.PROJECT)),
                "first_candidate_sha256":file_sha256(candidate_path),
                "initial_state_path":str(state_path.relative_to(gov.PROJECT)),
                "initial_state_sha256":file_sha256(state_path),
                "mandate_path":str(gov.MANDATE_PATH.relative_to(gov.PROJECT)),
                "mandate_sha256":file_sha256(gov.MANDATE_PATH),"mission_id":gov.MISSION_ID,
                "mission_scope":gov.MISSION_SCOPE,
                "policy_core_manifest_path":str(gov.POLICY_CORE_MANIFEST_PATH.relative_to(gov.PROJECT)),
                "policy_core_manifest_sha256":file_sha256(gov.POLICY_CORE_MANIFEST_PATH),
                "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_PILOT_STANDING_AUTHORIZATION_001"}))

            old_gov_consumption=gov.CONSUMPTION_ROOT
            old_state,old_auth=validation.STATE,validation.AUTHORIZATION
            old_cap_consumption=validation.WORKER_CAPABILITY_CONSUMPTION_ROOT
            try:
                gov.CONSUMPTION_ROOT=ledger/"PERMIT_CONSUMPTION"
                validation.STATE=state_path; validation.AUTHORIZATION=authorization
                validation.WORKER_CAPABILITY_CONSUMPTION_ROOT=ledger/"WORKER_CAPABILITY_CONSUMPTION"
                gov.activate_standing_autonomy(state_path=state_path,standing_authorization_path=authorization,
                    ledger_directory=ledger,activated_at_utc="2026-09-25T12:01:00Z",current_branch=gov.AUTONOMY_BRANCH)
                gov.register_pending_action(state_path=state_path,candidate_path=candidate_path,
                    standing_authorization_path=authorization,ledger_directory=ledger,
                    registered_at_utc="2026-09-25T12:02:00Z",current_branch=gov.AUTONOMY_BRANCH)
                gov.issue_permit(candidate_path=candidate_path,state_path=state_path,
                    standing_authorization_path=authorization,output_path=permit,ledger_directory=ledger,
                    issued_at_utc="2026-09-25T12:03:00Z")
                permit_marker=gov.consume_permit(permit,candidate_path=candidate_path,state_path=state_path,
                    standing_authorization_path=authorization,consumed_at_utc="2026-09-25T12:04:00Z")
                events=[]; transport=mock.Mock(side_effect=lambda:events.append("first_request_intent"))
                def synthetic_child(_command):
                    consume_worker_capability(capability,candidate=candidate,candidate_path=candidate_path,
                        output_directory=output,consumed_at_utc="2026-09-25T12:05:00Z")
                    events.append("capability_consumed"); transport()
                    write(output/"TERMINAL.json",sealed({"application_body_bytes_read":0,"counters":{},
                        "scope":candidate["scope"],"stage_id":candidate["stage_id"],
                        "state":"SOURCE_METADATA_ACQUISITION_COMPLETED"}))
                    return {"return_code":0,"synthetic":True}
                with mock.patch.object(supervisor,"run_child",side_effect=synthetic_child):
                    terminal=supervisor.run_worker(candidate,output,candidate_path=candidate_path,
                        permit_path=permit,standing_authorization_path=authorization,
                        autonomy_state_path=state_path,permit_consumption_marker=permit_marker)
                self.assertEqual(events,["capability_consumed","first_request_intent"])
                self.assertEqual(transport.call_count,1)
                self.assertEqual(terminal["state"],"SOURCE_METADATA_ACQUISITION_COMPLETED")
                self.assertTrue(worker_capability_consumption_path(capability).is_file())
            finally:
                gov.CONSUMPTION_ROOT=old_gov_consumption
                validation.STATE=old_state; validation.AUTHORIZATION=old_auth
                validation.WORKER_CAPABILITY_CONSUMPTION_ROOT=old_cap_consumption

    def test_candidate_commands_aggregate_and_zero_observation(self):
        candidate=validate_candidate()
        self.assertEqual(candidate["command_argv"],expected_command_argv()); self.assertEqual(candidate["worker_command"],expected_worker_command())
        self.assertEqual(candidate["implementation_aggregate"],implementation_aggregate())
        self.assertEqual(tuple(candidate[x] for x in ("network_requests","schema_rows_observed","source_counts_observed","source_rows_observed")),(0,0,0,0))

    def test_closed_predecessor_governor_is_terminal_and_inactive(self):
        gov.validate_static_authorities(); mandate=gov.validate_mandate(); state=gov.validate_state()
        self.assertEqual((state["state"],state["active"],state["permits_issued"]),(gov.STATE_TERMINAL,False,1))
        self.assertEqual((mandate["budgets"]["network_requests_parent"],mandate["budgets"]["application_body_bytes_parent"]),(5,67108864))
        self.assertTrue(gov.STANDING_AUTHORIZATION_PATH.exists()); self.assertTrue((gov.PROJECT/validate_candidate()["autonomy_policy"]["permit_output_path"]).exists())
        self.assertEqual(gov.evaluate_candidate(),{"decision":gov.MANDATE_NOT_ACTIVE,"permit_state":gov.NO_PERMIT_ISSUED})

    def test_predecessor_exact_bindings_and_terminal_commit(self):
        self.assertEqual(file_sha256(gov.PRIOR_FINAL_REPORT_PATH),gov.PRIOR_FINAL_REPORT_SHA256)
        self.assertEqual(file_sha256(gov.PRIOR_CLAIM_MATRIX_PATH),gov.PRIOR_CLAIM_MATRIX_SHA256)
        self.assertEqual(file_sha256(gov.PILOT_FRAME_PATH),gov.PILOT_FRAME_SHA256)
        self.assertEqual(gov.TERMINAL_COMMIT,"cf34a0efae274a198ac924f99da6135597a7d451")

    def test_policy_core_has_single_use_and_terminal_finalization(self):
        source=inspect.getsource(gov)
        self.assertIn("AUTONOMOUS_PERMIT_ALREADY_CONSUMED",source)
        self.assertIn("finalize_scientific_terminal",source)
        self.assertEqual(gov.TERMINAL_OUTCOMES,science.OUTCOMES)

    def test_no_scientific_topology_algorithm_in_acquisition_module(self):
        source=inspect.getsource(science).lower()
        for token in ("match_radius","object_group_id =","split_group_id =","bayes_factor","nearest_neighbor"):
            self.assertNotIn(token,source)
        for key in ("matching_operations","angular_separation_operations","object_group_ids_created","split_group_ids_created"):
            self.assertIn(key,gov.FIREWALL_KEYS)


if __name__ == "__main__":
    unittest.main()
