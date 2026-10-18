# Formal kernel checks (Lean 4, core only)

This directory is a Lean 4 package, `Singularity`, that kernel-checks the translation-normalization identity (roadmap push P07, manuscript theorem SNG-F02), the nested-level energy identity (push P08), and the two decisive coefficient certificates `results/certificates/spectral.json` and `results/certificates/binary_census.json` against the P07 coefficient definition (push P33). It also contains a partial formalization of the visibility comparison SNG-A11 (push P34, **PARTIAL**): the finite power-series cancellation is kernel-checked, the analytic part is a conditional theorem whose premises are listed explicitly (see the P34 section). It uses core Lean 4 only: no Mathlib, Batteries or other dependency (`lake-manifest.json` has an empty package list).

## Completed real analytic extension

The real-number completion of P34 is in the separate, dependency-pinned
[Mathlib analysis package](../formal-analysis/README.md). It imports these
core certificates, proves actual local-series convergence and logarithmic
remainders, proves convergence and positivity of the regularized prime
product, and connects to Mathlib's real-axis Riemann zeta Euler product and
residue. Its final spectral and binary theorems require no `RealFacts`,
`Expands` or `Good` hypotheses. The exact exponents at `q=1/2` are also proved.
The core-only conditional development below is retained unchanged as an
independently buildable component; its analytic limitations describe this
directory, not the complete two-package proof chain.

## Toolchain and build

- Toolchain: `leanprover/lean4:v4.12.0`, pinned in `lean-toolchain`.
- Dependencies: none beyond the Lean 4.12.0 core library (`Init`).
- Build, from the repository root, with `lake` from a Lean 4.12.0 release on `PATH` (or via `elan`, which reads `lean-toolchain`):

  ```sh
  cd formal
  lake build
  ```

  Expected output ends with `Build completed successfully.` Development used the official `lean-4.12.0-linux` release binaries, invoked directly without elan.
- Axiom audit (prints the axioms each main theorem depends on):

  ```sh
  cd formal
  lake env lean AxiomAudit.lean
  ```

  Every listed theorem depends only on Lean's standard axioms `propext`, `Quot.sound` and, for some theorems, `Classical.choice`. No project axiom is declared. A text search of `Singularity.lean`, `Singularity/*.lean` for `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by` and `unsafe` finds those words only in the header comments that say they are not used. In P07/P08, `decide` appears only in small evaluated examples (profiles of length at most 5, boxes of at most 16 profiles) and in `Decidable` plumbing for `List.filter`. In P33, `decide` is the kernel evaluation of the certificate checks described below (no `native_decide`: the proof term is `of_decide_eq_true (Eq.refl true)`, re-checked by the kernel).
- Clean build time for the whole package (P33 dominates): about 100 s wall clock (`rm -rf .lake && python3 scripts/check_formal.py`: 2 min 2 s including the axiom audit after P34, of which `Singularity/Visibility.lean` takes about 16 s) on the development container.

Files:

| File | Content |
|---|---|
| `lean-toolchain`, `lakefile.lean` | Pinned toolchain; package `Singularity`, default library `Singularity`. |
| `Singularity.lean` | Imports all modules. |
| `Singularity/Normalization.lean` | P07. |
| `Singularity/Thresholds.lean` | P08. |
| `Singularity/CertificateData.lean` | P33: Lean literals transcribed from the two certificates. Generated; do not edit. |
| `Singularity/Certificates.lean` | P33: enumerator, histogram correctness, table/difference/factorization checks and the certificate theorems. |
| `Singularity/Visibility.lean` | Core finite part of P34: truncated power series over a commutative ring, finite cancellation, the certificate quotient laws, and the conditional analytic theorem. |
| `tools/gen_certificates.py` | P33 transcription script (JSON → `CertificateData.lean`); `--check` detects a stale data file. |
| `AxiomAudit.lean` | `#print axioms` for the main theorems. It is not part of the library. |

## Model and conventions

