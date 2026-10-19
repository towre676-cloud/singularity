# Singularity training lab

This optional lab connects real PyTorch training to Singularity’s exact observation machinery. It provides small causal models, reproducible AdamW comparisons, a working one-step hyperparameter derivative, and exact diagnostic panels built from frozen predictions. The retained experiments did **not** produce grokking or a successful new general-purpose optimizer. Their clearest positive result concerns observation: full predicted-class histograms distinguish checkpoints that accuracy alone cannot distinguish, using an exactly minimized panel within the declared probe family.

The [retained analysis](results/analysis.json) covers 36 original confirmation runs, a nine-run declared follow-up, and a six-run coordinate-basis study. Twelve discovery runs bring the initial training total to 63 logical runs. Verification replays are recorded separately; they are additional computation, not additional independent seeds. The [original protocol](results/protocol.json), [follow-up declaration](results/grokking_followup/protocol.json), [basis protocol](results/basis_study/protocol.json), and [integrity replay receipt](results/integrity_replays.json) preserve those distinctions.

The v0.8.0 [audit toolkit guide](AUDIT_TOOLKIT.md) adds standalone audit packages, robust probe panels, a vectorized online blend and a cross-domain confirmation. The v0.7.0 [confirmed advantages guide](CONFIRMED_ADVANTAGES.md) adds fresh predictive gains, a causal online blend and measured behavioral smoke tests using these retained models. The historical training findings below remain the original study.

## Install and run a small check

Run the commands in this guide from the repository root. The exact arithmetic core remains usable without PyTorch. The `training` extra installs PyTorch, NumPy, Matplotlib and PyArrow; all retained experiments used CPU execution. The recorded environment was PyTorch 2.14.1+cpu, with one CPU thread per run. Version and source hashes in each run describe what actually executed; another software or hardware environment is not promised bitwise-identical results.

```sh
python -m pip install -e ".[training]"
singularity-train --help
python -m unittest discover -s tests -p "test_training*.py"
python -m unittest discover -s tests -p "test_byte_reference_baselines.py"
```

Save this configuration as `smoke.json`. It runs twenty updates on a small modular-addition population, with TEST evaluation disabled. A smoke test checks that the pipeline works; its outcome is not a meaningful generalization experiment.

```json
{
  "task": "modular_addition",
  "p": 7,
  "split": {
    "split_seed": 1729,
    "train_orbits_per_label": 2,
    "tune_orbits_per_label": 1,
    "test_orbits_per_label": 1
  },
  "model": {"name": "mlp", "hidden": 32},
  "optimizer": "adamw",
  "variant": "baseline",
  "lr": 0.001,
  "weight_decay": 0.1,
  "betas": [0.9, 0.999],
  "batch_size": 16,
  "steps": 20,
  "eval_every": 10,
  "seed": 0,
  "threads": 1,
  "evaluate_test": false
}
```

```sh
singularity-train --config smoke.json --output scratch-training/smoke
```

The equivalent module entry point is `python -m singularity.training.cli`. Use a new output directory for each experiment. The study drivers reject completed-run replacement; the low-level runner is intended for explicitly managed individual runs. Modular splits keep each unordered input orbit `{a,b}` together, stratify by the answer class, and then expand both input orders. Byte-language splits must be separate supplied files with distinct hashes; missing corpora never trigger synthetic replacement text.

## Prepare the real byte corpus

The [preparation script](../../scripts/prepare_training_text.py) retrieves the official Salesforce WikiText-2 raw splits at revision `b08601e04326c79dfdd32d625aee71d232d685c3`. It joins nonempty source rows with newlines and selects fixed byte prefixes: 262,144 training bytes and 32,768 bytes each for TUNE and TEST. It writes the source URLs, parquet hashes, selected-byte hashes, attribution and selection rule into `source_manifest.json`. The [retained source manifest](results/wikitext_source_manifest.json) records the published experiment’s inputs.

```sh
python scripts/prepare_training_text.py --output scratch-training/wikitext2
```

The language model predicts raw bytes, with 256 possible outputs. Targets shift exactly once, and ignored padding targets do not contribute to loss. Each split resets its context; within a split, nonoverlapping 64-input-byte windows score every byte except the first exactly once. Reported cross-entropy is weighted by valid targets. These prefix experiments measure byte-level loss and bits per byte, not standard word-level WikiText perplexity or pretrained GPT-2 performance.

## Reproduce the declared experiments

The [original driver](../../scripts/run_training_revision.py) first compares three fixed hyperparameter configurations on discovery seed 9000 using only final TUNE loss. It then freezes that choice per architecture and evaluates baseline AdamW, cosine scheduling, layer learning-rate decay, and local meta tuning on seeds 1000, 1001 and 1002. The tasks are a modular MLP, a small causal modular transformer, and a two-layer byte transformer. Their confirmation caps are 12,000, 6,000 and 1,500 optimizer updates respectively. TUNE can guide construction; TEST never feeds training and is scored once at the end of each logical confirmation run.

