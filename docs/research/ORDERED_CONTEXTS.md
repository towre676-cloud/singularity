# Ordered asymmetric contexts and an exact margin law

## Scope and API

`terminal_moves.OrderedContextAttachment(name, graph, terminals=(0, 1))`
checks a two-terminal simple context without assuming a terminal-swap
automorphism. The graph must be a validated `Graph`, the terminals must be
distinct existing vertices, the name must be nonempty, and the context must
have no terminal-terminal edge. Every attachment uses a fresh interior copy.
The terminal order is retained. For example,

```python
from fractions import Fraction
from singularity.graph import Graph
from singularity.terminal_moves import (
    EXTEND_A, OrderedContextAttachment, OrderedMoveSystem,
)

leaf_a = OrderedContextAttachment("leaf_at_a", Graph(3, ((0, 2),)))
language = OrderedMoveSystem(2, Fraction(1, 2), (leaf_a, EXTEND_A))
```

The leaf context is genuinely asymmetric: its terminal degrees are one and
zero, so no automorphism exchanges them. `OrderedMoveSystem` accepts both
this ordered context type and the existing swap-checked `ContextAttachment`.
`BoundaryExperimentSystem` continues to accept only the swap-checked type.
Thus an ordered context cannot silently enter a compiler that discards its
orientation information.

For ordered kernel coordinates

\[
Y_{(s,t),v}=[x^v]x^{s+t}K_G(s,t),
\]

fresh gluing gives

\[
Y'_{(s,t),v}=\sum_{j=0}^{v-s-t}[x^j]K_C(s,t)\,
Y_{(s,t),v-j}.
\]

The factorization follows by summing independently over the two disjoint
interiors at fixed terminal heights. It needs no automorphism. The absence
of terminal edges prevents repeated gluing from introducing an edge twice.
Every contributing coordinate has volume at most the output volume, so
truncation is exact for arbitrarily long words at the declared budget.
Terminal extension remains the existing volume-triangular operator; mixing
it with an asymmetric context yields a legitimate noncommuting language.

`tests/test_terminal_moves.py` compares all 85 words of length at most three
in the two one-sided leaf attachments and two terminal extensions, on three
base placements at volume budget two and parameter `2/3`. Each reading is
independently computed by height enumeration on the actual assembled graph.
Tests also verify noncommutation and rejection by the symmetric compiler.

## An all-budget maximum-margin theorem on actual graph blocks

Let the base graph be the path with edges `01,12`. Compare its endpoint
terminal placement `(0,2)` with its adjacent placement `(0,1)`. Fix
\(0<q<1\), use volume budget one, and retain the three symmetric coordinates

\[
((0,0),0),\qquad ((0,0),1),\qquad ((0,1),1).
\]

Let the two allowed attachments be the standard pendant-leaf pair and
shared neighbor, costing two and one respectively. Both direct coefficient
observations have zero cost and unit noise normalization. Define

\[
a=q(1-q)>0.
\]

The endpoint placement has state \((1,q^2,2q)\), while the adjacent placement
has state \((1,q,q+q^2)\). Their difference is therefore

\[
d=(0,-a,a).
\]

**Theorem.** For any real cost budget \(C\ge0\), the largest absolute
discrepancy attainable by a single experiment in this language is

\[
\boxed{\mu^*(C)=q(1-q)\bigl(1-q^{\lfloor C\rfloor}\bigr).}
\]

When \(C\ge1\), the unique optimal attachment word is the shared neighbor
repeated \(\lfloor C\rfloor\) times, followed by the volume-one observation.
For \(0\le C<1\), every affordable observation has zero discrepancy.

**Proof.** The two volume-one context operators, in the stated coordinate
order, are

\[
M_{\mathrm{leaf}}=
\begin{pmatrix}1&0&0\\2q&1&0\\0&0&q\end{pmatrix},
\qquad
M_{\mathrm{shared}}=
\begin{pmatrix}1&0&0\\q^2&1&0\\0&0&q\end{pmatrix}.
\]

Because the first component of the difference is zero, either attachment
leaves its second component unchanged and multiplies the third by \(q\).
Every chronological word of length \(k\) consequently sends the difference
to \((0,-a,aq^k)\). The volume-zero reading is zero; the volume-one reading
is \(-a(1-q^k)\). Its absolute value strictly increases with \(k\). Every
attachment costs at least one, so an affordable word has length at most
\(\lfloor C\rfloor\). Repeating the cost-one shared context attains that
length. A word of that maximal length containing a cost-two leaf pair costs
at least \(\lfloor C\rfloor+1>C\), proving uniqueness when the maximum is
positive. This proves the claim for all budgets, not just a finite search
range. The argument is valid over real \(q\); implementations use exact
rational specializations. \(\square\)

This is a theorem about single experiments, not shared panels. With a
common noise normalization \(\sigma>0\), divide the formula by \(\sigma\).
With unequal observation or attachment costs, the stated optimization
problem changes and the formula must not be reused without a new argument.

## Diminishing returns and a nonattained unlimited optimum

Writing \(\mu_k=a(1-q^k)\), each additional shared-neighbor attachment gains

\[
\mu_{k+1}-\mu_k=a(1-q)q^k,
\qquad
\sup_{C\ge0}\mu^*(C)=a.
\]

Every finite experiment has margin strictly below \(a\); the supremum is
not attained. At \(q=1/2\), the optimal margin is
\((1-2^{-\lfloor C\rfloor})/4\), approaching \(1/4\).

For adversarial scalar error of absolute magnitude at most \(\varepsilon\),
strict nearest-candidate separation requires a discrepancy greater than
\(2\varepsilon\). A finite successful experiment exists precisely when
\(\varepsilon<a/2\). Equality at the limiting threshold cannot be repaired
by any finite cost. This illustrates why unrestricted robustness is not the
same optimization problem as cheapest exact distinguishability.

`tests/test_path_margin.py` compares the formula against both exact search
algorithms for four rational parameters and fifteen integer or half-integer
budgets. Independently enumerated glued graphs verify every word of length
at most five at three parameters. These are finite checks supporting the
all-budget proof; the proof supplies the infinite quantifier.
