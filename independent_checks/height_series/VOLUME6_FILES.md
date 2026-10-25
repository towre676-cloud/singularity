# Volume 6 file layout

The volume-6 package (REPORT: `VOLUME6_REPORT.md`, proof: `VOLUME6_PROOF.md`)
was produced in a working directory whose main results file,
`vol6_results.json` (27 MB pretty-printed), exceeds the per-push size
limit of the snapshot tooling used to commit this work. It is therefore
shipped here, losslessly, as compact-JSON parts:

- `vol6_results_part1_meta_graphs_small.json` — the `checks`, `pools`,
  `pairs`, and `runtime_seconds` sections, plus `graphs` for n=8, 10, 12.
- `vol6_results_part2_graphs_n14_<i>.json` — `graphs.n14`, chunked.
- `vol6_results_part3_graphs_n16_<i>.json` — `graphs.n16`, chunked.
- `vol6_results_part4_pair_rows_small.json` — `pair_rows` for n=8, 10, 12.
- `vol6_results_part5_pair_rows_n14_<i>.json` — `pair_rows.n14`, chunked.
- `vol6_results_part6_pair_rows_n16_<i>.json` — `pair_rows.n16`, chunked.

Reassembly is a plain merge: the top-level `graphs` / `pair_rows` values
are the union of the per-part dictionaries, and each chunk file holds a
single section of the form `{"graphs": {"n14_chunk": i, "rows": [...]}}`
whose `rows` list extends that pool's list in chunk order. The split was
verified lossless: reassembling the parts reproduces the original
`vol6_results.json` exactly (deep equality of the parsed JSON). `vol6_final_check.py` reads the reassembled
`vol6_results.json`; every other script is self-contained as shipped.

Two generator scripts (`vol6_gen2.py`, `vol6_gen3.py`) import
`random_cubic` from `singularity_extension.py`, which already lives in
this directory (added by PR #4); in the original working directory they
reached the same module through a workspace path, replaced here by the
in-repository import.
