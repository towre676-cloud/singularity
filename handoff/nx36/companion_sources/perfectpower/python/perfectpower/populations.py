"""Finite exact populations: original objects, reversible ranks and sampling.

Domain configurations retain their parameter as part of object identity. Curve
populations use disjoint explicit charts (or a complete finite point list).
Ranks are chart-major, then increasing parameter; they are not lexicographic
coordinate ranks. Sampling is uniform over these objects under uniform RNG
draws, not over a projection that discards their identities.
"""
from bisect import bisect_right
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import tempfile

from .divisor_square import WorkLimit
from .residue_cover import integer_polynomial
from .semilinear_domains import semilinear_domain, count_domain, contains, select


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _integer(value, name, *, minimum=None, bits=4096):
    if type(value) is not int or minimum is not None and value < minimum:
        raise ValueError(f'{name} must be an integer' + (f' >= {minimum}' if minimum is not None else ''))
    if abs(value).bit_length() > bits:
        raise WorkLimit(f'{name} exceeds bit budget')
    return value


def _evaluate(coefficients, n, bit_limit):
    value = 0
    for c in reversed(coefficients):
        value = value*n+c
        if abs(value).bit_length() > bit_limit:
            raise WorkLimit('configuration field exceeds output bit budget')
    return value


def _finite(domain):
    if domain['cardinality'] is None:
        raise ValueError('a finite population is required; add bounds before sampling or ranking')
    return min((c['interval'][0] for c in domain['cells']), default=0)


