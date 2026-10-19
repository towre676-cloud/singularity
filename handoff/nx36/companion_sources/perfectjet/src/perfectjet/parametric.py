"""Multi-parameter rank loci by comprehensive Gaussian elimination.

A(t) has entries in Q[t1,...,tk]. Elimination branches on each candidate pivot
p: either p is nonzero (added to the inequations) or p vanishes (added to the
equations). A branch survives only if its constructible set
V(E) minus V(product of N) is nonempty over the algebraic closure, decided by
the Rabinowitsch test 1 not in <E, 1-z*prod(N)> with an exact Groebner basis.
The leaves partition parameter space into cells of constant rank; the drop
locus is the union of the cells whose rank is below the generic rank.

Polynomials are dicts {exponent tuple: Fraction}; the order is graded reverse
lexicographic.
"""
from fractions import Fraction as Q
from itertools import product
from .exact import rref

# ---------------------------------------------------------------- polynomials


def _key(e):return (sum(e),tuple(-x for x in reversed(e)))


def clean(p):return {e:Q(c) for e,c in p.items() if c}


def const(c,n):return clean({(0,)*n:Q(c)})


def var(i,n):return {tuple(int(j==i) for j in range(n)):Q(1)}


def add(p,q):
    out=dict(p)
    for e,c in q.items():
        v=out.get(e,0)+c
        if v:out[e]=v
        else:out.pop(e,None)
    return out


def scale(p,c,mono=None):
    if not c:return {}
    if mono is None:return {e:v*c for e,v in p.items()}
    return {tuple(a+b for a,b in zip(e,mono)):v*c for e,v in p.items()}


def sub(p,q):return add(p,scale(q,-1))


def mul(p,q):
    out={}
    for e,c in p.items():
        for f,d in q.items():
            g=tuple(a+b for a,b in zip(e,f));v=out.get(g,0)+c*d
            if v:out[g]=v
            else:out.pop(g,None)
    return out


def lead(p,key=_key):
    e=max(p,key=key);return e,p[e]


def monic(p,key=_key):
    if not p:return {}
    _,c=lead(p,key);return {e:v/c for e,v in p.items()}


def total_degree(p):return max((sum(e) for e in p),default=-1)


def evaluate(p,point):
    out=Q(0)
    for e,c in p.items():
        t=c
        for x,k in zip(point,e):t*=Q(x)**k
        out+=t
    return out


def extend(p,n):
    """Append zero exponents up to n variables."""
    return {e+(0,)*(n-len(e)):c for e,c in p.items()}


def fmt(p,names=None):
    if not p:return "0"
    n=len(next(iter(p)));names=names or [f"t{i+1}" for i in range(n)]
    terms=[]
    for e in sorted(p,key=_key,reverse=True):
        c=p[e];mono="*".join(f"{v}^{k}" if k>1 else v for v,k in zip(names,e) if k)
        if not mono:terms.append(str(c))
        elif c==1:terms.append(mono)
        elif c==-1:terms.append("-"+mono)
        else:terms.append(f"{c}*{mono}")
    return " + ".join(terms).replace("+ -","- ")


# ------------------------------------------------------------- Groebner bases


def _divides(a,b):return all(x<=y for x,y in zip(a,b))


def reduce(p,basis,key=_key):
    """Full normal form of p modulo the list basis."""
    leads=[lead(g,key) for g in basis];p=dict(p);rem={}
    while p:
        e,c=lead(p,key)
        for g,(le,lc) in zip(basis,leads):
            if _divides(le,e):
                p=sub(p,scale(g,c/lc,tuple(a-b for a,b in zip(e,le))));break
        else:
            rem[e]=c;del p[e]
    return rem


def _lcm(a,b):return tuple(max(x,y) for x,y in zip(a,b))


