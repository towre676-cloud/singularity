#!/usr/bin/env python3
import argparse,json,sys
from fractions import Fraction as Q
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.symmetry_channels import *
from singularity.thermal_diagnostics import build_plate_candidates,simulate_protocol,AffineCandidate

def encode(x):
    if isinstance(x,Q):return [x.numerator,x.denominator]
    if isinstance(x,(tuple,list)):return [encode(v) for v in x]
    if isinstance(x,dict):return {k:encode(v) for k,v in x.items()}
    return x

def run():
    P=((0,1),(1,0));A=((Q(1,2),Q(1,4)),(Q(1,4),Q(1,2)));Ps=reflection_channels(P)
    assert verify_channel_decomposition(Ps,(A,),(P,))
    # Exact C3 regular representation over Q. Its 2D augmentation channel
    # splits into conjugate 1D channels only after a complex field extension.
    mats=tuple(tuple(tuple(Q(j==(i+g)%3) for j in range(3)) for i in range(3)) for g in range(3))
    rep=FiniteRepresentation(('e','g','g2'),tuple(tuple((a+b)%3 for b in range(3)) for a in range(3)),mats)
    trivial=tuple((Q(1,3),)*3 for _ in range(3));augment=tuple(tuple(Q(i==j)-Q(1,3) for j in range(3)) for i in range(3))
    assert verify_channel_decomposition((trivial,augment),mats,rep.matrices)
    channel=channel_observability(mats,((1,0,0),),(trivial,augment));assert channel['channel_ranks']==(1,2)
    left,right=build_plate_candidates()[4:];reflection=tuple((i//12)*12+11-i%12 for i in range(144))
    assert conjugate_permutation_blindness(left,right,reflection,(0,1))
    checks=0
    for T in range(13):
        for word in ((1,)*T,tuple((-1)**t for t in range(T))):
            for s in (0,1):assert simulate_protocol(left,word,s)==simulate_protocol(right,word,s);checks+=1
    local=(1,)+(0,)*143
    def local_read(candidate):
        custom=AffineCandidate(candidate.identifier,candidate.dimension,candidate.entries,candidate.heater,(local,))
        return simulate_protocol(custom,(1,1),0)
    ys=lambda s,T:tuple(simulate_protocol(c,(1,)*T,s) for c in (left,right))
    options=(RepairOption('center_mean_T2',1,ys(1,2),(Q(1,1000),)*2,(1,1),'existing center mean'),
             RepairOption('corner_mean_T2',1,ys(0,2),(Q(1,1000),)*2,(1,1),'existing corner mean'),
             RepairOption('asymmetric_far_corner_T2',1,tuple(local_read(c) for c in (left,right)),(Q(1,1000),)*2,(1,1),'installed top-left point sensor'),
             RepairOption('left_center_T2',3,ys(2,2),(Q(1,1000),)*2,(1,1),'existing left-center mean'),
             RepairOption('left_center_T3',4,ys(2,3),(Q(1,1000),)*2,(1,1,1),'existing left-center mean'))
    repair=minimum_channel_repair((left.identifier,right.identifier),('left','right'),options)
    assert repair['cost']==3 and repair['panel']==('left_center_T2',)
    assert options[2].readings[0]==options[2].readings[1]
    return encode({'schema':'singularity.symmetry-channels/1','coefficient_field':'Q',
        'reflection_projectors':Ps,'two_state_channel':channel_observability((A,),((Q(1,2),Q(1,2)),),Ps),
        'finite_group':{'group':'C3','representation':'rational regular','projector_ranks':[1,2],'closure':channel,
                        'field_convention':'augmentation irreducible over Q, two conjugate 1D irreps over C'},
        'thermal':{'candidate_ids':(left.identifier,right.identifier),'zero_initial':True,'same_input':True,
            'permutation':reflection,'invariant_sensor_indices':(0,1),'conjugate_identities_verified':True,
            'finite_direct_checks':checks,'all_time_reason':'A_b P=P A_a; B_b=P B_a; C_b P=C_a',
            'repair':repair,'catalogue':tuple({'id':o.identifier,'cost':o.cost,'readings':o.readings,'errors':o.errors,
                                             'word':o.word,'sensor':o.physical_sensor} for o in options),
            'insufficient_repair':'asymmetric_far_corner_T2 breaks reflection but gives identical readings',
            'error_contract':'independent absolute intervals on original sensor readings; no basis ball transport'}})

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();data=run();path=ROOT/'results/symmetry_channels.json'
    if a.check:assert json.loads(path.read_text())==data;print('symmetry channels: rational groups, thermal blindness and costed repair passed')
    else:path.write_text(json.dumps(data,indent=2)+'\n');print('wrote',path)
if __name__=='__main__':main()
