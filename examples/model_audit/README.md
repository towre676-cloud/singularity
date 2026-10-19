# Certified model audits in GitHub CI

The composite action at `.github/actions/model-audit` checks a local Hugging Face causal-language-model deployment against a reviewed reference package. It independently verifies the package digest and finite robust-coverage witness before loading weights, runs only the selected probes, fails the job on a changed contract or observation, and uploads the mathematical certificate, raw observations, execution settings, JSON diagnostics and a readable report even when the audit fails. No billion-parameter model is required. The checker does not support remote inference endpoints, arbitrary serving wrappers, custom model code or quantized loaders; those need an adapter with its own execution contract. The local adapter tests the pipeline it executes, not an unrelated production server.

## Quick start without a model download

Use Python 3.12 and the dependencies measured here. The action installs Singularity from its own checked-out source with `--no-deps`; callers install their chosen framework first. This prevents a certificate check from silently upgrading the model runtime.

```bash
python -m pip install 'torch==2.8.0+cpu' --index-url https://download.pytorch.org/whl/cpu
python -m pip install 'transformers==4.57.1' 'tokenizers==0.22.2' 'safetensors==0.8.0' .
python examples/model_audit/create_reference.py --tiny --model ./tiny-model --output ./reference
python -m singularity.model_audit.ci check \
  --model ./tiny-model --package ./reference/reference.json \
  --execution ./reference/execution.json \
  --expected-package-sha256 "$(cat ./reference/reference.sha256)" --output ./healthy-audit
python -m singularity.model_audit.ci replay ./healthy-audit \
  --expected-package-sha256 "$(cat ./reference/reference.sha256)"
python examples/model_audit/intentional_fault.py ./tiny-model
python -m singularity.model_audit.ci check \
  --model ./tiny-model --package ./reference/reference.json \
  --execution ./reference/execution.json \
  --expected-package-sha256 "$(cat ./reference/reference.sha256)" --output ./fault-audit
# The last command must exit 1: deployment weight identity changed.
```

The tiny fixture is a seeded, randomly initialized GPT-2 architecture with a locally trained byte BPE tokenizer, not a pretrained language-quality experiment. It exercises actual Hugging Face loading and forward passes. `create_reference.py` observes three probes, calibrates on a clean batch-size-one rerun, declares a temperature-1.3 construction fault and selects an exact panel with two separating probes. The integration test also injects that silent temperature fault while keeping the declared identity fixed, proving probability-sensitive detection without relying on a changed weight-file digest.

Reference creation belongs in a trusted review process. The demonstration workflow creates its reference in the same job solely to test the plumbing. **Production CI must use an already reviewed package and separately pinned canonical `package_sha256`, never regenerate either from the deployment under test.** The canonical digest is the JSON package's `package_sha256` field, not `sha256sum reference.json`. Commit the reviewed reference and execution settings; put the digest literally in a protected workflow or a separately governed configuration. A checksum in the same untrusted PR does not establish authenticity.

## Optional small pretrained model

To use a small downloadable pretrained checkpoint instead of the random fixture, download the pinned `sshleifer/tiny-gpt2` snapshot and omit `--tiny`. This acquisition step requires Hub network access; deployment checks use local files only. The tiny-pretrained download recipe is provided for reproduction and was not downloaded in this session. The cached 124M GPT-2 checkpoint was executed instead, with retained evidence below.

```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="sshleifer/tiny-gpt2",
    revision="5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be",
    local_dir="tiny-pretrained",
    allow_patterns=["*.json", "*.txt", "pytorch_model.bin"],
)
```

```bash
python examples/model_audit/create_reference.py --model ./tiny-pretrained --output ./reference
```

This example fixes context 64, float32 CPU and eager attention. For other models, construct a package using `singularity.model_audit.build_package` and the adapter settings appropriate to that model, then freeze and review its calibration observations and fault coverage. Do not assume this one-fault demonstration provides useful coverage of a production deployment.

## Adopt the action in another repository

