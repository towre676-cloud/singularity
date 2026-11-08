#!/usr/bin/env python3
"""Exact eighth-order difference reader. Standard library only; delta = B - A."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
import json
from math import comb, isfinite
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = ('Q0', 'Q1', 'S8_10', 'S8_11', 'S8_12', 'Theta223', 'closed_diamond')
PANEL = (2, 6, 8, 18, 22, 28, 30)
OPTIMAL_PANEL = (4, 8, 12, 14, 18, 24, 26)
CONNECTED_INDICES = (0, 1, 2, 3, 5, 6)
CONNECTED_NAMES = tuple(NAMES[i] for i in CONNECTED_INDICES)
CONNECTED_PANEL = (6, 10, 14, 18, 24, 26)


def model(mode, panel):
    if mode not in ('general', 'connected'):
        raise ValueError('mode must be general or connected')
    names = CONNECTED_NAMES if mode == 'connected' else NAMES
    default = CONNECTED_PANEL if mode == 'connected' else PANEL
    panel = tuple(default if panel is None else panel)
    if (len(panel) != len(names) or any(type(e) is not int or e < 0 for e in panel)
            or len(set(panel)) != len(panel)):
        raise ValueError('Choose %s distinct nonnegative integer degrees' % len(names))
    return names, panel


def connected_graph(record):
    """Validate explicit topology; supplied calculations remain conditional."""
    if record.get('connected') is not True:
        raise ValueError('Connected mode requires connected=true on both records')
    graph = record.get('graph')
    if not isinstance(graph, dict):
        raise ValueError('Connected mode requires graph with n and edges')
    n, edges = graph.get('n'), graph.get('edges')
    if type(n) is not int or n < 4 or n % 2 or not isinstance(edges, list):
        raise ValueError('Invalid finite simple cubic graph')
    adj = [set() for _ in range(n)]
    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            raise ValueError('Edges must be endpoint pairs')
        a, b = edge
        if (type(a) is not int or type(b) is not int or not 0 <= a < n
                or not 0 <= b < n or a == b or b in adj[a]):
            raise ValueError('Invalid endpoint, loop or duplicate edge')
        adj[a].add(b); adj[b].add(a)
    if any(len(row) != 3 for row in adj):
        raise ValueError('Graph must be cubic')
    seen, pending = {0}, [0]
    while pending:
        for v in adj[pending.pop()]:
            if v not in seen:
                seen.add(v); pending.append(v)
    if len(seen) != n:
        raise ValueError('Graph must be connected')
    return n


def add(a, b, scale=1):
    c = dict(a)
    for e, x in b.items():
        c[e] = c.get(e, F(0)) + scale*x
    return {e: x for e, x in c.items() if x}


def mul(a, b):
    c = {}
    for e, x in a.items():
        for d, y in b.items():
            c[e+d] = c.get(e+d, F(0)) + x*y
    return {e: x for e, x in c.items() if x}


def rational(x):
    if isinstance(x, (float, bool)) or not isinstance(x, (int, str, F)):
        raise ValueError('Exact input requires integers or rational strings, never floats/bools')
    return F(x)


def polynomial(p):
    if not isinstance(p, dict):
        raise ValueError('A complete polynomial must be a coefficient dictionary')
    out = {}
    for e, x in p.items():
        if isinstance(e, bool) or not isinstance(e, (str, int)):
            raise ValueError('Polynomial degrees must be nonnegative integers')
        d = int(e)
        if str(d) != str(e) or d < 0 or d in out:
            raise ValueError('Noncanonical or duplicate polynomial degree')
        out[d] = rational(x)
    return {e: x for e, x in out.items() if x}


@lru_cache(None)
def factors(mode='general'):
    k = {8+2*j: F((-1)**j*comb(8, j)) for j in range(9)}
    f = {-2: F(1), 0: F(-1)}
    a = {2: F(3), 4: F(3), 6: F(1)}
    weights = [{0: F(1)}]
    for _ in range(4):
        weights.append(mul(weights[-1], f))
    weights += [{e: -x for e, x in a.items()}, mul(f, a)]
    model(mode, None)
    result = tuple(mul(k, w) for w in weights)
    return tuple(result[i] for i in CONNECTED_INDICES) if mode == 'connected' else result


def matrix(panel=None, *, mode='general'):
    _, panel = model(mode, panel)
    return [[p.get(e, F(0)) for p in factors(mode)] for e in panel]


def invert(a):
    n = len(a)
    rows = [[F(x) for x in row] + [F(i == j) for j in range(n)] for i, row in enumerate(a)]
    det = F(1)
    for j in range(n):
        pivot = next((i for i in range(j, n) if rows[i][j]), None)
        if pivot is None:
            raise ValueError('Singular coefficient panel')
        if pivot != j:
            rows[j], rows[pivot] = rows[pivot], rows[j]
            det = -det
        x = rows[j][j]
        det *= x
        rows[j] = [v/x for v in rows[j]]
        for i in range(n):
            if i != j and rows[i][j]:
                x = rows[i][j]
                rows[i] = [v-x*w for v, w in zip(rows[i], rows[j])]
    return tuple(tuple(row[n:]) for row in rows), det


def reconstruct(values, *, mode='general'):
    names, _ = model(mode, None)
    if len(values) != len(names):
        raise ValueError('Wrong coordinate count')
    p = {}
    for x, factor in zip(values, factors(mode)):
        p = add(p, factor, x)
    return p


def log_series(record):
    """Complete sparse polynomials: omitted degrees are zero, missing volumes error."""
    if record.get('schema') != 'singularity.height-calculation.v1':
        raise ValueError('Unsupported calculation schema')
    if record.get('graph_class') != 'finite_simple_cubic' or record.get('q_convention') != 'vol8_lib':
        raise ValueError('Require finite simple cubic graphs and vol8_lib q convention')
    kind = record.get('kind')
    if kind not in ('height', 'log'):
        raise ValueError('kind must be height or log')
    raw = record.get('coefficients', {})
    required = range(0 if kind == 'height' else 1, 9)
    if set(raw) != {str(r) for r in required}:
        raise ValueError('Supply every complete volume through eight, with no extra volumes')
    h = {r: polynomial(raw[str(r)]) for r in required}
    if kind == 'log':
        return h
    if h[0] != {0: F(1)}:
        raise ValueError('Height series must have H0 = 1')
    out = {}
    for n in range(1, 9):
        p = {e: n*x for e, x in h[n].items()}
        for k in range(1, n):
            p = add(p, mul(out[k], h[n-k]), -k)
        out[n] = {e: x/n for e, x in p.items() if x}
    return out


def extract(a, b, panel=None, *, mode='general'):
    """Return invariant differences B-A, conditional on complete calculations."""
    names, panel = model(mode, panel)
    orders = [connected_graph(record) for record in (a, b)] if mode == 'connected' else None
    left, right = log_series(a), log_series(b)
    if orders is not None and any(series[1] != {3: F(n)} for series, n in zip((left, right), orders)):
        raise ValueError('Volume one must agree with supplied graph order')
    for r in range(1, 8):
        if left[r] != right[r]:
            raise ValueError('Lower-order disagreement at volume %s' % r)
    delta = add(right[8], left[8], -1)
    inv, det = invert(matrix(panel, mode=mode))
    values = [sum(x*delta.get(e, 0) for x, e in zip(row, panel)) for row in inv]
    if reconstruct(values, mode=mode) != delta:
        raise ValueError('Eighth polynomial is inconsistent with the %s-coordinate model' % len(names))
    if mode == 'connected' and orders[0] <= 8 and delta:
        raise ValueError('Compatible connected graphs through order eight must have zero difference')
    if any(x.denominator != 1 for x in values):
        raise ValueError('Recovered invariant differences are not integers')
    result = {'schema': 'singularity.volume8.extraction.v1', 'delta': 'B-A',
            'status': 'exact_integer_algebraic_certificate',
            'scope': 'conditional on supplied complete cubic-graph calculations being correct',
            'panel': list(panel), 'determinant': str(det),
            'invariant_differences': dict(zip(names, map(int, values))),
            'full_polynomial_reconstructed': True}
    if mode == 'connected':
        result.update(model='connected', connected_topology_verified=True,
                      omitted_invariant_differences={'S8_12': 0},
                      research_delta_convention='A-B; negate retained witness differences for B-A')
    return result


def sensitivity(samples, radii, panel=PANEL):
    """Conditional linear propagation; no graph compatibility/integer certification."""
    if len(samples) != 7 or len(radii) != 7:
        raise ValueError('Supply seven difference measurements and seven error radii')
    samples, radii = [float(x) for x in samples], [float(x) for x in radii]
    if not all(isfinite(x) for x in samples+radii) or any(x < 0 for x in radii):
        raise ValueError('Require finite samples and nonnegative finite radii')
    inv, _ = invert(matrix(panel))
    estimates = [sum(float(x)*y for x, y in zip(row, samples)) for row in inv]
    bounds = [sum(abs(float(x))*y for x, y in zip(row, radii)) for row in inv]
    if not all(isfinite(x) for x in estimates+bounds):
        raise ValueError('Floating-point overflow')
    return {'status': 'numerical_estimate_only',
            'assumption': 'exact lower agreement and seven-coordinate model; radii bound B-A measurement errors',
            'roundoff': 'bounds estimate measurement propagation only; floating arithmetic is not outward rounded',
            'coordinates': {n: {'estimate': x, 'measurement_error_bound_estimate': e}
                            for n, x, e in zip(NAMES, estimates, bounds)},
            'inverse_infinity_norm': str(max(sum(map(abs, row)) for row in inv))}


def optimize(*, mode='general'):
    """Exhaust all unscaled single-coefficient panels; exact l-infinity error gain."""
    names, _ = model(mode, None)
    degrees = sorted({e for p in factors(mode) for e in p})
    best = None
    total = nonsingular = ties = 0
    for panel in combinations(degrees, len(names)):
        total += 1
        try:
            inv, det = invert(matrix(panel, mode=mode))
        except ValueError:
            continue
        nonsingular += 1
        gain = max(sum(map(abs, row)) for row in inv)
        if best is None or gain < best[0]:
            best = (gain, panel, det); ties = 1
        elif gain == best[0]:
            ties += 1
    return {'objective': 'minimize ||M^-1||_infinity, unscaled coefficient errors bounded equally',
            'candidate_degrees': degrees, 'panels_tested': total, 'nonsingular': nonsingular,
            'optimal_gain': str(best[0]), 'optimal_panel': list(best[1]),
            'optimal_determinant': str(best[2]), 'optimal_panel_count': ties,
            'scope': 'global within %s distinct single q-coefficient measurements, no rescaling' % ('six' if mode == 'connected' else 'seven')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', help='JSON with A and B calculation records')
    parser.add_argument('--mode', choices=('general', 'connected'), default='general')
    parser.add_argument('--optimize', action='store_true')
    parser.add_argument('--panel', choices=('tail', 'optimal'), default=None)
    parser.add_argument('--sensitivity', action='store_true', help='JSON with samples and radii')
    args = parser.parse_args()
    if args.optimize:
        out = optimize(mode=args.mode)
    else:
        if not args.input:
            parser.error('Provide input JSON or --optimize')
        data = json.loads(Path(args.input).read_text())
        if args.mode == 'connected' and (args.sensitivity or args.panel == 'tail'):
            parser.error('Connected mode supports exact extraction with its optimal panel; sensitivity is general-only')
        panel = (CONNECTED_PANEL if args.mode == 'connected' else
                 OPTIMAL_PANEL if args.panel == 'optimal' else PANEL)
        out = (sensitivity(data['samples'], data['radii'], panel) if args.sensitivity else
               extract(data['A'], data['B'], panel, mode=args.mode))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
