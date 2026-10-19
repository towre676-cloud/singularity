"""A small definition language for OEIS entries, with Lean emission.

The original `.seq` text is kept.  Supported `%N` definitions are *translated* into one of a few
encodings; everything else stays a candidate interpretation only.

Encodings
---------
* `LinRec`: `a(n) = c1 a(n-1) + c2 a(n-2) [+ e]` for `n >= start`, with initial values (taken
  from the text, or from the listed terms when the text omits them, which is recorded).
* `Coord`: a subsequence or polynomial map of a named base, e.g. `F(2n)`, `2*Fibonacci(2*n+2)`,
  `Lucas(2n)^2`, `Squares of Pell numbers`.
* `GF`: `Expansion of P(x)/Q(x)`, any rational expression in `x` whose normalized denominator has
  degree 2 or 3.
* `SetSquare`: `Numbers k such that D*k^2 + c is a square` (`D > 0` not a square), and the
  `Positive integers k ...` variants.

Each encoding is evaluated here with exact integers and must reproduce **every** listed term at
the entry's offset.  The emitters then produce a Lean definition *generated from the encoding*
and a theorem tying it to an orbit coordinate (or, for `SetSquare`, to the certified seed orbits
of the quadratic-unit engine `QuadOrbit`), together with the recurrence the entry states.
Promotion means: the encoding reproduces the entry, its domain and offset are the entry's, and
the Lean theorem compiles.

Coordinate families
-------------------
A family is the orbit of a quadratic unit `ε`, `ε^k = X_k + Y_k √D` (up to the factor `1/2` for
`φ`), so `x(k+2) = t x(k+1) + σ x(k)` with `t` the trace and `-σ` the norm of `ε`.  A stride-`α`
subsequence satisfies `x(k+2α) = T_α x(k+α) + S_α x(k)`, `T_α` the trace of `ε^α` and
`S_α = -(-σ)^α`.  `sqrt3` (`2 + √3`, norm `+1`) is the family added last and used as the
withheld test of discovery and formalization.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from math import isqrt

# ---------------------------------------------------------------------------
# coordinate families
# ---------------------------------------------------------------------------

_P = 'PerfectPower.'
FAMILIES = {
    'fib': {'t': 1, 'sigma': 1, 'x0': (2, 1), 'y0': (0, 1), 'unit': 'φ = (1 + √5)/2',
            'X': _P + 'FibOrbit.L', 'Y': _P + 'FibOrbit.F',
            'Xrec': _P + 'FibOrbit.L_rec', 'Yrec': _P + 'FibOrbit.F_rec',
            'stride': _P + 'OEISLib.stride_one', 'nstrides': 6,
            'names': {'Fibonacci': 'Y', 'F': 'Y', 'Lucas': 'X', 'L': 'X'}},
    'pell2': {'t': 2, 'sigma': 1, 'x0': (1, 1), 'y0': (0, 1), 'unit': '1 + √2',
              'X': _P + 'SqrtTwoOrbit.A', 'Y': _P + 'SqrtTwoOrbit.B',
              'Xrec': _P + 'SqrtTwoOrbit.A_rec', 'Yrec': _P + 'SqrtTwoOrbit.B_rec',
              'stride': _P + 'OEISLib.stride_two', 'nstrides': 4,
              'names': {'Pell': 'Y'}},
    'sqrt3': {'t': 4, 'sigma': -1, 'x0': (1, 2), 'y0': (0, 1), 'unit': '2 + √3',
              'X': _P + 'OEISLib.ox 3 2 1', 'Y': _P + 'OEISLib.oy 3 2 1',
              'Xrec': _P + 'OEISLib.s3x_rec', 'Yrec': _P + 'OEISLib.s3y_rec',
              'stride': _P + 'OEISLib.stride_four', 'nstrides': 4,
              'names': {}},
}


def strides(fam: str) -> dict[int, tuple[int, int]]:
    """alpha -> (T_alpha, S_alpha)."""
    f = FAMILIES[fam]
    t, s = f['t'], f['sigma']
    T = [2, t]
    for _ in range(f['nstrides']):
        T.append(t * T[-1] + s * T[-2])
    return {a: (T[a], -((-s) ** a)) for a in range(1, f['nstrides'] + 1)}


def _sel(fam: str, alpha: int) -> str:
    n = FAMILIES[fam]['nstrides']
    return '.2' * (alpha - 1) + ('.1' if alpha < n else '')


def family_seq(fam: str, which: str, n: int) -> list[int]:
    f = FAMILIES[fam]
    a, b = f['x0'] if which == 'X' else f['y0']
    out = [a, b]
    while len(out) < n:
        out.append(f['t'] * out[-1] + f['sigma'] * out[-2])
    return out[:n]


# ---------------------------------------------------------------------------
# rational functions in x (for generating functions)
# ---------------------------------------------------------------------------

def _padd(p, q):
    n = max(len(p), len(q))
    return [(p[i] if i < len(p) else 0) + (q[i] if i < len(q) else 0) for i in range(n)]


def _pmul(p, q):
    out = [Fraction(0)] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            out[i + j] += a * b
    return out


def _trim(p):
    p = list(p)
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return p


class _RF:
    def __init__(self, num, den=(Fraction(1),)):
        self.num, self.den = [Fraction(c) for c in num], [Fraction(c) for c in den]

    def __add__(self, o):
        return _RF(_padd(_pmul(self.num, o.den), _pmul(o.num, self.den)), _pmul(self.den, o.den))

    def __neg__(self):
        return _RF([-c for c in self.num], self.den)

    def __sub__(self, o):
        return self + (-o)

    def __mul__(self, o):
        return _RF(_pmul(self.num, o.num), _pmul(self.den, o.den))

    def __truediv__(self, o):
        return _RF(_pmul(self.num, o.den), _pmul(self.den, o.num))

    def __pow__(self, k):
        r = _RF([1])
        for _ in range(k):
            r = r * self
        return r


def _pdivmod(a, b):
    a, b = [Fraction(x) for x in _trim(a)], [Fraction(x) for x in _trim(b)]
    q = [Fraction(0)] * max(1, len(a) - len(b) + 1)
    while len(a) >= len(b) and any(a):
        c = a[-1] / b[-1]
        d = len(a) - len(b)
        q[d] = c
        for i, x in enumerate(b):
            a[i + d] -= c * x
        a = _trim(a[:-1]) if len(a) > 1 else [Fraction(0)]
        if len(a) < len(b):
            break
    return q, a


def _pgcd(a, b):
    a, b = _trim([Fraction(x) for x in a]), _trim([Fraction(x) for x in b])
    while any(b):
        _, r = _pdivmod(a, b)
        a, b = b, _trim(r)
    return [x / a[-1] for x in a]


def parse_ratfun(s: str):
    """(P, Q) integer coefficient lists in lowest terms with Q[0] = 1, or None."""
    toks = re.findall(r'\d+|[x()+\-*/^]', s.replace(' ', ''))
    if ''.join(toks) != s.replace(' ', ''):
        return None
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        pos[0] += 1
        return toks[pos[0] - 1]

    def atom():
        t = peek()
        if t == '(':
            take()
            r = expr()
            if take() != ')':
                raise ValueError
            return r
        if t == 'x':
            take()
            return _RF([0, 1])
        if t is not None and t.isdigit():
            return _RF([int(take())])
        if t == '-':
            take()
            return -atom()
        raise ValueError

    def power():
        r = atom()
        while peek() == '^':
            take()
            r = r ** int(take())
        return r

    def term():
        r = power()
        while peek() in ('*', '/') or (peek() in ('(', 'x')):
            op = take() if peek() in ('*', '/') else '*'
            r = r * power() if op == '*' else r / power()
        return r

    def expr():
        r = term() if peek() != '-' else -(take() and term())
        while peek() in ('+', '-'):
            op = take()
            r = r + term() if op == '+' else r - term()
        return r

    try:
        rf = expr()
        if pos[0] != len(toks):
            return None
    except (ValueError, IndexError, ZeroDivisionError):
        return None
    num, den = _trim(rf.num), _trim(rf.den)
    if not any(den):
        return None
    g = _pgcd(num, den) if any(num) else [Fraction(1)]
    if len(g) > 1:
        num, den = _trim(_pdivmod(num, g)[0]), _trim(_pdivmod(den, g)[0])
    if den[0] == 0:
        return None
    c = den[0]
    num, den = [a / c for a in num], [a / c for a in den]
    if any(a.denominator != 1 for a in num + den):
        return None
    return [int(a) for a in num], [int(a) for a in den]


def gf_coeffs(P, Q, n):
    """First n coefficients of P/Q (Q[0] = 1)."""
    out = []
    for i in range(n):
        v = P[i] if i < len(P) else 0
        for j in range(1, len(Q)):
            if i - j >= 0:
                v -= Q[j] * out[i - j]
        out.append(v)
    return out


# ---------------------------------------------------------------------------
# encodings
# ---------------------------------------------------------------------------

@dataclass
class LinRec:
    coeffs: list[int]          # [c1, c2]
    const: int
    init: dict[int, int]       # n -> a(n)
    start: int                 # the recurrence holds for n >= start
    init_from_terms: bool = False

    def values(self, offset, n):
        vals = {}
        for i in range(offset, offset + n):
            if i < self.start or i - len(self.coeffs) < offset:
                vals[i] = self.init[i]
            else:
                vals[i] = sum(c * vals[i - 1 - j] for j, c in enumerate(self.coeffs)) + self.const
        return [vals[i] for i in range(offset, offset + n)]


@dataclass
class Coord:
    family: str
    which: str                 # 'X' or 'Y'
    alpha: int
    beta: int
    scale: int = 1
    power: int = 1

    def values(self, offset, n):
        seq = family_seq(self.family, self.which, self.alpha * (offset + n) + self.beta + 2)
        return [self.scale * seq[self.alpha * m + self.beta] ** self.power
                for m in range(offset, offset + n)]


@dataclass
class GF:
    P: list[int]
    Q: list[int]

    def values(self, offset, n):
        return gf_coeffs(self.P, self.Q, offset + n)[offset:]


@dataclass
class SetSquare:
    D: int
    c: int
    lo: int                    # 0 (nonnegative k) or 1 (positive k)
    domain_note: str = ''

    def members(self, bound):
        return [k for k in range(self.lo, bound + 1)
                if self.D * k * k + self.c >= 0 and isqrt(self.D * k * k + self.c) ** 2 == self.D * k * k + self.c]


@dataclass
class Translation:
    aid: str
    encoding: object
    source: str                # the %N text the encoding was read from
    claims: list = field(default_factory=list)   # the entry's stated recurrences [(c1, c2)]

    def to_json(self):
        enc = asdict(self.encoding)
        if isinstance(self.encoding, LinRec):
            enc['init'] = {str(k): v for k, v in sorted(enc['init'].items())}
        return {'kind': type(self.encoding).__name__, 'encoding': enc, 'source': self.source,
                'claims': self.claims}


# ---------------------------------------------------------------------------
# parsing %N lines
# ---------------------------------------------------------------------------

def _norm(s):
    return s.replace(' ', '').replace('−', '-')


def _parse_rhs(rhs, sym, shift):
    """`c1*a(n-1)+c2*a(n-2)+e` -> ([c1, c2], e), with `n` shifted by `shift`."""
    parts, depth, cur = [], 0, ''
    for ch in rhs:
        if ch in '+-' and depth == 0 and cur:
            parts.append(cur)
            cur = '-' if ch == '-' else ''
            continue
        depth += ch == '('
        depth -= ch == ')'
        cur += ch
    parts.append(cur)
    coeffs, const = {}, 0
    for part in [p for p in parts if p]:
        m = re.fullmatch(r'(-?\d*)\*?' + sym + r'\(n([+-]\d+)?\)', part)
        if m:
            c = m.group(1)
            c = -1 if c == '-' else (int(c) if c else 1)
            lag = shift - int(m.group(2) or 0)
            coeffs[lag] = coeffs.get(lag, 0) + c
            continue
        if re.fullmatch(r'-?\d+', part):
            const += int(part)
            continue
        return None
    if not coeffs or min(coeffs) < 1:
        return None
    order = max(coeffs)
    return [coeffs.get(i, 0) for i in range(1, order + 1)], const


def parse_linrec(name):
    s = _norm(name)
    m = re.search(r'(?<![A-Za-z])([aLF])\(n(\+1)?\)=((?:-?\d*\*?[aLF]\(n[+-]?\d*\)|[+-]\d+)'
                  r'(?:[+-](?:\d*\*?[aLF]\(n[+-]?\d*\)|\d+))*)', s)
    if not m:
        return None
    sym, plus1, rhs = m.group(1), m.group(2), m.group(3)
    parsed = _parse_rhs(rhs, sym, 1 if plus1 else 0)
    if parsed is None:
        return None
    coeffs, const = parsed
    if len(coeffs) != 2:
        return None
    init = {}
    for mm in re.finditer(sym + r'\((\d+)\)=' + sym + r'\((\d+)\)=(-?\d+)', s):
        init[int(mm.group(1))] = init[int(mm.group(2))] = int(mm.group(3))
    for mm in re.finditer(sym + r'\((\d+)\)=(-?\d+)(?![\d*(])', s):
        init[int(mm.group(1))] = int(mm.group(2))
    start = None
    mm = re.search(r'forn>=?(\d+)|n>(\d+)', s)
    if mm:
        start = int(mm.group(1)) if mm.group(1) else int(mm.group(2)) + 1
        if mm.group(1) and '>=' not in s[mm.start():mm.end()]:
            start = int(mm.group(1)) + 1
    if start is None and init and max(init) + 1 > len(coeffs):
        start = max(init) + 1
    return LinRec(coeffs, const, init, start if start is not None else -1)


_BASE = r'(Fibonacci|Lucas|F|L)'


def parse_coords(name):
    """Every coordinate reading of the name (several families may use the same words)."""
    s = _norm(name)
    out = []
    for family, fam in FAMILIES.items():
        m = re.match(r'(Squares?of|Squared)(Pell|Fibonacci|Lucas)numbers', s)
        if m:
            which = fam['names'].get(m.group(2))
            if which:
                out.append(Coord(family, which, 1, 0, power=2))
            continue
        pats = [r'a\(n\)=(\d+)\*' + _BASE + r'\((\d*)\*?n([+-]\d+)?\)(\^2)?(?![+\-*/\d])',
                r'a\(n\)=()' + _BASE + r'\((\d*)\*?n([+-]\d+)?\)(\^2)?(?![+\-*/\d])',
                r'^()' + _BASE + r'\((\d*)\*?n([+-]\d+)?\)(\^2)?=']
        for p in pats:
            m = re.search(p, s)
            if m:
                which = fam['names'].get(m.group(2))
                beta = int(m.group(4) or 0)
                if which is not None and beta >= 0:
                    out.append(Coord(family, which, int(m.group(3) or 1), beta,
                                     scale=int(m.group(1) or 1), power=2 if m.group(5) else 1))
                break
    return out


def parse_gf(name):
    s = _norm(name)
    m = re.match(r'Expansionof(?:g\.f\.)?(.+?)(?:inpowersofx)?\.?$', s)
    if not m:
        return None
    r = parse_ratfun(m.group(1).rstrip('.'))
    if r is None or len(r[1]) - 1 not in (2, 3):
        return None
    return GF(*r)


def parse_setsq(name):
    s = _norm(name)
    m = re.match(r'(Numbers|Positiveintegervalues(?:of)?|Positiveintegers|Nonnegativeintegers)'
                 r'[kn](?:suchthat|forwhich|with|such)?(\d*)\*?[kn]\^2([+-]\d+)'
                 r'isa(?:perfect)?square\.?$', s)
    if not m:
        return None
    D = int(m.group(2) or 1)
    if D <= 0 or isqrt(D) ** 2 == D:
        return None
    return SetSquare(D, int(m.group(3)), 1 if m.group(1).startswith('Positive') else 0)


def translate(entry) -> Translation | None:
    """The first supported reading of the entry's name that reproduces every listed term."""
    name = entry.name
    n = len(entry.terms)
    if re.match(r'\s*Duplicate of', name):
        return None
    readings = [parse_gf(name), parse_setsq(name)] + parse_coords(name) + [parse_linrec(name)]
    for enc in readings:
        if enc is None:
            continue
        if isinstance(enc, SetSquare):
            if enc.lo == 0 and entry.terms and entry.terms[0] > 0 and enc.members(entry.terms[0] - 1) == [0]:
                # "Numbers k" with k = 0 a solution, and the entry lists positive k only
                enc.lo = 1
                enc.domain_note = 'k = 0 solves the equation but the listed terms start after it: positive k'
            elif enc.lo == 0 and entry.terms and entry.terms[0] > 0 and enc.members(entry.terms[0] - 1):
                continue
            last = entry.terms[-1]
            bound = min(last, 10 ** 6)
            if [t for t in entry.terms if t <= bound] == [k for k in enc.members(bound) if k >= enc.lo]:
                return Translation(entry.id, enc, name)
            continue
        if isinstance(enc, LinRec):
            order = len(enc.coeffs)
            first = entry.offset
            if enc.start < 0:
                enc.start = first + order
            if enc.start - order < first:
                continue
            for i in range(first, enc.start):
                if i not in enc.init:
                    enc.init[i] = entry.term(i)
                    enc.init_from_terms = True
        try:
            vals = enc.values(entry.offset, n)
        except (IndexError, KeyError, TypeError):
            continue
        if vals == entry.terms:
            claims = []
            if isinstance(enc, Coord):
                lr = parse_linrec(name)
                if lr is not None and lr.const == 0:
                    claims.append(tuple(lr.coeffs))
            return Translation(entry.id, enc, name, claims)
    return None


