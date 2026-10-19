"""Small dense float linear algebra; enough for ridge fits on tens of features."""
from math import sqrt


def zeros(m, n):
    return [[0.0]*n for _ in range(m)]


def transpose(a):
    return [list(r) for r in zip(*a)]


def matmul(a, b):
    bt = transpose(b)
    return [[sum(x*y for x, y in zip(row, col)) for col in bt] for row in a]


def matvec(a, v):
    return [sum(x*y for x, y in zip(row, v)) for row in a]


def dot(u, v):
    return sum(x*y for x, y in zip(u, v))


def solve(a, b):
    """Gaussian elimination with partial pivoting; b may be a vector or a matrix."""
    n = len(a)
    vec = not isinstance(b[0], list)
    rhs = [[x] for x in b] if vec else [list(r) for r in b]
    m = [list(map(float, a[i]))+list(map(float, rhs[i])) for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda i: abs(m[i][c]))
        if abs(m[p][c]) < 1e-12:
            raise ZeroDivisionError("singular system")
        m[c], m[p] = m[p], m[c]
        piv = m[c][c]
        m[c] = [x/piv for x in m[c]]
        for i in range(n):
            if i != c and m[i][c]:
                z = m[i][c]
                m[i] = [x-z*y for x, y in zip(m[i], m[c])]
    out = [row[n:] for row in m]
    return [r[0] for r in out] if vec else out


def inverse(a):
    n = len(a)
    return solve(a, [[float(i == j) for j in range(n)] for i in range(n)])


def ridge(x, y, lam, penalize_first=False, weights=None):
    """argmin sum w_i (y_i - x_i b)^2 + lam |b|^2 (intercept column 0 unpenalized by default)."""
    p = len(x[0])
    w = weights or [1.0]*len(x)
    xtx = zeros(p, p)
    xty = [0.0]*p
    for row, yi, wi in zip(x, y, w):
        for i in range(p):
            xty[i] += wi*row[i]*yi
            for j in range(p):
                xtx[i][j] += wi*row[i]*row[j]
    for i in range(p):
        if i or penalize_first:
            xtx[i][i] += lam
    xtx[0][0] += 1e-9
    return solve(xtx, xty)


def mean(v):
    v = list(v)
    return sum(v)/len(v) if v else float("nan")


def var(v):
    v = list(v)
    if len(v) < 2:
        return float("nan")
    m = mean(v)
    return sum((x-m)**2 for x in v)/(len(v)-1)


def sd(v):
    return sqrt(var(v))


def pearson(u, v):
    mu, mv = mean(u), mean(v)
    num = sum((a-mu)*(b-mv) for a, b in zip(u, v))
    den = sqrt(sum((a-mu)**2 for a in u)*sum((b-mv)**2 for b in v))
    return num/den if den else float("nan")


def quantile(v, q):
    s = sorted(v)
    if not s:
        return float("nan")
    k = (len(s)-1)*q
    lo = int(k)
    hi = min(lo+1, len(s)-1)
    return s[lo]+(s[hi]-s[lo])*(k-lo)


class Standardizer:
    """Column means and scales fitted on training rows only."""

    def __init__(self, rows):
        cols = transpose(rows)
        self.mu = [mean(c) for c in cols]
        self.sc = [(sd(c) if len(c) > 1 and sd(c) > 1e-12 else 1.0) for c in cols]

    def __call__(self, rows):
        return [[(x-m)/s for x, m, s in zip(r, self.mu, self.sc)] for r in rows]