- A graph on vertices `0, …, n-1` is an edge list `E : List (Nat × Nat)`. A height profile is `a : List Nat` of length `n`, and `a[v]?` is the height of vertex `v`.
- `vol a` is the total height. `energy E a = Σ_{(u,v) ∈ E} (a_u - a_v)^2`, computed in `Int` (`sqd x y = ((x:Int) - y)^2`).
- An edge whose endpoint is not an index of the profile contributes `0`. For a valid graph on `0..n-1` every edge is in range, so this convention changes nothing. Loops contribute `0` automatically. The theorems need no simplicity, looplessness or connectivity hypothesis, so they hold for disconnected graphs and arbitrary edge lists, including multi-edges.
- `MinZero b` means `0 ∈ b`. For nonempty `b` this is equivalent to `lmin b = 0` (`minZero_iff`).
- `shift b t = b.map (· + t)`. `norm a = a.map (· - lmin a)` is the minimum-zero representative, the same operation as Python's `normalize_heights`.
- Coefficients: `allCount E n V e` counts length-`n` profiles with volume `V` and energy `e`, so it is `[x^V q^e] L_G`. `mzCount E n V e` counts the minimum-zero ones, so it is `[x^V q^e] B_G`. Both are lengths of filters of the finite list `box n V` of all length-`n` lists with entries `≤ V`. `mem_allFilter` and `mem_mzFilter` prove that this finite enumeration contains *every* qualifying profile, which settles coefficient finiteness. Original labeled assignments are counted, with no automorphism quotient.
- Threshold sets: `inThr a r v` holds when `r ≤ a_v`. `thr a r` is the list of vertices of `S_r`. `thrCard a r = |S_r|`, with `thr_length` showing that it equals `(thr a r).length`. Levels are summed as `rsum M f = f 1 + ⋯ + f M` for any `M ≥ lmax a`. Nothing assumes that `S_r` are distinct or that heights have no gaps.

## Theorems: P07 (`Singularity/Normalization.lean`)

| Name | Statement |
|---|---|
| `lmin_le`, `lmin_mem` | `lmin a ≤ x` for all `x ∈ a`. For `a ≠ []`, `lmin a ∈ a`. |
| `minZero_iff` | For `a ≠ []`: `0 ∈ a ↔ lmin a = 0`. |
| `norm_minZero` | For `a ≠ []`, `a - min a` is minimum-zero. |
| `shift_norm` | `(a - min a) + min a = a`. |
| `lmin_shift_minZero` | For minimum-zero `b`, `min (b + t) = t`. |
| `norm_shift` | For minimum-zero `b`, `norm (b + t) = b`. |
| `shift_injective` | For minimum-zero `b, b'`, `b + t = b' + t'` implies `b = b'` and `t = t'`. |
| `shift_surjective` | Every nonempty `a` is `b + t` with `b` minimum-zero of the same length (witness `(norm a, lmin a)`). |
| `shift_unique` | For minimum-zero `b`, `b + t = a` forces `b = a - min a` and `t = min a`. |
| `shift_length`, `norm_length` | Length is preserved. |
| `vol_shift` | `vol (b + t) = vol b + n·t`, where `n = b.length`. |
| `energy_shift`, `energy_norm` | Energy is invariant under adding a constant and under normalization. |
| `mem_box`, `box_nodup` | `box n V` is exactly the duplicate-free list of length-`n` lists with entries `≤ V`. |
| `mem_allFilter`, `mem_mzFilter` | The finite filters contain exactly the profiles with the stated length, volume, energy (and minimum zero). |
| `allCount_rec` | For `n ≤ V`: `[x^V q^e]L = [x^V q^e]B + [x^{V-n} q^e]L`. This is the coefficient form of `B = (1 - x^n)L`. It is proved by a bijection that subtracts `1` from profiles with no zero height. |
| `allCount_eq_mzCount_of_lt` | For `V < n`: `[x^V q^e]L = [x^V q^e]B`. |
| `allCount_eq_shiftSum` | For `n ≥ 1` and all `V`, `e`: `[x^V q^e]L = Σ_{t ≥ 0, nt ≤ V} [x^{V-nt} q^e]B`, i.e. `L = B/(1 - x^n)` coefficientwise. |
| `length_eq_of_nodup_mem_iff` | Auxiliary: duplicate-free lists with the same members have equal length. |

