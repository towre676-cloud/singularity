/-
  Singularity.Visibility  (roadmap push P34, PARTIAL)

  The visibility comparison of manuscript theorem SNG-A11, split at the
  boundary of what core Lean 4.12 (no Mathlib, no real numbers) can check.

  Part A, kernel-checked, general.  Truncated formal power series in `x` over
  an arbitrary commutative ring `R` (class `VRing`, whose laws are hypotheses
  of the class, not axioms).  For series `A`, `B` with `B 0 = 1` that agree
  below degree `r`:
  * `quotient_first_discrepancy`: `A · B⁻¹ ≡ 1 + (A_r - B_r) x^r  (mod x^(r+1))`;
  * `logDer_first_discrepancy`, `log_first_discrepancy`: the logarithmic
    derivatives differ first in degree `r`, by `r (A_r - B_r)`, so over a
    torsion-free ring every formal logarithm difference `log A - log B` has
    vanishing coefficients in degrees `1..r-1` and coefficient `A_r - B_r` at `r`;
  * `binom_cancel`: a factor `≡ 1 - δ x^r` (the expansion of `(1 - x^r)^δ`)
    cancels the first discrepancy `δ` (`r ≥ 1`).

  Part B, kernel-checked, instantiated.  The local coefficient
  `ell G n V q = Σ_{a : vol a = V} q^(E_G a)` evaluated in any commutative ring,
  connected to the P33 certificate theorems (`Cert.*_agree_below`,
  `Cert.*_factorization`), gives the quotient law for the spectral pair
  (`r = 2`, `Δ = 2 q^2 (1-q)^2 (1-q^2)`) and the binary-census pair
  (`r = 3`, `Δ = q^3 (1-q) (1-q^3)^2 (1-q^4)^2`).

  Part C, NOT verified analytically.  `RealFacts K` lists, as explicit premises
  over an abstract commutative ring `K` with abstract operations, the standard
  real-analytic inputs (Euler product and right-hand simple pole of real zeta,
  algebra of convergent prime products and right limits, local power-series
  multiplication/inversion/binomial expansion, and the product convergence
  criterion that packages summability over primes with remainder estimates).
  `visibility_conditional` derives the shape of SNG-A11 (factorization
  `R = ζ(rs)^δ K` for real `rs > 1` and the positive-real asymptotic
  `(rs - 1)^δ R(s) → K(1/r) > 0` as `s ↓ 1/r`) from those premises and the
  Part A theorems.  No premise mentions the conclusion, but nothing here
  proves that `K` is the real numbers or that the abstract operations mean
  what their names say.  No global meromorphic continuation is stated.

  The separate ../formal-analysis package completes the actual positive-real
  theorem using Mathlib and imports the finite coefficient certificates here.
  Its concrete results do not assume RealFacts, Expands or Good. Part C below
  remains a core-only conditional argument with exactly the stated scope.

  No `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by` or `unsafe` is used.
-/
import Singularity.Certificates

namespace Singularity
namespace Vis

/-! ## A. Commutative rings (laws are class fields, i.e. hypotheses) -/

/-- A commutative ring with `0 = zero`, `1 = one`.  The laws are fields of the
    class: every theorem below holds for every structure satisfying them. -/
class VRing (R : Type) extends Add R, Mul R, Neg R where
  zero : R
  one : R
  add_assoc : ∀ a b c : R, a + b + c = a + (b + c)
  add_comm : ∀ a b : R, a + b = b + a
  zero_add : ∀ a : R, zero + a = a
  neg_add : ∀ a : R, -a + a = zero
  mul_assoc : ∀ a b c : R, a * b * c = a * (b * c)
  mul_comm : ∀ a b : R, a * b = b * a
  one_mul : ∀ a : R, one * a = a
  mul_add : ∀ a b c : R, a * (b + c) = a * b + a * c

local notation "𝟘" => VRing.zero
local notation "𝟙" => VRing.one

variable {R : Type} [VRing R]

instance : Sub R := ⟨fun a b => a + -b⟩
instance : Std.Associative (α := R) (· + ·) := ⟨VRing.add_assoc⟩
instance : Std.Commutative (α := R) (· + ·) := ⟨VRing.add_comm⟩
instance : Std.Associative (α := R) (· * ·) := ⟨VRing.mul_assoc⟩
instance : Std.Commutative (α := R) (· * ·) := ⟨VRing.mul_comm⟩

theorem sub_def (a b : R) : a - b = a + -b := rfl
theorem add_zero (a : R) : a + 𝟘 = a := by rw [VRing.add_comm, VRing.zero_add]
theorem add_neg (a : R) : a + -a = 𝟘 := by rw [VRing.add_comm, VRing.neg_add]
theorem sub_self (a : R) : a - a = 𝟘 := add_neg a

theorem add_left_cancel {a b c : R} (h : a + b = a + c) : b = c := by
  have : -a + (a + b) = -a + (a + c) := by rw [h]
  rwa [← VRing.add_assoc, ← VRing.add_assoc, VRing.neg_add, VRing.zero_add, VRing.zero_add] at this

theorem mul_one (a : R) : a * 𝟙 = a := by rw [VRing.mul_comm, VRing.one_mul]

theorem add_mul (a b c : R) : (a + b) * c = a * c + b * c := by
  rw [VRing.mul_comm, VRing.mul_add, VRing.mul_comm c a, VRing.mul_comm c b]

theorem mul_zero (a : R) : a * 𝟘 = 𝟘 := by
  have h : a * 𝟘 + a * 𝟘 = a * 𝟘 + 𝟘 := by rw [← VRing.mul_add, VRing.zero_add, add_zero]
  exact add_left_cancel h

theorem zero_mul (a : R) : 𝟘 * a = 𝟘 := by rw [VRing.mul_comm, mul_zero]

theorem neg_eq_of_add {a b : R} (h : a + b = 𝟘) : -a = b := by
  have : a + -a = a + b := by rw [add_neg, h]
  exact add_left_cancel this

theorem neg_neg (a : R) : - -a = a := neg_eq_of_add (VRing.neg_add a)
theorem neg_zero : -(𝟘 : R) = 𝟘 := neg_eq_of_add (VRing.zero_add _)

theorem neg_mul (a b : R) : -a * b = -(a * b) := by
  apply Eq.symm; apply neg_eq_of_add; rw [← add_mul, add_neg, zero_mul]

theorem mul_neg (a b : R) : a * -b = -(a * b) := by
  rw [VRing.mul_comm, neg_mul, VRing.mul_comm]

theorem neg_add_distrib (a b : R) : -(a + b) = -a + -b := by
  apply neg_eq_of_add
  calc a + b + (-a + -b) = (a + -a) + (b + -b) := by ac_rfl
    _ = 𝟘 := by rw [add_neg, add_neg, add_zero]

theorem sub_zero (a : R) : a - 𝟘 = a := by rw [sub_def, neg_zero, add_zero]

theorem add_sub_cancel' (a b : R) : b + (a - b) = a := by
  rw [sub_def]
  calc b + (a + -b) = a + (b + -b) := by ac_rfl
    _ = a := by rw [add_neg, add_zero]

