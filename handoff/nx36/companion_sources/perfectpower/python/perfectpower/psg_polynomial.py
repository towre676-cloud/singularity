"""Budgeted sparse Q-polynomials for source-bound PSG reductions.

No CAS dependency, floating-point acceptance, or executable input expressions.
Polynomials keep a fixed variable order; packets use exact rational strings.
"""
import ast
from fractions import Fraction as Q
from .divisor_square import WorkLimit


def rational(x):
    if type(x) not in (int, str, Q):
        raise ValueError('exact integer, rational string or Fraction required')
    q = Q(x)
    if max(abs(q.numerator).bit_length(), q.denominator.bit_length()) > 4096:
        raise WorkLimit('rational exceeds 4096 bits')
    return q


class Polynomial:
    """Canonical sparse multivariate polynomial, immutable public coefficients."""
    def __init__(self, variables, terms=()):
        self.variables = tuple(variables)
        if not 1 <= len(self.variables) <= 8 or len(set(self.variables)) != len(self.variables):
            raise ValueError('one to eight distinct variable names required')
        if any(type(v) is not str or not v.isidentifier() for v in self.variables):
            raise ValueError('identifier variable names required')
        items = terms.items() if isinstance(terms, dict) else terms
        out = {}
        for exponent, coefficient in items:
            exponent = tuple(exponent)
            if len(exponent) != len(self.variables) or any(type(e) is not int or e < 0 for e in exponent):
                raise ValueError('nonnegative integer exponent vector required')
            if sum(exponent) > 128:
                raise WorkLimit('total degree exceeds 128')
            out[exponent] = rational(out.get(exponent, Q(0)) + rational(coefficient))
            if len(out) > 4096:
                raise WorkLimit('monomial budget exceeded')
        self._terms = tuple(sorted((e,c) for e,c in out.items() if c))

    @property
    def terms(self): return dict(self._terms)
    def __bool__(self): return bool(self._terms)
    def __eq__(self, other):
        return isinstance(other, Polynomial) and self.variables == other.variables and self._terms == other._terms
    def constant(self, q): return Polynomial(self.variables, [(tuple(0 for _ in self.variables), rational(q))])
    def variable(self, name):
        i = self.variables.index(name)
        return Polynomial(self.variables, [(tuple(int(j == i) for j in range(len(self.variables))), 1)])
    def coerce(self, other):
        if not isinstance(other, Polynomial): return self.constant(other)
        if other.variables != self.variables: raise ValueError('variable order mismatch')
        return other
    def __add__(self, other):
        other = self.coerce(other)
        return Polynomial(self.variables, self._terms + other._terms)
    __radd__ = __add__
    def __neg__(self): return Polynomial(self.variables, [(e,-c) for e,c in self._terms])
    def __sub__(self, other): return self + -self.coerce(other)
    def __rsub__(self, other): return self.coerce(other) + -self
    def __mul__(self, other):
        other = self.coerce(other)
        if len(self._terms)*len(other._terms) > 200000:
            raise WorkLimit('polynomial multiplication work budget exceeded')
        out = {}
        for a,c in self._terms:
            for b,d in other._terms:
                e = tuple(x+y for x,y in zip(a,b))
                out[e] = out.get(e,Q(0))+c*d
        return Polynomial(self.variables,out)
    __rmul__ = __mul__
    def __truediv__(self, other):
        q = rational(other)
        if not q: raise ZeroDivisionError('zero scalar divisor')
        return Polynomial(self.variables, [(e,c/q) for e,c in self._terms])
    def __pow__(self, n):
        if type(n) is not int or not 0 <= n <= 128: raise ValueError('power in 0..128 required')
        result = self.constant(1); base = self
        while n:
            if n & 1: result = result*base
            n //= 2
            if n: base = base*base
        return result
    def derivative(self, variable):
        i = self.variables.index(variable)
        return Polynomial(self.variables, [(tuple(v-int(j==i) for j,v in enumerate(e)), c*e[i])
                                           for e,c in self._terms if e[i]])
    def degree(self, variable=None):
        if variable is None: return max((sum(e) for e,c in self._terms),default=-1)
        i = self.variables.index(variable)
        return max((e[i] for e,c in self._terms),default=-1)
    def substitute(self, replacements):
        if set(replacements)-set(self.variables): raise ValueError('unknown substitution variable')
        values = [self.coerce(replacements.get(v,self.variable(v))) for v in self.variables]
        powers = [{0:self.constant(1)} for _ in values]
        out = self.constant(0)
        for e,c in self._terms:
            term = self.constant(c)
            for i,k in enumerate(e):
                if k not in powers[i]: powers[i][k] = values[i]**k
                term = term*powers[i][k]
            out = out+term
        return out
    def evaluate(self, values):
        if isinstance(values, dict):
            if set(values) != set(self.variables): raise ValueError('all variable values required')
            values = [values[v] for v in self.variables]
        if len(values) != len(self.variables): raise ValueError('evaluation dimension mismatch')
        values = tuple(map(rational,values))
        result = Q(0)
        for e,c in self._terms:
            for v,k in zip(values,e): c = rational(c*v**k)
            result = rational(result+c)
        return result
    def divide(self, divisors):
        """Lexicographic multivariate division; emit quotients and remainder."""
        divisors = tuple(self.coerce(d) for d in divisors)
        if any(not d for d in divisors): raise ValueError('zero polynomial divisor')
        current = self; remainder = self.constant(0)
        quotients = [self.constant(0) for _ in divisors]
        steps = 0
        while current:
            steps += 1
            if steps > 10000: raise WorkLimit('division exceeds 10000 steps')
            e,c = current._terms[-1]
            for i,d in enumerate(divisors):
                f,b = d._terms[-1]
                if all(x>=y for x,y in zip(e,f)):
                    t = Polynomial(self.variables, [(tuple(x-y for x,y in zip(e,f)),c/b)])
                    quotients[i] = quotients[i]+t; current = current-t*d
                    break
            else:
                t = Polynomial(self.variables,[(e,c)])
                remainder = remainder+t; current = current-t
        return tuple(quotients),remainder
    def packet(self):
        return {'variables':list(self.variables),'terms':[[list(e),str(c)] for e,c in self._terms]}
    @classmethod
    def from_packet(cls, p):
        if not isinstance(p,dict) or set(p) != {'variables','terms'}: raise ValueError('invalid polynomial packet')
        return cls(p['variables'],p['terms'])
    def expression(self):
        parts=[]
        for e,c in self._terms:
            factors=[f'({c.numerator}:ℚ)' if c.denominator==1 else f'(({c.numerator}:ℚ)/{c.denominator})']
            factors += [f'{v}^{k}' for v,k in zip(self.variables,e) if k]
            parts.append('*'.join(factors))
        return '+'.join(parts) or '(0:ℚ)'


