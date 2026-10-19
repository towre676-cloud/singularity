/-
  OE12. Residue complementation for actual height profiles and squared edge
  differences, exact coefficient palindromes, and finite half-degree detection.
  No claim here formalizes the Python cyclotomic-ring implementation.
-/
import Singularity.Normalization

namespace Singularity
namespace Periodic

/-- Complement in the residue box `0,...,top`. -/
def complement (top : Nat) (a : List Nat) : List Nat := a.map (top - ·)

def Bounded (top : Nat) (a : List Nat) : Prop := ∀ x ∈ a, x ≤ top

@[simp] theorem complement_length (top : Nat) (a : List Nat) :
    (complement top a).length = a.length := by simp [complement]

theorem complement_bounded (top : Nat) (a : List Nat) : Bounded top (complement top a) := by
  intro x hx
  obtain ⟨y, _, rfl⟩ := List.mem_map.mp hx
  exact Nat.sub_le _ _

theorem complement_involution (top : Nat) (a : List Nat) (ha : Bounded top a) :
    complement top (complement top a) = a := by
  induction a with
  | nil => rfl
  | cons x xs ih =>
      have hx := ha x (by simp)
      have hxs : Bounded top xs := fun y hy => ha y (List.mem_cons_of_mem _ hy)
      simp only [complement, List.map]
      rw [show top - (top - x) = x by omega]
      exact congrArg (List.cons x) (ih hxs)

theorem complement_volume (top : Nat) : ∀ (a : List Nat), Bounded top a →
    vol (complement top a) + vol a = a.length * top
  | [], _ => by simp [complement, vol]
  | x :: xs, ha => by
      have hx := ha x (by simp)
      have ih := complement_volume top xs (fun y hy => ha y (List.mem_cons_of_mem _ hy))
      simp only [complement, List.map, vol, List.length_cons, Nat.add_mul] at ih ⊢
      omega

theorem square_complement (top x y : Nat) (hx : x ≤ top) (hy : y ≤ top) :
    sqd (top - x) (top - y) = sqd x y := by
  unfold sqd
  have hd : ((top - x : Nat) : Int) - ((top - y : Nat) : Int) = -((x : Int) - y) := by omega
  rw [hd]
  simp [Int.pow_succ, Int.pow_zero, Int.neg_mul_neg]

theorem edge_complement (top : Nat) (a : List Nat) (ha : Bounded top a) (e : Nat × Nat) :
    edgeVal (complement top a) sqd e = edgeVal a sqd e := by
  unfold edgeVal complement
  rw [List.getElem?_map, List.getElem?_map]
  cases hx : a[e.1]? with
  | none => simp
  | some x =>
    cases hy : a[e.2]? with
    | none => simp
    | some y =>
      have hxm : x ∈ a := List.getElem?_mem hx
      have hym : y ∈ a := List.getElem?_mem hy
      simp only [Option.map_some]
      exact square_complement top x y (ha x hxm) (ha y hym)

theorem energy_complement (top : Nat) (a : List Nat) (ha : Bounded top a)
    (edges : List (Nat × Nat)) : energy edges (complement top a) = energy edges a := by
  unfold energy
  induction edges with
  | nil => rfl
  | cons e es ih => simp only [esum]; rw [edge_complement top a ha e, ih]

/-- Integer edge phases may be arbitrary, including zero and negative phases. -/
def phaseEnergy (phases : List ((Nat × Nat) × Int)) (a : List Nat) : Int :=
  match phases with
  | [] => 0
  | (e, phase) :: rest => phase * edgeVal a sqd e + phaseEnergy rest a

theorem phaseEnergy_complement (top : Nat) (a : List Nat) (ha : Bounded top a)
    (phases : List ((Nat × Nat) × Int)) :
    phaseEnergy phases (complement top a) = phaseEnergy phases a := by
  induction phases with
  | nil => rfl
  | cons p ps ih => simp only [phaseEnergy]; rw [edge_complement top a ha p.1, ih]

/-- Exact histogram before specializing the phase variable to a root of unity. -/
def residueFilter (phases : List ((Nat × Nat) × Int)) (n top volume : Nat) (e : Int) : List (List Nat) :=
  (box n top).filter (fun a => decide (vol a = volume ∧ phaseEnergy phases a = e))

def residueCount (phases : List ((Nat × Nat) × Int)) (n top volume : Nat) (e : Int) : Nat :=
  (residueFilter phases n top volume e).length

theorem mem_residueFilter (phases : List ((Nat × Nat) × Int)) (n top volume : Nat)
    (e : Int) (a : List Nat) : a ∈ residueFilter phases n top volume e ↔
    a.length = n ∧ Bounded top a ∧ vol a = volume ∧ phaseEnergy phases a = e := by
  simp only [residueFilter, List.mem_filter, mem_box, decide_eq_true_eq, Bounded]
  constructor
  · rintro ⟨⟨hl, hb⟩, hv, he⟩; exact ⟨hl, hb, hv, he⟩
  · rintro ⟨hl, hb, hv, he⟩; exact ⟨⟨hl, hb⟩, hv, he⟩

