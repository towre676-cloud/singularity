import Std
namespace HeightCertificates
 theorem boundedResidueUnique (M x y : Nat) (hx : x < M) (hy : y < M)
     (h : x % M = y % M) : x = y := by
   simpa [Nat.mod_eq_of_lt hx, Nat.mod_eq_of_lt hy] using h
end HeightCertificates
#print axioms HeightCertificates.boundedResidueUnique
