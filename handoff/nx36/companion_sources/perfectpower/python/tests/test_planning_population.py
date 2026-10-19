"""Original-coordinate differential tests for residual polynomial planning."""
import itertools
import json
import random
import unittest
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from perfectpower.planning import CompletionPlanner
from perfectpower.planning_native import PopulationIndex, available, recursive_reference
from perfectpower.divisor_square import WorkLimit

@unittest.skipUnless(available(), 'C++17 compiler unavailable')
class PopulationTests(unittest.TestCase):
    def spec(self, seed):
        rng = random.Random(seed)
        m, n = 1+seed%5, 1+seed%10
        return {'kind': 'allocation', 'resources': [
            {'name': str(k), 'min': rng.randrange(3), 'max': 8+rng.randrange(8)} for k in range(m)],
            'variables': [{'name': str(j), 'costs': [rng.randrange(7) for _ in range(m)],
                           'profit': str(Fraction(rng.randrange(-3, 5), 7)), 'upper': 1}
                          for j in range(n)]}

    def test_exhaustive_population_and_queries(self):
        for seed in range(40):
            spec = self.spec(seed)
            ref = CompletionPlanner(dict(spec, strategy='enumeration'))
            p = CompletionPlanner(dict(spec, strategy='population'))
            self.assertEqual(ref.count(), p.count())
            self.assertEqual(ref.optimize(), p.optimize())
            for length in range(min(4, len(spec['variables']))+1):
                for prefix in itertools.product((0, 1), repeat=length):
                    self.assertEqual(ref.completions(prefix), p.completions(prefix))
            for optimal in (False, True):
                total = ref.root_entry.optimal_count if optimal else ref.count()
                for rank in sorted({0, total//2, total-1}) if total else []:
                    point = p.select(rank, optimal)
                    self.assertEqual(point, ref.select(rank, optimal))
                    # Bypass select/rank cross caches so this checks the recurrence.
                    p.selected_ranks.clear()
                    self.assertEqual(p.rank(point, optimal), rank)
            if p.count():
                point = p.sample(random.Random(seed))
                self.assertEqual(ref.completions(point)['count'], 1)

    def test_huge_original_population_zero_cost_ties(self):
        spec = {'kind': 'allocation', 'strategy': 'population', 'resources': [{'name': 'r', 'max': 0}],
                'variables': [{'name': str(j), 'costs': [0], 'profit': 0, 'upper': 1} for j in range(64)]}
        p = CompletionPlanner(spec)
        self.assertEqual(p.count(), 2**64)
        self.assertEqual(p.optimize()['maximizer_count'], 2**64)
        for rank in (0, 2**63, 2**64-1):
            point = p.select(rank)
            p.selected_ranks.clear()
            self.assertEqual(p.rank(point), rank)
        self.assertEqual(p.index.query(())['accepted_subcubes'], 1)
        self.assertEqual(p.evidence()['population_partition']['answers'][0]['answer']['count'], 2**64)
        self.assertGreater(p.summary()['compiled_states'], 0)

    def test_budgets_and_failure_cache(self):
        spec = {'kind':'allocation','resources':[{'name':str(k),'max':v} for k,v in enumerate((6,5,4))], 'variables':[{'name':str(j),'costs':[j%3+1,j%4+1,j%2+1],'upper':1,'profit':j} for j in range(12)]}
        for limit in ({'native_visit_limit': 1, 'population_work_limit': 1}, {'population_cache_states': 1, 'population_partition_limit': 1}):
            p = CompletionPlanner(dict(spec, strategy='population', **limit), _compile=False)
            index = PopulationIndex(p)
            with self.assertRaises(WorkLimit):
                index.query(())
            self.assertNotIn((), index.cache)
        for prefix in ([True], [2], [0]*13, '0'):
            with self.assertRaises(ValueError):
                PopulationIndex(CompletionPlanner(dict(spec, strategy='population'), _compile=False)).query(prefix)
        with self.assertRaises(ValueError):
            CompletionPlanner(dict(spec, strategy='population', population_memory_limit=1024))
        with self.assertRaises(ValueError):
            CompletionPlanner(dict(spec, strategy='population', variables=[dict(spec['variables'][0], upper=2)]))
        # Scalar table and DFS must agree when the arena is too small for tables.
        a = CompletionPlanner(dict(spec, strategy='population', population_memory_limit=1024*1024,
                                   population_cache_states=0))
        b = CompletionPlanner(dict(spec, strategy='enumeration', enumeration_limit=4096))
        self.assertEqual(a.count(), b.count())
        self.assertEqual(a.optimize(), b.optimize())
        r = a.index.query(())
        r['count'] = -1
        self.assertEqual(a.index.query(())['count'], b.count())

    def test_petersen_39_and_independent_conditional_fold(self):
        rows = json.loads((Path(__file__).resolve().parents[2]/'data/planning/petersen.json').read_text())
        p = CompletionPlanner(dict(rows[-2]['specification'], strategy='population'))
        self.assertEqual(p.count(), 368072359571)
        self.assertEqual(p.optimize()['maximum'], '10618')
        spec = deepcopy(rows[-1]['specification'])
        prefix = [0]*24
        p = CompletionPlanner(dict(spec, strategy='population'), _compile=False)
        index = PopulationIndex(p)
        answer = index.query(prefix)
        spec['variables'] = spec['variables'][24:]
        reference, scale = recursive_reference(CompletionPlanner(spec, _compile=False))
        self.assertEqual(answer['count'], reference['count'])
        self.assertEqual(answer['ties'], reference['ties'])
        self.assertEqual(answer['best'], reference['best'])
        self.assertEqual(answer['mask'], reference['mask'])

if __name__ == '__main__':
    unittest.main()
