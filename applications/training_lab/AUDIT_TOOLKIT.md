# Singularity 0.8.0: portable model audits, robust panels and a faster blend

Version 0.8.0 turns the 0.7.0 results into tools that can be applied to other models. It adds four pieces of work, each with frozen protocols and retained evidence:

1. **Standalone audit packages** (`singularity.model_audit`). You build a package from a resident model. It contains only the selected probe inputs, the expected observations, tolerances frozen from clean reruns, the declared execution contract and robust-coverage evidence. A later deployment is checked against that file alone, with no dataset download and no second reference forward pass.
2. **Robust coverage with missing-result tolerance** (`singularity.robust_coverage`). The selector finds the exact minimum-cost panel in which every declared fault is separated by at least *r* probes, together with a witness that can be checked independently.
3. **A vectorized causal online blend** (`score_online_probabilities_fast`, `VectorizedBlendState`). It gives the same predictions as the 0.7.0 loop, does not depend on chunk size, can save and resume exactly, and keeps the log(21) guarantee.
4. **A prospectively frozen cross-domain confirmation** on new prose, legal and source-code documents. It includes a stronger count baseline, and that baseline wins.

## Results at a glance

| Question | Result | Evidence |
|---|---|---|
| Can a cheap panel detect realistic silent deployment faults, even with one result missing? | Exact 2-robust panel: **195 of 961 pool tokens**, minimum confirmed by scanning all 2^20 subsets. Greedy costs 224 under the same requirement. The conventional four-sentence panel (255 tokens) meets the requirement for 6 of 14 distinctions; 1 of 1,000 random panels at the 195-token budget meets it. | [`robust_audit/construction.json`](results/robust_audit/construction.json) |
| Does the frozen panel transfer to a checkpoint excluded from selection? | On seed 1002: all **7/7 construction faults separated twice**; **5/5 held-out faults detected**, three of them twice. The excluded CRLF family and the weaker 56-token truncation are each seen by one panel probe. **No false alarms** in 12 clean control runs (4 controls × 3 checkpoints). The typical-sentence panel misses 6 of 12 faults on seed 1002. | [`robust_audit/audit.json`](results/robust_audit/audit.json) |
| What does checking cost? | Resident check, including package verification: **4.7 ms median**. Observing the full 20-probe pool takes 13.4 ms (2.8× slower, 4.9× more tokens). Cold command-line check: **2.3 s**, nearly all PyTorch import and checkpoint load (the check itself takes ≈9 ms). Break-even: **232** repeated checks counting construction only, or **327** including the development audit. | [`robust_audit/timing.json`](results/robust_audit/timing.json) |
| Is the faster blend the same predictor? | Maximum per-target difference from the 0.7.0 loop: **1.1×10⁻¹⁰ nats** over 2.13 million scored rows; identical argmax decisions. Per-target outputs are bit-identical for every chunk size; save/resume is exact. | [`cross_domain/results.json`](results/cross_domain/results.json), `tests/test_online_blend.py` |
| Is it fast enough? | On 710,397 targets in 40 documents: **1.78 s** median, versus 16.43 s for the 0.7.0 loop (**9.2×**). The 0.7.0 fixed-blend scoring path took 4.07 s median on this host, with a 1.18 s fastest round. The online scorer is within 2× even of that fastest round (1.44×). | same |
| Does blending help on new domains? | Online blending beats the neural model in **all 120 document–seed pairs**: −7.5% loss on legal prose, −16.0% on reference prose and −19.7% on code. It beats the 0.7.0 calibrated fixed blend in every domain and seed (by 0.22%, 0.99% and 1.94%) and in 119 of 120 document–seed pairs; the exception is CC0-1.0 with seed 1002, by 0.0004 nats/byte. | same |
| Is the neural model the best thing to blend? | **No.** The declared stronger count baseline (in-document Witten–Bell order 4) reaches 1.50–1.75 nats/byte, against 3.0–5.5 for the neural model. Blending neural with that adaptive baseline is best everywhere (1.44–1.60), improving on the adaptive counts alone by 0.06–0.15 nats/byte. | same |

All three neural checkpoints are the retained 84,544-parameter WikiText byte transformers. No neural training updates occur in 0.8.0.

## Use it on your own model

### A resident PyTorch callable

