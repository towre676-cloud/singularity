"""Small reproducible JSON interface for exact populations and comparisons."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
from typing import Sequence

from .examples import GRAPHS
from .graph import Graph
from .heights import local_coefficients, marked_coefficients, normalized_coefficients
from .invariants import binary_cut_profile, first_difference, laplacian_characteristic_polynomial
from .population import HeightPopulation


def _polynomial(poly: dict[int, int]) -> list[dict[str, int]]:
    return [{"energy": energy, "multiplicity": count} for energy, count in sorted(poly.items())]


def _graph_arguments(parser: argparse.ArgumentParser, *, allow_path: bool = False) -> None:
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--example", choices=sorted(GRAPHS), default=None)
    choice.add_argument("--graph-json", help="a graph JSON file, or an inline object with n and edges")
    if allow_path:
        choice.add_argument("--path", type=int, help="construct the path on this many vertices")


def _read_graph(args: argparse.Namespace) -> Graph:
    if getattr(args, "path", None) is not None:
        return Graph(args.path, ((i, i + 1) for i in range(args.path - 1)))
    if args.graph_json:
        source = args.graph_json
        text = source if source.lstrip().startswith("{") else Path(source).read_text(encoding="utf-8")
        return Graph.from_dict(json.loads(text))
    return GRAPHS[args.example or "binary_g"]


def _read_tuple(source: str) -> tuple[int, ...]:
    if source.lstrip().startswith("["):
        values = json.loads(source)
        if not isinstance(values, list):
            raise ValueError("rank candidate must be a JSON list or comma-separated integers")
        return tuple(values)
    return tuple(int(part.strip()) for part in source.split(","))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="singularity", description=__doc__)
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("examples", help="emit the four original labeled graph fixtures")
    profile = commands.add_parser("profile", help="compute exact cut and height observations")
    _graph_arguments(profile)
    profile.add_argument("--max-volume", type=int, default=3)
    compare = commands.add_parser("compare", help="compare two fixtures to a declared finite depth")
    compare.add_argument("left", choices=sorted(GRAPHS))
    compare.add_argument("right", choices=sorted(GRAPHS))
    compare.add_argument("--max-volume", type=int, default=4)
    compare.add_argument("--q", default="1/2", help="exact rational specialization of the first formal difference")
    population = commands.add_parser("population", help="count/rank/unrank a finite original-labeled height population")
    _graph_arguments(population)
    for parameter in ("max-height", "volume", "max-volume", "energy", "max-energy", "span", "max-span"):
        population.add_argument("--" + parameter, type=int)
    population.add_argument("--allow-positive-minimum", action="store_true", help="retain common height translations")
    population.add_argument("--sample", type=int, default=3)
    population.add_argument("--rank", help="candidate original heights as JSON or comma-separated integers")
    population.add_argument("--unrank", type=int, help="zero-based population index")
    euler = commands.add_parser("euler", help="compute exact formal Euler exponents and recompose them")
    _graph_arguments(euler)
    euler.add_argument("--max-volume", type=int, default=4)
    transfer = commands.add_parser("transfer", help="exact bounded-height forest message passing")
    _graph_arguments(transfer, allow_path=True)
    transfer.add_argument("--max-height", type=int, default=2)
    transfer.add_argument("--max-volume", type=int)
    transfer.add_argument("--min-zero", action="store_true")
    conductor = commands.add_parser("conductor", help="exact root-of-unity coefficient at an arbitrary index")
    _graph_arguments(conductor, allow_path=True)
    conductor.add_argument("--order", type=int, default=3)
    conductor.add_argument("--index", type=int, default=1000)
    conductor.add_argument("--max-profiles", type=int, default=1_000_000)
    conductor.add_argument("--numerator", action="store_true", help="include the complete finite residue numerator")
    certificate = commands.add_parser("certificate", help="build or independently replay an exact coefficient certificate")
    certificate_commands = certificate.add_subparsers(dest="certificate_action", required=True)
    create = certificate_commands.add_parser("build", help="emit the complete portable JSON certificate")
    _graph_arguments(create)
    create.add_argument("--max-volume", type=int, default=3)
    create.add_argument("--comparison", choices=sorted(GRAPHS))
    create.add_argument("--label", default="")
    create.add_argument("--claim-known-factorization", action="store_true", help="attach a checked factor claim for a canonical example pair")
    replay = certificate_commands.add_parser("replay", help="recompute and check a supplied certificate")
    replay.add_argument("source", help="certificate JSON file")
    replay.add_argument("--max-profiles", type=int, default=2_000_000)
    return parser


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.command == "examples":
        return {"schema": "singularity-examples/1", "graphs": {
            name: {**graph.to_dict(), "degrees": list(graph.degrees), "connected": graph.connected}
            for name, graph in GRAPHS.items()
        }}
    if args.command == "profile":
        graph = _read_graph(args)
        marked = marked_coefficients(graph, args.max_volume)
        return {
            "schema": "singularity-profile/1",
            "graph": graph.to_dict(),
            "degrees": list(graph.degrees),
            "connected": graph.connected,
            "max_volume": args.max_volume,
            "binary_cut_profile": [
                {"size": size, "cut": cut, "multiplicity": count}
                for (size, cut), count in binary_cut_profile(graph).items()
            ],
            "laplacian_characteristic_polynomial": list(laplacian_characteristic_polynomial(graph)),
            "local_coefficients": [_polynomial(row) for row in local_coefficients(graph, args.max_volume)],
            "normalized_coefficients": [_polynomial(row) for row in normalized_coefficients(graph, args.max_volume)],
            "marked_coefficients": [
                {"volume": volume, "energy": energy, "span": span, "multiplicity": count}
                for (volume, energy, span), count in marked.items()
            ],
        }
    if args.command == "compare":
        graph, other = GRAPHS[args.left], GRAPHS[args.right]
        difference = first_difference(graph, other, args.max_volume)
        q = Fraction(args.q)
        if not 0 <= q <= 1:
            raise ValueError("q must lie in [0,1] for the positive-weight interpretation")
        result: dict[str, object] = {
            "schema": "singularity-comparison/1",
            "left": {"name": args.left, **graph.to_dict()},
            "right": {"name": args.right, **other.to_dict()},
            "max_volume_searched": args.max_volume,
            "same_binary_cut_profile": binary_cut_profile(graph) == binary_cut_profile(other),
            "same_laplacian_characteristic_polynomial": laplacian_characteristic_polynomial(graph) == laplacian_characteristic_polynomial(other),
            "first_formal_difference": None,
            "interpretation": "a finite agreement is not a graph-isomorphism certificate",
        }
        if difference is not None:
            depth, polynomial = difference
            value = sum((Fraction(count) * q ** energy for energy, count in polynomial.items()), Fraction())
            result["first_formal_difference"] = {
                "volume": depth,
                "left_minus_right": _polynomial(polynomial),
                "specialization": {"q": str(q), "value": str(value)},
                "visibility_note": "specialization can erase this formal discrepancy" if value == 0 else "nonzero at the displayed exact q",
            }
        return result
    if args.command == "population":
        graph = _read_graph(args)
        population = HeightPopulation(
            graph,
            **{name: getattr(args, name) for name in ("max_height", "volume", "max_volume", "energy", "max_energy", "span", "max_span")},
            min_zero=not args.allow_positive_minimum,
        )
        output = population.to_dict(sample=args.sample)
        if args.rank is not None:
            output["rank_request"] = population.witness(_read_tuple(args.rank))
        if args.unrank is not None:
            output["unrank_request"] = population.witness(population.unrank(args.unrank))
        return output
    if args.command == "euler":
        from .euler import euler_exponents, recompose_euler
        from .polynomials import normalize, polynomial_to_json

        graph = _read_graph(args)
        local = local_coefficients(graph, args.max_volume)
        exponents = euler_exponents(local)
        return {
            "schema": "singularity-euler/1", "graph": graph.to_dict(),
            "max_volume": args.max_volume,
            "exponents": [polynomial_to_json(row) for row in exponents],
            "recomposition_matches": recompose_euler(exponents) == [normalize(row) for row in local],
            "interpretation": "finite formal exponents; no global analytic continuation is asserted",
        }
    if args.command == "transfer":
        from .transfer import bounded_height_histogram

        if args.path is None and args.example is None and args.graph_json is None:
            graph = Graph(4, [(0, 1), (1, 2), (2, 3)])
        else:
            graph = _read_graph(args)
        histogram = bounded_height_histogram(graph, args.max_height, args.max_volume, args.min_zero)
        return {
            "schema": "singularity-forest-transfer/1", "graph": graph.to_dict(),
            "max_height": args.max_height, "max_volume": args.max_volume,
            "min_zero": args.min_zero,
            "count": sum(histogram.values()),
            "histogram": [{"volume": volume, "energy": energy, "multiplicity": count} for (volume, energy), count in histogram.items()],
        }
    if args.command == "conductor":
        from .conductor import CyclotomicRing, remote_coefficient, residue_numerator

        graph = _read_graph(args)
        ring = CyclotomicRing(args.order)
        output = {
            "schema": "singularity-conductor/1", "graph": graph.to_dict(),
            "order": args.order, "index": args.index,
            "cyclotomic_polynomial_constant_first": list(ring.modulus),
            "coefficient_constant_first": list(remote_coefficient(graph, args.order, args.index, args.max_profiles)),
            "denominator": {"step": args.order, "power": graph.n},
            "residue_profiles": args.order ** graph.n,
        }
        if args.numerator:
            _, numerator = residue_numerator(graph, args.order, args.max_profiles)
            output["numerator_constant_first"] = [list(row) for row in numerator]
        return output
    if args.command == "certificate":
        from .certificates import build_certificate, replay_certificate

        if args.certificate_action == "replay":
            source = json.loads(Path(args.source).read_text(encoding="utf-8"))
            return replay_certificate(source, args.max_profiles)
        graph = _read_graph(args)
        comparison = None if args.comparison is None else GRAPHS[args.comparison]
        factors = None
        if args.claim_known_factorization:
            if args.example == "binary_g" and args.comparison == "binary_h":
                factors = {"coefficient": "1", "monomial": 3, "factors": [[1, 1], [3, 2], [4, 2]]}
            elif args.example == "spectral_g" and args.comparison == "spectral_h":
                factors = {"coefficient": "2", "monomial": 2, "factors": [[1, 2], [2, 1]]}
            else:
                raise ValueError("known factors require --example binary_g --comparison binary_h, or the corresponding spectral pair")
        return build_certificate(graph, args.max_volume, comparison, args.label, factors)
    raise ValueError("unknown command")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except (OSError, TypeError, ValueError, IndexError, ZeroDivisionError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, indent=None if args.compact else 2))
    return int(args.command == "certificate" and args.certificate_action == "replay" and not result["valid"])
