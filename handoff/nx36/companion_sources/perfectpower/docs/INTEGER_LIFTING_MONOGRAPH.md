# Recovering the missing whole-number lift

The previous operator release could find rational coordinates and construct rational task sections. It deliberately left a gap: a fractional lift in a carrier with a kernel does not prove that every lift is fractional. This release fills that gap. It returns every integer solution to an integral linear presentation, constructs complete integral task sections and intertwiner modules, and substitutes those integer fibres into complete SMT queries. A rejected fibre comes with a concrete row proving an exact image obstruction or a divisibility obstruction. The implementation is standard-library Python, with replayable arithmetic certificates. No new Lean proof or general nonlinear integer solver is claimed.

For an outsider, the practical point is simple. Dividing an equation can suggest fractions even when whole-number answers exist. We now keep track of the ways coordinates can move without changing the answer, and use those freedoms to decide whether a whole-number answer really exists. Once it does, we describe all such answers with integer parameters. The rest of the program can use that description in place of searching the original coordinates.

## What the old work contributed

The February `cone-native.txt` discussion, read at rendered lines 26210–26389 and 26680–26744, proposed replacing scalar obstruction scores with an integral relation module, tracking unimodular changes of basis and Smith/Hermite data. The September Wilson task-section machinery, already recovered in `exact_linear.py`, gives the rational equation `carrier * lift = target`. Combining these two ideas gives a constructive integral completion of the earlier rational interface.

There are two corrections to preserve. Smith factors classify an abstract cokernel up to an integral ambient basis change. They do not identify a particular embedded lattice. For example, columns of `diag(2,1)` and `diag(1,2)` have identical Smith factors `(1,2)`, but `(1,0)` lies in only the second image. Likewise, a bilateral reduction `U A V` should not be described as an unchanged row lattice in the original coordinates. This implementation records both basis changes, and checks embedded lattice equality with two actual integral inclusions.

The August Tube source, `The_Fixed_Locus_Tube_Theorem_V10_19_Always_Moving_Fast.html`, rendered lines 239–259, supplies the invariant basis containing the paired sums `X²+X³` and `F₂+F₃`, together with polarization cells `(1,1,2,1)`. Its statement that a paired sum is non-primitive in the ambient lattice is incorrect: a vector with coordinates `(1,1)` is primitive. The executable reconstruction separates the two maps. The 10-by-8 invariant inclusion has eight Smith factors equal to one, so it is primitive; the restricted symplectic pairing has factors `(1,1,1,1,1,1,2,2)` and cokernel `C₂ × C₂`. The doubled pairing is correct. The physical continuation and flux conclusions are not recomputed here.

## Constructive reduction and completeness

`perfectpower.integer_lifting.smith_certificate(A)` constructs integer matrices `U,V,D` with

`U A V = D`, where `D = diag(d₁,…,dᵣ,0,…,0)`, all `dᵢ > 0`, and `dᵢ | dᵢ₊₁`.

The reduction uses only row/column swaps, sign changes, and integer additions of one row or column to another. Each has an integer inverse. Euclidean remainders clear a pivot's row and column. If the pivot does not divide an entry in the remaining block, that entry is brought into the pivot row and Euclid resumes, decreasing the positive pivot before the block is finished. The completed pivot divides the entire remaining block, preserving the final divisibility chain. A transcript records every operation.

`verify_smith` replays that transcript from the supplied input and identity matrices, then checks the exact output matrices, diagonal shape, positivity and divisibility. It does not rerun the reduction algorithm or rely on a modular rank estimate. Operation, allocation and intermediate-entry budgets fail without returning a partial certificate. Replay establishes arithmetic consistency in this Python checker; it does not make Python execution formally verified.

For `A x = b`, set `x=V z`. The equation becomes `D z=U b`. A solution exists exactly when each of the first `r` transformed entries is divisible by its corresponding `dᵢ`, and every remaining entry is zero. A failed divisibility produces a row `h` with `h A ≡ 0 mod d` but `h b ≠ 0 mod d`. A failed zero row produces `h A=0` and `h b ≠ 0`.

For a surviving fibre, the first `r` coordinates of `z` are fixed quotients and the remaining coordinates are arbitrary integers. Consequently the result is exactly

`x = x₀ + t₁ k₁ + ⋯ + tₙ₋ᵣ kₙ₋ᵣ`, with every `tᵢ ∈ Z`.

The kernel vectors are the last columns of `V`. Because `V` is unimodular, these form the entire integer kernel, including its saturation. Clearing denominators of individual rational basis vectors would be insufficient: for `2x+y+z=0`, vectors `(-1,2,0)` and `(-1,0,2)` miss `(-1,1,1)` in their integer span.

## Interfaces that use the complete fibre

`solve_integer` returns the particular solution, saturated kernel basis, parameters and shared reduction certificate, or an obstruction. For `2x+3y=1`, the result is `(-1+3t, 1-2t)` for every integer `t`. The prior rational routine's chosen lift `(1/2,0)` remains valid over Q, but cannot decide integer solvability by itself.

`integral_task_section` solves all columns of `carrier*T=target` with one carrier reduction. Kernel parameters are independent for each target column; the returned count covers the complete family of integral sections. It does not assert injectivity.

`integral_intertwiners` builds the simultaneous equations `T Aᵢ=Bᵢ T` and returns a saturated integer basis of their solution module. It preserves every supplied context. A nonzero module does not by itself prove an integral isomorphism. `compare_column_lattices` constructs transports both ways, or returns the first failed inclusion and its witness.

`perfectpower.integer_projection.project_integer_query` recognizes direct affine equalities in one existential QF_NIA query, solves them together over Z, and substitutes the complete fibre into every remaining assertion. Direct conjunctions are flattened; equalities inside disjunctions or negations are never imposed globally. Unsupported commands, binders, undeclared symbols and ill-sorted expressions are rejected. Fresh integer parameters replace the original constants. `IntegerProjection.lift` reconstructs an original-variable model from integer parameter values.

This is existential elimination with a bijective fibre parameterization, not free-variable equality between formulas in different coordinates. Residual polynomial constraints, comparisons, Boolean combinations and integer `div`/`mod` expressions retain their meanings. A divisibility obstruction yields `false`. A remaining nonlinear product keeps QF_NIA; the existing sort checker selects QF_LIA only when the entire result is linear. No bounded point scan supplies a completeness claim.

## Repository replay and verification

Run `python python/recover_integer_lifting.py` from the repository root. This rebuilds the complete arithmetic receipt and eight original/projected SMT files using the standard library. Add `--z3` to check the four designed query examples and replay both surviving models on their original formulas; the optional industrial dependency provides Z3.

The runner audits all 23 actual entries in `receipts/order_transports.json`, matches each lattice index and reconstructs its three basis vectors: 69 exact pullbacks. A 12-by-18 presentation illustrates the practical difference between exhaustive minors and constructive reduction. The old routine exceeds its 100,000-minor budget; the new routine performs 174 elementary operations and returns six integer parameters. This is an algorithmic capability demonstration, not an industrial speedup benchmark.

The 17 new tests compare 180 random Smith reductions with the independent exhaustive-minor implementation, compare 180 random integer fibres with independent lattice-index membership, reconstruct every small solution in 25 random systems, check 30 constructed task sections, reject corrupted transcripts, exercise resource limits, and preserve nonlinear residual semantics and lifted models. The full-suite and cold-archive results are recorded beside the receipt. Existing formal results retain their original trust status; this release adds constructive exact execution, without claiming newly compiled Lean declarations.