def groebner(polys,key=_key):
    """Reduced Groebner basis (Buchberger with the product and chain criteria)."""
    basis=[monic(p,key) for p in polys if p]
    if not basis:return []
    lt=[lead(g,key)[0] for g in basis]
    pairs={(i,j) for j in range(len(basis)) for i in range(j)}
    while pairs:
        i,j=min(pairs,key=lambda ij:(sum(_lcm(lt[ij[0]],lt[ij[1]])),ij));pairs.discard((i,j))
        a,b=lt[i],lt[j];l=_lcm(a,b)
        if all(x+y==z for x,y,z in zip(a,b,l)):continue  # coprime leading monomials
        if any(k!=i and k!=j and _divides(lt[k],l)
               and (min(i,k),max(i,k)) not in pairs and (min(j,k),max(j,k)) not in pairs
               for k in range(len(basis))):continue  # chain criterion
        sp=sub(scale(basis[i],1,tuple(x-y for x,y in zip(l,a))),scale(basis[j],1,tuple(x-y for x,y in zip(l,b))))
        r=reduce(sp,basis,key)
        if r:
            r=monic(r,key);e=lead(r,key)[0]
            if not any(e):return [const(1,len(e))]
            basis.append(r);lt.append(e);k=len(basis)-1
            pairs.update((m,k) for m in range(k))
    keep=[]
    for idx,e in enumerate(lt):
        if not any(_divides(lt[o],e) and (lt[o]!=e or o<idx) for o in range(len(lt)) if o!=idx):keep.append(idx)
    kept=[basis[i] for i in keep]
    out=[monic(reduce(g,[h for h in kept if h is not g],key),key) for g in kept]
    return sorted(out,key=lambda g:key(lead(g,key)[0]))


def is_unit_ideal(gb):return len(gb)==1 and all(x==0 for x in lead(gb[0])[0])


def nonempty(equations,inequations,n):
    """Is V(E) minus V(prod N) nonempty over the algebraic closure? (Rabinowitsch.)"""
    if not equations:return all(inequations)
    if not inequations:return not is_unit_ideal(groebner(equations))
    prod_n=const(1,n)
    for q in inequations:prod_n=mul(prod_n,q)
    eqs=[extend(p,n+1) for p in equations]
    z=var(n,n+1);eqs.append(sub(const(1,n+1),mul(z,extend(prod_n,n+1))))
    return not is_unit_ideal(groebner(eqs))


def _elim_key(e):
    """Block order eliminating the last variable."""
    return (e[-1],_key(e[:-1]))


def saturate(equations,inequations,n):
    """Groebner basis of E : (prod N)^infinity, the ideal of the cell's Zariski closure up to radical."""
    if not inequations:return groebner(equations)
    prod_n=const(1,n)
    for q in inequations:prod_n=mul(prod_n,q)
    eqs=[extend(p,n+1) for p in equations]
    eqs.append(sub(const(1,n+1),mul(var(n,n+1),extend(prod_n,n+1))))
    g=groebner(eqs,_elim_key)
    return groebner([{e[:-1]:c for e,c in p.items()} for p in g if all(e[-1]==0 for e in p)])


def divide(p,q):
    """Exact quotient p/q in Q[t], or None when q does not divide p."""
    quo={};p=dict(p);lq,cq=lead(q)
    while p:
        e,c=lead(p)
        if not _divides(lq,e):return None
        m=tuple(x-y for x,y in zip(e,lq));quo[m]=c/cq
        p=sub(p,scale(q,c/cq,m))
    return quo


def _lex(e):return e


def rational_points(gb,n):
    """Rational points of a zero-dimensional ideal, by lex elimination and the rational root theorem."""
    from .loci import rational_roots
    g=groebner(gb,_lex)
    if is_unit_ideal(g):return []
    if n==0:return [()]
    last=[p for p in g if all(all(x==0 for x in e[:-1]) for e in p)]
    if not last:raise ValueError("ideal is not zero-dimensional")
    uni=[Q(0)]*(max(e[-1] for e in last[0])+1)
    for e,c in last[0].items():uni[e[-1]]=c
    out=[]
    for root in rational_roots(uni):
        sub_polys=[]
        for p in g:
            r={}
            for e,c in p.items():
                k=e[:-1];r[k]=r.get(k,0)+c*root**e[-1]
            r=clean(r)
            if r:sub_polys.append(r)
        if any(len(p)==1 and not any(next(iter(p))) for p in sub_polys):continue
        for rest in rational_points(sub_polys,n-1) if n>1 else [()]:out.append(rest+(root,))
    return sorted(set(out))


