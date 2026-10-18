# Order reciprocity: result record for P22

**Outcome:** a proved negative result for the energy-weighted extension, with the classical reciprocities checked as background. Full statements and proofs are in [chapter 13, section 13.6](../chapters/13_research_program.md).

| Statement | Status | Evidence |
|---|---|---|
| Strict assignments in \(\{0,\ldots,H\}\) number \((-1)^n\Omega(P,-(H+1))\) | Established background (Stanley) | `tests/test_reciprocity.py::EstablishedReciprocityTests.test_order_polynomial_reciprocity`, six posets, \(H\le4\) |
| \(S_P(x)=(-1)^nW_P(1/x)\) for weak maps \(a\ge0\) and strict maps \(a\ge1\), with chamber numerators | Established background; the chamber form is the project's derivation | `test_p_partition_reciprocity_as_rational_functions`, six posets, series through \(x^8\) |
| SNG-F34: for the 2-chain with its edge, the energy-weighted \(W,S\) are not rational in \(x\) over \(\mathbb Q(q)\), so the reciprocity has no weighted analogue of the same form | Proved project result (negative) | Chapter 13 proof; `EnergyObstructionTests`: closed forms through \(x^{12}\), nonzero Hankel determinants for \(k\le3\) |

**Translation to heights.** "Weak" means \(a_i\le a_j\) for \(i<_Pj\); "strict" means \(a_i<a_j\). In the bounded form both use values \(0,\ldots,H\), so the order polynomial argument is \(H+1\). In the unbounded P-partition form, strict maps also require every height to be at least \(1\), matching Stanley's convention.

**Smallest counterexample.** The two-element chain is the smallest poset with a relation. On a single vertex, or on any edgeless graph, the energy weight is trivial and the classical identity holds. With one edge on the chain, the weighted series contains the theta-type factor \(\sum_dx^dq^{d^2}\), whose coefficients satisfy no linear recurrence over \(\mathbb Q(q)\).

**Open.** A weighted reciprocity with boundary terms, or for a transformed analytic function of \(x\), is not excluded. Any such claim must define the evaluation it uses.
