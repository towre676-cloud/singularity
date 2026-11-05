# The marked cut lattice: reconstruction and explicit theta arithmetic

A supplement to *What Must Survive II*, Revision 6. 5 November 2026.

This supplement proves a reconstruction theorem for the **marked lattice**, makes the root-of-unity modularity precise, and computes exact arithmetic data for five graphs. It does **not** prove that the marked theta series determines that marked lattice. No priority claim or proof-assistant certification is made for these new arguments.

## 1. What the marking actually supplies

Let G be a finite connected loopless graph on n vertices. Work in U = R^n/R1, with integer lattice Z^n/Z1, identified with the integer cut lattice by the coboundary map. Write

    E_G([h]) = h^T L_G h,
    V([h]) = sum_i h_i - n min_i h_i.

The second expression is independent of the representative and agrees with the volume of the normalized nonnegative height vector. Define the n linear functionals

    ell_i([h]) = sum_j h_j - n h_i.

Then

    V = max_i ell_i,       sum_i ell_i = 0.

The ell_i are affinely independent. Their convex hull is an (n-1)-simplex in U*. It is also the polar of the unit ball {V <= 1}. Thus V supplies an intrinsic simplex in the dual vector space. It is considerably more information than an unmarked quadratic lattice.

### Theorem A. A volume-marked cut lattice determines its graph

Suppose G and H are finite connected loopless graphs and T is an additive lattice isomorphism between their cut lattices preserving both E and V. Then G and H are isomorphic. More precisely, the induced real linear map on potentials is a vertex permutation modulo constant vectors. The conclusion includes graphs with parallel edges, with their multiplicities.

**Proof.** The rank gives n. Extend T linearly to U. Equality of V on the lattice extends first to rational vectors by positive homogeneity and then to real vectors by continuity. Equality of support functions implies that T* permutes the vertices ell_i of the dual simplex. After the resulting permutation of vertex indices, ell_i(T[h]) = ell_i([h]) for every i. The differences ell_i-ell_j are -n(h_i-h_j), so T[h]=[h]. Restoring the permutation gives T[h]=[P h]. Preservation of energy gives h^T L_G h = h^T P^T L_H P h for all h. Both Laplacians annihilate constants; polarization gives L_G=P^T L_H P. Its off-diagonal entries recover edge multiplicities. QED.

This resolves **every Whitney ambiguity at the marked-object level**: a nonisomorphic Whitney twist cannot admit a volume-preserving lattice isometry. It does not assert that two such graphs necessarily have different marked series.

### An explicit reconstruction through effective resistance

Let the quadratic form induce the dual inner product on U*. Put

    D_ij = ||ell_i - ell_j||_*^2,
    J = I - 11^T/n,       P0 = 11^T/n.

If L^+ is the Moore-Penrose inverse of the Laplacian, then

    D_ij = n^2 (e_i-e_j)^T L^+ (e_i-e_j)
         = n^2 R_eff(i,j).

Consequently

    L^+ = - J D J / (2 n^2),
    L = (L^+ + P0)^(-1) - P0.

This recovers the Laplacian from the metric geometry of the marking's polar simplex, up to its vertex permutation. The identities are rational and were checked exactly on K4, K3,3, Petersen, and both members of the late-separating 14-vertex pair. These computations check the formulas; the preceding proof is what establishes the general statement.

## 2. The precise completeness gap

There are three distinct objects:

1. An integral quadratic lattice.
2. That lattice together with V on its individual vectors.
3. The series M(x,q), which records only the number of vectors at each pair (V,E).

Theorem A establishes 2 -> graph. It does not establish 3 -> 2. The required open implication is

    equality of M_G and M_H
        => a lattice isometry carrying V_G to V_H.

Equal representation counts do not supply correspondences compatible with addition. Even an isometry reconstructed from the unmarked lattice need not preserve the marking merely because its two-variable histograms agree. This is where a proof or a counterexample is still needed.

Su and Wagner prove a theorem about *isometries of flow lattices* of regular matroids, after contracting coloops. To apply it to cut lattices, pass to the dual regular matroid. For loopless graphs the dual has no coloops corresponding to graph loops, so the cut-lattice isometry recovers the cycle matroid. This is a theorem about a known lattice, not a theorem reconstructing a lattice from its theta series. Theorem A bypasses the Whitney stage once the marked object has been recovered.

## 3. Explicit modular data at roots of unity

Use q = exp(2 pi i tau). Choose a root vertex, put r=n-1, and let Q be the reduced graph Laplacian. A rooted integer potential z represents every cut exactly once. For zeta=exp(2 pi i j/n),

    F_j(tau) = M_G(zeta, exp(2 pi i tau))
             = sum_{z in Z^r} exp(2 pi i j sum(z)/n)
                               exp(2 pi i tau z^T Q z).

