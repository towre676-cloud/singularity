# Singularity fixed-order and pure-unit witness advance

Read **open_work/ADVANCE.md** for the new theorem, exact minima and remaining bounds.
The preceding connectivity-minima result is preserved in final_bundle/.

New verified results:

* The smallest common order for a six-direction connected/bridgeless basis is 20.
  The explicit six-vector matrix has determinant 1.
* Pure unit minima for Q0, Q1 and Theta223 are 18; for S8_10 the minimum is 20.
  All attaining pure witnesses are 3-edge-connected.
* The complete catalogue of 510,489 connected cubic graphs of order20 contains
  no pure closed_diamond or S8_11 unit witness. Both remaining minima are at least22.
* Explicit verified upper bounds remain 13,184 and25,932, respectively.

Replay from the archive root (Python3 standard library and a C++17 compiler):

    python open_work/verify_fixed20.py
    python open_work/verify_pure_witnesses.py
    python open_work/unit_tables.py
    g++ -O3 -std=c++17 open_work/unit_catalogue.cpp -o open_work/unit_catalogue
    open_work/unit_catalogue open_work/complete20.g6 open_work/weights.txt open_work/orbits.txt open_work/replayed20.json
    python open_work/unit_upper_bounds.py

The twenty-vertex catalogue is sorted; its manifest records the disjoint
nauty generator residues and hashes. Regenerate with the source pinned in
final_bundle/nauty_source.tar.gz, using r=0..7:

    geng -cq -d3 -D3 20 r/8

Concatenate those eight outputs and sort -u. The resulting unique count is510,489.
Earlier catalogues, recovered full lower-order reference tables, discovery pools,
exact masks/weights, direct height receipts and all complete witness edge lists
are included. No new evidence from this pass is declared lost.

The unit-count fields count representative pairs of distinct eighth-polynomial
points within a common lower-agreement fiber, not graph-multiplicity totals.
The source-law catalogue path and independent direct-height witness path are
separate. Twenty-two- and twenty-four-vertex family searches are partial; their
negative results are not nonexistence proofs at those orders.

proposed_fixed20.patch is review-only and has not been applied to the repository.
It proposes a report and compact exact certificates. The full standalone replay
and large catalogues are retained here. No remote repository changes were made.
