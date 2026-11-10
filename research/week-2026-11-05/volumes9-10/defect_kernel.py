"""Exact fixed-excess non-induced pattern kernels, Python standard library.

Compresses the particle partition formula onto exceptional vertices and
components of their deletion. No graph catalogue, cumulant or edge inversion.
Polynomials: exponent -> Fraction. Ambient degree d is explicit.
"""
from fractions import Fraction as Q
from itertools import combinations, product
from math import factorial, comb
from functools import lru_cache


def add(a, b, scale=1):
    out = dict(a)
    for e, c in b.items():
        out[e] = out.get(e, Q(0)) + scale*c
    return {e: c for e, c in out.items() if c}


def mul(a, b):
    out = {}
    for e, c in a.items():
        for f, d in b.items():
            out[e+f] = out.get(e+f, Q(0)) + c*d
    return {e: c for e, c in out.items() if c}


def compositions(n, k, positive=False):
    if not k:
        if not n:
            yield ()
        return
    start = int(positive)
    if k == 1:
        if n >= start:
            yield (n,)
        return
    for a in range(start, n-start*(k-1)+1):
        for tail in compositions(n-a, k-1, positive):
            yield (a,)+tail


@lru_cache(None)
def local_states(excess):
    return tuple(h for m in range(1, excess+2)
                 for h in compositions(excess+1, m, True))


def partitions(sites):
    """Set partitions of distinct particle labels, at most one per site/block."""
    blocks = []
    def visit(i):
        if i == len(sites):
            yield tuple(tuple(b) for b in blocks)
            return
        for b in blocks:
            if all(sites[j] != sites[i] for j in b):
                b.append(i)
                yield from visit(i+1)
                b.pop()
        blocks.append([i])
        yield from visit(i+1)
        blocks.pop()
    yield from visit(0)


def components(adj, deleted):
    unseen = set(range(len(adj))) - set(deleted)
    result = []
    while unseen:
        root = min(unseen)
        unseen.remove(root)
        todo, comp = [root], [root]
        while todo:
            u = todo.pop()
            for v in adj[u]:
                if v in unseen:
                    unseen.remove(v)
                    todo.append(v)
                    comp.append(v)
        result.append(tuple(comp))
    return tuple(result)


def geometric(w):
    """(z**w-1)/(z-1), including w=0."""
    return {j: Q(1) for j in range(w)}


def defect_kernel(k, edges, excess=3, ambient_degree=3):
    """[x**(k+excess)] B_H, for connected simple H with degree <= d.

    Valid as a Laurent polynomial for formal q. The public input is an
    ordinary edge list; no canonical mask convention is required.
    """
    for name, value, lower in (("k", k, 1), ("excess", excess, 0),
                                ("ambient_degree", ambient_degree, 0)):
        if type(value) is not int or value < lower:
            raise ValueError(name)
    es = []
    for edge in edges:
        if len(edge) != 2 or any(type(v) is not int for v in edge):
            raise ValueError("edge")
        u, v = sorted(edge)
        if not 0 <= u < v < k or (u, v) in es:
            raise ValueError("simple edge")
        es.append((u, v))
    es = tuple(sorted(es))
    adj = [set() for _ in range(k)]
    for u, v in es:
        adj[u].add(v)
        adj[v].add(u)
    if any(len(a) > ambient_degree for a in adj):
        raise ValueError("pattern exceeds ambient degree")
    if len(components(adj, ())) != 1:
        raise ValueError("connected pattern required")
    # q Laurent polynomial before multiplying the common (q^-2-1)^e.
    residual = {}
    if excess == 0:
        residual = {ambient_degree*k: Q(1)}
    for t in range(1, min(k, excess)+1):
        for X in combinations(range(k), t):
            xset = set(X)
            cs = components(adj, X)
            boundaries = [tuple((x, sum(v in adj[x] for v in c))
                                for x in X if any(v in adj[x] for v in c))
                          for c in cs]
            internal = [(u, v) for u, v in es if u in xset and v in xset]
            for allocation in compositions(excess, t, True):
                for states in product(*(local_states(a) for a in allocation)):
                    sites = tuple(x for x, h in zip(X, states) for _ in h)
                    heights = tuple(v for h in states for v in h)
                    denom = 1
                    for h in states:
                        denom *= factorial(len(h))
                    shift = ambient_degree*(k-t+sum(h*h for h in heights))
                    for pi in partitions(sites):
                        maps = [{sites[p]: heights[p] for p in b} for b in pi]
                        weight = {0: Q((-1)**(len(pi)-1)*factorial(len(pi)-1), denom)}
                        for u, v in internal:
                            w = sum(b.get(u, 0)*b.get(v, 0) for b in maps)
                            weight = mul(weight, geometric(w))
                            if not weight:
                                break
                        if not weight:
                            continue
                        for boundary in boundaries:
                            choices = {}
                            for b in maps:
                                option = {0: Q(1)}
                                for x, count in boundary:
                                    if x not in b:
                                        option = {}
                                        break
                                    g = geometric(b[x])
                                    for _ in range(count):
                                        option = mul(option, g)
                                choices = add(choices, option)
                            weight = mul(weight, choices)
                            if not weight:
                                break
                        residual = add(residual, {shift-2*j: c for j, c in weight.items()})
    e = len(es)
    common = {-2*j: Q(comb(e, j)*(-1)**(e-j)) for j in range(e+1)}
    return mul(common, residual)
