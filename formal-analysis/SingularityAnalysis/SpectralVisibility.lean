import SingularityAnalysis.CertificateReal
import SingularityAnalysis.CoefficientVisibility
import SingularityAnalysis.EulerRatio

/-! # The actual graph visibility theorems

The hypotheses are the graph coefficient bounds, the certified finite prefix,
and the numerical range of q. No analytic premise packet occurs at the end of
this chain. The continued ratio agrees with the quotient of the original
Euler products on their common convergence half-line s > 1.
-/

open Filter Set
open scoped Topology

noncomputable section

namespace SingularityAnalysis

/-- A complete real visibility statement including identification with the
original two Euler products where both converge separately. -/
def GraphVisibility (c d : ℕ → ℝ) (r : ℕ) (δ s0 : ℝ) : Prop :=
  ∃ R K : ℝ → ℝ,
    (∀ s, 1 < (r : ℝ) * s →
      HasProd (fun p : ℕ => if p.Prime then
        localRatio c d ((p : ℝ) ^ (-s)) else 1) (R s)) ∧
    (∀ s, 1 < ((r : ℝ) + 1) * s →
      HasProd (fun p : ℕ => if p.Prime then
        (1 - (p : ℝ) ^ (-((r : ℝ) * s))) ^ δ *
          localRatio c d ((p : ℝ) ^ (-s)) else 1) (K s)) ∧
    (∀ s, 1 < (r : ℝ) * s →
      R s = Singularity.RealVisibility.zeta ((r : ℝ) * s) ^ δ * K s) ∧
    0 < K s0 ∧
    Tendsto (fun s => ((r : ℝ) * s - 1) ^ δ * R s)
      (𝓝[>] s0) (𝓝 (K s0)) ∧
    (∀ s, 1 < s → R s = localEulerProduct c s / localEulerProduct d s)

/-- Finite certified coefficient agreement suffices for the actual analytic
comparison of any two graph local series with q in [0,1]. -/
theorem graph_visibility (G H : List (ℕ × ℕ)) (n r : ℕ) (q s0 : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hr : 1 ≤ r)
    (hagree : ∀ V < r, graphCoeff G n V q = graphCoeff H n V q)
    (hs0 : (r : ℝ) * s0 = 1) :
    GraphVisibility (fun V => graphCoeff G n V q) (fun V => graphCoeff H n V q)
      r (graphCoeff G n r q - graphCoeff H n r q) s0 := by
  let c := fun V => graphCoeff G n V q
  let d := fun V => graphCoeff H n V q
  have hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n :=
    fun V => graphCoeff_norm_le G n V q hq0 hq1
  have hd : ∀ V, ‖d V‖ ≤ (V + 1 : ℝ) ^ n :=
    fun V => graphCoeff_norm_le H n V q hq0 hq1
  have hc0 : c 0 = 1 := graphCoeff_zero G n q
  have hd0 : d 0 = 1 := graphCoeff_zero H n q
  have hcpos : ∀ V, 0 ≤ c V := fun V => (graphCoeff_bounds G n V q hq0 hq1).1
  have hdpos : ∀ V, 0 ≤ d V := fun V => (graphCoeff_bounds H n V q hq0 hq1).1
  obtain ⟨R, K, hR, hK, hfac, hpos, hlim⟩ :=
    visibility_of_coefficients c d n r s0 hc hd hc0 hd0 hcpos hdpos hr hagree hs0
  refine ⟨R, K, hR, hK, hfac, hpos, hlim, ?_⟩
  intro s hs
  have hrreal : (1 : ℝ) ≤ r := by exact_mod_cast hr
  have hsr : 1 < (r : ℝ) * s :=
    lt_of_lt_of_le hs (le_mul_of_one_le_left (by linarith : 0 ≤ s) hrreal)
  exact ratio_eq_localEulerProduct_quotient hc hd hc0 hd0 hcpos hdpos hs
    (by simpa only [localRatio] using hR s hsr)

open Singularity.Cert

theorem spectral_visibility (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    GraphVisibility (fun V => graphCoeff spectralG 7 V q)
      (fun V => graphCoeff spectralCmpG 7 V q) 2
      (2 * q ^ 2 * (1 - q) ^ 2 * (1 - q ^ 2)) (1 / 2) := by
  have h := graph_visibility spectralG spectralCmpG 7 2 q (1 / 2)
    hq0 hq1 (by decide) (spectral_coeff_agree q) (by norm_num)
  simpa only [spectral_coeff_delta] using h

theorem binary_visibility (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    GraphVisibility (fun V => graphCoeff binaryG 7 V q)
      (fun V => graphCoeff binaryCmpG 7 V q) 3
      (q ^ 3 * (1 - q) * (1 - q ^ 3) ^ 2 * (1 - q ^ 4) ^ 2) (1 / 3) := by
  have h := graph_visibility binaryG binaryCmpG 7 3 q (1 / 3)
    hq0 hq1 (by decide) (binary_coeff_agree q) (by norm_num)
  simpa only [binary_coeff_delta] using h

/-- The spectral pair's actual real exponent is 3/32 at q=1/2. -/
theorem spectral_visibility_half :
    GraphVisibility (fun V => graphCoeff spectralG 7 V (1 / 2))
      (fun V => graphCoeff spectralCmpG 7 V (1 / 2)) 2 (3 / 32) (1 / 2) := by
  have h := graph_visibility spectralG spectralCmpG 7 2 (1 / 2) (1 / 2)
    (by norm_num) (by norm_num) (by decide)
    (spectral_coeff_agree (1 / 2)) (by norm_num)
  simpa only [spectral_exponent_half] using h

/-- The binary-census pair's actual real exponent is 11025/262144 at q=1/2. -/
theorem binary_visibility_half :
    GraphVisibility (fun V => graphCoeff binaryG 7 V (1 / 2))
      (fun V => graphCoeff binaryCmpG 7 V (1 / 2)) 3 (11025 / 262144) (1 / 3) := by
  have h := graph_visibility binaryG binaryCmpG 7 3 (1 / 2) (1 / 3)
    (by norm_num) (by norm_num) (by decide)
    (binary_coeff_agree (1 / 2)) (by norm_num)
  simpa only [binary_exponent_half] using h

end SingularityAnalysis
