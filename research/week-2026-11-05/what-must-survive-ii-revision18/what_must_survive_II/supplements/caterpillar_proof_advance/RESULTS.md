# Caterpillars: an exact spine threshold and all-parameter separation

Supplement to *What Must Survive II*, Revision 9. November 4, 2026.

The general completeness theorem for caterpillars remains open. This supplement proves completeness of shells 1 and 2 on two infinite subclasses, establishes that five canonical spine vertices are the first possible obstruction by spine length, and strengthens Revision 9's collision family to an exact two-parameter obstruction that remains invisible through volume 3. Its one-parameter subfamily is proved to separate in shell 3 for every parameter, not just three examples. A precise partial removal of the pendant contribution and a complete spine formula for the third-shell correction are supplied.

No priority claim is made. The proofs are conventional; the accompanying algebra and enumeration checks are exact but not proof-assistant formalizations. The original archive is unchanged; revision9_errata.patch contains ready-to-apply corrections to its source and rendered monograph.

## 1. One interpretation of Theorem 25 needs correction

Theorem 25 is correct. But “the imbalance marginal is already fixed by shell 1” does not follow and is false. For delta>0 let N_delta count edge pairs with outer-component imbalance |a-c|=delta. The original sign formula gives

    N_delta = [x^(n+delta)] S_2.

For trees having the same A, Theorem 25 gives

    Delta S_2 = (1-x^n) Delta B,
    Delta N_delta = - [x^delta] Delta B.

Thus A fixes the sum of the imbalance and middle-size histograms at each positive delta, not the imbalance histogram alone. There is exactly one independent new statistic, B. The earlier description in terms of two marginals overcounted their independence once A was given.

An exact 7-vertex example has common

    A=4x+x^2+x^3+x^4+x^5+4x^6,
    Delta B=x-2x^2+x^3,
    Delta S_2=(1-x^7)(x-2x^2+x^3).

Its imbalance histogram therefore changes by -1,+2,-1 at imbalances 1,2,3 despite identical A. Explicit edge lists and direct energy enumeration are in imbalance_correction.json.

## 2. Caterpillar notation and partial decontamination

Use the canonical spine induced by the nonleaf vertices. For a spine of m>=2 vertices let p_i be the number of leaves attached to its i-th vertex. Then p_1,p_m>=1, internal p_i>=0, n=m+sum p_i, and ell=n-m is the number of leaves. Put

    a_i=sum_{j<=i}(p_j+1),       1<=i<=m-1,
    P(x)=sum_i x^a_i,           Pbar(x)=sum_i x^(n-a_i),
    S=P+Pbar=A-ell(x+x^(n-1)),
    L_i=a_i-i,                 R_i=ell-L_i.

The number ell is [x]A, so m and S are observable from shell 1. Deleting two pendant edges leaves the middle component of size n-2. Hence

    B=D+C+binom(ell,2)x^(n-2),
    D=sum_{i<j}x^(a_j-a_i),
    C=sum_i (L_i x^(a_i-1)+R_i x^(n-a_i-1)).

The unknown C is precisely the pendant contamination. It satisfies the exact identity

    C(x)+x^(n-2)C(1/x)=ell*x^(-1)S(x).                 (1)

Proof: pair the two terms for each cut and use L_i+R_i=ell. Equivalently, with the rank-weighted polynomial

    R=sum_i (i x^a_i+(m-i)x^(n-a_i)),

one has C=S'-R/x.

Let B0=B-binom(ell,2)x^(n-2). Equation (1) removes all pendant terms from the symmetrized observation:

    D(x)+x^(n-2)D(1/x)
       =B0(x)+x^(n-2)B0(1/x)-ell*x^(-1)S(x).        (2)

This is an exact removal of the symmetric part, not yet recovery of D itself. The missing part is antisymmetric under reflection about (n-2)/2. The positivity and point-configuration constraints on D remain relevant.

### Theorem A: completeness on short-span caterpillars

