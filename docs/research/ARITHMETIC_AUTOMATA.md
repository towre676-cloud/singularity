# NX20: finite quadratic-unit residue experiment automata

This adapter turns a declared arithmetic seed population into a finite exact experiment language. It preserves original seed IDs, distinguishes modular collisions from observational equivalence, and evaluates remote residues without constructing enormous Pell coordinates. It makes no claim to enumerate all global Pell seeds.

## Certified arithmetic actions

A unit is specified by nonsquare \(D>0\) and integers \(a,b\) satisfying

\[
 a^2-Db^2=1,\qquad U=\begin{pmatrix}a&Db\\b&a\end{pmatrix}.
\]

Multiplication sends \((x,y)\) to \((ax+Dby,bx+ay)\). Direct expansion gives

\[
 (ax+Dby)^2-D(bx+ay)^2=(a^2-Db^2)(x^2-Dy^2)=x^2-Dy^2.
\]

Also \(\det U=1\), and the inverse is obtained by replacing \(b\) with \(-b\). These identities certify integral norm preservation and invertibility modulo every positive modulus, including composite moduli. The constructor rejects square or nonpositive \(D\), malformed units, floats and booleans.

For \(D=2\), \(a=3,b=2\), the integer sequence beginning at \((1,0)\) starts

\[
 (1,0),(3,2),(17,12),(99,70),\ldots
\]

Every retained integer step is checked by direct quadratic multiplication. Modulo five its exact cycle is

\[
 (1,0)\to(3,2)\to(2,2)\to(4,0)\to(2,3)\to(3,3)\to(1,0).
\]

The cycle is computed, not copied as an assumed fixture. Bounded repeated integer multiplication and an independent cycle-remainder calculation check the remote implementation.

## Which finite population is represented?

Input seeds form a nonempty mapping from stable string IDs to original integer pairs. Their provenance is retained verbatim as a scope declaration. The state constructor begins with their actual reductions and closes under the declared legal actions. It does not replace that set with every solution of a modular norm equation.

Two projections remain explicit:

\[
 \{\text{original seed IDs}\}\longrightarrow
 \{\text{generated residue states}\}\longrightarrow
 \{\text{behavioral classes}\}.
\]

For example, original seeds \((1,0)\) and \((6,0)\) collide modulo five but remain separate IDs with separate original norms. Their modular equality does not assert global orbit equality or even equality of the original norm equation. Conversely, original seeds \((1,0)\) and \((4,0)\) have equal initial \(y\)-sensor output modulo five but become distinguishable after one unit action: their readings are two and three. The cheapest witness has action cost one when that cost is declared as one.

The norm-congruence class can contain residues outside a chosen seed orbit. The adapter's closure is derived from the actual supplied seed images, and the tests retain this distinction. No global completeness conclusion follows from covering the finite closure.

## Exact observations and chronological words

Each sensor reads \(x\), \(y\), or \(x^2-Dy^2\) modulo the declared modulus. Every output symbol becomes an indicator row. Thus equal readings correspond exactly to equal indicator vectors over \(\mathbb Q\); numerical addition of residue values is not confused with finite-field equality.

For a finite transition \(f_i\), the column-state matrix is \(M_i e_s=e_{f_i(s)}\). A chronological word \((i_1,\ldots,i_k)\) applies \(i_1\) first, giving

\[
 L_jM_{i_k}\cdots M_{i_1}e_s.
\]

The adapter uses the existing observability closure and cheapest-distinguishing-experiment contracts. Independent finite-machine partition refinement computes the same all-future equivalence classes. The test begins with the sensor-output partition and repeatedly refines by successor classes until stable. This oracle uses transition tables directly, without rational row-space elimination.

A sensor reading only the norm residue is forever blind between two states in the same norm class, because every legal unit action preserves the norm. The permanent fixture records such a genuinely all-future equivalent pair. This is a theorem for the declared finite sensors and actions, not a statement that the original arithmetic objects coincide.

Observation costs and positive action costs are exact rationals. Different sensor costs survive compilation by assigning the cost to every symbol-indicator row of that sensor. The least-cost witness returned by the existing engine therefore remains a real sensor/action experiment. One-hot dimension and dense-matrix limits are checked before allocation; a residue space can contain \(m^2\) states, so unrestricted dense compilation is not implied.

## Commuting units and a restricted noncommuting extension

Units in the same quadratic field commute. Their matrices have the form \(aI+bK\), where \(K^2=DI\), so multiplication is a commutative polynomial calculation. Adding more such units cannot create order sensitivity.

Conjugation is a separately declared action

\[
 J=\operatorname{diag}(1,-1),\qquad JUJ=U^{-1}.
\]

It preserves the norm but can leave a positive-coordinate seed convention. The API therefore requires `signed_states=True` before allowing it. For \((1,0)\) modulo five, unit then conjugation gives \((3,3)\), while conjugation then unit gives \((3,2)\). The actual chronological column-state actions reproduce this difference. The receipt treats this as a signed norm-preserving language, not as a positivity-preserving Pell iteration.

No arbitrary reset, projection or translation is called a Pell symmetry. Unsupported partial actions are rejected rather than silently becoming identities. Extending the action alphabet requires a new legality contract.

## Remote residues without giant integer coordinates

`remote_residue` accepts a nonnegative integer or a decimal digit string. To process a decimal prefix exponent \(k\) and next digit \(d\), update

\[
 U^{10k+d}=(U^k)^{10}U^d\pmod m.
\]

Small binary matrix powers perform each step. This avoids parsing a thousands-digit integer into Python's bounded decimal conversion path and avoids constructing the enormous exact Pell coordinates. Negative indices require an explicit inverse-action flag and use the certified inverse unit.

The retained remote index has 6,000 decimal digits, the pattern `9876543210` repeated 600 times. Decimal-stream matrix powering matches independent digit-stream reduction modulo the separately computed cycle length. The output is a residue pair. Nothing in the receipt claims that the corresponding full integer coordinates were computed cheaply.

## Serialization, tests and completion boundary

`singularity.arithmetic-orbit/1` records the exact field/unit, modulus, original seeds and their norms, provenance, generated residue states, seed-to-state map, named actions, action and sensor costs, transition tables, signed-state contract and explicit scope. Replay reconstructs arithmetic transitions and requires exact equality with the serialized receipt; an altered original norm is rejected. The tests cover modulus one, composite moduli, negative residues, malformed units, original modular collisions, forever-equivalent states, costed witnesses, huge indices and conjugation chronology.

Implementation: `src/singularity/arithmetic_automata.py`. Tests: `tests/test_arithmetic_automata.py`. Run `python scripts/arithmetic_automata.py --check` for the retained exact evidence. Completion concerns the finite declared population and language. Arbitrary Pell seed completeness, global orbit identification, positive global branch conventions and duplicate removal across a future PerfectPower adapter require separate mathematical proofs.
