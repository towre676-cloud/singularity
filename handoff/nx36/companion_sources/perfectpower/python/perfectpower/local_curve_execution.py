"""Exact Laurent charts and Frobenius logarithmic jets in Fuchsian frames."""
from fractions import Fraction as Q
from . import polyalg as P, exact_linear as E
from .rational_functions import RationalFunction as RF, AlgebraBudget, determinant
from .observable_machine import _q
from .curve_families import encode_matrix
from .divisor_square import WorkLimit


def s_power(k,budget=None):return RF([0]*k+[1],budget=budget) if k>=0 else RF([1],[0]*(-k)+[1],budget=budget)

def at_infinity(a):
    if not a:return a
    return RF(list(reversed(a.n)),list(reversed(a.d)),budget=a.budget)*s_power(len(a.d)-len(a.n),a.budget)


def local_function(a,parameter):
    if parameter=='infinity':return at_infinity(a)
    t=_q(parameter);return RF(P.compose_linear(a.n,t,1),P.compose_linear(a.d,t,1),budget=a.budget)


def valuation(a):
    if not a:return None
    return next(i for i,c in enumerate(a.n) if c)-next(i for i,c in enumerate(a.d) if c)


def laurent(a,last):
    if not a:return {}
    n0=next(i for i,c in enumerate(a.n) if c);d0=next(i for i,c in enumerate(a.d) if c);v=n0-d0
    n,d=a.n[n0:],a.d[d0:];out=[]
    for k in range(max(0,last-v+1)):
        out.append(((n[k] if k<len(n) else 0)-sum(d[j]*out[k-j] for j in range(1,min(k,len(d)-1)+1)))/d[0])
    return {v+k:c for k,c in enumerate(out) if c}


def diagonal_fuchsian_frame(matrix):
    """Difference constraints find an integral diagonal shear if one exists."""
    n=len(matrix);weights=[0]*n;edges=[]
    for i,row in enumerate(matrix):
        for j,a in enumerate(row):
            v=valuation(a)
            if v is None:continue
            if i==j and v<-1:return None
            if i!=j:edges.append((i,j,v+1))
    for step in range(n):
        changed=False
        for i,j,c in edges:
            if weights[j]>weights[i]+c:weights[j]=weights[i]+c;changed=True
        if not changed:break
    else:
        if changed:return None
    minimum=min(weights);weights=[w-minimum for w in weights]
    if max(weights)>32:raise WorkLimit('local diagonal shear exceeds exponent budget')
    zero=matrix[0][0].coerce(0)
    transformed=[[a*s_power(weights[i]-weights[j],a.budget)+(weights[i]*s_power(-1,a.budget) if i==j else zero) for j,a in enumerate(row)] for i,row in enumerate(matrix)]
    if any(valuation(a) is not None and valuation(a)<-1 for row in transformed for a in row):raise AssertionError('Fuchsian shear replay failed')
    return weights,transformed


def local_analysis(family,parameter=0,order=8):
    if type(order) is not int or not 1<=order<=24:raise ValueError('local jet order one through 24 required')
    budget=AlgebraBudget(**family.limits)
    matrix=[[local_function(RF.parse(a,budget),parameter) for a in row] for row in family.connection]
    if parameter=='infinity':matrix=[[-a*s_power(-2,budget) for a in row] for row in matrix]
    poles=[[valuation(a) for a in row] for row in matrix];frame=diagonal_fuchsian_frame(matrix)
    local_f=[local_function(RF.parse(a,budget),parameter) for a in family.f]
    v=min(valuation(a) for a in local_f if a)
    leading=P.poly(laurent(a,v).get(v,0) for a in local_f)
    scale,factors=P.squarefree_decomposition(leading)
    binary_degree=len(family.f) if len(family.f)%2==0 else len(family.f)-1
    infinity_multiplicity=binary_degree-P.degree(leading)
    disc=local_function(RF(family.discriminant,budget=budget),parameter)
    answer=dict(schema='pp-local-curve-chart/1',parameter=str(parameter),coordinate='s=1/t' if parameter=='infinity' else 's=t-parameter',
        original_connection=encode_matrix(matrix),entry_valuations=poles,
        discriminant_valuation=valuation(disc),primitive_coefficient_valuation=v,
        primitive_binary_discriminant_valuation=valuation(disc)-v*(2*binary_degree-2),
        primitive_special_fibre=list(map(str,leading)),finite_root_multiplicities={str(k):list(map(str,p)) for k,p in factors.items()},
        branch_multiplicity_at_x_infinity=infinity_multiplicity,
        interpretation='primitive binary-form coefficient limit in this x chart; may need blowups or further base changes for stable reduction',
        fuchsian_in_diagonal_frame=frame is not None,execution_verified=False,
        scope='exact local connection and branch multiplicities at a rational finite parameter or parameter infinity; arbitrary stable reduction and non-diagonal Fuchsian gauges are not inferred')
    if frame is None:return answer
    weights,a=frame;series=[[laurent(v,order-1) for v in row] for row in a]
    coefficient=lambda k:[[v.get(k,Q(0)) for v in row] for row in series]
    residue=coefficient(-1);char=determinant([[RF([-residue[i][j],int(i==j)],budget=budget) for j in range(len(a))] for i in range(len(a))])
    answer.update(shear_weights=weights,frame_identity='Y_new=diag(s^weights) Y; A_new=G_prime G_inverse+G A G_inverse',
        transformed_connection=encode_matrix(a),residue=[[str(v) for v in row] for row in residue],
        residue_characteristic_polynomial=list(map(str,char.n)),
        analytic_connection_coefficients=[[[str(v) for v in row] for row in coefficient(k)] for k in range(order)],
        jet_order=order,local_log_monodromy_scope='exp(2 pi i residue) only in a compatible nonresonant/normalized local fundamental frame; no integral cycle marking supplied')
    return answer


