"""Resource-bounded polynomial observation-module certificates (NX14).

A receipt carries both directions of every module equality. Replay checks
polynomial identities and all maximal minors, without invoking Hermite form.
"""
from fractions import Fraction
from itertools import combinations
from math import comb
from time import monotonic
from . import parametric as p


def _enc(f):return [[c.numerator,c.denominator] for c in f]
def _dec(v):
    if not isinstance(v,list):raise ValueError('polynomial coefficient list required')
    out=[]
    for z in v:
        if not isinstance(z,list) or len(z)!=2 or any(isinstance(t,bool) or not isinstance(t,int) for t in z) or z[1]<=0:raise ValueError('canonical rational pair required')
        c=Fraction(*z)
        if [c.numerator,c.denominator]!=z:raise ValueError('noncanonical rational')
        out.append(c)
    if out and not out[-1]:raise ValueError('trailing zero polynomial coefficient')
    return tuple(out)
def _em(M):return [[_enc(f) for f in r] for r in M]
def _dm(M):return tuple(tuple(_dec(f) for f in r) for r in M)
def _pmul(A,B,n=None):
    cols=n if n is not None else (len(B[0]) if B else 0)
    return tuple(tuple(sum_poly(p._mul(a,B[k][j]) for k,a in enumerate(r)) for j in range(cols)) for r in A)
def sum_poly(fs):
    z=()
    for f in fs:z=p._add(z,f)
    return z

def _hnf_witness(rows,n,check):
    N=len(rows);rs=[list(r) for r in rows];cs=[[p._poly(int(i==j)) for j in range(N)] for i in range(N)];pr=0
    for c in range(n):
        while True:
            nz=[i for i in range(pr,len(rs)) if rs[i][c]]
            if not nz:break
            i0=min(nz,key=lambda i:(len(rs[i][c]),i));rs[pr],rs[i0]=rs[i0],rs[pr];cs[pr],cs[i0]=cs[i0],cs[pr]
            piv=rs[pr][c];clean=True
            for i in range(pr+1,len(rs)):
                if rs[i][c]:
                    q,rem=p._divmod(rs[i][c],piv)
                    rs[i]=[p._sub(a,p._mul(q,b)) for a,b in zip(rs[i],rs[pr])]
                    cs[i]=[p._sub(a,p._mul(q,b)) for a,b in zip(cs[i],cs[pr])];clean=clean and not rem;check(rs+cs)
            if clean:break
        if pr<len(rs) and rs[pr][c]:
            z=1/rs[pr][c][-1];rs[pr]=[p._scale(a,z) for a in rs[pr]];cs[pr]=[p._scale(a,z) for a in cs[pr]]
            for i in range(pr):
                q=p._divmod(rs[i][c],rs[pr][c])[0] if rs[i][c] else ()
                rs[i]=[p._sub(a,p._mul(q,b)) for a,b in zip(rs[i],rs[pr])];cs[i]=[p._sub(a,p._mul(q,b)) for a,b in zip(cs[i],cs[pr])]
            pr+=1;check(rs+cs)
    return tuple(tuple(r) for r in rs[:pr]),tuple(tuple(r) for r in cs[:pr])

def _coordinates(row,basis):
    rest=list(row);out=[]
    for b in basis:
        col=next(i for i,f in enumerate(b) if f);q,rem=p._divmod(rest[col],b[col])
        if rem:raise ArithmeticError('non-polynomial module coordinate')
        out.append(q);rest=[p._sub(a,p._mul(q,z)) for a,z in zip(rest,b)]
    if any(rest):raise ArithmeticError('row not in generated module')
    return tuple(out)



