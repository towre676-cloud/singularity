#!/usr/bin/env python3
"""Reproduce trained score tables from the shipped, source-bound feature cache.

This is deterministic model reproduction, separate from independent optimum replay.
For raw extraction use run_hydraulic.py with the SHA256-pinned official archive.
"""
import argparse, importlib.util, json, tempfile
from pathlib import Path
import numpy as np

def main():
    ap=argparse.ArgumentParser();ap.add_argument('study',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
    here=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('hydraulic_runner',here/'run_hydraulic.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    X=np.load(a.study/'features.npz')['features'];d=np.load(a.study/'split.npz');y=d['labels'];part=d['split'];ref=np.load(a.study/'selection_table.npz');test=np.load(a.study/'test_evidence.npz')
    with tempfile.TemporaryDirectory() as tmp:
        scores,models,classes=m.fit_scores(X,y,part,Path(tmp))
    for t in range(4):
        assert np.array_equal(scores[t],ref[f'scores_{t}']),('selection',t)
        ts=np.stack([np.log(np.maximum(models[t][s].predict_proba(X[part==2,s]),1e-6)) for s in range(14)])
        assert np.array_equal(ts,test[f'scores_{t}']),('test',t)
    r={'status':'PASS','training_models_reproduced':56,'selection_and_test_score_tables_bit_identical':True,'source_feature_cache_sha256':m.digest(a.study/'features.npz'),'scope':'Deterministic training replay in recorded software environment; not an independent classifier implementation or fresh experiment.'}
    if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
