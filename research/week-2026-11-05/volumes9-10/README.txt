Singularity — complete ninth- and tenth-order height-series laws
4 November 2026

Start with Singularity_Volume9_10_Theorems_2026-11-04.html and
VOLUME9_10_THEOREMS.md. All polynomials count original labelled height
assignments; N_H means ordinary non-induced copies.

NEW RESULTS
Unrestricted cumulative ranks 24 -> 34 -> 48.
Ninth increments, unrestricted/connected/bridgeless/3-edge-connected:
10 / 10 / 9 / 8. Tenth increments: 14 / 12 / 12 / 10.
Exact invertible 10- and 14-coefficient readers; source-row witnesses;
unit-lattice realization through cutoff eleven; high-girth refinements;
pure Q0/Q1 twenty-vertex witnesses freshly checked.

FAST AUDIT (Python standard library only)
    python3 verify_saved.py
This independently checks saved coefficient-row combinations, inverses,
residual-elimination identities and the necessity witness core vectors.

FULL REGENERATION (Python 3.10+, pinned dependencies, C++ compiler)
    python3 -m pip install -r requirements.txt
    bash replay_full.sh
The script creates a fresh output directory and does not delete or
replace the packaged evidence. The complete run can take several minutes.
The supplied graph6 catalogues are inputs; see catalogue_provenance.json
for their verified construction. Nauty's original source archive is
included to regenerate subcubic9.g6 and subcubic10.g6 with geng -cq -D3.

CHECKED EVIDENCE
vol9_law.json, vol10_law.json: all exact coefficient rows and leaf normal forms.
vol9_reader.json, vol10_reader.json: coordinate definitions, exact inverses,
full polynomial functions and source-row witnesses.
vol9_witnesses.json, vol10_witnesses.json: triangular seed counts, admissible
isolators and equal-order graph recipes for the lower bounds.
vol9_host_checks.json, vol10_host_checks.json: every connected cubic host
through twelve vertices, direct heights versus independent motif counting.
automorphism_checks.json, automorphism10_checks.json: independent checks
on every new support's automorphism order.
high_girth_law.json, vol9_girth.json, vol10_girth.json: exact girth refinements.
pure20_verified.json: pending inherited Q0/Q1 direct replay closed.

BOUNDARIES
No proof-assistant formalization, minimum witness order, noise-optimal
ninth/tenth panel or volume-eleven coefficient table is claimed.
Large witness recipes are certified by exact seed arithmetic and a structural
reservoir proof. They were not allocated as large edge lists.
The canonical repository and remote were not changed.

PROVENANCE
Source baseline: towre676-cloud/singularity at
17f033ea9a1e6d93224e946a341f7a0e545ee64a.
vol8_lib.py, vol8_law.py, vol8_reduction.py, vol8_offdiagonal.py and
vol8_law.json are unmodified pinned source dependencies.
The fixed-excess kernel and its six-vertex certificate come from the
preceding checked research advance in this conversation.
New order-nine/ten masks are pynauty relabellings; lower masks retain the
source convention. Exact files and their hashes are in MANIFEST.json.