Evaluated examples at the end of the file check a single edge with `n = 2` and two isolated vertices with no edges, which is a disconnected case.

## Theorems: P08 (`Singularity/Thresholds.lean`)

| Name | Statement |
|---|---|
| `thr_nested`, `thr_succ_subset` | `S_s ⊆ S_r` for `r ≤ s`. In particular `S_{r+1} ⊆ S_r`. |
| `reconstruct` | For `M ≥ max a` and vertex `v` with height `x`: `x = #{r ∈ 1..M : v ∈ S_r}`. |
| `vol_eq_levels` | `Σ_v a_v = Σ_{r=1}^M |S_r|` for `M ≥ max a`. |
| `thrCard_pos_iff` | For `r ≥ 1`: `S_r ≠ ∅ ↔ r ≤ max a`. |
| `nonemptyLevels_eq_lmax` | The number of nonempty sets among `S_1..S_M` is `max a`. |
| `maxZero_no_levels` | If `max a = 0`, every `S_r` with `r ≥ 1` is empty. |
| `lmax_norm`, `span_eq` | After P07 normalization, `max (a - min a) = max a - min a`, and the number of nonempty threshold sets of `a - min a` is `max a - min a` (the span). |
| `thr_proper_of_minZero` | For minimum-zero `b` and `r ≥ 1`, `|S_r| < n`, so each `S_r` is proper. |
| `edge_square` | For `x, y ≤ M`: `(x - y)^2 = Σ_{r,s=1}^M δ_r δ_s`, with `δ_r = [r ≤ x] - [r ≤ y]`. |
| `delta_mul` | For `r ≤ s`: `δ_r δ_s = 1` exactly when one endpoint lies in the deeper set `S_s` and the other lies outside the shallower set `S_r`, and `0` otherwise. It is never `-1`, because signs agree on nested levels. |
| `delta_sq` | `δ_r^2` is the indicator that the edge crosses the boundary of `S_r`. |
| `rsum_sym` | A symmetric double sum equals its diagonal plus 2 × its strictly ordered part. |
| `edge_nested` | For `x, y ≤ M`: `(x - y)^2 = Σ_r [cut at S_r] + 2 Σ_{1 ≤ r < s ≤ M} [joins S_s to S_rᶜ]`. |
| `energy_nested` | For every edge list and profile, and every `M ≥ max a`: `E_G(a) = Σ_{r=1}^M cut(S_r) + 2 Σ_{1 ≤ r < s ≤ M} crossCount(r, s)`, summing over unordered edges with the factor 2 on the ordered pairs `r < s`. This is the formula of Python's `nested_energy`. |
| `energy_binary` | If all heights are `≤ 1`, then `E_G(a) = cut(S_1)`. |
| `binary_dichotomy` | A minimum-zero binary profile is either the all-zero profile (`max = 0`, no nonempty level, energy 0) or an exact-span-one profile (`max = 1`, `S_1` nonempty and proper, exactly one nonempty level, energy `= cut(S_1)`). |

The concrete instance `exA = [0, 2, 2, 5, 0]` has repeated thresholds and gaps: `S_1 = S_2 = {1,2,3}` and `S_3 = S_4 = S_5 = {3}`. On a six-edge graph it checks the threshold lists, the direct energy `67`, the nested formula evaluated through `energy_nested`, and the volume identity.

## Theorems: P33 (`Singularity/Certificates.lean`)

### Generic chain (any edge list, any `n`, `V`, `e`)