Check out the exact Singularity integration commit into `.singularity`, or use the packaged action directly as shown. Replace `AUDITED_COMMIT_SHA` with the full commit containing this integration and `REVIEWED_PACKAGE_DIGEST` with the reviewed canonical package digest. Acquire the model at a pinned revision in a separate preceding step; the action's `model` input is a local directory. GitHub Actions checkout and upload versions below match the repository's existing workflow conventions; pin action dependencies to reviewed full commit SHAs in a production workflow.

```yaml
name: Model deployment contract
on: [push, pull_request]
permissions:
  contents: read
jobs:
  audit:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install frozen CPU runtime
        run: |
          python -m pip install 'torch==2.8.0+cpu' --index-url https://download.pytorch.org/whl/cpu
          python -m pip install 'transformers==4.57.1' 'tokenizers==0.22.2' 'safetensors==0.8.0'
      # Acquire or restore your pinned local model into ./deployment here.
      - uses: towre676-cloud/singularity/.github/actions/model-audit@AUDITED_COMMIT_SHA
        with:
          model: ./deployment
          reference-package: ./audit/reference.json
          expected-package-sha256: REVIEWED_PACKAGE_DIGEST
          execution-settings: ./audit/execution.json
          artifact-name: deployment-audit
```

A complete executable same-repository workflow, including reference creation, healthy execution, model-free replay and intentional weight replacement with required rejection, lives at [model-audit-example.yml](../../.github/workflows/model-audit-example.yml). Its separate artifacts are named `healthy-audit` and `intentional-fault-audit`. The action uses read-only repository permissions and does not send comments, update references or alter deployment files. Framework installation, Hub authentication and GPU provisioning remain explicit caller steps. The composite action targets Linux runners with Bash, Python and GitHub artifact service access; self-hosted GPUs may use their own compatible runtime. GitHub Enterprise Server compatibility with `upload-artifact@v4` is not claimed.

## Execution settings and verdicts

`execution.json` must specify exactly `max_context`, `truncate_to`, `pad_id`, `normalization`, `temperature`, `pass_attention_mask`, `position_correction`, `use_cache`, `dtype`, `device`, `batch_size` and `attention_backend`. The generated file is a working example. Contract settings and dtype must equal the frozen reference. Device and batch size are explicit runtime choices; attention backend is restricted to `eager` or `sdpa`. Backend, framework, device and precision changes need independent clean calibration before treating numerical differences as faults. The original package schema does not bind all runtime choices, so `execution.json` and runtime versions are retained alongside the contract. Pin and review that file too; no calibration is invented by this integration.

The checker recomputes local model-file identity (`snapshot_manifest_sha256`) and the tokenizer processing fingerprint. It also compares the adapter's model configuration, dtype and declared pipeline contract. It refuses packages lacking a snapshot content binding. Remote model code is disabled. The snapshot digest covers the existing local provenance helper's recognized model, configuration and tokenizer file suffixes; extra recognized files also affect identity. Preserve the exact snapshot layout and metadata across checks. A separate tokenizer directory is supported via the optional `tokenizer` input and is checked through its loaded processing fingerprint.

`pass` means the recorded probes match frozen observations within calibrated tolerances and the identity contract matches. `changed` means a probe or contract moved, including a planned weight update. `incomplete` means insufficient remaining evidence to retain the declared missing-result guarantee. `error` means verification, loading, malformed observations, non-finite values or another execution step failed. Only `pass` exits zero. An error must never be reported as an unchanged model. JSON contains exact probe deviations and contract differences; Markdown provides a concise verdict and interpretation.

The action expects every selected result. For explicit offline missing-result analysis the CLI also accepts `--missing ID ...`; the verdict remains passing only when fewer than `requirement` results are missing and every declared construction fault retains a separating observation. This is the original finite construction-table guarantee, not a probabilistic promise about all future faults. The tests cover one missing result, exhaustion of the guarantee, wrong observation counts and unknown missing ids. Actual runtime failures fail the action; they are not silently discarded as missing probes.

