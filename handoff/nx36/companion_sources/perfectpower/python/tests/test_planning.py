"""Independent exhaustive models, original ranks, optimum ties and failure scopes."""
import json
import random
import unittest
from copy import deepcopy
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
from perfectpower.planning import CompletionPlanner
from perfectpower.divisor_square import WorkLimit
from perfectpower.catalogue import Catalogue
from perfectpower.query_service import dispatch
from perfectpower.planning_cli import execute


def independent(spec):
    variables = spec['variables']
    domains = [range(v.get('lower', 0), v['upper']+1) for v in variables]
    answers = []
    for point in product(*domains):
        if any(x % v.get('modulus', 1) != v.get('residue', 0) for x, v in zip(point, variables)):
            continue
        costs = [sum(x*v['costs'][j] for x, v in zip(point, variables)) for j in range(len(spec['resources']))]
        if any(not r.get('min', 0) <= c <= r['max'] for c, r in zip(costs, spec['resources'])):
            continue
        machine = spec.get('machine')
        if machine:
            state = machine['initial']
            for x, v in zip(point, variables):
                state = machine['model']['actions'][v['actions'][str(x)]][state]
                if state is None:
                    break
            if state not in machine['accepting']:
                continue
        score = sum(Q(v.get('profit', 0))*x for x, v in zip(point, variables))
        answers.append((point, score))
    return answers


