"""Exact modular polynomial-coefficient recurrence orbits and reusable hit domains.

A state includes the index phase. Singular denominators terminate deterministic
transport and return the exact next-value congruence, never a spurious cycle.
"""
from math import gcd
from fractions import Fraction
import json
from .residue_cover import integer_polynomial
from .semilinear_domains import count_domain,select,contains
from .divisor_square import WorkLimit


def _eval(f,n,m):
    v=0
    for c in reversed(f):v=(c+n*v)%m
    return v


def next_congruence(q,rhs,m):
    g=gcd(q,m)
    if rhs%g:return {'status':'IMPOSSIBLE','base':None,'step':None,'count':0}
    step=m//g;base=((rhs//g)*pow(q//g,-1,step))%step if step>1 else 0
    return {'status':'EXACT','base':base,'step':step,'count':g}


def recurrence_orbit(P,Q,modulus,seed,*,step_limit=100000):
    P=list(integer_polynomial(P));Q=list(integer_polynomial(Q))
    if type(modulus) is not int or not 2<=modulus<=65536 or type(seed) is not int or abs(seed).bit_length()>16384:
        raise ValueError('modulus in [2,65536] and bounded integer seed required')
    if type(step_limit) is not int or step_limit<1:raise ValueError('positive state budget required')
    states=[];seen={};value=seed%modulus;n=0
    base={'schema':'pp-recurrence-orbit/1','P':P,'Q':Q,'modulus':modulus,'seed':seed,
          'execution_verified':False}
    while (n%modulus,value) not in seen:
        if len(states)>=step_limit:raise WorkLimit('recurrence state budget exhausted before closure')
        seen[(n%modulus,value)]=n;states.append([n%modulus,value])
        p=_eval(P,n%modulus,modulus);q=_eval(Q,n%modulus,modulus);rhs=p*value%modulus
        if gcd(q,modulus)!=1:
            return {**base,'status':'SINGULAR','complete':False,'states':states,'prefix_length':len(states),
                    'cycle_start':None,'period':None,'singular_index':n,
                    'next_values':next_congruence(q,rhs,modulus),
                    'scope':'exact deterministic prefix through singular_index; next-value congruence only'}
        value=rhs*pow(q,-1,modulus)%modulus;n+=1
    start=seen[(n%modulus,value)]
    return {**base,'status':'PERIODIC','complete':True,'states':states,'prefix_length':start,
            'cycle_start':start,'period':n-start,'singular_index':None,'next_values':None,
            'scope':'all nonnegative integer indices'}


def verify_orbit(result,*,step_limit=100000):
    try:return recurrence_orbit(result['P'],result['Q'],result['modulus'],result['seed'],step_limit=step_limit)==result
    except (ValueError,TypeError,KeyError,ArithmeticError,WorkLimit):return False


def orbit_value(orbit,n):
    if type(n) is not int or n<0 or n.bit_length()>16384:raise ValueError('bounded nonnegative index required')
    if n>=len(orbit['states']):
        if not orbit['complete']:raise ValueError('index beyond deterministic prefix')
        n=orbit['cycle_start']+(n-orbit['cycle_start'])%orbit['period']
    return orbit['states'][n][1]


def orbit_domain(orbit,*,residues=None,power=None):
    m=orbit['modulus']
    if (residues is None)==(power is None):raise ValueError('supply either residue set or power exponent')
    if power is not None:
        if type(power) is not int or not 2<=power<=64:raise ValueError('power exponent in [2,64] required')
        accepted=sorted({pow(v,power,m) for v in range(m)})
    else:
        if not isinstance(residues,(list,tuple)) or any(type(v) is not int or not 0<=v<m for v in residues):raise ValueError('normalized residue list required')
        accepted=sorted(set(residues))
    allowed=set(accepted);cells=[];start=orbit['cycle_start'] if orbit['complete'] else len(orbit['states'])
    for i in range(start):
        if orbit['states'][i][1] in allowed:cells.append({'interval':[i,i],'modulus':1,'residues':[0]})
    tail=[]
    if orbit['complete']:
        tail=sorted(i%orbit['period'] for i in range(start,len(orbit['states'])) if orbit['states'][i][1] in allowed)
        if tail:cells.append({'interval':[start,None],'modulus':orbit['period'],'residues':tail})
    return {'schema':'pp-recurrence-hit-domain/1','orbit':orbit,'accepted_residues':accepted,
            'power_exponent':power,'cells':cells,'complete':orbit['complete'],'execution_verified':False,
            'nonnegative_density':str(Fraction(len(tail),orbit['period'])) if orbit['complete'] else None,
            'scope':orbit['scope']}