def _domain_exception(root,a,b,h,basis,max_refinements=10000):
    """Refine an isolated algebraic root against rational domain boundaries.

    Factor sharing excludes denominator poles algebraically, independently
    of whether a floating or rational representative happens to hit a pole.
    """
    if 'rational' in root:
        z=root['rational']
        return {'rational':[z.numerator,z.denominator],'rank':p.rank_at_rational(basis,z)} if a<z<b and p._eval(h,z) else None
    g=p._poly(root['factor'])
    if p._deg(p._gcd(g,h))>0:return None
    lo,hi=root['interval']
    for _ in range(max_refinements):
        if hi<=a or lo>=b:return None
        if a<lo and hi<b:
            return {'interval':[[lo.numerator,lo.denominator],[hi.numerator,hi.denominator]],'factor':_enc(g),'rank':p.rank_at_algebraic(basis,p._to_dict(g))}
        mid=(lo+hi)/2
        if p.count_roots(p._to_dict(g),lo,mid):hi=mid
        else:lo=mid
    raise ArithmeticError('algebraic root/domain refinement budget exhausted')


def parameter_module_receipt(system,domain=(Fraction(0),Fraction(1)),limits=None,*,denominator=None):
    if not isinstance(system,p.PolynomialOperatorSystem):raise TypeError('polynomial operator system required')
    defaults={'max_dimension':12,'max_degree':100,'max_coefficient_bits':10000,'max_steps':20,'max_minors':10000,'seconds':10}
    if limits is not None and (not isinstance(limits,dict) or set(limits)-set(defaults)):raise ValueError('unknown resource limit')
    limits=dict(defaults,**(limits or {}))
    if isinstance(limits['seconds'],bool) or not isinstance(limits['seconds'],(int,Fraction)) or limits['seconds']<=0:raise ValueError('positive exact wall-clock allowance required')
    for k in ('max_dimension','max_degree','max_coefficient_bits','max_steps','max_minors'):
        if isinstance(limits[k],bool) or not isinstance(limits[k],int) or limits[k]<0:raise ValueError('nonnegative integer limits required')
    if len(domain)!=2 or any(isinstance(x,bool) or not isinstance(x,(int,Fraction)) for x in domain):raise TypeError('two exact rational domain endpoints required')
    a,b=map(Fraction,domain)
    if not a<b:raise ValueError('increasing rational domain required')
    h=p._poly(denominator if denominator is not None else 1)
    if not h:raise ValueError('identically zero denominator')
    n=system.dimension;start=monotonic();peakdeg=-1;peakbits=0;steps=0
    receipt={'schema':'singularity.parameter-module/1','state':'budget_refusal','dimension':n,'domain':[[a.numerator,a.denominator],[b.numerator,b.denominator]],
             'excluded_denominator':_enc(h),'operators':[_em(M) for M in system.operators],'observations':_em(system.observations),'limits':limits}
    def check(rows):
        nonlocal peakdeg,peakbits
        peakdeg=max(peakdeg,max((len(f)-1 for r in rows for f in r),default=-1))
        peakbits=max(peakbits,max((max(abs(c.numerator).bit_length(),c.denominator.bit_length()) for r in rows for f in r for c in f),default=0))
        if peakdeg>limits['max_degree']:raise ArithmeticError('polynomial degree limit')
        if peakbits>limits['max_coefficient_bits']:raise ArithmeticError('coefficient bit limit')
        if monotonic()-start>limits['seconds']:raise ArithmeticError('wall-time limit')
    try:
        if n>limits['max_dimension']:raise ArithmeticError('dimension preflight limit')
        check(list(system.observations)+[r for M in system.operators for r in M]);chain=[];prev=None
        for step in range(limits['max_steps']+1):
            inputs=tuple(system.observations)+(tuple(p._row_times(r,M,n) for M in system.operators for r in prev) if prev is not None else ())
            basis,fwd=_hnf_witness(inputs,n,check);steps=step+1;back=tuple(_coordinates(r,basis) for r in inputs)
            chain.append({'basis':_em(basis),'forward':_em(fwd),'reverse':_em(back)})
            if prev is not None and basis==prev:break
            prev=basis
        else:raise ArithmeticError('module step limit')
        r=len(basis)
        if comb(n,r)>limits['max_minors']:raise ArithmeticError('maximal-minor enumeration limit')
        minors=[p._det(tuple(tuple(row[j] for j in J) for row in basis)) for J in combinations(range(n),r)] if r else [(Fraction(1),)]
        divisor=()
        for f in minors:divisor=p._gcd(divisor,f)
        lead,factors=p.factor_over_q(p._to_dict(divisor));check(basis)
        complete=all(c['method']!='not certified irreducible' for _,_,c in factors)
        roots=p.real_roots(p._to_dict(divisor),'real') if complete else []
        exceptions=[]
        for root in roots:
            record=_domain_exception(root,a,b,h,basis)
            if record is not None:exceptions.append(record)
        receipt.update({'state':'complete' if complete else 'module_complete_factor_partial','chain':chain,'generic_rank':r,
                'divisor':_enc(divisor),'factors':[{'factor':_enc(p._poly(g)),'multiplicity':i,'evidence':c['method']} for g,i,c in factors],
                'exceptions':exceptions,'basis_words_are_not_module_rows':True,
                'atlas':{'regular_cells':'domain minus exact divisor roots and denominator zeros','regular_rank':r,'exception_points':exceptions,
                         'module_basis':_em(basis),'interpretation':'polynomial combinations of real experiments; actual witness words retained by generic_closure on each cell'}})
        # Actual legal experiment word basis, independently specialized on
        # each rational cell witness; complete rank strata derive from D_r.
        rational_points=sorted({a,b,*[Fraction(*e['rational']) for e in exceptions if 'rational' in e],*[root['rational'] for root in p.real_roots(p._to_dict(h),'real') if 'rational' in root and a<root['rational']<b]})
        receipt['charts']=[]
        from .observability import observable_closure
        for lo,hi in zip(rational_points,rational_points[1:]):
            z=(lo+hi)/2
            if not p._eval(divisor,z) or not p._eval(h,z):continue
            c=observable_closure(system.specialize(z))
            words=[[e.observation,list(e.word)] for e in c.basis]
            word_rows=tuple(p.experiment_row(system,j,w) for j,w in words)
            J=next((J for J in combinations(range(n),r) if p._eval(p._det(tuple(tuple(row[j] for j in J) for row in word_rows)),z)),())
            minor=p._det(tuple(tuple(row[j] for j in J) for row in word_rows)) if r else (Fraction(1),)
            receipt['charts'].append({'cell':[[lo.numerator,lo.denominator],[hi.numerator,hi.denominator]],'sample':[z.numerator,z.denominator],
                                      'words':words,'columns':list(J),'determinant':_enc(minor),
                                      'scope':'actual experiment basis wherever this determinant and the denominator are nonzero'})
        chart_gcd=()
        for chart in receipt['charts']:chart_gcd=p._gcd(chart_gcd,_dec(chart['determinant']))
        receipt['atlas']['charts_cover_regular_locus']=(chart_gcd==divisor)
        receipt['atlas']['chart_divisor']=_enc(chart_gcd)
    except ArithmeticError as e:receipt['reason']=str(e)
    receipt['resources']={'maximum_degree':peakdeg,'maximum_coefficient_bits':peakbits,'module_steps':steps}
    if receipt['state']!='budget_refusal' and not replay_parameter_module_receipt(receipt):raise ArithmeticError('receipt self-replay failed')
    return receipt


