# The complete fourth jet and the uniform order-fifteen ceiling

This supplement advances Revision 4 of *What Must Survive II*. It proves a finite formula for the entire fourth jet and a computer-assisted uniform upper bound with an exact leading-amplitude formula. It does **not** prove that a nonzero-amplitude lift exists at every later volume. Nor does it settle the next promotion, completeness, or physical annular minimality.

The arguments use the established loop law and its Bethe fixed point. All polynomial arithmetic below is exact in characteristic zero; pole means pole at t=infinity after normalization by q^(3V), with t=q^2 and f=(1-t)/t. The local degree checks are finite symbolic computations, not proof-assistant formalizations or literature-priority claims.

## 1. A finite formula for the complete fourth jet

Let Q be connected, leafless and subcubic, with k vertices and E edges. The degree labels d_u are degrees in Q, **not** degrees in an induced defect subgraph. Let

T_Q = q^(3k) f^E,   pi=p(1)/(x q^3),   phi=F(1,1)/f.

Use the Bethe data B,p,F of Revision 4, and define

rho_d(h) = p(h)/p(1) * (F(h,1)/F(1,1))^d,
psi(a,b) = F(a,b) F(1,1)/(F(a,1) F(1,b)).

For a vertex subset S let

Z_S = sum over T subset S and h:T->{0,2,3,4,5}
      product_(u in T) rho_(d_u)(h_u)
      product_(uv in E(Q[T])) psi(h_u,h_v).

All operations are truncated modulo x^5. The empty assignment has weight one. Define the subset cumulant

K_U = sum_(S subset U) (-1)^(|U|-|S|) log Z_S.

Set

L_j(Q) = [x^j] { k log pi + E log phi
                   + sum_(U subset V(Q), Q[U] connected, 1<=|U|<=4) K_U }.

Then the coefficients Theta_(Q,s)=[x^(k+s)]Theta(Q), for 0<=s<=4, are exactly T_Q times the coefficients of exp(sum_(j=1)^4 L_j x^j). In particular

Theta_(Q,4) = T_Q * (L_4 + L_1 L_3 + L_2^2/2
                         + L_1^2 L_2/2 + L_1^4/24).

This is a finite formula for every pattern size, not a fitted interpolation on a pattern census.

### Proof of truncation and locality

For h>=2, rho_d(h) has x-valuation h-1. For h=0 its valuation is d-1. The interaction psi has nonnegative x-valuation after these factors are extracted. Thus every defect vertex costs at least one order. Heights >=6 cost at least five orders and cannot enter J_4. Height **5 does enter** and must not be dropped from the single-site term.

Subset inversion gives log Z_V=sum_(U subset V) K_U. If Q[U] is disconnected, Z factors over its components, so K_U=0. Since each vertex of U must occur in a surviving mixed term, K_U=O(x^|U|). Consequently all connected subsets of size above four can be discarded modulo x^5. Exponentiation gives the displayed formula.

### The external polymer correction

Write J_4(Q)=[x^(k+4)]b_Q. For an unordered polymer pair A,B with edge union Q, put s=|V(A)|+|V(B)|-k. Then

J_4(Q) = Theta_(Q,4)
 - sum_(unordered pairs A,B, union Q, s<=4)
     1/(1+1_(A=B)) * sum_(a+b=4-s) Theta_(A,a) Theta_(B,b)
 + sum_(unordered triples C_1,C_2,C_3, union Q,
         sum_i |V(C_i)|=k+4)
     phi(H)/product_C multiplicity(C)! * product_i Theta_(C_i,0).

H is the vertex-overlap graph of the three polymers. Its Ursell coefficient is 1 for a path, 2 for a triangle, and zero when disconnected. Repeated polymers are included.

To see completeness, an ordering of a connected cluster can be chosen in which every new polymer intersects the earlier union. Two leafless subgraphs of a subcubic graph sharing a vertex share an edge there, hence at least two vertices. A cluster of p polymers therefore has total vertex multiplicity at least k+2(p-1). At excess four, p<=3. Triples can contribute only at their leading order. This proves that the formula omits no external cluster term.

The same argument yields a general finite jet formula: at excess r, defect supports have at most r vertices, defect heights have an explicit finite cutoff, and at most floor(r/2)+1 polymers enter. No universal finite pattern-size cutoff for the entire invariant is claimed.

## 2. The exact promoted-edge coefficient

Let G_ab be the connected two-site contribution K_U with endpoint degree labels a,b. Define

gamma_4 = [x^4](G_22 - 2G_23 + G_33).

Exact rational-function calculation gives

gamma_4 = -q^6 (q^2-1)(q^2+1)^3 R(q^2)/2,

where

R(t) = 4t^17 + 8t^16 + 20t^15 + 26t^14 + 40t^13
     + 42t^12 + 24t^11 - 52t^10 - 158t^9 - 178t^8
     - 50t^7 + 172t^6 + 179t^5 + 6t^4 - 96t^3
     - 2t^2 + 21t - 2.

