# Fourth-jet supplement to What Must Survive II, Revision 4

Read QUARTIC_THEOREMS.md first. This is a supplement, not a replacement for the original monograph.

Closed here: complete finite fourth-jet formula; uniform pole ceiling 15; conditional leading amplitude 2 B(-1); exact rational volume-14 pole profile.

Still open: existence of a nonzero-amplitude lift for every later volume, next promotion, all-volume window law, completeness, physical annular minimality.

Dependencies: Python 3.10+, SymPy 1.14.0, python-flint 0.9.0. The finite-formula numerical verifier uses only the standard library.

Run in this directory:

    python prepare_testdata.py
    python verify_quartic.py
    python symbolic_edge.py
    python carry_bounds.py
    python local_pole_bounds.py
    python certify_profile.py

Saved JSON receipts accompany each successful run. certify_profile.py uses the three-prime exact rational input rows, not rational reconstruction from a single prime. The source engine was not regenerated in this run.

quartic_exact.py is a readable finite subset/Ursell formula evaluator; it is not an optimized large-census engine. The exact coefficient cross-check is at q=3/2 and is not represented as a polynomial identity proof. The formula and the uniform arguments are proved in the accompanying note, with finite rational-function degree checks used explicitly in the pole-bound proof.