| Name | Statement |
|---|---|
| `mem_comps`, `comps_nodup` | `comps n V` (weak compositions) is exactly the duplicate-free list of length-`n` profiles with `vol a = V`. |
| `allCount_eq_compCount` | P07's `allCount E n V e` (a filter of `box n V`) equals the length of `comps n V` filtered by `energy E a = e`. Proof: both filters are duplicate-free with the same members (`length_eq_of_nodup_mem_iff`). |
| `look_addE`, `look_histOf` | The accumulator `histOf` records, for every `e`, the number of occurrences of `e`. |
| `allCount_eq_look_hist` | **Histogram correctness:** `allCount E n V e = look e (hist E n V)` for every `e : Int`, where `hist E n V` is the energy histogram of `comps n V`. |
| `look_eq_of_agree`, `table_of_ok`, `table_entries_of_ok`, `table_absent_of_ok` | If the Boolean `tableOK E n T` (two-sided comparison of each `hist E n V` with row `V` of `T`) is `true`, then for each listed volume and *every* `e : Int`, `allCount E n V e = look e (T.getD V [])`; every listed entry is a true coefficient; unlisted energies have coefficient `0`. |
| `allCount_eq_nestedCount` | P08: the same coefficient counts profiles of volume `V` by the nested threshold energy `Σ cut(S_r) + 2 Σ_{r<s} crossCount(r,s)` (levels `1..V`), via `energy_nested`. |
| `diff_of_ok`, `dense_of_ok` | Bounded key checks extend to equality of the row difference with a sparse polynomial (`plook`) or a dense polynomial (`dcoeff`) at every `e : Int`. |
| `peval_padd`, `peval_pscale`, `peval_pmul`, `peval_ppow`, `peval_oneMinusQ`, `peval_expandFac` | The dense integer polynomial arithmetic is correct: `expandFac c m fs` evaluates at every integer `x` to `c · x^m · ∏ (1 - x^k)^mult` (factors of positive degree). |

### Certificate theorems (namespace `Singularity.Cert`, prefix `spectral` or `binary`)

For each pair (`spectral`: `spectral.json`, first discrepancy at volume 2; `binary`: `binary_census.json`, first discrepancy at volume 3), with `n = 7` and `max_volume = 4`:

| Name | Statement |
|---|---|
| `X_tableOK`, `XCmp_tableOK` | Kernel evaluation: the computed histograms of `comps 7 V`, `V = 0..4` (330 profiles), equal the transcribed `local_coefficients` of the certificate graph and of the comparison graph. |
| `X_local`, `XCmp_local` | **Full local tables:** `∀ V ≤ 4, ∀ e : Int, allCount G 7 V e = look e (table row V)`, so every listed coefficient holds and every unlisted coefficient is `0`. |
| `X_local_entries`, `XCmp_local_entries` | Entry form: `∀ V ≤ 4, ∀ (e, c) ∈ row V, allCount G 7 V e = c`. |
| `X_normalized` | `normalized_coefficients`: `mzCount G 7 V e = look e (normalized row V)`, derived from P07 `allCount_eq_mzCount_of_lt` (all `V ≤ 4 < 7`). |
| `X_nested` | The transcribed rows count profiles by the P08 nested threshold energy. |
| `X_agree_below` | `∀ V < d, ∀ e, allCount G 7 V e = allCount G' 7 V e` (equality at all lower volumes). |
| `X_first_difference` | `∀ e : Int, allCount G 7 d e - allCount G' 7 d e = plook e P` with `P` the transcribed `first_difference.polynomial` (all denominators are 1). |
| `X_factorization` | `∀ e : Int`, the same difference equals the coefficient of `q^e` in `expandFac c m fs`, the expansion of the stated factorization (`2 q^2 (1-q)^2 (1-q^2)` for `spectral`, `q^3 (1-q) (1-q^3)^2 (1-q^4)^2` for `binary`). |
| `X_factorization_eval` | `peval (expandFac c m fs) x = c · x^m · facProd x fs` for every integer `x`. |
| `X_discrepancy` | The difference is nonzero at volume `d` (energy 2 for `spectral`, 3 for `binary`). |
| `X_edge_mutation_rejected`, `X_edge_mutation_table` | Replacing one edge (`(3,6) → (4,6)` in the spectral graph, `(3,5) → (4,5)` in the binary-census graph) falsifies the decisive coefficient (`[x^2 q^2] = 6`, resp. `[x^3 q^3] = 5`), and `tableOK` of the released table for the mutated graph is `false`. |
| `X_coefficient_mutation_rejected`, `X_mutated_table_rejected` | The decisive coefficient changed by one (`7`, resp. `6`) is false, and the table carrying that change is rejected (`tableOK = false`). |
| `X_mutated_difference_rejected`, `X_mutated_factorization_rejected` | A changed first-difference polynomial and a changed factor multiplicity are rejected (`diffOK = false`, `denseOK = false`). |

