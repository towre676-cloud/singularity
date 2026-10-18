import Mathlib.Analysis.SpecificLimits.Normed
import Mathlib.Analysis.NormedSpace.FunctionSeries
import Mathlib.Analysis.Asymptotics.Asymptotics
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring
import Mathlib.Tactic.GCongr
import Mathlib.Tactic.Positivity
import Singularity.Visibility

/-! # Real local height series

This file supplies the real analytic bridge for graph coefficients: an
elementary polynomial coefficient bound, absolute convergence in the unit
disc, locally uniform convergence, positivity, and exact Taylor remainders.
All sums range over the same certified `comps` enumerator as P33.
-/

open scoped BigOperators Topology
open Filter Asymptotics

set_option maxHeartbeats 1000000

noncomputable section

namespace SingularityAnalysis

private theorem length_bind_le {α β : Type*} (l : List α) (f : α → List β)
    (M : ℕ) (h : ∀ a ∈ l, (f a).length ≤ M) :
    (l.bind f).length ≤ l.length * M := by
  induction l with
  | nil => simp
  | cons a l ih =>
    simp only [List.bind_cons, List.length_append, List.length_cons]
    have ha := h a (by simp)
    have hl := ih (fun b hb => h b (by simp [hb]))
    calc
      _ ≤ M + l.length * M := Nat.add_le_add ha hl
      _ = (l.length + 1) * M := by ring

/-- The certified weak-composition list has at most the containing box size. -/
theorem comps_length_le : ∀ n V : ℕ,
    (Singularity.comps n V).length ≤ (V + 1) ^ n
  | 0, 0 => by decide
  | 0, V + 1 => by simp [Singularity.comps]
  | n + 1, V => by
    rw [Singularity.comps]
    calc
      _ ≤ (List.range (V + 1)).length * (V + 1) ^ n := by
        apply length_bind_le
        intro a _ha
        simp only [List.length_map]
        exact (comps_length_le n (V - a)).trans
          (Nat.pow_le_pow_left (by omega) n)
      _ = (V + 1) ^ (n + 1) := by simp [pow_succ, Nat.mul_comm]

/-- Actual finite local coefficient of an edge-list graph, evaluated in ℝ. -/
def graphCoeff (E : List (ℕ × ℕ)) (n V : ℕ) (q : ℝ) : ℝ :=
  ((Singularity.comps n V).map
    (fun a => q ^ (Singularity.energy E a).toNat)).sum

