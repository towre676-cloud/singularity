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


def regularized_tail_constant(vertex_count, first_depth, delta, radius):
    """The constant C of (7.12) for |log((1-t^r)^delta L_G/L_H)| <= C t^(r+1).

    Valid for 0 <= t <= radius < 1 under the hypotheses of SNG-A11 at a fixed
    q in [0,1]: equal orders, equal coefficients below r, discrepancy delta at
    r.  With A_n = C(n+k-1, k-1),
        D = ((1-rho)^(-k) - 1) / rho,
        T = 2 rho^(-(r+1)) ((1-rho)^(-k) - sum_{n<=r} A_n rho^n),
        C = T + |delta| D + |delta| rho^(r-1) / (2 (1 - rho^r)).
    Unlike ``normalized_ratio_tail_constant`` it needs no condition U < 1.
    This routine does not check the hypotheses; ``certified_tail_record`` does.
    """
    if type(vertex_count) is not int or vertex_count < 1 or type(first_depth) is not int or first_depth < 1:
        raise ValueError("positive integer graph order and depth required")
    radius = Fraction(radius); delta = Fraction(delta)
    if not 0 < radius < 1:
        raise ValueError("radius must lie strictly between zero and one")
    from math import comb
    k, r = vertex_count, first_depth
    whole = (1 - radius) ** (-k)
    head = sum(comb(n + k - 1, k - 1) * radius ** n for n in range(r + 1))
    d_constant = (whole - 1) / radius
    t_constant = 2 * (whole - head) / radius ** (r + 1)
    return t_constant + abs(delta) * d_constant + abs(delta) * radius ** (r - 1) / (2 * (1 - radius ** r))


def regularized_prime_tail_bound(constant, first_depth, s_numerator, s_denominator, cutoff_root, radius):
    """Bound C P^(1-(r+1)s) / ((r+1)s - 1) on the omitted primes p > P (7.13).

    The cutoff is P = N^b for s = a/b, so every power is an exact rational.
    Requires (r+1)s > 1 and the radius condition P^(-s) = N^(-a) <= radius,
    which places every omitted prime inside the certified local disc; the
    primes p <= P are kept exactly in the finite product.  At s = 1/r this is
    C r / N, the bound of ``boundary_prime_tail_bound``.
    """
    for value, name in ((first_depth, "depth"), (s_numerator, "s numerator"), (s_denominator, "s denominator"), (cutoff_root, "cutoff root")):
        if type(value) is not int or value < 1:
            raise ValueError(f"positive integer {name} required")
    constant, radius = Fraction(constant), Fraction(radius)
    if constant < 0:
        raise ValueError("tail constant must be nonnegative")
    s = Fraction(s_numerator, s_denominator)
    excess = (first_depth + 1) * s - 1
    if excess <= 0:
        raise ValueError("the regularized tail needs (r+1)s > 1")
    if Fraction(1, cutoff_root ** s_numerator) > radius:
        raise ValueError("cutoff too small: omitted primes would leave the certified radius")
    exponent = s_denominator - (first_depth + 1) * s_numerator  # log_N of P^(1-(r+1)s)
    return constant * Fraction(cutoff_root) ** exponent / excess


def certified_tail_record(left_coefficients, right_coefficients, vertex_count, q, radius, s_numerator, s_denominator, cutoff_root):
    """Bind the tail bound to an exactly recomputed first discrepancy at q.

    The caller supplies both local coefficient prefixes; the first volume r
    with a nonzero value at q, and delta, are recomputed here.  If the
    prefixes agree at q through their common length, no record is produced.
    """
    from .euler import first_difference_at_q
    q = Fraction(q)
    if not 0 <= q <= 1:
        raise ValueError("q must lie in [0,1]")
    found = first_difference_at_q(left_coefficients, right_coefficients, q)
    if found is None:
        raise ValueError("no first discrepancy within the supplied prefixes at this q")
    depth, delta = found
    if depth < 1:
        raise ValueError("graphs of equal order agree at volume zero; check the inputs")
    constant = regularized_tail_constant(vertex_count, depth, delta, radius)
    tail = regularized_prime_tail_bound(constant, depth, s_numerator, s_denominator, cutoff_root, radius)
    text = lambda value: f"{value.numerator}/{value.denominator}"
    return {
        "schema": "singularity.tail-record/1", "theorem": "SNG-A14 with constant (7.12)",
        "vertex_count": vertex_count, "q": text(q), "first_depth": depth, "delta": text(delta),
        "radius": text(Fraction(radius)), "s": text(Fraction(s_numerator, s_denominator)),
        "cutoff": f"{cutoff_root}^{s_denominator}", "local_constant": text(constant), "tail_bound": text(tail),
        "hypotheses": [
            "equal vertex counts (supplied, not checked against graphs)",
            "coefficients at q agree below first_depth (recomputed from the supplied prefixes)",
            "local inequality for 0 <= t <= radius on the real branch, q in [0,1]",
            "omitted primes p > cutoff satisfy p^(-s) <= radius; primes up to the cutoff are kept exactly",
            "(r+1)s > 1",
        ],
    }
