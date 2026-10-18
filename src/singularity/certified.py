"""Certified enclosures of the normalized prime product K_{G,H}(s,q) (SNG-F38).

For equal-order connected graphs with first discrepancy delta at volume r,

    log K = sum_p [ delta log(1 - p^(-rs)) + log B_G(p^(-s)) - log B_H(p^(-s)) ],

because L_G/L_H = B_G/B_H with B = (1 - x^n) L.  Every primewise term is
enclosed rigorously:

* t = p^(-a/b) by integer b-th roots at a fixed binary scale;
* B(t) is increasing in t (nonnegative coefficients), so B(t) lies between
  the height-truncated sums B_{<=H}(t_lo) and B_{<=H}(t_hi) + tail, the sums
  being evaluated on a checked tree decomposition with outward-rounded
  fixed-point arithmetic and a "minimum zero reached" flag;
* the height tail is at most sum_{h>H} N_n(h) t^h q^ceil(h^2/D), with
  N_n(h) = (h+1)^n - 2h^n + (h-1)^n minimum-zero profiles of maximum h and
  D the diameter (a shortest path from a minimum to a maximum vertex gives
  h^2 <= D E);
* logarithms are enclosed by atanh series with explicit remainders.

The omitted primes p > P are bounded by the coefficient-aware constant of
``coefficient_aware_tail_constant`` and the integral test.  No floating point
participates in any bound; floats appear only in human-readable summaries.
"""

from __future__ import annotations

from fractions import Fraction
from math import comb, isqrt
from typing import Sequence

from .decomposition import TreeDecomposition, _rooted, charge_owners, check_decomposition, elimination_decomposition
from .graph import Graph

BITS = 256
ONE = 1 << BITS


# ---------------------------------------------------------------- intervals

def _floor_div(a: int, b: int) -> int:
    return a // b


