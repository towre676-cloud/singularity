"""Exact geometry and finite-pool selection for polynomial experiments.

The integral metric observes an entire polynomial curve on a declared interval.
It is not a claim about a measurement at one fixed q: those are scalar samples
and can vanish even when the integral distance is positive. All scores are exact
rational numbers; no floating-point uncertainty is silently rounded away.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Mapping, Sequence


def _rational(value):
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError("expected an integer or Fraction")
    return Fraction(value)


def _vector(value, dimension=None):
    if isinstance(value, Mapping):
        if any(isinstance(k, bool) or not isinstance(k, int) or k < 0 for k in value):
            raise ValueError("polynomial exponents must be nonnegative integers")
        size = max(value, default=-1) + 1
        if dimension is not None and size > dimension:
            raise ValueError("vector exceeds metric dimension")
        result = tuple(_rational(value.get(i, 0)) for i in range(dimension or size))
    else:
        result = tuple(_rational(v) for v in value)
        if dimension is not None:
            if len(result) > dimension:
                raise ValueError("vector exceeds metric dimension")
            result += (Fraction(0),) * (dimension - len(result))
    return result


def monomial_gram(max_degree, a=0, b=1):
    degree = max_degree
    """Gram matrix of 1,q,...,q^degree in L2([a,b],dq)."""
    if isinstance(degree, bool) or not isinstance(degree, int) or degree < 0:
        raise ValueError("degree must be a nonnegative integer")
    a, b = _rational(a), _rational(b)
    if a >= b:
        raise ValueError("interval must have a < b")
    return tuple(tuple((b ** (i+j+1) - a ** (i+j+1)) / (i+j+1)
                       for j in range(degree+1)) for i in range(degree+1))


@dataclass(frozen=True)
class RationalMetric:
    """Positive definite rational Gram matrix, verified by exact LDL^T."""
    gram: tuple

    def __post_init__(self):
        gram = tuple(tuple(_rational(x) for x in row) for row in self.gram)
        n = len(gram)
        if not n or any(len(row) != n for row in gram):
            raise ValueError("metric must be a nonempty square matrix")
        if any(gram[i][j] != gram[j][i] for i in range(n) for j in range(n)):
            raise ValueError("metric must be symmetric")
        lower = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
        diagonal = []
        for j in range(n):
            pivot = gram[j][j] - sum(lower[j][k]**2 * diagonal[k] for k in range(j))
            if pivot <= 0:
                raise ValueError("metric must be positive definite")
            diagonal.append(pivot)
            for i in range(j+1, n):
                lower[i][j] = (gram[i][j] - sum(lower[i][k] * lower[j][k] * diagonal[k]
                                               for k in range(j))) / pivot
        object.__setattr__(self, "gram", gram)
        object.__setattr__(self, "lower", tuple(tuple(row) for row in lower))
        object.__setattr__(self, "diagonal", tuple(diagonal))

    @property
    def dimension(self):
        return len(self.gram)

    @property
    def ldl(self):
        return self.lower, self.diagonal

    def inner(self, left, right):
        left, right = _vector(left, self.dimension), _vector(right, self.dimension)
        return sum((left[i]*self.gram[i][j]*right[j]
                    for i in range(self.dimension) for j in range(self.dimension)), Fraction(0))

    inner_product = inner

    def squared_norm(self, value):
        return self.inner(value,value)

    def distance_squared(self, left, right):
        left, right = _vector(left, self.dimension), _vector(right, self.dimension)
        difference = tuple(a-b for a,b in zip(left,right))
        return self.inner(difference, difference)

    def pullback(self, transform):
        """Return T^T G T for an injective coordinate map old_vector=T*new_vector."""
        transform = tuple(tuple(_rational(x) for x in row) for row in transform)
        if len(transform) != self.dimension or not transform or not transform[0]:
            raise ValueError("transform has wrong dimensions")
        width = len(transform[0])
        if any(len(row) != width for row in transform):
            raise ValueError("transform is ragged")
        return RationalMetric(tuple(tuple(sum((transform[i][k]*self.gram[i][j]*transform[j][l]
                    for i in range(self.dimension) for j in range(self.dimension)), Fraction(0))
                    for l in range(width)) for k in range(width)))


def integral_inner_product(left, right, a=0, b=1):
    left, right = _vector(left), _vector(right)
    n = max(len(left), len(right), 1)
    return RationalMetric(monomial_gram(n-1,a,b)).inner(left,right)


def integral_distance_squared(left, right, a=0, b=1):
    left, right = _vector(left), _vector(right)
    n = max(len(left), len(right), 1)
    return RationalMetric(monomial_gram(n-1,a,b)).distance_squared(left,right)


@dataclass(frozen=True)
class OrthogonalPolynomialBasis:
    polynomials: tuple
    norms_squared: tuple
    a: Fraction
    b: Fraction

    @property
    def metric(self):
        return RationalMetric(tuple(tuple(self.norms_squared[i] if i == j else Fraction(0)
                                         for j in range(len(self.polynomials)))
                                    for i in range(len(self.polynomials))))

    def coordinates(self, polynomial):
        metric = RationalMetric(monomial_gram(len(self.polynomials)-1,self.a,self.b))
        return tuple(metric.inner(polynomial,p)/norm
                     for p,norm in zip(self.polynomials,self.norms_squared))

    def polynomial(self, coordinates):
        coordinates = _vector(coordinates,len(self.polynomials))
        return tuple(sum((coordinates[j]*self.polynomials[j][i]
                          for j in range(len(coordinates))),Fraction(0))
                     for i in range(len(coordinates)))


def orthogonal_polynomial_basis(max_degree, a=0, b=1):
    """Monic exact Gram-Schmidt polynomials, padded ascending coefficient rows."""
    metric = RationalMetric(monomial_gram(max_degree,a,b))
    basis = []
    for k in range(max_degree+1):
        p = [Fraction(int(i == k)) for i in range(max_degree+1)]
        for previous in basis:
            coefficient = metric.inner(p,previous) / metric.inner(previous,previous)
            for i,c in enumerate(previous):
                p[i] -= coefficient*c
        basis.append(tuple(p))
    return OrthogonalPolynomialBasis(tuple(basis),tuple(metric.inner(p,p) for p in basis),
                                     _rational(a),_rational(b))


@dataclass(frozen=True)
class Separation:
    delta_squared: Fraction
    closest_pairs: tuple

    @property
    def squared(self):
        return self.delta_squared

    def guarantees_identification(self, noise):
        noise = _rational(noise)
        if noise < 0:
            raise ValueError("noise must be nonnegative")
        return 4*noise*noise < self.delta_squared


def minimum_separation(candidates, metric):
    """Smallest pair distance and all pairs attaining it."""
    items = list(candidates.items()) if isinstance(candidates, Mapping) else list(enumerate(candidates))
    if len(items) < 2:
        raise ValueError("at least two candidates are required")
    distances = [(metric.distance_squared(v,w),(a,b))
                 for (a,v),(b,w) in combinations(items,2)]
    delta = min(distance for distance,pair in distances)
    return Separation(delta,tuple(pair for distance,pair in distances if distance == delta))


@dataclass(frozen=True)
class NearestCandidate:
    nearest_labels: tuple
    squared_distance: Fraction
    separation: Separation
    error_bound_squared: Fraction | None
    within_declared_error: bool
    margin_guarantee: bool
    certified_unique: bool


def nearest_candidate(observation, candidates, metric, *, error_bound_squared=None):
    """Report nearest labels, ties, and a guarantee tied to a declared error ball.

    A separated candidate family alone is insufficient: the observation must
    also lie in the declared error ball of a candidate for certified recovery.
    """
    items = list(candidates.items()) if isinstance(candidates, Mapping) else list(enumerate(candidates))
    separation = minimum_separation(candidates,metric)
    distances = [(metric.distance_squared(observation,v),label) for label,v in items]
    best = min(distance for distance,label in distances)
    labels = tuple(label for distance,label in distances if distance == best)
    if error_bound_squared is not None:
        error_bound_squared = _rational(error_bound_squared)
        if error_bound_squared < 0:
            raise ValueError("error_bound_squared must be nonnegative")
    within = error_bound_squared is not None and best <= error_bound_squared
    margin = error_bound_squared is not None and 4*error_bound_squared < separation.delta_squared
    return NearestCandidate(labels,best,separation,error_bound_squared,within,margin,
                            len(labels) == 1 and within and margin)


@dataclass(frozen=True)
class Experiment:
    name: str
    observations: object
    metric: RationalMetric
    cost: Fraction = Fraction(1)
    noise_squared: Fraction = Fraction(1)

    def __post_init__(self):
        cost, noise = _rational(self.cost), _rational(self.noise_squared)
        if cost <= 0 or noise <= 0:
            raise ValueError("cost and noise_squared must be positive")
        if not isinstance(self.metric,RationalMetric):
            raise TypeError("metric must be RationalMetric")
        minimum_separation(self.observations,self.metric)
        object.__setattr__(self,"cost",cost)
        object.__setattr__(self,"noise_squared",noise)


@dataclass(frozen=True)
class ExperimentScore:
    name: str
    separation: Separation
    cost: Fraction
    noise_squared: Fraction
    score: Fraction
    robust: bool


def rank_experiments(experiments):
    """Rank a finite pool by delta_squared/(cost*noise_squared), greatest first.

    This optimizes only this explicit pool; it does not search all realizable
    attachment words or solve a shared-panel experiment-design problem.
    """
    experiments = tuple(experiments)
    if any(not isinstance(item,Experiment) for item in experiments):
        raise TypeError("expected Experiment instances")
    names = [item.name for item in experiments]
    if len(set(names)) != len(names):
        raise ValueError("experiment names must be unique")
    def labels(observations):
        return set(observations) if isinstance(observations,Mapping) else set(range(len(observations)))
    if experiments and any(labels(item.observations) != labels(experiments[0].observations)
                           for item in experiments):
        raise ValueError("experiments must use the same candidate labels")
    scores = []
    for item in experiments:
        separation = minimum_separation(item.observations,item.metric)
        scores.append(ExperimentScore(item.name,separation,item.cost,item.noise_squared,
                    separation.delta_squared/(item.cost*item.noise_squared),
                    4*item.noise_squared < separation.delta_squared))
    return tuple(sorted(scores,key=lambda item:(-item.score,item.name)))
