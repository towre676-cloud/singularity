import SingularityAnalysis.LocalSeries
import SingularityAnalysis.LogExpansion
import SingularityAnalysis.PrimeProduct
import SingularityAnalysis.VisibilityReal

/-!
# The continued ratio agrees with the original Euler-product quotient

Individual local series with nonnegative polynomially bounded coefficients
and constant coefficient one define actual positive convergent Euler products
for `s > 1`.  Their quotient has the local ratio as its Euler factors.  Thus
any product-defined continuation of that ratio agrees with the quotient of
the two original products on their common initial half-line.
-/

open Filter Set
open scoped Topology BigOperators

noncomputable section

namespace SingularityAnalysis

def unitCoeff (V : ℕ) : ℝ := if V = 0 then 1 else 0

@[simp] theorem unitCoeff_zero : unitCoeff 0 = 1 := by simp [unitCoeff]

@[simp] theorem localSeries_unitCoeff (x : ℝ) : localSeries unitCoeff x = 1 := by
  classical
  unfold localSeries
  rw [tsum_eq_single 0]
  · simp [unitCoeff]
  · intro V hV
    simp [unitCoeff, hV]

theorem unitCoeff_norm_le (n V : ℕ) : ‖unitCoeff V‖ ≤ (V + 1 : ℝ) ^ n := by
  by_cases hV : V = 0
  · simp [hV]
  · simp only [unitCoeff, if_neg hV, norm_zero]
    positivity

/-- A unit-constant polynomially bounded local series has a first-order
logarithmic bound at zero. -/
theorem localSeries_log_powerBound {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n) (hc0 : c 0 = 1) :
    LogPowerBound (fun x => Real.log (localSeries c x)) 1 := by
  have h := localSeries_log_difference_isBigO hc (unitCoeff_norm_le n)
    hc0 unitCoeff_zero (r := 1) (by decide) (by
      intro V hV
      have hV0 : V = 0 := by omega
      simpa [hV0] using hc0)
  have hb := LogPowerBound.of_isBigO_nat (m := 1)
    (g := fun x => Real.log (localSeries c x)) (by simpa using h)
  simpa using hb

/-- The original Euler product associated with an individual local series. -/
def localEulerProduct (c : ℕ → ℝ) (s : ℝ) : ℝ :=
  primeProduct (fun x => Real.log (localSeries c x)) s

theorem localEulerProduct_pos (c : ℕ → ℝ) (s : ℝ) : 0 < localEulerProduct c s :=
  primeProduct_pos _ _

theorem hasProd_localEulerProduct {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hc0 : c 0 = 1) (hcpos : ∀ V, 0 ≤ c V) {s : ℝ} (hs : 1 < s) :
    HasProd (fun p : ℕ => if p.Prime then localSeries c ((p : ℝ) ^ (-s)) else 1)
      (localEulerProduct c s) := by
  apply hasProd_positive_factors (m := 1) _ (by norm_num) (by simpa using hs)
    (localSeries_log_powerBound hc hc0)
  intro x hx
  exact lt_of_lt_of_le zero_lt_one (localSeries_one_le hc hc0 hcpos hx.1.le hx.2)

theorem continuousAt_localEulerProduct {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hc0 : c 0 = 1) (hcpos : ∀ V, 0 ≤ c V) {s : ℝ} (hs : 1 < s) :
    ContinuousAt (localEulerProduct c) s := by
  apply continuousAt_primeProduct (m := 1) _ (by norm_num) (by simpa using hs)
    (localSeries_log_powerBound hc hc0)
  intro x hx
  have hxabs : |x| < 1 := by simpa [abs_of_pos hx.1] using hx.2
  exact (localSeries_continuousAt hc hxabs).continuousWithinAt.log
    (ne_of_gt (lt_of_lt_of_le zero_lt_one
      (localSeries_one_le hc hc0 hcpos hx.1.le hx.2)))

/-- Division of convergent real products, using division of their finite
partial-product limits.  No nonexistent `CommGroup ℝ` instance is needed. -/
theorem hasProd_div_real {ι : Type*} {f g : ι → ℝ} {a b : ℝ}
    (hf : HasProd f a) (hg : HasProd g b) (hb : b ≠ 0) :
    HasProd (fun i => f i / g i) (a / b) := by
  change Tendsto (fun S : Finset ι => ∏ i ∈ S, f i / g i) atTop (𝓝 (a / b))
  simpa only [Finset.prod_div_distrib] using (Filter.Tendsto.div hf hg hb)

/-- The quotient of the original Euler products has precisely the ratio
of the original local factors. -/
theorem hasProd_localEulerProduct_ratio {c d : ℕ → ℝ} {n m : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hd : ∀ V, ‖d V‖ ≤ (V + 1 : ℝ) ^ m)
    (hc0 : c 0 = 1) (hd0 : d 0 = 1)
    (hcpos : ∀ V, 0 ≤ c V) (hdpos : ∀ V, 0 ≤ d V)
    {s : ℝ} (hs : 1 < s) :
    HasProd (fun p : ℕ => if p.Prime then
      localSeries c ((p : ℝ) ^ (-s)) / localSeries d ((p : ℝ) ^ (-s)) else 1)
      (localEulerProduct c s / localEulerProduct d s) := by
  have h := hasProd_div_real
    (hasProd_localEulerProduct hc hc0 hcpos hs)
    (hasProd_localEulerProduct hd hd0 hdpos hs)
    (ne_of_gt (localEulerProduct_pos d s))
  apply h.congr_fun
  intro p
  by_cases hp : p.Prime <;> simp [hp]

/-- Uniqueness identifies a product-defined continued ratio with the quotient
of its two independently constructed original products on `s > 1`. -/
theorem ratio_eq_localEulerProduct_quotient {c d : ℕ → ℝ} {n m : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hd : ∀ V, ‖d V‖ ≤ (V + 1 : ℝ) ^ m)
    (hc0 : c 0 = 1) (hd0 : d 0 = 1)
    (hcpos : ∀ V, 0 ≤ c V) (hdpos : ∀ V, 0 ≤ d V)
    {s R : ℝ} (hs : 1 < s)
    (hR : HasProd (fun p : ℕ => if p.Prime then
      localSeries c ((p : ℝ) ^ (-s)) / localSeries d ((p : ℝ) ^ (-s)) else 1) R) :
    R = localEulerProduct c s / localEulerProduct d s :=
  hR.unique (hasProd_localEulerProduct_ratio hc hd hc0 hd0 hcpos hdpos hs)

end SingularityAnalysis
