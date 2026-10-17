"""Portable exact coefficient certificates with independent profile replay.

The source digest identifies the declared finite graph. It provides integrity,
not authentication of an external source or proof of historical provenance.
Replay does not trust a digest, a recorded success flag, or supplied totals:
it reconstructs graph energies, enumerates profiles independently, checks the
threshold-set identity and normalization, and verifies supplied factor claims.

Two recomputation routes are used, neither of which is the builder's
weak-composition engine in ``heights.py``: a replay-local stars-and-bars
generator, and the level-chain generator of ``chains.py``, which produces
nested threshold sets directly.  ``parse_certificate`` checks the packet's
structure and canonical JSON form before any arithmetic.  The format name
``relational-height/1`` from the original roadmap is not a second format;
see decision D007 and docs/specifications/COEFFICIENTS-v1.md, section 9.
"""

from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from math import comb
import json

from .chains import chain_marked_coefficients
from .euler import euler_exponents, first_difference, recompose_euler
from .polynomials import normalize, polynomial_from_json, polynomial_to_json, verify_factorization

VERSION = "singularity.certificate/1"
SUPERSEDED_NAMES = ("relational-height/1",)
_TOP_LEVEL = {
    "format", "label", "graph", "graph_sha256", "max_volume", "local_coefficients",
    "normalized_coefficients", "marked_coefficients", "profile_count",
    "euler_exponents", "identities",
}
_COMPARISON = {"graph", "graph_sha256", "local_coefficients", "first_difference"}


def _source(graph) -> dict:
    return {"n": graph.n, "edges": [list(edge) for edge in graph.edges]}