def replay_parameter_module_receipt(receipt):
    """Verify module generation and closure by explicit polynomial identities.

    Refusals are scoped resource records, not mathematical rank certificates.
    """
    try:
        r=receipt
        if r['schema']!='singularity.parameter-module/1' or r['state'] not in ('complete','module_complete_factor_partial','budget_refusal'):return False
        if r['state']=='budget_refusal':return isinstance(r.get('reason'),str) and bool(r['reason'])
        n=r['dimension'];ops=tuple(_dm(M) for M in r['operators']);obs=_dm(r['observations']);prev=None
        if not r['chain']:return False
        for node in r['chain']:
            B=_dm(node['basis']);F=_dm(node['forward']);R=_dm(node['reverse'])
            inputs=obs+(tuple(p._row_times(row,M,n) for M in ops for row in prev) if prev is not None else ())
            if any(len(row)!=n for row in B) or _pmul(F,inputs,n)!=B or _pmul(R,B,n)!=inputs:return False
            prev=B
        B=prev
        if len(r['chain'])<2 or _dm(r['chain'][-2]['basis'])!=B:return False
        rank=len(B)
        if p.generic_rank([[p._to_dict(f) for f in row] for row in B])!=rank or rank!=r['generic_rank']:return False
        D=()
        for J in combinations(range(n),rank):D=p._gcd(D,p._det(tuple(tuple(row[j] for j in J) for row in B)))
        if not rank:D=(Fraction(1),)
        if D!=_dec(r['divisor']):return False
        f=(Fraction(1),)
        for fac in r['factors']:
            e=fac['multiplicity']
            if isinstance(e,bool) or not isinstance(e,int) or e<1:return False
            f=p._mul(f,p._pow(_dec(fac['factor']),e))
        if p._monic(f)!=D:return False
        system=p.PolynomialOperatorSystem(n,tuple(tuple(tuple(p._to_dict(f) for f in row) for row in M) for M in ops),tuple(tuple(p._to_dict(f) for f in row) for row in obs))
        chart_gcd=()
        for chart in r['charts']:
            W=tuple(p.experiment_row(system,j,w) for j,w in chart['words']);J=chart['columns']
            minor=p._det(tuple(tuple(row[j] for j in J) for row in W)) if rank else (Fraction(1),)
            if minor!=_dec(chart['determinant']):return False
            chart_gcd=p._gcd(chart_gcd,minor)
        if chart_gcd!=_dec(r['atlas']['chart_divisor']) or r['atlas']['charts_cover_regular_locus']!=(chart_gcd==D):return False
        expected=[];a,b=(Fraction(*v) for v in r['domain']);h=_dec(r['excluded_denominator'])
        lead,fac=p.factor_over_q(p._to_dict(D))
        if r['factors']!=[{'factor':_enc(p._poly(g)),'multiplicity':i,'evidence':c['method']} for g,i,c in fac]:return False
        factor_complete=all(c['method']!='not certified irreducible' for g,i,c in fac)
        if (r['state']=='complete')!=factor_complete:return False
        if factor_complete:
            for root in p.real_roots(p._to_dict(D),'real'):
                record=_domain_exception(root,a,b,h,B)
                if record is not None:expected.append(record)
        return expected==r['exceptions']
    except (TypeError,ValueError,KeyError,IndexError,ZeroDivisionError,StopIteration,ArithmeticError):return False


def guarded_specialization(receipt,q):
    """Numerator generators divided by one declared common denominator."""
    if not replay_parameter_module_receipt(receipt):raise ValueError('invalid receipt')
    if isinstance(q,bool) or not isinstance(q,(int,Fraction)):raise TypeError('exact rational parameter required')
    q=Fraction(q)
    a,b=(Fraction(*v) for v in receipt['domain'])
    if not a<q<b:raise ValueError('parameter outside declared open domain')
    h=p._eval(_dec(receipt['excluded_denominator']),q)
    if not h:raise ValueError('parameter excluded by denominator pole guard')
    from .observability import OperatorSystem
    ops=tuple(tuple(tuple(p._eval(f,q)/h for f in row) for row in _dm(M)) for M in receipt['operators'])
    obs=tuple(tuple(p._eval(f,q) for f in row) for row in _dm(receipt['observations']))
    return OperatorSystem(receipt['dimension'],ops,obs)
