/-
  Singularity.Normalization  (roadmap push P07)

  Translation normalization for height profiles on a finite labeled graph.

  Model (core Lean 4 only, no Mathlib):
  * A graph on vertices `0, …, n-1` is given by an edge list `E : List (Nat × Nat)`.
  * A height profile is `a : List Nat` of length `n`; `a[v]?` is the height of `v`.
  * An edge whose endpoint is not a valid index of the profile contributes `0`
    (for well-formed graphs every edge is in range, so this convention is invisible).
    Loops contribute `0` automatically.  No simplicity, looplessness or
    connectivity hypothesis is used anywhere, so every statement below covers
    disconnected graphs and arbitrary edge lists.
  * `vol a` is the total height, `energy E a = Σ_{uv ∈ E} (a_u - a_v)^2` computed in `Int`.
  * A profile is minimum-zero when `0 ∈ b` (all heights are natural numbers).

  No `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by` or `unsafe` is used.
-/
namespace Singularity

/-! ## Basic objects -/

/-- Total integer height (volume) of a profile. -/
def vol : List Nat → Nat
  | [] => 0
  | x :: xs => x + vol xs

/-- Squared height difference, in `Int`. -/
def sqd (x y : Nat) : Int := ((x : Int) - (y : Int)) ^ 2

/-- Value of a two-point function on the endpoints of an edge;
    `0` if an endpoint is not an index of the profile. -/
def edgeVal (a : List Nat) (F : Nat → Nat → Int) (e : Nat × Nat) : Int :=
  match a[e.1]?, a[e.2]? with
  | some x, some y => F x y
  | _, _ => 0

/-- Sum of `edgeVal a F` over an edge list. -/
def esum (a : List Nat) (F : Nat → Nat → Int) : List (Nat × Nat) → Int
  | [] => 0
  | e :: es => edgeVal a F e + esum a F es

/-- Edge-square energy `E_G(a) = Σ_{uv ∈ E} (a_u - a_v)^2`. -/
def energy (E : List (Nat × Nat)) (a : List Nat) : Int := esum a sqd E

/-- Minimum of a profile (`0` for the empty list, which is never used as a profile). -/
def lmin : List Nat → Nat
  | [] => 0
  | [x] => x
  | x :: y :: ys => min x (lmin (y :: ys))

/-- Add the constant `t` to every height. -/
def shift (b : List Nat) (t : Nat) : List Nat := b.map (· + t)

/-- Minimum-zero normalization `a ↦ a - min a`. -/
def norm (a : List Nat) : List Nat := a.map (· - lmin a)

/-- Minimum-zero predicate. -/
def MinZero (b : List Nat) : Prop := 0 ∈ b

/-! ## Minimum -/

theorem lmin_le : ∀ (a : List Nat) (x : Nat), x ∈ a → lmin a ≤ x
  | [], x, h => absurd h (List.not_mem_nil x)
  | [y], x, h => by
      simp at h
      simp [lmin, h]
  | y :: z :: zs, x, h => by
      simp only [lmin]
      rcases List.mem_cons.mp h with h | h
      · omega
      · have := lmin_le (z :: zs) x h
        omega

theorem lmin_mem : ∀ (a : List Nat), a ≠ [] → lmin a ∈ a
  | [], h => absurd rfl h
  | [y], _ => by simp [lmin]
  | y :: z :: zs, _ => by
      simp only [lmin]
      rcases Nat.le_total y (lmin (z :: zs)) with h | h
      · rw [Nat.min_eq_left h]; exact List.mem_cons_self _ _
      · rw [Nat.min_eq_right h]
        exact List.mem_cons_of_mem _ (lmin_mem (z :: zs) (by simp))

/-- For a nonempty profile, minimum-zero is the same as `lmin = 0`. -/
theorem minZero_iff (a : List Nat) (ha : a ≠ []) : MinZero a ↔ lmin a = 0 := by
  constructor
  · intro h; have := lmin_le a 0 h; omega
  · intro h; have := lmin_mem a ha; rw [h] at this; exact this