The character follows because V(z) = sum(z) modulo n. In particular the character is additive even though V itself is not.

For cubic graphs the original Gram Q is odd: a vertex cut has norm 3. Also r is odd. One must keep the half-integral weight multiplier. With our q convention use the even Gram B=2Q; its quadratic exponent is B[z]/2 = Q[z]. This change of convention does not change F_j.

Let d=n/gcd(n,j), with d=1 for j=0, and j/n=a/d in lowest terms. Set

    K_d = {z in Z^r : sum(z) = 0 mod d}.

A basis matrix H has first column d e_1 and other columns e_i-e_1. Thus

    B_d = 2 H^T Q H,
    det(B_d) = d^2 2^r tau(G).

Here tau(G)=det Q is the spanning-tree count; the original cut lattice has covolume sqrt(tau(G)), not tau(G).

Let A_d=K_d^*/K_d for the metric B. Original Z^r embeds in K_d^*, so the d cosets k e_1+K_d are elements of A_d. If theta_mu denotes the usual coset theta series of K_d, then exactly

    F_j = sum_{k=0}^{d-1} exp(2 pi i a k/d) theta_[k e_1].

This is a complete finite-discriminant-form description of the twist. It supplies weight r/2 and all transformation data via

    theta_mu(tau+1) = exp(2 pi i q_A(mu)) theta_mu(tau),
    theta_mu(-1/tau) = (-i tau)^(r/2) / sqrt(|A_d|)
                      * sum_nu exp(-2 pi i b_A(mu,nu)) theta_nu(tau),

where q_A(mu)=B[mu]/2 modulo 1 and b_A is the discriminant pairing. The square-root branch is the usual holomorphic branch on the upper half-plane. Equivalently use the associated metaplectic Weil representation. Sign-conjugate conventions for that representation change its presentation, not these theta functions.

### Exact level

The level N_d of this even lattice is the least positive N such that N B_d^(-1) is integral with even diagonal. If C=B_d^(-1), it is the least common multiple of

    denominators(C_ij), i<j;
    denominators(C_ii/2), all i.

This is an exact formula, with no modular rank computation or guessed reconstruction. It is the level of this auxiliary even lattice, not a claim of smallest possible scalar modular level for F_j.

### A scalar subgroup and its character, for cubic graphs

Let theta(tau)=sum_m exp(2 pi i tau m^2) and j_theta(gamma,tau)=theta(gamma tau)/theta(tau). For gamma in Gamma_0(N_d) intersect Gamma_1(d),

    F_j(gamma tau) = ( tau(G) / D ) * j_theta(gamma,tau)^r * F_j(tau),

where D is the bottom-right entry of gamma and the parenthesis is the Kronecker symbol. This describes the scalar multiplier without choosing square-root signs separately. N_d is a multiple of 4 in the odd-rank case, so j_theta is the classical theta multiplier on the required subgroup.

**Justification.** The coset transformation formula on Gamma_0(N_d) has a common scalar multiplier, permutes discriminant classes by a diagonal entry, and multiplies by exp(2 pi i times an integral multiple of q_A(mu)). For the cosets from Z^r, q_A(mu)=Q[mu] is integral, so that phase is 1. Gamma_1(d) fixes their cyclic coset indices. The common scalar is the scalar multiplier of theta_{K_d}. For an integral symmetric quadratic matrix Q_d=H^T Q H of odd rank this is (det Q_d / D) j_theta^r. Since det Q_d=d^2 tau(G) and D is coprime to d, the character reduces to (tau(G)/D). The scalar formula also follows by adjoining the rank-one theta lattice, applying the even-rank transformation law, and dividing by theta.

The full discriminant quadratic form controls the vector transformation. The single scalar quadratic character on this subgroup is therefore substantially less information than the whole Weil representation, and generally less than the Jacobian with its pairing. An abstract Jacobian group alone does not specify every relevant quadratic refinement.

### Computed levels

All determinants, inverses, Smith forms and least common multiples below were computed over Q or Z. Full matrices and inverses are in theta_arithmetic.json.

| Graph | tau(G) | character order d | N_d |
|---|---:|---:|---:|
| K4 | 16 | 1, 2, 4 | 8, 16, 64 |
| K3,3 | 81 | 1, 2, 3, 6 | 36, 144, 36, 144 |
| Petersen | 2000 | 1, 2, 5, 10 | 20, 80, 100, 400 |
| late pair A | 38258 | 1, 2, 7, 14 | 153032, 153032, 7498568, 7498568 |
| late pair B | 38258 | 1, 2, 7, 14 | 153032, 153032, 7498568, 7498568 |

Equal levels in the late pair do not imply equal theta series or isometric lattices. Its primitive-character auxiliary discriminant group has order 61,428,269,056: the vector-valued description is conceptually finite but naive enumeration of that whole group would be impractical.

