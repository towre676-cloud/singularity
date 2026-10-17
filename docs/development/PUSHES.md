# Thirty-six concrete research pushes

This is a proposed sequence after the initial release. No entry is marked complete by its presence here. A push closes when its mathematical output and acceptance criterion are both met; a negative theorem or certified counterexample can be a successful outcome. Pushes are ordered for review and integration, while the explicit dependencies identify which preparatory work can proceed independently. Every completed push should update the manuscript, release its finite inputs and outputs, and record unresolved questions in ordinary prose. A larger computation is justified by the question it settles, not by its runtime.

The sequence follows six linked paths: exact populations, separator algorithms, nested boundaries and matroids, arithmetic specializations, order geometry, and visibility. Formal proof work follows concrete definitions and certificates. General graph reconstruction is a question to be investigated, never an acceptance criterion satisfied by a finite census. The two supplied graph pairs remain fixed regression examples throughout, so an expansion cannot silently change their labeling, normalization, or first-discrepancy statements.

## P01 — Freeze the coefficient semantics

**Inputs:** the graph and height definitions of the initial release. **Outcome:** a versioned mathematical data specification covering labels, minimum-zero normalization, span, and truncation. **Acceptance:** every public function has an explicit finite meaning, and disconnected examples distinguish global from componentwise translation. **Dependencies:** the initial release. This push settles conventions before optimization introduces alternative representations.

## P02 — Add independent level-chain enumeration

**Inputs:** P01 and the nested-boundary identity. **Outcome:** a second coefficient enumerator using nonempty nested level sets with repetitions. **Acceptance:** complete marked histograms agree with weak compositions on a declared small graph population, including profiles with height gaps. **Dependencies:** P01. The implementation must charge mixed boundary terms rather than substitute absolute-difference energy.

## P03 — Publish portable coefficient certificates

**Inputs:** both enumerators and canonical graph serialization. **Outcome:** `relational-height/1` records with exact integer or rational coefficients and source digests. **Acceptance:** an independent reader rejects malformed degrees, duplicate terms, invalid edges, and altered coefficients, while reproducing all released small tables. **Dependencies:** P01–P02. Hash agreement alone does not close this push.

## P04 — Give the spectral pair a short coefficient proof

**Inputs:** the fixed seven-vertex spectral pair. **Outcome:** a human-readable volume-two classification yielding \(2q^2(1-q)^3(1+q)\). **Acceptance:** classify every profile type at volumes zero, one, and two; compare exact Laplacian characteristic polynomials; match both enumerators. **Dependencies:** P03. The proof should explain the difference through explicit degree and adjacency contributions.

## P05 — Explain the binary-census separation

**Inputs:** the second fixed graph pair and its 128 binary assignments. **Outcome:** a full binary equality certificate and a volume-three proof of the displayed discrepancy. **Acceptance:** identify the span-two profile types responsible, account for every lower coefficient, and recover the exact value at \(q=1/2\). **Dependencies:** P02–P03. Binary sampling is insufficient.

## P06 — Derive universal low-volume formulas

**Inputs:** arbitrary simple graphs and profile partitions through volume three. **Outcome:** formulas using degree statistics and explicitly defined adjacent-vertex statistics. **Acceptance:** prove each formula by a disjoint profile classification and compare it against complete small-graph enumeration. **Dependencies:** P04–P05. Any proposed graph statistic must have a definition independent of the formula it explains.

## P07 — Formalize translation normalization

**Inputs:** the finite graph energy definition and minimum-zero bijection. **Outcome:** a proof-assistant theorem for \(B=(1-x^n)L\) at coefficient level. **Acceptance:** prove injectivity, surjectivity, volume shift, and energy preservation without admitted lemmas; publish the actual build command and dependencies. **Dependencies:** P01. No analytic infinite-product library is needed for this push.

## P08 — Formalize the nested-level energy identity

