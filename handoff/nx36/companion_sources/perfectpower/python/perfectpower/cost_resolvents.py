"""Positive-cost transfer matrices and source-bound quotient transport.

A cost c contributes z^c A_c. V solves (I-sum z^c A_c)V=s as
formal series. Replay checks polynomial/rational identities, not samples.
"""
from copy import deepcopy
from hashlib import sha256
from . import exact_linear as E, polyalg as P
from .observable_machine import _q, _matrix, _apply
from .rational_functions import RationalFunction as RF, AlgebraBudget, solve_many
from .generating_functions import RationalSeries
from .catalogue import encoded
from .divisor_square import WorkLimit


def _source(spec):
    if not isinstance(spec, dict) or set(spec) != {'operators', 'seed', 'readouts'}:
        raise ValueError('operators, seed and readouts required')
    s = tuple(map(_q, spec['seed'])); n = len(s)
    if not 1 <= n <= 256 or not 1 <= len(spec['readouts']) <= 16 or not 1 <= len(spec['operators']) <= 16:
        raise WorkLimit('cost resolvent carrier/readout/operator budget exceeded')
    ops = []
    for op in spec['operators']:
        if not isinstance(op, dict) or set(op) != {'cost', 'matrix'} or type(op['cost']) is not int or not 1 <= op['cost'] <= 16:
            raise ValueError('positive integer action costs 1 through 16 required')
        ops.append({'cost': op['cost'], 'matrix': _matrix(op['matrix'], n, n)})
    return {'operators': ops, 'seed': s, 'readouts': _matrix(spec['readouts'], len(spec['readouts']), n)}


def _polynomial_matrix(source, budget):
    n = len(source['seed'])
    result = [[RF([int(i == j)], budget=budget) for j in range(n)] for i in range(n)]
    for op in source['operators']:
        z = RF([0]*op['cost']+[1], budget=budget)
        for i in range(n):
            for j in range(n):
                result[i][j] -= z*op['matrix'][i][j]
    return result


def cost_resolvent(specification):
    source = _source(specification); budget = AlgebraBudget(degree_limit=256, bit_limit=8192)
    if len(source['seed']) > 12:
        raise WorkLimit('rational elimination dimension exceeds 12; supply a smaller exact quotient')
    matrix = _polynomial_matrix(source, budget)
    rhs = [[RF([v], budget=budget)] for v in source['seed']]
    solution = solve_many(matrix, rhs)
    if solution is None:
        raise AssertionError('positive-cost transfer matrix must be invertible at zero')
    vector = [r[0] for r in solution]
    outputs = [RationalSeries.from_rf(sum((c*v for c, v in zip(row, vector)), RF([0], budget=budget))).summary()
               for row in source['readouts']]
    packet = {'schema': 'pp-cost-resolvent/1', 'source': source,
              'source_sha256': sha256(encoded(source).encode()).hexdigest(),
              'vector': [v.packet() for v in vector], 'outputs': outputs,
              'scope': 'all nonnegative total costs; matrix products retain order and path multiplicity',
              'execution_verified': False}
    if not verify_cost_resolvent(packet, source):
        raise AssertionError('cost resolvent coefficient identity failed')
    return packet


def verify_cost_resolvent(packet, source=None):
    """Check (I-T)V=s and each H*V, without elimination or sequence fitting."""
    try:
        if packet['schema'] != 'pp-cost-resolvent/1' or packet['execution_verified'] is not False:
            return False
        original = _source(packet['source'])
        if len(original['seed']) > 12:
            return False
        if source is not None and encoded(original) != encoded(_source(source)):
            return False
        if packet['source_sha256'] != sha256(encoded(original).encode()).hexdigest():
            return False
        budget = AlgebraBudget(degree_limit=256, bit_limit=8192)
        if len(packet['vector']) != len(original['seed']) or len(packet['outputs']) != len(original['readouts']):
            return False
        vector = [RF.parse(v, budget) for v in packet['vector']]
        if any(not v.d[0] for v in vector):
            return False
        matrix = _polynomial_matrix(original, budget)
        if any(sum((c*v for c, v in zip(row, vector)), RF([0], budget=budget)) != s
               for row, s in zip(matrix, original['seed'])):
            return False
        for h, out in zip(original['readouts'], packet['outputs']):
            expected = sum((c*v for c, v in zip(h, vector)), RF([0], budget=budget))
            actual = RationalSeries({'numerator': out['numerator'], 'denominator': out['denominator']})
            if actual._rf != expected or encoded(actual.summary()) != encoded(out):
                return False
        return True
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError, WorkLimit):
        return False