def verify_orbit_domain(domain,*,step_limit=100000):
    try:
        if not verify_orbit(domain['orbit'],step_limit=step_limit):return False
        rebuilt=orbit_domain(domain['orbit'],residues=domain['accepted_residues']) if domain['power_exponent'] is None else orbit_domain(domain['orbit'],power=domain['power_exponent'])
        return all(json.dumps(domain[k],sort_keys=True)==json.dumps(v,sort_keys=True) for k,v in rebuilt.items())
    except (ValueError,TypeError,KeyError,ArithmeticError):return False


def orbit_count(domain,lo,hi):
    if type(lo) is not int or type(hi) is not int or lo<0 or max(lo.bit_length(),abs(hi).bit_length())>16384:raise ValueError('bounded nonnegative lower index and integer upper index required')
    if not domain['complete'] and hi>=len(domain['orbit']['states']):raise ValueError('query exceeds deterministic prefix')
    return count_domain(domain,lo,hi)


def orbit_select(domain,rank,*,start=0):
    if not domain['complete']:raise ValueError('global rank selection requires a closed orbit')
    if type(start) is not int or start<0:raise ValueError('nonnegative starting index required')
    return select(domain,rank,start=start)


def orbit_optimize(domain,objective,*,sense='min',node_limit=100000,work_limit=1000000):
    """Global polynomial index optimization over a closed recurrence hit set."""
    from . import polyalg as A
    from .semilinear_domains import _optimizer_data
    from .sturm_fibres import root_certificate
    if not domain['complete'] or not verify_orbit_domain(domain):raise ValueError('closed replayable hit domain required')
    if sense not in ('min','max'):raise ValueError('min or max required')
    if any(type(v) is not int or v<1 for v in (node_limit,work_limit)):raise ValueError('positive budgets required')
    original=integer_polynomial(objective);f=original if sense=='min' else tuple(-c for c in original)
    certificates=[];used=0
    if domain['cells'] and len(f)>1:
        for m in sorted({c['modulus'] for c in domain['cells']}):
            if used>=node_limit:raise WorkLimit('shared recurrence-optimization root budget exceeded')
            diff=integer_polynomial(int(v) for v in A.subtract(A.compose_linear(A.poly(f),m,1),A.poly(f)))
            cert=root_certificate(diff,node_limit=node_limit-used);used+=cert['nodes_checked']
            certificates.append({'modulus':m,'certificate':cert})
    data=_optimizer_data(domain,f,certificates,work_limit)
    if sense=='max' and data['value'] is not None:
        data['value']=-data['value'];data['candidates']=[(n,-v) for n,v in data['candidates']]
    return {'schema':'pp-recurrence-optimum/1','domain':domain,'objective':list(original),'sense':sense,
            'difference_certificates':certificates,'root_nodes':used,'complete':True,'execution_verified':False,**data}


def verify_orbit_optimum(result,*,node_limit=100000,work_limit=1000000):
    try:
        rebuilt=orbit_optimize(result['domain'],result['objective'],sense=result['sense'],node_limit=node_limit,work_limit=work_limit)
        return json.dumps(rebuilt,sort_keys=True)==json.dumps(result,sort_keys=True)
    except (ValueError,TypeError,KeyError,ArithmeticError,WorkLimit):return False