def _source_digest(source: dict) -> str:
    return sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _same_json(left, right) -> bool:
    """Type-sensitive JSON equality: a supplied boolean is not the count one."""
    return json.dumps(left, sort_keys=True, separators=(",", ":"), allow_nan=False) == json.dumps(right, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _counts_to_json(coefficients) -> list[list[list[int]]]:
    return [[[energy, count] for energy, count in sorted(poly.items()) if count] for poly in coefficients]


def _marked_to_json(marked) -> list[list[int]]:
    return [[volume, energy, span, count] for (volume, energy, span), count in sorted(marked.items()) if count]


def build_certificate(graph, max_volume: int, comparison=None, label: str = "", factorization: dict | None = None) -> dict:
    """Construct a JSON-serializable mathematical claim from the core engine.

    ``comparison`` is an optional second graph. ``factorization``, if supplied,
    declares coefficient*q**monomial*prod((1-q**degree)**multiplicity), with
    rational coefficient written as a string and factors as [degree,power].
    An invalid factorization is rejected immediately and also checked by replay.
    """
    from .heights import local_coefficients, marked_coefficients, normalized_coefficients

    if not isinstance(max_volume, int) or isinstance(max_volume, bool) or max_volume < 0:
        raise ValueError("max_volume must be a nonnegative integer")
    if not isinstance(label, str):
        raise TypeError("label must be text")
    local = local_coefficients(graph, max_volume)
    source = _source(graph)
    certificate = {
        "format": VERSION, "label": label, "graph": source,
        "graph_sha256": _source_digest(source), "max_volume": max_volume,
        "local_coefficients": _counts_to_json(local),
        "normalized_coefficients": _counts_to_json(normalized_coefficients(graph, max_volume)),
        "marked_coefficients": _marked_to_json(marked_coefficients(graph, max_volume)),
        "profile_count": comb(max_volume + graph.n, graph.n),
        "euler_exponents": [polynomial_to_json(poly) for poly in euler_exponents(local)],
        "identities": {"shift_normalization": True, "nested_threshold_energy": True},
    }
    if comparison is not None:
        if comparison.n != graph.n:
            raise ValueError("comparison graphs must have the same number of vertices")
        other = local_coefficients(comparison, max_volume)
        found = first_difference(local, other)
        difference = None if found is None else {"volume": found[0], "polynomial": polynomial_to_json(found[1])}
        comparison_source = _source(comparison)
        certificate["comparison"] = {
            "graph": comparison_source, "graph_sha256": _source_digest(comparison_source),
            "local_coefficients": _counts_to_json(other), "first_difference": difference,
        }
        if factorization is not None:
            if found is None or not _verify_factors(found[1], factorization):
                raise ValueError("supplied factorization does not match the first difference")
            certificate["comparison"]["factorization"] = factorization
    elif factorization is not None:
        raise ValueError("factorization requires a comparison graph")
    return certificate


def _verify_factors(poly, declaration: dict) -> bool:
    if set(declaration) != {"coefficient", "monomial", "factors"}:
        return False
    if isinstance(declaration["coefficient"], bool) or not isinstance(declaration["coefficient"], (str, int)):
        return False
    monomial, factors = declaration["monomial"], declaration["factors"]
    if not isinstance(monomial, int) or isinstance(monomial, bool) or monomial < 0:
        return False
    total_degree = monomial
    for factor in factors:
        if len(factor) != 2:
            return False
        degree, multiplicity = factor
        if any(not isinstance(v, int) or isinstance(v, bool) for v in factor) or degree <= 0 or multiplicity < 0:
            return False
        total_degree += degree * multiplicity
    # A declared gigantic power cannot be expanded merely to discover that it
    # has the wrong degree. Nonzero products of these factors have this degree.
    if not poly or total_degree != max(poly) or not Fraction(declaration["coefficient"]):
        return False
    return verify_factorization(poly, Fraction(declaration["coefficient"]), declaration["monomial"], declaration["factors"])


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _graph_errors(source, name: str) -> list[str]:
    if not isinstance(source, dict) or set(source) != {"n", "edges"}:
        return [f"{name}: must be an object with exactly n and edges"]
    n, edges = source["n"], source["edges"]
    if not _is_int(n) or n < 1:
        return [f"{name}: n must be a positive integer"]
    if not isinstance(edges, list):
        return [f"{name}: edges must be a list"]
    errors, previous = [], None
    for index, edge in enumerate(edges):
        if not isinstance(edge, list) or len(edge) != 2 or not all(map(_is_int, edge)):
            errors.append(f"{name}: edge {index} must be a pair of integers")
            continue
        u, v = edge
        if u == v:
            errors.append(f"{name}: edge {index} is a loop")
        elif not (0 <= u < n and 0 <= v < n):
            errors.append(f"{name}: edge {index} has an endpoint outside 0..n-1")
        elif u > v:
            errors.append(f"{name}: edge {index} is not written (min, max)")
        elif previous is not None and (u, v) <= previous:
            errors.append(f"{name}: edge {index} is duplicated or out of canonical order")
        else:
            previous = (u, v)
    return errors


def _count_rows_errors(rows, length: int, name: str) -> list[str]:
    if not isinstance(rows, list) or len(rows) != length:
        return [f"{name}: expected {length} volume rows"]
    errors = []
    for volume, row in enumerate(rows):
        if not isinstance(row, list):
            errors.append(f"{name}[{volume}]: row must be a list")
            continue
        last = -1
        for term in row:
            if not isinstance(term, list) or len(term) != 2 or not all(map(_is_int, term)):
                errors.append(f"{name}[{volume}]: terms must be [energy, count] integer pairs")
                break
            energy, count = term
            if energy < 0:
                errors.append(f"{name}[{volume}]: negative energy degree {energy}")
            elif energy <= last:
                errors.append(f"{name}[{volume}]: duplicate or unsorted energy degree {energy}")
            if count < 1:
                errors.append(f"{name}[{volume}]: counts must be positive")
            last = max(last, energy)
    return errors


def _marked_errors(rows, max_volume: int) -> list[str]:
    if not isinstance(rows, list):
        return ["marked_coefficients: must be a list"]
    errors, last = [], None
    for term in rows:
        if not isinstance(term, list) or len(term) != 4 or not all(map(_is_int, term)):
            errors.append("marked_coefficients: terms must be [volume, energy, span, count] integers")
            continue
        volume, energy, span, count = term
        if not 0 <= volume <= max_volume or energy < 0 or span < 0 or count < 1:
            errors.append(f"marked_coefficients: invalid term {term}")
        key = (volume, energy, span)
        if last is not None and key <= last:
            errors.append(f"marked_coefficients: duplicate or unsorted key {list(key)}")
        last = key
    return errors


def _polynomial_errors(entries, name: str) -> list[str]:
    if not isinstance(entries, list):
        return [f"{name}: polynomial must be a list"]
    last = -1
    for item in entries:
        if not isinstance(item, list) or len(item) != 3 or not all(map(_is_int, item)):
            return [f"{name}: terms must be [degree, numerator, denominator] integers"]
        degree, numerator, denominator = item
        if degree < 0:
            return [f"{name}: negative degree {degree}"]
        if degree <= last:
            return [f"{name}: duplicate or unsorted degree {degree}"]
        if numerator == 0 or denominator <= 0:
            return [f"{name}: zero numerator or nonpositive denominator"]
        if Fraction(numerator, denominator).denominator != denominator:
            return [f"{name}: rational coefficient is not in lowest terms"]
        last = degree
    return []


def parse_certificate(certificate) -> list[str]:
    """Return structural diagnostics; an empty list means well formed.

    This is a parser, not a proof: it checks keys, types, ranges, canonical
    ordering and uniqueness so that replay compares like with like.  It does
    not decide whether any count is mathematically correct.
    """
    if not isinstance(certificate, dict):
        return ["certificate must be a JSON object"]
    name = certificate.get("format")
    if name in SUPERSEDED_NAMES:
        return [f"format {name!r} is a superseded roadmap name; the implemented format is {VERSION!r}"]
    if name != VERSION:
        return ["unrecognized certificate format"]
    keys = set(certificate)
    missing = sorted(_TOP_LEVEL - keys)
    extra = sorted(keys - _TOP_LEVEL - {"comparison"})
    errors = [f"missing field {key}" for key in missing] + [f"unknown field {key}" for key in extra]
    if errors:
        return errors
    max_volume = certificate["max_volume"]
    if not _is_int(max_volume) or max_volume < 0:
        return ["max_volume must be a nonnegative integer"]
    if not isinstance(certificate["label"], str):
        errors.append("label must be text")
    errors += _graph_errors(certificate["graph"], "graph")
    for field in ("graph_sha256",):
        value = certificate[field]
        if not isinstance(value, str) or len(value) != 64 or set(value) - set("0123456789abcdef"):
            errors.append(f"{field} must be 64 lowercase hexadecimal digits")
    errors += _count_rows_errors(certificate["local_coefficients"], max_volume + 1, "local_coefficients")
    errors += _count_rows_errors(certificate["normalized_coefficients"], max_volume + 1, "normalized_coefficients")
    errors += _marked_errors(certificate["marked_coefficients"], max_volume)
    if not _is_int(certificate["profile_count"]) or certificate["profile_count"] < 1:
        errors.append("profile_count must be a positive integer")
    exponents = certificate["euler_exponents"]
    if not isinstance(exponents, list) or len(exponents) != max_volume + 1:
        errors.append(f"euler_exponents: expected {max_volume + 1} polynomials")
    else:
        for index, poly in enumerate(exponents):
            errors += _polynomial_errors(poly, f"euler_exponents[{index}]")
    if not isinstance(certificate["identities"], dict):
        errors.append("identities must be an object")
    if "comparison" in certificate:
        comparison = certificate["comparison"]
        if not isinstance(comparison, dict):
            return errors + ["comparison must be an object"]
        keys = set(comparison)
        if not _COMPARISON <= keys or keys - _COMPARISON - {"factorization"}:
            return errors + ["comparison must contain graph, graph_sha256, local_coefficients, first_difference and optional factorization"]
        errors += _graph_errors(comparison["graph"], "comparison.graph")
        digest = comparison["graph_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or set(digest) - set("0123456789abcdef"):
            errors.append("comparison.graph_sha256 must be 64 lowercase hexadecimal digits")
        errors += _count_rows_errors(comparison["local_coefficients"], max_volume + 1, "comparison.local_coefficients")
        found = comparison["first_difference"]
        if found is not None:
            if not isinstance(found, dict) or set(found) != {"volume", "polynomial"}:
                errors.append("comparison.first_difference must be null or {volume, polynomial}")
            elif not _is_int(found["volume"]) or not 0 <= found["volume"] <= max_volume:
                errors.append("comparison.first_difference.volume is out of range")
            else:
                errors += _polynomial_errors(found["polynomial"], "comparison.first_difference.polynomial")
        if "factorization" in comparison:
            declaration = comparison["factorization"]
            if not isinstance(declaration, dict) or set(declaration) != {"coefficient", "monomial", "factors"}:
                errors.append("comparison.factorization must contain coefficient, monomial and factors")
            elif not isinstance(declaration["factors"], list) or not all(
                isinstance(f, list) and len(f) == 2 and all(map(_is_int, f)) for f in declaration["factors"]
            ):
                errors.append("comparison.factorization.factors must be [degree, multiplicity] integer pairs")
    return errors


def _own_compositions(total: int, length: int):
    """Replay-local stars-and-bars generator, independent of the height engine.

    The iterative combination construction also avoids recursion-depth failure
    for many isolated vertices with a very small volume budget.
    """
    for bars in combinations(range(total + length - 1), length - 1):
        endpoints = (-1,) + bars + (total + length - 1,)
        yield tuple(endpoints[i + 1] - endpoints[i] - 1 for i in range(length))


def _independent_enumeration(graph, max_volume: int):
    local = [{} for _ in range(max_volume + 1)]
    normalized = [{} for _ in range(max_volume + 1)]
    marked: dict[tuple[int, int, int], int] = {}
    nested_checks = 0
    for volume in range(max_volume + 1):
        for profile in _own_compositions(volume, graph.n):
            energy = sum((profile[u] - profile[v]) ** 2 for u, v in graph.edges)
            local[volume][energy] = local[volume].get(energy, 0) + 1
            if min(profile) == 0:
                normalized[volume][energy] = normalized[volume].get(energy, 0) + 1
                span = max(profile)
                key = volume, energy, span
                marked[key] = marked.get(key, 0) + 1
                levels = [{i for i, height in enumerate(profile) if height >= t} for t in range(1, span + 1)]
                nested_energy = sum(sum((u in level) != (v in level) for u, v in graph.edges) for level in levels)
                for r in range(len(levels)):
                    for t in range(r + 1, len(levels)):
                        inner, outer = levels[t], levels[r]
                        crossing = sum((u in inner and v not in outer) or (v in inner and u not in outer) for u, v in graph.edges)
                        nested_energy += 2 * crossing
                if nested_energy != energy or sum(map(len, levels)) != volume:
                    raise ArithmeticError("threshold-set decomposition failed")
                nested_checks += 1
    for volume in range(max_volume + 1):
        shifted = dict(local[volume])
        if volume >= graph.n:
            for energy, count in local[volume - graph.n].items():
                shifted[energy] = shifted.get(energy, 0) - count
        shifted = {energy: count for energy, count in shifted.items() if count}
        if shifted != normalized[volume]:
            raise ArithmeticError("shift-normalization identity failed")
    return local, normalized, marked, nested_checks


def replay_certificate(certificate: dict, max_profiles: int = 2_000_000) -> dict:
    """Recompute every mathematical claim; return errors rather than trust flags.

    The work bound is explicit and can be raised by a caller. Refusal due to
    resource budget is not evidence that the certificate's mathematics is false.
    Metadata labels are displayed provenance only and are not authenticated.
    """
    from .graph import Graph

    report = {"valid": False, "errors": [], "checks": {}}
    errors, checks = report["errors"], report["checks"]
    try:
        structural = parse_certificate(certificate)
        if structural:
            errors.extend(structural)
            raise ValueError("malformed certificate; no arithmetic was attempted")
        max_volume = certificate["max_volume"]
        if not isinstance(max_volume, int) or isinstance(max_volume, bool) or max_volume < 0:
            raise ValueError("max_volume must be a nonnegative integer")
        if not isinstance(max_profiles, int) or isinstance(max_profiles, bool) or max_profiles < 1:
            raise ValueError("max_profiles must be a positive integer")
        source = certificate["graph"]
        if not isinstance(source, dict) or set(source) != {"n", "edges"}:
            raise ValueError("graph source must contain exactly n and edges")
        if not isinstance(source["n"], int) or isinstance(source["n"], bool) or not 1 <= source["n"] <= max_profiles:
            raise ValueError("graph order is invalid or exceeds replay work budget")
        graph = Graph(source["n"], source["edges"])
        if not _same_json(source, _source(graph)):
            raise ValueError("graph source must use sorted canonical edges")
        profiles = comb(max_volume + graph.n, graph.n)
        chains = profiles - comb(max_volume, graph.n)
        budget = (profiles + chains) * (2 if "comparison" in certificate else 1)
        if budget > max_profiles:
            raise ValueError(f"replay requires {budget} profiles and chains, exceeding max_profiles={max_profiles}")
        if certificate["graph_sha256"] != _source_digest(source):
            errors.append("graph source checksum mismatch")
        if not _same_json(certificate["profile_count"], profiles):
            errors.append("profile_count mismatch")
        local, normalized, marked, nested_checks = _independent_enumeration(graph, max_volume)
        checks.update({"profiles_recomputed": profiles, "nested_profiles_checked": nested_checks, "shift_normalization": True})
        chain_marked = chain_marked_coefficients(graph, max_volume)
        if chain_marked != marked:
            errors.append("level-chain and composition replay routes disagree")
        checks["chain_profiles_recomputed"] = sum(chain_marked.values())
        if not _same_json(certificate["local_coefficients"], _counts_to_json(local)):
            errors.append("local coefficients mismatch")
        if not _same_json(certificate["normalized_coefficients"], _counts_to_json(normalized)):
            errors.append("normalized coefficients mismatch")
        if not _same_json(certificate["marked_coefficients"], _marked_to_json(marked)):
            errors.append("marked coefficients mismatch")
        if not _same_json(certificate["identities"], {"shift_normalization": True, "nested_threshold_energy": True}):
            errors.append("identity declarations mismatch")
        supplied_euler = [polynomial_from_json(poly) for poly in certificate["euler_exponents"]]
        if len(supplied_euler) != max_volume + 1 or recompose_euler(supplied_euler) != [normalize(poly) for poly in local]:
            errors.append("Euler exponent recomposition mismatch")
        else:
            checks["euler_recomposition"] = True
        if "comparison" in certificate:
            comparison = certificate["comparison"]
            other_source = comparison["graph"]
            if set(other_source) != {"n", "edges"}:
                raise ValueError("comparison source must contain exactly n and edges")
            if not isinstance(other_source["n"], int) or isinstance(other_source["n"], bool) or other_source["n"] != graph.n:
                raise ValueError("comparison graph order mismatch")
            other = Graph(other_source["n"], other_source["edges"])
            if other.n != graph.n or not _same_json(other_source, _source(other)):
                raise ValueError("comparison graph order or canonical source mismatch")
            if comparison["graph_sha256"] != _source_digest(other_source):
                errors.append("comparison graph checksum mismatch")
            other_local, _, other_marked, other_nested = _independent_enumeration(other, max_volume)
            checks["profiles_recomputed"] += profiles
            checks["nested_profiles_checked"] += other_nested
            other_chain = chain_marked_coefficients(other, max_volume)
            # Local rows follow from marked rows by the shift identity, which
            # _independent_enumeration has already checked for this graph.
            if other_chain != other_marked:
                errors.append("comparison level-chain and composition replay routes disagree")
            checks["chain_profiles_recomputed"] += sum(other_chain.values())
            if not _same_json(comparison["local_coefficients"], _counts_to_json(other_local)):
                errors.append("comparison local coefficients mismatch")
            found = first_difference(local, other_local)
            expected = None if found is None else {"volume": found[0], "polynomial": polynomial_to_json(found[1])}
            if not _same_json(comparison["first_difference"], expected):
                errors.append("first difference mismatch")
            if "factorization" in comparison and (found is None or not _verify_factors(found[1], comparison["factorization"])):
                errors.append("first difference factorization mismatch")
            checks["comparison_recomputed"] = True
    except (KeyError, TypeError, ValueError, ArithmeticError, OverflowError) as error:
        errors.append(f"certificate could not be replayed: {error}")
    report["valid"] = not errors
    return report
