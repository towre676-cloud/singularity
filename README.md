# Singularity

**How much of a hidden structure can observation reveal?**

Singularity turns that question into exact mathematics. It counts the configurations a network makes possible, finds the first observation that exposes a difference, and designs experiments that reveal more for less. It can also prove when an entire language of experiments will remain blind.

![The cube and Möbius ladder agree through volume three, then separate at volume four by an exact polynomial.](docs/assets/singularity-observation.svg)

[**Read the monograph**](output/pdf/monograph.pdf) · [**Explore the discoveries**](docs/papers/locality.md) · [**Use the confirmed AI tools**](applications/training_lab/CONFIRMED_ADVANTAGES.md) · [**See the applied experiment**](applications/thermal_diagnostics/README.md)

## Better predictions. Smaller checks. Measured results.

Singularity now connects exact observation mathematics to useful tools for trained AI models. The **0.7.0 confirmation release** improves fresh-text predictions, builds economical behavioral smoke tests, and supplies a causal probability-combination API with a proved finite-grid log-loss bound.

![Every retained neural seed improves with a tuning-selected count mixture on fresh WikiText text; a stronger three-model ensemble improves too.](docs/assets/confirmed-prediction.svg)

**Improve the models already trained.** A blend of our frozen byte transformer and TRAIN-only text counts reduces mean fresh TEST loss by **2.82%**, with improvements in all three seeds and all sixteen text blocks. Mean next-byte accuracy rises from **41.35% to 42.20%**. The stronger three-model ensemble also improves by **0.47%** in loss. Settings were selected on separate TUNE text before TEST; the new study performs **zero neural training updates**. These are small, real WikiText-2 byte-model results, with saved per-target losses and complete comparators.

**Adapt a blend without calibrating its weight.** A separate causal Bayesian blend improves loss by **2.87%** over the neural model on another fresh passage. Its cumulative log loss stays within **log(21) nats** of the best declared fixed grid mixture. Predictions precede the current target; only earlier targets update the blending weights. This standard aggregation guarantee is implemented and independently replayed. Count smoothing still uses earlier TUNE, and online bookkeeping adds runtime.

![A selected behavioral smoke panel uses eight times fewer input tokens and reduces median resident CPU prediction from 131.7 to 15.9 milliseconds.](docs/assets/confirmed-deployment.svg)

**Check executed behavior with less inference.** A frozen panel uses **4,096 instead of 32,768 input tokens**, retaining full contexts. It detects all eight declared output changes on a checkpoint excluded from selection, including perturbation strengths absent from construction. Thirty paired CPU measurements show **131.7 ms to 15.9 ms median resident prediction**, an **8.27× speedup**. Construction and the complete development audit amortize after **103 checks**. The runtime demonstration catches changed predictions even when the weight file and every state tensor remain identical. Cold CLI setup is separate; simple one-block selectors match the exact optimum in this example.

Use the [**confirmation guide and commands**](applications/training_lab/CONFIRMED_ADVANTAGES.md), read the [**new research companion**](output/pdf/confirmed_advantages.pdf), or inspect the [**independent result audit**](applications/training_lab/results/confirmed_advantages_audit.json). The [training lab](applications/training_lab/README.md) retains the original 63 training runs, checkpoints, compressed logs, and earlier outcomes. The guarantees concern the stated finite workloads and observation languages; all source, cost and transfer boundaries remain explicit.

## A small difference with a long reach

The two networks above each have eight vertices, twelve edges, and three neighbors at every vertex. Give their vertices nonnegative integer heights, and measure the squared height difference along every edge. Count the resulting profiles by their total height. The first three layers agree exactly. The fourth reveals the difference.

Singularity proves where that distinction comes from: the cube has six squares; the Möbius ladder has four. More generally, for regular graphs with no shorter cycles, the first visible cycle count determines an exact discrepancy coefficient. There are also infinite families whose differences hide beyond any prescribed finite depth. Observation has a structure of its own—and we can calculate it.

The arithmetic connection goes further. Feed these local counts into a product over the primes, and the first different coefficient controls a singularity at a precise reciprocal depth. A finite combinatorial distinction becomes a measurable feature of an infinite arithmetic object. The [arithmetic visibility paper](docs/papers/visibility.md) develops that bridge; the [Lean analysis project](formal-analysis/README.md) checks the positive-real factorization and boundary asymptotic.

## Recover structure. Choose the experiment. Know the limit.

**Recover a network from its possibilities.** Singularity reconstructs every simple 2-regular graph of known order from a sharp finite observation budget. Retaining squared height as an additional marker gives a complete graph invariant at every fixed parameter between zero and one. That completeness proof can require enormous observation depths; efficient general reconstruction remains an open frontier. The [observation-depth paper](docs/papers/locality.md) explains the results and their boundaries.

