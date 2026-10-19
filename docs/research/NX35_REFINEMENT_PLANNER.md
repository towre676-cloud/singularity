# NX35: proof-directed finite computational refinement

For independently reset scalar observations and target-distinct candidate pair
\(a,b\), a robust separating test has positive margin

\[
m_{e,ab}=|r_{e,a}-r_{e,b}|-\rho_{e,a}-\rho_{e,b}>0.
\]

This is specifically independent scalar interval geometry. It must not be used
as a substitute for joint correlated uncertainty-set separation. Given certified
margin intervals \([l_{e,ab},u_{e,ab}]\), define certain and possible masks by
\(l>0\) and \(u>0\), respectively. Equality at zero never counts as coverage.
Every true test mask lies between these masks. Every cover feasible in the
certain world is truly feasible, and every true cover is feasible in the
possible world. Hence

\[
\operatorname{OPT}(S^+)\le\operatorname{OPT}(S)
\le\operatorname{cost}(E^-).
\]

The implementation solves each finite mask cover by exact prefix dynamic
programming. A state stores the least cost for the covered-pair union after
processing an experiment prefix. Adding or omitting the next experiment gives
the complete recurrence; positive costs and a finite pool ensure termination.
Its complexity can be exponential in the required pair count. A declared state
budget refusal does not establish infeasibility or optimality.

The deterministic planner examines an unresolved cell on a cheapest optimistic
competitor, requests a tighter certified enclosure, intersects it with the old
enclosure, and updates both cover bounds. Source/candidate/domain bindings must
be identical. Disjoint purported enclosures or reversed fidelity levels are
rejected. A stalled oracle is recorded and blocked; exhausted work returns a
valid incumbent and unresolved gap. When a concrete certainly feasible panel
has cost equal to the optimistic lower bound, optimality follows without
evaluating every cell at maximum fidelity.

The three-test exact example initially has lower bound one and upper bound
two. Refining the single uncertain zero margin of the first test raises the
lower bound to two. The expensive all-pair test need not be refined. Independent
enumeration of every tiny panel checks the two inequalities and final optimum.

## Typed NX09 integration

`BoundedReading` separates computational radius from physical uncertainty. If
the computed center difference is \(d\), combined computational error is \(e\),
and combined physical radius is \(\rho\), a valid margin enclosure is

\[
[\max(0,|d|-e)-\rho,\ |d|+e-\rho].
\]

The adapter checks equal units, horizon and reset/input domain. Refining
arithmetic or a reduced model can shrink \(e\), but cannot erase an assumed
physical or source radius. The integration calls the actual source-pinned
DynaComp evaluator separately for every model/sensor/word/fidelity combination;
it never transplants a nominal certificate to another fault.

The retained synthetic 4-by-4 example uses the original nominal,
conductance-half and heater-half hypotheses, preserving their IDs. Its finite
pool has two reset protocols: left-center observation after \((2,0,2)\), cost
one, and center observation after \((2,2)\), cost two. Physical error radius is
the declared assumption \(1/100000\). Six initial rank-one model evaluations
give a feasible cost-two plan and an optimistic cost-one competitor. Only the
nominal and conductance-half readings of that competitor need enrichment.
Two higher-fidelity evaluations certify its true positive gap and the cost-one
optimum, compared with six higher-fidelity evaluations for the complete baseline.

Validation performs the remaining four fine evaluations separately and checks
all coarse/fine envelopes against full exact sparse thermal predictions. They
are reported as validation work, not hidden inside the planner's two-call claim.
A second retained case enlarges the physical/source radii so that even exact
arithmetic cannot separate the candidates. Its optimistic cover is infeasible:
more digits cannot repair that model limitation.

The complete margins, refinement transcript, source evaluator records, calls,
incumbent and lower bound are in `results/nx36/nx35_acceptance.json`. The claim
is a finite-pool accounting optimum under the stated source and uncertainty
premises, not hardware-global experimental optimality.