```sh
python scripts/run_training_revision.py discovery --output scratch-training/reproduction --data-dir scratch-training/wikitext2
python scripts/run_training_revision.py confirmation --output scratch-training/reproduction --data-dir scratch-training/wikitext2
```

The [follow-up driver](../../scripts/run_grokking_followup.py) was declared after the original TUNE curves showed memorization without generalization. It uses a new orbit split, discovery seed 9001, and a three-value weight-decay search. On fresh seeds 2000–2002 it compares the original fixed settings, the selected stronger fixed settings, and meta tuning from those selected settings for 20,000 updates. It is a separate follow-up, not a retroactive change to the original protocol.

```sh
python scripts/run_grokking_followup.py discovery --output scratch-training/reproduction/grokking_followup
python scripts/run_grokking_followup.py confirmation --output scratch-training/reproduction/grokking_followup
```

The [basis study](basis_study.py) tests a different mathematical idea: complete orthonormal input coordinates preserve the nonlinear MLP’s initial function, while coordinatewise AdamW need not preserve its updates. The real Fourier features contain no answer labels and retain the full input information. The first weight matrix is transported so that all 961 initial input outputs agree within the declared tolerance. Separate single-update controls check SGD’s orthogonal equivariance, AdamW’s permutation equivariance, and AdamW’s Fourier non-equivariance. The command without `--run` writes the frozen protocol and performs only those initial and single-update checks; `--run` launches six 20,000-update runs on seeds 3000–3002. TEST is scored at completion, with no TUNE hyperparameter search in this study.

```sh
python applications/training_lab/basis_study.py --output scratch-training/reproduction/basis_study
python applications/training_lab/basis_study.py --output scratch-training/reproduction/basis_study --run
```

Grokking requires more than a lower loss. The declared memorization threshold is TRAIN accuracy at least 99% for three consecutive scheduled evaluations; generalization requires TUNE accuracy at least 95% for three consecutive evaluations. A positive delay between observed thresholds is required to describe delayed generalization. Uncrossed thresholds remain right-censored at the fixed update cap. None of the retained original, follow-up or basis runs crossed the generalization criterion.

## What the retained results show

The table gives means over the three original confirmation seeds. Modular accuracy is a fraction of correct answers; loss is cross-entropy in nats per target. The uniform modular reference is accuracy `1/31` and loss `log(31)`, about 3.434 nats.

| Original task | Fixed AdamW TEST loss | Meta TEST loss | Fixed AdamW accuracy | Meta accuracy |
| --- | ---: | ---: | ---: | ---: |
| Modular MLP | 16.5470 | 6.4287 | 0.0000 | 0.0000 |
| Modular transformer | 9.4583 | 7.9129 | 0.0112 | 0.0153 |
| WikiText byte transformer | 2.1160 | 2.1269 | 0.3973 | 0.3942 |

The local meta mechanism computes connected one-step learning-rate and weight-decay derivatives and accepts proposals by backtracking on a fixed, separately sampled TUNE batch. This proves that the implementation can differentiate its virtual AdamW step; it does not prove improved generalization. In the modular tasks, its lower loss does not raise accuracy to the uniform reference, and its loss remains worse than that reference too. On the byte task, fixed AdamW has the lower mean TEST loss, at 3.0527 bits per byte versus meta’s 3.0685. Cosine and layer-decay results are retained in the full analysis, with no winning-arm omissions.

The stronger-decay follow-up selected weight decay 3.0 at learning rate 0.001 and betas `(0.9,0.99)`. Retuned fixed AdamW and retuned meta both retained zero TEST accuracy; their mean losses were 3.9508 and 3.9492 nats. The Fourier basis study likewise retained zero TEST accuracy for both arms, although Fourier coordinates lowered mean loss from 5.7787 to 5.4538 nats. The isolated coordinate-control effect is real; these runs do not turn it into a grokking or accuracy result.

The [count-model references](results/byte_reference_baselines.json) fit unigram, bigram and trigram counts on TRAIN, choose each smoothing coefficient on TUNE, then score the selected models on the same 32,767 TEST targets. The retained trigram reached 3.2003 bits per byte and 37.22% accuracy. The small neural baseline has lower loss on these prefixes, but this is an explicitly post-training short-memory reference comparison, not a broad language-model superiority claim.

## Exact observation panels

Accuracy loses information about *which* wrong classes a checkpoint predicts. The original accuracy language gives one signature class for the twelve MLP checkpoints and five classes for the twelve modular-transformer checkpoints. The exploratory histogram language retains all 31 predicted-class counts within each of eight fixed labelled blocks, defined by target class modulo eight. Base-`N+1` encoding stores each count vector exactly; it does not add model expressivity or training information.