def cost_quotient(original, encoder, operators, readouts):
    """Accept E A_c=G_c E, D E=H and the encoded seed, cost by cost."""
    source = _source(original); n = len(source['seed']); r = len(encoder)
    if not 1 <= r <= n:
        raise ValueError('nonempty quotient dimension no larger than source required')
    encoder = _matrix(encoder, r, n)
    reduced = _source({'operators': operators, 'seed': _apply(encoder, source['seed']), 'readouts': readouts})
    if len(source['operators']) != len(reduced['operators']) or len(source['readouts']) != len(reduced['readouts']):
        raise ValueError('matching original/reduced operator and output lists required')
    for a, g in zip(source['operators'], reduced['operators']):
        if a['cost'] != g['cost'] or E.multiply(encoder, a['matrix']) != E.multiply(g['matrix'], encoder):
            raise ValueError('cost-specific intertwining identity failed')
    if E.multiply(reduced['readouts'], encoder) != source['readouts']:
        raise ValueError('target output transport failed')
    # Only compile the reduced system. Exact intertwining establishes equality
    # even when the original rational elimination would be much more expensive.
    return {'schema': 'pp-cost-quotient/1', 'original': source, 'encoder': encoder,
            'reduced': reduced, 'resolvent': cost_resolvent(reduced),
            'original_dimension': n, 'reduced_dimension': r,
            'scope': 'same output generating functions at every cost, from exact cost-specific operator transport',
            'execution_verified': False}


def verify_cost_quotient(packet):
    try:
        if packet['schema'] != 'pp-cost-quotient/1' or packet['execution_verified'] is not False:
            return False
        source, reduced = _source(packet['original']), _source(packet['reduced'])
        n, r = len(source['seed']), len(reduced['seed'])
        if (packet['original_dimension'], packet['reduced_dimension']) != (n, r) or r > n:
            return False
        encoder = _matrix(packet['encoder'], r, n)
        if tuple(_apply(encoder, source['seed'])) != reduced['seed']:
            return False
        if len(source['operators']) != len(reduced['operators']):
            return False
        if any(a['cost'] != g['cost'] or E.multiply(encoder, a['matrix']) != E.multiply(g['matrix'], encoder)
               for a, g in zip(source['operators'], reduced['operators'])):
            return False
        if E.multiply(reduced['readouts'], encoder) != source['readouts']:
            return False
        return verify_cost_resolvent(packet['resolvent'], reduced)
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError, WorkLimit):
        return False


def finite_machine_series(model, initial, accepting, costs=None, quotient=True):
    """Count enabled named action words by total cost; disabled paths vanish.

    Acceptance must be constant on future-equivalence blocks before transport.
    Distinct actions with identical destinations are counted separately.
    """
    from .future_states import normalize, future_quotient, check_quotient
    model = normalize(deepcopy(model)); n = len(model['observations'])
    if type(initial) is not int or not 0 <= initial < n or not isinstance(accepting, (list, tuple)) or any(type(s) is not int or not 0 <= s < n for s in accepting) or len(set(accepting)) != len(accepting):
        raise ValueError('valid initial state and distinct accepting state IDs required')
    if type(quotient) is not bool:
        raise ValueError('quotient must be Boolean')
    costs = {a: 1 for a in model['actions']} if costs is None else costs
    if not isinstance(costs, dict) or set(costs) != set(model['actions']):
        raise ValueError('one positive cost for every named action required')
    def source(m, start, final):
        size = len(m['observations']); ops = []
        for a, row in sorted(m['actions'].items()):
            matrix = [[0]*size for _ in range(size)]
            for s, t in enumerate(row):
                if t is not None:
                    matrix[t][s] = 1
            ops.append({'cost': costs[a], 'matrix': matrix})
        return {'operators': ops, 'seed': [int(s == start) for s in range(size)],
                'readouts': [[int(s in final) for s in range(size)]]}
    original = source(model, initial, accepting)
    if not quotient:
        return cost_resolvent(original)
    q = future_quotient(model); check_quotient(q, model)
    final = []
    for i, block in enumerate(q['blocks']):
        statuses = {s in accepting for s in block}
        if len(statuses) != 1:
            raise ValueError('acceptance must be constant on every future-equivalence block')
        if True in statuses:
            final.append(i)
    reduced = source(q['quotient'], q['projection'][initial], final)
    encoder = [[int(q['projection'][s] == i) for s in range(n)] for i in range(len(q['blocks']))]
    packet = cost_quotient(original, encoder, reduced['operators'], reduced['readouts'])
    return {'schema': 'pp-finite-machine-series/1', 'model': model, 'initial': initial,
            'accepting': list(accepting), 'costs': deepcopy(costs), 'future_quotient': q,
            'transport': packet, 'execution_verified': False}


