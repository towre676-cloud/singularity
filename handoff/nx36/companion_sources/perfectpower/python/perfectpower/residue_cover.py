"""Complete local power-residue covers and exact finite progression scans.

Noncoprime moduli are supported. Empty cover is a global obstruction; a
nonempty cover is only a necessary condition. No p-adic lifting is presumed.
"""
from functools import lru_cache
import json
from heapq import merge
from math import lcm
from .core import integer_power_root
from .divisor_square import WorkLimit


def integer_polynomial(coefficients,*,degree_limit=64):
    f=tuple(coefficients)
    if type(degree_limit) is not int or not 1<=degree_limit<=256:raise ValueError('degree limit 1 through 256 required')
    if not f or len(f)>degree_limit+1 or any(type(c) is not int for c in f):raise ValueError('integer polynomial exceeds degree limit')
    while len(f)>1 and f[-1]==0:f=f[:-1]
    if any(abs(c).bit_length()>16384 for c in f):raise WorkLimit('coefficient bit budget exceeded')
    return f


def evaluate(f,x):
    value=0
    for c in reversed(f):value=value*x+c
    return value


@lru_cache(maxsize=8192)
def _local(coefficients,degree,modulus):
    powers={pow(y,degree,modulus) for y in range(modulus)}
    return tuple(r for r in range(modulus) if evaluate(coefficients,r)%modulus in powers)


def residue_cover(coefficients,degree,moduli=(16,9,5,7),*,period_limit=65536,work_limit=200000):
    f=integer_polynomial(coefficients);moduli=tuple(moduli)
    if type(degree) is not int or not 2<=degree<=64:raise ValueError('integer power in [2,64] required')
    if not moduli or any(type(m) is not int or not 2<=m<=4096 for m in moduli):raise ValueError('moduli must be integers in [2,4096]')
    if any(type(v) is not int or v<1 for v in (period_limit,work_limit)):raise ValueError('positive cover budgets required')
    period=1;allowed=(0,);tables=[];work=0
    for m in moduli:
        new_period=lcm(period,m)
        if new_period>period_limit:raise WorkLimit('residue period budget exceeded')
        work+=m+len(allowed)*(new_period//period)
        if work>work_limit:raise WorkLimit('complete residue cover exceeds work limit')
        local=_local(tuple(c%m for c in f),degree,m);accepted=set(local)
        allowed=tuple(sorted(r+t*period for r in allowed for t in range(new_period//period) if (r+t*period)%m in accepted))
        tables.append({'modulus':m,'allowed':local});period=new_period
        if not allowed:break
    return {'coefficients':f,'degree':degree,'tables':tables,'modulus':period,'allowed':allowed,
            'global_obstruction':not allowed,'table_work':work,'exact_replay':True,
            'execution_verified':False,'scope':'necessary local conditions; empty cover proves no integer points'}


def verify_cover(cover):
    if not isinstance(cover,dict):return False
    try:
        if cover.get('schema')=='pp-factored-cover/1':
            from .factored_sieve import verify_factored_cover
            return verify_factored_cover(cover)
        rebuilt=residue_cover(cover['coefficients'],cover['degree'],[t['modulus'] for t in cover['tables']])
        return all(json.dumps(rebuilt[k],sort_keys=True)==json.dumps(cover[k],sort_keys=True) for k in ('modulus','allowed','tables','global_obstruction'))
    except (ValueError,KeyError,TypeError,IndexError):return False


def candidate_count(cover,lo,hi):
    if cover.get('schema')=='pp-factored-cover/1':
        from .factored_sieve import factored_candidate_count
        return factored_candidate_count(cover,lo,hi)
    if type(lo) is not int or type(hi) is not int or hi<lo:raise ValueError('ordered closed integer interval required')
    m=cover['modulus']
    return sum((hi-r)//m-(lo-1-r)//m for r in cover['allowed'])


def scan_cover(cover,lo,hi,*,work_limit=100000):
    if cover.get('schema')=='pp-factored-cover/1':
        from .factored_sieve import scan_factored
        return scan_factored(cover,lo,hi,work_limit=work_limit)
    if type(work_limit) is not int or work_limit<1:raise ValueError('positive candidate budget required')
    if not verify_cover(cover):raise ValueError('invalid local residue cover')
    count=candidate_count(cover,lo,hi)
    if count>work_limit:raise WorkLimit('complete surviving candidate count exceeds budget; no partial list')
    m=cover['modulus'];ranges=[range(lo+(r-lo)%m,hi+1,m) for r in cover['allowed']]
    points=[]
    for x in merge(*ranges):
        root=integer_power_root(evaluate(cover['coefficients'],x),cover['degree'])
        if root is not None:
            points.extend((x,y) for y in sorted({root,-root} if cover['degree']%2==0 else {root}))
    return {'points':points,'interval':[lo,hi],'interval_size':hi-lo+1,'candidates_checked':count}
