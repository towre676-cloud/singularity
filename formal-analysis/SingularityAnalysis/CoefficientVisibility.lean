import SingularityAnalysis.LocalSeries
import SingularityAnalysis.LogExpansion
import SingularityAnalysis.PrimeProduct
import SingularityAnalysis.VisibilityReal

/-! # From certified coefficients to actual real visibility

Polynomial growth, positivity, and a finite coefficient agreement certificate
suffice for convergent prime products, exact zeta factorization, and the
positive boundary asymptotic. No analytic premise packet is assumed.
-/

open Filter Set Topology Asymptotics

noncomputable section

namespace SingularityAnalysis

set_option maxHeartbeats 1000000

/-- The actual quotient of two convergent local coefficient series. -/
def localRatio (c d : ℕ → ℝ) (x : ℝ) : ℝ :=
  localSeries c x / localSeries d x

/-- Convergent raw and regularized prime products, zeta factorization, and the
positive right-hand boundary limit. All operations are those of actual ℝ. -/
def VisibilityConclusion (Q : ℝ → ℝ) (r : ℕ) (δ s0 : ℝ) : Prop :=
  ∃ R K : ℝ → ℝ,
    (∀ s, 1 < (r : ℝ) * s →
      HasProd (fun p : ℕ => if p.Prime then Q ((p : ℝ) ^ (-s)) else 1) (R s)) ∧
    (∀ s, 1 < ((r : ℝ) + 1) * s →
      HasProd (fun p : ℕ => if p.Prime then
        (1 - (p : ℝ) ^ (-((r : ℝ) * s))) ^ δ * Q ((p : ℝ) ^ (-s)) else 1)
        (K s)) ∧
    (∀ s, 1 < (r : ℝ) * s →
      R s = Singularity.RealVisibility.zeta ((r : ℝ) * s) ^ δ * K s) ∧
    0 < K s0 ∧
    Tendsto (fun s => ((r : ℝ) * s - 1) ^ δ * R s)
      (𝓝[>] s0) (𝓝 (K s0))

/-- A finite first-discrepancy certificate yields faithful real analytic
visibility for every pair of nonnegative, polynomially bounded unit series. -/
theorem visibility_of_coefficients (c d : ℕ → ℝ) (n r : ℕ) (s0 : ℝ)
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hd : ∀ V, ‖d V‖ ≤ (V + 1 : ℝ) ^ n)
    (hc0 : c 0 = 1) (hd0 : d 0 = 1)
    (hcpos : ∀ V, 0 ≤ c V) (hdpos : ∀ V, 0 ≤ d V)
    (hr : 1 ≤ r) (hagree : ∀ V < r, c V = d V)
    (hs0 : (r : ℝ) * s0 = 1) :
    VisibilityConclusion (localRatio c d) r (c r - d r) s0 := by
  have hApos : ∀ x ∈ Ioo (0 : ℝ) 1, 0 < localSeries c x := by
    intro x hx
    exact lt_of_lt_of_le zero_lt_one
      (localSeries_one_le hc hc0 hcpos hx.1.le hx.2)
  have hBpos : ∀ x ∈ Ioo (0 : ℝ) 1, 0 < localSeries d x := by
    intro x hx
    exact lt_of_lt_of_le zero_lt_one
      (localSeries_one_le hd hd0 hdpos hx.1.le hx.2)
  have hAon : ContinuousOn (localSeries c) (Ioo (0 : ℝ) 1) := by
    intro x hx
    exact (localSeries_continuousAt hc (by simpa [abs_of_pos hx.1] using hx.2)).continuousWithinAt
  have hBon : ContinuousOn (localSeries d) (Ioo (0 : ℝ) 1) := by
    intro x hx
    exact (localSeries_continuousAt hd (by simpa [abs_of_pos hx.1] using hx.2)).continuousWithinAt
  have hQon : ContinuousOn (localRatio c d) (Ioo (0 : ℝ) 1) :=
    hAon.div hBon (fun x hx => (hBpos x hx).ne')
  have hQpos : ∀ x ∈ Ioo (0 : ℝ) 1, 0 < localRatio c d x := by
    intro x hx
    exact div_pos (hApos x hx) (hBpos x hx)
  have hAc : ContinuousAt (localSeries c) 0 := localSeries_continuousAt hc (by norm_num)
  have hBc : ContinuousAt (localSeries d) 0 := localSeries_continuousAt hd (by norm_num)
  have hAne := hAc.eventually_ne (show localSeries c 0 ≠ 0 by simp [hc0])
  have hBne := hBc.eventually_ne (show localSeries d 0 ≠ 0 by simp [hd0])
  have hlog : (fun x => Real.log (localRatio c d x))
      =O[𝓝 (0 : ℝ)] (fun x => x ^ r) := by
    apply (localSeries_log_difference_isBigO hc hd hc0 hd0 hr hagree).congr'
    · filter_upwards [hAne, hBne] with x hxA hxB
      dsimp [localRatio]
      rw [Real.log_div hxA hxB]
    · exact Filter.Eventually.of_forall (fun _ => rfl)
  have hreg : (Singularity.RealVisibility.regularizedLog (localRatio c d) r (c r - d r))
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
    apply (localSeries_regularized_log_isBigO hc hd hc0 hd0 hr hagree).congr'
    · filter_upwards [hAne, hBne] with x hxA hxB
      dsimp [Singularity.RealVisibility.regularizedLog, localRatio]
      rw [Real.log_div hxA hxB]
      ring
    · exact Filter.Eventually.of_forall (fun _ => rfl)
  exact Singularity.RealVisibility.visibility_of_log_bounds
    (localRatio c d) r (c r - d r) s0 hr hs0 hQon hQpos
    (LogPowerBound.of_isBigO_nat hlog)
    (by simpa only [Nat.cast_add, Nat.cast_one] using LogPowerBound.of_isBigO_nat hreg)

end SingularityAnalysis
