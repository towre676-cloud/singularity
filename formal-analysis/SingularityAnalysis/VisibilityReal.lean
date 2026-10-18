/-
  Faithful real-analytic ingredients for the visibility theorem.

  This module uses Mathlib's actual real numbers, real powers, topology,
  Riemann zeta function, and infinite products.  It does not instantiate the
  abstract `RealFacts` packet or replace missing analytic arguments by axioms.
-/
import SingularityAnalysis.ZetaReal
import Mathlib.Analysis.SpecialFunctions.Pow.Continuity
import Singularity.Visibility
import SingularityAnalysis.PrimeProduct

open Filter Set Topology

noncomputable section

namespace Singularity
namespace RealVisibility

open SingularityAnalysis

/-- Prime powers at a natural integral multiple of the real argument. -/
theorem prime_power_scale (p r : ℕ) (s : ℝ) :
    ((p : ℝ) ^ (-s)) ^ r = (p : ℝ) ^ (-((r : ℝ) * s)) := by
  rw [← Real.rpow_natCast, ← Real.rpow_mul (Nat.cast_nonneg p)]
  congr 1
  ring

theorem zeta_euler_product_nat {s : ℝ} (hs : 1 < s) :
    HasProd (fun n : ℕ => if n.Prime then (1 - (n : ℝ) ^ (-s))⁻¹ else 1)
      (zeta s) := by
  have h := (hasProd_subtype_iff_mulIndicator
    (f := fun n : ℕ => (1 - (n : ℝ) ^ (-s))⁻¹)
    (a := zeta s) (s := {n : ℕ | n.Prime})).mp (zeta_euler_product hs)
  apply h.congr_fun
  intro n
  simp only [Set.mulIndicator, Set.mem_setOf_eq]

/-- The prime logarithm equals the actual real zeta value, rather than a
second unrelated function with a zeta-like name. -/
theorem zeta_eq_primeProduct {s : ℝ} (hs : 1 < s) :
    zeta s = primeProduct (fun x => -Real.log (1 - x)) s := by
  have hp := hasProd_primeProduct (g := fun x => -Real.log (1 - x))
    (by norm_num : (0 : ℝ) < 1) (by simpa using hs) logPowerBound_zeta
  have heq : HasProd
      (fun n : ℕ => if n.Prime then (1 - (n : ℝ) ^ (-s))⁻¹ else 1)
      (primeProduct (fun x => -Real.log (1 - x)) s) := by
    apply hp.congr_fun
    intro n
    split_ifs with hn
    · have hn1 : (1 : ℝ) < n := by exact_mod_cast hn.one_lt
      have hx : (n : ℝ) ^ (-s) < 1 :=
        Real.rpow_lt_one_of_one_lt_of_neg hn1 (by linarith)
      rw [Real.exp_neg, Real.exp_log (by linarith)]
    · rfl
  exact (zeta_euler_product_nat hs).unique heq

theorem zeta_pos {s : ℝ} (hs : 1 < s) : 0 < zeta s := by
  rw [zeta_eq_primeProduct hs]
  exact primeProduct_pos _ _

/-- The logarithm of the regularized local ratio. -/
def regularizedLog (Q : ℝ → ℝ) (r : ℕ) (δ : ℝ) (x : ℝ) : ℝ :=
  δ * Real.log (1 - x ^ r) + Real.log (Q x)

