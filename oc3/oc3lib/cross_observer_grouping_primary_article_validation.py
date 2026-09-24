"""Offline validator for the exact ADS primary-article recovery."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence
from .core import canonical
from .cross_observer_grouping import PROJECT,file_sha256,load_canonical_json,sha256_bytes,validate_sealed

STAGE_ID="OC3-CROSS-OBSERVER-GROUPING-PRIMARY-ARTICLE-RECOVERY-002"
SCOPE="PRIMARY_CROSS_IDENTIFICATION_ARTICLE_RECOVERY_ONLY"
SPEC=PROJECT/"OC3_CROSS_OBSERVER_GROUPING_PRIMARY_ARTICLE_RECOVERY_SPEC_002.md"
MANIFEST=PROJECT/"oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_PRIMARY_ARTICLE_RECOVERY_MANIFEST_002.json"
CANDIDATE=PROJECT/"oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_PRIMARY_ARTICLE_RECOVERY_CANDIDATE_002.json"
RECEIPT=PROJECT/"oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_PRIMARY_ARTICLE_RECOVERY_VALIDATION_002.json"
PERMIT=PROJECT/"oc3/CROSS_OBSERVER_GROUPING_AUTONOMY_PERMITS/OC3_CROSS_OBSERVER_GROUPING_PRIMARY_ARTICLE_RECOVERY_PERMIT_002.json"
AUTHORIZATION=PROJECT/"oc3/OC3_CROSS_OBSERVER_GROUPING_STANDING_AUTHORIZATION_002.json"
STATE=PROJECT/"oc3/OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_STATE_002.json"
OUTPUT=PROJECT/"oc3/cross_observer_grouping/OC3-CROSS-OBSERVER-GROUPING-PRIMARY-ARTICLE-RECOVERY-002"
EXECUTABLE=PROJECT/"oc3/.venv/bin/python"; SCRIPT=PROJECT/"oc3/oc3_cross_observer_grouping_primary_article.py"
USER_AGENT="Mozilla/5.0 (compatible; OC3Research/1.0)"
IMPLEMENTATION_FILES=("OC3_CROSS_OBSERVER_GROUPING_PRIMARY_ARTICLE_RECOVERY_SPEC_002.md",
 "oc3/oc3_cross_observer_grouping_primary_article.py","oc3/oc3lib/cross_observer_grouping_primary_article_validation.py",
 "oc3/oc3lib/cross_observer_grouping_documentary_provenance.py")
class ArticleValidationError(Exception): pass
def implementation_aggregate(): return sha256_bytes(canonical({n:file_sha256(PROJECT/n) for n in IMPLEMENTATION_FILES}))
def expected_command_argv(): return [str(EXECUTABLE),str(SCRIPT),"--acquire-primary-article","--candidate",str(CANDIDATE),"--permit",str(PERMIT),"--standing-authorization",str(AUTHORIZATION),"--autonomy-state",str(STATE),"--output-directory",str(OUTPUT)]
def validate_manifest():
 v=validate_sealed(load_canonical_json(MANIFEST)); rs=v.get("resources")
 if (v.get("schema_version")!="OC3_CROSS_OBSERVER_GROUPING_PRIMARY_ARTICLE_RECOVERY_MANIFEST_002" or v.get("stage_id")!=STAGE_ID or v.get("network_request_cap")!=1 or v.get("application_body_byte_cap")!=8388608 or v.get("concurrency")!=1 or v.get("retries")!=0 or v.get("broad_crawling") is not False or v.get("mirror_substitution") is not False or not isinstance(rs,list) or len(rs)!=1): raise ArticleValidationError("ARTICLE_MANIFEST_INVALID")
 r=rs[0]
 if (r.get("id")!="BUDAVARI_SZALAY_2008_ADS_ARTICLE" or r.get("url")!="https://articles.adsabs.harvard.edu/pdf/2008ApJ...679..301B" or r.get("host")!="articles.adsabs.harvard.edu" or r.get("method")!="GET" or r.get("accepted_content_types")!=["application/pdf"] or r.get("application_body_byte_cap")!=8388608 or r.get("redirects")!=0 or r.get("retries")!=0 or r.get("evidence_capture_mode")!="HASHED_RESPONSE_SNAPSHOT" or r.get("revision_identity") is not None): raise ArticleValidationError("ARTICLE_RESOURCE_INVALID")
 return v
def validate_candidate(path:Path=CANDIDATE):
 v=validate_sealed(load_canonical_json(path)); command=expected_command_argv()
 if (v.get("schema_version")!="OC3_CROSS_OBSERVER_GROUPING_PRIMARY_ARTICLE_RECOVERY_CANDIDATE_002" or v.get("stage_id")!=STAGE_ID or v.get("scope")!=SCOPE or v.get("candidate_state")!="AUTONOMOUS_PROSPECTIVE_ACTION" or v.get("implementation_aggregate")!=implementation_aggregate() or v.get("request_headers")!={"User-Agent":USER_AGENT} or v.get("source_rows_read")!=0 or v.get("resource_caps")!={"application_body_bytes":8388608,"concurrency":1,"network_requests":1,"retries":0} or v.get("command_argv")!=command or v.get("command_argv_sha256")!=sha256_bytes(canonical(command))): raise ArticleValidationError("ARTICLE_CANDIDATE_INVALID")
 validate_manifest()
 if v.get("resource_manifest")!={"path":str(MANIFEST.relative_to(PROJECT)),"sha256":file_sha256(MANIFEST)}: raise ArticleValidationError("ARTICLE_MANIFEST_BINDING_INVALID")
 return v
def validate_runtime(c,e:str,s:str,a:Sequence[str]):
 o=[e,s,*a]
 if o!=c["command_argv"] or sha256_bytes(canonical(o))!=c["command_argv_sha256"]: raise ArticleValidationError("RUNTIME_COMMAND_MISMATCH")

