"""Optional AdamW construction and a mutation-free, one-step meta proposal.

PyTorch is imported only by the public functions.  Importing Singularity's exact
arithmetic package therefore does not require the optional training dependency.

``meta_proposal`` asks a deliberately local question: would changing the next
AdamW step's learning rate and weight decay improve loss on a separate TUNE
batch?  It differentiates that virtual update, then accepts a bounded proposal
only after backtracking on that same TUNE batch.  This is neither a multi-step
hypergradient nor a claim about performance on a held-out validation/test set.
The live parameters, gradients, Adam state, buffers, training mode and CPU/CUDA
random-number states are not changed by the proposal.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
import math
import re
from typing import Any, Callable


def _torch():
    try:
        import torch
    except ImportError as exc:
        raise ImportError(
            "The optional training utilities require PyTorch; install the "
            "project's training extras before running an experiment."
        ) from exc
    return torch


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    raise TypeError("configuration must be a mapping or an attribute object")


def _optimizer_config(cfg: Any) -> dict[str, Any]:
    out = _as_dict(cfg)
    nested = out.get("optimizer")
    if isinstance(nested, Mapping) or hasattr(nested, "__dict__"):
        out.update(_as_dict(nested))
    elif nested is not None and str(nested).lower() != "adamw":
        raise ValueError("the training harness supports the AdamW optimizer")
    return out


def _finite_float(value: Any, name: str, *, positive: bool = False) -> float:
    answer = float(value)
    if not math.isfinite(answer) or (positive and answer <= 0):
        qualifier = "finite and positive" if positive else "finite"
        raise ValueError(f"{name} must be {qualifier}")
    return answer


def build_optimizer(model: Any, cfg: Any):
    """Build AdamW with explicit no-decay masks and optional layer LR decay.

    ``cfg`` may contain the optimizer fields directly or in an ``optimizer``
    mapping.  Supported fields are ``lr``/``learning_rate``, ``weight_decay``/
    ``wd``, ``betas`` (or ``beta1``/``beta2``), ``eps``, ``amsgrad`` and
    ``variant``.  ``baseline``, ``cosine`` and ``meta`` use the same optimizer;
    the runner owns scheduling.  ``layer_decay`` uses ``layer_decay`` (default
    0.8) between named blocks, with embeddings assigned the earliest depth.

    Biases and one-dimensional parameters are excluded from decay by default.
    Set ``exclude_bias_norm_decay=False`` to decay all trainable parameters.
    The saved ``lr_scale`` and ``weight_decay_scale`` fields let a caller apply
    global proposals without destroying either the layer ratios or this mask.
    """
    torch = _torch()
    options = _optimizer_config(cfg)
    lr = _finite_float(options.get("lr", options.get("learning_rate", 3e-4)), "lr", positive=True)
    wd = _finite_float(options.get("weight_decay", options.get("wd", 0.01)), "weight_decay")
    if wd < 0:
        raise ValueError("weight_decay must be nonnegative")
    betas = tuple(options.get("betas", (options.get("beta1", 0.9), options.get("beta2", 0.999))))
    if len(betas) != 2 or any(not 0 <= float(beta) < 1 for beta in betas):
        raise ValueError("betas must contain two values in [0, 1)")
    betas = tuple(float(beta) for beta in betas)
    eps = _finite_float(options.get("eps", 1e-8), "eps", positive=True)
    variant = str(options.get("variant", "baseline")).lower()
    if variant not in {"baseline", "cosine", "layer_decay", "meta"}:
        raise ValueError(f"unknown optimizer variant: {variant}")
    factor = _finite_float(options.get("layer_decay", 0.8), "layer_decay", positive=True)
    if factor > 1:
        raise ValueError("layer_decay must be at most one")
    named = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
    if not named:
        raise ValueError("model has no trainable parameters")

    def block_index(name: str) -> int | None:
        found = re.search(r"(?:^|\.)(?:layers|blocks|h|layer)\.(\d+)(?:\.|$)", name)
        if found is None:
            found = re.search(r"(?:^|\.)(\d+)(?:\.|$)", name)
        return int(found.group(1)) + 1 if found else None

    indices = sorted({index for name, _ in named if (index := block_index(name)) is not None})
    # Sequential activation modules leave holes (e.g. net.0, net.2); they do
    # not constitute additional trainable layers for LR-decay purposes.
    depth_by_index = {index: depth + 1 for depth, index in enumerate(indices)}
    explicit_head = any(re.search(r"(?:^|\.)(?:head|classifier|readout|lm_head)(?:\.|$)", name)
                        for name, _ in named)
    final_depth = max(len(indices) + int(explicit_head), 1)
    mask = bool(options.get("exclude_bias_norm_decay", True))
    grouped: dict[tuple[int, bool], dict[str, Any]] = {}
    for name, parameter in named:
        depth = block_index(name)
        if depth is not None:
            depth = depth_by_index[depth]
        if depth is None:
            # Recognise both transformer and small-model embedding conventions.
            embedding = any(part in name.lower() for part in ("embed", "wte", "wpe", "position", "token"))
            depth = 0 if embedding else final_depth
        if variant != "layer_decay":
            depth = final_depth
        no_decay = mask and (parameter.ndim < 2 or name.endswith(".bias"))
        key = (depth, no_decay)
        if key not in grouped:
            scale = factor ** (final_depth - depth) if variant == "layer_decay" else 1.0
            grouped[key] = {
                "params": [],
                "param_names": [],
                "lr": lr * scale,
                "initial_lr": lr * scale,
                "lr_scale": scale,
                "weight_decay": 0.0 if no_decay else wd,
                "weight_decay_scale": 0.0 if no_decay else 1.0,
            }
        grouped[key]["params"].append(parameter)
        grouped[key]["param_names"].append(name)
    return torch.optim.AdamW(
        list(grouped.values()), lr=lr, weight_decay=wd, betas=betas,
        eps=eps, amsgrad=bool(options.get("amsgrad", False)),
    )


def _batch_call(batch: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
    if isinstance(batch, Mapping):
        if "model_args" in batch or "model_kwargs" in batch:
            args = batch.get("model_args", ())
            if not isinstance(args, (tuple, list)):
                args = (args,)
            return tuple(args), dict(batch.get("model_kwargs", {}))
        for key in ("input_ids", "inputs", "x"):
            if key in batch:
                return (batch[key],), {}
        raise ValueError("batch needs input_ids, inputs, x, or explicit model_args/model_kwargs")
    if isinstance(batch, (tuple, list)):
        if not batch:
            raise ValueError("batch is empty")
        # Conventional (inputs, targets); targets remain available to loss_fn.
        return (batch[0],), {}
    return (batch,), {}


def meta_proposal(
    model: Any,
    opt: Any,
    train_batch: Any,
    tune_batch: Any,
    loss_fn: Callable[[Any, Any], Any],
    meta_cfg: Any = None,
) -> dict[str, Any]:
    """Return a backtracked LR/decay proposal without applying any update.

    ``loss_fn(logits, batch)`` must return a scalar differentiable loss.
    Models receive ``batch['input_ids']`` (or ``inputs``/``x``); explicit
    ``model_args``/``model_kwargs`` support other forward signatures.  Train
    and TUNE should be separate, preselected data.  No validation/test batch
    belongs in this interface.

    The virtual update uses the *actual* Adam first/second moments, each
    parameter's actual next step for bias correction, AMSGrad when enabled,
    each group's betas/epsilon, and the optimizer's decay mask.  Existing
    moments are detached and cloned.  A single detached train gradient is
    shared by the baseline and every candidate.  Hypergradients are exact for
    that one-step frozen-gradient computation, not for the past trajectory.

    Configuration: ``hyper_lr`` (0.1), ``max_backtracks`` (8),
    ``backtrack_factor`` (0.5), ``min_lr`` (1e-8), ``max_lr`` (1.0),
    ``min_weight_decay`` (0), ``max_weight_decay`` (1), ``wd_shift`` (1e-4),
    ``grad_clip`` (None), ``min_improvement`` (0), and
    ``normalize_hypergradient`` (True).  Normalization is a diagonal positive
    preconditioner, so the initial search direction remains a descent
    direction.  Log LR and shifted-log decay are graph-connected leaves;
    the latter has a nonzero derivative even when current decay is zero.

    On rejection, ``lr``/``weight_decay`` and their group lists are the current
    settings.  On acceptance, apply the returned group lists explicitly (or
    preserve their scales when applying the returned global settings).
    """
    torch = _torch()
    if not isinstance(opt, torch.optim.AdamW):
        raise TypeError("meta_proposal requires torch.optim.AdamW")
    cfg = _as_dict(meta_cfg)
    hyper_lr = _finite_float(cfg.get("hyper_lr", 0.1), "hyper_lr", positive=True)
    backtrack_factor = _finite_float(cfg.get("backtrack_factor", 0.5), "backtrack_factor", positive=True)
    if backtrack_factor >= 1:
        raise ValueError("backtrack_factor must be less than one")
    max_backtracks = int(cfg.get("max_backtracks", 8))
    if max_backtracks < 0:
        raise ValueError("max_backtracks must be nonnegative")
    min_lr = _finite_float(cfg.get("min_lr", 1e-8), "min_lr", positive=True)
    max_lr = _finite_float(cfg.get("max_lr", 1.0), "max_lr", positive=True)
    min_wd = _finite_float(cfg.get("min_weight_decay", 0.0), "min_weight_decay")
    max_wd = _finite_float(cfg.get("max_weight_decay", 1.0), "max_weight_decay")
    if min_lr > max_lr or min_wd < 0 or min_wd > max_wd:
        raise ValueError("invalid hyperparameter bounds")
    wd_shift = _finite_float(cfg.get("wd_shift", 1e-4), "wd_shift", positive=True)
    min_improvement = _finite_float(cfg.get("min_improvement", 0.0), "min_improvement")
    if min_improvement < 0:
        raise ValueError("min_improvement must be nonnegative")
    grad_clip = cfg.get("grad_clip")
    if grad_clip is not None:
        grad_clip = _finite_float(grad_clip, "grad_clip")
        if grad_clip < 0:
            raise ValueError("grad_clip must be nonnegative")
        grad_clip = grad_clip or None
    group_lrs = [float(group["lr"]) for group in opt.param_groups]
    group_wds = [float(group.get("weight_decay", 0.0)) for group in opt.param_groups]
    if not group_lrs or any(not math.isfinite(lr) or lr <= 0 for lr in group_lrs):
        raise ValueError("every AdamW group must have a finite positive learning rate")
    if any(not math.isfinite(wd) or wd < 0 for wd in group_wds):
        raise ValueError("every AdamW group must have finite nonnegative weight decay")
    base_lr = max(
        lr / float(group.get("lr_scale", 1.0))
        for lr, group in zip(group_lrs, opt.param_groups)
    )
    decay_scales = [float(group.get("weight_decay_scale", 1.0 if wd > 0 else 0.0))
                    for wd, group in zip(group_wds, opt.param_groups)]
    # All-zero unannotated AdamW groups still have a tunable decay coefficient.
    if not any(decay_scales) and not any("weight_decay_scale" in group for group in opt.param_groups):
        decay_scales = [1.0] * len(opt.param_groups)
    base_wd = max((wd / scale for wd, scale in zip(group_wds, decay_scales) if scale > 0), default=0.0)
    if not min_lr <= base_lr <= max_lr or not min_wd <= base_wd <= max_wd:
        raise ValueError("current global learning rate/weight decay lies outside meta bounds")
    result: dict[str, Any] = {
        "accepted": False, "lr": base_lr, "weight_decay": base_wd,
        "group_lrs": group_lrs, "group_weight_decays": group_wds,
        "baseline_tune_loss": None, "candidate_tune_loss": None,
        "train_loss": None, "hypergradients": None, "backtracks": 0,
        "attempts": 0, "reason": "not_evaluated",
        "hyperparameter_coordinates": "log_lr, log(weight_decay + wd_shift)",
        "wd_shift": wd_shift,
    }

    original = OrderedDict(model.named_parameters())
    if not original:
        raise ValueError("model has no parameters")
    if any(parameter.is_complex() for parameter in original.values()):
        raise ValueError("the functional AdamW proposal supports real parameters only")
    id_to_name = {id(parameter): name for name, parameter in original.items()}
    records: list[tuple[str, dict[str, Any], dict[str, Any], int]] = []
    seen: set[str] = set()
    for group_index, group in enumerate(opt.param_groups):
        for parameter in group["params"]:
            if id(parameter) not in id_to_name:
                raise ValueError("optimizer contains a parameter outside the supplied model")
            name = id_to_name[id(parameter)]
            if name in seen:
                raise ValueError("optimizer contains a parameter more than once")
            seen.add(name)
            # get(), rather than state[parameter], avoids creating empty state.
            state = opt.state.get(parameter, {})
            frozen = {key: value.detach().clone() if torch.is_tensor(value) else value
                      for key, value in state.items()}
            records.append((name, group, frozen, group_index))
    params = OrderedDict((name, parameter.detach().clone().requires_grad_(parameter.requires_grad))
                         for name, parameter in original.items())
    buffers = OrderedDict((name, buffer.detach().clone()) for name, buffer in model.named_buffers())
    active_names = [name for name in seen if params[name].requires_grad]
    # Keep gradient order reproducible across processes, independent of set order.
    active_names = [name for name in params if name in active_names]
    if not active_names:
        raise ValueError("optimizer has no trainable model parameters")
    device = params[active_names[0]].device
    cuda_devices = sorted({parameter.device.index for parameter in params.values()
                           if parameter.device.type == "cuda"})

    with torch.enable_grad(), torch.random.fork_rng(devices=cuda_devices, enabled=True):
        cpu_rng = torch.random.get_rng_state().clone()
        cuda_rng = {index: torch.cuda.get_rng_state(index).clone() for index in cuda_devices}

        def evaluate(current_params: Mapping[str, Any], batch: Any):
            # Every candidate sees the same randomness and pristine cloned buffers.
            torch.random.set_rng_state(cpu_rng)
            for index, rng in cuda_rng.items():
                torch.cuda.set_rng_state(rng, index)
            args, kwargs = _batch_call(batch)
            current_buffers = OrderedDict((name, value.clone()) for name, value in buffers.items())
            output = torch.func.functional_call(
                model, (current_params, current_buffers), args, kwargs,
                tie_weights=True, strict=True,
            )
            loss = loss_fn(output, batch)
            if not torch.is_tensor(loss) or loss.numel() != 1:
                raise ValueError("loss_fn must return a scalar tensor")
            return loss.reshape(())

        train_loss = evaluate(params, train_batch)
        train_value = float(train_loss.detach().cpu())
        if not math.isfinite(train_value):
            result["reason"] = "nonfinite_train_loss"
            return result
        result["train_loss"] = train_value
        gradients = torch.autograd.grad(
            train_loss, tuple(params[name] for name in active_names),
            allow_unused=True, create_graph=False,
        )
        grads = {name: gradient.detach() if gradient is not None else None
                 for name, gradient in zip(active_names, gradients)}
        if any(gradient is not None and gradient.is_sparse for gradient in grads.values()):
            raise ValueError("AdamW meta proposals do not support sparse gradients")
        if any(gradient is not None and not bool(torch.isfinite(gradient).all()) for gradient in grads.values()):
            result["reason"] = "nonfinite_train_gradient"
            return result
        if not any(gradient is not None for gradient in grads.values()):
            result["reason"] = "no_train_gradient"
            return result
        if grad_clip is not None:
            # A tensor-valued scale preserves the mathematical clipping map.
            norm_sq = sum((gradient.to(device=device, dtype=torch.float64).square().sum()
                           for gradient in grads.values() if gradient is not None))
            norm = torch.sqrt(norm_sq)
            scale = torch.clamp(grad_clip / (norm + 1e-6), max=1.0)
            grads = {name: gradient * scale.to(gradient.device, gradient.dtype) if gradient is not None else None
                     for name, gradient in grads.items()}
            result["train_gradient_norm"] = float(norm.detach().cpu())

        def virtual_update(lr: Any, wd: Any):
            updated = OrderedDict((name, value.detach()) for name, value in params.items())
            for name, group, state, group_index in records:
                gradient = grads.get(name)
                if gradient is None:
                    continue  # AdamW also skips decay for parameters with no gradient.
                parameter = params[name].detach()
                if bool(group.get("maximize", False)):
                    gradient = -gradient
                beta1, beta2 = group["betas"]
                old_m = state.get("exp_avg", torch.zeros_like(parameter))
                old_v = state.get("exp_avg_sq", torch.zeros_like(parameter))
                moment = beta1 * old_m + (1.0 - beta1) * gradient
                variance = beta2 * old_v + (1.0 - beta2) * gradient.square()
                old_step = state.get("step", 0)
                if torch.is_tensor(old_step):
                    old_step = old_step.detach().cpu().item()
                step = int(old_step) + 1
                if bool(group.get("amsgrad", False)):
                    variance = torch.maximum(state.get("max_exp_avg_sq", torch.zeros_like(parameter)), variance)
                corrected_m = moment / (1.0 - beta1 ** step)
                corrected_v = variance / (1.0 - beta2 ** step)
                effective_lr = lr * (group_lrs[group_index] / base_lr)
                # Offset from actual group decay preserves pre-existing masks and
                # arbitrary group settings at the baseline exactly.
                effective_wd = (group_wds[group_index] + decay_scales[group_index] * (wd - base_wd)).clamp_min(0.0)
                effective_lr = effective_lr.to(parameter.device, parameter.dtype)
                effective_wd = effective_wd.to(parameter.device, parameter.dtype)
                updated[name] = (
                    parameter * (1.0 - effective_lr * effective_wd)
                    - effective_lr * corrected_m / (corrected_v.sqrt() + group["eps"])
                )
            return updated

        coordinates = torch.tensor(
            [math.log(base_lr), math.log(base_wd + wd_shift)],
            dtype=torch.float64, device=device, requires_grad=True,
        )
        # Centering makes the virtual baseline exactly the current Python
        # hyperparameters, including wd=0, without losing either derivative.
        eta = base_lr * (coordinates[0] - math.log(base_lr)).exp()
        decay = base_wd + (base_wd + wd_shift) * torch.expm1(
            coordinates[1] - math.log(base_wd + wd_shift)
        )
        baseline_loss = evaluate(virtual_update(eta, decay), tune_batch)
        baseline_value = float(baseline_loss.detach().cpu())
        if not math.isfinite(baseline_value):
            result["reason"] = "nonfinite_baseline_tune_loss"
            return result
        result["baseline_tune_loss"] = baseline_value
        if not baseline_loss.requires_grad:
            result["reason"] = "disconnected_hyperparameters"
            return result
        hypergradient, = torch.autograd.grad(baseline_loss, coordinates, allow_unused=True)
        if hypergradient is None:
            result["reason"] = "disconnected_hyperparameters"
            return result
        if not bool(torch.isfinite(hypergradient).all()):
            result["reason"] = "nonfinite_hypergradient"
            return result
        result["hypergradients"] = {
            "log_lr": float(hypergradient[0].detach().cpu()),
            "log_shifted_weight_decay": float(hypergradient[1].detach().cpu()),
        }
        if not bool((hypergradient != 0).any()):
            result["reason"] = "zero_hypergradient"
            return result
        direction = hypergradient.detach()
        if bool(cfg.get("normalize_hypergradient", True)):
            direction = direction / (direction.abs() + 1e-12)
        origin = coordinates.detach()
        result["reason"] = "no_tune_improvement"
        previous_trial: tuple[float, float] | None = None
        for backtracks in range(max_backtracks + 1):
            trial = origin - hyper_lr * backtrack_factor ** backtracks * direction
            # Bound the log coordinates *before* exp to avoid overflow.
            bounded_lr_coordinate = trial[0].clamp(math.log(min_lr), math.log(max_lr))
            bounded_wd_coordinate = trial[1].clamp(math.log(min_wd + wd_shift), math.log(max_wd + wd_shift))
            trial_lr = base_lr * (bounded_lr_coordinate - origin[0]).exp()
            trial_wd = base_wd + (base_wd + wd_shift) * torch.expm1(bounded_wd_coordinate - origin[1])
            trial_lr = trial_lr.clamp(min_lr, max_lr)
            trial_wd = trial_wd.clamp(min_wd, max_wd)
            lr_value = max(min_lr, min(max_lr, float(trial_lr.cpu())))
            wd_value = max(min_wd, min(max_wd, float(trial_wd.cpu())))
            result["backtracks"] = backtracks
            if (lr_value, wd_value) == previous_trial:
                continue
            previous_trial = (lr_value, wd_value)
            result["attempts"] += 1
            result["proposed_lr"] = lr_value
            result["proposed_weight_decay"] = wd_value
            with torch.no_grad():
                candidate_loss = evaluate(virtual_update(trial_lr, trial_wd), tune_batch)
            candidate_value = float(candidate_loss.detach().cpu())
            result["candidate_tune_loss"] = candidate_value if math.isfinite(candidate_value) else None
            if math.isfinite(candidate_value) and candidate_value < baseline_value - min_improvement:
                result.update({
                    "accepted": True, "lr": lr_value, "weight_decay": wd_value,
                    "group_lrs": [lr * lr_value / base_lr for lr in group_lrs],
                    "group_weight_decays": [max(0.0, wd + scale * (wd_value - base_wd))
                                             for wd, scale in zip(group_wds, decay_scales)],
                    "reason": "accepted_tune_improvement",
                })
                return result
        return result
