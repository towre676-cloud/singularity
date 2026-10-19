# Program design: targets, populations, operations, and experiments

## The central object

An experiment program consists of a population of original candidates, a requested target, legal interventions, observation semantics, uncertainty, and cost. It may be finite and exact, continuous with certified bounds, or a restricted algebraic family. The backend must declare which class it supports. There is no claim of a universal algorithm deciding arbitrary nonlinear identification problems.

Write an original candidate as \(c\in\Omega\), its hidden state as \(x\), and its target as \(T(c,x)\). The target can be fault identity, a material property, a graph coefficient, a future wind functional, a period combination, or a movement-response contrast. Candidate identities and their multiplicities survive every compiled representation. A quotient preserving one target need not preserve another.

For a fixed experiment or terminating policy \(\pi\), define \(\mathcal Y_c^\pi\) as the complete set of possible observation transcripts under the declared model and uncertainty. Zero-error target identification is possible exactly when the transcript sets for target-incompatible candidates are disjoint. This formulation covers scalar intervals, joint zonotopes, finite noisy channels, and properly bounded stateful histories, but each needs its own effective decision method.

## Linear observable closure

In the exact finite-dimensional sector, states lie in \(V\), interventions are \(M_i\), and direct output rows form \(L\). The least future-observation space is

\[
W=\operatorname{span}\{\ell M_{i_k}\cdots M_{i_1}:\ell\in L,\ k\ge0\}.
\]

Finite dimension supplies an exact stopping rule: retain independent rows until every generator extension lies in their span. If basis rows form \(B\), return factorizations \(L=AB\) and \(BM_i=T_iB\). They certify that the quotient keeps every observation in the allowed language. Invisible vectors are \(\ker B\). This minimality is linear and relative to the formal state space and declared language. A restricted graph-realizable population can admit additional nonlinear or combinatorial compression.

Chronological words act on states with the latest matrix on the left. Every returned experiment must carry a chronological witness and be replayed in that convention. Parallel graph attachments commute, so they alone cannot reveal an ordering bug. Retain asymmetric/noncommuting examples as regression evidence.

## Costs and robustness are distinct

Positive attachment costs make affordable exact row search finite after rational costs are scaled to integer units. Cost-ordered span pruning preserves the cheapest nonzero distinction because a discarded row and every extension are combinations of no-more-expensive retained rows. It does not preserve the largest margin, best conditioning, or best noise amplification. Robust search requires those quantities explicitly.

For independent scalar error intervals, experiment \(e\) covers pair \(a,b\) when \(\lvert r_{e,a}-r_{e,b}\rvert>\rho_{e,a}+\rho_{e,b}\). Equality leaves a shared endpoint and is not separation. A finite panel is a weighted pair-cover problem under this geometry. Joint correlated panels instead compare complete sets; they can succeed even when every coordinate fails its individual interval test. Do not use scalar set cover as a substitute for joint convex separation.

Installation cost, intervention cost, observation cost, setup computation, per-query computation, and arithmetic bit cost should be recorded separately. Combining them requires declared conversion weights. Current thermal cost units are normalized accounting units, not measured money or electricity. A low per-query cost does not establish a setup-inclusive advantage before the break-even number of uses.

## Uncertainty contracts

Separate source-model discrepancy, discretization/transformation error, reduction residual, machine arithmetic, initial-state uncertainty, process disturbance, and sensor error. Add scalar bounds only after they refer to the same output and units. Preserve correlation when a nuisance is fixed across observations. Allow independent nuisance values in alternative candidate explanations unless a shared cross-hypothesis relation is independently known.

The thermal baseline starts at zero excess-temperature centre with a bounded reset box. Reset occurs independently before every panel member. A shared physical history has different semantics and cannot reuse the reset Bellman equation. The latter needs beliefs retaining original identity, possible current state, persistent nuisance, and the entire information prefix.

Uniform identification over continuous severity is generally impossible when every fault family approaches nominal at severity zero. Either bound severity away from zero, estimate a target interval, or return an unresolved class. A model-rejection outcome means no declared candidate fits; it does not guarantee detection of every possible unmodelled fault.

## Algebraic parameters and fibres

A parameter observation map \(\Phi_E(\theta)\) identifies target \(T(\theta)\) only when the target is constant on each admissible fibre. The tangent inclusion \(\ker D\Phi_E\subseteq\ker DT\) is a local necessary diagnostic in regular settings. It does not remove disconnected global branches. Quadratic targets on affine fibres admit explicit linear and Hessian conditions; curved fibres require the constraint geometry as well.

For a polynomial observation matrix, determine exceptional rank using the full determinantal ideal or its one-variable divisors. A selected basis determinant can vanish while another basis retains full rank. Denominators, excluded singular loci, and real parameter domains belong to the result. An algebraic root outside the declared interval is not an experimental obstruction inside it.

## Dynamic and differential extension

Physical-time linear responses have rational generating functions because a finite transition matrix advances time. An untruncated graph-height coefficient sequence need not have that transition structure and is not made rational by this analogy. Effective finite-prefix results need a closed recurrence, finite algebraic argument, or equivalent advance operator; coefficient-vector finiteness at one truncation is insufficient.

For parameter-dependent systems \(x'=A(t)x\), moving coordinates \(z=B(t)x\) are exact when \(B'+BA=TB\). Target recovery also requires \(c=LB\). Gauge changes \(z\mapsto G(t)z\) add the derivative term \(G'G^{-1}\) to the reduced connection. These equations make the quotient/transport bridge precise on constant-rank regular charts. Exceptional points require stratification rather than a fictional fixed-rank global bundle.

## Four kinds of result

Keep established mathematical background, proved project statements, exact finite computations, and proposed research targets explicit. A finite negative graph search is scoped to its population. A conditional external arithmetic result keeps its premise. A synthetic diagnostic result is not an empirical physical advantage. A held-out negative prediction result must not be relabelled as an advantage because a new feature is elegant.

The package's worked examples establish understanding and provide initial regression targets. They do not replace the full packet acceptance criteria. A roadmap tool verifies dependency and evidence-record consistency; it cannot make a future theorem true or validate a physical source model.

## Recommended outcome

For every accepted unit, leave a compact exact statement, an explanation in human sentences, the implementation and proposed/actual API distinction, a meaningful independent comparison, bounded retained evidence, and the effect on the full program. The eventual product answers a practical question: which action or measurement changes the target uncertainty enough to justify its total cost?
