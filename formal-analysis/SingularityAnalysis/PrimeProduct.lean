import Mathlib.Analysis.PSeries
import Mathlib.Analysis.NormedSpace.FunctionSeries
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Asymptotics

/-!
# Positive prime products from a local logarithmic bound

All objects in this file are the actual real numbers, topology, infinite sums,
and infinite products from Mathlib.  A prime product is represented on `ℕ`
with factor `1` at nonprimes.  Its logarithm is represented with term `0` at
nonprimes.  The assumptions are local data about an individual factor;
summability, positivity and continuity of the resulting product are proved.
-/

open Filter Set
open Asymptotics
open scoped Topology

namespace SingularityAnalysis

noncomputable section

def primeTerm (g : ℝ → ℝ) (n : ℕ) (s : ℝ) : ℝ :=
  if n.Prime then g ((n : ℝ) ^ (-s)) else 0

def primeSum (g : ℝ → ℝ) (s : ℝ) : ℝ := ∑' n : ℕ, primeTerm g n s

def primeProduct (g : ℝ → ℝ) (s : ℝ) : ℝ := Real.exp (primeSum g s)

theorem primeTerm_add (g h : ℝ → ℝ) (n : ℕ) (s : ℝ) :
    primeTerm (fun x => g x + h x) n s = primeTerm g n s + primeTerm h n s := by
  unfold primeTerm
  split_ifs <;> simp

theorem primeTerm_const_mul (c : ℝ) (g : ℝ → ℝ) (n : ℕ) (s : ℝ) :
    primeTerm (fun x => c * g x) n s = c * primeTerm g n s := by
  unfold primeTerm
  split_ifs <;> simp

theorem primeSum_add {g h : ℝ → ℝ} {s : ℝ}
    (hg : Summable (fun n => primeTerm g n s))
    (hh : Summable (fun n => primeTerm h n s)) :
    primeSum (fun x => g x + h x) s = primeSum g s + primeSum h s := by
  unfold primeSum
  simp_rw [primeTerm_add]
  exact tsum_add hg hh

theorem primeSum_const_mul (c : ℝ) (g : ℝ → ℝ) (s : ℝ) :
    primeSum (fun x => c * g x) s = c * primeSum g s := by
  unfold primeSum
  simp_rw [primeTerm_const_mul]
  exact tsum_mul_left

theorem primeProduct_add {g h : ℝ → ℝ} {s : ℝ}
    (hg : Summable (fun n => primeTerm g n s))
    (hh : Summable (fun n => primeTerm h n s)) :
    primeProduct (fun x => g x + h x) s = primeProduct g s * primeProduct h s := by
  unfold primeProduct
  rw [primeSum_add hg hh, Real.exp_add]

/-- A local bound at zero on a logarithmic factor.  The exponent is real,
so the lemma also applies when it is not an integer. -/
def LogPowerBound (g : ℝ → ℝ) (m : ℝ) : Prop :=
  ∃ C ε : ℝ, 0 ≤ C ∧ 0 < ε ∧
    ∀ x : ℝ, 0 < x → x < ε → ‖g x‖ ≤ C * x ^ m

/-- An ordinary Mathlib big-O estimate at zero supplies the quantitative
local estimate used by the prime-product criterion. -/
theorem LogPowerBound.of_isBigO_nat {g : ℝ → ℝ} {m : ℕ}
    (h : g =O[𝓝 (0 : ℝ)] (fun x : ℝ => x ^ m)) :
    LogPowerBound g (m : ℝ) := by
  obtain ⟨C, hC, hbound⟩ := Asymptotics.isBigO_iff'.1 h
  obtain ⟨ε, hε, hb⟩ := Metric.eventually_nhds_iff.1 hbound
  refine ⟨C, ε, hC.le, hε, ?_⟩
  intro x hx hxε
  have hd : dist x 0 < ε := by simpa [Real.dist_eq, abs_of_pos hx] using hxε
  simpa [Real.rpow_natCast, norm_pow, Real.norm_eq_abs, abs_of_pos hx] using hb hd

