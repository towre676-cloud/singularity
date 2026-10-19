"""One JSON interface for the exact engines and the recovered mathematics.

This is also the installed-package API used by the Math Lab page and CLI.
Examples are constructed mathematical models. Every result carries its scope;
no example is presented as measured sporting or commercial performance.
"""
from __future__ import annotations

from fractions import Fraction as Q
from importlib.resources import files
import importlib
import json
import math

from .workflow import decision_pipeline, rational


def _integer(value, name, low=0, high=10000):
    if isinstance(value, str) and len(value) <= 310 and value.lstrip('-').isdigit():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _json(value):
    if isinstance(value, Q):
        return value.numerator if value.denominator == 1 else str(value)
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, 'record'):
        return _json(value.record())
    if hasattr(value, 'to_dict'):
        return _json(value.to_dict())
    raise TypeError(f"unsupported result type: {type(value).__name__}")


def _resource(name, fallback):
    path = files('perfectjet').joinpath('resources', name)
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else fallback


def _field(key, label, value, kind='number', low=None, high=None, help=None):
    out = dict(key=key, label=label, value=value, type=kind)
    if low is not None: out['min'] = low
    if high is not None: out['max'] = high
    if help: out['help'] = help
    return out


LABS = [
    dict(id='pipeline', title='Make a complete decision', category='explore', question='What can I choose with the information and budget I have?', description='Recover values, count every feasible portfolio, then separate a winner under declared error bounds.', example={'params': {}}, fields=[_field('uncertainty', 'Measurement uncertainty', 0, low=0, high=20)]),
    dict(id='recover', title='Can we know the answer?', category='know', question='Do these measurements reveal the target?', description='Get an exact recovery formula or a hidden-direction witness and a repair.', example={'params': {}}, fields=[_field('repair', 'Add the missing measurement', False, 'checkbox')]),
    dict(id='compress', title='Keep only the useful state', category='know', question='How small can the world become without losing its future answers?', description='Compile a finite arithmetic model and replay its all-future behavioral quotient.', example={'params': {'prime': 13}}, fields=[_field('prime', 'Arithmetic modulus (prime)', 13, low=2, high=13)]),
    dict(id='count', title='Explore every feasible choice', category='explore', question='How many combinations fit, and which are best?', description='Exact count, optimum, all optimal ties, ranks and conditional inclusion.', example={'params': {}}, fields=[_field('capacity', 'First resource budget', 3, low=0, high=30)]),
    dict(id='series', title='Jump to a distant future', category='explore', question='Can we count a remote history length without stepping through every length?', description='Derive a global recurrence and evaluate it by modular binary powering.', example={'params': {'prime': 7, 'index': '10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', 'modulus': 1000000007}}, fields=[_field('index', 'History length', '100000000000000000000', 'text')]),
    dict(id='features', title='Find exact nonlinear coordinates', category='know', question='Which features make this nonlinear system exactly linear?', description='Add residual-implicated features and replay exact polynomial closure.', example={'params': {}}, fields=[_field('growth', 'Try a system whose degree grows', False, 'checkbox')]),
    dict(id='experiments', title='Choose the next experiment', category='measure', question='What is the cheapest sequence of observations that reveals a hidden target?', description='An adaptive policy remembers the original target through destructive actions.', example={'params': {}}),
    dict(id='allocate', title='Choose measurements together', category='measure', question='Which measurement package is best for the target?', description='Compute exact joint information rather than adding isolated measurement scores.', example={'params': {'budget': 2}}, fields=[_field('budget', 'Measurement budget', 2, low=0, high=3)]),
    dict(id='decision', title='Is the winner separated?', category='check', question='Could the declared errors change the leader?', description='Compare lower and upper bounds across every supplied alternative.', example={'params': {'error': 2}}, fields=[_field('error', 'Error bound per alternative', 2, low=0, high=50)]),
    dict(id='precision', title='Check numerical cancellation', category='check', question='Is a small numerical difference reliable?', description='Expose lost digits, bound recursive summation and repair the sum.', example={'params': {'terms': ['10000000000000000', '1', '-10000000000000000']}}),
    dict(id='moyal', title='Reveal higher-order corrections', category='structure', question='Where does the classical bracket stop being exact?', description='Exact polynomial Moyal arithmetic, with rational coefficients and no floating equality.', example={'params': {'degree': 3}}, fields=[_field('degree', 'Power of q and p', 3, low=1, high=10)]),
    dict(id='hahn', title='Classify an exactness corridor', category='structure', question='Do all active higher-order coefficients vanish?', description='A finite integer gate distinguishes exact rays from deceptive first-order cancellations.', example={'params': {'r': 2, 'decoy': False}}, fields=[_field('r', 'Ray index', 2, low=1, high=30), _field('decoy', 'Try a higher-order decoy', False, 'checkbox')]),
    dict(id='categorical', title='Repair a cyclic obstruction', category='structure', question='Can a larger representation remove this obstruction?', description='Compute the cyclic invariant and an explicit cochain repair on the enlarged group.', example={'params': {'n': 3, 'k': 1}}, fields=[_field('n', 'Cyclic group order', 3, low=2, high=6), _field('k', 'Cocycle class', 1, low=0, high=5)]),
    dict(id='reach', title='Connect hidden sectors', category='structure', question='Do these couplings unlock the whole matrix algebra?', description='Sector connectivity and an exact small generated-algebra replay.', example={'params': {}}),
    dict(id='conductor', title='Transport between arithmetic levels', category='structure', question='Do the Fourier and chirp maps agree between levels?', description='Exact cyclotomic transport and correctly twisted CRT factorization.', example={'params': {}}),
    dict(id='theta', title='Compress a lattice series', category='explore', question='Can this infinite theta coefficient sequence become finite data?', description='Build the finite Dynkin numerator and replay boundary-twisted reciprocity.', example={'params': {}}),
    dict(id='growth', title='Reprice a weighted path population', category='explore', question='Which path types matter, and what changes when their weights change?', description='Exact finite histograms and explicitly scoped subcritical growth bounds.', example={'params': {}}),
    dict(id='branches', title='Keep every outcome channel', category='check', question='When should a retry stop, including silent failures?', description='Conserve branch probabilities and optimize a stated truncated-repeat model.', example={'params': {}}),
    dict(id='analytic', title='Replace repeated analytic work', category='structure', question='Which exact formula replaces this numerical loop or arithmetic sum?', description='Isolated logarithmic charge and visible-ray Dirichlet identities with local factors.', example={'params': {}}),
    dict(id='algebra', title='Carry arithmetic answers back', category='explore', question='What does a Pell history mean in the original equation?', description='Reconstruction, modular cycles, original-domain endpoints and complete word multiplicity.', example={'params': {}}),
    dict(id='partners', title='Build an exact algebraic partner', category='structure', question='Which higher-order gates vanish, and is the remaining dynamics active?', description='Compute exact correction kernels and separate instance proofs from solver-dependent classifications.', example={'params': {'operation':'incidence','degree':5}}, fields=[_field('degree','Partner degree',5,low=3,high=20)]),
    dict(id='deformation', title='Test a beautiful relation', category='check', question='Does the relation survive the allowed perturbations?', description='Exact stationary response separates first-order protection from an accidental equality.', example={'params': {}}),
    dict(id='rank', title='Find exceptional parameters', category='structure', question='Where does rank change?', description='Partition a polynomial matrix into constructible constant-rank cells.', example={'params': {'parameter': 0}}, fields=[_field('parameter', 'Inspect parameter t', 0, low=-10, high=10)]),
    dict(id='lattice', title='Require whole-number settings', category='check', question='Does a rational solution correspond to an integer implementation?', description='Smith divisibility supplies a solution or an exact impossibility certificate.', example={'params': {'rhs': 1}}, fields=[_field('rhs', 'Right side of 2x = rhs', 1, low=-10, high=10)]),
    dict(id='jets', title='Measure motion without nuisance drift', category='measure', question='Which position weights recover acceleration with least stated noise?', description='Exact derivative constraints, minimum-variance weights and a remainder bound.', example={'params': {}}),
]


