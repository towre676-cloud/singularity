# Singularity volume 5: the next height-series coefficient

All work in this directory is new (nothing committed to GitHub; the cloned
repo was only read). Scripts: `vol5_lib.py` (exact enumerator library),
`vol5_main.py` (pools, cumulants, pair fits), `vol5_decomp2.py` (spanning
polynomial decomposition), `vol5_relations.py` (determination identities),
`vol5_final_check.py` (final formula on all pairs),
`vol5_k23e_search.py` (targeted search for the \(f^2\) term). Data:
`vol5_results.json`, `vol5_decomp2.json`, `vol5_relations.json`,
`vol5_final_check.json`, `vol5_k23e_search.json`, with `.log` files.

## The result

For cubic graphs \(A,B\) on \(n\) vertices agreeing through volume 4
(equivalently \((N_3,N_4,N_{\mathrm{dia}},N_{K_4})\) equal), with
\(\kappa=q(1-q^2)\) and \(f=q^{-2}-1\):

\[
\Delta [x^5]L
=\kappa^{5}\Bigl[\Delta N_5
+ f\,\bigl(\Delta N_{K_{2,3}}+\Delta N_{\Theta(1,2,3)}\bigr)\Bigr]
+ \kappa^{5} f^{2}\,\Delta N_{K_{2,3}+e}.
\]

Here \(N_{\Theta(1,2,3)}\) counts houses (a triangle and a square sharing an
edge) and \(N_{K_{2,3}+e}\) counts \(K_{2,3}\) with an extra edge on the
3-side — equivalently, diamonds whose two apex-external edges meet at a
common vertex. A complete proof by the volume-4 method is in `PROOF.md`.

Relation to the repo's SNG-F61: at girth \(\ge4\) the two triangle-bearing
terms vanish and the formula is exactly SNG-F61's
\(\kappa^5(\Delta N_5+f\Delta N_{\mathrm{bicycle}})\), with the bicycle
invariant identified concretely as \(N_{K_{2,3}}\). We confirmed SNG-F61 in
its stated domain: it holds on all 617 triangle-free agreeing pairs in the
pools. Outside that domain it fails (184 of 665 agreeing pairs at \(n=12\)),
and the house term is precisely what repairs it. One plausible guess is
**wrong**: a bowtie term (two triangles at a vertex) cannot appear, because
the bowtie has a vertex of degree 4 and hence count zero in every cubic
graph — the \(f^6\) support that looks like a "multi-triangle correction"
splits instead into the bicycle \(K_{2,3}\), the house, and the
old-determined diamond-with-tail (\(2N_{\mathrm{dia}}\)).

## Computation performed

The stored pools were used in full — no subsampling was needed. The
volume-5 coefficient costs \(\binom{n+4}{5}\) height assignments per graph
(4368 at \(n=12\)); the whole main run (518 graphs: \(n=8\): 62, \(n=10\):
303, \(n=12\): 153, including all subgraph counts on \(\le5\) vertices and
all-pairs analysis) took about 29 s. Sanity anchors all pass: for every
graph and every \(k\le5\), \(\sum_q [x^k]L_G=\binom{n+k-1}{k}\) (the
volume-5 total is \(\binom{n+4}{5}\)); the recomputed \(N_3,N_4,N_{\mathrm
{dia}}\) match the values stored in PR #4's data everywhere; and the
cumulant identity \(\ell_5(G)=\sum_{k\le5}\sum_\tau s_\tau(G)c_\tau\) from
SNG-F55 holds exactly for every graph, cross-validating the height
enumerator against the connected-support expansion.

