"""Exact completion-count planning over allocations or positive-cost words.

Counts, optimal tie counts and suffix objectives share one acyclic fold.
Resource saturation merges only slack exceeding every possible suffix use.
Python execution is tested, not formally verified. WorkLimit never means empty.
"""
from copy import deepcopy
from fractions import Fraction as Q
from math import prod, lcm
from bisect import bisect_left
from random import SystemRandom
from collections import namedtuple
from .divisor_square import WorkLimit
from .budget_populations import BudgetPopulation
from .future_states import normalize, future_quotient, check_quotient

Entry = namedtuple('Entry', 'count best optimal_count')
EMPTY = Entry(0, None, 0)
UNIT = Entry(1, Q(0), 1)


def integer(v, lo, hi, name):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(f'{name}: integer in {lo}..{hi} required')
    return v


def rational(v):
    if isinstance(v, (bool, float)):
        raise ValueError('exact rational profit required')
    q = Q(v)
    if max(abs(q.numerator).bit_length(), q.denominator.bit_length()) > 4096:
        raise WorkLimit('profit exceeds arithmetic budget')
    return q


def bounded_score(q):
    if max(abs(q.numerator).bit_length(), q.denominator.bit_length()) > 8192:
        raise WorkLimit('objective arithmetic exceeds 8192 bits')
    return q


