/- NX36 scoped semantic theorem, core Lean 4.12.0.
   Python parsing, rational interval arithmetic, dynamic-table construction,
   source calibration and model correctness are separate obligations. -/
import Init

namespace Singularity.NXDecision

variable {Candidate Target Experiment Reading : Type}

def Identifies (target : Candidate → Target)
    (possible : List Experiment → Candidate → Reading → Prop)
    (panel : List Experiment) : Prop :=
  ∀ a b, target a ≠ target b →
    ¬ ∃ y, possible panel a y ∧ possible panel b y

/-- Accepted disjointness witnesses imply target identification. -/
theorem pair_witness_sound
    (target : Candidate → Target)
    (possible : List Experiment → Candidate → Reading → Prop)
    (panel : List Experiment)
    (witness : ∀ a b, target a ≠ target b →
      ∀ y, possible panel a y → possible panel b y → False) :
    Identifies target possible panel := by
  intro a b hab hex
  obtain ⟨y, hya, hyb⟩ := hex
  exact witness a b hab y hya hyb

/-- A feasible witness and exclusion of every cheaper admissible panel imply
    catalogue optimality. Costs are natural units after one positive common
    denominator has been checked by the exact rational certificate checker. -/
theorem decision_sound
    (target : Candidate → Target)
    (possible : List Experiment → Candidate → Reading → Prop)
    (admissible : List Experiment → Prop)
    (cost : List Experiment → Nat)
    (panel : List Experiment)
    (feasible : Identifies target possible panel)
    (allowed : admissible panel)
    (lower : ∀ other, admissible other → cost other < cost panel →
      ¬ Identifies target possible other) :
    admissible panel ∧ Identifies target possible panel ∧
      ∀ other, admissible other → Identifies target possible other →
        cost panel ≤ cost other := by
  refine ⟨allowed, feasible, ?_⟩
  intro other ha hf
  exact Nat.le_of_not_gt (fun hlt => lower other ha hlt hf)

/-- A strict scalar interval gap prevents a shared reading.  This abstract
    ordered-value version requires only the supplied transitivity/irreflexivity
    facts, so it makes no claim to implement rational arithmetic inside Lean. -/
theorem strict_gap_sound {Value : Type}
    (lt : Value → Value → Prop)
    (trans : ∀ a b c, lt a b → lt b c → lt a c)
    (irrefl : ∀ a, ¬ lt a a)
    (leftUpper rightLower : Value)
    (gap : lt leftUpper rightLower)
    (left right : Value → Prop)
    (leftBound : ∀ y, left y → y = leftUpper ∨ lt y leftUpper)
    (rightBound : ∀ y, right y → y = rightLower ∨ lt rightLower y) :
    ¬ ∃ y, left y ∧ right y := by
  intro hex
  obtain ⟨y, hl, hr⟩ := hex
  have hy : lt y rightLower := by
    cases leftBound y hl with
    | inl h => simpa [h] using gap
    | inr h => exact trans y leftUpper rightLower h gap
  cases rightBound y hr with
  | inl h => exact irrefl y (by simpa [h] using hy)
  | inr h => exact irrefl y (trans y rightLower y hy h)

end Singularity.NXDecision
