# Session checkpoints

## Handoff baseline — 2026-10-17

**Research baseline:** 89fb96d25bef0463e41feb74d987b464e5fd534f on main, https://github.com/towre676-cloud/singularity. The handoff package metadata records the later source commit that adds these instructions and task packets.

**Existing research:** fourteen authored chapters; assembled monograph of 34,147 source words and 105 PDF pages; six-page companion paper; exact standard-library Python engine; three retained graph comparisons; independent certificate replay; exhaustive connected-graph census through six vertices; bounded-height forest benchmark through a 96-vertex path.

**Historical checks observed at baseline:** 55 tests passed; retained examples matched; repository checks passed; twelve published relative targets passed against the actual remote tree; all 86 remote blob hashes matched; GitHub Actions succeeded. A new checkout must rerun the inexpensive checks rather than inherit these results by assertion.

**Roadmap status:** see push_status.json and PUSH_AUDIT.md. No formal proof-assistant project exists. An independent level-chain generator, arbitrary tree-decomposition engine and terminal-kernel module remain unimplemented. The broad impact discussion is recorded as proposals in STRATEGIC_EXTENSIONS.md.

**Recommended next batch:** audit and close P01; implement the missing independent enumeration for P02; reconcile and strengthen existing certificates for P03. Reuse working components and preserve all permanent comparison inputs.

## Session 1: 2026-10-17 to 2026-10-18 (Claude Code, cloud session)

**Starting commit, branch and remote relation:** `f79944c` (handoff preparation on top of baseline `89fb96d`), branch `claude/exciting-brown-95vyq3`, created from that commit; the uploaded handoff archive's `repository/` snapshot was byte-identical to the checkout. Baseline checks passed before any edit: 61 tests, retained-example replay, repository and link checks.

**Scope:** the user asked to "build as much as you can"; D008 records this as the explicit override of the three-push batch limit. Each push was accepted only against its original criteria, and most got their own commit.

**Accepted (22):** P01, P02, P03, P04, P05, P06, P09, P10, P11, P12, P17, P18, P19, P20, P21, P22, P23, P24, P25, P26, P28, P29. Each record in `push_status.json` has an `acceptance` receipt that maps every original criterion to tests, data or proofs. The audit sections are synced.

**Mathematical results added (stable IDs):** SNG-F21 volume-pruned chain enumeration; SNG-F23 forest messages; SNG-F24 safe truncation and H=R sufficiency; SNG-F25 span by bounded-box subtraction; SNG-F26 bag-conditioned decomposition recursion; SNG-F27 volume congruence filter; SNG-F28 energy roots of unity and the remote formula; SNG-F29 disjoint order chambers; SNG-F30 rank-sensitive odd-prime Gauss sums; SNG-F31 exact exceptional parameter strata; SNG-F32 order polytopes and non-polynomiality of quadratic weighting; SNG-F33 finite visibility filtrations; SNG-F34 energy weights obstruct P-partition reciprocity (P22, a proved negative result; the Stanley reciprocities are recorded as background); SNG-F35 explicit complex disc around 1/r with branches and uniform tail (P28). Chapter 9 now proves the spectral and binary-pair discrepancies from degree-pair tables and pattern sectors; chapter 4 has the low-volume pattern table; chapter 7 has the exact tail-constant implementation note.

**New specifications:** `docs/specifications/COEFFICIENTS-v1.md` (singularity.coefficients/1, full API crosswalk) and `docs/specifications/CENSUS-v1.md` (singularity.census-manifest/1).

**New modules:** `chains`, `lowvolume`, `decomposition`, `congruence`, `gauss`, `chambers`, `orders`, `parameters`, `visibility`. Extended: `heights` (componentwise quotient), `transfer` (root messages, statistics, marked forests), `certificates` (parser and chain route), `arithmetic` (constant (7.12), exact prime tail and record).