# ---------------------------------------------------------------------------
# fitting an orbit coordinate: d * a(m) + s = p X(alpha m + beta) + q Y(alpha m + beta)
# ---------------------------------------------------------------------------

def _solve3(M, b):
    M = [[Fraction(x) for x in row] + [Fraction(y)] for row, y in zip(M, b)]
    for c in range(3):
        piv = next((r for r in range(c, 3) if M[r][c] != 0), None)
        if piv is None:
            return None
        M[c], M[piv] = M[piv], M[c]
        for r in range(3):
            if r != c and M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    return [M[i][3] / M[i][i] for i in range(3)]


def fit_coordinate(vals, family):
    """(alpha, beta, d, p, q, s) with d*vals[m] + s = p X(alpha m + beta) + q Y(alpha m + beta)
    for every given value (the least alpha, then beta, then d)."""
    N = len(vals)
    if N < 6:
        return None
    for alpha in sorted(strides(family)):
        X = family_seq(family, 'X', alpha * N + 2 * alpha + 20)
        Y = family_seq(family, 'Y', alpha * N + 2 * alpha + 20)
        for beta in range(0, 2 * alpha + 2):
            for d in (1, 2, 4, 5):
                sol = _solve3([[X[alpha * m + beta], Y[alpha * m + beta], -1] for m in range(3)],
                              [d * vals[m] for m in range(3)])
                if sol is None:
                    continue
                p, q, s = sol
                if any(x.denominator != 1 for x in (p, q, s)) or (p == 0 and q == 0):
                    continue
                p, q, s = int(p), int(q), int(s)
                if all(d * vals[m] + s == p * X[alpha * m + beta] + q * Y[alpha * m + beta]
                       for m in range(N)):
                    return alpha, beta, d, p, q, s
    return None