/-- An elementary logarithmic estimate, proved without a logarithmic Taylor
series.  This converts a bound on a factor minus one into a log bound. -/
theorem abs_log_le_two_mul_abs_sub_one {y : ℝ} (hy : |y - 1| ≤ 1 / 2) :
    |Real.log y| ≤ 2 * |y - 1| := by
  have hlo : -(1 / 2 : ℝ) ≤ y - 1 := (abs_le.1 hy).1
  have hy0 : 0 < y := by linarith
  have hupper := Real.log_le_sub_one_of_pos hy0
  have hlower := Real.log_le_sub_one_of_pos (inv_pos.2 hy0)
  rw [Real.log_inv] at hlower
  have hinv : y⁻¹ - 1 ≤ 2 * |y - 1| := by
    have heq : y⁻¹ - 1 = (1 - y) / y := by field_simp
    rw [heq, div_le_iff₀ hy0]
    have habs := neg_abs_le (y - 1)
    have hmul := mul_nonneg (abs_nonneg (y - 1))
      (show 0 ≤ 2 * y - 1 by linarith)
    nlinarith
  apply abs_le.2
  constructor
  · linarith
  · have := le_abs_self (y - 1)
    have := abs_nonneg (y - 1)
    linarith

/-- Transfer a local power estimate on `f - 1` to its logarithm. -/
theorem LogPowerBound.log_of_small {f : ℝ → ℝ} {m : ℝ}
    (hbound : LogPowerBound (fun x => f x - 1) m)
    (hsmall : ∃ ε : ℝ, 0 < ε ∧ ∀ x : ℝ, 0 < x → x < ε → |f x - 1| ≤ 1 / 2) :
    LogPowerBound (fun x => Real.log (f x)) m := by
  obtain ⟨C, ε, hC, hε, hb⟩ := hbound
  obtain ⟨δ, hδ, hd⟩ := hsmall
  refine ⟨2 * C, min ε δ, mul_nonneg (by norm_num) hC, lt_min hε hδ, ?_⟩
  intro x hx hxsmall
  calc
    ‖Real.log (f x)‖ = |Real.log (f x)| := Real.norm_eq_abs _
    _ ≤ 2 * |f x - 1| := abs_log_le_two_mul_abs_sub_one (hd x hx (lt_of_lt_of_le hxsmall (min_le_right _ _)))
    _ ≤ 2 * (C * x ^ m) := by
      apply mul_le_mul_of_nonneg_left _ (by norm_num)
      simpa only [Real.norm_eq_abs] using hb x hx (lt_of_lt_of_le hxsmall (min_le_left _ _))
    _ = (2 * C) * x ^ m := by ring

/-- The elementary Euler-zeta logarithmic factor has a linear local bound. -/
theorem logPowerBound_zeta : LogPowerBound (fun x => -Real.log (1 - x)) 1 := by
  refine ⟨2, 1 / 2, by norm_num, by norm_num, ?_⟩
  intro x hx hhalf
  have hnear : |(1 - x) - 1| ≤ 1 / 2 := by
    simpa [sub_sub_cancel_left, abs_of_pos hx, abs_neg] using hhalf.le
  have h := abs_log_le_two_mul_abs_sub_one hnear
  simpa [Real.norm_eq_abs, abs_neg, Real.rpow_one, sub_sub_cancel_left, abs_of_pos hx] using h

private theorem primeTerm_continuousOn {g : ℝ → ℝ}
    (hg : ContinuousOn g (Ioo 0 1)) {a : ℝ} (ha : 0 < a) (n : ℕ) :
    ContinuousOn (primeTerm g n) (Ici a) := by
  unfold primeTerm
  split_ifs with hn
  · have hn1 : (1 : ℝ) < n := by exact_mod_cast hn.one_lt
    have hn0 : (0 : ℝ) < n := lt_trans zero_lt_one hn1
    have hc : Continuous (fun s : ℝ => (n : ℝ) ^ (-s)) :=
      continuous_const.rpow continuous_neg (fun _ => Or.inl (ne_of_gt hn0))
    exact hg.comp hc.continuousOn (fun s hs =>
      ⟨Real.rpow_pos_of_pos hn0 _,
        Real.rpow_lt_one_of_one_lt_of_neg hn1 (by have : a ≤ s := hs; linarith)⟩)
  · exact continuousOn_const

