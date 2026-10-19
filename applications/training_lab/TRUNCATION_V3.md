# Version 3: quantified truncation coverage

Version 3 is separate from the frozen version-2 GPU experiment. Its validated deliverables are a source-bound retrospective replay, a quantified shape-observability specification, exact multicover with an independently checked optimum, a conservative longer-probe design, and a prospective GPU runner. **No new T4 or A100 forward pass was performed for this change.** Fresh hardware detection, clean-control behavior, and timing remain unmeasured. Version 2's script, protocols, packages and archived results are byte-for-byte preserved from `1e15a4d`; any A100 evaluation of version 2 must continue using its own frozen protocol.

## What the archived evidence actually says

The Qwen2.5-1.5B real input lengths, descending, start at 76, 72, 66 and 64. Padding widths and continuation costs are not input lengths. Only `full_history` has more than 72 input tokens. The two archived separators for `truncate_to_72` are `full_history` and `full_sport`. The latter's input and teacher-forced output both remain 72 tokens: its flag is continuous, with maximum top-logprob and entropy deviations of approximately 0.02356 and 0.03342 nats against 0.0001 tolerances. It has no discrete mismatch or shape mismatch. This second signal cannot serve as a value-independent truncation guarantee. Changed batching is a possible explanation, not an established causal measurement.

The v2 exact panel costs 261 forwarded-token units and misses that known case. All nine formerly held-out v2 faults were already exposed before v3 design. **They are retests in v3, never genuinely new held-out validation.** Numerical health remains a separate failure: the archived eager-attention candidate is not an approved clean configuration.

## Observability theorem and its boundary

Let probe e contain N_e real input tokens. Assume the observer returns one teacher-forced argmax entry for every retained real token, removes padding positions, and does not fabricate outputs for removed positions. A service cap t, applied before the forward pass, leaves min(N_e,t) entries. Therefore the Boolean structural separation column is

$$A_{e,t} = [N_e > t].$$

If N_e > t, the differing list length flags regardless of logits, ties or continuous tolerances. If N_e <= t, there is no structural guarantee; numerical changes may still occur. Retaining the first t tokens, the last t tokens, or any t real positions has the same cardinality argument. This does not prove sensitivity to hidden-context windowing that still returns full-shaped outputs, fabricated observations, last-token-only endpoints, or generation-only APIs. Passing any finite panel is not semantic equivalence.

For requirement r=2 and every integer cap 1 through T, coverage requires

$$\sum_e x_e A_{e,t}\ge2\quad(1\le t\le T),\qquad x_e\in\{0,1\}.$$

The columns are nested. The constraint at T implies every smaller-cap constraint. Equivalently, the pool must contain at least two distinct probes longer than T. The greatest feasible T is the second-largest N_e minus one. A selected panel satisfying these constraints retains at least one separator for each declared cap after any single probe erasure. Distinct probes provide erasure robustness, not statistical independence or protection against a shared adapter failure.

Every integer cap is represented. Caps between consecutive distinct real lengths have identical separation columns, so the implementation stores maximal intervals with constant columns. This compression preserves the feasible set and the exact optimum. Greedy uses this same frozen canonical interval representation; as with any set-cover heuristic, duplicating equivalent columns could change its gain weighting and its output. Every comparator here sees identical columns, costs and requirements.

The optimization also includes the measured non-length construction distinctions:

$$\min_x\sum_e c_ex_e\quad\text{subject to}\quad\sum_e B_{e,f}x_e\ge2\ (f\in F),\quad\sum_e A_{e,t}x_e\ge2\ (1\le t\le T).$$

Here B is derived only from calibrated construction observations. The old position-offset variant has zero observed separators; it is explicitly outside the retrospective guarantee and remains a diagnostic in the prospective runner. The six previously detectable construction faults remain declared. Version 3 refuses any deficient declared column, unavailable declared variant, or unhealthy selection data instead of silently narrowing F.

## Retrospective evaluation on the original 18-probe pool

