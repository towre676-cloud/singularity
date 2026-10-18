# Algebraic geometry as an observability tool

Research supplement, 18 October 2026. Starting point: Singularity v0.2.0, commit `f88da95`. This note records original applications to the existing height machinery, supported by exact finite experiments. It does not claim historical priority or kernel verification of the new propositions.

## Source and scope

The source mined here is Ravi Vakil, *Foundations of Algebraic Geometry*, June 11, 2013 draft, [public PDF](https://math.stanford.edu/~vakil/216blog/FOAGjun1113public.pdf). The useful inputs are Noetherian ideals and the Hilbert Basis Theorem (§3.6.16–17, printed pp.122–123), tangent spaces (§12.1, pp.321–326), and compatible constructions (§1.3–1.4 and §9.1–9.2). The applications and proofs below are ours; Vakil does not discuss Singularity. The PDF identifies itself as an early version, so the section references refer to this exact linked draft.

The existing scalar-parameter engine `parameters.py` already isolates all exceptional roots of a supplied finite discrepancy prefix. The context machinery already has completeness and transport results. Merely calling those constructions “schemes”, “Yoneda” or “sheaves” would not supply a stronger theorem. The two new useful steps are a finite-determination theorem for polynomial families and exact composition rules for compressed interfaces.

The v0.2.0 repository also includes `formal-analysis`, which proves the positive-real visibility theorem using actual Mathlib analysis. That completed result is not reopened here. Algebraic geometry supplies no replacement for the complex-analytic continuation questions that remain outside that proof's scope.

## 1. Uniform finite determination of full-series equality

Fix a finite graph template G and put a separate factor t_e on each edge. Define

$$
F_G(x;\mathbf t)=\sum_{h:V(G)\to\mathbb N}x^{\sum_v h_v}
\prod_{e=uv}t_e^{(h_u-h_v)^2}
=\sum_{r\ge0}c_{G,r}(\mathbf t)x^r.
$$

Each coefficient is a polynomial with integer coefficients: there are only finitely many labeled profiles of a fixed total height. Setting every t_e=q recovers L_G. Setting t_e=q^{w_e} recovers a nonnegative weighted-edge energy; the independent algebraic parameters are the factors t_e, not the exponents w_e. A nonedge can be encoded by factor 1 on a complete template.

**Proposition (finite determination).** For two fixed finite templates G and H there is an integer R_* such that, for every commutative Q-algebra K and every pair of edge-factor choices in K, equality of the coefficients through R_* is equivalent to equality of the complete formal series in K[[x]]. R_* depends on the templates and chosen observation family, not on the particular factors.

**Proof.** In the finite-variable polynomial ring

$$
A=\mathbb Q[\mathbf t,\mathbf s],\qquad
I_R=(c_{G,r}(\mathbf t)-c_{H,r}(\mathbf s):0\le r\le R),
$$

the ascending chain I_0⊆I_1⊆… eventually stabilizes. Equivalently the union I_∞ is finitely generated, and its generators all lie in some I_{R_*}. Consequently every later coefficient difference is an A-linear combination of the differences through R_*. Evaluation A→K takes a vanishing finite prefix to vanishing of every difference. The converse is immediate. This proves the assertion, including specialization to rings with nilpotents. The same argument works over Z, or in a finitely generated coefficient algebra after imposing polynomial parameter constraints. □

For moment-marked observations, include every coefficient [x^r u^s] through r≤R. Only finitely many s occur at each r (r≤s≤r² for r>0), so the proof is unchanged. It also applies to any finite collection of fixed templates, by taking the maximum of their pairwise cutoffs.

This is more than the elementary observation that a fixed finite collection of unweighted graphs has a finite distinguishing budget: the parameter population here is continuous, and the conclusion also controls infinitesimal parameter choices. It is still an application of a standard theorem, rather than a new result in general algebraic geometry.

The conclusion is deliberately about **equality of complete observations**. It neither proves the ordinary invariant complete nor reconstructs its inputs. No explicit R_* is supplied. A plateau I_R=I_{R+1} is insufficient: later coefficients can enlarge the ideal. A simple abstract example has c_1=…=c_M=0 and c_{M+1}=t. Nor does finite generation of the equalizer ideal say that every later coefficient is a polynomial in the retained observed values. No numerical stability estimate follows. An effective stopping certificate needs a separate recurrence, structural tail-membership proof, or a proved cutoff.

## 2. A complete tangent-rank classification for weighted triangles

Consider the triangle with edge factors a,b,c on edges 01,02,12. Its moment series retains total height and squared height. For k≥1, maximal squared height at total height k forces exactly one nonzero vertex, giving

$$
m_k=[x^ku^{k^2}]\mathcal P=(ab)^{k^2}+(ac)^{k^2}+(bc)^{k^2}.
$$

**Proposition (three probes).** On the positive octant a,b,c>0, the Jacobian of (m_1,m_2,m_3) has rank 3, 2 or 1 according as the three edge factors have three, two or one distinct values. These ranks already equal the maximum attainable by all coefficients of the ordinary and moment series.

**Proof.** Put A=ab, B=ac, C=bc. The product-coordinate map has Jacobian determinant −2abc, so it is locally invertible throughout the positive octant. The moment-probe Jacobian in those coordinates is

$$
\begin{pmatrix}
1&1&1\\4A^3&4B^3&4C^3\\9A^8&9B^8&9C^8
\end{pmatrix}.
$$

At three distinct positive nodes its determinant is nonzero. Otherwise a nonzero polynomial α+βz³+γz⁸ would have three positive roots. Rolle's theorem would force at least two positive roots of its derivative z²(3β+8γz⁵), which has at most one. At two distinct nodes the first two rows are independent; at one node the rank is one. Distinctness of A,B,C has the same pattern as distinctness of a,b,c.

Every aggregate coefficient is symmetric in a,b,c, since all edge permutations of a triangle are realized by vertex relabelings. At coincident factors, the corresponding partial derivatives are equal. Thus no additional aggregate observations can exceed the ranks just computed. □

The inverse function theorem therefore gives local recovery of all three factors from these three moment observations at every point with distinct positive factors. This does not assert a global inverse or distinguish vertex relabelings. The result applies in particular to physical factors in (0,1). On the locus of equal factors, the failure is a first-order one; it is not proof of a continuous family of exactly indistinguishable models.

For example, at a=b=c=t the two-dimensional plane of sum-zero perturbations is invisible to first order at every volume. In the ring of dual numbers, with ε²=0, (t+ε,t−ε,t) and (t,t,t) have identical full moment series. For a real ε with 0<|ε|<t, however,

$$m_1(t+\varepsilon,t-\varepsilon,t)=3t^2-\varepsilon^2.$$

The difference appears at second order. This is an exact example of symmetry causing branching and weak first-order sensitivity, rather than a missing graph distinction. At t=1/2, perturbations ε=1/10,1/100,1/1000 give first-coefficient changes −1/100,−1/10000,−1/1000000.

This gives a precise experiment-design remedy. If the vertices can be probed separately, the three one-unit observations are A=ab, B=ac and C=bc, instead of their aggregate sum. Their Jacobian determinant is −2abc, nonzero even at equal factors. In the positive region the labeled factors are recovered globally by a=√(AB/C), b=√(AC/B), c=√(BC/A). At a=b=c=1/2 the determinant is −1/4. Thus asymmetric vertex probes remove this symmetry-induced first-order blindness; adding more symmetric aggregate coefficients cannot. This requires access to those labeled interventions, and is not a claim that the original aggregate series contains them.

There is a useful unmarked control. Directly enumerating total heights 1,2,3 gives

$$c_1=ab+ac+bc,$$
$$c_2=c_1+(ab)^4+(ac)^4+(bc)^4,$$
$$c_3=1+(ab)^9+(ac)^9+(bc)^9+2abc(a^3+b^3+c^3).$$

At (a,b,c)=(1/2,1/3,1/5), the Jacobian determinant of (c_1,c_2,c_3) is exactly

$$-229387106779/1230187500000000\ne0.$$

Thus the ordinary volume-three observation map is generically locally invertible too. Unlike the moment argument, this single witness does not establish invertibility at every distinct-positive point.

`src/singularity/edge_factors.py` implements exact factor-polynomial coefficients, moment coefficients, rational evaluation and gradients, with an explicit profile budget. `scripts/vakil_bridge.py` retains the three rank strata through volume eight, the ordinary nonzero determinant, and the second-order response. The all-depth and all-positive-parameter conclusions come from the proofs above, not from those finite checks.

## 3. A compositional algebra for boundary charges

The existing interface of a block with ordered terminals stores interior volume j, boundary charge Q and energy E. Write it as

$$A(x,\mathbf z;q)=\sum_{j,Q,E}n_{j,Q,E}x^j\mathbf z^Qq^E.$$

Let d_i be the terminal's number of interior neighbors, and let E_T be its terminal-edge energy. At terminal heights b the interior kernel is

$$K_b=x^{|b|}q^{\sum_i d_i b_i^2+E_T(b)}A(x,\mathbf z=q^{-2\mathbf b};q).$$

The following updates keep the compressed interface rather than expanding every terminal height.

**Parallel composition.** If two blocks have disjoint interiors and edge-disjoint terminal graphs on the same ordered boundary, then A_union=A_1 A_2, their terminal degrees add, and their terminal edges form a disjoint union. Coefficients convolve by (j,Q,E)+(j',Q',E'). This follows from the independent choices of the two interior height assignments and additivity of volume, charge and energy. Shared terminal edges must not be counted twice. The implementation rejects overlapping terminal-edge metadata; disjoint interior copies are part of its declared input interpretation.

**Forgetting a terminal.** Suppose terminal t becomes interior, and ζ records its adjacency to the remaining terminals. If its new interior height is h≥0, then a cell updates by

$$(j,Q,E)\mapsto\bigl(j+h,Q_{-t}+h\zeta,E+(d_t+|\zeta|)h^2-2hQ_t\bigr).$$

The remaining terminal degrees become d_i+ζ_i, and edges at t leave the terminal-edge graph. Equivalently,

$$A_{forget}(x,\mathbf z';q)=\sum_{h\ge0}x^h q^{(d_t+|\zeta|)h^2}(\mathbf z')^{h\zeta}A(x,\mathbf z',z_t=q^{-2h};q).$$

The old charge term −2hQ_t accounts for cross terms with old interior vertices. The contribution d_t h² accounts for their incident edges, while |ζ|h² accounts for edges to the remaining terminals. Every original height assignment is recovered once by choosing h and the old interior assignment. For an output budget R only h≤R−j is needed; a source interface complete through R therefore suffices. This proves both the update and truncation safety. Individual displayed Laurent factors may have negative exponents, but every actual output energy is a sum of squares and is nonnegative.

These are standard composition and marginalization principles applied to our compressed charge coordinates. They provide a useful compiler primitive, not a claim that aggregated counts themselves satisfy an unrestricted sheaf gluing law. Named compatible assignments glue; their aggregate marginals may lose exactly the correlations needed to do so. A full separator compiler and performance comparison remain further work.

## 4. Two broader uses worth pursuing next

For PerfectJet's binary-sextic incidence matrices, rank-jump families should be described by determinantal ideals and a complete cover of pivot-minor charts. A generic line can miss components of codimension two or more. This is a stronger target than collecting additional line probes. If a matrix has N+1 columns, the condition that its kernel has dimension at least k is the vanishing of all (N+2−k)-minors, in the nontrivial range 1≤k≤N+1; an impossible minor size is handled by the usual rank convention. A nonzero pivot minor permits exact Schur-complement equations on that chart. Every omitted pivot-vanishing locus must be handled separately. This is a proposed extension, not a completed classification for higher degrees.

For PerfectPower's original-model genus-one transport, projective extension and the group-variety translation theorem suggest certificates containing both rational maps, their composition identities, exceptional denominator charts, and the image of the chosen origin. Subtracting that image gives the origin-preserving homomorphism. Relevant source locations are §16.5, §17.4, and Corollary 10.3.13. Birational coordinate transport does not preserve integrality automatically and supplies no Mordell–Weil rank or saturation bound. These cross-repository applications were assessed but are not implemented by this supplement.

A further bridge is to view attachment patterns η as generators (1,η) of a graded affine semigroup. At volume j, the distinct achievable charges are exactly the degree-j monomials in its semigroup algebra. Its Hilbert function could therefore provide exact support forecasts beyond the existing asymptotic dimension bound. This is a proposed next step. Integer points in a dilated convex hull must not automatically be treated as achievable charges; lattice constraints and semigroup holes matter.

## Reproduction and evidence

Run from the repository root with Python 3.10 or newer; the new code has no third-party dependency:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_edge_factors.py' -v
PYTHONPATH=src python -m unittest discover -s tests -p 'test_charge_gluing.py' -v
PYTHONPATH=src python scripts/vakil_bridge.py --check
```

The first test uses independent finite height boxes to check coefficient evaluation, and checks specialization against ordinary q-polynomials. The second test compares interface composition and terminal forgetting against direct enumeration on actual glued graphs. `results/vakil_bridge.json` records exact rational evidence. New propositions in this note have not been formalized in Lean. Charge tables now declare their complete interior-volume bound as `max_volume`. Calls requesting a deeper prefix are rejected; manually constructed legacy tables must be rebuilt or supplied with a truthful bound. Standard calls to `charge_interface` retain their signatures.

The existing monograph remains the account of the v0.2.0 theorems; this supplement records the additional work without making its generated PDF silently stale.

Delivery validation: all 272 Python tests passed; the retained bridge experiment, charge-interface receipt, original example reproduction, repository checks and handoff verification passed. Formal packages were unchanged and were not rebuilt for this supplement.
