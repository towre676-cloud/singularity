# NX32: monodromy as a costed experiment language

The adapter records a basepoint, basis, loop descriptions, positive loop costs,
observation costs and source revision. States are columns. In a chronological
word \((i_1,\ldots,i_m)\), the first loop is executed first, so the reading is
\(cT_{i_m}\cdots T_{i_1}v\). Every returned witness is replayed in this convention.
Every loop matrix must be invertible, including standalone algebraic examples:
continuation is an isomorphism of the local-system fiber. General singular
actions remain supported by `OperatorSystem`, rather than this adapter.

The finite operator closure from `observability.py` proves all-word visibility.
If the final row space \(W\) contains the observation rows and is preserved by
right multiplication by every available \(T_i\), induction places every future
experiment row in \(W\). Its annihilator is therefore permanently invisible in
this declared loop language. A finite word census alone would not prove this
statement. Cheapest exact witnesses use the existing cost-filtered closure.

Under \(v'=Sv\), the matrices and outputs transform as
\(T_i'=ST_iS^{-1}\), \(c'=cS^{-1}\); substitution shows every reading is unchanged.
The tests independently enumerate every word through length six under three
invertible rational gauges. Inverse loops are added only with explicit positive
costs, and exact matrix inversion rejects singular gauges.

For the algebraic toy matrices
\(T_0=\left(\begin{smallmatrix}1&1\\0&1\end{smallmatrix}\right)\),
\(T_1=\left(\begin{smallmatrix}1&0\\1&1\end{smallmatrix}\right)\), the two length-two
words have readings 1 and 2 on \(v=(1,0)\), \(c=(1,0)\). For difference
\((0,1/100)\), a cost-one experiment is nonzero but does not tolerate radius
\(1/100\). The cheapest robust word costs three; equality at twice the error
radius is rejected. Robust enumeration retains the complete finite cost-bounded
word family, because linear dependence is not safe amplitude pruning.

## Actual marked Legendre loops

The archived PerfectPower `period_matrix_balls.py` supplies the marked Legendre
family, its seed normalization and a source-bound integral-cycle premise.
Starting at \(t=1/2\), the retained counterclockwise polygons are

\[
(1/2,i/2,-1/2,-i/2,1/2),\qquad
(1/2,1-i/2,3/2,1+i/2,1/2).
\]

Each loop was independently continued using 215 certified ordinary disks,
Taylor order 16 and outward 96-bit center rounding. The resulting marked-cycle
matrices are

\[
T_0=\begin{pmatrix}1&2\\0&1\end{pmatrix},\qquad
T_1=\begin{pmatrix}1&0\\-2&1\end{pmatrix}.
\]

Their determinant-one and unipotence relations are exact, and they do not
commute. No complete presentation of the fundamental or monodromy group is
claimed. Exact recognition is conditional on the independently stated integral
cycle marking: a row-norm enclosure of radius below one half identifies at most
one integral matrix, but numerical proximity itself does not prove integrality.
The two full continuation transcripts are retained alongside their hashes.

The fast receipt checks the source-bound transcripts and exact loop-language
claims. `python scripts/nx_analytic_decisions.py --check --slow` recomputes both
certified continuations, including their rational analytic errors. These loop
replays take much longer than finite row closure and are intentionally separate
from the unit-test loop. Their scope is the declared Legendre integral basis;
the standalone algebraic toy is not relabeled as geometric monodromy.
