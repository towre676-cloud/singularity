# NX15: actual graph populations versus formal invisible vectors

This work combines exact necessary filters, two complete bounded graph constructors, and a broad structural exclusion obtained from the newly proved threshold inverse. No graph realizing the surviving general frontier is reported. A nonzero vector in a formal nullspace is not an adjacency matrix, and agreement through a finite budget is not equality of full series.

## Which difference is being sought?

For an ordered two-terminal block, use the existing raw kernel convention

\[
 K_G(s,t;x,q)=\sum_{h_I\ge0}x^{|h_I|}q^{E_G(s,t,h_I)}.
\]

The total interface volume is \(s+t+|h_I|\). Symmetrization adds the two ordered terminal states once each when they differ; it does not average or divide height multiplicities by automorphism counts.

At fixed rational pinning, the retained terminal-edge candidate at total volume 38 has states \((1,18),(6,17),(10,15)\), all on the circle \(s^2+t^2=325\). Their required interior volumes are 19, 15, and 13. Write

\[
 y=(q^{289},q^{121},q^{25}),\qquad
 v=(y_3-y_2,\ y_1-y_3,\ y_2-y_1).
\]

Then \(\sum v_i=\sum y_iv_i=0\) by cancellation. At the edge-free frontier, total volume 11, the formal vector is \(e_{(0,5)}-e_{(3,4)}\), with interior volumes six and four. These calculations reproduce the candidate frontiers. They do not construct graph pairs. The earlier rational interpolation hypotheses remain in force; the exceptional irrational parameters are not silently included.

For the declared symmetric context language, the existing quotient characterization implies that a frontier-only hidden difference must agree at every lower interface volume. Therefore any exact discrepancy already found in a lower kernel prefix excludes that pair from realizing the frontier vector. The search uses this necessary condition rather than computing enormous volume-38 populations.

## Necessary charge-population restrictions

The charge table groups original interior assignments by volume \(j\), terminal charge \(Q\), and energy. Every coefficient is a nonnegative integer. If the interior has \(m\) vertices, its total population in slice \(j\) is

\[
 \sum_{Q,e}a_{j,Q,e}=\binom{j+m-1}{m-1}\quad(m>0).
\]

For zero interior vertices it is one at slice zero and zero otherwise. A charge produced by \(j\) units of height must be a sum of \(j\) available terminal-neighborhood patterns from \(\{0,1\}^2\). The necessary relaxation checks this semigroup condition, nonnegative energies, positive stored multiplicities, and exact slice population totals. All 64 labeled four-vertex graphs pass the filter through interior slice three. A deliberately altered multiplicity and an impossible zero-slice charge are rejected.

These checks are only necessary. They do not ensure that every slice arises from one common graph, that interior-edge energies are compatible, or that an integer charge table has an adjacency realization. This distinction makes the filter useful for rejection while preventing it from manufacturing false witnesses.

## Two complete bounded exclusions

Every census is stratified by known graph order. Isomorphism reduction fixes the terminal set, allows its swap, and permutes only interior labels. This reduction selects one representative block per isomorphism class. Every kernel still counts all original labeled height assignments; no population is divided by automorphisms.

| Declared family | Labeled constructor objects | Terminal-swap block classes | Independent profiles through volume four | Result |
|---|---:|---:|---:|---|
| All labeled trees on 2–5 vertices, terminals 0 and 1 | 145 | 24 | 2,395 | Every distinct class separates in the required prefix |
| Both terminals dominate an arbitrary labeled interior on 0–4 vertices; no terminal edge | 76 | 19 | 3,004 | Every distinct class separates in the required prefix |

The tree constructor enumerates every Prüfer word. Its counts per order are \(n^{n-2}\). An independent edge-subset constructor tests every \((n-1)\)-edge set for connectedness and confirms equality of the actual labeled edge sets, not just agreement of totals. The second constructor enumerates every interior adjacency bit mask, yielding \(\sum_{m=0}^4 2^{\binom m2}=76\) objects. It is complete by direct binary encoding of every allowed interior edge.

For every representative, the bag-message terminal kernel is compared with independent weak-composition enumeration. The fixed-parameter symmetric signatures are then compared within each known-order stratum. No nonisomorphic pair survives volume four. Since a nonzero frontier difference at volume eleven must vanish at every lower interface volume under the existing quotient theorem, none of these pairs can realize it. This is a complete finite exclusion with an explicit constructor and lower-prefix certificate, not a claim about all trees, all dominating interiors, or cross-order ambiguities.

**Proposition NX15.1.** At \(q=1/2\), no pair of distinct terminal-swap isomorphism classes within either displayed known-order family realizes the edge-free volume-eleven frontier vector.

**Proof.** Constructor completeness gives the stated exhaustive object sets. Independent bag and composition kernels agree for every class. Their retained volume-four signatures are pairwise different within each order stratum. Every proposed frontier realization would have equal required lower kernel coefficients, including this prefix, contradicting one of those differences. Isomorphic representatives have identical complete kernels and cannot supply a nonzero difference. □

## Structural exclusion for threshold interiors

There is a much larger family where enumeration is unnecessary. Let both nonadjacent terminals dominate an unknown threshold interior \(H\) of known order \(m\). The existing closure operator is unit lower triangular and converts its pinned sequence \(A_{H,j}\) to the raw series of any supported single closing context. FR05 proves that, at rational \(q=A/B\), this sequence through

\[
 R_* =\min\{R\ge2:B^{2(R-1)}>m\}
\]

reconstructs the promised threshold graph. Therefore every such single closure distinguishes nonisomorphic threshold interiors by volume \(R_*\).

**Proposition NX15.2.** For a fixed rational pinning and an integer budget \(R\ge2\), two dominating blocks whose promised threshold interiors have equal known order

\[
 m<B^{2(R-1)}
\]

cannot have equal supported closure prefixes through \(R\) unless their interiors are isomorphic.

**Proof.** Invert the known unit-triangular context map at the same budget. The resulting pinned coefficient prefix meets FR05's strict cutoff inequality. Apply its inverse theorem, which uses only the known order, pinning and prefix. Both interiors reconstruct to the same canonical threshold creation word. Hence the blocks are isomorphic, and their entire ordered interfaces coincide. □

At one half, the volume-eleven ambiguity is therefore incompatible with these dominating threshold interiors whenever \(m\le2^{20}-1\). At volume 38 the analogous order bound is \(2^{74}-1\). The enormous second number is an exact structural bound, not a completed graph census or a promise that coefficients of that size can be processed cheaply. This is a new application of FR05 to the surviving interface ambiguity, not a second implementation of its reconstruction algorithm.

The class promise is essential. A successful arithmetic or charge check does not prove threshold membership. The theorem does not eliminate general balanced blocks, general trees, or arbitrary interiors with the same pinned series.

## Resource contract and replay

The supporting module is `src/singularity/realizable_interfaces.py`; the receipt is `results/realizable_interfaces.json`; run `python scripts/realizable_interfaces.py --check`. Constructor bounds, original labeled counts, isomorphism-class counts, pinning, language, lower prefix, target frontier and independent profile work are retained. Profile work is estimated as \(\binom{R+n}{n}\) per representative before the independent population engine is called. A limit refusal is an arithmetic resource error, never a fabricated negative result.

The search states distinguish `complete_bounded_exclusion` from `incomplete_budget`. A surviving lower-prefix class would remain incomplete until its whole frontier condition and independent glued observations were checked. The current two complete exclusions need no such positive-pair check because no nonisomorphic lower-prefix survivor exists. The general realization questions remain open outside the precise families above.
