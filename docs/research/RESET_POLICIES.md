# NX05: exact adaptive policies across independent resets

This track concerns a finite candidate population, finite scalar experiment
pool and positive rational costs. Every selected experiment is independently
reset, and its error is adversarial within its candidate-specific closed
interval. Persistent nuisance learning and a continuing physical trajectory are
different contracts handled by NX02 and NX06.

## Exact finite abstraction of continuous observations

`ResetExperimentFamily` retains original candidate IDs, target labels, costs and
an experiment-by-candidate table of closed intervals. A belief S is a tuple of
possible original candidates. An observation y in experiment e updates it to

\[
S_{e,y}=\{c\in S:l_{ec}\le y\le u_{ec}\}.
\]

`observation_cells` collects every endpoint among these intervals. Each endpoint
is a separate singleton cell. Consecutive endpoints bound an open cell, and the
two exterior rays are retained as explicit model-rejection regions. Rational
midpoints represent bounded open cells; one unit beyond the extreme endpoint
represents each ray. Membership is constant on every open cell because interval
membership can change only at an endpoint. Direct comparison at the endpoint
itself gives the separate closed-boundary membership.

For [0,1] and [1,2], y=1 is compatible with both candidates. A branch compiler
that omits this singleton would falsely certify guaranteed identification.
Point, duplicate, nested and disjoint intervals are all covered by the same
construction. Empty-consistency cells do not enter adversarial worst-case cost,
but runtime replay returns `model_rejected` when an actual reading lands there.

## Proper-policy theorem and Bellman recurrence

The error contract is memoryless across resets: conditional on a candidate,
any value in each test's interval remains possible regardless of earlier
numeric readings. Thus the set S is a sufficient belief. A terminal belief has
one target label, even when several original configurations share that target.

Suppose a finite guaranteed policy chooses a test with a possible branch that
retains all of S. Its subtree on that branch must itself solve the same S
problem, because no candidate or persistent nuisance has been eliminated. Use
that subtree immediately, omitting the first test. It remains valid for all
candidates and costs strictly less on every path through the deleted test.
Repeating this deletion yields a policy whose every nonterminal child is a
strict subset of its parent belief.

**SNG-NX05-01.** A finite worst-case optimum, if one exists under the declared
memoryless interval contract, is attained by a proper strictly shrinking policy.
Its depth is at most K-1 for K original candidates. Consequently the complete
recurrence is

\[
V(S)=0\quad(T\text{ constant on }S),
\]
\[
V(S)=\min_{e:\,S_{e,Q}\subsetneq S\ \forall Q}
\left[c_e+\max_{Q:S_{e,Q}\ne\varnothing}V(S_{e,Q})\right].
\]

An experiment with a same-S branch is excluded, not assigned an optimistic
finite value. If every experiment is excluded or reaches an impossible child,
no finite guaranteed policy exists. The proof would fail for persistent gain
or calibration, where numeric observations can constrain hidden parameters
while leaving the candidate ID set unchanged; this solver does not claim that
broader setting.

`minimum_reset_policy` memoizes exact beliefs, with a default 100,000-belief
budget. Each candidate interval contributes at most two endpoints, so there
are O(K) cells per experiment before equal child beliefs are consolidated.
The number of possible beliefs remains exponential. A budget refusal is
inconclusive and cannot be reinterpreted as impossibility.

## Certificates, costs and independent replay

Every node records its complete original belief, selected experiment, exact
endpoint cells, all nonempty children and worst-case subtree cost. Leaves retain
the target and every remaining original ID. The certificate also stores all
completed Bellman values. `verify_reset_policy` recomputes the continuous cell
partition, checks every possible branch, rejects cycles, checks target-pure
leaves and recomputes the exact maximum path cost. It also recomputes the finite
Bellman optimum before accepting an optimality claim. Runtime `replay_policy`
returns an identified target, a partial transcript awaiting more readings or
explicit model rejection; an empty candidate set is not a successful diagnosis.

The four-candidate worked example has one test dividing AB from CD and two
branch-specific tests that identify B or D. The adaptive policy costs two.
Every fixed two-test panel leaves a pair ambiguous, while all three tests
suffice. The one-test lower bound follows because each individual test has an
ambiguity cell of size at least two. The tests independently enumerate finite
trees to depth K-1 on twenty-five random rational interval instances and obtain
the same optimum or impossibility result. That oracle directly evaluates
endpoint inequalities and does not call the production cell compiler or
Bellman routine.

## Thermal comparison on identical contracts

The primary retained experiment uses the unchanged six source-derived
12-by-12 candidates and all 112 original protocols. Initial radius and sensor
noise remain 1/100, with original per-candidate radii, costs, heater words and
sensors. The static and adaptive solvers therefore optimize the same physical
and uncertainty contract. Both return exact worst-case optimum twenty. The
adaptive engine does not claim an improvement where a single existing test
already attains the minimum.

A second comparison uses the first eight original configurations from the
79-mask four-by-four pilot, twelve predeclared short protocols, zero reset
radius and sensor error 1/100,000. Both static and adaptive exact-location
identification are impossible within that declared pool. All original mask IDs
are retained, and the failed ambiguity branches are part of the evidence.
This negative result prevents an adaptive planner from appearing to solve a
measurement-language limitation by merely choosing its tests in a new order.

Costs are worst-case sums of actual reset experiments. No prior is supplied,
so no expected cost or branch probability is claimed. Repeated adversarial
bounded-noise tests cannot be averaged as if their errors were random Gaussian
samples. The receipt records the full policy, Bellman values and static result
for both comparisons. Run `PYTHONPATH=src python scripts/adaptive_thermal.py --check`.
