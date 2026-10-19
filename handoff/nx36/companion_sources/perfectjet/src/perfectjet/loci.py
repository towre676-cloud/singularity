"""Exact rank loci of matrices depending polynomially on one parameter.

For A(t) with entries in Q[t], the generic rank r is the rank over Q(t). The
drop locus {t : rank A(t) < r} is the zero set of the gcd of the r-by-r minors.
It is computed without enumerating minors: one nonzero r-minor M0 bounds the
locus, and elimination over Q[t]/(squarefree M0) splits the modulus whenever a
pivot is a zero divisor. Each returned factor carries the rank that holds at
every one of its roots.
"""
from fractions import Fraction as Q
from math import isqrt
from .exact import rank

# Univariate polynomials are coefficient lists, lowest degree first, no trailing zeros.


def trim(p):
    p=[Q(x) for x in p]
    while p and p[-1]==0:p.pop()
    return p


def degree(p):return len(trim(p))-1


def padd(a,b):
    n=max(len(a),len(b))
    return trim([(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(n)])


def pneg(a):return [-x for x in a]


def pmul(a,b):
    if not a or not b:return []
    out=[Q(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return trim(out)


def pdivmod(a,b):
    a,b=trim(a),trim(b)
    if not b:raise ZeroDivisionError("polynomial division by zero")
    q=[Q(0)]*max(len(a)-len(b)+1,1)
    while len(a)>=len(b) and a:
        c=a[-1]/b[-1];k=len(a)-len(b);q[k]=c
        a=trim([x-(c*b[i-k] if 0<=i-k<len(b) else 0) for i,x in enumerate(a)])
    return trim(q),a


def monic(p):
    p=trim(p)
    return [x/p[-1] for x in p] if p else []


def pgcd(a,b):
    a,b=trim(a),trim(b)
    while b:a,b=b,pdivmod(a,b)[1]
    return monic(a)


def derivative(p):return trim([i*x for i,x in enumerate(p)][1:])


def squarefree(p):
    p=trim(p)
    if degree(p)<1:return [Q(1)]
    return monic(pdivmod(p,pgcd(p,derivative(p)))[0])


def evaluate(p,x):
    out=Q(0)
    for c in reversed(p):out=out*x+c
    return out


def interpolate(xs,ys):
    """Newton interpolation through distinct rational nodes."""
    xs=[Q(x) for x in xs];coef=[Q(y) for y in ys];n=len(xs)
    for j in range(1,n):
        for i in range(n-1,j-1,-1):coef[i]=(coef[i]-coef[i-1])/(xs[i]-xs[i-j])
    p=[]
    for i in range(n-1,-1,-1):
        p=padd(pmul(p,[-xs[i],Q(1)]),[coef[i]])
    return p


def polynomial_matrix(fn,max_degree):
    """Recover A(t) from evaluations when every entry has degree <= max_degree."""
    xs=list(range(max_degree+1));samples=[fn(Q(x)) for x in xs]
    m=len(samples[0]);n=len(samples[0][0]) if m else 0
    return [[interpolate(xs,[s[i][j] for s in samples]) for j in range(n)] for i in range(m)]


def _evaluate_matrix(a,x):return [[evaluate(p,x) for p in row] for row in a]


def _det(a):
    a=[list(r) for r in a];n=len(a);d=Q(1)
    for c in range(n):
        p=next((i for i in range(c,n) if a[i][c]),None)
        if p is None:return Q(0)
        if p!=c:a[c],a[p]=a[p],a[c];d=-d
        d*=a[c][c]
        for i in range(c+1,n):
            z=a[i][c]/a[c][c];a[i]=[x-z*y for x,y in zip(a[i],a[c])]
    return d


def generic_rank(a):
    """Rank over Q(t). A nonzero r-minor has degree <= r*deg, so that many+1 nodes suffice."""
    a=[[trim(p) for p in row] for row in a]
    if not a or not a[0]:return 0,Q(0)
    d=max((degree(p) for row in a for p in row),default=0);d=max(d,0)
    bound=min(len(a),len(a[0]))*d
    best=(-1,Q(0))
    for x in range(bound+1):
        r=rank(_evaluate_matrix(a,Q(x)))
        if r>best[0]:best=(r,Q(x))
    return best


def _independent(rows):
    chosen=[]
    for i,row in enumerate(rows):
        if rank([rows[j] for j in chosen]+[row])>len(chosen):chosen.append(i)
    return chosen


def _mod(p,q):return pdivmod(p,q)[1]


def _inverse_mod(a,q):
    """Inverse of a modulo q, or the nontrivial gcd when a is a zero divisor."""
    r0,r1,s0,s1=trim(q),_mod(a,q),[],[Q(1)]
    while r1:
        quo,rem=pdivmod(r0,r1)
        r0,r1,s0,s1=r1,rem,s1,padd(s0,pneg(pmul(quo,s1)))
    if degree(r0)>0:return None,monic(r0)
    return _mod([x/r0[0] for x in s0],q),None


def _rank_mod(a,q):
    """[(factor,rank)] with factors multiplying to squarefree q and rank constant on each factor's roots."""
    work=[[_mod(p,q) for p in row] for row in a]
    m=len(work);n=len(work[0]) if m else 0;row=0
    for col in range(n):
        if row==m:break
        piv=next((i for i in range(row,m) if work[i][col]),None)
        if piv is None:continue
        inv,g=_inverse_mod(work[piv][col],q)
        if g is not None:
            other=monic(pdivmod(q,g)[0])
            return _rank_mod(a,g)+_rank_mod(a,other)
        work[row],work[piv]=work[piv],work[row]
        work[row]=[_mod(pmul(x,inv),q) for x in work[row]]
        for i in range(row+1,m):
            if work[i][col]:
                z=work[i][col]
                work[i]=[_mod(padd(x,pneg(pmul(z,y))),q) for x,y in zip(work[i],work[row])]
        row+=1
    return [(monic(q),row)]


def rational_roots(p):
    """All rational roots of p, by the rational root theorem on the cleared integer form."""
    from math import lcm
    p=trim(p)
    if not p:raise ValueError("zero polynomial")
    roots=[]
    while p and p[0]==0:
        if Q(0) not in roots:roots.append(Q(0))
        p=p[1:]
    if len(p)<2:return roots
    den=lcm(*(x.denominator for x in p));ints=[int(x*den) for x in p]
    if max(abs(ints[0]),abs(ints[-1]))>10**8:
        return sorted(roots+_isolated_rational_roots(ints))
    for cand in sorted({Q(s*u,v) for u in _divisors(ints[0]) for v in _divisors(ints[-1]) for s in (1,-1)}):
        if evaluate(p,cand)==0:roots.append(cand)
    return sorted(roots)


def _sturm_changes(seq,x):
    signs=[s for s in ((evaluate(p,x)>0)-(evaluate(p,x)<0) for p in seq) if s]
    return sum(1 for u,v in zip(signs,signs[1:]) if u!=v)


def _simplest_between(lo,hi):
    """Smallest-denominator rational in the closed interval [lo,hi] (Stern-Brocot descent)."""
    from math import floor
    fl=floor(lo)
    if fl==lo:return Q(fl)
    if fl+1<=hi:return Q(fl+1)
    rest=_simplest_between(1/(hi-fl),1/(lo-fl))
    return fl+1/rest


def _isolated_rational_roots(ints):
    """Rational roots when the rational-root-theorem candidate set is too large to enumerate.

    A root p/q has q dividing the leading coefficient D, so distinct candidates are at
    least 1/D^2 apart. Sturm bisection isolates each real root of the squarefree part in
    an interval narrower than that; the simplest rational in the interval is then the
    only possible rational root there, and it is tested exactly.
    """
    p=squarefree(ints);lead=abs(ints[-1])
    seq=[p,derivative(p)]
    while degree(seq[-1])>0:
        r=pneg(pdivmod(seq[-2],seq[-1])[1])
        if not r:break
        seq.append(r)
    bound=1+max(abs(c/p[-1]) for c in p[:-1]) if len(p)>1 else Q(1)
    width=Q(1,2*lead*lead);out=[];stack=[(-bound,bound)]
    while stack:
        lo,hi=stack.pop()
        count=_sturm_changes(seq,lo)-_sturm_changes(seq,hi)
        if count==0:continue
        if hi-lo<width:
            cand=_simplest_between(lo,hi)
            if evaluate(p,cand)==0 and cand not in out:out.append(cand)
            if evaluate(p,hi)==0 and hi not in out:out.append(hi)
            continue
        mid=(lo+hi)/2
        if evaluate(p,mid)==0:
            if mid not in out:out.append(mid)
            stack+=[(lo,mid-width/4),(mid+width/4,hi)]
        else:stack+=[(lo,mid),(mid,hi)]
    return [r for r in out if r!=0]


def _divisors(n):
    n=abs(n);small=[d for d in range(1,isqrt(n)+1) if n%d==0]
    return sorted(set(small+[n//d for d in small]))


def rank_locus(a):
    """Generic rank, locus factors where the rank drops, and rational drop points with replayed ranks."""
    a=[[trim(p) for p in row] for row in a]
    r,x0=generic_rank(a)
    if r==0:return {"generic_rank":0,"locus":[Q(1)],"factors":[],"rational_points":[]}
    sample=_evaluate_matrix(a,x0);rows=_independent(sample)
    cols=_independent([list(c) for c in zip(*[sample[i] for i in rows])])
    d=max(degree(p) for row in a for p in row)
    nodes=list(range(r*max(d,0)+1))
    minor=interpolate(nodes,[_det([[evaluate(a[i][j],Q(x)) for j in cols] for i in rows]) for x in nodes])
    assert minor,"selected minor vanishes identically"
    pieces=_rank_mod(a,squarefree(minor)) if degree(minor)>0 else []
    drops=[(f,k) for f,k in pieces if k<r]
    locus=[Q(1)]
    for f,_ in drops:locus=pmul(locus,f)
    points=[]
    for f,k in drops:
        for root in rational_roots(f):
            replay=rank(_evaluate_matrix(a,root))
            assert replay==k
            points.append({"t":root,"rank":replay})
    return {"generic_rank":r,"locus":monic(locus),"factors":[{"factor":f,"rank":k} for f,k in drops],
            "rational_points":sorted(points,key=lambda p:p["t"])}


def partner_loci(degrees=range(3,13)):
    """Parameter values of the C3 sextic family where the correction kernel or active quotient jumps."""
    from .transvectants import c3_family,gate_matrix
    out=[]
    for n in degrees:
        gates=polynomial_matrix(lambda t:gate_matrix(c3_family(t)[0],n,3)+gate_matrix(c3_family(t)[0],n,5),1)
        joint=polynomial_matrix(lambda t:gate_matrix(c3_family(t)[0],n,3)+gate_matrix(c3_family(t)[0],n,5)
                                +gate_matrix(c3_family(t)[0],n,1),1)
        g,j=rank_locus(gates),rank_locus(joint)
        out.append({"degree":n,"correction_rank":g["generic_rank"],"joint_rank":j["generic_rank"],
                    "generic_active_dimension":j["generic_rank"]-g["generic_rank"],
                    "correction_locus":g["locus"],"correction_points":g["rational_points"],
                    "joint_locus":j["locus"],"joint_points":j["rational_points"]})
    return out