/-- After deleting finitely many primes, the same summable majorant works
for every parameter `s ≥ a`. -/
private theorem uniform_tail_bound {g : ℝ → ℝ} {m a : ℝ}
    (hm : 0 < m) (ha : 0 < a) (hbound : LogPowerBound g m) :
    ∃ C : ℝ, 0 ≤ C ∧ ∃ N : ℕ, ∀ n : ℕ, ∀ s : ℝ, a ≤ s →
      ‖primeTerm g (n + N) s‖ ≤ C * ((n + N : ℕ) : ℝ) ^ (-(m * a)) := by
  obtain ⟨C, ε, hC, hε, hb⟩ := hbound
  have ht : Tendsto (fun n : ℕ => (n : ℝ) ^ (-a)) atTop (𝓝 0) :=
    (tendsto_rpow_neg_atTop ha).comp tendsto_natCast_atTop_atTop
  obtain ⟨N, hN⟩ := eventually_atTop.1 ((tendsto_order.1 ht).2 ε hε)
  refine ⟨C, hC, max N 2, ?_⟩
  intro n s hs
  let k : ℕ := n + max N 2
  have hk2 : 2 ≤ k := by dsimp [k]; omega
  have hkN : N ≤ k := by dsimp [k]; omega
  have hk1 : (1 : ℝ) ≤ k := by exact_mod_cast (show 1 ≤ k by omega)
  have hk0 : (0 : ℝ) < k := by exact_mod_cast (show 0 < k by omega)
  change ‖primeTerm g k s‖ ≤ C * (k : ℝ) ^ (-(m * a))
  unfold primeTerm
  split_ifs with hp
  · have hsmall : (k : ℝ) ^ (-s) < ε :=
      lt_of_le_of_lt (Real.rpow_le_rpow_of_exponent_le hk1 (by linarith)) (hN k hkN)
    calc
      ‖g ((k : ℝ) ^ (-s))‖ ≤ C * ((k : ℝ) ^ (-s)) ^ m :=
        hb _ (Real.rpow_pos_of_pos hk0 _) hsmall
      _ = C * (k : ℝ) ^ ((-s) * m) := by rw [Real.rpow_mul hk0.le]
      _ ≤ C * (k : ℝ) ^ (-(m * a)) :=
        mul_le_mul_of_nonneg_left
          (Real.rpow_le_rpow_of_exponent_le hk1 (by nlinarith)) hC
  · simp only [norm_zero]
    exact mul_nonneg hC (Real.rpow_nonneg hk0.le _)

/-- Absolute convergence of the prime logarithm in its natural half-line. -/
theorem summable_primeTerm {g : ℝ → ℝ} {m s : ℝ}
    (hm : 0 < m) (hs : 1 < m * s) (hbound : LogPowerBound g m) :
    Summable (fun n : ℕ => ‖primeTerm g n s‖) := by
  have hs0 : 0 < s := by nlinarith
  obtain ⟨C, _, N, hN⟩ := uniform_tail_bound hm hs0 hbound
  have hpow : Summable (fun n : ℕ => (n : ℝ) ^ (-(m * s))) :=
    Real.summable_nat_rpow.2 (by linarith)
  have hmajor : Summable (fun n : ℕ => C * ((n + N : ℕ) : ℝ) ^ (-(m * s))) :=
    ((summable_nat_add_iff N).2 hpow).mul_left C
  apply (summable_nat_add_iff N).1
  exact Summable.of_nonneg_of_le (fun _ => norm_nonneg _) (fun n => hN n s le_rfl) hmajor