# ---------------------------------------------------------------------------
# Lean emission
# ---------------------------------------------------------------------------

def _i(v):
    return f'({v})' if v < 0 else str(v)


def _coord_expr(family, alpha, beta, p, q, var='m'):
    f = FAMILIES[family]
    idx = f'{alpha} * {var} + {beta}'
    return f"{_i(p)} * {f['X']} ({idx}) + {_i(q)} * {f['Y']} ({idx})"


def _stride_haves(family, alpha, k, tag=''):
    f = FAMILIES[family]
    sel = _sel(family, alpha)
    return [f"have hX{tag} := ({f['stride']} {f['Xrec']} ({k})){sel}",
            f"have hY{tag} := ({f['stride']} {f['Yrec']} ({k})){sel}"]


def _stride_rewrites(family, alpha, beta, p, q, var='m'):
    """Tactic lines closing a stride-alpha recurrence goal for p X + q Y."""
    k = f'{alpha} * {var} + {beta}'
    return _stride_haves(family, alpha, k) + [
        f"rw [show {alpha} * ({var} + 2) + {beta} = {k} + {2 * alpha} by ring, "
        f"show {alpha} * ({var} + 1) + {beta} = {k} + {alpha} by ring]",
        f"linear_combination ({_i(p)}) * hX + ({_i(q)}) * hY"]