## What the certificate proves

The model-free checker recomputes the canonical package digest and separation flags from stored fault deviations and frozen tolerances, checks the robust witness and rejects inconsistent stored flags. It verifies finite declared coverage; it does not authenticate observation acquisition or independently rerun the expensive model construction experiment. Exact minimum-cost selection remains the existing builder's computation, with an independent exhaustive-subset oracle on the regression fixture. The portable coverage witness alone is not an optimality proof over an omitted full candidate pool. `replay` recomputes the deployment report from raw stored observations and deployed contract without importing torch or transformers. It detects report/evidence disagreement; coordinated replacement of all self-consistent observations still requires a trusted acquisition process to exclude. The artifact manifest hashes file bytes for transport integrity and is not a signed attestation.

A deployment flag is evidence of changed tested behavior, not a diagnosis of its cause or a judgment of overall model quality. Planned updates need their own reviewed reference and regression comparison. The pretrained study's held-out absolute-position miss and observationally invisible masking faults remain limitations. The supplied Qwen 1.5B/T4 run reports 261 exact and 261 optimally pruned greedy tokens, six of seven held-out faults detected, two control alarms, a zero-separator position fault excluded from declared construction coverage, and 2.18x resident full-pool/panel timing. Those are user-supplied measurements from the attached notebook output, not independently replayed certificates here; they do not support a universal exact-versus-pruned advantage or a universal false-alarm claim. In particular, non-finite eager-attention values and a cache-disabled control alarm require diagnosis or a narrower predeclared execution policy before using that run as a production gate.

## Actual measured costs and reproduction

The retained [tiny evidence](measured/tiny/report.json), [intentional weight-replacement rejection](measured/tiny-weight-fault/report.json) and [pretrained GPT-2 evidence](measured/gpt2/report.json) were obtained on the local Linux x86-64 CPU runtime, Python 3.12.14, torch 2.8.0+cpu and transformers 4.57.1, with `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`. Each is a single measured run, not a latency distribution or hosted-runner prediction. Dependency installation and model downloading are excluded.

The random tiny fixture selected 6 of 28 unpadded input tokens across two of three probes. Model loading plus reference construction took 0.0461 seconds after framework imports; the fresh-process CI check recorded 4.2830 seconds for verification/loading and 0.0131 seconds for selected observations, 4.2972 seconds total. Pretrained GPT-2 124M at acquisition revision `607a30d783dfa663caf39e06633721c8d4cfcd7e` selected 9 of 31 tokens. Its reference construction including model loading took 4.4479 seconds after framework imports, and the fresh check took 4.5850 seconds for verification/loading plus 0.8822 seconds for observations, 5.4677 seconds total. Model-file hashing is included in these check costs. Both selected panels tie ordinary greedy cost on this deliberately simple one-fault example; no exact-over-greedy speedup is claimed from these two examples. The earlier multi-fault studies establish their own workload-specific savings; CI reuses their selected panels without claiming cold loading is free.

Replay both retained healthy runs using only the standard-library package:

```bash
python -m singularity.model_audit.ci replay examples/model_audit/measured/tiny \
  --expected-package-sha256 416178bd786e127c7cf490593c42e2ee3dbf8a4deaf01709be7e92ff98f47ccc
python -m singularity.model_audit.ci replay examples/model_audit/measured/gpt2 \
  --expected-package-sha256 6703e61919c4241f3e42f8ee527f68b795116ece5b7279e5ad076416c018f0ce
python -m unittest discover -s tests -p 'test_model_audit*.py' -v
```

The small pretrained acquisition recipe follows the [pinned model snapshot](https://huggingface.co/sshleifer/tiny-gpt2/tree/5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be) and Hugging Face's [revision-specific download documentation](https://huggingface.co/docs/huggingface_hub/guides/download). Action packaging follows GitHub's [composite action documentation](https://docs.github.com/en/actions/tutorials/create-actions/create-a-composite-action).
