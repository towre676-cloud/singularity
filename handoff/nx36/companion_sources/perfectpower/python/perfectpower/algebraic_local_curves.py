"""Algebraic closed-point Laurent charts and resonance-complete formal jets.

An algebraic point is represented by a squarefree Q polynomial q(alpha)=0.
Coefficients are computed in Q(s)[alpha]/q with t=alpha+s^e (or t=s^-e).
Components split on actual nonunit witnesses. No complex root ordering is used.
"""
from fractions import Fraction as Q
from . import field_polynomials as F, polyalg as P
from .rational_functions import RationalFunction as RF, AlgebraBudget, solve_many
from .differential_extensions import EtaleAlgebra, EtaleElement, ExtensionNonUnit, encode, matrix_encode
from .local_curve_execution import s_power, valuation as rf_valuation, laurent as rf_laurent
from .observable_machine import _q
from .divisor_square import WorkLimit


def valuation(a):
    if not a:return None
    if isinstance(a,RF):return rf_valuation(a)
    return min(valuation(c) for c in a.coefficients if c)


def laurent(a,last):
    if isinstance(a,RF):return {k:RF([v],budget=a.budget) for k,v in rf_laurent(a,last).items()}
    out={}
    for i,c in enumerate(a.coefficients):
        for k,v in laurent(c,last).items():
            term=a.algebra.element([0]*i+[v]);out[k]=out.get(k,a.coerce(0))+term
    return {k:v for k,v in out.items() if v}


def compose(a,coordinate):
    n=F.evaluate([coordinate.coerce(c) for c in a.n],coordinate)
    d=F.evaluate([coordinate.coerce(c) for c in a.d],coordinate)
    return n/d


def fuchsian_frame(matrix):
    n=len(matrix);weights=[0]*n;edges=[]
    for i,row in enumerate(matrix):
        for j,a in enumerate(row):
            v=valuation(a)
            if v is None:continue
            if i==j and v<-1:return None
            if i!=j:edges.append((i,j,v+1))
    for _ in range(n):
        changed=False
        for i,j,c in edges:
            if weights[j]>weights[i]+c:weights[j]=weights[i]+c;changed=True
        if not changed:break
    else:
        if changed:return None
    weights=[w-min(weights) for w in weights]
    if max(weights)>64:raise WorkLimit('local shear exponent exceeds 64')
    zero=matrix[0][0].coerce(0)
    transformed=[[a*s_power(weights[i]-weights[j],a.budget)+(weights[i]*s_power(-1,a.budget) if i==j else zero) for j,a in enumerate(row)] for i,row in enumerate(matrix)]
    if any(valuation(a) is not None and valuation(a)<-1 for row in transformed for a in row):raise AssertionError('algebraic local shear failed')
    return weights,transformed


def characteristic(matrix):
    n=len(matrix);z=matrix[0][0].coerce(0)
    b=[[z.coerce(int(i==j)) for j in range(n)] for i in range(n)];out=[z.coerce(1)]
    for k in range(1,n+1):
        ab=F.matrix_product(matrix,b);c=-sum((ab[i][i] for i in range(n)),z)/k;out.append(c)
        b=[[ab[i][j]+(c if i==j else z) for j in range(n)] for i in range(n)]
    return list(reversed(out))


def squarefree_layers(f):
    f=F.trim(f);f=[v/f[-1] for v in f];z=f[0].coerce(0)
    g=F.extended_gcd(f,F.derivative(f))[0];w=F.divide(f,g)[0];layers=[];i=1
    while len(w)>1:
        y=F.extended_gcd(w,g)[0];part=F.divide(w,y)[0]
        if len(part)>1:layers.append((i,part))
        w=y;g=F.divide(g,y)[0];i+=1
    return layers


