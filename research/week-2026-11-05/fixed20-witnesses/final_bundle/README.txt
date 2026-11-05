Singularity connectivity and witness minima — November 4, 2026

Read RESULTS.md first. The graph-class measurement minima are 7 / 6 / 6 / 4
for unrestricted / connected / bridgeless / 3-edge-connected graphs.

Quick exact algebra replay (Python 3 standard library):
  cd replay
  python verify_advance.py

Independent selected-witness replay, including the new 18-vertex pair:
  python verify_advance.py --witnesses

Full exhaustive direct replay (C++17 compiler and Python; takes longer):
  bash replay_all.sh --full-search

The retained graph6 catalogues contain every connected cubic graph at the
listed orders. To regenerate them, unpack nauty_source.tar.gz into a new
directory, run ./configure and make geng, then run for each even n=4..18:
  ./geng -cq -d3 -D3 n > cubicN.g6
The exact source commit is 3915d891af81630853ab485f2696828a31253cd9.

Evidence status is explicit in RESULTS.md. Earlier full raw run files were
removed by workspace maintenance. observed_run_summary.json records results
actually observed before that event. fresh_algebra_certificate.json and
fresh_small_witnesses.json are newly regenerated checks, not reconstructed logs.
The direct search and summarizer regenerate the full missing pair tables.

The prior connected result is preserved unchanged in prior/.
proposed.patch is a review-only additive proposal. It has not been applied
to upstream. No remote commit, branch, PR, proof, or reader was modified.