### Trusted boundary for P33

- **Transcription (trusted).** `tools/gen_certificates.py` copies the JSON numbers into `Singularity/CertificateData.lean` without computing anything; the header of that file records the input digests. Inputs at transcription time:

  | File | SHA-256 |
  |---|---|
  | `results/certificates/spectral.json` | `379d5c47c53588d28b2295da1dd4ecf41cd64de53fa8445b52c0a4290b7ec6b2` |
  | `results/certificates/binary_census.json` | `e654012d141c080b457816b880807a2b9c47ed3af610c46d309e54ae4663e4b2` |

  Re-run and compare from the repository root: `python3 formal/tools/gen_certificates.py --check` (fails if the data module differs from a fresh transcription; `sha256sum` on the two JSON files compares the digests). The script reads `graph`, `local_coefficients`, `normalized_coefficients`, `max_volume`, the comparison graph and table, `first_difference` and `factorization`. JSON parsing and this copying are the only unverified link between the released files and the kernel.
- **Checked by the kernel.** Everything else: the enumeration, its coverage and uniqueness, the energy computation, the histogram, its comparison with the literals, the lower-volume equalities, the first difference and the factorization expansion, all connected by proof to `allCount`/`mzCount` of P07. No theorem assumes a table value.
- **Lean itself.** The Lean 4.12.0 kernel and elaborator, and the standard axioms reported by the audit.
- **Not checked.** The `marked_coefficients` (span-marked) rows, the `euler_exponents`, `profile_count`, the graph digests and the `identities` flags are not transcribed; nor is the Python replay code. The certificate graphs are not checked to be simple here (the Python parser checks canonical simple edge lists); the theorems hold for the edge lists as given.

## What is not proved here

- P07/P08/P33 use no generating functions or formal power series (P34 introduces truncated series, see its section). SNG-F02 is formalized coefficientwise (`allCount_eq_shiftSum`, `allCount_rec`); the series identity `B = (1 - x^n)L` is that statement read off coefficients.
- The span-marked version (the `z` variable of SNG-F02) is not formalized. Span invariance under shift follows from `lmin_shift`, `lmax_map_sub` and similar lemmas, but no `(volume, energy, span)` count identity is stated.
- The model represents a graph as an edge list with natural-number indices, not as a separate `Graph` type with simplicity validation. The theorems are more general than simple graphs, and they do not check that a given edge list is simple or loopless.
- There is no link to the Python implementation: nothing here proves that `src/singularity/heights.py` computes these functions. The correspondence of definitions (`normalize_heights` ↔ `norm`, `threshold_sets` ↔ `thr`, `nested_energy` ↔ the right side of `energy_nested`) holds by inspection only.
- The independent P02 histogram comparison and the primewise lift are outside this package. Analytic statements appear only in P34 and only as a conditional theorem: its real-analytic premises are not verified (see the P34 section). For P33, the span-marked and Euler-exponent parts of the certificates remain unchecked (see the trusted boundary above).

## Theorems: P34 (`Singularity/Visibility.lean`) — PARTIAL

Status: **partial formalization.** The finite power-series cancellation behind manuscript theorem SNG-A11 is proved in general and connected to the P33 certificates. The analytic statement is proved only *conditionally*, from an explicit structure of real-analytic premises over an abstract type. Core Lean 4.12 has no real numbers, limits, infinite products or zeta function, so none of those premises is verified. SNG-A11 is **not** formally verified by this core-only package; its positive-real statement is completed in [formal-analysis](../formal-analysis/README.md).

