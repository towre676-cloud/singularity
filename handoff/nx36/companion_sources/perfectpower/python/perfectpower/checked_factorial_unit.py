"""Reconstructed kernel certificates for the original factorial's prime-free unit."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .gamma_arithmetic import factorial_unit
from .divisor_square import WorkLimit
from .resources import runtime_root


def unit_certificate(n, p, depth, *, work_limit=8192):
    if type(work_limit) is not int or not 1 <= work_limit <= 32768:
        raise ValueError('certificate work_limit must be in [1,32768]')
    result = factorial_unit(n, p, depth, work_limit=work_limit)
    modulus = result['modulus']
    if modulus * max(1, len(result['levels'])) > work_limit:
        raise WorkLimit('all residue-block levels exceed certificate budget')
    spec = dict(n=n, p=p, depth=depth, work_limit=work_limit)
    digest = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    name = 'PerfectPower.CheckedUnit_' + digest[:16]
    value = result['unit']
    source = f'''import PerfectPower.FactorialUnit
set_option maxRecDepth 16384
set_option maxHeartbeats 4000000
namespace {name}
open PerfectPower.FactorialUnit
private theorem prime_checked : Nat.Prime {p} := by decide +kernel
theorem computed : algorithm {p} {modulus} {n} =
    ({value} : ZMod {modulus}) := by decide +kernel
theorem original_factorial_unit :
    ((({n} : Nat).factorial / {p}^(({n} : Nat).factorial.factorization {p}) : Nat) : ZMod {modulus}) =
      ({value} : ZMod {modulus}) := by
  exact (prime_power_correct {p} {depth} {n} prime_checked (by decide +kernel)).symm.trans computed
end {name}
#print axioms {name}.computed
#print axioms {name}.original_factorial_unit
'''
    return dict(schema='pp-checked-factorial-unit/1', specification=spec,
                arithmetic=result, lean=source, namespace=name,
                specification_sha256=digest,
                source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                proof_status='emitted', execution_verified=False,
                scope='original factorial with every prime power removed, modulo prime^depth')


def check_unit(packet, *, lean=None, lean_path=None, timeout=60):
    """Compile only reconstructed source. Mathlib is required on LEAN_PATH.

    The arithmetic packet is a proposal until this accepts it. Acceptance does
    not claim formal verification of the Python implementation or JSON parser.
    """
    if type(timeout) not in (int, float) or not 0 < timeout <= 600:
        raise ValueError('timeout must be positive and at most 600 seconds')
    try:
        expected = unit_certificate(**packet['specification'])
    except (KeyError, TypeError, ValueError, WorkLimit) as error:
        return dict(accepted=False, reason='invalid specification: '+str(error))
    if packet != expected:
        return dict(accepted=False, reason='packet differs from reconstructed original query')
    return _check_source(expected, 'FactorialUnit', 2, lean=lean, lean_path=lean_path, timeout=timeout)


def _check_source(expected, module, audits, *, lean=None, lean_path=None, timeout=60):
    """Internal runner: callers must reconstruct and compare their complete packet."""
    binary = lean or os.environ.get('PERFECTPOWER_LEAN') or shutil.which('lean')
    mathlib_path = lean_path if lean_path is not None else os.environ.get('LEAN_PATH', '')
    if not binary or not mathlib_path:
        return dict(accepted=False, reason='Lean 4.20.0 and pinned Mathlib on LEAN_PATH required')
    library = runtime_root()/f'PerfectPower/{module}.lean'
    if not library.is_file():
        return dict(accepted=False, reason='kernel library unavailable: '+module)
    try:
        version = subprocess.run([binary, '--version'], capture_output=True, text=True,
                                 timeout=timeout, check=True).stdout.strip()
        if not version.startswith('Lean (version 4.20.0,'):
            return dict(accepted=False, reason='Lean 4.20.0 required', version=version)
        with tempfile.TemporaryDirectory(prefix='pp-checked-unit-') as directory:
            root = Path(directory); (root/'PerfectPower').mkdir()
            generic = root/f'PerfectPower/{module}.lean'
            generic.write_bytes(library.read_bytes())
            query = root/'Query.lean'; query.write_text(expected['lean'], encoding='utf-8')
            environment = dict(os.environ, LEAN_PATH=str(root)+os.pathsep+mathlib_path)
            logs = []
            for command in [[binary, str(generic), '-o', str(generic.with_suffix('.olean'))],
                            [binary, str(query)]]:
                run = subprocess.run(command, cwd=root, env=environment, capture_output=True,
                                     text=True, timeout=timeout)
                log = run.stdout+run.stderr; logs.append(log)
                axioms = [a.strip() for group in re.findall(r'depends on axioms: \[([^\]]*)\]', log)
                          for a in group.split(',') if a.strip()]
                if run.returncode or 'sorry' in log or 'ofReduceBool' in log or any(
                        a not in {'propext', 'Classical.choice', 'Quot.sound'} for a in axioms):
                    return dict(accepted=False, reason='kernel rejected query', log=log[-12000:])
            if ''.join(logs).count('depends on axioms:') != audits:
                return dict(accepted=False, reason='required theorem audit missing')
        return dict(accepted=True, proof_status='kernel_checked', execution_verified=False,
                    scope=expected['scope'], version=version,
                    specification_sha256=expected['specification_sha256'],
                    source_sha256=expected['source_sha256'],
                    library_sha256=hashlib.sha256(library.read_bytes()).hexdigest(), log=''.join(logs))
    except (OSError, subprocess.SubprocessError) as error:
        return dict(accepted=False, reason='kernel execution failed: '+str(error))


def add_commands(sub):
    p = sub.add_parser('checked-factorial-unit', help='original factorial unit Lean certificate')
    p.add_argument('--n', type=int, required=True)
    p.add_argument('--prime', type=int, required=True)
    p.add_argument('--depth', type=int, required=True)
    p.add_argument('--work-limit', type=int, default=8192)
    p.add_argument('--check', action='store_true')


def cli(args):
    if args.command != 'checked-factorial-unit':
        return False
    packet = unit_certificate(args.n, args.prime, args.depth, work_limit=args.work_limit)
    output = dict(packet=packet)
    if args.check:
        output['acceptance'] = check_unit(packet)
    print(json.dumps(output, sort_keys=True))
    if args.check and not output['acceptance']['accepted']:
        raise SystemExit(1)
    return True
