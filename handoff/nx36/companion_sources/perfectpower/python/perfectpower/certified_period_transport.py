"""Rational complex Taylor transport with a proved Cauchy/Gronwall tail bound.

Disks are certified pole-free by denominator lower bounds. Conservative bounds
can reject a safe path; there is no floating point error estimate in a receipt.
"""
from fractions import Fraction as Q
from math import comb
from .rational_functions import RationalFunction as RF
from .differential_modules import DifferentialModule


class Gaussian:
    def __init__(self,a=0,b=0):self.a,self.b=Q(a),Q(b)
    @classmethod
    def parse(cls,v):
        if isinstance(v,cls):return v
        if isinstance(v,(list,tuple)) and len(v)==2:return cls(*v)
        return cls(v)
    def __bool__(self):return bool(self.a or self.b)
    def __add__(self,v):v=self.parse(v);return Gaussian(self.a+v.a,self.b+v.b)
    __radd__=__add__
    def __neg__(self):return Gaussian(-self.a,-self.b)
    def __sub__(self,v):return self+-self.parse(v)
    def __mul__(self,v):v=self.parse(v);return Gaussian(self.a*v.a-self.b*v.b,self.a*v.b+self.b*v.a)
    __rmul__=__mul__
    def __truediv__(self,v):
        v=self.parse(v);norm=v.a*v.a+v.b*v.b
        if not norm:raise ZeroDivisionError('complex zero')
        return self*Gaussian(v.a/norm,-v.b/norm)
    def __rtruediv__(self,v):return self.parse(v)/self
    def __pow__(self,k):
        out=Gaussian(1)
        for _ in range(k):out=out*self
        return out
    def norm(self):return abs(self.a)+abs(self.b)
    def packet(self):return [str(self.a),str(self.b)]


def centered(p,c):return [sum((p[j]*c**(j-k)*comb(j,k) for j in range(k,len(p))),Gaussian()) for k in range(len(p))]
def jets(r,c,n):
    a,b=centered(r.n,c),centered(r.d,c)
    if not b[0]:raise ValueError('path hits a connection pole')
    out=[]
    for k in range(n):out.append(((a[k] if k<len(a) else Gaussian())-sum((b[j]*out[k-j] for j in range(1,min(k,len(b)-1)+1)),Gaussian()))/b[0])
    return out
