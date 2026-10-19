"""Finite modular exclusion proposals for primitive quartic points.

Adapts Morphonic's two projective charts, with the nonunit chart evaluated at
p*u, not merely given a witness scale p. No p-adic or global solubility verdict
is inferred from a surviving residue. Exclusions can be emitted to Lean.
"""
from math import isqrt


def _prime(p):
    return type(p) is int and p >= 2 and all(p % d for d in range(2, isqrt(p)+1))


def primitive_residue_certificate(d, A, c, p, *, max_work=1_000_000):
    if any(type(a) is not int for a in (d, A, c, p)) or p < 2:
        raise ValueError('integer coefficients and a prime modulus are required')
    if type(max_work) is not int or max_work < 1 or p*p > max_work:
        raise ValueError('residue work budget exceeded; no certificate returned')
    if not _prime(p):
        raise ValueError('a prime modulus is required')
    squares = {z*z % p for z in range(p)}
    surviving = [(x, e) for x in range(p) for e in range(p)
                 if (x or e) and (d*x**4 + A*x*x*e*e + c*e**4) % p in squares]
    return {'d': d, 'A': A, 'c': c, 'prime': p, 'obstructed': not surviving,
            'surviving_residues': surviving, 'execution_verified': False,
            'scope': 'primitive integer points; surviving residues are unresolved',
            'theorem': 'PerfectPower.LocalQuarticObstruction.no_primitive_point'}


def chart_polynomials(d, A, c, p):
    if any(type(a) is not int for a in (d, A, c)) or not _prime(p):
        raise ValueError('a prime is required')
    return (c, 0, A, 0, d), (d, 0, A*p*p, 0, c*p**4)


def emit_lean(cert, name='quartic_obstruction'):
    import re
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name):
        raise ValueError('a simple Lean identifier is required')
    actual = primitive_residue_certificate(cert['d'], cert['A'], cert['c'], cert['prime'])
    if not actual['obstructed']:
        raise ValueError('the proposed obstruction is false')
    p, d, A, c = (actual[k] for k in ('prime', 'd', 'A', 'c'))
    return ('import PerfectPower.LocalQuarticObstruction\n\n'
            f'theorem {name} : PerfectPower.LocalQuarticObstruction.obstructed '
            f'{p} ({d}) ({A}) ({c}) := by decide +kernel\n'
            f'#print axioms {name}\n')
