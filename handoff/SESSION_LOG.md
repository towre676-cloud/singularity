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

**Accepted (20):** P01, P02, P03, P04, P05, P06, P09, P10, P11, P12, P17, P18, P19, P20, P21, P23, P24, P25, P26, P29. Each record in `push_status.json` has an `acceptance` receipt that maps every original criterion to tests, data or proofs. The audit sections are synced.

**Mathematical results added (stable IDs):** SNG-F21 volume-pruned chain enumeration; SNG-F23 forest messages; SNG-F24 safe truncation and H=R sufficiency; SNG-F25 span by bounded-box subtraction; SNG-F26 bag-conditioned decomposition recursion; SNG-F27 volume congruence filter; SNG-F28 energy roots of unity and the remote formula; SNG-F29 disjoint order chambers; SNG-F30 rank-sensitive odd-prime Gauss sums; SNG-F31 exact exceptional parameter strata; SNG-F32 order polytopes and non-polynomiality of quadratic weighting; SNG-F33 finite visibility filtrations. Chapter 9 now proves the spectral and binary-pair discrepancies from degree-pair tables and pattern sectors; chapter 4 has the low-volume pattern table; chapter 7 has the exact tail-constant implementation note.

**New specifications:** `docs/specifications/COEFFICIENTS-v1.md` (singularity.coefficients/1, full API crosswalk) and `docs/specifications/CENSUS-v1.md` (singularity.census-manifest/1).

**New modules:** `chains`, `lowvolume`, `decomposition`, `congruence`, `gauss`, `chambers`, `orders`, `parameters`, `visibility`. Extended: `heights` (componentwise quotient), `transfer` (root messages, statistics, marked forests), `certificates` (parser and chain route), `arithmetic` (constant (7.12), exact prime tail and record).

**Independent oracles and finite scopes:** level chains, weak compositions and chambers agree on all labeled graphs with n<=4 through volume 6. Chains and compositions also agree on all 1,099 labeled graphs with n<=5 through volume 6 (479,963 profiles, `results/chain_agreement.json`, 3.8 s). Marked forests agree on all 339 labeled forests with n<=5. Twelve decompositions are checked against Cartesian enumeration. Congruence filters agree with tuple filtering on all graphs with n<=4. Gauss-sum formulas agree with residue sums on all graphs with n<=4 for p=3,5,7 and n=5 for p=3. The census manifest reconciles 1,1,4,38,728,26704 and 1,1,2,6,21,112 through an independent recurrence and orbit–stabilizer.

**Retained outputs added:** `results/chain_agreement.json`, `pair_acceptance.json`, `conductor_fixtures.json`, `gauss_fixtures.json`, `parameter_strata.json`, `visibility_filtration.json`, `tail_records.json`, `census_manifest.json`, `certificates/regular_cube_mobius.json`. `transfer_benchmark.json` has new H=R cases. Reference discrepancies at volumes 2, 3 and 4 and all fixture labels are unchanged.

**Commands run at every acceptance:** `PYTHONPATH=src python -m unittest discover -s tests -v` (164 tests at the end, all passing), `PYTHONPATH=src python scripts/reproduce.py --check`, `python scripts/check_repository.py`, `python scripts/check_links.py` on README, monograph, CLAUDE.md, handoff, task packets and specifications, `python scripts/handoff.py verify`. Also run: `scripts/chain_agreement.py --check`, `scripts/census_manifest.py --check`, `scripts/benchmark_transfer.py`, `scripts/build_documents.py --no-pdf`. CI now also runs the two `--check` scripts.

**Remote and CI:** every acceptance commit was pushed to `origin/claude/exciting-brown-95vyq3`, and the remote head was compared with the local head each time. The GitHub Actions runs observed for P01–P03, P04–P06, P09–P11 and P12 succeeded on Python 3.10 and 3.12. Later runs were queued or not yet observed when this entry was written.

**Decisions:** D007 (certificate name), D008 (session scope), D009 (no proof-assistant toolchain: P07 and the formal chain stay open), D010 (PDFs stale; LaTeX, HTML and Markdown regenerated with Pandoc 3.1.3).

**Open and next:** dependency-ready after this session: P22 (now `planned`), P27, P28 and P07 (needs a proof assistant). P27's obstacle is quantitative: near s=1/r the proved tail decays like C r P^(-1/r), with C about 451 for the binary pair at rho=1/32, so a useful certified enclosure needs a coefficient-aware sharper constant and interval-enclosed prime products. Exact first action for P28: use `regularized_tail_constant` to give an explicit disc around s=1/r on which the omitted-prime logarithm is uniformly bounded, and certify the finitely many small-prime factors nonzero there. P13, P14, P15, P16, P31–P36 wait on the formal chain or on P14.

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
