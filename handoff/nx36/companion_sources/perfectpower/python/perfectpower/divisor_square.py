"""Exact factor-pair solver for y²=P(x)²+k, in all integer coordinates.

The Lean theorem NativeDivisorSquare.complete proves the algorithm's mathematics.
Python execution remains unverified; emit_lean produces a kernel-checkable instance.
Coefficients are integers in ascending order. Work budgets raise, never truncate.
"""
from math import isqrt


class WorkLimit(ValueError):
    """No complete list was produced within the explicitly requested budget."""


class Budget:
    def __init__(self, limit=1_000_000):
        if type(limit) is not int or limit < 1:
            raise ValueError('work limit must be a positive integer')
        self.limit, self.used = limit, 0

    def spend(self):
        self.used += 1
        if self.used > self.limit:
            raise WorkLimit(f'divisor work exceeded {self.limit}; no complete result')


def _integers(coefficients):
    out = tuple(coefficients)
    if not out or any(type(c) is not int for c in out):
        raise ValueError('a nonempty sequence of integer coefficients is required')
    if out[-1] == 0:
        raise ValueError('remove trailing zero coefficients')
    return out


def evaluate(coefficients, x):
    v = 0
    for c in reversed(coefficients):
        v = c + x*v
    return v


def signed_divisors(n, budget):
    if n == 0:
        raise ValueError('zero has infinitely many divisors')
    a, out = abs(n), set()
    for d in range(1, isqrt(a)+1):
        budget.spend()
        if a % d == 0:
            out.update((d, -d, a//d, -a//d))
    return sorted(out)


def integer_roots(coefficients, budget=None):
    """All distinct integer roots of a nonzero integer polynomial."""
    coefficients = _integers(coefficients)
    budget = budget if budget is not None else Budget()
    zeros = 0
    while coefficients[zeros] == 0:
        zeros += 1
    tail = coefficients[zeros:]
    out = {0} if zeros else set()
    if len(tail) > 1:
        out.update(x for x in signed_divisors(tail[0], budget)
                   if evaluate(tail, x) == 0)
    return sorted(out)


def solve(coefficients, k, *, work_limit=1_000_000):
    coefficients = _integers(coefficients)
    if len(coefficients) < 2:
        raise ValueError('a nonconstant polynomial is required')
    if type(k) is not int or k == 0:
        raise ValueError('k must be a nonzero integer; k=0 is an infinite family')
    budget, out, fibres = Budget(work_limit), set(), {}
    pairs = 0
    for u in signed_divisors(k, budget):
        v = k//u
        if (v-u) % 2 or (v+u) % 2:
            continue
        p, y = (v-u)//2, (v+u)//2
        pairs += 1
        if p not in fibres:
            fibre = (coefficients[0]-p,) + coefficients[1:]
            fibres[p] = integer_roots(fibre, budget)
        out.update((x, y) for x in fibres[p])
    return {'points': sorted(out), 'coefficients': list(coefficients), 'k': k,
            'divisor_trials': budget.used, 'value_pairs': pairs, 'fibres': len(fibres),
            'complete': True, 'execution_verified': False,
            'theorem': 'PerfectPower.NativeDivisorSquare.complete'}


def match_square_plus_constant(coefficients):
    """Recognize an integral P²+k by exact top-down coefficient comparison."""
    f = list(coefficients)
    while len(f) > 1 and f[-1] == 0:
        f.pop()
    if len(f) < 3 or (len(f)-1) % 2 or f[-1] <= 0:
        return None
    d, top = (len(f)-1)//2, isqrt(f[-1])
    if top*top != f[-1]:
        return None
    q = [0]*(d+1)
    q[d] = top
    for j in range(d-1, -1, -1):
        i = d+j
        known = sum(q[a]*q[i-a] for a in range(j+1, d+1) if 0 <= i-a <= d)
        residual = f[i]-known
        if residual % (2*top):
            return None
        q[j] = residual//(2*top)
    sq = [sum(q[a]*q[i-a] for a in range(d+1) if 0 <= i-a <= d)
          for i in range(2*d+1)]
    if sq[1:] != f[1:]:
        return None
    return tuple(q), f[0]-sq[0]


def analyse(coefficients, k, *, parameter_work_limit=1_000_000,
            fibre_work_limit=1_000_000):
    """Return exact solved fibres and explicit residual parameter obligations.

    Exhausting the coverage budget raises: an incomplete parameter cover cannot
    support this contract. Exhausting a fibre budget retains that entire fibre
    as unresolved. Python results still require independent Lean checking.
    """
    coefficients = _integers(coefficients)
    if len(coefficients) < 2 or type(k) is not int or k == 0:
        raise ValueError('a nonconstant polynomial and nonzero integer k are required')
    Budget(fibre_work_limit)  # Validate even when the parameter set is empty.
    budget = Budget(parameter_work_limit)
    parameters = set()
    for u in signed_divisors(k, budget):
        v = k//u
        if (v-u) % 2 == 0 and (v+u) % 2 == 0:
            parameters.add(((v-u)//2, (v+u)//2))
    roots, unresolved = {}, set()
    for p in sorted({p for p, _ in parameters}):
        try:
            roots[p] = integer_roots((coefficients[0]-p,) + coefficients[1:],
                                     Budget(fibre_work_limit))
        except WorkLimit:
            unresolved.add(p)
    solved = sorted((p, y) for p, y in parameters if p not in unresolved)
    residual = sorted((p, y) for p, y in parameters if p in unresolved)
    fibres = [{'parameter': (p, y), 'points': [(x, y) for x in roots[p]],
               'cardinality': len(roots[p])} for p, y in solved]
    known = sorted({point for fibre in fibres for point in fibre['points']})
    return {'coefficients': list(coefficients), 'k': k,
            'parameters': sorted(parameters), 'solved_parameters': solved,
            'residual_parameters': residual, 'fibres': fibres, 'known_points': known,
            'known_cardinality': len(known), 'complete': not residual,
            'status': 'PARTIAL' if residual else 'COMPLETE',
            'execution_verified': False,
            'contract': 'PerfectPower.NativeSquareChart.chart'}


def emit_lean(coefficients, k, name='divisor_solution'):
    """Emit a native command; its point list is independently kernel checked."""
    import re
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name):
        raise ValueError('a simple Lean identifier is required')
    coefficients = _integers(coefficients)
    if len(coefficients) < 2 or type(k) is not int or k == 0:
        raise ValueError('a nonconstant polynomial and nonzero integer k are required')
    return ('import PerfectPower.Tactic.NativePolynomialPower\n\n'
            f'native_polynomial_square {name} for {list(coefficients)}, {k}\n'
            f'#print axioms {name}_complete\n')
