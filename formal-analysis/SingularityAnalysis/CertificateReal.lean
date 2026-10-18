import Mathlib.Tactic.NormNum
import SingularityAnalysis.RealRing
import SingularityAnalysis.LocalSeries

/-! Actual real coefficients and exponents, derived from the kernel certificates. -/

noncomputable section

namespace SingularityAnalysis

private theorem psum_eq_real_sum (q : ℝ) (E : List (ℕ × ℕ)) (l : List (List ℕ)) :
    Singularity.Vis.psum q E l =
      (l.map (fun a => q ^ (Singularity.energy E a).toNat)).sum := by
  induction l with
  | nil => rfl
  | cons a l ih => simp [Singularity.Vis.psum, ih]

theorem graphCoeff_eq_ell (E : List (ℕ × ℕ)) (n V : ℕ) (q : ℝ) :
    graphCoeff E n V q = Singularity.Vis.ell E n V q := by
  exact (psum_eq_real_sum q E (Singularity.comps n V)).symm

@[simp] theorem graphCoeff_zero (E : List (ℕ × ℕ)) (n : ℕ) (q : ℝ) :
    graphCoeff E n 0 q = 1 := by
  simp [graphCoeff]

theorem spectral_coeff_zero (q : ℝ) :
    graphCoeff Singularity.Cert.spectralG 7 0 q = 1 ∧
    graphCoeff Singularity.Cert.spectralCmpG 7 0 q = 1 := by
  simpa [graphCoeff_eq_ell] using Singularity.Vis.spectral_const q

theorem binary_coeff_zero (q : ℝ) :
    graphCoeff Singularity.Cert.binaryG 7 0 q = 1 ∧
    graphCoeff Singularity.Cert.binaryCmpG 7 0 q = 1 := by
  simpa [graphCoeff_eq_ell] using Singularity.Vis.binary_const q

theorem spectral_coeff_agree (q : ℝ) (V : ℕ) (hV : V < 2) :
    graphCoeff Singularity.Cert.spectralG 7 V q =
      graphCoeff Singularity.Cert.spectralCmpG 7 V q := by
  simpa [graphCoeff_eq_ell] using Singularity.Vis.spectral_agree q V hV

theorem binary_coeff_agree (q : ℝ) (V : ℕ) (hV : V < 3) :
    graphCoeff Singularity.Cert.binaryG 7 V q =
      graphCoeff Singularity.Cert.binaryCmpG 7 V q := by
  simpa [graphCoeff_eq_ell] using Singularity.Vis.binary_agree q V hV

theorem spectral_coeff_delta (q : ℝ) :
    graphCoeff Singularity.Cert.spectralG 7 2 q -
      graphCoeff Singularity.Cert.spectralCmpG 7 2 q =
      2 * q ^ 2 * (1 - q) ^ 2 * (1 - q ^ 2) := by
  have h := Singularity.Vis.spectral_delta q
  simpa [graphCoeff_eq_ell, Singularity.Cert.spectralDiffVolume,
    Singularity.Cert.spectralN, mul_assoc] using h

theorem binary_coeff_delta (q : ℝ) :
    graphCoeff Singularity.Cert.binaryG 7 3 q -
      graphCoeff Singularity.Cert.binaryCmpG 7 3 q =
      q ^ 3 * (1 - q) * (1 - q ^ 3) ^ 2 * (1 - q ^ 4) ^ 2 := by
  have h := Singularity.Vis.binary_delta q
  simpa [graphCoeff_eq_ell, Singularity.Cert.binaryDiffVolume,
    Singularity.Cert.binaryN, mul_assoc] using h

theorem spectral_exponent_half :
    graphCoeff Singularity.Cert.spectralG 7 2 (1 / 2 : ℝ) -
      graphCoeff Singularity.Cert.spectralCmpG 7 2 (1 / 2 : ℝ) = 3 / 32 := by
  rw [spectral_coeff_delta]
  norm_num

theorem binary_exponent_half :
    graphCoeff Singularity.Cert.binaryG 7 3 (1 / 2 : ℝ) -
      graphCoeff Singularity.Cert.binaryCmpG 7 3 (1 / 2 : ℝ) = 11025 / 262144 := by
  rw [binary_coeff_delta]
  norm_num

end SingularityAnalysis
