# PerfectJet observation-design bridge

The volume-eight graph-height reader and PerfectJet now share an independently
replayable exact observation-design contract.

Singularity continues to own the graph combinatorics, realizability theorem,
and retained six-/seven-coordinate models. PerfectJet is used only for the
generic linear-algebra problem:

1. take exact polynomial response vectors \(f_1,\dots,f_d\);
2. choose \(d\) distinct coefficient degrees;
3. build the square measurement matrix;
4. reject singular panels exactly;
5. minimize
   \[
   \|M^{-1}\|_\infty
   \]
   over the complete candidate set.

The bridge independently reproduces the existing general optimum

\[
(4,8,12,14,18,24,26),\qquad
\|M^{-1}\|_\infty=\frac{93093}{14165},
\]

and the connected optimum

\[
(6,10,14,18,24,26),\qquad
\|M^{-1}\|_\infty=\frac{44191}{19786},
\]

including the connected determinant \(74791080\), exhaustive subset count,
number of invertible panels, and uniqueness of the optimum.

This does **not** enlarge the optimization domain: both implementations still
optimize only over distinct, unscaled, single-\(q\)-coefficient measurements.
Arbitrary rational linear sensors remain a larger research problem.
