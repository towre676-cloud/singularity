# Collision cases (P31 ledger)

This ledger records the collisions selected for structural resolution, the mechanism found for each, and the maps that were tried and failed. Every separation listed has its exact first discrepancy verified through all lower volumes. No pair with equal full series is claimed.

## 1. Late collisions in the connected census (selected first)

The census population is the connected graphs with at most six vertices (`results/census_manifest.json`). The pairs that agree through volume two are exactly the 14 pairs below, all on six vertices. They were selected before any further computation, as the smallest unresolved collisions. Source data: `results/late_collisions.json`, produced by `scripts/reproduce.py`.

| Census codes | n | First difference volume | Triangles | Ordered adjacent-degree sector | Induced-triple sector |
|---|---|---|---|---|---|
| 1141, 1197 | 6 | 3 | 1, 0 | equal | differs |
| 1270, 1459 | 6 | 3 | 1, 0 | equal | differs |
| 2282, 2409 | 6 | 3 | 1, 0 | equal | differs |
| 3441, 5717 | 6 | 3 | 1, 0 | equal | differs |
| 3441, 5779 | 6 | 3 | 1, 2 | equal | differs |
| 3452, 3870 | 6 | 3 | 1, 0 | equal | differs |
| 3452, 3885 | 6 | 3 | 1, 2 | equal | differs |
| 3578, 3949 | 6 | 3 | 2, 3 | equal | differs |
| 3687, 6735 | 6 | 3 | 2, 3 | equal | differs |
| 3870, 3885 | 6 | 3 | 0, 2 | equal | differs |
| 3871, 5791 | 6 | 3 | 3, 4 | equal | differs |
| 5717, 5779 | 6 | 3 | 0, 2 | equal | differs |
| 7672, 7916 | 6 | 3 | 0, 2 | equal | differs |
| 7673, 7917 | 6 | 3 | 3, 4 | equal | differs |

**Mechanism.** Every pair agrees in the ordered adjacent-degree sector \(2e_i+e_j\) of SNG-F14 and differs in the induced-triple sector at volume three. The triangle counts differ in every pair. This is the classical triangle mechanism. For regular pairs it is the case \(g=3\) of SNG-F56: the first difference is \(\Delta N_3\,q^{(d+\lambda-2)3}(1-q^2)^3\) times the triangle difference.

**Attempted map.** A single Whitney twist at a two-vertex separator. `scripts/collision_cases.py` (receipt `results/collision_cases.json`, checked in CI) tests every two-vertex separator of either graph and every split of the remaining components into two sides, in both directions. That is 282 twists in total; the two pairs 7672/7916 and 7673/7917 have no two-vertex separator. No twist reproduces the partner. As a positive control, `tests/test_collision_cases.py` confirms that the same search finds retained straight/twisted gluings. The separation is therefore not the twist mechanism.

## 2. Structural families with proved mechanisms

| Family | First discrepancy | Mechanism | Where verified |
|---|---|---|---|
| Cube vs Möbius ladder (8 vertices, cubic, girth 4) | volume 4, \(2q^4(1-q^2)^4\) in \(L\) | square counts 6 vs 4 (SNG-F56) | `results/exact_examples.json`, `results/locality_family.json` |
| Prism vs \(K_{3,3}\) | volume 3, \(2q^3(1-q^2)^3\) in \(L\) | triangle counts 2 vs 0 (SNG-F56) | `results/locality_family.json` |
| \(4\times4\) rook vs Shrikhande (16 vertices, 6-regular, cospectral) | volume 4, \(8q^{12+4\lambda}(1-q^2)^6\) | \(K_4\) counts 8 vs 0; triangles, squares and diamond subgraphs agree (SNG-F61) | `results/overlap_hierarchy.json`, `results/loop_series.json` |
| \(C_{2g}\) vs \(C_g\sqcup C_g\), all \(g\ge3\) | volume \(g\), \(2[q^2(1-q^2)]^g\) in \(A\) | exterior-square transfer argument; \(g\)-cycle counts (SNG-F56); reconstruction of 2-regular graphs at the sharp budget \(\lfloor n/2\rfloor\) (SNG-F57) | `results/locality_family.json` |
| Dominating blocks over \(C_{12}\) and \(C_6\sqcup C_6\) | volume 6 under every context, \(729/8{,}388{,}608\) at \(q=1/2\) | unit-triangular context operator (SNG-F54) | `results/locality_family.json` |
| Pendant-cycle family \(G_{p,\ell}\) | depth \(p+1\), \(q^2(1-q)^2(1-q^2)^p\) | 2x2 transfer and placement lemma (SNG-F36) | `results/pendant_family.json` |
| Whitney twists of blocks | first nonzero antisymmetric pairing | \(L-L_{\mathrm{tw}}=2\sum x^{|b|}A_1A_2\) (SNG-F41, SNG-F42, SNG-F45) | `results/whitney_switches.json` |
| Regular graphs of girth \(\ge g\) with equal cycle counts | first unequal \(N_\ell\) or theta count | loop decomposition and first overlap (SNG-F60, SNG-F61) | `results/loop_series.json` |

## 3. Bounded census outcomes

On all graphs with eight vertices (12,346 classes, disconnected ones included), twenty pairs agree through volume five, the same twenty for \(A_H\), \(L_H\) and the moment series. All are connected with equal degree sequences, and all separate at volume six (`results/loop_series.json`, `collision_census`). Their individual mechanisms are not recorded here; the bounded statement is that the volume-six series separate all 8-vertex graphs.

## 4. Remaining conjectures

- Whether any two non-isomorphic graphs have equal full local series \(L_H\), or equal \(A_H\), is open. The moment series is complete at every fixed \(q_0\in(0,1)\) (SNG-F58).
- For regular graphs beyond the first overlap, the next corrections involve larger multicyclic footprints. They are not classified.
