/-
  Singularity.Thresholds  (roadmap push P08)

  Threshold sets `S_r = {v : a_v ≥ r}` (r ≥ 1) of a nonnegative height profile and the
  nested-level form of the squared-difference energy, in core Lean 4 (no Mathlib).

  Conventions are those of `Singularity.Normalization`: profiles are `List Nat`, vertices
  are indices, edges are `List (Nat × Nat)`, and an edge with an out-of-range endpoint
  contributes `0`.  Levels are summed over `r = 1, …, M` for any `M ≥ max a`; repeated
  threshold sets (height gaps) are allowed and no strict nesting is assumed anywhere.

  No `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by` or `unsafe` is used.
-/
import Singularity.Normalization

namespace Singularity

/-! ## Maximum -/

/-- Maximum of a profile (`0` for the empty list). -/
def lmax : List Nat → Nat
  | [] => 0
  | x :: xs => max x (lmax xs)

theorem le_lmax : ∀ (a : List Nat) (x : Nat), x ∈ a → x ≤ lmax a
  | [], x, h => absurd h (List.not_mem_nil x)
  | y :: ys, x, h => by
      simp only [lmax]
      rcases List.mem_cons.mp h with h | h
      · omega
      · have := le_lmax ys x h; omega

theorem lmax_le_iff : ∀ (a : List Nat) (M : Nat), lmax a ≤ M ↔ ∀ x ∈ a, x ≤ M
  | [], M => by simp [lmax]
  | y :: ys, M => by
      have ih := lmax_le_iff ys M
      simp only [lmax, List.mem_cons, forall_eq_or_imp]
      constructor
      · intro h; exact ⟨by omega, ih.mp (by omega)⟩
      · rintro ⟨h1, h2⟩; have := ih.mpr h2; omega

/-- `r ≤ max a` iff some height is at least `r` (for `r ≥ 1`). -/
theorem exists_ge_iff (a : List Nat) (r : Nat) (hr : 1 ≤ r) : (∃ x ∈ a, r ≤ x) ↔ r ≤ lmax a := by
  constructor
  · rintro ⟨x, hx, h⟩; have := le_lmax a x hx; omega
  · intro h
    apply Classical.byContradiction
    intro hn
    have : lmax a ≤ r - 1 := (lmax_le_iff a (r - 1)).mpr (fun x hx => by
      have : ¬ r ≤ x := fun h' => hn ⟨x, hx, h'⟩
      omega)
    omega

theorem lmax_map_sub (m : Nat) : ∀ (a : List Nat), lmax (a.map (· - m)) = lmax a - m
  | [] => by simp [lmax]
  | x :: xs => by
      have ih := lmax_map_sub m xs
      simp only [List.map, lmax] at ih ⊢
      rw [ih]; omega

/-- `max (a - min a) = max a - min a`. -/
theorem lmax_norm (a : List Nat) : lmax (norm a) = lmax a - lmin a := lmax_map_sub _ a

/-! ## Threshold sets -/

/-- `inThr a r v` : vertex `v` lies in `S_r = {v : a_v ≥ r}`. -/
def inThr (a : List Nat) (r v : Nat) : Bool :=
  match a[v]? with
  | some x => decide (r ≤ x)
  | none => false

/-- The threshold set `S_r` as the increasing list of its vertices. -/
def thr (a : List Nat) (r : Nat) : List Nat := (List.range a.length).filter (inThr a r)

/-- `|S_r|`, counted on heights. -/
def thrCard (a : List Nat) (r : Nat) : Nat := (a.filter (fun x => decide (r ≤ x))).length

theorem mem_thr (a : List Nat) (r v : Nat) : v ∈ thr a r ↔ v < a.length ∧ inThr a r v = true := by
  unfold thr; rw [List.mem_filter, List.mem_range]

/-- The vertex list `thr a r` has `thrCard a r` elements. -/
theorem thr_length : ∀ (a : List Nat) (r : Nat), (thr a r).length = thrCard a r
  | [], _ => rfl
  | x :: xs, r => by
      have ih := thr_length xs r
      unfold thr thrCard at *
      rw [List.length_cons, List.range_succ_eq_map, List.filter_cons, List.filter_map]
      have hc : (inThr (x :: xs) r ∘ Nat.succ) = inThr xs r := by
        funext i; simp [Function.comp, inThr]
      have h0 : inThr (x :: xs) r 0 = decide (r ≤ x) := by simp [inThr]
      rw [hc, h0, List.filter_cons]
      by_cases h : r ≤ x <;> simp [h, ih]