# --------------------------------------------------------- comprehensive rank


def saturate_by(ideal,q,n):
    """Groebner basis of I : q^infinity, by eliminating z from I + <1 - z q>."""
    if total_degree(q)<=0:return ideal
    if not ideal:return []
    eqs=[extend(p,n+1) for p in ideal]
    eqs.append(sub(const(1,n+1),mul(var(n,n+1),extend(q,n+1))))
    g=groebner(eqs,_elim_key)
    return groebner([{e[:-1]:c for e,c in p.items()} for p in g if all(e[-1]==0 for e in p)])


def rank_cells(a,nvars,equations=None,inequations=None):
    """Partition of parameter space (or of one cell of it) into constructible cells of constant rank.

    Each cell is V(S) minus V(prod N) with S already saturated by every member of N.
    Then the cell is nonempty exactly when S is not the unit ideal, and it is dense
    in V(S), so a pivot p vanishes on the whole cell exactly when S : p^infinity = 1.
    A starting cell V(equations) minus V(prod inequations) restricts the partition to
    that cell; equations must already be saturated by the inequations.
    """
    a=[[clean(p) for p in row] for row in a]
    cells=[]

    def content(row):
        for p in row:
            if p:
                _,c=lead(p);return [scale(q,1/c) for q in row]
        return row

    def run(m,S,N,r,prev):
        m=[[reduce(p,S) if S else p for p in row] for row in m]
        m=[row for row in m if any(row)]
        candidates=[(i,j) for i,row in enumerate(m) for j,p in enumerate(row) if p]
        if not candidates:
            cells.append({"equations":S,"inequations":N,"rank":r});return
        i,j=min(candidates,key=lambda ij:(total_degree(m[ij[0]][ij[1]]),len(m[ij[0]][ij[1]])))
        p=m[i][j]
        constant=total_degree(p)==0
        pivot_ideal=S if constant else saturate_by(S,p,nvars)
        if not is_unit_ideal(pivot_ideal):
            # Pivot branch: p is nonzero throughout the cell.
            rest=[]
            for k,row in enumerate(m):
                if k==i:continue
                new=[sub(mul(p,x),mul(row[j],y)) for x,y in zip(row,m[i])]
                new=[x for c,x in enumerate(new) if c!=j]
                # Bareiss step: the previous pivot is nonzero on the cell, so dividing by it
                # (when exact) leaves the pointwise rank unchanged and stops degree doubling.
                if prev is not None and total_degree(prev)>0:
                    q=[divide(x,prev) if x else {} for x in new]
                    if all(v is not None for v in q):new=q
                rest.append(content(new))
            run(rest,pivot_ideal,N if constant else N+[p],r+1,p)
        if not constant:
            zero=groebner(S+[p])
            for q in N:
                if is_unit_ideal(zero):break
                zero=saturate_by(zero,q,nvars)
            if not is_unit_ideal(zero):run(m,zero,N,r,prev)

    run(a,list(equations or []),list(inequations or []),0,None)
    return cells


def generic_rank_cells(cells):return max(c["rank"] for c in cells)


def cell_contains(cell,point):
    return all(evaluate(p,point)==0 for p in cell["equations"]) and all(evaluate(q,point)!=0 for q in cell["inequations"])


def classify(cells,point):
    """Rank at a rational point read from the cell decomposition."""
    hits=[c["rank"] for c in cells if cell_contains(c,point)]
    if len(hits)!=1:raise AssertionError(f"point lies in {len(hits)} cells")
    return hits[0]


