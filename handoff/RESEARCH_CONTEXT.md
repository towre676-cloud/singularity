# Mathematical and strategic context

## What this project is trying to establish

Singularity studies the information preserved when all labeled integer height assignments on a graph are counted by a few numerical marks. The first question is combinatorial: which graphs become indistinguishable after correspondence between vertices and observations is forgotten? The second question is analytic: how does the first surviving coefficient discrepancy appear after assembling identical local factors over the primes? The current repository supplies a substantial research draft and exact finite machinery. Its existence does not establish historical priority, complete graph reconstruction, a computational complexity breakthrough, or a verified proof-assistant development.

The owner requested a creative mathematical direction beyond the physical, external and commercial ambitions of earlier projects. The useful inheritance from PerfectPower is exact population counting and navigation; from PerfectJet, representations closed under declared operations; from SOE, equivalence under future continuations. The original archival files are not bundled here. Chapter 11 records the bridges that were actually used. Treat those summaries as the available provenance, not as access to unseen personal history.

## Authoritative coefficient semantics

Let G be a finite simple undirected graph with labeled vertices 0,...,n-1. The Graph constructor rejects an empty vertex set, loops, duplicate edges, booleans used as integers and invalid endpoints. Disconnected graphs are allowed. For a nonnegative integer tuple a,

\[
|a|=\sum_i a_i,\qquad E_G(a)=\sum_{ij\in E(G)}(a_i-a_j)^2.
\]

The local series and its common-translation normalization are

\[
L_G(x,q)=\sum_{a\in\mathbb N^n}x^{|a|}q^{E_G(a)},\qquad
B_G(x,q)=(1-x^n)L_G(x,q).
\]

B counts profiles with global minimum zero. This normalization is valid for disconnected graphs too, but it removes one common shift across all vertices. Removing an independent shift in each connected component gives a different population. The fully marked version counts minimum-zero profiles with an additional z raised to their maximum; on these representatives maximum equals span. Never replace a multiplicity by a single occupied-cell indicator.

For threshold sets S_t={i:a_i>=t}, the level chain may have repeated sets. Its identities are

\[
|a|=\sum_t|S_t|,
\qquad
E_G(a)=\sum_t|\delta S_t|+
2\sum_{r<t}e(S_t,V\setminus S_r).
\]

An independent level-chain enumerator must generate chains as its primary objects. Reusing weak compositions and then checking this identity is an identity check, not that independent enumerator. This is an important remaining gap in P02.

## Three permanent comparison inputs

All polynomial differences below mean left minus right; q is formal until explicitly specialized. Graph JSON inputs, not illustrative layouts, specify the graphs.

| Pair | Shared data | First volume r | Difference polynomial | Value at q=1/2 |
|---|---|---:|---|---:|
| spectral_g versus spectral_h | Degree multiset and Laplacian characteristic polynomial | 2 | 2q^2(1-q)^3(1+q) | 3/32 |
| binary_g versus binary_h | Complete binary cut-volume census, all 128 assignments | 3 | q^3(1-q)(1-q^3)^2(1-q^4)^2 | 11025/262144 |
| Cube versus eight-vertex Mobius ladder | Cubic, triangle-free, equal local and marked prefixes through volume 3 | 4 | 2q^4(1-q^2)^4 | 81/2048 |

The spectral witness is already explained by degree-adjacency statistics. The binary pair is not Laplacian cospectral. The cube witness is in span one. Do not conflate these three results into a single stronger pair. Equality with one known invariant does not establish superiority to every established invariant. Use scripts/reproduce.py --check to retain labels, coefficients, signs, factorization and certificate replay.

## Arithmetic scope

For fixed real q in [0,1], the primewise series initially has the elementary absolute convergence domain Re(s)>1:

\[
Z_G(s,q)=\prod_pL_G(p^{-s},q).
\]

For connected G, q=0 gives zeta(ns), while q=1 gives zeta(s)^n. At an interior real q, if equal-order graphs first differ at volume r by delta(q), their ratio has a factor zeta(rs) raised to delta(q), with a controlled normalized remainder near the positive real point s=1/r. Read Chapters 6-8 before changing hypotheses or branch statements. The remainder's real convergence estimate and a local nonvanishing complex neighborhood do not imply global meromorphic continuation.

The prime lift does not add graph information: coefficients at prime powers recover the local coefficients. Delta may vanish at exceptional q, changing the first visibility depth. Formal Euler exponents depending on q need not be integer combinatorial counts. Exact sparse polynomials use Fraction coefficients where rational arithmetic is necessary.

## What the finite evidence establishes

The retained connected simple graph census exhausts labeled inputs through six vertices and quotients by exact degree-respecting permutations. Isomorphism class counts are 1,1,2,6,21,112. At order six all 112 classes separate by local volume three. This is a finite statement. It proves neither unrestricted reconstruction nor a universal depth bound.

The 96-vertex path transfer experiment uses heights at most two and total volume at most twelve. It retains 2,506,262,962,660,245 labeled profiles; each volume marginal is independently checked. It does not enumerate all 3^96 assignments. Forest message passing rejects cycles. Conductor calculations have an explicit finite residue-box budget. Source hashes establish integrity of declared inputs, not authentication or historical priority.

## The 36 pushes and the newer strategic discussion

docs/development/PUSHES.md preserves the original 36 acceptance contracts. handoff/push_status.json audits what exists. The task packets turn those contracts into executable work. Close existing gaps before replacing APIs that already work. In particular the actual certificate format is singularity.certificate/1; the roadmap's relational-height/1 name was a proposal and must not trigger an undocumented format migration.

The later chat identified a possible broader objective: quantify what a representation must remember to remain sufficient under future composition. Boundary-conditioned kernels, minimal linear interfaces and delayed visibility are proposed ways to investigate that objective. No rooted.py, separators.py, general separator engine or completed infinite-family blindness theorem exists in this baseline. Earlier chat discussed those developments, but discussion and attempted delegation did not produce committed implementations. handoff/STRATEGIC_EXTENSIONS.md keeps the proposals separate from completed work and the original push IDs.

The immediate research value comes from a short, inspectable chain: explicitly defined population, exact calculation or proof, precise limitation, and one new structural conclusion. Additional pages are justified when they clarify that chain. A negative result, a counterexample or a proved limitation is a successful research output when its scope and assumptions are explicit.
