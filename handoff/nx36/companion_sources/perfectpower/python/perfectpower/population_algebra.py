"""Boolean algebra of restrictions of one finite, original-object population.

Membership and rank transport use original parameters or integer coordinates,
never projected values, chart numbers, or another population's rank.
"""
from copy import deepcopy
from hashlib import sha256
import json

from .populations import ExactPopulation, _json


class PopulationComparison:
    """Compare two predicates inside an explicitly bounded common universe.

    Specification: {universe: ExactPopulation specification, left: predicate,
    right: predicate}. Domain predicates use polynomial atoms; curve predicates
    use original-coordinate expressions. Parts retain the backend's ordering.
    """
    PARTS = ('universe', 'left', 'right', 'both', 'left_only', 'right_only',
             'neither', 'union', 'symmetric_difference')

    def __init__(self, specification, **budgets):
        if not isinstance(specification, dict) or set(specification) != {'universe', 'left', 'right'}:
            raise ValueError('comparison requires universe, left and right')
        spec = deepcopy(specification)
        universe = ExactPopulation(spec['universe'], **budgets)
        spec['universe'] = universe.specification
        self._spec = _json(spec)
        self._parts = {'universe': universe,
                       'left': universe.restrict(spec['left']),
                       'right': universe.restrict(spec['right'])}
        family = dict(universe.specification)
        family.pop('predicate')
        self._family_id = sha256(('pp-population-family/1\n'+_json(family)).encode()).hexdigest()
        self._comparison_id = sha256(('pp-population-comparison/1\n'+self._spec).encode()).hexdigest()

    @property
    def specification(self):
        return json.loads(self._spec)

    @property
    def comparison_id(self):
        return self._comparison_id

    @property
    def family_id(self):
        return self._family_id

    def population(self, part):
        if part not in self.PARTS:
            raise ValueError('unknown comparison part')
        if part not in self._parts:
            spec = self.specification
            a, b = spec['left'], spec['right']
            neg = lambda p: {'op': 'not', 'args': [p]}
            conjunction = lambda *p: {'op': 'and', 'args': list(p)}
            predicates = {'both': conjunction(a, b),
                          'left_only': conjunction(a, neg(b)),
                          'right_only': conjunction(neg(a), b),
                          'neither': conjunction(neg(a), neg(b)),
                          'union': {'op': 'or', 'args': [a, b]},
                          'symmetric_difference': {'op': 'or', 'args': [
                              conjunction(a, neg(b)), conjunction(neg(a), b)]}}
            self._parts[part] = self._parts['universe'].restrict(predicates[part])
        return self._parts[part]

    def count(self, part='universe'):
        return self.population(part).count()

    def summary(self):
        counts = {k: self.count(k) for k in ('universe', 'left', 'right', 'both',
                                            'left_only', 'right_only', 'neither')}
        if counts['universe'] != sum(counts[k] for k in ('both', 'left_only', 'right_only', 'neither')):
            raise AssertionError('compiled comparison failed its universe partition identity')
        if counts['left'] != counts['both']+counts['left_only'] or counts['right'] != counts['both']+counts['right_only']:
            raise AssertionError('compiled comparison failed its side partition identity')
        counts['union'] = counts['both']+counts['left_only']+counts['right_only']
        counts['symmetric_difference'] = counts['left_only']+counts['right_only']
        return dict(schema='pp-population-comparison/1', comparison_id=self.comparison_id,
                    family_id=self.family_id, counts=counts, specification=self.specification,
                    ordering=self.population('universe').summary()['ordering'],
                    identity='parameter and field schema' if self.specification['universe']['kind']=='domain'
                    else 'original integer point (x,y) and defining equation',
                    execution_verified=False, completeness='inherited from each supported exact population backend')

    def _coordinates(self, record):
        if self.specification['universe']['kind'] == 'domain':
            return {'parameter': record['parameter']}
        return dict(record['values'])

    def _decorate(self, record):
        coordinates = self._coordinates(record)
        addresses = {part: self.population(part).locate(**coordinates) for part in self.PARTS}
        object_id = sha256(('pp-population-object/1\n'+self.family_id+'\n'+_json(coordinates)).encode()).hexdigest()
        category = next(k for k in ('both', 'left_only', 'right_only', 'neither') if addresses[k] is not None)
        return dict(comparison_id=self.comparison_id, object_id=object_id, family_id=self.family_id,
                    category=category, addresses=addresses, record=deepcopy(record))

    def select(self, part, rank):
        return self._decorate(self.population(part).select(rank))

    def locate(self, *, parameter=None, x=None, y=None):
        universe = self.population('universe')
        rank = universe.locate(parameter=parameter, x=x, y=y)
        return None if rank is None else self._decorate(universe.select(rank))

    def classify(self, record, *, source='universe'):
        """Validate a complete source record before recovering its shared identity."""
        population = self.population(source)
        return self._decorate(population.select(population.rank(record)))

    def transport(self, source, rank, target):
        """Return a target record at the same original object, or None if excluded."""
        record = self.population(source).select(rank)
        population = self.population(target)
        target_rank = population.locate(**self._coordinates(record))
        return None if target_rank is None else self.select(target, target_rank)

    def page(self, part, start=0, size=128):
        return [self._decorate(record) for record in self.population(part).page(start, size)]

    def sample(self, part, size, *, seed=0, replace=False):
        return [self._decorate(record) for record in self.population(part).sample(size, seed=seed, replace=replace)]

    def optimize(self, part, objective, *, sense='min'):
        return self.population(part).optimize(objective, sense=sense)

    def evidence(self):
        return dict(schema='pp-population-comparison-evidence/1', summary=self.summary(),
                    parts={k: self.population(k).evidence() for k in self.PARTS},
                    interpretation='Exact Python execution; generic Lean partition laws do not verify this compiler.')