def drop_locus(a,nvars,names=None):
    cells=rank_cells(a,nvars);r=generic_rank_cells(cells)
    drops=[c for c in cells if c["rank"]<r]
    report=[]
    for c in drops:
        closure=c["equations"];dim=dimension(closure,nvars)
        row={"closure":[fmt(p,names) for p in closure],"excluding":[fmt(q,names) for q in c["inequations"]],
             "rank":c["rank"],"dimension":dim}
        if dim==0:
            row["rational_points"]=[pt for pt in rational_points(closure,nvars)
                                    if all(evaluate(q,pt)!=0 for q in c["inequations"])]
        report.append(row)
    return {"generic_rank":r,"cells":len(cells),"drop_cells":report,"_cells":cells}


def dimension(gb,n):
    """Krull dimension of Q[t]/(E): largest variable set free of leading monomials."""
    if not gb:return n
    if is_unit_ideal(gb):return -1
    leads=[lead(g)[0] for g in gb];best=0
    for mask in product((0,1),repeat=n):
        free=[i for i in range(n) if mask[i]]
        if all(any(e[i] for i in range(n) if i not in free) for e in leads):best=max(best,len(free))
    return best


# ----------------------------------------------------------- matrix recovery


def polynomial_matrix(fn,nvars,degree):
    """Recover A(t) whose entries have degree <= degree in each variable, from grid values."""
    grid=list(product(range(degree+1),repeat=nvars));monos=grid
    samples=[fn(*[Q(x) for x in pt]) for pt in grid]
    vander=[[Q(1) for _ in monos] for _ in grid]
    for r,pt in enumerate(grid):
        for c,e in enumerate(monos):
            v=Q(1)
            for x,k in zip(pt,e):v*=Q(x)**k
            vander[r][c]=v
    m=len(samples[0]);n=len(samples[0][0]) if m else 0
    out=[[None]*n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            aug=[row+[s[i][j]] for row,s in zip(vander,samples)]
            rr,_=rref(aug)
            out[i][j]=clean({e:rr[c][-1] for c,e in enumerate(monos)})
    return out


# ------------------------------------------------------------ partner family


def sextic_family(a,b):
    """x^6+y^6+a x^3y^3+b(x^4y^2+x^2y^4): the C3 family is the slice b=0."""
    from .polynomial import Poly
    x,y=Poly.variable(0),Poly.variable(1)
    return x**6+y**6+Q(a)*x**3*y**3+Q(b)*(x**4*y**2+x**2*y**4)


def partner_surface(degrees=range(3,7)):
    from .transvectants import gate_matrix
    out=[]
    for n in degrees:
        gates=polynomial_matrix(lambda a,b:gate_matrix(sextic_family(a,b),n,3)+gate_matrix(sextic_family(a,b),n,5),2,1)
        res=drop_locus(gates,2,["a","b"])
        out.append({"degree":n,"correction_rank":res["generic_rank"],"cells":res["cells"],
                    "drop_cells":res["drop_cells"]})
    return out


def exceptional_factorizations():
    """Exact factorizations of the rational exceptional sextics found by partner_surface."""
    from .polynomial import Poly
    x,y=Poly.variable(0),Poly.variable(1)
    table=[((16,-9),(x-y)**4*(x*x+4*x*y+y*y),"fourfold root"),
           ((-16,-9),(x+y)**4*(x*x-4*x*y+y*y),"fourfold root"),
           ((0,3),(x*x+y*y)**3,"perfect cube"),
           ((0,15),(x*x+y*y)*(x**4+14*x*x*y*y+y**4),"squarefree"),
           ((0,-5),(x*x+y*y)*(x*x-2*x*y-y*y)*(x*x+2*x*y-y*y),"squarefree")]
    return [{"a":a,"b":b,"factorization_verified":sextic_family(a,b)==f,"structure":s} for (a,b),f,s in table]


def surface_receipt(degrees=range(3,13)):
    rows=partner_surface(degrees)
    return {"family":"x^6+y^6+a x^3y^3+b(x^4y^2+x^2y^4); b=0 is the C3 family",
            "over":"cells are constructible sets over the algebraic closure; rational points listed separately",
            "degrees":rows,"exceptional_factorizations":exceptional_factorizations()}