def _doc(aid, source):
    src = source.replace('-/', '- /')
    return f'/-- {aid} (generated from its name): «{src}» -/'


def emit_linrec(aid, t: Translation, family, fit):
    """Definition by the entry's recurrence; theorem d * a(m + m0) + s = coordinate."""
    enc: LinRec = t.encoding
    off = min(enc.init)
    c1, c2 = enc.coeffs
    alpha, beta, d, p, q, s, m0 = fit
    if (c1, c2) != strides(family)[alpha] or d * enc.const + s * (1 - c1 - c2) != 0:
        return None
    k = enc.start - off           # number of initial cases; the recurrence case is `m + k`
    assert k == m0 + 2
    lines = [_doc(aid, t.source), f'def {aid} : ℕ → ℤ']
    for i in range(off, enc.start):
        lines.append(f'  | {i - off} => {_i(enc.init[i])}')
    lines.append(f'  | m + {k} => {_i(c1)} * {aid} (m + {k - 1}) + {_i(c2)} * {aid} (m + {k - 2}) + {_i(enc.const)}')
    g = _coord_expr(family, alpha, beta, p, q)
    fm = f'{d} * {aid} (m + {m0}) + {_i(s)}'
    lines += ['',
              f'/-- **{aid} is an orbit coordinate** of `{FAMILIES[family]["unit"]}` (from index {m0 + off}). -/',
              f'theorem {aid}_eq (m : ℕ) : {fm} = {g} :=',
              f'  PerfectPower.QuadOrbit.rec_unique (f := fun m => {fm})',
              f'    (g := fun m => {g}) {_i(c1)} {_i(c2)} 0',
              f'    (fun m => by',
              f'      show {d} * {aid} (m + {k}) + {_i(s)} = {_i(c1)} * ({d} * {aid} (m + {k - 1}) + {_i(s)}) + {_i(c2)} * ({d} * {aid} (m + {k - 2}) + {_i(s)}) + 0',
              f'      simp only [{aid}]; ring)',
              f'    (fun m => by',
              f'      show {_coord_expr(family, alpha, beta, p, q, "(m + 2)")} = {_i(c1)} * ({_coord_expr(family, alpha, beta, p, q, "(m + 1)")}) + {_i(c2)} * ({g}) + 0']
    lines += ['      ' + x + (')' if j == 3 else '') for j, x in enumerate(_stride_rewrites(family, alpha, beta, p, q))]
    lines += ['    (by decide +kernel) (by decide +kernel) m', '']
    return '\n'.join(lines)


