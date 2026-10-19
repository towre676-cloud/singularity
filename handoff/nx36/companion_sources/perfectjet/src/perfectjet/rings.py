"""Exact quotient rings, cyclotomic polynomials, and explicit field-element replay."""
from fractions import Fraction as Q
from functools import lru_cache


def trim(p):
    p = list(map(Q,p))
    while len(p)>1 and not p[-1]:
        p.pop()
    return p or [Q(0)]


def divide(a,b):
    a,b=trim(a),trim(b)
    if b==[0]:
        raise ZeroDivisionError("zero polynomial")
    q=[Q(0)]*max(1,len(a)-len(b)+1)
    while len(a)>=len(b) and a!=[0]:
        j=len(a)-len(b);z=a[-1]/b[-1];q[j]+=z
        for i,c in enumerate(b):
            a[i+j]-=z*c
        a=trim(a)
    return trim(q),trim(a)


@lru_cache(None)
def cyclotomic(n):
    if n<1:
        raise ValueError("positive conductor required")
    p=[Q(-1)]+[Q(0)]*(n-1)+[Q(1)]
    for d in range(1,n):
        if n%d==0:
            p,r=divide(p,cyclotomic(d))
            if r!=[0]:
                raise ArithmeticError("nonexact cyclotomic division")
    return tuple(p)


class QuotientRing:
    def __init__(self, modulus):
        self.modulus=tuple(trim(modulus))
        if len(self.modulus)<2 or self.modulus[-1]!=1:
            raise ValueError("monic positive-degree modulus required")
        self.degree=len(self.modulus)-1

    def element(self,coefficients):
        _,r=divide(coefficients,self.modulus)
        return Element(self,tuple(r+[Q(0)]*(self.degree-len(r))))

    @property
    def zero(self):
        return self.element([0])

    @property
    def one(self):
        return self.element([1])

    @property
    def generator(self):
        return self.element([0,1])


class Element:
    def __init__(self,ring,coefficients):
        self.ring,self.coefficients=ring,coefficients

    def coerce(self,other):
        if not isinstance(other,Element):
            return self.ring.element([other])
        if other.ring.modulus!=self.ring.modulus:
            raise ValueError("different quotient rings")
        return other

    def __add__(self,other):
        other=self.coerce(other)
        return self.ring.element([a+b for a,b in zip(self.coefficients,other.coefficients)])

    __radd__=__add__

    def __neg__(self):
        return self.ring.element([-a for a in self.coefficients])

    def __sub__(self,other):
        return self+-self.coerce(other)

    def __rsub__(self,other):
        return self.coerce(other)-self

    def __mul__(self,other):
        other=self.coerce(other)
        p=[Q(0)]*(2*self.ring.degree-1)
        for i,a in enumerate(self.coefficients):
            for j,b in enumerate(other.coefficients):
                p[i+j]+=a*b
        return self.ring.element(p)

    __rmul__=__mul__

    def __pow__(self,n):
        if not isinstance(n,int):
            raise ValueError("integer exponent required")
        if n<0:
            return self.inverse()**(-n)
        out,base=self.ring.one,self
        while n:
            if n&1:out=out*base
            base=base*base;n//=2
        return out

    def inverse(self):
        from .exact import rref
        n=self.ring.degree
        cols=[(self*self.ring.element([0]*j+[1])).coefficients for j in range(n)]
        rows=[[cols[j][i] for j in range(n)]+[Q(i==0)] for i in range(n)]
        rr,piv=rref(rows,n+1)
        if len(piv)!=n or n in piv:
            raise ZeroDivisionError("nonunit quotient-ring element")
        coeff=[Q(0)]*n
        for i,p in enumerate(piv):coeff[p]=rr[i][-1]
        out=self.ring.element(coeff)
        if self*out!=1:raise ArithmeticError("inverse replay failed")
        return out

    def __truediv__(self,other):
        return self*self.coerce(other).inverse()

    def __eq__(self,other):
        return self.coefficients==self.coerce(other).coefficients

    def record(self):
        return [str(x) for x in self.coefficients]


def core_field_receipt():
    ring=QuotientRing([-1,5,-4,1]);u=ring.generator;alpha=u-1;beta=-(alpha**-1)
    h=(-2*u**2+3*u-2)/(-u**2+u)
    v=(6*u-8)/(3*u**2-8*u+5)
    return {"modulus": [-1,5,-4,1],"arithmetic":"exact rational quotient ring",
            "alpha_polynomial_zero":alpha**3-alpha**2+1==0,
            "plastic_polynomial_zero":beta**3-beta-1==0,
            "hessian_identity_zero":h**3+4*h**2-23*h+23==0,
            "vertex_identity_zero":23*v**3+4*v+200==0,
            "hessian_coordinates":h.record(),"vertex_coordinates":v.record()}
