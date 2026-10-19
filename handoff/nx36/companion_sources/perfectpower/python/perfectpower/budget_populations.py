"""Queryable weighted-budget tuples using rational generating functions.

Rank/select use coefficient differences and binary search, never scan the
coordinate range. Equal weights still represent distinct original coordinates.
"""
from copy import deepcopy
from .generating_functions import RationalSeries, ONE, _index
from .rational_functions import RationalFunction as RF
from .divisor_square import WorkLimit


class BudgetPopulation:
    def __init__(self, specification):
        if not isinstance(specification, dict) or set(specification) != {'coordinates'}:
            raise ValueError('coordinates required')
        coords = specification['coordinates']
        if not isinstance(coords, (list, tuple)) or not 1 <= len(coords) <= 16:
            raise ValueError('1 through 16 coordinates required')
        self.specification = deepcopy(specification)
        self.coordinates = []
        for row in coords:
            if not isinstance(row, dict) or set(row)-{'weight', 'lower', 'upper', 'modulus', 'residue'} or 'weight' not in row:
                raise ValueError('weighted nonnegative coordinate specification required')
            w, lo, hi, m, r = (row.get(k, d) for k, d in
                              [('weight', 1), ('lower', 0), ('upper', None), ('modulus', 1), ('residue', 0)])
            if any(type(v) is not int for v in (w, lo, m, r)) or not 1 <= w <= 256 or not 1 <= m <= 256 or not 0 <= lo < 2**64 or not 0 <= r < m:
                raise ValueError('positive bounded weights/moduli and nonnegative lower bounds required')
            if hi is not None and (type(hi) is not int or not 0 <= hi < 2**64):
                raise ValueError('nonnegative upper bound or null required')
            first = lo+(r-lo) % m
            count = None if hi is None else max(0, (hi-first)//m+1)
            self.coordinates.append((w, first, m, count))
        self.offset = sum(w*a for w, a, _, _ in self.coordinates)
        self.empty = any(c == 0 for _, _, _, c in self.coordinates)
        self.suffix = [ONE]*(len(coords)+1)
        self.suffix_offsets = [0]*(len(coords)+1)
        self.prefix_kernels = [None]*len(coords)
        for i in reversed(range(len(coords))):
            w, a, m, count = self.coordinates[i]; step = w*m
            if step > 256 or count is not None and step*count > 256:
                raise WorkLimit('coordinate generating-function degree budget exceeded')
            den = [1]+[0]*(step-1)+[-1]
            num = [1] if count is None else [0] if count == 0 else [1]+[0]*(step*count-1)+[-1]
            self.prefix_kernels[i] = RationalSeries.from_rf(self.suffix[i+1]._fresh() / RF(den))
            self.suffix[i] = RationalSeries({'numerator': num, 'denominator': den}) * self.suffix[i+1]
            self.suffix_offsets[i] = w*a+self.suffix_offsets[i+1]

    def summary(self):
        return {'schema': 'pp-budget-population/1', 'specification': deepcopy(self.specification),
                'offset': self.offset, 'empty': self.empty, 'ordering': 'lexicographic original coordinate tuple',
                'scope': 'nonnegative integer tuples satisfying the supplied coordinate restrictions and exact weighted budget',
                'execution_verified': False}

    def evidence(self):
        return dict(self.summary(), series={'shift': self.offset, 'rational_part': self.suffix[0].summary()},
                    rank_method='coefficient differences and binary search over each original coordinate')

    def count(self, budget, modulus=None):
        _index(budget)
        if self.empty or budget < self.offset:
            return 0
        return int(self.suffix[0].coefficient(budget-self.offset, modulus))

    def cumulative_count(self, budget, modulus=None):
        _index(budget)
        if self.empty or budget < self.offset:
            return 0
        return int(self.suffix[0].prefix_sums().coefficient(budget-self.offset, modulus))

    def _prefix(self, i, remaining, last_index):
        if last_index < 0:
            return 0
        w, a, m, count = self.coordinates[i]
        if count is not None:
            last_index = min(last_index, count-1)
        n = remaining-self.suffix_offsets[i]
        if n < 0 or last_index < 0:
            return 0
        kernel = self.prefix_kernels[i]
        end = n-w*m*(last_index+1)
        return int(kernel.coefficient(n) - (kernel.coefficient(end) if end >= 0 else 0))

    def select(self, budget, rank):
        _index(budget)
        if type(rank) is not int or rank < 0:
            raise ValueError('nonnegative rank required')
        if rank >= self.count(budget):
            raise ValueError('rank outside this budget population')
        remaining, point = budget, []
        for i, (w, a, m, count) in enumerate(self.coordinates):
            high = (remaining-self.suffix_offsets[i])//(w*m)
            if count is not None:
                high = min(high, count-1)
            low = 0
            while low < high:
                mid = (low+high)//2
                if self._prefix(i, remaining, mid) > rank:
                    high = mid
                else:
                    low = mid+1
            rank -= self._prefix(i, remaining, low-1)
            value = a+m*low; point.append(value); remaining -= w*value
        if remaining or rank:
            raise AssertionError('coefficient rank decomposition failed')
        return point

    def rank(self, budget, point):
        _index(budget)
        if not isinstance(point, (list, tuple)) or len(point) != len(self.coordinates):
            raise ValueError('original coordinate tuple required')
        remaining, rank = budget, 0
        for i, (value, (w, a, m, count)) in enumerate(zip(point, self.coordinates)):
            if type(value) is not int or value < a or (value-a) % m or count is not None and (value-a)//m >= count:
                raise ValueError('point outside coordinate domain')
            rank += self._prefix(i, remaining, (value-a)//m-1)
            remaining -= w*value
        if remaining:
            raise ValueError('point does not have the supplied weighted budget')
        return rank

    def page(self, budget, start=0, size=20):
        if type(start) is not int or start < 0 or type(size) is not int or not 0 <= size <= 256:
            raise ValueError('nonnegative start and page size at most 256 required')
        total = self.count(budget)
        return [self.select(budget, k) for k in range(start, min(total, start+size))]