class PlannerTests(unittest.TestCase):
    def test_gray_binary_prefixes_objectives_and_ties(self):
        rng=random.Random(343)
        for _ in range(20):
            spec={'kind':'allocation','resources':[{'name':'r','min':rng.randrange(3),'max':rng.randrange(4,10)}],
                  'variables':[{'name':str(i),'costs':[rng.randrange(4)],'profit':str(Q(rng.randrange(-2,3),3)),'upper':1} for i in range(6)]}
            self.compare(spec,('gray','dp','enumeration'))

    def compare(self, spec, strategies=('enumeration', 'dp')):
        expected = independent(spec)
        best = max((s for p, s in expected), default=None)
        optimal = [p for p, s in expected if s == best]
        for strategy in strategies:
            planner = CompletionPlanner(dict(spec, strategy=strategy))
            self.assertEqual(planner.count(), len(expected))
            self.assertEqual(planner.optimize()['maximum'], None if best is None else str(best))
            self.assertEqual(planner.optimize()['maximizer_count'], len(optimal))
            for rank, (point, score) in enumerate(expected):
                self.assertEqual(planner.select(rank), list(point))
                self.assertEqual(planner.rank(point), rank)
                for length in (0, len(point)//2, len(point)):
                    prefix = point[:length]
                    completions = [(p,s) for p,s in expected if p[:length] == prefix]
                    answer = planner.completions(prefix)
                    self.assertEqual(answer['count'], len(completions))
                    self.assertEqual(answer['maximum'], str(max(s for p,s in completions)))
                    self.assertEqual(answer['maximizer_count'], sum(s==max(t for p,t in completions) for p,s in completions))
            for rank, point in enumerate(optimal):
                self.assertEqual(planner.select(rank, optimal=True), list(point))
                self.assertEqual(planner.rank(point, optimal=True), rank)
            if expected:
                # A deterministic rank source exhausts the sample support once,
                # checking the bijection rather than a flaky statistical test.
                class Ranks:
                    def __init__(self): self.i = 0
                    def randrange(self, n):
                        value = self.i; self.i += 1; return value
                rng = Ranks()
                self.assertEqual([planner.sample(rng) for _ in expected], [list(p) for p,s in expected])

    def test_random_multiresource_models(self):
        rng = random.Random(1462)
        for _ in range(30):
            n, m = rng.randrange(1,5), rng.randrange(1,4)
            spec = {'kind':'allocation', 'resources':[{'name':str(i),'min':rng.randrange(3),'max':rng.randrange(3,10)} for i in range(m)],
                    'variables':[{'name':str(i),'costs':[rng.randrange(4) for j in range(m)],'profit':str(Q(rng.randrange(-3,4),rng.randrange(1,4))),
                                  'upper':rng.randrange(1,4),'modulus':rng.randrange(1,3),'residue':0} for i in range(n)]}
            self.compare(spec)

    def test_machine_acceptance_and_disabled_prefix(self):
        model = {'observations':[0]*4,'actions':{'skip':[0,1,2,3],'take':[1,None,3,None]}}
        spec = {'kind':'allocation','resources':[{'name':'budget','max':3}],
                'variables':[{'name':str(i),'costs':[1],'upper':1,'profit':1,'actions':{'0':'skip','1':'take'}} for i in range(4)],
                'machine':{'model':model,'initial':0,'accepting':[1,3]}}
        self.compare(spec)
        reduced = CompletionPlanner(dict(spec,strategy='dp'))
        self.assertEqual(reduced.summary()['reduced_states'],2)
        self.assertEqual(reduced.completions([1,1])['count'],0)
        self.assertEqual(reduced.count(),4)
        original = CompletionPlanner(dict(spec,strategy='dp',reduce_machine=False))
        self.assertEqual(original.page(size=20),reduced.page(size=20))

    def test_acceptance_never_disappears_in_quotient(self):
        model={'observations':[0,0],'actions':{'a':[0,1]}}
        p=CompletionPlanner({'kind':'words','budget':0,'machine':{'model':model,'initial':0,'accepting':[1]},'actions':[{'name':'a','cost':1}]})
        self.assertEqual(p.count(),0); self.assertEqual(p.summary()['reduced_states'],2)

    def test_words_against_enumeration_and_cost_series(self):
        model={'observations':[0]*4,'actions':{'a':[1,0,3,2],'b':[0,None,2,None]}}
        for budget in range(10):
            spec={'kind':'words','budget':budget,'machine':{'model':model,'initial':0,'accepting':[0,2]},
                  'actions':[{'name':'a','cost':1,'profit':-1},{'name':'b','cost':2,'profit':3}]}
            expected=[]
            def search(word,cost,state,score):
                if cost==budget:
                    if state in (0,2): expected.append((word,score))
                    return
                for a,c,p in [('a',1,-1),('b',2,3)]:
                    t=model['actions'][a][state]
                    if t is not None and cost+c<=budget: search(word+[a],cost+c,t,score+p)
            search([],0,0,0)
            planner=CompletionPlanner(spec)
            self.assertEqual(planner.page(size=256),[w for w,s in expected])
            self.assertEqual(planner.count(),len(expected))
            for i,(word,score) in enumerate(expected):self.assertEqual(planner.rank(word),i)
            best=max((s for w,s in expected),default=None)
            self.assertEqual(planner.optimize()['maximum'],None if best is None else str(best))
            from perfectpower.generating_functions import RationalSeries
            output=planner.evidence()['cost_series']['transport']['resolvent']['outputs'][0]
            gf=RationalSeries({k:output[k] for k in ('numerator','denominator')})
            self.assertEqual(gf.coefficient(budget),len(expected))
            flat=deepcopy(spec)
            for action in flat['actions']:action['profit']=action['cost']
            ties=CompletionPlanner(flat)
            self.assertEqual(ties.optimize()['maximizer_count'],len(expected))
            for rank,(word,score) in enumerate(expected):
                self.assertEqual(ties.select(rank,optimal=True),word)
                self.assertEqual(ties.rank(word,optimal=True),rank)

    def test_gf_against_bounded_enumeration_and_dp(self):
        for budget in range(20):
            spec={'kind':'allocation','resources':[{'name':'budget','min':budget,'max':budget}],
                  'variables':[{'name':'x','costs':[1],'upper':10,'profit':'3/2','modulus':3,'residue':1},
                               {'name':'y','costs':[2],'upper':10,'profit':2}]}
            self.compare(spec,('gf','dp','enumeration'))
        spec={'kind':'allocation','resources':[{'name':'budget','min':10**12,'max':10**12}],
              'variables':[{'name':str(i),'costs':[w],'upper':None,'profit':w} for i,w in enumerate((1,2,1,2))]}
        planner=CompletionPlanner(spec)
        self.assertEqual(planner.summary()['strategy'],'gf')
        self.assertEqual(planner.optimize()['maximizer_count'],planner.count())
        point=planner.select(10**30);self.assertEqual(planner.rank(point),10**30)
        self.assertEqual(planner.completions(point)['count'],1)

    def test_limits_reuse_and_immutability(self):
        spec={'kind':'allocation','strategy':'dp','resources':[{'name':'r','max':12}],
              'variables':[{'name':str(i),'costs':[1],'upper':1,'profit':i} for i in range(12)]}
        planner=CompletionPlanner(spec)
        changed=planner.with_resources([{'name':'r','max':10}])
        fresh=CompletionPlanner(dict(spec,resources=[{'name':'r','max':10}]))
        self.assertEqual(changed.count(),fresh.count())
        self.assertEqual(changed.optimize(),fresh.optimize())
        self.assertGreater(changed.reused_entries,0)
        self.assertEqual(planner.count(),4096)
        copied=planner.specification;copied['variables'][0]['profit']=100
        self.assertEqual(planner.specification,spec)
        with self.assertRaises(WorkLimit):CompletionPlanner(dict(spec,state_limit=1))
        one={'kind':'allocation','strategy':'enumeration','state_limit':1,'resources':[{'name':'r','max':1}],
             'variables':[{'name':'x','costs':[1],'lower':1,'upper':1}]}
        with self.assertRaises(WorkLimit):CompletionPlanner(one)
        with self.assertRaises(ValueError):planner.rank([0])
        with self.assertRaises(ValueError):planner.select(True)
        with self.assertRaises(ValueError):planner.page(optimal='yes',size=0)
        with self.assertRaises(ValueError):planner.rank([0]*12,optimal=True)

    def test_catalogue_cli_and_source_data(self):
        rows=json.loads((Path(__file__).resolve().parents[2]/'data/planning/petersen.json').read_text())
        for row in rows[:3]:
            planner=CompletionPlanner(row['specification'])
            self.assertEqual(Q(planner.optimize()['maximum']),Q(row['published_optimum']))
        with Catalogue(':memory:') as db:
            record=db.register('completion_planner',rows[0]['specification'],'projects')
            answer=dispatch(db,{'op':'call','object':'projects','method':'completions','args':{'prefix':[1]}})
            self.assertGreater(answer['count'],0)
        r=execute({'specification':rows[0]['specification'],'queries':[{'method':'sample'}],'seed':43})
        self.assertEqual(r,execute({'specification':rows[0]['specification'],'queries':[{'method':'sample'}],'seed':43}))


if __name__=='__main__':unittest.main()
