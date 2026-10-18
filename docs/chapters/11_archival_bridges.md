# Archival bridges: what is inherited and what changes

Singularity did not arise from an empty mathematical landscape. PerfectPower, PerfectJet, the SOE program, and older conductor and lattice investigations already contain several of its ingredients. The appropriate historical claim is therefore narrow: the present project selects a different object and a different inverse question from a substantial existing toolkit. It does not claim to invent prime valuations, graph Laplacians, discrete Gaussian heights, cut lattices, binary Ising polynomials, or Euler products. Those established subjects are part of the mathematical background [BHN1997; AM2009; BPR2024]. The value of the new direction must be demonstrated through its precise marking, its exact examples, and the questions those examples make available.

This chapter explains the bridges in mathematical terms. A shared vocabulary such as population, shadow, quotient or phase is not enough to establish a bridge. There must be a defined map, a preserved quantity, an exact identity, or a specifically stated proposal. The distinction matters because the archives contain both successful computations and ambitious descriptions whose full objects were not implemented. Reusing a phrase should not silently upgrade the status of either the old claim or the new one.

## From multiplicative integers to relational exponent geometry

The oldest relevant arithmetic step is the valuation embedding

\[
n\longmapsto v(n)=(v_2(n),v_3(n),v_5(n),\ldots).
\]

Every positive integer gives a finitely supported nonnegative integer vector, and multiplication becomes addition: \(v(mn)=v(m)+v(n)\). The June collision work used this geometry to define

\[
\kappa(m,n)=\sum_pv_p(m)v_p(n).
\]

It related shared prime support to a dot product and represented divisors of an integer as a product of finite chains. Its analytic deformation rewarded or penalized shared exponents with \(e^{t\kappa(m,n)}\). The exact Euler factor was \(\sum_{a,b\ge0}e^{tab}p^{-s(a+b)}\). A positive real reward is unstable because the terms with \(a=b=N\) contain quadratic exponential growth against only a linear exponential penalty. This is a specific mathematical limitation, not a general failure of the valuation viewpoint [PJ2026].

The present construction uses exponent differences instead of that attractive dot product. For a graph \(G\), put

\[
\mathcal E_G(n_1,\ldots,n_k)
=\sum_p\sum_{ij\in E(G)}(v_p(n_i)-v_p(n_j))^2.
\]

The sum is finite for every tuple because only finitely many primes divide the product. For \(0\le q\le1\), the weight \(q^{\mathcal E_G}\) is bounded by one. The resulting series is therefore dominated by the independent tuple series in its elementary convergence domain. This change does more than repair a divergent sign. It creates a zero-energy relation: two adjacent integer positions must have equal valuations at every prime, hence equal integers. On a connected graph, zero energy means the entire tuple is constant.

**Proposition SNG-I020: exact synchronization at zero parameter.** For a connected graph on \(k\) vertices,

\[
\mathcal E_G(n_1,\ldots,n_k)=0
\quad\Longleftrightarrow\quad n_1=\cdots=n_k.
\]

The forward direction follows because each squared difference must vanish and equality propagates along graph paths. The reverse direction is immediate. For disconnected graphs, equality is required separately on each component. Thus the earlier multiplicative linearization now supports a relational arithmetic population. The graph specifies which exponent coordinates must agree; the primewise product turns that specification into a Dirichlet series.

There is no information gain in the Euler lift itself. Once \(P_G(x,q)\) is known, \(\prod_pP_G(p^{-s},q)\) is fixed in its convergence domain. Conversely, the coefficient of a prime power \(p^r\) in the Dirichlet series recovers \([x^r]P_G\), because a product equal to \(p^r\) forces every tuple entry to be a power of that single prime. The arithmetic series is an exact re-expression with useful analytic operations, not an additional sensor that distinguishes graphs whose full local factors agree.

## From exact populations to navigable height assignments

PerfectPower repeatedly studies a large finite population through counts, conditional counts, rankings and samples instead of explicitly listing every member. That approach transfers directly to bounded height populations [PP2026]. At depth \(D\), the original objects are vectors \(a\in\{0,\ldots,D\}^k\) with minimum zero. Their number is \((D+1)^k-D^k\). If energy, volume and span constraints are imposed, the retained population is smaller but remains a population of original assignments. A conditional count can determine how many completions remain after the first few coordinates have been fixed.

The released `HeightPopulation` supplies exact completion counts; lexicographic ranking and unranking follow from the usual branching identity. At a prefix \(u\), the total completion count is the sum of completion counts after each allowed next height. A rank selects the first branch whose cumulative count exceeds it. An original assignment receives a rank by adding all earlier branch populations. This supplies an exact navigation mechanism for height configurations without identifying assignments that merely share a profile. It also makes uniform sampling possible by drawing a uniform integer rank in the feasible population.