def frobenius_jet(family,parameter=0,order=8,exponent=0,seed=None,log_degree=None):
    packet=local_analysis(family,parameter,order)
    if not packet['fuchsian_in_diagonal_frame']:raise ValueError('no supported diagonal Fuchsian frame; inspect local_analysis')
    n=family.dimension;rho=_q(exponent);seed=[_q(v) for v in (seed if seed is not None else [1]+[0]*(n-1))]
    if len(seed)!=n:raise ValueError('one seed coefficient per state coordinate required')
    degree=n-1 if log_degree is None else log_degree
    if type(degree) is not int or not 0<=degree<=6:raise ValueError('log degree zero through six required')
    residue=[[Q(v) for v in row] for row in packet['residue']]
    analytic=[[[Q(v) for v in row] for row in a] for a in packet['analytic_connection_coefficients']]
    nil=[[residue[i][j]-rho*int(i==j) for j in range(n)] for i in range(n)]
    initial=[seed]
    for _ in range(degree):initial.append(list(E.apply(nil,initial[-1])))
    if any(E.apply(nil,initial[-1])):raise ValueError('seed does not lie in the requested generalized residue eigenspace within the log bound')
    jets=[initial];resonance=None
    for k in range(1,order+1):
        matrix=[[Q(k+rho)*int(i==j)-residue[i][j] for j in range(n)] for i in range(n)]
        if E.rank(matrix)<n:
            resonance=k;break
        current=[[Q(0)]*n for _ in range(degree+1)]
        for ell in range(degree,-1,-1):
            target=[sum(sum(analytic[j][i][c]*jets[k-1-j][ell][c] for c in range(n)) for j in range(k))-(current[ell+1][i] if ell<degree else 0) for i in range(n)]
            current[ell]=list(E.solve(matrix,target))
        jets.append(current)
    # Replay the recurrence, including the logarithmic derivative contribution.
    for k,row in enumerate(jets):
        for ell,v in enumerate(row):
            left=[(k+rho)*v[i]+(row[ell+1][i] if ell<degree else 0)-sum(residue[i][c]*v[c] for c in range(n)) for i in range(n)]
            right=[sum(sum(analytic[j][i][c]*jets[k-1-j][ell][c] for c in range(n)) for j in range(k)) for i in range(n)]
            if left!=right:raise AssertionError('Frobenius coefficient replay failed')
    return dict(schema='pp-frobenius-log-jet/1',local_chart=packet,exponent=str(rho),
        coefficients=[[[str(v) for v in vector] for vector in row] for row in jets],
        representation='Y_new=s^exponent sum_n s^n sum_l coefficients[n][l] log(s)^l/l!',
        requested_order=order,completed_order=len(jets)-1,recurrence_checked=True,
        resonance_at_order=resonance,complete_requested_jet=resonance is None,
        numerical_error_certified=False,execution_verified=False,
        scope='exact finite logarithmic Frobenius jet in the recorded frame; unresolved positive resonance is reported, no analytic error enclosure or integral monodromy inferred')
