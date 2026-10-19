# 16. Costed interventions for thermal fault identification

## 16.1 From graph observation to a source-derived model

Chapter 15 separates three questions: whether a permitted experiment can distinguish two states, which distinguishing experiment is cheapest, and which finite panel remains informative under error. This chapter applies the last question to a discrete thermal model already used in DynaComp. The graph-height energy is not a heat equation. The connection is the common operator and observation contract, with different front-end semantics.

The nominal source is DynaComp commit `cd788c7ac695728e3f5b22056a0f99a2c1e1463c`, function `plate_model` in `src/dynacomp/thermal.py`. Its exact rational fixture, source excerpt and hashes are retained under `applications/thermal_diagnostics/`. The 12 by 12 plate has 144 states, conductance \(k=1/8\), loss \(\ell=1/100\), a heater distributed equally over the central four cells, and an original sensor averaging the four corners. States are excess temperatures in the source model's units; coefficients are per step. The model is a synthetic discrete benchmark, and the additional faults are constructed hypotheses. No measured fault population or continuum discretization-error bound is inferred.

For a cell \(i\) with adjacent cells \(N(i)\), the nominal equation is

\[
x_i(t+1)=(1-\ell)x_i(t)
 +k\sum_{j\in N(i)}(x_j(t)-x_i(t))+B_i u_t,
\qquad B_i=\tfrac14\mathbf1_{i\text{ central}}.
\]

Equivalently, \(x^+=Ax+Bu\), with \(A_{ij}=k\) on adjacent distinct cells and \(A_{ii}=1-\ell-k|N(i)|\). All entries are nonnegative and every row sums to \(1-\ell\). The reference fixture is compared entry by entry with an independent undirected-edge construction. An optional source check also imports the pinned DynaComp function and compares its generated model exactly. Ordinary replay is offline and uses only the Python standard library.

Six candidate identities are preserved: nominal; conductance halved; heater gain halved; loss doubled; one blocked bond immediately to the left of the central heater; and its reflected right-hand bond. A blocked bond removes the two off-diagonal conductances and adds each removed conductance to the corresponding diagonal. This preserves the loss rate and changes transport rather than inventing a new sink. The finite population contains these six single-fault hypotheses, not arbitrary combinations of faults.

The sensors are the corner mean, central-four mean, and means of the left and right pairs of central cells. Every reading is an exact rational linear functional. A separate experiment starts from the zero excess-temperature center \(\mathbf0\), with a declared componentwise reset uncertainty. The source's earlier nine-state approximation and its error certificate are not reused for changed faults or changed sensors. This pilot simulates every candidate's full 144-state model exactly, so its model-reduction error is zero.

## 16.2 A common affine experiment contract

**Proposition SNG-T01 (candidate-preserving affine lift).** Let finitely many candidates \(c\) have rational dynamics \(x^+=A_cx+B_cu\), and expose the same sensor labels \(y_j=C_{c,j}x\). For a finite allowed input alphabet, define

\[
H_{c,a}=\begin{pmatrix}A_c&B_cu_a\\0&1\end{pmatrix},
\qquad M_a=\operatorname{diag}_c H_{c,a},
\qquad L_j=\bigl([C_{c,j},0]\bigr)_c.
\]

Put the augmented initial state \((x_{0,c},1)\) in candidate block \(c\), and zero in every other block. For every chronological action word, the operator-system reading equals that candidate's original thermal reading. Distinct original identifiers remain distinct even when all available readings agree.

*Proof.* Each homogeneous block sends \((x,1)\) to \((A_cx+B_cu_a,1)\), while a zero block stays zero. Induction on word length leaves exactly the selected block active and gives its original state evolution there. The output concatenation selects the desired sensor reading from that block. No assumption about commuting matrices is used. In particular, heater commands can be order-sensitive. \(\square\)

This gives a mathematically closed bridge to the generic experiment engine. The large pilot computes its declared finite pool by sparse evolution rather than materializing a large dense block matrix. Tiny cases compare the lift, direct model evolution, noncommuting words and original candidate identities. The pilot does not claim an all-future closure calculation for every possible thermal protocol.

## 16.3 Propagating the uncertainty actually declared

**Proposition SNG-T02 (box propagation and safe panel radii).** Suppose the nominal candidate state follows \(\bar x_{t+1}=A_c\bar x_t+B_cu_t\), while the actual state has initial deviation bounded by \(b_{0,c}\ge0\) and additive per-step disturbance bounded by \(d_{t,c}\ge0\). Define componentwise

\[
b_{t+1,c}=|A_c|b_{t,c}+d_{t,c}.
\]

For experiment \(e=(w,j)\) with length \(T\), a safe total output-error radius is

\[
\rho_{e,c}=|C_{c,j}|b_{T,c}
 +\varepsilon_{e,\mathrm{sensor}}
 +\varepsilon_{e,c,\mathrm{reduction}}.
\]

Consequently \(\varepsilon_e=\max_c\rho_{e,c}\) is a common envelope for the existing box-noise panel theorem. If the chosen panel separates every pair by some coordinate satisfying \(|r_e(a)-r_e(b)|>2\varepsilon_e\), its consistency decoder identifies the true member of the declared candidate family.

*Proof.* The state error obeys \(e_{t+1}=A_ce_t+d_t\). The componentwise triangle inequality gives \(|e_{t+1}|\le|A_c|b_{t,c}+d_{t,c}\). Induction gives the state bound; another triangle inequality after observation and addition of the separately justified sensor and reduction errors gives \(\rho_{e,c}\). Replacing it by its maximum is safe for every candidate. The strict separation and decoder implication are SNG-O16. \(\square\)