Three numerical checks of the primitive fourth-root K4 scalar transformation passed with relative discrepancies below 1.6e-14. A fourth check on the four-vertex diamond graph (tree count 8, level 32) verified the nontrivial character (8/11)=-1. These floating-point checks are consistency checks, not certificates of modularity or rigorous tail bounds.

## 4. Two limits of the modular route

First, the n specializations zeta^n=1 determine only volume modulo n. If

    P_E(x) = sum_V a(E,V) x^V,

their discrete Fourier transform determines sums of a(E,V) over V in each residue class modulo n. It does not in general recover P_E itself. Multiples of x^n-1 are invisible to these evaluations. This is a loss of information in specialization; it is not a constructed pair of graph invariants with that difference. Consequently, even complete root-of-unity modular data does not by itself close completeness of the full marking.

Second, in the Poisson formula a nontrivial character shifts the dual Gaussian away from 0. Its asymptotic contains exponential suppression controlled by the closest shifted dual vectors. The direct spanning-tree prefactor is cleanest at the trivial character x=1, where

    M_G(1,exp(-epsilon)) ~ (pi/epsilon)^(r/2) / sqrt(tau(G)).

At other characters the leading exponential and its multiplicity must also be accounted for.

## 5. The exact inversion symmetry needs amplitude

Negating a cut sends normalized volume V to n A - V, where A=max(h)-min(h). It does not simply replace V by -V. Introduce

    N_G(x,z,q) = sum_c x^V(c) z^A(c) q^E(c).

Then the involution c -> -c proves the coefficientwise identity

    N_G(x,z,q) = N_G(x^(-1), x^n z, q).

At zeta^n=1 this gives M_G(zeta,q)=M_G(zeta^(-1),q). For generic x, the amplitude variable is required for this literal inversion identity. The earlier epsilon-jet reflection law should retain its own proof; calling it a shadow of cut negation is an interpretation, not a replacement derivation.

## 6. Infinity poles are not automatically an artifact

For a simple cubic graph and fixed volume V>0, E(h) is a convex quadratic function on the simplex h>=0, sum(h)=V. Its maximum is 3 V^2, attained at the n single-vertex height configurations. Positive definiteness on the quotient makes the inequality strict for nontrivial convex combinations of distinct simplex vertices. Therefore

    [x^V] L_G(x,q) = n q^(3 V^2) + lower powers of q.

Thus q=infinity already describes a genuine extremal-energy problem in finite volume. Promotion poles arise after further normalization and cancellation; their geometric mechanism is still open. The absence of analytic convergence at infinity does not by itself make them artificial.

## 7. What is closed and what remains

Closed here by conventional proofs: marked-lattice reconstruction of the graph; effective-resistance reconstruction; the finite-discriminant decomposition of root-of-unity twists; an exact auxiliary level algorithm; and an explicit scalar subgroup/multiplier in cubic odd rank.

Computed exactly here: levels and discriminant data on five graphs, and rational reconstruction checks on those graphs. No rank table was recomputed. The supplied late-pair edge lists were copied unchanged from Revision 6. The main Revision 6 archive was not edited.

Open: reconstructing the marked lattice from its two-variable representation counts; the smallest scalar level for individual twists; a uniform window theorem; completeness of L_G; the later promotion sequence; and the physical/formal-verification tasks from the parallel program. These results do not close those problems.

The next mathematical target is now precise: either reconstruct the addition law from the joint (energy,volume) histogram within graph cut lattices, or find two nonisomorphic graphs with equal such histograms. Restricting first to a fixed Whitney orbit isolates the marking problem, but equality of histograms there still must be proved to induce a marking-preserving isometry. Passing the modular character tests is only a necessary condition for a collision.

## References and provenance

- Bacher, de la Harpe and Nagnibeda, *The lattice of integral flows and the lattice of integral cuts on a finite graph*, Bull. SMF 125 (1997), 167-198. https://www.numdam.org/item/BSMF_1997__125_2_167_0/
- Su and Wagner, *The lattice of integer flows of a regular matroid*, arXiv:0908.4071. https://arxiv.org/abs/0908.4071
- Zemel, *A p-adic Approach to the Weil Representation of Discriminant Forms Arising from Even Lattices*, arXiv:1208.2570v2, especially Section 1 and the Gamma_0(N) specialization following Theorem 6.1. https://arxiv.org/pdf/1208.2570

The graph-specific derivations above apply classical theta transformation theory. A comprehensive priority search for volume-marked cut lattices has not been completed.

## Replay

Python packages: sympy, networkx, numpy, scipy (networkx Laplacian dependency).

    python theta_arithmetic.py
    python check_reconstruction.py
    python check_modular.py

The first two are exact arithmetic. The third is explicitly floating point. The supplied pair file is included, so replay needs no path into Revision 6. These scripts are not formal proofs of the general graph-to-lattice construction or of theta modularity.