**Inputs:** finite height tuples and threshold sets. **Outcome:** kernel-checked volume, span, and quadratic energy identities. **Acceptance:** allow repeated levels, prove the mixed term equals the stated edge count for nested sets, and derive binary extraction. **Dependencies:** P07. The theorem should expose the pairwise edge model rather than introduce a different interaction law.

## P09 — Implement bounded-height tree messages

**Inputs:** rooted trees, height bound \(H\), and volume bound \(R\). **Outcome:** exact separator-conditioned message polynomials. **Acceptance:** prove the child-product recursion, count every vertex and edge once, and match reference coefficients on paths, stars, and branched trees. **Dependencies:** P02. Report polynomial support sizes separately from height-state counts.

## P10 — Prove safe volume truncation

**Inputs:** P09's recursion and nonnegative volume exponents. **Outcome:** a theorem that intermediate reduction modulo \(x^{R+1}\) preserves the requested output. **Acceptance:** show that \(H=R\) suffices for unrestricted coefficients through \(R\), then demonstrate larger tree computations with identical semantics. **Dependencies:** P09. Benchmarks must compare complete coefficient ranges.

## P11 — Recover span by bounded-box subtraction

**Inputs:** the bounded-height polynomials \(C_H\). **Outcome:** a marked tree algorithm using \(D_H=C_H-x^nC_{H-1}\) and exact-span differences. **Acceptance:** prove the shift subtraction and compare every \((v,e,h)\) count with direct marked enumeration. **Dependencies:** P09–P10. Negative intermediate coefficients must be investigated rather than clipped to zero.

## P12 — Extend messages to bounded separators

**Inputs:** a graph with an explicitly supplied tree decomposition. **Outcome:** a bag-conditioned exact algorithm and decomposition checker. **Acceptance:** verify the decomposition axioms, prove local charge bookkeeping, and compare cycles and bounded-width examples with reference data. **Dependencies:** P10–P11. State-count and sparse polynomial-convolution costs must remain separate in the complexity discussion.

## P13 — Classify the first positive-energy layer

**Inputs:** connected graphs and marked coefficients. **Outcome:** a theorem describing minimum-energy nonconstant profiles and their relation to minimum cuts. **Acceptance:** handle possible nonbinary competitors explicitly, prove the stated multiplicities, and compare with exhaustive profiles. **Dependencies:** P06 and P08. Energy order must not be confused with volume order.

## P14 — Compute the nested-pair census

**Inputs:** all \(T\subseteq S\subseteq V\) in a declared graph population. **Outcome:** the five-statistic nested-boundary tensor described in Chapter 13. **Acceptance:** recover the span-two generating function by an explicit projection and explain the binary-census example's separation. **Dependencies:** P05 and P08. A new tensor name is not itself a structural result.

## P15 — Separate lattice information from chamber information

**Inputs:** the cut-lattice realization and minimum-zero volume functional. **Outcome:** a precise preservation question with proved sufficient conditions for marked-series equality. **Acceptance:** specify which lattice isometries preserve height volume and span, and exhibit a nontrivial worked instance or a failure of a proposed condition. **Dependencies:** P08 and P14. Abstract energy preservation alone is insufficient.

## P16 — Test Whitney switches systematically

**Inputs:** a documented family of admissible two-terminal gluings and switches. **Outcome:** exact comparison tables and either a separating pair or a transformation conjecture. **Acceptance:** verify the matroid-preserving hypotheses independently and retain tested volume bounds for unresolved pairs. **Dependencies:** P15. No finite failure to separate may be reported as universal matroid invariance.

## P17 — Add exact volume congruence filters

**Inputs:** local polynomials and a positive modulus. **Outcome:** character-filtered populations for volume residue classes. **Acceptance:** prove the root-of-unity averaging identity and compare it with direct modular filtering of assignments. **Dependencies:** P03. This filter must not be described as extracting span or the binary sector after those marks have been summed away.

## P18 — Prove root-of-unity rationality in energy