def multiply(a,b):return [[sum((v*w for v,w in zip(row,col)),Gaussian()) for col in zip(*b)] for row in a]
def rownorm(a):return max(sum(v.norm() for v in row) for row in a)
def exp_upper(x):
    n=max(1,2*(x.numerator//x.denominator+1));return (1-x/n)**(-n)


def certified_transport(matrix,path,order=18,step_limit=128,rounding_bits=None):
    module=DifferentialModule({'matrix':matrix});n=module.dimension
    if n>6 or type(order) is not int or not 4<=order<=40 or type(step_limit) is not int or not 1<=step_limit<=256:raise ValueError('dimension at most 6, order 4 through 40, bounded steps required')
    if not isinstance(path,list) or not 2<=len(path)<=65:raise ValueError('2 through 65 rational complex vertices required')
    if rounding_bits is not None and (type(rounding_bits) is not int or not 16<=rounding_bits<=4096):raise ValueError('rounding precision 16 through 4096 bits required')
    path=list(map(Gaussian.parse,path));a=module.connection
    total=[[Gaussian(i==j) for j in range(n)] for i in range(n)];error=Q(0);receipts=[]
    for target in path[1:]:
        c=path[0] if not receipts else Gaussian.parse(receipts[-1]['end'])
        while (target-c).norm():
            h=target-c
            while True:
                radius=4*h.norm();bounds=[];valid=True
                for row in a:
                    brow=[]
                    for r in row:
                        denominator=centered(r.d,c);lower=max(abs(denominator[0].a),abs(denominator[0].b))-sum(v.norm()*radius**j for j,v in enumerate(denominator) if j)
                        if lower<=0:valid=False;break
                        numerator=centered(r.n,c);upper=sum(v.norm()*radius**j for j,v in enumerate(numerator));brow.append(upper/lower)
                    if not valid:break
                    bounds.append(sum(brow))
                # A bounded exponential also avoids giant, uninformative
                # Cauchy estimates near poles in the rounded long-path mode.
                if valid and (rounding_bits is None or max(bounds)*radius<=1):break
                h=h/2
                if h.norm()<Q(1,10**12):raise ValueError('no certified ordinary disk at this path point')
            if len(receipts)>=step_limit:raise ValueError('certified transport step budget exhausted')
            M=max(bounds);aj=[[jets(r,c,order) for r in row] for row in a]
            series=[[[Gaussian(i==j) for j in range(n)] for i in range(n)]]
            for k in range(order):
                terms=[multiply([[aj[i][j][r] for j in range(n)] for i in range(n)],series[k-r]) for r in range(k+1)]
                series.append([[sum((v[i][j] for v in terms),Gaussian())/(k+1) for j in range(n)] for i in range(n)])
            step=[[sum((series[k][i][j]*h**k for k in range(order+1)),Gaussian()) for j in range(n)] for i in range(n)]
            rho=h.norm()/radius;tail=n*exp_upper(M*radius)*rho**(order+1)/(1-rho)
            error=rownorm(step)*error+tail*rownorm(total)+tail*error
            total=multiply(step,total)
            if rounding_bits is not None:
                # Centre rounding has <=2*n/scale row error; round the error
                # upward too, so neither centres nor bounds accumulate huge
                # denominators across hundreds of continuation steps.
                scale=1<<rounding_bits
                total=[[Gaussian(Q(v.a.numerator*scale//v.a.denominator,scale),
                                 Q(v.b.numerator*scale//v.b.denominator,scale)) for v in row] for row in total]
                error+=Q(2*n,scale)
                error=Q(-(-error.numerator*scale//error.denominator),scale)
            if any(max(abs(v.a.numerator).bit_length(),v.a.denominator.bit_length(),abs(v.b.numerator).bit_length(),v.b.denominator.bit_length())>100000 for row in total for v in row):raise ValueError('transport coefficient bit budget exhausted')
            receipts.append(dict(start=c.packet(),end=(c+h).packet(),radius=str(radius),connection_row_bound=str(M),step_row_error_bound=str(tail),order=order));c=c+h
    result=dict(schema='pp-certified-complex-transport/1',matrix=[[v.packet() for v in row] for row in total],row_error_bound=str(error),steps=receipts,
        certified=True,tail_argument='On the pole-free radius-R disk ||S||<=exp(MR); Cauchy tail <= dimension*exp(MR)*rho^(N+1)/(1-rho). All modulus estimates and arithmetic are rational upper bounds.',
        scope='ordinary analytic continuation along this polygon; fundamental matrix starts at identity; singular endpoints and automatic integer monodromy recognition are excluded')
    if rounding_bits is not None:result['rounding_bits']=rounding_bits
    return result


def legendre_marked_periods(path,order=18,seed_terms=48,rounding_bits=None,step_limit=128):
    if type(seed_terms) is not int or not 8<=seed_terms<=256:raise ValueError('seed terms 8 through 256 required')
    if not path or Gaussian.parse(path[0]).packet()!=Gaussian(Q(1,2)).packet():raise ValueError('marked Legendre seed requires initial parameter 1/2')
    t=RF([0,1]);z=t.coerce(0);one=t.coerce(1);a=[[z,one],[1/(4*t*(1-t)),(2*t-1)/(t*(1-t))]]
    receipt=certified_transport([[v.packet() for v in row] for row in a],path,order,step_limit,rounding_bits)
    N=seed_terms;q=Q(1,2);F=sum(Q(comb(2*k,k)**2,16**k)*q**k for k in range(N+1));dF=sum(Q(comb(2*k,k)**2,16**k)*k*q**(k-1) for k in range(1,N+1))
    ef=q**(N+1)/(1-q);ed=q**N*((N+1)-N*q)/(1-q)**2
    seed=[[Gaussian(F),Gaussian(0,F)],[Gaussian(dF),Gaussian(0,-dF)]]
    center=[[Gaussian.parse(v) for v in row] for row in receipt['matrix']];product=multiply(center,seed)
    et=Q(receipt['row_error_bound']);seed_error=2*max(ef,ed);error=rownorm(center)*seed_error+et*rownorm(seed)+et*seed_error
    return dict(schema='pp-certified-marked-legendre-periods/1',period_state=[[v.packet() for v in row] for row in product],row_error_bound=str(error),transport=receipt,
        normalization='periods of dx/y divided by 2*pi; columns a,b; intersection a.b=1; seed columns [F(t),Fprime(t)] and [i F(1-t),-i Fprime(1-t)], F=2 K(t)/pi',
        seed_terms=N,seed_bounds=[str(ef),str(ed)],seed_certified=True,
        scope='standard marked Legendre cycles and their analytic continuation; no identification with unrelated mesh or finite Hodge objects')
