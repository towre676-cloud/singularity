"""Valuation geometry and exact affine-periodic cyclotomic collision populations."""
from math import exp
from .rings import QuotientRing,cyclotomic


def valuations(n):
    if not isinstance(n,int) or n<1:
        raise ValueError("positive integer required")
    d,p={},2
    while p*p<=n:
        while n%p==0:
            d[p]=d.get(p,0)+1;n//=p
        p=3 if p==2 else p+2
    if n>1:d[n]=d.get(n,0)+1
    return d


def kappa(m,n):
    a,b=valuations(m),valuations(n)
    return sum(v*b.get(p,0) for p,v in a.items())


def valuation_rbf(m,n,beta=1.0):
    if beta<0:raise ValueError("nonnegative beta required")
    a,b=valuations(m),valuations(n)
    return exp(-beta*sum((a.get(p,0)-b.get(p,0))**2 for p in a.keys()|b.keys()))


def divisor_rank_polynomial(n):
    coefficients=[1]
    for e in valuations(n).values():
        out=[0]*(len(coefficients)+e)
        for i,c in enumerate(coefficients):
            for j in range(e+1):out[i+j]+=c
        coefficients=out
    return coefficients


class CyclotomicCollision:
    def __init__(self,conductor):
        self.conductor=conductor
        self.ring=QuotientRing(cyclotomic(conductor))
        self.zeta=self.ring.generator
        L=conductor
        self.gauss=[sum((self.zeta**(j*(r-j)%L) for j in range(L)),self.ring.zero)
                    for r in range(L)]
        self.partial=[sum((self.zeta**(j*(r-j)%L) for j in range(r+1)),self.ring.zero)
                      for r in range(L)]

    def coefficient(self,n):
        if n<0 or not isinstance(n,int):raise ValueError("nonnegative index required")
        d,r=divmod(n,self.conductor)
        return d*self.gauss[r]+self.partial[r]

    def direct(self,n):
        L=self.conductor
        return sum((self.zeta**(j*(n-j)%L) for j in range(n+1)),self.ring.zero)

    def numerator(self):
        L=self.conductor
        out=[self.ring.zero for _ in range(2*L-1)]
        for r in range(L):
            for s in range(L):out[r+s]=out[r+s]+self.zeta**(r*s%L)
        return out


def collision_receipt():
    rows=[]
    for L in range(2,11):
        c=CyclotomicCollision(L);num=c.numerator()
        checks=[c.coefficient(n)==c.direct(n) for n in range(5*L+3)]
        recurrence=[c.coefficient(n+2*L)-2*c.coefficient(n+L)+c.coefficient(n)==0
                    for n in range(3*L)]
        rows.append({"conductor":L,"direct_coefficients_match":all(checks),
                     "stride_recurrence":all(recurrence),"numerator_at_one":sum(num,c.ring.zero).record(),
                     "numerator_at_one_is_L":sum(num,c.ring.zero)==L,
                     "large_index":str(10**100),"large_coefficient":c.coefficient(10**100).record()})
    return {"arithmetic":"exact cyclotomic quotient rings","kappa_72_108":kappa(72,108),"rows":rows}