The distinction between counting assignments and counting profile types is essential. The energy-volume-span histogram may have relatively few occupied cells, but a cell's coefficient is its multiplicity. Replacing that coefficient by one changes the invariant. The seven-vertex span-two cubic sector has forty-two ordered assignments even when only a modest set of energies occurs. Its successful distinction depends on the distribution of those multiplicities. The population machinery is therefore relevant as an exact computational method, while its prior application domains need not be imported into the present mathematical target.

An exact residual decomposition also becomes possible. A partial assignment contributes the energy of edges whose endpoints are both processed. Edges crossing to unprocessed vertices remain symbolic functions of their boundary heights. Their contributions should not be guessed from the already accumulated scalar energy. Keeping the boundary state allows future assignments to complete the squared differences exactly. This is the natural finite-state interface for dynamic programming over a path or tree decomposition. For a fixed cutoff \(D\), a boundary of size \(b\) has at most \((D+1)^b\) raw height states before any further reduction. This is a conditional complexity observation about a chosen decomposition, not a universal small-state theorem.

## From all-future behavioral equivalence to weighted transfer states

The SOE program formalizes the principle that two partial states should be identified exactly when every allowed future continuation gives the same observable behavior [SOE2026]. A direct analog exists for a fixed finite height-transfer computation. The observation is now a polynomial population, and a continuation adds vertices, edges, weights, or terminal conditions according to a declared processing scheme. Two boundary states can be merged only when all continuations permitted by that scheme produce the same remaining generating polynomial.

That sentence is a proposed computational use of the SOE idea, not a claim that the previous Lean theorem has already verified this graph algorithm. Several details must be fixed before a formal transport is legitimate. The state must include any boundary heights required by future edges, the accumulated or deferred volume information, and sufficient data to enforce the global span convention. Polynomial weights must be handled over a specified coefficient structure. A quotient of a two-state partial machine does not automatically verify a family of graph transfers with arbitrarily many boundary states.

The proposal nevertheless has a concrete exact form. Let a processing alphabet encode the legal remaining transfer steps for a fixed decomposition. To a partial state \(s\), associate the function \(f_s(w)\) giving the remaining polynomial after continuation word \(w\). Define \(s\sim t\) when \(f_s(w)=f_t(w)\) for every permitted \(w\). This equivalence is correct by definition and is stable under a common legal next step. The research problem is to compute it efficiently and provide a finite certificate that the retained tests suffice. On a fixed finite continuation space, exhaustive comparison is available. Across unbounded decompositions, the finite characterization requires an additional argument.

The distinction connects usefully to PerfectJet's exact representation work. A vector of sufficient boundary quantities should remain closed under every declared transfer. If it does not, the missing interaction is part of the returned mathematical diagnosis. In the present examples the binary population is insufficient for a specific higher-height question, and the span-two population supplies an explicit witness. This is an actual object-level result, stronger than merely observing that a chosen summary might omit information.

## The relation to classical cut lattices

For a connected graph choose an orientation of its edges and write \(d\) for the vertex-to-edge incidence map. Then \(E_G(a)=\|da\|^2\), and \(\ker d\) consists of common constant shifts. The image of integer vertex heights under \(d\) is the integral cut lattice. Every integer height class modulo common shifts has a unique representative of minimum zero. Consequently

\[
B_G(1,q,1)=\sum_{a\in\mathbb Z^k/\mathbb Z\mathbf1}q^{\|da\|^2}
\]

is its ordinary theta series for \(0<q<1\). This is classical lattice territory. The relation between a cut lattice's minimum norm and graph edge connectivity is established background [BHN1997]. Singularity's elementary minimum-cut proof should be read as a proof in its chosen coordinates, not as a historical priority claim about that relationship.

The added volume and span markers retain the position of a height class relative to the vertex-height coordinate system. They are not invariants of an abstract Euclidean lattice by itself. An isometry of cut lattices need not preserve the minimum-normalized sum of vertex heights or their maximum. This is the precise sense in which the new object can distinguish vertex realizations that an ordinary theta series identifies.

The examples give a concrete instance. Gluing two graph blocks at a single vertex makes their cut lattices an orthogonal direct sum. To see this, independently choose integer heights on each block modulo constants, and shift their representatives so the common vertex agrees. The edge-energy sum splits into the two blocks, and the correspondence is bijective. A bridge contributes a one-dimensional standard integer lattice. Each spectral graph therefore has a cut lattice isometric to the triangle cut lattice plus four such bridge factors. Each binary graph has the cut lattice of its common theta block plus two bridge factors. The placement of those bridge attachments does not change this abstract lattice decomposition, but it does change the marked populations established in the preceding chapter.