def parse(expression, variables):
    """Read arithmetic only: names, integers, +,-,*, constant /, integer powers."""
    if type(expression) is not str or len(expression)>100000: raise ValueError('bounded expression required')
    prototype=Polynomial(variables); nodes=0
    def visit(n):
        nonlocal nodes
        nodes+=1
        if nodes>10000: raise WorkLimit('expression node budget exceeded')
        if isinstance(n,ast.Constant) and type(n.value) is int: return prototype.constant(n.value)
        if isinstance(n,ast.Name) and n.id in prototype.variables: return prototype.variable(n.id)
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):
            p=visit(n.operand); return -p if isinstance(n.op,ast.USub) else p
        if isinstance(n,ast.BinOp):
            if isinstance(n.op,ast.Pow):
                if not isinstance(n.right,ast.Constant) or type(n.right.value) is not int: raise ValueError('literal exponent required')
                return visit(n.left)**n.right.value
            a,b=visit(n.left),visit(n.right)
            if isinstance(n.op,ast.Add): return a+b
            if isinstance(n.op,ast.Sub): return a-b
            if isinstance(n.op,ast.Mult): return a*b
            if isinstance(n.op,ast.Div) and b.degree()<=0: return a/b.evaluate([0]*len(variables))
        raise ValueError('unsupported polynomial syntax')
    return visit(ast.parse(expression.replace('^','**'),mode='eval').body)


def power_coordinates(polynomial, variables, mapping):
    """Exact polynomial factor through declared monomial coordinates.

Every surviving exponent must be divisible by its declared power. Variables
omitted from the map must have exponent zero, including an eliminated one.
"""
    variables=tuple(variables); out=[]
    for old,(new,power) in mapping.items():
        if old not in polynomial.variables or new not in variables or type(power) is not int or power<1:
            raise ValueError('invalid power coordinate')
    if len({new for new,power in mapping.values()})!=len(mapping):
        raise ValueError('power coordinates must have distinct targets')
    for e,c in polynomial._terms:
        exponent=[0]*len(variables)
        for old,k in zip(polynomial.variables,e):
            if old not in mapping:
                if k:raise ValueError('unmapped variable survives')
                continue
            new,power=mapping[old]
            if k%power:raise ValueError('exponent is not in declared power image')
            exponent[variables.index(new)]=k//power
        out.append((tuple(exponent),c))
    return Polynomial(variables,out)
