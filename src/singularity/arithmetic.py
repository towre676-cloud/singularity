"""Prime-valuation assembly and conservative exact Euler-tail constants."""
from fractions import Fraction
from collections import Counter


def prime_valuations(n):
    if type(n) is not int or n < 1:
        raise ValueError("a positive integer is required")
    result = {}; prime = 2
    while prime * prime <= n:
        if n % prime == 0:
            exponent = 0
            while n % prime == 0:
                n //= prime; exponent += 1
            result[prime] = exponent
        prime = 3 if prime == 2 else prime + 2
    if n > 1:
        result[n] = 1
    return result


def valuation_energy(graph, integers):
    if len(integers) != graph.n:
        raise ValueError("one integer per graph vertex is required")
    valuations = [prime_valuations(n) for n in integers]
    primes = set().union(*(v.keys() for v in valuations))
    return sum(graph.energy(tuple(v.get(p, 0) for v in valuations)) for p in primes)


def dirichlet_coefficients(graph, bound):
    """Return {n: {q_energy: integer_count}} for product n <= bound."""
    if type(bound) is not int or bound < 1:
        raise ValueError("bound must be a positive integer")
    from .heights import local_coefficients
    max_exponent = bound.bit_length() - 1
    local = local_coefficients(graph, max_exponent)
    result = {}
    for n in range(1, bound + 1):
        polynomial = {0: 1}
        for exponent in prime_valuations(n).values():
            out = Counter()
            for a, multiplicity in polynomial.items():
                for b, count in local[exponent].items():
                    out[a + b] += multiplicity * count
            polynomial = dict(sorted(out.items()))
        result[n] = polynomial
    return result


def normalized_ratio_tail_constant(vertex_count, first_depth, delta, radius):
    """Conservative exact C for |log normalized local ratio| <= C*x^(r+1).

    Requires equal graph orders, lower-coefficient cancellation through r-1,
    and the declared first discrepancy delta at the selected q in [0,1].
    This routine certifies the universal majorant, not those hypotheses.
    The inequality is for 0 <= x <= radius on the real logarithm branch.
    If U=(1-radius)^(-k)-1<1, the coefficient l1 norm of log(L) at
    radius is at most U/(1-U). Add the two local log bounds and the
    extracted factor's bound, then use cancellation through degree r.
    """
    if type(vertex_count) is not int or vertex_count < 1 or type(first_depth) is not int or first_depth < 1:
        raise ValueError("positive integer graph order and depth required")
    radius = Fraction(radius); delta = Fraction(delta)
    if not 0 < radius < 1:
        raise ValueError("radius must lie strictly between zero and one")
    majorant = (1 - radius) ** (-vertex_count) - 1
    if majorant >= 1:
        raise ValueError("radius too large: local logarithm majorant must be below one")
    absolute_log_bound = 2 * majorant / (1 - majorant)
    absolute_log_bound += abs(delta) * radius**first_depth / (1 - radius**first_depth)
    return absolute_log_bound / radius ** (first_depth + 1)


def boundary_prime_tail_bound(first_depth, cutoff_root, constant):
    """At s=1/r and P=N^r, bound omitted normalized log tail by C*r/N.

    Valid when every omitted prime has p^(-1/r) in the radius certified by
    normalized_ratio_tail_constant. Primes are bounded by all integers and
    then by an integral. The returned value is exact and can be quite loose.
    """
    if type(first_depth) is not int or first_depth < 1 or type(cutoff_root) is not int or cutoff_root < 1:
        raise ValueError("positive integer depth and cutoff root required")
    constant = Fraction(constant)
    if constant < 0:
        raise ValueError("tail constant must be nonnegative")
    return constant * first_depth / cutoff_root