An actuator-command error can be included as a justified additional disturbance bound \(|B_c|r_{u,t}\). The retained experiment sets process disturbance and reduction error to zero; these are stated assumptions of the discrete model, not calibrated physical measurements. The API allows nonzero bounds without silently deriving them from a nominal run.

For the plate candidates, \(A_c\ge0\), \(A_c\mathbf1=(1-\ell_c)\mathbf1\), and every sensor has nonnegative weights summing to one. Thus a uniform reset box of radius \(r_0\), with no process disturbance, has exactly attained output radius \(r_0(1-\ell_c)^T\). The two constant initial corners attain the endpoints. This gives both a transparent sensitivity formula and an independent check of the general bound.

The common envelope can exceed a particular candidate's radius. The optimizer is exact for the declared common-box uncertainty model; a smaller panel might suffice under sharper candidate-dependent correlated uncertainty. Panels here consist of separately reset experiments, so no unmodeled shared initial-state history is discarded. Irreversible protocols require the history-aware semantics appropriate to that different problem.

## 16.4 A permanent blindness and its remedy

**Proposition SNG-T03 (reflection blindness).** Let \(P\) reflect the plate left to right. For the two blocked-bond candidates,

\[
A_{\mathrm{right}}=PA_{\mathrm{left}}P^{-1},\qquad
PB=B,\qquad Px_0=x_0.
\]

The corner-mean and center-mean sensors satisfy \(CP=C\). Therefore these two fault identities have identical readings under every finite scalar heater word and every observation horizon using those symmetric sensors.

*Proof.* Reflection maps the left removed edge to the right removed edge and preserves the grid, loss and heater. The initial center is uniform. Inductively \(x_{\mathrm{right}}(t)=Px_{\mathrm{left}}(t)\) under the same input word. Applying an invariant sensor proves equal outputs. The uniform reset box is also preserved by reflection, so the possible-output sets coincide as well. \(\square\)

This is an all-word obstruction, rather than a finite search that happened not to find a witness. A left-center sensor is not invariant under reflection; its reflected version is the right-center sensor. Adding the spatially resolved channel changes the experiment language and removes this particular obstruction. The example is the thermal counterpart of the terminal-move result in Chapter 15: repeated use of an invariant sensor cannot recover the orientation that sensor discards.

## 16.5 Retained finite-pool optimum and baselines

The declared pool contains 112 experiments. Heater amplitudes are zero or two; horizons are 1, 2, 3, 4, 6, 8, 12 and 20 steps. Step, first-pulse, last-pulse and alternating protocols are included, with duplicate words removed and all four sensor channels retained. Original candidate identities are never deduplicated. The exact reading table therefore has 672 entries. Its scope is the explicit pool, rather than every conceivable input signal or sensor placement.

Costs are normalized laboratory accounting units:

\[
c(w,j)=2+|w|+\tfrac12\sum_tu_t+s_j,
\qquad(s_0,s_1,s_2,s_3)=(1,1,2,2).
\]

The terms account for reset, elapsed steps, commanded heating and sensor access. These are declared costs, not measured money, energy tariffs or procurement quotations. Every member of a multi-experiment panel pays its own reset cost.

With reset radius \(r_0=1/100\) and sensor error \(1/100\), the exact minimum robust panel costs 20. It heats at amplitude two for eight steps, then reads the left-center mean: \(2+8+8+2=20\). The greedy panel costs 31 on the same pool and uncertainty envelope. The saving is exactly \(11/31\), approximately 35.48 percent. A fixed twenty-step full-heating local-sensor experiment costs 44 and also meets the declared robustness test. With the same reset uncertainty and sensor error \(1/1000\), the optimum costs 16 versus greedy's 20. These are exact finite-model optimization results and do not measure field performance.

The branch-and-bound result is checked independently by a shortest-path calculation on pair-coverage masks derived directly from the reading and error tables. Tiny pools are additionally compared with exhaustive subset enumeration. Sensitivity records vary reset uncertainty and sensor error, and retain the finite-pool sensor-error frontier for several reset radii. A frontier calculated using the common envelope characterizes that declared envelope, not every sharper physical uncertainty description.

## 16.6 Reproduction, integration and open questions

Run `PYTHONPATH=src python scripts/thermal_diagnostics.py --check`. Optional comparison with the separately cloned pinned source uses `--dynacomp-root PATH`. The retained receipt is `results/thermal_diagnostics.json`; the source record and a plain-language account are under `applications/thermal_diagnostics/`, with the expanded derivation in `docs/research/THERMAL_DIAGNOSTICS.md`. The core requires no DynaComp installation. The independent edge-flux oracle constructs evolution from neighboring heat exchanges, rather than calling the sparse matrix simulator it checks.

This pilot is a concrete interface between existing programs: a DynaComp source model, Singularity's costed panel engine, and stable original candidate identities ready for a higher-level decision interface. It does not automatically modify PerfectJet or PerfectPower. Further work can add constrained combinations of faults, calibrated process uncertainty, continuous-time sampling bounds and adaptive policies with shared histories. Their domains must be stated before reusing any guarantee here. SNG-T01 to SNG-T03 have manuscript proofs and exact computational evidence; no Lean formalization of these thermal statements is claimed.