def _chart(family,parameter,order,ramification,budget):
    if type(order) is not int or not 1<=order<=32:raise ValueError('local order one through 32 required')
    if type(ramification) is not int or not 1<=ramification<=32:raise ValueError('ramification one through 32 required')
    algebra=None
    if isinstance(parameter,dict):
        if set(parameter)-{'modulus','element'} or 'modulus' not in parameter:raise ValueError('algebraic parameter needs a squarefree rational modulus and optional element')
        modulus=[_q(v) for v in parameter['modulus']]
        algebra=EtaleAlgebra(modulus,budget=budget);alpha=algebra.element(parameter.get('element',[0,1]))
        coordinate=alpha+algebra.zero.coerce(s_power(ramification,budget));jacobian=ramification*s_power(ramification-1,budget)
        location=dict(modulus=list(map(str,P.monic(modulus))),element=alpha.packet())
    elif parameter=='infinity':
        coordinate=s_power(-ramification,budget);jacobian=-ramification*s_power(-ramification-1,budget);location='infinity'
    else:
        coordinate=RF([_q(parameter)],budget=budget)+s_power(ramification,budget);jacobian=ramification*s_power(ramification-1,budget);location=str(_q(parameter))
    matrix=[[compose(RF.parse(a,budget),coordinate)*jacobian for a in row] for row in family.connection]
    local_f=[compose(RF.parse(a,budget),coordinate) for a in family.f];zero=matrix[0][0].coerce(0)
    primitive_v=min(valuation(a) for a in local_f if a)
    fibre=F.trim([laurent(a,primitive_v).get(primitive_v,zero) for a in local_f])
    layers=squarefree_layers(fibre);disc=compose(RF(family.discriminant,budget=budget),coordinate)
    if algebra:
        # Split components whose first nonzero discriminant coefficient
        # vanishes on only some locations: orders must be uniform per packet.
        laurent(disc,valuation(disc))[valuation(disc)].inverse()
    binary_degree=len(family.f);frame=fuchsian_frame(matrix)
    packet=dict(schema='pp-algebraic-local-curve/1',parameter=location,ramification=ramification,
        coordinate='t=alpha+s^e' if parameter!='infinity' else 't=s^-e',
        local_polynomial=[encode(a) for a in local_f],original_connection=matrix_encode(matrix),
        entry_valuations=[[valuation(a) for a in row] for row in matrix],
        discriminant_valuation=valuation(disc),primitive_coefficient_valuation=primitive_v,
        primitive_binary_discriminant_valuation=valuation(disc)-primitive_v*(2*binary_degree-2),
        primitive_special_fibre=[encode(v) for v in fibre],
        finite_root_multiplicities=[dict(multiplicity=i,polynomial=[encode(v) for v in p]) for i,p in layers],
        branch_multiplicity_at_x_infinity=binary_degree-len(fibre)+1,
        fuchsian_in_diagonal_frame=frame is not None,jet_order=order,
        scope='exact Laurent chart over the recorded finite etale coefficient algebra; coefficient limits are not automatically stable models; no numerical root selection or integral marking')
    analytic=[];residue=None
    if frame:
        weights,a=frame;series=[[laurent(v,order-1) for v in row] for row in a]
        coefficient=lambda k:[[v.get(k,zero) for v in row] for row in series]
        residue=coefficient(-1);analytic=[coefficient(k) for k in range(order)]
        packet.update(shear_weights=weights,transformed_connection=matrix_encode(a),residue=matrix_encode(residue),
            residue_characteristic_polynomial=[encode(v) for v in characteristic(residue)],
            analytic_connection_coefficients=[matrix_encode(v) for v in analytic],
            frame_identity='Y_new=diag(s^weights)Y; A_new=G_prime G_inverse+G A G_inverse')
    return packet,algebra,residue,analytic


def local_chart(family,parameter=0,order=8,ramification=1):
    budget=AlgebraBudget(**family.limits)
    return _chart(family,parameter,order,ramification,budget)[0]


