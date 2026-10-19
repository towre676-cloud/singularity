# Typed observability: finite type graphs, graph adapters and cheapest witnesses (NX13)

## What this note covers

The existing observation engine (`observability.py`) works in one state
space. Every action there is a square matrix on that space. Some graph
operations do not fit that picture. Introducing a terminal, forgetting
one, or adding the edge between the two terminals changes what the
boundary looks like. A single ambient matrix can hide an illegal
composition. Adding the terminal edge twice is the clearest case: the
algebra silently computes a multigraph.

This note extends the engine to a finite directed graph of state types.
It has three parts:

1. **NX13-A.** The typed algebra contract: closure, quotient invariance,
   per-type minimality and the cheapest-witness property, with proofs.
2. **NX13-B.** One finite boundary grammar for graph assembly that
   genuinely closes at a fixed volume budget. It is checked against height
   enumeration on the actual assembled graphs.
3. **NX13-C.** Portable certificates that replay without the closure
   computation. Cheapest witnesses are compared with exhaustive legal-path
   search under a cost bound.

The four categories are kept separate. Sections 2–4 are **proved project
results** about the typed algebra and the grammar's formulas. Section 5
records **exact computations over declared finite populations**. Section 7
lists what remains **outside scope**.

Code: `src/singularity/typed_observability.py` (algebra and portable
format) and `src/singularity/typed_contexts.py` (graph adapter).
Tests: `tests/test_typed_observability.py` and `tests/test_typed_contexts.py`.
Receipt: `scripts/typed_contexts.py` and `results/typed_contexts.json`.

## 1. Objects and conventions

A **typed operator system** consists of:

- a finite set of types $B$, with type $b$ carrying $V_b=\mathbb{Q}^{d_b}$
  ($d_b=0$ is allowed);
- actions $a:s(a)\to t(a)$ with exact matrices $M_a$ of shape
  $d_{t(a)}\times d_{s(a)}$ and costs $c_a>0$;
- observations at type $b$: rows $L\in\mathbb{Q}^{1\times d_b}$ with costs
  $c_L\ge 0$.

A zero-dimensional space's shape comes from its declared type. An empty
tuple is accepted only where the type dimensions say the matrix has no rows.
A $2\times 0$ matrix is `((), ())`, never `()`.

**Words are chronological.** A word $w=(a_1,\dots,a_m)$ is *legal* when
$t(a_i)=s(a_{i+1})$ for every $i$. It starts at $s(a_1)$ and ends at
$t(a_m)$. It sends a state $x$ to $M_{a_m}\cdots M_{a_1}x$, so the latest
matrix acts on the left. An *experiment* $(w,L)$ is legal when $L$ lives at
the end type of $w$. Its row and cost are

$$
\rho(w,L)=L\,M_{a_m}\cdots M_{a_1}\in\mathbb{Q}^{1\times d_{s(a_1)}},\qquad
c(w,L)=c_L+\textstyle\sum_i c_{a_i}.
$$

The empty word is legal at the observation's own type. Reading an
observation at another type is rejected. So is a word whose consecutive
types do not match.

Write $W_b$ for the span of all rows of legal experiments starting at $b$.

## 2. The typed algebra (NX13-A)

### Algorithm

`typed_closure` keeps a priority queue of actual experiments, ordered by
cost. It starts with all observations, read with the empty word. It pops
the cheapest experiment $e$, which starts at type $b$. If $\rho(e)$ is
independent of the rows already retained at $b$, the algorithm retains $e$.
It then pushes the child $(a\cdot e)$ for every action $a$ with $t(a)=b$.
The child's row is $\rho(e)M_a$, it starts at $s(a)$, and its cost is
$c(e)+c_a$. Prepending is correct because the action $a$ happens *before*
the experiment $e$. Dependent rows are discarded and never extended.

The algorithm outputs retained witness rows $B_b$ (a $r_b\times d_b$ matrix
whose rows are actual experiments), and unique coordinates $A_b$ and $T_a$
with

