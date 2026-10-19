# Operator, experiment and periodic interfaces, version 1

**Identifier:** `singularity.operators/1`. **Status:** frozen for release 0.3.0. **Scope:** the public functions of `observability.py`, `graph_experiments.py`, `experiment_design.py` and `periodic.py`. The mathematics, proofs and limitations are in [Chapter 15](../chapters/15_operators_experiments.md).

## 1. Exact input contract

Public numbers are `int` or `fractions.Fraction`.

- **TypeError** for `bool`, `float`, `str` and other non-exact types. This holds for dimensions, indices, matrix and vector entries, costs, `q`, phase exponents and moduli.
- **ValueError** for the right type with the wrong value or shape: negative dimension, out-of-range index, ragged matrix, nonpositive attachment cost, negative observation cost, `q` outside \((0,1)\), modulus below one, a phase on a non-edge, or an exceeded work budget.
- **Portable replay** (`replay_bundle`) raises ValueError for every malformed bundle.

No function changes the normalization of local coefficients. Graph states use raw labeled counts on nonnegative heights.

## 2. `singularity.observability`

| Object | Contract |
|---|---|
| `OperatorSystem(dimension, operators, observations, attachment_costs=None, observation_costs=None)` | Frozen. States are columns. Defaults: attachment cost 1 for every generator, observation cost 0 for every row. Attachment costs must be positive and observation costs nonnegative. Dimension 0 and empty families are allowed. |
| `experiment(system, observation, word=())` | Returns `Experiment(observation, word, row, cost)`. The word is chronological, and the row is \(L_jM_{i_m}\cdots M_{i_1}\). |
| `apply_word(system, state, word=())` | Returns \(M_{i_m}\cdots M_{i_1}v\). |
| `observable_closure(system)` | Returns a `ClosureCertificate`: basis experiments in nondecreasing cost, `observation_coordinates` \(A\), `transition_coordinates` \(T_i\), canonical `nullspace` of \(\ker B\), and RREF `pivots`. |
| `verify_certificate(system, certificate)` | Exact replay of SNG-O01 to SNG-O03 without rediscovery. Returns False, never raises, on any defect, including inexact types such as `0.0` or `False` in place of `Fraction(0)`. |
| `quotient_state(system, certificate, state)` | \(y=Bv\). Verifies the certificate first. |
| `quotient_update(certificate, operator, y)`, `quotient_output(certificate, y)` | \(T_iy\) and \(Ay\). |
| `future_equivalent(system, first, second, certificate=None)` | Equality of quotient states. |
| `minimum_distinguishing_experiment(system, difference, certificate=None)` | The globally cheapest experiment nonzero on the difference within the declared language, or `None` if the states are future-equivalent. It does not maximize the signal. |
| `certificate_bundle(system, certificate=None)`, `replay_bundle(bundle)` | Format `singularity.operator-closure/1`: rationals are reduced `[numerator, denominator]` pairs. Limits: dimension ≤ 128, at most 16 generators, at most 128 observations, words of length ≤ 256, integers of at most 4096 bits. |

## 3. `singularity.graph_experiments`

| Object | Contract |
|---|---|
| `ContextAttachment(name, graph, terminals=(0, 1), swap_automorphism=None)` | Rejects a terminal–terminal edge and checks that the declared or default permutation is a graph automorphism exchanging the terminals. Every attachment copies the interior freshly. |
| `standard_attachments()` | The pendant-leaf pair and the shared neighbour. |
| `BoundaryExperimentSystem(max_volume, q, attachments=None)` | Coordinates are \(((s,t),v)\) with \(s\le t\) and \(s+t\le v\le R\). Operators follow SNG-O05; there are \(R+1\) observation rows, one per volume. |
| `.compile_graph(graph, terminals)` | The raw symmetrized state of an arbitrary base block, which may be asymmetric. |
| `.observe(state, word)`, `.apply_word(state, word)` | Prediction through the compiled operators. |
| `.attached_graph(graph, terminals, word)`, `.direct_observations(graph, terminals, word)` | The actual glued graph and its local coefficients by direct height enumeration, as an independent check. |
| `.operator_system(attachment_costs=None, observation_costs=None)` | The compiled operators as an `OperatorSystem`. |

## 4. `singularity.experiment_design`

These functions use exact Gram matrices: `monomial_gram`, `RationalMetric` (positive definiteness checked by \(LDL^{\mathsf T}\)), `integral_inner_product`, `orthogonal_polynomial_basis`, `minimum_separation`, `nearest_candidate` and `rank_experiments`. `nearest_candidate(..., error_bound_squared=e2)` reports `certified_unique` only if all three hold: the nearest label is unique, it lies within the declared error ball, and \(4e_2<\delta^2\) (SNG-O07). Equality \(4e_2=\delta^2\) is never certified.

## 5. `singularity.periodic`

| Object | Contract |
|---|---|
| `PeriodicModel(graph, modulus, phases=None)` | The phase map sends sorted edge tuples to integer exponents; a missing edge has exponent 1. Exponents are stored unreduced. |
| `residue_numerator(model, max_profiles=10**6)` | \(P_0,\ldots,P_K\) as elements of \(\mathbb Z[t]/\Phi_M\), with a work budget of \(M^n\) profiles. |
| `series_from_numerator(model, numerator, max_volume)` | Expansion of \(P/(1-x^M)^n\). |
| `direct_coefficients(model, max_volume, max_profiles=10**6)` | An independent oracle that enumerates heights directly, without residues. |
| `is_palindromic`, `periodic_cutoff(n, M)` | \(\lfloor n(M-1)/2\rfloor\). |
| `compare_models(first, second)` | Needs equal \(n\) and \(M\). Returns `PeriodicComparison(cutoff, equal, first_difference, first_coefficient, second_coefficient)`. `equal=True` is a proof of full-series equality by SNG-O09. |

## 6. Margins, panels and compression (added after the 0.3.0 freeze)

| Module | Contract |
|---|---|
| `robust_search` | `bounded_margin_search(system, difference, noise, budget)` and `bounded_family_search(system, states, noise, budget)` return the exact bounded maximum of the normalized margin (SNG-O15), with `exhaustive_*` reference searches. The noise vector holds one positive rational per observation. Exceeding `max_nodes` raises ValueError and is not a mathematical result. |
| `panels` | `experiment_pool`, `minimum_cost_panel(pool, epsilon=None)` (exact branch-and-bound, worst-case exponential), `exhaustive_minimum_panel`, `greedy_panel` (heuristic), and box and Euclidean consistency decoders (SNG-O16). |
| `compression` | `independent_star`, `star_transition`, `reachable_subspace(system, states)` (Krylov closure of the transposed system), `cyclicity_certificate(system)` (the hypotheses of SNG-O13), `star_reconstruction(system)` (SNG-O14, verified on held-out alpha). |

## 7. Compatibility

- `quotient_state(system, certificate, state)` and `minimum_distinguishing_experiment(system, difference, certificate=None)` keep their checkpoint signatures.
- Certificates retained before this version replay unchanged. The retained R=4 certificate was regenerated with identical content; only its key order changed.
- The single behavioural change is in the verifier. Checkpoint certificates containing non-`Fraction` numbers are now rejected; no such certificate was retained.
