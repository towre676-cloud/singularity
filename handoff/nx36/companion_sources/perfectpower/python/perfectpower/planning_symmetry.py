"""Weighted permutation orbits of independent interchangeable binary choices."""
from math import comb
from .divisor_square import WorkLimit

class SymmetryIndex:
    def __init__(self,planner):
        self.planner=planner
        keys=[(v[0],v[1]) for v in planner.variables]
        self.groups=tuple(dict.fromkeys(keys));self.ids=[self.groups.index(k) for k in keys]
        self.sizes=tuple(keys.count(k) for k in self.groups)
        self.memo={};self.edges=0
    def query(self,prefix):
        p=self.planner;p._mask(prefix)
        sizes=list(self.sizes);used=[0]*len(p.lower);score=0
        for j,x in enumerate(prefix):
            g=self.ids[j];sizes[g]-=1;c,profit=self.groups[g]
            for k,w in enumerate(c):used[k]+=x*w
            score+=x*profit
        if any(u>hi for u,hi in zip(used,p.upper)):return (0,None,0)
        lo=tuple(max(0,l-u) for l,u in zip(p.lower,used));hi=tuple(h-u for h,u in zip(p.upper,used))
        a=self.fold(tuple(sizes),lo,hi)
        from .planning import bounded_score
        return a[0],None if a[1] is None else bounded_score(a[1]+score),a[2]
    def fold(self,sizes,lo,hi):
        maximum=tuple(sum(n*c[k] for n,(c,profit) in zip(sizes,self.groups)) for k in range(len(lo)))
        hi=tuple(min(h,m) for h,m in zip(hi,maximum))
        if any(l>m or h<0 for l,m,h in zip(lo,maximum,hi)):return (0,None,0)
        if not any(sizes):return (1,0,1) if not any(lo) else (0,None,0)
        key=(sizes,lo,hi)
        if key in self.memo:return self.memo[key]
        p=self.planner
        if len(self.memo)>=p.state_limit:raise WorkLimit('symmetry state budget exceeded')
        g=next(i for i,n in enumerate(sizes) if n);n=sizes[g];c,profit=self.groups[g]
        rest=list(sizes);rest[g]=0;rest=tuple(rest)
        count,best,ties=0,None,0
        for k in range(n+1):
            if any(k*w>h for w,h in zip(c,hi)):break
            self.edges+=1
            if self.edges>p.edge_limit:raise WorkLimit('symmetry edge budget exceeded')
            a=self.fold(rest,tuple(max(0,l-k*w) for l,w in zip(lo,c)),tuple(h-k*w for h,w in zip(hi,c)))
            if not a[0]:continue
            from .planning import bounded_score
            multiplicity=comb(n,k);count+=multiplicity*a[0];value=bounded_score(k*profit+a[1])
            if best is None or value>best:best=value;ties=multiplicity*a[2]
            elif value==best:ties+=multiplicity*a[2]
        # Reserve/check on insertion too: recursive calls can fill the budget.
        if len(self.memo)>=p.state_limit:raise WorkLimit('symmetry state budget exceeded')
        self.memo[key]=(count,best,ties);return self.memo[key]