For both architectures, exact search selects the single block `label-mod-8-7`: **23 construction examples instead of 239**, a 90.4% reduction in prospective panel inference cost. It distinguishes all twelve frozen checkpoint signatures. A separate TEST audit, with no panel reselection, keeps all **66 of 66** checkpoint pairs separated using the corresponding 22-example block. Independent enumeration checks all 256 subsets of the eight declared blocks. This minimum is exact within that supplied probe pool, not among every conceivable experiment. The full construction table had already been evaluated, so its discovery cost is not a free saving. Histogram equality is also weaker than equality of per-input predictions; the result is a finite observation theorem, not model equivalence or improved prediction accuracy.

The [prediction-table builder](../../scripts/build_training_prediction_table.py) checks the retained checkpoints, predictions and metadata before creating accuracy-panel inputs. The [histogram adapter](../../scripts/training_output_language.py) reuses the same saved predictions and needs no additional neural inference. The [MLP histogram report](results/output_language/modular_mlp_output_language_report.json) and [transformer histogram report](results/output_language/modular_transformer_output_language_report.json) preserve construction costs, exact selections and separate audit witnesses.

```sh
python scripts/build_training_prediction_table.py --results applications/training_lab/results/confirmation --output-dir scratch-training/audit/accuracy-panels
python scripts/training_output_language.py --self-check
python scripts/training_output_language.py --results applications/training_lab/results/confirmation --output-dir scratch-training/audit/histogram-panels
python scripts/training_panels.py scratch-training/audit/accuracy-panels/modular_transformer_prediction_table.json --output scratch-training/audit/transformer-panel.json
```

## Audit, checkpoints and reproducibility

Each run saves its configuration, environment and training-source hashes, data identity, raw update records, completion summary and checkpoint. Checkpoints contain model parameters, Adam state, Python/Torch/sampler RNG states, update counters, initial/final tensor hashes and meta-probe identity when applicable. Modular runs also retain final labelled TUNE predictions and, when enabled, TEST predictions. TEST-free discovery still loads or constructs split metadata and hashes; `evaluate_test:false` means no TEST **evaluation**, not that the file is never opened for identity checks.

```sh
python scripts/analyze_training_revision.py --results applications/training_lab/results --output scratch-training/audit/analysis.json --figure scratch-training/audit/training-results.svg
python scripts/draw_training_observation.py --results applications/training_lab/results --output scratch-training/audit/training-observations.svg
```

The analysis accepts raw `metrics.jsonl` or its lossless gzip representation, verifies the uncompressed content hash and update coverage, and reports whether original byte-corpus paths remain available. On another machine, unavailable original paths limit that check to metadata binding; reproduce the pinned source bytes and compare their manifest hashes before claiming corpus-byte verification. Shared-host elapsed times include monitoring and additional computation and are not dedicated-hardware throughput measurements. Three observed seeds support seed ranges, not a general statistical significance claim.

Only load checkpoints you trust: the helpers use PyTorch’s full checkpoint format with `weights_only=False`. For ordinary lab models, `singularity.training.runner.load_checkpoint(path)` returns `(model, optimizer, state)` for inspection. Basis checkpoints require `load_basis_checkpoint` from [basis_study.py](basis_study.py); the ordinary factory does not automatically understand `basis_mlp`. Saved RNG states make detailed replay possible, but the loader is not a command for resuming an interrupted trajectory. File hashes identify artifacts; equal final tensor hashes are a stronger numerical comparison than equality of serialized checkpoint bytes, which also contain metadata and RNG records.

The original experiment’s [frozen engine snapshot](results/engine_source_snapshot/manifest.json) remains available. An integrity audit found incomplete saved streaming logs in several completed runs. The [replay receipt](results/integrity_replays.json) discloses 24,100 extra optimizer updates and eight additional TEST evaluations, including a failed replay attempt; verified replay models, optimizer states and final outcomes matched. These repeats repair artifact evidence and do not count as fresh confirmation seeds. The current production runner closes the stream, rebuilds the complete JSONL payload from its existing in-memory records, atomically replaces the log and verifies its bytes before completion. This changes persistence and elapsed I/O time, not the numerical update rule.

The repair command below is deliberately separate from the read-only analysis: it can retrain affected runs, archive original artifacts and replace canonical copies after equality checks. Use it on an experiment directory you intentionally want repaired, with the original corpus paths available, rather than as a routine viewing command.

```sh
python scripts/replay_training_integrity.py --results scratch-training/reproduction
```

Update covariance sketches, spectral concentration, entropy and their gap are descriptive feature telemetry. They are not Hessian eigenvalues or stability certificates. The source tests cover causal masking, target alignment, orbit separation, padding, functional hypergradients, state preservation and deterministic replay; the retained result files establish only the outcomes actually reported above.
