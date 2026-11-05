import Std

namespace HeightCertificates

def dot : List Int → List Int → Int
  | a :: as, b :: bs => a*b + dot as bs
  | _, _ => 0

def allZero (rows : List (List Int)) (z : List Int) : Bool :=
  rows.all (fun r => dot r z == 0)

def accepted (rows : List (List Int)) (target z : List Int) : Bool :=
  allZero rows z && (dot target z != 0)

theorem allZero_sound (rows : List (List Int)) (z : List Int)
    (h : allZero rows z = true) : ∀ r ∈ rows, dot r z = 0 := by
  intro r hr
  have h' := List.all_eq_true.mp h r hr
  simpa using h'

theorem accepted_sound (rows : List (List Int)) (target z : List Int)
    (h : accepted rows target z = true) :
    (∀ r ∈ rows, dot r z = 0) ∧ dot target z ≠ 0 := by
  have hh : allZero rows z = true ∧ (dot target z != 0) = true := by
    simpa [accepted] using h
  constructor
  · exact allZero_sound rows z hh.1
  · simpa using hh.2

end HeightCertificates
#print axioms HeightCertificates.allZero_sound
#print axioms HeightCertificates.accepted_sound
