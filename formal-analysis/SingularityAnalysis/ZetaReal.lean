import Mathlib.NumberTheory.EulerProduct.DirichletLSeries
import Mathlib.Analysis.SpecialFunctions.Pow.Continuity

open Filter Set Topology
noncomputable section
namespace Singularity
namespace RealVisibility

def zeta (s : ℝ) : ℝ := (riemannZeta (s : ℂ)).re

theorem ofReal_zeta {s : ℝ} (hs : 1 < s) :
    ((zeta s : ℝ) : ℂ) = riemannZeta (s : ℂ) := by
  have hz := zeta_eq_tsum_one_div_nat_cpow (s := (s : ℂ)) (by simpa using hs)
  have ht : riemannZeta (s : ℂ) =
      ((∑' n : ℕ, (n : ℝ) ^ (-s) : ℝ) : ℂ) := by
    rw [hz, Complex.ofReal_tsum]
    congr 1
    ext n
    rw [Complex.ofReal_cpow (Nat.cast_nonneg n), Complex.ofReal_neg,
      Complex.cpow_neg, one_div]
    simp only [Complex.ofReal_natCast]
  rw [zeta, ht]
  simp

theorem zeta_euler_product {s : ℝ} (hs : 1 < s) :
    HasProd (fun p : Nat.Primes => (1 - (p : ℝ) ^ (-s))⁻¹) (zeta s) := by
  apply (Complex.isometry_ofReal.uniformInducing.inducing.hasProd_iff
    (g := Complex.ofReal)
    (fun p : Nat.Primes => (1 - (p : ℝ) ^ (-s))⁻¹) (zeta s)).mp
  have h := riemannZeta_eulerProduct_hasProd (s := (s : ℂ)) (by simpa using hs)
  rw [← ofReal_zeta hs] at h
  convert h using 1
  ext p
  simp only [Function.comp_apply, Complex.ofReal_eq_coe, Complex.ofReal_inv, Complex.ofReal_sub,
    Complex.ofReal_one, Complex.ofReal_cpow (Nat.cast_nonneg p.val), Complex.ofReal_neg]
  rfl

theorem zeta_residue_one :
    Tendsto (fun s : ℝ => (s - 1) * zeta s) (𝓝[>] (1 : ℝ)) (𝓝 1) := by
  have hcoe : Tendsto (fun s : ℝ => (s : ℂ)) (𝓝[>] (1 : ℝ)) (𝓝[≠] (1 : ℂ)) := by
    apply tendsto_nhdsWithin_iff.mpr
    constructor
    · exact Complex.continuous_ofReal.continuousAt.tendsto.mono_left nhdsWithin_le_nhds
    · filter_upwards [self_mem_nhdsWithin] with s hs
      simpa only [mem_compl_iff, mem_singleton_iff, Complex.ofReal_eq_one] using ne_of_gt hs
  have h := Complex.continuous_re.continuousAt.tendsto.comp
    (riemannZeta_residue_one.comp hcoe)
  simpa [Function.comp_def, zeta, Complex.mul_re] using h

end RealVisibility
end Singularity
