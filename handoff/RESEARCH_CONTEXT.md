# Mathematical and strategic context

## What this project is trying to establish

Singularity studies the information preserved when all labeled integer height assignments on a graph are counted by a few numerical marks. The first question is combinatorial: which graphs become indistinguishable after correspondence between vertices and observations is forgotten? The second question is analytic: how does the first surviving coefficient discrepancy appear after assembling identical local factors over the primes? The v0.2.0 release completes the original P01–P36 acceptance program and contains two focused papers, exact algorithms and two Lean proof packages. These achievements do not establish historical priority, efficient general graph reconstruction or completeness of the original fixed-pinning series.

The original handoff at commit `89fb96d25bef0463e41feb74d987b464e5fd534f` had a 105-page monograph, partial implementations and no proof package. That is historical context. The current documents are a 146-page monograph, a ten-page visibility paper and an eight-page observation-depth paper. `results/manuscript_counts.json` records the exact assembled source word count. Use the current ledger and source-bound receipts rather than treating old baseline limitations as current gaps.

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

The independent level-chain enumerator is implemented in `src/singularity/chains.py`: chains are its primary search objects, repeated levels are allowed, and mixed boundary terms supply the energy. Weak compositions provide its independent comparison oracle. The retained finite agreement is in `results/chain_agreement.json`. The P01 specification is `docs/specifications/COEFFICIENTS-v1.md`; P02 is no longer a missing implementation.

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

The formal chain now has two parts. `formal/` is a core-only Lean 4.12.0 package covering normalization, nested levels, decisive graph certificates and finite cancellation; its audit lists 91 declarations. `formal-analysis/` uses pinned Mathlib to prove actual local convergence, logarithmic remainders, the regularized prime product, real zeta factorization and the positive normalized boundary limit. Its source-bound audit lists 79 declarations. The concrete spectral and binary theorems at q=1/2 discharge the finite hypotheses and prove their exact exponents. Read `formal-analysis/README.md` for setup and scope: this is a positive-real theorem, not global complex meromorphic continuation.

## What the finite evidence establishes

The retained connected simple graph census exhausts labeled inputs through six vertices and quotients by exact degree-respecting permutations. Isomorphism class counts are 1,1,2,6,21,112. At order six all 112 classes separate by local volume three. This is a finite statement. It proves neither unrestricted reconstruction nor a universal depth bound.

The 96-vertex path transfer experiment uses heights at most two and total volume at most twelve. It retains 2,506,262,962,660,245 labeled profiles; each volume marginal is independently checked. It does not enumerate all 3^96 assignments. Forest message passing rejects cycles. Conductor calculations have an explicit finite residue-box budget. Source hashes establish integrity of declared inputs, not authentication or historical priority.

## Structural achievements and the next research frontier

The original P01–P36 program is complete. `docs/development/PUSHES.md` preserves its contracts; `handoff/push_status.json` and `handoff/PUSH_AUDIT.md` record acceptance evidence. The actual certificate format remains `singularity.certificate/1`; the alternate original name was resolved without a silent migration. An empty `python scripts/handoff.py next --limit 3` result means the original program is finished, not that the project has no open questions.

Named terminal kernels, checked tree decompositions, marked gluing, Whitney-twist identities, symmetric-context quotients and boundary-charge interfaces are implemented. Explicit pendant-cycle and twist families have unbounded first-separation volume. Connected-support locality supplies a compiler with linear graph-size cost at fixed degree and budget. For simple 2-regular interiors of known order n, the pinned series determines the cycle type through volume floor(n/2), with a sharp worst-case budget for n>=6. These are family theorems, stronger than extrapolations from a small census.

The moment enrichment `P_H(x,u,q)=sum_h x^(sum h) u^(sum h^2) q^(E_H(h))` is complete at every fixed 0<q<1 (SNG-F58), with an enormous constructive separating-volume bound. This is not an efficient isomorphism algorithm. The scalar fixed-pinning series `A_H(x,q)=sum_h x^(sum h) q^(E_H(h)+2 sum h^2)` has a different unresolved inverse problem: prove completeness or construct a genuine full-series collision. Keeping squared height as a separate marker and specializing it away are distinct operations.

Start the next work from `docs/papers/second_paper_choice.md` and its precise open agenda. Productive targets include a hybrid connected-support/separator compiler, reconstruction beyond 2-regular interiors, the fixed-pinning inverse, and realization or exclusion of the remaining symmetric-interface candidates at budgets 38 with a terminal edge and 11 without. `handoff/STRATEGIC_EXTENSIONS.md` distinguishes achieved components from these frontiers. The proposed P37–P72 file is an ideas inventory whose older evidence annotations require a fresh audit, not a second completed ledger.

The immediate research value comes from a short, inspectable chain: explicitly defined population, exact calculation or proof, precise limitation, and one new structural conclusion. Additional pages are justified when they clarify that chain. A negative result, a counterexample or a proved limitation is a successful research output when its scope and assumptions are explicit.