private theorem list_weight_bounds (l : List (List ℕ)) (E : List (ℕ × ℕ))
    (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    0 ≤ (l.map (fun a => q ^ (Singularity.energy E a).toNat)).sum ∧
    (l.map (fun a => q ^ (Singularity.energy E a).toNat)).sum ≤ l.length := by
  induction l with
  | nil => simp
  | cons a l ih =>
    simp only [List.map_cons, List.sum_cons, List.length_cons, Nat.cast_add, Nat.cast_one]
    have hpow0 : 0 ≤ q ^ (Singularity.energy E a).toNat := pow_nonneg hq0 _
    have hpow1 : q ^ (Singularity.energy E a).toNat ≤ 1 := pow_le_one _ hq0 hq1
    constructor <;> linarith [ih.1, ih.2]

/-- Every graph coefficient is nonnegative and has polynomial growth in volume. -/
theorem graphCoeff_bounds (E : List (ℕ × ℕ)) (n V : ℕ) (q : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    0 ≤ graphCoeff E n V q ∧ graphCoeff E n V q ≤ (V + 1 : ℝ) ^ n := by
  have h := list_weight_bounds (Singularity.comps n V) E q hq0 hq1
  constructor
  · exact h.1
  · exact h.2.trans (by exact_mod_cast comps_length_le n V)

theorem graphCoeff_norm_le (E : List (ℕ × ℕ)) (n V : ℕ) (q : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    ‖graphCoeff E n V q‖ ≤ (V + 1 : ℝ) ^ n := by
  rw [Real.norm_eq_abs, abs_of_nonneg (graphCoeff_bounds E n V q hq0 hq1).1]
  exact (graphCoeff_bounds E n V q hq0 hq1).2

/-- A useful shifted polynomial/geometric majorant. -/
theorem summable_polynomial_geometric (n k : ℕ) {ρ : ℝ}
    (hρ0 : 0 ≤ ρ) (hρ1 : ρ < 1) :
    Summable (fun V : ℕ => (V + k + 1 : ℝ) ^ n * ρ ^ V) := by
  have hbase := summable_pow_mul_geometric_of_norm_lt_one n
    (show ‖ρ‖ < 1 by simpa [Real.norm_eq_abs, abs_of_nonneg hρ0] using hρ1)
  have hmajor := hbase.mul_left ((k + 2 : ℝ) ^ n)
  apply hmajor.of_norm_bounded_eventually_nat
  filter_upwards [eventually_ge_atTop (1 : ℕ)] with V hV
  rw [Real.norm_eq_abs, abs_of_nonneg (mul_nonneg (pow_nonneg (by positivity) _) (pow_nonneg hρ0 _))]
  have hv : (1 : ℝ) ≤ V := by exact_mod_cast hV
  have hb : (V + k + 1 : ℝ) ≤ (k + 2 : ℝ) * V := by nlinarith
  calc
    _ ≤ ((k + 2 : ℝ) * V) ^ n * ρ ^ V := by gcongr
    _ = (k + 2 : ℝ) ^ n * ((V : ℝ) ^ n * ρ ^ V) := by rw [mul_pow]; ring

/-- Evaluation of the local series as an actual real infinite sum. -/
def localSeries (c : ℕ → ℝ) (x : ℝ) : ℝ := ∑' V : ℕ, c V * x ^ V

/-- Absolute convergence throughout the open unit interval, for polynomially
bounded coefficients. -/
theorem localSeries_summable {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n) {x : ℝ} (hx : |x| < 1) :
    Summable (fun V : ℕ => c V * x ^ V) := by
  apply (summable_polynomial_geometric n 0 (abs_nonneg x) hx).of_norm_bounded
  intro V
  simp only [norm_mul, norm_pow, Real.norm_eq_abs]
  simpa using mul_le_mul_of_nonneg_right (hc V) (pow_nonneg (abs_nonneg x) V)

theorem graphSeries_summable (E : List (ℕ × ℕ)) (n : ℕ) (q : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) {x : ℝ} (hx : |x| < 1) :
    Summable (fun V : ℕ => graphCoeff E n V q * x ^ V) := by
  apply localSeries_summable (n := n) _ hx
  intro V
  rw [Real.norm_eq_abs, abs_of_nonneg (graphCoeff_bounds E n V q hq0 hq1).1]
  exact (graphCoeff_bounds E n V q hq0 hq1).2

/-- Uniform convergence gives continuity on every compact subinterval of the
unit interval. -/
theorem localSeries_continuousOn_closed {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n) {ρ : ℝ}
    (hρ0 : 0 ≤ ρ) (hρ1 : ρ < 1) :
    ContinuousOn (localSeries c) (Set.Icc (-ρ) ρ) := by
  change ContinuousOn (fun x : ℝ => ∑' V : ℕ, c V * x ^ V) (Set.Icc (-ρ) ρ)
  apply continuousOn_tsum (f := fun V x => c V * x ^ V) (u := fun V : ℕ => (V + 1 : ℝ) ^ n * ρ ^ V)
  · intro V
    exact (continuous_const.mul (continuous_id.pow V)).continuousOn
  · simpa using summable_polynomial_geometric n 0 hρ0 hρ1
  · intro V x hx
    rw [norm_mul, norm_pow, Real.norm_eq_abs]
    apply mul_le_mul (hc V) (pow_le_pow_left (abs_nonneg x) ((abs_le).mpr hx) V)
      (pow_nonneg (abs_nonneg x) V) (by positivity)

theorem localSeries_continuousAt {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n) {x : ℝ} (hx : |x| < 1) :
    ContinuousAt (localSeries c) x := by
  let ρ := (|x| + 1) / 2
  have hxρ : |x| < ρ := by dsimp [ρ]; linarith
  have hρ0 : 0 ≤ ρ := by dsimp [ρ]; positivity
  have hρ1 : ρ < 1 := by dsimp [ρ]; linarith
  apply (localSeries_continuousOn_closed hc hρ0 hρ1).continuousAt
  exact Icc_mem_nhds (by linarith [(neg_le_abs x)]) (by linarith [(le_abs_self x)])

/-- Nonnegative coefficients and unit constant term imply strict positivity
on the entire nonnegative convergence interval. -/
theorem localSeries_one_le {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hc0 : c 0 = 1) (hcpos : ∀ V, 0 ≤ c V)
    {x : ℝ} (hx0 : 0 ≤ x) (hx1 : x < 1) :
    1 ≤ localSeries c x := by
  have hs := localSeries_summable hc (x := x) (by simpa [abs_of_nonneg hx0] using hx1)
  have h := le_tsum hs 0 (fun V _ => mul_nonneg (hcpos V) (pow_nonneg hx0 V))
  simpa [localSeries, hc0] using h

/-- The power series obtained after deleting its first `k` coefficients. -/
def localTail (c : ℕ → ℝ) (k : ℕ) (x : ℝ) : ℝ :=
  ∑' V : ℕ, c (V + k) * x ^ V

theorem localTail_summable {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n) (k : ℕ)
    {x : ℝ} (hx : |x| < 1) :
    Summable (fun V : ℕ => c (V + k) * x ^ V) := by
  apply (summable_polynomial_geometric n k (abs_nonneg x) hx).of_norm_bounded
  intro V
  rw [norm_mul, norm_pow, Real.norm_eq_abs]
  exact mul_le_mul_of_nonneg_right (by simpa [Nat.cast_add] using hc (V + k))
    (pow_nonneg (abs_nonneg x) V)

/-- A single finite constant bounds the normalized Taylor tail on a compact
subinterval. This is an explicit real estimate, not a formal-series premise. -/
theorem localTail_norm_le {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n) (k : ℕ)
    {ρ : ℝ} (hρ0 : 0 ≤ ρ) (hρ1 : ρ < 1) {x : ℝ} (hx : |x| ≤ ρ) :
    ‖localTail c k x‖ ≤ ∑' V : ℕ, (V + k + 1 : ℝ) ^ n * ρ ^ V := by
  apply tsum_of_norm_bounded (summable_polynomial_geometric n k hρ0 hρ1).hasSum
  intro V
  rw [norm_mul, norm_pow, Real.norm_eq_abs]
  apply mul_le_mul (by simpa [Nat.cast_add] using hc (V + k))
    (pow_le_pow_left (abs_nonneg x) hx V)
    (pow_nonneg (abs_nonneg x) V) (by positivity)

/-- The analytic infinite sum has exactly the certified finite Taylor prefix. -/
theorem localSeries_remainder_eq {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n) (k : ℕ)
    {x : ℝ} (hx : |x| < 1) :
    localSeries c x - ∑ V ∈ Finset.range k, c V * x ^ V =
      x ^ k * localTail c k x := by
  have hs := sum_add_tsum_nat_add k (localSeries_summable hc hx)
  have ht : (∑' V : ℕ, c (V + k) * x ^ (V + k)) = x ^ k * localTail c k x := by
    rw [localTail, ← tsum_mul_left]
    congr 1
    funext V
    rw [pow_add]
    ring
  rw [ht] at hs
  unfold localSeries
  linarith

/-- Taylor's remainder bound at zero, justified by actual convergence. -/
theorem localSeries_remainder_isBigO {c : ℕ → ℝ} {n : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n) (k : ℕ) :
    (fun x : ℝ => localSeries c x - ∑ V ∈ Finset.range k, c V * x ^ V)
      =O[𝓝 (0 : ℝ)] (fun x => x ^ k) := by
  let M := ∑' V : ℕ, (V + k + 1 : ℝ) ^ n * (1 / 2 : ℝ) ^ V
  apply isBigO_iff.mpr
  refine ⟨M, ?_⟩
  filter_upwards [Metric.ball_mem_nhds (0 : ℝ) (by norm_num : (0 : ℝ) < 1 / 2)] with x hx
  have hxabs : |x| ≤ (1 / 2 : ℝ) := by
    exact le_of_lt (by simpa [Metric.mem_ball, Real.dist_eq] using hx)
  rw [localSeries_remainder_eq hc k (lt_of_le_of_lt hxabs (by norm_num)), norm_mul]
  calc
    _ ≤ ‖x ^ k‖ * M := mul_le_mul_of_nonneg_left
      (localTail_norm_le hc k (by norm_num) (by norm_num) hxabs) (norm_nonneg _)
    _ = M * ‖x ^ k‖ := mul_comm _ _

@[simp] theorem localSeries_zero (c : ℕ → ℝ) : localSeries c 0 = c 0 := by
  classical
  unfold localSeries
  rw [tsum_eq_single 0]
  · simp
  · intro V hV
    simp [hV]

/-- Certified agreement of coefficient prefixes becomes the corresponding
first-order analytic difference. -/
theorem localSeries_first_difference_isBigO {c d : ℕ → ℝ} {n r : ℕ}
    (hc : ∀ V, ‖c V‖ ≤ (V + 1 : ℝ) ^ n)
    (hd : ∀ V, ‖d V‖ ≤ (V + 1 : ℝ) ^ n)
    (hagree : ∀ V < r, c V = d V) :
    (fun x : ℝ => localSeries c x - localSeries d x - (c r - d r) * x ^ r)
      =O[𝓝 (0 : ℝ)] (fun x => x ^ (r + 1)) := by
  have h := (localSeries_remainder_isBigO hc (r + 1)).sub
    (localSeries_remainder_isBigO hd (r + 1))
  apply h.congr_left
  intro x
  have hp : (∑ V ∈ Finset.range r, c V * x ^ V) =
      ∑ V ∈ Finset.range r, d V * x ^ V := by
    apply Finset.sum_congr rfl
    intro V hV
    rw [hagree V (Finset.mem_range.mp hV)]
  rw [Finset.sum_range_succ, Finset.sum_range_succ, hp]
  ring

end SingularityAnalysis
