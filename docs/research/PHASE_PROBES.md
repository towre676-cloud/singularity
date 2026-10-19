# NX22 — Finite-volume multi-frequency arithmetic probing

This release reconstructs original integer energy histograms from complete exact phase samples. It distinguishes this finite-volume theorem from periodic full-series identities and from finite-candidate phase identification.

## Degree bound and complete transform

For a simple graph and a nonnegative integer profile of volume \(r\),
\[
 Q_G(h)=\sum_vd_vh_v^2-2\sum_{uv\in E}h_uh_v
 \le\Delta\sum_vh_v^2\le\Delta r^2.
\]
Thus every coefficient polynomial through volume \(R\) has degree at most \(D=\Delta R^2\). For \(M>D\), let \(\zeta\) be primitive of order \(M\) in the ambient exact ring \(\mathbb Z[t]/\Phi_M(t)\). Then
\[
 a_{r,e}=\frac1M\sum_{k=0}^{M-1}P_r(\zeta^k)\zeta^{-ke}.
\]
Expanding \(P_r\), the inner sum is \(M\) for equal exponent residues and zero otherwise. Since every exponent lies in \([0,D]\subset[0,M-1]\), residue equality is genuine exponent equality. This proves exact integer reconstruction including the original labeled-profile multiplicities.

All phase indices, including zero and nonprimitive phases, are embedded in the same order-\(M\) ring. The inverse sum must reduce to an integer multiple of the unit, with the integer exactly divisible by \(M\). Negative reconstructed multiplicities or incorrect total profile mass are rejected. The mass checksum is
\[
 \sum_e a_{r,e}=\binom{r+n-1}{n-1}.
\]

`phase_table` supports independent direct height-composition and periodic residue-box routes. The latter first forms a finite numerator in the same phase field, then expands its rational denominator. Their equality is tested before inverse reconstruction is compared with symbolic coefficient enumeration.

## Aliasing is a theorem boundary

For one edge at volume two,
\[
 P_2(q)=1+2q^4.
\]
Order five recovers energies zero and four with multiplicities one and two. Order four instead produces residue histogram \(\{0:3\}\). Every exact order-four phase sample is three: no arithmetic precision can undo the lost residue distinction. The unrestricted reconstruction API therefore requires the strict bound \(M>D\). An explicitly named `allow_aliasing` diagnostic mode returns residue counts and makes no original-energy claim.

The certificate checker reconstructs the graph and recomputes its degree bound. Missing or duplicate phase labels, unknown fields, noncanonical cyclotomic tuples, a forged bound, nonintegral inverse results and mass failures are rejected. `verify_phase_reconstruction` additionally reruns the declared original-model sample route.

## Three different design questions

| Problem | Assumption | Certified conclusion |
|---|---|---|
| Complete histogram recovery | Every phase, exact samples, proven \(M>D\) | All original energy multiplicities through declared volume |
| Finite candidate identification | Explicit finite candidate IDs, phase-output tables, positive rational costs | Cheapest phase panel separating that declared population |
| Support-conditioned sparse recovery | An externally declared exact support set | Unique multiplicities on that support when the checked sample matrix has full column rank |

The candidate panel optimizer enumerates every phase subset in its bounded catalogue. Candidates remain distinct original identities even if every available phase makes them observationally equal; in that case it reports infeasibility rather than deduplicating them.

For conditional sparse recovery, expand each cyclotomic sample over its rational basis. This gives an ordinary exact rational linear system in the unknown support masses. Full column rank proves uniqueness within the declared support, while consistency and nonnegative integrality validate the recovered masses. The algorithm neither discovers an unknown support nor proves compressed-sensing uniqueness across all sparse supports. In particular two support exponents congruent modulo \(M\) can never be distinguished by these phases, and rank testing rejects that case.

## Retained census and costs

`results/phase_probes.json` contains all eleven labeled graphs of orders one through three at volume two, with direct and residue routes, explicit histograms and total original profile masses. A disconnected graph with an isolated vertex is also checked at composite order six, including its nonprimitive phases. The finite four-candidate panel uses five potential phases; exhaustive subset search finds a cost-two singleton phase that separates empty, edge, path and triangle candidates at volume one. The single-edge order-five sparse example recovers counts one and two from a sample under declared support \(\{0,4\}\).

The complete transform does not promise a computational speedup. Direct enumeration costs \(\binom{R+n}{n}\) profiles per phase; a residue route can cost \(M^n\), and the ambient field dimension is \(\varphi(M)\). Polynomial coefficients can instead be obtained from \(D+1\) distinct rational evaluations by ordinary Vandermonde interpolation. Neither alternative is universally better: phase arithmetic avoids numerical approximation but retains exact coefficient and storage growth. The receipt reports which routes actually ran rather than hiding their setup.

Run `python scripts/phase_probes.py --check`.