def _ceil_div(a: int, b: int) -> int:
    return -((-a) // b)


def to_fixed(value: Fraction, up: bool) -> int:
    value = Fraction(value)
    return (_ceil_div if up else _floor_div)(value.numerator * ONE, value.denominator)


def from_fixed(value: int) -> Fraction:
    return Fraction(value, ONE)


def iroot(value: int, degree: int) -> int:
    """floor(value^(1/degree)) for value >= 0."""
    if value < 0 or degree < 1:
        raise ValueError("nonnegative value and positive degree required")
    if degree == 1 or value < 2:
        return value
    if degree == 2:
        return isqrt(value)
    low, high = 0, 1 << (value.bit_length() // degree + 1)
    while high - low > 1:
        middle = (low + high) // 2
        if middle ** degree <= value:
            low = middle
        else:
            high = middle
    return low


def prime_power_enclosure(prime: int, numerator: int, denominator: int) -> tuple[int, int]:
    """Fixed-point (lo, hi) with lo <= p^(-a/b) * 2^BITS <= hi."""
    scale = ONE ** denominator
    power = prime ** numerator
    low = iroot(scale // power, denominator)
    high = iroot(_ceil_div(scale, power), denominator) + 1
    return low, high


def _log_unit(m_low: Fraction, m_high: Fraction) -> tuple[Fraction, Fraction]:
    """Enclose log m for 1 <= m_low <= m_high <= 2 via 2 atanh((m-1)/(m+1))."""
    def series(m: Fraction, up: bool) -> Fraction:
        z = (m - 1) / (m + 1)  # 0 <= z <= 1/3
        z2, term, total, k = z * z, z, Fraction(0), 0
        bound = Fraction(1, ONE)
        while True:
            total += term / (2 * k + 1)
            term *= z2
            k += 1
            remainder = term / ((2 * k + 1) * (1 - z2))
            if remainder < bound:
                break
        total = 2 * total
        return total + 2 * remainder if up else total
    return series(m_low, False), series(m_high, True)


_LOG2 = None


def _log2() -> tuple[Fraction, Fraction]:
    global _LOG2
    if _LOG2 is None:
        low, high = _log_unit(Fraction(2), Fraction(2))
        _LOG2 = (low, high)
    return _LOG2


def log_enclosure(low: Fraction, high: Fraction) -> tuple[Fraction, Fraction]:
    """Enclose [log low, log high] for 0 < low <= high, rounded to dyadics."""
    if not 0 < low <= high:
        raise ValueError("positive ordered endpoints required")
    # Outward rounding to the fixed-point grid keeps denominators small.
    if low >= Fraction(1, 2 ** (BITS - 56)):
        low = from_fixed(to_fixed(low, False))  # still positive at this size
    high = from_fixed(to_fixed(high, True))

    def reduce(x: Fraction) -> tuple[int, Fraction]:
        e = 0
        while x >= 2:
            x /= 2
            e += 1
        while x < 1:
            x *= 2
            e -= 1
        return e, x

    l2_low, l2_high = _log2()
    e1, m1 = reduce(Fraction(low))
    e2, m2 = reduce(Fraction(high))
    lo = e1 * (l2_low if e1 >= 0 else l2_high) + _log_unit(m1, m1)[0]
    hi = e2 * (l2_high if e2 >= 0 else l2_low) + _log_unit(m2, m2)[1]
    return from_fixed(to_fixed(lo, False)), from_fixed(to_fixed(hi, True))


def exp_enclosure(low: Fraction, high: Fraction) -> tuple[Fraction, Fraction]:
    """Enclose [exp low, exp high] by Taylor bounds on [-1, 1] and repeated squaring."""
    def bounds(x: Fraction) -> tuple[Fraction, Fraction]:
        total, term, k = Fraction(1), Fraction(1), 0
        while True:
            k += 1
            term = term * x / k
            total += term
            # |remainder| <= |x|^(k+1)/(k+1)! * e^|x| <= 3 |term| / (k+1)
            remainder = 3 * abs(term) / (k + 1)
            if remainder < Fraction(1, ONE):
                return total - remainder, total + remainder
    def reduced(x: Fraction, which: int) -> Fraction:
        halvings = 0
        while abs(x) > 1:
            x /= 2
            halvings += 1
        value = bounds(x)[which]
        for _ in range(halvings):  # exp(2y) = exp(y)^2, monotone on positive values
            value = from_fixed(to_fixed(value * value, which == 1))
        return value

    return reduced(Fraction(low), 0), reduced(Fraction(high), 1)


# ------------------------------------------------- normalized local factors

def diameter(graph: Graph) -> int:
    if not graph.connected:
        raise ValueError("a connected graph is required")
    longest = 0
    for start in range(graph.n):
        seen, frontier, depth = {start}, [start], 0
        while frontier:
            nxt = [w for v in frontier for w in graph.neighbors[v] if w not in seen]
            seen.update(nxt)
            frontier = list(dict.fromkeys(nxt))
            if frontier:
                depth += 1
        longest = max(longest, depth)
    return longest


def greedy_decomposition(graph: Graph) -> TreeDecomposition:
    """Min-degree elimination order; validity is checked by the engine."""
    remaining = {v: set(graph.neighbors[v]) for v in range(graph.n)}
    order = []
    while remaining:
        v = min(remaining, key=lambda u: (len(remaining[u]), u))
        neighbours = remaining.pop(v)
        for a in neighbours:
            remaining[a] |= neighbours - {a}
            remaining[a].discard(v)
        order.append(v)
    return elimination_decomposition(graph, order)


def height_tail_bound(n: int, diam: int, height: int, t: Fraction, q: Fraction) -> Fraction:
    """Upper bound on sum_{h > H} N_n(h) t^h q^ceil(h^2/D) for 0 < t, q < 1.

    Terms are summed exactly until the ratio bound
    rho(h) = ((h+2)/(h+1))^(n-2) t q^floor((2h+1)/D), which majorizes the
    ratio of consecutive majorants n(n-1)(h+1)^(n-2) t^h q^ceil(h^2/D) and is
    nonincreasing in h, drops to 1/2; the rest is at most twice the next
    majorant term.
    """
    t, q = Fraction(t), Fraction(q)

    def count(h):
        return (h + 1) ** n - 2 * h ** n + (h - 1) ** n

    def majorant(h):
        return n * (n - 1) * Fraction(h + 1) ** (n - 2) * t ** h * q ** (-(-h * h // diam))

    total, h = Fraction(0), height + 1
    while True:
        ratio = Fraction(h + 2, h + 1) ** (n - 2) * t * q ** ((2 * h + 1) // diam)
        if ratio <= Fraction(1, 2):
            return total + 2 * majorant(h)
        total += count(h) * t ** h * q ** (-(-h * h // diam))
        h += 1


def min_zero_box_sum(graph: Graph, decomposition: TreeDecomposition, height: int, t_fixed: int,
                     q: Fraction, up: bool) -> int:
    """Fixed-point bound on sum over a in {0..H}^n with min a = 0 of t^|a| q^E(a).

    ``up=False`` rounds every product down (a lower bound), ``up=True`` up.
    All summands are nonnegative, so monotone rounding gives valid bounds.
    """
    errors = check_decomposition(graph, decomposition)
    if errors:
        raise ValueError("; ".join(errors))
    div = _ceil_div if up else _floor_div

    def mul(a: int, b: int) -> int:
        return div(a * b, ONE)

    t_pow = [ONE]
    for _ in range(height * graph.n + 1):
        t_pow.append(mul(t_pow[-1], t_fixed))
    q_pow = {d * d: to_fixed(Fraction(q) ** (d * d), up) for d in range(height + 1)}
    order, parent = _rooted(decomposition)
    vertex_owner, edge_owner = charge_owners(graph, decomposition)
    bags = decomposition.bags
    children: list[list[int]] = [[] for _ in bags]
    for node in order[1:]:
        children[parent[node]].append(node)
    owned_v = [[v for v in bags[s] if vertex_owner[v] == s] for s in range(len(bags))]
    owned_e = [[e for e, o in edge_owner.items() if o == s] for s in range(len(bags))]
    messages: dict[int, dict[tuple, int]] = {}
    from itertools import product as cartesian

    for node in reversed(order):
        bag = bags[node]
        pos = {v: i for i, v in enumerate(bag)}
        tables = []
        for child in children[node]:
            shared = [v for v in bags[child] if v in pos]
            cpos = {v: i for i, v in enumerate(bags[child])}
            table: dict[tuple, int] = {}
            for (assignment, flag), value in messages.pop(child).items():
                key = (tuple(assignment[cpos[v]] for v in shared), flag)
                table[key] = table.get(key, 0) + value
            tables.append((shared, table))
        message: dict[tuple, int] = {}
        for assignment in cartesian(range(height + 1), repeat=len(bag)):
            weight = t_pow[sum(assignment[pos[v]] for v in owned_v[node])]
            for u, v in owned_e[node]:
                weight = mul(weight, q_pow[(assignment[pos[u]] - assignment[pos[v]]) ** 2])
            state = {any(assignment[pos[v]] == 0 for v in owned_v[node]): weight}
            for shared, table in tables:
                key = tuple(assignment[pos[v]] for v in shared)
                nxt: dict[bool, int] = {}
                for flag, value in state.items():
                    for child_flag in (False, True):
                        c = table.get((key, child_flag))
                        if c:
                            f = flag or child_flag
                            nxt[f] = nxt.get(f, 0) + mul(value, c)
                state = nxt
            for flag, value in state.items():
                if value:
                    message[assignment, flag] = message.get((assignment, flag), 0) + value
        messages[node] = message
    return sum(v for (_, flag), v in messages[decomposition.root].items() if flag)


def normalized_factor_enclosure(graph: Graph, t_low: int, t_high: int, q: Fraction,
                                target: Fraction = Fraction(1, 2 ** 60),
                                decomposition: TreeDecomposition | None = None) -> dict:
    """Enclose B_G(t, q) for t in [t_low, t_high] / 2^BITS (fixed point)."""
    decomposition = decomposition or greedy_decomposition(graph)
    diam = diameter(graph)
    th = from_fixed(t_high)
    height = 1
    while height_tail_bound(graph.n, diam, height, th, q) > target:
        height += 1
    tail = from_fixed(to_fixed(height_tail_bound(graph.n, diam, height, th, q), True))
    low = from_fixed(min_zero_box_sum(graph, decomposition, height, t_low, q, False))
    high = from_fixed(min_zero_box_sum(graph, decomposition, height, t_high, q, True)) + tail
    return {"low": low, "high": high, "height": height, "height_tail": tail}


# ------------------------------------------------------- omitted primes

def coefficient_aware_tail_constant(left: Sequence[Fraction], right: Sequence[Fraction], vertex_count: int,
                                    first_depth: int, radius: Fraction) -> Fraction:
    """Sharpened (7.12): exact coefficient values through len-1, A_n beyond.

    With l_n, m_n the local coefficients at the fixed q, delta = l_r - m_r,
    S = (1-rho)^(-k) - sum_{n<=M} A_n rho^n (the A_n tail beyond M):
        T = sum_{r<n<=M} |l_n - m_n| rho^(n-r-1) + 2 S / rho^(r+1),
        D = sum_{1<=n<=M} max(l_n, m_n) rho^(n-1) + S / rho,
        C = T + |delta| D + |delta| rho^(r-1) / (2 (1 - rho^r)).
    """
    k, r, rho = vertex_count, first_depth, Fraction(radius)
    if not 0 < rho < 1 or len(left) != len(right) or len(left) <= r + 1:
        raise ValueError("need 0 < rho < 1 and coefficients beyond the first depth")
    if any(left[n] != right[n] for n in range(r)) or left[r] == right[r]:
        raise ValueError("coefficients must agree below r and differ at r")
    top = len(left) - 1
    a = lambda n: comb(n + k - 1, k - 1)
    beyond = (1 - rho) ** (-k) - sum(a(n) * rho ** n for n in range(top + 1))
    delta = left[r] - right[r]
    t_const = sum(abs(left[n] - right[n]) * rho ** (n - r - 1) for n in range(r + 1, top + 1)) + 2 * beyond / rho ** (r + 1)
    d_const = sum(max(left[n], right[n]) * rho ** (n - 1) for n in range(1, top + 1)) + beyond / rho
    return t_const + abs(delta) * d_const + abs(delta) * rho ** (r - 1) / (2 * (1 - rho ** r))


def primes_up_to(limit: int) -> list[int]:
    sieve = bytearray([1]) * (limit + 1)
    sieve[:2] = b"\x00\x00"
    for i in range(2, isqrt(limit) + 1):
        if sieve[i]:
            sieve[i * i:: i] = bytearray(len(sieve[i * i:: i]))
    return [i for i, flag in enumerate(sieve) if flag]


def certified_k(left: Graph, right: Graph, q: Fraction, s_numerator: int, s_denominator: int,
                cutoff_root: int, coefficient_volume: int = 6) -> dict:
    """Enclose log K and K at s = a/b with primes up to N^b kept exactly."""
    from .heights import local_coefficients
    from .polynomials import evaluate

    q = Fraction(q)
    if left.n != right.n or not left.connected or not right.connected:
        raise ValueError("equal-order connected graphs are required")
    l_vals = [evaluate(row, q) for row in local_coefficients(left, coefficient_volume)]
    r_vals = [evaluate(row, q) for row in local_coefficients(right, coefficient_volume)]
    depth = next((v for v in range(len(l_vals)) if l_vals[v] != r_vals[v]), None)
    if depth is None or depth < 1 or depth + 1 >= len(l_vals):
        raise ValueError("no usable first discrepancy within the coefficient volume")
    delta = l_vals[depth] - r_vals[depth]
    a, b, n_root = s_numerator, s_denominator, cutoff_root
    s = Fraction(a, b)
    if (depth + 1) * s <= 1:
        raise ValueError("the regularized product needs (r+1)s > 1")
    cutoff = n_root ** b
    radius = Fraction(1, n_root ** a)  # = cutoff^(-s)
    constant = coefficient_aware_tail_constant(l_vals, r_vals, left.n, depth, radius)
    prime_tail = constant * Fraction(n_root) ** (b - (depth + 1) * a) / ((depth + 1) * s - 1)
    dec_left, dec_right = greedy_decomposition(left), greedy_decomposition(right)
    log_low = log_high = Fraction(0)
    local_error = Fraction(0)
    max_height = 0
    primes = primes_up_to(cutoff)
    for p in primes:
        t_lo, t_hi = prime_power_enclosure(p, a, b)
        bg = normalized_factor_enclosure(left, t_lo, t_hi, q, decomposition=dec_left)
        bh = normalized_factor_enclosure(right, t_lo, t_hi, q, decomposition=dec_right)
        max_height = max(max_height, bg["height"], bh["height"])
        local_error += bg["height_tail"] + bh["height_tail"]
        if depth * a % b == 0:  # t^r = p^(-r a / b) is an exact rational
            y_lo = y_hi = Fraction(1, p ** (depth * a // b))
        else:
            y_lo, y_hi = from_fixed(t_lo) ** depth, from_fixed(t_hi) ** depth
        f_lo, f_hi = log_enclosure(1 - y_hi, 1 - y_lo)  # log(1 - y), increasing in 1 - y
        if delta > 0:
            fac_lo, fac_hi = delta * f_lo, delta * f_hi
        else:
            fac_lo, fac_hi = delta * f_hi, delta * f_lo
        g_lo, g_hi = log_enclosure(bg["low"], bg["high"])
        h_lo, h_hi = log_enclosure(bh["low"], bh["high"])
        log_low += fac_lo + g_lo - h_hi
        log_high += fac_hi + g_hi - h_lo
    k_low, k_high = exp_enclosure(log_low - prime_tail, log_high + prime_tail)
    text = lambda x: f"{x.numerator}/{x.denominator}" if x.denominator < 10 ** 12 else None
    return {
        "s": f"{a}/{b}", "q": f"{q.numerator}/{q.denominator}", "first_depth": depth, "delta": f"{delta.numerator}/{delta.denominator}",
        "primes_kept": len(primes), "cutoff": f"{n_root}^{b}", "radius": text(radius),
        "omitted_prime_constant": float(constant), "omitted_prime_log_bound": float(prime_tail),
        "finite_product_log_interval": [float(log_low), float(log_high)],
        "log_k_interval": [float(log_low - prime_tail), float(log_high + prime_tail)],
        "k_interval": [float(k_low), float(k_high)],
        "k_interval_exact_dyadic": [str(from_fixed(to_fixed(k_low, False))), str(from_fixed(to_fixed(k_high, True)))],
        "max_height_used": max_height, "total_height_tail": float(local_error),
        "arithmetic": f"fixed point with {BITS} fractional bits, outward rounding",
    }