This is the complete connected-edge logarithmic coefficient. It is not by itself the whole J_4; the Bell-polynomial terms, larger defect supports and external polymer terms above are also required.

For a direction at size k=V-4 put

A(f)=sum_E (sum_(Q of size k and edge count E) z_Q e_22(Q)) f^(E+1).

Its normalized gamma_4 contribution at volume V is exactly

                   (1+t)^3 R(t) A(f)/(2t^2).

The factors and sign follow from f=(1-t)/t, including the division by f introduced by the E+1 convention in A.

## 3. Uniform ceiling and leading amplitude

**Theorem.** For V>=14 and any rational direction z supported on patterns of sizes V-4 through V and killed by every earlier row, write A=(1+f)^3 B(f). Then

q^(-3V) [x^V] sum_Q z_Q b_Q
   = (1+t)^3 R(t) A(f)/(2t^2) + H(t),

where H has pole order at infinity at most **13**. Consequently every such direction has pole order at most **15**, and its coefficient of t^15 is

                            2 B(-1).

A direction has pole exactly fifteen if and only if B(-1) is nonzero.

### Proof and finite symbolic certificates

The first active row separates the grouped counts by edge number, forcing all grouped sums at size k to vanish. The next row does the same at size k+1. The row at k+2 then forces (1+f)^3 to divide A: all other terms in that equation are polynomial in f, while (2+f)^3/(1+f)^3 has exactly that denominator.

To bound the remaining terms, decompose the logarithmic coefficient as a grouped base plus e_22 gamma_j and the connected defect supports of size three and four. Degree identities e_23=2n_2-2e_22, e_33=E-2n_2+e_22 give this decomposition without assumptions on the pattern size. The exact symbolic normalized pole bounds are:

- grouped base at orders 1 and 2: at most 3 and 9;
- gamma_2, gamma_3, gamma_4: 3, 9, 18;
- three-site coefficient at order 3: at most 10 (the explicit certificate supplies the sharper values);
- three-site coefficient at order 4: at most 13;
- four-site coefficient at order 4: at most 9.

The last two checks exhaust all 10 admissible degree-labelled connected three-site types and all 30 four-site types. The script uses the finite subset formula above in a rational function field; it checks exact degrees, with no sampling in q. Coefficients from grouped-base products vanish on the lowest grouped sums. Every remaining Bell-polynomial cross term has pole at most 13: base_1*gamma_3 <=12, base_2*gamma_2 <=12, base_1^2*gamma_2 <=9, gamma_2^2 <=6, and base_1*three_site_3 <=13. Pair-polymer corrections have at most two residual jet orders and hence pole at most 9; triples have no residual order. At higher support sizes only J_3,J_2,J_1,J_0 enter. The grouped J_3 base vanishes at size k+1, and the surviving higher-size terms again have pole at most 13. These cover every term of the complete formula.

Finally 1+f=1/t, so (1+t)^3 A=(1+1/t)^3 B(-1+1/t). Since R/(2t^2)=2t^15+O(t^14), the leading term is 2B(-1)t^15. The remainder cannot change it. This proves the theorem with a finite symbolic computation as part of its certificate.

**What this does not prove.** A uniform ceiling is not uniform attainment. It remains to prove, for every V>=14, that the full earlier-row kernel contains a direction with B(-1) nonzero. The onset condition is necessary; it does not supply that lift. At V=14, B=c f^12 and the supplied witness has c=-10, hence amplitude -20, as predicted.

## 4. Exact rational profile at volume fourteen

The new independent rank audit uses the three-prime reconstructed rational rows directly, not the original rational-reconstruction helper. It confirms:

- W(14,3): dimension 14;
- W(14,4): dimension 19;
- exact leading-pole profile: -7,-6,...,10,15;
- all rows above energy 72 lie in the earlier row space;
- the increment is exactly five;
- modulo W(14,3), there is no additional low-pole kernel.

Thus the maximum and the gaps at 11,12,13,14 in the **leading-pole profile** are certified over Q. Those gaps do not mean that every polynomial has zero coefficients at these powers.

## 5. Verification scope and unresolved work

A new independent finite-formula implementation matches 215 exact coefficient evaluations at q=3/2 on 43 patterns: all patterns through six vertices plus the 24 patterns of the supplied order-15 witness. The formula includes height five, all connected defect supports through four, repeated pair polymers and triple polymers. This is an exact rational cross-check at one q, not a polynomial identity proof by sampling. The identity is justified by the subset and Ursell arguments above.

The symbolic edge coefficient, the local pole bounds and the rational profile have separate replay scripts. The supplied 31-pattern order-seventeen witness also replays against the three-prime rational rows: every earlier row vanishes, and the top coefficient is -56 at energy 73. This verifies the witness, not the heuristic promotion explanation.

The original modular engine was not rerun to volume fourteen. Correctness of its certified source rows remains the inherited trust point for rank claims.

Still open: a lift with nonzero amplitude at every later volume; the proposed order-27 onset; an all-volume window theorem; completeness of L_G; and physical annular state/readout certification. No claim of closing these problems is made.
