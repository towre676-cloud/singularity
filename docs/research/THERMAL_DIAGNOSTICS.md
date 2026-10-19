# Source-pinned thermal experiment design

This pilot connects Singularity's exact experiment-panel optimization to a concrete model already developed in DynaComp. It starts from the actual 144-state rational plate generator, preserves the original nominal transition and heater, introduces six explicit fault hypotheses, and asks which affordable observations identify them despite a stated error envelope. It is a synthetic discrete-model experiment. It is not measured fault detection, a calibrated digital twin, or an empirical claim about an installed thermal system.

## Source and mathematical model

The source is [DynaComp commit cd788c7](https://github.com/towre676-cloud/DynaComp/tree/cd788c7ac695728e3f5b22056a0f99a2c1e1463c), specifically [`src/dynacomp/thermal.py`](https://github.com/towre676-cloud/DynaComp/blob/cd788c7ac695728e3f5b22056a0f99a2c1e1463c/src/dynacomp/thermal.py), function `plate_model`. Its generating function and its complete 144-state output are retained in [`applications/thermal_diagnostics`](../../applications/thermal_diagnostics/README.md). The canonical nominal model has SHA-256 `d2b52864fae8e4e3344f3ab7fb25b9274d0452f7c4a91ad061b04efd6c2b4381`. Source-module and function hashes are bound separately. The source model was obtained by directly calling the pinned DynaComp function; the receipt reconstructs it independently by adding one Laplacian contribution per undirected grid edge.

Let the cells form a 12 by 12 nearest-neighbor grid, with row-major labels from 0 to 143. Write \(L\) for the unweighted grid Laplacian. The state is excess temperature above a fixed ambient in model-defined units. At one discrete time step,

\[
x_{t+1}=Ax_t+bu_t,\qquad A=(1-\lambda)I-kL,
\qquad k=\frac18,\quad\lambda=\frac1{100}.
\]

At each of the four central cells, \(b_i=1/4\); elsewhere \(b_i=0\). The original output is the average of the four corner coordinates. Every transition entry is nonnegative because \(4k+\lambda\le1\), and every row sum is \(1-\lambda\). Consequently the model preserves positivity and contracts the infinity norm by \(1-\lambda\). These are exact finite-matrix facts. No continuum discretization bound or empirical physical-parameter uncertainty follows merely from them.

For a deterministic input word \(w=(u_0,\ldots,u_{T-1})\), a candidate \(c\), and sensor row \(h_s\), the central predicted reading is

\[
r_{w,s}(c)=h_s\left(A_c^T x_0+
\sum_{j=0}^{T-1}A_c^{T-1-j}b_cu_j\right).
\]

In this formula \(A_c^T\) means the \(T\)-th power; it is not a transpose. The implementation evaluates sparse rational updates directly, so it does not form a dense matrix power. The protocol pool contains supplied step, first-pulse, last-pulse, and alternating input words at declared horizons. Each protocol reads one sensor at its final time. Repeating the experiment requires the declared reset; the cost includes reset, elapsed time, heater amplitude, and sensor use. These costs are model units rather than money, energy calibration, or instrument procurement prices.

## The finite hypothesis family

The nominal candidate uses the source coefficients unchanged. The conductance hypothesis replaces every \(k\) by \(k/2\). The heater hypothesis replaces \(b\) by \(b/2\). The loss hypothesis replaces \(\lambda\) by \(2\lambda\). The remaining two hypotheses block one interior bond immediately left of the central heater or its horizontal reflection on the right. On the 12 by 12 source these bonds are \(\{64,65\}\) and \(\{66,67\}\).

If \(v=e_i-e_j\), removing a bond of conductance \(k\) replaces \(A\) by \(A+kvv^{\mathsf T}\). The off-diagonal entries for that bond become zero and each endpoint diagonal increases by \(k\). This preserves symmetry, positivity, and the original row sum. Altering only the off-diagonal entries would change ambient loss and would describe a different hypothesis. Independent neighbor-flux checks explicitly cover this distinction.

There is no assertion that these six candidates exhaust faults in a real installation. Finite-candidate identification assumes that the true model is among them and that the declared error bounds hold. Unknown faults can produce no consistent candidate or can be observationally compatible with one retained model. That is a limitation of the declared population, rather than a uniqueness theorem outside it.

## Why the original observation cannot succeed

Let \(P\) reflect the grid horizontally. For the two blocked-bond candidates,

\[
A_{\rm right}=PA_{\rm left}P^{-1},\qquad Pb=b.
\]

The reset center is the zero field, so \(Px_0=x_0\). The original corner-mean sensor satisfies \(hP=h\). Induction gives \(x_{{\rm right},t}=Px_{{\rm left},t}\) under every scalar heater word. Therefore

\[
r_{w,\mathrm{corner}}(\mathrm{left})=
r_{w,\mathrm{corner}}(\mathrm{right})
\quad\text{for every finite }w.
\]

No search length can overcome this symmetry within the original actuator and sensor language. More computation of the same observations will not identify the fault location. The finite receipt confirms the obstruction on its pool; the reflection proof establishes it at every horizon. The same indistinguishability persists for uncertainty sets preserved by reflection when one considers sets of possible readings.

The enlarged language includes averages localized to the left and right parts of the central region as well as the central and corner means. These rows need not satisfy \(hP=h\). They can distinguish the reflected hypotheses. This is an explicit example of changing an allowed observation to eliminate an information obstruction; it does not claim that an unchanged symmetric experiment somehow recovered orientation.

## Error propagation and experimental meaning

The pilot uses an independent reset for each experiment with central state zero and componentwise initial radius \(\rho_0\). A candidate trajectory may also receive an additive process disturbance \(e_t\), where \(|e_{t,i}|\le\eta\), and its final sensor has additive error bounded by \(\nu\). Given nominal exact predictions, propagate a nonnegative coordinate radius vector by

\[
z_0=\rho_0\mathbf1,\qquad
z_{t+1}=|A_c|z_t+\eta\mathbf1,
\qquad \varepsilon_{c,w,s}=|h_s|z_T+\nu.
\]

The enclosure follows from \(|A_c d_t+e_t|\le|A_c||d_t|+\eta\mathbf1\) and induction. It is valid even without a contraction assumption. For this positive plate family, all sensor rows are nonnegative averages with row sum one, so a scalar bound is also available:

\[
\varepsilon_{c,T}=\nu+\rho_0(1-\lambda_c)^T
+\eta\frac{1-(1-\lambda_c)^T}{\lambda_c}.
\]

In the primary retained run \(\rho_0=1/100\), \(\nu=1/100\), and \(\eta=0\). The receipt also evaluates every combination of reset radius \(0,1/10000,1/1000,1/100\) and sensor noise \(0,1/1000,1/100\). These are supplied mathematical assumptions. They are not measurements of preparation quality or sensor hardware. The simulator performs exact rational arithmetic, so model-reduction error and numerical rounding error are zero in this run. No nominal DynaComp approximate-plan certificate is borrowed for changed fault models or output rows.

For a common panel-envelope contract, set \(\varepsilon_e=\max_c\varepsilon_{c,e}\). Then every candidate's admissible scalar reading lies inside \([r_e(c)-\varepsilon_e,r_e(c)+\varepsilon_e]\). Two candidates are robustly separated by experiment \(e\) exactly when

\[
|r_e(c)-r_e(d)|>2\varepsilon_e.
\]

The strict inequality is necessary for a guaranteed unique interval decoder at the boundary. Using a candidate-independent maximum can be conservative: pair-specific intervals could separate at a smaller margin. The retained optimum is exact for the common-envelope problem as stated. It is not a claim of optimality under every less conservative uncertainty representation.

## Exact panel selection and its limits

Each experiment covers the pairs it separates. A panel identifies the entire finite candidate population if its union covers every unordered pair. The existing exact weighted-cover solver chooses a least-cost panel within the declared finite pool. The receipt compares exact separation, box-robust separation, and greedy robust selection under identical costs and observations. Greedy output is feasible when it covers all pairs; it carries no minimum-cost guarantee.

The retained pool contains 112 experiment/sensor combinations and 672 exact candidate readings. At reset radius and sensor noise both \(1/100\), the cheapest robust panel costs 20 units: apply input 2 for eight steps, then read the left-central average. Greedy robust selection costs 31 units under the identical pool and error contract. The exact optimizer therefore reduces this heuristic cost by \(11/31\), approximately 35.5 percent. A fixed twenty-step full-heating protocol with the same sensor costs 44 units and is robustly feasible. The original corner sensor cannot identify all six hypotheses at any cost because of the reflected-fault obstruction. With zero noise, the cheapest exact panel costs 8 units. These comparisons separate information availability, uncertainty, and planning cost; none is a measured equipment performance result.

An independent shortest-path oracle recomputes pair coverage directly from the raw readings and error intervals. Its states are the subsets of separated candidate pairs. Taking experiment \(e\) adds its pair subset and its cost. Dijkstra's algorithm on this finite coverage graph gives the same optimum as the production branch-and-bound solver, without reusing its dominance pruning, coverage function, lower bound, or branching rule. Repeating an experiment never enlarges its covered-pair set, so a minimum path corresponds to an ordinary set of experiments. Both exact and robust optima are checked this way on the full 112-member pool.

The result is a finite-pool optimum, not an optimum over all possible thermal interventions. A richer pool could contain a cheaper observation. Furthermore, purchasing a panel with independent resets differs from planning one adaptive trajectory with shared setup. The present additive cost and independently reset measurements are deliberate, explicit semantics. A future adaptive policy or shared-setup planner needs a separate cost and uncertainty model.

For each reset radius the receipt also finds the exact common sensor-noise frontier. If \(b_e\) is the reset contribution before sensor noise, define

\[
\nu_*=\min_{c<d}\max_e\left(\frac{|r_e(c)-r_e(d)|}{2}-b_e\right).
\]

There exists a robust identifying panel from the entire pool precisely when \(\nu<\nu_*\), provided the nonnegative-noise domain is respected. For every pair, at least one experiment must have positive separation slack; conversely taking the union of those experiments covers all pairs. Finiteness makes the inner maxima attained, and the strict separation inequality excludes equality at the frontier. This is a finite-pool arithmetic threshold, not a universal sensitivity limit of the plate. The receipt checks infeasibility at the exact rational boundary.

The receipt simulates every protocol again with a separately written neighbor-flux oracle that never reads the compiled sparse entries or uses the production prefix-state cache. It verifies all 672 candidate readings, checks actual interval-boundary noisy observations, and requires the consistency decoder to return the correct singleton. Every nominal adapter entry, heater coefficient, and original sensor coefficient is compared with the DynaComp fixture, which is also compared against an independent edge-by-edge construction. These checks target the adapter and its semantics, in addition to the existing panel solver's independent exhaustive tests.

## Relation to the existing DynaComp guarantees

DynaComp's original nine-state approximation guarantees a corner-mean error below 0.1 for twenty steps at nominal conductance, with independent initial excess temperatures in \([18,22]\) and inputs in \([0,2]\). Its separate seventeen-state exact family handles arbitrary time-varying spatially uniform conductance in \([1/16,1/8]\) under the original observation contract. Neither result certifies these local bond faults and new sensor rows without another acceptance calculation.

The reset box in this pilot is intentionally a different experimental domain. It is much narrower and is centered at zero. Such preparation would need to be justified operationally before deploying a real fault test. In return, the pilot avoids interpreting a coarse existing reduction envelope as sufficient to separate much smaller fault signatures. A later high-throughput implementation can compile candidate-specific or common exact observable quotients and prove the same selected readings. It must charge setup and amortization, and preserve original candidate identities.

The retained SLICOT heat sources were inspected as a possible external sequel. They are public engineering benchmark models, not measured fault trajectories. Their sampled sources and error domains differ from this exact plate, and their calibration and fault hypotheses would require separate contracts. No third-party MAT data is redistributed by this pilot.

## Reproduction

Run `python scripts/thermal_diagnostics.py --check` from the repository root. All retained arithmetic and the core simulator use the standard library. The complete selected words, sensor names, candidate readings, costs, uncertainty radii, original-language ambiguity, and independent-check count are in [`results/thermal_diagnostics.json`](../../results/thermal_diagnostics.json). The optional `--dynacomp-source PATH` additionally calls the hash-matched original generator in an existing checkout. Generating a replacement result without `--check` is an explicit maintenance action; the check command never silently replaces retained evidence.
