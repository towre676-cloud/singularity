"""Kernel-checked bounded quadratic queries (`PerfectPower/BoundedPell.lean`).

`plan(a, b, c, q, p, r, lo, hi)` prepares every input of `BoundedPell.quad_bounded` for the query
"all integer `(N, S)` with `lo ≤ N ≤ hi` and `a S² + b S + c = q N² + p N + r`":
- `D = a q` and `Δ = a(q(4ac − b²) − a(4qr − p²))`;
- a unit `u + v√D` of norm 1, the smallest by continued fractions;
- the seed roots and `Ymax` exactly as `QuadOrbit.seedCheck` checks them;
- `J` with `a(2q·hi + p) < 2^J`, and the orbit list `L` with the recovered pairs `L0`.

`lean_theorem(...)` emits the instance; its five checks are closed by `decide`.  The requirements
are `a > 0`, `q > 0`, `D` not a square, and `2q·lo + p > 0`; a query outside them is refused
(`Unsupported`), never approximated.
"""
from __future__ import annotations

from math import isqrt


class Unsupported(Exception):
    pass


MAX_BOX = 20000   # largest root box (Y range) the kernel seed check is asked to enumerate


def pell_unit(D: int) -> tuple[int, int]:
    """The fundamental solution of u² − D v² = 1 (continued fraction of √D)."""
    a0 = isqrt(D)
    if a0 * a0 == D:
        raise Unsupported('D is a square')
    m, d, a = 0, 1, a0
    p0, p1, q0, q1 = 1, a0, 0, 1
    while p1 * p1 - D * q1 * q1 != 1:
        m = d * a - m
        d = (D - m * m) // d
        a = (a0 + m) // d
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
    return p1, q1


def _sol(D, Delta, x, y):
    return x > 0 and y >= 0 and x * x - D * y * y == Delta


def _pred(D, u, v, x, y):
    return x * u - D * y * v, u * y - v * x


def seeds_for(D, u, v, Delta):
    """(seeds, Ymax) as `QuadOrbit.seedCheck` verifies them."""
    # least Ymax with |Δ| u² < D (Ymax + 1)², exactly (integer square root, no float)
    Ymax = max(0, isqrt(abs(Delta) * u * u // D) - 1)
    while not (abs(Delta) * u * u < D * (Ymax + 1) ** 2):
        Ymax += 1
    while Ymax > 0 and abs(Delta) * u * u < D * Ymax ** 2:
        Ymax -= 1
    if Ymax > MAX_BOX:
        raise Unsupported(f'root box Y <= {Ymax} too large for a kernel seed check (unit {u} + {v}√{D}); '
                          'needs a continued-fraction root characterization')
    seeds = []
    for Y in range(Ymax + 1):
        t = Delta + D * Y * Y
        if t <= 0:
            continue
        x = isqrt(t)
        if x * x == t and x > 0 and not _sol(D, Delta, *_pred(D, u, v, x, Y)):
            seeds.append((x, Y))
    return seeds, Ymax


def plan(a, b, c, q, p, r, lo, hi):
    if not (a > 0 and q > 0):
        raise Unsupported('needs a > 0 and q > 0 (normalize signs first)')
    if not (2 * q * lo + p > 0):
        raise Unsupported('needs 2 q lo + p > 0; split the range and reflect N -> -N')
    if lo > hi:
        raise Unsupported('empty range')
    D = a * q
    Delta = a * (q * (4 * a * c - b * b) - a * (4 * q * r - p * p))
    u, v = pell_unit(D)
    seeds, Ymax = seeds_for(D, u, v, Delta)
    Xmax = a * (2 * q * hi + p)
    J = max(1, Xmax.bit_length())
    while not Xmax < 2 ** J:
        J += 1
    L = []
    for (x, y) in seeds:
        for _ in range(J):
            if x <= Xmax:
                L.append((x, y))
            x, y = x * u + D * y * v, x * v + y * u
    L0 = set()
    for (X, Y0) in L:
        for Y in (Y0, -Y0):
            if (X - a * p) % (2 * a * q) == 0 and (Y - b) % (2 * a) == 0:
                N, S = (X - a * p) // (2 * a * q), (Y - b) // (2 * a)
                if lo <= N <= hi:
                    assert a * S * S + b * S + c == q * N * N + p * N + r
                    L0.add((N, S))
    return {'a': a, 'b': b, 'c': c, 'q': q, 'p': p, 'r': r, 'lo': lo, 'hi': hi, 'D': D, 'Delta': Delta,
            'u': u, 'v': v, 'seeds': seeds, 'Ymax': Ymax, 'J': J, 'L': sorted(set(L)), 'L0': sorted(L0)}


def _z(x):
    return f'({x})' if x < 0 else str(x)


def _list(xs):
    return '[' + ', '.join(f'({_z(x)}, {_z(y)})' for x, y in xs) + ']'


def lean_theorem(name: str, P: dict) -> str:
    a, b, c, q, p, r, lo, hi = (P[k] for k in 'a b c q p r lo hi'.split())
    return f'''/-- Bounded query: every `(N, S)` with `{lo} ≤ N ≤ {hi}` and
`{a} S² + {b} S + {c} = {q} N² + {p} N + {r}` (norm form `X² − {P['D']} Y² = {P['Delta']}`, unit
`{P['u']} + {P['v']}√{P['D']}`, {len(P['seeds'])} seed(s), {P['J']} orbit steps). -/
theorem {name} (N S : ℤ) (h1 : {_z(lo)} ≤ N) (h2 : N ≤ {_z(hi)}) :
    {_z(a)} * S ^ 2 + {_z(b)} * S + {_z(c)} = {_z(q)} * N ^ 2 + {_z(p)} * N + {_z(r)} ↔
      (N, S) ∈ ({_list(P['L0'])} : List (ℤ × ℤ)) :=
  BoundedPell.quad_bounded (u := {P['u']}) (v := {P['v']}) {_z(a)} {_z(b)} {_z(c)} {_z(q)} {_z(p)} {_z(r)} {_z(lo)} {_z(hi)}
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num)
    (seeds := {_list(P['seeds'])}) (Ymax := {P['Ymax']}) (by decide +kernel) {P['J']} (by norm_num)
    {_list(P['L'])} {_list(P['L0'])}
    (by decide +kernel) (by decide +kernel) (by decide +kernel) N S h1 h2
'''


def kernel_check(P: dict, timeout: float = 300) -> tuple[bool, str]:
    """Emit the instance and run the Lean kernel on it (`lake env lean`).  (ok, detail)."""
    import hashlib
    import os
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    lake = shutil.which('lake') or str(Path.home() / '.elan' / 'bin' / 'lake')
    if not Path(lake).exists():
        return False, 'lake not found'
    name = 'q_' + hashlib.sha256(repr(sorted(P.items())).encode()).hexdigest()[:12]
    text = ('import PerfectPower.BoundedPell\nnamespace PerfectPower.BoundedQuery\nopen PerfectPower\n'
            + lean_theorem(name, P) + 'end PerfectPower.BoundedQuery\n')
    with tempfile.TemporaryDirectory(dir=root / '.lake') as d:
        f = Path(d) / 'Query.lean'
        f.write_text(text)
        env = dict(os.environ, PATH=str(Path(lake).parent) + os.pathsep + os.environ.get('PATH', ''))
        try:
            run = subprocess.run([lake, 'env', 'lean', str(f)], cwd=root, capture_output=True, text=True,
                                 timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return False, 'kernel check timed out'
    out = run.stdout + run.stderr
    if run.returncode != 0 or 'error' in out or 'sorry' in out:
        return False, out[:300]
    return True, name