**Inputs:** an energy root of unity of order \(m\). **Outcome:** the residue-cube numerator over \((1-x^m)^n\), represented in an exact cyclotomic ring. **Acceptance:** prove the coordinate residue decomposition and reproduce local coefficients through an independent bound. **Dependencies:** P03 and P17. Complex specialization does not inherit positive-real branch assertions.

## P19 — Analyze finite quadratic Gauss sums

**Inputs:** P18 numerators at \(x=1\) and odd-prime moduli. **Outcome:** formulas in terms of Laplacian rank and nonsingular discriminant, with singular directions accounted for. **Acceptance:** compare direct residue enumeration with diagonalized forms and give explicit exceptional-prime examples. **Dependencies:** P18. Prime powers and characteristic two remain separate until proved.

## P20 — Build the disjoint order-chamber formula

**Inputs:** vertex permutations with label-based tie breaking. **Outcome:** a gap-coordinate expression for volume and quadratic energy. **Acceptance:** prove that every profile belongs to exactly one chamber, including tied heights, and match complete histograms. **Dependencies:** P02 and P06. Summing closed chambers without boundary corrections fails this criterion.

## P21 — Relate constrained heights to order polytopes

**Inputs:** an explicit finite poset of height inequalities. **Outcome:** a comparison between constrained populations and established order-polytope lattice counts. **Acceptance:** derive the unweighted bounded-height specialization with correct weak and strict inequalities, then identify what quadratic weighting adds. **Dependencies:** P20. Ordinary Ehrhart conclusions require an ordinary fixed-polytope counting problem.

## P22 — Establish one genuine reciprocity statement

**Inputs:** a precisely chosen bounded order or chamber population. **Outcome:** a proved reciprocity identity with explicit boundary terms, or a counterexample to the proposed weighted extension. **Acceptance:** verify complete small instances and give a full argument for the stated scope. **Dependencies:** P21. An analogy to Ehrhart or chromatic reciprocity does not close the push.

## P23 — Implement formal logarithmic extraction

**Inputs:** exact local coefficient polynomials through volume \(R\). **Outcome:** formal logarithm, inverse series, and finite Euler exponents using rational arithmetic. **Acceptance:** reconstruct the input truncation by multiplication and verify the Möbius coefficient identities. **Dependencies:** P03. Distinguish scalar exponents depending on \(q\) from integer combinatorial multiplicities.

## P24 — Determine exceptional energy parameters

**Inputs:** discrepancy polynomials for a graph pair. **Outcome:** exact rational or algebraic parameter strata where the first differing volume changes. **Acceptance:** isolate every real root in \((0,1)\) for the tested leading polynomials and recompute at each exceptional value. **Dependencies:** P23. A plot or a finite parameter grid cannot establish absence of roots.

## P25 — Organize successive visibility levels

**Inputs:** coefficient differences through a declared volume bound. **Outcome:** a filtration by first discrepancy, including parameter-dependent refinements. **Acceptance:** prove every reported equality below the first differing coefficient and label unresolved collisions with their tested bound. **Dependencies:** P23–P24. Claims of an unrestricted separation depth require an additional theorem.

## P26 — Make analytic remainder bounds explicit

**Inputs:** local coefficient growth bounds and a first discrepancy at \(r\). **Outcome:** a quantified normalized-factor estimate sufficient for convergence when \(s>1/(r+1)\). **Acceptance:** display constants, parameter restrictions, and treatment of finitely many small primes. **Dependencies:** P25. A formal expansion without a controlled remainder is not the analytic theorem.

## P27 — Produce controlled real singularity experiments

**Inputs:** P26 bounds and exact discrepancy exponents. **Outcome:** prime-product evaluations of the normalized positive-real remainder near \(s=1/r\). **Acceptance:** attach finite-cutoff error intervals and recover the predicted asymptotic within them. **Dependencies:** P26. Numerical slope fitting illustrates an established exponent; it does not determine the exponent's proof.

