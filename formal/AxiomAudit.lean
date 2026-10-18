/- Prints the axioms each main theorem depends on.  Run: `lake env lean AxiomAudit.lean`. -/
import Singularity
open Singularity
#print axioms shift_injective
#print axioms shift_surjective
#print axioms shift_unique
#print axioms vol_shift
#print axioms energy_shift
#print axioms energy_norm
#print axioms mem_allFilter
#print axioms allCount_rec
#print axioms allCount_eq_mzCount_of_lt
#print axioms allCount_eq_shiftSum
#print axioms thr_nested
#print axioms reconstruct
#print axioms vol_eq_levels
#print axioms nonemptyLevels_eq_lmax
#print axioms span_eq
#print axioms thr_proper_of_minZero
#print axioms edge_square
#print axioms delta_mul
#print axioms edge_nested
#print axioms energy_nested
#print axioms energy_binary
#print axioms binary_dichotomy