### Algebraic setting

- `VRing R` is a commutative ring class. Its ring laws are fields of the class, so they are hypotheses on `R`, not axioms. Every theorem in Parts A and B holds for every commutative ring: `ℤ`, `ℚ`, `ℝ`, or polynomial and function rings. The file defines `ncast` (natural cast), `icast` (integer cast, with `icast_add` and `icast_mul`), `npow` and `fsum` (finite sums).
- A formal power series in `x` over `R` is a coefficient function `Nat → R`. `conv` is the Cauchy product, and `mono c r` is `c x^r`. `TruncEq N F G` means `F ≡ G (mod x^(N+1))`. `sinv B` is the formal inverse, defined by `C_0 = 1` and `C_k = -Σ_{j<k} B_(k-j) C_j`. `xder A` is `x A'`, and `logDer A = x A'/A`.
- Coefficients that are polynomials in `q` are elements of `R` evaluated at `q : R`. `ell G n V q = Σ_{a ∈ comps n V} q^(E_G a)` is `[x^V] L_G(x,q)`, summed over P33's complete, duplicate-free enumeration of the profiles of volume `V`. `lseries G n q` is the series `V ↦ ell G n V q`. `pevalR` evaluates a dense integer polynomial in `R`.

### Part A: finite cancellation (kernel-checked, for all `r` and all series)

| Name | Statement |
|---|---|
| `conv_sinv` | If `B 0 = 1`, then `B · B⁻¹ = 1` in every degree. |
| `conv_quot` | If `B 0 = 1`, `B · C ≡ 1 (mod x^(r+1))` and `A_k = B_k` for `k < r`, then `A · C ≡ 1 + (A_r - B_r) x^r (mod x^(r+1))`. |
| `quotient_first_discrepancy` | **Quotient law:** if `B 0 = 1` and `A_k = B_k` for `k < r`, then `A · B⁻¹ ≡ 1 + (A_r - B_r) x^r (mod x^(r+1))`. |
| `first_difference` | Under the same agreement, `A - B ≡ (A_r - B_r) x^r (mod x^(r+1))`. |
| `sinv_agree` | Inverse coefficients below `r` depend only on coefficients below `r`. |
| `logDer_first_discrepancy` | If `A_k = B_k` for `k < r`, then `x A'/A - x B'/B ≡ r (A_r - B_r) x^r (mod x^(r+1))`. |
| `log_first_discrepancy` | Assume `R` has no additive torsion (`k a = 0` with `k ≥ 1` forces `a = 0`). Let `lA`, `lB` be formal logarithms, characterized by `k (log A)_k = (x A'/A)_k` for `1 ≤ k ≤ r`. Then `log A - log B` vanishes in degrees `1..r-1` and has coefficient `A_r - B_r` in degree `r`. Lean defines no rational numbers here, so the logarithm itself is defined only through this derivative characterization. Over `ℚ` or `ℝ` it is the usual `log A = Σ (-1)^(j+1) (A-1)^j / j`. |
| `binom_cancel` | Let `r ≥ 1`. If `F ≡ 1 - δ x^r` (the expansion of `(1 - x^r)^δ`) and `Q ≡ 1 + δ x^r (mod x^(r+1))`, then `F · Q ≡ 1 (mod x^(r+1))`. The zeta factor cancels the first discrepancy. |

### Part B: the two certificates (kernel-checked)

Bridge lemmas: `ell_eq_counts` writes `ℓ_{G,V}(q) = Σ_{k<N} allCount G n V k · q^k` (P07 coefficients), provided every energy at volume `V` lies in `[0, N)`. `ell_eq_of_counts` and `ell_sub_of_dense` carry P33's coefficientwise equalities and differences into `R`. `pevalR_expandFac` shows that P33's `expandFac c m fs` evaluates in every commutative ring to `c · x^m · ∏ (1 - x^k)^mult`. The energy range at volumes `≤ 2` (`< 17`) and `≤ 3` (`< 37`) is evaluated by `decide` in `spectral_energy_range` and `binary_energy_range`. The coefficient data come only from the P33 theorems `Cert.spectral_agree_below`, `Cert.spectral_factorization`, `Cert.binary_agree_below` and `Cert.binary_factorization`. No coefficient is restated.