def algebraic_degenerations(family,order=6,ramification=1):
    """All finite discriminant locations, including repeated discriminant roots."""
    budget=AlgebraBudget(**family.limits);d=P.monic(family.discriminant)
    support=P.exact_div(d,P.gcd_poly(d,P.derivative(d)))
    pending=[support] if len(support)>1 else [];charts=[];splits=[]
    while pending:
        q=pending.pop(0)
        try:charts.append(_chart(family,dict(modulus=list(q)),order,ramification,budget)[0])
        except ExtensionNonUnit as error:
            # A constant defining modulus makes its nonunit factors constant.
            factor=P.poly(v.evaluate(0) for v in error.factor)
            if any(v!=RF([c]) for v,c in zip(error.factor,factor)):raise AssertionError('nonconstant factor in a constant local algebra')
            factor=P.gcd_poly(q,factor)
            if not 0<P.degree(factor)<P.degree(q):raise AssertionError('invalid algebraic-point split')
            pending[0:0]=[factor,P.exact_div(q,factor)];splits.append(list(map(str,factor)))
    if sum(len(c['parameter']['modulus'])-1 for c in charts)!=P.degree(support):raise AssertionError('closed-point chart coverage failed')
    return dict(schema='pp-algebraic-degenerations/1',discriminant_support=list(map(str,support)),
        covered_roots=P.degree(support),charts=charts,split_witnesses=splits,
        scope='all finite algebraic discriminant locations; chart components split when exact divisions require it; general stable reduction remains separate')


def _constant(algebra,value):
    if algebra is None:return RF([_q(value)])
    if isinstance(value,list):return algebra.element([_q(v) for v in value])
    return algebra.element([_q(value)])


def resonant_frobenius(family,parameter=0,order=8,ramification=1,exponent=0,seed=None,log_degree=None):
    """Block logarithmic recurrence, including singular positive resonances.

    Coefficients use log(s)^l/l!. Free recurrence coordinates are set to zero;
    increased log bounds are tried, never division by a singular matrix.
    """
    budget=AlgebraBudget(**family.limits);chart,algebra,r,analytic=_chart(family,parameter,order,ramification,budget)
    if r is None:raise ValueError('no supported diagonal Fuchsian frame')
    n=family.dimension;rho=_constant(algebra,exponent);z=r[0][0].coerce(0)
    raw=seed if seed is not None else [1]+[0]*(n-1)
    if not isinstance(raw,list) or len(raw)!=n:raise ValueError('one seed per period coordinate required')
    seed=[_constant(algebra,v) for v in raw]
    if log_degree is not None and (type(log_degree) is not int or not 0<=log_degree<=12):raise ValueError('log bound zero through twelve required')
    bounds=[log_degree] if log_degree is not None else range(n-1,min(12,2*n)+1)
    attempted=[]
    for degree in bounds:
        nil=[[r[i][j]-rho*int(i==j) for j in range(n)] for i in range(n)]
        initial=[seed]
        for _ in range(degree):initial.append([sum((nil[i][j]*initial[-1][j] for j in range(n)),z) for i in range(n)])
        if any(sum((nil[i][j]*initial[-1][j] for j in range(n)),z) for i in range(n)):
            attempted.append(dict(log_degree=degree,reason='seed needs a larger generalized eigenspace log bound'));continue
        jets=[initial];resonances=[];failure=None
        for k in range(1,order+1):
            diagonal=[[(rho+k)*int(i==j)-r[i][j] for j in range(n)] for i in range(n)]
            if F.matrix_rank(diagonal)<n:resonances.append(k)
            size=(degree+1)*n;block=[[z]*size for _ in range(size)];target=[]
            for ell in range(degree+1):
                for i in range(n):
                    for j in range(n):block[ell*n+i][ell*n+j]=diagonal[i][j]
                    if ell<degree:block[ell*n+i][(ell+1)*n+i]=z.coerce(1)
                    target.append([sum((analytic[j][i][c]*jets[k-1-j][ell][c] for j in range(k) for c in range(n)),z)])
            solution=solve_many(block,target)
            if solution is None:failure=k;break
            jets.append([[solution[ell*n+i][0] for i in range(n)] for ell in range(degree+1)])
        if failure is not None:
            attempted.append(dict(log_degree=degree,reason='inconsistent block recurrence within log bound',order=failure));continue
        for k,row in enumerate(jets):
            for ell,v in enumerate(row):
                left=[(rho+k)*v[i]+(row[ell+1][i] if ell<degree else z)-sum((r[i][c]*v[c] for c in range(n)),z) for i in range(n)]
                right=[sum((analytic[j][i][c]*jets[k-1-j][ell][c] for j in range(k) for c in range(n)),z) for i in range(n)]
                if left!=right:raise AssertionError('resonant Frobenius replay failed')
        return dict(schema='pp-resonant-frobenius/1',local_chart=chart,exponent=encode(rho),
            coefficients=[matrix_encode(v) for v in jets],completed_order=order,requested_order=order,
            complete_requested_jet=True,positive_resonances_resolved=resonances,log_degree=degree,
            recurrence_checked=True,attempted_log_bounds=attempted,
            representation='Y_new=s^rho sum_n s^n sum_l coefficients[n][l] log(s)^l/l!',
            normalization='free coordinates in each exact block recurrence are set to zero',
            scope='finite formal jet including consistent resonances within the recorded log bound; no convergence enclosure or integral monodromy matrix')
    return dict(schema='pp-resonant-frobenius/1',local_chart=chart,complete_requested_jet=False,
        requested_order=order,attempted_log_bounds=attempted,reason='no solution within the tested logarithmic bounds')


