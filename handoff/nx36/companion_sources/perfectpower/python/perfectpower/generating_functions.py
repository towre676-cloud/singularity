"""Exact rational formal series on the existing Q(z) and recurrence engines.

Coefficients use parity reduction (Bostan--Mori), not prefix fitting. All
polynomials are constant-first. Analytic convergence is outside this API.
"""
from fractions import Fraction as Q
from functools import lru_cache
from . import polyalg as P
from .core import mul
from .observable_machine import _q
from .rational_functions import RationalFunction as RF, AlgebraBudget
from .divisor_square import WorkLimit


def _index(n):
    if type(n) is not int or not 0 <= n < 2**64:
        raise ValueError('nonnegative 64-bit index required')
    return n


class RationalSeries:
    """A normalized Q[[z]] rational series with bounded exact coefficient access."""
    def __init__(self, specification):
        if not isinstance(specification, dict) or set(specification) != {'numerator', 'denominator'}:
            raise ValueError('numerator and denominator required')
        if any(not isinstance(specification[k], (list, tuple)) or
               not 1 <= len(specification[k]) <= 257 for k in specification):
            raise WorkLimit('series polynomial degree budget is 256')
        self._rf = RF(specification['numerator'], specification['denominator'],
                      budget=AlgebraBudget(degree_limit=256, bit_limit=8192))
        if not self._rf.d[0]:
            raise ValueError('formal series denominator must be nonzero at zero')
        self.numerator = P.scale(self._rf.n, 1/self._rf.d[0])
        self.denominator = P.scale(self._rf.d, 1/self._rf.d[0])

    @classmethod
    def from_rf(cls, rf):
        return cls({'numerator': rf.n, 'denominator': rf.d})

    @classmethod
    def from_recurrence(cls, model):
        p, q = model.generating_function()
        return cls({'numerator': p, 'denominator': q})

    def summary(self):
        return {'schema': 'pp-rational-series/1',
                'numerator': list(map(str, self.numerator)),
                'denominator': list(map(str, self.denominator)),
                'scope': 'all nonnegative formal coefficients of this supplied rational function',
                'execution_verified': False}

    def realization_certificate(self):
        """Exact sequence realization with a nonzero Hankel minimality witness."""
        from .generating import RationalGF
        return RationalGF(self.numerator,self.denominator).packet()

    def analytic_tail(self, argument, radius, count):
        """Certified Cauchy remainder where the explicit disk test succeeds."""
        from .generating import RationalGF
        return RationalGF(self.numerator,self.denominator).tail(argument,radius,count)

    def evidence(self):
        from .recurrence import from_generating_function
        model = from_generating_function(self.numerator, self.denominator)
        return dict(self.summary(), recurrence={
            'coefficients': list(map(str, model.coefficients)),
            'initial': list(map(str, model.initial)),
            'ordering': 'chronological: a[n+r] = sum(c[i]*a[n+i])'})

    def __add__(self, other):
        return self.from_rf(self._fresh() + other._fresh())

    def __mul__(self, other):
        return self.from_rf(self._fresh() * other._fresh())

    def _fresh(self):
        return RF(self.numerator, self.denominator, budget=AlgebraBudget(degree_limit=256, bit_limit=8192))

    def prefix_sums(self):
        return self.from_rf(self._fresh() / RF([1, -1]))

    def theta(self):
        """Coefficient n becomes n*a[n]; repeat for polynomial moments."""
        return self.from_rf(RF([0, 1]) * self._fresh().derivative())

    def coefficient(self, index, modulus=None, bit_limit=8192):
        """[z^index] P/Q in logarithmically many parity reductions.

        Modular queries require every input rational denominator to be a
        unit modulo modulus. Composite moduli are supported under that rule.
        """
        n = _index(index)
        if type(bit_limit) is not int or not 1 <= bit_limit <= 8192:
            raise ValueError('bit limit 1 through 8192 required')
        if modulus is not None and (type(modulus) is not int or not 2 <= modulus < 2**64):
            raise ValueError('modulus must be an integer 2 through 2^64-1')
        return self._coefficient(n, modulus, bit_limit)

    @lru_cache(maxsize=1024)
    def _coefficient(self, n, modulus, bit_limit):
        def checked(xs):
            if modulus is not None:
                return tuple(x % modulus for x in xs)
            if any(max(abs(x.numerator).bit_length(), x.denominator.bit_length()) > bit_limit for x in xs):
                raise WorkLimit('formal coefficient bit budget exceeded')
            return tuple(xs)
        if modulus is None:
            p, q = checked(self.numerator), checked(self.denominator)
        else:
            def reduce(xs):
                try:
                    return tuple(x.numerator * pow(x.denominator, -1, modulus) % modulus for x in xs)
                except ValueError as error:
                    raise ValueError('nonunit rational denominator modulo modulus') from error
            p, q = reduce(self.numerator), reduce(self.denominator)
        def product(a, b):
            if modulus is None:
                return checked(mul(a, b))
            out = [0]*(len(a)+len(b)-1)
            for i, x in enumerate(a):
                for j, y in enumerate(b):
                    out[i+j] = (out[i+j] + x*y) % modulus
            return tuple(out)
        while n:
            conjugate = tuple(x if i % 2 == 0 else -x for i, x in enumerate(q))
            pq, qq = product(p, conjugate), product(q, conjugate)
            p = pq[n % 2::2] or (Q(0),)
            q = qq[::2]
            if modulus is None:
                # Preserve the rational function while removing the common
                # scalar introduced by repeated denominator squaring. Without
                # this normalization intermediate bits can grow far beyond
                # the size of the requested exact probability coefficient.
                constant = q[0]
                p = checked(tuple(x/constant for x in p))
                q = checked(tuple(x/constant for x in q))
            n //= 2
        if modulus is not None:
            return int(p[0] * pow(int(q[0]), -1, modulus) % modulus)
        return checked((p[0]/q[0],))[0]

    def terms(self, start=0, size=12, modulus=None):
        _index(start)
        if type(size) is not int or not 0 <= size <= 1024 or start+size > 2**64:
            raise ValueError('bounded term window required')
        return [self.coefficient(n, modulus) for n in range(start, start+size)]

    def subsequence(self, offset=0, step=1):
        """Exact rational function for a[offset+step*n], including step zero."""
        from .recurrence import from_generating_function
        from .witness_resolvent import subsequence_resolvent
        _index(offset); _index(step)
        model = from_generating_function(self.numerator, self.denominator)
        r = model.order
        if r > 64:
            raise WorkLimit('subsequence companion dimension exceeds 64')
        a = [[int(j == i+1) for j in range(r)] for i in range(r-1)] + [list(model.coefficients)]
        receipt = subsequence_resolvent(a, model.initial, [[1]+[0]*(r-1)], offset=offset, step=step)
        return self.from_rf(RF(receipt['outputs'][0]['numerator'], receipt['outputs'][0]['denominator']))


