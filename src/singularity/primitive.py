"""Primitive normalized height populations and exact scaling inversion."""
from collections import Counter
from functools import reduce
from math import gcd


def mobius(n):
    if type(n) is not int or n < 1:
        raise ValueError("positive integer required")
    sign=1; p=2
    while p*p <= n:
        if n%p == 0:
            n//=p; sign=-sign
            if n%p == 0:
                return 0
        p+=1
    return -sign if n>1 else sign


def primitive_marked_coefficients(graph, max_volume):
    """Recover gcd-one normalized profiles from full marked counts by inversion."""
    from .heights import marked_coefficients
    full=marked_coefficients(graph,max_volume)
    result=Counter()
    for (volume,energy,span),count in full.items():
        if volume == 0:
            continue
        for d in range(1,max_volume//volume+1):
            mu=mobius(d)
            if mu:
                result[volume*d,energy*d*d,span*d]+=mu*count
    if any(value<0 for value in result.values()):
        raise ArithmeticError("primitive inversion produced a negative multiplicity")
    return dict(sorted((key,value) for key,value in result.items() if value))


def direct_primitive_marked_coefficients(graph,max_volume):
    """Independent gcd-filtered enumeration, useful as a small-instance oracle."""
    from .heights import weak_compositions
    result=Counter()
    for volume in range(1,max_volume+1):
        for a in weak_compositions(volume,graph.n):
            if min(a)==0 and reduce(gcd,a)==1:
                result[volume,graph.energy(a),max(a)]+=1
    return dict(sorted(result.items()))


def recompose_primitive_counts(primitive,max_volume):
    """Return B coefficients including the unique zero profile."""
    result=Counter({(0,0,0):1})
    for (volume,energy,span),count in primitive.items():
        if volume<1 or count<0:
            raise ValueError("nonzero primitive profiles and nonnegative counts required")
        for d in range(1,max_volume//volume+1):
            result[volume*d,energy*d*d,span*d]+=count
    return dict(sorted((key,value) for key,value in result.items() if value))
