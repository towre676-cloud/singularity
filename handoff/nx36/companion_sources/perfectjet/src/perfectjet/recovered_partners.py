"""Exact archived quintic partners and usable universal sextic constructions.

This module replays instances with rational polynomial arithmetic. It does not
rerun the archived R5 maximal-minor elimination, certify its orbit count, or
assert the still-open converse for the degree-12 construction.
"""
from __future__ import annotations

from fractions import Fraction as Q

from .polynomial import Poly
from .transvectants import transvectant, gate_matrix, partner_dimensions
from .invariants import (clebsch, cubic_gate_identity, quartic_covariant_partner,
                         degree12_partner, degree12_gate_identities)
from .exact import nullspace
from .loci import trim, derivative, pgcd, degree


def _form(value, default=None):
    if value is None:
        if default is not None:return default
        x,y=Poly.variable(0),Poly.variable(1)
        return x**6+x**3*y**3+x*x*y**4+x**4*y*y+y**6
    if isinstance(value,Poly):f=value
    else:
        if not isinstance(value,(list,tuple)):raise ValueError("form must be an exact binary-form term array")
        terms={}
        for term in value:
            if not isinstance(term,dict) or "exponents" not in term or "coefficient" not in term:
                raise ValueError("each term requires exponents and coefficient")
            e=term["exponents"];c=term["coefficient"]
            if not isinstance(e,(tuple,list)) or len(e)!=2 or any(type(k) is not int or k<0 for k in e):
                raise ValueError("binary-form exponents must be two nonnegative integers")
            if type(c) is bool or not isinstance(c,(int,str,Q)):
                raise ValueError("exact integer or rational-string coefficients are required")
            try:c=Q(c)
            except (ValueError,ZeroDivisionError) as error:raise ValueError("invalid rational coefficient") from error
            terms[tuple(e)]=terms.get(tuple(e),Q(0))+c
        f=Poly(terms)
    if f.variables!=2 or not f.terms or any(sum(e)!=6 for e in f.terms):
        raise ValueError("a nonzero homogeneous binary sextic is required")
    return f


def _zero(form):return not form.terms


def _squarefree(form):
    d=max(sum(e) for e in form.terms)
    p=trim([form.terms.get((i,d-i),Q(0)) for i in range(d+1)])
    # Homogeneous roots at infinity must also have multiplicity at most one.
    return d-degree(p)<=1 and degree(pgcd(p,derivative(p)))==0


def _gate_replay(f,g):
    t1,t3,t5=(transvectant(f,g,k) for k in (1,3,5))
    return {"T3_zero":_zero(t3),"T5_zero":_zero(t5),"T1_nonzero":not _zero(t1),
            "correction_free":_zero(t3) and _zero(t5),
            "active":_zero(t3) and _zero(t5) and not _zero(t1),
            "T1":t1.record(),"T3":t3.record(),"T5":t5.record()}


def archived_r5_pair():
    """Return the recovered exact rational pair as polynomial objects (f,g)."""
    x,y=Poly.variable(0),Poly.variable(1)
    f=(2*x**6-6*x**5*y+5*x**4*y*y+5*x*x*y**4-6*x*y**5+2*y**6)*Q(1,2)
    g=-x*y*(x-y)*(x*x-x*y+y*y)
    return f,g


def _multiply_coefficients(a,b):
    out=[0]*(len(a)+len(b)-1)
    for i,c in enumerate(a):
        for j,d in enumerate(b):out[i+j]+=c*d
    return out