Agreeing-through-volume-4 pairs are exactly the pairs with equal
\((N_3,N_4,N_{\mathrm{dia}},N_{K_4})\): 519 pairs at \(n=8\), 3,861 at
\(n=10\), 665 at \(n=12\) (5,045 total). Simpler candidate formulas fail as
follows (failures out of those pairs): the zero formula \(\Delta L_5=0\)
fails 42 pairs at \(n=10\) and 417 at \(n=12\); the cycles-only formula
\(\kappa^5\Delta N_5\) fails 186 pairs at \(n=12\); SNG-F61's girth formula
used outside its domain fails 184 pairs at \(n=12\) — exactly the pairs
where \(\Delta N_{\Theta(1,2,3)}\ne0\). The stated formula (with or without
the \(f^2\) term, which vanishes on all pool pairs) has **zero failures on
all 5,045 pairs**.

At \(n=10\) only \(\Delta N_5\) ever varies on agreeing pairs; the house
invariant first separates graphs at \(n=12\) (\(\Delta N_\Theta\ne0\) on
184 pairs, \(\Delta N_{K_{2,3}}\ne0\) on 28). \(N_{K_{2,3}+e}\) is rare in
the pools (nonzero for only 3 of 518 graphs, never varying on an agreeing
pair), so the pools alone do not test the \(f^2\) term; it is forced by the
proof (Step 4: \(K_{2,3}+e\) is a connected 5-vertex pattern with 7 edges,
non-vacuous, and not determined by the other counts). A targeted search
(`vol5_k23e_search.py`, fresh configuration-model samples, seeds
777001/777002, about 320 s) confirms it empirically and decisively: at
\(n=12\), 2,000 graphs gave 115,563 agreeing pairs but none with
\(\Delta N_{K_{2,3}+e}\ne0\); at \(n=14\), 1,500 graphs gave 58,850
agreeing pairs of which **59 have \(\Delta N_{K_{2,3}+e}\ne0\) — the full
formula holds on all 59 and the reduced formula (without the \(f^2\) term)
fails on all 59**. The \(f^2\) term is therefore both proved and
empirically necessary.

## Proof status

**Proved** (in `PROOF.md`, modulo SNG-F55 and the volume-4 theorem): the
full formula including the \(f^2\) term. The argument follows the volume-4
method exactly: the Bell bridge gives \(\Delta L_5=\Delta\ell_5\); supports
of size \(\le4\) are universal functions of \((n,N_3,N_4,N_{\mathrm{dia}},
N_{K_4})\) (via invertibility of the subgraph matrices and eleven explicit
4-vertex pattern formulas, correcting the naive guess — e.g.
\(N_{P_4}=4m-3N_3\), not half that); size-5 supports enter through the raw
identity \(\sum_\tau s_\tau P(\tau)=\sum_Y N_Y f^{e(Y)}\); patterns with a
vertex of degree \(\ge4\) are vacuous in cubic graphs; and the six remaining
non-target counts are absorbed by double-counting identities
(\(N_{\mathrm{fork}}=6n-6N_3\), \(N_{P_5}=12n-9N_3-4N_4\),
\(N_{\text{tri+2 tails}}=3N_3-2N_{\mathrm{dia}}\),
\(N_{\mathrm{tadpole}}=6N_3-4N_{\mathrm{dia}}\),
\(N_{C_4+\mathrm{pend}}=4N_4-2N_{\mathrm{dia}}\),
\(N_{\mathrm{dia+tail}}=2N_{\mathrm{dia}}\)), whose proofs are given in
`PROOF.md` Step 6 and which are also verified exactly on all 518 pool
graphs. No step had to be left as an isolated missing identity: the proof
closes, with the same division of labour as the volume-4 proof (hand double
counting plus finite exact checks on graphs of at most 5 vertices,
itemised in `PROOF.md`).

**Computed:** everything in the previous two sections (pools, fits,
identities, final zero-failure check).

**Conjectured / open:** nothing at volume 5 for cubic graphs. The natural
next question — volume 6, with its much larger set of size-6 support types
and unknown determined/undetermined split — is untouched, as is any
analogue for non-cubic regular graphs, where the vacuity step fails
immediately (bowties and stars reappear).
