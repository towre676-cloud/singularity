"""Exact iterated rational-function fields Q(t_1,...,t_r), r <= 3.

A tower uses polynomial Euclidean gcd over the preceding coefficient field.
No symbolic expression evaluation or optional algebra package is used.
"""
from fractions import Fraction as Q
from .observable_machine import _q
from .rational_functions import AlgebraBudget
from .divisor_square import WorkLimit


def trim(a):
    a=list(a)
    while len(a)>1 and not a[-1]:a.pop()
    return tuple(a)


def add(a,b,zero):return trim([(a[i] if i<len(a) else zero)+(b[i] if i<len(b) else zero) for i in range(max(len(a),len(b)))])
def scale(a,c):return trim([v*c for v in a])
def mul(a,b,zero):
    out=[zero]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        if x:
            for j,y in enumerate(b):
                if y:out[i+j]=out[i+j]+x*y
    return trim(out)


def divide(a,b,zero):
    a,b=trim(a),trim(b)
    if not any(b):raise ZeroDivisionError('zero tower polynomial')
    q=[zero]*max(1,len(a)-len(b)+1)
    while any(a) and len(a)>=len(b):
        k=len(a)-len(b);c=a[-1]/b[-1];q[k]=q[k]+c
        a=add(a,[zero]*k+list(scale(b,-c)),zero)
    return trim(q),a


def gcd(a,b,zero):
    while any(b):a,b=b,divide(a,b,zero)[1]
    return scale(a,1/a[-1]) if any(a) else (zero,)


def fraction_free_system(matrix,rhs=None):
    """Bareiss elimination and back substitution over the exact field tower.

    Keeping polynomial minors until back substitution avoids introducing a
    rational denominator at every Gaussian elimination entry.
    """
    n=len(matrix)
    if not n or any(len(row)!=n for row in matrix):raise ValueError('square field matrix required')
    rhs=[[] for _ in matrix] if rhs is None else rhs
    if len(rhs)!=n or any(len(row)!=len(rhs[0]) for row in rhs):raise ValueError('matching field right-hand sides required')
    a=[list(row)+list(b) for row,b in zip(matrix,rhs)];width=len(a[0]);zero=matrix[0][0].coerce(0);one=zero.coerce(1);previous=one;sign=1
    for k in range(n-1):
        pivot=next((i for i in range(k,n) if a[i][k]),None)
        if pivot is None:return zero,None
        if pivot!=k:a[k],a[pivot]=a[pivot],a[k];sign=-sign
        p=a[k][k]
        for i in range(k+1,n):
            value=a[i][k]
            for j in range(k+1,width):a[i][j]=(p*a[i][j]-value*a[k][j])/previous
            a[i][k]=zero
        previous=p
    det=sign*a[-1][n-1]
    if not det:return zero,None
    columns=width-n;solution=[[zero]*columns for _ in range(n)]
    for i in range(n-1,-1,-1):
        for c in range(columns):solution[i][c]=(a[i][n+c]-sum((a[i][j]*solution[j][c] for j in range(i+1,n)),zero))/a[i][i]
    return det,solution


