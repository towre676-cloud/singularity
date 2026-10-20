# MIMII: a complete eight-microphone design audit

This application extends Singularity's existing physical-sensor replay programme to the original MIMII public 1.0 corpus. Its concrete methodological advantage is complete, independently checkable knowledge of all 255 nonempty microphone panels under the frozen numerical model: minimum channel count, every tied optimum, failures within noise and class cells, and the cost or infeasibility of surviving channel erasures. This certificate concerns a finite selection table. The separately protected machine recordings determine whether a selected reduction transfers.

**Protected finding.** The exact nominal optimum is microphones 3 and 6: 193/384 correct (50.26%) on the protected machines, versus 203/384 (52.86%) for the full array. Its 2.60-point loss exceeds the declared two-point pooled margin and its per-type contract fails. Greedy and optimally pruned greedy choose microphones 1 and 7 at the same minimum cost and score 213/384 (55.47%); mic 1 alone, fixed in advance, scores 219/384 (57.03%). The predeclared greedy/pruned pair meets the nominal protected per-type contract using two of eight prerecorded streams (75% fewer model inputs), but fails the noise-aware and class-aware contracts. This is a bounded retrospective positive result. No exact-versus-pruned-greedy cost advantage is demonstrated. The weak absolute scores and failed per-class 50% floor prevent interpreting relative preservation as reliable diagnosis.

**The useful advantage is a complete robustness audit.** Across all 255 panels, adding nominal-noise constraints raises the exact development requirement from two microphones to all eight; adding class constraints retains all eight. No panel satisfies one- or two-channel erasure safety, even when the sensitivity margin reaches ten points. All 255 selection prediction traces are distinct, so no finite trace alias is observed. All twelve empirical normal/abnormal descriptor-box distinctions lack a coordinate separation certificate. These are complete finite-table and sufficient-envelope findings, not physical impossibility theorems.

The illustrated [research report](MIMII_Array_Research.html), [compact PDF](../../../output/pdf/mimii_array_research.pdf) and [mathematical chapter](../../../docs/chapters/17_mimii_array.md) give the findings and their boundaries. `results.json` contains complete protected outcomes; `selection_snapshot.json` contains the choices made before those outcomes. The original MAFAULDA experiments are preserved byte for byte.

## Data and frozen design