def emit_coord(aid, t: Translation):
    enc: Coord = t.encoding
    f = FAMILIES[enc.family]
    base = f[enc.which]
    body = f'{base} ({enc.alpha} * m + {enc.beta})'
    if enc.power == 2:
        body = f'({body}) ^ 2'
    if enc.scale != 1:
        body = f'{enc.scale} * {body}'
    lines = [_doc(aid, t.source), f'def {aid} (m : ℕ) : ℤ := {body}', '']
    for (c1, c2) in t.claims:
        if enc.power != 1 or (c1, c2) != strides(enc.family).get(enc.alpha):
            continue
        rec = f['Yrec' if enc.which == 'Y' else 'Xrec']
        k = f'{enc.alpha} * m + {enc.beta}'
        lines += [f'/-- The recurrence stated in {aid}. -/',
                  f'theorem {aid}_rec (m : ℕ) : {aid} (m + 2) = {_i(c1)} * {aid} (m + 1) + {_i(c2)} * {aid} m := by',
                  f'  simp only [{aid}]',
                  f"  have h := ({f['stride']} {rec} ({k})){_sel(enc.family, enc.alpha)}",
                  f'  rw [show {enc.alpha} * (m + 2) + {enc.beta} = {k} + {2 * enc.alpha} by ring,',
                  f'    show {enc.alpha} * (m + 1) + {enc.beta} = {k} + {enc.alpha} by ring]',
                  f'  linear_combination ({enc.scale}) * h', '']
    return '\n'.join(lines)


