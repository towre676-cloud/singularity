/- OE12: concrete noncommuting integer matrices and the rank-zero case. -/
import Singularity.Operators

namespace Singularity.Operators
namespace Examples

def step (swap : Bool) (x : Int × Int) : Int × Int :=
  if swap then (x.2, x.1) else (x.1 + x.2, x.2)

def observe (_ : Unit) (x : Int × Int) : Int := x.1

def basis (b : Fin 2) (x : Int × Int) : Int := if b.val = 0 then x.1 else x.2

private theorem index_cases (b : Fin 2) : b = 0 ∨ b = 1 := by
  by_cases h : b.val = 0
  · exact Or.inl (Fin.ext h)
  · exact Or.inr (Fin.ext (by omega))

def certificate : Certificate step observe 2 where
  basis := basis
  initial := fun _ => by simpa only [basis, Fin.val_zero, if_pos rfl] using (Span.basis (basis := basis) 0)
  closed := by
    intro a b
    rcases index_cases b with rfl | rfl <;> cases a
    · have h : pull (step false) (basis 0) = (fun x => basis 0 x + basis 1 x) := by
        funext x; simp [pull, step, basis]
      rw [h]
      exact Span.add (Span.basis 0) (Span.basis 1)
    · have h : pull (step true) (basis 0) = basis 1 := by funext x; simp [pull, step, basis]
      rw [h]; exact Span.basis 1
    · have h : pull (step false) (basis 1) = basis 1 := by funext x; simp [pull, step, basis]
      rw [h]; exact Span.basis 1
    · have h : pull (step true) (basis 1) = basis 0 := by funext x; simp [pull, step, basis]
      rw [h]; exact Span.basis 0
  witnessed := by
    intro b
    rcases index_cases b with rfl | rfl
    · exact ⟨(), [], by funext x; simp [basis, experiment, run, observe]⟩
    · exact ⟨(), [true], by funext x; simp [basis, experiment, run, observe, step]⟩

/-- The matrix example catches chronological word reversal: actions do not commute. -/
theorem actions_do_not_commute : run step [true, false] (1, 2) ≠ run step [false, true] (1, 2) := by decide

/-- The retained finite certificate proves every future observation equality,
not just a bounded list of example words. -/
theorem future_iff_state (x y : Int × Int) : FutureEquivalent step observe x y ↔ x = y := by
  constructor
  · intro h
    have he := (encode_eq_iff_future certificate x y).mpr h
    have h0 := congrFun he 0
    have h1 := congrFun he 1
    apply Prod.ext
    · simpa [encode, certificate, basis] using h0
    · simpa [encode, certificate, basis] using h1
  · intro h; subst h; exact fun _ _ => rfl

def zeroCertificate {State Action Obs : Type} (s : Action → State → State) :
    Certificate s (fun (_ : Obs) (_ : State) => (0 : Int)) 0 where
  basis := Fin.elim0
  initial := fun _ => Span.zero
  closed := fun _ b => Fin.elim0 b
  witnessed := fun b => Fin.elim0 b

/-- Rank zero is legitimate and proves equality for every action word. -/
theorem rank_zero_complete {State Action Obs : Type} (s : Action → State → State)
    (x y : State) : FutureEquivalent s (fun (_ : Obs) (_ : State) => (0 : Int)) x y := by
  apply (encode_eq_iff_future (zeroCertificate s) x y).mp
  funext b
  exact Fin.elim0 b

end Examples
end Singularity.Operators
