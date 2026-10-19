#!/usr/bin/env python3
import argparse,json,sys
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.population_geometry import *
from singularity.fault_population import FaultPopulation
from singularity.integer_quotients import integer_image_certificate,bounded_fibre_population

def enc(x):
    if isinstance(x,Q):return [x.numerator,x.denominator]
    if isinstance(x,dict):return {str(k):enc(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [enc(v) for v in x]
    return x

def run():
    binary=WeightedPopulation(tuple(PopulationObject(str(bits),(sum(bits),),bits[0]) for bits in product((0,1),repeat=2)))
    moments=tilted_moments(binary,(2,));assert moments['normalization']==9 and moments['mean']==(Q(4,3),)
    # Source-backed original fault masks, with an explicitly synthetic prior.
    faults=FaultPopulation(('left0','left1','right0','right1'),max_faults=2)
    masks=tuple(faults.unrank(i) for i in range(faults.count()))
    weighted=WeightedPopulation(tuple(PopulationObject('mask:'+''.join(map(str,m)),(sum(m),),m[0],Q(2)**(-sum(m))) for m in masks),
                                'FaultPopulation four original bonds, Boolean masks with sum<=2')
    assert sum(pushforward_mass(weighted).values())==sum(o.weight for o in weighted.objects)
    channels=tuple(FiniteObservationChannel(f'inspect_bond{j}',(0,1),tuple((o.identifier,tuple(int(y==m[j]) for y in (0,1))) for o,m in zip(weighted.objects,masks)),j+1) for j in range(4))
    choice=minimum_expected_target_risk(weighted,channels,2)
    assert choice['risk']==0 and choice['panel']==('inspect_bond0',)
    for i,m in enumerate(masks):assert faults.rank(m)==i and weighted.rank(weighted.unrank(i).identifier)==i
    # NX19 fibres retain their original-coordinate multiplicities.
    lattice=integer_image_certificate(((2,2),));fibre=bounded_fibre_population(lattice,(4,),((0,2),(0,2)))
    vectors=tuple(fibre.unrank(i) for i in range(fibre.count()))
    fibre_pop=WeightedPopulation(tuple(PopulationObject(str(v),(sum(v),),v[0]) for v in vectors))
    assert pushforward_mass(fibre_pop)=={(2,):3}
    # Same one-experiment budget: Bayes and worst-original-object objectives differ.
    decision=WeightedPopulation((PopulationObject('a',(0,),'a',9),PopulationObject('b',(1,),'b',9),PopulationObject('c',(2,),'c',2)))
    majority=FiniteObservationChannel('majority',(0,1),(('a',(1,0)),('b',(0,1)),('c',(1,0))))
    balanced=FiniteObservationChannel('balanced',('a','b','c'),tuple((o.identifier,tuple(Q(17,20) if t==o.target else Q(3,40) for t in ('a','b','c'))) for o in decision.objects))
    bayes=minimum_expected_target_risk(decision,(majority,balanced),1)
    minimax={c.identifier:deterministic_minimax_risk(decision,c) for c in (majority,balanced)}
    assert bayes['panel']==('majority',) and bayes['risk']==Q(1,10) and minimax['balanced']['risk']==Q(3,20)
    posterior=posterior_target(decision,balanced,'c')
    return enc({'schema':'singularity.population-geometry/1','binary':{'mass_table':pushforward_mass(binary),'joint_target_table':joint_target_mass(binary),'tilt2':moments},
                'fault_population':{'original_masks':masks,'count':faults.count(),'completion_states':faults.completion_states,
                    'original_mass':sum((o.weight for o in weighted.objects),Q()),'feature_mass':pushforward_mass(weighted),'target_mass':joint_target_mass(weighted),
                    'prior':'synthetic weight 2^(-number_of_faults); no empirical calibration','design':choice,
                    'channel_scope':'synthetic direct single-bond inspections; independently reset, exact readings, declared accounting costs'},
                'integer_fibre':{'original_vectors':vectors,'feature_mass':pushforward_mass(fibre_pop),'target_mass':joint_target_mass(fibre_pop)},
                'decision_disagreement':{'prior':[Q(9,20),Q(9,20),Q(1,10)],'bayes':bayes,'deterministic_minimax':minimax,'posterior_example':posterior},
                'separation':'Bayes uses original weights and zero-one target loss; minimax uses worst original state with deterministic decision rules',
                'zero_observation':'UnsupportedObservation rejects zero-probability observations rather than normalizing zero mass'})

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();data=run();path=ROOT/'results/population_geometry.json'
    if a.check:assert json.loads(path.read_text())==data;print('population geometry: original masks/fibres, exact posteriors and design passed')
    else:path.write_text(json.dumps(data,indent=2)+'\n');print('wrote',path)
if __name__=='__main__':main()
