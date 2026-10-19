# Frontier companion: Claude entry point

This branch adds companion research beside NX36. Start with
[the scope and implications](../../docs/research/FRONTIER_COMPANION.md), then
the five FR proof documents in `docs/research/`. Do not treat this supplement
as completion of an NX acceptance unit.

The source baseline is published commit
`438ed423d7d389a1a483c61e0b50eca6a9fc0827`. The NX36 handoff was prepared in
a separate checkout. Its packets, proposed modules and acceptance ledger are
not modified here. If you begin from that handoff, merge these additive files
and the small README pointer; do not replace your working tree with an older
source snapshot.

## Reproduce

```sh
PYTHONPATH=src python scripts/frontier_companion.py --check
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/check_repository.py
python scripts/check_links.py
```

The first command independently regenerates each retained FR receipt and
compares it with the committed JSON. The unit suite also checks public API
validation and independent small-instance oracles. Proofs are in the manuscript;
passing replay does not convert an ordinary proof into a kernel-checked one.

## Files and ownership

| Unit | New module | Detailed proof | Retained evidence |
|---|---|---|---|
| FR01 | `src/singularity/pole_divisors.py` | `docs/research/FR01_POLE_DIVISORS.md` | `results/fr01_pole_divisors.json` |
| FR02 | `src/singularity/denominator_recovery.py` | `docs/research/FR02_DENOMINATOR_RECOVERY.md` | `results/fr02_denominator_recovery.json` |
| FR03 | `src/singularity/tree_positivity.py` | `docs/research/FR03_TREE_POSITIVITY.md` | `results/fr03_tree_positivity.json` |
| FR04 | `src/singularity/pinned_theta.py` | `docs/research/FR04_PINNED_THETA.md` | `results/fr04_pinned_theta.json` |
| FR05 | `src/singularity/threshold_reconstruction.py` | `docs/research/FR05_THRESHOLD_RECONSTRUCTION.md` | `results/fr05_threshold_reconstruction.json` |

## Carry these limitations forward

FR01's pole theorem is for the unpinned local series. Arbitrary mixed-size
disconnected components need the declared noncancellation condition. FR02
uses exact rational arithmetic and a known order; decoding is cheap compared
with potentially expensive coefficient generation. FR03 concerns ordered tree
kernels and compatible height boxes, not arbitrary symmetric interfaces or
volume truncations. FR04 supplies necessary limiting invariants, not an
equivalence theorem for the full pinned sequence.

The three main research frontiers remain open. Finite agreement, equal theta
limits, a matching maximum degree, or a positive finite collection of minors
does not settle full-series equality or graph realization in general. FR05
does reconstruct graphs within the promised threshold class from a sufficient
logarithmic prefix. It does not establish that arbitrary input graphs belong
to that class.