The old pool's two-witness structural frontier is T=71. Exact selection costs **271**, optimally pruned greedy **271**, ordinary greedy **301**, and the unchanged representative panel **286**. The representative panel fails the combined requirement; its minimum-cost feasible completion costs **409**. The exact panel is `full_history`, `full_sport`, `pad_capital`, `uni_ligature`, `uni_width`, and `nl_list`.

The additional cost over v2 is **10 tokens, or 3.83%**. The pool still costs 667. Exact and pruned greedy tie; there is no advantage over that stronger baseline. Exact costs 9.97% less than ordinary greedy on this frozen interval representation. Every declared cap 1–71 has two guaranteed shape witnesses, and every one of the six declared measured construction faults has two archived witnesses. The panel flags all nine old v2 evaluation cases on replay, including two signals for the known 72-token case. Four archived clean validations still have no flags. These are reused observations, not newly executed panel batches; fresh selected-panel execution may have different numerical behavior.

The complete exact cost frontier is retained in `results/gpu_deployment_audit/v3_retrospective_t4/results.json`. Costs stay 261 through cap 65, rise to 271 for caps 66–71, and become structurally infeasible for a two-witness guarantee at caps 72–75. At cap 76 and above no original probe is longer than the cap, so even one structural witness is impossible. Merely adding the two historically flagged probes cannot change that length limit.

## Conservative repair through cap 72

A narrower projected repair uses two distinct 73-token guards and declares **every cap 1–72**, rather than selecting the two previously flagged original probes. The independently certified conservative cost is **269 tokens**, only **8 more than v2 (3.07%)**, again tying optimally pruned greedy. These new guard observations are unmeasured. The original four non-length probes cost 123 and the guards cost 146. Although the original pool's cap-71 guarantee costs 271, adding suitable probes changes the feasible set and can reduce the panel cost even while strengthening the guarantee. Comparators are evaluated on the same expanded pool. The runner supports this design with `--maximum-cap 72`; its default 127 gives a broader declared family.

## Conservative design through cap 127

Add two distinct 128-token inputs. Give them no unmeasured coverage credit for quantization, Unicode, masking, temperature or dtype changes. Credit their truncation-to-48 separation only by the same conditional shape theorem. An exact solution of this conservative design costs **379**, comprising 256 tokens for the guards plus 123 for `pad_capital`, `uni_ligature`, `uni_width` and `nl_list`. It is optimal for this explicitly conservative coverage table, not a measured optimum for a new GPU observation table. Actual long-probe measurements may reveal additional coverage and a cheaper panel.

The incremental projected cost is **118 tokens, or 45.21%**, over v2's 261. On the same conservative table, pruned greedy ties 379; ordinary greedy costs 557. The unchanged representative panel is infeasible; its cheapest feasible completion costs 665. The projected full pool costs 923. There is no measured latency or break-even claim. A 379-token accounting cost does not imply a proportional GPU speed change.

Any two length-only witnesses for cap 127 must each have at least 128 real tokens, so they alone cost at least 256 under this accounting. The 379 solution demonstrates a sufficient combined design. Both new token sequences must actually be distinct and meet their recorded lengths under the frozen tokenizer. The runner constructs guards from different texts, measures their actual tokenization and charges actual cost, so the projected 379 is not hard-coded as a promised run result. This conservative calculation assumes the original probes retain their source-configuration coverage; new calibration and execution must remeasure it.

## Prospective runner and separation of evidence

