# Audit a deployed model artifact

Singularity builds a small behavioral audit package once, then checks later deployments against that package. A check runs the deployed model only. It uses the saved reference observations, tolerances and coverage witness; it does not rerun the reference model or select new probes.

The deployment experiment extends the earlier pretrained audit with actual Safetensors serialization/reload, an executable TorchScript graph, dynamic INT8 Linear modules saved and reconstructed from their packed state, eager versus SDPA attention, and two-chunk KV-cache execution. The intentionally injected pipeline faults execute in a separate text-to-logit service, outside the unchanged audit adapter.

## Build a package

The benchmark runner currently supports CPU FP32 Llama-style Hugging Face models with unscaled RoPE. Its graph has an explicit contract: batches of one through three, at most 96 input positions, and full prefill without a KV cache. The separate native service exercises KV caches. The general [`TorchCallableAdapter`](../../src/singularity/model_audit/adapters.py) and [`build_package`](../../src/singularity/model_audit/core.py) support other model services without this benchmark's Llama graph restriction.

Install the measured dependency versions to reproduce the study:

```sh
python -m pip install -e '.[pretrained]'
python -m pip install torch==2.8.0 transformers==4.57.1 tokenizers==0.22.2 safetensors==0.8.0 numpy==2.5.4 matplotlib==3.10.7
```

Download the pinned SmolLM2-360M snapshot outside the repository. Restoring the acquisition receipt also restores the original download bookkeeping after every file hash is verified:

```sh
python scripts/fetch_pretrained_models.py \
  --model smollm2-360m --destination ../models \
  --receipt applications/training_lab/results/pretrained_audit/smollm2-360m/acquisition.json
```

Freeze the protocol before executing the model. Choose an empty results directory and a fresh artifact directory. Preserve the protocol and source revision before running the next command.

```sh
python scripts/confirm_deployment_audit.py freeze \
  --model-path ../models/smollm2-360m \
  --model-id HuggingFaceTB/SmolLM2-360M \
  --revision f8027fd0eaeea54caa13c31d31b9fdc459c38b49 \
  --target float32 --threads 4 \
  --output ../deployment-rerun/float32 --artifacts ../deployment-rerun-artifacts

python scripts/confirm_deployment_audit.py run \
  --model-path ../models/smollm2-360m \
  --model-id HuggingFaceTB/SmolLM2-360M \
  --revision f8027fd0eaeea54caa13c31d31b9fdc459c38b49 \
  --target float32 --threads 4 \
  --output ../deployment-rerun/float32 --artifacts ../deployment-rerun-artifacts
```

The original `--target dynamic_int8` profile halted at its declared clean calibration: SDPA changed non-tie outputs. That prospective no-package outcome remains retained. The useful quantized package comes from a separate, explicitly post-calibration **eager-only contract repair**, with unchanged probes, faults, tolerances and selection. Reproduce that profile using the wrapper after restoring the original failure receipt:

```sh
python scripts/materialize_pretrained_evidence.py materialize
python scripts/confirm_int8_contract.py freeze \
  --model-path ../models/smollm2-360m \
  --model-id HuggingFaceTB/SmolLM2-360M \
  --revision f8027fd0eaeea54caa13c31d31b9fdc459c38b49 \
  --threads 4 --output ../deployment-rerun/dynamic_int8_eager \
  --artifacts ../deployment-rerun-eager-artifacts
```

Preserve the frozen protocol and repeat that exact command with `run` instead of `freeze`. The wrapper binds its own source hash and the original failure/protocol hashes, and adds the approved eager/batch-one/full-prefill envelope to every package before hashing and measurement. It never changes the original frozen producer.

The INT8 target requires PyTorch's `fbgemm` CPU quantization backend. It reconstructs the quantized model independently and loads its packed state with `torch.load(weights_only=True)`. The receipt binds the original and reconstructed state hashes, the actual quantized module names, and every saved artifact. The FP32 receipt separately binds the executable graph file and its shape contract. Generated weights and graphs are local execution artifacts; the repository retains their hashes and complete behavioral evidence.