This distinction also cautions against interpreting the construction as a new kind of Euclidean spectral statistic. The Laplacian spectrum, the abstract cut lattice, and the marked height population forget different information. Their comparison is valuable precisely because they are not interchangeable. The examples show a difference after some conventional data have been fixed; they do not prove a total ordering among every graph invariant.

## Finite conductors and the part that is already old

The conductor archive studied rational phases and exact residue closure. The same algebraic mechanism works for the present unmarked local factor. Let \(q=\zeta_L\) be an \(L\)-th root of unity. Changing a single coordinate by \(L\) changes energy by

\[
E_G(a+Le_i)-E_G(a)
=2L\sum_{j\sim i}(a_i-a_j)+L^2d_i,
\]

which is divisible by \(L\). The phase is therefore periodic in each height coordinate modulo \(L\). Splitting \(a_i=r_i+Lb_i\) gives the exact identity

\[
P_G(x,\zeta_L)=\frac{N_{G,L}(x)}{(1-x^L)^k},
\qquad
N_{G,L}(x)=\sum_{r\in\{0,\ldots,L-1\}^k}
\zeta_L^{E_G(r)}x^{|r|}.
\tag{SNG-I021}
\]

The equality holds as a formal series and analytically for \(|x|<1\). It is a finite cyclotomic calculation. The archive already used this kind of residue decomposition for collision and Cartan quadratic forms [PJ2026]. Its presence here is an inherited bridge, not the new claim. The difference is that a graph Laplacian has a common-shift null direction and the project retains coordinate-sensitive marks around that direction.

The marked span variable prevents one from copying the same numerator formula unchanged. Adding \(L\) to one coordinate can alter the common minimum and maximum, so its effect on the span marker is not determined by that coordinate's residue alone. One may specialize to \(z=1\), keep a finite height cutoff, or develop an additional boundary description. The unmarked rational formula does not establish a correspondingly simple rational formula for the full marked series.

There is a further exact bridge to spanning trees. For an odd prime \(p\), let

\[
\Gamma_G(p)=\sum_{a\in\mathbb F_p^k}
\exp\bigl(2\pi i E_G(a)/p\bigr).
\]

Fix one vertex height to zero and separate the free common shift. The remaining quadratic form has a reduced Laplacian matrix with determinant \(\tau(G)\), the spanning-tree count. If \(p\nmid\tau(G)\), the reduced form is nondegenerate. Standard finite-field diagonalization then gives

\[
\Gamma_G(p)=p\left(\frac{\tau(G)}p\right)g_p^{\,k-1},
\qquad
g_p=\sum_{u\in\mathbb F_p}e^{2\pi i u^2/p}.
\tag{SNG-I022}
\]

In particular its absolute value is \(p^{(k+1)/2}\). When \(p\) divides the spanning-tree count, the reduced quadratic form is singular and this nondegenerate formula must be replaced by its rank-sensitive version, which holds for every graph, connected or not.

**Theorem SNG-F30 (rank-sensitive Gauss sum).** Let \(p\) be an odd prime, \(\omega=e^{2\pi i/p}\), and \(g_p=\sum_{u\in\mathbb F_p}\omega^{u^2}\). Let \(P\in GL_k(\mathbb F_p)\) satisfy \(P^{\top}\Delta_GP\equiv\operatorname{diag}(\lambda_1,\ldots,\lambda_r,0,\ldots,0)\) with \(\lambda_i\not\equiv0\). Then \(r\) is the rank of \(\Delta_G\) over \(\mathbb F_p\), the class of \(D=\lambda_1\cdots\lambda_r\) modulo squares does not depend on \(P\), and
\[
\Gamma_G(p)=p^{\,k-r}\left(\frac Dp\right)g_p^{\,r},
\]
with the convention that the right side is \(p^k\) when \(r=0\).