```python
from singularity.model_audit import build_package, save_package, check_package, load_package
from singularity.model_audit.adapters import TorchCallableAdapter

def forward(input_ids, attention_mask, position_ids):   # your model; returns [B, T, V] logits
    return model(input_ids, attention_mask=attention_mask, position_ids=position_ids).logits

adapter = TorchCallableAdapter(forward, encode=my_tokenizer_encode, max_context=512, pad_id=0,
                               identity={"weights_sha256": my_digest})
probes = [{"id": "p0", "text": "A short padded prompt", "pad_to": 64, "cost": 64}, ...]
reference = adapter.observe(probes)
clean = [TorchCallableAdapter(forward, encode=my_tokenizer_encode, max_context=512, pad_id=0,
                              batch_size=1).observe(probes)]              # benign reruns
faults = {"no_attention_mask": TorchCallableAdapter(forward, encode=my_tokenizer_encode, max_context=512,
                                                    pad_id=0, pass_attention_mask=False).observe(probes)}
package = build_package(probes, reference, clean, faults, contract=adapter.contract(), requirement=2)
save_package(package, "audit.json")

# Later, against the deployment only:
report = check_package(load_package("audit.json"), deployed.observe, deployed.contract())
```

### A Hugging Face causal model

```python
from singularity.model_audit.adapters import HuggingFaceCausalAdapter
adapter = HuggingFaceCausalAdapter(model, tokenizer, max_context=1024, use_cache=True)
probes = [{"id": "c0", "text": "The capital of France is", "pad_to": 16, "continuation_tokens": 8, "cost": 24}]
```

The adapter tokenizes with `add_special_tokens=False`, left-pads with the tokenizer's pad (or eos) token, passes an attention mask, and offsets position ids by the padding. Continuations are decoded greedily and incrementally with key/value caches. The contract records the tokenizer class, vocabulary digest, special tokens, model class, configuration digest, dtype, padding, positions, cache use, temperature and decoding. Sampling and logits processors are never applied, so generation settings cannot silently alter an observation.

### Command line

```sh
PYTHONPATH=src python -m singularity.model_audit verify applications/training_lab/results/robust_audit/seed_1002_package.json
PYTHONPATH=src python -m singularity.model_audit check applications/training_lab/results/robust_audit/seed_1002_package.json \
    --byte-checkpoint applications/training_lab/results/confirmation/wikitext_byte/baseline/seed_1002/checkpoint.pt
```

`verify` needs no model or PyTorch: it recomputes every separation from the stored deviations and tolerances, checks the witness, and confirms the digest. `check` exits 0 when no declared observation moved, 1 otherwise. `--missing ID ...` reports what the remaining panel still covers when some probe results are unavailable.

## Observations, tolerances and what a flag means

Each probe is scored teacher-forced at every real position. The observations are the argmax token, the top log-probability, the top-two gap and the entropy; continuation probes add the greedy continuation and its log-probabilities. Discrete outputs must match exactly, except at positions where the reference's top two log-probabilities are within `tie_margin = 10⁻⁴`. Continuous features may move by at most

$$\tau_{e,k}=4\cdot\max_{\text{clean runs}}|o_{e,k}-o^{\mathrm{ref}}_{e,k}|+10^{-6}.$$

Clean runs used for calibration (batch size 1, one thread) are separate from those used to measure false alarms (deep copy, batch size 3, reversed order, four threads).

Probability-sensitive observations matter. On the excluded checkpoint, a temperature change from 1.0 to 1.1 leaves every argmax unchanged on the selected panel. It is still flagged by every panel probe through the top log-probability and entropy.

## Robust coverage: the mathematics

Let probes $e$ have exact costs $c_e\ge0$, and let $S_p$ be the set of probes that separate declared distinction $p$. A panel $P$ is *r-robust* if $|P\cap S_p|\ge r$ for every $p$.

**Erasure lemma.** $P$ still separates every distinction after any $f=r-1$ of its results are lost if and only if $P$ is $r$-robust. If some $|P\cap S_p|\le f$, erasing exactly those probes hides $p$. Conversely, erasing $f$ probes from an $r$-robust panel leaves at least one separator in each $S_p$. `survives_erasures` checks the lemma directly by enumerating erasures.

Choosing a minimum-cost $r$-robust panel is weighted set multicover, which is NP-hard in general. The solver uses exact branch and bound. It branches on the deficient distinction with the least slack, and its $i$-th branch includes that distinction's $i$-th admissible separator while excluding the earlier ones. The lower bound sums the $d_p$ cheapest admissible separators of each deficient distinction over a family whose admissible separator sets are pairwise disjoint. Probes counted for different family members are therefore distinct. An exhaustive oracle, written separately, agrees with the solver on 150 random instances at $r=1,2,3$. In the study, a separate bitmask scan of all $2^{20}$ subsets confirms the 195-token optimum.

Exactness covers only the declared construction table. Two panels tie at 195 tokens; the solver returns the one listed first in `construction.json`.

## The vectorized blend