class ExactPopulation:
    """Compile once from a domain or curve specification; reuse exact ranks.

Domain spec: {kind:'domain', predicate:..., fields:{name:[coefficients]}}.
Curve spec: {kind:'curve', left:[...], right:[...], predicate:...}.
Species spec: {kind:'species', bound:N, power:d, power_free:k,
divisor_count:tau, omega:total}; optional filters may be omitted.
Use ``restrict`` for an intersection in the same predicate language. The
source specification and records are copied at every public boundary.
"""
    def __init__(self, specification, *, node_limit=100000, period_limit=65536,
                 work_limit=1000000, row_limit=100000, bit_limit=4096):
        for name, value in [('node_limit', node_limit), ('period_limit', period_limit),
                            ('work_limit', work_limit), ('row_limit', row_limit), ('bit_limit', bit_limit)]:
            _integer(value, name, minimum=1)
        self._budgets = dict(node_limit=node_limit, period_limit=period_limit,
                             work_limit=work_limit, row_limit=row_limit, bit_limit=bit_limit)
        spec = deepcopy(specification)
        if not isinstance(spec, dict):
            raise ValueError('population specification must be an object')
        kind = spec.get('kind')
        self._parts = []
        self._points = None
        self._species = None
        if kind == 'domain':
            if set(spec)-{'kind', 'predicate', 'fields'}:
                raise ValueError('unknown domain specification field')
            fields = spec.get('fields', {'n': [0, 1]})
            if not isinstance(fields, dict) or not 1 <= len(fields) <= 64:
                raise ValueError('one through 64 polynomial fields required')
            if any(not isinstance(k, str) or not k.isidentifier() or k.startswith('_') for k in fields):
                raise ValueError('field names must be public identifiers')
            fields = {k: list(integer_polynomial(v)) for k, v in fields.items()}
            spec = dict(kind=kind, predicate=spec.get('predicate', True), fields=fields)
            domain = semilinear_domain(spec['predicate'], node_limit=node_limit,
                                       period_limit=period_limit, work_limit=work_limit)
            start = _finite(domain)
            self._parts.append(dict(chart=0, domain=domain, start=start,
                                    fields={k: dict(numerator=v, denominator=1) for k, v in fields.items()}))
            self._source = domain
            self._identity = 'parameter; projected field values may coincide'
        elif kind == 'curve':
            if set(spec)-{'kind', 'left', 'right', 'predicate'} or not {'left', 'right'} <= set(spec):
                raise ValueError('curve left/right polynomials and optional predicate required')
            from .query_space import CurveSpace
            spec = dict(kind=kind, left=list(integer_polynomial(spec['left'])),
                        right=list(integer_polynomial(spec['right'])), predicate=spec.get('predicate', True))
            self._space = CurveSpace(spec['left'], spec['right'], node_limit=node_limit, period_limit=period_limit)
            result = self._space.query(spec['predicate'], point_limit=row_limit, node_limit=node_limit,
                                       period_limit=period_limit, work_limit=work_limit)
            if not result['complete']:
                raise ValueError('this curve has no complete queryable original-coordinate population')
            if result['solution_count'] is None:
                raise ValueError('a finite population is required; add curve bounds')
            if result['schema'] == 'pp-finite-curve-query/1':
                if result['points'] is None:
                    raise WorkLimit('complete finite curve list exceeds row budget')
                self._points = sorted(tuple(p) for p in result['points'])
            else:
                for row in result['charts']:
                    chart = result['generator']['charts'][row['chart']]
                    self._parts.append(dict(chart=row['chart'], domain=row['domain'], start=_finite(row['domain']),
                                            fields={k: chart[k] for k in ('x', 'y')}))
            self._source = result
            self._identity = 'original integer point (x,y); disjoint chart ownership'
        elif kind == 'species':
            from .species import SpeciesPopulation
            allowed = {'kind', 'bound', 'power', 'power_free', 'divisor_count', 'omega'}
            if set(spec)-allowed or 'bound' not in spec:
                raise ValueError('species bound and supported exponent filters required')
            self._species = SpeciesPopulation(**{k:v for k,v in spec.items() if k != 'kind'},
                                               state_limit=node_limit)
            self._source = self._species.packet()
            spec = dict(kind='species', **self._source['specification'])
            self._identity = 'ordered prime-exponent species; not every realizing integer'
        else:
            raise ValueError('population kind must be domain, curve or species')
        self._spec = _json(spec)
        from .integer_image_index import IntegerImageIndex
        self._images = IntegerImageIndex()
        self._population_id = sha256(('pp-exact-population/1\n'+self._spec).encode()).hexdigest()
        self._ends = []
        total = 0
        for part in self._parts:
            total += part['domain']['cardinality']
            self._ends.append(total)
        self._cardinality = (self._species.count() if self._species is not None else
                             len(self._points) if self._points is not None else total)
        _integer(self.cardinality, 'population cardinality', minimum=0)

    @property
    def cardinality(self):
        return self._cardinality

    @property
    def population_id(self):
        return self._population_id

    @property
    def specification(self):
        return json.loads(self._spec)

    def summary(self):
        return dict(schema='pp-exact-population/1', population_id=self.population_id,
                    cardinality=self.cardinality, specification=self.specification,
                    ordering=('prefix first, then increasing next exponent' if self._species is not None else
                              'lexicographic point list' if self._points is not None else 'chart-major, increasing parameter'),
                    identity=self._identity, execution_verified=False,
                    compilation=dict(parts=len(self._parts), finite_points=self._points is not None))

    def evidence(self):
        return deepcopy(self._source)

    def count(self):
        return self.cardinality

    def page(self, start=0, size=128):
        """Materialize a bounded rank window without traversing earlier objects."""
        _integer(start, 'page start', minimum=0)
        _integer(size, 'page size', minimum=0)
        if size > self._budgets['row_limit']:
            raise WorkLimit('page size exceeds row budget')
        return [self.select(i) for i in range(start, min(start+size, self.cardinality))]

    def next(self, parameter, *, inclusive=False):
        """Next domain configuration in parameter order; None after the finite end."""
        if self.specification['kind'] != 'domain' or type(inclusive) is not bool:
            raise ValueError('next requires a domain population and Boolean inclusive flag')
        n = _integer(parameter, 'parameter')
        part = self._parts[0]
        found = select(part['domain'], 0, start=n if inclusive else n+1)
        return None if found is None else self.select(self.locate(parameter=found))

    def select(self, rank):
        """Return one record; IndexError means the rank is outside the population."""
        _integer(rank, 'rank', minimum=0)
        if rank >= self.cardinality:
            raise IndexError('rank is outside the finite population')
        if self._species is not None:
            from .species import minimum
            from math import prod
            a = self._species.select(rank)
            return dict(population_id=self.population_id, rank=rank, chart=None, parameter=None,
                        species=list(a), values=dict(least_representative=minimum(a), omega=sum(a),
                        divisor_count=prod(e+1 for e in a), distinct_prime_count=len(a)))
        if self._points is not None:
            x, y = self._points[rank]
            _integer(x, 'x', bits=self._budgets['bit_limit'])
            _integer(y, 'y', bits=self._budgets['bit_limit'])
            return dict(population_id=self.population_id, rank=rank, chart=None, parameter=None, values=dict(x=x, y=y))
        index = bisect_right(self._ends, rank)
        part = self._parts[index]
        local = rank-(self._ends[index-1] if index else 0)
        n = select(part['domain'], local, start=part['start'])
        values = {}
        for name, field in part['fields'].items():
            numerator = _evaluate(field['numerator'], n, self._budgets['bit_limit'])
            value, remainder = divmod(numerator, field['denominator'])
            if remainder:
                raise AssertionError('compiled population lost an integer coordinate image')
            values[name] = value
        return dict(population_id=self.population_id, rank=rank, chart=part['chart'], parameter=n, values=values)

    def rank(self, record):
        """Recover rank from identity and values; do not trust a supplied rank."""
        if not isinstance(record, dict) or record.get('population_id') != self.population_id:
            raise ValueError('record belongs to another population')
        if self._species is not None:
            rank = self._species.rank(record.get('species', ()))
        elif self._points is not None:
            from bisect import bisect_left
            values = record.get('values', {})
            if set(values) != {'x', 'y'}:
                raise ValueError('curve point required')
            point = (_integer(values['x'], 'x'), _integer(values['y'], 'y'))
            rank = bisect_left(self._points, point)
            if rank == len(self._points) or self._points[rank] != point:
                raise ValueError('point is outside population')
        else:
            n = _integer(record.get('parameter'), 'parameter')
            chart = _integer(record.get('chart'), 'chart', minimum=0)
            index = next((i for i, p in enumerate(self._parts) if p['chart'] == chart), None)
            if index is None or not contains(self._parts[index]['domain'], n):
                raise ValueError('parameter is outside chart domain')
            part = self._parts[index]
            rank = (self._ends[index-1] if index else 0)+count_domain(part['domain'], part['start'], n-1)
        expected = self.select(rank)
        if self._species is not None and record.get('species') != expected['species']:
            raise ValueError('species identity mismatch')
        if any(type(v) is not int for v in record.get('values', {}).values()) or any(
                record.get(k) != expected[k] for k in ('chart', 'parameter', 'values')):
            raise ValueError('record values do not match its population identity')
        return rank

    def locate(self, *, parameter=None, x=None, y=None, exponents=None):
        """Recover rank from a parameter or original curve point, caching inverse fibres."""
        if self._species is not None:
            if parameter is not None or x is not None or y is not None or exponents is None:
                raise ValueError('species identity requires exponents only')
            try:
                return self._species.rank(exponents)
            except ValueError:
                return None
        if exponents is not None:
            raise ValueError('exponents require a species population')
        if self.specification['kind'] == 'domain':
            if x is not None or y is not None:
                raise ValueError('domain identity is its parameter')
            n = _integer(parameter, 'parameter')
            part = self._parts[0]
            if not contains(part['domain'], n):
                return None
            return count_domain(part['domain'], part['start'], n-1)
        if parameter is not None:
            raise ValueError('curve identity is its original point')
        x, y = _integer(x, 'x'), _integer(y, 'y')
        if self._points is not None:
            from bisect import bisect_left
            index = bisect_left(self._points, (x, y))
            return index if index < len(self._points) and self._points[index] == (x, y) else None
        for index, part in enumerate(self._parts):
            if not part['domain']['cardinality']:
                continue
            nonconstant = [k for k in ('x', 'y') if len(part['fields'][k]['numerator']) > 1]
            if not nonconstant:
                rank = self._ends[index-1] if index else 0
                if self.select(rank)['values'] == dict(x=x, y=y):
                    return rank
                continue
            name = min(nonconstant, key=lambda k: len(part['fields'][k]['numerator']))
            field = part['fields'][name]
            polynomial = list(field['numerator'])
            polynomial[0] -= field['denominator']*({'x': x, 'y': y}[name])
            roots = self._images.fibre(polynomial, node_limit=self._budgets['node_limit'])['roots']
            for n in roots:
                if not contains(part['domain'], n):
                    continue
                rank = (self._ends[index-1] if index else 0)+count_domain(part['domain'], part['start'], n-1)
                if self.select(rank)['values'] == dict(x=x, y=y):
                    return rank
        return None

    def restrict(self, predicate):
        spec = self.specification
        if self._species is not None:
            raise ValueError('species restrictions must be declared as exponent filters in a new specification')
        spec['predicate'] = {'op': 'and', 'args': [spec['predicate'], deepcopy(predicate)]}
        return ExactPopulation(spec, **self._budgets)

    def optimize(self, objective, *, sense='min'):
        """Exact optimum/all ties using the existing domain or original curve backend."""
        if self._species is not None:
            if objective not in ('least_representative', 'omega', 'divisor_count', 'distinct_prime_count') or sense not in ('min', 'max'):
                raise ValueError('species optimization requires a supported invariant and min/max sense')
            if self.cardinality > self._budgets['work_limit']:
                raise WorkLimit('species invariant optimization exceeds exhaustive rank budget')
            best, ties = None, []
            for rank in range(self.cardinality):
                record = self.select(rank)
                value = record['values'][objective]
                if best is None or (value < best if sense == 'min' else value > best):
                    best, ties = value, [record]
                elif value == best:
                    ties.append(record)
            if len(ties) > self._budgets['row_limit']:
                raise WorkLimit('complete species optimum tie set exceeds row budget')
            return dict(value=best, records=ties, objective=objective, sense=sense,
                        method='complete bounded species rank traversal', complete=True)
        budgets = {k: self._budgets[k] for k in ('node_limit', 'period_limit', 'work_limit')}
        if self.specification['kind'] == 'curve':
            return self._space.query(self.specification['predicate'], objective=objective,
                                     sense=sense, point_limit=self._budgets['row_limit'], **budgets)['optimization']
        from .semilinear_domains import optimize_semilinear
        return optimize_semilinear(self.specification['predicate'], objective, sense=sense, **budgets)

    def sample(self, size, *, seed=0, replace=False):
        """Uniform rank draws, or ordered sampling without replacement in O(size) memory.

        Sparse partial Fisher-Yates does not allocate a range(cardinality) list.
        Reproducibility uses Python's Random implementation recorded in exports.
        """
        _integer(size, 'sample size', minimum=0)
        _integer(seed, 'seed')
        if type(replace) is not bool:
            raise ValueError('replace must be Boolean')
        if size > self._budgets['row_limit']:
            raise WorkLimit('sample size exceeds row budget')
        if size and not self.cardinality or not replace and size > self.cardinality:
            raise ValueError('sample size exceeds available population')
        rng = random.Random(seed)
        swaps = {}
        result = []
        for i in range(size):
            if replace:
                rank = rng.randrange(self.cardinality)
            else:
                remaining = self.cardinality-i
                draw = rng.randrange(remaining)
                rank = swaps.get(draw, draw)
                swaps[draw] = swaps.get(remaining-1, remaining-1)
                swaps.pop(remaining-1, None)
            result.append(self.select(rank))
        return result

    def partition(self, shards, index):
        """Contiguous balanced rank shard, represented by [start, stop)."""
        _integer(shards, 'shards', minimum=1)
        _integer(index, 'shard index', minimum=0)
        if index >= shards:
            raise ValueError('shard index must be below shard count')
        return dict(start=self.cardinality*index//shards, stop=self.cardinality*(index+1)//shards)

    def export(self, path, *, size, seed=0, replace=False):
        """Atomically publish JSONL metadata plus records; retain exact large integers."""
        import platform
        records = self.sample(size, seed=seed, replace=replace)
        metadata = dict(schema='pp-population-dataset/1', population=self.summary(), size=size,
                        seed=seed, replace=replace, sampling='sparse-fisher-yates/1' if not replace else 'uniform-rank/1',
                        rng='python.random.Random', python=platform.python_version())
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=path.name+'.', dir=path.parent)
        digest = sha256()
        try:
            with os.fdopen(fd, 'wb') as stream:
                for item in [dict(metadata=metadata), *records]:
                    data = (_json(item)+'\n').encode()
                    stream.write(data)
                    digest.update(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return dict(path=str(path), sha256=digest.hexdigest(), records=size, population_id=self.population_id)
