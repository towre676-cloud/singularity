# 1. What the population observes

## 1.1 A relation before a prediction

This book begins with a finite graph and a deliberately restricted experiment. Each vertex receives a nonnegative integer height. An edge pays the square of the difference between its endpoint heights. We count all height assignments having a specified total height and a specified energy. We then ask how much of the original relation between vertices survives in those counts. The question concerns the information contained in an exact mathematical observation. It does not require interpreting vertices as people, particles, assets, or physical locations.

The restriction is essential. If an experiment reports every vertex height and every labeled edge contribution, the graph can be read directly from the report. The interesting problem begins after that correspondence is removed. A histogram may tell us how many assignments have a certain energy without telling us which assignments they were. The resulting observation can preserve information that a familiar spectrum loses, while still losing information of its own. Establishing either possibility requires a proof or a concrete exact comparison.

There are consequently two distinct tasks. The forward task computes the population produced by a supplied graph. The inverse task decides what a population determines about its source. An efficient and correct forward computation does not settle the inverse question. Nor does a pair of distinguishable examples establish that every pair is distinguishable. Throughout the manuscript, reconstruction is a question to investigate, not an advertised theorem.

## 1.2 Objects, assignments, and the meaning of a coefficient

Let \(G=(V,E)\) be a finite simple undirected graph with labeled vertex set
\[
V=\{0,1,\ldots,k-1\},\qquad k\ge1.
\]
An edge is an unordered pair of distinct vertices, and each unordered pair occurs at most once. Write \(d_i\) for the degree of vertex \(i\), and \(A_{ij}\in\{0,1\}\) for the adjacency matrix. Connectedness will be required explicitly when needed. The basic formal counting series itself is defined for disconnected graphs as well.

A height profile is a vector \(a=(a_0,\ldots,a_{k-1})\in\mathbb Z_{\ge0}^k\). Its volume, energy, and span are
\[
|a|=\sum_i a_i,\qquad
E_G(a)=\sum_{\{i,j\}\in E}(a_i-a_j)^2,\qquad
h(a)=\max_i a_i-\min_i a_i.
\]
The word **volume** always means total integer height. It is not a Euclidean volume, a determinant, the number of occupied vertices, or the number of nonzero levels. A profile of volume four might put height four at one vertex, height two at two vertices, or height one at four vertices. These assignments generally have different energies.

Define the local series
\[
L_G(x,q)=\sum_{a\in\mathbb Z_{\ge0}^k}x^{|a|}q^{E_G(a)}
=\sum_{m\ge0}C_{G,m}(q)x^m.
\]
The coefficient \([x^m q^e]L_G\) is the number of original labeled assignments of volume \(m\) and energy \(e\). It does not count graph automorphism orbits. If a symmetry exchanges two assignments, both remain in the population. This convention makes coefficients directly comparable to enumeration and avoids inserting unannounced symmetry factors.

**Theorem SNG-F01 (finite local coefficients).** For every finite graph on \(k\ge1\) vertices and every \(m\ge0\), \(C_{G,m}(q)\) is a polynomial in \(q\) with nonnegative integer coefficients. Its coefficient sum is
\[
C_{G,m}(1)=\binom{m+k-1}{k-1}.
\]
If \(\Delta=\max_i d_i\), its degree is at most \(\Delta m^2\).

*Proof.* The nonnegative integer solutions of \(a_0+\cdots+a_{k-1}=m\) are the weak compositions of \(m\) into \(k\) parts. The usual separator construction gives their number as the displayed binomial coefficient. In particular, there are finitely many terms in \(C_{G,m}\). Every energy is a nonnegative integer. Moreover,
\[
E_G(a)=\sum_i d_i a_i^2-2\sum_{\{i,j\}\in E}a_i a_j
\le\Delta\sum_i a_i^2\le\Delta\Bigl(\sum_i a_i\Bigr)^2.
\]
The first inequality uses nonnegativity of all heights; the second follows by expanding the square. This proves all assertions. \(\square\)

Thus \(L_G\) is well defined as an element of \(\mathbb Z[q][[x]]\). This assertion is formal: no choice of numerical \(x\) or \(q\), and no convergence argument, is required. Later analytic interpretations must separately state the region in which a formal identity can be evaluated.

## 1.3 Removing a repetition that carries no relational information

