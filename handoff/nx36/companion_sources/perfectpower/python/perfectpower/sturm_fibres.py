"""Budgeted, proof-carrying integer roots and complete divisor-value fibres.

Adapts the existing exact Sturm core to a reusable certificate interface.
Replay checks factorization, signed remainders and a complete subdivision tree.
It performs no trial division of polynomial constants or numerical root finding.
"""
from fractions import Fraction as Q
from math import isqrt
import json
from . import polyalg as P
from .core import evaluate
from .divisor_square import Budget,WorkLimit,signed_divisors
from .residue_cover import integer_polynomial as _integer_polynomial

def integer_polynomial(coefficients):
    """Sturm certificates admit degree 256; residue atlases keep their 64 cap."""
    return _integer_polynomial(coefficients,degree_limit=256)


def _same(a,b):
    return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)


def _rational(values):
    if any(type(v) not in (int,Q,str) for v in values):raise ValueError('exact coefficients required')
    return P.poly(Q(v) for v in values)


def _budget(limit):
    if type(limit) is not int or limit<1:raise ValueError('positive node budget required')


def root_certificate(coefficients,*,lo=None,hi=None,node_limit=100000):
    f=integer_polynomial(coefficients);_budget(node_limit)
    if f==(0,):raise ValueError('zero polynomial has infinitely many roots')
    for endpoint in (lo,hi):
        if endpoint is not None and type(endpoint) is not int:raise ValueError('integer interval required')
    if lo is not None and hi is not None and lo>hi:raise ValueError('ordered interval required')
    lead,parts=P.squarefree_decomposition(P.poly(f));squarefree=P.ONE
    for factor in parts.values():squarefree=P.mul(squarefree,factor)
    chain=P.sturm_chain(squarefree) if P.degree(squarefree)>0 else [tuple(map(int,squarefree))]
    chain=[integer_polynomial(p) for p in chain]
    bound=P.cauchy_bound(squarefree);left=-bound if lo is None else max(-bound,lo);right=bound if hi is None else min(bound,hi)
    nodes=[];roots=[];stack=[(left-1,right)] if left<=right else []
    while stack:
        a,b=stack.pop()
        if len(nodes)>=node_limit:raise WorkLimit('complete Sturm subdivision exceeds node budget; no partial root list')
        va=P._sign_changes(chain,a);vb=P._sign_changes(chain,b);count=va-vb
        nodes.append([a,b,va,vb])
        if count==0:continue
        if b-a==1:
            if evaluate(f,b)==0:roots.append(b)
        else:
            mid=(a+b)//2;stack.extend(((mid,b),(a,mid)))
    return {'coefficients':f,'domain':[lo,hi],'leading_coefficient':str(lead),
        'squarefree_factors':[[k,[str(c) for c in v]] for k,v in sorted(parts.items())],
        'squarefree':[str(c) for c in squarefree],'sturm_chain':chain,'root_bound':bound,'clipped_interval':[left,right],
        'nodes':nodes,'roots':sorted(roots),'nodes_checked':len(nodes),'complete':True,'execution_verified':False}