Among caterpillars whose spine cut positions satisfy

    2(a_(m-1)-a_1) <= n-2,

shells 1 and 2 determine the caterpillar up to isomorphism.

Proof: D has no exponent above (n-2)/2. Equation (2) therefore recovers D from its lower half; halve the midpoint coefficient when n is even. The difference histogram gives

    P Pbar=(m-1)x^n+sum_{d>0}D_d(x^(n+d)+x^(n-d)).

Together with S this determines (P-Pbar)^2=S^2-4P Pbar. Polynomial square roots in Z[x] differ only by sign, so P is recovered up to reflection. Its successive gaps give p_i+1. QED.

The hypothesis says that the two endpoint spine weights together are at least (n+2)/2; it allows unbounded spine length. This is completeness **within the stated subclass**. We have not proved that a short-span caterpillar cannot share A,B with a caterpillar outside the subclass.

## 3. An exact threshold at four spine vertices

### Theorem B: shells 1 and 2 distinguish all caterpillars with at most four canonical spine vertices

Within the caterpillar class, A gives ell and hence m. Stars and two-spine caterpillars are immediate: the latter has one non-pendant cut known up to complementation.

For three spine vertices, write the two cut radii as 2<=a<=b<=n/2. Up to a global reflection the only possible cut sets are {a,b} and {a,n-b}, discarding sets with repeated points. Define

    mu_r=sum_{edge pairs} b(e,f)^r=(x d/dx)^r B(x) at x=1.

The difference of mu_2 for the two candidates is

    2(a-1)(n-2b).

It vanishes only when the candidates coincide (or the all-left candidate is invalid).

For four spine vertices let the sorted cut radii, with multiplicities, be

    2<=a<=b<=c<=n/2.

Every possible cut set, up to reflection, is among

    Q0={a,b,c},       Q1={a,b,n-c},
    Q2={a,c,n-b},     Q3={b,c,n-a}.

Discard repeated cut points. These four exhaust the choices because a global reflection can make at least two of the three points lie in the left half.

The following are exact mu_2 differences, with the order indicated:

| Pair | mu_2 difference |
|---|---|
| Q0-Q1 | 2(n-2c)(a+b-2) |
| Q0-Q2 | 2[(a-2)(n-2b)+b(n-2c)+2(c-b)] |
| Q0-Q3 | 4(a-1)(n-b-c) |
| Q1-Q2 | 4(a-1)(c-b) |
| Q2-Q3 | -2(b-a)(n-2c) |

In the permitted domain, every zero above makes the candidates identical, reflections, or invalid. Only Q1 versus Q3 could require another moment. Writing delta_r=mu_r(Q1)-mu_r(Q3), exact algebra gives

    delta_3 = (3/2)(n-a-b)delta_2
              -6(a-1)(b-1)(b-c).

If delta_2=delta_3=0 then b=c. But Q3 then has repeated cut points and is invalid. Thus mu_2 and mu_3 resolve every remaining ambiguity. QED.

The moment formulas come by substituting each cut set into

    mu_r=sum_{i<j}(a_j-a_i)^r
         +sum_i[(a_i-i)(a_i-1)^r
                 +(ell-a_i+i)(n-a_i-1)^r]
         +binom(ell,2)(n-2)^r.

This proves an all-order theorem, not a finite census claim. The reconstruction algorithm passed exactly on all **41,743 caterpillars with two to four spine vertices and 4 through 40 total vertices**. Stars are handled directly by the proof.

Revision 9's five-spine family proves that this threshold is sharp by spine length.

## 4. Complete spine formula for the third-shell correction

To avoid a clash with the earlier nonnegative residue-lift H_E, write K_3 for Revision 9's H_3. These use different baselines and signs. Let U_3 be the elementary third symmetric sum of the edge polynomials x^s+x^(n-s). Then

    S_3=U_3+(1-x^n)K_3.

U_3 is determined by A: if e=n-1 is the number of edges,

    U_3=(A^3-3A A(x^2)+2A(x^3))/6-(e-1)x^n A.