ONE = RationalSeries({'numerator': [1], 'denominator': [1]})


def semilinear_series(predicate):
    """Exact nonnegative indicator series from the existing disjoint cell compiler."""
    from .semilinear_domains import semilinear_domain, verify_domain
    source = semilinear_domain(predicate, period_limit=256)
    if not verify_domain(source):
        raise AssertionError('semilinear source replay failed')
    result = RF([0]); pieces = []
    for cell in source['cells']:
        lo, hi = cell['interval']; lo = max(0, lo if lo is not None else 0)
        m = cell['modulus']
        for residue in cell['residues']:
            first = lo + (residue-lo) % m
            if hi is not None and first > hi:
                continue
            if first > 256:
                raise WorkLimit('semilinear series onset exceeds dense degree budget')
            numerator = [0]*first+[1]
            if hi is not None:
                end = first + m*((hi-first)//m+1)
                if end > 256:
                    raise WorkLimit('semilinear finite endpoint exceeds dense degree budget')
                numerator += [0]*(end-first)
                numerator[end] = -1
            denominator = [1]+[0]*(m-1)+[-1]
            result += RF(numerator, denominator)
            pieces.append({'first': first, 'last': hi, 'step': m})
    series = RationalSeries.from_rf(result)
    return {'schema': 'pp-semilinear-series/1', 'source': source,
            'progressions': pieces, 'series': series.summary(), 'execution_verified': False}
