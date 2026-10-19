"""Dependency-free rational linear algebra. Matrices use row lists."""
from fractions import Fraction as Q


def matrix(a):
    rows = [[Q(x) for x in row] for row in a]
    if rows and any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("ragged matrix")
    return rows


def rref(a, ncols=None):
    a = matrix(a)
    n = len(a[0]) if a else (ncols or 0)
    if ncols is not None and a and n != ncols:
        raise ValueError("column count differs")
    pivots = []
    row = 0
    for col in range(n):
        pivot = next((i for i in range(row, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[row], a[pivot] = a[pivot], a[row]
        z = a[row][col]
        a[row] = [x / z for x in a[row]]
        for i in range(len(a)):
            if i != row and a[i][col]:
                z = a[i][col]
                a[i] = [x - z*y for x, y in zip(a[i], a[row])]
        pivots.append(col)
        row += 1
        if row == len(a):
            break
    return a, pivots


def rank(a, ncols=None):
    return len(rref(a, ncols)[1])


def nullspace(a, ncols=None):
    rr, pivots = rref(a, ncols)
    n = len(rr[0]) if rr else (ncols or 0)
    out = []
    for f in range(n):
        if f in pivots:
            continue
        v = [Q(0)] * n
        v[f] = Q(1)
        for i, p in enumerate(pivots):
            v[p] = -rr[i][f]
        out.append(v)
    return out


def matmul(a, b):
    a, b = matrix(a), matrix(b)
    if not a or not b:
        raise ValueError("empty matrix multiplication needs explicit shape")
    if len(a[0]) != len(b):
        raise ValueError("incompatible matrix shapes")
    return [[sum((a[i][k]*b[k][j] for k in range(len(b))), Q(0))
             for j in range(len(b[0]))] for i in range(len(a))]


def transpose(a):
    return [list(x) for x in zip(*a)]


def row_basis(a, ncols=None):
    rr, p = rref(a, ncols)
    return rr[:len(p)]


def observable_space(a, c):
    """Smallest row space containing C and closed under right multiplication by A."""
    a, c = matrix(a), matrix(c)
    n = len(a)
    if not n or len(a[0]) != n or not c or len(c[0]) != n:
        raise ValueError("need square A and nonempty compatible C")
    basis = row_basis(c, n)
    while True:
        expanded = row_basis(basis + matmul(basis, a), n) if basis else []
        if len(expanded) == len(basis):
            return expanded
        basis = expanded


def target_recovery(observation, target, ncols=None):
    """Exact ker(O) subset ker(G) decision, with a hidden vector on failure."""
    o, g = matrix(observation), matrix(target)
    n = ncols or (len(o[0]) if o else len(g[0]))
    if any(len(row) != n for row in o + g):
        raise ValueError("incompatible observations and targets")
    for v in nullspace(o, n):
        response = [sum((x*y for x, y in zip(row, v)), Q(0)) for row in g]
        if any(response):
            return {"recoverable": False, "hidden_vector": v, "target_response": response}
    return {"recoverable": True, "hidden_vector": None, "target_response": None}


def hankel(values, rows, cols):
    if len(values) < rows + cols - 1:
        raise ValueError("insufficient sequence values")
    return [[Q(values[i+j]) for j in range(cols)] for i in range(rows)]
