# What Must Survive II
Monograph (`monograph.html`), engine and receipts for the loop law of cubic heights, measurement minima through volume 13, the depth theorem for `H=P(Q)+eps q`, and the annular readout criterion.
Run `./verify_all.sh` for the clean-room replay through volume 12. Volume 13: `gen 13` patterns, then `engine 13 patterns rows out.txt [prime]`, about 30 minutes per prime. Volume 14 needs 3 primes and `certify3.py`, `exact_ranks3.py`; `analyze.rr` is only valid through volume 13 for exact values.
Row-file format: `V e nz (col value)*` modulo the prime, column 0 is `n`, column j+1 is pattern j in the `.pats` file (`n m iota edges`). `analyze.py` reconstructs rationals.
Status labels are in the monograph. The source reports quoted by the first report were not available; agreement means agreement with the numbers quoted there.
Revision 4 adds: `promo.py` (pole profiles and sparse witnesses), `witness_verify.py` (exact and independent witness checks), `source.py` (constrained comparisons), `review3.py` (rational window certificates, general-graph reflection). `verify_all.sh` replays through volume 12; volumes 13 and 14 have their rows in `data/` and a rerun takes about 30 minutes per prime. Volume 14 needs 3 primes and `certify3.py`, `exact_ranks3.py`; `analyze.rr` is only valid through volume 13 for exact values.

## Revision 10
Scripts in src/spine replay the caterpillar results (run from a directory holding their outputs): cc.cpp is the census, with DUMP=1 writing d<n>.txt; v.py, m.py, st.py, fl.py, fin.py, ex.py hold the checks. They are not part of verify_all.sh. That statement described the author's original session. The missing caterpillar advance is now restored under supplements/caterpillar_proof_advance; see the November 5 review below.

## Revision 11
src/ising holds the shell 3 energy and caterpillar completeness checks: e.py (closed form), sy.py (symbolic couplings), mf.py (reduced form on census), ms.py (coupling and top term). They read the census dumps made by src/spine/cc.cpp with DUMP=1. Not part of verify_all.sh.

## Revision 12
src/rec holds the exchange identity, first-shell measurements (ex3.py with fast.cpp, a modular dynamic program), the recognition search (rs.py) and explicit volume pairs (vx.py). Not part of verify_all.sh.

## Revision 13
src/root holds the rooted independence rank test (emit.py, rk.cpp: ./rk V nq A < trees), the survivor classification (sw.py, chkm.py) and the 2-terminal identity check (id2.py). Not part of verify_all.sh.

## Revision 14
src/rec/cz.cpp filters all trees for caterpillar impostors, and mx.py classifies them as single exchanges. receipts/rooted_rank_w12_V40.txt records an incomplete rank (7363 of 7813) at weight 12 with V=40 and 10 values of q; a larger cutoff was not completed, so this is unresolved and not evidence of a relation.

## Revision 15
Conjecture 43 of revision 14 is retracted (two.py gives the counterexample). nn.py and nm.py test the ancestor matrix N; bf.py checks Theorem 44.

## Revision 16
src/rec/gr.py checks the bridge covariance relation, and gt.py computes gathering slack on the census dumps.

## Revision 17
src/rec/th49.py checks Theorem 49 on the census dumps.

## Revision 18
src/rec/dg.cpp is the spin census (./dg N), used for Conjecture 33 through n=44 and the gathering search. The tree scripts in src/spine, src/ising, src/rec and src/root are not part of verify_all.sh and use hardcoded paths under ~/wms. receipts/verify_all_rev17.log is a passing core replay.

## November 5 independent assistant audit and portable tree replay

Read `review/REVIEW.md` for the mathematical review of Theorems 35, 38 and 45, exact coverage and limitations; `review/LITERATURE.md` compares primary sources. The correction to Theorem 38 is the forest normalization q^(-rho(W)*a^2). The core graph engine was not changed or rerun.

From the package root:

```bash
python verify_trees.py
python supplements/caterpillar_proof_advance/replay.py
```

These bounded exact Python checks need networkx and sympy. They avoid the author's original directory layout. The recovered supplement contains the full two-parameter volume-4 identity and its checks.

To replay historical scripts through portable staging (optional native targets require g++ with C++17 and __int128):

```bash
python tree_replay.py build tree/shell
python tree_replay.py run cat/fam.py
python tree_replay.py census 18
python tree_replay.py run --max-order 18 ising/mf.py
```

`tree_replay.py` stages sources and outputs under `.tree_work`; `--work-dir PATH` selects another location. It rewrites the old absolute source paths in the staged copies and runs each script in its required working directory. `--max-order` bounds the historical mf/ms census loops; it does not silently change their algebra. Other historical scripts retain their stated order ranges and may require larger census dumps. Direct historical invocations remain archival; use this runner.

The 8.9-million-tree hunt, spin census through N=42 and 7,813-row rooted-rank run are retained as original receipts, not presented as new audit runs. No general-tree completeness claim, external peer-review label or novelty claim is added.

Small historical census fixtures through order 18 are supplied in `data/tree_census` and staged when missing. They can be regenerated by the census command above. The independent Python audit uses exact A,B tuples and does not rely on these fingerprints for its conclusions.
