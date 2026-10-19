# NX03: whole original populations of bond faults

The module `fault_population.py` replaces a hand-picked list of hypotheses by
an exact constrained population of original Boolean masks. It implements all
three NX03 units without altering the historical six-candidate constructor.
Configuration multiplicities and physical labels remain part of the contract.

## Exact populations and prefix completion counts

For ordered distinct bond IDs e_1,...,e_m, the original population is

\[
\Omega=\{\theta\in\{0,1\}^m:R\theta\le b\}.
\]

`FaultPopulation` accepts integer inequalities, an optional cardinality cap,
an optional source-model digest and a completion-state budget. General signed
integer rows are allowed, so coupling constraints such as theta_1+theta_2<=1
and theta_3+theta_4<=theta_2 are not reduced to independent cardinality limits.
The domain is explicitly Boolean; arbitrary integer coordinates or floating
constraint coefficients are rejected.

For a prefix p of length t, subtract its contribution from each original
constraint. The memoized state consists of t and this residual right-hand side.
The smallest possible remaining contribution of row r is the sum of its
negative coefficients. If that lower bound exceeds the residual bound, the
prefix has no completion. At t=m every surviving state is a feasible original
mask. Otherwise

\[
C(p)=C(p0)+C(p1).
\]

**SNG-NX03-01.** The completion recurrence, with the stated rejection rule,
counts every original feasible Boolean mask exactly once. This follows by
partitioning completions according to their next bit; the lower-bound rejection
cannot discard a feasible assignment. Memoization identifies equal residual
subproblems but adds their original multiplicities through the recurrence.

Lexicographic rank adds C(p0) when the next bit is one. Unrank compares the
requested index with C(p0), follows the zero branch when smaller and subtracts
that count before taking the one branch otherwise. Induction on remaining
length proves that these maps are inverse. Enumeration is implemented by
unranking all integer indices; its own mask-count budget is separate from the
completion-state budget. Conditioning retains the complete original masks that
satisfy a caller predicate. A count is not a probability and a uniformly sampled
compressed state is not a uniformly sampled fault.

The worked three-bond at-most-one population has masks 000,001,010,100.
Prefix zero has three completions and the final mask has rank three. More
generally, summing counts over every prefix at a fixed depth partitions the
original population and returns its total count.

## Source-consistent physics of simultaneous faults

`fault_candidate` takes an existing exact `AffineCandidate`, an original mask,
canonical undirected bonds and the declared nominal bond conductance k. It
rejects repeated or reversed duplicate bonds, invalid endpoints and a selected
edge whose two off-diagonal conductances do not equal k. Each selected bond
updates

\[
A_\theta=A_0+k\sum_i\theta_i(e_{u_i}-e_{v_i})(e_{u_i}-e_{v_i})^T.
\]

The off-diagonal entries lose k and both endpoint diagonal entries gain k.
Thus symmetry and each row sum are preserved. Removing only off-diagonal
entries would incorrectly add an ambient loss term. Distinct simultaneous
faults may share endpoints; their diagonal increments add and do not remove a
bond twice. Every result retains the source heater and sensors. Its identifier
contains the full original mask, even if another configuration happens to give
identical readings.

`plate_bonds` specifies row-major canonical undirected adjacency. The retained
12-by-12 pilot uses the explicitly frozen list

\[
\begin{split}
&(0,1),(0,12),(1,2),(1,13),(2,3),(2,14),\\
&(3,4),(3,15),(4,5),(4,16),(5,6),(5,17).
\end{split}
\]

At most two blocked bonds therefore gives 1+12+66=79 original models. The full
plate has 264 undirected bonds and the analogous population count is
1+264+34,716=34,981. This larger number is a count only, not a claim that all
models and all long protocols have been simulated. The physical tiny check uses
the two-by-two plate, whose four bonds yield eleven configurations.

## Complete declared-pool diagnosis

`pilot_fault_candidates(12)` returns the population together with all 79
`AffineCandidate` models. No graph symmetry or duplicate reading merges the
location identities. A source digest hashes the exact nominal matrix, heater
and sensors. The diagnostic receipt retains every mask, its model identifier,
every reading and every candidate-specific error bound, so the ordinary NX01
decoder can return all compatible original configurations.

The retained protocol pool is fixed before inspecting results: words (2,0) and
(2,0,...,0) of length twelve, each observed with the four original sensors.
Its eight experiments define a complete finite optimization problem. The exact
zero-noise readings produce sixty behavioral classes among the 79 masks, so
exact location identification is impossible within that pool. The receipt
lists each original-mask class and every uncoverable target pair. This is not
an all-future equivalence claim: later words or extra sensors may split those
classes. With independent error 1/10,000, all pairs are uncoverable in this
particular distant-fault pilot, illustrating the distinction between exact
arithmetic separation and robustly useful measurement.

The optimizer's infeasible status is a completed finite-pool proof, not a
search-budget failure. The broader problem of finding a sufficiently powerful
physical experiment language remains separate. The fixed-pool negative result
therefore completes the declared pilot while explicitly retaining the reason
to expand the sensor/protocol language.

## Independent checks and resource contract

Every two-by-two mask is compared against a separately written undirected-flux
update on a nonuniform rational state. This checks all eleven models, all row
sums, matrix symmetry, nonnegativity and preservation of the original heater
and sensors. Two removed bonds sharing endpoint zero are checked explicitly.
Tiny coupled populations agree with literal Boolean products; all rank/unrank
round trips and every prefix-partition sum are checked. The 79-model receipt
independently propagates selected masks through both short and twelve-step words
using the neighbour-flux oracle, without importing the new matrix assembler.

Completion counting has exponentially many possible residual states for general
Boolean inequalities. The default limit is 100,000 states; enumeration has a
separate 100,000-mask limit. Exceeding either raises a work refusal and cannot
be interpreted as an empty population. The 79-model optimizer uses the existing
bounded exact candidate-box engine, and its status is retained verbatim.

Run `PYTHONPATH=src python scripts/fault_population_diagnostics.py --check`.
The receipt includes source provenance, source-model digest, all masks, prefix
partition, raw readings, original behavioral-class multiplicities, independent
flux spots, optimizer evidence and rational bit-length statistics.