| Name | Statement (for every commutative ring `R` and every `q : R`) |
|---|---|
| `spectral_const`, `binary_const` | `ℓ_{G,0}(q) = ℓ_{G',0}(q) = 1`. |
| `spectral_agree`, `binary_agree` | `ℓ_{G,V}(q) = ℓ_{G',V}(q)` for `V < d` (`d = 2`, resp. `3`). |
| `spectral_delta` | `ℓ_{G,2}(q) - ℓ_{G',2}(q) = 2 q^2 (1-q)^2 (1-q^2)`. |
| `binary_delta` | `ℓ_{G,3}(q) - ℓ_{G',3}(q) = q^3 (1-q) (1-q^3)^2 (1-q^4)^2`. |
| `spectral_quotient` | `L_G / L_G' ≡ 1 + 2 q^2 (1-q)^2 (1-q^2) x^2 (mod x^3)`. |
| `binary_quotient` | `L_G / L_G' ≡ 1 + q^3 (1-q) (1-q^3)^2 (1-q^4)^2 x^3 (mod x^4)`. |
| `spectral_logDer`, `binary_logDer` | The logarithmic-derivative form, with first term `d Δ x^d`. |

In Lean the factorizations print with trivial factors such as `icast 2 * npow q 2 * (npow (1 - npow q 1) 2 * (npow (1 - npow q 2) 1 * 1))`. The certificate graphs are P33's literal edge lists, `n = 7`.

### Part C: the analytic boundary (premises, NOT verified)

`RealFacts K` is a structure over an abstract commutative ring `K` with uninterpreted operations: `lt`, `inv`, `rpow`, `pms p s = p^(-s)`, `zeta`, `HasProdP` (absolutely convergent positive product over primes), `RightLim` (limit as real `s ↓ a`), `Expands` (convergent power series near `0`) and `Good` (positive and continuous on `(0,1)`). Its fields are the missing analytic inputs, each a standard fact when `K = ℝ` is read with those meanings:

| Packet item | Fields |
|---|---|
| Euler product for real zeta | `euler`: `ζ(σ) = ∏_p (1 - p^(-σ))^(-1)`, `σ > 1`. |
| Simple boundary asymptotic, from the right on the positive real axis | `pole`: `(σ - 1) ζ(σ) → 1` as `σ ↓ 1`. |
| Convergence and nonvanishing of infinite products | `prod_unique`, `prod_pos`, `prod_congr`, `prod_mul`, `prod_rpow`. |
| Summability over primes and remainder estimates | `prod_crit`: if `f` is positive and continuous on `(0,1)` and `f(t) = 1 + O(t^(m+1))` as a convergent power series, then `∏_p f(p^(-s))` converges absolutely to a positive `P(s)` for real `(m+1)s > 1`, and `P` is continuous there. This packages `Σ_p p^(-(m+1)s) < ∞`, `|log f(t)| ≤ C t^(m+1)` near `0`, and local uniform convergence. |
| Local power-series division and logarithms over the reals | `exp_mul`, `exp_inv` (the reciprocal of a series with constant term `1` has the formal inverse as its expansion), `exp_binom` (`(1 - t^r)^δ = 1 - δ t^r + O(t^(r+1))`), `good_mul`, `good_inv`, `good_binom`. |
| Real powers, order and right limits | `rpow_inv_cancel`, `rpow_mul`, `rpow_one`, `pms_pow`, `one_sub_pos`, `zero_lt_one`, `sub_pos`, `scale_mono`, `scale_right`, `scale_succ`, `lim_mul`, `lim_rpow`, `lim_scale`, `lim_congr`. |