/-- Local uniform convergence, proved using a common summable tail; no
analytic product-continuity hypothesis is assumed. -/
theorem continuousOn_primeSum {g : ℝ → ℝ} {m a : ℝ}
    (hg : ContinuousOn g (Ioo 0 1)) (hm : 0 < m) (ha : 0 < a)
    (hma : 1 < m * a) (hbound : LogPowerBound g m) :
    ContinuousOn (primeSum g) (Ici a) := by
  obtain ⟨C, _, N, hN⟩ := uniform_tail_bound hm ha hbound
  have hpow : Summable (fun n : ℕ => (n : ℝ) ^ (-(m * a))) :=
    Real.summable_nat_rpow.2 (by linarith)
  have hmajor : Summable (fun n : ℕ => C * ((n + N : ℕ) : ℝ) ^ (-(m * a))) :=
    ((summable_nat_add_iff N).2 hpow).mul_left C
  have htail : ContinuousOn (fun s => ∑' n : ℕ, primeTerm g (n + N) s) (Ici a) :=
    continuousOn_tsum (fun n => primeTerm_continuousOn hg ha (n + N)) hmajor
      (fun n s hs => hN n s hs)
  have hfinite : ContinuousOn (fun s => ∑ n ∈ Finset.range N, primeTerm g n s) (Ici a) :=
    continuousOn_finset_sum _ (fun n _ => primeTerm_continuousOn hg ha n)
  apply (hfinite.add htail).congr
  intro s hs
  exact (sum_add_tsum_nat_add N
    (summable_primeTerm hm (lt_of_lt_of_le hma (mul_le_mul_of_nonneg_left hs hm.le)) hbound).of_norm).symm

/-- Continuity on the open convergence half-line. -/
theorem continuousAt_primeSum {g : ℝ → ℝ} {m s : ℝ}
    (hg : ContinuousOn g (Ioo 0 1)) (hm : 0 < m)
    (hs : 1 < m * s) (hbound : LogPowerBound g m) :
    ContinuousAt (primeSum g) s := by
  have hs' : 1 / m < s := (div_lt_iff hm).2 (by nlinarith)
  obtain ⟨a, ha, has⟩ := exists_between hs'
  have ha0 : 0 < a := lt_trans (div_pos zero_lt_one hm) ha
  have hma : 1 < m * a := by have := (div_lt_iff hm).1 ha; nlinarith
  exact (continuousOn_primeSum hg hm ha0 hma hbound s has.le).continuousAt
    (Ici_mem_nhds has)

theorem primeProduct_pos (g : ℝ → ℝ) (s : ℝ) : 0 < primeProduct g s :=
  Real.exp_pos _

theorem continuousAt_primeProduct {g : ℝ → ℝ} {m s : ℝ}
    (hg : ContinuousOn g (Ioo 0 1)) (hm : 0 < m)
    (hs : 1 < m * s) (hbound : LogPowerBound g m) :
    ContinuousAt (primeProduct g) s :=
  (continuousAt_primeSum hg hm hs hbound).rexp

/-- The defined exponential really is an infinite prime product. -/
theorem hasProd_primeProduct {g : ℝ → ℝ} {m s : ℝ}
    (hm : 0 < m) (hs : 1 < m * s) (hbound : LogPowerBound g m) :
    HasProd (fun n : ℕ => if n.Prime then Real.exp (g ((n : ℝ) ^ (-s))) else 1)
      (primeProduct g s) := by
  have h := ((summable_primeTerm hm hs hbound).of_norm.hasSum).rexp
  apply h.congr_fun
  intro n
  by_cases hn : n.Prime <;> simp [Function.comp_def, primeTerm, hn]

theorem hasProd_primeProduct_subtype {g : ℝ → ℝ} {m s : ℝ}
    (hm : 0 < m) (hs : 1 < m * s) (hbound : LogPowerBound g m) :
    HasProd (fun p : Nat.Primes => Real.exp (g (((p : ℕ) : ℝ) ^ (-s))))
      (primeProduct g s) := by
  change HasProd ((fun n : ℕ => Real.exp (g ((n : ℝ) ^ (-s)))) ∘
    ((↑) : Nat.Primes → ℕ)) (primeProduct g s)
  apply (hasProd_subtype_iff_mulIndicator (s := {n : ℕ | n.Prime})).2
  apply (hasProd_primeProduct hm hs hbound).congr_fun
  intro n
  simp only [Set.mulIndicator_apply, Set.mem_setOf_eq]

/-- Positive continuous local factors with a local bound on their logarithm
give a positive continuous product of those actual factors. -/
theorem hasProd_positive_factors {f : ℝ → ℝ} {m s : ℝ}
    (hf : ∀ x ∈ Ioo (0 : ℝ) 1, 0 < f x)
    (hm : 0 < m) (hs : 1 < m * s)
    (hbound : LogPowerBound (fun x => Real.log (f x)) m) :
    HasProd (fun n : ℕ => if n.Prime then f ((n : ℝ) ^ (-s)) else 1)
      (primeProduct (fun x => Real.log (f x)) s) := by
  have hs0 : 0 < s := by nlinarith
  apply (hasProd_primeProduct hm hs hbound).congr_fun
  intro n
  split_ifs with hn
  · have hn1 : (1 : ℝ) < n := by exact_mod_cast hn.one_lt
    have hx : (n : ℝ) ^ (-s) ∈ Ioo (0 : ℝ) 1 :=
      ⟨Real.rpow_pos_of_pos (lt_trans zero_lt_one hn1) _,
        Real.rpow_lt_one_of_one_lt_of_neg hn1 (by linarith)⟩
    exact (Real.exp_log (hf _ hx)).symm
  · rfl

end

end SingularityAnalysis
