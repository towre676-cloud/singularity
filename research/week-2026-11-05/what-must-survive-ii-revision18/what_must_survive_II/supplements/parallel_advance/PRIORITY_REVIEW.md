# Priority review: first pass, primary sources

This is a bounded literature review, not an exhaustive novelty certification. It distinguishes established mechanisms from height-series-specific results whose priority has not been settled. Searches covered loop calculus, nonbinary/continuous extensions, core-subgraph graph polynomials, Ising graph invariants, geometric moments, and homomorphism partition functions.

## Established antecedents

1. Michael Chertkov and Vladimir Y. Chernyak, *Loop calculus in statistical physics and information science* (2006), Physical Review E 73, 065102. https://doi.org/10.1103/PhysRevE.73.065102 . Detailed companion: *Loop series for discrete statistical models on graphs*, https://arxiv.org/abs/cond-mat/0603189 . The partition function is expressed as a Bethe term with generalized-loop corrections. The no-loose-end condition is already central here. The abstract mechanism of a leafless correction expansion should not be claimed as new.

2. Ryuhei Mori, *Loop Calculus for Non-Binary Alphabets using Concepts from Information Geometry*, first submitted 2013, revised 2014. https://arxiv.org/abs/1309.6550 . Its Theorem 12 treats finite nonbinary alphabets; section VI also treats continuous alphabets and attributes an earlier continuous version to Xiao and Zhou. A countably infinite height alphabet in a formal x-adic ring still requires its own coefficientwise truncation/limit justification; the finite-spin theorem is not silently identical to that setting.

3. Yusuke Watanabe and Kenji Fukumizu, *New graph polynomials from the Bethe approximation of the Ising partition function*, preprint 2009, revised 2010, published in Combinatorics, Probability and Computing. https://arxiv.org/abs/0908.3850 . Their theta polynomial is an explicit sum over edge subsets with no degree-one vertices. For subcubic graphs the nonzero vertex factors are f2=1 and f3=gamma, so the weight of a leafless pattern is beta^E gamma^(2(E-k)). This is a particularly close antecedent, beyond generic loop-calculus terminology.

## A precise comparison with the new leading pattern weight

The leading weight in our reflection expansion is

(-2 epsilon)^E v^k (1+4v)^(E-k).

In the Watanabe-Fukumizu polynomial, set

beta=-2 epsilon v,  gamma^2=(1+4v)/v.

Then beta^E gamma^(2(E-k)) is exactly the displayed leading weight. The even exponent removes the square-root ambiguity. This is an algebraic comparison of the per-pattern leading terms, not an equality of the complete height series with their polynomial. Higher-order height corrections still carry additional local and overlap data.

Accordingly, the leading weight has a close prior combinatorial form. The specific formal height specialization, reflection-derived rank constraints, exact minimum panels, delayed jets and promotion/onset theorems need to be assessed individually; they are not automatically covered by this comparison, and no novelty declaration is made here.

## Completeness and graph-polynomial cautions

4. Daniel Andren and Klas Markstrom, *The bivariate Ising polynomial of a graph*, Discrete Applied Mathematics (2009). Publisher record: https://www.sciencedirect.com/science/article/pii/S0166218X09000821 . The record was located; access to the full publisher article was blocked, so fine-grained theorem claims from it are not treated as verified in this review. An independently computed binary-collision panel is provided instead.

5. Andrew Goodall, Guus Regts and Lluis Vena, *Matroid invariants and counting graph homomorphisms* (2016). https://arxiv.org/abs/1512.01507 . The authors characterize when finite weighted homomorphism targets produce cycle-matroid invariants. This provides a route to investigate Whitney-type invariances, but its hypotheses do not automatically apply to our countably infinite height target with the nonuniform weight x^h. No matroid-invariance claim or resulting counterexample to L_G is established here.

6. Michael Freedman, Laszlo Lovasz and Alexander Schrijver, *Reflection positivity, rank connectivity, and homomorphism of graphs*. https://arxiv.org/abs/math/0404468 . This characterizes finite weighted-target partition functions through connection-matrix conditions. It is useful framework, not a completeness theorem for one special two-parameter target family.

## Reflection-law priority

Geometric moments and Eulerian-polynomial structure have substantial prior literature. For example Yilmaz Simsek's 2024 paper gives geometric moment and characteristic-function formulas: https://onlinelibrary.wiley.com/doi/full/10.1002/mma.10066 . The elementary generating-function involution used in the current proof is not in itself enough to support a novelty claim. This search did not locate an exact prior statement of the full graph-energy triangular reflection law in our formal variables. Failure to find one is not evidence of priority.

## Recommended claim discipline

Describe the loop method as a formal height-series specialization of established loop-calculus ideas. Cite the close core-subgraph polynomial comparison explicitly. Present the exact coefficient/rank results, source code, graph realization arguments and promotion statements with their own hypotheses and certificates. Keep the reflection-law priority question open until the moment/reciprocity literature has been checked more deeply.
