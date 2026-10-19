# Local arithmetic and shared operator machines

PerfectPower now uses two further mechanisms from the older work: local arithmetic remains factored by prime and depth, and related linear output programs share an exact minimal state machine. The first strengthens the integer solver's finite leaves without constructing a huge combined residue table. The second replaces redundant recurrence state with a smaller exact rational representation while preserving every future output, including outputs of noncommuting operator words.

These are classical mechanisms implemented and adapted to the supplied arithmetic workloads. They introduce no new mathematical priority claim. Their certificates replay in Python; this development performs no new Lean compilation.

## The recovered sources and their adaptation

The selected source is DBB, *Mixed CRT & Ramified Locality*, in `level_deformation_monograph_v4_54_1(5).html`, a 4,053,819-byte version of *The Level and the Deformation*. The selected source window is lines 12076–12155; the DBB excerpt and its hash are retained in `receipts/lost_work_development/source_excerpt.json`. It distinguishes locality across coprime factors from depth within a prime-power factor. The adaptation uses that distinction for integer power membership and finite searches. It does not reproduce the original quantum SELECT system, Weil commutant calculations, or hardware estimates.

The Wilson/Forge donors are the archived `DUAL_HANKEL_EXECUTION_SEMANTICS_v26.md` and `TASK_DESIGNED_DICTIONARY_AND_EXECUTION_v24.md`. They distinguish written matrix-product order from chronological execution on columns and reduce exact residual machines through Hankel structure. Their source paths and hashes, together with the earlier arithmetic/operator monographs checked for overlap, are in `source_review.json`. This development minimizes an unbounded linear word-output representation over the rationals. It does not claim the older Wilson 81-call program has been improved, or reinterpret nonlinear arithmetic descent as a linear automaton.

## Local power membership with zero and valuation retained

For a residue t modulo pᵃ, zero is always a d-th power. Otherwise write

\[
t=p^v u,\qquad 0\le v<a,\quad p\nmid u.
\]

It is a d-th power exactly when d divides v and u is a d-th power in the unit group modulo pᵃ⁻ᵛ. The valuation condition is essential: unit-only tests can incorrectly admit nonunits.

For odd p, the unit group is cyclic of order

\[
\varphi(p^k)=(p-1)p^{k-1},\qquad k=a-v.
\]

In a cyclic group of order N, an element u belongs to the image of the d-th-power map precisely when

\[
u^{N/\gcd(d,N)}=1.
\]

This supplies membership by one modular power rather than enumerating every possible root. The implementation tests primality for its supported p ≤ 257 and handles d between 2 and 64.

Two is treated separately. The unit group modulo 2ᵏ is trivial for k=1, cyclic of order two for k=2, and `C₂ × C₂^(k−2)` for k≥3. An odd d induces a bijection on that group. For even d and k≥3, membership is

\[
u\equiv1\pmod{2^{\min(k,v_2(d)+2)}}.
\]

For k=2, it is u≡1 modulo four. Thus fourth powers, eighth powers, and deeper dyadic conditions are not processed by the odd-prime cyclic rule. The public `power_residue` predicate supports large depths without an explicit residue table, with bounded integer input and exponent sizes.

