"""Fail-closed integration with SMT-LIB scripts: script replay, source-bound certificates, an
independent certificate checker, and a per-query ledger.

The adapter in `smt_adapter.py` rewrites a flat set of assertions.  Real verification tasks are
*scripts*: declarations, `push`/`pop`, many `check-sat` queries, each with its own live
assertion stack.  This module works at that level and is deliberately conservative.

**Replay.**  `split_commands` splits a script into top-level commands (comments, string literals
and `|quoted|` symbols handled).  `replay` walks them, tracking the assertion and declaration stack
through `push`/`pop`/`reset`, and yields every `check-sat` with its live assertions.  Nothing in
the script is executed.

**Classification.**  Every assertion is parsed once, in the declaration context live when it was
asserted, and each positive top-level conjunct is classified by an AST walk: linear; `div`/`mod`
by a numeral; a product of two unknowns or a power of an unknown (genuinely nonlinear); a solver
extension; or a Boolean/let/defined-symbol barrier the adapter does not look through.

**Certificates.**  A conjunct `m^2 = P(n)` over two Int unknowns can become a *checked
replacement* only when every condition below holds.  Otherwise it is recorded as an unchecked
candidate or as unsupported, and the solver keeps the original obligation.
1. Int semantics: both unknowns are declared `Int`, and the atom uses only `+ - *`, numerals, and
   powers with numeral exponents.
2. Positive context: the atom is asserted directly or as a conjunct of a top-level `and`. No `let`,
   no defined symbol, no `or`/`not`/`ite`/`=>` above it.
3. Checked normalization: `P(n) = (r n + s)^3 + k` exactly, coefficient by coefficient, with
   `k != 0` (`k = 0` is the singular curve `m^2 = t^3`, with infinitely many points).
4. A complete theorem whose statement is re-parsed from the Lean source and quantifies over
   **all** integers `x, y`. That is the solved-family registry (checked against its statements),
   the 1163 descent theorems `no_points_*`, or a hand-proved curve with a one-line statement.
   A theorem that is only cited is not enough.
5. Witness and sign transport: the witnesses are exactly `{((t - s)/r, ±y) : (t, y) in L, r | t - s}`,
   and each one is re-evaluated on the source polynomial.
6. Source binding: the certificate records the SHA-256 of the source script, the command index, the
   exact assertion text, the relation (`=`) and the normalized polynomial.  The checker requires a
   binary equality *before* normalizing: an inequality such as `m^2 > n^3 - 56` has the same
   operand polynomial but is not equivalent to the finite list. `check_certificate` re-derives all of them
   from the source.

Bounded Pell/radical enumerations (`smt_adapter.bounded_quadratic_hits`) are executed in Python
and stay **unchecked candidates** here.

The result of a checked replacement is a statement about one mathematical Int conjunct.  It is not
a proof accepted by any downstream verifier (Why3, GNATprove, ...); that bridge is separate.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .resources import runtime_root
ROOT = runtime_root()


# ---------------------------------------------------------------- script splitting and replay

def split_commands(text: str) -> list[str]:
    """Top-level s-expressions of an SMT-LIB script, as exact source substrings."""
    out, depth, start, i, n = [], 0, None, 0, len(text)
    while i < n:
        c = text[i]
        if c == ';':
            j = text.find('\n', i)
            i = n if j < 0 else j + 1
            continue
        if c == '"':
            i += 1
            while i < n:
                if text[i] == '"':
                    if i + 1 < n and text[i + 1] == '"':
                        i += 2
                        continue
                    break
                i += 1
        elif c == '|':
            j = text.find('|', i + 1)
            if j < 0:
                raise ValueError('unterminated quoted symbol')
            i = j
        elif c == '(':
            if depth == 0:
                start = i
            depth += 1
        elif c == ')':
            depth -= 1
            if depth < 0:
                raise ValueError('unbalanced parentheses')
            if depth == 0:
                out.append(text[start:i + 1])
        i += 1
    if depth:
        raise ValueError('unbalanced parentheses')
    return out


def head(cmd: str) -> str:
    m = re.match(r'\(\s*([^\s()]+)', cmd)
    return m.group(1) if m else ''


@dataclass
class Query:
    index: int                 # 0-based index among check-sat commands
    command_index: int
    live_asserts: list         # command indices of live assertions
    assuming: bool             # check-sat-assuming (its assumptions are not analyzed)


class DeclContext:
    """The declarations live at one point of a script, as a snapshot (list, length) per frame:
    constant work per assertion; iterated only when a declaration context is needed."""
    __slots__ = ('snap',)

    def __init__(self, frames):
        self.snap = [(f['decls'], len(f['decls'])) for f in frames]

    def __iter__(self):
        for lst, n in self.snap:
            yield from lst[:n]


def replay(cmds: list[str]):
    """(queries, assert_decl_context): the live assertion stack at every check-sat, and for each
    assert command the declaration commands live when it was asserted."""
    frames = [{'asserts': [], 'decls': []}]
    queries, context = [], {}
    for i, c in enumerate(cmds):
        h = head(c)
        if h in ('declare-fun', 'declare-const', 'define-fun', 'declare-sort', 'define-sort',
                 'declare-datatype', 'declare-datatypes', 'define-fun-rec', 'define-funs-rec'):
            frames[-1]['decls'].append(i)
        elif h == 'assert':
            frames[-1]['asserts'].append(i)
            context[i] = DeclContext(frames)
        elif h == 'push':
            k = int((re.findall(r'\d+', c) or ['1'])[0])
            frames += [{'asserts': [], 'decls': []} for _ in range(k)]
        elif h == 'pop':
            k = int((re.findall(r'\d+', c) or ['1'])[0])
            if k >= len(frames):
                raise ValueError(f'pop {k} below the base frame at command {i}')
            del frames[len(frames) - k:]
        elif h == 'reset':
            frames = [{'asserts': [], 'decls': []}]
        elif h == 'reset-assertions':
            frames = [{'asserts': [], 'decls': [d for f in frames for d in f['decls']]}]
        elif h in ('check-sat', 'check-sat-assuming'):
            queries.append(Query(len(queries), i, [a for f in frames for a in f['asserts']],
                                 h == 'check-sat-assuming'))
    return queries, context


# ---------------------------------------------------------------- classification

EXTENSION_HINTS = ('int.pow2', 'iand', 'int2bv', 'bv2nat', 'ubv_to_int', 'sbv_to_int', 'int.log2')


def _is_numeral(e) -> bool:
    import z3
    if z3.is_int_value(e) or z3.is_rational_value(e):
        return True
    if e.decl().kind() in (z3.Z3_OP_UMINUS, z3.Z3_OP_TO_REAL):
        return _is_numeral(e.arg(0))
    return False


def ast_features(e) -> set:
    """Nonlinearity features of a term: 'product' (two non-numeral factors), 'power',
    'div_var' / 'mod_var' (non-numeral divisor), 'div_const' / 'mod_const'."""
    import z3
    out, seen, todo = set(), set(), [e]
    while todo:
        t = todo.pop()
        if t.get_id() in seen:
            continue
        seen.add(t.get_id())
        if z3.is_app(t):
            k = t.decl().kind()
            if k == z3.Z3_OP_MUL and sum(not _is_numeral(a) for a in t.children()) >= 2:
                out.add('product')
            elif k == z3.Z3_OP_POWER and not _is_numeral(t.arg(0)):
                out.add('power')
            elif k in (z3.Z3_OP_IDIV, z3.Z3_OP_DIV):
                out.add('div_const' if _is_numeral(t.arg(1)) else 'div_var')
            elif k in (z3.Z3_OP_MOD, z3.Z3_OP_REM):
                out.add('mod_const' if _is_numeral(t.arg(1)) else 'mod_var')
            todo.extend(t.children())
    return out


def _conjuncts(a):
    import z3
    out, todo = [], [a]
    while todo:
        t = todo.pop(0)
        if z3.is_and(t):
            todo = list(t.children()) + todo
        else:
            out.append(t)
    return out


@dataclass
class AtomRecord:
    command_index: int
    conjunct: int
    category: str          # linear | div_mod_const | nonlinear | extension | barrier | parse_error
    features: list
    atom: str = ''
    candidate: dict | None = None     # recognized shape, before checking
    certificate: dict | None = None   # only when fully checked
    note: str = ''


def _sexpr(text: str):
    """A small s-expression reader (strings and |quoted| symbols kept as atoms)."""
    toks = re.findall(r'\|[^|]*\||"(?:[^"]|"")*"|[()]|[^\s()]+', text)
    stack = [[]]
    for t in toks:
        if t == '(':
            stack.append([])
        elif t == ')':
            e = stack.pop()
            stack[-1].append(e)
        else:
            stack[-1].append(t)
    return stack[0][0] if stack[0] else []


def _numeral(e) -> bool:
    if isinstance(e, str):
        return bool(re.fullmatch(r'\d+(\.\d+)?', e))
    return len(e) == 2 and e[0] == '-' and _numeral(e[1])


def _lexical_features(e) -> set:
    """Conservative nonlinearity scan of one conjunct (false positives only send the conjunct
    to the precise z3 path)."""
    out, todo = set(), [e]
    while todo:
        t = todo.pop()
        if isinstance(t, list) and t:
            h = t[0]
            if h == '*' and sum(not _numeral(a) for a in t[1:]) >= 2:
                out.add('product')
            elif h in ('^', 'pow') and not _numeral(t[1]):
                out.add('power')
            elif h in ('div', 'mod', 'rem', '/') and len(t) == 3:
                out.add(('div' if h in ('div', '/') else 'mod') + ('_const' if _numeral(t[2]) else '_var'))
            todo.extend(t)
    return out


def defined_names(cmds) -> dict:
    """command index -> name, for every `define-fun` (computed once per script)."""
    out = {}
    for i, c in enumerate(cmds):
        m = re.match(r'\(\s*define-fun\s+([^\s()]+)', c)
        if m:
            out[i] = m.group(1)
    return out


def classify_assert(cmds, idx, context, source_sha, defnames=None) -> list[AtomRecord]:
    import z3
    text = cmds[idx]
    if defnames is None:
        defnames = defined_names(cmds)
    defined = {defnames[d] for d in context if d in defnames} if defnames else set()
    toks = set(re.findall(r'[^\s()]+', text))
    if any(h in text for h in EXTENSION_HINTS):
        return [AtomRecord(idx, 0, 'extension', [], note='solver extension symbol')]
    if '(let' in text.replace(' ', '') or defined & toks:
        return [AtomRecord(idx, 0, 'barrier', [], note='let or defined symbol: not normalized without a checked rule')]
    if not any(op in toks for op in ('*', '^', 'div', 'mod', 'rem', '/')) and '(*' not in text:
        return [AtomRecord(idx, 0, 'linear', [], note='no multiplicative operator')]
    # lexical pre-pass: only conjuncts that may be nonlinear go to z3
    body = _sexpr(text)[1]
    conj = body[1:] if isinstance(body, list) and body and body[0] == 'and' else [body]
    lex = [_lexical_features(c) for c in conj]
    if not any(f & {'product', 'power', 'div_var', 'mod_var'} for f in lex):
        return [AtomRecord(idx, j, 'div_mod_const' if f & {'div_const', 'mod_const'} else 'linear',
                           sorted(f), note='lexical') for j, f in enumerate(lex)]
    try:
        parsed = z3.parse_smt2_string('\n'.join(cmds[d] for d in context) + '\n' + text)
    except z3.Z3Exception as ex:
        return [AtomRecord(idx, 0, 'parse_error', [], note=str(ex)[:200])]
    out = []
    for a in parsed:
        for j, c in enumerate(_conjuncts(a)):
            f = ast_features(c)
            if f & {'product', 'power', 'div_var', 'mod_var'}:
                cat = 'nonlinear'
            elif f & {'div_const', 'mod_const'}:
                cat = 'div_mod_const'
            else:
                cat = 'linear'
            rec = AtomRecord(idx, j, cat, sorted(f), atom=c.sexpr())
            if cat == 'nonlinear':
                rec.candidate, rec.certificate, rec.note = _certify(c, text, idx, source_sha)
            out.append(rec)
    return out


# ---------------------------------------------------------------- certificates

def _poly_key(P) -> list:
    return sorted([[list(map(list, mono)), c] for mono, c in P.items()])


def _lean_list(k: int):
    """(theorem name, complete point list or [] for no points), re-parsed from the Lean source,
    for y^2 = x^3 + k over all integers.  None when no statement for k is parsed."""
    from importlib import util
    if k < 0:
        spec = util.spec_from_file_location('reg', ROOT / 'python' / 'make_mordell_registry.py')
        reg = util.module_from_spec(spec)
        spec.loader.exec_module(reg)
        lists = reg.lean_lists()
        if -k in lists:
            name, pts = lists[-k]
            return name, [tuple(p) for p in pts]
    text = (ROOT / 'PerfectPower' / 'Generated' / 'MordellDescent.lean').read_text()
    tag = f'm{-k}' if k < 0 else f'p{k}'
    pat = re.compile(rf'^theorem no_points_{tag} \(x y : ℤ\) : y \^ 2 ≠ x \^ 3 \+ '
                     rf'{re.escape(f"({k})" if k < 0 else str(k))} :=', re.M)
    if pat.search(text):
        return f'PerfectPower.Generated.no_points_{tag}', []
    hand = {-2: 'MordellMinus2', -13: 'MordellMinus13', -5: 'MordellMinus5', -6: 'MordellMinus6'}
    if k in hand:
        src = (ROOT / 'PerfectPower' / f'{hand[k]}.lean').read_text()
        m = re.search(rf'^theorem points \(x y : ℤ\) : y \^ 2 = x \^ 3 - {-k} ↔ x = (\d+) ∧ '
                      rf'\(y = (\d+) ∨ y = -(\d+)\) :=', src, re.M)
        if m and m.group(2) == m.group(3):
            x0, y0 = int(m.group(1)), int(m.group(2))
            return f'PerfectPower.{hand[k]}.points', [(x0, y0), (x0, -y0)]
        if re.search(rf'^theorem no_points \(x y : ℤ\) : y \^ 2 ≠ x \^ 3 - {-k} :=', src, re.M):
            return f'PerfectPower.{hand[k]}.no_points', []
    return None


def _witnesses(L, r, s):
    return sorted({((t - s) // r, y) for t, y in L if (t - s) % r == 0})


def _certify(atom, assert_text, idx, source_sha):
    """(candidate, certificate or None, note) for one nonlinear conjunct."""
    import z3
    from .compiler import match_affine_cube
    from .smt_adapter import Unsupported, _padd, recognize, recognize_quadratic, to_poly
    if not z3.is_eq(atom):
        return None, None, 'nonlinear, not an equality'
    try:
        P = _padd(to_poly(atom.arg(0)), to_poly(atom.arg(1)), -1)
    except Unsupported as ex:
        return None, None, f'unsupported term: {ex}'
    rec = recognize(P)
    if rec is None:
        q = recognize_quadratic(P)
        if q:
            return ({'shape': 'quadratic_in_two_unknowns', 'readings': len(q)}, None,
                    'bounded Pell/radical enumeration would be unchecked Python: not applied')
        return None, None, 'nonlinear shape outside the supported fragment'
    n, m, F = rec
    F = tuple(F) + (0,) * max(0, 4 - len(F))
    mac = match_affine_cube(F) if len(F) == 4 else None
    if mac is None:
        return {'shape': 'square_equals_polynomial', 'degree': len(F) - 1}, None, 'not an affine cube'
    r, s, k = mac
    cand = {'shape': 'm^2 = (r n + s)^3 + k', 'n': n, 'm': m, 'r': r, 's': s, 'k': k}
    if k == 0:
        return cand, None, 'k = 0: singular curve m^2 = t^3, infinitely many points (t = u^2)'
    thm = _lean_list(k)
    if thm is None:
        return cand, None, f'no parsed complete theorem for y^2 = x^3 + ({k})'
    name, L = thm
    cert = {'version': 1, 'source_sha256': source_sha, 'command_index': idx,
            'assert_sha256': hashlib.sha256(assert_text.encode()).hexdigest(),
            'atom': atom.sexpr(), 'relation': '=', 'unknowns': {'n': n, 'm': m, 'sort': 'Int'},
            'polynomial': _poly_key(P), 'affine': {'r': r, 's': s, 'k': k},
            'theorem': name, 'curve_points': sorted(map(list, L)),
            'witnesses': [list(w) for w in _witnesses(L, r, s)],
            'domain': 'all integers (theorem quantifies over x y : ℤ; no n >= 1 contract)'}
    ok, why = check_certificate(cert, None, _atom=atom)
    return cand, (cert if ok else None), ('checked' if ok else f'certificate rejected: {why}')


def check_certificate(cert: dict, source_text: str | None, _atom=None):
    """Independent re-derivation.  With `source_text`, the binding to the source script is checked
    too (file hash, command index, assertion hash, atom re-parsed in its declaration context).
    Returns (ok, reason)."""
    import z3
    from .smt_adapter import Unsupported, _padd, to_poly
    try:
        if cert.get('version') != 1:
            return False, 'unknown certificate version'
        atom = _atom
        if source_text is not None:
            if hashlib.sha256(source_text.encode()).hexdigest() != cert['source_sha256']:
                return False, 'source hash mismatch'
            cmds = split_commands(source_text)
            idx = cert['command_index']
            if not (0 <= idx < len(cmds)) or head(cmds[idx]) != 'assert':
                return False, 'command index is not an assertion'
            if hashlib.sha256(cmds[idx].encode()).hexdigest() != cert['assert_sha256']:
                return False, 'assertion text mismatch'
            _, context = replay(cmds)
            parsed = z3.parse_smt2_string('\n'.join(cmds[d] for d in context[idx]) + '\n' + cmds[idx])
            atoms = [c for a in parsed for c in _conjuncts(a) if c.sexpr() == cert['atom']]
            if not atoms:
                return False, 'atom not a positive conjunct of that assertion'
            atom = atoms[0]
        if atom is None:
            return False, 'no atom to check'
        # the relation is part of the certified statement: only a binary Int equality qualifies,
        # checked before any normalization (m^2 > n^3 - 56 has the same operand polynomial)
        if not (z3.is_eq(atom) and atom.num_args() == 2 and cert.get('relation') == '='):
            return False, 'atom is not a binary equality'
        if atom.arg(0).sort() not in (z3.IntSort(), z3.RealSort()):
            return False, 'atom is not arithmetic'
        n, m = cert['unknowns']['n'], cert['unknowns']['m']
        P = _padd(to_poly(atom.arg(0)), to_poly(atom.arg(1)), -1)
        if _poly_key(P) != cert['polynomial']:
            return False, 'polynomial does not match the atom'
        r, s, k = cert['affine']['r'], cert['affine']['s'], cert['affine']['k']
        if r == 0 or k == 0:
            return False, 'degenerate substitution or singular curve'
        # exact: P = ±(m^2 - (r n + s)^3 - k)
        expect = {((m, 2),): 1}
        for mono, c in {((n, 3),): r ** 3, ((n, 2),): 3 * r * r * s, ((n, 1),): 3 * r * s * s,
                        (): s ** 3 + k}.items():
            if c:
                expect[mono] = expect.get(mono, 0) - c
        if P != expect and P != {mono: -c for mono, c in expect.items()}:
            return False, 'coefficients are not (r n + s)^3 + k'
        thm = _lean_list(k)
        if thm is None or thm[0] != cert['theorem']:
            return False, 'theorem statement not found or different'
        L = sorted(map(list, thm[1]))
        if L != cert['curve_points']:
            return False, 'curve points differ from the parsed theorem'
        W = [list(w) for w in _witnesses([tuple(p) for p in L], r, s)]
        if W != cert['witnesses']:
            return False, 'witness transport mismatch'
        for a, b in W:
            val = sum(c * (a ** dict(mono).get(n, 0)) * (b ** dict(mono).get(m, 0)) for mono, c in P.items())
            if val != 0:
                return False, f'witness ({a}, {b}) does not satisfy the atom'
        return True, 'ok'
    except (Unsupported, KeyError, TypeError, ValueError, z3.Z3Exception) as ex:
        return False, f'malformed: {ex}'


def replacement_formula(cert: dict):
    """The finite disjunction equivalent (over Z) to the certified atom."""
    import z3
    N, M = z3.Int(cert['unknowns']['n']), z3.Int(cert['unknowns']['m'])
    W = cert['witnesses']
    return z3.Or([z3.And(N == a, M == b) for a, b in W]) if W else z3.BoolVal(False)


# ---------------------------------------------------------------- per-file ledger

def ledger_for_file(path: Path, rel: str) -> dict:
    import time
    raw = path.read_bytes()
    text = raw.decode('utf-8')
    sha = hashlib.sha256(raw).hexdigest()
    t0 = time.perf_counter()
    try:
        cmds = split_commands(text)
        queries, context = replay(cmds)
    except ValueError as ex:
        return {'file': rel, 'sha256': sha, 'error': f'script: {ex}'}
    records, defnames = {}, defined_names(cmds)
    for i, c in enumerate(cmds):
        if head(c) == 'assert':
            records[i] = classify_assert(cmds, i, context[i], sha, defnames)
    analysis_s = time.perf_counter() - t0
    qrows = []
    for q in queries:
        recs = [r for a in q.live_asserts for r in records[a]]
        cats = {}
        for r in recs:
            cats[r.category] = cats.get(r.category, 0) + 1
        qrows.append({'query': q.index, 'command_index': q.command_index, 'check_sat_assuming': q.assuming,
                      'live_assertions': len(q.live_asserts), 'atoms': len(recs), 'categories': cats,
                      'checked_replacements': sum(r.certificate is not None for r in recs),
                      'unchecked_candidates': sum(r.candidate is not None and r.certificate is None for r in recs)})
    nonlinear = [r for rs in records.values() for r in rs if r.category == 'nonlinear']
    cat_tot = {}
    for rs in records.values():
        for r in rs:
            cat_tot[r.category] = cat_tot.get(r.category, 0) + 1
    return {'file': rel, 'sha256': sha, 'commands': len(cmds), 'queries': len(queries),
            'assertions': len(records), 'atom_categories': cat_tot,
            'nonlinear_atoms': [{'command_index': r.command_index, 'atom': r.atom[:300], 'features': r.features,
                                 'candidate': r.candidate, 'checked': r.certificate is not None,
                                 'note': r.note} for r in nonlinear],
            'certificates': [r.certificate for rs in records.values() for r in rs if r.certificate],
            'analysis_seconds': round(analysis_s, 4), 'per_query': qrows}