**Independent oracles and finite scopes:** level chains, weak compositions and chambers agree on all labeled graphs with n<=4 through volume 6. Chains and compositions also agree on all 1,099 labeled graphs with n<=5 through volume 6 (479,963 profiles, `results/chain_agreement.json`, 3.8 s). Marked forests agree on all 339 labeled forests with n<=5. Twelve decompositions are checked against Cartesian enumeration. Congruence filters agree with tuple filtering on all graphs with n<=4. Gauss-sum formulas agree with residue sums on all graphs with n<=4 for p=3,5,7 and n=5 for p=3. The census manifest reconciles 1,1,4,38,728,26704 and 1,1,2,6,21,112 through an independent recurrence and orbit–stabilizer.

**Retained outputs added:** `results/chain_agreement.json`, `pair_acceptance.json`, `conductor_fixtures.json`, `gauss_fixtures.json`, `parameter_strata.json`, `visibility_filtration.json`, `tail_records.json`, `complex_discs.json`, `census_manifest.json`, `certificates/regular_cube_mobius.json`. `transfer_benchmark.json` has new H=R cases. Reference discrepancies at volumes 2, 3 and 4 and all fixture labels are unchanged.

**Commands run at every acceptance:** `PYTHONPATH=src python -m unittest discover -s tests -v` (170 tests at the end, all passing), `PYTHONPATH=src python scripts/reproduce.py --check`, `python scripts/check_repository.py`, `python scripts/check_links.py` on README, monograph, CLAUDE.md, handoff, task packets and specifications, `python scripts/handoff.py verify`. Also run: `scripts/chain_agreement.py --check`, `scripts/census_manifest.py --check`, `scripts/benchmark_transfer.py`, `scripts/build_documents.py --no-pdf`. CI now also runs the two `--check` scripts.

**Remote and CI:** every acceptance commit was pushed to `origin/claude/exciting-brown-95vyq3`, and the remote head was compared with the local head each time. The GitHub Actions runs observed for P01–P03, P04–P06, P09–P11 and P12 succeeded on Python 3.10 and 3.12. Later runs were queued or not yet observed when this entry was written.

**Decisions:** D007 (certificate name), D008 (session scope), D009 (no proof-assistant toolchain: P07 and the formal chain stay open), D010 (PDFs stale; LaTeX, HTML and Markdown regenerated with Pandoc 3.1.3).

**Open and next:** P27 is the only dependency-ready push besides P07, which needs a proof assistant (D009). Its obstacle is quantitative, as the ledger records. At s=1/2 the prime 2 has t~0.71, so local factors of the seven-vertex pairs must be evaluated through volume ~100 at fixed q, and the coefficient-aware form of (7.12) is needed for the omitted primes. Exact first action: add a fixed-q, outward-rounded fixed-point variant of the bag-message engine in `decomposition.py`, then build the certified K(s,1/2) table. P35 waits on P27 and P33. P13, P14, P15, P16 and P30–P36 wait on the formal chain (P07/P08) or on P14. P22's result record is `docs/results/order_reciprocity.md`.

## Session 2: 2026-10-18 (Claude Code, cloud session, continued)

**Starting commit:** `0ffc9f9`. The owner proposed three new centers: certified analytic evaluation, an infinite family with exactly controlled visibility depth, and reusable boundary responses. The owner also proposed units P37–P72, recorded in `docs/development/PUSHES-NEXT.md`; the ledger still tracks only P01–P36.

**Accepted:** P27. Certified enclosures of K(s,1/2) are in `results/certified_k.json`, produced by `scripts/certified_k.py` in about 41 minutes and not run in CI:
- spectral pair: K(1/2) in [0.84973, 0.85750]; K(3/5) in [0.89931, 0.89971]; K(1) in [0.9678188, 0.9678191];
- binary pair: K(1/3) in [0.90084, 0.94230].

**Implemented, pending original gates:**
- P32: SNG-F36/F37 pendant-cycle family; gate P31 is open.
- P14: SNG-F40 nested-pair census; gate P08 is open (D009).