Split K_3 into K_3^(r) according to the number r of retained pendant edges. Define

    C2=sum_i[binom(L_i,2)x^(a_i-2)
              +binom(R_i,2)x^(n-a_i-2)].

The two simplest pieces are

    K_3^(3)=binom(ell,3)[x^(n-3)+3x^(n-1)+x^(2n-3)],
    K_3^(2)=C2+(ell-1)x C+binom(ell,2)x^(n-2)S.

Thus shell 3 introduces a quadratic leaf-count term C2, while much of the apparently complicated two-pendant contribution is already determined by lower data.

For two spine cuts u=a_i<v=a_j put d=v-u and M=d-(j-i). Then

    K_3^(1)=sum_{i<j}[
        ell(x^(d+1)+x^(n+d-1))
        +(ell-M)x^(n-d-1)+M x^(d-1)
        +L_j x^(u+v-1)+R_i x^(2n-u-v-1)].

For three spine cuts u<v<w,

    K_3^(0)=sum_[u<v<w][
        x^(u-v+w)+x^(n-u+v-w)
        +x^(-u+v+w)+x^(n-u-v+w)].

Proof: retain the chosen spine cuts and classify each pendant edge by which resulting component contains its attachment. Apply the weighted-path or weighted-star sign formulas of Theorem 26. For r=2, the high terms combine using binom(L,2)+LR+binom(R,2)=binom(ell,2), and 2binom(L,2)+LR=(ell-1)L. This yields the stated simplification.

The formula is exact and uses only O(m^3) summands, regardless of the number of pendant leaves. It was independently checked against direct integer edge-difference enumeration on all **548 nonstar caterpillars with 4 through 12 vertices**. It has not yet supplied the antisymmetric part missing in (2) for arbitrary caterpillars.

## 5. Stronger all-parameter collision and separation statements

### Theorem C: a two-parameter extension of the family

For integers a>=1 and b>=0, compare pendant sequences

    p=(a,b,a-1,a+b,b+1),
    q=(a,a+b,b,a-1,b+1),        n=3a+3b+5.

They have equal A and B and equal coefficients [x^V]M for V=1,2,3. They are isomorphic exactly when a=b+1. In every other case volume 4 separates them.

The original family is the specialization a=s, b=s+1. The choice a=b=1 gives the 11-vertex pair recorded elsewhere in Revision 9.

**Non-isomorphism proof.** The endpoints each have at least one pendant leaf, so deleting all leaves gives the canonical 5-vertex spine, even when an internal pendant count is zero. Any isomorphism preserves or reverses it. A forward match fails at coordinate 2 because b differs from a+b. A reversed match holds exactly when a=b+1, as inspection of all five entries then verifies.

**Equality proof.** The cut positions of p are

    a+1, a+b+2, 2a+b+2, 3a+2b+3.

The q cut positions replace a+b+2 by its complement n-(a+b+2) and retain the other three. Thus A is equal. Substituting these positions and L_i=a_i-i into B gives an exact coefficientwise identity; the checker treats exponents as affine functions of two independent variables and coefficients as polynomials, rather than checking finitely many values.

The low-volume equalities and the following volume-4 identity are obtained by the finite transfer calculation described below. Write u=q^a and v=q^b. Then

    Delta[x^4]M = (u v/q)(q^2-1)^2(q^2+1)
                 *(u-1)(qv-1)(qv-u)*F(q,u,v),

    F=q^4 u^2 v^2+q^4 u v^2+q^4 v^2
      +q^3 u^2 v+q^3 u v+q^3 v
      +q^2 u^2+q^2 u-q^2 v^2+q^2-q u v-u^2.

For a>=1,b>=0, F(q,q^a,q^b) has unique highest term q^(2a+2b+4). Every displayed factor is nonzero as a formal Laurent polynomial except qv-u, which vanishes exactly when a=b+1. This proves volume-4 separation in every nonisomorphic case. The 1/q causes no singularity in the expanded polynomial; n>=8 and the original finite sum has nonnegative energy exponents.

