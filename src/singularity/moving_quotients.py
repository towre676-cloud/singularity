"""NX33 exact chartwise moving quotients and differential gauge identities."""
from dataclasses import dataclass
from itertools import combinations
from .period_observations import (_matrix,_coordinates,_derivative_row,_product,_rf,
    _excluded,_backend,RationalConnection,assert_regular_segment)


@dataclass(frozen=True)
class MovingQuotient:
    connection: RationalConnection
    basis: tuple
    reduced_connection: tuple
    targets: tuple
    target_coordinates: tuple
    excluded_polynomials: tuple

    @property
    def rank(self): return len(self.basis)


def construct_quotient(connection,basis,targets=()):
    """Construct T iff B'+BA factors through B; retain target factorization."""
    if not isinstance(connection,RationalConnection):
        raise TypeError("RationalConnection required")
    b=_matrix(basis,connection.dimension);targets=_matrix(targets,connection.dimension)
    independent=[]
    for row in b:
        if _coordinates(row,independent)is not None:
            raise ValueError("basis rows must be field-independent")
        independent.append(row)
    reduced=tuple(_coordinates(_derivative_row(row,connection.matrix),b) for row in b)
    if any(row is None for row in reduced):
        raise ValueError("moving hidden direction leaks: B'+BA is outside span(B)")
    coords=tuple(_coordinates(row,b) for row in targets)
    if any(row is None for row in coords):
        raise ValueError("closed quotient omits the requested target")
    exclusions=_excluded((connection.matrix,b,reduced,coords))
    if b:
        for columns in combinations(range(connection.dimension),len(b)):
            d=_backend("rational_functions").determinant([[row[j] for j in columns]for row in b])
            if d:
                if len(d.n)>1:exclusions.add(tuple(d.n))
                break
    return MovingQuotient(connection,b,reduced,targets,coords,tuple(sorted(exclusions)))


def verify_quotient(q):
    try:
        replay=construct_quotient(q.connection,q.basis,q.targets)
        return replay==q
    except(ValueError,TypeError):return False


def gauge_quotient(quotient,gauge):
    g=_matrix(gauge,quotient.rank)
    if len(g)!=quotient.rank:raise ValueError("square reduced gauge required")
    inv=_backend("rational_functions").solve_many(list(map(list,g)),
        [[_rf(int(i==j))for j in range(len(g))]for i in range(len(g))])
    if inv is None:raise ValueError("invertible gauge required")
    b=_product(g,quotient.basis)
    transformed=construct_quotient(quotient.connection,b,quotient.targets)
    derivative=tuple(tuple(v.derivative()for v in row)for row in g)
    lhs=_product(derivative,inv);conjugate=_product(_product(g,quotient.reduced_connection),inv)
    law=tuple(tuple(v+w for v,w in zip(a,b))for a,b in zip(lhs,conjugate))
    if transformed.reduced_connection!=law:
        raise ArithmeticError("differential gauge law failed")
    return transformed


def verify_overlap(first,second,gauge):
    try:
        transformed=gauge_quotient(first,gauge)
        return (transformed.basis==second.basis and
                transformed.reduced_connection==second.reduced_connection and
                transformed.target_coordinates==second.target_coordinates and
                first.connection==second.connection)
    except(ValueError,TypeError):return False


def assert_quotient_path(quotient,path):
    for a,b in zip(path,path[1:]):
        assert_regular_segment(quotient.connection,a,b,quotient.excluded_polynomials)
    return True


def obstruction_at(connection,basis,parameter):
    """A rational sample is a failure witness, never a closure proof."""
    from fractions import Fraction
    b=_matrix(basis,connection.dimension)
    evaluated=tuple(tuple(v.evaluate(parameter)for v in row)for row in b)
    # Avoid a private nullspace API: solve one free-coordinate linear system.
    rf=_backend("rational_functions")
    for free in range(connection.dimension):
        matrix=[list(row)for row in evaluated]
        matrix.append([Fraction(i==free)for i in range(connection.dimension)])
        rhs=[[Fraction(0)]for _ in evaluated]+[[Fraction(1)]]
        try:
            solution=rf.solve_many([[_rf(v)for v in row]for row in matrix],
                                   [[_rf(v[0])]for v in rhs])
        except(ValueError,ZeroDivisionError):continue
        if solution is None:continue
        hidden=tuple(v[0].evaluate(parameter)for v in solution)
        rates=tuple(sum((v.evaluate(parameter)*h for v,h in zip(_derivative_row(row,connection.matrix),hidden)),Fraction(0))for row in b)
        if any(rates):return {"parameter":parameter,"hidden":hidden,"exposure_rates":rates}
    return None
