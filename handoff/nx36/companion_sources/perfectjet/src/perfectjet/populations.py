"""Residual-capacity counting, original-order ranking, and exact weighted aggregation."""
from functools import lru_cache
from fractions import Fraction as Q
from .exact import matmul,matrix


class SelectionPopulation:
    """Nonnegative integral resource costs; original project order is preserved."""
    def __init__(self,costs,capacities,profits=None):
        self.costs=tuple(tuple(row) for row in costs)
        self.capacities=tuple(capacities)
        self.n=len(self.costs)
        if any(not isinstance(x,int) or x<0 for x in self.capacities):
            raise ValueError("capacities must be nonnegative integers")
        if any(len(row)!=len(self.capacities) or any(not isinstance(x,int) or x<0 for x in row)
               for row in self.costs):
            raise ValueError("compatible nonnegative integral resource costs required")
        self.profits=tuple(profits if profits is not None else [0]*self.n)
        if len(self.profits)!=self.n:raise ValueError("one profit per project required")
        self._count=lru_cache(None)(self._count_impl)
        self._opt=lru_cache(None)(self._opt_impl)

    def _count_impl(self,i,caps):
        if any(x<0 for x in caps):return 0
        if i==self.n:return 1
        included=tuple(x-c for x,c in zip(caps,self.costs[i]))
        return self._count(i+1,caps)+self._count(i+1,included)

    def count(self):
        return self._count(0,self.capacities)

    def _prefix(self,prefix):
        if len(prefix)>self.n or any(b not in (0,1) for b in prefix):
            raise ValueError("invalid prefix")
        caps=list(self.capacities)
        for i,b in enumerate(prefix):
            if b:caps=[x-c for x,c in zip(caps,self.costs[i])]
        return tuple(caps)

    def conditional_count(self,prefix):
        return self._count(len(prefix),self._prefix(prefix))

    def rank(self,bits):
        if len(bits)!=self.n or self.conditional_count(bits)!=1:
            raise ValueError("full feasible selection required")
        caps=self.capacities;r=0
        for i,b in enumerate(bits):
            if b:
                r+=self._count(i+1,caps)
                caps=tuple(x-c for x,c in zip(caps,self.costs[i]))
        return r

    def unrank(self,r):
        if not isinstance(r,int) or not 0<=r<self.count():raise ValueError("rank outside population")
        caps=self.capacities;bits=[]
        for i in range(self.n):
            zero=self._count(i+1,caps)
            if r<zero:bits.append(0)
            else:
                bits.append(1);r-=zero
                caps=tuple(x-c for x,c in zip(caps,self.costs[i]))
        return tuple(bits)

    def sample(self,rng):
        if not self.count():raise ValueError("empty population")
        return self.unrank(rng.randrange(self.count()))

    def _opt_impl(self,i,caps):
        if any(x<0 for x in caps):return None,0
        if i==self.n:return 0,1
        a,ta=self._opt(i+1,caps)
        b,tb=self._opt(i+1,tuple(x-c for x,c in zip(caps,self.costs[i])))
        if b is not None:b+=self.profits[i]
        if b is None or a>b:return a,ta
        if b>a:return b,tb
        return a,ta+tb

    def optimum(self):
        value,ties=self._opt(0,self.capacities)
        return {"value":value,"tie_count":ties}


    def _restricted(self,item,value,capacities=None):
        """Population of the other projects after fixing project `item` to 0 or 1."""
        caps=list(capacities or self.capacities)
        if value:caps=[x-c for x,c in zip(caps,self.costs[item])]
        if any(x<0 for x in caps):return None
        keep=[i for i in range(self.n) if i!=item]
        return SelectionPopulation([self.costs[i] for i in keep],caps,[self.profits[i] for i in keep])

    def inclusion_profile(self):
        """Exact share of feasible and of optimal selections containing each project."""
        total=self.count();best=self.optimum()
        rows=[]
        for i in range(self.n):
            sub=self._restricted(i,1)
            with_i=sub.count() if sub else 0
            opt_i=0
            if sub:
                o=sub.optimum()
                if o["value"] is not None and o["value"]+self.profits[i]==best["value"]:opt_i=o["tie_count"]
            rows.append({"project":i,"feasible_share":Q(with_i,total) if total else None,
                         "optimal_share":Q(opt_i,best["tie_count"]) if best["tie_count"] else None})
        return rows

    def attribution(self):
        """How many selections each capacity constraint removes on its own.

        relaxed_k counts selections with constraint k dropped; relaxed_k - count is the
        number violating constraint k and no other. The unconstrained population is 2^n.
        """
        total=self.count();out=[]
        for k in range(len(self.capacities)):
            caps=list(self.capacities);caps[k]=sum(row[k] for row in self.costs)
            relaxed=SelectionPopulation(self.costs,caps,self.profits).count()
            out.append({"constraint":k,"capacity":self.capacities[k],"count_without":relaxed,
                        "removed_only_by_this":relaxed-total})
        return {"unconstrained":2**self.n,"feasible":total,"constraints":out}


def weighted_quotient_replay(a,aggregation,reduced):
    """Column-state convention: RA = Abar R."""
    a,r,b=matrix(a),matrix(aggregation),matrix(reduced)
    return matmul(r,a)==matmul(b,r)


def histogram_partition(histogram,weights):
    """Exact finite weighted partition function from type-count multiplicities."""
    total=Q(0)
    for counts,multiplicity in histogram.items():
        if len(counts)!=len(weights):raise ValueError("type dimensions differ")
        term=Q(multiplicity)
        for n,w in zip(counts,weights):term*=Q(w)**n
        total+=term
    return total