def emit_gf(aid, t: Translation, family, fit):
    enc: GF = t.encoding
    qs_ = [-c for c in enc.Q[1:]]
    alpha, beta, d, p, qq, s, r = fit
    T, S = strides(family)[alpha]
    P = '[' + ', '.join(_i(c) for c in enc.P) + ']'
    fn = 'gf2' if len(qs_) == 2 else 'gf3'
    qs = ' '.join(_i(c) for c in qs_)
    if len(qs_) == 2:
        if tuple(qs_) != (T, S) or s * (1 - T - S) != 0:
            return None
    else:
        # the denominator must be (1 - x)(1 - T x - S x^2)
        if qs_ != [1 + T, S - T, -S]:
            return None
    g = _coord_expr(family, alpha, beta, p, qq)
    lhs = f'{d} * {aid} (m + {r}) + {_i(s)}'
    lines = [_doc(aid, t.source),
             f'def {aid} : ℕ → ℤ := PerfectPower.OEISLib.{fn} {P} {qs}', '',
             f'/-- **{aid} is an orbit coordinate** of `{FAMILIES[family]["unit"]}` (from index {r}). -/',
             f'theorem {aid}_eq (m : ℕ) : {lhs} = {g} :=',
             f'  PerfectPower.OEISLib.{fn}_eq {P} {qs} {d} {_i(s)} {r} (fun m => {g})',
             f'    (fun m => by']
    if len(qs_) == 2:
        lines.append(f'      show {_coord_expr(family, alpha, beta, p, qq, "(m + 2)")} = {_i(qs_[0])} * ({_coord_expr(family, alpha, beta, p, qq, "(m + 1)")}) + {_i(qs_[1])} * ({g}) + {_i(s)} * (1 - {_i(qs_[0])} - {_i(qs_[1])})')
        lines += ['      ' + x + (')' if j == 3 else '') for j, x in enumerate(_stride_rewrites(family, alpha, beta, p, qq))]
    else:
        k0, k1 = f'{alpha} * m + {beta}', f'{alpha} * m + {beta} + {alpha}'
        lines.append(f'      show {_coord_expr(family, alpha, beta, p, qq, "(m + 3)")} = {_i(qs_[0])} * ({_coord_expr(family, alpha, beta, p, qq, "(m + 2)")}) + {_i(qs_[1])} * ({_coord_expr(family, alpha, beta, p, qq, "(m + 1)")}) + {_i(qs_[2])} * ({g}) + {_i(s)} * (1 - {_i(qs_[0])} - {_i(qs_[1])} - {_i(qs_[2])})')
        lines += ['      ' + x for x in _stride_haves(family, alpha, k0, '0')]
        lines += ['      ' + x for x in _stride_haves(family, alpha, k1, '1')]
        lines += [f'      rw [show {alpha} * (m + 3) + {beta} = {k1} + {2 * alpha} by ring,',
                  f'        show {alpha} * (m + 2) + {beta} = {k0} + {2 * alpha} by ring,',
                  f'        show {alpha} * (m + 1) + {beta} = {k0} + {alpha} by ring]',
                  f'      rw [show {k1} + {alpha} = {k0} + {2 * alpha} by ring] at hX1 hY1',
                  f'      linear_combination ({_i(p)}) * (hX1 - hX0) + ({_i(qq)}) * (hY1 - hY0))']
    lines += [f'    (fun i hi => by have hi\' : i < {len(enc.P) + len(qs_)} := hi; interval_cases i <;> decide +kernel) m', '']
    return '\n'.join(lines)


