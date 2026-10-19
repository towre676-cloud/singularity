# Project reference

Detailed mathematical results, engines, documents, releases, and development records. For an introduction, return to [Singularity](../README.md).

## Read or download

[0.9.0 pretrained result guide](../applications/training_lab/PRETRAINED_RESULTS.md) · [Numerical summary](../applications/training_lab/results/pretrained_summary.json) · [Pretrained audit receipts](../applications/training_lab/results/pretrained_audit/) · [Prediction receipts and readable traces](../applications/training_lab/results/pretrained_prediction/)

Version 0.9.0 applies the tools to actual pretrained checkpoints up to 1.71B parameters, with pinned model/tokenizer identities, exact two-witness panels, exhaustive subset verification, CPU audit timing and six causal prediction arms. All measured outcomes are retained. A separate post-hoc nonuniform-prior blend supplies a data-independent ceiling on whole-document extra loss relative to the pure neural predictor. No neural weights are updated.

[0.8.0 audit toolkit guide](../applications/training_lab/AUDIT_TOOLKIT.md) · [Robust audit evidence](../applications/training_lab/results/robust_audit/audit.json) · [Cross-domain confirmation](../applications/training_lab/results/cross_domain/results.json)

Version 0.8.0 adds portable behavioral audit packages for PyTorch and Hugging Face causal models, exact minimum-cost panels that tolerate missing probe results (r-fold coverage with checkable witnesses), a vectorized causal online blend equivalent to the 0.7.0 loop, and a prospectively frozen prose/legal/code confirmation in which an adaptive count baseline outperforms the neural experts. No companion PDF was rebuilt for 0.8.0; the guide is the reference document.

[Confirmed advantages - PDF](../output/pdf/confirmed_advantages.pdf) · [Editable companion](papers/confirmed_advantages.md) · [Runnable confirmation guide](../applications/training_lab/CONFIRMED_ADVANTAGES.md) · [Independent audit](../applications/training_lab/results/confirmed_advantages_audit.json)

Version 0.7.0 confirms fresh-text neural/count prediction gains, finite-grid causal aggregation with a cumulative log-loss bound, and smaller behavioral smoke tests with measured resident inference savings. It includes portable count artifacts, frozen recipes, cached golden outputs and exact/source-bound receipts. The companion separates the empirical gains, mathematical guarantees and workload costs.

[Learning, coordinates, and the cost of observation - PDF](../output/pdf/training_observation.pdf) · [Editable companion](papers/training_observation.md) · [Training lab](../applications/training_lab/README.md) · [Measured analysis](../applications/training_lab/results/analysis.json)

The v0.6.0 revision connects real PyTorch checkpoints to exact finite observation panels. It retains 63 planned training runs, complete compressed trajectories, byte-model references, a coordinate-change study, and disclosed integrity replays. No grokking was observed, and the local meta tuner did not improve mean byte-model test loss. Predicted-class histograms distinguish all twelve checkpoints per architecture using a 23-example construction panel, with all 66 pairs separated again on separate audit examples. These are finite catalogue results. Build the companion with `python scripts/build_training_documents.py` (Pandoc, XeLaTeX, and DejaVu fonts required); package the committed source, PDFs, checkpoints, and evidence with `python scripts/package_training_revision.py`.

[NX36 implementation companion — PDF](../output/pdf/nx36_implementation.pdf) · [HTML](../docs/nx36_implementation.html) · [Editable manuscript](../docs/NX36_MANUSCRIPT.md) · [Acceptance ledger](../handoff/nx36/roadmap.json) · [Recovery audit](../handoff/nx36/recovery/CLAUDE_AUDIT.md)

