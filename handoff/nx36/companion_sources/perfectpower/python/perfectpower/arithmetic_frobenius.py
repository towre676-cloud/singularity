"""Bounded exact Kedlaya reduction, finite-field checks and deformation jets.

Odd monic hyperelliptic models, prime field, p>degree. Exact Q reductions
avoid working-precision division ambiguities. Published pole-reduction loss
bounds certify the omitted binomial tail, not a stability heuristic.
"""
from fractions import Fraction as Q
from itertools import product as cartesian
from math import factorial
from . import polyalg as P
from .root_cluster_geometry import prime, valuation
from .exact_linear import multiply, identity, inverse
from .rational_functions import RationalFunction as RF


def modular(q,p,N=1):
    q=Q(q);mod=p**N
    if q.denominator%p==0:raise ValueError('nonintegral p-adic coefficient')
    return q.numerator*pow(q.denominator,-1,mod)%mod
def logp(n,p):
    v=0
    while n>=p:n//=p;v+=1
    return v
def xgcd(a,b):
    old,r=a,b;s,ns=P.ONE,P.ZERO;t,nt=P.ZERO,P.ONE
    while not P.is_zero(r):
        q,rem=P.divmod_poly(old,r);old,r=r,rem;s,ns=ns,P.add(s,P.scale(P.mul(q,ns),-1));t,nt=nt,P.add(t,P.scale(P.mul(q,nt),-1))
    return P.monic(old),P.scale(s,1/old[-1]),P.scale(t,1/old[-1])
def ppow(a,n):
    out=P.ONE
    for _ in range(n):out=P.mul(out,a)
    return out
def mm(a,b):return [[sum(v*w for v,w in zip(row,col)) for col in zip(*b)] for row in a]
def characteristic(a):
    n=len(a);out=[Q(1)];power=identity(n);traces=[]
    for k in range(1,n+1):
        power=multiply(power,a);traces.append(sum(power[i][i] for i in range(n)));out.append(-sum(out[k-j]*traces[j-1] for j in range(1,k+1))/k)
    return out


def _model(coefficients,p,cohomology=True):
    f=P.poly(map(Q,coefficients));m=len(f)-1
    if not prime(p) or not 3<=p<=19 or m not in (3,5,7) or (cohomology and p<=m) or f[-1]!=1:raise ValueError('monic odd degree 3,5,7 and prime <=19 required; cohomology additionally needs p>degree')
    fm=[modular(c,p) for c in f]
    # Finite-field Euclid; rational gcd alone would miss bad reduction.
    def trim(a):
        while len(a)>1 and not a[-1]:a.pop()
        return a
    a=fm[:];b=trim([(i*fm[i])%p for i in range(1,len(fm))])
    while any(b):
        r=a[:]
        while len(r)>=len(b) and any(r):
            factor=r[-1]*pow(b[-1],-1,p)%p;shift=len(r)-len(b)
            for i,v in enumerate(b):r[i+shift]=(r[i+shift]-factor*v)%p
            trim(r)
        a,b=b,r
    if len(a)!=1:raise ValueError('singular reduction at this prime')
    return f


