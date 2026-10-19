/- OE12: finite detection for actual formal series with a shared unit denominator.
The denominator representation is an explicit premise. The residue decomposition
and cyclotomic-ring implementation are not claimed kernel-checked here. -/
import Singularity.Periodic
import Singularity.Visibility

namespace Singularity
namespace Periodic

open Vis
local notation "𝟘" => Vis.VRing.zero
local notation "𝟙" => Vis.VRing.one

variable {R : Type} [Vis.VRing R]

theorem conv_prefix (F G D : Nat → R) (cutoff : Nat)
    (h : ∀ k, k ≤ cutoff → F k = G k) :
    ∀ k, k ≤ cutoff → conv F D k = conv G D k := by
  intro k hk
  apply fsum_congr
  intro j hj
  rw [h (k - j) (by omega)]

theorem conv_unit_leading (F D : Nat → R) (hD : D 0 = 𝟙) (k : Nat) :
    conv F D k = F k + fsum (fun j => F (k - (j + 1)) * D (j + 1)) k := by
  unfold conv
  rw [fsum_first]
  simp only [Nat.sub_zero, hD, Vis.mul_one]

/-- Multiplication by a formal series of constant coefficient one is injective.
The proof is triangular strong induction, not an assumed rationality theorem. -/
theorem conv_unit_injective (D F G : Nat → R) (hD : D 0 = 𝟙)
    (h : ∀ k, conv F D k = conv G D k) : F = G := by
  funext k
  induction k using Nat.strongRecOn with
  | ind k ih =>
    have htail : fsum (fun j => F (k - (j + 1)) * D (j + 1)) k =
        fsum (fun j => G (k - (j + 1)) * D (j + 1)) k := by
      apply fsum_congr
      intro j hj
      rw [ih (k - (j + 1)) (by omega)]
    have hk := h k
    rw [conv_unit_leading F D hD, conv_unit_leading G D hD, htail] at hk
    rw [Vis.VRing.add_comm (F k), Vis.VRing.add_comm (G k)] at hk
    exact Vis.add_left_cancel hk

/-- Sufficient half-degree cutoff for two series with the same unit denominator
and finite palindromic numerators. Applies to the periodic sector after supplying
its residue decomposition; graph completeness at ordinary positive q is unrelated. -/
theorem periodic_series_cutoff (degree : Nat) (D F G P Q : Nat → R)
    (hD : D 0 = 𝟙)
    (hF : ∀ k, conv F D k = P k) (hG : ∀ k, conv G D k = Q k)
    (hP : ∀ k, k ≤ degree → P k = P (degree - k))
    (hQ : ∀ k, k ≤ degree → Q k = Q (degree - k))
    (tailP : ∀ k, degree < k → P k = 𝟘)
    (tailQ : ∀ k, degree < k → Q k = 𝟘)
    (agree : ∀ k, k ≤ degree / 2 → F k = G k) : F = G := by
  have hn : P = Q := palindrome_finite_cutoff 𝟘 degree P Q hP hQ tailP tailQ (by
    intro k hk
    rw [← hF k, ← hG k]
    exact conv_prefix F G D (degree / 2) agree k hk)
  apply conv_unit_injective D F G hD
  intro k
  rw [hF k, hG k, hn]

end Periodic
end Singularity