The implemented NX36 programme adds uncertainty-aware experiment design, original-population reconstruction, typed and arithmetic observation languages, source-bound physical transport, measured application pilots, validated period transport, a larger local analytic disc and independently replayable decision certificates. The [integration review](../handoff/nx36/recovery/INDEPENDENT_REVIEW.md) records cross-review fixes. The [validation report](../results/nx36_validation.json) states actual checks and empirical limitations. A complete source/PDF ZIP is generated with `python scripts/package_nx36.py`; the archive excludes restricted raw athlete data and build caches.

[Frontier companion — PDF](../output/pdf/frontier_companion.pdf) · [HTML](../docs/frontier_companion.html) · [Editable manuscript](../docs/FRONTIER_MANUSCRIPT.md) · [Claude integration note](../handoff/frontier/START_HERE.md)

This separate companion adds exact connected poles, rational-coefficient degree recovery (including fixed pinning), ordered-tree positivity, centered pinned theta limits, and reconstruction of promised threshold graphs from a sufficient logarithmic coefficient prefix. It accompanies the open reconstruction questions and does not implement the proposed NX36 programme.

[Research monograph — PDF](../output/pdf/monograph.pdf) · [HTML](../docs/monograph.html) · [Editable source](../docs/MONOGRAPH.md)

[Paper 1: arithmetic visibility — PDF](../output/pdf/visibility_paper.pdf) · [Source](../docs/papers/visibility.md) · [Claim register](../docs/papers/visibility_claims.md)

[Paper 2: exact observation depth — PDF](../output/pdf/locality_paper.pdf) · [Source](../docs/papers/locality.md) · [Claim register](../docs/papers/locality_claims.md) · [Selection and literature comparison](../docs/papers/second_paper_choice.md)

