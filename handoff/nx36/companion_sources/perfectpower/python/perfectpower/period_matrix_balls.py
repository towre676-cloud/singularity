"""Exact inverse enclosures and conditional integral recognition for periods.

Errors use the induced row norm with |Re z|+|Im z| on complex entries.
The caller must justify the input enclosure. Proximity alone never proves that
a matrix is integral; the recognition result exposes that separate premise.
"""
from fractions import Fraction as Q
from .certified_period_transport import Gaussian as G, multiply, rownorm, legendre_marked_periods


def _matrix(matrix):
    if not isinstance(matrix, list) or not 1 <= len(matrix) <= 6:
        raise ValueError('square matrix of dimension 1 through 6 required')
    n = len(matrix)
    if any(not isinstance(row, list) or len(row) != n for row in matrix):
        raise ValueError('square matrix required')
    return [[G.parse(v) for v in row] for row in matrix]


def _error(value):
    value = Q(value)
    if value < 0:
        raise ValueError('nonnegative row error bound required')
    return value


def _packet(matrix):
    return [[v.packet() for v in row] for row in matrix]


def exact_inverse(matrix):
    matrix = _matrix(matrix)
    n = len(matrix)
    rows = [row + [G(i == j) for j in range(n)] for i, row in enumerate(matrix)]
    for j in range(n):
        pivot = next((i for i in range(j, n) if rows[i][j]), None)
        if pivot is None:
            raise ValueError('singular centre matrix')
        rows[j], rows[pivot] = rows[pivot], rows[j]
        divisor = rows[j][j]
        rows[j] = [v/divisor for v in rows[j]]
        for i in range(n):
            if i != j:
                factor = rows[i][j]
                rows[i] = [v-factor*w for v, w in zip(rows[i], rows[j])]
    inverse = [row[n:] for row in rows]
    product = multiply(matrix, inverse)
    if any((product[i][j]-G(i == j)).norm() for i in range(n) for j in range(n)):
        raise ArithmeticError('exact inverse identity failed')
    return inverse


def inverse_matrix_ball(matrix, row_error_bound):
    """If ||A-C||<=e and ||C^-1||e<1, enclose every A^-1 by Neumann's lemma."""
    centre = _matrix(matrix)
    error = _error(row_error_bound)
    inverse = exact_inverse(centre)
    norm = rownorm(inverse)
    residual = norm*error
    if residual >= 1:
        raise ValueError('inverse enclosure cannot certify nonsingularity: residual >= 1')
    return dict(schema='pp-inverse-matrix-ball/1', matrix=_packet(inverse),
                row_error_bound=str(norm*residual/(1-residual)),
                inverse_centre_row_norm=str(norm), residual_upper_bound=str(residual),
                certified_under_input_enclosure=True,
                argument='A=C(I+C^-1 E); ||C^-1 E||<=q<1. Inverse error <= ||C^-1||q/(1-q).',
                scope='conditional on the supplied row enclosure; no period marking inferred')


def multiply_matrix_balls(left, left_error, right, right_error):
    a, b = _matrix(left), _matrix(right)
    if len(a) != len(b):
        raise ValueError('matrix dimensions differ')
    ea, eb = _error(left_error), _error(right_error)
    error = rownorm(a)*eb + ea*rownorm(b) + ea*eb
    return dict(schema='pp-product-matrix-ball/1', matrix=_packet(multiply(a, b)),
                row_error_bound=str(error), certified_under_input_enclosures=True)


def recognize_integral_matrix(matrix, row_error_bound, *, symplectic=False):
    """Identify the unique possible integral matrix, conditional on integrality."""
    centre = _matrix(matrix)
    error = _error(row_error_bound)
    if error >= Q(1, 2):
        raise ValueError('strict error below 1/2 required for integral recognition')
    candidate = []
    for row in centre:
        values = []
        for v in row:
            nearest = (v.a + Q(1, 2)).numerator // (v.a + Q(1, 2)).denominator
            if abs(v.a-nearest)+abs(v.b) > error:
                raise ValueError('entry enclosure contains no integral value')
            values.append(nearest)
        candidate.append(values)
    # The row norm, rather than just independent entry bounds, is the premise.
    if any(sum(abs(v.a-k)+abs(v.b) for v, k in zip(row, integers)) > error
           for row, integers in zip(centre, candidate)):
        raise ValueError('row enclosure contains no integral matrix')
    if symplectic:
        n = len(candidate)
        if n % 2:
            raise ValueError('even dimension required for symplectic marking')
        g = n//2
        form = [[int(j == i+g)-int(i == j+g) for j in range(n)] for i in range(n)]
        transformed = [[sum(candidate[k][i]*form[k][l]*candidate[l][j]
                            for k in range(n) for l in range(n))
                        for j in range(n)] for i in range(n)]
        if transformed != form:
            raise ValueError('unique integral candidate does not preserve the standard symplectic form')
    return dict(schema='pp-integral-matrix-recognition/1', candidate=candidate,
                row_error_bound=str(error), integrality_premise_required=True,
                unique_under_integrality_premise=True, symplectic_checked=bool(symplectic),
                scope='proximity identifies an integral matrix only when integrality is independently justified')


def marked_legendre_monodromy(path, order=18, seed_terms=48, rounding_bits=128, step_limit=256):
    """Recognize P(base)^-1 P(end) on a closed marked Legendre path.

    Integrality comes from continuation of the marked integral cycles, not
    numerical closeness. Conservative enclosures may reject a valid loop.
    """
    if not isinstance(path, list) or len(path) < 2:
        raise ValueError('closed polygon with at least two vertices required')
    if (G.parse(path[0])-G.parse(path[-1])).norm():
        raise ValueError('closed path required')
    initial = legendre_marked_periods([path[0], path[0]], order, seed_terms, rounding_bits, step_limit)
    continued = legendre_marked_periods(path, order, seed_terms, rounding_bits, step_limit)
    inverse = inverse_matrix_ball(initial['period_state'], initial['row_error_bound'])
    monodromy = multiply_matrix_balls(inverse['matrix'], inverse['row_error_bound'],
                                     continued['period_state'], continued['row_error_bound'])
    recognition = recognize_integral_matrix(monodromy['matrix'], monodromy['row_error_bound'], symplectic=True)
    return dict(schema='pp-marked-legendre-monodromy/1', monodromy=recognition['candidate'],
                enclosure=monodromy, initial=initial, continued=continued,
                recognition=recognition,
                integrality_argument='Closed continuation transports the standard integral a,b cycles; their intersection is preserved.',
                scope='standard marked Legendre periods only; analytic estimates and cycle marking are not Lean verified')


def verify_marked_legendre_monodromy(path, receipt, order=18, seed_terms=48,
                                     rounding_bits=128, step_limit=256):
    """Replay from the externally supplied path, checking every serialized field.

    This recomputes exact rational analytic bounds; it is a replay checker, not
    an independent analytic proof or a Lean verification of the integrality premise.
    """
    import json
    try:
        expected = marked_legendre_monodromy(path, order, seed_terms, rounding_bits, step_limit)
        # JSON equality distinguishes booleans from integers and binds the entire
        # transcript, including marking, errors and each continuation disk.
        return json.dumps(receipt, sort_keys=True, separators=(',', ':'), allow_nan=False) == \
            json.dumps(expected, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (ValueError, TypeError, ArithmeticError, OverflowError):
        return False
