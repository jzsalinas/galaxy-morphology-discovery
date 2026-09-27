#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from oc3lib.cross_observer_grouping import load_canonical_json
from oc3lib.manual_source_metadata_acquisition import run_manual_acquisition

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-acquisition",action="store_true")
    parser.add_argument("--binding",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if not args.run_acquisition: parser.error("--run-acquisition is required")
    try:
        return run_manual_acquisition(binding=load_canonical_json(args.binding),binding_path=args.binding,root=args.output)
    except (ValueError,FileExistsError) as exc:
        print(json.dumps({"state":"MANUAL_ACQUISITION_LOCAL_INTEGRITY_STOP","error":str(exc)},sort_keys=True),file=sys.stderr)
        return 22

if __name__=="__main__": raise SystemExit(main())