$$
L=A_L B_b\ \ (L\text{ at }b),\qquad B_{t(a)}M_a=T_aB_{s(a)},
$$

where $T_a$ has shape $r_{t(a)}\times r_{s(a)}$. Neither $A$ nor $T$ need
be square. The kernel $N_b=\ker B_b$ is reported as an exact basis.

### Lemma 1 (monotone pops, termination)

Every child costs strictly more than its parent, and children are pushed
only when the parent is popped. So the popped costs never decrease. Each
retained row raises the rank at its type by one. Hence at most
$D=\sum_b d_b$ rows are retained. Only retained rows have children, so at
most $1+D\cdot|A|$ batches of pushes happen and the algorithm stops.

### Theorem 1 (typed closure and cost filtration)

*For every legal experiment $(w,L)$ starting at $b$, the row $\rho(w,L)$ is
a linear combination of retained rows of $B_b$ whose costs are at most
$c(w,L)$. Consequently $\operatorname{row}(B_b)=W_b$ for every type.*

*Proof.* Use induction on the length of $w$.

- **Length 0.** The experiment $(\,(),L)$ was pushed initially. When it was
  popped, it was either retained (and is its own combination) or it lay in
  the span of rows already retained at $b$. Those rows were popped earlier,
  so by Lemma 1 they cost at most $c_L$.
