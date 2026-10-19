#!/usr/bin/env python3
import argparse,json,sys,hashlib
from fractions import Fraction as Q
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.prefix_certificates import *
from singularity.heights import local_coefficients

def enc(x):
    if isinstance(x,Q):return [x.numerator,x.denominator]
    if isinstance(x,dict):return {str(k):enc(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [enc(v) for v in x]
    return x

def run():
    params=(Q(0),Q(1,5),Q(1,3),Q(1,2),Q(2,3),Q(4,5),Q(1));checks=0;comparisons=0;retained=[]
    for isolates in range(4):
        graph=Graph(2+isolates,((0,1),));hist=local_coefficients(graph,10)
        for q in params:
            a=IdealClosurePrefixCertificate(q,isolates);oracle=tuple(sum((c*q**e for e,c in h.items()),Q()) for h in hist)
            assert a.coefficients(10)==oracle;checks+=11
            assert parse_certificate(certificate_to_dict(a))==a
            for eta in params:
                b=IdealClosurePrefixCertificate(eta,isolates);result=compare_prefix(a,b);comparisons+=1
                assert result['equal']==(q==eta)
                for r,(u,v) in enumerate(zip(a.coefficients(10),b.coefficients(10))):
                    assert u-v==2*(q-eta)*ideal_difference_quotient(r,q,eta,isolates)
            retained.append({'isolates':isolates,'q':q,'stratum':a.exceptional_stratum,'coefficient1':oracle[1],
                             'coefficient10':oracle[10],'cutoff':1})
    binomial_params=(Q(-2),Q(-1,2),Q(0),Q(1,3),Q(1),Q(2));recurrences=0
    for a in binomial_params:
        for b in binomial_params:
            A=RecurrencePrefixCertificate(a);B=RecurrencePrefixCertificate(b)
            difference=tuple(u-v for u,v in zip(A.coefficients(20),B.coefficients(20)))
            for n in range(19):assert sum(c*y for c,y in zip(comparison_recurrence(a,b,n),difference[n:n+3]))==0;recurrences+=1
    rejected=[]
    for name,data in (('delayed_b_x^100',{'samples':[0]*100}),('temporary_ideal_stabilization',{'ideals':['a-a_prime']*100}),('guessed_recurrence',{'recurrence':[1,-1]})):
        try:verify_certificate(data)
        except ValueError:rejected.append(name)
    assert len(rejected)==3
    source=ROOT/'src/singularity/prefix_certificates.py'
    return enc({'schema':'singularity.effective-prefix/1','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'new_graph_theorem':{'family':'one q-weighted edge plus k known isolates, same k in comparison','parameter_domain':'rational 0<=q<=1; theorem algebraic in q and eta',
                  'cutoff':1,'generator':'f1(q)-f1(eta)=2(q-eta)','all_coefficient_witness':'q^m-eta^m=(q-eta) sum(q^(m-1-i)*eta^i)',
                  'nonperiodic':'0<q<1; B=1+2 sum(q^(d*d)*x^d) entire nonpolynomial, hence L is nonrational',
                  'exceptional_strata':{'q0':'L=1/((1-x)^k*(1-x^2))','q1':'L=(1-x)^(-k-2)'},
                  'original_coefficients_checked':checks,'parameter_comparisons':comparisons,'census':retained},
                'recurrence_theorem':{'family':'formal binomial ODE (1-x)F_prime=aF; supplemental family, not an arbitrary graph series',
                    'comparison_recurrence':'(n+1)(n+2)y[n+2]-(n+1)(2n+a+b+1)y[n+1]+(n+a)(n+b)y[n]=0',
                    'leading_term':'(n+1)(n+2)>0 for all integer n>=0, no singular index','cutoff':1,
                    'parameters':binomial_params,'identities_checked':recurrences},
                'baselines':'combined finite-state Cayley-Hamilton and existing periodic palindromic cutoff preserve original scope',
                'false_stopping_rules_rejected':rejected,
                'denominator_domain':'canonical reduced rational pairs with positive denominator; denominators 0 rejected before construction',
                'resource_limits':'finite-state dimension and coefficient bit growth are caller-declared; corpus R=10, n<=5; exact refusal is not inequivalence'})

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();data=run();path=ROOT/'results/effective_prefix.json'
    if a.check:assert json.loads(path.read_text())==data;print('effective prefix: new nonperiodic graph theorem, common recurrence and exceptional strata passed')
    else:path.write_text(json.dumps(data,indent=2)+'\n');print('wrote',path)
if __name__=='__main__':main()