class CompletionPlanner:
    def __init__(self, specification, *, _reuse=None, _compile=True, _progress=None):
        if not isinstance(specification, dict):
            raise ValueError('planner specification required')
        self._progress = _progress
        self._specification = deepcopy(specification)
        spec = deepcopy(specification)
        self.kind = spec.get('kind')
        allowed = {'kind', 'strategy', 'state_limit', 'edge_limit', 'enumeration_limit', 'binary_limit', 'reduce_machine', 'native_record_limit', 'native_visit_limit', 'population_memory_limit', 'population_cache_states', 'population_partition_limit', 'population_work_limit'}
        allowed |= {'variables', 'resources', 'machine'} if self.kind == 'allocation' else {'machine', 'actions', 'budget'}
        if self.kind not in ('allocation', 'words') or set(spec)-allowed:
            raise ValueError('allocation or words planner with declared fields required')
        self.state_limit = integer(spec.get('state_limit', 200000), 1, 1000000, 'state_limit')
        self.edge_limit = integer(spec.get('edge_limit', 2000000), 1, 4000000, 'edge_limit')
        self.enum_limit = integer(spec.get('enumeration_limit', 4096), 1, 1000000, 'enumeration_limit')
        self.binary_limit = integer(spec.get('binary_limit', 20), 1, 20, 'binary_limit')
        self.native_records = integer(spec.get('native_record_limit', 1100000), 1, 2200000, 'native_record_limit')
        self.native_visits = integer(spec.get('native_visit_limit', 2000000000), 1, 2000000000, 'native_visit_limit')
        self.population_memory = integer(spec.get('population_memory_limit', 128*1024*1024), 1024*1024, 1024*1024*1024, 'population_memory_limit')
        self.population_cache_states = integer(spec.get('population_cache_states', 1000000), 0, 8000000, 'population_cache_states')
        self.population_partition_limit = integer(spec.get('population_partition_limit', 8192), 1, 65536, 'population_partition_limit')
        self.population_work_limit = integer(spec.get('population_work_limit', 2000000000), 1, 100000000000, 'population_work_limit')
        self.reduce = spec.get('reduce_machine', True)
        if type(self.reduce) is not bool:
            raise ValueError('reduce_machine must be Boolean')
        self.requested_strategy = spec.get('strategy', 'auto')
        if self.requested_strategy not in ('auto', 'enumeration', 'gray', 'dp', 'gf', 'symmetry', 'mitm', 'population'):
            raise ValueError('unknown planning strategy')
        self.memo, self.states, self.edges, self.failed = {}, 0, 0, False
        self.query_arcs = {}
        self.index_views, self.selected_plans, self.selected_ranks = {}, {}, {}
        self.compiled_candidates = 0
        self.quotient = None
        self._machine(spec.get('machine'))
        if self.kind == 'allocation':
            self._allocation(spec)
        else:
            self._words(spec)
        self.reused_entries = 0
        if not _compile:
            return
        if _reuse is not None:
            old = _reuse.specification; old['resources'] = self.specification.get('resources')
            if old != self.specification:
                raise ValueError('memo reuse requires the same source apart from resource limits')
            if self.kind == 'allocation' and self.strategy == _reuse.strategy == 'dp':
                self.memo = dict(_reuse.memo)
                self.reused_entries = len(self.memo)
        if self.strategy == 'symmetry':
            from .planning_symmetry import SymmetryIndex
            self.index = SymmetryIndex(self)
            self.root_entry = Entry(*self.index.query(()))
        elif self.strategy in ('mitm', 'population'):
            from .planning_native import NativeIndex, PopulationIndex
            try:
                self.index = (PopulationIndex if self.strategy == 'population' else NativeIndex)(self)
                self.root_entry = self._indexed_entry(())
            except WorkLimit as error:
                if self.requested_strategy != 'auto' or not str(error).startswith('optional native planner'):
                    raise
                self.strategy = 'gray' if len(self.variables)<=self.binary_limit else 'dp'
                if self.strategy == 'gray':
                    self._gray(); self.root_entry = self.gray_entry
                else:
                    self.root_entry = self._entry(self.root)
        elif self.strategy == 'enumeration':
            self._enumerate()
            self.root_entry = self.enum_entry
        elif self.strategy == 'gray':
            self._gray()
            self.root_entry = self.gray_entry
        elif self.strategy == 'dp':
            self.root_entry = self._entry(self.root)
        else:
            self.root_entry = self._gf_entry(())

    @property
    def specification(self):
        return deepcopy(self._specification)

    def _machine(self, packet):
        if packet is None:
            self.actions, self.initial, self.accepting = {}, 0, frozenset({0})
            self.machine_model = None
            return
        if not isinstance(packet, dict) or set(packet) != {'model', 'initial', 'accepting'}:
            raise ValueError('machine requires model, initial and accepting')
        model = normalize(packet['model']); n = len(model['observations'])
        initial = integer(packet['initial'], 0, n-1, 'initial')
        final = packet['accepting']
        if not isinstance(final, list) or any(type(s) is not int or not 0 <= s < n for s in final) or len(set(final)) != len(final):
            raise ValueError('distinct accepting state IDs required')
        # Acceptance is a protected observation, even when the supplied
        # observations alone would incorrectly merge accepting/nonaccepting states.
        model['observations'] = [{'source': o, 'accepting': s in final} for s, o in enumerate(model['observations'])]
        self.machine_model = deepcopy(model)
        if self.reduce:
            self.quotient = future_quotient(model); check_quotient(self.quotient, model)
            initial = self.quotient['projection'][initial]
            final = sorted({self.quotient['projection'][s] for s in final})
            model = self.quotient['quotient']
        self.actions = {a: tuple(row) for a, row in model['actions'].items()}
        self.initial, self.accepting = initial, frozenset(final)

    def _allocation(self, spec):
        resources, variables = spec.get('resources'), spec.get('variables')
        if not isinstance(resources, list) or not 1 <= len(resources) <= 16 or not isinstance(variables, list) or not 1 <= len(variables) <= 64:
            raise ValueError('1..16 resources and 1..64 variables required')
        lows, highs, names = [], [], set()
        for row in resources:
            if not isinstance(row, dict) or set(row)-{'name', 'min', 'max'} or not {'name', 'max'} <= set(row):
                raise ValueError('resource name, max and optional min required')
            name = row['name']
            if type(name) is not str or not name or name in names:
                raise ValueError('distinct resource names required')
            names.add(name)
            lo = integer(row.get('min', 0), 0, 2**64-1, 'resource minimum')
            hi = integer(row['max'], lo, 2**64-1, 'resource maximum')
            lows.append(lo); highs.append(hi)
        self.lower, self.upper = tuple(lows), tuple(highs)
        self.variables, names = [], set()
        for row in variables:
            if not isinstance(row, dict) or set(row)-{'name', 'costs', 'profit', 'lower', 'upper', 'modulus', 'residue', 'actions'} or not {'name', 'costs', 'upper'} <= set(row):
                raise ValueError('named variable with costs and upper bound required')
            name, costs = row['name'], row['costs']
            if type(name) is not str or not name or name in names:
                raise ValueError('distinct variable names required')
            names.add(name)
            if not isinstance(costs, list) or len(costs) != len(resources):
                raise ValueError('one cost per resource required')
            costs = tuple(integer(w, 0, 2**32-1, 'nonnegative cost') for w in costs)
            lo = integer(row.get('lower', 0), 0, 2**64-1, 'variable lower')
            hi = row['upper']
            if hi is not None:
                integer(hi, lo, 2**64-1, 'variable upper')
            m = integer(row.get('modulus', 1), 1, 256, 'modulus')
            r = integer(row.get('residue', 0), 0, m-1, 'residue')
            first = lo+(r-lo) % m
            size = None if hi is None else max(0, (hi-first)//m+1)
            mapping = row.get('actions')
            if self.machine_model is not None:
                if size is None or size > 256 or not isinstance(mapping, dict) or set(mapping) != {str(first+m*i) for i in range(size)} or any(a not in self.actions for a in mapping.values()):
                    raise ValueError('machine variables require one known action per bounded admissible value')
            elif mapping is not None:
                raise ValueError('variable actions require a machine')
            self.variables.append((costs, rational(row.get('profit', 0)), first, m, size, mapping))
        self.variables = tuple(self.variables)
        exact = len(resources) == 1 and lows == highs
        gf_ok = exact and self.machine_model is None and len(variables) <= 16 and all(1 <= v[0][0] <= 256 for v in self.variables)
        if gf_ok and len(variables) > 2:
            gf_ok = len({v[1]/v[0][0] for v in self.variables}) == 1
        self.gf_suffix = None
        self.strategy = self.requested_strategy
        finite = all(v[4] is not None and v[4] <= 256 for v in self.variables)
        candidates = prod(v[4] for v in self.variables) if finite else self.enum_limit+1
        independent_binary = self.machine_model is None and all(v[2:5] == (0, 1, 2) for v in self.variables)
        binary = independent_binary and len(variables) <= self.binary_limit
        groups = len({(v[0], v[1]) for v in self.variables})
        repeated = independent_binary and groups < len(variables)
        from .planning_native import available
        native_scale = lcm(*(v[1].denominator for v in self.variables)) if independent_binary else 1
        native_ok = independent_binary and len(variables) <= 40 and available() and sum(abs(int(v[1]*native_scale)) for v in self.variables) <= 2**60
        grid = (len(variables)+1)*prod(min(high, sum(v[0][j]*(v[2]+v[3]*max(0,(v[4] or 1)-1)) for v in self.variables))+1 for j,high in enumerate(highs))
        if self.strategy == 'auto':
            self.strategy = ('symmetry' if repeated else 'dp' if independent_binary and grid < min(candidates//2,self.state_limit) else 'mitm' if native_ok and len(variables)>=15 else 'gray' if binary else
                             'enumeration' if finite and candidates <= self.enum_limit else 'gf' if gf_ok else 'dp')
        if self.strategy in ('symmetry', 'mitm', 'population') and not independent_binary:
            raise ValueError('symmetry, MITM and population require independent binary allocations')
        if self.strategy == 'gray' and not binary:
            raise ValueError('Gray route requires an independent binary allocation within binary_limit')
        if self.strategy == 'gf':
            if not gf_ok:
                raise ValueError('GF route needs one exact positive-cost resource, no machine, and two variables or a cost-proportional objective')
            coords = [{'weight': c[0], 'lower': first, 'modulus': m, 'residue': first % m,
                       'upper': None if size is None else first+m*(size-1) if size else max(0, first-1)}
                      for c, p, first, m, size, mapping in self.variables]
            # Preserve empty residue domains without inventing an invalid upper.
            if any(v[4] == 0 for v in self.variables) or sum(v[0][0]*v[2] for v in self.variables) > self.upper[0]:
                self.gf_empty = True
            else:
                self.gf_empty = False
                try:
                    self.gf_suffix = [BudgetPopulation({'coordinates': coords[i:]}) for i in range(len(coords))]
                except WorkLimit:
                    if self.requested_strategy != 'auto' or not finite:
                        raise
                    self.strategy = 'dp'
        if self.strategy in ('dp', 'enumeration') and not finite:
            raise WorkLimit('finite completion fold permits at most 256 values per variable; use a supported GF route')
        if self.strategy == 'enumeration' and candidates > self.enum_limit:
            raise WorkLimit('enumeration candidate budget exceeded')
        self.suffix_min = [(0,)*len(resources)]*(len(variables)+1)
        self.suffix_max = list(self.suffix_min)
        if finite:
            for i in reversed(range(len(variables))):
                costs, profit, first, m, size, mapping = self.variables[i]
                last = first+m*max(0, size-1)
                self.suffix_min[i] = tuple(a+w*first for a, w in zip(self.suffix_min[i+1], costs))
                self.suffix_max[i] = tuple(a+w*last for a, w in zip(self.suffix_max[i+1], costs))
        self.root = self._key(0, self.lower, self.upper, self.initial)

    def _gray(self):
        n, m = len(self.variables), len(self.lower)
        self.gray_scale = lcm(*(v[1].denominator for v in self.variables))
        units = [int(v[1]*self.gray_scale) for v in self.variables]
        if self.gray_scale.bit_length() > 8192 or any(abs(v).bit_length() > 8128 for v in units):
            raise WorkLimit('Gray profit scaling exceeds arithmetic budget')
        used, value, previous, records = [0]*m, 0, 0, []
        self.compiled_candidates = 1 << n
        for i in range(self.compiled_candidates):
            mask = i ^ (i >> 1)
            if i:
                changed = mask ^ previous; j = n-changed.bit_length()
                sign = 1 if mask & changed else -1
                for k, weight in enumerate(self.variables[j][0]):
                    used[k] += sign*weight
                value += sign*units[j]
            if all(lo <= x <= hi for lo, x, hi in zip(self.lower, used, self.upper)):
                records.append((mask, value))
            previous = mask
        records.sort()
        self.gray_masks = [mask for mask, value in records]
        base = 1 << max(0, (len(records)-1).bit_length())
        self.gray_base = base
        self.gray_best, self.gray_ties = [None]*(2*base), [0]*(2*base)
        for i, (mask, value) in enumerate(records):
            self.gray_best[base+i], self.gray_ties[base+i] = value, 1
        for i in reversed(range(1, base)):
            a, b = self.gray_best[2*i], self.gray_best[2*i+1]
            best = b if a is None else a if b is None else max(a,b)
            self.gray_best[i] = best
            self.gray_ties[i] = (self.gray_ties[2*i] if a == best else 0)+(self.gray_ties[2*i+1] if b == best else 0)
        best = self.gray_best[1]
        self.gray_optimal = [mask for mask, value in records if value == best]
        if len(self.gray_optimal) == len(self.gray_masks):
            self.gray_optimal = self.gray_masks
        self.gray_entry = EMPTY if best is None else Entry(len(records), Q(best,self.gray_scale), len(self.gray_optimal))

    def _mask(self, prefix):
        if len(prefix) > len(self.variables) or any(type(x) is not int or x not in (0,1) for x in prefix):
            raise ValueError('binary original-coordinate prefix required')
        result = 0
        for x in prefix: result = 2*result+x
        return result

    def _decode(self, mask):
        return [(mask >> (len(self.variables)-i-1)) & 1 for i in range(len(self.variables))]

    def _gray_prefix(self, prefix):
        mask = self._mask(prefix); shift = len(self.variables)-len(prefix)
        low = bisect_left(self.gray_masks, mask << shift)
        high = bisect_left(self.gray_masks, (mask+1) << shift)
        count = high-low
        if count == 0: return EMPTY
        left, right, best, ties = low+self.gray_base, high+self.gray_base, None, 0
        while left < right:
            indices = []
            if left & 1: indices.append(left); left += 1
            if right & 1: right -= 1; indices.append(right)
            for i in indices:
                score = self.gray_best[i]
                if best is None or score > best: best, ties = score, self.gray_ties[i]
                elif score == best: ties += self.gray_ties[i]
            left //= 2; right //= 2
        return Entry(count, Q(best,self.gray_scale), ties)

    def _words(self, spec):
        if self.machine_model is None:
            raise ValueError('word planner requires a finite partial machine')
        self.budget = integer(spec.get('budget'), 0, 256, 'word budget')
        rows = spec.get('actions')
        if not isinstance(rows, list) or not rows or len(rows) > 16:
            raise ValueError('1..16 weighted actions required')
        actions = []
        for row in rows:
            if not isinstance(row, dict) or set(row)-{'name', 'cost', 'profit'} or not {'name', 'cost'} <= set(row):
                raise ValueError('named action with positive cost required')
            if row['name'] not in self.actions:
                raise ValueError('unknown machine action')
            actions.append((row['name'], integer(row['cost'], 1, 16, 'action cost'), rational(row.get('profit', 0))))
        if len({a[0] for a in actions}) != len(actions) or {a[0] for a in actions} != set(self.actions):
            raise ValueError('one cost and profit for every machine action required')
        self.word_actions = tuple(sorted(actions))
        if self.requested_strategy not in ('auto', 'dp'):
            raise ValueError('ordered words use the positive-cost completion DP')
        self.strategy, self.root = 'dp', (self.budget, self.initial)

    def _key(self, i, needs, room, state):
        if self.strategy == 'gf':
            return None
        return (i, tuple(max(0, x) for x in needs), tuple(min(x, bound) for x, bound in zip(room, self.suffix_max[i])), state)

    def _terminal(self, key):
        if self.kind == 'words':
            remaining, state = key
            return UNIT if remaining == 0 and state in self.accepting else EMPTY if remaining == 0 else None
        i, needs, room, state = key
        if any(v[4] == 0 for v in self.variables[i:]) or any(r < s or n > t for r, s, n, t in zip(room, self.suffix_min[i], needs, self.suffix_max[i])):
            return EMPTY
        if i == len(self.variables):
            return UNIT if not any(needs) and state in self.accepting else EMPTY
        return None

    def _arcs(self, key):
        if self.kind == 'words':
            remaining, state = key
            for name, cost, profit in self.word_actions:
                target = self.actions[name][state]
                if cost <= remaining and target is not None:
                    yield name, profit, (remaining-cost, target)
            return
        i, needs, room, state = key
        costs, profit, first, m, size, mapping = self.variables[i]
        for k in range(size):
            value = first+m*k
            target = state if mapping is None else self.actions[mapping[str(value)]][state]
            if target is None or any(w*value > r for w, r in zip(costs, room)):
                continue
            yield value, profit*value, self._key(i+1, tuple(n-w*value for n, w in zip(needs, costs)), tuple(r-w*value for r, w in zip(room, costs)), target)

    def _entry(self, key):
        if self.failed:
            raise WorkLimit('planner compilation exceeded its work budget')
        if key in self.memo:
            return self.memo[key]
        self.states += 1
        if self.states+self.reused_entries > self.state_limit:
            self.failed = True; raise WorkLimit('completion state budget exceeded')
        result = self._terminal(key)
        if result is None:
            count, best, ties = 0, None, 0
            for token, profit, child in self._arcs(key):
                self.edges += 1
                if self.edges > self.edge_limit:
                    self.failed = True; raise WorkLimit('completion edge budget exceeded')
                entry = self._entry(child); count += entry.count
                if entry.count:
                    score = bounded_score(profit+entry.best)
                    if best is None or score > best:
                        best, ties = score, entry.optimal_count
                    elif score == best:
                        ties += entry.optimal_count
            result = Entry(count, best, ties)
        self.memo[key] = result
        return result

    def _query_arcs(self, key):
        # Cache only paths actually queried, not the whole large fold.
        if key not in self.query_arcs:
            self.query_arcs[key] = tuple(self._arcs(key))
        return self.query_arcs[key]

    def _walk(self, prefix):
        if not isinstance(prefix, (list, tuple)) or len(prefix) > (len(self.variables) if self.kind == 'allocation' else self.budget):
            raise ValueError('bounded original-coordinate prefix required')
        key, score = self.root, Q(0)
        for i, token in enumerate(prefix):
            if self.kind == 'allocation':
                c, p, first, m, size, mapping = self.variables[i]
                if type(token) is not int or token < first or (token-first) % m or (size is not None and (token-first)//m >= size):
                    raise ValueError('prefix value outside variable domain')
            elif type(token) is not str or token not in self.actions:
                raise ValueError('unknown prefix action')
            if key is None or self._terminal(key) is not None:
                key = None; continue
            match = next(((p, child) for value, p, child in self._query_arcs(key) if value == token), None)
            if match is None:
                key = None
            else:
                profit, key = match; score = bounded_score(score+profit)
        return key, score

    def _enumerate(self):
        points = []
        def visit(key, point, score):
            self.states += 1
            if self.states > self.state_limit:
                self.failed = True; raise WorkLimit('enumeration state budget exceeded')
            terminal = self._terminal(key)
            if terminal == UNIT:
                points.append((point, score))
            elif terminal is None:
                for value, profit, child in self._arcs(key):
                    self.edges += 1
                    if self.states > self.state_limit or self.edges > self.edge_limit:
                        self.failed = True; raise WorkLimit('enumeration fold budget exceeded')
                    visit(child, point+(value,), bounded_score(score+profit))
        visit(self.root, (), Q(0))
        self.points = tuple(points)
        best = max((p for _, p in points), default=None)
        self.optimal_points = tuple(point for point, p in points if p == best)
        self.point_ranks = {p: i for i, (p, _) in enumerate(points)}
        self.optimal_ranks = {p: i for i, p in enumerate(self.optimal_points)}
        self.enum_entry = Entry(len(points), best, len(self.optimal_points))
        prefixes = {}
        for point, score in points:
            for i in range(len(point)+1):
                key = point[:i]
                previous = prefixes.get(key, EMPTY)
                maximum = score if previous.best is None else max(score, previous.best)
                ties = (previous.optimal_count if previous.best == maximum else 0)+(score == maximum)
                prefixes[key] = Entry(previous.count+1, maximum, ties)
        self.enum_prefixes = prefixes

    def _gf_entry(self, prefix):
        if not isinstance(prefix, (list, tuple)) or len(prefix) > len(self.variables):
            raise ValueError('original-coordinate prefix required')
        remaining, score = self.upper[0], Q(0)
        for value, (c, p, first, m, size, mapping) in zip(prefix, self.variables):
            if type(value) is not int or value < first or (value-first) % m or size is not None and (value-first)//m >= size:
                raise ValueError('prefix value outside variable domain')
            remaining -= c[0]*value; score = bounded_score(score+p*value)
        if self.gf_empty or remaining < 0:
            return EMPTY
        if len(prefix) == len(self.variables):
            return Entry(1, score, 1) if remaining == 0 else EMPTY
        suffix = self.gf_suffix[len(prefix)]; count = suffix.count(remaining)
        if not count:
            return EMPTY
        variables = self.variables[len(prefix):]
        if len({v[1]/v[0][0] for v in variables}) == 1:
            return Entry(count, bounded_score(score+variables[0][1]/variables[0][0][0]*remaining), count)
        if len(variables) <= 2:
            ends = [suffix.select(remaining, 0), suffix.select(remaining, count-1)]
            scores = [score+sum(v[1]*x for v, x in zip(variables, point)) for point in ends]
            return Entry(count, bounded_score(max(scores)), count if scores[0] == scores[1] else 1)
        return Entry(count, bounded_score(score+variables[0][1]/variables[0][0][0]*remaining), count)

    def _view(self, prefix):
        if not isinstance(prefix, (list, tuple)):
            raise ValueError('original-coordinate prefix required')
        if not prefix:
            return self.root_entry
        if self.strategy == 'gf':
            return self._gf_entry(prefix)
        if self.strategy in ('mitm','symmetry','population'):
            return self._indexed_entry(prefix)
        if self.strategy == 'gray':
            return self._gray_prefix(prefix)
        if self.strategy == 'enumeration':
            if len(prefix) > len(self.variables):
                raise ValueError('bounded original-coordinate prefix required')
            for value, (c, p, first, m, size, mapping) in zip(prefix, self.variables):
                if type(value) is not int or value < first or (value-first) % m or (value-first)//m >= size:
                    raise ValueError('prefix value outside variable domain')
            return self.enum_prefixes.get(tuple(prefix), EMPTY)
        key, score = self._walk(prefix)
        if key is None:
            return EMPTY
        entry = self._entry(key)
        return Entry(entry.count, None if entry.best is None else entry.best+score, entry.optimal_count)

    def _indexed_entry(self, prefix):
        self._mask(prefix)
        key = tuple(prefix)
        if key in self.index_views: return self.index_views[key]
        if self.strategy == 'symmetry':
            entry = Entry(*self.index.query(prefix))
        else:
            r = self.index.query(prefix)
            entry = Entry(r['count'], Q(r['best'],self.index.scale) if r['count'] else None, r['ties'])
        if len(self.index_views)>=8192: self.index_views.clear()
        self.index_views[key] = entry
        return entry

    def _indexed_size(self, prefix, optimal):
        e = self._view(prefix)
        return e.optimal_count if optimal and e.best == self.root_entry.best else 0 if optimal else e.count

    def completions(self, prefix=()):
        entry = self._view(prefix)
        return {'count': entry.count, 'maximum': None if entry.best is None else str(entry.best),
                'maximizer_count': entry.optimal_count, 'prefix': list(prefix),
                'scope': 'all feasible completions and conditional optimum under this prefix'}

    def count(self):
        return self._view(()).count

    def select(self, rank, optimal=False):
        if type(optimal) is not bool:
            raise ValueError('optimal must be Boolean')
        root = self._view(())
        total = root.optimal_count if optimal else root.count
        integer(rank, 0, total-1, 'rank')
        if self.strategy in ('mitm','symmetry','population'):
            cache_key = (rank,optimal)
            if cache_key in self.selected_plans: return list(self.selected_plans[cache_key])
            original_rank = rank
            prefix = []
            for i in range(len(self.variables)):
                size = self._indexed_size(prefix+[0],optimal)
                if rank < size: prefix.append(0)
                else: prefix.append(1); rank -= size
            if len(self.selected_plans)>=8192: self.selected_plans.clear(); self.selected_ranks.clear()
            self.selected_plans[cache_key] = tuple(prefix)
            self.selected_ranks[(tuple(prefix),optimal)] = original_rank
            return prefix
        if self.strategy == 'gray':
            return self._decode((self.gray_optimal if optimal else self.gray_masks)[rank])
        if self.strategy == 'enumeration':
            return list(self.optimal_points[rank] if optimal else self.points[rank][0])
        if self.strategy == 'gf':
            if not optimal or root.optimal_count == root.count:
                return self.gf_suffix[0].select(self.upper[0], rank)
            suffix = self.gf_suffix[0]
            ends = [suffix.select(self.upper[0], 0), suffix.select(self.upper[0], root.count-1)]
            return max(ends, key=lambda point: sum(v[1]*x for v, x in zip(self.variables, point)))
        key, result = self.root, []
        while self._terminal(key) is None:
            current = self._entry(key)
            for token, profit, child in self._query_arcs(key):
                entry = self._entry(child)
                size = entry.optimal_count if optimal and entry.count and profit+entry.best == current.best else 0 if optimal else entry.count
                if rank < size:
                    result.append(token); key = child; break
                rank -= size
            else:
                raise AssertionError('completion rank decomposition failed')
        return result

    def rank(self, point, optimal=False):
        if type(optimal) is not bool:
            raise ValueError('optimal must be Boolean')
        if self.strategy in ('mitm','symmetry','population'):
            if not isinstance(point,(list,tuple)): raise ValueError('original plan required')
            self._mask(point)
            key = (tuple(point),optimal)
            if key in self.selected_ranks: return self.selected_ranks[key]
        entry = self._view(point); root = self._view(())
        if entry.count != 1 or self.kind == 'allocation' and len(point) != len(self.variables) or self.kind == 'words' and sum(dict((a, c) for a, c, p in self.word_actions)[a] for a in point) != self.budget:
            raise ValueError('complete feasible original plan required')
        if optimal and entry.best != root.best:
            raise ValueError('plan is not a global maximizer')
        if self.strategy in ('mitm','symmetry','population'):
            rank = 0
            for i, value in enumerate(point):
                if value: rank += self._indexed_size(list(point[:i])+[0],optimal)
            return rank
        if self.strategy == 'gray':
            return bisect_left(self.gray_optimal if optimal else self.gray_masks, self._mask(point))
        if self.strategy == 'enumeration':
            return (self.optimal_ranks if optimal else self.point_ranks)[tuple(point)]
        if self.strategy == 'gf':
            return 0 if optimal and root.optimal_count == 1 else self.gf_suffix[0].rank(self.upper[0], point)
        key, rank = self.root, 0
        for value in point:
            current = self._entry(key)
            for token, profit, child in self._query_arcs(key):
                if token == value:
                    key = child; break
                entry = self._entry(child)
                rank += entry.optimal_count if optimal and entry.count and profit+entry.best == current.best else 0 if optimal else entry.count
        return rank

    def sample(self, rng=None, optimal=False):
        if type(optimal) is not bool:
            raise ValueError('optimal must be Boolean')
        entry = self._view(())
        total = entry.optimal_count if optimal else entry.count
        if total == 0:
            raise ValueError('cannot sample an empty population')
        return self.select((SystemRandom() if rng is None else rng).randrange(total), optimal=optimal)

    def optimize(self):
        entry = self._view(())
        if self.strategy in ('mitm', 'population'):
            return {'maximum':None if entry.best is None else str(entry.best), 'maximizer_count':entry.optimal_count,
                    'point':self._decode(self.index.query(())['mask']) if entry.count else None}
        return {'maximum': None if entry.best is None else str(entry.best),
                'maximizer_count': entry.optimal_count,
                'point': None if not entry.count else self.select(0, optimal=True)}

    def page(self, start=0, size=20, optimal=False):
        if type(optimal) is not bool:
            raise ValueError('optimal must be Boolean')
        integer(start, 0, 2**8192-1, 'page start'); integer(size, 0, 256, 'page size')
        entry = self._view(())
        total = entry.optimal_count if optimal else entry.count
        return [self.select(i, optimal=optimal) for i in range(start, min(total, start+size))]

    def with_resources(self, resources):
        if self.kind != 'allocation':
            raise ValueError('resource changes apply to allocations')
        spec = deepcopy(self.specification); spec['resources'] = resources
        return type(self)(spec, _reuse=self)

    def summary(self):
        optimization = self.optimize()
        if self.strategy == 'symmetry':
            self.states, self.edges = len(self.index.memo), self.index.edges
        elif self.strategy == 'population':
            self.states, self.edges = len(self.index.fixed_cache), 2*len(self.index.partitions)
        elif self.strategy == 'mitm':
            self.compiled_candidates = self.index.query(())['records']
        return {'schema': 'pp-completion-planner/1', 'kind': self.kind, 'strategy': self.strategy,
                'count': self.count(), 'optimization': optimization,
                'compiled_states': self.states, 'compiled_edges': self.edges,
                'memo_entries': len(self.memo), 'source_states': None if self.machine_model is None else len(self.machine_model['observations']),
                'compiled_candidates': self.compiled_candidates,
                'reused_entries': self.reused_entries,
                'reduced_states': None if self.machine_model is None else len(next(iter(self.actions.values()))),
                'ordering': 'lexicographic original variable values' if self.kind == 'allocation' else 'lexicographic named action word',
                'execution_verified': False,
                'symmetry_groups': len(self.index.groups) if self.strategy == 'symmetry' else None,
                'population_limits': {'memory_bytes':self.population_memory, 'cache_states':self.population_cache_states, 'search_visits':self.native_visits, 'setup_cells':self.native_visits, 'total_work_per_query':self.population_work_limit, 'partition_nodes':self.population_partition_limit} if self.strategy == 'population' else None,
                'native_provenance': self.index.lib._provenance if self.strategy in ('mitm', 'population') else None}

    def evidence(self):
        result = dict(self.summary(), specification=deepcopy(self.specification), quotient=self.quotient)
        if self.strategy == 'population':
            result['population_partition'] = self.index.partition_receipt()
        elif self.strategy == 'gf' and not self.gf_empty:
            result['generating_function'] = self.gf_suffix[0].evidence()
        elif self.kind == 'words':
            from .cost_resolvents import finite_machine_series
            costs = {a: c for a, c, p in self.word_actions}
            original_final = [i for i, row in enumerate(self.machine_model['observations']) if row['accepting']]
            result['cost_series'] = finite_machine_series(self.machine_model, self.specification['machine']['initial'], original_final, costs)
        return result


def optimize_allocation(specification):
    """Find one exact binary maximizer without counting plans or optimal ties."""
    planner = CompletionPlanner(specification, _compile=False)
    from .planning_native import optimize
    r, scale, provenance = optimize(planner)
    point = planner._decode(r['mask']) if r['count'] else None
    if point is not None:
        used = [sum(x*v[0][k] for x,v in zip(point,planner.variables)) for k in range(len(planner.lower))]
        score = sum(x*v[1] for x,v in zip(point,planner.variables))
        if any(not lo<=u<=hi for lo,u,hi in zip(planner.lower,used,planner.upper)) or score != Q(r['best'],scale):
            raise AssertionError('native optimization witness failed exact original-coordinate replay')
    return {'schema':'pp-optimization-only/1', 'maximum':str(Q(r['best'],scale)) if point is not None else None,
            'point':point, 'optimal':True, 'nodes':r['visits'], 'native_provenance':provenance,
            'scope':'one maximizer; feasible count and maximizer count are not computed', 'execution_verified':False}