Adding the same integer to every height leaves every edge difference unchanged:
\[
E_G(a+t\mathbf1)=E_G(a),\qquad |a+t\mathbf1|=|a|+kt.
\]
Every nonnegative profile has a unique decomposition
\[
a=b+t\mathbf1,\qquad t=\min_i a_i,\qquad \min_i b_i=0.
\]
We therefore retain the normalized series
\[
B_G(x,q)=\sum_{\substack{b\ge0\\\min b=0}}x^{|b|}q^{E_G(b)}.
\]
The normalization removes the common-height tower, not an assignment-specific ambiguity. It retains one explicitly specified representative of each integer profile modulo common translation.

To distinguish assignments with one nonzero level from assignments with several levels, introduce the full marked series
\[
\mathcal B_G(x,q,z)
=\sum_{\substack{b\ge0\\\min b=0}}
x^{|b|}q^{E_G(b)}z^{\max b}.
\]
The symbol \(B_G(x,q,z)\) may be used for this same three-variable object when its arguments are displayed. In these foundational chapters, \(\mathcal B_G\) makes the extra mark visually explicit, while \(B_G(x,q)=\mathcal B_G(x,q,1)\). On normalized profiles, maximum height equals span. Consequently \(z\) records a property that common translation does not change.

**Theorem SNG-F02 (normalization and span marking).** For every finite graph on \(k\ge1\) vertices,
\[
B_G(x,q)=(1-x^k)L_G(x,q).
\]
More generally, if
\[
\widetilde L_G(x,q,z)=\sum_{a\ge0}x^{|a|}q^{E_G(a)}z^{h(a)},
\]
then
\[
\mathcal B_G(x,q,z)=(1-x^k)\widetilde L_G(x,q,z).
\]
Both normalized series have nonnegative integer coefficients despite the subtraction in these formulas.

*Proof.* Use the unique decomposition \(a=b+t\mathbf1\). Energy and span are unchanged, whereas volume increases by \(kt\). Hence \(\widetilde L_G=\mathcal B_G\sum_{t\ge0}x^{kt}=\mathcal B_G/(1-x^k)\). Specializing \(z=1\) gives the first identity. Each coefficient of \(\mathcal B_G\) counts an explicitly defined finite set, proving nonnegativity without relying on cancellation. \(\square\)

Keeping \(k\) fixed, \(B_G\) and \(L_G\) contain exactly the same formal information: either is recovered from the other by multiplication or division by \(1-x^k\). The span mark is a different matter. Specializing \(z=1\) merges populations of different spans. We do not assume that this merging can be inverted.

| Observation | Coefficient meaning | Correspondence deliberately removed |
|---|---|---|
| \(L_G(x,q)\) | All profiles by total height and energy | Identity of each profile |
| \(B_G(x,q)\) | Translation-normalized profiles by total height and energy | Identity of each normalized profile |
| \(\mathcal B_G(x,q,z)\) | Normalized profiles by total height, energy, and span | Identity of each profile within a marked cell |
| \([z]\mathcal B_G\) | Binary profiles, excluding the two constant profiles | Identity of the vertex subset |
| \(B_G(1,q)\), when defined | Translation classes by energy alone | Total height and span |

## 1.4 Labeled populations can define unlabeled observations

