"""Exact hyperelliptic family connections and observable differential operators.

Monic odd x degrees 3/5/7, polynomial parameter coefficients over Q. Numerical
marked-period initialization/continuation is a separate optional backend.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import reduce
from math import gcd, lcm
from . import polyalg as P
from .core import mul, integer_power_root
from .observable_machine import _q
from .rational_functions import RationalFunction as RF, AlgebraBudget, solve_many, determinant
from .divisor_square import WorkLimit


def xmul(a, b):
    zero = a[0].coerce(0); out = [zero for _ in range(len(a)+len(b)-1)]
    for i, c in enumerate(a):
        for j, d in enumerate(b): out[i+j] = out[i+j] + c*d
    return out


def xadd(a, b):
    zero = a[0].coerce(0)
    return [(a[i] if i < len(a) else zero)+(b[i] if i < len(b) else zero) for i in range(max(len(a), len(b)))]


def xderivative(a): return [i*c for i, c in enumerate(a) if i] or [a[0].coerce(0)]
def pad(a, n): return a+[a[0].coerce(0)]*(n-len(a))
def encode_matrix(a): return [[v.packet() for v in row] for row in a]


def primitive_operator(coefficients, budget):
    denominator = P.ONE
    for a in coefficients:
        denominator = mul(denominator, P.exact_div(a.d, P.gcd_poly(denominator, a.d)))
        budget.check(denominator)
    polynomials = [mul(a.n, P.exact_div(denominator, a.d)) for a in coefficients]
    budget.check(*polynomials)
    common = reduce(P.gcd_poly, polynomials)
    polynomials = [P.exact_div(p, common) for p in polynomials]
    scale = lcm(*(c.denominator for p in polynomials for c in p))
    integers = [[int(c*scale) for c in p] for p in polynomials]
    content = reduce(gcd, (abs(c) for p in integers for c in p))
    if integers[-1][-1] < 0: content = -content
    integers = [[c//content for c in p] for p in integers]
    budget.check(*(P.poly(p) for p in integers))
    return integers


class CurveFamily:
    def __init__(self, specification, *, _parameter_degree_limit=8):
        if not isinstance(specification, dict) or not {'coefficients'} <= set(specification) or set(specification)-{'coefficients','work_limit','degree_limit','bit_limit'}:
            raise ValueError('family coefficient arrays and optional algebra budgets required')
        self.specification = deepcopy(specification)
        self.limits = {k: specification[k] for k in ('work_limit','degree_limit','bit_limit') if k in specification}
        budget = AlgebraBudget(**self.limits)
        coefficients = specification['coefficients']
        if not isinstance(coefficients, (list, tuple)) or len(coefficients) not in (4,6,8):
            raise ValueError('monic odd x degree 3, 5 or 7 required')
        self.f = [RF.parse(c, budget) for c in coefficients]
        if any(a.d != P.ONE or P.degree(a.n) > _parameter_degree_limit for a in self.f) or self.f[-1] != 1:
            raise ValueError(f'polynomial parameter degree at most {_parameter_degree_limit} and monic x polynomial required')
        m = len(self.f)-1; self.dimension = m-1; self.genus = (m-1)//2
        df = xderivative(self.f); zero = RF.parse(0, budget)
        # Sylvester resultant det, both input polynomials use descending x order.
        sylvester = []
        for k in range(m-1): sylvester.append([zero]*k+list(reversed(self.f))+[zero]*(m-2-k))
        for k in range(m): sylvester.append([zero]*k+list(reversed(df))+[zero]*(m-1-k))
        disc = (-1)**(m*(m-1)//2)*determinant(sylvester)
        if not disc: raise ValueError('family is generically singular')
        if disc.d != P.ONE: raise AssertionError('monic polynomial discriminant is not polynomial')
        self.discriminant = disc.n
        # -x^i P_t/2 = B_i P + R_i' P - R_i P_x/2.
        size = 2*m-1; columns = []
        for j in range(m-1): columns.append(pad([zero]*j+self.f, size))
        for k in range(m):
            first = [k*c for c in self.f]
            first = [zero]*(k-1)+first if k else [zero]
            second = [zero]*k+[-c/2 for c in df]
            columns.append(pad(xadd(first, second), size))
        matrix = list(map(list, zip(*columns)))
        dt = [a.derivative() for a in self.f]
        targets = [pad([zero]*i+[-c/2 for c in dt], size) for i in range(m-1)]
        solution = solve_many(matrix, list(map(list, zip(*targets))))
        if solution is None: raise AssertionError('smooth family reduction failed')
        self.connection = [list(row) for row in zip(*solution[:m-1])]
        self.reductions = [list(row) for row in zip(*solution[m-1:])]
        for i, (a, r) in enumerate(zip(self.connection, self.reductions)):
            replay = xadd(xmul(a, self.f), xadd(xmul(xderivative(r), self.f), [-c/2 for c in xmul(r, df)]))
            if pad(replay, size) != targets[i]: raise AssertionError('differential reduction identity failed')
        self.packet = dict(schema='pp-curve-family/1',equation='y^2=P(x,t)',genus=self.genus,state_dimension=self.dimension,
            coefficients=[list(map(str, a.n)) for a in self.f],discriminant=list(map(str, self.discriminant)),
            basis=[dict(x_power=i,expression=f'x^{i} dx/y',kind='holomorphic' if i<self.genus else 'second_kind') for i in range(m-1)],
            connection=encode_matrix(self.connection),exact_derivative_numerators=encode_matrix(self.reductions),
            reduction_identity='-x^i P_t/2 = (sum_j A_ij x^j) P + R_i_prime P - R_i P_x/2',
            reduction_identities_checked=m-1,algebra_work=budget.work,
            algebraic_function_operator=dict(derivative_coefficient=[a.packet() for a in [2*c for c in self.f]],
                constant_coefficient=[(-a).packet() for a in df],variable='x',
                parameter_derivative_constant_coefficient=[(-a).packet() for a in dt],
                relation_retained='y^2=P; either first-order operator alone permits arbitrary constant multiples',local_domain='P(x,t) != 0'),
            complete=True,execution_verified=False,scope='exact rational-function Gauss-Manin reduction on smooth monic odd-degree hyperelliptic fibres; no new Lean theorem')

    def summary(self): return dict(genus=self.genus,state_dimension=self.dimension,discriminant=list(map(str,self.discriminant)),complete=True)
    def evidence(self): return deepcopy(self.packet)

    def deformation(self):
        from .curve_structure import deformation
        return deformation(self)

    def root_motion(self):
        from .curve_structure import root_motion
        return root_motion(self)

    def collisions(self):
        from .curve_structure import collisions
        return collisions(self)

    def projective_deformation(self):
        from .projective_deformation import projective_deformation
        return projective_deformation(self.specification)

    def local_analysis(self, parameter=0, order=8):
        from .local_curve_execution import local_analysis
        return local_analysis(self, parameter, order)

    def frobenius_jet(self, parameter=0, order=8, exponent=0, seed=None, log_degree=None):
        from .local_curve_execution import frobenius_jet
        return frobenius_jet(self, parameter, order, exponent, seed, log_degree)

    def de_rham_pairing(self):
        from .horizontal_projectors import de_rham_pairing
        return dict(pairing=encode_matrix(de_rham_pairing(self)),
                    construction='residue of a local primitive times a differential at infinity',
                    pairing_identity_checked=True, integral_cycle_marking=False)

    def horizontal_projectors(self, degree=0, denominator=None, candidate_limit=128):
        from .horizontal_projectors import search_horizontal_projectors
        return search_horizontal_projectors(self, degree, denominator, candidate_limit)

    def check_projector(self, matrix):
        from .horizontal_projectors import projector_check
        return projector_check(self, matrix)

    def algebraic_local_chart(self, parameter=0, order=8, ramification=1):
        from .algebraic_local_curves import local_chart
        return local_chart(self, parameter, order, ramification)

    def algebraic_degenerations(self, order=6, ramification=1):
        from .algebraic_local_curves import algebraic_degenerations
        return algebraic_degenerations(self, order, ramification)

    def resonant_frobenius(self, parameter=0, order=8, ramification=1, exponent=0, seed=None, log_degree=None):
        from .algebraic_local_curves import resonant_frobenius
        return resonant_frobenius(self, parameter, order, ramification, exponent, seed, log_degree)

    def node_branches(self, parameter, order=8):
        from .algebraic_local_curves import node_branches
        return node_branches(self, parameter, order)

    def ramified_scaling_chart(self, parameter=0):
        from .arithmetic_curve_structure import ramified_scaling_chart
        return ramified_scaling_chart(self, parameter)

    def cyclic_projector_obstruction(self, matrix=None):
        from .arithmetic_curve_structure import cyclic_projector_obstruction
        return cyclic_projector_obstruction(self, matrix)

    def specialize(self, parameter):
        t = _q(parameter); disc = P.evaluate(self.discriminant,t)
        if not disc: raise ValueError('singular family parameter')
        return dict(parameter=t,coefficients=[a.evaluate(t) for a in self.f],discriminant=disc,
            connection=[[a.evaluate(t) for a in row] for row in self.connection],genus=self.genus,state_dimension=self.dimension)

    def _observable(self, coefficients=None):
        budget = AlgebraBudget(**self.limits)
        if coefficients is None: coefficients = [1]+[0]*(self.dimension-1)
        if not isinstance(coefficients,(list,tuple)) or len(coefficients)!=self.dimension:
            raise ValueError('one rational-function coefficient per differential required')
        row = [RF.parse(a,budget) for a in coefficients]
        connection = [[RF.parse(a,budget) for a in r] for r in self.connection]
        rows = []
        while True:
            if rows:
                decoder = solve_many(list(map(list,zip(*rows))),[[v] for v in row])
            else: decoder = [] if not any(row) else None
            if decoder is not None: break
            if len(rows)>=self.dimension: raise AssertionError('differential row span did not close')
            rows.append(row)
            row = [a.derivative()+sum((rows[-1][k]*connection[k][j] for k in range(self.dimension)),RF.parse(0,budget)) for j,a in enumerate(rows[-1])]
        coefficients = [-a[0] for a in decoder]+[RF.parse(1,budget)]
        primitive = primitive_operator(coefficients, budget)
        leading = P.poly(primitive[-1]); outside = leading
        while P.degree(P.gcd_poly(outside,self.discriminant))>0:
            outside = P.exact_div(outside,P.gcd_poly(outside,self.discriminant))
        outside = P.exact_div(outside,P.gcd_poly(outside,P.derivative(outside)))
        packet = dict(schema='pp-family-observable/1',order=len(rows),derivative_rows=encode_matrix(rows),
            terminal_row=[a.packet() for a in row],monic_operator=[a.packet() for a in coefficients],
            polynomial_operator=primitive,weyl_terms=[dict(t_degree=i,D_degree=j,coefficient=str(c)) for j,p in enumerate(primitive) for i,c in enumerate(p) if c],
            scalar_leading_coefficient=list(map(str,leading)),scalar_singularities_outside_discriminant=list(map(str,P.monic(outside))),
            algebra_work=budget.work,complete=True,execution_verified=False,
            minimality='successive differential rows independent until first exact Q(t) dependency; minimal universal operator for this observable on the full period module, not every individual cycle',
            singularity_scope='zeros outside the family discriminant may be apparent or poles of supplied observable coefficients; removability not asserted')
        return packet, rows, coefficients

    def observable(self, coefficients=None): return self._observable(coefficients)[0]

    def parameter_domain(self, predicate=True):
        from .semilinear_domains import semilinear_domain
        return semilinear_domain({'op':'and','args':[{'poly':list(P.integer_primitive(self.discriminant)),'relation':'!='},predicate]})

    def parameter_population(self, lower, upper, predicate=True):
        from .populations import ExactPopulation
        if type(lower) is not int or type(upper) is not int or lower>upper:
            raise ValueError('ordered integer parameter bounds required')
        scale = P.common_denominator(self.discriminant)
        specification = dict(kind='domain',predicate={'op':'and','args':[
            {'poly':[-lower,1],'relation':'>='},{'poly':[-upper,1],'relation':'<='},
            {'poly':list(P.integer_primitive(self.discriminant)),'relation':'!='},predicate]},
            fields={'parameter':[0,1],'discriminant_scaled':[int(c*scale) for c in self.discriminant]})
        population = ExactPopulation(specification)
        return dict(specification=specification,summary=population.summary(),discriminant_scale=scale)

    def integer_points(self, parameter, lower, upper):
        if type(lower) is not int or type(upper) is not int or not 0<=upper-lower<=1000000:
            raise ValueError('ordered x interval of at most one million steps required')
        if max(abs(lower).bit_length(),abs(upper).bit_length())>4096: raise WorkLimit('x bound bit budget')
        f = self.specialize(parameter)['coefficients']; points=[]
        for x in range(lower,upper+1):
            value = P.evaluate(f,x)
            if value.denominator!=1: continue
            if abs(value.numerator).bit_length()>8192: raise WorkLimit('bounded curve output bit budget')
            y=integer_power_root(value.numerator,2)
            if y is not None: points.extend([(x,y)] if not y else [(x,-y),(x,y)])
        return dict(parameter=_q(parameter),x_interval=[lower,upper],points=points,complete_in_interval=True,
            global_integer_completeness=False,scope='all integer points in the supplied closed x interval only')

    def marked_period(self, parameter, contour, tolerance=1e-10):
        from .family_continuation import marked_period
        return marked_period(self,parameter,contour,tolerance)

    def transport(self, path, tolerance=1e-10):
        from .family_continuation import transport
        return transport(self,path,tolerance)

    def period_path(self, path, contour, coefficients=None, mode='matrix', tolerance=1e-10):
        from .family_continuation import period_path
        return period_path(self,path,contour,coefficients,mode,tolerance)