With grid log-likelihoods $\ell_{s,k}=\log\big((1-\alpha_k)p^{\mathrm n}_s(y_s)+\alpha_kp^{\mathrm c}_s(y_s)\big)$, the posterior used at row $t$ is $w_{t,k}\propto\pi_k\exp S_{t,k}$, where $S_{t,k}=\sum_{s<t}\ell_{s,k}$ is an exclusive prefix sum. Row $t$ never reads $y_t$ before forming its weights. Prepending the carried $S$ to each chunk and accumulating sequentially performs the same floating-point additions in the same order for any chunking. Chunked, resumed and whole-stream runs are therefore bit-identical per target, and the saved state is a hexadecimal float vector. The guarantee $L_{\text{online}}\le\min_kL_k+\log K$ is unchanged.

The cross-domain runs exposed one numerical fact. When the posterior concentrates on a single grid weight, the bound's slack is exponentially small, and rounding over about $3\times10^4$ terms can make the computed slack about $-10^{-10}$. This happens in both the reference loop and the vectorized scorer. The first execution attempt aborted on a fixed $10^{-9}$ allowance before writing any results. Revision 2 uses $10^{-9}+2^{-36}L_{\text{online}}$; [`execution_attempts.json`](results/cross_domain/execution_attempts.json) records the abort and the slack-only diagnostic.

## Cross-domain confirmation protocol

Forty documents were selected by a declared hash rule before scoring:

- 16 Python reference-manual topics (technical prose);
- 8 license texts, with duplicate contents removed (legal prose);
- 16 Python standard-library modules (code).

Each document keeps at most its first 32 KiB. Each document is scored independently. Neural windows and TRAIN-count history start at the document start; adaptive counts and online posteriors reset at every document. The protocol and documents were committed (8d95d6c, revision 2 in 876ad5f) before execution. The full per-target archive is retrievable at commit 45c304b. Exact per-document loss sums ([`document_loss_sums.json`](results/cross_domain/document_loss_sums.json)) replay every reported mean and document-cluster interval; `tests/test_v080_evidence.py` performs that replay.

| Domain | Docs | Targets | Neural | TRAIN count | Calibrated fixed | Online | Adaptive count | Online neural+adaptive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Reference prose | 16 | 247,805 | 3.900 | 3.516 | 3.309 | 3.276 | 1.675 | **1.558** |
| Legal prose | 8 | 146,067 | 2.999 | 3.011 | 2.782 | 2.775 | 1.745 | **1.597** |
| Python source | 16 | 316,525 | 5.469 | 4.701 | 4.477 | 4.390 | 1.503 | **1.440** |

All values are NLL in nats per byte, averaged over three seeds where the arm uses a neural model. Every paired document-cluster 95% interval for online−neural, online−calibrated and adaptive−TRAIN-count excludes zero. The neural models were trained on WikiText and are badly out of domain here. Both their raw scores and the size of their blend gains reflect that. The adaptive baseline learns repeated strings within each document (identifiers, license phrasing), which a 64-byte-context neural model cannot. **For these documents, the best deployed choice is the neural + adaptive-count online blend, not the neural model alone or with static counts.**

## Limits

- The fault catalogue is simulated in software on 84,544-parameter byte models. The Hugging Face adapter is tested on a locally constructed GPT-2-architecture model and tokenizer, because this build environment cannot download pretrained models. No pretrained Hugging Face model was audited.
- Robust coverage is exact for the construction table. Detection on seed 1002, held-out faults and the zero false-alarm count are measurements on declared runs, not bounds. The excluded CRLF family and the 56-token truncation each had a single panel separator, so one missing result could hide them.
- A passing check means no declared observation moved beyond its frozen tolerance. It does not establish equivalence, quality or safety.
- The cross-domain documents come from one build environment, and the comparison is descriptive. The log(21) bound is a per-document guarantee against the declared grid only.
- Timings are CPU measurements on a shared host with controlled threads, warmup and randomized order. No GPU was measured.

## Reproduce

```sh
PYTHONPATH=src python -m unittest tests.test_robust_coverage tests.test_online_blend tests.test_adaptive_counts tests.test_model_audit tests.test_v080_evidence -v
PYTHONPATH=src python scripts/confirm_robust_audit.py {freeze,construct,audit,timing}   # refuses to overwrite retained phases
PYTHONPATH=src python scripts/confirm_cross_domain.py {select,freeze,execute}           # likewise
```

Use `--output` with an empty directory to rerun a study without touching the retained evidence. The cross-domain `select` phase reads the build interpreter's standard library and `pydoc_data`; stored documents make later replays independent of the interpreter version.