def dynacomp_series(packet, cost=1, initial=None):
    """Read a DynaComp linear packet without importing its discovery code.

    Source/quotient identities are replayed here. Forced systems are exported
    as zero-state impulse series, plus an optional initial-response series.
    """
    required = {'A', 'B', 'C', 'E', 'G', 'H', 'D'}
    if not isinstance(packet, dict) or not required <= set(packet):
        raise ValueError('DynaComp linear packet with A,B,C,E,G,H,D required')
    a, b, c, e, g, h, d = (packet[k] for k in ('A', 'B', 'C', 'E', 'G', 'H', 'D'))
    n, r = len(a), len(g)
    if not 1 <= n <= 256 or not 1 <= r <= min(n, 12):
        raise WorkLimit('DynaComp series carrier budget exceeded')
    a, e, g = _matrix(a, n, n), _matrix(e, r, n), _matrix(g, r, r)
    c, d = _matrix(c, len(c), n), _matrix(d, len(c), r)
    b, h = _matrix(b, n, len(b[0])), _matrix(h, r, len(b[0]))
    if E.multiply(e, b) != h:
        raise ValueError('DynaComp input transport E B=H failed')
    sources = [('input_'+str(i), [row[i] for row in b]) for i in range(len(b[0]))]
    if initial is not None:
        if len(initial) != n:
            raise ValueError('initial state dimension mismatch')
        sources.append(('initial', list(map(_q, initial))))
    # Even a packet without input columns must satisfy transition/output laws.
    if E.multiply(e, a) != E.multiply(g, e) or E.multiply(d, e) != c:
        raise ValueError('DynaComp transition/output transport failed')
    results = {}
    for name, seed in sources:
        original = {'operators': [{'cost': cost, 'matrix': a}], 'seed': seed, 'readouts': c}
        results[name] = cost_quotient(original, e, [{'cost': cost, 'matrix': g}], d)
    return {'schema': 'pp-dynacomp-series/1', 'responses': results,
            'timing': 'input coefficients are C A^n B; for x[t+1]=A x[t]+B u[t], output contribution occurs at t=n+1',
            'execution_verified': False}


def dynacomp_switched_series(packet, initial, costs):
    """Consume actual dynacomp.switched/1 mode transport packets."""
    if not isinstance(packet, dict) or packet.get('schema') != 'dynacomp.switched/1':
        raise ValueError('DynaComp switched packet required')
    modes = packet['modes']
    if not isinstance(costs, dict) or set(costs) != set(modes) or set(packet['G']) != set(modes):
        raise ValueError('one cost and reduced operator for every mode required')
    labels = sorted(modes)
    original = {'operators': [{'cost': costs[k], 'matrix': modes[k]} for k in labels],
                'seed': initial, 'readouts': packet['C']}
    reduced = [{'cost': costs[k], 'matrix': packet['G'][k]} for k in labels]
    result = cost_quotient(original, packet['E'], reduced, packet['D'])
    result['mode_order'] = labels
    result['scope'] += '; aggregation counts ordered mode words, and does not assert word-by-word equivalence from counts alone'
    return result