*Proof.* Energy is the integer quadratic form \(a^\top\Delta_Ga\), so \(\omega^{E_G(a)}\) depends only on \(a\bmod p\). Every symmetric matrix over a field of odd characteristic is congruent to a diagonal one: if some diagonal entry is nonzero, move it to the pivot and clear its row and column by the substitutions \(e_j\mapsto e_j-(m_{kj}/m_{kk})e_k\); if all remaining diagonal entries vanish but \(m_{ij}\ne0\), replace \(e_i\) by \(e_i+e_j\), whose new diagonal entry is \(2m_{ij}\ne0\) because \(p\) is odd; if the remaining block is zero, stop. Since \(P\) is invertible, \(a=Pb\) is a bijection of \(\mathbb F_p^k\), so
\[
\Gamma_G(p)=\sum_b\omega^{\sum_i\lambda_ib_i^2}=\prod_{i\le r}\bigl(\sum_{u}\omega^{\lambda_iu^2}\bigr)\cdot p^{\,k-r}.
\]
Each zero diagonal entry is a singular direction and contributes a full factor \(p\); these include the constant vector of every connected component, and further directions at primes dividing invariant factors of the Laplacian. For \(\lambda\ne0\), substituting \(u\mapsto\lambda^{-1}u\) when \(\lambda\) is a square, and counting the solutions of \(u^2=v\) when it is not, gives \(\sum_u\omega^{\lambda u^2}=\left(\frac\lambda p\right)g_p\). Multiplicativity of the Legendre symbol gives the formula. Rank is a congruence invariant. The radical \(R=\ker\Delta_G\) is intrinsic, and the induced nondegenerate form on \(\mathbb F_p^k/R\) has Gram determinant \(D\) in the basis given by the images of the first \(r\) columns of \(P\). A change of basis multiplies it by a nonzero square, so the square class is well defined. \(\square\)

For a connected graph with \(p\nmid\tau(G)\), the rank is \(k-1\) and \(D\) has the square class of \(\tau(G)\), which recovers SNG-I022. The triangle at \(p=3\) is an exceptional prime: \(\tau=3\), and \(\Delta_{K_3}\equiv2J\pmod 3\) has rank one, with \(D=2\) a non-square. Hence \(\Gamma_{K_3}(3)=-9g_3=-9-18\omega\), whereas the nondegenerate formula would predict a multiple of \(g_3^2\). The implementation `src/singularity/gauss.py` returns the diagonalizing matrix as a witness and rechecks \(P^\top\Delta_GP\) and \(\det P\ne0\) exactly. It compares \(p^{k-r}(D/p)g_p^r\) with the direct residue-cube sum in \(\mathbb Z[t]/\Phi_p(t)\), with no square root of \(p\), on all labeled graphs with at most four vertices for \(p=3,5,7\) and all five-vertex graphs for \(p=3\). It rejects \(p=2\), composite moduli and prime powers, which this theorem does not cover. This provides a defined arithmetic role for discriminant primes: they signal additional modular degeneracy. It does not make every finite-conductor phase statistic complete for graph reconstruction.

## What the new direction actually adds

The archival programs often sought an invariant that survived a passage from a large object to a smaller representation. That ambition remains useful, but the present project asks a more relational inverse question: what is preserved when one counts every nested height pattern while forgetting which vertex carried it? A binary subset census counts one boundary at a time. A two-level height configuration simultaneously places two nested boundaries and records edges that cross both. The exact co-binary example proves that this added relation is not determined by the entire one-boundary census.

The difference should not be called a higher-body interaction in the energy. The energy remains a sum of pairwise edge terms. Higher relational information appears because the observation organizes those same pairwise terms across several nested threshold sets. This distinction matters both mathematically and historically. The project has changed what is retained about a population, rather than positing a new force or claiming a new physical realization.

The resulting research program is therefore internal to mathematics at this stage. It studies a hierarchy of marked populations, their inverse problems, exact computation, and arithmetic singularities after a precisely defined Euler lift. Older physical, commercial, or external ambitions neither prove its significance nor limit the objects it can now examine. The useful inheritance is the ability to calculate exact populations, distinguish insufficient representations, and move consistently between valuation, lattice and conductor descriptions. The new work must earn its further claims through theorems or explicit counterexamples about the height hierarchy itself.

One further lesson from the archive is that a change of coefficient domain and a change of question are separate moves. Exact cyclotomic arithmetic can certify a finite phase sum that floating-point recognition only suggests. Exact integer arithmetic can certify the histogram of a large finite population. Neither act automatically changes what the histogram measures. A perfectly certified binary census remains a binary census. The co-binary example makes that point without relying on measurement noise, numerical instability, unverified physical premises or imperfect training data: even exact binary information can be insufficient for an exact higher-height question.

Conversely, enlarging the question does not require abandoning the old exact arithmetic. The same graph can be studied through an integer coefficient table, a real parameter \(0<q<1\), a cyclotomic specialization, a cut-lattice theta series, or a Dirichlet series. Each view should carry an explicit account of the markers it retains. A statement about the full marked hierarchy cannot be replaced by a statement about one root-of-unity specialization. A statement about an Euler singularity cannot substitute for equality of every local coefficient. The creative move is the selection of the relational population, while the archival discipline supplies the maps that let its different views be compared honestly.