For a one-cell T4 run, open [the Colab notebook](https://colab.research.google.com/github/towre676-cloud/singularity/blob/main/notebooks/Singularity_v3_T4.ipynb), or paste [the launcher](../../scripts/colab_t4_v3_launcher.py) into one Colab cell. It pins the tested source commit `1b54e3c`, checks the original Qwen revision before freezing, reports progress, independently verifies the result and downloads a ZIP containing evidence and environment receipts. Failure produces a clearly labelled partial diagnostic ZIP. Model weights, temporary exports and caches are excluded. The launcher does not change the v3 protocol or rerun v2. No fresh T4 result is claimed merely by publishing the launcher.

For a command-line run, install the repository's optional pretrained dependencies in an existing GPU environment, including accelerate and bitsandbytes for the declared quantized variants. Run the separate script from a checkout containing this change:

```bash
python scripts/colab_deployment_audit_v3.py --model Qwen/Qwen2.5-1.5B --maximum-cap 127 --output deployment_audit_v3_t4
python scripts/colab_deployment_audit_v3.py --phase verify --output deployment_audit_v3_t4
```

The model revision, hardware, dtype, tokenizer contract, software versions, input texts, real lengths, costs, maximum cap, calibration envelope, construction faults, evaluation variants, comparator representation and relevant source hashes are frozen before forward passes. Reference and calibration observations must have healthy full teacher-forced shapes. Calibration retains the v2 cache/batch envelope, tie handling, shared continuation prefixes, factor 4 and floor 1e-4. Non-finite reference, calibration or construction output aborts selection; it cannot become a cheap construction witness. Evaluation health failures remain explicit, and a numerically unhealthy candidate is never approved clean.

The exact and comparator panels are saved after construction and before evaluation. The runner then executes known v2 retests, cap-family implementation checks, genuinely selection-excluded new faults, independent clean configurations, the position diagnostic and eager-attention candidate. Cap-family checks validate implementations of a declared family; they do not establish out-of-family generalization. New held-out variants alter alternating attention-mask positions, permute output-vocabulary logits, and translate every vocabulary logit by the same constant. They never affect selection or calibration. The uniform logit translation is an intentionally observationally invisible mathematical control for normalized probabilities, subject to floating-point effects; it should not be portrayed as a fault the audit ought universally to detect. It is reported alongside the actual misses.

The local-test mode uses a random tiny CPU model and explicitly omits bitsandbytes faults. It is a software smoke test, not Qwen or GPU evidence. No optional model dependencies were available in the local development environment; the full phase and health workflow was exercised locally with an explicitly labelled test double. Subsequently, the focused GitHub CPU job successfully executed the entire prospective workflow with a real tiny random Qwen model, and the main-branch neural contracts and v3 certificate workflows passed. None of these CPU checks is a T4/A100 measurement. No test-double observations were retained as scientific measurements.

The emitted portable `package.json` certifies measured construction coverage. The accompanying `certificate.json` additionally certifies the conditional shape family, identical comparator requirements and independently enumerated minimum costs. Keep both. The portable package alone does not prove the quantified truncation claim. Source hashes establish identity, not external authenticity or correctness of a model adapter. A frozen timestamp and phase files document process order; they are not a trusted remote attestation.

## Independent replay and regression checks

```bash
python scripts/confirm_truncation_v3.py --verify
PYTHONPATH=src python -m unittest discover -s tests -p test_truncation_v3.py -v
```

The retrospective verifier recomputes the source protocol digest, verifies its portable package, reconstructs stabilized observations and tolerances, recomputes every construction/retest/clean separation, rebuilds length intervals, reruns exact optimization, and independently enumerates subsets to check optimality. Every retained v2 file is SHA-256-bound. The design certificate is checked separately and expressly labels its new probes unmeasured.

The prospective verifier binds protocol, raw observations, portable package and combined certificate; rebuilds the pre-evaluation construction snapshot; requires every declared observation collection; reconstructs the package; recounts health sentinels; and recomputes all evaluation verdicts. Coverage and optimal pruning are checked by integer-mask all-subsets enumeration independent of branch-and-bound. Enumeration above 22 probes fails with a work-limit error, never an infeasibility verdict. Larger pools need a separately checkable lower-bound/optimality certificate before this protocol can scale further.

Regression tests cover every integer-cap boundary, real versus padded length, missing witnesses, duplicate probes, exact agreement with another exhaustive oracle on random small problems, rehashed certificate tampering, invisible observations, the full retained T4 replay, phase order, unavailable numerical calibration, clean shape changes and falsified numerical-health reports. The new standard-library CI job runs the selection and evidence checks without requiring a model download or GPU.