def verify_roots(receipt,*,node_limit=100000):
    """Replay supplied factorization/chain/tree without root discovery or gcd search."""
    try:
        _budget(node_limit)
        if receipt['complete'] is not True or receipt['execution_verified'] is not False:return False
        f=integer_polynomial(receipt['coefficients'])
        if f==(0,):return False
        leading=_rational([receipt['leading_coefficient']])[0];expanded=P.poly([leading]);sf=P.ONE;seen=set();total_degree=0
        for multiplicity,factor in receipt['squarefree_factors']:
            if type(multiplicity) is not int or not 1<=multiplicity<=256 or multiplicity in seen:return False
            seen.add(multiplicity);p=_rational(factor)
            if P.degree(p)<1 or P.lead(p)!=1:return False
            total_degree+=multiplicity*P.degree(p)
            if total_degree>len(f)-1:return False
            expanded=P.mul(expanded,P.power(p,multiplicity));sf=P.mul(sf,p)
        if expanded!=P.poly(f) or sf!=_rational(receipt['squarefree']):return False
        chain=[integer_polynomial(p) for p in receipt['sturm_chain']]
        expected=[P.integer_primitive(sf)]
        if P.degree(sf)>0:
            expected.append(P.integer_primitive(P.derivative(sf)))
            for p in chain[2:]:
                remainder=P.divmod_poly(P.poly(expected[-2]),P.poly(expected[-1]))[1]
                if P.is_zero(remainder):return False
                wanted=P.integer_primitive(P.scale(remainder,-1))
                if p!=wanted:return False
                expected.append(p)
            if len(expected[-1])!=1:return False
            if not P.is_zero(P.divmod_poly(P.poly(expected[-2]),P.poly(expected[-1]))[1]):return False
        if chain!=expected:return False
        bound=P.cauchy_bound(sf)
        if type(receipt['root_bound']) is not int or receipt['root_bound']!=bound:return False
        lo,hi=receipt['domain']
        if any(x is not None and type(x) is not int for x in (lo,hi)) or (lo is not None and hi is not None and lo>hi):return False
        left=-bound if lo is None else max(-bound,lo);right=bound if hi is None else min(bound,hi)
        if not _same(receipt['clipped_interval'],[left,right]):return False
        stack=[(left-1,right)] if left<=right else [];roots=[];nodes=receipt['nodes']
        if len(nodes)>node_limit or type(receipt['nodes_checked']) is not int or receipt['nodes_checked']!=len(nodes):return False
        for node in nodes:
            if len(node)!=4 or any(type(x) is not int for x in node) or not stack:return False
            a,b=stack.pop();va=P._sign_changes(chain,a);vb=P._sign_changes(chain,b)
            if node!=[a,b,va,vb]:return False
            if va-vb<0:return False
            if va==vb:continue
            if b-a==1:
                if evaluate(f,b)==0:roots.append(b)
            else:
                mid=(a+b)//2;stack.extend(((mid,b),(a,mid)))
        return not stack and _same(receipt['roots'],sorted(roots))
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,OverflowError):return False


def square_fibres(coefficients,k,*,work_limit=100000):
    f=integer_polynomial(coefficients)
    if len(f)<2 or type(k) is not int or k==0:raise ValueError('nonconstant polynomial and nonzero integer constant required')
    budget=Budget(work_limit);parameters=set()
    if isqrt(abs(k))>work_limit:raise WorkLimit('complete factor-pair coverage exceeds work budget')
    for u in signed_divisors(k,budget):
        v=k//u
        if (v-u)%2==0 and (v+u)%2==0:parameters.add(((v-u)//2,(v+u)//2))
    fibres=[];points=set()
    for value in sorted({p for p,y in parameters}):
        remaining=budget.limit-budget.used
        if remaining<1:raise WorkLimit('complete polynomial fibres exceed work budget')
        cert=root_certificate((f[0]-value,)+f[1:],node_limit=remaining);budget.used+=cert['nodes_checked']
        fibres.append({'value':value,'certificate':cert})
        for p,y in parameters:
            if p==value:points.update((x,y) for x in cert['roots'])
    return {'coefficients':f,'constant':k,'parameters':sorted(parameters),'fibres':fibres,'points':sorted(points),
        'work_used':budget.used,'complete':True,'execution_verified':False,'method':'factor pairs and certified Sturm fibres'}


def verify_square_fibres(receipt,*,work_limit=100000):
    try:
        f=integer_polynomial(receipt['coefficients']);k=receipt['constant'];budget=Budget(work_limit)
        if len(f)<2 or type(k) is not int or k==0 or receipt['complete'] is not True or receipt['execution_verified'] is not False:return False
        parameters=set()
        for u in signed_divisors(k,budget):
            v=k//u
            if (v-u)%2==0 and (v+u)%2==0:parameters.add(((v-u)//2,(v+u)//2))
        if not _same(sorted(parameters),receipt['parameters']):return False
        points=set();values=[]
        for fibre in receipt['fibres']:
            p=fibre['value'];cert=fibre['certificate']
            if type(p) is not int or integer_polynomial(cert['coefficients'])!=(f[0]-p,)+f[1:]:return False
            if not verify_roots(cert,node_limit=max(1,budget.limit-budget.used)):return False
            budget.used+=cert['nodes_checked']
            if budget.used>budget.limit:return False
            values.append(p)
            for value,y in parameters:
                if value==p:points.update((x,y) for x in cert['roots'])
        return values==sorted({p for p,y in parameters}) and _same(sorted(points),receipt['points']) and receipt['work_used']==budget.used
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError):return False