**Find the experiment that makes the difference.** Attachments to a graph become operators on an exact interface. The engine discovers everything the allowed operators can reveal, preserves the information needed for every future attachment sequence, and returns a cheapest distinguishing experiment under the declared costs. It also searches for robust shared panels when observations carry bounded uncertainty. The [operator chapter](docs/chapters/15_operators_experiments.md) connects these guarantees to runnable algorithms.

![The same path has two terminal choices with equal passive readings. One shared-neighbor attachment separates their readings by exactly one eighth.](docs/assets/chosen-experiment.svg)

**Count enormous populations through their structure.** A retained experiment on a 96-vertex path counts **2,506,262,962,660,245 labeled height profiles** under its stated bounds. Locality, separator methods, and exact generating functions make those populations accessible without listing each profile. The [implementation guide](docs/IMPLEMENTATION.md) describes which method fits which problem.

**Prove when observation cannot succeed.** Symmetry and invisible interface directions can make two states indistinguishable under every experiment in a specified language. Singularity returns the invisible space and the observable quotient. That turns a failed search into an explanation of what information is missing—and what kind of new observation is needed.

## From a theorem to a better diagnostic

Consider a heated plate with six possible fault hypotheses. A symmetric sensor cannot distinguish two reflected faults, however long the original heater protocol runs. Changing the observations breaks the symmetry. Singularity then chooses a diagnostic panel robust to the declared reset and sensor errors.

![Exact simulated thermal fields for reflected blocked bonds, the fixed left sensor, and diagnostic costs of 20, 31 and 44.](docs/assets/thermal-diagnosis.svg)

On the exact 144-state model, its optimal robust panel costs **20**, compared with **31** for greedy selection and **44** for a fixed protocol. An independent heat-flux simulator checks all 672 candidate predictions, and a separate optimization confirms the minimum. These are constructed faults and normalized model costs, not field measurements. The [thermal diagnostic example](applications/thermal_diagnostics/README.md) gives the complete model, uncertainty assumptions, and reproduction command.

## The mathematics underneath

![A five-cycle with heights 0, 1, 3, 2, 0 has total height six, squared-edge energy ten, and three nested threshold sets.](docs/assets/height-profile.svg)

One series starts the story:

$$
L_G(x,q)=\sum_{h\in\mathbb N^{V(G)}}x^{\sum_vh_v}\,q^{\sum_{uv\in E(G)}(h_u-h_v)^2}.
$$

Here **x records how much height we use**, while **q records the disagreement across edges**. Each coefficient counts original labeled assignments. From this common language come connected-support expansions, cycle and overlap formulas, boundary-charge interfaces, exact observation operators, reconstruction theorems, and arithmetic visibility.

The evidence is part of the project. The [result index](docs/THEOREM_INDEX.md) and [claim registers](docs/papers/visibility_claims.md) distinguish mathematical proofs from finite computations. The [core Lean project](formal/README.md) and separate [Mathlib analysis project](formal-analysis/README.md) state exactly what is kernel-checked. General completeness of the ordinary fixed-pinning invariant remains open.

## Try an exact comparison

Python **3.10+**, using the standard library. From a source checkout:

```sh
PYTHONPATH=src python -m singularity compare binary_g binary_h --max-volume 3 --q 1/2
```

This compares two seven-vertex graphs with the same complete binary cut census and reveals their first height-series difference at volume three. For the full command interface, run `PYTHONPATH=src python -m singularity --help`. On Windows PowerShell, first set `$env:PYTHONPATH='src'`, then run the Python command without the prefix.

## Go deeper

The [**research monograph**](output/pdf/monograph.pdf) develops the original theory. The [**frontier companion**](output/pdf/frontier_companion.pdf) extends reconstruction and analytic structure. The [**NX36 implementation companion**](output/pdf/nx36_implementation.pdf) connects experiment design, uncertainty, arithmetic observations, physical transport, and measured application pilots. Each has editable sources and accompanying evidence in the [reading and project reference](docs/PROJECT_REFERENCE.md).

For developers and researchers, that reference also preserves the complete engine catalogue, reproduction commands, release history, handoff ledgers, proof audits, and [validation results](results/nx36_validation.json). The packaged release is a versioned snapshot; [download current main](https://github.com/towre676-cloud/singularity/archive/refs/heads/main.zip) for subsequent work.

**The next question is yours:** which hidden structures can your observations distinguish, what will they always miss, and what is the best experiment to perform next?

