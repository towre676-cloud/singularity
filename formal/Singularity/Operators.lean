/-
  OE12. Exact finite observation certificates, invariant observational quotients,
  and cost-filtered completeness. Core Lean 4.12, no analytic assumptions.

  State transitions are arbitrary functions. Observation rows are functions with
  pointwise finite linear combinations. Thus the theorems apply in particular
  to rational matrix systems, but do not assume transitions commute. The
  certificate has a finite retained family, closure relations, and actual word
  witnesses. Algorithm termination, row independence, dimension minimality,
  the Python parser and concrete graph compilations are separate obligations.
-/
import Init

namespace Singularity
namespace Operators

variable {State K Action Obs : Type}
variable [Add K] [Mul K] [OfNat K 0]

abbrev Row (State K : Type) := State → K

def pull (step : State → State) (row : Row State K) : Row State K :=
  fun x => row (step x)

/-- Chronological actions: the head action is executed first. -/
def run (step : Action → State → State) : List Action → State → State
  | [], x => x
  | a :: w, x => run step w (step a x)

def experiment (step : Action → State → State) (observe : Obs → Row State K)
    (o : Obs) (w : List Action) : Row State K := fun x => observe o (run step w x)

@[simp] theorem run_nil (step : Action → State → State) (x : State) :
    run step [] x = x := rfl

omit [Add K] [Mul K] [OfNat K 0] in
@[simp] theorem experiment_cons (step : Action → State → State)
    (observe : Obs → Row State K) (o : Obs) (a : Action) (w : List Action) :
    experiment step observe o (a :: w) = pull (step a) (experiment step observe o w) := rfl

/-- The finite linear-combination closure of retained rows. Ring laws are not
needed for the semantic soundness proofs, so coefficients are maximally general. -/
inductive Span {rank : Nat} (basis : Fin rank → Row State K) : Row State K → Prop
  | basis (b : Fin rank) : Span basis (basis b)
  | zero : Span basis (fun _ => 0)
  | add {u v} : Span basis u → Span basis v → Span basis (fun x => u x + v x)
  | scale (c : K) {u} : Span basis u → Span basis (fun x => c * u x)

theorem span_agreement {rank : Nat} {basis : Fin rank → Row State K}
    {row : Row State K} (h : Span basis row) {x y : State}
    (hb : ∀ b, basis b x = basis b y) : row x = row y := by
  induction h with
  | basis b => exact hb b
  | zero => rfl
  | add _ _ hu hv => simp only [hu, hv]
  | scale c _ hu => exact congrArg (c * ·) hu

theorem span_pull {rank : Nat} {basis : Fin rank → Row State K}
    (step : State → State) (closed : ∀ b, Span basis (pull step (basis b)))
    {row : Row State K} (h : Span basis row) : Span basis (pull step row) := by
  induction h with
  | basis b => exact closed b
  | zero => exact Span.zero
  | add _ _ hu hv => exact Span.add hu hv
  | scale c _ hu => exact Span.scale c hu

/-- Independently checkable semantic content of a finite closure certificate.
Actual implementations supply the span expressions by exact matrix identities. -/
structure Certificate (step : Action → State → State) (observe : Obs → Row State K)
    (rank : Nat) where
  basis : Fin rank → Row State K
  initial : ∀ o, Span basis (observe o)
  closed : ∀ a b, Span basis (pull (step a) (basis b))
  witnessed : ∀ b, ∃ o w, basis b = experiment step observe o w

theorem certificate_complete {step : Action → State → State}
    {observe : Obs → Row State K} {rank : Nat}
    (cert : Certificate step observe rank) (o : Obs) (w : List Action) :
    Span cert.basis (experiment step observe o w) := by
  induction w with
  | nil => exact cert.initial o
  | cons a w ih => exact span_pull (step a) (cert.closed a) ih

def encode {rank : Nat} (basis : Fin rank → Row State K) (x : State) : Fin rank → K :=
  fun b => basis b x

def FutureEquivalent (step : Action → State → State) (observe : Obs → Row State K)
    (x y : State) : Prop := ∀ o w, experiment step observe o w x = experiment step observe o w y

