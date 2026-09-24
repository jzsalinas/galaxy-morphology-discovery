#!/usr/bin/env python3
"""Deterministic zero-network semantic review of captured primary evidence."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from html.parser import HTMLParser
import json,os
from pathlib import Path
import subprocess,sys

sys.dont_write_bytecode=True
for _key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[_key]="1"

from oc3lib.cross_id_formalism_recovery import PROJECT,sealed,write_json_immutable
from oc3lib.cross_id_formalism_recovery_offline_review_validation import (
 CANDIDATE,OfflineReviewValidationError,validate_candidate,validate_runtime_invocation)

class CitationParser(HTMLParser):
    def __init__(self): super().__init__(); self.values={}
    def handle_starttag(self,tag,attrs):
        if tag!="meta": return
        item=dict(attrs); name=item.get("name","")
        if name.startswith("citation_"): self.values.setdefault(name,[]).append(item.get("content",""))

def parser():
    result=argparse.ArgumentParser(description="Offline primary-literature semantic review")
    modes=result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-candidate",action="store_true")
    modes.add_argument("--review-primary-evidence",action="store_true")
    result.add_argument("--candidate",type=Path,default=CANDIDATE); result.add_argument("--permit",type=Path)
    result.add_argument("--standing-authorization",type=Path); result.add_argument("--autonomy-state",type=Path)
    result.add_argument("--output-directory",type=Path); return result

def _evidence(candidate):
    by_name={Path(x["path"]).name:PROJECT/x["path"] for x in candidate["input_bindings"]}
    html=by_name["BUDAVARI_SZALAY_ARXIV_ABSTRACT_V3.body"].read_text(errors="strict")
    parsed=CitationParser(); parsed.feed(html)
    pdf=by_name["BUDAVARI_SZALAY_ASPC_394_165_DIRECT_PUBLISHER.body"]
    run=subprocess.run(["pdftotext","-layout",str(pdf),"-"],check=True,capture_output=True,text=True)
    text=run.stdout
    required_html={"citation_title":"Probabilistic Cross-Identification of Astronomical Sources",
        "citation_arxiv_id":"0707.1611","citation_online_date":"2008/02/11"}
    for key,expected in required_html.items():
        if expected not in parsed.values.get(key,[]): raise OfflineReviewValidationError("ARXIV_IDENTITY_MISMATCH")
    authors=parsed.values.get("citation_author",[])
    if authors!=["Budavari, Tamas","Szalay, Alexander S."]:
        raise OfflineReviewValidationError("ARXIV_AUTHORSHIP_MISMATCH")
    markers=("ASP Conference Series, Vol. 394","Probabilistic Cross-Identification of Astronomical Sources",
        "Budava", "Nieto-Santisteban", "astronomical point sources", "Bayesian approach",
        "not symmetric", "algorithms that are symmetric", "same source", "separate sources",
        "normal distribution", "probability density function", "spherical normal distribution",
        "inverse of the covariance matrix", "prior probability", "physical properties",
        "posterior probability", "simple radius thresholds", "maximum search radius", "custom thresholds")
    missing=[m for m in markers if m not in text]
    if missing: raise OfflineReviewValidationError("PRIMARY_EVIDENCE_MARKER_MISSING:"+",".join(missing))
    return parsed.values,text,subprocess.run(["pdftotext","-v"],capture_output=True,text=True).stderr.splitlines()[0]

def _review(candidate,output):
    metadata,text,tool=_evidence(candidate)
    output.mkdir(parents=True,exist_ok=False)
    claims=[
      ("A_BAYESIAN_PROBABILISTIC","SUPPORTED","FORMALISM_FACT","Abstract and Bayes-factor sections explicitly present a Bayesian probabilistic formalism."),
      ("B_SAME_SOURCE_VS_SEPARATE_SOURCE","SUPPORTED","FORMALISM_FACT","H models one common source location; K models separate source locations."),
      ("C_SYMMETRY","SUPPORTED","FORMALISM_FACT","The sources criticize order-dependent pairwise matching and require symmetry across catalogs/observations."),
      ("D_POSITIONAL_UNCERTAINTY_MODEL","SUPPORTED","FORMALISM_FACT","The likelihood accepts general astrometric PDFs and develops a spherical-normal case."),
      ("E_KNOWN_POSITIONAL_UNCERTAINTIES","SUPPORTED","FORMALISM_FACT","The method consumes quoted precision/PDF information; the arXiv abstract names known circular position errors."),
      ("F_CIRCULAR_GAUSSIAN_SPHERICAL_APPROXIMATIONS","SUPPORTED","FORMALISM_FACT","The proceeding states spherical-normal, large-weight/small-separation approximations and an anisotropic covariance extension."),
      ("G_PRIORS","SUPPORTED","FORMALISM_FACT","Posterior probabilities require P(H); catalog counts, coverage and selection functions enter the prior."),
      ("H_POINT_SOURCE_ASSUMPTION","SUPPORTED","FORMALISM_FACT","Both captured abstracts explicitly scope the method to astronomical point sources."),
      ("I_OPTIONAL_PHYSICAL_PROPERTIES","SUPPORTED","FORMALISM_FACT","Colors, redshift and luminosity may augment spatial evidence."),
      ("J_EXTENDED_DR9_GALAXY_TRANSFER_LIMIT","INCONCLUSIVE","PROJECT_SUITABILITY_INFERENCE","The primary evidence is point-source scoped and does not validate transfer to extended DR9 galaxy centroids; seeing, resolution, deblending, segmentation, fitting, morphology and observer domain remain unresolved."),
      ("K_NO_ARBITRARY_MATCH_DECISION_RADIUS_REQUIREMENT","SUPPORTED","FORMALISM_FACT","The scientific evidence is a Bayes factor/posterior with priors; practical radius thresholds generate candidates from a final target threshold and are not themselves a universal same-object rule."),
    ]
    rows=[{"claim_id":a,"decision":b,"epistemic_layer":c,"evidence":d} for a,b,c,d in claims]
    claim9="SUPPORTED"; claim10="SUPPORTED"
    matrix=sealed({"claim_order":["CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS","BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD"],
      "claims":[{"claim_id":"CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS","decision":claim9,
        "epistemic_layer":"FORMALISM_FACT","reason":"A-I and K are established by captured primary evidence; the point-source scope and unresolved extended-galaxy transfer are retained explicitly."},
       {"claim_id":"BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD","decision":claim10,
        "epistemic_layer":"PROJECT_SUITABILITY_INFERENCE","reason":"A future descriptive pilot can measure candidate topology without declaring same-object identity; search support remains distinct from a scientific decision threshold."}],
      "extended_source_transfer":"NOT_DEMONSTRATED","formalism_subclaims":rows,
      "schema_version":"OC3_CROSS_ID_FORMALISM_RECOVERY_CLAIM_MATRIX_001",
      "search_bound_selected":False,"scientific_threshold_selected":False})
    write_json_immutable(output/"CLAIM_MATRIX.json",matrix)
    report=f'''# Cross-ID Formalism Recovery Offline Review\n\n## Decisions\n\n- `CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS`: `{claim9}`.\n- `BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD`: `{claim10}`.\n\nThe captured primary evidence establishes a Bayesian comparison of a common-source hypothesis against separate-source hypotheses, with explicit positional likelihoods, priors, spherical-normal approximations, optional physical properties, and symmetric multi-catalog intent. It is explicitly scoped to point sources. Direct transfer to extended DR9 galaxy centroids is not demonstrated and remains a project-suitability limitation.\n\nA practical maximum search radius is described as candidate-generation support derived from a target posterior/evidence threshold. It is not promoted to a universal scientific same-object radius. This review selects neither a search bound nor a match-decision threshold.\n\nA future bounded descriptive DR9 metadata pilot is prospectively specifiable because it can measure separation distributions, multiplicity and uncertainty availability without declaring equivalence. This mission does not authorize or execute that pilot.\n\nPDF extraction tool: `{tool}`. Network, source rows, matching, morphology, Panel V3 and P1 were zero.\n'''
    (output/"REVIEW_REPORT.md").write_text(report)
    counters={"network_requests_started":0,"retry_requests":0,"PHOTSYS_reads":0,"TYPE_values_read":0,
      "DCHISQ_values_read":0,"Sersic_shape_values_read":0,"photometric_values_read":0,"photoz_values_read":0,
      "source_rows_read":0,"image_pixels_read":0,"morphology_accesses":0,"label_accesses":0,
      "model_operations":0,"training_operations":0,"embedding_operations":0,"clustering_operations":0,
      "panel_v3_operations":0,"p1_operations":0}
    terminal=sealed({"application_body_bytes_read":0,"claim_9_decision":claim9,"claim_10_decision":claim10,
      "counters":counters,"scope":candidate["scope"],"stage_id":candidate["stage_id"],
      "state":"OFFLINE_SEMANTIC_REVIEW_COMPLETED","terminal_recommendation":"CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE"})
    write_json_immutable(output/"TERMINAL.json",terminal); return terminal

def main(argv=None):
    args=parser().parse_args(argv)
    try:
      candidate=validate_candidate(args.candidate)
      if args.validate_candidate:
        print(json.dumps({"network_requests":0,"source_rows":0,"state":"READY_AT_OFFLINE_SEMANTIC_REVIEW_BOUNDARY"},sort_keys=True)); return 0
      if None in (args.permit,args.standing_authorization,args.autonomy_state,args.output_directory):
        raise OfflineReviewValidationError("GOVERNED_ARGUMENTS_REQUIRED")
      validate_runtime_invocation(candidate,executable=sys.executable,script_path=sys.argv[0],argument_vector=sys.argv[1:])
      from oc3lib.cross_id_formalism_recovery_governor import consume_permit,validate_permit
      validate_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
        standing_authorization_path=args.standing_authorization)
      consume_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
        standing_authorization_path=args.standing_authorization,consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"))
      print(json.dumps(_review(candidate,args.output_directory),sort_keys=True)); return 0
    except Exception as exc:
      print(json.dumps({"error":getattr(exc,"code",str(exc)),"network_requests":0,"source_rows":0,
        "state":"OFFLINE_SEMANTIC_REVIEW_BLOCKED"},sort_keys=True),file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
