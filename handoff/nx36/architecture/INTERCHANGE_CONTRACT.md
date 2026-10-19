# Shared exact interchange and experiment semantics

## Purpose

The packets propose several future APIs. This document is authoritative for shared NX interchange fields so that individually sensible implementations do not become mutually incompatible. Existing upstream schemas retain their established encodings. Import them through explicit validated adapters rather than silently renaming or weakening them.

## Exact numbers and matrices

Portable NX JSON represents a rational by `[numerator, denominator]`, both JSON integers, denominator strictly positive, greatest common divisor one, and zero represented as `[0,1]`. Reject booleans, floats, nonfinite values, duplicate keys, zero denominators, and noncanonical pairs in exact fields. Human-facing tables can display fractions normally. An upstream rational string or numerator/denominator object can be accepted by a named adapter with strict round-trip tests; it is not the same wire format.

A rational matrix records row and column counts and a rectangular list of rational entries. Empty dimensions need explicit shape rather than inference from an empty list. A positive-definite metric, positive-semidefinite form, covariance matrix, and arbitrary symmetric matrix are distinct semantic types even when their storage is identical. State the norm or uncertainty set a matrix represents.

For polynomial or rational-function values, record the coefficient field, variable order, exact coefficient encoding, sparse or dense convention, denominator, and excluded domain. An identity after denominator clearing is valid only where the original expressions are defined. Algebraic numbers need a defining polynomial and an isolating specification; a decimal approximation is not an exact algebraic identifier.

## Identity and populations

Candidate IDs refer to original configurations, not compiled aliases. Store target labels and reconstruction maps separately. If several configurations share a state or observation, retain their multiplicities. A count is not a posterior probability unless weights or a prior are declared. A finite population description must actually bound every free variable.

Models have source revisions and a semantic identity including parameter values, normalization, state ordering, boundary type, input and sensor maps, and units. A digest binds bytes; a mathematical source map explains what those bytes mean. No certificate can infer a physical calibration guarantee merely from a hash.

## Words, policies, and reset

Store intervention words in chronological order. For linear state maps the last operation acts on the left: word `[a,b]` sends a state to `M_b M_a v`. Observation rows and retained witnesses must use the same convention. List legal source and target types when an action changes the boundary or state space.

Every panel or policy records whether each experiment independently resets, continues from the preceding physical state, or uses a specified partial reset. Fixed calibration nuisances may persist across readings. Initial target labels remain attached to candidates after destructive actions. A current state alone is insufficient for a history-sensitive identification claim.

## Error geometry

An independent scalar interval, a joint box, a zonotope, an ellipsoid, and a stochastic likelihood are different contracts. A persistent common offset is not two fresh independent errors. Cross-candidate explanations generally quantify their unknown nuisance parameters independently. Within one candidate history, preserve the correlation assumptions actually justified by the model.

For ellipsoid shape matrix R, the convention is `eta^T R^-1 eta <= epsilon^2`, with R positive definite. Whitened observation weighting is therefore R^-1. If R is instead a precision matrix, label it explicitly and change the formulas. For movement signatures, the antisymmetric level-two statistic is twice the conventional signed area of the straight-line-closed path; retain that declared scale.

Strict separation excludes touching boundaries. Store open or closed parameter endpoints explicitly. Do not encode unresolved or unbounded results as JSON Infinity or a very large finite number; use a status with the applicable bounds and assumptions.

## Cost and optimization

Installation, reset, heating, switching, observation, setup computation, and repeated execution costs have named units. A combined objective records conversion coefficients and number of planned repetitions. Attachment costs are positive for the finite affordable-language guarantees; direct observation costs can be nonnegative where the theorem permits it.

An optimum names its search space: a supplied finite pool, every word up to a cost bound, a generated grammar, or a proved all-horizon family. A greedy result is a baseline. A feasible result is an upper bound. An independently checked lower bound is required to claim optimality. Exact span dependence supports cheapest nonzero distinction, not arbitrary noise-margin pruning.

## Progress evidence

The initial roadmap has 36 proposed tracks and 108 proposed units. Complete units need a nonempty evidence summary, existing repository-relative artifacts, actual check commands and scopes with successful exit codes, a commit, and a mathematical status. The handoff tool checks metadata consistency and evidence presence; it does not rerun arbitrary saved commands or decide whether the underlying research claim is true.

Supported statuses are `proposed`, `in_progress`, `blocked`, and `complete`. A track is complete exactly when its three units are complete. Mark blockers concretely. Preserve scoped negative results and counterexamples where allowed; do not manufacture completion by silently replacing a requested theorem with a weaker computation.
