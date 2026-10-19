#!/usr/bin/env python3
"""Standalone NX36 source/decision replay, without proposal/search compilers."""
from fractions import Fraction as Q
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.decision_certificates import verify_decision_certificate


def exact(v):
    if type(v)is int:return Q(v)
    if type(v)is not list or len(v)!=2 or any(type(x)is not int for x in v)or v[1]<=0:
        raise ValueError('canonical exact pair required')
    q=Q(*v)
    if [q.numerator,q.denominator]!=v:raise ValueError('unreduced exact pair')
    return q


def check(path=ROOT/'results/nx36/nx36_acceptance.json'):
    data=json.loads(Path(path).read_text());source=data['thermal_source'];cert=data['thermal_certificate'];problem=cert['problem']
    digest=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
    if problem['semantics']['source_bindings']!=[digest]:raise ValueError('source reconstruction digest mismatch')
    models=source['models'];protocols=source['protocols']
    if [m['identifier']for m in models]!=problem['candidate_ids']:raise ValueError('lost original candidate identities')
    # Direct scalar sparse stepping. No AffineCandidate/protocol compiler,
    # optimizer, proposal routine or reduction engine is imported.
    for e,(word,sensor)in enumerate(protocols):
        word=tuple(map(exact,word))
        for c,model in enumerate(models):
            n=model['dimension'];state=[Q(0)]*n
            for amplitude in word:
                updated=[exact(v)*amplitude for v in model['heater']]
                for i,j,value in model['entries']:updated[i]+=exact(value)*state[j]
                state=updated
            value=sum((exact(a)*b for a,b in zip(model['sensors'][sensor],state)),Q(0))
            lower,upper=map(exact,problem['intervals'][e][c])
            if (lower,upper)!=(value-Q(1,100000),value+Q(1,100000)):
                raise ValueError('source/readout/reset interval mismatch')
    if not verify_decision_certificate(cert,problem):raise ValueError('decision certificate failed')
    return {'candidates':len(models),'experiments':len(protocols),'selected_panel':cert['selected_panel'],
            'selected_cost':cert['selected_cost'],'source_reconstruction':True,'decision_replay':True,
            'scope':'three declared original hypotheses; exactly two reset protocols; physical radius1/100000 premise'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt',nargs='?',type=Path,default=ROOT/'results/nx36/nx36_acceptance.json')
    args=parser.parse_args()
    print(json.dumps(check(args.receipt),sort_keys=True))