Primary background and proofs of the unit-group structure are in [Keith Conrad, *Prime Powers Units and Finite Subgroups of GLₙ(Q)*](https://kconrad.math.uconn.edu/blurbs/gradnumthy/primepowerunitsandGLnQ.pdf), especially Theorems 1.1 and 2.3. The predicate is checked against independently enumerated root images over every p in `{2,3,5,7}`, depth 1–4, and exponent 2–16.

## Complete depth tables and bounded factored search

At depth one, inspect each residue r modulo p. At the next depth, inspect every r+t pᵉ above each previously retained r, with 0≤t<p. A discarded parent cannot have a surviving child: any root modulo a higher power projects to a root below. The receipt records every retained level and the number of tested lifts. Singular and zero-valued branches remain present; no smoothness assumption is imposed. This is complete residue lifting, not an assertion that every survivor lifts forever to a p-adic root.

Explicit tables are limited to modulus 65,536 and have a construction budget checked before cache use. `verify_prime_power_table` rebuilds the complete finite levels and their metadata. The additional default factors are

\[
2^8,\ 3^4,\ 11,\ 13,\ 17,\ 19,\ 23,\ 31.
\]

They accompany the existing wheel modulo `lcm(16,9,5,7)=5040`. Their combined least common multiple is **23,901,277,720,320**, but no allowed-residue vector of that length is built. Candidates come from the original wheel's progressions inside the requested interval, then pass the additional local membership tables before exact root extraction. Overlapping prime powers are conjunctions, not independent CRT factors. The nominal combined modulus describes periodicity, not allocated memory or enumerated work.

If any individual table is empty, the equation is globally impossible. Otherwise, survival is only a necessary local condition. The bounded scanner returns every solution in its closed interval; it makes no claim beyond that interval. Separate limits govern base progression candidates and surviving root extractions, and exceeding either raises without a partial answer. The default base-candidate limit is two million. Large nominal periods therefore do not license an unbounded interval scan.

The arithmetic engine adapts automatically when a finite leaf has at least 128 base-wheel candidates and at most two million. Smaller leaves retain the cheap existing wheel. The independent result replay recognizes both historical wheel receipts and the new factored schema. The new schema does not retroactively modify the earlier archived receipts.

For the complete equation

\[
y^3=x^6+x-10^{20},
\]

the sharp-gap machinery gives a central interval `[-100000,100000]` and a separate residual-zero fibre at x=10²⁰. The original wheel would check 4,763 central candidates; the factored filters retain 119. The exceptional fibre is checked separately, giving 120 root checks in total. The complete answer is exactly `(10²⁰,10⁴⁰)`. Filtering the central interval does not erase this distant solution.

On the bounded degree-64 equation `y¹⁰=x⁶⁴+x+1`, for `−10000≤x≤10000`, root extractions fall from **2,225 to 16**, with the same four signed points. This is bounded completeness, not a global classification of that equation. Recorded alternating warm-cache timing comparisons are in `benchmark.json`, separate from the deterministic receipts.

In five alternating repetitions on this host, median bounded-scan times were 0.073093 seconds for the old wheel versus 0.002791 seconds for the factored filters on the degree-64 example, and 0.025773 versus 0.003983 seconds on the cubic-power central interval. The quadratic-square offset example improved more modestly, from 0.002577 to 0.002033 seconds. These measurements include certificate replay and exclude initial cover construction; they are constructed warm-cache scan comparisons, not a claim about industrial workloads or the full solver's end-to-end speed.

All 12,320 preceding plain/affine arithmetic cases still solve completely and replay, retaining the same 5,255 plain and 1,362 affine point occurrences. Their aggregate surviving root checks remain 11,203: those already-small leaves do not account for the larger gains in the new stress cases.

## Minimal machines preserve future observations

Let A₁,…,Aₛ be exact rational n×n operators, γ a seed, and H a matrix of requested readouts. The output of a chronologically executed word `(i₁,…,iₜ)` is

\[
H A_{i_t}\cdots A_{i_1}\gamma.
\]

A written algebra product `A_i₁…A_iₜ` acts on a column in reverse order. Both conventions are exposed explicitly. The two unipotent examples in `observable_examples.json` give output one in execution order and two in written order for the same letter list. Swapping the convention would change an actual answer.

Start with the span R of every state reachable from γ. Beginning at γ, extend an independent basis by generator applications until every image lies in the span. Each basis vector retains its actual executed word. With the basis columns in J, the receipt provides restricted transitions Bᵢ and an initial coordinate vector z₀ satisfying

\[
A_iJ=JB_i,\qquad Jz_0=\gamma.
\]

These identities and the word witnesses prove that J describes exactly the reachable states: it contains the seed, is invariant, and its columns were actually reached. Unreachable ambient directions are removed.

Now start from the rows of HJ and close their span under right multiplication by every Bᵢ. Put an independent row basis in O. The receipt records the readout and chronological future word that produced each row, as well as compressed transitions Cᵢ and an output decoder D satisfying

\[
OB_i=C_iO,\qquad HJ=DO.
\]

The compressed seed is q₀=Oz₀. By induction on every finite word,

\[
H A_{i_t}\cdots A_{i_1}\gamma
=D C_{i_t}\cdots C_{i_1}q_0.
\]

This removes only states that are invisible to **all future** readouts. A state invisible now can become visible after another operator; the row closure retains that distinction. Independent tests cover noncommuting generators, rational inputs, nilpotent and zero cases, and every word of length at most four in random small systems.

The state dimension is minimal over Q for these supplied outputs. A finite Hankel block has entries given by applying each witnessed future readout to each witnessed reachable state. In the chosen coordinates this block is O. Its rank k provides a lower bound on the dimension of any linear realization of the same word outputs. A nonsingular k×k minor and its determinant are recorded. The constructed k-dimensional machine achieves that bound. Minimal state dimension does not imply minimum primitive calls, shortest operator words, integral compressed coordinates, or identification of an OEIS definition.

`verify_machine` checks the recorded words, basis independence, both intertwining identities, decoder identity, seed, and nonzero Hankel minor without discovering or minimizing either span. Zero-output behavior has the exact zero-dimensional realization. The bounded matrix, word, product, and rational-entry budgets raise explicitly; there is no universal bit-complexity claim.

Primary background is [Stefan Kiefer, *Notes on Equivalence and Minimization of Weighted Automata*](https://arxiv.org/abs/2009.01217). The implementation uses exact rational elimination rather than floating SVD or approximate model reduction.

## Shared execution on the actual recurrence models

`recurrence_batch` forms one block operator from supplied recurrence definitions and exposes all their first-coordinate readouts. It then minimizes that combined machine. The 135 stored reconstructed models form 40 groups by their exact coefficient vectors. Together they require **368 state coordinates** when represented separately and **121 coordinates** in their shared minimal machines. The eleven stored Fibonacci-type models in one group share two coordinates instead of twenty-two.

The runner independently compares all model outputs at indices 0, 1, 2, 10, 50, and 100 against the existing exact `Recurrence.nth` implementation, for 810 value comparisons. The finite identities prove preservation for every future index of the supplied models; the sampled comparisons are independent execution checks. These are models reconstructed from finite prefixes, and their agreement with the original OEIS definitions retains its earlier status. Binary powering through `power_outputs` evaluates long repeated words in the shared machine.

## Run and reproduce

```sh
python python/develop_lost_work.py
PYTHONPATH=python python -m perfectpower factored-scan --coeff '[1,1,0,0,1]' --d 2 --lo -10000 --hi 10000 --verify
PYTHONPATH=python python -m perfectpower observable-machine --operators '[[[2,0],[0,3]]]' --seed '[1,1]' --readouts '[[1,0]]' --word '[0,0]' --verify
PYTHONPATH=python python -m perfectpower recurrence-batch --models '[{"coefficients":[1,1],"initial":[0,1]},{"coefficients":[1,1],"initial":[2,1]}]' --index 100 --verify
PYTHONPATH=python python -m unittest discover -s python/tests
```

Optional `--benchmark` records timing separately. The deterministic output includes the six arithmetic receipts and four local/machine receipts. This development adds 23 focused tests; the full core suite runs 658 tests with four dependency skips. Source hashes and fresh-copy reproduction checks are retained with the results. New Lean verification of these prime-power predicates, lifting tables, factored scan assembly, and minimal-machine certificate interfaces remains separate work; inherited Lean proofs are not relabelled as proofs of these new Python programs.
