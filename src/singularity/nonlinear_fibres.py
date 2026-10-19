"""Exact bounded polynomial ambiguity witnesses and regular second variations.

No function turns finite witness coverage into global fibre identification.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import combinations
from ._application_exact import vector,matrix,dot,apply,multiply,transpose,rref,solve,rational


@dataclass(frozen=True)
class Polynomial:
    dimension:int
    terms:tuple

    def __init__(self,dimension,terms):
        if type(dimension) is not int or not 1<=dimension<=4:raise ValueError("dimension must be 1..4")
        items=terms.items() if isinstance(terms,dict) else terms
        clean={}
        for powers,c in items:
            powers=tuple(powers);c=rational(c)
            if len(powers)!=dimension or any(type(p) is not int or p<0 for p in powers) or sum(powers)>4:raise ValueError("invalid monomial")
            clean[powers]=clean.get(powers,Q())+c
        clean={p:c for p,c in clean.items() if c}
        if len(clean)>32:raise ValueError("term budget")
        object.__setattr__(self,"dimension",dimension);object.__setattr__(self,"terms",tuple(sorted(clean.items())))

    def evaluate(self,x):
        x=vector(x)
        if len(x)!=self.dimension:raise ValueError("dimension mismatch")
        out=Q()
        for p,c in self.terms:
            for v,e in zip(x,p):c*=v**e
            out+=c
        return out

    def derivative(self,j):
        if type(j) is not int or not 0<=j<self.dimension:raise ValueError("invalid coordinate")
        out=[]
        for p,c in self.terms:
            if p[j]:
                z=list(p);z[j]-=1;out.append((tuple(z),c*p[j]))
        return Polynomial(self.dimension,out)

    def gradient(self,x):return tuple(self.derivative(j).evaluate(x) for j in range(self.dimension))

    def hessian(self,x):
        # Direct coefficient formula, separate from derivative composition.
        x=vector(x);out=[]
        for i in range(self.dimension):
            row=[]
            for j in range(self.dimension):
                value=Q()
                for p,c in self.terms:
                    z=list(p)
                    if not z[i]:continue
                    c*=z[i];z[i]-=1
                    if not z[j]:continue
                    c*=z[j];z[j]-=1
                    for a,b in zip(x,z):c*=a**b
                    value+=c
                row.append(value)
            out.append(tuple(row))
        return tuple(out)


@dataclass(frozen=True)
class PolynomialFibre:
    lower:tuple
    upper:tuple
    observations:tuple
    target:Polynomial
    equations:tuple=()
    inequalities:tuple=()

    def __post_init__(self):
        lo,hi=vector(self.lower),vector(self.upper)
        if len(lo)!=self.target.dimension or len(hi)!=len(lo) or any(a>b for a,b in zip(lo,hi)):raise ValueError("finite compact box required")
        ps=tuple(self.observations)+tuple(self.equations)+tuple(self.inequalities)
        if any(not isinstance(p,Polynomial) or p.dimension!=len(lo) for p in ps):raise ValueError("polynomial dimension mismatch")
        object.__setattr__(self,"lower",lo);object.__setattr__(self,"upper",hi)

    def admissible(self,x):
        x=vector(x)
        return (len(x)==len(self.lower) and all(a<=v<=b for a,v,b in zip(self.lower,x,self.upper)) and
                all(p.evaluate(x)==0 for p in self.equations) and all(p.evaluate(x)>=0 for p in self.inequalities))


def verify_witness(fibre,x,y,minimum_gap=0):
    x,y=vector(x),vector(y);gap=rational(minimum_gap)
    if gap<0:raise ValueError("negative requested gap")
    if not fibre.admissible(x) or not fibre.admissible(y):return {"status":"invalid_state"}
    ox=tuple(p.evaluate(x) for p in fibre.observations);oy=tuple(p.evaluate(y) for p in fibre.observations)
    if ox!=oy:return {"status":"observation_mismatch"}
    delta=abs(fibre.target.evaluate(x)-fibre.target.evaluate(y))
    return {"status":"verified_ambiguity" if delta>0 and delta>=gap else "no_positive_gap","states":(x,y),"observation":ox,"target_gap":delta,"diameter_lower_bound":delta,"complete_diameter":None}


def affine_quadratic_constancy(x0,N,g,Qmatrix,*,relatively_open):
    x0,g=vector(x0),vector(g);N=matrix(N);q=matrix(Qmatrix)
    n=len(x0)
    if len(g)!=n or len(N)!=n or len(q)!=n or any(len(r)!=n for r in q):raise ValueError("shape mismatch")
    if type(relatively_open) is not bool:raise TypeError("relatively_open must be explicit bool")
    qs=tuple(tuple((q[i][j]+q[j][i])/2 for j in range(n)) for i in range(n))
    nt=transpose(N);lin=apply(nt,tuple(a+b for a,b in zip(g,apply(qs,x0))))
    quad=multiply(multiply(nt,qs),N)
    zero=not any(lin) and not any(v for r in quad for v in r)
    return {"status":"constant_on_affine_fibre" if zero else ("nonconstant_on_relatively_open_fibre" if relatively_open else "domain_analysis_required"),"linear_coefficients":lin,"quadratic_hessian":quad,"symmetrized_target_matrix":qs,"relatively_open":relatively_open}


def curved_second_variation(constraints,target,point,tangent):
    constraints=tuple(constraints);x,n=vector(point),vector(tangent)
    if not constraints:raise ValueError("at least one constraint required")
    if any(k.evaluate(x) for k in constraints):raise ValueError("point is not on the constraint fibre")
    jac=tuple(k.gradient(x) for k in constraints);grad=target.gradient(x)
    if len(rref(jac)[1])<len(jac):return {"status":"singular_stratum"}
    if any(dot(r,n) for r in jac):raise ValueError("direction is not tangent")
    lam=solve(transpose(jac),grad,len(jac))
    if lam is None:return {"status":"not_stationary_on_fibre"}
    h=target.hessian(x);kh=tuple(k.hessian(x) for k in constraints)
    corrected=tuple(tuple(h[i][j]-sum((v*a[i][j] for v,a in zip(lam,kh)),Q()) for j in range(len(x))) for i in range(len(x)))
    curvature=tuple(dot(n,apply(a,n)) for a in kh)
    acceleration=solve(jac,tuple(-v for v in curvature),len(x))
    return {"status":"regular_stationary","multipliers":lam,"second_variation":dot(n,apply(corrected,n)),"corrected_hessian":corrected,"one_compatible_acceleration":acceleration,"constraint_curvatures":curvature}


def minimum_witness_repair(witness_pairs,sensors):
    """sensors=(identifier, Polynomial, deterministic radius, cost)."""
    pairs=tuple((vector(x),vector(y)) for x,y in witness_pairs);sensors=tuple(sensors)
    if len(sensors)>6 or len(pairs)>256:raise ValueError("pilot work budget")
    if len({s[0] for s in sensors})!=len(sensors):raise ValueError("unique sensor identifiers required")
    for _,_,e,c in sensors:
        if rational(e)<0 or rational(c)<0:raise ValueError("negative radius or cost")
    best=None
    for k in range(len(sensors)+1):
        for ix in combinations(range(len(sensors)),k):
            if not all(any(abs(sensors[i][1].evaluate(x)-sensors[i][1].evaluate(y))>2*rational(sensors[i][2]) for i in ix) for x,y in pairs):continue
            cost=sum((rational(sensors[i][3]) for i in ix),Q());names=tuple(sensors[i][0] for i in ix)
            score=(cost,names)
            if best is None or score<best:best=score
    return {"status":"infeasible_finite_witnesses" if best is None else "optimal_finite_witness_repair","selected":None if best is None else best[1],"cost":None if best is None else best[0],"coverage_scope":"retained_finite_pairs_only","global_fibre_constancy":False}