theorem encode_eq_iff_future {step : Action → State → State}
    {observe : Obs → Row State K} {rank : Nat}
    (cert : Certificate step observe rank) (x y : State) :
    encode cert.basis x = encode cert.basis y ↔ FutureEquivalent step observe x y := by
  constructor
  · intro h o w
    exact span_agreement (certificate_complete cert o w) (fun b => congrFun h b)
  · intro h
    funext b
    obtain ⟨o, w, hw⟩ := cert.witnessed b
    change cert.basis b x = cert.basis b y
    rw [hw]
    exact h o w

theorem encode_step_eq {step : Action → State → State}
    {observe : Obs → Row State K} {rank : Nat}
    (cert : Certificate step observe rank) (a : Action) {x y : State}
    (h : encode cert.basis x = encode cert.basis y) :
    encode cert.basis (step a x) = encode cert.basis (step a y) := by
  funext b
  exact span_agreement (cert.closed a b) (fun j => congrFun h j)

def observationSetoid {rank : Nat} (basis : Fin rank → Row State K) : Setoid State where
  r x y := encode basis x = encode basis y
  iseqv := ⟨fun _ => rfl, Eq.symm, Eq.trans⟩

def quotientStep {step : Action → State → State} {observe : Obs → Row State K}
    {rank : Nat} (cert : Certificate step observe rank) (a : Action) :
    Quotient (observationSetoid cert.basis) → Quotient (observationSetoid cert.basis) :=
  Quotient.lift (fun x => Quotient.mk _ (step a x))
    (fun _ _ h => Quotient.sound (encode_step_eq cert a h))

@[simp] theorem quotientStep_mk {step : Action → State → State}
    {observe : Obs → Row State K} {rank : Nat}
    (cert : Certificate step observe rank) (a : Action) (x : State) :
    quotientStep cert a (Quotient.mk _ x) = Quotient.mk _ (step a x) := rfl

/-- Every quotient identifies exactly all-future indistinguishable states. -/
theorem quotient_complete {step : Action → State → State}
    {observe : Obs → Row State K} {rank : Nat}
    (cert : Certificate step observe rank) (x y : State) :
    (Quotient.mk (observationSetoid cert.basis) x = Quotient.mk _ y) ↔
      FutureEquivalent step observe x y := by
  constructor
  · intro h
    exact (encode_eq_iff_future cert x y).mp (Quotient.exact h)
  · intro h
    exact Quotient.sound ((encode_eq_iff_future cert x y).mpr h)

/-- Natural costs cover integral tariffs; finitely many nonnegative rational
costs admit common-denominator scaling. That scaling is not formalized here. -/
inductive FilteredSpan {rank : Nat} (basis : Fin rank → Row State K)
    (cost : Fin rank → Nat) (budget : Nat) : Row State K → Prop
  | basis (b : Fin rank) : cost b ≤ budget → FilteredSpan basis cost budget (basis b)
  | zero : FilteredSpan basis cost budget (fun _ => 0)
  | add {u v} : FilteredSpan basis cost budget u → FilteredSpan basis cost budget v →
      FilteredSpan basis cost budget (fun x => u x + v x)
  | scale (c : K) {u} : FilteredSpan basis cost budget u →
      FilteredSpan basis cost budget (fun x => c * u x)

theorem filtered_mono {rank : Nat} {basis : Fin rank → Row State K}
    {cost : Fin rank → Nat} {b c : Nat} (hbc : b ≤ c)
    {row : Row State K} (h : FilteredSpan basis cost b row) :
    FilteredSpan basis cost c row := by
  induction h with
  | basis j hj => exact FilteredSpan.basis j (Nat.le_trans hj hbc)
  | zero => exact FilteredSpan.zero
  | add _ _ hu hv => exact FilteredSpan.add hu hv
  | scale a _ hu => exact FilteredSpan.scale a hu

theorem filtered_agreement {rank : Nat} {basis : Fin rank → Row State K}
    {cost : Fin rank → Nat} {budget : Nat} {row : Row State K}
    (h : FilteredSpan basis cost budget row) {x y : State}
    (hb : ∀ b, cost b ≤ budget → basis b x = basis b y) : row x = row y := by
  induction h with
  | basis b hc => exact hb b hc
  | zero => rfl
  | add _ _ hu hv => simp only [hu, hv]
  | scale c _ hu => exact congrArg (c * ·) hu

