# Proposed extensions from the impact discussion

These are optional future research directions, not accepted theorems or completed modules. They preserve the original P01–P36 program. Use X01–X04 as discussion identifiers until a deliberate roadmap revision gives them full acceptance contracts. Relevant original work can motivate them, but a new idea does not discharge an old criterion.

## X01: terminal-conditioned response and gluing

**Connects to:** P09–P12 and P15–P16. **Question:** what must a graph fragment retain to remain exactly usable when another fragment is attached through named terminals?

For ordered terminals B, internal vertices I and heights bounded by H, consider

\[
K_G^B(b;x,q)=\sum_{a_I\in\{0,\ldots,H\}^{I}}
x^{\sum_{i\in I}a_i}q^{E_G(a_I,b)}.
\]

Terminal volume is excluded from the kernel. Two edge-disjoint blocks meeting only at their named terminals assemble by summing products over the common terminal heights and multiplying by x raised to terminal volume once. A suitable implementation must reject duplicate shared-terminal edges or prove an explicit correction, retain terminal order and validate volume cutoffs.

The three-vertex path provides a tiny diagnostic. Pin its designated terminal to zero. The internal-volume-one coefficient is 2q when the terminal is the center, and q+q^2 when it is an endpoint. The closed graph is the same; attachment information is different. This is an elementary check, not a new graph-reconstruction theorem.

An interesting two-terminal calculation to prove and test concerns straight versus twisted gluing of blocks A and B. Pairing terminal heights i<j suggests the discrepancy

\[
\sum_{i<j}x^{i+j}
\bigl(K_A(i,j)-K_A(j,i)\bigr)
\bigl(K_B(i,j)-K_B(j,i)\bigr).
\]

Derive this by pairing ordered boundary assignments before asserting it. For identical blocks it becomes a sum of squares at positive real x,q, subject to the same edge-disjoint conventions. Determine when this gives a meaningful structural distinction rather than a trivial degree witness. Full span marking and minimum-zero normalization need their own assembly bookkeeping.

## X02: minimal exact interfaces relative to future contexts

**Connects to:** P12, P15–P16 and X01. **Question:** for a declared class C of attachments, which fragment descriptions preserve every resulting answer?

\[
G\equiv_CG'\iff Z_{G\cup C_0}=Z_{G'\cup C_0}
\text{ for every permitted attachment }C_0\in C.
\]

This is contextual equivalence. Conditional partition functions, connection matrices and graph algebras are established background, not an invention of this project. A possible contribution is a sharp specialization with constructive reductions, explicit resource bounds and a nontrivial class admitting useful compression.

The coupling matrix W_ij=q^((i-j)^2), 0<=i,j<=H, factors into invertible diagonal matrices and a Vandermonde matrix, so its rank is H+1 for 0<q<1. For b independent couplings, tensor rank as a matrix is (H+1)^b. If permitted probes include independently pinned boundary heights, this creates a lower bound for exact linear response representations. It is not a lower bound for every conceivable nonlinear encoding, nor does rank alone quantify bit cost or efficient realizability. Restricted future contexts, symmetries or certified approximation may change the practical problem.

Primary background to check before a novelty claim: Freedman, Lovasz and Schrijver, Reflection positivity, rank connectivity, and homomorphism of graphs, MSR-TR-2004-41; Lovasz, The rank of connection matrices and the dimension of graph algebras, MSR-TR-2004-82. Author pages: https://www.microsoft.com/en-us/research/publication/reflection-positivity-rank-connectivity-and-homomorphism-of-graphs/ and https://www.microsoft.com/en-us/research/publication/the-rank-of-connection-matrices-and-the-dimension-of-graph-algebras/ .

## X03: arbitrary finite blindness with eventual visibility

**Connects to:** P25 and P29–P32. **Target, not yet a theorem:** for every R, construct nonisomorphic equal-order graphs whose local height coefficients agree through volume R but whose full series differ.

One proposed route uses equal-order regular graphs with sufficiently large girth. Supports smaller than the girth induce forests; prove, rather than assume, that the relevant decorated small-support counts depend only on order and degree. Noninjective embeddings and disconnected supports require explicit accounting. A bridge in one graph and no bridge in the other could force eventual separation: a bridge cut produces an energy-one minimum-zero binary profile, while a bridgeless graph has no energy-one profile. The existence of compatible graph orders, regularity, girth and connectivity must be established in the construction.

Do not infer this result from a finite search or from a local-neighborhood analogy. A successful proof would turn isolated delayed witnesses into an infinite structural statement. The complementary positive task is a depth or reconstruction theorem on a narrowly specified family. It may be more productive to disprove an overly strong conjecture with a certified family than to push an unexplained cutoff higher.

## X04: fixed-cost relational observation benchmarks

**Connects to:** P29–P32 and X01–X03. **Question:** do height-derived observations retain useful distinctions per unit of computational cost compared with well-specified alternatives?

Use fixed input populations, degree and graphlet baselines, explicit Weisfeiler-Leman variants where implemented, and matched resource budgets. Differentiate graph separation from downstream predictive accuracy. A small symbolic separation does not establish a learning advantage. Relevant primary background includes Beyond Weisfeiler-Lehman: A Quantitative Framework for GNN Expressiveness, arXiv:2401.08514. Any learning claim needs a separate experimental design, data split, leakage check, uncertainty report and reproducible baseline implementation.

## Choosing among these directions

First close cheap foundational acceptance gaps, particularly P01–P03. Then prefer an infinite-family theorem, a precise impossibility boundary or a demonstrated useful exact interface to additional terminology. The Euler product remains an analytic expression of the local information; it cannot restore correspondence that the local series already discarded. The strongest long-term objective is a quantitative account of which relations an observation retains, what future uses require them and what that retention costs.
