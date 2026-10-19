"""Exact divisor-sum arithmetic and finite square-class joins.

Completeness always names its domain. A bounded sigma census is not a global
classification. Quartic bounds use the separate Lean-proved solver family;
Python execution itself is not a Lean proof.
"""
from math import gcd, isqrt


def _nat(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')


def geometric_sum(base, exponent):
    _nat(base, 'base'); _nat(exponent, 'exponent')
    # Horner avoids division and includes base=0 and base=1.
    answer = 1
    for _ in range(exponent):
        answer = base * answer + 1
    return answer


def sigma_sieve(limit):
    """Linear sieve: sigma[n] for every 1 <= n <= limit, sigma[0]=0."""
    _nat(limit, 'limit')
    sigma = [0] * (limit + 1)
    least = [0] * (limit + 1)
    prime_power = [0] * (limit + 1)
    prime_sum = [0] * (limit + 1)
    primes = []
    if limit:
        sigma[1] = prime_power[1] = prime_sum[1] = 1
    for n in range(2, limit + 1):
        if not least[n]:
            least[n] = n; primes.append(n)
            prime_power[n] = n; prime_sum[n] = sigma[n] = n + 1
        for p in primes:
            t = n * p
            if t > limit:
                break
            least[t] = p
            if p == least[n]:
                prime_power[t] = prime_power[n] * p
                prime_sum[t] = prime_sum[n] + prime_power[t]
                sigma[t] = sigma[n // prime_power[n]] * prime_sum[t]
                break
            prime_power[t] = p; prime_sum[t] = p + 1
            sigma[t] = sigma[n] * (p + 1)
    return sigma, primes


def exact_root(value, degree):
    """Return the nonnegative integer root, or None. No floating arithmetic."""
    _nat(value, 'value'); _nat(degree, 'degree', 2)
    if degree == 2:
        root = isqrt(value)
        return root if root * root == value else None
    if value < 2:
        return value
    lo, hi = 0, 1 << ((value.bit_length() + degree - 1) // degree)
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if mid ** degree <= value:
            lo = mid
        else:
            hi = mid
    return lo if lo ** degree == value else (hi if hi ** degree == value else None)


def square_product_witness(a, b):
    """For positive a,b, ab is square iff a/g and b/g are squares.

    Coprimality after division by gcd proves the reverse implication. Return
    the gcd and both quotient roots, making every successful join replayable.
    """
    _nat(a, 'a', 1); _nat(b, 'b', 1)
    g = gcd(a, b)
    u, v = isqrt(a // g), isqrt(b // g)
    if u*u != a//g or v*v != b//g:
        return None
    return {'gcd': g, 'left_root': u, 'right_root': v, 'product_root': g*u*v}


def prime_power_rows(prime_limit=1000, max_exponent=8):
    _nat(prime_limit, 'prime_limit', 2); _nat(max_exponent, 'max_exponent', 1)
    _, primes = sigma_sieve(prime_limit)
    return [{'prime': p, 'exponent': a, 'n': p**a,
             'sigma': geometric_sum(p, a)}
            for p in primes for a in range(1, max_exponent + 1)]


def square_classes(rows):
    """Partition supplied positive sigma values modulo rational squares.

    No integer factorization is required: membership is checked using gcd and
    two exact square roots. Class labels refer to supplied representatives,
    rather than pretending to be canonical squarefree kernels.
    """
    classes = []
    for index, row in enumerate(rows):
        _nat(row['sigma'], 'sigma', 1)
        for group in classes:
            witness = square_product_witness(row['sigma'], rows[group[0]]['sigma'])
            if witness is not None:
                group.append(index)
                break
        else:
            classes.append([index])
    return classes


def prime_pair_squares(rows):
    """All p^a q^b in the supplied grid with p<q and square divisor sum."""
    groups = square_classes(rows)
    answers = []
    for group in groups:
        for position, i in enumerate(group):
            for j in group[position+1:]:
                left, right = rows[i], rows[j]
                if left['prime'] == right['prime']:
                    continue  # multiplicativity requires different prime bases
                if left['prime'] > right['prime']:
                    left, right = right, left
                witness = square_product_witness(left['sigma'], right['sigma'])
                if witness is None:
                    raise AssertionError('square class equivalence violated')
                answers.append({'p': left['prime'], 'a': left['exponent'],
                                'q': right['prime'], 'b': right['exponent'],
                                'n': left['n']*right['n'],
                                'sigma': left['sigma']*right['sigma'],
                                'root': witness['product_root'], 'join': witness,
                                'both_factors_square': exact_root(left['sigma'],2) is not None
                                    and exact_root(right['sigma'],2) is not None})
    answers.sort(key=lambda r: (r['p'],r['a'],r['q'],r['b']))
    return groups, answers


def sigma_from_factorization(factors):
    """Evaluate a supplied prime factorization, rejecting composite bases.

    Trial primality checks are deliberately budgeted: unsupported large bases
    raise an error rather than silently trusting the caller's prime claim.
    """
    n = answer = 1
    seen = set()
    for p,a in factors:
        _nat(p,'prime',2); _nat(a,'exponent',1)
        if p in seen:raise ValueError('duplicate prime base')
        if isqrt(p)>1_000_000:raise ValueError('prime validation exceeds trial budget')
        if any(p%d==0 for d in range(2,isqrt(p)+1)):
            raise ValueError('factorization base is composite')
        seen.add(p); n*=p**a; answer*=geometric_sum(p,a)
    return {'n':n,'sigma':answer,'execution_verified':False}


def repunit_quartic(shift=0):
    """All integer points of 1+x+x^2+x^3+x^4+shift=y^2."""
    if type(shift) is not int:raise ValueError('integer shift required')
    from .linear_perturbation import solve_square_leading
    result=solve_square_leading(1,1,1,1,1+shift)
    _,primes=sigma_sieve(result['coordinate_bound'])
    prime_set=set(primes)
    positive=sorted({x for x,y in result['points'] if x>0})
    return {**result,'shift':shift,'positive_inputs':positive,
            'prime_inputs':[x for x in positive if x in prime_set],
            'interpretation':'sigma(p^4)+shift is a square for exactly these prime inputs'}