def archived_r5(parameter_b=None):
    """Replay the pair and reconstruct the archived eliminant's exact factors.

    The polynomial is the recorded b-eliminant. Multiplication verifies the
    returned coefficient vector from those factors; it is not a fresh proof
    that the vector generates a maximal-minor elimination ideal.
    """
    f,g=archived_r5_pair()
    factors=[{"expression":"b","coefficients_ascending":[0,1],"multiplicity":6,"kind":"collision boundary"},
             {"expression":"b-1","coefficients_ascending":[-1,1],"multiplicity":6,"kind":"collision boundary"},
             {"expression":"b^2-3b+3","coefficients_ascending":[3,-3,1],"multiplicity":1,"kind":"squarefree candidate"},
             {"expression":"b^2-b+1","coefficients_ascending":[1,-1,1],"multiplicity":1,"kind":"squarefree candidate"},
             {"expression":"b^2+b+1","coefficients_ascending":[1,1,1],"multiplicity":1,"kind":"squarefree candidate"},
             {"expression":"3b^2-3b+1","coefficients_ascending":[1,-3,3],"multiplicity":1,"kind":"squarefree candidate"}]
    polynomial=[1]
    for factor in factors:
        for _ in range(factor["multiplicity"]):polynomial=_multiply_coefficients(polynomial,factor["coefficients_ascending"])
    eliminant={"variable":"b","expression":"b^6(b-1)^6(b^2-3b+3)(b^2-b+1)(b^2+b+1)(3b^2-3b+1)",
               "coefficients_ascending":polynomial,"degree":len(polynomial)-1,"factors":factors,
               "factor_expansion_replayed":True,"maximal_minor_elimination_regenerated":False,
               "scope":"Archived factorization reconstructed exactly; the a-coordinate equations and orbit-classification certificates are not regenerated."}
    if parameter_b is not None:
        if type(parameter_b) is bool or not isinstance(parameter_b,(int,str,Q)):
            raise ValueError("parameter_b must be an exact rational")
        try:b=Q(parameter_b)
        except (ValueError,ZeroDivisionError) as error:raise ValueError("invalid rational parameter_b") from error
        value=sum(Q(c)*b**i for i,c in enumerate(polynomial))
        product=Q(1)
        for factor in factors:
            product*=sum(Q(c)*b**i for i,c in enumerate(factor["coefficients_ascending"]))**factor["multiplicity"]
        eliminant["evaluation"]={"b":str(b),"value":str(value),"factor_product_replayed":value==product,
                                 "collision_boundary":b in (0,1)}
    return {"operation":"r5","form":f.record(),"partner":g.record(),
            "form_squarefree":_squarefree(f),"partner_squarefree":_squarefree(g),
            "gates":_gate_replay(f,g),"dimensions":partner_dimensions(f,5),"eliminant":eliminant,
            "orbit_status":"The archived one-orbit assertion used numerical Mobius matching; no exact orbit certificate is asserted here.",
            "scope":"One recovered rational sextic/quintic pair with exact gate and active-dimension replay."}


def cubic_partner(form=None):
    """Test the universal determinant criterion and construct its full kernel."""
    f=_form(form);identity=cubic_gate_identity(f)
    basis=[]
    for vector in nullspace(gate_matrix(f,3,3),4):
        g=Poly({(3-i,i):c for i,c in enumerate(vector) if c})
        basis.append({"partner":g.record(),"gates":_gate_replay(f,g)})
    return {"operation":"cubic","form":f.record(),"determinant":str(identity["det_L3"]),
            "A2_minus_B_over_6":str(identity["A2_minus_B_over_6"]),"identity_replayed":identity["identity"],
            "partner_exists":bool(basis),"kernel_basis":basis,"dimensions":partner_dimensions(f,3),
            "criterion":"A cubic correction-free partner exists exactly when B=6A^2.",
            "scope":"Exact supplied-form replay of the universal determinant identity; no full grid evaluated by this call."}


def quartic_partner(form=None):
    """Construct the universal covariant i=(f,f)_4 and replay its activity."""
    f=_form(form);i=transvectant(f,f,4);check=quartic_covariant_partner(f)
    return {"operation":"quartic","form":f.record(),"partner":i.record(),
            "partner_nonzero":not _zero(i),"universal_gates_replayed":check["gates_vanish"],
            "gates":_gate_replay(f,i),"dimensions":partner_dimensions(f,4),
            "scope":"The universal quartic covariant is correction-free; a nonzero first transvectant is separately required for activity."}


