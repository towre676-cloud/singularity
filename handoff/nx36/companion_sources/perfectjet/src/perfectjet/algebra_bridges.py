"""Executable bridges among integer reconstruction, histories and algebraic laws.

Polynomial inputs use ``[{"exponents": [i,j], "coefficient": "p/q"}, ...]``;
integer/rational constants and dictionaries with tuple exponent keys also work.
No floating coefficient is silently interpreted as exact input. Rank cells are
algebraic parameter statements; Smith certificates apply at one specialization.
"""
from __future__ import annotations

from fractions import Fraction as Q
from math import comb, isqrt

from .quadratic import QuadraticSquare
from .observatory.arithmetic import pell_point, pell_residue_system
from .observatory.model import FiniteSystem
from .observatory.histories import HistoryPopulation
from . import parametric as P
from .exact import rank
from .lattice import smith_form, integer_solve, integer_kernel, saturation
from .invariants import invariant_relations, family_invariants


def _integer(value, name, minimum=None, maximum=None):
    if type(value) is not int or (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be an integer" + (f" in [{minimum},{maximum}]" if maximum is not None else f" >= {minimum}" if minimum is not None else ""))
    return value


def _rational(value):
    if type(value) is bool or not isinstance(value, (int, str, Q)):
        raise ValueError("exact integer or rational-string coefficients are required")
    try:return Q(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("invalid exact rational coefficient") from error


def _poly(value, nvars):
    if isinstance(value, (int, str, Q)):
        return P.const(_rational(value), nvars)
    if isinstance(value, dict):
        items=value.items()
    elif isinstance(value, (list, tuple)):
        try:items=[(t["exponents"],t["coefficient"]) for t in value]
        except (KeyError,TypeError) as error:raise ValueError("polynomial terms require exponents and coefficient") from error
    else:raise ValueError("polynomial must be a constant or exact term records")
    out={}
    for exponents, coefficient in items:
        if isinstance(exponents,str):
            try:exponents=tuple(int(x.strip()) for x in exponents.split(","))
            except ValueError as error:raise ValueError("invalid polynomial exponent key") from error
        try:e=tuple(exponents)
        except TypeError as error:raise ValueError("polynomial exponents must be arrays") from error
        if len(e)!=nvars or any(type(x) is not int or x<0 for x in e):
            raise ValueError("nonnegative integer exponents with one entry per parameter are required")
        out[e]=out.get(e,Q(0))+_rational(coefficient)
    return P.clean(out)


def _record(poly):
    return [{"exponents":list(e),"coefficient":str(c)} for e,c in sorted(poly.items())]


def _json(value):
    if isinstance(value,Q):return str(value)
    if isinstance(value,dict):return {k:_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_json(v) for v in value]
    return value


def _costs(costs):
    if not isinstance(costs,(tuple,list)) or len(costs)!=2:
        raise ValueError("costs must contain advance and retreat costs")
    return tuple(_integer(v,"action cost",1) for v in costs)


def _population_witness(population, word_rank):
    count=population.count();_integer(word_rank,"word_rank",0)
    if not count:
        if word_rank:raise ValueError("word_rank lies outside the empty population")
        return None
    word=population.unrank(word_rank)
    return {"rank":str(word_rank),"actions":[population.system.actions[a] for a in word],
            "rank_replayed":population.rank(word)==word_rank,
            "net_exponent":sum(1 if a==0 else -1 for a in word)}


def quadratic_population(k, a, b, c, nmax=10**6, nmin=0, max_scan=10**6):
    """All hits in an interval, carrying original and norm-equation witnesses."""
    q=QuadraticSquare(k,a,b,c)
    _integer(nmin,"nmin");_integer(nmax,"nmax");_integer(max_scan,"max_scan",1)
    if nmax<nmin:raise ValueError("nmax must be at least nmin")
    # Branches that enumerate a line, square roots or divisor candidates must
    # respect an explicit allowance rather than unexpectedly expanding a range.
    work=0
    if q.branch=="linear":
        work=(nmax-nmin+1) if b==0 else isqrt(max(0,q.F(nmin),q.F(nmax))//k)+2
    elif q.branch=="degenerate_square":
        work=2*max(abs(2*a*nmin+b),abs(2*a*nmax+b))+1
    elif q.branch=="finite" and q.d<0 and q.n0>=0:
        work=2*isqrt(q.n0//-q.d)+3
    elif q.branch=="finite" and q.d>=0 and q.n0:
        work=isqrt(abs(q.n0))
    if work>max_scan:raise ValueError(f"this branch needs approximately {work} candidates; increase max_scan explicitly")
    hits=q.hits(nmax,nmin)
    witnesses=[]
    for n in hits:
        y=q.y_of(n);X=2*a*n+b
        witnesses.append({"n":str(n),"y":str(y),"X":str(X),"Y":str(y),
                          "original_replayed":q.holds(n,y),
                          "norm_replayed":a==0 or X*X-q.d*y*y==q.n0})
    return {"operation":"quadratic","coefficients":{"k":k,"a":a,"b":b,"c":c},
            "interval":[str(nmin),str(nmax)],"branch":q.branch,"count":len(hits),"witnesses":witnesses,
            "transport":{"D":q.d,"N0":q.n0,"forward":"X=2an+b, Y=y", "inverse":"n=(X-b)/(2a), X=b mod 2a" if a else "linear congruence branch"},
            "orbit_structure":_json(q.orbit_structure()) if q.branch=="pell" else None,
            "scope":"Distinct integer n in the requested interval, with y>=0 used as its witness."}


def pell_history_bridge(D, unit, seed, modulus, horizon=20, accepted_x=None,
                        costs=(1,1), budget=None, word_rank=0, max_states=100000):
    """Exact modular seeded-orbit histories, independently checked by binomial fibers."""
    costs=_costs(costs)
    system,transport=pell_residue_system(D,unit,seed,modulus,accepted_x,costs=costs,max_states=max_states)
    population=HistoryPopulation(system,horizon,budget=budget)
    count=population.count();period=transport["period"]
    independent=sum(comb(horizon,k) for k in range(horizon+1)
                    if system.accepting[(2*k-horizon)%period]
                    and (budget is None or k*costs[0]+(horizon-k)*costs[1]<=budget))
    witness=_population_witness(population,word_rank)
    if witness:
        X,Y=pell_point(D,unit,seed,witness["net_exponent"],modulus)
        witness["endpoint_modulus"]={"X":X,"Y":Y}
    return {"operation":"pell_histories","transport":transport,"horizon":horizon,"budget":budget,
            "count":str(count),"independent_binomial_count":str(independent),
            "binomial_replayed":count==independent,"witness":witness,
            "scope":"Counts original advance/retreat words on the supplied modular seed/unit orbit; not distinct points or all integer norm solutions."}


def quadratic_history_bridge(k, a, b, c, horizon=20, orbit_index=0,
                             modulus=1, accepted_n=None, costs=(1,1), budget=None,
                             word_rank=0, max_bits=1000000):
    """Histories whose endpoint reconstructs an actual nonnegative quadratic hit.

    A finite exponent interval [-H,H] covers every length-H word from exponent0.
    Retaining the exponent prevents modular collisions from confusing negative,
    nonintegral and nonnegative original endpoints. The endpoint residue filter
    is on n modulo ``modulus``. Counts retain action-word multiplicity.
    """
    q=QuadraticSquare(k,a,b,c)
    if q.branch!="pell":raise ValueError("quadratic_histories requires the nonsquare Pell branch")
    _integer(horizon,"horizon",0,HistoryPopulation.MAX_HORIZON)
    _integer(orbit_index,"orbit_index",0);_integer(modulus,"modulus",1)
    costs=_costs(costs);structure=q.orbit_structure();orbits=structure["positive_orbits"]
    if orbit_index>=len(orbits):raise ValueError("orbit_index lies outside the normalized positive unit classes")
    if accepted_n is None:accepted=None
    else:
        if type(accepted_n) is int:accepted_n=[accepted_n]
        if not isinstance(accepted_n,(tuple,list)):raise ValueError("accepted_n must be an integer or residue array")
        accepted={_integer(v,"accepted_n residue")%modulus for v in accepted_n}
    unit,canonical=structure["unit"],orbits[orbit_index]["seed"]
    if not orbits[orbit_index]["admissible"]:
        raise ValueError("this unit class never reconstructs an integral n")
    _integer(max_bits,"max_bits",1)
    seed,shift=canonical,0
    while (seed[0]-b)%(2*a) or (seed[0]-b)//(2*a)<0:
        X,Y=seed
        seed=(X*unit[0]+q.d*Y*unit[1],X*unit[1]+Y*unit[0]);shift+=1
        if max(abs(seed[0]).bit_length(),abs(seed[1]).bit_length())>max_bits:
            raise ValueError("first nonnegative reconstructed seed exceeds max_bits")
    # The allocation bound is checked before constructing original coordinates.
    pell_point(q.d,unit,seed,-horizon,max_bits=max_bits)
    pell_point(q.d,unit,seed,horizon,max_bits=max_bits)
    endpoints=[]
    for exponent in range(-horizon,horizon+1):
        X,Y=pell_point(q.d,unit,seed,exponent,max_bits=max_bits)
        n=(X-b)//(2*a) if (X-b)%(2*a)==0 else None
        accept=n is not None and n>=0 and (accepted is None or n%modulus in accepted)
        endpoints.append({"exponent":exponent,"X":X,"Y":Y,"n":n,"accepting":accept})
    size=len(endpoints)
    system=FiniteSystem(states=tuple(f"exponent {j}" for j in range(-horizon,horizon+1)),
                        actions=("advance","retreat"),costs=costs,
                        transitions=tuple((i+1 if i+1<size else None,i-1 if i else None) for i in range(size)),
                        observations=tuple(e["X"]%(2*a*modulus) for e in endpoints),
                        targets=tuple(str(e["n"]) if e["n"] is not None else "nonintegral" for e in endpoints),
                        accepting=tuple(e["accepting"] for e in endpoints),initial=horizon,
                        name="Quadratic reconstruction-carrying history bridge")
    population=HistoryPopulation(system,horizon,budget=budget);count=population.count()
    independent=sum(comb(horizon,j) for j in range(horizon+1)
                    if endpoints[2*j]["accepting"] and (budget is None or j*costs[0]+(horizon-j)*costs[1]<=budget))
    witness=_population_witness(population,word_rank)
    if witness:
        endpoint=endpoints[witness["net_exponent"]+horizon];n,Y=endpoint["n"],endpoint["Y"]
        witness["endpoint"]={"n":str(n),"y":str(abs(Y)),"X":str(endpoint["X"]),"Y":str(Y),
                             "original_replayed":q.holds(n,Y),"nonnegative":n>=0}
    return {"operation":"quadratic_histories","coefficients":{"k":k,"a":a,"b":b,"c":c},
            "orbit_index":orbit_index,"canonical_seed":list(canonical),"seed_index_shift":shift,
            "seed":list(seed),"unit":list(unit),"D":q.d,"N0":q.n0,
            "horizon":horizon,"modulus":modulus,"accepted_n":None if accepted is None else sorted(accepted),
            "budget":budget,"count":str(count),"independent_binomial_count":str(independent),
            "binomial_replayed":count==independent,"witness":witness,
            "asymptotic":structure["asymptotic"],
            "scope":"One normalized seed class; endpoint n must be integral and >=0. Different action words remain distinct even at the same n."}


def bounded_invariant_laws(equations, max_weight=6, nvars=2, inequations=None, invariants=None):
    """Find the first nonempty weight of invariant laws on an algebraic cell.

    Defaults to Clebsch A,B,C,D of the two-parameter sextic family. Custom exact
    parameter polynomials allow the same bounded mechanism on other models.
    The search reports a degree bound and never claims all invariant relations.
    """
    _integer(nvars,"nvars",1,3);_integer(max_weight,"max_weight",1,8)
    equations=[_poly(p,nvars) for p in equations]
    inequations=[_poly(p,nvars) for p in (inequations or [])]
    ideal=P.saturate(equations,inequations,nvars)
    if P.is_unit_ideal(ideal):raise ValueError("the declared algebraic cell is empty")
    if invariants is None:
        if nvars!=2:raise ValueError("the default sextic invariants have two parameters")
        inv=family_invariants()
    else:
        if len(invariants)!=4:raise ValueError("four invariants A,B,C,D of weights 1,2,3,5 are required")
        inv=[_poly(p,nvars) for p in invariants]
    found=invariant_relations(ideal,max_weight,inv,nvars)
    return {"operation":"invariant_laws","parameter_count":nvars,"max_weight":max_weight,
            "searched_coefficient_degree":2*max_weight if invariants is None else None,
            "cell_closure":[_record(p) for p in ideal],"inequations":[_record(p) for p in inequations],
            "invariants":[_record(p) for p in inv],"weights":[1,2,3,5],"relations":_json(found),
            "scope":"Exact laws on the cell closure, excluding identities of the whole parameter family; first nonempty searched weight only, not an unrestricted classification."}


def parameter_integer_analysis(matrix, point, rhs=None, nvars=None, equations=None, inequations=None):
    """Combine comprehensive rank cells with pointwise integer certificates."""
    if nvars is None:nvars=len(point)
    _integer(nvars,"nvars",1,3)
    if len(point)!=nvars:raise ValueError("point must contain one coordinate per parameter")
    point=tuple(_rational(v) for v in point)
    if not matrix or not matrix[0] or len(matrix)>8 or len(matrix[0])>8:
        raise ValueError("a nonempty polynomial matrix of at most 8 by 8 is required")
    width=len(matrix[0])
    if any(len(row)!=width for row in matrix):raise ValueError("matrix must be rectangular")
    poly=[[_poly(value,nvars) for value in row] for row in matrix]
    eq=[_poly(p,nvars) for p in (equations or [])];neq=[_poly(p,nvars) for p in (inequations or [])]
    ideal=P.saturate(eq,neq,nvars)
    if P.is_unit_ideal(ideal):raise ValueError("the declared algebraic parameter cell is empty")
    cells=P.rank_cells(poly,nvars,ideal,neq)
    matching=[i for i,cell in enumerate(cells) if P.cell_contains(cell,point)]
    if len(matching)!=1:raise ValueError("specialization lies outside the declared parameter cell")
    specialized=[[P.evaluate(p,point) for p in row] for row in poly]
    point_rank=rank(specialized,width)
    if point_rank!=cells[matching[0]]["rank"]:raise ArithmeticError("specialized rank disagrees with its cell")
    out={"operation":"parameter_smith","point":[str(x) for x in point],
         "specialized_matrix":_json(specialized),"rank":point_rank,"matching_cell":matching[0],
         "rank_replayed":True,"cells":[{"rank":c["rank"],"equations":[_record(p) for p in c["equations"]],
                                          "inequations":[_record(p) for p in c["inequations"]]} for c in cells],
         "integer_scope":"Smith results concern this specialization only; constant algebraic rank does not imply constant integer solvability."}
    if any(x.denominator!=1 for row in specialized for x in row):
        out["integer_status"]="nonintegral specialization";out["smith"]=None
        return out
    integer_matrix=[[int(x) for x in row] for row in specialized]
    u,d,v=smith_form(integer_matrix)
    out.update(integer_status="integer matrix",smith={"U":u,"D":d,"V":v},
               integer_kernel=integer_kernel(integer_matrix),row_lattice=_json(saturation(integer_matrix)))
    if rhs is not None:
        if len(rhs)!=len(matrix):raise ValueError("rhs must contain one integer per row")
        rhs=[_integer(v,"rhs value") for v in rhs]
        result=integer_solve(integer_matrix,rhs)
        if result["solvable"]:
            replay=[sum(a*x for a,x in zip(row,result["solution"])) for row in integer_matrix]==rhs
        else:
            y=result["certificate"]
            row=[sum(y[i]*integer_matrix[i][j] for i in range(len(y))) for j in range(width)]
            target=sum(p*q for p,q in zip(y,rhs))
            replay=(all(x.denominator==1 for x in row) and target.denominator!=1) if result["rational"] else (not any(row) and target!=0)
        result["certificate_replayed"]=replay
        if not replay:raise ArithmeticError("integer solution/certificate failed replay")
        out["integer_solution"]=_json(result)
    return out


def evaluate(operation, params=None):
    """JSON-friendly dispatch used by the CLI, workbench and saved research packets."""
    operations={"quadratic":quadratic_population,"quadratic_histories":quadratic_history_bridge,
                "pell_histories":pell_history_bridge,"invariant_laws":bounded_invariant_laws,
                "parameter_smith":parameter_integer_analysis}
    if operation not in operations:raise ValueError("unknown algebra bridge operation: "+str(operation))
    if params is None:params={}
    if not isinstance(params,dict):raise ValueError("params must be an object")
    return operations[operation](**params)


def receipt():
    """Fast, reproducible examples with independent history and certificate checks."""
    t=[{"exponents":[1],"coefficient":"1"}]
    # A=t, B=t^2+u: B-A^2 is a law exactly on u=0, not on the whole family.
    custom=[{(1,0):1},{(2,0):1,(0,1):1},{(3,0):1},{(5,0):1}]
    return {"schema":"perfectjet/algebra-bridges/1",
            "quadratic":quadratic_population(2,1,0,7,10**12),
            "quadratic_histories":quadratic_history_bridge(2,1,0,7,horizon=12),
            "pell_histories":pell_history_bridge(2,[3,2],[1,0],35,horizon=100,accepted_x=[1]),
            "invariant_laws":bounded_invariant_laws([{(0,1):1}],2,invariants=custom),
            "parameter_smith":parameter_integer_analysis([[t,0],[0,2]],[2],rhs=[1,2]),
            "scope":"Exact finite algebraic bridges, with local integer certificates and explicit bounded searches."}