## Check an existing deployment

The new checker takes the selected package, the pinned source snapshot, the existing deployment artifacts and their receipt. It verifies file hashes, tokenizer identity and loaded state before checking the selected observations. This example checks the saved TorchScript graph:

```sh
python scripts/check_deployment_package.py \
  ../deployment-rerun/float32/package_exact.json \
  --model-path ../models/smollm2-360m \
  --artifacts ../deployment-rerun-artifacts/float32 \
  --artifact-receipt ../deployment-rerun/float32/artifact.json \
  --backend torchscript --threads 4 \
  --output ../deployment-rerun/float32/cli_torchscript.json
```

Use `--backend eager` or `--backend sdpa` to check the native artifact. `--batch-size 3`, `--threads 2` and `--cache-split-denominator 2` or `3` exercise different serving paths. The latter runs two chunks, split after one half or one third of the input; the traced graph supports full prefill only. `--missing PROBE_ID` excludes an unavailable selected probe and reports which declared construction distinctions remain separated. The checker exits 0 for `unchanged`, 2 for a behavioral or contract change, 3 for a measurement outside the calibrated INT8 envelope, and 4 when missing results remove retained coverage without a positive flag. It reports setup/load time separately from resident check time.

An INT8 package has its own numerical reference and tolerances. The repaired contract approves the eager backend with batch-one full prefill. SDPA, batch-three and cache-chunk clean transfers are retained separately and can flag numerical drift. The checker reads that approved envelope from the hashed package metadata, gives an outside-envelope request the top-level `deployment_status: outside_calibration`, preserves its raw behavioral measurement, and exits 3 even when no drift is observed. Hard identity or contract failures take precedence. Such a clean transfer is not classified as a faulty deployment, and a quantized model is not assumed equivalent to its FP32 source.

## Read and independently verify the evidence

`protocol.json` binds the code, original snapshot, immutable model revision, probe inputs, costs, construction faults, held-out faults, clean configurations and timing design before inference. `frozen_panel.json` binds all compared panels before held-out observations. `package_exact.json` is the portable minimum-cost two-witness package; `package_pruned_greedy.json`, `package_random_median.json` and `package_full_pool.json` preserve the matched alternatives.

Every cost comparison uses the same coverable construction distinctions and the same two-witness requirement. The exact cost is checked against every one of the $2^{18}$ subsets. The greedy baseline is optimally pruned over all of its subsets. Each of 64 seeded random feasible prefixes is also optimally pruned; all outcomes are retained, including how often random search reaches the exact optimum. Exact selection certifies the optimum even when a heuristic finds the same cost.

Raw observations are readable JSON chunks of at most 64 KiB. `observations_manifest.json` specifies their coordinates, byte sizes and hashes. The independent verifier needs only these files and the result receipts, without model weights, PyTorch or the benchmark's comparison/selection implementation:

```sh
python scripts/verify_deployment_confirmation.py ../deployment-rerun/float32
PYTHONPATH=src python -m singularity.model_audit verify \
  ../deployment-rerun/float32/package_exact.json
```

Resident timings include package verification, inference and comparison for every arm, including the full 18-probe package. The result separates common reference/calibration time, construction-fault observations, selection, package creation, and artifact preparation. Break-even counts charge all comparator selection work to each panel as a conservative overhead. They describe repeated resident audit checks on this host; cold process imports, disk hashing and model loading are reported separately by the checker. They do not measure generation or training acceleration.

The two-witness certificate guarantees that losing one selected result cannot hide a covered construction distinction in the retained construction observations. Held-out faults and clean transfers are measurements. `unchanged` means none of the declared observations moved beyond its frozen tolerance; it does not prove that the model is equivalent or that all possible deployment faults are covered.