def degree12_partner_report(form=None):
    """Construct G and replay the universal gate identities at a supplied form."""
    if form is None:
        from .parametric import sextic_family
        form=sextic_family(Q(32,25),Q(-9,5))
    f=_form(form);a,b,_,_=clebsch(f);s=a*a-Q(25,96)*b;g=degree12_partner(f)
    return {"operation":"degree12","form":f.record(),"form_squarefree":_squarefree(f),
            "partner":g.record(),"partner_nonzero":not _zero(g),"s_A2_minus_25B_over_96":str(s),
            "on_invariant_hypersurface":s==0,"gate_identities_replayed":degree12_gate_identities(f),
            "gates":_gate_replay(f,g),"dimensions":partner_dimensions(f,12),
            "sufficient_condition":"If A^2=25B/96 and G is nonzero, G is a degree-12 correction-free partner.",
            "converse_status":"open","full_grid_evaluated":False,
            "scope":"Exact instance replay; the converse that every degree-12 partner forces A^2=25B/96 is not asserted."}


def sextic_partners(form=None):
    """Combined exact cubic/quartic/degree-12 analysis of one sextic."""
    f=_form(form)
    return {"operation":"sextic","form":f.record(),"squarefree":_squarefree(f),
            "clebsch_invariants":[str(v) for v in clebsch(f)],
            "cubic":cubic_partner(f),"quartic":quartic_partner(f),"degree12":degree12_partner_report(f)}


def evaluate(operation,params=None):
    operations={"r5":archived_r5,"cubic":cubic_partner,"quartic":quartic_partner,
                "degree12":degree12_partner_report,"sextic":sextic_partners,"incidence":incidence_report}
    if operation not in operations:raise ValueError("unknown recovered-partner operation: "+str(operation))
    if params is None:params={}
    if not isinstance(params,dict):raise ValueError("params must be an object")
    return operations[operation](**params)


def receipt():
    """Small exact examples; universal full-slice grids are intentionally omitted."""
    x,y=Poly.variable(0),Poly.variable(1)
    return {"schema":"perfectjet/recovered-partners/1","r5":archived_r5(),
            "cubic":cubic_partner(x**6+20*x**3*y**3+y**6),
            "quartic":quartic_partner(),"degree12":degree12_partner_report(),
            "full_grid_evaluated":False,"converse_status":"degree-12 converse remains open"}


def incidence_report(form=None, degree=5):
    """Exact supplied-form kernel; global classification evidence is reported separately."""
    if type(degree) is not int or not 3 <= degree <= 20:
        raise ValueError("degree must be an integer in 3..20")
    from .incidence import correction_matrix, THEOREMS, c3_degree8_certificate
    f = _form(form, archived_r5_pair()[0])
    basis = nullspace(correction_matrix(f, degree), degree+1)
    partners = [Poly({(degree-i,i): c for i,c in enumerate(v) if c}) for v in basis]
    return {"operation":"incidence", "degree":degree, "form":f.record(),
            "kernel_dimension":len(basis), "dimensions":partner_dimensions(f,degree),
            "kernel_basis":[{"partner":g.record(),"gates":_gate_replay(f,g)} for g in partners],
            "c3_degree8_identity":c3_degree8_certificate(), "classification":THEOREMS,
            "external_solvers_rerun":False,
            "classification_scope":"Nonzero binary sextics over the algebraic closure of Q, GL2 equivalence; exact supplied-form rational kernel replay is distinct from global classification.",
            "external_evidence":"Archived msolve over Q and Singular finite-field receipts: results/partner_incidence_solver_receipts.json. These are not kernel-checked certificates and were not rerun by this call.",
            "open_obligations":["Degrees >=21", "Independent rational or proof-carrying replay of optional solver classifications", "Line genericity is not certified by random probes"],
            "scope":"Instance gates and activity are exact; kernel existence does not by itself imply activity."}