def catalogue():
    equations = _resource('equations.json', {'equations': []})['equations']
    ranking = _resource('equation_power.json', {'equations': [], 'families': []})
    assignments = ranking.get('assignments', {})
    family_names = {row['rank']: row.get('name', row.get('title')) for row in ranking.get('families', [])}
    ranks = {row['id']: row for row in ranking.get('equations', [])}
    if assignments:
        ranks = {eid: {'family_rank': rank, 'family': family_names.get(rank), 'callable_labs': ranking.get('callable_labs', {}).get(eid, [])} for eid, rank in assignments.items()}
    enriched = [dict(e, **{k: ranks.get(e['id'], {}).get(k) for k in ('family_rank', 'family', 'callable_labs')}) for e in equations]
    from .recovered_requests import schemas
    request_shapes = schemas()
    labs = [dict(lab, request_schema=request_shapes.get(lab['id'])) for lab in LABS]
    return {'schema': 'perfectjet/math-lab-catalogue/1', 'labs': labs,
            'equations': enriched, 'families': ranking.get('families', []),
            'ranking_scope': 'Subjective ordinal mathematical families; definitions and rejected or historical statements retain their evidence status.'}


def _out(lab, summary, metrics, details, ids, scope=None, visual=None):
    title = next((x['title'] for x in LABS if x['id'] == lab), 'PerfectJet Math Lab')
    if visual is None:
        visual = {'kind': 'flow', 'nodes': [{'id': str(i), 'label': label, 'value': value} for i, (label, value) in enumerate(metrics)], 'edges': [[str(i), str(i+1)] for i in range(max(0, len(metrics)-1))]}
    details = dict(details)
    details['visual'] = visual
    return _json({'schema': 'perfectjet/math-lab-result/1', 'lab': lab, 'title': title,
                  'summary': summary, 'metrics': [{'label': k, 'value': v} for k, v in metrics],
                  'details': details, 'visual': visual, 'equation_ids': ids,
                  'scope': scope or 'Exact computation in the supplied mathematical model. No empirical sports or market advantage is inferred.'})