/-- Nesting: `S_s ⊆ S_r` whenever `r ≤ s` (in particular `S_{r+1} ⊆ S_r`). -/
theorem thr_nested (a : List Nat) (r s v : Nat) (hrs : r ≤ s) (h : v ∈ thr a s) : v ∈ thr a r := by
  rw [mem_thr] at h ⊢
  refine ⟨h.1, ?_⟩
  revert h
  unfold inThr
  cases a[v]? with
  | none => simp
  | some x => simp only [decide_eq_true_eq]; intro h; omega

theorem thr_succ_subset (a : List Nat) (r v : Nat) (h : v ∈ thr a (r + 1)) : v ∈ thr a r :=
  thr_nested a r (r + 1) v (Nat.le_succ r) h

/-! ## Sums over levels `r = 1, …, M` -/

/-- `rsum M f = f 1 + ⋯ + f M`. -/
def rsum : Nat → (Nat → Int) → Int
  | 0, _ => 0
  | M + 1, f => rsum M f + f (M + 1)

theorem rsum_congr (f g : Nat → Int) : ∀ M, (∀ r, 1 ≤ r → r ≤ M → f r = g r) → rsum M f = rsum M g
  | 0, _ => rfl
  | M + 1, h => by
      simp only [rsum]
      rw [rsum_congr f g M (fun r h1 h2 => h r h1 (by omega)), h (M + 1) (by omega) (Nat.le_refl _)]

theorem rsum_add (f g : Nat → Int) : ∀ M, rsum M (fun r => f r + g r) = rsum M f + rsum M g
  | 0 => by simp [rsum]
  | M + 1 => by simp only [rsum]; rw [rsum_add f g M]; omega

theorem rsum_sub (f g : Nat → Int) : ∀ M, rsum M (fun r => f r - g r) = rsum M f - rsum M g
  | 0 => by simp [rsum]
  | M + 1 => by simp only [rsum]; rw [rsum_sub f g M]; omega

theorem rsum_zero : ∀ M, rsum M (fun _ => 0) = 0
  | 0 => rfl
  | M + 1 => by simp only [rsum]; rw [rsum_zero M]; rfl

theorem rsum_mul_left (c : Int) (f : Nat → Int) : ∀ M, rsum M (fun r => c * f r) = c * rsum M f
  | 0 => by simp [rsum]
  | M + 1 => by simp only [rsum]; rw [rsum_mul_left c f M, Int.mul_add]

theorem rsum_mul_right (c : Int) (f : Nat → Int) : ∀ M, rsum M (fun r => f r * c) = rsum M f * c
  | 0 => by simp [rsum]
  | M + 1 => by simp only [rsum]; rw [rsum_mul_right c f M, Int.add_mul]

/-- Level indicator `[r ≤ x]`. -/
def ind (r x : Nat) : Int := if r ≤ x then 1 else 0

/-- `Σ_{r=1}^M [r ≤ x] = min M x`. -/
theorem rsum_ind (x : Nat) : ∀ M, rsum M (fun r => ind r x) = (min M x : Nat)
  | 0 => by simp [rsum]
  | M + 1 => by
      simp only [rsum]
      rw [rsum_ind x M]
      unfold ind
      by_cases h : M + 1 ≤ x
      · rw [if_pos h]; omega
      · rw [if_neg h]; omega

/-- Height reconstruction for a number: `x = #{r ∈ 1..M : r ≤ x}` when `x ≤ M`. -/
theorem height_eq_levels (x M : Nat) (h : x ≤ M) : rsum M (fun r => ind r x) = x := by
  rw [rsum_ind]; congr 1; omega

/-- **Reconstruction**: for every vertex `v` of height `a_v`,
    `a_v = #{r ∈ 1..M : v ∈ S_r}` for any `M ≥ max a`. -/
theorem reconstruct (a : List Nat) (M : Nat) (hM : lmax a ≤ M) (v x : Nat) (hv : a[v]? = some x) :
    rsum M (fun r => if inThr a r v then 1 else 0) = x := by
  have hx : x ≤ M := Nat.le_trans (le_lmax a x (List.getElem?_mem hv)) hM
  rw [← height_eq_levels x M hx]
  apply rsum_congr
  intro r _ _
  simp [inThr, hv, ind]