theorem lmin_shift : ∀ (b : List Nat) (t : Nat), b ≠ [] → lmin (shift b t) = lmin b + t
  | [], _, h => absurd rfl h
  | [y], t, _ => by simp [shift, lmin]
  | y :: z :: zs, t, _ => by
      have ih := lmin_shift (z :: zs) t (by simp)
      simp only [shift, List.map] at ih ⊢
      simp only [lmin]
      rw [ih]
      omega

/-! ## Lengths -/

theorem shift_length (b : List Nat) (t : Nat) : (shift b t).length = b.length := by
  simp [shift]

theorem norm_length (a : List Nat) : (norm a).length = a.length := by
  simp [norm]

/-! ## The shift bijection -/

private theorem map_eq_self (f : Nat → Nat) : ∀ (a : List Nat), (∀ x ∈ a, f x = x) → a.map f = a
  | [], _ => rfl
  | x :: xs, h => by
      simp only [List.map]
      rw [h x (List.mem_cons_self _ _), map_eq_self f xs (fun y hy => h y (List.mem_cons_of_mem _ hy))]

/-- The normalization of a nonempty profile is minimum-zero. -/
theorem norm_minZero (a : List Nat) (ha : a ≠ []) : MinZero (norm a) := by
  unfold MinZero norm
  exact List.mem_map.mpr ⟨lmin a, lmin_mem a ha, Nat.sub_self _⟩

/-- `a = norm a + min a`. -/
theorem shift_norm (a : List Nat) : shift (norm a) (lmin a) = a := by
  unfold shift norm
  rw [List.map_map]
  apply map_eq_self
  intro x hx
  have := lmin_le a x hx
  simp only [Function.comp]
  omega

/-- If `b` is minimum-zero then the minimum of `b + t` is `t`. -/
theorem lmin_shift_minZero (b : List Nat) (t : Nat) (hb : MinZero b) : lmin (shift b t) = t := by
  have hne : b ≠ [] := by intro h; rw [h] at hb; exact List.not_mem_nil 0 hb
  rw [lmin_shift b t hne, (minZero_iff b hne).mp hb]
  omega

/-- If `b` is minimum-zero then normalizing `b + t` returns `b`. -/
theorem norm_shift (b : List Nat) (t : Nat) (hb : MinZero b) : norm (shift b t) = b := by
  have hm := lmin_shift_minZero b t hb
  unfold norm
  rw [hm]
  unfold shift
  rw [List.map_map]
  apply map_eq_self
  intro x _
  simp only [Function.comp]
  omega