**New results:**
- SNG-F36: depth p+1 with discrepancy q^2(1-q)^2(1-q^2)^p, and a closed binary form via a 2x2 transfer matrix.
- SNG-F37: sum-of-squares sign and monotonicity.
- SNG-F38: certified product enclosure with a coefficient-aware tail constant.
- SNG-F39: B_G entire for connected G, with a quadratic height tail.
- SNG-F40: the nested-pair census.
- SNG-F41: gluing and the Whitney twist identity, L - L_tw = 2 sum x^|b| A1 A2.
- SNG-F42: identical-block twist depth min_b(|b|+2v_b), positivity. SNG-F36 with even p is a twist of identical path blocks.
- SNG-F43: marked composition via box kernels.
- SNG-F44: star probes determine a block's kernel; contextual equivalence equals kernel equality.
- SNG-F45: rooted decks bound the asymmetry order. It is sharp on all 27,474 connected blocks with at most six vertices (finite observation).

**Also:** P24's isolating-interval endpoint contract is fixed, with a regression test.

**New modules:** `families`, `certified`, `nested_census`, `terminals`. `decomposition._box` can now return root-conditioned messages.

**Finite searches:**
- No block with at most six vertices has a symmetric kernel without a terminal-swapping automorphism.
- No pairing of distinct asymmetric kernels with at most five vertices vanishes through volume six.
- The six-vertex balanced pairing search was still running at the time of writing.

**Checks:** full unit suite, reproduce --check, repository and link checks, and handoff verify at every commit. `scripts/pendant_family.py --check` was added to CI.

**Next:**
- P31 (structural collision resolution). P32 also needs either P31 or an explicit amendment.
- Formal chain P07/P08 in an environment with a proof assistant.
- Tightness of the star-probe interface count (P51).
- The converse of SNG-F45.
- Narrowing the binary-pair enclosure with a sharper constant.

## Template for the next entry

Date and authoring environment:

Starting commit, branch and remote relation:

Selected roadmap IDs and acceptance claims:

Mathematical result and proof paths:

Implementation, independent oracle, input bounds and measured cost:

Commands actually run and outcomes:

Accepted IDs, partial IDs and remaining acceptance gaps:

Decision record updates:

Local commits, observed remote commit and CI state:

Next dependency-ready item and exact first action:

**Continuation (boundary responses):**
- SNG-F47: swap-symmetric contexts factor through the symmetrized kernel K⁺.
- SNG-F48: (a) a proved top-degree obstruction for edge-free symmetric contexts, positive from budget 7, where {0,5} and {3,4} share s²+t². (b) A constructive recovery of K⁺ from 2M leaf-and-edge probes for budgets R ≤ 24.
- New module `contexts`. `scripts/symmetric_contexts.py --check` runs in CI; its `--census` section, about three minutes, is retained in the file.
- Exact ranks at q0 = 1/2 for R ≤ 9: full with the terminal edge; without it, short by exactly the top-degree bound.
- No nontrivial K⁺ class among the 12,753 connected blocks with at most six vertices, through volume 4.
- These are evidence for the proposed P52/P53 in `PUSHES-NEXT.md`; the ledger is unchanged.
- Open: the budget-free edge-free converse, and orbit triples at R ≥ 25.

**Continuation (observable interface, P54 evidence):**
- SNG-F49: exact observable quotient \(V_R/N_R\) for simple swap-symmetric contexts.
  - Explicit coordinates and a spanning probe family.
  - Exactness proved through R ≤ 25 without the terminal edge, and through R ≤ 91 with it. The proof uses a second functional τ, obtained by trading a leaf for a shared neighbour at the next volume.
  - Explicit blind direction at R = 25 (the triple 325). It is not realizable by blocks, because interior-volume-zero coefficients are fixed by terminal degrees: simple symmetric contexts separate actual blocks through R = 25.
- SNG-F50: a terminal edge of weight below μ_R restores recovery at every budget. μ_R = 2, 3, 4, 5 from R = 7, 25, 47, 91.
- Modular probe-map ranks equal dim V_R − dim N_R for R ≤ 18 without the edge. R = 8..12 are rechecked in CI.
- Compile-once benchmark: kernel 4.6 s; 7.6 ms per query against 1.33 s direct; break-even after 3.5 queries.
- Searches:
  - No two non-isomorphic blocks with at most six vertices share a kernel through volume 4.
  - No two-terminal tree with at most ten vertices has a symmetric kernel without a swap automorphism.
  - Five ten-vertex tree pairs agree through volume 4 and separate at volume 5.