## P28 — State the available complex domain exactly

**Inputs:** fixed admissible \(q\), local factor zeros, and normalized products. **Outcome:** a local complex branch statement on an explicitly described nonvanishing domain, or a documented obstruction. **Acceptance:** specify logarithm choices and convergence uniformly on compact subsets. **Dependencies:** P26. Do not infer global meromorphic continuation from real-axis control.

## P29 — Specify a complete finite graph census

**Inputs:** a chosen graph class, order bound, and graph-generation method. **Outcome:** a canonical input manifest with isomorphism handling documented. **Acceptance:** independently reconcile population counts, generation options, and graph hashes. **Dependencies:** P03. Degree and spectrum filters are not a substitute for a complete census or a graph-isomorphism decision.

## P30 — Measure collision classes across invariants

**Inputs:** P29's fixed graph population and exact coefficient algorithms. **Outcome:** collision partitions for spectra, binary census, and specified height truncations. **Acceptance:** release full class memberships, first-discrepancy witnesses, resource limits, and unresolved classes. **Dependencies:** P12, P14, and P29. Report bounded separation percentages with their exact denominator.

## P31 — Resolve targeted collisions structurally

**Inputs:** the smallest unresolved classes from P30. **Outcome:** an explicit bijection, a higher-volume separation, or a precise remaining conjecture for each selected pair. **Acceptance:** explain the mechanism rather than only increase a cutoff; retain negative results. **Dependencies:** P16 and P30. A full-series equality claim needs an all-volume argument.

## P32 — Seek a separation bound for one graph family

**Inputs:** low-volume formulas, tree messages, and collision evidence. **Outcome:** a proved first-separation bound for a narrowly stated family, or an explicit family defeating the proposed bound. **Acceptance:** parameterize the family and prove the statement uniformly. **Dependencies:** P06, P12, and P31. Complete graph reconstruction remains outside the claim unless proved separately.

## P33 — Verify concrete coefficient certificates in a kernel

**Inputs:** P03 certificates and the formal finite identities. **Outcome:** a checker connecting released tables to the mathematical coefficient definition. **Acceptance:** kernel-check both decisive pair certificates and reject a changed coefficient or graph edge. **Dependencies:** P07–P08 and P23. A verified parser alone does not verify enumerated multiplicities.

## P34 — Formalize the visibility comparison boundary

**Inputs:** the finite first-discrepancy theorem and available analytic libraries. **Outcome:** a formal statement connecting the normalized local expansion to the real zeta-factor asymptotic. **Acceptance:** expose every imported theorem and any unformalized premise; claim complete verification only when the full chain compiles. **Dependencies:** P26 and P33. Missing library infrastructure is recorded explicitly.

## P35 — Release the first focused manuscript

**Inputs:** the exact examples, finite proofs, and real comparison theorem. **Outcome:** a literature-positioned paper matching Candidate A in Chapter 14, with source and reproducible artifacts. **Acceptance:** independently replay decisive coefficients, reconcile every claim with its proof or certificate, and remove unsupported priority language. **Dependencies:** P04–P05, P26–P27, and P33; formal analytics are included only to their achieved scope.

## P36 — Choose the second paper from actual results

**Inputs:** the tree, matroid, arithmetic, and order outcomes. **Outcome:** one coherent methods or structural paper, plus an updated open-problem ledger. **Acceptance:** select a theorem or decisive negative classification as its center, complete the relevant literature comparison, and package reproducible data. **Dependencies:** P19, P22, P31–P32, and P35. Do not combine unfinished paths merely to make the manuscript larger.

The final decision is mathematical. If the work yields only a useful enumerator and two small examples, the release should say so clearly. If it yields a family theorem, a genuine comparison boundary, or a sharp analytic statement with quantitative control, the paper should lead with that result. The plan is designed to make these outcomes distinguishable early enough that the next few dozen pushes accumulate knowledge rather than accumulate terminology.
