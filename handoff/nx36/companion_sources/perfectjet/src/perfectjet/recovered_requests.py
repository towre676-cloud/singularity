"""Bounded JSON request adapters for the recovered mathematical laboratories.

Every accepted parameter is used.  Unknown and mode-incompatible keys raise an
error rather than falling back to a demonstration. Exact rational parameters
are integers or strings such as ``"1/10"``; JSON floats are deliberately rejected.
``schemas()`` supplies directly runnable sample requests for each laboratory.
"""
from __future__ import annotations

from fractions import Fraction as Q
import re


def _keys(params, allowed):
    unknown = set(params) - set(allowed)
    if unknown:
        raise ValueError("unsupported parameter(s): " + ", ".join(sorted(map(str, unknown))))


def _integer(value, name, minimum=0, maximum=1000):
    if isinstance(value, str) and len(value) <= 310 and re.fullmatch(r"[+-]?\d+", value):
        value = int(value)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def _bool(value, name):
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _q(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Q)):
        raise ValueError("exact rational inputs must be integers or rational strings")
    if isinstance(value, str):
        if len(value) > 256:
            raise ValueError("rational string exceeds the request limit")
        exponent = re.search(r"[eE]([+-]?\d+)$", value)
        if exponent and abs(int(exponent.group(1))) > 100:
            raise ValueError("rational exponent exceeds the request limit")
    try:
        result = Q(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("invalid exact rational") from exc
    if max(result.numerator.bit_length(), result.denominator.bit_length()) > 512:
        raise ValueError("rational bit-size exceeds the request limit")
    return result


def _list(value, name, maximum):
    if not isinstance(value, (list, tuple)) or len(value) > maximum:
        raise ValueError(f"{name} must be an array with at most {maximum} entries")
    return value


def _point(value):
    value = _list(value, "point", 2)
    if len(value) != 2:
        raise ValueError("point must have two rational coordinates")
    return tuple(_q(x) for x in value)


def _json(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(v) for v in value]
    return value


def schemas() -> dict:
    """Accepted request shapes, limits, and examples; no input is decorative."""
    return {
        "branches": {
            "description": "Independent identical attempts; strict error threshold; all four outcome channels retained.",
            "allowed_keys": ["exact", "frame", "repeat", "silent", "cost", "max_attempts", "failure_threshold",
                             "risk", "risk_price", "exhaustion_failure", "exhaustion_cost", "frame_cost"],
            "sample_params": {"exact": "3/5", "frame": "1/5", "repeat": "19/100", "silent": "1/100",
                              "cost": 1, "max_attempts": 6, "failure_threshold": "1/20", "risk": 10},
            "limits": "1..128 attempts; exact nonnegative costs and probabilities summing to one",
        },
        "analytic": {
            "description": "Exact circular-log coefficient or finite twisted visible-ray coefficient identity.",
            "modes": {
                "log_circle": ["mode", "charge", "center", "radius", "orientation", "divisors"],
                "visible_ray": ["mode", "n", "modulus", "residue", "root_order", "character_exponents"],
            },
            "sample_params": {"mode": "log_circle", "charge": 3, "radius": "1/10", "orientation": 1},
            "additional_samples": [{"mode": "visible_ray", "n": 40, "modulus": 5, "residue": 2,
                                    "root_order": 4, "character_exponents": [None, 0, 1, 3, 2]}],
            "limits": "64 supplied divisors; modulus/root order <=32; 1..512 arithmetic coefficients",
        },
        "growth": {
            "description": "Finite colored graph census, weighted partition, and all-walk block bound.",
            "allowed_keys": ["node_count", "edges", "weights", "horizon", "start", "accepting",
                             "self_avoiding", "block_length", "tail_minimum"],
            "sample_params": {"node_count": 2, "edges": [[0, 1, "heavy"], [1, 0, "light"]],
                              "weights": {"heavy": 2, "light": "1/10"}, "horizon": 6, "block_length": 2},
            "limits": "32 nodes; 128 edges; 8 colors; horizon/block length <=32; bounded enumeration",
        },
        "conductor": {
            "description": "Conductor degeneracy transport or coprime CRT with Fourier/chirp twists.",
            "modes": {"transport": ["mode", "L", "M", "replay", "vector"],
                      "crt": ["mode", "L", "M", "replay"]},
            "sample_params": {"mode": "transport", "L": 3, "M": 9, "replay": True, "vector": [1, 2, 0]},
            "additional_samples": [{"mode": "crt", "L": 3, "M": 4, "replay": True}],
            "limits": "conductors/product <=32; exact entrywise replays",
        },
        "theta": {
            "description": "Type-A Cartan lattice finite numerator and remote exact coefficient.",
            "allowed_keys": ["rank", "conductor", "index", "direct_through"],
            "sample_params": {"rank": 3, "conductor": 3, "index": "100000000000000000000", "direct_through": 8},
            "limits": "rank 1..6; conductor 1..16; at most 20000 residue terms; index <=10^300",
        },
        "reach": {
            "description": "Sector connectivity under a supplied rational projector; optional independent matrix-span closure.",
            "allowed_keys": ["block_sizes", "vector", "projector", "verify_algebra"],
            "sample_params": {"block_sizes": [1, 2], "vector": [1, 1, 0], "verify_algebra": True},
            "limits": "total dimension <=8; supply either vector or projector, not both",
        },
    }


def _branches(p):
    from .branch_channels import Branch, BranchPartition, RetryModel
    _keys(p, schemas()["branches"]["allowed_keys"])
    if "risk" in p and "risk_price" in p:
        raise ValueError("supply risk or risk_price, not both")
    defaults = {"exact": "3/5", "frame": "1/5", "repeat": "19/100", "silent": "1/100"}
    partition = BranchPartition(tuple(Branch(kind, kind, _q(p.get(kind, default)),
                                             cost=_q(p.get("frame_cost", 0)) if kind == "frame" else 0)
                                      for kind, default in defaults.items()))
    model = RetryModel(partition, _q(p.get("cost", 1)), _q(p.get("exhaustion_failure", 1)),
                       _q(p.get("exhaustion_cost", 0)))
    depth = _integer(p.get("max_attempts", 8), "max_attempts", 1, 128)
    threshold = _q(p.get("failure_threshold", "1/20"))
    risk = _q(p.get("risk", p.get("risk_price", 0)))
    return {"partition": partition.receipt(), "silent_floor": str(model.silent_floor),
            "asymptotic_failure": str(model.asymptotic_failure),
            "at_max_attempts": model.evaluate(depth).receipt(),
            "schedule": model.optimize(depth, threshold, risk).receipt(),
            "scope": "explicit independent identical-attempt probability/cost model; no device-rate inference"}


def _analytic(p):
    from . import analytic_recovery as a
    mode = p.get("mode", "log_circle")
    if mode not in schemas()["analytic"]["modes"]:
        raise ValueError("analytic mode must be log_circle or visible_ray")
    _keys(p, schemas()["analytic"]["modes"][mode])
    if mode == "log_circle":
        center = _point(p.get("center", [0, 0]))
        if "divisors" in p:
            if "charge" in p:
                raise ValueError("charge is specified inside divisors; do not also supply charge")
            divisor_rows = _list(p["divisors"], "divisors", 64)
            divisors = []
            for row in divisor_rows:
                if not isinstance(row, dict) or set(row) != {"name", "point", "charge"}:
                    raise ValueError("each divisor requires exactly name, point, charge")
                divisors.append(a.LogDivisor(row["name"], _point(row["point"]),
                                             _integer(row["charge"], "charge", -1000000, 1000000)))
        else:
            divisors = [a.LogDivisor("target", center, _integer(p.get("charge", 3), "charge", -1000000, 1000000))]
        result = a.isolated_circle_period(divisors, center, _q(p.get("radius", "1/10")),
                                          _integer(p.get("orientation", 1), "orientation", -1, 1)).receipt()
        return {"mode": mode, "period": result}
    n = _integer(p.get("n", 40), "n", 1, 512)
    modulus = _integer(p.get("modulus", 3), "modulus", 1, 32)
    residue = _integer(p.get("residue", 1), "residue", -1000000, 1000000)
    root_order = _integer(p.get("root_order", 2), "root_order", 1, 32)
    if "character_exponents" in p:
        exponents = _list(p["character_exponents"], "character_exponents", 32)
        exponents = tuple(None if e is None else _integer(e, "root exponent", -1000000, 1000000) for e in exponents)
        character = a.DirichletCharacter(modulus, exponents, root_order)
    else:
        character = a.DirichletCharacter.principal(modulus, root_order)
    direct = a.twisted_visible_coefficients(character, n)
    quotient = a.dirichlet_l_ratio_coefficients(character, n)
    return {"mode": mode, "n": n, "modulus": modulus, "residue": residue % modulus,
            "root_order": root_order, "character_exponents": list(character.exponents),
            "coefficients": [x.receipt() for x in direct],
            "ratio_coefficients": [x.receipt() for x in quotient],
            "ratio_coefficient_identity": direct == quotient,
            "progression_coefficients": list(a.progression_visible_coefficients(modulus, residue, n)),
            "progression_residue_factor_times_inverse_zeta2": str(a.progression_residue_factor(modulus, residue)),
            "scope": "finite exact Dirichlet coefficients; not ratios of truncated numerical L-series"}


def _growth(p):
    from .weighted_growth import ColoredGraph
    _keys(p, schemas()["growth"]["allowed_keys"])
    node_count = _integer(p.get("node_count", 2), "node_count", 1, 32)
    edges = _list(p.get("edges", [[0, 0, "space"], [0, 1, "time"], [1, 0, "space"]]), "edges", 128)
    colors = []
    normalized_edges = []
    for edge in edges:
        edge = _list(edge, "edge", 3)
        if len(edge) != 3 or not isinstance(edge[2], str) or not 1 <= len(edge[2]) <= 64:
            raise ValueError("edges are [source, target, nonempty color]")
        normalized_edges.append((_integer(edge[0], "source", 0, node_count - 1),
                                 _integer(edge[1], "target", 0, node_count - 1), edge[2]))
        if edge[2] not in colors:
            colors.append(edge[2])
    if len(colors) > 8:
        raise ValueError("at most eight graph colors are supported")
    weights = p.get("weights", {"space": "1/7", "time": "1/5"})
    if not isinstance(weights, dict) or set(weights) != set(colors):
        raise ValueError("weights must specify exactly the graph colors")
    weights = {key: _q(value) for key, value in weights.items()}
    graph = ColoredGraph(node_count, normalized_edges)
    horizon = _integer(p.get("horizon", 10), "horizon", 0, 32)
    start = _integer(p.get("start", 0), "start", 0, node_count - 1)
    accepting = p.get("accepting")
    if accepting is not None:
        accepting = [_integer(x, "accepting node", 0, node_count - 1)
                     for x in _list(accepting, "accepting", 32)]
    self_avoiding = _bool(p.get("self_avoiding", False), "self_avoiding")
    block_length = _integer(p.get("block_length", 1), "block_length", 1, 32)
    tail_minimum = _integer(p.get("tail_minimum", 5), "tail_minimum", 0, 1000)
    histogram = graph.histogram(horizon, start=start, accepting=accepting, self_avoiding=self_avoiding,
                                max_frontier=20000, max_expansions=50000)
    evaluation = histogram.evaluate(weights)
    direct = graph.weighted_paths(horizon, weights, start=start, accepting=accepting,
                                  self_avoiding=self_avoiding, max_frontier=20000, max_expansions=50000)
    return {"node_count": node_count, "edges": normalized_edges, "weights": weights,
            "horizon": horizon, "start": start, "accepting": accepting, "self_avoiding": self_avoiding,
            "histogram": histogram.to_dict(), "repriced": evaluation.to_dict(),
            "direct_path_weight": str(direct), "direct_path_sum_agrees": direct == evaluation.partition,
            "growth_certificate": graph.block_certificate(weights, block_length).to_dict(tail_minimum),
            "scope": "finite graph only; certificate bounds all walks uniformly, including self-avoiding subsets"}


def _conductor(p):
    from .conductor_transport import ConductorTransport, crt_factorization, crt_permutation
    mode = p.get("mode", "transport")
    if mode not in schemas()["conductor"]["modes"]:
        raise ValueError("conductor mode must be transport or crt")
    _keys(p, schemas()["conductor"]["modes"][mode])
    lower = _integer(p.get("L", 3), "L", 1, 32)
    upper = _integer(p.get("M", 9 if mode == "transport" else 4), "M", 1, 32)
    replay = _bool(p.get("replay", True), "replay")
    if mode == "crt":
        if lower * upper > 32:
            raise ValueError("CRT conductor product must not exceed 32")
        return {"mode": mode, "L": lower, "M": upper,
                "permutation": crt_permutation(lower, upper),
                "replay": crt_factorization(lower, upper, max_conductor=32) if replay else None,
                "replayed": replay}
    model = ConductorTransport(lower, upper, max_conductor=32)
    vector = [_q(x) for x in _list(p.get("vector", [1] + [0] * (lower - 1)), "vector", 32)]
    # The public methods check the exact vector length against L.
    embedded, pullback = model.embed_support(vector), model.pullback(vector)
    return {"mode": mode, "L": lower, "M": upper, "vector": vector,
            "support_embedding": [x.record() for x in embedded],
            "pullback": [x.record() for x in pullback],
            "fourier_of_embedding": [x.record() for x in model.upper.fourier(embedded)],
            "replay": model.replay() if replay else None, "replayed": replay}


def _theta(p):
    from .conductor_transport import FiniteLatticeTheta, type_a_cartan
    _keys(p, schemas()["theta"]["allowed_keys"])
    rank = _integer(p.get("rank", 2), "rank", 1, 6)
    conductor = _integer(p.get("conductor", 3), "conductor", 1, 16)
    index = _integer(p.get("index", 10**100), "index", 0, 10**300)
    direct_through = _integer(p.get("direct_through", 8), "direct_through", 0, 12)
    if conductor ** rank > 20000:
        raise ValueError("theta residue population exceeds 20000")
    theta = FiniteLatticeTheta(type_a_cartan(rank), conductor, max_terms=20000, max_conductor=16)
    return theta.record(direct_through=direct_through, remote_index=index)


def _reach(p):
    from .categorical import rank_one_projector, sector_reach
    _keys(p, schemas()["reach"]["allowed_keys"])
    sizes = [_integer(x, "block size", 1, 8)
             for x in _list(p.get("block_sizes", [1, 2, 3]), "block_sizes", 8)]
    if not sizes or sum(sizes) > 8:
        raise ValueError("total sector dimension must be 1..8")
    n = sum(sizes)
    if "vector" in p and "projector" in p:
        raise ValueError("supply vector or projector, not both")
    if "projector" in p:
        projector = [[_q(x) for x in _list(row, "projector row", 8)]
                     for row in _list(p["projector"], "projector", 8)]
    else:
        vector = [_q(x) for x in _list(p.get("vector", [1] * n), "vector", 8)]
        if len(vector) != n:
            raise ValueError("vector length must equal total sector dimension")
        projector = rank_one_projector(vector)
    verify = _bool(p.get("verify_algebra", True), "verify_algebra")
    result = sector_reach(sizes, projector, verify_algebra=verify, max_dimension=8, max_products=20000)
    result["projector"] = projector
    result["verified_by_matrix_span"] = verify
    return result


def evaluate(lab: str, params: dict | None = None) -> dict:
    """Evaluate one laboratory, preserving the demo only for empty params."""
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ValueError("params must be an object")
    dispatch = {"branches": _branches, "analytic": _analytic, "growth": _growth,
                "conductor": _conductor, "theta": _theta, "reach": _reach}
    if lab not in dispatch:
        raise ValueError("unsupported recovered laboratory: " + str(lab))
    if not params:
        if lab == "branches":
            from .branch_channels import receipt
        elif lab == "analytic":
            from .analytic_recovery import receipt
        elif lab == "growth":
            from .weighted_growth import receipt
        elif lab in ("conductor", "theta"):
            from .conductor_transport import receipt
        else:
            from .categorical import receipt
        result = receipt()
        if lab == "theta":
            result = result["theta"]
        elif lab == "reach":
            result = {"reach_algebras": result["reach_algebras"], "scope": result["scope"]}
    else:
        result = dispatch[lab](params)
    return _json(result)