def seeds_for(D, c, bound=10 ** 6):
    """(u, v, seeds, Ymax) for x^2 - D y^2 = c from the engine's root box, seeds sorted by y."""
    from .arith import pell_fundamental
    u, v = pell_fundamental(D)
    Ymax = 0
    while abs(c) * u * u >= D * (Ymax + 1) ** 2:
        Ymax += 1
    if Ymax > bound:
        return None
    seeds = []
    for y in range(Ymax + 1):
        t = c + D * y * y
        if t <= 0:
            continue
        x = isqrt(t)
        if x * x != t:
            continue
        px, py = x * u - D * y * v, u * y - v * x      # the predecessor under the unit
        if px > 0 and py >= 0:
            continue
        seeds.append((x, y))
    return u, v, seeds, Ymax


def order_ok(D, u, v, seeds):
    ys = [y for _, y in seeds]
    return bool(seeds) and ys == sorted(set(ys)) and ys[-1] < u * ys[0] + v * seeds[0][0]


def _hx0(D, c):
    if c > 0:
        return 'fun k => ne_of_gt (by positivity)'
    if (-c) % D:
        return 'fun k h => by generalize k ^ 2 = w at h; omega'
    m = -c // D
    r = isqrt(m)
    if r * r == m:
        return None
    return (f'fun k h => by\n    have h1 : k ^ 2 = {m} := by linarith\n'
            f'    rcases le_or_lt |k| {r} with hk | hk <;> nlinarith [abs_nonneg k, sq_abs k]')


def emit_setsq(aid, t: Translation, offset):
    enc: SetSquare = t.encoding
    got = seeds_for(enc.D, enc.c)
    if got is None:
        return None, None
    u, v, seeds, Ymax = got
    hx0 = _hx0(enc.D, enc.c)
    if hx0 is None or not order_ok(enc.D, u, v, seeds):
        return None, None
    skip = sum(1 for _, y in seeds if y < enc.lo)     # merged values below lo (only k = 0)
    if any(y < enc.lo for _, y in seeds[skip:]):
        return None, None
    sl = '[' + ', '.join(f'({x}, {y})' for x, y in seeds) + ']'
    args = f'{enc.D} {u} {v} {_i(enc.c)} {sl} {Ymax}'
    it = f'PerfectPower.OEISLib.interleave {enc.D} {u} {v} {sl}'
    lines = [_doc(aid, t.source),
             f'def {aid}Set : Set ℤ := {{k | {enc.lo} ≤ k ∧ ∃ x : ℤ, x ^ 2 = {enc.D} * k ^ 2 + {_i(enc.c)}}}', '',
             f'/-- {aid} as the increasing enumeration of `{aid}Set` from offset {offset}. -/',
             f'def {aid} (n : ℕ) : ℤ := {it} (n - {offset} + {skip})', '',
             f'/-- Seed certificate for `x^2 - {enc.D} y^2 = {enc.c}`, unit `{u} + {v}√{enc.D}`: '
             f'{len(seeds)} seed orbit(s), complete. -/',
             f'theorem {aid}_cert : PerfectPower.QuadOrbit.seedCheck {enc.D} {u} {v} {_i(enc.c)} {sl} {Ymax} = true := by',
             '  decide +kernel', '',
             f'theorem {aid}_order : PerfectPower.OEISLib.orderB {enc.D} {u} {v} {sl} = true := by',
             '  decide +kernel', '',
             f'/-- **{aid} lists its defining set in increasing order, from its offset.** -/',
             f'theorem {aid}_enumerates : PerfectPower.OEISLib.Enumerates {aid} {offset} {aid}Set :=',
             f'  PerfectPower.OEISLib.setsq_enumerates {args} (by norm_num) (by norm_num) (by norm_num)',
             f'    (by norm_num) {aid}_cert {aid}_order ({hx0}) {enc.lo} (by norm_num) {skip}',
             f'    (by decide +kernel) (by decide +kernel) {offset}', '']
    return '\n'.join(lines), {'D': enc.D, 'c': enc.c, 'unit': [u, v], 'seeds': [list(x) for x in seeds],
                              'Ymax': Ymax, 'skip': skip, 'domain': f'k >= {enc.lo}',
                              'domain_note': enc.domain_note}