def frobenius_matrix(coefficients,p,precision=2):
    f=_model(coefficients,p);m=len(f)-1;n=m-1
    if type(precision) is not int or not 1<=precision<=4:raise ValueError('precision 1 through 4 required')
    K=1;extra=logp(2*p*m+1,p)
    while K+1-logp(2*p*K+p,p)-extra<precision:K+=1
    dx=P.derivative(f);g,_,v=xgcd(f,dx)
    if g!=P.ONE:raise ValueError('smooth polynomial required')
    fp=tuple(f[i//p] if i%p==0 else Q(0) for i in range(p*m+1));delta=P.add(fp,P.scale(ppow(f,p),-1))
    if any(c and valuation(c,p)<1 for c in delta):raise AssertionError('Frobenius defect is not divisible by p')
    def reduce(h,r):
        for k in range(r,0,-1):
            b=P.divmod_poly(P.mul(h,v),f)[1];a=P.exact_div(P.add(h,P.scale(P.mul(b,dx),-1)),f)
            h=P.add(a,P.scale(P.derivative(b),Q(2,2*k-1)))
        while len(h)>n:
            k=len(h)-m;factor=h[-1]/(k+Q(m,2));monomial=P.poly([0]*k+[factor])
            exact=P.add(P.mul(P.derivative(monomial),f),P.scale(P.mul(monomial,dx),Q(1,2)))
            h=P.add(h,P.scale(exact,-1))
        return list(h)+[Q(0)]*(n-len(h))
    rows=[[Q(0)]*n for _ in range(n)];power=P.ONE;binomial=Q(1)
    for k in range(K):
        for i in range(n):
            h=P.scale(P.poly([0]*(p*(i+1)-1)+list(power)),p*binomial);c=reduce(h,p*k+(p-1)//2)
            rows[i]=[a+b for a,b in zip(rows[i],c)]
        power=P.mul(power,delta);binomial*=Q(-1-2*k,2*(k+1))
    residue=[[modular(v,p,precision) for v in row] for row in rows]
    char=[modular(v,p,precision) for v in characteristic(rows)]
    return dict(schema='pp-kedlaya-prime-field-frobenius/1',p=p,precision=precision,modulus=p**precision,matrix=residue,
      characteristic_residues=char,exact_truncated_matrix=[[str(v) for v in row] for row in rows],binomial_terms=K,
      tail_valuation_lower_bound=K+1-logp(2*p*K+p,p)-extra,precision_certified=True,
      precision_argument='Expand every numerator in powers of the monic f, with remainders of degree <=2g. Kedlaya Lemmas 2 and 3 bound negative and positive y-power reductions by floor(log_p(abs(y exponent))). For term k the loss is bounded conservatively by floor(log_p(2pk+p))+floor(log_p(2p deg(f)+1)), and the coefficient has valuation >=k+1. This lower bound is nondecreasing for k>=1.',
      scope='prime-field good reduction, odd monic models degree<p<=19, precision<=4; exact rational reduction, not an optimized arbitrary-field backend')


class FiniteField:
    def __init__(self,p,r):
        self.p,self.r=p,r;self.zero=(0,)*r;self.one=(1,)+(0,)*(r-1)
        if r==1:self.modulus=[0,1]
        else:
            # For degrees two/three, no base-field root is equivalent to
            # irreducibility. The genus guard never requests higher degrees.
            self.modulus=None
            for v in cartesian(range(p),repeat=r):
                if v[0] and all((sum(v[i]*x**i for i in range(r))+x**r)%p for x in range(p)):
                    self.modulus=list(v)+[1];break
            if self.modulus is None:raise AssertionError('irreducible polynomial search failed')
    def add(self,a,b):return tuple((x+y)%self.p for x,y in zip(a,b))
    def mul(self,a,b):
        r,p=self.r,self.p;c=[0]*(2*r-1)
        for i,x in enumerate(a):
            for j,y in enumerate(b):c[i+j]=(c[i+j]+x*y)%p
        for k in range(len(c)-1,r-1,-1):
            for i in range(r):c[k-r+i]=(c[k-r+i]-c[k]*self.modulus[i])%p
        return tuple(c[:r])


def zeta_by_counting(coefficients,p):
    f=_model(coefficients,p,cohomology=False);g=(len(f)-2)//2;counts=[];fields=[]
    for r in range(1,g+1):
        field=FiniteField(p,r);elements=list(cartesian(range(p),repeat=r));squares={}
        for y in elements:
            square=field.mul(y,y);squares[square]=squares.get(square,0)+1
        count=1
        for x in elements:
            value=field.zero
            for c in reversed(f):value=field.add(field.mul(value,x),(modular(c,p),)+(0,)*(r-1))
            count+=squares.get(value,0)
        counts.append(count);fields.append(field.modulus)
    traces=[p**r+1-counts[r-1] for r in range(1,g+1)];c=[Q(1)]
    for k in range(1,g+1):c.append(-sum(c[k-j]*traces[j-1] for j in range(1,k+1))/k)
    full=c+[Q(0)]*g
    for k in range(g):full[2*g-k]=p**(g-k)*c[k]
    if any(v.denominator!=1 for v in full):raise AssertionError('noninteger Weil polynomial')
    return dict(schema='pp-exact-hyperelliptic-zeta/1',p=p,genus=g,extension_counts=counts,extension_moduli=fields,
      weil_polynomial_high_to_low=list(map(int,full)),zeta_numerator_low_to_high=list(map(int,full)),
      scope='complete finite-field enumeration in degrees 1 through genus, Newton identities and the curve functional equation; not a large-prime scalable point counter')


def frobenius_deformation(coefficients,p,precision=2,order=6):
    from .superelliptic_families import SuperellipticFamily
    from .certified_period_transport import jets,Gaussian
    if not prime(p) or p<=2 or type(precision) is not int or not 1<=precision<=4 or type(order) is not int or not 1<=order<=12:raise ValueError('odd prime, precision 1 through 4 and deformation order 1 through 12 required')
    family=SuperellipticFamily({'coefficients':coefficients,'cover_degree':2});n=family.dimension
    a=family.connection
    for row in a:
        for v in row:
            if any(c and valuation(c,p)<0 for c in v.n+v.d) or not v.d[0] or valuation(v.d[0],p)!=0:raise ValueError('connection must be integral and analytic on the p-adic unit disk at zero')
    loss=valuation(Q(factorial(order)),p);base=frobenius_matrix([v.evaluate(0) for v in family.f],p,precision+loss)
    first=[[Q(v) for v in row] for row in base['exact_truncated_matrix']]
    aj=[[[jets(v,Gaussian(),order)[k].a for v in row] for row in a] for k in range(order)]
    bj=[[[Q(0)]*n for _ in range(n)] for _ in range(order)]
    for k in range(order):
        if k>=p-1 and (k-p+1)%p==0:bj[k]=[[p*v for v in row] for row in aj[(k-p+1)//p]]
    out=[first]
    for k in range(order):
        left=[mm(bj[j],out[k-j]) for j in range(k+1)];right=[mm(out[k-j],aj[j]) for j in range(k+1)]
        out.append([[sum(v[i][l] for v in left)-sum(v[i][l] for v in right) for l in range(n)] for i in range(n)])
        out[-1]=[[v/(k+1) for v in row] for row in out[-1]]
        if any((k+1)*out[-1][i][l]-sum(v[i][l] for v in left)+sum(v[i][l] for v in right) for i in range(n) for l in range(n)):raise AssertionError('Frobenius deformation recurrence replay failed')
    # Jet k is known with absolute precision at least base_N-v_p(k!).
    packets=[]
    for k,matrix in enumerate(out):
        scale=p**valuation(Q(factorial(k)),p)
        packets.append(dict(order=k,scale=scale,scaled_matrix=[[modular(scale*v,p,precision) for v in row] for row in matrix],absolute_precision=base['precision']-valuation(Q(factorial(k)),p)))
    return dict(schema='pp-horizontal-frobenius-deformation/1',p=p,precision=precision,base_frobenius=base,jets=packets,
      equation='Fprime=p t^(p-1) A(t^p) F-F A(t)',recurrence_checked=True,
      scope='formal Frobenius jets about the integral ordinary base point, with factorial precision loss; no evaluation across a nonconvergent parameter boundary')


def tower_frobenius(tower=None,p=7,precision=2,delta=1):
    """Transport three small Frobenius blocks through a verified actual cover."""
    from .curve_correspondences import genus_three_elliptic_tower
    verified=genus_three_elliptic_tower()
    if tower is not None and (not isinstance(tower,dict) or any(tower.get(k)!=verified[k] for k in ('maps','pullback','source','base_change'))):raise ValueError('tower receipt does not match the independently reconstructed geometric maps and pullbacks')
    tower=verified
    r=Q(delta);t=[[RF.parse(v).evaluate(r) for v in row] for row in tower['pullback']]
    ti=inverse(t);loss=max([0]+[-valuation(v,p) for row in t+list(ti) for v in row if v])
    if loss:raise ValueError('pullback and inverse must be p-integral for this specialization')
    blocks=[];zeta=[]
    for packet in tower['maps']:
        f=[RF.parse(v).evaluate(r) for v in packet['target_coefficients']]
        blocks.append(frobenius_matrix(f,p,precision));zeta.append(zeta_by_counting(f,p))
    block=[[Q(0)]*6 for _ in range(6)]
    for k,v in enumerate(blocks):
        for i,row in enumerate(v['exact_truncated_matrix']):
            for j,value in enumerate(row):block[2*k+i][2*k+j]=Q(value)
    matrix=multiply(multiply(ti,block),t)
    source=[RF.parse(v).evaluate(r) for v in tower['source']['polynomial']];counts=zeta_by_counting(source,p)
    expected=P.ONE
    for v in zeta:expected=P.mul(expected,P.poly(v['zeta_numerator_low_to_high']))
    if list(map(int,expected))!=counts['zeta_numerator_low_to_high']:raise AssertionError('tower factorization conflicts with independent finite-field counts')
    if [modular(v,p,precision) for v in characteristic(matrix)]!=[v%(p**precision) for v in counts['weil_polynomial_high_to_low']]:raise AssertionError('Frobenius matrix does not match independent counts')
    return dict(schema='pp-geometric-tower-frobenius/1',p=p,precision=precision,delta=str(r),matrix=[[modular(v,p,precision) for v in row] for row in matrix],
      elliptic_blocks=blocks,source_zeta=counts,factor_zetas=zeta,independent_counts_match=True,precision_certified=True,
      scope='good split specialization of the actual three-cover tower; six-dimensional Frobenius obtained from three two-dimensional computations via functorial pullback')
