"""Original-equation bounded answers checked by a small standalone Lean library.

The emitted theorem includes both coordinate bounds. No global height bound,
Python enumeration, supplied analytic premise, or Mathlib build is trusted.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

from .divisor_square import WorkLimit
from .resources import runtime_root


def _integer(value, name):
    if type(value) is not int or abs(value).bit_length() > 128:
        raise ValueError(name + ' must be an integer of at most 128 bits')
    return value


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def box_certificate(coefficients, exponent, x_bounds, y_bounds=None, *,
                    ranks=None, objective=None, work_limit=4096):
    """Emit a complete list, exact count, selections and optional x-objective minimum.

    A packet is an unaccepted proposal until check_box compiles its reconstructed
    original-equation theorem. Reversed bounds denote the empty rectangle.
    """
    if not isinstance(coefficients, (list, tuple)) or not 1 <= len(coefficients) <= 33:
        raise ValueError('one through 33 integer coefficients required')
    cs = [_integer(c, 'coefficient') for c in coefficients]
    if type(exponent) is not int or not 2 <= exponent <= 16:
        raise ValueError('exponent must be between 2 and 16')
    bounds = []
    automatic=y_bounds is None
    if automatic:y_bounds=[0,0]
    for name, pair in [('x_bounds', x_bounds), ('y_bounds', y_bounds)]:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(name + ' must contain two integer endpoints')
        bounds.append([_integer(v, name) for v in pair])
    (xl, xu), (yl, yu) = bounds
    if type(work_limit) is not int or not 1 <= work_limit <= 65536:
        raise ValueError('work_limit must be between 1 and 65536')
    if max(0,xu-xl+1)>work_limit:raise WorkLimit('x interval exceeds certificate work budget')

    def evaluate(poly, x):
        v = 0
        for c in reversed(poly):
            v = c + x*v
        return v

    # Bound reduction cost, even for an empty rectangle with huge endpoints.
    size = max(abs(xl), abs(xu), 1)
    if sum(abs(c) * size**i for i, c in enumerate(cs)).bit_length() > 4096:
        raise WorkLimit('polynomial evaluation exceeds 4096-bit budget')
    maximum=0;cap=0
    if automatic:
        maximum=max((abs(evaluate(cs,x)) for x in range(xl,xu+1)),default=0)
        low,high=0,1 << ((maximum.bit_length()+exponent-1)//exponent)
        while low+1<high:
            mid=(low+high)//2
            if mid**exponent<=maximum:low=mid
            else:high=mid
        cap=low
        yl,yu=-cap,cap;bounds[1]=[yl,yu]
    if max(0,xu-xl+1)*max(0,yu-yl+1)>work_limit:
        raise WorkLimit('rectangle exceeds certificate work budget')
    points = [[x, y] for x in range(xl, xu+1) for y in range(yl, yu+1)
              if y**exponent == evaluate(cs, x)] if yl <= yu else []
    ranks = [] if ranks is None else ranks
    if not isinstance(ranks, list) or len(ranks) > 64 or any(
            type(i) is not int or not 0 <= i < len(points) for i in ranks):
        raise ValueError('at most 64 valid selection ranks required')
    if objective is not None:
        if not isinstance(objective, list) or not 1 <= len(objective) <= 33:
            raise ValueError('objective must be a polynomial in x')
        objective = [_integer(c, 'objective coefficient') for c in objective]
    spec = dict(coefficients=cs, exponent=exponent, x_bounds=bounds[0],
                y_bounds=None if automatic else bounds[1], ranks=ranks, objective=objective, work_limit=work_limit)
    tag = _hash(spec)[:16]
    namespace = 'PerfectPower.CheckedBox_' + tag
    literal = '[' + ','.join(f'(({x}),({y}))' for x,y in points) + ']'
    args = f'{cs} {exponent} ({xl}) ({xu}) ({yl}) ({yu})'
    source = f'''import PerfectPower.BoundedNative
namespace {namespace}
open PerfectPower.BoundedNative
def answer : List (Int × Int) := {literal}
theorem literal_checked : solutions {args} = answer := by decide +kernel
theorem original_complete (x y : Int) :
    (x,y) ∈ answer ↔ ({xl}) ≤ x ∧ x ≤ ({xu}) ∧ ({yl}) ≤ y ∧ y ≤ ({yu}) ∧
      y ^ {exponent} = horner {cs} x :=
  literal_complete {args} answer literal_checked x y
theorem count_checked : (solutions {args}).length = {len(points)} := by decide +kernel
'''
    if automatic:
        source += f'''theorem value_bound_checked :
    ((interval ({xl}) ({xu})).all fun x => decide ((horner {cs} x).natAbs ≤ {maximum})) = true :=
  by decide +kernel
theorem complete_all_integer_y (x y : Int) :
    (x,y) ∈ answer ↔ ({xl}) ≤ x ∧ x ≤ ({xu}) ∧ y ^ {exponent} = horner {cs} x :=
  bounded_source_complete {cs} {exponent} ({xl}) ({xu}) {maximum} {cap}
    value_bound_checked (by decide +kernel) answer literal_checked x y
'''
    for j, i in enumerate(ranks):
        x,y = points[i]
        source += f'''theorem selection_{j} : (solutions {args})[{i}]? =
    some (({x}),({y})) := by decide +kernel
theorem reverse_rank_{j} : ((solutions {args}).take {i}).contains (({x}),({y})) =
    false := by decide +kernel
'''
    minimum = None
    if objective is not None and points:
        value = min(evaluate(objective, x) for x,y in points)
        minimizers = [p for p in points if evaluate(objective,p[0]) == value]
        minimum = dict(value=value, points=minimizers)
        # Reduction proves universal finite minimality; includes every tie.
        source += f'''theorem lower_bound_checked :
    (answer.all fun p => decide (({value}) ≤ horner {objective} p.1)) = true :=
  by decide +kernel
theorem minimizers_checked :
    answer.filter (fun p => decide (horner {objective} p.1 = ({value}))) =
      {str([tuple(p) for p in minimizers])} := by decide +kernel
'''
        statement=(f'({xl}) ≤ x ∧ x ≤ ({xu}) ∧ y ^ {exponent} = horner {cs} x'
            if automatic else f'({xl}) ≤ x ∧ x ≤ ({xu}) ∧ ({yl}) ≤ y ∧ y ≤ ({yu}) ∧ y ^ {exponent} = horner {cs} x')
        theorem='complete_all_integer_y' if automatic else 'original_complete'
        source += f'''theorem minimum_original (x y : Int) (h : {statement}) :
    ({value}) ≤ horner {objective} x := by
  have hp := ({theorem} x y).mpr h
  exact of_decide_eq_true (List.all_eq_true.mp lower_bound_checked (x,y) hp)
theorem minimizers_original (x y : Int) :
    (x,y) ∈ ({str([tuple(p) for p in minimizers])} : List (Int × Int)) ↔
      ({statement}) ∧ horner {objective} x = ({value}) := by
  rw [← minimizers_checked]
  simp only [List.mem_filter, decide_eq_true_eq, {theorem}]
'''
    source += f'''end {namespace}
#print axioms {namespace}.original_complete
#print axioms {namespace}.literal_checked
#print axioms {namespace}.count_checked
'''
    if automatic:source+=f'#print axioms {namespace}.complete_all_integer_y\n'
    if minimum is not None:source+=f'#print axioms {namespace}.minimum_original\n#print axioms {namespace}.minimizers_original\n'
    return dict(schema='pp-checked-box/1', specification=spec, resolved_y_bounds=bounds[1], points=points,
                count=len(points), selections=[dict(rank=i,point=points[i]) for i in ranks],
                minimum=minimum, lean=source, namespace=namespace,
                specification_sha256=_hash(spec), source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                proof_status='emitted', execution_verified=False,
                scope='complete for bounded x and all integer y' if automatic else
                      'complete only within the explicit integer rectangle')


def check_box(packet, *, lean=None, timeout=30):
    """Reconstruct then kernel-check; reject mutations and never trust supplied Lean.

    Toolchain execution is external. A successful receipt binds the reconstructed
    source, original specification and generic library; it does not verify JSON parsing.
    """
    if type(timeout) not in (int,float) or not 0 < timeout <= 600:
        raise ValueError('timeout must be positive and at most 600 seconds')
    try:
        expected = box_certificate(**packet['specification'])
    except (KeyError, TypeError, ValueError, WorkLimit) as error:
        return dict(accepted=False, reason='invalid specification: '+str(error))
    if packet != expected:
        return dict(accepted=False, reason='packet differs from reconstructed original query')
    binary = lean or os.environ.get('PERFECTPOWER_LEAN') or shutil.which('lean')
    if not binary:
        return dict(accepted=False, reason='Lean 4.20.0 unavailable; proposal remains unaccepted')
    library = runtime_root() / 'PerfectPower/BoundedNative.lean'
    if not library.is_file():
        return dict(accepted=False, reason='bounded kernel library unavailable')
    try:
        version = subprocess.run([binary,'--version'], capture_output=True,text=True,
                                 timeout=timeout,check=True).stdout.strip()
        if not version.startswith('Lean (version 4.20.0,'):
            return dict(accepted=False, reason='Lean 4.20.0 required', version=version)
        with tempfile.TemporaryDirectory(prefix='pp-checked-box-') as directory:
            root = Path(directory); (root/'PerfectPower').mkdir()
            generic = root/'PerfectPower/BoundedNative.lean'
            generic.write_bytes(library.read_bytes())
            query = root/'Query.lean';query.write_text(expected['lean'],encoding='utf-8')
            environment = dict(os.environ, LEAN_PATH=str(root))
            commands = [[binary,str(generic),'-o',str(generic.with_suffix('.olean'))],
                        [binary,str(query)]]
            logs=[]
            for command in commands:
                run = subprocess.run(command,cwd=root,env=environment,capture_output=True,
                                     text=True,timeout=timeout)
                log=run.stdout+run.stderr;logs.append(log)
                axioms=[a.strip() for group in re.findall(r'depends on axioms: \[([^\]]*)\]',log)
                        for a in group.split(',') if a.strip()]
                if run.returncode or 'sorry' in log or 'ofReduceBool' in log or any(
                        a not in {'propext','Classical.choice','Quot.sound'} for a in axioms):
                    return dict(accepted=False, reason='kernel rejected query',log=log[-12000:])
        return dict(accepted=True, proof_status='kernel_checked',
            execution_verified=False, scope=expected['scope'], version=version,
            specification_sha256=expected['specification_sha256'],
            source_sha256=expected['source_sha256'],
            library_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
            log=''.join(logs))
    except (OSError,subprocess.SubprocessError) as error:
        return dict(accepted=False,reason='kernel execution failed: '+str(error))


def add_commands(sub):
    p=sub.add_parser('checked-box',help='complete bounded original-equation Lean certificate')
    p.add_argument('--coeff',required=True,type=json.loads)
    p.add_argument('--d',required=True,type=int)
    p.add_argument('--x',required=True,type=json.loads,help='[lower,upper] integer x bounds')
    p.add_argument('--y',type=json.loads,help='optional [lower,upper]; omitted means all integer y')
    p.add_argument('--ranks',type=json.loads,default=[])
    p.add_argument('--objective',type=json.loads)
    p.add_argument('--work-limit',type=int,default=4096)
    p.add_argument('--check',action='store_true',help='require successful Lean kernel acceptance')


def cli(args):
    if args.command!='checked-box':return False
    packet=box_certificate(args.coeff,args.d,args.x,args.y,ranks=args.ranks,
                           objective=args.objective,work_limit=args.work_limit)
    result=dict(packet=packet)
    if args.check:
        result['acceptance']=check_box(packet)
        print(json.dumps(result,sort_keys=True))
        if not result['acceptance']['accepted']:raise SystemExit(1)
    else:print(json.dumps(result,sort_keys=True))
    return True