theorem filtered_pull {rank : Nat} {basis : Fin rank → Row State K}
    {cost : Fin rank → Nat} (step : State → State) (fee : Nat)
    (closed : ∀ b, FilteredSpan basis cost (cost b + fee) (pull step (basis b)))
    {budget : Nat} {row : Row State K} (h : FilteredSpan basis cost budget row) :
    FilteredSpan basis cost (budget + fee) (pull step row) := by
  induction h with
  | basis b hb => exact filtered_mono (Nat.add_le_add_right hb fee) (closed b)
  | zero => exact FilteredSpan.zero
  | add _ _ hu hv => exact FilteredSpan.add hu hv
  | scale c _ hu => exact FilteredSpan.scale c hu

def wordCost (fee : Action → Nat) : List Action → Nat
  | [] => 0
  | a :: w => wordCost fee w + fee a

structure CostCertificate (step : Action → State → State) (observe : Obs → Row State K)
    (fee : Action → Nat) (readCost : Obs → Nat) (rank : Nat) where
  basis : Fin rank → Row State K
  cost : Fin rank → Nat
  initial : ∀ o, FilteredSpan basis cost (readCost o) (observe o)
  closed : ∀ a b, FilteredSpan basis cost (cost b + fee a) (pull (step a) (basis b))
  witnessed : ∀ b, ∃ o w, basis b = experiment step observe o w ∧
    readCost o + wordCost fee w ≤ cost b

theorem cost_certificate_complete {step : Action → State → State}
    {observe : Obs → Row State K} {fee : Action → Nat} {readCost : Obs → Nat}
    {rank : Nat} (cert : CostCertificate step observe fee readCost rank)
    (o : Obs) (w : List Action) :
    FilteredSpan cert.basis cert.cost (readCost o + wordCost fee w)
      (experiment step observe o w) := by
  induction w with
  | nil => exact cert.initial o
  | cons a w ih =>
      have h := filtered_pull (step a) (fee a) (cert.closed a) ih
      simpa [wordCost, Nat.add_assoc] using h

/-- Cost-bounded agreement is exactly agreement on affordable retained rows. -/
theorem affordable_basis_iff {step : Action → State → State}
    {observe : Obs → Row State K} {fee : Action → Nat} {readCost : Obs → Nat}
    {rank : Nat} (cert : CostCertificate step observe fee readCost rank)
    (budget : Nat) (x y : State) :
    (∀ b, cert.cost b ≤ budget → cert.basis b x = cert.basis b y) ↔
    (∀ o w, readCost o + wordCost fee w ≤ budget →
      experiment step observe o w x = experiment step observe o w y) := by
  constructor
  · intro hb o w hw
    exact filtered_agreement (filtered_mono hw (cost_certificate_complete cert o w)) hb
  · intro h b hb
    obtain ⟨o, w, he, hc⟩ := cert.witnessed b
    rw [he]
    exact h o w (Nat.le_trans hc hb)

/-- A distinguishing retained word with no cheaper distinguishing retained row
has no cheaper distinguishing experiment anywhere in the generator language. -/
theorem cheapest_witness {step : Action → State → State}
    {observe : Obs → Row State K} {fee : Action → Nat} {readCost : Obs → Nat}
    {rank : Nat} (cert : CostCertificate step observe fee readCost rank)
    (x y : State) (o : Obs) (w : List Action)
    (different : experiment step observe o w x ≠ experiment step observe o w y)
    (cheaper : ∀ b, cert.cost b < readCost o + wordCost fee w →
      cert.basis b x = cert.basis b y) :
    experiment step observe o w x ≠ experiment step observe o w y ∧
    ∀ o' w', readCost o' + wordCost fee w' < readCost o + wordCost fee w →
      experiment step observe o' w' x = experiment step observe o' w' y := by
  constructor
  · exact different
  intro o' w' hc
  exact filtered_agreement (cost_certificate_complete cert o' w')
    (fun b hb => cheaper b (Nat.lt_of_le_of_lt hb hc))

end Operators
end Singularity