/-- Injectivity of `(b, t) ↦ b + t` on minimum-zero `b`. -/
theorem shift_injective (b b' : List Nat) (t t' : Nat) (hb : MinZero b) (hb' : MinZero b')
    (h : shift b t = shift b' t') : b = b' ∧ t = t' := by
  constructor
  · rw [← norm_shift b t hb, ← norm_shift b' t' hb', h]
  · rw [← lmin_shift_minZero b t hb, ← lmin_shift_minZero b' t' hb', h]

/-- Surjectivity onto all nonnegative nonempty profiles, with explicit inverse
    `a ↦ (a - min a, min a)`. -/
theorem shift_surjective (a : List Nat) (ha : a ≠ []) :
    ∃ b t, MinZero b ∧ b.length = a.length ∧ shift b t = a :=
  ⟨norm a, lmin a, norm_minZero a ha, norm_length a, shift_norm a⟩

/-- Uniqueness of the decomposition: any minimum-zero `b` and shift `t` with
    `b + t = a` are `b = a - min a` and `t = min a`. -/
theorem shift_unique (a b : List Nat) (t : Nat) (hb : MinZero b) (h : shift b t = a) :
    b = norm a ∧ t = lmin a := by
  subst h
  exact ⟨(norm_shift b t hb).symm, (lmin_shift_minZero b t hb).symm⟩

/-! ## Volume and energy -/

/-- `vol (b + t) = vol b + n t` where `n = b.length`. -/
theorem vol_shift : ∀ (b : List Nat) (t : Nat), vol (shift b t) = vol b + b.length * t
  | [], _ => by simp [shift, vol]
  | x :: xs, t => by
      have ih := vol_shift xs t
      simp only [shift, List.map, vol, List.length_cons] at ih ⊢
      rw [ih, Nat.add_mul]
      omega

theorem sqd_shift (x y t : Nat) : sqd (x + t) (y + t) = sqd x y := by
  unfold sqd
  rw [show ((x + t : Nat) : Int) - ((y + t : Nat) : Int) = (x : Int) - (y : Int) by omega]

theorem edgeVal_shift (a : List Nat) (t : Nat) (e : Nat × Nat) :
    edgeVal (shift a t) sqd e = edgeVal a sqd e := by
  unfold edgeVal shift
  rw [List.getElem?_map, List.getElem?_map]
  cases a[e.1]? <;> cases a[e.2]? <;> simp [sqd_shift]

/-- Energy is invariant under adding a constant to every height. -/
theorem energy_shift (E : List (Nat × Nat)) (a : List Nat) (t : Nat) :
    energy E (shift a t) = energy E a := by
  unfold energy
  induction E with
  | nil => rfl
  | cons e es ih => simp only [esum]; rw [edgeVal_shift, ih]

theorem energy_norm (E : List (Nat × Nat)) (a : List Nat) : energy E (norm a) = energy E a := by
  conv => rhs; rw [← shift_norm a]
  rw [energy_shift]

/-! ## Finite enumeration of profiles with bounded entries -/

/-- All lists of length `n` with entries in `0..V`. -/
def box : Nat → Nat → List (List Nat)
  | 0, _ => [[]]
  | n + 1, V => (List.range (V + 1)).bind (fun x => (box n V).map (x :: ·))

theorem mem_box : ∀ (n V : Nat) (a : List Nat), a ∈ box n V ↔ a.length = n ∧ ∀ x ∈ a, x ≤ V
  | 0, V, a => by
      cases a with
      | nil => simp [box]
      | cons y ys => simp [box]
  | n + 1, V, a => by
      cases a with
      | nil => simp [box]
      | cons y ys =>
          simp only [box, List.mem_bind, List.mem_range, List.mem_map, List.length_cons,
            List.mem_cons, forall_eq_or_imp]
          constructor
          · rintro ⟨x, hx, c, hc, he⟩
            injection he with h1 h2
            subst h1; subst h2
            have := (mem_box n V c).mp hc
            exact ⟨by omega, by omega, this.2⟩
          · rintro ⟨hl, hy, hys⟩
            exact ⟨y, by omega, ys, (mem_box n V ys).mpr ⟨by omega, hys⟩, rfl⟩

private theorem nodup_bind_cons (L : List (List Nat)) (hL : L.Nodup) :
    ∀ (l : List Nat), l.Nodup → (l.bind (fun x => L.map (x :: ·))).Nodup
  | [], _ => List.Pairwise.nil
  | x :: xs, hl => by
      rw [List.bind_cons]
      have hl' := List.nodup_cons.mp hl
      unfold List.Nodup
      rw [List.pairwise_append]
      refine ⟨?_, nodup_bind_cons L hL xs hl'.2, ?_⟩
      · exact List.Pairwise.map _ (fun a b h e => h (List.cons.inj e).2) hL
      · intro p hp q hq e
        rcases List.mem_map.mp hp with ⟨c, _, rfl⟩
        rcases List.mem_bind.mp hq with ⟨y, hy, hq'⟩
        rcases List.mem_map.mp hq' with ⟨d, _, rfl⟩
        have : x = y := (List.cons.inj e).1
        subst this
        exact hl'.1 hy

theorem nodup_range' : ∀ (k : Nat), (List.range k).Nodup := by
  intro k
  exact List.nodup_range k

theorem box_nodup : ∀ (n V : Nat), (box n V).Nodup
  | 0, _ => by simp [box]
  | n + 1, V => nodup_bind_cons _ (box_nodup n V) _ (nodup_range' _)

/-- Two duplicate-free lists with the same members have the same length. -/
theorem length_eq_of_nodup_mem_iff {α : Type} [DecidableEq α] :
    ∀ (l1 l2 : List α), l1.Nodup → l2.Nodup → (∀ x, x ∈ l1 ↔ x ∈ l2) → l1.length = l2.length
  | [], [], _, _, _ => rfl
  | [], y :: _, _, _, h => absurd ((h y).mpr (List.mem_cons_self _ _)) (List.not_mem_nil y)
  | x :: xs, l2, h1, h2, h => by
      have hx : x ∈ l2 := (h x).mp (List.mem_cons_self _ _)
      have h1' := List.nodup_cons.mp h1
      have hrec := length_eq_of_nodup_mem_iff xs (l2.erase x) h1'.2 (List.Nodup.erase x h2) (by
        intro y
        rw [List.Nodup.mem_erase_iff h2]
        constructor
        · intro hy
          refine ⟨?_, (h y).mp (List.mem_cons_of_mem _ hy)⟩
          intro e; subst e; exact h1'.1 hy
        · rintro ⟨hne, hy⟩
          rcases List.mem_cons.mp ((h y).mpr hy) with e | e
          · exact absurd e hne
          · exact e)
      rw [List.length_erase_of_mem hx] at hrec
      have := List.length_pos_of_mem hx
      simp only [List.length_cons]
      omega

/-- Every height is bounded by the volume. -/
theorem le_vol : ∀ (a : List Nat) (x : Nat), x ∈ a → x ≤ vol a
  | [], x, h => absurd h (List.not_mem_nil x)
  | y :: ys, x, h => by
      simp only [vol]
      rcases List.mem_cons.mp h with h | h
      · omega
      · have := le_vol ys x h; omega

/-- A profile of length `n` without zero entries has volume at least `n`. -/
theorem length_le_vol_of_pos : ∀ (a : List Nat), (∀ x ∈ a, 1 ≤ x) → a.length ≤ vol a
  | [], _ => by simp [vol]
  | y :: ys, h => by
      have := length_le_vol_of_pos ys (fun x hx => h x (List.mem_cons_of_mem _ hx))
      have hy := h y (List.mem_cons_self _ _)
      simp only [vol, List.length_cons]
      omega

/-! ## Coefficients

`allCount E n V e` is the coefficient `[x^V q^e] L_G` and `mzCount E n V e` is the
coefficient `[x^V q^e] B_G`.  The enumerations are finite by construction (`box n V`),
and `mem_allFilter` / `mem_mzFilter` show they contain *every* length-`n` profile with
volume `V` and energy `e` (respectively every such minimum-zero profile).
-/

instance (b : List Nat) : Decidable (MinZero b) := by unfold MinZero; infer_instance

def allFilter (E : List (Nat × Nat)) (n V : Nat) (e : Int) : List (List Nat) :=
  (box n V).filter (fun a => decide (vol a = V ∧ energy E a = e))

def mzFilter (E : List (Nat × Nat)) (n V : Nat) (e : Int) : List (List Nat) :=
  (box n V).filter (fun a => decide ((vol a = V ∧ energy E a = e) ∧ MinZero a))

/-- `[x^V q^e] L_G`: number of nonnegative profiles with volume `V` and energy `e`. -/
def allCount (E : List (Nat × Nat)) (n V : Nat) (e : Int) : Nat := (allFilter E n V e).length

/-- `[x^V q^e] B_G`: number of minimum-zero profiles with volume `V` and energy `e`. -/
def mzCount (E : List (Nat × Nat)) (n V : Nat) (e : Int) : Nat := (mzFilter E n V e).length

theorem mem_allFilter (E : List (Nat × Nat)) (n V : Nat) (e : Int) (a : List Nat) :
    a ∈ allFilter E n V e ↔ a.length = n ∧ vol a = V ∧ energy E a = e := by
  unfold allFilter
  rw [List.mem_filter, mem_box]
  simp only [decide_eq_true_eq]
  constructor
  · rintro ⟨⟨hl, _⟩, hv, he⟩; exact ⟨hl, hv, he⟩
  · rintro ⟨hl, hv, he⟩
    exact ⟨⟨hl, fun x hx => hv ▸ le_vol a x hx⟩, hv, he⟩

theorem mem_mzFilter (E : List (Nat × Nat)) (n V : Nat) (e : Int) (a : List Nat) :
    a ∈ mzFilter E n V e ↔ a.length = n ∧ vol a = V ∧ energy E a = e ∧ MinZero a := by
  unfold mzFilter
  rw [List.mem_filter, mem_box]
  simp only [decide_eq_true_eq]
  constructor
  · rintro ⟨⟨hl, _⟩, ⟨hv, he⟩, hm⟩; exact ⟨hl, hv, he, hm⟩
  · rintro ⟨hl, hv, he, hm⟩
    exact ⟨⟨hl, fun x hx => hv ▸ le_vol a x hx⟩, ⟨hv, he⟩, hm⟩

/-- Profiles of volume `V` and energy `e` with all heights positive. -/
def posFilter (E : List (Nat × Nat)) (n V : Nat) (e : Int) : List (List Nat) :=
  (box n V).filter (fun a => decide ((vol a = V ∧ energy E a = e) ∧ ¬ MinZero a))

private theorem filter_split {α : Type} (P Q : α → Prop) [DecidablePred P] [DecidablePred Q] :
    ∀ (l : List α), (l.filter (fun a => decide (P a))).length =
      (l.filter (fun a => decide (P a ∧ Q a))).length +
      (l.filter (fun a => decide (P a ∧ ¬ Q a))).length
  | [] => rfl
  | x :: xs => by
      have ih := filter_split P Q xs
      by_cases hp : P x <;> by_cases hq : Q x <;>
        simp [List.filter_cons, hp, hq, ih] <;> omega

theorem allCount_split (E : List (Nat × Nat)) (n V : Nat) (e : Int) :
    allCount E n V e = mzCount E n V e + (posFilter E n V e).length := by
  unfold allCount mzCount posFilter allFilter mzFilter
  exact filter_split (fun a => vol a = V ∧ energy E a = e) MinZero (box n V)

private theorem nodup_filter {α : Type} (p : α → Bool) (l : List α) (h : l.Nodup) :
    (l.filter p).Nodup := List.Pairwise.filter p h

/-- Profiles with no zero height and volume `V` correspond, by subtracting `1`
    from every height, to all profiles of volume `V - n`. -/
theorem posCount_eq (E : List (Nat × Nat)) (n V : Nat) (e : Int) (hV : n ≤ V) :
    (posFilter E n V e).length = allCount E n (V - n) e := by
  unfold allCount
  rw [← List.length_map (allFilter E n (V - n) e) (fun b => shift b 1)]
  apply length_eq_of_nodup_mem_iff
  · exact nodup_filter _ _ (box_nodup n V)
  · apply List.Pairwise.map _ _ (nodup_filter _ _ (box_nodup n (V - n)))
    intro b b' hne heq
    apply hne
    have h := congrArg (List.map (· - 1)) heq
    simp only [shift, List.map_map] at h
    have hid : ∀ c : List Nat, List.map ((· - 1) ∘ (· + 1)) c = c := fun c =>
      map_eq_self _ c (fun x _ => by simp [Function.comp])
    rwa [hid, hid] at h
  · intro a
    have hbox : ∀ c : List Nat, c ∈ posFilter E n V e ↔
        c.length = n ∧ vol c = V ∧ energy E c = e ∧ ¬ MinZero c := by
      intro c
      unfold posFilter
      rw [List.mem_filter, mem_box]
      simp only [decide_eq_true_eq]
      constructor
      · rintro ⟨⟨hl, _⟩, ⟨hv, he⟩, hm⟩; exact ⟨hl, hv, he, hm⟩
      · rintro ⟨hl, hv, he, hm⟩
        exact ⟨⟨hl, fun x hx => hv ▸ le_vol c x hx⟩, ⟨hv, he⟩, hm⟩
    rw [hbox, List.mem_map]
    constructor
    · rintro ⟨hl, hv, he, hm⟩
      have hpos : ∀ x ∈ a, 1 ≤ x := by
        intro x hx
        have : x ≠ 0 := by intro h0; subst h0; exact hm hx
        omega
      refine ⟨a.map (· - 1), ?_, ?_⟩
      · rw [mem_allFilter]
        have hs : shift (a.map (· - 1)) 1 = a := by
          unfold shift; rw [List.map_map]
          exact map_eq_self _ a (fun x hx => by have := hpos x hx; simp [Function.comp]; omega)
        have hvol := vol_shift (a.map (· - 1)) 1
        rw [hs, List.length_map, hl] at hvol
        refine ⟨by simp [hl], by omega, ?_⟩
        rw [← energy_shift E (a.map (· - 1)) 1, hs, he]
      · unfold shift; rw [List.map_map]
        exact map_eq_self _ a (fun x hx => by have := hpos x hx; simp [Function.comp]; omega)
    · rintro ⟨b, hb, rfl⟩
      rw [mem_allFilter] at hb
      obtain ⟨hl, hv, he⟩ := hb
      refine ⟨by rw [shift_length, hl], ?_, by rw [energy_shift, he], ?_⟩
      · rw [vol_shift, hl, hv]; omega
      · intro h0
        unfold shift at h0
        rcases List.mem_map.mp h0 with ⟨x, _, hx⟩
        omega

/-- Coefficient recurrence behind `B = (1 - x^n) L`, for `V ≥ n`:
    `[x^V q^e] L = [x^V q^e] B + [x^(V-n) q^e] L`. -/
theorem allCount_rec (E : List (Nat × Nat)) (n V : Nat) (e : Int) (hV : n ≤ V) :
    allCount E n V e = mzCount E n V e + allCount E n (V - n) e := by
  rw [allCount_split, posCount_eq E n V e hV]

/-- For `V < n`: `[x^V q^e] L = [x^V q^e] B` (every such profile has a zero height). -/
theorem allCount_eq_mzCount_of_lt (E : List (Nat × Nat)) (n V : Nat) (e : Int) (hV : V < n) :
    allCount E n V e = mzCount E n V e := by
  rw [allCount_split]
  suffices h : posFilter E n V e = [] by rw [h]; rfl
  unfold posFilter
  rw [List.filter_eq_nil]
  intro a ha hp
  simp only [decide_eq_true_eq] at hp
  obtain ⟨⟨hv, _⟩, hm⟩ := hp
  have hl := ((mem_box n V a).mp ha).1
  have hpos : ∀ x ∈ a, 1 ≤ x := by
    intro x hx
    have : x ≠ 0 := by intro h0; subst h0; exact hm hx
    omega
  have := length_le_vol_of_pos a hpos
  omega

/-! ## The summed coefficient identity -/

/-- `sumBelow K f = f 0 + ⋯ + f (K-1)`. -/
def sumBelow : Nat → (Nat → Nat) → Nat
  | 0, _ => 0
  | k + 1, f => sumBelow k f + f k

theorem sumBelow_succ_left (f : Nat → Nat) : ∀ k, sumBelow (k + 1) f = f 0 + sumBelow k (fun t => f (t + 1))
  | 0 => by simp [sumBelow]
  | k + 1 => by
      have ih := sumBelow_succ_left f k
      simp only [sumBelow] at ih ⊢
      rw [ih]; omega

theorem sumBelow_congr (f g : Nat → Nat) : ∀ k, (∀ t, t < k → f t = g t) → sumBelow k f = sumBelow k g
  | 0, _ => rfl
  | k + 1, h => by
      simp only [sumBelow]
      rw [sumBelow_congr f g k (fun t ht => h t (by omega)), h k (by omega)]

theorem sumBelow_extend (f : Nat → Nat) (K : Nat) (hz : ∀ t, K ≤ t → f t = 0) :
    ∀ d, sumBelow (K + d) f = sumBelow K f
  | 0 => rfl
  | d + 1 => by
      rw [← Nat.add_assoc]
      simp only [sumBelow]
      rw [sumBelow_extend f K hz d, hz (K + d) (by omega)]
      rfl

/-- `Σ_{t ≥ 0, n t ≤ V} [x^(V - n t) q^e] B`. -/
def shiftSum (E : List (Nat × Nat)) (n V : Nat) (e : Int) : Nat :=
  sumBelow (V + 1) (fun t => if n * t ≤ V then mzCount E n (V - n * t) e else 0)

/-- **Coefficient form of `L_G = B_G / (1 - x^n)`** (SNG-F02, P07):
    for `n ≥ 1`, every volume `V` and energy `e`,
    `#{a ≥ 0 : |a| = n, vol a = V, E(a) = e} = Σ_{t ≥ 0, n t ≤ V} #{b min-zero : vol b = V - n t, E(b) = e}`.
    No connectivity hypothesis. -/
theorem allCount_eq_shiftSum (E : List (Nat × Nat)) (n : Nat) (hn : 1 ≤ n) (e : Int) :
    ∀ V, allCount E n V e = shiftSum E n V e := by
  intro V
  induction V using Nat.strongRecOn with
  | _ V ih =>
    unfold shiftSum
    rw [sumBelow_succ_left]
    simp only [Nat.mul_zero, Nat.zero_le, if_true, Nat.sub_zero]
    by_cases hV : n ≤ V
    · rw [allCount_rec E n V e hV, ih (V - n) (by omega)]
      congr 1
      unfold shiftSum
      have hstep : ∀ t, (if n * (t + 1) ≤ V then mzCount E n (V - n * (t + 1)) e else 0) =
          (if n * t ≤ V - n then mzCount E n (V - n - n * t) e else 0) := by
        intro t
        rw [Nat.mul_succ]
        have h1 : (n * t + n ≤ V) = (n * t ≤ V - n) := propext (by omega)
        have h2 : V - (n * t + n) = V - n - n * t := by omega
        simp only [h1, h2]
      rw [sumBelow_congr _ _ V (fun t _ => hstep t)]
      have hz : ∀ t, V - n + 1 ≤ t → (if n * t ≤ V - n then mzCount E n (V - n - n * t) e else 0) = 0 := by
        intro t ht
        have : t ≤ n * t := by simpa using Nat.mul_le_mul_right t hn
        rw [if_neg (by omega)]
      have hK := sumBelow_extend _ (V - n + 1) hz (n - 1)
      rw [show V - n + 1 + (n - 1) = V by omega] at hK
      exact hK.symm
    · have hV' : V < n := by omega
      rw [allCount_eq_mzCount_of_lt E n V e hV']
      have hz : ∀ t, 0 ≤ t → (if n * (t + 1) ≤ V then mzCount E n (V - n * (t + 1)) e else 0) = 0 := by
        intro t _
        rw [Nat.mul_succ, if_neg (by omega)]
      have := sumBelow_extend _ 0 hz V
      simp only [Nat.zero_add] at this
      rw [this]
      rfl

/-! ## Small evaluated instances (single edge `0 – 1`, `n = 2`, volume `2`)

Profiles of volume 2: `(2,0), (0,2)` with energy 4 and `(1,1)` with energy 0.
-/
example : allCount [(0, 1)] 2 2 4 = 2 := by decide
example : allCount [(0, 1)] 2 2 0 = 1 := by decide
example : mzCount [(0, 1)] 2 2 0 = 0 := by decide
example : mzCount [(0, 1)] 2 0 0 = 1 := by decide
example : allCount [(0, 1)] 2 2 0 = shiftSum [(0, 1)] 2 2 0 :=
  allCount_eq_shiftSum [(0, 1)] 2 (by decide) 0 2
/-- Disconnected example: two isolated vertices, no edges. -/
example : allCount [] 2 3 0 = 4 := by decide

end Singularity
