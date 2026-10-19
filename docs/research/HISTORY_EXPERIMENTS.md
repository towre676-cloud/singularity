# NX06: experiments retaining physical history and original identity

This track provides an exact finite-world bounded-horizon planner and an exact
small rational affine-conditioning backend. It distinguishes continuing a
physical trajectory from buying independent reset experiments. It also records
the original target even when actions erase the current distinction.

## Original-world finite semantics

`HistoryWorld` consists of an original ID, immutable target and current state.
`HistoryBelief` stores all possible such worlds and the action/observation
transcript. `HistoryModel` specifies legal action names, per-world transition
relations, measurement maps, positive exact action costs and reading costs.
Transitions may be nondeterministic. An action missing from any currently
possible world is infeasible, rather than a measurement that happens not to
distinguish the candidates.

`advance_belief` applies the transition relation to every possible world while
preserving its original ID and target. Equal current states with different
original IDs remain separate. Duplicate paths reaching the same original ID,
target and current state may merge because their future finite semantics are
identical and no probabilistic path multiplicity is being inferred.
`condition_belief` intersects with the exact displayed measurement equation.
An empty intersection is model rejection, not identification.

For the erase fixture, original states zero and one have targets zero and one.
Erasure maps both current states to zero. The correct belief still contains two
original targets, and all later identity or erase actions retain the ambiguity.
An observation before erasure identifies the target. The test independently
enumerates every four-action word and compares literal original-world evolution
with the belief updates; a current-state-only implementation would fail it.

## Complete bounded-horizon policy search

`history_policy_search` considers every legal control action and every available
measurement at each belief. A control has one successor belief containing all
possible transitioned worlds. A measurement branches on every displayed
possible output. The adversary selects the most expensive possible branch;
the solver chooses the cheapest action or measurement. Terminal beliefs have a
single original target, and nonterminal zero-horizon beliefs are impossible.

**SNG-NX06-01.** The returned value is the exact minimax value among policies
whose combined controls and readings have length at most the declared horizon.
Proof is induction on that finite horizon: the first step must be one of the
enumerated legal actions or measurements, and each successor is solved exactly
at the preceding horizon. This is not an unbounded-history completeness claim.
Positive costs do not themselves supply an infinite-history stopping theorem.

The cache key includes the complete current original-world possibilities and
remaining horizon. The default state ceiling is explicit. The certificate
checker regenerates every successor, verifies every possible observation
branch, checks original-target leaves and maximum path cost, and recomputes the
bounded optimum before accepting the optimality claim. Cyclic purported trees
are rejected. No successful sample path substitutes for all-branch validation.

## Exact rational affine conditioning

For small continuous worlds, `AffineHistoryWorld` stores

\[
x_t=c_t+G_tz,\qquad H_tz\le h_t.
\]

The latent labels distinguish persistent gain/calibration and each reset-local
initial quantity. This representation is a constrained affine image, not an
ordinary zonotope posterior. `latent_box_world` initializes exact [-1,1] bounds.
For a known candidate matrix A and nominal heater b, with an optional affine
heater-generator matrix B, control u gives

\[
c_{t+1}=Ac_t+bu,\qquad G_{t+1}=AG_t+Bu.
\]

This is exact when the uncertain heater dependence is affine in the same
latents. The module does not silently linearize an uncertain transition matrix
times an uncertain state, which would generally be nonlinear.

An observation y with sensor C and independently fresh bounded error epsilon
adds the two inequalities

\[
C G_tz\le y-Cc_t+\epsilon,\qquad
-C G_tz\le -y+Cc_t+\epsilon.
\]

Eliminating the fresh sensor-error variable into this strip is exact because
each error may independently take any value in its closed interval. The
persistent latent variables and all earlier strips remain. The rational
polytope solver from NX02 returns a feasible latent witness or exact Farkas
infeasibility certificate, subject to its row budget.

`affine_reset` replaces the current state while preserving original identity
and all prior constraints on persistent latents. Fresh reset-local coordinates
may be appended with new labels and independent box inequalities. Reusing a
fresh label is rejected. Old latent coordinates may cease to affect the current
state but are not confused with a new draw or with a changed original target.

## Shared-gain example and robustness

For x'=a x+g u, a in {1/2,3/4}, g in [1,2] and x_0=0, the pulse-then-wait
transcript is (g,ag). Observing y_1=6/5 and then y_2=3/5 leaves only a=1/2.
The exact conditioning certificate preserves the gain learned at the first
reading. A final-only value 9/10 is compatible with both candidates at different
gains, so an independently redrawn gain or a current-output interval alone
would lose the distinction.

The contrast y_2-y_1/2 is zero for a=1/2 and at least 1/4 for a=3/4. Error delta
in each reading gives support at most 3delta/2 in either candidate world.
Thus delta<1/12 is sufficient for robust joint separation. The receipt stores a
strict rational contrast at delta=1/100 and a final-only overlap witness, each
checked under independent nuisance values between hypotheses. Noncommuting
pulse/wait order and a fresh reset-local variable are independent test fixtures.

## Fair four-by-four thermal pilot

Three original models are used: nominal, left blocked bond and right blocked
bond. All control transitions for the complete language of at most two inputs
from {0,2} are built and independently checked by undirected neighbour flux.
Left and right center sensors each cost two; waiting costs one; a heating step
costs two including elapsed and heating; initial setup costs two. Initial state
and measurement error are exactly zero for this finite-policy comparison.

The exact shared-history optimum is seven action/reading units plus the single
setup cost two, total nine. The separately reset panel optimizer is supplied
every word in precisely the same at-most-two-control language and the same two
sensors. Its optimum is fourteen. The comparison does not grant the history
planner a longer word or more powerful sensor. The saving comes from retaining
the heated physical state between the two readings and paying setup/heating
once. No measured laboratory savings or robustness outside the declared exact
model are claimed.

A separately retained fixed schedule pulses once, waits twice and reads both
sensors at every time. Its six readings cost eighteen when the trajectory is
shared, versus forty-two for reproducing each reading as an independent reset
experiment. This is a cost-accounting comparison, separate from the optimized
two-control policy. The complete intermediate trajectories match the same
source-independent flux oracle.

Run `PYTHONPATH=src python scripts/history_thermal.py --check`. Evidence includes
the bounded policy, full original-world states and every branch, reset/cost
convention, intermediate readings, shared-gain overlap/separation certificates,
source digest and rational arithmetic/work limits.
