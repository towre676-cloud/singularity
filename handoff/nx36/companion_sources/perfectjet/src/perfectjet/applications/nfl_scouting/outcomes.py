"""Context-adjusted NFL targets built without contaminating validation.

For an eligible play p, r_i = (1/n_i) sum_p [y_ip - m(x_ip)], where m is a context
model. Training athletes receive cross-fitted residuals: m is fitted on the other
player folds. Validation athletes receive residuals from an m fitted on training
athletes only. Shrinkage toward zero uses n_i/(n_i+k) with k = sigma_play^2/tau^2
estimated on training athletes only; the rule is fixed before features are compared.

This target describes observed NFL participants. A player without eligible plays
has no target; that is missing information, not zero ability.
"""
from .linalg import ridge, dot, mean, var


def context_vector(play, levels):
    v = [1.0]
    for name, values in levels.items():
        val = play.context.get(name)
        if values is None:
            v.append(float(val) if isinstance(val, (int, float)) else 0.0)
        else:
            v.extend(1.0 if val == lv else 0.0 for lv in values[1:])
    return v


def context_levels(plays):
    levels = {}
    for p in plays:
        for k, val in p.context.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                levels.setdefault(k, None)
            else:
                cur = levels.setdefault(k, [])
                if cur is not None and val not in cur:
                    cur.append(val)
    return {k: (sorted(v, key=str) if v is not None else None) for k, v in sorted(levels.items())}


def fit_context(plays, levels, lam=1.0):
    return ridge([context_vector(p, levels) for p in plays], [p.outcome for p in plays], lam)


def _residual_means(plays, coef, levels):
    out = {}
    for p in plays:
        out.setdefault(p.athlete_id, []).append(p.outcome-dot(context_vector(p, levels), coef))
    return out


def player_folds(ids, k, groups=None):
    groups = groups or {}
    original = sorted({groups.get(a, a) for a in ids})
    fold = {a: i % k for i, a in enumerate(original)}
    return {a: fold[groups.get(a, a)] for a in ids}


def build_targets(plays, train_ids, test_ids, folds=5, minimum_plays=1, groups=None,
                  train_season_before=None, test_season=None):
    """Cross-fitted training targets and training-only validation targets, with shrinkage."""
    train_ids, test_ids = set(train_ids), set(test_ids)
    train_plays = [p for p in plays if p.athlete_id in train_ids
                   and (train_season_before is None or p.season < train_season_before)]
    levels = context_levels(train_plays)
    fold_of = player_folds(train_ids, folds, groups)
    resid = {}
    for f in range(folds):
        fit_on = [p for p in train_plays if fold_of[p.athlete_id] != f]
        if not fit_on:
            continue
        inner_levels = context_levels(fit_on)
        coef = fit_context(fit_on, inner_levels)
        held = [p for p in train_plays if fold_of[p.athlete_id] == f]
        resid.update(_residual_means(held, coef, inner_levels))
    coef_all = fit_context(train_plays, levels) if train_plays else None
    test_resid = _residual_means([p for p in plays if p.athlete_id in test_ids
                                and (test_season is None or p.season == test_season)],
                               coef_all, levels) if coef_all else {}
    # Shrinkage constant from training athletes only.
    within = [var(v) for v in resid.values() if len(v) > 1]
    sigma2 = mean(within) if within else 0.0
    means = [mean(v) for v in resid.values() if len(v) >= minimum_plays]
    n_bar = mean([len(v) for v in resid.values()]) if resid else 1.0
    tau2 = max(1e-12, (var(means) if len(means) > 1 else 0.0)-sigma2/max(n_bar, 1.0))
    k = sigma2/tau2 if tau2 > 0 else 0.0

    def summarize(d):
        return {a: {"raw": mean(v), "n": len(v), "shrunk": mean(v)*len(v)/(len(v)+k)}
                for a, v in d.items() if len(v) >= minimum_plays}
    return {"train": summarize(resid), "test": summarize(test_resid), "shrinkage_k": k,
            "context_coefficients": coef_all, "levels": levels}


def leakage_check(plays, train_ids, test_ids, perturb=10.0):
    """Perturbing held-out outcomes must leave every training target and the context model unchanged."""
    from dataclasses import replace
    a = build_targets(plays, train_ids, test_ids)
    moved = [replace(p, outcome=p.outcome+perturb) if p.athlete_id in set(test_ids) else p for p in plays]
    b = build_targets(moved, train_ids, test_ids)
    same_train = all(abs(a["train"][k]["shrunk"]-b["train"][k]["shrunk"]) < 1e-12 for k in a["train"])
    same_model = a["context_coefficients"] == b["context_coefficients"] and a["shrinkage_k"] == b["shrinkage_k"]
    return {"training_targets_unchanged": same_train, "context_model_unchanged": same_model}