- **Prepending an action.** Let $w=(a)\cdot w'$, where $w'$ starts at
  $t(a)$. By induction $\rho(w',L)=\sum_k\lambda_k\,\beta_k$, a sum over
  retained rows $\beta_k$ at $t(a)$ with $c(\beta_k)\le c(w',L)$. Then
  $\rho(w,L)=\sum_k\lambda_k\,\beta_kM_a$. Each $\beta_kM_a$ is the row of
  a child that was pushed, with cost $c(\beta_k)+c_a\le c(w,L)$. When that
  child was popped, it was retained or dependent on rows of cost at most its
  own. Substituting gives the claim.

Thus $W_b\subseteq\operatorname{row}(B_b)$. Conversely each retained row
*is* a legal experiment, so $\operatorname{row}(B_b)\subseteq W_b$. Both
inclusions matter. An elimination residual is not an experiment, and the
code never stores one as a witness. $\square$

The same argument works with the packet's simultaneous iteration
$W_b^{k+1}=W_b^k+\sum_{a:s(a)=b}W^k_{t(a)}M_a$. That chain is increasing.
If it is stationary at one step for every $b$, it stays stationary. Each
strict step raises the total rank, so it stabilizes after at most $D$
steps. **Words of length at most $D$ therefore span every $W_b$.** The
independent oracle in the tests relies on this bound.

### Theorem 2 (quotient invariance)

*For every action, $M_aN_{s(a)}\subseteq N_{t(a)}$. The observable state
$z_b=B_bx$ updates exactly by $z_{t(a)}=T_az_{s(a)}$, and every legal
reading factors through it: $\rho(w,L)x=A_L\,T_{a_m}\cdots T_{a_1}\,z_{s(a_1)}$.*

*Proof.* For $x\in N_s$, $B_tM_ax=T_aB_sx=0$, so $M_ax\in N_t$. The update
is the identity $B_tM_a=T_aB_s$ applied to $x$. The reading formula
follows by applying the update along the word and then using
$L=A_LB_{t(a_m)}$. So the quotient dynamics on $V_b/N_b\cong\mathbb{Q}^{r_b}$
is well defined, and it is also rectangular across types. $\square$

### Theorem 3 (per-type linear minimality)

*Let $P_b:V_b\to U_b$ be linear maps such that every legal reading from $b$
factors through $P_b$, meaning $\rho(w,L)=f_{w,L}\circ P_b$ for some linear
$f_{w,L}$. Then $\ker P_b\subseteq N_b$ and $\dim\operatorname{im}P_b\ge r_b$.
The witness compression $P_b=B_b$ attains this bound.*

*Proof.* If $P_bx=0$, then every legal reading vanishes on $x$. By
Theorem 1 every row of $B_b$ is such a reading, so $B_bx=0$. Rank–nullity
gives $\dim\operatorname{im}P_b=d_b-\dim\ker P_b\ge d_b-\dim N_b=r_b$.
Theorem 2 shows that $B_b$ itself makes every reading factor. $\square$

This minimality is linear and per type. It says nothing about nonlinear
compressions, and nothing about compressions that may discard some future
readings.

### Theorem 4 (cheapest exact witness from the certificate alone)

*Suppose a certificate satisfies the replayed identities, and each nonzero
coordinate obeys the filtration
$A_L[k]\neq0\Rightarrow c(\beta_k)\le c_L$ and
$T_a[k,m]\neq0\Rightarrow c(\beta^{s}_m)\le c(\beta^{t}_k)+c_a$. Then for
any $\delta\in V_b$, the first retained row of $B_b$ in cost order with
$\beta\delta\neq0$ is a cheapest legal experiment separating states whose
difference is $\delta$. If no retained row pairs nonzero with $\delta$, no
legal experiment does.*

*Proof.* Rerun the induction of Theorem 1 using only the two coordinate
identities and their filtrations. Every legal row $\rho$ is a combination
of rows of $B_b$ with cost at most $c(\rho)$. If $\rho\delta\neq0$, some
basis row in that combination has $\beta\delta\neq0$ and
$c(\beta)\le c(\rho)$. The rows of $B_b$ are ordered by cost, and each one
is itself a legal experiment. $\square$

Theorem 4 holds for replayed certificates. It needs neither the queue nor
any trust in the code that produced the certificate. It covers **exact**
distinction only. A dependent row can have a much larger discrepancy than a
cheaper one under noise. Span pruning therefore says nothing about maximum
margin. The ordered-contexts note gives a margin law that needs its own
argument.

### Worked example, checked by hand

Let type $a$ have $V_a=\mathbb{Q}^2$ with no observation, and type $b$ have
$V_b=\mathbb{Q}$ with $L_b=(1)$. Let $M_f=(1\ 1):a\to b$ cost 2 and
$M_g=(1,0)^{\mathsf T}:b\to a$ cost 3.

- The first pop is $L_b$ at $b$ (cost 0). It is retained, and the child
  $f\cdot L_b$ is pushed with row $(1)(1\ 1)=(1,1)$ at $a$ and cost 2.
- That child is retained. Its child $g\cdot(f\cdot L_b)$ has row
  $(1,1)(1,0)^{\mathsf T}=(1)$ at $b$ and cost 5. It is dependent.

So $B_a=(1,1)$, $B_b=(1)$, $N_a=\operatorname{span}\{(1,-1)\}$, $N_b=0$,
$A_a$ is $0\times1$, $A_b=(1)$ and $T_f=T_g=(1)$. The states $(2,0)$ and
$(0,2)$ at $a$ agree forever. The states $(2,0)$ and $(0,3)$ are separated
by $(f,L_b)$ at cost 2. Reading $L_b$ directly at $a$ is rejected. The unit
test `test_packet_example_by_hand` asserts exactly these numbers.

## 3. A finite boundary grammar (NX13-B)

### Types and coordinates

Fix a volume budget $R\ge0$ and a rational $0<q<1$. A *placed graph* is a
finite labeled simple graph with an ordered tuple of at most two distinct
terminals. Its terminal kernel $K_G(\mathbf b)$ sums
$x^{\text{interior volume}}q^{E_G}$ over interior heights. The energy is the
**full** graph energy, so a terminal–terminal edge is included. The four
types are:

| type | terminals | coordinates | dimension at $R=2$ |
|---|---|---|---|
| `closed` | none | $Y[v]=[x^v]L_G$, $0\le v\le R$ | 3 |
| `one` | $(a)$ | $Y[(s),v]=[x^v]x^sK_G(s)$, $s\le v\le R$ | 6 |
| `two` | $(a,b)$, **not adjacent** | $Y[(s,t),v]=[x^v]x^{s+t}K_G(s,t)$ | 10 |
| `two_adj` | $(a,b)$, **adjacent** | same coordinates | 10 |

These are raw labeled counts at $q$. There is no normalization and no
automorphism quotient. `two` and `two_adj` have the same coordinates; the
edge status is legality metadata. Every type observes the local coefficients
$[x^v]L$ of the current graph, $v=0,\dots,R$, at cost 0.

### Actions and their exact formulas

Each formula is proved by summing over the heights of the vertices whose
role changes. Every other sum is unchanged.

| action | typing | formula | why |
|---|---|---|---|
| `open` | closed→one | $Y'[(s),v]=Y[v-s]$ | new isolated terminal: $K'(s)=L_G$ |
| `close` | one→closed | $Y'[v]=\sum_sY[(s),v]$ | the terminal height joins the interior volume |
| `intro` | one→two | $Y'[(s,t),v]=Y[(s),v-t]$ | new isolated terminal $b$: $K'(s,t)=K(s)$ |
| `intro_adj` | one→two_adj | $Y'[(s,t),v]=q^{(s-t)^2}Y[(s),v-t]$ | the new edge $ab$ contributes $(s-t)^2$ |
| `pendant` | one→one | $Y'[(s),v]=\sum_j[x^j]K_{\text{leaf}}(s)\,Y[(s),v-j]$ | fresh leaf: $K'(s)=K(s)\sum_hx^hq^{(s-h)^2}$ |
| `join` | two→two_adj | $Y'=q^{(s-t)^2}Y$ | adds the edge $ab$ |
| `cut` | two_adj→two | $Y'=q^{-(s-t)^2}Y$ | removes the edge $ab$, which the type guarantees is present |
| `forget_a` | two, two_adj→one | $Y'[(t),v]=\sum_sY[(s,t),v]$ | $a$ joins the interior and $b$ becomes the terminal |
| `forget_b` | two, two_adj→one | $Y'[(s),v]=\sum_tY[(s,t),v]$ | symmetric to `forget_a` |
| `extend_a/b` | two, two_adj→two | existing `OrderedMoveSystem` operator | new terminal adjacent only to the old terminal |
| `swap` | two→two, two_adj→two_adj | $Y'[(s,t),v]=Y[(t,s),v]$ | reorders the terminals |
| contexts | two→two, two_adj→two_adj | existing ordered context operator | a fresh interior and no terminal edge |

The default contexts are an asymmetric one-sided leaf `leaf_a` and the
shared neighbour `shared`. The context and extension matrices are reused
unchanged from `terminal_moves.OrderedMoveSystem`, and the code checks that
their coordinate order matches. Action identifiers on `two_adj` carry the
suffix `@adj`, for example `extend_a@adj`.

### Proposition 5 (the grammar closes at fixed budget)

*Every output coordinate of volume $v$ is a combination of input
coordinates of volume at most $v$. Consequently, for every legal word of
any length, the product of the typed matrices applied to the truncated state
of a placed graph equals the truncated state of the assembled graph.*

*Proof.* Read off the table. `open`, `intro` and `intro_adj` use input
volume $v-s$ or $v-t$. `pendant` and the contexts use $v-j$. Every other
action keeps $v$. The ordered-contexts note proves the extension and
context cases. The formula for each action is exact on the untruncated
kernel. Truncation keeps it exact because no output ever reads an input of
higher volume. Induction on word length finishes the proof. $\square$

### Proposition 6 (legality is sound for assembly)

*If a word is legal from the type of a placed graph, then sequential
assembly never creates a duplicate edge or a loop, and the actual type of
the assembled graph equals the typed end type.*

*Proof.* Use induction over the word. `open`, `intro` and `extend` add a
fresh vertex adjacent to at most one current terminal, so the two
terminals are non-adjacent afterwards. `intro_adj` makes them adjacent
through a fresh edge. `join` is legal only on `two`, where the terminals are
non-adjacent, so the new edge is not a duplicate. `cut` is legal only on
`two_adj`, where the edge exists. Contexts are glued through fresh interior
copies and have no terminal edge (the `OrderedContextAttachment` check), so
they keep the adjacency status and cannot repeat an edge. `swap` and the
forget actions add no edges. $\square$

Proposition 6 does not follow from any matrix identity. Squaring the `join`
matrix gives the factor $q^{2(s-t)^2}$. That is the population of a
*multigraph* with a doubled terminal edge, and the tests confirm it with an
independent multigraph enumeration. The type split `two`/`two_adj` is what
rejects this word. This is the "edge-status changes need boundary metadata"
failure mode named in the packet, resolved here by one bit of type
information.

### Refused extensions

- **Three or more terminals.** Allowing `intro` from `two` would require an
  unbounded family of types. The grammar refuses it. This is an
  implementation boundary, not a theorem that such operations are
  impossible.
- **Joins of two unknown blocks.** These are bilinear and stay outside the
  linear setting. Gluing a *fixed* context is linear, and those operations
  are included.
- **State-dependent guards and minimum-zero normalization.** Neither is
  modelled.

## 4. Certificates and costs (NX13-C)

The portable format is `singularity.typed-operator-closure/1`. It is a new
schema. The single-space format `singularity.operator-closure/1` is
unchanged, and nothing is renamed or migrated. A bundle records the
following:

- each type's identifier and dimension;
- each action's ordered source and target, its matrix with explicit
  `rows` and `columns`, and its cost;
- each observation's type, row and cost;
- per type: the witness experiments (observation, start type, chronological
  word, row, cost), the observation coordinates, the nullspace and the
  pivots;
- per action: the coordinates $T_a$ with explicit shape.

Rationals are canonical `[numerator, denominator]` pairs. An optional
`provenance` field holds the graph adapter's volume convention, terminal
labels, context graphs, coordinate lists and assembly rule. That field is
descriptive only. Algebraic replay does **not** prove the adapter;
Section 5's enumeration does.

`replay_typed_bundle` decodes strictly. It rejects booleans, floats,
noncanonical rationals, shape disagreements, unknown fields, order
mismatches and oversize inputs. `load_typed_bundle` also rejects duplicate
JSON keys and NaN or Infinity. Replay then calls `verify_typed_certificate`,
which rechecks every identity, every witness, cost order, pivots, kernels,
the inclusion $M_aN_s\subseteq N_t$ and the filtration. Replay never calls
`typed_closure`. `scripts/typed_contexts.py --replay` disables both the
closure and the adapter module while it runs, and a unit test disables the
closure the same way.

### Proposition for the operator chapter (proposed text)

> **Proposition (typed observation closure).** Let a finite typed operator
> system have rational matrices $M_a:V_{s(a)}\to V_{t(a)}$, positive action
> costs and nonnegative observation costs. There are realizable witness
> experiments $B_b$, with $\operatorname{rank}B_b\le\dim V_b$, and rational
> matrices $A_b$, $T_a$ with $L_b=A_bB_b$ and $B_{t(a)}M_a=T_aB_{s(a)}$,
> such that (i) every legal chronological experiment row lies in
> $\operatorname{row}B_b$; (ii) $\ker B_b$ is the space of states that no
> legal future experiment detects, and it is carried into $\ker B_{t(a)}$ by
> each $M_a$; (iii) every linear compression preserving all legal future
> readings has rank at least $\operatorname{rank}B_b$; and (iv) if the
> coordinates respect the cost filtration, the first witness pairing
> nonzero with a difference is a cheapest exact distinguishing experiment.
> The identities, and hence (i)–(iv), can be checked from the certificate
> alone.

## 5. Exact finite evidence

These are exact computations over declared finite populations. They are
not proofs of the infinite quantifiers, which Sections 2–3 supply.

- **Adapter against enumeration.** The receipt uses 13 base placements:
  P3 closed; K1 closed; P3 at its middle, at an end, and K1 with one
  terminal; P3 endpoints in both orders; 2K1; P4 at $(0,2)$; P3 adjacent
  in both orders; K2; and a triangle edge. Every legal word of length at
  most 4 at $R=2$, $q=2/3$ (27,439 words) and every legal word of length
  at most 2 at $R=3$, $q=1/2$ (610 words) gives a matrix state that
  **equals the full state of the actually assembled graph**. That state is
  computed by weak-composition enumeration (`kernel_by_enumeration`, or
  `local_coefficients` for `closed`). The unit tests repeat length 3 at
  $R=2$ (4,087 words) and length 2 at $R=3$.
- **Cross-check with existing machinery.** The `forget` and `intro`
  matrices agree with `charges.forget_terminal` and
  `separator_compiler.introduce_terminal`, followed by
  `charges.kernel_from_charges`.
- **Noncommutation.** On actual graphs:
  - (`extend_a`,`shared`) ≠ (`shared`,`extend_a`) on P3 endpoints;
  - (`swap`,`leaf_a`) ≠ (`leaf_a`,`swap`) on P4 $(0,2)$;
  - (`join`,`extend_a@adj`) ≠ (`extend_a`,`join`).

  The swap/leaf pair agrees on the automorphic P3 endpoints even though the
  matrices do not commute. This is a reminder that a reading depends on the
  base as well as the word.
- **Closure.** At $R=2$, $q=2/3$ the full grammar has ranks 3/6/10/10, so
  every type is fully observable. The symmetric sublanguage `shared`,
  `join`, `cut`, `forget_a`, `close`, `open` has ranks 3/3/7/7. Certificates
  for both, and for two rectangular fixtures, are retained and replayed.
  One fixture has a rank-zero type, a zero-dimensional type, a type with no
  outputs, cycles, rectangular maps and noncommuting actions.
- **Cheapest witnesses.** Every reported witness equals the minimum found
  by exhaustive forward search over all legal experiments within the cost
  bound. The bound is 8 for the fixtures and 3 for the graph pairs, giving
  up to 1,185 legal experiments per pair. Each graph witness also reads
  differently on the two actually assembled graphs. The automorphic P3
  endpoint pair has no witness, and the exhaustive search also finds none
  within the bound. The unbounded statement follows from Theorem 4.
- **Tampering.** Reversing a witness word (`("u","f")` becomes illegal; a
  graph witness with a legal reversal gives a different row), changing a
  cost, row, coordinate or type order, or replacing Fractions with ints all
  make verification fail.

## 6. Reproduction

```sh
PYTHONPATH=src python -m unittest tests.test_typed_observability tests.test_typed_contexts -v
PYTHONPATH=src python scripts/typed_contexts.py --check
python scripts/typed_contexts.py --replay results/typed_contexts.json
```

## 7. Limitations

- The grammar is finite and declared: at most two ordered terminals, one
  bit of edge status, fixed $R$ and fixed rational $q$. The type graph is
  not derived from an arbitrary separator schedule.
- Ranks and witnesses are specific to the declared $R$, $q$ and grammar.
  Full rank at $R=2$ says nothing about other budgets or parameters. Equal
  truncated states do not imply equal full series or isomorphic graphs.
- Minimality is linear and per type (Theorem 3). Cheapest means exact
  nonzero distinction under the declared additive costs (Theorem 4). It is
  not robust or maximum-margin optimality.
- State-dependent guards, nonlinear charge joins, infinite type
  collections, three or more terminals, minimum-zero normalization and
  physical or thermal semantics are excluded.
- No proof-assistant formalization exists.