The source is Purohit and colleagues at Hitachi, Ltd., [MIMII Dataset public 1.0](https://zenodo.org/records/3384388), DOI 10.5281/zenodo.3384388, under CC BY-SA 4.0. Original WAVs contain eight synchronized microphone channels, 160,000 samples per channel, 16 kHz and 16-bit PCM. All four machine types are included: fan, pump, slider and valve. The original paper describes factory-noise mixing and the original per-machine normal-only anomaly benchmark: <https://arxiv.org/html/1909.09347v1>. This study instead asks a supervised cross-machine binary diagnosis question; it is not a replication of that benchmark or a state-of-the-art classifier comparison.

The deterministic case-control subset comprises sixteen normal and sixteen abnormal stems per machine ID, four IDs per type, and all three nominal archive SNR versions (-6, 0, +6 dB): 512 stems and 1,536 WAVs. The common-name intersection across all three archives is SHA-256 ranked before signals are acquired. IDs 00 and 02 train, ID 04 selects and ID 06 confirms, independently within each type. A single global physical channel mask is selected, while classifier references and normalization are trained separately by machine type. All related SNR versions of a stem stay together. The paper sets noise using model-average signal power, so these archive labels are not per-recording measured SNR guarantees. Hidden factory-noise segment identities are unavailable, so independence of those nuisance sessions is not established.

The [protocol](protocol.json) was published before signal acquisition at [commit 30132a5](https://github.com/towre676-cloud/singularity/commit/30132a5f7e332c832dc7ad471937a97b3483aa6f). `freeze_receipt.json` binds its exact bytes. `selection_lock.json` binds the feature, numerical-model source, prediction and choice bytes before confirmation. A frozen two-percentage-point margin is applied with exact rational arithmetic after floating-point predictions. Contracts progressively add per-type balanced accuracy, per-type/SNR balanced accuracy and per-class recall, followed by one- and two-channel erasure requirements. Every allowed survivor is checked against intact full-array thresholds. Nonmonotone fusion is never treated as set coverage.

Whole archives total 100,243,834,344 bytes in the official record; the selected signal members total exactly 2,852,963,714 compressed bytes and 3,932,282,880 raw WAV bytes. `official_record.json`, `central_indexes.json.gz` (lossless; its hash binds the decompressed original JSON bytes), `source_subset_manifest.json` and `source_receipts.json` retain exact original archive sizes, paths, ZIP64 offsets, CRC32, SHA-256 and request evidence. Whole-archive publisher MD5 values are metadata, not verified full-download checksums. Raw recordings are reacquired to ignored `../mimii_data` and are not redistributed in this package.

## Reproduction

From the repository root, use Python 3.12 or newer for raw WAV acquisition and feature replay (the original files use extensible PCM headers). The core retains its Python 3.10+ contract. Use the optional physical-application dependencies in `applications/sensor_replay/requirements.txt`. Evidence-only verification needs NumPy; raw feature verification additionally uses its FFT implementation. The offline checker independently reconstructs every prediction using flattened masked vectors, every rational constraint, the exact optima, forward greedy and optimally pruned greedy comparisons, erasure survivors and sensitivity tables without importing the study implementation.

```sh
python applications/sensor_replay/mimii_v1/verify_study.py
python applications/sensor_replay/verify_all.py
```

To reacquire the precise official members and independently recompute all descriptors, use the retained plan. HTTP Range responses are validated before consumption; ignored or shifted ranges fail rather than downloading a whole archive. ZIP64 support is required because archive offsets exceed four gigabytes. Acquisition may take tens of minutes, and about seven gigabytes of temporary disk space are needed when both compressed and raw caches are retained.

```sh
python applications/sensor_replay/mimii_v1/acquire.py --help
python applications/sensor_replay/mimii_v1/acquire.py --manifest applications/sensor_replay/mimii_v1/source_receipts.json --reacquire --workers 8
python applications/sensor_replay/mimii_v1/verify_raw_features.py
python applications/sensor_replay/mimii_v1/verify_study.py --raw
```

A new raw-to-results study requires a fresh output directory containing the frozen protocol and acquisition evidence. `run_study.py --root NEW_DIRECTORY --extract`, then `--select`, then `--confirm` are separate phases. Existing selected evidence is sealed and existing confirmation results cannot be overwritten. Do not use confirmation outcomes to revise the original choice. The explicit FFT checker is independent of the primary SciPy Welch extractor and reports numerical agreement at a declared tolerance, not proof-assistant verification.

## Interpretation

Exact, ordinary forward greedy under the declared deficit rule, and optimally pruned greedy are compared under identical contracts and cost proxies. Mic 1 is the representative singleton fixed in advance; all eight singleton controls are retained. Margins of 0, 2, 5 and 10 points, channel erasures, class-specific failures and complete prediction-trace equivalence are descriptive sensitivities, with no confirmation-driven winner substituted for the frozen primary panels. With only sixteen examples per class/noise cell, one error changes recall by 6.25 points, so the two-point cell margin permits no additional error.

The paired bootstrap resamples whole stems with every SNR version together, stratified by type and class. It is conditional on four fixed confirmation machines and does not estimate generalization across the population of machines. Relative preservation of a poor full-array classifier does not establish good diagnosis; the report separately tests an absolute 50% per-class recall floor. Equal finite prediction traces do not prove acoustic equality or universal physical indistinguishability.

`observability.py` directly reuses `singularity.robust_coverage` for empirical min/max class boxes. Strictly disjoint descriptor intervals provide a sufficient per-channel distinction; the existing branch-and-bound and independent exhaustive core oracle check requirements one, two and three. This is a conditional envelope diagnostic, separate from additive nearest-reference fusion. Overlap is a failed sufficient certificate, not an impossibility theorem about the physical machine.

No result establishes new sensor placement, beamforming, acquisition speed, power consumption, hardware cost or field performance. The retained sample counts measure prerecorded stream volume only. See [DATA_LICENSE.md](DATA_LICENSE.md) for source attribution and derived-data licensing.
