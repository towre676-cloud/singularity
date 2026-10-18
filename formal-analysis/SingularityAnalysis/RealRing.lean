import Mathlib.Data.Real.Basic
import Singularity.Visibility

/-! The core certificate ring, interpreted by the actual real numbers. -/

noncomputable section

namespace SingularityAnalysis

instance realVRing : Singularity.Vis.VRing ℝ where
  toAdd := inferInstance
  toMul := inferInstance
  toNeg := inferInstance
  zero := 0
  one := 1
  add_assoc := _root_.add_assoc
  add_comm := _root_.add_comm
  zero_add := _root_.zero_add
  neg_add := _root_.neg_add_cancel
  mul_assoc := _root_.mul_assoc
  mul_comm := _root_.mul_comm
  one_mul := _root_.one_mul
  mul_add := _root_.mul_add

@[simp] theorem real_vzero : (Singularity.Vis.VRing.zero : ℝ) = 0 := rfl
@[simp] theorem real_vone : (Singularity.Vis.VRing.one : ℝ) = 1 := rfl

@[simp] theorem real_ncast (n : ℕ) : (Singularity.Vis.ncast n : ℝ) = n := by
  induction n with
  | zero => simp [Singularity.Vis.ncast]
  | succ n ih => simp [Singularity.Vis.ncast, ih, Nat.cast_add, Nat.cast_one]

@[simp] theorem real_icast (n : ℤ) : (Singularity.Vis.icast n : ℝ) = n := by
  cases n with
  | ofNat n => simp [Singularity.Vis.icast]
  | negSucc n => simp [Singularity.Vis.icast, Int.negSucc_coe]

@[simp] theorem real_npow (x : ℝ) (n : ℕ) : Singularity.Vis.npow x n = x ^ n := by
  induction n with
  | zero => rfl
  | succ n ih => simp [Singularity.Vis.npow, ih, pow_succ]

@[simp] theorem comps_zero (n : ℕ) :
    Singularity.comps n 0 = [List.replicate n 0] := by
  induction n with
  | zero => rfl
  | succ n ih =>
    simp [Singularity.comps, ih, List.replicate_succ,
      show List.range 1 = [0] by decide]

@[simp] theorem energy_zero_profile (E : List (ℕ × ℕ)) (n : ℕ) :
    Singularity.energy E (List.replicate n 0) = 0 := by
  induction E with
  | nil => rfl
  | cons e E ih =>
    by_cases hu : e.1 < n <;> by_cases hv : e.2 < n <;>
      simpa [Singularity.energy, Singularity.esum, Singularity.edgeVal,
        List.getElem?_replicate, hu, hv, Singularity.sqd] using ih

end SingularityAnalysis
