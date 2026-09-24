"""Offline validator for Stage B documentary semantic review."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_observer_grouping import PROJECT,file_sha256,load_canonical_json,sha256_bytes,validate_sealed

STAGE_ID="OC3-CROSS-OBSERVER-GROUPING-OFFLINE-DOCUMENTARY-SEMANTIC-REVIEW-001"
SCOPE="OFFLINE_DOCUMENTARY_SEMANTIC_REVIEW_ONLY"
SPEC=PROJECT/"OC3_CROSS_OBSERVER_GROUPING_OFFLINE_DOCUMENTARY_REVIEW_SPEC_001.md"
CANDIDATE=PROJECT/"oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_OFFLINE_DOCUMENTARY_REVIEW_CANDIDATE_001.json"
RECEIPT=PROJECT/"oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_OFFLINE_DOCUMENTARY_REVIEW_VALIDATION_001.json"
PERMIT=PROJECT/"oc3/CROSS_OBSERVER_GROUPING_AUTONOMY_PERMITS/OC3_CROSS_OBSERVER_GROUPING_OFFLINE_DOCUMENTARY_REVIEW_PERMIT_001.json"
AUTHORIZATION=PROJECT/"oc3/OC3_CROSS_OBSERVER_GROUPING_STANDING_AUTHORIZATION_002.json"
STATE=PROJECT/"oc3/OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_STATE_002.json"
OUTPUT=PROJECT/"oc3/cross_observer_grouping/OC3-CROSS-OBSERVER-GROUPING-OFFLINE-DOCUMENTARY-SEMANTIC-REVIEW-001"
EXECUTABLE=PROJECT/"oc3/.venv/bin/python"
SCRIPT=PROJECT/"oc3/oc3_cross_observer_grouping_offline_review.py"
IMPLEMENTATION_FILES=(
 "OC3_CROSS_OBSERVER_GROUPING_OFFLINE_DOCUMENTARY_REVIEW_SPEC_001.md",
 "oc3/oc3_cross_observer_grouping_offline_review.py",
 "oc3/oc3lib/cross_observer_grouping_offline_review_validation.py",
 "oc3/oc3lib/cross_observer_grouping_documentary_provenance.py")
REQUIRED_INPUT_SUFFIXES=(
 "DR9_CATALOG_FORMAT.body","DR9_RELEASE_DESCRIPTION.body","DR9_FILES_PRODUCTS.body",
 "DATALAB_DR9_TABLE_METADATA_CORRECTED.body","DATALAB_DR9_COLUMN_METADATA_CORRECTED.body",
 "DOCUMENTARY-EVIDENCE-COMPLETION-003/TERMINAL.json",
 "PRIMARY-LITERATURE-RECOVERY-001/TERMINAL.json")

class OfflineReviewValidationError(Exception): pass

def implementation_aggregate():
 return sha256_bytes(canonical({name:file_sha256(PROJECT/name) for name in IMPLEMENTATION_FILES}))

def expected_command_argv():
 return [str(EXECUTABLE),str(SCRIPT),"--review-documentary-evidence","--candidate",str(CANDIDATE),
  "--permit",str(PERMIT),"--standing-authorization",str(AUTHORIZATION),"--autonomy-state",str(STATE),
  "--output-directory",str(OUTPUT)]

def validate_candidate(path:Path=CANDIDATE):
 value=validate_sealed(load_canonical_json(path)); inputs=value.get("input_bindings")
 if (value.get("schema_version")!="OC3_CROSS_OBSERVER_GROUPING_OFFLINE_DOCUMENTARY_REVIEW_CANDIDATE_001" or
     value.get("stage_id")!=STAGE_ID or value.get("scope")!=SCOPE or
     value.get("candidate_state")!="AUTONOMOUS_PROSPECTIVE_ACTION" or
     value.get("implementation_aggregate")!=implementation_aggregate() or
     value.get("resource_caps")!={"application_body_bytes":0,"concurrency":1,"network_requests":0,"retries":0} or
     value.get("source_rows_read")!=0 or value.get("threshold_state")!="NO_RADIUS_OR_SCORE_THRESHOLD_SELECTED" or
     not isinstance(inputs,list) or len(inputs)!=7):
  raise OfflineReviewValidationError("OFFLINE_REVIEW_CANDIDATE_INVALID")
 for binding,suffix in zip(inputs,REQUIRED_INPUT_SUFFIXES):
  p=PROJECT/binding.get("path","")
  if not str(p).endswith(suffix) or not p.is_file() or binding.get("sha256")!=file_sha256(p):
   raise OfflineReviewValidationError("OFFLINE_REVIEW_INPUT_INVALID")
 command=expected_command_argv()
 if value.get("command_argv")!=command or value.get("command_argv_sha256")!=sha256_bytes(canonical(command)):
  raise OfflineReviewValidationError("OFFLINE_REVIEW_COMMAND_INVALID")
 return value

def validate_runtime(candidate,executable:str,script:str,argv:Sequence[str]):
 observed=[executable,script,*argv]
 if observed!=candidate["command_argv"] or sha256_bytes(canonical(observed))!=candidate["command_argv_sha256"]:
  raise OfflineReviewValidationError("RUNTIME_COMMAND_MISMATCH")