**Finite algebra underlying the low-volume identity.** For spine height h and p pendant leaves, let c_j be the number of those leaves at height j>0, with k=sum c_j. The multiplicity and leaf energy are

    (p)_k / product_j c_j!,
    p h^2+sum_j c_j(j^2-2jh).

Since n>=8, the coefficients of M and the nonnegative height sum agree through volume 4. For total volume at most 4, only h<=4 and partitions of an integer at most 4 occur. Multiply these finite local sums along the five-site spine and insert q^((h_i-h_(i+1))^2) for each spine edge. This is an identity in QQ[a,b] with affine energy exponents, valid for all nonnegative integer pendant counts. Its expanded receipt has zero differences at volumes 1,2,3 and the factored difference above at volume 4. Direct height enumeration independently checked eleven parameter instances, including isomorphic and nonisomorphic cases.

Consequently adding **all** coefficients of volumes at most 3 to **all** coefficients of energies at most 2 is still incomplete on caterpillars. This is a theorem about that particular joint truncation; it does not show that every fixed bidegree fails.

### Theorem D: the original family first separates at energy 3 for every s>=1

The third-shell correction difference for the original family is

    Delta K_3 = (1-s)x^(3s+3)+(s+1)x^(3s+5)
        -x^(4s+3)+x^(4s+7)
        -(s+2)x^(5s+5)+s x^(5s+7)
        +x^(6s+5)-x^(6s+9)
        +(s-1)x^(7s+7)-(s+1)x^(7s+9)
        +(s+2)x^(9s+9)-s x^(9s+11).

For every s>=1 its unique highest term is -s x^(9s+11). Since Delta U_3=0,

    Delta S_3=(1-x^(6s+8))Delta K_3
             =s x^(15s+19)+lower powers of x.

This proves exact first separation at shell 3 uniformly. Specialization of Theorem C also proves exact first separation at volume 4 uniformly; its volume-4 difference has unique highest energy q^(9s+16) with coefficient 1. Direct checks at s=1,2,3,4,5 agree in both directions.

The all-parameter third-shell statement is asserted here for the original one-parameter family. No such claim is inferred for every member of the two-parameter extension from finite tests.

## 6. Scope repairs and literature

Theorem 28's reported number 1392 is the excess at **n=26 alone**, among 4,196,351 tested caterpillars. It is not a cumulative count through order 26, nor the total number of graphs in collision classes. Shell 3 splitting every recorded collision class was tested at the five orders 11,14,17,18,20. Neither census was rerun here. The patch repairs this wording and writes out the original family's non-isomorphism proof.

A relevant existing endpoint is Loebl and Sereni, *Isomorphism of weighted trees and Stanley's isomorphism conjecture for caterpillars*, Ann. Inst. Henri Poincare D 6 (2019), 357-384, DOI 10.4171/AIHPD/74. They prove caterpillar reconstruction from the U-polynomial, equivalently the census of component-size partitions after edge deletion. Thus recovering that census from M would suffice for caterpillar completeness. That recovery is not established here; their theorem cannot be applied directly to a height series without the missing implication. Primary source: https://www.numdam.org/item/10.4171/aihpd/74.pdf .

## 7. What remains open and how to replay

General caterpillar completeness from shell 3, or from M itself, is unproved. We have no graph collision. The new formulas identify the remaining decontamination problem: recover the antisymmetric part of D in (2) from K_3 and the graph-realizability constraints. The short-span theorem solves it by a support restriction; the four-spine theorem solves the finite orientation alternatives. Neither argument covers arbitrary long spines.

Run `python replay.py`. Requirements are networkx and sympy. All inputs and scripts are included and use exact integer or rational arithmetic. The core row engine, the 8.9-million-tree hunt, the asymptotic profile claim, promotion orders and annular transfer were not revalidated here. Proof-assistant verification and a comprehensive priority review remain separate tasks.