theorem complement_map_nodup (top : Nat) (l : List (List Nat)) (hl : l.Nodup)
    (hb : ∀ a ∈ l, Bounded top a) : (l.map (complement top)).Nodup := by
  apply List.pairwise_map.mpr
  apply List.Pairwise.imp_of_mem (p := hl)
  intro a b ha hb' hne he
  apply hne
  have h := congrArg (complement top) he
  rwa [complement_involution top a (hb a ha), complement_involution top b (hb b hb')] at h

/-- Actual residue-box histogram symmetry, with arbitrary integer edge phases. -/
theorem residueCount_palindrome (phases : List ((Nat × Nat) × Int))
    (n top volume : Nat) (e : Int) (hv : volume ≤ n * top) :
    residueCount phases n top volume e = residueCount phases n top (n * top - volume) e := by
  unfold residueCount
  rw [← List.length_map (residueFilter phases n top volume e) (complement top)]
  apply length_eq_of_nodup_mem_iff
  · apply complement_map_nodup top
    · exact List.Pairwise.filter _ (box_nodup n top)
    · intro a ha
      exact ((mem_residueFilter phases n top volume e a).mp ha).2.1
  · exact List.Pairwise.filter _ (box_nodup n top)
  · intro a
    rw [List.mem_map, mem_residueFilter]
    constructor
    · rintro ⟨b, hb, rfl⟩
      obtain ⟨hl, hbound, hvol, he⟩ := (mem_residueFilter phases n top volume e b).mp hb
      have hc := complement_volume top b hbound
      rw [hl, hvol] at hc
      exact ⟨by simpa using hl, complement_bounded top b, by omega,
        by rw [phaseEnergy_complement top b hbound phases, he]⟩
    · rintro ⟨hl, hbound, hvol, he⟩
      refine ⟨complement top a, ?_, complement_involution top a hbound⟩
      apply (mem_residueFilter phases n top volume e _).mpr
      have hc := complement_volume top a hbound
      rw [hl, hvol] at hc
      exact ⟨by simpa using hl, complement_bounded top a, by omega,
        by rw [phaseEnergy_complement top a hbound phases, he]⟩

theorem residueCount_above (phases : List ((Nat × Nat) × Int))
    (n top volume : Nat) (e : Int) (hv : n * top < volume) :
    residueCount phases n top volume e = 0 := by
  unfold residueCount residueFilter
  have hn : (box n top).filter (fun a => decide (vol a = volume ∧ phaseEnergy phases a = e)) = [] := by
    apply List.filter_eq_nil.mpr
    intro a ha hp
    obtain ⟨hl, hb⟩ := (mem_box n top a).mp ha
    have hc := complement_volume top a hb
    have hp' : vol a = volume ∧ phaseEnergy phases a = e := of_decide_eq_true hp
    rw [hl, hp'.1] at hc
    omega
  rw [hn]
  rfl

/-- The half-degree uniqueness lemma holds for coefficients in any type. -/
theorem palindrome_half_unique {K : Type} (degree : Nat) (p q : Nat → K)
    (hp : ∀ k, k ≤ degree → p k = p (degree - k))
    (hq : ∀ k, k ≤ degree → q k = q (degree - k))
    (low : ∀ k, k ≤ degree / 2 → p k = q k) :
    ∀ k, k ≤ degree → p k = q k := by
  intro k hk
  by_cases hl : k ≤ degree / 2
  · exact low k hl
  · rw [hp k hk, hq k hk]
    apply low
    omega

/-- Bounded palindromes agreeing through half the declared degree agree
coefficientwise, including all coefficients beyond the finite support. -/
theorem palindrome_finite_cutoff {K : Type} (zero : K) (degree : Nat) (p q : Nat → K)
    (hp : ∀ k, k ≤ degree → p k = p (degree - k))
    (hq : ∀ k, k ≤ degree → q k = q (degree - k))
    (ptail : ∀ k, degree < k → p k = zero)
    (qtail : ∀ k, degree < k → q k = zero)
    (low : ∀ k, k ≤ degree / 2 → p k = q k) : p = q := by
  funext k
  by_cases hk : k ≤ degree
  · exact palindrome_half_unique degree p q hp hq low k hk
  · rw [ptail k (by omega), qtail k (by omega)]

/-- Complete equality of the finite phase-energy numerators follows from the
low half of their actual residue histograms. This is stronger than any one
root-of-unity specialization, and does not assume the palindrome as a premise. -/
theorem residue_histogram_cutoff (left right : List ((Nat × Nat) × Int))
    (n top : Nat)
    (low : ∀ volume, volume ≤ (n * top) / 2 → ∀ e,
      residueCount left n top volume e = residueCount right n top volume e) :
    ∀ volume e, residueCount left n top volume e = residueCount right n top volume e := by
  intro volume e
  exact congrFun (palindrome_finite_cutoff 0 (n * top)
    (fun k => residueCount left n top k e) (fun k => residueCount right n top k e)
    (fun k hk => residueCount_palindrome left n top k e hk)
    (fun k hk => residueCount_palindrome right n top k e hk)
    (fun k hk => residueCount_above left n top k e hk)
    (fun k hk => residueCount_above right n top k e hk)
    (fun k hk => low k hk e)) volume

end Periodic
end Singularity
