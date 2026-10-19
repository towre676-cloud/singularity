# Confirmed advantages in Singularity 0.7.0

The new work establishes useful gains from the retained trained byte models. TUNE-selected neural/count blends reduce fresh TEST loss by **2.8186%** across all three seeds, and improve the stronger three-model neural ensemble by **0.4668%**. A separate causal online blend reduces loss by **2.8731%** against the neural models on another fresh suffix, with a standard finite-grid cumulative log-loss guarantee and no blend-weight calibration. A frozen behavioral panel requires **8× fewer input tokens** and gives **8.268× faster median resident prediction** in the declared regression-check workload. The [research companion](../../output/pdf/confirmed_advantages.pdf) develops the methods, exact scopes and complete costs.

The [independent audit](results/confirmed_advantages_audit.json) reconstructs the numerical results without further neural inference. The [validation receipt](results/advantage_validation.json) records the actual local checks. All original training evidence remains available through the [training guide](README.md). The new confirmation studies perform zero neural training updates.

## Use a frozen predictive mixture

Install the optional scientific dependencies with `python -m pip install -e ".[training]"`. The release contains a portable TRAIN-only trigram in [count_expert.json](results/predictive_mixture/count_expert.json). Its smoothing is 0.01 and its TRAIN hash matches the retained neural models. The [frozen deployment recipe](results/predictive_mixture/deployment_recipe.json) records selected weights: neural weights 0.65, 0.65 and 0.60 for seeds 1000, 1001 and 1002. The CLI accepts the **neural** weight, while the study reports the complementary count weight.

From the repository root, score a supplied raw-byte corpus using seed 1000:

```sh
PYTHONPATH=src python scripts/score_byte_mixture.py score \
  --checkpoint applications/training_lab/results/confirmation/wikitext_byte/baseline/seed_1000/checkpoint.pt \
  --counts applications/training_lab/results/predictive_mixture/count_expert.json \
  --neural-weight .65 --corpus new-corpus.txt --output score.json
```

This scores every noninitial byte once, preserves the 64-input causal window, and records hashes and target-weighted metrics. It has no corpus-driven fitting branch. Only load trusted PyTorch checkpoints. The count/neural TRAIN identity and window length must match. Count smoothing and weights supplied to a new deployment should come from an appropriate selection policy; the retained weights are confirmed on the stated WikiText study, not universally optimal.

To fit your own portable count expert using TRAIN only, supply a frozen positive smoothing value. This command needs the standard library; neural scoring needs the training extra.

```sh
PYTHONPATH=src python scripts/score_byte_mixture.py fit-counts \
  --train-path your-train.txt --order 3 --alpha .01 \
  --sequence-length 64 --output counts.json --receipt count-fit.json
```

`CountByteExpert` and `score_frozen_mixture` live in [byte_experts.py](../../src/singularity/training/byte_experts.py). Their public API reproduced all three selected research TUNE scores exactly. The three-model ensemble is retained as a stronger study control; the single-checkpoint CLI does not silently run an ensemble.

## Use causal online blending

[online_blend.py](../../src/singularity/training/online_blend.py) exports `BayesianByteBlend`. Call `predict(neural_probabilities, count_probabilities)` before revealing the target, then `observe(target)` after receiving it. The object rejects a second prediction while an observation is outstanding. `guarantee()` reports the cumulative identity, finite-grid reference and bound.

For equal prior over 21 fixed mixtures, cumulative online log loss is at most the best fixed grid member plus `log(21)` nats. This is a standard Bayesian aggregation guarantee, not a guarantee about accuracy, continuous mixture weights or changing expert policies. The model/count experts stay frozen; the posterior uses only earlier observed targets. It persists across the evaluated stream while neural input windows reset every 64 inputs. Count smoothing still comes from earlier TUNE. This Python implementation adds bookkeeping time, so select it for the blend-weight calibration and cumulative-loss contract rather than speed.

## Run a behavioral smoke check