class ParameterFunction:
    def __init__(self,parameters,numerator=(0,),denominator=(1,),budget=None):
        self.parameters=tuple(parameters);self.budget=budget or AlgebraBudget()
        if not 1<=len(self.parameters)<=3:raise ValueError('one through three parameters required')
        self.zero=self._lower(0);n=trim([self._lower(a) for a in numerator]);d=trim([self._lower(a) for a in denominator])
        if not any(d):raise ValueError('nonzero tower denominator required')
        self._check(n,d)
        if not any(n):n,d=(self.zero,),(self._lower(1),)
        elif n==d:n,d=(self._lower(1),),(self._lower(1),)
        elif len(n)==1 or len(d)==1:
            leading=d[-1]
            if leading!=1:n,d=scale(n,1/leading),scale(d,1/leading)
        else:
            common=gcd(n,d,self.zero);n,r=divide(n,common,self.zero);d,s=divide(d,common,self.zero)
            if any(r) or any(s):raise AssertionError('tower gcd division failed')
            leading=d[-1];n,d=scale(n,1/leading),scale(d,1/leading)
        self.n,self.d=n,d;self._check(n,d)

    def _lower(self,v):
        if len(self.parameters)==1:return _q(v)
        if isinstance(v,ParameterFunction) and v.parameters==self.parameters[:-1]:return v
        return ParameterFunction(self.parameters[:-1],[v],budget=self.budget)

    def _check(self,*polys):
        self.budget.work+=1+sum(len(p) for p in polys)
        if self.budget.work>self.budget.work_limit:raise WorkLimit('parameter field work budget')
        for p in polys:
            if len(p)-1>self.budget.degree_limit:raise WorkLimit('parameter field degree budget')
            for c in p:
                if isinstance(c,Q) and max(abs(c.numerator).bit_length(),c.denominator.bit_length())>self.budget.bit_limit:raise WorkLimit('parameter coefficient bit budget')

    @classmethod
    def parse(cls,parameters,value,budget=None):
        budget=budget or AlgebraBudget();zero=cls(parameters,budget=budget)
        if isinstance(value,cls):
            if value.parameters!=tuple(parameters):raise ValueError('different parameter fields')
            return value.with_budget(budget)
        if isinstance(value,dict):
            if set(value)=={'parameters','tower_variable','numerator','denominator'}:
                if value['parameters']!=list(parameters) or value['tower_variable']!=parameters[-1]:raise ValueError('different parameter packet field')
                for key in ('numerator','denominator'):
                    if not isinstance(value[key],list) or not 1<=len(value[key])<=budget.degree_limit+1:raise ValueError('bounded tower coefficient arrays required')
                lower=lambda v:cls.parse(parameters[:-1],v,budget) if len(parameters)>1 else _q(v)
                return cls(parameters,[lower(v) for v in value['numerator']],[lower(v) for v in value['denominator']],budget)
            if set(value)=={'numerator','denominator'}:
                return cls.parse(parameters,value['numerator'],budget)/cls.parse(parameters,value['denominator'],budget)
            if set(value)!={'terms'} or not isinstance(value['terms'],list) or len(value['terms'])>100:raise ValueError('sparse terms required, at most 100 per coefficient')
            out=zero
            for term in value['terms']:
                if not isinstance(term,dict) or set(term)!={'powers','coefficient'}:raise ValueError('powers and coefficient required')
                powers=term['powers']
                if not isinstance(powers,list) or len(powers)!=len(parameters) or any(type(p) is not int or p<0 for p in powers) or sum(powers)>8:raise ValueError('parameter monomial total degree at most eight required')
                v=zero.coerce(term['coefficient'])
                for i,p in enumerate(powers):v=v*zero.variable(i)**p
                out=out+v
            return out
        return zero.coerce(value)

    def with_budget(self,budget):
        copy=lambda p:[a.with_budget(budget) if isinstance(a,ParameterFunction) else a for a in p]
        return ParameterFunction(self.parameters,copy(self.n),copy(self.d),budget)

    def coerce(self,value):
        if isinstance(value,ParameterFunction):
            if value.parameters!=self.parameters:raise ValueError('different parameter fields')
            return value
        return ParameterFunction(self.parameters,[_q(value)],budget=self.budget)

    def variable(self,index):
        if not 0<=index<len(self.parameters):raise ValueError('unknown parameter index')
        if index==len(self.parameters)-1:return ParameterFunction(self.parameters,[0,1],budget=self.budget)
        lower=ParameterFunction(self.parameters[:-1],budget=self.budget).variable(index)
        return ParameterFunction(self.parameters,[lower],budget=self.budget)

    def __bool__(self):return any(self.n)
    def __eq__(self,value):
        if getattr(value,'_accepts_scalar',lambda _:False)(self):return NotImplemented
        other=self.coerce(value);return self.n==other.n and self.d==other.d
    def __neg__(self):return ParameterFunction(self.parameters,scale(self.n,-1),self.d,self.budget)
    def __add__(self,value):
        if getattr(value,'_accepts_scalar',lambda _:False)(self):return NotImplemented
        b=self.coerce(value)
        if not self:return b
        if not b:return self
        if self.d==b.d:return ParameterFunction(self.parameters,add(self.n,b.n,self.zero),self.d,self.budget)
        g=gcd(self.d,b.d,self.zero);a1=divide(self.d,g,self.zero)[0];b1=divide(b.d,g,self.zero)[0]
        return ParameterFunction(self.parameters,add(mul(self.n,b1,self.zero),mul(b.n,a1,self.zero),self.zero),mul(self.d,b1,self.zero),self.budget)
    __radd__=__add__
    def __sub__(self,value):
        if getattr(value,'_accepts_scalar',lambda _:False)(self):return NotImplemented
        return self+-self.coerce(value)
    def __rsub__(self,value):return self.coerce(value)+-self
    def __mul__(self,value):
        if getattr(value,'_accepts_scalar',lambda _:False)(self):return NotImplemented
        b=self.coerce(value)
        if not self or not b:return self.coerce(0)
        if self==1:return b
        if b==1:return self
        if self.d==(self._lower(1),) and b.d==self.d:return ParameterFunction(self.parameters,mul(self.n,b.n,self.zero),budget=self.budget)
        g=gcd(self.n,b.d,self.zero);h=gcd(b.n,self.d,self.zero)
        return ParameterFunction(self.parameters,mul(divide(self.n,g,self.zero)[0],divide(b.n,h,self.zero)[0],self.zero),mul(divide(self.d,h,self.zero)[0],divide(b.d,g,self.zero)[0],self.zero),self.budget)
    __rmul__=__mul__
    def __truediv__(self,value):
        if getattr(value,'_accepts_scalar',lambda _:False)(self):return NotImplemented
        b=self.coerce(value)
        if not b:raise ZeroDivisionError('zero parameter function')
        if self==b:return self.coerce(1)
        if b==1:return self
        return self*ParameterFunction(self.parameters,b.d,b.n,self.budget)
    def __rtruediv__(self,value):return self.coerce(value)/self
    def __pow__(self,n):
        if type(n) is not int or not 0<=n<=256:raise ValueError('bounded nonnegative exponent required')
        out=self.coerce(1);v=self
        while n:
            if n%2:out=out*v
            n//=2
            if n:v=v*v
        return out
    def derivative(self,parameter=0):
        index=self.parameters.index(parameter) if isinstance(parameter,str) else parameter
        if type(index) is not int or not 0<=index<len(self.parameters):raise ValueError('unknown parameter')
        def deriv(p):
            if index==len(self.parameters)-1:return trim([i*p[i] for i in range(1,len(p))] or [self.zero])
            return trim([c.derivative(index) for c in p])
        return ParameterFunction(self.parameters,add(mul(deriv(self.n),self.d,self.zero),scale(mul(self.n,deriv(self.d),self.zero),-1),self.zero),mul(self.d,self.d,self.zero),self.budget)
    def evaluate(self,values):
        if isinstance(values,dict):values=[values[p] for p in self.parameters]
        if len(values)!=len(self.parameters):raise ValueError('one rational value per parameter')
        values=[_q(v) for v in values]
        if len(self.parameters)>1:
            from .parameter_specialization import evaluate
            return evaluate(self,values)
        t=_q(values[-1])
        def at(p):
            out=Q(0)
            for c in reversed(p):out=out*t+(c.evaluate(values[:-1]) if isinstance(c,ParameterFunction) else c)
            return out
        d=at(self.d)
        if not d:raise ValueError('parameter function pole')
        return at(self.n)/d
    def packet(self):
        encode=lambda p:[a.packet() if isinstance(a,ParameterFunction) else str(a) for a in p]
        return dict(parameters=list(self.parameters),tower_variable=self.parameters[-1],numerator=encode(self.n),denominator=encode(self.d))