def node_branches(family,parameter,order=8):
    """Exact two-root Hensel expansions at a transverse ordinary node.

    The coefficient extension kappa^2=-2 P_t/P_xx is explicit. After t=alpha+r^2
    both branches are ordinary power series, exchanged by kappa -> -kappa.
    """
    if type(order) is not int or not 1<=order<=16:raise ValueError('node branch order one through 16 required')
    if not isinstance(parameter,dict):raise ValueError('node branch parameter must be an algebraic point specification')
    budget=AlgebraBudget(**family.limits);chart,a,_,_=_chart(family,parameter,order+1,1,budget)
    alpha=a.element(parameter.get('element',[0,1]));zero=a.zero
    f=[compose(RF.parse(v,budget),alpha) for v in family.f]
    common,_,_=F.extended_gcd(f,F.derivative(f))
    if len(common)!=2:raise ValueError('one common double root required for a nodal branch chart')
    root=-common[0]/common[1]
    curvature=F.evaluate(F.derivative(F.derivative(f)),root)
    transverse=F.evaluate([compose(RF.parse(v,budget).derivative(),alpha) for v in family.f],root)
    curvature.inverse();transverse.inverse()
    extension=EtaleAlgebra([2*transverse/curvature,zero,a.one],a.zero,budget);kappa=extension.generator
    r=extension.zero.coerce(a.zero.coerce(s_power(1,budget)))
    alpha2=extension.zero.coerce(alpha);root2=extension.zero.coerce(root)
    local_f=[compose(RF.parse(v,budget),alpha2+r*r) for v in family.f]
    coefficients=[root2,kappa];series=root2+kappa*r
    for k in range(2,order+1):
        residual=F.evaluate(local_f,series)
        coefficient=laurent(residual,k+1).get(k+1,extension.zero)
        b=-coefficient/(kappa*extension.zero.coerce(curvature))
        coefficients.append(b);series=series+b*r**k
    residual=F.evaluate(local_f,series);values=laurent(residual,order+1)
    if values:raise AssertionError('nodal Hensel expansion replay failed')
    conjugate=-kappa
    return dict(schema='pp-node-root-branches/1',parameter=chart['parameter'],
        collision_x=root.packet(),P_xx=curvature.packet(),P_t=transverse.packet(),
        coefficient_extension_modulus=[encode(v) for v in extension.modulus],
        parameter_ramification=2,branch_plus=[v.packet() for v in coefficients],
        branch_minus=[v.at(conjugate).packet() for v in coefficients],
        residual_vanishes_through_order=order+1,identity_checked=True,
        local_connection=chart,representation='t=alpha+r^2; x=sum_j branch[j] r^j',
        scope='the two roots near the declared transverse double root; exact truncated series over recorded coefficient extensions, no convergence enclosure or integral braid matrix')