Labels specify the population being counted, but the aggregate series does not privilege a particular labeling. Let \(\sigma:V(G)\to V(H)\) be a graph isomorphism. Transport a profile by \(a'_{\sigma(i)}=a_i\). This operation permutes the coordinates; it does not merge assignments.

**Theorem SNG-F03 (isomorphism invariance with original multiplicity).** Graph isomorphisms preserve \(L_G\), \(B_G\), and \(\mathcal B_G\).

*Proof.* Coordinate permutation is a bijection on profiles and on normalized profiles. It preserves the sum, minimum, and maximum of their coordinates. Since it is a bijection on edges, it preserves the sum of squared differences. Each coefficient population is therefore carried bijectively to the corresponding population for \(H\). \(\square\)

The theorem proves one implication: isomorphic graphs have equal observations. It does not prove the converse. An invariant is allowed to identify nonisomorphic graphs. The inverse program investigates whether this particular invariant does so, and, if it does, which features remain recoverable despite that blindness.

For example, a single edge has energy \((a_0-a_1)^2\). A normalized nonzero profile is either \((h,0)\) or \((0,h)\), so
\[
\mathcal B_{K_2}(x,q,z)=1+2\sum_{h\ge1}x^h q^{h^2}z^h.
\]
The coefficient two records the two original assignments. It is not replaced by one because the edge has an endpoint-exchanging symmetry. This elementary example is a useful check on every later convention.

For a slightly richer example, take the three-vertex path \(0-1-2\). Its degrees are \((1,2,1)\), and direct enumeration gives
\[
[x]B_G=2q+q^2,
\qquad
[x^2]B_G=2q+q^2+2q^4+q^8.
\]
At volume two, placing both units at an endpoint contributes \(q^4\), placing both at the middle contributes \(q^8\), and placing one unit at each of two vertices contributes the remaining terms. The full mark separates the two mechanisms:
\[
[x^2]\mathcal B_G
=z(2q+q^2)+z^2(2q^4+q^8).
\]
The span-one term consists of three binary subsets. The span-two term consists of three profiles concentrated at one vertex. Setting \(z=1\) adds these two populations without recording which mechanism produced each contribution.

At volume three, the unnormalized count contains the all-one profile, whose energy is zero. The normalized coefficient removes that one translation of the zero profile:
\[
[x^3]B_G=2q^2+4q^5+2q^9+q^{18}.
\]
Its coefficient sum is nine, compared with ten weak compositions of three into three parts. Thus normalization changes an original population by a precisely specified quotient rule; it does not arbitrarily discard an inconvenient solution. A useful calculation record should make this distinction visible whenever normalized and unnormalized outputs appear together.

For comparison, the triangle has
\[
[x]B_{K_3}=3q^2,
\qquad [x^2]B_{K_3}=3q^2+3q^8.
\]
Already the first coefficient distinguishes the two graphs because their degree histograms differ. Such an example checks conventions but is not a demanding test of an inverse method. Later comparisons should deliberately match the simpler observations before attributing a discrepancy to a deeper mechanism.

## 1.5 What a result in this book means

Several mathematical activities appear together, and their conclusions should not be conflated. A proved identity between formal series applies coefficientwise to every allowed input. An exact finite computation establishes the cells actually enumerated. A comparison through volume \(M\) establishes equality or discrepancy through that volume. A numerical graph search may suggest a pattern without proving that no later counterexample exists. An analytic theorem requires its own convergence and continuation hypotheses even when its starting Euler factors have exact coefficients.

The book therefore separates mathematical propositions, software behavior, finite examples, and research targets. The numbered foundational statements below are proved from their displayed hypotheses. They are mathematical statements, not assertions that a proof assistant checked the implementation. Software validation supplies another kind of evidence: it tests whether a program realizes the stated mathematics on the cases examined.

| Type of statement | Appropriate evidence | Scope of conclusion |
|---|---|---|
| Exact forward coefficient | Enumeration, recurrence, or an exact algebraic identity | The stated coefficient or family |
| Prefix agreement | Equal coefficient dictionaries through a declared volume | That finite prefix |
| Strict separation | One exact unequal coefficient | The two observations differ |
| Reconstruction theorem | A proof recovering isomorphism from equality | Every graph in the proved class |
| Reconstruction conjecture | A precise proposed implication | A question, not an established result |
| Analytic continuation | A convergent factorization on a stated domain | That domain and chosen branches |

There is also a useful distinction between a new question for this project and a historically new mathematical construction. Integer graph lattices, Ising-type observations, graph partition functions, and inverse problems all have substantial literatures. The graph cut-lattice viewpoint belongs to established background, including [BHN1997]. Binary energy populations overlap directly with graph Ising polynomials with an external field; [AM2009] is relevant background. General graph reconstruction from families of observations must be compared carefully with the much richer families studied in [Lovasz2012]. No historical priority claim is needed to make the present calculations worthwhile.

The particular program here is to track exactly which relational information survives a succession of increasingly marked arithmetic height observations. Its central difficulty is **lost correspondence**. Counts can be exact while the identities responsible for them are absent. An inverse theorem must recover what that loss hides; an impossibility theorem must demonstrate that the lost information cannot be recovered from the declared observation. Both are substantive mathematical outcomes.

The next chapter puts the translation quotient on an integral lattice. The third chapter explains why multiple nested boundaries retain more information than a single binary cut and why repeated levels cannot be omitted. The fourth chapter turns coefficient order into a precise hierarchy of visibility, beginning with degrees and degree mixing and ending with the open reconstruction question.