Prepare the pinned WikiText parquet cache using the original [source preparation script](../../scripts/prepare_training_text.py). It downloads the official splits and retains their hashes and attribution. The behavioral study uses all 512 complete contexts in official TEST bytes [65536,98304); its frozen panel selects 64 of them without shortening any context.

```sh
python scripts/prepare_training_text.py --output scratch-training/wikitext2
PYTHONPATH=src python scripts/check_checkpoint_smoke.py \
  --checkpoint applications/training_lab/results/confirmation/wikitext_byte/baseline/seed_1002/checkpoint.pt \
  --source-dir scratch-training/wikitext2 --reference-seed 1002 --output smoke.json
```

The consumer forwards only selected inputs and compares cached golden outputs. An observed change returns nonzero exit status. An unchanged result establishes equality only on selected argmax predictions. The [runtime pipeline demonstration](results/checkpoint_confirmation/runtime_pipeline_check.json) changes 2,583 selected outputs while the weight file and all thirty state tensors remain identical; this is why behavior testing can reveal a runtime problem that file identity misses.

The measured 8.268× ratio concerns resident forward, argmax and concatenation: 131.657 to 15.923 milliseconds median over thirty randomized pairs. A cold CLI check took 2.386 seconds including imports, corpus loading and model loading. Construction amortizes after 46 resident checks, or 103 including the complete development audit. All eight singleton panels and the simple selectors tie; this example demonstrates smaller behavioral testing, not superiority of exact search. The [timing receipt](results/checkpoint_confirmation/timing.json) retains every pair.

## Inspect and reproduce the confirmation studies

The fixed predictor used fresh TUNE/TEST offsets [32768,65536). The behavioral study used [65536,98304), with seed 1002 and seven-/five-bit perturbations excluded from selection. The online study used TEST [98304,131072). These are separate intervals of the same official dataset, not independent corpora. Protocols preserve these boundaries, selection rules and code hashes.

The commands below create new study directories and perform new scoring. They do not overwrite the reported studies. For inspection alone, read the JSON and loss archives already retained. Use the original result root for the frozen trained checkpoints and the online study's earlier TUNE selection.

```sh
PYTHONPATH=src python scripts/confirm_predictive_mixture.py --freeze --output scratch-training/predictive-replay
PYTHONPATH=src python scripts/confirm_predictive_mixture.py --execute --output scratch-training/predictive-replay --corpus-dir scratch-training/wikitext2
PYTHONPATH=src python scripts/confirm_checkpoint_panels.py freeze --output scratch-training/panel-replay --source-dir scratch-training/wikitext2
PYTHONPATH=src python scripts/confirm_checkpoint_panels.py construct --output scratch-training/panel-replay --source-dir scratch-training/wikitext2
PYTHONPATH=src python scripts/confirm_checkpoint_panels.py audit --output scratch-training/panel-replay --source-dir scratch-training/wikitext2
PYTHONPATH=src python scripts/confirm_checkpoint_panels.py timing --output scratch-training/panel-replay --source-dir scratch-training/wikitext2
PYTHONPATH=src python scripts/confirm_online_blend.py --freeze --output scratch-training/online-replay
PYTHONPATH=src python scripts/confirm_online_blend.py --execute --output scratch-training/online-replay --corpus-dir scratch-training/wikitext2
```

The [fixed predictive receipt](results/predictive_mixture/results.json), [diagnostic audit](results/checkpoint_confirmation/audit.json) and [online receipt](results/online_blend/results.json) include all declared comparators. Loss archives permit numerical replay without more neural inference. Descriptive block intervals are conditional on these frozen models and passages. Full-corpus, new-architecture and unknown-fault advantages require their own confirmation.

Rebuild the two data-derived figures with `python scripts/draw_confirmed_advantages.py`. Build the new PDF with `python scripts/build_training_documents.py --confirmation` using Pandoc, XeLaTeX and DejaVu fonts. The source and every figure read the retained result receipts.