def evaluate(request):
    if not isinstance(request, dict):
        raise ValueError('request must be a JSON object')
    if request.get('operation') == 'math-catalog':
        return catalogue()
    lab, p = request.get('lab', 'overview'), request.get('params', {})
    if not isinstance(p, dict):
        raise ValueError('params must be an object')
    if len(json.dumps(p)) > 50000:
        raise ValueError('Math Lab parameters exceed the interface limit')
    if lab == 'overview':
        cat = catalogue()
        return _out(lab, 'Start with a question. Each card computes an answer with the same exact Python engine used by the command line.', [('Callable tools', len(LABS)), ('Equation entries', len(cat['equations']))], {'labs': LABS}, [])
    if lab == 'pipeline':
        spec = dict(p)
        uncertainty = spec.pop('uncertainty', None)
        if uncertainty is not None:
            spec['observation_errors'] = [rational(uncertainty)] * len(spec.get('observation', [[1, 0], [0, 1]]))
        result = decision_pipeline(spec)
        summary = ('The winner is separated under your declared bounds.' if result['settled'] else
                   ('A missing measurement hides the target; the cheapest supplied sensor repair is available.' if result['repair']['possible'] else 'A missing measurement hides the target; none of the supplied candidate sensors repairs it.') if result['status'] == 'needs_measurement' else
                   'The best values tie exactly. Keep the tied optima or add a preference.' if result['status'] == 'exact_tie' else
                   'The current bounds overlap. Tighten the uncertain inputs before choosing.')
        metrics = [('Feasible portfolios', result['feasible_count']), ('Status', result['status'])]
        if 'selected_value' in result: metrics += [('Leading value', result['selected_value']), ('Value bound', result['selected_error_bound'])]
        values = [{'label': name, 'value': value} for name, value in zip(result['items'], result.get('item_values', []))]
        return _out(lab, summary, metrics, result, ['PJ-E085', 'PJ-E055', 'PJ-E057', 'PJ-E319'], scope=result['scope'], visual={'kind': 'bars', 'values': values})
    if lab == 'recover':
        from .engine import sensing
        observation = p.get('observation', [[1, 1]])
        if p.get('repair'):
            observation = list(observation) + [[1, -1]]
        target = p.get('target', [[1, -1]])
        candidates = p.get('candidates', [[1, -1]])
        if not target or len(observation) > 12 or len(target) > 12 or len(candidates) > 12 or any(not x or len(x) > 12 for x in observation + target + candidates):
            raise ValueError('recover supports at most 12 rows and columns')
        width = len(target[0])
        if any(len(row) != width for row in observation + target + candidates):
            raise ValueError('recover measurement, target and candidate widths must match')
        result = sensing([[rational(x) for x in row] for row in observation], [[rational(x) for x in row] for row in target], [[rational(x) for x in row] for row in candidates])
        solved = result['answer'] is not None
        return _out(lab, 'The target is determined by these measurements.' if solved else 'Two states can have identical measurements and different target values. The hidden direction explains what to measure.', [('Measurement rows', len(observation)), ('Target recoverable', solved)], result, ['PJ-E085', 'PJ-E088', 'PJ-E315'])
    if lab in ('compress', 'series'):
        from .observatory.examples import arithmetic_interferometer
        from .observatory.model import compile_system, replay_compilation
        from .observatory.series import compile_series
        prime = _integer(p.get('prime', 13 if lab == 'compress' else 7), 'prime', 2, 13)
        model = arithmetic_interferometer(prime, lifted=True)
        compiled = compile_system(model)
        if lab == 'compress':
            result = {'original_states': model.n, 'quotient_states': compiled.system.n,
                      'blocks': compiled.blocks, 'mapping': compiled.mapping,
                      'replayed': replay_compilation(model, compiled), 'model': compiled.system.to_dict()}
            return _out(lab, 'States with identical specified futures now share one state. Every original state and action is replayed.', [('Original states', model.n), ('Behavior classes', compiled.system.n)], result, ['PJ-E076', 'PJ-E079', 'PJ-E407'], visual={'kind': 'bars', 'values': [{'label': 'Original', 'value': model.n}, {'label': 'Behavior', 'value': compiled.system.n}]})
        series = compile_series(compiled.system, compiled.mapping[model.initial])
        index = _integer(p.get('index', 10**100), 'index', 0, 10**300)
        modulus = _integer(p.get('modulus', 1000000007), 'modulus', 2, 10**18)
        result = {'series': series.record(), 'index': str(index), 'modulus': modulus,
                  'coefficient': series.coefficient(index, modulus), 'prefix': series.coefficients(20)}
        return _out(lab, 'A whole-state identity proves the recurrence at every later length. The remote answer is a residue modulo the displayed modulus.', [('Global recurrence order', series.order), ('History residue', result['coefficient']), ('Modulus', modulus)], result, ['PJ-E413', 'PJ-E414'], visual={'kind': 'bars', 'values': [{'label': str(i), 'value': n} for i, n in enumerate(result['prefix'])]})
    if lab == 'count':
        from .populations import SelectionPopulation
        costs = p.get('costs', [[2, 1], [1, 2], [2, 2], [0, 1]])
        caps = p.get('capacities', [_integer(p.get('capacity', 3), 'capacity', 0, 10000), 3])
        values = [rational(x) for x in p.get('values', [4, 3, 5, 0])]
        if len(costs) > 18 or not caps or len(caps) > 3 or any(isinstance(x, bool) for x in caps) or any(isinstance(x, bool) for row in costs for x in row):
            raise ValueError('count supports at most 18 items and 3 integral resources')
        pop = SelectionPopulation(costs, caps, values)
        selected = _integer(p.get('rank', 0), 'rank', 0, max(0, pop.count()-1))
        result = {'count': pop.count(), 'optimum': pop.optimum(), 'selected_rank': selected,
                  'selected': pop.unrank(selected), 'inclusion': pop.inclusion_profile(), 'attribution': pop.attribution()}
        return _out(lab, 'Every counted combination fits the stated resources. Rank moves directly through the complete feasible population.', [('Feasible choices', pop.count()), ('Best value', result['optimum']['value']), ('Optimal ties', result['optimum']['tie_count'])], result, ['PJ-E055', 'PJ-E057', 'PJ-E058', 'PJ-E323'])
    if lab == 'features':
        from .polynomial import Poly
        from .engine import adaptive_closure
        x, y = Poly.variable(0, 2), Poly.variable(1, 2)
        if p.get('growth'):
            result = adaptive_closure([x*x, y], [x], max_features=20, max_degree=6)
        else:
            result = adaptive_closure([x*Q(1, 2), y*Q(1, 3)+x*x], [y+12*x*x], max_features=20, max_degree=6)
        representation = result['representation']
        return _out(lab, 'The retained features close exactly under evolution.' if result['answer'] else 'The next pullback grows beyond this feature budget; the missing terms are exposed.', [('Retained coordinates', representation.get('minimal_dimension', representation.get('size', 0))), ('Closure found', result['answer'] is not None)], result, ['PJ-E094', 'PJ-E095', 'PJ-E321'])
    if lab == 'experiments':
        from .observatory.examples import protocol_machine, irreversible_machine
        from .observatory.experiments import adaptive_experiment
        model = irreversible_machine() if p.get('destructive') else protocol_machine()
        result = adaptive_experiment(model, prefix=p.get('prefix', []))
        return _out(lab, 'The policy chooses its next action from the observed branch and keeps the initial target in memory.', [('States', model.n), ('Policy status', result.get('status', 'computed')), ('Worst-case cost', result.get('worst_cost'))], result, ['PJ-E411', 'PJ-E412'])
    if lab == 'allocate':
        from .applications.nfl_scouting.allocation import TargetInformationModel, MeasurementCandidate
        model = TargetInformationModel([[1, 0], [0, 1]], [1, 0])
        candidates = (MeasurementCandidate('direct', (1, 0), 1, 1), MeasurementCandidate('mixed', (1, 1), Q(1, 10), 1), MeasurementCandidate('nuisance', (0, 1), Q(1, 10), 1))
        result = model.optimize_package(candidates, _integer(p.get('budget', 2), 'budget', 0, 3))
        isolated = {c.candidate_id: model.package_information([c])['target_variance_reduction'] for c in candidates}
        result['isolated_values'] = isolated
        return _out(lab, 'The best package is computed jointly. A measurement with zero isolated value can unlock another measurement.', [('Selected package', ', '.join(result['candidate_ids']) or 'none'), ('Joint information value', result['objective_reduction']), ('Feasible packages', result['feasible_count'])], result, ['PJ-E366', 'PJ-E367', 'PJ-E374'], scope='Exact supplied Gaussian example with frozen covariance and loadings. This is information value, not profit or demonstrated prediction gain.', visual={'kind': 'bars', 'values': [{'label': k, 'value': v} for k, v in isolated.items()] + [{'label': 'Best package', 'value': result['objective_reduction']}]})
    if lab == 'decision':
        from .decisions import certified_choice
        error = rational(p.get('error', 2))
        raw = p.get('bounds', {'A': [100, error], 'B': [92, error], 'C': [75, error]})
        if not raw or len(raw) > 100:
            raise ValueError('1..100 alternatives are required')
        bounds = {str(k): (rational(v[0]), rational(v[1])) for k, v in raw.items()}
        if any(v[1] < 0 for v in bounds.values()): raise ValueError('error bounds must be nonnegative')
        result = certified_choice(bounds)
        result['bounds'] = bounds
        return _out(lab, 'One lower bound exceeds every rival upper bound.' if result['settled'] else 'The contenders overlap; the present bounds do not certify a winner.', [('Settled', result['settled']), ('Leader', result['leader']), ('Separation margin', result['margin'])], result, ['PJ-E110', 'PJ-E319'], visual={'kind': 'bars', 'values': [{'label': k, 'value': v[0]} for k, v in bounds.items()]})
    if lab == 'moyal':
        from .moyal import PolyH, scaled_moyal_bracket, poisson_bracket, classify_defect, covariance_example
        degree = _integer(p.get('degree', 3), 'degree', 1, 10)
        q, pp = PolyH.q(1, 0), PolyH.p(1, 0)
        f, g = q**degree, pp**degree
        bracket, poisson = scaled_moyal_bracket(f, g), poisson_bracket(f, g)
        defect = bracket - poisson
        result = {'degree': degree, 'poisson': str(poisson), 'moyal': str(bracket), 'defect': str(defect), 'classification': classify_defect(defect), 'covariance': covariance_example()}
        return _out(lab, 'Every polynomial correction is computed exactly; central and dynamically varying defects remain distinct.', [('Degree', degree), ('Higher corrections vanish', defect.is_zero()), ('Defect', str(defect))], result, ['PJ-E418', 'PJ-E419', 'PJ-E420'])
    if lab == 'hahn':
        from .hahn import classify_pair
        r = _integer(p.get('r', 2), 'r', 1, 30)
        pair = (1, 4, 3*r+2, 2*r) if p.get('decoy') else (1, 3, 3*r+2, r)
        result = classify_pair(*pair)
        return _out(lab, 'All active odd coefficients are checked, including the higher terms that reject a first-correction decoy.', [('Monomial exponents', ', '.join(map(str, pair))), ('Classification', result.get('classification', result.get('class', 'computed')))], result, ['PJ-E422', 'PJ-E423', 'PJ-E424'])
    if lab in ('categorical', 'reach'):
        module = importlib.import_module('.categorical', __package__)
        result = module.receipt()
        if lab == 'categorical':
            n = _integer(p.get('n', 3), 'n', 2, 6)
            k = _integer(p.get('k', 1), 'k', 0, n-1)
            result = module.cyclic_repair(n, k)
            return _out(lab, 'The original cyclic obstruction is measured, then its pullback is explicitly repaired on the larger group.', [('Original group order', n), ('Repair group order', n*n), ('Cocycle class', k)], result, ['PJ-E425', 'PJ-E426'])
        if p:
            from .recovered_requests import evaluate as recovered_evaluate
            result = recovered_evaluate(lab, p)
            metrics = [('Generated dimension', result.get('generated_algebra_dimension', 'computed'))]
        else:
            metrics = [('Computed examples', len(result['reach_algebras']))]
        return _out(lab, 'Cross-sector coupling changes the algebra. A connected sector graph unlocks every block under the stated full-block assumptions.', metrics, result, ['PJ-E427'])
    if lab in ('conductor', 'theta'):
        if p:
            from .recovered_requests import evaluate as recovered_evaluate
            result = recovered_evaluate(lab, p)
            return _out(lab, 'The supplied arithmetic-level request is computed with its exact conventions and scope.', [('Computation', 'completed')], result, ['PJ-E428', 'PJ-E429'] if lab == 'conductor' else ['PJ-E430', 'PJ-E431'])
        result = importlib.import_module('.conductor_transport', __package__).receipt()
        detail = result if lab == 'conductor' else result['theta']
        return _out(lab, 'The level maps replay exactly in cyclotomic arithmetic.' if lab == 'conductor' else 'A finite numerator represents the lattice series and preserves its twisted reciprocity.', [('Exact transport cases', len(result['transport']))] if lab == 'conductor' else [('Lattice rank', detail['rank']), ('Conductor', detail['conductor'])], detail, ['PJ-E428', 'PJ-E429'] if lab == 'conductor' else ['PJ-E430', 'PJ-E431'])
    if lab in ('precision', 'growth', 'branches', 'analytic'):
        module_name = {'precision': 'precision', 'growth': 'weighted_growth', 'branches': 'branch_channels', 'analytic': 'analytic_recovery'}[lab]
        module = importlib.import_module('.'+module_name, __package__)
        if lab == 'precision' and 'terms' in p:
            terms = p['terms']
            if not isinstance(terms, list) or not 1 <= len(terms) <= 200:
                raise ValueError('precision requires 1..200 terms')
            result = {'analysis': module.analyze_sum(terms), 'repair': module.repair_sum(terms)}
        elif lab in ('growth', 'branches', 'analytic'):
            from .recovered_requests import evaluate as recovered_evaluate
            result = recovered_evaluate(lab, p)
        else:
            result = module.receipt()
        summaries = {'precision': 'The calculation reports cancellation, a stated roundoff bound and a repaired sum. Data and model errors remain separate.', 'growth': 'The finite weighted population is computed exactly; infinite tails use explicitly stated domination assumptions.', 'branches': 'All outcome channels conserve probability. Retry cost and silent failures remain separate in the selected policy.', 'analytic': 'The analytic replacement keeps its loop geometry, branch convention and arithmetic local factors explicit.'}
        return _out(lab, summaries[lab], [('Computation', 'completed')], result, {'precision': ['PJ-E432', 'PJ-E433'], 'growth': ['PJ-E434', 'PJ-E435'], 'branches': ['PJ-E436', 'PJ-E437'], 'analytic': ['PJ-E438', 'PJ-E439']}[lab])
    if lab == 'algebra':
        module = importlib.import_module('.algebra_bridges', __package__)
        result = module.receipt() if not p else module.evaluate(p.get('operation', 'pell_histories'), p)
        return _out(lab, 'The result retains its original coordinates, domain and seeded-orbit completeness scope.', [('Computation', 'completed')], result, ['PJ-E326', 'PJ-E417', 'PJ-E440', 'PJ-E441'])
    if lab == 'partners':
        from .recovered_partners import receipt, evaluate as partner_evaluate
        result = dict(receipt(), incidence=partner_evaluate('incidence', {})) if not p else partner_evaluate(p.get('operation', 'r5'), {k: v for k, v in p.items() if k != 'operation'})
        return _out(lab, 'Exact gates are replayed for the supplied form. Global degree 6–20 classifications depend on archived external solver receipts; degrees 21 and above remain open.', [('Computation', 'completed')], result, ['PJ-E332', 'PJ-E333', 'PJ-E334', 'PJ-E444', 'PJ-E455', 'PJ-E462'])
    if lab == 'deformation':
        from .deformation import deformation_receipt
        result = deformation_receipt()
        return _out(lab, 'The mirror relation survives the stated symmetric perturbations at first order; a fixed numerical location does not.', [('Perturbation directions', 3)], result, ['PJ-E220', 'PJ-E221', 'PJ-E324', 'PJ-E325'])
    if lab == 'rank':
        from . import parametric as poly
        t, zero, one = poly.var(0, 1), poly.const(0, 1), poly.const(1, 1)
        cells = poly.rank_cells([[t, zero], [zero, one]], 1)
        at = rational(p.get('parameter', 0))
        result = {'matrix': [['t', '0'], ['0', '1']], 'cells': [{**c, 'equations': [poly.fmt(x) for x in c['equations']], 'inequations': [poly.fmt(x) for x in c['inequations']]} for c in cells], 'parameter': at, 'selected_cell': poly.classify(cells, [at])}
        return _out(lab, 'The whole parameter line is split into t=0 and t≠0, where the ranks differ.', [('Parameter cells', len(cells)), ('Inspected parameter', at)], result, ['PJ-E303', 'PJ-E306', 'PJ-E307'])
    if lab == 'lattice':
        from .engine import integer_problem
        rhs = _integer(p.get('rhs', 1), 'rhs', -100000, 100000)
        result = integer_problem([[2]], [rhs])
        return _out(lab, 'Divisibility determines whether the rational setting can be implemented with an integer.', [('Equation', f'2x = {rhs}'), ('Integer solution exists', result['answer'] is not None)], result, ['PJ-E050', 'PJ-E051', 'PJ-E296'])
    if lab == 'jets':
        from .stopped_jets import minimum_variance_jet, derivative_remainder_bound
        times = [Q(i, 10) for i in range(6)]
        result = minimum_variance_jet(times, 2, 3)
        result['remainder_bound_with_fourth_derivative_bound_one'] = derivative_remainder_bound(times, result['weights'], 3, 1)
        return _out(lab, 'These six position weights cancel constant position and velocity while recovering cubic-polynomial midpoint acceleration.', [('Samples', 6), ('Conditional variance per unit noise', result['variance']), ('Weights sum', sum(result['weights']))], result, ['PJ-E395', 'PJ-E397', 'PJ-E399'], visual={'kind': 'bars', 'values': [{'label': str(t), 'value': w} for t, w in zip(times, result['weights'])]})
    raise ValueError(f'unknown Math Lab tool: {lab}')


def main(argv=None):
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Run the same exact Math Lab computations as the local browser.')
    parser.add_argument('--lab', default='overview', choices=['overview'] + [x['id'] for x in LABS])
    parser.add_argument('--request', type=Path, help='JSON request with lab and params')
    parser.add_argument('--catalog', action='store_true')
    parser.add_argument('--all', action='store_true', help='recompute every supplied example')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if sum([bool(args.request), args.catalog, args.all]) > 1:
        parser.error('choose request, catalog or all')
    try:
        if args.catalog:
            result = catalogue()
        elif args.all:
            result = {'schema': 'perfectjet/math-lab-replay/1', 'examples': {x['id']: evaluate({'lab': x['id'], 'params': x['example']['params']}) for x in LABS}}
        else:
            request = json.loads(args.request.read_text()) if args.request else {'lab': args.lab}
            result = evaluate(request)
    except (ValueError, KeyError, TypeError, IndexError) as error:
        parser.error(str(error))
    content = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
    else:
        print(content, end='')


if __name__ == '__main__':
    main()
