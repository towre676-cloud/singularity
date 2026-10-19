"""NX32 gauge-covariant, chronological exact continuation experiments."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product
from .observability import (OperatorSystem, apply_word, experiment,
    observable_closure, minimum_distinguishing_experiment, verify_certificate)
from .period_observations import _backend, _q


def _inverse(matrix):
    n = len(matrix)
    a = [list(map(_q, row)) + [Q(i == j) for j in range(n)]
         for i, row in enumerate(matrix)]
    if any(len(row) != 2*n for row in a):
        raise ValueError("square gauge required")
    for j in range(n):
        p = next((i for i in range(j, n) if a[i][j]), None)
        if p is None:
            raise ValueError("invertible gauge required")
        a[j], a[p] = a[p], a[j]
        v = a[j][j]; a[j] = [x/v for x in a[j]]
        for i in range(n):
            if i != j:
                v = a[i][j]; a[i] = [x-v*y for x, y in zip(a[i], a[j])]
    return tuple(tuple(row[n:]) for row in a)


def _mul(a, b):
    return tuple(tuple(sum((x*y for x, y in zip(row, col)), Q(0))
                       for col in zip(*b)) for row in a)


@dataclass(frozen=True)
class MonodromyLanguage:
    system: OperatorSystem
    basepoint: str
    basis: str
    loops: tuple
    source_revision: str
    geometric: bool = False

    def __init__(self, matrices, observations, *, costs=None, observation_costs=None,
                 basepoint="algebraic-toy", basis="declared-rational-basis",
                 loops=None, source_revision="explicit-input", geometric=False):
        matrices = tuple(tuple(tuple(map(_q, row)) for row in m) for m in matrices)
        n = len(matrices[0]) if matrices else len(observations[0])
        system = OperatorSystem(n, matrices, observations, costs, observation_costs)
        # Continuation along a loop is an isomorphism of its local-system
        # fiber, including in the standalone algebraic examples. Singular
        # actions belong to OperatorSystem, not a monodromy language.
        for matrix in system.operators:
            _inverse(matrix)
        if any(not isinstance(v, str) or not v for v in (basepoint,basis,source_revision)):
            raise ValueError("nonempty source, basepoint and basis identifiers required")
        labels = tuple(loops if loops is not None else (f"loop-{i}" for i in range(len(matrices))))
        if len(labels) != len(matrices) or len(set(labels)) != len(labels):
            raise ValueError("one distinct description per allowed loop required")
        if type(geometric) is not bool:
            raise TypeError("geometric flag must be bool")
        for name, value in (("system",system),("basepoint",basepoint),("basis",basis),
                            ("loops",labels),("source_revision",source_revision),("geometric",geometric)):
            object.__setattr__(self,name,value)

    def closure(self):
        cert = observable_closure(self.system)
        if not verify_certificate(self.system, cert):
            raise ArithmeticError("all-word closure failed replay")
        return cert

    def reading(self, state, observation, word=()):
        state = apply_word(self.system, state, word)
        return sum((x*y for x,y in zip(self.system.observations[observation],state)),Q(0))

    def cheapest(self, difference):
        witness = minimum_distinguishing_experiment(self.system,difference)
        if witness is not None:
            if self.reading(difference,witness.observation,witness.word) == 0:
                raise ArithmeticError("chronological witness replay failed")
        return witness

    def with_inverses(self, inverse_costs):
        inverse_costs=tuple(map(_q,inverse_costs))
        if len(inverse_costs)!=len(self.loops) or any(c<=0 for c in inverse_costs):
            raise ValueError("every inverse requires its own positive cost")
        return MonodromyLanguage(self.system.operators+tuple(_inverse(m) for m in self.system.operators),
            self.system.observations,costs=self.system.attachment_costs+inverse_costs,
            observation_costs=self.system.observation_costs,basepoint=self.basepoint,basis=self.basis,
            loops=self.loops+tuple(v+"^-1" for v in self.loops),source_revision=self.source_revision,
            geometric=self.geometric)

    def gauge(self, matrix, basis):
        s=tuple(tuple(map(_q,row)) for row in matrix);inv=_inverse(s)
        n=self.system.dimension
        if len(s)!=n:
            raise ValueError("gauge dimension mismatch")
        return MonodromyLanguage(tuple(_mul(_mul(s,m),inv) for m in self.system.operators),
            _mul(self.system.observations,inv),costs=self.system.attachment_costs,
            observation_costs=self.system.observation_costs,basepoint=self.basepoint,basis=basis,
            loops=self.loops,source_revision=self.source_revision,geometric=self.geometric)


def bounded_robust_experiments(language, difference, budget, radius, max_words=100000):
    """Complete finite cost language; no rank pruning for robust amplitudes."""
    budget,radius=_q(budget),_q(radius)
    if budget<0 or radius<0 or type(max_words)is not int or max_words<1:
        raise ValueError("nonnegative budget/radius and positive work limit required")
    out=[];stack=[((),Q(0))];nodes=0
    while stack:
        word,cost=stack.pop();nodes+=1
        if nodes>max_words:
            raise ValueError("bounded loop population exceeds max_words")
        for j,gamma in enumerate(language.system.observation_costs):
            if cost+gamma<=budget:
                value=language.reading(difference,j,word)
                out.append((cost+gamma,word,j,value,abs(value)>2*radius))
        for i,c in enumerate(language.system.attachment_costs):
            if cost+c+min(language.system.observation_costs,default=Q(0))<=budget:
                stack.append((word+(i,),cost+c))
    return tuple(sorted(out,key=lambda r:(r[0],len(r[1]),r[1],r[2])))


def marked_legendre_loops(*, order=16, rounding_bits=96):
    """Actual integral-cycle monodromy, recognized only under the source marking.

    The independent continuation uses rational Cauchy/Gronwall enclosures.  The
    integral cycle premise is explicit in each source receipt; proximity alone
    is not claimed to establish integrality.
    """
    paths=(['1/2',[0,'1/2'],'-1/2',[0,'-1/2'],'1/2'],
           ['1/2',[1,'-1/2'],'3/2',[1,'1/2'],'1/2'])
    engine=_backend("period_matrix_balls")
    receipts=tuple(engine.marked_legendre_monodromy(p,order=order,rounding_bits=rounding_bits)
                   for p in paths)
    language=MonodromyLanguage(tuple(r['monodromy'] for r in receipts),((1,0),),
        basepoint="t=1/2",basis="standard integral Legendre a,b cycles; periods/(2*pi)",
        loops=("counterclockwise loop about 0","counterclockwise loop about 1"),
        source_revision="pinned-PerfectPower-period_matrix_balls.py",geometric=True)
    return language,paths,receipts