private theorem regularizedLog_continuousOn {Q : ℝ → ℝ} {r : ℕ} (δ : ℝ)
    (hr : 1 ≤ r) (hQ : ContinuousOn Q (Ioo 0 1))
    (hQpos : ∀ x ∈ Ioo (0 : ℝ) 1, 0 < Q x) :
    ContinuousOn (regularizedLog Q r δ) (Ioo 0 1) := by
  have hb : ContinuousOn (fun x : ℝ => 1 - x ^ r) (Ioo 0 1) :=
    (continuous_const.sub (continuous_id.pow r)).continuousOn
  have hbpos : ∀ x ∈ Ioo (0 : ℝ) 1, 0 < 1 - x ^ r := by
    intro x hx
    have hxpow : x ^ r < 1 := pow_lt_one hx.1.le hx.2 (by omega)
    linarith
  exact (continuousOn_const.mul (hb.log (fun x hx => (hbpos x hx).ne'))).add
    (hQ.log (fun x hx => (hQpos x hx).ne'))

/-- A faithful real-analytic visibility theorem from explicit local factor
data.  Infinite-product convergence, continuity and positivity are conclusions,
not assumed analytic packets.  The graph specialization below discharges the
local bounds from certified coefficients and polynomial growth. -/
theorem visibility_of_log_bounds (Q : ℝ → ℝ) (r : ℕ) (δ s0 : ℝ)
    (hr : 1 ≤ r) (hs0 : (r : ℝ) * s0 = 1)
    (hQ : ContinuousOn Q (Ioo 0 1))
    (hQpos : ∀ x ∈ Ioo (0 : ℝ) 1, 0 < Q x)
    (hQbound : LogPowerBound (fun x => Real.log (Q x)) (r : ℝ))
    (hKbound : LogPowerBound (regularizedLog Q r δ) ((r : ℝ) + 1)) :
    ∃ R K : ℝ → ℝ,
      (∀ s, 1 < (r : ℝ) * s →
        HasProd (fun p : ℕ => if p.Prime then Q ((p : ℝ) ^ (-s)) else 1) (R s)) ∧
      (∀ s, 1 < ((r : ℝ) + 1) * s →
        HasProd (fun p : ℕ => if p.Prime then
          (1 - (p : ℝ) ^ (-((r : ℝ) * s))) ^ δ * Q ((p : ℝ) ^ (-s)) else 1)
          (K s)) ∧
      (∀ s, 1 < (r : ℝ) * s → R s = zeta ((r : ℝ) * s) ^ δ * K s) ∧
      0 < K s0 ∧
      Tendsto (fun s => ((r : ℝ) * s - 1) ^ δ * R s)
        (𝓝[>] s0) (𝓝 (K s0)) := by
  let gQ : ℝ → ℝ := fun x => Real.log (Q x)
  let gK : ℝ → ℝ := regularizedLog Q r δ
  let gZ : ℝ → ℝ := fun x => -Real.log (1 - x)
  let R : ℝ → ℝ := primeProduct gQ
  let K : ℝ → ℝ := primeProduct gK
  have hr0 : (0 : ℝ) < r := by exact_mod_cast (show 0 < r by omega)
  have hr1 : (0 : ℝ) < (r : ℝ) + 1 := by positivity
  have hR : ∀ s, 1 < (r : ℝ) * s →
      HasProd (fun p : ℕ => if p.Prime then Q ((p : ℝ) ^ (-s)) else 1) (R s) :=
    fun s hs => hasProd_positive_factors hQpos hr0 hs hQbound
  have hK : ∀ s, 1 < ((r : ℝ) + 1) * s →
      HasProd (fun p : ℕ => if p.Prime then
        (1 - (p : ℝ) ^ (-((r : ℝ) * s))) ^ δ * Q ((p : ℝ) ^ (-s)) else 1) (K s) := by
    intro s hs
    have hspos : 0 < s := by nlinarith
    apply (hasProd_primeProduct hr1 hs hKbound).congr_fun
    intro p
    split_ifs with hp
    · have hp1 : (1 : ℝ) < p := by exact_mod_cast hp.one_lt
      have hx0 : 0 < (p : ℝ) ^ (-s) := Real.rpow_pos_of_pos (by linarith) _
      have hx1 : (p : ℝ) ^ (-s) < 1 :=
        Real.rpow_lt_one_of_one_lt_of_neg hp1 (by linarith)
      have hbase : 0 < 1 - (p : ℝ) ^ (-((r : ℝ) * s)) := by
        have hpw := Real.rpow_lt_one_of_one_lt_of_neg hp1
          (show -((r : ℝ) * s) < 0 by nlinarith)
        linarith
      dsimp [gK, regularizedLog]
      rw [Real.exp_add, prime_power_scale, Real.exp_log (hQpos _ ⟨hx0, hx1⟩),
        Real.rpow_def_of_pos hbase]
      congr 1
      congr 1
      ring
    · rfl
  have hfac : ∀ s, 1 < (r : ℝ) * s → R s = zeta ((r : ℝ) * s) ^ δ * K s := by
    intro s hs
    have hspos : 0 < s := by nlinarith
    have hsk : 1 < ((r : ℝ) + 1) * s := by nlinarith
    have hsumK := (summable_primeTerm hr1 hsk hKbound).of_norm
    have hsumZ := (summable_primeTerm (m := 1) (by norm_num)
      (by simpa using hs) logPowerBound_zeta).of_norm
    have hterm : ∀ p : ℕ, primeTerm gQ p s =
        primeTerm gK p s + δ * primeTerm gZ p ((r : ℝ) * s) := by
      intro p
      unfold primeTerm
      split_ifs
      · dsimp [gQ, gK, gZ, regularizedLog]
        rw [prime_power_scale]
        ring
      · ring
    have hsum : primeSum gQ s = primeSum gK s + δ * primeSum gZ ((r : ℝ) * s) := by
      unfold primeSum
      simp_rw [hterm]
      rw [tsum_add hsumK (hsumZ.mul_left δ), tsum_mul_left]
    have hz : Real.log (zeta ((r : ℝ) * s)) = primeSum gZ ((r : ℝ) * s) := by
      rw [zeta_eq_primeProduct hs]
      exact Real.log_exp _
    dsimp [R, K, primeProduct]
    rw [hsum, Real.exp_add, Real.rpow_def_of_pos (zeta_pos hs), hz]
    rw [mul_comm (Real.exp (primeSum gK s))]
    congr 1
    congr 1
    ring
  have hs0pos : 0 < s0 := by nlinarith
  have hs0k : 1 < ((r : ℝ) + 1) * s0 := by nlinarith
  have hKcont : ContinuousAt K s0 :=
    continuousAt_primeProduct (regularizedLog_continuousOn δ hr hQ hQpos)
      hr1 hs0k hKbound
  have hscale : Tendsto (fun s : ℝ => (r : ℝ) * s) (𝓝[>] s0) (𝓝[>] (1 : ℝ)) := by
    apply tendsto_nhdsWithin_iff.mpr
    constructor
    · have h : Tendsto (fun s : ℝ => (r : ℝ) * s) (𝓝[>] s0) (𝓝 ((r : ℝ) * s0)) :=
        (continuous_const.mul continuous_id).continuousAt.tendsto.mono_left nhdsWithin_le_nhds
      rwa [hs0] at h
    · filter_upwards [self_mem_nhdsWithin] with s hs
      change s0 < s at hs
      show 1 < (r : ℝ) * s
      nlinarith
  have hzlim := zeta_residue_one.comp hscale
  have hpow := hzlim.rpow_const (p := δ) (Or.inl one_ne_zero)
  rw [Real.one_rpow] at hpow
  have hlim := hpow.mul (hKcont.tendsto.mono_left nhdsWithin_le_nhds)
  rw [one_mul] at hlim
  refine ⟨R, K, hR, hK, hfac, primeProduct_pos _ _, ?_⟩
  apply hlim.congr'
  filter_upwards [self_mem_nhdsWithin] with s hs
  have hrs : 1 < (r : ℝ) * s := by
    change s0 < s at hs
    nlinarith
  change (((r : ℝ) * s - 1) * zeta ((r : ℝ) * s)) ^ δ * K s =
    ((r : ℝ) * s - 1) ^ δ * R s
  rw [Real.mul_rpow (by linarith) (zeta_pos hrs).le, hfac s hrs]
  ring

end RealVisibility
end Singularity