theorem thrCard_cons (x : Nat) (xs : List Nat) (r : Nat) :
    (thrCard (x :: xs) r : Int) = ind r x + thrCard xs r := by
  unfold thrCard ind
  rw [List.filter_cons]
  by_cases h : r ≤ x <;> simp [h] <;> omega

/-- **Volume by levels**: `Σ_v a_v = Σ_{r=1}^M |S_r|` for any `M ≥ max a`. -/
theorem vol_eq_levels : ∀ (a : List Nat) (M : Nat), lmax a ≤ M → (vol a : Int) = rsum M (fun r => (thrCard a r : Int))
  | [], M, _ => by
      show (0 : Int) = _
      exact ((rsum_congr (fun r => ((thrCard [] r : Nat) : Int)) (fun _ => 0) M
        (fun r _ _ => rfl)).trans (rsum_zero M)).symm
  | x :: xs, M, hM => by
      have hM' := (lmax_le_iff (x :: xs) M).mp hM
      have ih := vol_eq_levels xs M ((lmax_le_iff xs M).mpr (fun y hy => hM' y (List.mem_cons_of_mem _ hy)))
      rw [rsum_congr _ (fun r => ind r x + thrCard xs r) M (fun r _ _ => thrCard_cons x xs r),
        rsum_add, ← ih, height_eq_levels x M (hM' x (List.mem_cons_self _ _))]
      simp only [vol]; omega

/-! ## Span -/

/-- `S_r` (for `r ≥ 1`) is nonempty iff `r ≤ max a`. -/
theorem thrCard_pos_iff (a : List Nat) (r : Nat) (hr : 1 ≤ r) : 0 < thrCard a r ↔ r ≤ lmax a := by
  rw [← exists_ge_iff a r hr]
  unfold thrCard
  constructor
  · intro h
    obtain ⟨x, hx⟩ := List.exists_mem_of_length_pos h
    rw [List.mem_filter, decide_eq_true_eq] at hx
    exact ⟨x, hx⟩
  · rintro ⟨x, hx, h⟩
    exact List.length_pos_of_mem (List.mem_filter.mpr ⟨hx, by simpa using h⟩)

/-- Number of nonempty threshold sets among `S_1, …, S_M`. -/
def nonemptyLevels (a : List Nat) (M : Nat) : Int :=
  rsum M (fun r => if 0 < thrCard a r then 1 else 0)

/-- The number of nonempty threshold sets is `max a` (for `M ≥ max a`).
    In particular `max a = 0` gives no nonempty threshold set. -/
theorem nonemptyLevels_eq_lmax (a : List Nat) (M : Nat) (hM : lmax a ≤ M) :
    nonemptyLevels a M = lmax a := by
  unfold nonemptyLevels
  rw [rsum_congr _ (fun r => ind r (lmax a)) M (fun r hr _ => by
    unfold ind
    dsimp only
    by_cases h : r ≤ lmax a
    · rw [if_pos h, if_pos ((thrCard_pos_iff a r hr).mpr h)]
    · rw [if_neg h, if_neg (fun h' => h ((thrCard_pos_iff a r hr).mp h'))])]
  exact height_eq_levels _ M hM

/-- **Span**: after P07 normalization, the number of nonempty threshold sets of
    `a - min a` is `max a - min a`. -/
theorem span_eq (a : List Nat) (M : Nat) (hM : lmax a ≤ M) :
    nonemptyLevels (norm a) M = (lmax a - lmin a : Nat) := by
  rw [nonemptyLevels_eq_lmax (norm a) M (by rw [lmax_norm]; omega), lmax_norm]

theorem maxZero_no_levels (a : List Nat) (h : lmax a = 0) (r : Nat) (hr : 1 ≤ r) : thrCard a r = 0 := by
  have := thrCard_pos_iff a r hr
  omega

private theorem filter_length_lt {α : Type} (p : α → Bool) :
    ∀ (l : List α), (∃ x ∈ l, p x = false) → (l.filter p).length < l.length
  | [], ⟨_, h, _⟩ => absurd h (List.not_mem_nil _)
  | y :: ys, ⟨x, hx, hp⟩ => by
      rw [List.filter_cons]
      rcases List.mem_cons.mp hx with e | e
      · subst e; simp only [hp]
        have := List.length_filter_le p ys
        simp; omega
      · have := filter_length_lt p ys ⟨x, e, hp⟩
        split <;> simp <;> omega

/-- For a minimum-zero profile, each `S_r` with `r ≥ 1` is a proper subset. -/
theorem thr_proper_of_minZero (b : List Nat) (hb : MinZero b) (r : Nat) (hr : 1 ≤ r) :
    thrCard b r < b.length :=
  filter_length_lt _ b ⟨0, hb, by simp; omega⟩

/-! ## Edgewise squared-difference identity -/

/-- Signed threshold difference `δ_r = [a_u ≥ r] - [a_v ≥ r] ∈ {-1, 0, 1}`. -/
def delta (r x y : Nat) : Int := ind r x - ind r y

/-- Boundary of `S_r` is crossed by the edge. -/
def cutInd (r x y : Nat) : Int := if (r ≤ x ∧ y < r) ∨ (r ≤ y ∧ x < r) then 1 else 0

/-- For `r < s`: the edge joins the deeper set `S_s` to the complement of the shallower `S_r`. -/
def crossInd (r s x y : Nat) : Int := if (s ≤ x ∧ y < r) ∨ (s ≤ y ∧ x < r) then 1 else 0

theorem sq_eq_mul (d : Int) : d ^ 2 = d * d := by simp [Int.pow_succ, Int.pow_zero]

/-- `(x - y)^2 = Σ_{r,s=1}^M δ_r δ_s` for `x, y ≤ M`. -/
theorem edge_square (x y M : Nat) (hx : x ≤ M) (hy : y ≤ M) :
    sqd x y = rsum M (fun r => rsum M (fun s => delta r x y * delta s x y)) := by
  have hd : rsum M (fun r => delta r x y) = (x : Int) - y := by
    unfold delta
    rw [rsum_sub, height_eq_levels x M hx, height_eq_levels y M hy]
  rw [rsum_congr _ (fun r => delta r x y * rsum M (fun s => delta s x y)) M
      (fun r _ _ => rsum_mul_left _ _ M),
    rsum_mul_right, hd]
  unfold sqd
  exact sq_eq_mul _

/-- **Sign agreement**: for `r ≤ s`, `δ_r δ_s` is `1` exactly when the edge joins `S_s`
    to the complement of `S_r`, and `0` otherwise (never `-1`). -/
theorem delta_mul (r s x y : Nat) (hrs : r ≤ s) : delta r x y * delta s x y = crossInd r s x y := by
  unfold delta ind crossInd
  by_cases h1 : r ≤ x <;> by_cases h2 : r ≤ y <;> by_cases h3 : s ≤ x <;> by_cases h4 : s ≤ y <;>
    simp [h1, h2, h3, h4] <;> omega

theorem delta_sq (r x y : Nat) : delta r x y * delta r x y = cutInd r x y := by
  rw [delta_mul r r x y (Nat.le_refl r)]; rfl

/-- Symmetric double sum = diagonal + 2 × strictly ordered part. -/
theorem rsum_sym (g : Nat → Nat → Int) (hg : ∀ r s, g r s = g s r) : ∀ M,
    rsum M (fun r => rsum M (fun s => g r s)) =
      rsum M (fun r => g r r) + 2 * rsum M (fun s => rsum (s - 1) (fun r => g r s))
  | 0 => by simp [rsum]
  | M + 1 => by
      have ih := rsum_sym g hg M
      have e1 : rsum (M + 1) (fun r => rsum (M + 1) (fun s => g r s)) =
          rsum M (fun r => rsum M (fun s => g r s)) + rsum M (fun r => g r (M + 1)) +
            (rsum M (fun s => g (M + 1) s) + g (M + 1) (M + 1)) := by
        simp only [rsum]
        rw [rsum_add]
      have e2 : rsum M (fun s => g (M + 1) s) = rsum M (fun r => g r (M + 1)) :=
        rsum_congr _ _ M (fun r _ _ => hg _ _)
      rw [e1, e2, ih]
      simp only [rsum, Nat.add_sub_cancel]
      omega

/-- **Nested edge identity**: for `x, y ≤ M`,
    `(x - y)^2 = Σ_{r=1}^M [edge crosses ∂S_r] + 2 Σ_{1 ≤ r < s ≤ M} [edge joins S_s to S_rᶜ]`. -/
theorem edge_nested (x y M : Nat) (hx : x ≤ M) (hy : y ≤ M) :
    sqd x y = rsum M (fun r => cutInd r x y) +
      2 * rsum M (fun s => rsum (s - 1) (fun r => crossInd r s x y)) := by
  rw [edge_square x y M hx hy,
    rsum_sym (fun r s => delta r x y * delta s x y) (fun r s => Int.mul_comm _ _) M]
  congr 1
  · exact rsum_congr _ _ M (fun r _ _ => delta_sq r x y)
  · congr 1
    apply rsum_congr
    intro s _ _
    apply rsum_congr
    intro r _ hr
    exact delta_mul r s x y (by omega)

/-! ## Summing over edges -/

theorem esum_add (a : List Nat) (F G : Nat → Nat → Int) : ∀ E : List (Nat × Nat),
    esum a (fun x y => F x y + G x y) E = esum a F E + esum a G E
  | [] => rfl
  | e :: es => by
      simp only [esum]
      rw [esum_add a F G es]
      unfold edgeVal
      cases a[e.1]? <;> cases a[e.2]? <;> simp <;> omega

theorem esum_mul (a : List Nat) (c : Int) (F : Nat → Nat → Int) : ∀ E : List (Nat × Nat),
    esum a (fun x y => c * F x y) E = c * esum a F E
  | [] => by simp [esum]
  | e :: es => by
      simp only [esum]
      rw [esum_mul a c F es, Int.mul_add]
      unfold edgeVal
      cases a[e.1]? <;> cases a[e.2]? <;> simp

theorem esum_rsum (a : List Nat) (M : Nat) (F : Nat → Nat → Nat → Int) : ∀ E : List (Nat × Nat),
    esum a (fun x y => rsum M (fun r => F r x y)) E = rsum M (fun r => esum a (F r) E)
  | [] => by simp only [esum]; exact (rsum_zero M).symm
  | e :: es => by
      simp only [esum]
      rw [esum_rsum a M F es, rsum_add (fun r => edgeVal a (F r) e) (fun r => esum a (F r) es)]
      congr 1
      unfold edgeVal
      cases a[e.1]? <;> cases a[e.2]? <;> simp [rsum_zero]

/-- `esum` only depends on the two-point function at heights occurring in `a`. -/
theorem esum_congr (a : List Nat) (F G : Nat → Nat → Int)
    (h : ∀ x y, x ∈ a → y ∈ a → F x y = G x y) : ∀ E : List (Nat × Nat), esum a F E = esum a G E
  | [] => rfl
  | e :: es => by
      simp only [esum]
      rw [esum_congr a F G h es]
      congr 1
      unfold edgeVal
      cases h1 : a[e.1]? <;> cases h2 : a[e.2]? <;> simp
      exact h _ _ (List.getElem?_mem h1) (List.getElem?_mem h2)

/-- Cut size of `S_r`: number of edges with exactly one endpoint in `S_r`. -/
def cutSize (E : List (Nat × Nat)) (a : List Nat) (r : Nat) : Int := esum a (cutInd r) E

/-- Number of edges joining `S_s` to the complement of `S_r`. -/
def crossCount (E : List (Nat × Nat)) (a : List Nat) (r s : Nat) : Int := esum a (crossInd r s) E

/-- **Nested-level energy identity** (P08): for every edge list and every profile `a`,
    and any `M ≥ max a`,
    `E_G(a) = Σ_{r=1}^M cut(S_r) + 2 Σ_{1 ≤ r < s ≤ M} #{uv : one endpoint in S_s, the other ∉ S_r}`.
    Repeated threshold sets and height gaps are allowed. -/
theorem energy_nested (E : List (Nat × Nat)) (a : List Nat) (M : Nat) (hM : lmax a ≤ M) :
    energy E a = rsum M (fun r => cutSize E a r) +
      2 * rsum M (fun s => rsum (s - 1) (fun r => crossCount E a r s)) := by
  have hle : ∀ x, x ∈ a → x ≤ M := (lmax_le_iff a M).mp hM
  unfold energy
  rw [esum_congr a sqd (fun x y => rsum M (fun r => cutInd r x y) +
      2 * rsum M (fun s => rsum (s - 1) (fun r => crossInd r s x y)))
      (fun x y hx hy => edge_nested x y M (hle x hx) (hle y hy)) E,
    esum_add, esum_mul, esum_rsum, esum_rsum]
  unfold cutSize crossCount
  congr 2
  apply rsum_congr
  intro s _ _
  exact esum_rsum a (s - 1) (fun r x y => crossInd r s x y) E

/-! ## Binary sector -/

/-- Profiles with all heights `≤ 1`: energy is the cut size of `S_1`. -/
theorem energy_binary (E : List (Nat × Nat)) (a : List Nat) (h : ∀ x ∈ a, x ≤ 1) :
    energy E a = cutSize E a 1 := by
  unfold energy cutSize
  apply esum_congr
  intro x y hx hy
  have hx' := h x hx
  have hy' := h y hy
  have : (x = 0 ∨ x = 1) ∧ (y = 0 ∨ y = 1) := by omega
  rcases this with ⟨rfl | rfl, rfl | rfl⟩ <;> rfl

/-- Binary minimum-zero profiles split into the all-zero profile (no nonempty level,
    energy `0`) and exact-span-one profiles (exactly one nonempty level `S_1`, which is a
    nonempty proper subset, and energy = cut size of `S_1`). -/
theorem binary_dichotomy (E : List (Nat × Nat)) (b : List Nat) (hb : MinZero b) (h : ∀ x ∈ b, x ≤ 1) :
    (lmax b = 0 ∧ (∀ x ∈ b, x = 0) ∧ energy E b = 0 ∧ nonemptyLevels b 1 = 0) ∨
    (lmax b = 1 ∧ 0 < thrCard b 1 ∧ thrCard b 1 < b.length ∧ nonemptyLevels b 1 = 1 ∧
      energy E b = cutSize E b 1) := by
  have hM : lmax b ≤ 1 := (lmax_le_iff b 1).mpr h
  by_cases h0 : lmax b = 0
  · left
    have hz : ∀ x ∈ b, x = 0 := fun x hx => by have := le_lmax b x hx; omega
    refine ⟨h0, hz, ?_, by rw [nonemptyLevels_eq_lmax b 1 hM, h0]; rfl⟩
    rw [energy_binary E b h]
    unfold cutSize
    rw [esum_congr b (cutInd 1) (fun _ _ => 0 * 0) (fun x y hx hy => by
      rw [hz x hx, hz y hy]; rfl), esum_mul]
    simp
  · right
    have h1 : lmax b = 1 := by omega
    exact ⟨h1, (thrCard_pos_iff b 1 (Nat.le_refl 1)).mpr (by omega),
      thr_proper_of_minZero b hb 1 (Nat.le_refl 1),
      by rw [nonemptyLevels_eq_lmax b 1 hM, h1]; rfl, energy_binary E b h⟩

/-! ## A concrete instance with repeated thresholds and gaps

`a = [0, 2, 2, 5, 0]`: `S_1 = S_2 = {1,2,3}`, `S_3 = S_4 = S_5 = {3}`.
-/

section Example

def exA : List Nat := [0, 2, 2, 5, 0]
def exE : List (Nat × Nat) := [(0, 1), (1, 3), (3, 4), (2, 4), (0, 3), (1, 2)]

example : thr exA 1 = [1, 2, 3] := by decide
example : thr exA 2 = [1, 2, 3] := by decide
example : thr exA 3 = [3] := by decide
example : thr exA 5 = [3] := by decide
example : thr exA 6 = [] := by decide
example : lmax exA = 5 := by decide

/-- Direct energy: 4 + 9 + 25 + 4 + 25 + 0 = 67. -/
example : energy exE exA = 67 := by decide

/-- The general theorem instantiated on this profile, with both sides evaluated. -/
example : rsum 5 (fun r => cutSize exE exA r) +
    2 * rsum 5 (fun s => rsum (s - 1) (fun r => crossCount exE exA r s)) = 67 := by
  rw [← energy_nested exE exA 5 (by decide)]
  decide

example : (vol exA : Int) = rsum 5 (fun r => (thrCard exA r : Int)) :=
  vol_eq_levels exA 5 (by decide)

end Example

end Singularity
