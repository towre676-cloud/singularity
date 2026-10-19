"""Complete observations of rational periodic Mellin/Dirichlet families.

The rational kernel, its entire future coefficient sequence and its Dirichlet
function on Re(s)>1 determine one another.  A selected special value need not.
Minimal machines are the existing exact observable-machine implementation;
this module adds a periodic input convention, not another minimization engine.

All certificates here are exact Python arithmetic, not Lean proofs.  The
observable state dimension concerns the trace output, not its representation.
"""

from dataclasses import dataclass
from fractions import Fraction as Q
from math import lcm

from .divisor_square import WorkLimit
from .generating import RationalGF
from .observable_machine import minimal_machine, verify_machine


def _rational(value):
    if type(value) not in (int, str, Q):
        raise ValueError('an exact integer, Fraction, or rational string is required')
    value = Q(value)
    if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 8192:
        raise WorkLimit('periodic coefficient exceeds the 8192-bit budget')
    return value


def _json_exact(value):
    """Keep receipt integers and booleans; serialize only rational entries."""
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_exact(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_exact(item) for item in value]
    return value


@dataclass(frozen=True)
class PeriodObservation:
    """A rational block c_1,...,c_N extended periodically for n >= 1.

    The declared period need not be the smallest period.  Equality of the
    complete observation is checked by ``separating_witness``; dataclass
    equality instead compares the supplied, normalized finite blocks.
    """

    coefficients: tuple

    def __post_init__(self):
        values = []
        for item in self.coefficients:
            if len(values) == 4096:
                raise WorkLimit('the declared period exceeds the 4096-entry budget')
            values.append(_rational(item))
        if not values:
            raise ValueError('a nonempty rational coefficient block is required')
        object.__setattr__(self, 'coefficients', tuple(values))

    @property
    def period(self):
        return len(self.coefficients)

    def coefficient(self, n):
        if type(n) is not int or n < 1:
            raise ValueError('a positive integer coefficient index is required')
        return self.coefficients[(n - 1) % self.period]

    def generating_function(self):
        """Reduced K(x)=sum_(n>=1) c_n*x**(n-1), exactly over Q."""
        denominator = (1,) + (0,) * (self.period - 1) + (-1,)
        return RationalGF(self.coefficients, denominator)

    def dirichlet(self):
        """F(s)=sum_(n>=1) c_n/n**s, absolutely convergent on Re(s)>1."""
        from .dirichlet_periods import PeriodicDirichlet
        return PeriodicDirichlet(self.coefficients)

    def separating_witness(self, other, *, period_budget=65536):
        """Find the first unequal coefficient in one common period, if any.

        Uniqueness of bounded Dirichlet series makes this an exact equality
        test for the full functions on Re(s)>1.  It does not compare just a
        finite list of values of s or rely on numerical recognition.
        """
        if not isinstance(other, PeriodObservation):
            raise ValueError('another PeriodObservation is required')
        if type(period_budget) is not int or period_budget < 1:
            raise ValueError('a positive integer common-period budget is required')
        common = lcm(self.period, other.period)
        if common > period_budget:
            raise WorkLimit('least common period exceeds the comparison budget')
        for n in range(1, common + 1):
            left, right = self.coefficient(n), other.coefficient(n)
            if left != right:
                return {'equal': False, 'common_period': common, 'checked_indices': n,
                        'first_differing_index': n, 'left': str(left), 'right': str(right),
                        'difference': str(left - right),
                        'scope': 'complete coefficient sequence and Dirichlet function on Re(s)>1'}
        return {'equal': True, 'common_period': common, 'checked_indices': common,
                'first_differing_index': None,
                'scope': 'complete coefficient sequence and Dirichlet function on Re(s)>1'}

    def machine(self):
        """Minimize the N-state cyclic shift using the existing exact engine.

        At time k>=0 the readout is c_(k+1).  The dense engine's period-64
        limit is separate from the period-4096 symbolic-kernel limit.
        """
        n = self.period
        if n > 64:
            raise WorkLimit('the dense periodic machine has a 64-state budget')
        shift = tuple(tuple(Q(j == (i + 1) % n) for j in range(n)) for i in range(n))
        readout = (Q(1),) + (Q(0),) * (n - 1)
        result = minimal_machine((shift,), self.coefficients, (readout,))
        if not verify_machine(result):
            raise ArithmeticError('the periodic observable-machine certificate did not replay')
        if result['minimal_dimension'] != self.generating_function().dimension:
            raise ArithmeticError('rational-kernel and observable-machine ranks disagree')
        return result

    def packet(self, *, include_machine=False):
        """A JSON-safe reduced kernel, with an optional replayable machine."""
        if type(include_machine) is not bool:
            raise ValueError('include_machine must be a boolean')
        kernel = self.generating_function()
        result = {'schema': 'pp-period-observation/1',
                  'coefficients': list(map(str, self.coefficients)),
                  'declared_period': self.period,
                  'reduced_kernel': {'numerator_low_to_high': list(map(str, kernel.numerator)),
                                     'denominator_low_to_high': list(map(str, kernel.denominator))},
                  'minimal_dimension': kernel.dimension,
                  'indexing': 'machine time k>=0 reads c_(k+1); Dirichlet indices n>=1',
                  'analytic_scope': 'complete Dirichlet function on Re(s)>1',
                  'verification': 'exact rational Python arithmetic, not Lean',
                  'dimension_scope': 'minimal linear state dimension for the coefficient output'}
        if include_machine:
            result['machine'] = _json_exact(self.machine())
        return result


def e8_observations():
    """Trace outputs of E8 reflection and adjoint Coxeter representations.

    The adjoint formula is c_30(n)+240*[30 divides n], as checked by the
    separate actual E8 Lie-algebra lift.  No 30-dimensional Lie algebra is
    inferred from the compressed trace sequence.
    """
    from .e8_periods import ramanujan_sum_30
    reflection = tuple(ramanujan_sum_30(n) for n in range(1, 31))
    adjoint = tuple(c + (240 if n == 30 else 0) for n, c in enumerate(reflection, 1))
    return PeriodObservation(reflection), PeriodObservation(adjoint)


def receipt():
    """Deterministic independent kernel and machine certificates for E8."""
    reflection, adjoint = e8_observations()
    outputs = []
    for name, observation, dimension in (('reflection', reflection, 8), ('adjoint', adjoint, 248)):
        item = observation.packet(include_machine=True)
        item['representation'] = name
        item['underlying_representation_dimension'] = dimension
        item['rational_gf'] = observation.generating_function().packet()
        outputs.append(item)
    if [item['minimal_dimension'] for item in outputs] != [8, 30]:
        raise ArithmeticError('the E8 trace-output dimensions changed unexpectedly')
    return {'schema': 'pp-period-observability/1', 'field': 'Q',
            'reflection': outputs[0], 'adjoint': outputs[1],
            'adjoint_thirtieth_coefficient': str(adjoint.coefficient(30)),
            'scope': 'all-future trace-output compression; not an isomorphism of representations',
            'proof_status': 'exact Python certificates with analytic uniqueness argument; not Lean'}
