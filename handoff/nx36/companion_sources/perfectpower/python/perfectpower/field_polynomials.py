"""Small exact polynomial operations over Q(t) or a squarefree Q-algebra.

Squarefree quotient algebras may be products of fields. A nonunit raises a
factor witness; callers must split the modulus, never silently divide by it.
"""
from fractions import Fraction as Q
from . import polyalg as P
from .core import mul
from .observable_machine import _q
from .rational_functions import RationalFunction as RF, AlgebraBudget


def trim(a):
    a=list(a)
    while len(a)>1 and not a[-1]:a.pop()
    return a


def add(a,b):
    zero=a[0].coerce(0)
    return trim([(a[i] if i<len(a) else zero)+(b[i] if i<len(b) else zero) for i in range(max(len(a),len(b)))])


def scale(a,c):return trim([v*c for v in a])
def product(a,b):
    out=[a[0].coerce(0) for _ in range(len(a)+len(b)-1)]
    for i,c in enumerate(a):
        for j,d in enumerate(b):out[i+j]=out[i+j]+c*d
    return trim(out)


def derivative(a):return trim([i*a[i] for i in range(1,len(a))] or [a[0].coerce(0)])
def evaluate(a,x):
    out=a[0].coerce(0)
    for c in reversed(a):out=out*x+c
    return out


def power(a,n):
    if type(n) is not int or n<0:raise ValueError('nonnegative polynomial exponent required')
    out=[a[0].coerce(1)]
    for _ in range(n):out=product(out,a)
    return out


def shift(a,h):
    out=[a[0].coerce(0)]
    for c in reversed(a):out=add(product(out,[h,h.coerce(1)]),[c])
    return out


def divide(a,b):
    a,b=trim(a),trim(b)
    if len(b)==1 and not b[0]:raise ZeroDivisionError('zero field polynomial')
    zero=a[0].coerce(0);q=[zero for _ in range(max(1,len(a)-len(b)+1))]
    while any(a) and len(a)>=len(b):
        k=len(a)-len(b);c=a[-1]/b[-1];q[k]=q[k]+c
        a=add(a,[zero]*k+scale(b,-c))
    return trim(q),trim(a)


def extended_gcd(a,b):
    zero,one=a[0].coerce(0),a[0].coerce(1)
    r,s,u,v=[one],[zero],[zero],[one]
    a,b=trim(a),trim(b)
    while any(b):
        q,c=divide(a,b);a,b=b,c
        r,s=s,add(r,scale(product(q,s),-1));u,v=v,add(u,scale(product(q,v),-1))
    k=one/a[-1]
    return scale(a,k),scale(r,k),scale(u,k)


def matrix_product(a,b):
    zero=a[0][0].coerce(0)
    return [[sum((x*y for x,y in zip(row,col)),zero) for col in zip(*b)] for row in a]


def matrix_rank(a):
    a=[list(r) for r in a];k=0
    for j in range(len(a[0])):
        p=next((i for i in range(k,len(a)) if a[i][j]),None)
        if p is None:continue
        a[k],a[p]=a[p],a[k];v=a[k][j];a[k]=[x/v for x in a[k]]
        for i in range(k+1,len(a)):
            v=a[i][j];a[i]=[x-v*y for x,y in zip(a[i],a[k])]
        k+=1
        if k==len(a):break
    return k


class NonUnit(ArithmeticError):
    def __init__(self,factor):
        super().__init__('nonunit in squarefree quotient algebra; split required')
        self.factor=factor


class SquarefreeAlgebra:
    def __init__(self,modulus,budget=None):
        self.modulus=P.monic(P.poly(map(_q,modulus)))
        self.budget=budget or AlgebraBudget()
        self.budget.check(self.modulus)
        if P.degree(self.modulus)<1 or P.degree(P.gcd_poly(self.modulus,P.derivative(self.modulus)))>0:
            raise ValueError('positive-degree squarefree modulus required')

    def element(self,coefficients):return AlgebraElement(self,coefficients)
    def rational_function(self,value):
        return self.element(value.n)/self.element(value.d)


class AlgebraElement:
    def __init__(self,algebra,coefficients):
        self.algebra=algebra
        self.coefficients=P.divmod_poly(P.poly(map(_q,coefficients)),algebra.modulus)[1]
        algebra.budget.check(self.coefficients)

    def coerce(self,value):
        if isinstance(value,AlgebraElement):
            if value.algebra is not self.algebra:raise ValueError('different quotient algebras')
            return value
        return self.algebra.element([_q(value)])
    def __bool__(self):return not P.is_zero(self.coefficients)
    def __eq__(self,value):return self.coefficients==self.coerce(value).coefficients
    def __neg__(self):return self.algebra.element(P.scale(self.coefficients,-1))
    def __add__(self,value):return self.algebra.element(P.add(self.coefficients,self.coerce(value).coefficients))
    __radd__=__add__
    def __sub__(self,value):return self+-self.coerce(value)
    def __rsub__(self,value):return self.coerce(value)+-self
    def __mul__(self,value):return self.algebra.element(mul(self.coefficients,self.coerce(value).coefficients))
    __rmul__=__mul__
    def inverse(self):
        if not self:raise ZeroDivisionError('zero algebra element')
        a,b=self.coefficients,self.algebra.modulus
        r,s=P.ONE,P.ZERO
        while not P.is_zero(b):
            q,c=P.divmod_poly(a,b);a,b=b,c;r,s=s,P.add(r,P.scale(mul(q,s),-1))
            self.algebra.budget.check(a,b,r,s)
        if P.degree(a)>0:raise NonUnit(P.monic(a))
        if P.is_zero(a):raise ZeroDivisionError('zero algebra element')
        return self.algebra.element(P.scale(r,1/a[0]))
    def __truediv__(self,value):return self*self.coerce(value).inverse()
    def __rtruediv__(self,value):return self.coerce(value)/self
    def packet(self):return list(map(str,self.coefficients))


def polynomial_inverse(a,modulus):
    g,s,_=extended_gcd(a,modulus)
    if len(g)!=1:raise ValueError('polynomial not invertible modulo the curve equation')
    return divide(s,modulus)[1]