# ---------------------------------------------------------------------------
# one entry, end to end (without Lean)
# ---------------------------------------------------------------------------

def compile_entry(entry):
    """Translate, fit and emit.  Returns a record; `lean` is the block, or None with a reason."""
    t = translate(entry)
    rec = {'oeis': entry.id, 'offset': entry.offset, 'terms': len(entry.terms)}
    if t is None:
        return {**rec, 'status': 'NOT_TRANSLATED', 'lean': None}
    rec['translation'] = t.to_json()
    enc = t.encoding
    aid = entry.id
    if isinstance(enc, Coord):
        return {**rec, 'status': 'EMITTED', 'family': enc.family, 'lean': emit_coord(aid, t),
                'theorems': [aid] + ([aid + '_rec'] if any(c == strides(enc.family).get(enc.alpha)
                                                           for c in t.claims) and enc.power == 1 else []),
                'relation': 'definition is the coordinate'}
    if isinstance(enc, SetSquare):
        block, cert = emit_setsq(aid, t, entry.offset)
        if block is None:
            return {**rec, 'status': 'NO_PROOF_ROUTE', 'lean': None,
                    'reason': 'seed box too large, order check fails, or D k^2 + c = 0 solvable'}
        return {**rec, 'status': 'EMITTED', 'family': 'engine', 'certificate': cert, 'lean': block,
                'theorems': [aid + 'Set', aid, aid + '_cert', aid + '_order', aid + '_enumerates'],
                'relation': 'increasing enumeration of the set'}
    if isinstance(enc, LinRec):
        m0 = enc.start - len(enc.coeffs) - entry.offset
        vals = enc.values(entry.offset, len(entry.terms) + 20)[m0:]
        for family in FAMILIES:
            fit = fit_coordinate(vals, family)
            if fit:
                block = emit_linrec(aid, t, family, fit + (m0,))
                if block:
                    return {**rec, 'status': 'EMITTED', 'family': family, 'fit': list(fit),
                            'shift': m0, 'lean': block, 'theorems': [aid, aid + '_eq'],
                            'relation': 'exact' if m0 == 0 else f'exact from index {entry.offset + m0}'}
        return {**rec, 'status': 'NO_PROOF_ROUTE', 'lean': None,
                'reason': 'no coordinate of a known family with the stated recurrence'}
    if isinstance(enc, GF):
        vals = gf_coeffs(enc.P, enc.Q, len(entry.terms) + entry.offset + 20)
        for r in range(0, len(enc.P) + 1):
            for family in FAMILIES:
                fit = fit_coordinate(vals[r:], family)
                if fit:
                    block = emit_gf(aid, t, family, fit + (r,))
                    if block:
                        return {**rec, 'status': 'EMITTED', 'family': family, 'fit': list(fit),
                                'shift': r, 'lean': block, 'theorems': [aid, aid + '_eq'],
                                'relation': 'exact' if r == 0 else f'exact from index {r}'}
        return {**rec, 'status': 'NO_PROOF_ROUTE', 'lean': None,
                'reason': 'denominator is not (1 - x)^e times a family characteristic polynomial'}
    return {**rec, 'status': 'NOT_TRANSLATED', 'lean': None}
