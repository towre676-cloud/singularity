"""Finite rational-cell proofs of universal factorial-ratio integrality."""
from fractions import Fraction
import hashlib
import json

from .checked_factorial_unit import _check_source
from .gamma_arithmetic import landau
from .divisor_square import WorkLimit


def _rational(value):
    q = Fraction(value)
    return f'(({q.numerator} : ℚ)/{q.denominator})'


def landau_certificate(numerator, denominator, *, work_limit=4096):
    if type(work_limit) is not int or not 1 <= work_limit <= 32768:
        raise ValueError('certificate work_limit must be in [1,32768]')
    arithmetic = json.loads(json.dumps(landau(numerator, denominator, work_limit=work_limit)))
    if not arithmetic['integral_for_all_n']:
        raise ValueError('nonnegative balanced floor-step function required')
    a, b = arithmetic['numerator'], arithmetic['denominator']
    slopes = sorted(set(a+b))
    intervals = arithmetic['intervals']
    if len(intervals)*max(1, len(slopes)) > work_limit:
        raise WorkLimit('rational-cell proof exceeds certificate budget')
    spec = dict(numerator=a, denominator=b, work_limit=work_limit)
    digest = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    name = 'PerfectPower.CheckedLandau_' + digest[:16]
    source = f'''import PerfectPower.LandauIntegral
import Mathlib.Tactic.NormNum
set_option maxRecDepth 16384
set_option maxHeartbeats 4000000
namespace {name}
open PerfectPower.LandauIntegral
'''
    for j, row in enumerate(intervals):
        left, right = Fraction(row['left']), Fraction(row['right'])
        source += f'''private theorem cell_{j} (x : ℚ)
    (hl : {_rational(left)} ≤ x) (hr : x < {_rational(right)}) :
    0 ≤ delta {a} {b} x := by
'''
        for c in slopes:
            value = (c*left).numerator // (c*left).denominator
            source += f'''  have f_{c} : ⌊({c} : ℚ)*x⌋ = ({value} : ℤ) := by
    apply Int.floor_eq_iff.mpr
    constructor <;> norm_num at * <;> linarith
'''
        if 1 in slopes:
            source += '  simp only [one_mul] at f_1\n'
        rules = ', '.join('f_'+str(c) for c in slopes)
        source += ('  simp only [delta, floorSum, List.map_cons, List.map_nil, '
                   'List.sum_cons, List.sum_nil, Nat.cast_ofNat, Nat.cast_one, one_mul' + (', '+rules if rules else '') + ']\n  norm_num\n')
    source += f'''theorem cells_complete (x : ℚ) (hl : 0 ≤ x) (hr : x < 1) :
    0 ≤ delta {a} {b} x := by
'''
    previous = '(by simpa using hl)'
    for j, row in enumerate(intervals):
        if j == len(intervals)-1:
            source += f'  exact cell_{j} x {previous} (by simpa using hr)\n'
        else:
            source += f'''  by_cases h_{j} : x < {_rational(row['right'])}
  · exact cell_{j} x {previous} h_{j}
  have l_{j} : {_rational(row['right'])} ≤ x := le_of_not_gt h_{j}
'''
            previous = 'l_'+str(j)
    source += f'''theorem all_rational_steps (x : ℚ) : 0 ≤ delta {a} {b} x :=
  nonnegative_of_cells {a} {b} (by decide +kernel) cells_complete x
theorem original_integral_for_all_indices (n : ℕ) :
    factorialProduct {b} n ∣ factorialProduct {a} n :=
  integral_of_nonnegative {a} {b} all_rational_steps n
end {name}
#print axioms {name}.cells_complete
#print axioms {name}.all_rational_steps
#print axioms {name}.original_integral_for_all_indices
'''
    return dict(schema='pp-checked-landau/1', specification=spec, arithmetic=arithmetic,
                lean=source, namespace=name, specification_sha256=digest,
                source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                proof_status='emitted', execution_verified=False,
                scope='original balanced factorial ratio is integral for every natural index')


def check_landau(packet, *, lean=None, lean_path=None, timeout=60):
    if type(timeout) not in (int, float) or not 0 < timeout <= 600:
        raise ValueError('timeout must be positive and at most 600 seconds')
    try:
        expected = landau_certificate(**packet['specification'])
    except (KeyError, TypeError, ValueError, WorkLimit) as error:
        return dict(accepted=False, reason='invalid specification: '+str(error))
    if packet != expected:
        return dict(accepted=False, reason='packet differs from reconstructed original query')
    return _check_source(expected, 'LandauIntegral', 3, lean=lean,
                         lean_path=lean_path, timeout=timeout)


def add_commands(sub):
    p = sub.add_parser('checked-landau', help='universal original factorial integrality proof')
    p.add_argument('--numerator', type=json.loads, required=True)
    p.add_argument('--denominator', type=json.loads, required=True)
    p.add_argument('--work-limit', type=int, default=4096)
    p.add_argument('--check', action='store_true')


def cli(args):
    if args.command != 'checked-landau':
        return False
    packet = landau_certificate(args.numerator, args.denominator, work_limit=args.work_limit)
    output = dict(packet=packet)
    if args.check:
        output['acceptance'] = check_landau(packet)
    print(json.dumps(output, sort_keys=True))
    if args.check and not output['acceptance']['accepted']:
        raise SystemExit(1)
    return True