The pair-specific analytic inputs are separate hypotheses: `M.Expands LG (lseries G n q)` and `M.Good LG`, and the same for `H`. They say that `L_G(·,q)` is a real function, positive and continuous on `(0,1)`, given near `0` by the power series with coefficients `ℓ_{G,V}(q)`. This holds for `0 ≤ q ≤ 1`. The admissibility of `q` enters only through these hypotheses.

| Name | Statement |
|---|---|
| `visibility_conditional` | Assume `M : RealFacts K`, the pair-specific inputs, `ℓ_{H,0}(q) = 1`, `r ≥ 1`, `r s0 = 1` and `ℓ_{G,V}(q) = ℓ_{H,V}(q)` for `V < r`. Let `δ = ℓ_{G,r}(q) - ℓ_{H,r}(q)` (`firstDelta`). Then there exist `R`, `Kr` with: `R(s) = ∏_p L_G(p^(-s))/L_H(p^(-s))` for real `rs > 1`; `Kr(s) = ∏_p (1 - p^(-rs))^δ L_G/L_H` for real `(r+1)s > 1`; `R(s) = ζ(rs)^δ Kr(s)` for `rs > 1`; `Kr(1/r) > 0`; and `(rs - 1)^δ R(s) → Kr(1/r)` as real `s ↓ 1/r`. |
| `spectral_visibility_conditional` | The instance `r = 2`, `δ = 2 q^2 (1-q)^2 (1-q^2)` (`spectral_delta`), discharging agreement and constant term from P33. |
| `binary_visibility_conditional` | The instance `r = 3`, `δ = q^3 (1-q) (1-q^3)^2 (1-q^4)^2` (`binary_delta`). |
| `realFacts_consistent` | `RealFacts Unit` is inhabited by a degenerate one-point model. The premises are therefore not contradictory, so the conditional theorem is not vacuous by inconsistency. The model says nothing about `ℝ`. |

How the proof uses the premises: Part A's `quotient_first_discrepancy` and `binom_cancel` discharge the expansion hypotheses of `prod_crit`, for the ratio factor (`m = r - 1`) and for the regularized factor (`m = r`). `euler`, `prod_rpow`, `prod_mul`, `prod_congr` and `prod_unique` give the factorization. `pole`, `lim_scale`, `lim_rpow`, `lim_mul`, `lim_congr` and the continuity part of `prod_crit` give the asymptotic. No premise mentions the ratio product, its regularization, the factorization or the asymptotic.

### Unformalized boundary (what P34 does not verify)

- **No real analysis is checked.** `RealFacts` is a list of hypotheses. Lean does not construct `ℝ`, `ζ`, convergent products or limits, so it does not check that a faithful model exists or that the abstract operations mean what their names say. The degenerate `Unit` model satisfies every premise, which shows that the premises do not by themselves force the intended meaning. Verifying SNG-A11 requires an instance `RealFacts ℝ` with the intended operations, for example from Mathlib's real analysis and `riemannZeta`, together with proofs of `Expands` and `Good` for the actual local series at `0 ≤ q ≤ 1`. Neither is defined in this core-only directory. The separate [formal-analysis](../formal-analysis/README.md) package discharges the analytic boundary directly with actual Mathlib real functions, rather than constructing an instance of the abstract packet.
- The conditional theorem concerns the **positive real axis only**: the factorization for real `rs > 1` and the right-hand limit as `s ↓ 1/r`. It states nothing about complex `s`, the local holomorphic branch of SNG-A11, or any global meromorphic continuation. It also omits the identification of `R` with `Z_G/Z_H` on `s > 1`. For nonintegral `δ` the singularity is a branch point, not a pole. The statement makes no claim about it either way.
- The real logarithm and the binomial series are premises (`exp_binom`). Part A treats the formal logarithm only through `k (log A)_k = (x A'/A)_k`, because there are no rationals.
- The effective tail bound SNG-A14 is not formalized.
- The concrete exponents are kernel-checked only as elements of an arbitrary commutative ring. The numerical exponents at `q = 1/2` are not formalized. These are `δ = 3/32` for the spectral pair and `δ = 11025/262144` for the binary pair; the manuscript writes the exponents as `-δ`.
