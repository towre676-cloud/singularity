# Operator experiment checkpoint

This is a recovered development checkpoint, not a completed new release. The original Vakil work is preserved at local commit 0ea8807; the recovered operator, graph and metric modules are committed at 09aa342. The previous published release is f88da95.

## What can be run

`singularity.observability` computes a rational invariant observation space with actual experiment words, exact cost-filtered closure identities, an annihilator, descended quotient operators, cheapest single distinguishing experiments and portable certificate replay. `singularity.graph_experiments` compiles swap-symmetric two-terminal contexts without terminal edges into truncated convolution operators. `singularity.experiment_design` supplies exact polynomial Gram metrics, monic orthogonal coordinates, finite-pool experiment scoring and nearest-candidate margins.

Fresh recovery checks reproduce dimension22 and observable rank22 at volume4 and q=1/2, and replay the saved exact certificate. On the three-vertex path with endpoints versus adjacent terminal placements, both direct volume-one readings agree. With pendant-pair cost2 and shared-neighbor cost1, the minimum-cost witness is one shared neighbor: volume-one readings1 and9/8. The restored metric module passes11 regression tests. The original Vakil snapshot passes272 tests. These statements do not substitute for the not-yet-restored complete operator regression suites.

## Why the certificate works

Let B contain independent rows of actual experiments, L the direct observation rows and M_i the permitted state operators. The certificate checks L=A B and B M_i=T_i B. Induction on every finite word puts every future observation in row(B). Conversely each row of B comes with its actual experiment word. Thus row(B) is exactly the completed observation space, without a horizon assumption. The invisible states are N=ker(B); the quotient coordinate y=Bv obeys y_next=T_i y and output A y. Any linear map preserving every future reading on the entire formal state space must have kernel contained in N, so at least rank(B) coordinates are necessary. This lower bound need not hold for nonlinear maps or physical graph families occupying a constrained subset.

For costs, a nonzero A[j,b] may use only a basis experiment of cost at most the seed observation cost. A nonzero T_i[a,b] may use only a basis experiment costing at most cost(a)+cost(i). Induction proves that every experiment of cost at most C lies in the span of basis rows of cost at most C. Therefore the cheapest retained row nonzero on a model difference is globally cheapest in the declared positive-additive-cost language. This does not optimize amplitude, a robustness threshold, or a shared experiment panel. Chronological words act on states as M_last ... M_first; extending a row on the right prepends a physical attachment.

For graph states, coordinates are [x^v]x^(s+t)K_plus(s,t), s<=t and s+t<=v<=R. Structural context symmetry gives K_C(s,t)=K_C(t,s), hence the update is multiplication by the ordered context kernel on each orbit. Nonnegative interior volumes make truncation stable under arbitrary word length. Fresh disjoint context interiors and absence of terminal-terminal edges preserve simple graphs under repeated attachment. The compiler uses raw kernels, not changing-order minimum-zero normalization.

## Metric and mathematical findings

For polynomial coefficient vectors on [0,1], the integral Gram matrix has G[i,j]=1/(i+j+1). The ordinary coefficient dot product is different. The path discrepancy polynomial is -q(1-q)^2; its squared integral is1/105, whereas its coefficient dot product is6. Orthogonal coordinates preserve the same integral geometry. For a declared finite candidate collection with minimum norm separation delta, error norm epsilon gives unique nearest-candidate identification when 4epsilon^2<delta^2. A whole-curve integral norm supplies no pointwise margin at a chosen q. Dependence pruning preserves exact distinguishability and cheapest nonzero witnesses, not the strongest possible signal.

The prior exact calculation at R7 gave dimension70 and rank69. Its formal invisible direction is e[((0,5),7)]-e[((3,4),7)]; both generators multiply it by q^25. No pair of physical graph states realizing this direction is asserted. The rank69 calculation was independently checked before workspace pruning, but has not been replayed on this recovered checkpoint.

There is a proved sufficient periodic cutoff worth implementing next. If every edge factor satisfies t_e^M=1, residue decomposition gives F=P/(1-x^M)^n, deg(P)<=K=n(M-1). Complementing every residue rho to M-1-rho preserves all squared differences and reverses total residue volume, so P_k=P_(K-k). Equality through floor(K/2) therefore determines the low half of the numerator, then the whole palindromic numerator and complete series. This is a sufficient bound, not a sharpness claim. Its earlier implementation was removed by workspace cleanup and is not included in this checkpoint.

## Remaining delivery work

Restore the periodic implementation and complete graph/operator test suites, reconcile their public APIs, rerun the full new regression set and retained rank69 calculation, then prepare the combined publication and observe its remote CI. The bundled monograph remains the completed v0.2.0 monograph; this supplement records the new checkpoint separately, without claiming the book has incorporated these additions.