[Complete v0.4.0 download](https://github.com/towre676-cloud/singularity/blob/main/releases/Singularity-v0.4.0-complete.zip) · [Release manifest](../results/archive_manifest.json) · [Release checks](../results/release_0_4.json) · [Earlier operator release record](../results/operator_checkpoint.json) · [Earlier v0.3.0 archive](https://github.com/towre676-cloud/singularity/blob/main/releases/Singularity-v0.3.0-complete.zip) · [Earlier v0.2.0 archive](https://github.com/towre676-cloud/singularity/blob/main/releases/Singularity-v0.2.0-complete.zip) and [its publication checks](../results/publication_release.json)

The archive contains the source, all three PDFs, editable mathematical documents, exact results, tests, proof sources and dependency manifests. Lean and Mathlib build caches are excluded. No document compiler is needed to read the PDFs.

## What is established

**Exact distinctions.** The retained spectral, binary-census and cube–Möbius pairs first differ at volumes 2, 3 and 4. Explicit infinite families agree to arbitrarily late volumes. Their discrepancy coefficients are proved and independently replayed. The connected six-vertex census has 112 classes, all separated by volume three. The later census covers disconnected graphs too: all 1,044 seven-vertex classes separate through volume five; among all 12,346 eight-vertex classes, twenty pairs agree through volume five and all separate at six. These are finite-population results; see the [retained loop-series report](../results/loop_series.json).

**A scalable compiler.** Connected-support locality computes a prefix from small connected induced vertex sets with ambient degrees retained. Its graph-size cost is linear at fixed maximum degree and volume budget. Separator and forest engines provide complementary algorithms and independent comparisons. Retained benchmarks state their graph class, cutoff and measured scope. The bounded-height 96-vertex path experiment retains 2,506,262,962,660,245 labeled profiles, with every volume marginal independently checked.

For equal-order $d$-regular graphs of girth at least $g$, all coefficients below $g$ agree, and

$$
[x^g](../L_G-L_H)=\bigl(N_g(G)-N_g(H)\bigr)q^{(d-2)g}(1-q^2)^g,
$$

where $N_g$ counts $g$-cycles. This explains the cube–Möbius witness. The loop expansion extends the calculation to the first overlap threshold, with an explicit correction there.

**Sharp reconstruction on a graph class.** Every simple 2-regular graph of known order $n$ is determined by its pinned height series through volume $\lfloor n/2\rfloor$. This worst-case budget is sharp for $n\ge6$.

**A complete enrichment.** Keeping squared height as a separate marker gives $\mathcal P_G(x,u,q)=\sum_hx^{\sum h}u^{\sum h^2}q^{E_G(h)}$, which is complete at every fixed $0<q<1$. Its constructive separating volumes are enormous; this is not an efficient graph-isomorphism algorithm. Completeness of the original fixed-pinning series remains open.

**Interfaces and observation.** Boundary-charge tables compile terminal responses; complete ordered observation charts transport information between experiments. Cycle counts determine the regular-graph series before the first overlap threshold, after which theta, diamond and clique corrections become observable.

**Experiments and observability (v0.3.0).** A two-terminal state can be changed by attaching symmetric graph contexts and read through its coefficients. `observability.py` computes the exact observation space with retained rows that are actual experiment words, certificates of $L=AB$ and $BM_i=T_iB$, the invisible subspace, quotient dynamics, and a provably cheapest distinguishing experiment under positive attachment costs. Cheapest is not strongest: a discarded longer experiment can amplify a discrepancy. `graph_experiments.py` compiles contexts into exact operators. At budget four the interface has dimension 22 and full observable rank, with length-filtered ranks 5, 11, 15, 17, 18, 19, 20, 21, 22. At budget seven a formal direction $e_{((0,5),7)}-e_{((3,4),7)}$ is invisible, explained by the top-volume corank bound. `periodic.py` treats root-of-unity edge phases. There the numerator of $P/(1-x^M)^n$ is palindromic, so agreement through $\lfloor n(M-1)/2\rfloor$ proves full equality. [Chapter 15](../docs/chapters/15_operators_experiments.md) gives the proofs and limitations, [the interface specification](../docs/specifications/OPERATORS-v1.md) gives the contracts, and [the retained receipt](../results/operator_experiments.json) gives the exact evidence. The [edge-factor supplement](../docs/research/VAKIL_BRIDGES.md) adds finite determination for polynomial edge-factor families, triangle tangent ranks and compressed-interface composition. Its [exact experiment](../results/vakil_bridge.json) is replayed in CI.

**Operator expansion (v0.4.0).** Each result below is proved in Chapter 15, implemented, and replayed in CI.
- **Bounded maximum-margin experiments** (`robust_search.py`). No unrestricted optimum need exist, and a finite supremum need not be attained.
- **Minimum-cost shared panels with certified identification** under bounded noise (`panels.py`). Exact branch-and-bound; the problem is set-cover hard in general.
- **Parameter-aware ranks** via determinantal divisors (`parametric.py`). At budgets 1–4 the interface has full rank at every $q\in(0,1)$.
- **Family compression** (`compression.py`). Realizable states are cyclic, so attachment-closed families admit no savings at budgets $\le6$, while star families compress from cubic to quadratic dimension.
- **Sharper periodic cutoffs** from square periods, with a closed form at $M=2$.
- **Noncommuting terminal moves** on ordered states (`terminal_moves.py`).
- **A charge-aware separator compiler** (`separator_compiler.py`) with proved cell and bit bounds.

**Arithmetic and proof scope.** Explicit remainder bounds and outward-rounded computations control the normalized real Euler-product remainder. Core Lean 4.12.0 checks normalization, nested levels, both decisive coefficient certificates and finite cancellation. The separate [Mathlib analysis project](../formal-analysis/README.md) proves the actual real Euler-product factorization and positive normalized boundary limit, including both certified graph pairs at $q=1/2$. Its [source-bound audit](../results/formal_analysis_audit.json) checks 79 declarations, alongside the earlier 91 core declarations, now extended to 128 by OE12. The newer reconstruction and loop theorems have manuscript proofs and computational checks; their Lean formalization is a separate future task.

**Thermal experiment pilot (v0.4.0).** The [source-derived DynaComp plate example](../applications/thermal_diagnostics/README.md) preserves six fault identities on a 144-state exact model. Among 112 declared tests, the cheapest robust diagnostic costs **20**, compared with greedy’s **31** and a fixed protocol’s **44**, at per-cell reset uncertainty and sensor error both **1/100**. All 672 predictions are checked by a separate heat-flux simulator; an independent pair-mask shortest-path computation confirms the optimum. [Chapter 16](../docs/chapters/16_thermal_diagnostics.md) proves the model lift, error composition and permanent blindness of symmetric sensors; [the receipt](../results/thermal_diagnostics.json) records scope and uncertainty sensitivity. Costs are normalized model units and faults are constructed hypotheses, not measured physical outcomes.

**New core proof coverage.** The [operator audit](../results/formal_operator_audit.json) checks 37 new Lean declarations and all 128 core declarations. It covers all-future closure and quotient behavior, natural-cost witnesses, actual residue-complement histograms and the shared-denominator cutoff. Linear dimension minimality, the Python discovery algorithm and rational-cost scaling remain outside that formal coverage. The existing 79-declaration Mathlib project is unchanged. The [ordered-context supplement](../docs/research/ORDERED_CONTEXTS.md) also proves the actual path margin for every budget, with an unattained limiting signal.

## Run and reproduce

```sh
PYTHONPATH=src python -m singularity --help
PYTHONPATH=src python -m singularity compare binary_g binary_h --max-volume 3 --q 1/2
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/reproduce.py --check
PYTHONPATH=src python scripts/locality_family.py --check
PYTHONPATH=src python scripts/overlap_hierarchy.py --check
PYTHONPATH=src python scripts/loop_series.py --check
PYTHONPATH=src python scripts/operator_experiments.py --check
PYTHONPATH=src python scripts/thermal_diagnostics.py --check
python scripts/check_repository.py
python scripts/check_links.py
python scripts/nx36_replay.py --check
python handoff/nx36/tools/handoff.py verify
python scripts/check_nx_decision.py
```

Advanced transfer, locality, moment, terminal and charge-chart engines are available through their Python modules and retained-result scripts. Counts and rank/unrank preserve original labeled assignments. Forest transfer rejects cycles and conductor calculations retain explicit work budgets.

On Windows PowerShell, first set `$env:PYTHONPATH='src'` and omit the `PYTHONPATH=src` prefixes. Optional installation is `python -m pip install -e .`; the command is then `singularity`.

`python scripts/build_documents.py` rebuilds the monograph and both papers with Pandoc and XeLaTeX. `python scripts/build_nx36_documents.py` builds the separate NX36 companion. `python scripts/package_nx36.py` creates the current complete archive and verifies every member hash. [GitHub Actions](https://github.com/towre676-cloud/singularity/actions) runs the exact Python checks, NX36 receipts, the pinned core Lean builds, and the Mathlib analysis build.

## Continue the research

The [NX36 handoff](../handoff/nx36/START_HERE.md) preserves the original **36 expansion tracks and 108 acceptance units**, with an equation-rich [design handbook](../handoff/nx36/HANDBOOK.pdf), source-grounded packets and pinned companion engines. The live ledger and implementation companion record what was built and the exact scope accepted. A unit may legitimately conclude with a proved obstruction, a negative measured result or an explicitly permitted resource-bound refusal; completion does not mean every broader research question was solved. Earlier release ledgers remain intact.

The [original 36-push ledger](../handoff/PUSH_AUDIT.md), [session log](../handoff/SESSION_LOG.md), [current task selector](../handoff/START_HERE.md), and [second-paper decision](../docs/papers/second_paper_choice.md) record achieved scope and precise open questions. The main research frontiers are efficient reconstruction beyond cycle interiors, completeness or a full-series collision for fixed pinning, and realization of the surviving symmetric-interface ambiguities. Finite prefix agreement alone settles none of those questions.

