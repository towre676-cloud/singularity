"""Exact two-player repeat-plan populations under a specified scalar noise model.

The coefficients, current mean gap and radius are frozen assumptions. This is
NOT a claim that more attempts achieve the forecast gap in real athletes. It
counts integer plans without enumerating every plan: a bounded frontier plus a
floor-sum tail, with rank/unrank and uniform sampling in population order.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from numbers import Integral


def floor_sum(n, m, a, b):
    """sum((a*i+b)//m for i in range(n)), using Euclidean remainders."""
    if any(isinstance(v, bool) or not isinstance(v, Integral) for v in (n,m,a,b)) or min(n,a,b) < 0 or m < 1:
        raise ValueError('nonnegative integer n,a,b and positive integer m required')
    n,m,a,b = map(int,(n,m,a,b)); out = 0
    while True:
        qa,a = divmod(a,m); qb,b = divmod(b,m)
        out += qa*n*(n-1)//2+qb*n
        y = a*n+b
        if y < m:
            return out
        n,b = divmod(y,m); m,a = a,m


def _q(v):
    if isinstance(v, bool):
        raise ValueError('boolean coefficient is invalid')
    try:
        value = Q(str(v)) if not isinstance(v,Q) else v
    except (ValueError,TypeError,ZeroDivisionError) as exc:
        raise ValueError('finite rational coefficient required') from exc
    if value < 0:
        raise ValueError('coefficients must be nonnegative')
    return value


@dataclass(frozen=True)
class RepeatPlanPopulation:
    signal_a: Q
    noise_a: Q
    signal_b: Q
    noise_b: Q
    gap: Q
    radius: Q
    budget: int
    known_a: int
    known_b: int
    cost_a: int
    cost_b: int
    target: str
    frontier: tuple
    tail: tuple | None
    predicates: int

    @classmethod
    def build(cls, signal_a, noise_a, signal_b, noise_b, gap, radius,
              *, budget, known_a=1, known_b=1, cost_a=1, cost_b=1,
              target='next_attempt', max_frontier=100000):
        s,n,t,p,g,q = map(_q,(signal_a,noise_a,signal_b,noise_b,gap,radius))
        ints = (budget,known_a,known_b,cost_a,cost_b,max_frontier)
        if any(isinstance(v,bool) or not isinstance(v,Integral) for v in ints) or budget < 0 or min(ints[1:]) < 1:
            raise ValueError('nonnegative integer budget and positive integer counts/costs/limit required')
        budget,known_a,known_b,cost_a,cost_b,max_frontier = map(int,ints)
        if target not in ('latent','next_attempt'):
            raise ValueError('target must be latent or next_attempt')
        calls = 0
        def variance(s,n,k):
            residual = s*n/(n+k*s) if s and n else Q(0)
            return residual+(n if target == 'next_attempt' else 0)
        def separated(va,vb):
            nonlocal calls
            calls += 1
            if not g:
                return False
            if not q:
                return True
            d = (g/q)**2-va-vb
            return d > 0 and d*d > 4*va*vb
        def first_true(lo,hi,predicate):
            # Caller has established that predicate(hi) holds.
            while lo < hi:
                mid = (lo+hi)//2
                if predicate(mid):
                    hi = mid
                else:
                    lo = mid+1
            return lo
        amax = known_a+budget//cost_a; bmax = known_b+budget//cost_b
        floor_a = n if target == 'next_attempt' else Q(0)
        args = (s,n,t,p,g,q,budget,known_a,known_b,cost_a,cost_b,target)
        if not separated(floor_a,variance(t,p,bmax)):
            return cls(*args,(),None,calls)
        b_limit = first_true(known_b,bmax,lambda b: separated(floor_a,variance(t,p,b)))
        tail_start = amax+1
        if separated(variance(s,n,amax),variance(t,p,b_limit)):
            tail_start = first_true(known_a,amax,lambda a: separated(variance(s,n,a),variance(t,p,b_limit)))
        if tail_start-known_a > max_frontier:
            raise ValueError('frontier exceeds exact compiler limit; increase max_frontier explicitly')
        rows = []
        for a in range(known_a,tail_start):
            upper = known_b+(budget-cost_a*(a-known_a))//cost_b
            if not separated(variance(s,n,a),variance(t,p,upper)):
                continue
            lower = first_true(b_limit,upper,lambda b: separated(variance(s,n,a),variance(t,p,b)))
            rows.append((a,lower,upper))
        tail_end = known_a+(budget-cost_b*(b_limit-known_b))//cost_a
        tail = (tail_start,tail_end,b_limit) if tail_start <= tail_end else None
        return cls(*args,tuple(rows),tail,calls)

    def _tail_count(self, stop):
        if self.tail is None:
            return 0
        start,end,lower = self.tail
        stop = min(stop,end+1); count = max(0,stop-start)
        if not count:
            return 0
        residue = self.budget-self.cost_a*((stop-1)-self.known_a)
        return count*(self.known_b-lower+1)+floor_sum(count,self.cost_b,self.cost_a,residue)

    def count(self):
        return sum(hi-lo+1 for _,lo,hi in self.frontier)+(self._tail_count(self.tail[1]+1) if self.tail else 0)

    def rank(self, plan):
        if not isinstance(plan,(tuple,list)) or len(plan) != 2 or any(isinstance(v,bool) or not isinstance(v,Integral) for v in plan):
            raise ValueError('two integer total-attempt counts required')
        a,b = map(int,plan); before = 0
        for row,lo,hi in self.frontier:
            if row == a and lo <= b <= hi:
                return before+b-lo
            before += hi-lo+1
        if self.tail:
            start,end,lo = self.tail
            hi = self.known_b+(self.budget-self.cost_a*(a-self.known_a))//self.cost_b
            if start <= a <= end and lo <= b <= hi:
                return before+self._tail_count(a)+b-lo
        raise ValueError('plan is not in feasible population')

    def unrank(self, rank):
        if isinstance(rank,bool) or not isinstance(rank,Integral) or not 0 <= rank < self.count():
            raise ValueError('rank outside feasible population')
        r = int(rank)
        for a,lo,hi in self.frontier:
            if r <= hi-lo:
                return (a,lo+r)
            r -= hi-lo+1
        start,end,lower = self.tail
        lo,hi = start,end
        while lo < hi:
            mid = (lo+hi)//2
            if self._tail_count(mid+1) > r:
                hi = mid
            else:
                lo = mid+1
        return (lo,lower+r-self._tail_count(lo))

    def sample(self, rng):
        if not self.count():
            raise ValueError('empty population')
        return self.unrank(rng.randrange(self.count()))

    def minimum(self):
        candidates = [(a,lo) for a,lo,_ in self.frontier]
        if self.tail:
            candidates.append((self.tail[0],self.tail[2]))
        if not candidates:
            return {'additional_cost':None,'plans':[]}
        cost = lambda p: self.cost_a*(p[0]-self.known_a)+self.cost_b*(p[1]-self.known_b)
        best = min(map(cost,candidates))
        return {'additional_cost':best,'plans':[p for p in candidates if cost(p)==best]}

    def receipt(self):
        return {'count':str(self.count()),'budget':str(self.budget),'frontier_rows':len(self.frontier),
                'tail':self.tail,'exact_predicates':self.predicates,'minimum':self.minimum(),
                'target':self.target,'scope':'exact conditional scalar working model; frozen means/radius; no empirical guarantee'}
