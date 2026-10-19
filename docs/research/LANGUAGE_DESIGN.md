# Capability purchase and the intervention language (NX07)

The accepted decision problem is finite. A capability is an explicitly priced sensor or actuator, an experiment has an immutable set of requirements, and each original candidate retains its identifier. Installation cost is paid once. Runtime cost is paid for each independently reset diagnosis. All costs below are exact accounting units. They are not measurements of hardware price, elapsed seconds, energy, or deployment demand.

For candidate indices \(i,j\), let \(T_i\) be the requested target label and let an experiment return closed intervals \(I_{ei}=[r_{ei}-\rho_{ei},r_{ei}+\rho_{ei}]\). Its pair mask contains \((i,j)\) exactly when

\[
T_i\ne T_j,\qquad |r_{ei}-r_{ej}|>\rho_{ei}+\rho_{ej}.
\]

Equality is insufficient: closed intervals touching at an endpoint admit a common observation. Models with the same target need not be distinguished. This coarsening never removes their original labels from the source population.

## Activation theorem and exact optimizer

For capabilities \(K\), experiment requirements \(R_e\), one-time prices \(a_k\), runtime prices \(c_e\), and positive integer deployment horizon \(N\), the objective is

\[
\min_{z,x}\left[\sum_k a_kz_k+N\sum_ec_ex_e\right],\qquad
x_e\le z_k\quad(k\in R_e),\qquad
\sum_{e:(i,j)\in S_e}x_e\ge1\quad(T_i\ne T_j).
\]

Enumerate every installed subset \(J\subseteq K\). Experiments with requirements outside \(J\) are unavailable. On the remaining experiments, the dynamic program maintains the least runtime cost for each covered-pair mask. Processing an experiment has two branches: skip it or include its mask and add its runtime cost. Induction on the processed experiment prefix proves that each state contains precisely the minimum cost of every panel producing that mask. The full mask therefore gives the minimum runtime cost under that installation. Taking the minimum of installation plus \(N\) times runtime over all \(J\) proves global optimality **within this finite catalogue**.

Empty masks can be omitted because their nonnegative costs cannot improve coverage or objective. The solver retains tied panels up to its explicit tie-reporting limit; `ties_truncated` reports any loss of tie enumeration without changing the proved optimal value. A node budget that interrupts installation or mask enumeration returns `optimality_unresolved` or `resource_limit`, never `optimal`.

A panel is a set of separate reset experiments. Combining simultaneous sensor outputs into one shared physical run requires a different joint-noise and cost contract. No such saving is inferred here.

## Tiny independent acceptance oracle

Three candidates have states \((0,0),(1,0),(0,1)\). Sensors \(s_1,s_2\) cost two to install and one to read; they measure individual coordinates. Sensor \(s_3\) costs five to install and one to read and measures \(x_1+2x_2\). Every reading has radius \(1/10\). At \(N=1\), installing \(s_1,s_2\) and installing \(s_3\) both cost six and both are retained. At \(N=2\), their costs are eight and seven. Tests independently enumerate every installation bit vector and every experiment bit vector; that oracle does not call the dynamic program.

## Synthetic thermal catalogue and all-word blindness

The 4-by-4 source-derived plate exposes four sensor purchases and one optional asymmetric heater. Every experiment uses one selected heater with a scalar amplitude word. The adapter does not overload scalar amplitudes as heater identifiers, and it does not simulate two simultaneous independently addressed heater channels. New heater and sensor installations are synthetic assumptions. The original six-candidate fixture is left intact.

For reflected blocked-bond candidates, the retained permutation \(P\) satisfies

\[
A_b=PA_aP^{-1},\qquad B_b=PB_a,\qquad x_{0,b}=Px_{0,a},\qquad C_bP=C_a
\]

under the original symmetric heater and symmetric corner/center sensors. If \(x_b(t)=Px_a(t)\), then the chronological update gives

\[
x_b(t+1)=PA_ax_a(t)+PB_au_t=P x_a(t+1).
\]

Induction proves equality for every finite amplitude word, not merely the stored horizons. The receipt checks the exact permutation identities. It separately retains an actual local-sensor protocol that distinguishes the reflected candidates and recomputes its outputs by neighbour-flux stepping. Violation of sensor invariance alone is not used as a reachability proof.

## Expanded fault population: a useful null result

The NX03 adapter supplies exactly 79 original configurations, including nominal, single removed bonds and two removed bonds among twelve declared bonds. At the declared horizon-six catalogue, four configurations are merged into the same response classes as others: there are **75 observable classes**. The exact identity-target optimizer therefore reports `unseparable`; the receipt lists the original indistinguishable pairs.

A second, explicitly labelled target is the maximal distinction this finite catalogue can express: each configuration is labelled by its complete catalogue response vector. Its Pareto frontier compares installation cost and per-diagnosis cost at \(N\in\{1,2,10,100\}\). Every original fault ID and mask remains reconstructable in the receipt. This quotient frontier is not sold as original-fault identification or an all-word impossibility theorem. Longer horizons, additional sensors and different permitted protocols may split these classes.

The replay script is `python scripts/nx_decision_recovery.py --track NX07 --check`. Its retained file includes the complete source catalogue, target semantics, exact prices, all reported optima, finite null witnesses and original-mask reconstruction. Integrity hashes bind source bytes; independent enumeration and exact replay establish the finite optimization claim.

The optional asymmetric heater is a substitute installed actuator. In this synthetic catalogue its injection vector replaces the original heater vector, so it bypasses the original `heater_half` source fault instead of assuming that fault also halves newly installed hardware. Experiments on the original heater retain the original gain fault. This is an explicit hardware assumption of this finite demonstration.
