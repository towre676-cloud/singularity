"""Complete bounded smooth residue patches with exact first Hensel lifts.

Input polynomial: sparse terms [integer coefficient, x exponent, y exponent].
Every returned point satisfies the source equation; completeness is relative
to the declared closed rectangle and prime residue class, never a height bound.
"""
from math import comb, gcd
import hashlib
import json
from .residue_determinant import auxiliary_packet, integer, verify_auxiliary


def terms_checked(terms):
    if not isinstance(terms, list) or not 1 <= len(terms) <= 24:
        raise ValueError('one through 24 sparse terms required')
    result = {}
    for t in terms:
        if not isinstance(t, list) or len(t) != 3:
            raise ValueError('terms are [coefficient,x exponent,y exponent]')
        c = integer(t[0], 256); i = integer(t[1], 8); j = integer(t[2], 8)
        if i < 0 or j < 0 or i+j > 12:
            raise ValueError('total degree at most twelve required')
        result[i, j] = integer(result.get((i, j), 0)+c, 256)
    return [[c, i, j] for (i, j), c in sorted(result.items()) if c]


def evaluate(terms, x, y):
    return integer(sum(c*x**i*y**j for c, i, j in terms))


def taylor_data(terms, p, a, b):
    expanded = {}
    for c, i, j in terms:
        for k in range(i+1):
            for l in range(j+1):
                value = c*comb(i, k)*comb(j, l)*a**(i-k)*b**(j-l)*p**(k+l)
                expanded[k, l] = integer(expanded.get((k, l), 0)+value)
    f0 = expanded.get((0, 0), 0)
    if f0 % p:
        raise ValueError('base residue is not on the curve modulo the prime')
    dx = expanded.get((1, 0), 0)//p
    dy = expanded.get((0, 1), 0)//p
    if gcd(dy, p) != 1:
        raise ValueError('vertical derivative is not a unit: choose another patch chart')
    remainder = [[v//p**2, k, l] for (k, l), v in sorted(expanded.items())
                 if k+l >= 2 and v]
    return {'constant': f0//p, 'dx': dx, 'dy': dy, 'vertical_inverse': pow(dy, -1, p),
            'remainder_terms': remainder}


def _prime(p):
    p = integer(p, 16)
    if not 2 <= p <= 257 or any(p % d == 0 for d in range(2, int(p**0.5)+1)):
        raise ValueError('prime from two through 257 required')
    return p


def _axis(lo, hi, m, r):
    return list(range(lo+(r-lo) % m, hi+1, m))


def patch_packet(terms, bounds, prime, residue, *, exponents=None):
    terms = terms_checked(terms)
    if not terms:
        raise ValueError('nonzero source polynomial required')
    p = _prime(prime)
    if not isinstance(bounds, list) or len(bounds) != 2 or any(not isinstance(v, list) or len(v) != 2 for v in bounds):
        raise ValueError('bounds are [[xmin,xmax],[ymin,ymax]]')
    bounds = [[integer(v, 64) for v in row] for row in bounds]
    if any(lo > hi or hi-lo > 8192 for lo, hi in bounds):
        raise ValueError('nonempty axes with width at most 8192 required')
    if not isinstance(residue, list) or len(residue) != 2:
        raise ValueError('two residue coordinates required')
    a, b = [integer(v, 64) % p for v in residue]
    taylor = taylor_data(terms, p, a, b)
    xs = _axis(*bounds[0], p, a); ys = _axis(*bounds[1], p, b)
    coarse_count = len(xs)*len(ys)
    if coarse_count > 4096:
        raise ValueError('complete coarse residue grid exceeds 4096-point budget')
    candidates = []
    for x in xs:
        u = (x-a)//p
        v = (-taylor['constant']-taylor['dx']*u)*taylor['vertical_inverse'] % p
        for y in _axis(*bounds[1], p*p, b+p*v):
            candidates.append([x, y])
    points = [z for z in candidates if evaluate(terms, *z) == 0]
    if len(points) > 64:
        raise ValueError('complete solution list exceeds 64-point packet budget')
    if exponents is None:
        exponents = [[0, 0], [1, 0], [0, 1], [2, 0]]
    auxiliary = auxiliary_packet(points, exponents) if points else None
    return {'schema': 'pp-bounded-residue-patch/1', 'terms': terms, 'bounds': bounds,
            'prime': p, 'residue': [a, b], 'taylor': taylor,
            'x_residues': xs, 'y_residues': ys, 'coarse_count': coarse_count,
            'lift_candidates': candidates, 'candidate_count': len(candidates),
            'points': points, 'auxiliary': auxiliary, 'complete_in_box': True,
            'global_height_bound': False, 'execution_verified': False}


def verify_patch(packet):
    """Replay by the full finite residue grid, independently of Hensel discovery."""
    try:
        if packet['schema'] != 'pp-bounded-residue-patch/1':
            return False
        terms = terms_checked(packet['terms'])
        p = _prime(packet['prime']); a, b = packet['residue']
        if type(a) is not int or type(b) is not int or not 0 <= a < p or not 0 <= b < p:
            return False
        if terms != packet['terms'] or taylor_data(terms, p, a, b) != packet['taylor']:
            return False
        bounds = packet['bounds']
        if not isinstance(bounds, list) or len(bounds) != 2 or any(not isinstance(v, list) or len(v) != 2 for v in bounds):
            return False
        for lo, hi in bounds:
            integer(lo, 64); integer(hi, 64)
            if lo > hi or hi-lo > 8192:
                return False
        xs = _axis(*bounds[0], p, a); ys = _axis(*bounds[1], p, b)
        if len(xs)*len(ys) > 4096 or packet['x_residues'] != xs or packet['y_residues'] != ys:
            return False
        candidates = [[x, y] for x in xs for y in ys if evaluate(terms, x, y) % (p*p) == 0]
        points = [z for z in candidates if evaluate(terms, *z) == 0]
        if packet['lift_candidates'] != candidates or packet['points'] != points or len(points) > 64:
            return False
        if integer(packet['coarse_count']) != len(xs)*len(ys) or integer(packet['candidate_count']) != len(candidates):
            return False
        aux = packet['auxiliary']
        if points:
            if aux is None or aux['points'] != points or not verify_auxiliary(aux):
                return False
        elif aux is not None:
            return False
        return (packet['complete_in_box'] is True and packet['global_height_bound'] is False
                and packet['execution_verified'] is False)
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        return False


def formula(terms, x='x', y='y'):
    return ' + '.join(f'({c}) * ({x})^{i} * ({y})^{j}' for c, i, j in terms) or '0'


def _finset(points):
    return ('{' + ', '.join(f'({x},{y})' for x, y in points) + '}') if points else '∅'


def native_patch(packet):
    if not verify_patch(packet):
        raise ValueError('valid complete patch packet required')
    tag = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()[:16]
    ns = 'Patch_' + tag; p = packet['prime']; a, b = packet['residue']
    (x0, x1), (y0, y1) = packet['bounds']; t = packet['taylor']
    # Bezout coefficients, independently kernel-checked below.
    inv = t['vertical_inverse']; quotient = (1-inv*t['dy'])//p
    lines = ['import PerfectPower.BoundedResiduePatch', 'import Mathlib.Tactic',
             'set_option maxRecDepth 100000', 'set_option maxHeartbeats 0',
             f'namespace {ns}', 'open PerfectPower.BoundedResiduePatch',
             f'def F (x y : ℤ) : ℤ := {formula(packet["terms"])}',
             f'def R (u v : ℤ) : ℤ := {formula(t["remainder_terms"], "u", "v")}',
             f'def bounds : (ℤ × ℤ) × (ℤ × ℤ) := (({x0},{x1}),({y0},{y1}))',
             f'def points : Finset (ℤ × ℤ) := {_finset(packet["points"])}',
             f'def candidates : Finset (ℤ × ℤ) := {_finset(packet["lift_candidates"])}',
             f'theorem taylor_identity (u v : ℤ) : F ({a}+{p}*u) ({b}+{p}*v) =',
             f'    {p}*({t["constant"]}+({t["dx"]})*u+({t["dy"]})*v)+{p}^2*R u v := by',
             '  unfold F R; ring',
             f'theorem vertical_unit : IsCoprime ({p} : ℤ) ({t["dy"]} : ℤ) := by',
             f'  refine ⟨{quotient}, {inv}, ?_⟩; decide +kernel',
             f'def taylor : TaylorPacket F {p} {a} {b} :=',
             f'  ⟨{t["constant"]}, {t["dx"]}, {t["dy"]}, R, taylor_identity, vertical_unit⟩',
             f'theorem prime_checked : Nat.Prime {p} := by norm_num',
             f'theorem candidate_list_checked : lifts F bounds {p} {a} {b} = candidates := by decide +kernel',
             f'theorem point_list_checked : solutions F bounds {p} {a} {b} = points := by decide +kernel',
             f'def cover : CoverPacket F bounds {p} {a} {b} := ⟨points, point_list_checked⟩',
             f'theorem complete (x y : ℤ) : (x,y) ∈ points ↔',
             f'    ({x0} ≤ x ∧ x ≤ {x1} ∧ {y0} ≤ y ∧ y ≤ {y1} ∧',
             f'     ({p} : ℤ) ∣ x-{a} ∧ ({p} : ℤ) ∣ y-{b} ∧ F x y = 0) := cover.complete x y',
             '#print axioms taylor_identity', '#print axioms vertical_unit',
             '#print axioms prime_checked', '#print axioms candidate_list_checked',
             '#print axioms point_list_checked', '#print axioms complete']
    if packet['auxiliary']:
        aux = packet['auxiliary']; exps = aux['exponents']; center = aux['center']
        for i, c in enumerate(aux['kernel']['relations']):
            rterms = [[coef, *e] for coef, e in zip(c, exps) if coef]
            expression = formula(rterms, f'x-({center[0]})', f'y-({center[1]})')
            lines += [f'def auxiliary{i} (x y : ℤ) : ℤ := {expression}',
                      f'theorem auxiliary{i}_values : ∀ z ∈ points, auxiliary{i} z.1 z.2 = 0 := by decide +kernel',
                      f'theorem auxiliary{i}_covers (x y : ℤ)',
                      f'    (hx0 : {x0} ≤ x) (hx1 : x ≤ {x1}) (hy0 : {y0} ≤ y) (hy1 : y ≤ {y1})',
                      f'    (hxp : ({p} : ℤ) ∣ x-{a}) (hyp : ({p} : ℤ) ∣ y-{b}) (hF : F x y = 0) :',
                      f'    auxiliary{i} x y = 0 :=',
                      f'  relation_on_box cover auxiliary{i} auxiliary{i}_values x y hx0 hx1 hy0 hy1 hxp hyp hF',
                      f'#print axioms auxiliary{i}_covers']
    else:
        lines += [f'theorem no_solution (x y : ℤ)',
                  f'    (hx0 : {x0} ≤ x) (hx1 : x ≤ {x1}) (hy0 : {y0} ≤ y) (hy1 : y ≤ {y1})',
                  f'    (hxp : ({p} : ℤ) ∣ x-{a}) (hyp : ({p} : ℤ) ∣ y-{b}) : F x y ≠ 0 :=',
                  '  empty_box cover rfl x y hx0 hx1 hy0 hy1 hxp hyp', '#print axioms no_solution']
    lines += [f'end {ns}']
    return '\n'.join(lines)+'\n'
