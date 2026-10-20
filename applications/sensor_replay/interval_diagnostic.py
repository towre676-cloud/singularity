#!/usr/bin/env python3
"""Post-hoc conservative envelope diagnostic using Singularity's existing core.

Ranges enclose train+selection feature values. They are empirical boxes, not
physical noise bounds. Overlapping boxes do not prove physical indistinguishability.
"""
import argparse, hashlib, itertools, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from singularity.robust_coverage import coverage_problem, minimum_robust_panel, exhaustive_robust_panel
SENSORS=['PS1','PS2','PS3','PS4','PS5','PS6','EPS1','FS1','FS2','TS1','TS2','TS3','TS4','VS1']
TASKS=['cooler','valve','pump','accumulator']

def run(root):
    a=np.load(root/'features.npz');d=np.load(root/'split.npz');x=a['features'];y=d['labels'];use=d['split']!=2
    allrows=[[] for _ in SENSORS];labels=[];envelopes={}
    for t,task in enumerate(TASKS):
        values=np.unique(y[:,t]);bounds={}
        for v in values:
            z=x[use&(y[:,t]==v)];bounds[int(v)]=(z.min(0),z.max(0))
        envelopes[task]={str(v):{'min':bounds[int(v)][0].tolist(),'max':bounds[int(v)][1].tolist()} for v in values}
        for a,b in itertools.combinations(values,2):
            labels.append(f'{task}:{a}-vs-{b}')
            la,ua=bounds[int(a)];lb,ub=bounds[int(b)]
            for s in range(14):allrows[s].append(bool(np.any(ua[s]<lb[s]) or np.any(ub[s]<la[s])))
    costs=[100000+60*r for r in [100]*7+[10]*2+[1]*5]
    problem=coverage_problem(costs,allrows,SENSORS,labels)
    outcomes={}
    for requirement in [1,2]:
        fast=minimum_robust_panel(problem,requirement);oracle=exhaustive_robust_panel(problem,requirement)
        assert fast.feasible==oracle.feasible and fast.cost==oracle.cost
        outcomes[str(requirement)]={'feasible':fast.feasible,'panel':[SENSORS[s] for s in fast.panel] if fast.panel is not None else None,'cost':str(fast.cost),'uncovered_distinctions':[labels[p] for p in fast.deficient],'independent_enumeration_agrees':True}
    result={'schema':'singularity.sensor-envelope-diagnostic/1','status':'post-hoc supplementary diagnostic, not a new held-out experiment','rule':'A physical sensor separates a pair of component severity envelopes if at least one of its19 fixed features has strictly disjoint empirical train+selection min-max intervals. All nuisance conditions in train+selection are included. Test features are excluded.','source_features_sha256':hashlib.sha256((root/'features.npz').read_bytes()).hexdigest(),'separation_table':allrows,'sensor_labels':SENSORS,'distinctions':labels,'core_outcomes':outcomes,'envelopes':envelopes,'boundary':'Ranges enclose observed development data only. Product-box overlap is failure of this conservative certificate; it is not a proof of physical nonidentifiability. No Gaussian, independence or universal noise claim.'}
    (root/'interval_diagnostic.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(outcomes,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);run(ap.parse_args().root)
