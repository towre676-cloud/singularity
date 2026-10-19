"""Executable analytic receipts for the mathematics joining the scouting bridge.

Run ``python -m perfectjet.applications.nfl_scouting.bridge_receipt`` to emit
JSON.  All sequences and measurement costs are synthetic.  Exact identities
concern the explicitly declared algebraic models, not athlete physiology.  The
numerical continuation results verify implementation behavior and establish no
NFL scouting improvement.  No competition inputs or outcome labels are used.
"""

import json
from fractions import Fraction as Q

import numpy as np

from ...engine import adaptive_closure, readout_problem, report, sensing
from ...exact import matmul
from ...polynomial import Poly
from ...readout import dot, identify, repair
from ...realization import coarsest_lumping
from .allocation import allocation_receipt
from .predictive_state import MovementSequence, continuation_diagnostics, discover_predictive_state


BRIDGE_RECEIPT_VERSION = "nfl-math-bridge-receipt/1"


def _json_value(value):
    """Serialize exact fractions losslessly; keep numerical results numeric."""
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, np.ndarray):
        return _json_value(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _ar2_sequences(players, frames=45, noise=0.0, seed=441):
    rng = np.random.default_rng(seed)
    sequences = []
    for i in range(players):
        signal = np.zeros(frames)
        signal[:2] = rng.normal(size=2)
        for t in range(2, frames):
            signal[t] = 1.5 * signal[t - 1] - 0.75 * signal[t - 2]
        observed = (signal + rng.normal(scale=noise, size=frames))[:, None]
        sequences.append(MovementSequence(f"analytic-player-{i:02d}", f"analytic-attempt-{i}",
                                          np.arange(frames) * 0.1, observed))
    return sequences


def _exact_dynamics():
    previous, current = Poly.variable(0), Poly.variable(1)
    # This known synthetic recurrence closes after adding precisely the missing
    # previous-value feature.  No generic finite closure claim is made.
    closure = adaptive_closure([current, Q(3, 2) * current - Q(3, 4) * previous], [current])
    next_readout = (Q(-3, 4), Q(3, 2))
    memory = sensing([[0, 1]], [next_readout], candidates=[[1, 0]])
    a, b = (Q(0), Q(1)), (Q(2), Q(1))
    return {
        "equations": ["y[t+1] = (3/2)y[t] - (3/4)y[t-1]",
                      "x[t] = (y[t-1], y[t])",
                      "F(x) = (x2, (3/2)x2 - (3/4)x1)",
                      "psi(F(x)) = K psi(x), psi=(x1,x2)",
                      "H=(0,1), G=(-3/4,3/2): ker(H) is not contained in ker(G)"],
        "assumptions": ["Declared noiseless rational linear recurrence",
                        "Current observation contains y[t] only; the prior value is initially hidden"],
        "closure_report": closure,
        "instantaneous_observation_report": memory,
        "same_current_different_future": {"state_a": a, "state_b": b,
                                          "current_a": a[1], "current_b": b[1],
                                          "next_a": dot(next_readout, a),
                                          "next_b": dot(next_readout, b)},
        "scope": "Exact synthetic dynamics, not a physiological model",
    }


def _numerical_continuations():
    sequences = _ar2_sequences(18)
    fit = discover_predictive_state(
        sequences[:12], history_steps=(1, 2, 3), ranks=(1, 2, 3), horizon_steps=3,
        ridge_penalties=(0.0,), inner_folds=3, forecast_tolerance=1e-7,
        channel_names=("synthetic_forward_velocity",), output_names=("synthetic_forward_velocity",),
    )
    held = continuation_diagnostics(fit.model, sequences[12:])
    instantaneous = continuation_diagnostics(fit.instantaneous_model, sequences[12:])
    witness_a, witness_b = [[0.0], [1.0]], [[2.0], [1.0]]
    numerical = report(
        "Predict a three-step movement continuation using an instantaneous value or a delay state",
        {"kind": "Numerical target-directed delay-block model", "state_count": fit.model.state_count,
         "history_steps": fit.model.history_steps, "horizon_steps": fit.model.horizon_steps},
        ["Direct physical-coordinate forecast over the fitted three-step horizon"],
        [{"equation": "s = ((history-mu)/scale - past_center) B V_r", "replayed": True},
         {"equation": "forecast = unscale(s V_r^T + future_center)", "replayed": True}],
        answer={"heldout_delay_mse": held["standardized_mse"],
                "heldout_instantaneous_mse": instantaneous["standardized_mse"],
                "heldout_delay_rmse": held["standardized_rmse"],
                "training_athletes": len(fit.training_athlete_ids),
                "heldout_athletes": held["independent_athletes"],
                "inner_continuation_gain": fit.continuation_gain,
                "forecast_a": fit.model.forecast(witness_a),
                "forecast_b": fit.model.forecast(witness_b)},
        obligations=["Numerical rank is selected empirically within training-player folds",
                     "This result is on synthetic recurrence data, not NFL observations",
                     "Finite-horizon success does not establish all-future dynamical realization"],
        next_step="Evaluate the frozen representation on untouched movement and final football outcomes",
    )
    noisy_sequences = _ar2_sequences(24, frames=50, noise=0.015, seed=982)
    noisy = discover_predictive_state(
        noisy_sequences[:18], history_steps=(1, 3, 5), ranks=(1, 2), horizon_steps=3,
        ridge_penalties=(1e-6, 0.01), forecast_tolerance=0.1,
    )
    noisy_held = continuation_diagnostics(noisy.model, noisy_sequences[18:])
    return {
        "equations": ["P[t] = vec(y[t-L+1], ..., y[t])",
                      "F[t] = vec(y[t+1], ..., y[t+H])",
                      "B_lambda = argmin_B sum_i w_i ||P_i B - F_i||^2 + lambda ||B||_F^2",
                      "Weighted fitted continuations = U Sigma V^T; B_r = B_lambda V_r V_r^T"],
        "assumptions": ["Uniform sampling at 0.1 seconds, independent synthetic player initial states",
                        "Scalers, ridge fits and rank selection use training players only",
                        "Every history candidate is scored at identical forecast origins",
                        "Equal total sampled-athlete weights; bootstrap originals share folds",
                        "SVD coordinates may rotate across fits; output features remain in physical coordinates"],
        "noiseless_report": numerical,
        "noiseless_selection_scores": fit.selection_scores,
        "noisy_fixture": {"seed": 982, "observation_noise_sd": 0.015,
                          "training_players": 18, "heldout_players": 6,
                          "history_steps": noisy.model.history_steps,
                          "state_count": noisy.model.state_count,
                          "inner_rmse": noisy.selected_cv_mse ** 0.5,
                          "instantaneous_inner_rmse": noisy.instantaneous_cv_mse ** 0.5,
                          "unseen_player_rmse": noisy_held["standardized_rmse"],
                          "declared_standardized_rmse_tolerance": noisy.forecast_tolerance,
                          "inner_meets_declared_tolerance": noisy.meets_declared_tolerance,
                          "defect_candidates": noisy_held["defect_candidates"]},
        "scope": "Synthetic finite-horizon continuation fixtures; zero NFL performance evidence",
    }


def _readout_counterexample():
    design, target = [[1, 1]], [1, 0]
    identification = identify(design, target)
    witness = identification["witness"]
    base = (Q(1, 5), Q(4, 5))
    alternate = tuple(value + Q(1, 10) * delta for value, delta in zip(base, witness))
    report_value = readout_problem(design, target, candidates=[[1, 1], [0, 1]])
    return {
        "equations": ["t_cross = tau_onset + u_travel", "X=(1,1), h=(1,0)",
                      "X n = 0 but h^T n != 0", "beta' = beta + (1/10)n"],
        "assumptions": ["Declared additive onset/travel duration model",
                        "Only crossing duration is observed; both example component durations are positive",
                        "The additional travel observation is a mathematical candidate, not a verified drill"],
        "engine_report": report_value,
        "exact_witness": witness,
        "two_positive_duration_fits": {
            "components_a": base, "components_b": alternate,
            "crossing_a": dot(design[0], base), "crossing_b": dot(design[0], alternate),
            "onset_a": dot(target, base), "onset_b": dot(target, alternate),
        },
        "repair": repair(design, target, [[1, 1], [0, 1]]),
        "scope": "Exact ambiguity of a declared readout; not a measured reaction-time decomposition",
    }


def _quotient_receipt():
    # Column-state convention: states 0/1 advance to 2/3, then remain there.
    advance = [[0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1]]
    idle = [[int(i == j) for j in range(4)] for i in range(4)]
    output = [[0, 0, 1, 1]]
    quotient = coarsest_lumping([idle, advance], output)
    r, reduced = quotient["aggregation"], quotient["reduced"]
    identity_replays = [matmul(r, action) == matmul(small, r)
                        for action, small in zip((idle, advance), reduced)]
    output_replay = matmul(quotient["output"], r) == [[Q(v) for v in row] for row in output]
    # A different declared machine has two equally observed states whose next
    # observations differ.  Matching a current readout cannot justify merging.
    separating = [[0, 0, 0], [0, 1, 0], [1, 0, 1]]
    separating_output = [[0, 0, 1]]
    separate_quotient = coarsest_lumping([separating], separating_output)
    first, second = [1, 0, 0], [0, 1, 0]
    first_next = [dot(row, first) for row in separating]
    second_next = [dot(row, second) for row in separating]
    return {
        "equations": ["R A_c = Abar_c R for every declared action c", "H = Hbar R",
                      "H A_word x = Hbar Abar_word R x for every finite action word"],
        "assumptions": ["Exact rational finite transition matrices and declared output map",
                        "Conclusions concern these supplied machines, not observational equivalence of athletes"],
        "engine_report": report(
            "Compress the declared finite machine while preserving its future output behavior",
            {"kind": "Exact weighted quotient", "original_states": 4, "quotient_states": len(quotient["blocks"])},
            ["Declared output under every finite action sequence"],
            [{"equation": "R A_c = Abar_c R", "replayed": all(identity_replays)},
             {"equation": "H = Hbar R", "replayed": output_replay}],
            answer=quotient,
        ),
        "same_initial_different_future": {
            "initial_output_a": dot(separating_output[0], first),
            "initial_output_b": dot(separating_output[0], second),
            "next_output_a": dot(separating_output[0], first_next),
            "next_output_b": dot(separating_output[0], second_next),
            "quotient_blocks": separate_quotient["blocks"],
        },
        "scope": "Exact finite-machine bridge; no physiological or scouting equivalence claim",
    }


def build_bridge_receipt():
    """Execute the cross-core analytic/numerical bridge and return plain JSON."""
    allocation = allocation_receipt()
    allocation_report = {
        "equations": ["Sigma' = Sigma - Sigma E^T (R + E Sigma E^T)^(-1) E Sigma",
                      "Target value = h^T(Sigma - Sigma')h",
                      "max_{S: sum(cost)<=2} target_value(S)",
                      "110/131 > 21/32; isolated measurement values are not additive"],
        "assumptions": ["Two independent unit-variance Gaussian source coordinates; target is coordinate one",
                        "Direct observation (1,0) has noise variance 1",
                        "Mixed (1,1) and nuisance (0,1) observations each have noise variance 1/10",
                        "Every candidate has synthetic unit cost; budget is two; observation errors are independent",
                        "Frozen target loading is supplied, not learned from NFL outcomes"],
        "result": allocation,
        "exact_gain_over_isolated_greedy": allocation["optimal_joint_reduction"] - allocation["greedy_joint_reduction"],
        "scope": "Exact declared Gaussian package example; not an empirical scouting gain",
    }
    value = {
        "version": BRIDGE_RECEIPT_VERSION,
        "evidence_scope": "Analytic and synthetic mathematics only; no NFL prediction improvement is established",
        "real_nfl_experiment_executed": False,
        "raw_competition_data_required": False,
        "exact_history_bridge": _exact_dynamics(),
        "numerical_predictive_state_bridge": _numerical_continuations(),
        "readout_identifiability_bridge": _readout_counterexample(),
        "finite_quotient_bridge": _quotient_receipt(),
        "joint_measurement_allocation_bridge": allocation_report,
        "cross_core_links": {
            "engine": "adaptive_closure, sensing, readout_problem and report",
            "readout": "identify and repair return exact ambiguity/repair witnesses",
            "realization": "coarsest_lumping replays transition and output aggregation identities",
            "populations": "allocation_receipt executes SelectionPopulation package enumeration through TargetInformationModel",
            "numerical": "predictive_state uses player-held delay blocks and physical-coordinate forecasts",
        },
    }
    serializable = _json_value(value)
    # Fail locally rather than emitting NaN/Infinity or silently lossy fractions.
    json.dumps(serializable, allow_nan=False)
    return serializable


if __name__ == "__main__":
    print(json.dumps(build_bridge_receipt(), indent=2, sort_keys=True, allow_nan=False))
