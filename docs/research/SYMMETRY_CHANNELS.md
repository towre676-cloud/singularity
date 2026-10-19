# NX21 — Exact symmetry channels and costed repairs

The implementation supports verified finite rational representations, rational projectors, exact row-space closure, original-model permutation conjugacy, and finite-catalogue robust sensor repairs. It never substitutes a floating eigenspace for an exact channel certificate.

## Two distinct blindness theorems

For a single state system let an idempotent \(P\) commute with every allowed operator \(M_i\). If the actual output rows obey \(LP=0\), then for every legal word,
\[
 LM_{i_m}\cdots M_{i_1}P=LP M_{i_m}\cdots M_{i_1}=0.
\]
Thus the channel \(\operatorname{im}P\) is permanently invisible under those operators and sensors. Reachability and whether the actual original population occupies that channel are separate questions.

For two candidate models the relevant theorem is instead intertwining. Suppose
\[
 A_bP=PA_a,\quad B_b=PB_a,\quad x_{0,b}=Px_{0,a},\quad C_bP=C_a.
\]
Induction gives \(x_{t,b}=Px_{t,a}\) under every shared input word, and hence equal outputs at every time. Neither faulted matrix needs to commute with \(P\). The sparse thermal adapter checks this theorem on the original candidate entries and a bijective original-state permutation. It uses the fixed zero initial state and actual named sensor rows.

## Rational finite groups

`FiniteRepresentation` checks the entire finite multiplication table: identity, inverses, associativity, and every representation multiplication identity. It rejects duplicated group labels, incompatible dimensions, non-rational entries, and oversized groups. `verify_channel_decomposition` independently checks
\[
 P_i^2=P_i,\qquad P_iP_j=0\ (i\ne j),\qquad \sum_iP_i=I,
 \qquad [P_i,M_a]=[P_i,\rho(g)]=0.
\]
For an involution \(S^2=I\), `reflection_channels` returns \((I+S)/2\) and \((I-S)/2\). Rational division is exact.

The corpus includes the rational regular representation of \(C_3\), with a rank-one constant channel and rank-two augmentation channel. The augmentation representation is irreducible over \(\mathbb Q\); over \(\mathbb C\) it splits into two conjugate one-dimensional characters. The release does not identify these field conventions. A Klein-four corpus verifies four rational channels and repeated irreducible multiplicities in two regular copies.

## A necessary caveat about summing channel ranks

Commutation alone does not make projected sensors physically available. For example \(M=I\), a reflection that swaps two coordinates, and the one sensor \((1,0)\), have full observable rank one, while separately projecting the sensor onto the plus and minus channels produces two nonzero rows. Claiming rank two for the actual sensor would be false.

`channel_observability` therefore computes the actual full closure and all projected-channel closures, then explicitly reports whether the dimensions add correctly. It does not infer equality from commutation. In the retained finite-group examples the available group operators generate the necessary channel separation, and full closure rank equals the sum. Original observation semantics are preserved.

## Exact uncertainty transport

A basis change generally destroys independence of coordinate noise. For an original box \(D[-1,1]^n\), a transform \(T\) produces the zonotope
\[
 TD[-1,1]^n.
\]
`transformed_noise_set` retains the factor \(TD\), not merely its coordinate bounds. For a Euclidean-ball model it retains the ellipsoid factor and Gram matrix
\[
 G=TD^2T^T.
\]
For \(T=\bigl(\begin{smallmatrix}1&1\\0&1\end{smallmatrix}\bigr)\), unit radii produce Gram \(\bigl(\begin{smallmatrix}2&1\\1&1\end{smallmatrix}\bigr)\). Replacing it by a unit ball would erase both scaling and correlation. The physical repair examples work directly with original sensor intervals and need no such change of coordinates.

## Thermal reflection and cheapest repair

The original blocked-left and blocked-right candidates on the 12-by-12 source-derived plate are related by horizontal reflection. The heater is invariant; the corner mean and central mean sensor rows are invariant. Sparse conjugacy verifies the all-input all-time blindness theorem for those rows. Direct constant and alternating input words through horizon twelve provide independent finite checks of the identities' consequences.

The repair catalogue contains original mean sensors and one newly installed top-left point sensor, with declared total accounting costs and absolute reading error \(1/1000\). Each experiment starts from a reset zero state. The cheapest target-separating repair in this catalogue is the existing left-center mean after two unit input steps, cost three. The two exact readings differ by \(1/64\), exceeding the sum of their error radii \(1/500\).

Every one of the 32 possible capability panels is independently checked by finite enumeration. The far-corner point sensor breaks reflection but gives equal readings at this short horizon, because influence has not reached that location. It is retained as an explicit counterexample: symmetry breaking does not establish target observability.

A repair separates a target pair exactly when some installed reading has disjoint closed uncertainty intervals. `minimum_channel_repair` optimizes total positive rational catalogue cost and retains actual experiment words, sensor descriptions, errors and original candidate IDs. Its optimality is restricted to the declared finite catalogue, independent-reset semantics and interval error model. It does not claim minimal laboratory hardware over all imaginable actions.

Replay `python scripts/symmetry_channels.py --check`. The strict representation and projector constructors reject broken commutation or multiplication identities before a channel proof is accepted.