theorem eq_of_sub_eq_zero {a b : R} (h : a - b = 𝟘) : a = b := by
  rw [← add_sub_cancel' a b, h, add_zero]

theorem add_sub_add_right (x y t : R) : (x + t) - (y + t) = x - y := by
  rw [sub_def, sub_def, neg_add_distrib]
  calc x + t + (-y + -t) = x + -y + (t + -t) := by ac_rfl
    _ = x + -y := by rw [add_neg, add_zero]

theorem mul_sub (a b c : R) : a * (b - c) = a * b - a * c := by
  rw [sub_def, sub_def, VRing.mul_add, mul_neg]

theorem sub_mul (a b c : R) : (a - b) * c = a * c - b * c := by
  rw [VRing.mul_comm, mul_sub, VRing.mul_comm c a, VRing.mul_comm c b]

theorem eq_sub_of_add_eq {x A B : R} (h : x + B = A) : x = A - B := by
  rw [sub_def, ← h, VRing.add_assoc, add_neg, add_zero]

theorem sub_add_self (A N : R) : A - (A + N) = -N := by
  rw [sub_def, neg_add_distrib, ← VRing.add_assoc, add_neg, VRing.zero_add]

/-! ### Natural and integer casts, powers -/

/-- `k ↦ 1 + ⋯ + 1`. -/
def ncast : Nat → R
  | 0 => 𝟘
  | k + 1 => ncast k + 𝟙

theorem ncast_add (a : Nat) : ∀ b, (ncast (a + b) : R) = ncast a + ncast b
  | 0 => (add_zero _).symm
  | b + 1 => by
      show ncast (a + b) + 𝟙 = ncast a + (ncast b + 𝟙)
      rw [ncast_add a b, VRing.add_assoc]

theorem ncast_mul (a : Nat) : ∀ b, (ncast (a * b) : R) = ncast a * ncast b
  | 0 => (mul_zero _).symm
  | b + 1 => by
      show ncast (a * b + a) = ncast a * (ncast b + 𝟙)
      rw [ncast_add, ncast_mul a b, VRing.mul_add, mul_one]

/-- Integer cast. -/
def icast : Int → R
  | Int.ofNat k => ncast k
  | Int.negSucc k => -(ncast (k + 1))

theorem icast_eq (z : Int) (a b : Nat) (h : z = (a : Int) - b) : (icast z : R) = ncast a - ncast b := by
  cases z with
  | ofNat k =>
      rw [Int.ofNat_eq_coe] at h
      have hk : k + b = a := by omega
      show ncast k = _
      apply eq_sub_of_add_eq
      rw [← ncast_add, hk]
  | negSucc k =>
      rw [Int.negSucc_eq] at h
      have hk : a + (k + 1) = b := by omega
      show -(ncast (k + 1)) = _
      rw [← hk, ncast_add a (k + 1), sub_add_self]

theorem icast_zero : (icast 0 : R) = 𝟘 := rfl
theorem icast_one : (icast 1 : R) = 𝟙 := VRing.zero_add _
theorem icast_neg_one : (icast (-1) : R) = -𝟙 := by
  show -(ncast 1) = _
  rw [show (ncast 1 : R) = 𝟙 from VRing.zero_add _]

/-- Positive and negative parts of an integer. -/
def ipos : Int → Nat
  | Int.ofNat k => k
  | Int.negSucc _ => 0
def ineg : Int → Nat
  | Int.ofNat _ => 0
  | Int.negSucc k => k + 1

theorem int_split (z : Int) : z = (ipos z : Int) - (ineg z : Int) := by
  cases z with
  | ofNat k => show Int.ofNat k = (k : Int) - ((0 : Nat) : Int); rw [Int.ofNat_eq_coe]; omega
  | negSucc k => show Int.negSucc k = ((0 : Nat) : Int) - ((k + 1 : Nat) : Int); rw [Int.negSucc_eq]; omega

theorem icast_split (z : Int) : (icast z : R) = ncast (ipos z) - ncast (ineg z) :=
  icast_eq z _ _ (int_split z)

theorem icast_add (z w : Int) : (icast (z + w) : R) = icast z + icast w := by
  have h : z + w = ((ipos z + ipos w : Nat) : Int) - ((ineg z + ineg w : Nat) : Int) := by
    have := int_split z; have := int_split w; omega
  rw [icast_eq _ _ _ h, icast_split z, icast_split w, ncast_add, ncast_add, sub_def, sub_def, sub_def,
    neg_add_distrib]
  ac_rfl

theorem mul_split (a b c d : Nat) :
    ((a : Int) - b) * ((c : Int) - d) = ((a * c + b * d : Nat) : Int) - ((a * d + b * c : Nat) : Int) := by
  simp only [Int.sub_mul, Int.mul_sub, Int.natCast_add, Int.natCast_mul]; omega

theorem icast_mul (z w : Int) : (icast (z * w) : R) = icast z * icast w := by
  have h : z * w = ((ipos z * ipos w + ineg z * ineg w : Nat) : Int) -
      ((ipos z * ineg w + ineg z * ipos w : Nat) : Int) := by
    calc z * w = ((ipos z : Int) - ineg z) * ((ipos w : Int) - ineg w) := by
          rw [← int_split z, ← int_split w]
      _ = _ := mul_split _ _ _ _
  rw [icast_eq _ _ _ h, icast_split z, icast_split w, ncast_add, ncast_add, ncast_mul, ncast_mul,
    ncast_mul, ncast_mul, sub_mul, mul_sub, mul_sub]
  simp only [sub_def, neg_add_distrib, neg_neg]
  ac_rfl

/-- `a^k`. -/
def npow (a : R) : Nat → R
  | 0 => 𝟙
  | k + 1 => npow a k * a

/-! ### Finite sums -/

/-- `fsum f n = f 0 + ⋯ + f (n-1)`. -/
def fsum (f : Nat → R) : Nat → R
  | 0 => 𝟘
  | n + 1 => fsum f n + f n

theorem fsum_congr {f g : Nat → R} : ∀ n, (∀ i, i < n → f i = g i) → fsum f n = fsum g n
  | 0, _ => rfl
  | n + 1, h => by
      show fsum f n + f n = fsum g n + g n
      rw [fsum_congr n (fun i hi => h i (by omega)), h n (by omega)]

theorem fsum_zero {f : Nat → R} : ∀ n, (∀ i, i < n → f i = 𝟘) → fsum f n = 𝟘
  | 0, _ => rfl
  | n + 1, h => by
      show fsum f n + f n = 𝟘
      rw [fsum_zero n (fun i hi => h i (by omega)), h n (by omega), add_zero]

theorem fsum_add (f g : Nat → R) : ∀ n, fsum (fun i => f i + g i) n = fsum f n + fsum g n
  | 0 => (add_zero _).symm
  | n + 1 => by
      show fsum (fun i => f i + g i) n + (f n + g n) = (fsum f n + f n) + (fsum g n + g n)
      rw [fsum_add f g n]; ac_rfl

theorem fsum_neg (f : Nat → R) : ∀ n, fsum (fun i => -(f i)) n = -(fsum f n)
  | 0 => neg_zero.symm
  | n + 1 => by
      show fsum (fun i => -(f i)) n + -(f n) = -(fsum f n + f n)
      rw [fsum_neg f n, neg_add_distrib]

theorem fsum_sub (f g : Nat → R) (n : Nat) : fsum (fun i => f i - g i) n = fsum f n - fsum g n := by
  rw [sub_def, ← fsum_neg, ← fsum_add]; rfl

theorem fsum_mul_left (c : R) (f : Nat → R) : ∀ n, fsum (fun i => c * f i) n = c * fsum f n
  | 0 => (mul_zero _).symm
  | n + 1 => by
      show fsum (fun i => c * f i) n + c * f n = c * (fsum f n + f n)
      rw [fsum_mul_left c f n, VRing.mul_add]

theorem fsum_first (f : Nat → R) : ∀ n, fsum f (n + 1) = f 0 + fsum (fun i => f (i + 1)) n
  | 0 => by show 𝟘 + f 0 = f 0 + 𝟘; rw [VRing.zero_add, add_zero]
  | n + 1 => by
      show fsum f (n + 1) + f (n + 1) = f 0 + (fsum (fun i => f (i + 1)) n + f (n + 1))
      rw [fsum_first f n, VRing.add_assoc]

/-- A sum with a single possibly nonzero term. -/
theorem fsum_single (i : Nat) (c : R) : ∀ n,
    fsum (fun j => if j = i then c else 𝟘) n = if i < n then c else 𝟘
  | 0 => by rw [if_neg (Nat.not_lt_zero i)]; rfl
  | n + 1 => by
      show fsum (fun j => if j = i then c else 𝟘) n + (if n = i then c else 𝟘) = _
      rw [fsum_single i c n]
      by_cases h1 : i < n
      · rw [if_pos h1, if_neg (by omega), if_pos (by omega), add_zero]
      · by_cases h2 : n = i
        · rw [if_neg h1, if_pos h2, if_pos (by omega), VRing.zero_add]
        · rw [if_neg h1, if_neg h2, if_neg (by omega), add_zero]

/-! ### Truncated power series -/

/-- Cauchy product: `(F·G)_k = Σ_{j ≤ k} F_(k-j) G_j`. -/
def conv (F G : Nat → R) (k : Nat) : R := fsum (fun j => F (k - j) * G j) (k + 1)

/-- The series `c x^r`. -/
def mono (c : R) (r : Nat) (k : Nat) : R := if k = r then c else 𝟘

theorem mono_self (c : R) (r : Nat) : mono c r r = c := if_pos rfl
theorem mono_ne (c : R) {r k : Nat} (h : k ≠ r) : mono c r k = 𝟘 := if_neg h

/-- `F ≡ G (mod x^(N+1))`. -/
def TruncEq (N : Nat) (F G : Nat → R) : Prop := ∀ k, k ≤ N → F k = G k

/-- Formal inverse of a series with constant term `1`: coefficients `0..k`
    computed by `C_0 = 1`, `C_k = -Σ_{j<k} B_(k-j) C_j`. -/
def invUpTo (B : Nat → R) : Nat → Nat → R
  | 0 => fun i => if i = 0 then 𝟙 else 𝟘
  | k + 1 => fun i => if i = k + 1 then -(fsum (fun j => B (k + 1 - j) * invUpTo B k j) (k + 1))
      else invUpTo B k i

/-- The formal inverse `B⁻¹` (meaningful when `B 0 = 1`). -/
def sinv (B : Nat → R) (k : Nat) : R := invUpTo B k k

theorem invUpTo_stable (B : Nat → R) (i k : Nat) (hi : i ≤ k) : ∀ m, invUpTo B (k + m) i = invUpTo B k i
  | 0 => rfl
  | m + 1 => by
      show (if i = k + m + 1 then _ else invUpTo B (k + m) i) = _
      rw [if_neg (by omega), invUpTo_stable B i k hi m]

theorem sinv_eq (B : Nat → R) {i k : Nat} (hi : i ≤ k) : sinv B i = invUpTo B k i := by
  have := invUpTo_stable B i i (Nat.le_refl i) (k - i)
  rw [Nat.add_sub_cancel' hi] at this
  exact this.symm

theorem sinv_zero (B : Nat → R) : sinv B 0 = 𝟙 := by
  show (if 0 = 0 then 𝟙 else 𝟘) = 𝟙
  exact if_pos rfl

theorem sinv_succ (B : Nat → R) (k : Nat) :
    sinv B (k + 1) = -(fsum (fun j => B (k + 1 - j) * sinv B j) (k + 1)) := by
  show (if k + 1 = k + 1 then _ else _) = _
  rw [if_pos rfl]
  congr 1
  apply fsum_congr
  intro j hj
  rw [sinv_eq B (show j ≤ k by omega)]

/-- `B · B⁻¹ = 1` whenever `B 0 = 1` (all degrees). -/
theorem conv_sinv (B : Nat → R) (hB0 : B 0 = 𝟙) : ∀ k, conv B (sinv B) k = mono 𝟙 0 k
  | 0 => by
      show 𝟘 + B 0 * sinv B 0 = mono 𝟙 0 0
      rw [VRing.zero_add, hB0, sinv_zero, mul_one, mono_self]
  | k + 1 => by
      show fsum (fun j => B (k + 1 - j) * sinv B j) (k + 1) + B (k + 1 - (k + 1)) * sinv B (k + 1) = _
      rw [Nat.sub_self, hB0, VRing.one_mul, sinv_succ, add_neg, mono_ne _ (by omega)]

/-! ### Finite cancellation -/

/-- **Quotient law (general form).**  If `B 0 = 1`, `C` is an inverse of `B`
    modulo `x^(r+1)` and `A_k = B_k` for `k < r`, then
    `A · C ≡ 1 + (A_r - B_r) x^r (mod x^(r+1))`. -/
theorem conv_quot (A B C : Nat → R) (r : Nat) (hB0 : B 0 = 𝟙) (hC : TruncEq r (conv B C) (mono 𝟙 0))
    (hAB : ∀ k, k < r → A k = B k) :
    TruncEq r (conv A C) (fun k => mono 𝟙 0 k + mono (A r - B r) r k) := by
  have hC0 : C 0 = 𝟙 := by
    have h := hC 0 (Nat.zero_le _)
    have e : conv B C 0 = B 0 * C 0 := by
      show 𝟘 + B (0 - 0) * C 0 = _
      rw [VRing.zero_add]
    rw [e, hB0, VRing.one_mul, mono_self] at h
    exact h
  intro k hk
  have split : conv A C k = conv B C k + fsum (fun j => (A (k - j) - B (k - j)) * C j) (k + 1) := by
    unfold conv
    rw [← fsum_add]
    apply fsum_congr
    intro j _
    rw [← add_mul, add_sub_cancel']
  rw [split, hC k hk, fsum_first, Nat.sub_zero, hC0, mul_one]
  rw [fsum_zero k (fun j hj => by rw [hAB (k - (j + 1)) (by omega), sub_self, zero_mul]), add_zero]
  show mono 𝟙 0 k + (A k - B k) = mono 𝟙 0 k + mono (A r - B r) r k
  by_cases hkr : k = r
  · rw [hkr, mono_self]
  · rw [hAB k (by omega), sub_self, mono_ne _ hkr]

/-- **Finite cancellation.**  For `B 0 = 1` and `A_k = B_k` for all `k < r`,
    `A · B⁻¹ ≡ 1 + (A_r - B_r) x^r (mod x^(r+1))`.  Holds for every `r` and every
    pair of such series over every commutative ring. -/
theorem quotient_first_discrepancy (A B : Nat → R) (r : Nat) (hB0 : B 0 = 𝟙)
    (hAB : ∀ k, k < r → A k = B k) :
    TruncEq r (conv A (sinv B)) (fun k => mono 𝟙 0 k + mono (A r - B r) r k) :=
  conv_quot A B (sinv B) r hB0 (fun k _ => conv_sinv B hB0 k) hAB

/-- The same hypotheses say exactly that `A - B ≡ (A_r - B_r) x^r (mod x^(r+1))`:
    `A_r - B_r` is the first difference. -/
theorem first_difference (A B : Nat → R) (r : Nat) (hAB : ∀ k, k < r → A k = B k) :
    TruncEq r (fun k => A k - B k) (mono (A r - B r) r) := by
  intro k hk
  by_cases hkr : k = r
  · rw [hkr, mono_self]
  · show A k - B k = mono (A r - B r) r k
    rw [hAB k (by omega), sub_self, mono_ne _ hkr]

/-! ### Logarithmic derivative and formal logarithm -/

/-- `x · A'`: coefficient `k · A_k`. -/
def xder (A : Nat → R) (k : Nat) : R := ncast k * A k

/-- The logarithmic derivative `x A' / A`, the `x`-derivative of `log A`. -/
def logDer (A : Nat → R) : Nat → R := conv (xder A) (sinv A)

theorem invUpTo_agree (A B : Nat → R) (r : Nat) (hAB : ∀ k, k < r → A k = B k) :
    ∀ k, k < r → ∀ i, invUpTo A k i = invUpTo B k i
  | 0, _, _ => rfl
  | k + 1, hk, i => by
      show (if i = k + 1 then -(fsum (fun j => A (k + 1 - j) * invUpTo A k j) (k + 1)) else invUpTo A k i) =
        (if i = k + 1 then -(fsum (fun j => B (k + 1 - j) * invUpTo B k j) (k + 1)) else invUpTo B k i)
      have ih := invUpTo_agree A B r hAB k (by omega)
      have hs : fsum (fun j => A (k + 1 - j) * invUpTo A k j) (k + 1) =
          fsum (fun j => B (k + 1 - j) * invUpTo B k j) (k + 1) :=
        fsum_congr _ (fun j _ => by rw [hAB (k + 1 - j) (by omega), ih j])
      rw [hs, ih i]

/-- Inverse coefficients below `r` depend only on coefficients below `r`. -/
theorem sinv_agree (A B : Nat → R) (r : Nat) (hAB : ∀ k, k < r → A k = B k) :
    ∀ j, j < r → sinv A j = sinv B j :=
  fun j hj => invUpTo_agree A B r hAB j hj j

/-- **Logarithmic derivatives.**  If `A_k = B_k` for `k < r`, then
    `x A'/A - x B'/B ≡ r (A_r - B_r) x^r (mod x^(r+1))`. -/
theorem logDer_first_discrepancy (A B : Nat → R) (r : Nat) (hAB : ∀ k, k < r → A k = B k) :
    TruncEq r (fun k => logDer A k - logDer B k) (mono (ncast r * (A r - B r)) r) := by
  intro k hk
  show conv (xder A) (sinv A) k - conv (xder B) (sinv B) k = _
  unfold conv
  rw [fsum_first, fsum_first]
  have htail : fsum (fun j => xder A (k - (j + 1)) * sinv A (j + 1)) k =
      fsum (fun j => xder B (k - (j + 1)) * sinv B (j + 1)) k := by
    apply fsum_congr
    intro j hj
    by_cases hjr : j + 1 < r
    · unfold xder
      rw [hAB (k - (j + 1)) (by omega), sinv_agree A B r hAB (j + 1) hjr]
    · have h0 : k - (j + 1) = 0 := by omega
      rw [h0]
      show 𝟘 * A 0 * _ = 𝟘 * B 0 * _
      rw [zero_mul, zero_mul, zero_mul, zero_mul]
  rw [htail, add_sub_add_right, Nat.sub_zero, sinv_zero, sinv_zero, mul_one, mul_one]
  unfold xder
  rw [← mul_sub]
  by_cases hkr : k = r
  · rw [hkr, mono_self]
  · rw [hAB k (by omega), sub_self, mul_zero, mono_ne _ hkr]

/-- **First coefficient of `log A - log B`.**  Over a ring without additive
    torsion (`k a = 0`, `k ≥ 1` ⇒ `a = 0`; true for `ℤ`, `ℚ`, `ℝ`), let `lA`, `lB`
    be any formal logarithms, characterized by `k · (log A)_k = (x A'/A)_k`
    for `1 ≤ k ≤ r`.  If `A_k = B_k` for `k < r`, then `log A - log B` has zero
    coefficients in degrees `1..r-1` and coefficient `A_r - B_r` in degree `r`. -/
theorem log_first_discrepancy (A B lA lB : Nat → R) (r : Nat)
    (htf : ∀ (k : Nat) (a : R), 1 ≤ k → ncast k * a = 𝟘 → a = 𝟘)
    (hAB : ∀ k, k < r → A k = B k)
    (hlA : ∀ k, 1 ≤ k → k ≤ r → ncast k * lA k = logDer A k)
    (hlB : ∀ k, 1 ≤ k → k ≤ r → ncast k * lB k = logDer B k) :
    (∀ k, 1 ≤ k → k < r → lA k = lB k) ∧ (1 ≤ r → lA r - lB r = A r - B r) := by
  have hD := logDer_first_discrepancy A B r hAB
  refine ⟨fun k h1 hk => ?_, fun h1 => ?_⟩
  · apply eq_of_sub_eq_zero
    apply htf k _ h1
    rw [mul_sub, hlA k h1 (by omega), hlB k h1 (by omega)]
    exact (hD k (by omega)).trans (mono_ne _ (by omega))
  · apply eq_of_sub_eq_zero
    apply htf r _ h1
    rw [mul_sub, mul_sub, hlA r h1 (Nat.le_refl r), hlB r h1 (Nat.le_refl r)]
    have := hD r (Nat.le_refl r)
    simp only [] at this
    rw [this, mono_self, sub_self]

/-- **Cancellation by the zeta factor (formal).**  For `r ≥ 1`, if
    `F ≡ 1 - δ x^r` (the expansion of `(1 - x^r)^δ`) and `Q ≡ 1 + δ x^r`
    modulo `x^(r+1)`, then `F · Q ≡ 1 (mod x^(r+1))`. -/
theorem binom_cancel (F Q : Nat → R) (r : Nat) (δ : R) (hr : 1 ≤ r)
    (hF : TruncEq r F (fun k => mono 𝟙 0 k + mono (-δ) r k))
    (hQ : TruncEq r Q (fun k => mono 𝟙 0 k + mono δ r k)) :
    TruncEq r (conv F Q) (mono 𝟙 0) := by
  intro k hk
  unfold conv
  rw [fsum_first, Nat.sub_zero]
  have hQ0 : Q 0 = 𝟙 := by
    rw [hQ 0 (Nat.zero_le _)]
    show mono 𝟙 0 0 + mono δ r 0 = 𝟙
    rw [mono_self, mono_ne _ (by omega), add_zero]
  have htail : fsum (fun j => F (k - (j + 1)) * Q (j + 1)) k =
      fsum (fun j => if j = k - 1 then mono δ r k else 𝟘) k := by
    apply fsum_congr
    intro j hj
    rw [hF (k - (j + 1)) (by omega), hQ (j + 1) (by omega)]
    show (mono 𝟙 0 (k - (j + 1)) + mono (-δ) r (k - (j + 1))) * (mono 𝟙 0 (j + 1) + mono δ r (j + 1)) = _
    rw [mono_ne (-δ) (show k - (j + 1) ≠ r by omega), add_zero, mono_ne 𝟙 (show j + 1 ≠ 0 by omega),
      VRing.zero_add]
    by_cases hjk : j = k - 1
    · rw [if_pos hjk, show k - (j + 1) = 0 by omega, mono_self, VRing.one_mul, show j + 1 = k by omega]
    · rw [if_neg hjk, mono_ne 𝟙 (show k - (j + 1) ≠ 0 by omega), zero_mul]
  rw [htail, fsum_single, hF k hk, hQ0, mul_one]
  show mono 𝟙 0 k + mono (-δ) r k + (if k - 1 < k then mono δ r k else 𝟘) = mono 𝟙 0 k
  by_cases hkr : k = r
  · rw [if_pos (by omega), hkr, mono_self, mono_self, VRing.add_assoc, VRing.neg_add, add_zero]
  · rw [mono_ne _ hkr, add_zero]
    by_cases h0 : k - 1 < k
    · rw [if_pos h0, mono_ne _ hkr, add_zero]
    · rw [if_neg h0, add_zero]

/-! ## B. Local coefficients evaluated in a ring, and the P33 certificates -/

/-- `Σ_{a ∈ L} q^(E_G a)` (energies are nonnegative, so `toNat` loses nothing on profiles). -/
def psum (q : R) (E : List (Nat × Nat)) : List (List Nat) → R
  | [] => 𝟘
  | a :: L => npow q (energy E a).toNat + psum q E L

/-- The local coefficient `ℓ_{G,V}(q) = [x^V] L_G(x,q) = Σ_{a ∈ ℕ^n, vol a = V} q^(E_G a)`,
    summed over the complete duplicate-free enumeration `comps n V` (P33 `mem_comps`,
    `comps_nodup`), evaluated at an element `q` of any commutative ring. -/
def ell (E : List (Nat × Nat)) (n V : Nat) (q : R) : R := psum q E (comps n V)

/-- The local series `L_G(·, q)` as a formal power series in `x`. -/
def lseries (E : List (Nat × Nat)) (n : Nat) (q : R) : Nat → R := fun V => ell E n V q

/-- Grouping by energy: if all energies in `L` lie in `[0, N)`, the sum over
    profiles is `Σ_{k<N} #{a ∈ L : E a = k} q^k`. -/
theorem psum_eq_counts (q : R) (E : List (Nat × Nat)) (N : Nat) : ∀ (L : List (List Nat)),
    (∀ a ∈ L, 0 ≤ energy E a ∧ energy E a < N) →
    psum q E L = fsum (fun k => ncast ((L.filter (fun a => decide (energy E a = (k : Int)))).length) *
      npow q k) N
  | [], _ => (fsum_zero N (fun _ _ => zero_mul _)).symm
  | a :: L, h => by
      have ha := h a (List.mem_cons_self a L)
      have ih := psum_eq_counts q E N L (fun b hb => h b (List.mem_cons_of_mem a hb))
      have hnn : ((energy E a).toNat : Int) = energy E a := Int.toNat_of_nonneg ha.1
      have hpt : ∀ k, k < N →
          ncast ((List.filter (fun b => decide (energy E b = (k : Int))) (a :: L)).length) * npow q k =
          (if k = (energy E a).toNat then npow q (energy E a).toNat else 𝟘) +
          ncast ((L.filter (fun b => decide (energy E b = (k : Int)))).length) * npow q k := by
        intro k _
        by_cases hk : energy E a = (k : Int)
        · rw [List.filter_cons_of_pos (by simp [hk]), List.length_cons]
          have : k = (energy E a).toNat := by omega
          rw [if_pos this, ← this]
          show (ncast _ + 𝟙) * npow q k = _
          rw [add_mul, VRing.one_mul, VRing.add_comm]
        · rw [List.filter_cons_of_neg (by simp [hk])]
          rw [if_neg (by omega), VRing.zero_add]
      rw [fsum_congr N hpt, fsum_add, fsum_single, if_pos (by omega), ← ih]
      rfl

/-- `ℓ_{G,V}(q) = Σ_{k<N} [x^V q^k] L_G · q^k`, with the P07 coefficient `allCount`,
    whenever every energy at volume `V` lies in `[0, N)`. -/
theorem ell_eq_counts (E : List (Nat × Nat)) (n V N : Nat) (q : R)
    (h : ∀ a ∈ comps n V, 0 ≤ energy E a ∧ energy E a < N) :
    ell E n V q = fsum (fun k => ncast (allCount E n V k) * npow q k) N := by
  unfold ell
  rw [psum_eq_counts q E N _ h]
  apply fsum_congr
  intro k _
  rw [allCount_eq_compCount]
  rfl

/-- Integer polynomial `Σ p_i x^i` (dense coefficient list) evaluated in `R`. -/
def pevalR : List Int → R → R
  | [], _ => 𝟘
  | a :: p, x => icast a + x * pevalR p x

theorem fsum_poly (x : R) : ∀ (p : List Int) (N : Nat), p.length ≤ N →
    fsum (fun k => icast (p.getD k 0) * npow x k) N = pevalR p x
  | [], N, _ => fsum_zero N (fun _ _ => zero_mul _)
  | a :: p, 0, h => by simp at h
  | a :: p, N + 1, h => by
      rw [fsum_first]
      have ih := fsum_poly x p N (by simp at h; omega)
      have e : fsum (fun i => icast ((a :: p).getD (i + 1) 0) * npow x (i + 1)) N =
          fsum (fun i => x * (icast (p.getD i 0) * npow x i)) N := by
        apply fsum_congr; intro i _
        show icast (p.getD i 0) * (npow x i * x) = _
        ac_rfl
      rw [e, fsum_mul_left, ih]
      show icast a * 𝟙 + _ = _
      rw [mul_one]; rfl

/-- Equal coefficient tables give equal local coefficients. -/
theorem ell_eq_of_counts {G H : List (Nat × Nat)} {n V N : Nat} (q : R)
    (hG : ∀ a ∈ comps n V, 0 ≤ energy G a ∧ energy G a < N)
    (hH : ∀ a ∈ comps n V, 0 ≤ energy H a ∧ energy H a < N)
    (h : ∀ e : Int, allCount G n V e = allCount H n V e) : ell G n V q = ell H n V q := by
  rw [ell_eq_counts G n V N q hG, ell_eq_counts H n V N q hH]
  exact fsum_congr N (fun k _ => by rw [h])

/-- A coefficientwise first difference given by a dense integer polynomial `p`
    gives `ℓ_{G,d}(q) - ℓ_{H,d}(q) = p(q)` in every ring. -/
theorem ell_sub_of_dense {G H : List (Nat × Nat)} {n d N : Nat} {p : List Int} (q : R)
    (hG : ∀ a ∈ comps n d, 0 ≤ energy G a ∧ energy G a < N)
    (hH : ∀ a ∈ comps n d, 0 ≤ energy H a ∧ energy H a < N) (hp : p.length ≤ N)
    (h : ∀ e : Int, (allCount G n d e : Int) - allCount H n d e = dcoeff p e) :
    ell G n d q - ell H n d q = pevalR p q := by
  rw [ell_eq_counts G n d N q hG, ell_eq_counts H n d N q hH, ← fsum_sub, ← fsum_poly q p N hp]
  apply fsum_congr
  intro k _
  rw [← sub_mul, ← icast_eq _ _ _ rfl, h k]
  rfl

/-! ### Evaluation semantics of P33's dense polynomial operations in `R` -/

theorem pevalR_padd (x : R) : ∀ (p q : List Int), pevalR (padd p q) x = pevalR p x + pevalR q x
  | [], [] => (add_zero _).symm
  | [], b :: q => (VRing.zero_add _).symm
  | a :: p, [] => by show pevalR (a :: p) x = _ + 𝟘; rw [add_zero]
  | a :: p, b :: q => by
      show icast (a + b) + x * pevalR (padd p q) x = (icast a + x * pevalR p x) + (icast b + x * pevalR q x)
      rw [icast_add, pevalR_padd x p q, VRing.mul_add]; ac_rfl

theorem pevalR_pscale (x : R) (c : Int) : ∀ (p : List Int), pevalR (pscale c p) x = icast c * pevalR p x
  | [] => (mul_zero _).symm
  | a :: p => by
      have ih := pevalR_pscale x c p
      unfold pscale at ih
      show icast (c * a) + x * pevalR (p.map (c * ·)) x = icast c * (icast a + x * pevalR p x)
      rw [ih, icast_mul, VRing.mul_add]; ac_rfl

theorem pevalR_pmul (x : R) : ∀ (p q : List Int), pevalR (pmul p q) x = pevalR p x * pevalR q x
  | [], _ => (zero_mul _).symm
  | a :: p, q => by
      show pevalR (padd (pscale a q) (0 :: pmul p q)) x = (icast a + x * pevalR p x) * pevalR q x
      rw [pevalR_padd, pevalR_pscale]
      show icast a * pevalR q x + (icast 0 + x * pevalR (pmul p q) x) = _
      rw [pevalR_pmul x p q, icast_zero, VRing.zero_add, add_mul, VRing.mul_assoc]

theorem pevalR_ppow (x : R) (p : List Int) : ∀ k, pevalR (ppow p k) x = npow (pevalR p x) k
  | 0 => by show icast 1 + x * 𝟘 = 𝟙; rw [icast_one, mul_zero, add_zero]
  | k + 1 => by
      show pevalR (pmul p (ppow p k)) x = npow (pevalR p x) k * pevalR p x
      rw [pevalR_pmul, pevalR_ppow x p k, VRing.mul_comm]

theorem pevalR_replicate_append (x : R) : ∀ (m : Nat) (tail : List Int),
    pevalR (List.replicate m 0 ++ tail) x = npow x m * pevalR tail x
  | 0, tail => (VRing.one_mul _).symm
  | m + 1, tail => by
      rw [List.replicate_succ, List.cons_append]
      show icast 0 + x * pevalR (List.replicate m 0 ++ tail) x = npow x m * x * pevalR tail x
      rw [pevalR_replicate_append x m tail, icast_zero, VRing.zero_add]; ac_rfl

theorem pevalR_pmono (x : R) (m : Nat) : pevalR (pmono m) x = npow x m := by
  unfold pmono
  rw [pevalR_replicate_append]
  show npow x m * (icast 1 + x * 𝟘) = _
  rw [icast_one, mul_zero, add_zero, mul_one]

theorem pevalR_oneMinusQ (x : R) : ∀ k, 1 ≤ k → pevalR (oneMinusQ k) x = 𝟙 - npow x k
  | 0, h => absurd h (by decide)
  | k + 1, _ => by
      show icast 1 + x * pevalR (List.replicate k 0 ++ [-1]) x = 𝟙 - npow x k * x
      rw [pevalR_replicate_append]
      show icast 1 + x * (npow x k * (icast (-1) + x * 𝟘)) = _
      rw [icast_one, icast_neg_one, mul_zero, add_zero, mul_neg, mul_neg, mul_one, sub_def,
        VRing.mul_comm x (npow x k)]

/-- `∏ (1 - x^k)^mult` in `R`. -/
def facProdR (x : R) : List (Nat × Nat) → R
  | [] => 𝟙
  | f :: fs => npow (𝟙 - npow x f.1) f.2 * facProdR x fs

theorem pevalR_foldl (x : R) : ∀ (fs : List (Nat × Nat)) (acc : List Int), (∀ f ∈ fs, 1 ≤ f.1) →
    pevalR (fs.foldl (fun acc f => pmul acc (ppow (oneMinusQ f.1) f.2)) acc) x =
      pevalR acc x * facProdR x fs
  | [], acc, _ => (mul_one _).symm
  | f :: fs, acc, h => by
      simp only [List.foldl]
      rw [pevalR_foldl x fs _ (fun g hg => h g (List.mem_cons_of_mem _ hg)), pevalR_pmul,
        pevalR_ppow, pevalR_oneMinusQ x f.1 (h f (List.mem_cons_self _ _))]
      show _ = pevalR acc x * (npow (𝟙 - npow x f.1) f.2 * facProdR x fs)
      rw [VRing.mul_assoc]

/-- **Factorization semantics in any commutative ring:**
    `expandFac c m fs` evaluates to `c · x^m · ∏ (1 - x^k)^mult`. -/
theorem pevalR_expandFac (c : Int) (m : Nat) (fs : List (Nat × Nat)) (h : ∀ f ∈ fs, 1 ≤ f.1) (x : R) :
    pevalR (expandFac c m fs) x = icast c * npow x m * facProdR x fs := by
  unfold expandFac
  rw [pevalR_foldl x fs _ h, pevalR_pscale, pevalR_pmono]

/-! ### Instantiation with the two kernel-checked certificates (P33)

The energy-range facts below are evaluated by `decide` (1 + 7 + 28 + 84
profiles); all coefficient information comes from the P33 theorems
`Cert.*_agree_below` and `Cert.*_factorization`, not from new literals. -/

open Cert in
theorem spectral_energy_range (G : List (Nat × Nat)) (hG : G = spectralG ∨ G = spectralCmpG) :
    ∀ V, V ≤ 2 → ∀ a ∈ comps 7 V, 0 ≤ energy G a ∧ energy G a < 17 := by
  rcases hG with rfl | rfl <;> decide

open Cert in
theorem binary_energy_range (G : List (Nat × Nat)) (hG : G = binaryG ∨ G = binaryCmpG) :
    ∀ V, V ≤ 3 → ∀ a ∈ comps 7 V, 0 ≤ energy G a ∧ energy G a < 37 := by
  rcases hG with rfl | rfl <;> decide

theorem ell_zero_seven (E : List (Nat × Nat)) (hE : energy E [0, 0, 0, 0, 0, 0, 0] = 0) (q : R) :
    ell E 7 0 q = 𝟙 := by
  show psum q E (comps 7 0) = 𝟙
  rw [show comps 7 0 = [[0, 0, 0, 0, 0, 0, 0]] by decide]
  show npow q (energy E [0, 0, 0, 0, 0, 0, 0]).toNat + 𝟘 = 𝟙
  rw [hE, add_zero]; rfl

section Pairs
open Cert

/-- Spectral pair: `L_G`, `L_G'` have constant term `1` (at every `q`). -/
theorem spectral_const (q : R) : ell spectralG spectralN 0 q = 𝟙 ∧ ell spectralCmpG spectralN 0 q = 𝟙 :=
  ⟨ell_zero_seven _ (by decide) q, ell_zero_seven _ (by decide) q⟩

/-- Spectral pair: `ℓ_{G,V}(q) = ℓ_{G',V}(q)` for `V < 2`, in every commutative ring,
    from `Cert.spectral_agree_below`. -/
theorem spectral_agree (q : R) : ∀ V, V < spectralDiffVolume →
    ell spectralG spectralN V q = ell spectralCmpG spectralN V q := fun V hV =>
  ell_eq_of_counts q (spectral_energy_range _ (Or.inl rfl) V (by unfold spectralDiffVolume at hV; omega))
    (spectral_energy_range _ (Or.inr rfl) V (by unfold spectralDiffVolume at hV; omega))
    (Cert.spectral_agree_below V hV)

/-- Spectral pair: the first difference `ℓ_{G,2}(q) - ℓ_{G',2}(q) = 2 q^2 (1-q)^2 (1-q^2)`
    in every commutative ring, from `Cert.spectral_factorization`. -/
theorem spectral_delta (q : R) :
    ell spectralG spectralN spectralDiffVolume q - ell spectralCmpG spectralN spectralDiffVolume q =
      icast 2 * npow q 2 * (npow (𝟙 - npow q 1) 2 * (npow (𝟙 - npow q 2) 1 * 𝟙)) := by
  show ell spectralG 7 2 q - ell spectralCmpG 7 2 q = _
  rw [ell_sub_of_dense q (spectral_energy_range _ (Or.inl rfl) 2 (by decide))
    (spectral_energy_range _ (Or.inr rfl) 2 (by decide)) (by decide) Cert.spectral_factorization,
    pevalR_expandFac _ _ _ (by decide)]
  rfl

/-- **Spectral quotient law** (`r = 2`):
    `L_G / L_G' ≡ 1 + 2 q^2 (1-q)^2 (1-q^2) x^2 (mod x^3)`, in every commutative ring. -/
theorem spectral_quotient (q : R) :
    TruncEq 2 (conv (lseries spectralG spectralN q) (sinv (lseries spectralCmpG spectralN q)))
      (fun k => mono 𝟙 0 k +
        mono (icast 2 * npow q 2 * (npow (𝟙 - npow q 1) 2 * (npow (𝟙 - npow q 2) 1 * 𝟙))) 2 k) := by
  have h := quotient_first_discrepancy (lseries spectralG spectralN q) (lseries spectralCmpG spectralN q)
    spectralDiffVolume (spectral_const q).2 (spectral_agree q)
  rw [show lseries spectralG spectralN q spectralDiffVolume - lseries spectralCmpG spectralN q spectralDiffVolume
    = _ from spectral_delta q] at h
  exact h

/-- Spectral pair, logarithmic form: `x L_G'/L_G - x L_G''/L_G' ≡ 2 Δ x^2 (mod x^3)`. -/
theorem spectral_logDer (q : R) :
    TruncEq 2 (fun k => logDer (lseries spectralG spectralN q) k - logDer (lseries spectralCmpG spectralN q) k)
      (mono (ncast 2 * (icast 2 * npow q 2 * (npow (𝟙 - npow q 1) 2 * (npow (𝟙 - npow q 2) 1 * 𝟙)))) 2) := by
  have h := logDer_first_discrepancy (lseries spectralG spectralN q) (lseries spectralCmpG spectralN q)
    spectralDiffVolume (spectral_agree q)
  rw [show lseries spectralG spectralN q spectralDiffVolume - lseries spectralCmpG spectralN q spectralDiffVolume
    = _ from spectral_delta q] at h
  exact h

/-- Binary-census pair: constant terms. -/
theorem binary_const (q : R) : ell binaryG binaryN 0 q = 𝟙 ∧ ell binaryCmpG binaryN 0 q = 𝟙 :=
  ⟨ell_zero_seven _ (by decide) q, ell_zero_seven _ (by decide) q⟩

/-- Binary-census pair: agreement below volume `3`, from `Cert.binary_agree_below`. -/
theorem binary_agree (q : R) : ∀ V, V < binaryDiffVolume →
    ell binaryG binaryN V q = ell binaryCmpG binaryN V q := fun V hV =>
  ell_eq_of_counts q (binary_energy_range _ (Or.inl rfl) V (by unfold binaryDiffVolume at hV; omega))
    (binary_energy_range _ (Or.inr rfl) V (by unfold binaryDiffVolume at hV; omega))
    (Cert.binary_agree_below V hV)

/-- Binary-census pair: `ℓ_{G,3}(q) - ℓ_{G',3}(q) = q^3 (1-q) (1-q^3)^2 (1-q^4)^2`,
    from `Cert.binary_factorization`. -/
theorem binary_delta (q : R) :
    ell binaryG binaryN binaryDiffVolume q - ell binaryCmpG binaryN binaryDiffVolume q =
      icast 1 * npow q 3 *
        (npow (𝟙 - npow q 1) 1 * (npow (𝟙 - npow q 3) 2 * (npow (𝟙 - npow q 4) 2 * 𝟙))) := by
  show ell binaryG 7 3 q - ell binaryCmpG 7 3 q = _
  rw [ell_sub_of_dense q (binary_energy_range _ (Or.inl rfl) 3 (by decide))
    (binary_energy_range _ (Or.inr rfl) 3 (by decide)) (by decide) Cert.binary_factorization,
    pevalR_expandFac _ _ _ (by decide)]
  rfl

/-- **Binary-census quotient law** (`r = 3`):
    `L_G / L_G' ≡ 1 + q^3 (1-q) (1-q^3)^2 (1-q^4)^2 x^3 (mod x^4)`. -/
theorem binary_quotient (q : R) :
    TruncEq 3 (conv (lseries binaryG binaryN q) (sinv (lseries binaryCmpG binaryN q)))
      (fun k => mono 𝟙 0 k + mono (icast 1 * npow q 3 *
        (npow (𝟙 - npow q 1) 1 * (npow (𝟙 - npow q 3) 2 * (npow (𝟙 - npow q 4) 2 * 𝟙)))) 3 k) := by
  have h := quotient_first_discrepancy (lseries binaryG binaryN q) (lseries binaryCmpG binaryN q)
    binaryDiffVolume (binary_const q).2 (binary_agree q)
  rw [show lseries binaryG binaryN q binaryDiffVolume - lseries binaryCmpG binaryN q binaryDiffVolume
    = _ from binary_delta q] at h
  exact h

/-- Binary-census pair, logarithmic form. -/
theorem binary_logDer (q : R) :
    TruncEq 3 (fun k => logDer (lseries binaryG binaryN q) k - logDer (lseries binaryCmpG binaryN q) k)
      (mono (ncast 3 * (icast 1 * npow q 3 *
        (npow (𝟙 - npow q 1) 1 * (npow (𝟙 - npow q 3) 2 * (npow (𝟙 - npow q 4) 2 * 𝟙))))) 3) := by
  have h := logDer_first_discrepancy (lseries binaryG binaryN q) (lseries binaryCmpG binaryN q)
    binaryDiffVolume (binary_agree q)
  rw [show lseries binaryG binaryN q binaryDiffVolume - lseries binaryCmpG binaryN q binaryDiffVolume
    = _ from binary_delta q] at h
  exact h

end Pairs

/-! ## C. The analytic boundary (premises, NOT verified)

Core Lean 4.12 has no real numbers, limits, infinite products or zeta
function.  `RealFacts K` is therefore a list of explicit premises over an
abstract commutative ring `K` with uninterpreted operations.  The intended
reading is `K = ℝ`, with:

* `lt` the order, `inv` the reciprocal, `rpow x y = x^y` for `x > 0`,
  `pms p s = p^(-s)`, `zeta` the Riemann zeta function on `(1, ∞)`;
* `HasProdP f a`: all `f p > 0` for primes `p`, `Σ_p |log f p| < ∞`, and
  `∏_p f p = a` (so `a > 0`);
* `RightLim f a L`: `f s → L` as real `s ↓ a`;
* `Expands f F`: near `t = 0` (some radius `ρ > 0`), `f t = Σ_k F_k t^k`
  with absolute convergence;
* `Good f`: `f` is positive and continuous on the open interval `(0, 1)`.

Each field is a standard real-analysis fact under that reading; none mentions
a graph, the ratio product or its regularization.  The local inputs for a
particular pair (`Expands L_G (ℓ_{G,·}(q))`, `Good L_G`) are separate
hypotheses of `visibility_conditional`.  Nothing here constructs such a
model: the theorem is a verified implication from these premises, not a
verified analytic theorem. -/

/-- Standard real-analytic inputs, as hypotheses (see the section comment). -/
structure RealFacts (K : Type) [VRing K] where
  lt : K → K → Prop
  inv : K → K
  rpow : K → K → K
  pms : Nat → K → K
  zeta : K → K
  HasProdP : (Nat → K) → K → Prop
  RightLim : (K → K) → K → K → Prop
  Expands : (K → K) → (Nat → K) → Prop
  Good : (K → K) → Prop
  /-- Euler product for real zeta: `ζ(σ) = ∏_p (1 - p^(-σ))^(-1)` for real `σ > 1`. -/
  euler : ∀ σ, lt 𝟙 σ → HasProdP (fun p => inv (𝟙 - pms p σ)) (zeta σ)
  /-- Simple pole at `1` approached from the right: `(σ - 1) ζ(σ) → 1` as `σ ↓ 1`. -/
  pole : RightLim (fun σ => (σ - 𝟙) * zeta σ) 𝟙 𝟙
  /-- Products over primes: uniqueness, positivity, dependence only on primes. -/
  prod_unique : ∀ f a b, HasProdP f a → HasProdP f b → a = b
  prod_pos : ∀ f a, HasProdP f a → lt 𝟘 a
  prod_congr : ∀ f g a, (∀ p, 2 ≤ p → f p = g p) → HasProdP f a → HasProdP g a
  /-- Products of absolutely convergent positive products, and real powers of them. -/
  prod_mul : ∀ f g a b, HasProdP f a → HasProdP g b → HasProdP (fun p => f p * g p) (a * b)
  prod_rpow : ∀ f a δ, HasProdP f a → HasProdP (fun p => rpow (f p) δ) (rpow a δ)
  /-- Real powers of positive numbers. -/
  rpow_inv_cancel : ∀ y δ w, lt 𝟘 y → rpow (inv y) δ * (rpow y δ * w) = w
  rpow_mul : ∀ x y δ, lt 𝟘 x → lt 𝟘 y → rpow (x * y) δ = rpow x δ * rpow y δ
  rpow_one : ∀ δ, rpow 𝟙 δ = 𝟙
  /-- `(p^(-s))^r = p^(-rs)` and `0 < 1 - p^(-rs)` for primes and `rs > 1`. -/
  pms_pow : ∀ p r s, 2 ≤ p → npow (pms p s) r = pms p (ncast r * s)
  one_sub_pos : ∀ p r s, 2 ≤ p → 1 ≤ r → lt 𝟙 (ncast r * s) → lt 𝟘 (𝟙 - npow (pms p s) r)
  /-- Order facts on the real line. -/
  zero_lt_one : lt 𝟘 𝟙
  sub_pos : ∀ a b, lt a b → lt 𝟘 (b - a)
  scale_mono : ∀ (a b : Nat) s, a ≤ b → lt 𝟙 (ncast a * s) → lt 𝟙 (ncast b * s)
  scale_right : ∀ (r : Nat) s0 s, 1 ≤ r → ncast r * s0 = 𝟙 → lt s0 s → lt 𝟙 (ncast r * s)
  scale_succ : ∀ (r : Nat) s0, 1 ≤ r → ncast r * s0 = 𝟙 → lt 𝟙 (ncast (r + 1) * s0)
  /-- Right limits: products, continuity of `x ↦ x^δ` at `L > 0`, the
      substitution `σ = r s`, and local congruence. -/
  lim_mul : ∀ f g a L M, RightLim f a L → RightLim g a M → RightLim (fun s => f s * g s) a (L * M)
  lim_rpow : ∀ f a L δ, RightLim f a L → lt 𝟘 L → RightLim (fun s => rpow (f s) δ) a (rpow L δ)
  lim_scale : ∀ f (r : Nat) s0 L, 1 ≤ r → ncast r * s0 = 𝟙 → RightLim f 𝟙 L →
    RightLim (fun s => f (ncast r * s)) s0 L
  lim_congr : ∀ f g a L, (∀ s, lt a s → f s = g s) → RightLim f a L → RightLim g a L
  /-- Local power series: Cauchy products, reciprocals of series with constant
      term `1`, and the binomial expansion `(1 - t^r)^δ = 1 - δ t^r + O(t^(r+1))`. -/
  exp_mul : ∀ f g F G, Expands f F → Expands g G → Expands (fun t => f t * g t) (conv F G)
  exp_inv : ∀ f F, Expands f F → F 0 = 𝟙 → Expands (fun t => inv (f t)) (sinv F)
  exp_binom : ∀ (r : Nat) δ, 1 ≤ r → ∃ F, Expands (fun t => rpow (𝟙 - npow t r) δ) F ∧
    TruncEq r F (fun k => mono 𝟙 0 k + mono (-δ) r k)
  good_mul : ∀ f g, Good f → Good g → Good (fun t => f t * g t)
  good_inv : ∀ f, Good f → Good (fun t => inv (f t))
  good_binom : ∀ (r : Nat) δ, 1 ≤ r → Good (fun t => rpow (𝟙 - npow t r) δ)
  /-- **Product criterion** (summability of `Σ_p p^(-(m+1)s)` for `(m+1)s > 1`,
      the remainder estimate `|log f(t)| ≤ C t^(m+1)` near `0`, absolute
      convergence of the product, and local uniform convergence): if `f` is
      positive and continuous on `(0,1)` and `f(t) = 1 + O(t^(m+1))` as a
      convergent power series at `0`, then `∏_p f(p^(-s))` converges absolutely
      to a positive `P(s)` for real `(m+1)s > 1`, and `P` is continuous there. -/
  prod_crit : ∀ f F (m : Nat), Expands f F → Good f → F 0 = 𝟙 → (∀ k, 1 ≤ k → k ≤ m → F k = 𝟘) →
    ∃ P : K → K, (∀ s, lt 𝟙 (ncast (m + 1) * s) → HasProdP (fun p => f (pms p s)) (P s)) ∧
      (∀ s0, lt 𝟙 (ncast (m + 1) * s0) → RightLim P s0 (P s0))

/-- First discrepancy `δ = ℓ_{G,r}(q) - ℓ_{H,r}(q)`. -/
def firstDelta {K : Type} [VRing K] (G H : List (Nat × Nat)) (n r : Nat) (q : K) : K :=
  ell G n r q - ell H n r q

/-- **SNG-A11, conditional on `RealFacts`.**  Let the local series of `G`, `H`
    (on `n` vertices, at the parameter `q`) be real functions `LG`, `LH`,
    positive and continuous on `(0,1)` and given near `0` by their power series
    with coefficients `ℓ_{·,V}(q)`.  If `ℓ_{H,0}(q) = 1`, `r ≥ 1`, `r s0 = 1` and
    `ℓ_{G,V}(q) = ℓ_{H,V}(q)` for `V < r`, then, with `δ = ℓ_{G,r}(q) - ℓ_{H,r}(q)`,
    there are functions `R`, `Kr` with
    1. `R(s) = ∏_p L_G(p^(-s))/L_H(p^(-s))` (absolutely convergent) for real `rs > 1`;
    2. `Kr(s) = ∏_p (1 - p^(-rs))^δ L_G(p^(-s))/L_H(p^(-s))` for real `(r+1)s > 1`;
    3. `R(s) = ζ(rs)^δ Kr(s)` for real `rs > 1`;
    4. `Kr(1/r) > 0`;
    5. `(rs - 1)^δ R(s) → Kr(1/r)` as real `s ↓ 1/r`.
    The finite cancellation (Part A) supplies the expansion hypotheses of the
    product criterion; everything analytic is a `RealFacts` premise. -/
theorem visibility_conditional {K : Type} [VRing K] (M : RealFacts K)
    (G H : List (Nat × Nat)) (n r : Nat) (q s0 : K) (LG LH : K → K)
    (hexpG : M.Expands LG (lseries G n q)) (hexpH : M.Expands LH (lseries H n q))
    (hgoodG : M.Good LG) (hgoodH : M.Good LH)
    (hH0 : ell H n 0 q = 𝟙) (hr : 1 ≤ r) (hs0 : ncast r * s0 = 𝟙)
    (hagree : ∀ V, V < r → ell G n V q = ell H n V q) :
    ∃ Rf Kr : K → K,
      (∀ s, M.lt 𝟙 (ncast r * s) →
        M.HasProdP (fun p => LG (M.pms p s) * M.inv (LH (M.pms p s))) (Rf s)) ∧
      (∀ s, M.lt 𝟙 (ncast (r + 1) * s) →
        M.HasProdP (fun p => M.rpow (𝟙 - npow (M.pms p s) r) (firstDelta G H n r q) *
          (LG (M.pms p s) * M.inv (LH (M.pms p s)))) (Kr s)) ∧
      (∀ s, M.lt 𝟙 (ncast r * s) → Rf s = M.rpow (M.zeta (ncast r * s)) (firstDelta G H n r q) * Kr s) ∧
      M.lt 𝟘 (Kr s0) ∧
      M.RightLim (fun s => M.rpow (ncast r * s - 𝟙) (firstDelta G H n r q) * Rf s) s0 (Kr s0) := by
  -- formal input: the quotient series and its first-order term (Part A)
  have hquot := quotient_first_discrepancy (lseries G n q) (lseries H n q) r hH0 hagree
  have hexpQ := M.exp_mul _ _ _ _ hexpG (M.exp_inv _ _ hexpH hH0)
  have hgoodQ := M.good_mul _ _ hgoodG (M.good_inv _ hgoodH)
  have hQ0 : conv (lseries G n q) (sinv (lseries H n q)) 0 = 𝟙 := by
    rw [hquot 0 (Nat.zero_le _)]
    show mono 𝟙 0 0 + mono _ r 0 = 𝟙
    rw [mono_self, mono_ne _ (by omega), add_zero]
  -- the ratio product, from the product criterion with `m + 1 = r`
  obtain ⟨Rf, hRf, _⟩ := M.prod_crit _ _ (r - 1) hexpQ hgoodQ hQ0 (fun k h1 hk => by
    rw [hquot k (by omega)]
    show mono 𝟙 0 k + mono _ r k = 𝟘
    rw [mono_ne _ (by omega), mono_ne _ (by omega), add_zero])
  rw [Nat.sub_add_cancel hr] at hRf
  -- the regularized product: the binomial factor cancels the first discrepancy
  obtain ⟨Fb, hexpB, hFb⟩ := M.exp_binom r (firstDelta G H n r q) hr
  have hcan := binom_cancel Fb (conv (lseries G n q) (sinv (lseries H n q))) r
    (firstDelta G H n r q) hr hFb hquot
  obtain ⟨Kr, hKr, hKcont⟩ := M.prod_crit _ _ r (M.exp_mul _ _ _ _ hexpB hexpQ)
    (M.good_mul _ _ (M.good_binom r _ hr) hgoodQ)
    (by rw [hcan 0 (Nat.zero_le _)]; exact mono_self _ _)
    (fun k h1 hk => by rw [hcan k hk]; exact mono_ne _ (by omega))
  -- factorization through the Euler product
  have hfac : ∀ s, M.lt 𝟙 (ncast r * s) →
      Rf s = M.rpow (M.zeta (ncast r * s)) (firstDelta G H n r q) * Kr s := by
    intro s hs
    have hK := hKr s (M.scale_mono r (r + 1) s (by omega) hs)
    have hZ := M.prod_rpow _ _ (firstDelta G H n r q) (M.euler _ hs)
    have hM := M.prod_mul _ _ _ _ hZ hK
    have hM' := M.prod_congr _ (fun p => LG (M.pms p s) * M.inv (LH (M.pms p s))) _ (fun p hp => by
      show M.rpow (M.inv (𝟙 - M.pms p (ncast r * s))) _ * (M.rpow (𝟙 - npow (M.pms p s) r) _ * _) = _
      rw [← M.pms_pow p r s hp]
      exact M.rpow_inv_cancel _ _ _ (M.one_sub_pos p r s hp hr hs)) hM
    exact M.prod_unique _ _ _ (hRf s hs) hM'
  have hs0' := M.scale_succ r s0 hr hs0
  refine ⟨Rf, Kr, hRf, hKr, hfac, M.prod_pos _ _ (hKr s0 hs0'), ?_⟩
  -- the positive-real asymptotic from the right-hand simple pole
  have h1 := M.lim_scale _ r s0 𝟙 hr hs0 M.pole
  have h2 := M.lim_rpow _ _ _ (firstDelta G H n r q) h1 M.zero_lt_one
  rw [M.rpow_one] at h2
  have h3 := M.lim_mul _ _ _ _ _ h2 (hKcont s0 hs0')
  rw [VRing.one_mul] at h3
  refine M.lim_congr _ _ _ _ (fun s hs => ?_) h3
  have hrs := M.scale_right r s0 s hr hs0 hs
  show M.rpow ((ncast r * s - 𝟙) * M.zeta (ncast r * s)) _ * Kr s = M.rpow (ncast r * s - 𝟙) _ * Rf s
  rw [M.rpow_mul _ _ _ (M.sub_pos _ _ hrs) (M.prod_pos _ _ (M.euler _ hrs)), hfac s hrs, VRing.mul_assoc]

/-- The premises are not contradictory: a degenerate one-point model satisfies
    them.  (It says nothing about `ℝ`; it only shows that `visibility_conditional`
    is not vacuous by inconsistency of `RealFacts`.) -/
instance : VRing Unit where
  add _ _ := ()
  mul _ _ := ()
  neg _ := ()
  zero := ()
  one := ()
  add_assoc _ _ _ := rfl
  add_comm _ _ := rfl
  zero_add _ := rfl
  neg_add _ := rfl
  mul_assoc _ _ _ := rfl
  mul_comm _ _ := rfl
  one_mul _ := rfl
  mul_add _ _ _ := rfl

def unitFacts : RealFacts Unit where
  lt _ _ := True
  inv _ := ()
  rpow _ _ := ()
  pms _ _ := ()
  zeta _ := ()
  HasProdP _ _ := True
  RightLim _ _ _ := True
  Expands _ _ := True
  Good _ := True
  euler _ _ := trivial
  pole := trivial
  prod_unique _ _ _ _ _ := rfl
  prod_pos _ _ _ := trivial
  prod_congr _ _ _ _ _ := trivial
  prod_mul _ _ _ _ _ _ := trivial
  prod_rpow _ _ _ _ := trivial
  rpow_inv_cancel _ _ _ _ := rfl
  rpow_mul _ _ _ _ _ := rfl
  rpow_one _ := rfl
  pms_pow _ _ _ _ := rfl
  one_sub_pos _ _ _ _ _ _ := trivial
  zero_lt_one := trivial
  sub_pos _ _ _ := trivial
  scale_mono _ _ _ _ _ := trivial
  scale_right _ _ _ _ _ _ := trivial
  scale_succ _ _ _ _ := trivial
  lim_mul _ _ _ _ _ _ _ := trivial
  lim_rpow _ _ _ _ _ _ := trivial
  lim_scale _ _ _ _ _ _ _ := trivial
  lim_congr _ _ _ _ _ _ := trivial
  exp_mul _ _ _ _ _ _ := trivial
  exp_inv _ _ _ _ := trivial
  exp_binom _ _ _ := ⟨fun _ => (), trivial, fun _ _ => rfl⟩
  good_mul _ _ _ _ := trivial
  good_inv _ _ := trivial
  good_binom _ _ _ := trivial
  prod_crit _ _ _ _ _ _ _ := ⟨fun _ => (), fun _ _ => trivial, fun _ _ => trivial⟩

theorem realFacts_consistent : Nonempty (RealFacts Unit) := ⟨unitFacts⟩

section Pairs
open Cert

/-- **Spectral pair, conditional asymptotic** (`r = 2`, `s0 = 1/2`):
    with `Δ = 2 q^2 (1-q)^2 (1-q^2)` (kernel-checked, `spectral_delta`),
    `R(s) = ζ(2s)^Δ Kr(s)` for real `2s > 1` and `(2s - 1)^Δ R(s) → Kr(1/2) > 0` as `s ↓ 1/2`,
    under `RealFacts` and the local analytic inputs for `L_G`, `L_G'`. -/
theorem spectral_visibility_conditional {K : Type} [VRing K] (M : RealFacts K) (q s0 : K) (LG LH : K → K)
    (hexpG : M.Expands LG (lseries spectralG spectralN q)) (hexpH : M.Expands LH (lseries spectralCmpG spectralN q))
    (hgoodG : M.Good LG) (hgoodH : M.Good LH) (hs0 : ncast 2 * s0 = 𝟙) :
    let Δ : K := icast 2 * npow q 2 * (npow (𝟙 - npow q 1) 2 * (npow (𝟙 - npow q 2) 1 * 𝟙))
    ∃ Rf Kr : K → K,
      (∀ s, M.lt 𝟙 (ncast 2 * s) →
        M.HasProdP (fun p => LG (M.pms p s) * M.inv (LH (M.pms p s))) (Rf s)) ∧
      (∀ s, M.lt 𝟙 (ncast 3 * s) →
        M.HasProdP (fun p => M.rpow (𝟙 - npow (M.pms p s) 2) Δ * (LG (M.pms p s) * M.inv (LH (M.pms p s)))) (Kr s)) ∧
      (∀ s, M.lt 𝟙 (ncast 2 * s) → Rf s = M.rpow (M.zeta (ncast 2 * s)) Δ * Kr s) ∧
      M.lt 𝟘 (Kr s0) ∧
      M.RightLim (fun s => M.rpow (ncast 2 * s - 𝟙) Δ * Rf s) s0 (Kr s0) := by
  have h := visibility_conditional M spectralG spectralCmpG spectralN spectralDiffVolume q s0 LG LH
    hexpG hexpH hgoodG hgoodH (spectral_const q).2 (by decide) hs0 (spectral_agree q)
  have hd : firstDelta spectralG spectralCmpG spectralN spectralDiffVolume q = _ := spectral_delta q
  rw [hd] at h
  exact h

/-- **Binary-census pair, conditional asymptotic** (`r = 3`, `s0 = 1/3`):
    with `Δ = q^3 (1-q) (1-q^3)^2 (1-q^4)^2` (kernel-checked, `binary_delta`). -/
theorem binary_visibility_conditional {K : Type} [VRing K] (M : RealFacts K) (q s0 : K) (LG LH : K → K)
    (hexpG : M.Expands LG (lseries binaryG binaryN q)) (hexpH : M.Expands LH (lseries binaryCmpG binaryN q))
    (hgoodG : M.Good LG) (hgoodH : M.Good LH) (hs0 : ncast 3 * s0 = 𝟙) :
    let Δ : K := icast 1 * npow q 3 *
      (npow (𝟙 - npow q 1) 1 * (npow (𝟙 - npow q 3) 2 * (npow (𝟙 - npow q 4) 2 * 𝟙)))
    ∃ Rf Kr : K → K,
      (∀ s, M.lt 𝟙 (ncast 3 * s) →
        M.HasProdP (fun p => LG (M.pms p s) * M.inv (LH (M.pms p s))) (Rf s)) ∧
      (∀ s, M.lt 𝟙 (ncast 4 * s) →
        M.HasProdP (fun p => M.rpow (𝟙 - npow (M.pms p s) 3) Δ * (LG (M.pms p s) * M.inv (LH (M.pms p s)))) (Kr s)) ∧
      (∀ s, M.lt 𝟙 (ncast 3 * s) → Rf s = M.rpow (M.zeta (ncast 3 * s)) Δ * Kr s) ∧
      M.lt 𝟘 (Kr s0) ∧
      M.RightLim (fun s => M.rpow (ncast 3 * s - 𝟙) Δ * Rf s) s0 (Kr s0) := by
  have h := visibility_conditional M binaryG binaryCmpG binaryN binaryDiffVolume q s0 LG LH
    hexpG hexpH hgoodG hgoodH (binary_const q).2 (by decide) hs0 (binary_agree q)
  have hd : firstDelta binaryG binaryCmpG binaryN binaryDiffVolume q = _ := binary_delta q
  rw [hd] at h
  exact h

end Pairs

end Vis
end Singularity
