import SingularityAnalysis.LocalSeries
import Mathlib.Analysis.SpecialFunctions.Log.Deriv

/-! # Analytic logarithm cancellation

The coefficient certificate is transported to a real logarithmic remainder.
The only inputs are the coefficient bounds and equal finite prefixes; the
quadratic logarithm estimate is proved in Mathlib for the actual real log.
-/

open scoped BigOperators Topology
open Filter Asymptotics

namespace SingularityAnalysis

set_option maxHeartbeats 1000000

noncomputable section

theorem power_isBigO_of_le {m k : ℕ} (hmk : m ≤ k) :
    (fun x : ℝ => x ^ k) =O[𝓝 (0 : ℝ)] (fun x => x ^ m) := by
  apply IsBigO.of_bound 1
  filter_upwards [Metric.ball_mem_nhds (0 : ℝ) (by norm_num : (0 : ℝ) < 1)] with x hx
  have hxabs : |x| ≤ 1 := by
    exact le_of_lt (by simpa [Metric.mem_ball, Real.dist_eq] using hx)
  simpa [norm_pow, Real.norm_eq_abs] using
    pow_le_pow_of_le_one (abs_nonneg x) hxabs hmk

theorem log_one_add_sub_isBigO :
    (fun u : ℝ => Real.log (1 + u) - u) =O[𝓝 (0 : ℝ)] (fun u => u ^ 2) := by
  apply IsBigO.of_bound 2
  filter_upwards [Metric.ball_mem_nhds (0 : ℝ) (by norm_num : (0 : ℝ) < 1 / 2)] with u hu
  have huabs : |u| ≤ (1 / 2 : ℝ) := by
    exact le_of_lt (by simpa [Metric.mem_ball, Real.dist_eq] using hu)
  have h := Real.abs_log_sub_add_sum_range_le
    (x := -u) (by simpa using lt_of_le_of_lt huabs (by norm_num : (1 / 2 : ℝ) < 1)) 1
  have hden : 0 < 1 - |u| := by linarith
  have hb : |u| ^ 2 / (1 - |u|) ≤ 2 * |u| ^ 2 := by
    apply (div_le_iff₀ hden).mpr
    nlinarith
  have h' : |Real.log (1 + u) - u| ≤ |u| ^ 2 / (1 - |u|) := by
    simpa [Finset.sum_range_succ, sub_eq_add_neg, add_comm, add_left_comm, add_assoc] using h
  simpa [norm_pow, Real.norm_eq_abs] using h'.trans hb

theorem log_one_sub_add_isBigO :
    (fun u : ℝ => Real.log (1 - u) + u) =O[𝓝 (0 : ℝ)] (fun u => u ^ 2) := by
  have h := log_one_add_sub_isBigO.comp_tendsto
    (show Tendsto (fun u : ℝ => -u) (𝓝 0) (𝓝 0) by
      simpa using (show ContinuousAt (fun u : ℝ => -u) 0 from continuousAt_id.neg).tendsto)
  simpa [Function.comp_def, sub_eq_add_neg] using h

