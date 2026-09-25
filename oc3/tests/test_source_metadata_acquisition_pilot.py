import io
import inspect
from email.message import Message
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import file_sha256, load_canonical_json, sealed, sha256_bytes
from oc3lib import source_metadata_acquisition_pilot as science
from oc3lib import source_metadata_acquisition_pilot_governor as gov
from oc3lib.source_metadata_acquisition_pilot_validation import (
    CANDIDATE, DOCUMENTARY_PROVENANCE, FRAME, FRAME_SHA256, QUERY_MANIFEST,
    expected_command_argv, expected_worker_command, implementation_aggregate,
    validate_candidate, validate_documentary_provenance, validate_query_manifest,
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
            with self.assertRaisesRegex(ValueError,"WORKER_RUNTIME_FAILURE"):
                supervisor.run_worker(candidate,output,CANDIDATE)
            self.assertTrue((output/"START_INTENT.json").is_file()); self.assertTrue((output/"SUPERVISOR_FAILURE.json").is_file())
            self.assertFalse((output/"TERMINAL.json").exists())

    def test_terminal_taxonomy_is_separate(self):
        self.assertEqual(science.terminal_outcome_for("SOURCE_COUNT_RESOURCE_BOUND"),"SOURCE_METADATA_ACQUISITION_RESOURCE_BOUND")
        self.assertEqual(science.terminal_outcome_for("DATALAB_TRANSPORT_FAILURE"),"SOURCE_METADATA_ACQUISITION_INCONCLUSIVE")
        self.assertEqual(science.terminal_outcome_for("SOURCE_ORDERING_INTEGRITY_FAILURE"),"SOURCE_METADATA_ACQUISITION_INTEGRITY_FAILED")


class BootstrapGovernanceTests(unittest.TestCase):
    def test_candidate_commands_aggregate_and_zero_observation(self):
        candidate=validate_candidate()
        self.assertEqual(candidate["command_argv"],expected_command_argv()); self.assertEqual(candidate["worker_command"],expected_worker_command())
        self.assertEqual(candidate["implementation_aggregate"],implementation_aggregate())
        self.assertEqual(tuple(candidate[x] for x in ("network_requests","schema_rows_observed","source_counts_observed","source_rows_observed")),(0,0,0,0))

    def test_governor_waits_without_authorization_or_permit(self):
        gov.validate_static_authorities(); mandate=gov.validate_mandate(); state=gov.validate_state()
        self.assertEqual((state["state"],state["active"],state["permits_issued"]),(gov.STATE_WAITING,False,0))
        self.assertEqual((mandate["budgets"]["network_requests_parent"],mandate["budgets"]["application_body_bytes_parent"]),(5,67108864))
        self.assertFalse(gov.STANDING_AUTHORIZATION_PATH.exists()); self.assertFalse((gov.PROJECT/validate_candidate()["autonomy_policy"]["permit_output_path"]).exists())
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