/-- Generic real logarithmic cancellation at a known first coefficient.
No convergence or analytic conclusion is assumed: `A`, `B` are continuous,
their stated first-difference and unit-constant estimates are sufficient. -/
theorem regularized_log_isBigO {A B : ℝ → ℝ} {r : ℕ} {δ : ℝ}
    (hr : 1 ≤ r) (hA : ContinuousAt A 0) (hB : ContinuousAt B 0)
    (hA0 : A 0 = 1) (hB0 : B 0 = 1)
    (hBfirst : (fun x => B x - 1) =O[𝓝 (0 : ℝ)] (fun x => x))
    (hfirst : (fun x => A x - B x - δ * x ^ r)
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1))) :
    (fun x => Real.log (A x) - Real.log (B x) + δ * Real.log (1 - x ^ r))
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
  let D : ℝ → ℝ := fun x => (A x - B x) * (B x)⁻¹
  have hBne0 : B 0 ≠ 0 := by rw [hB0]; norm_num
  have hAne0 : A 0 ≠ 0 := by rw [hA0]; norm_num
  have hBne := hB.eventually_ne hBne0
  have hAne := hA.eventually_ne hAne0
  have hInv : (fun x => (B x)⁻¹) =O[𝓝 (0 : ℝ)] (fun _ => (1 : ℝ)) :=
    (hB.inv₀ hBne0).tendsto.isBigO_one ℝ
  have hcross : (fun x => δ * x ^ r * (B x - 1))
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
    have h := ((isBigO_refl (fun x : ℝ => x ^ r) (𝓝 0)).const_mul_left δ).mul hBfirst
    simpa [pow_succ] using h
  have hDfirst : (fun x => D x - δ * x ^ r)
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
    have h := (hfirst.sub hcross).mul hInv
    simp only [mul_one] at h
    apply h.congr'
    · filter_upwards [hBne] with x hx
      dsimp [D]
      field_simp
      ring
    · exact Filter.Eventually.of_forall (fun _ => rfl)
  have hD : D =O[𝓝 (0 : ℝ)] (fun x => x ^ r) := by
    have h := (hDfirst.trans (power_isBigO_of_le (by omega : r ≤ r + 1))).add
      ((isBigO_refl (fun x : ℝ => x ^ r) (𝓝 0)).const_mul_left δ)
    simpa only [sub_add_cancel] using h
  have hDzero : Tendsto D (𝓝 0) (𝓝 0) := by
    have hDc := (hA.sub hB).mul (hB.inv₀ hBne0)
    simpa [D, hA0, hB0] using hDc.tendsto
  have hquad : (fun x => D x ^ 2) =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
    have h := hD.pow 2
    have heq : (fun x : ℝ => (x ^ r) ^ 2) = (fun x => x ^ (r * 2)) := by
      funext x; rw [pow_mul]
    rw [heq] at h
    exact h.trans (power_isBigO_of_le (by omega : r + 1 ≤ r * 2))
  have hlogD : (fun x => Real.log (1 + D x) - D x)
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) :=
    (log_one_add_sub_isBigO.comp_tendsto hDzero).trans hquad
  have hpowzero : Tendsto (fun x : ℝ => x ^ r) (𝓝 0) (𝓝 0) := by
    have hp : ContinuousAt (fun x : ℝ => x ^ r) 0 := (continuous_id.pow r).continuousAt
    simpa [zero_pow (by omega : r ≠ 0)] using hp.tendsto
  have hlogPow : (fun x : ℝ => Real.log (1 - x ^ r) + x ^ r)
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
    have h := log_one_sub_add_isBigO.comp_tendsto hpowzero
    have hp : (fun x : ℝ => (x ^ r) ^ 2) =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
      simpa [← pow_mul] using power_isBigO_of_le (by omega : r + 1 ≤ r * 2)
    exact h.trans hp
  have hsum := (hlogD.add hDfirst).add (hlogPow.const_mul_left δ)
  apply hsum.congr'
  · filter_upwards [hBne, hAne] with x hBx hAx
    have hratio : 1 + D x = A x / B x := by
      dsimp [D]
      field_simp
    rw [hratio, Real.log_div hAx hBx]
    ring
  · exact Filter.Eventually.of_forall (fun _ => rfl)

/-- The coefficient certificate plus polynomial coefficient bounds imply
the exact logarithmic remainder required by the prime-product proof. -/
theorem localSeries_regularized_log_isBigO {c d : ℕ → ℝ} {n r : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hd : ∀ V, ‖d V‖ ≤ (V + 1 : ℝ) ^ n)
    (hc0 : c 0 = 1) (hd0 : d 0 = 1) (hr : 1 ≤ r)
    (hagree : ∀ V < r, c V = d V) :
    (fun x => Real.log (localSeries c x) - Real.log (localSeries d x) +
      (c r - d r) * Real.log (1 - x ^ r))
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
  apply regularized_log_isBigO hr
    (localSeries_continuousAt hc (by norm_num))
    (localSeries_continuousAt hd (by norm_num))
    (by simpa using hc0) (by simpa using hd0)
  · simpa [Finset.sum_range_succ, hd0] using localSeries_remainder_isBigO hd 1
  · exact localSeries_first_difference_isBigO hc hd hagree

/-- The unregularized logarithmic ratio begins at the certified degree. -/
theorem localSeries_log_difference_isBigO {c d : ℕ → ℝ} {n r : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hd : ∀ V, ‖d V‖ ≤ (V + 1 : ℝ) ^ n)
    (hc0 : c 0 = 1) (hd0 : d 0 = 1) (hr : 1 ≤ r)
    (hagree : ∀ V < r, c V = d V) :
    (fun x => Real.log (localSeries c x) - Real.log (localSeries d x))
      =O[𝓝 (0 : ℝ)] (fun x => x ^ r) := by
  have hreg := (localSeries_regularized_log_isBigO hc hd hc0 hd0 hr hagree).trans
    (power_isBigO_of_le (by omega : r ≤ r + 1))
  have hpzero : Tendsto (fun x : ℝ => x ^ r) (𝓝 0) (𝓝 0) := by
    have hp : ContinuousAt (fun x : ℝ => x ^ r) 0 := (continuous_id.pow r).continuousAt
    simpa [zero_pow (by omega : r ≠ 0)] using hp.tendsto
  have hquad := (log_one_sub_add_isBigO.comp_tendsto hpzero).trans
    (show (fun x : ℝ => (x ^ r) ^ 2) =O[𝓝 (0 : ℝ)] (fun x => x ^ r) from
      by simpa [← pow_mul] using power_isBigO_of_le (by omega : r ≤ r * 2))
  have hlog : (fun x : ℝ => Real.log (1 - x ^ r))
      =O[𝓝 (0 : ℝ)] (fun x => x ^ r) := by
    have h := hquad.sub (isBigO_refl (fun x : ℝ => x ^ r) (𝓝 0))
    simpa only [Function.comp_apply, add_sub_cancel_right] using h
  have h := hreg.sub (hlog.const_mul_left (c r - d r))
  simpa only [add_sub_cancel_right] using h

end

end SingularityAnalysis
