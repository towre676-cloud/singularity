"""Finite visibility filtrations: prefix-equivalence classes and split witnesses.

Two series are equivalent through volume v when every coefficient at degrees
0..v agrees in the chosen domain (SNG-F33):

* ``"polynomial"``: equality of q-polynomials (the symbolic series);
* ``"marked"``: equality of (volume, energy, span) counts, through a bound
  the caller states (marked dictionaries carry no length);
* a rational parameter ``Fraction``: equality of values at q = q0;
* an algebraic parameter ``{"defining": f, "root": r}`` from parameters.py:
  equality of values at that root, decided exactly by gcd and Sturm counts.

Classes are ordered by their least member name and identified by
``"v<volume>:c<index>"``.  When a class splits at volume v, the witness is
the signed discrepancy (first member minus other) at v between the class's
first member and the first member of each new part; all lower coefficients
agree by construction.  Classes alive at the bound are agreement through the
bound only, never equality of full series.  Inputs of different lengths are
compared through their common prefix.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Mapping, Sequence

from .parameters import vanishes_at
from .polynomials import evaluate, normalize, polynomial_to_json, sub


def _rows(series, domain, bound=None) -> list:
    if domain == "marked":
        if not isinstance(series, Mapping):
            raise TypeError("marked domain expects (volume, energy, span) dictionaries")
        if bound is None:
            raise ValueError("marked dictionaries carry no length: state the bound they were computed through")
        rows = [{} for _ in range(bound + 1)]
        for (volume, energy, span), count in series.items():
            if volume <= bound:
                rows[volume][(energy, span)] = count
        return rows
    return [normalize(row) for row in series]


def _equal(left, right, domain) -> bool:
    if domain in ("polynomial", "marked"):
        return left == right
    difference = sub(left, right)
    if isinstance(domain, Fraction) or isinstance(domain, int):
        return evaluate(difference, Fraction(domain)) == 0
    return vanishes_at(difference, domain["root"], domain["defining"])


def _witness(left, right, domain):
    if domain == "marked":
        keys = sorted(set(left) | set(right))
        return [[e, h, left.get((e, h), 0) - right.get((e, h), 0)] for e, h in keys if left.get((e, h), 0) != right.get((e, h), 0)]
    difference = sub(left, right)
    if isinstance(domain, (Fraction, int)) and not isinstance(domain, bool):
        value = evaluate(difference, Fraction(domain))
        return {"polynomial": polynomial_to_json(difference), "value": f"{value.numerator}/{value.denominator}"}
    return {"polynomial": polynomial_to_json(difference)}


def visibility_filtration(named: Mapping[str, object], domain="polynomial", bound: int | None = None) -> dict:
    """Partition named series by prefix equivalence at every volume 0..bound."""
    if isinstance(domain, bool):
        raise TypeError("domain must be 'polynomial', 'marked', a rational, or an algebraic root")
    names = sorted(named)
    if not names:
        raise ValueError("at least one series is required")
    rows = {name: _rows(named[name], domain, bound) for name in names}
    common = min(len(r) for r in rows.values()) - 1
    if bound is None:
        bound = common
    if not isinstance(bound, int) or isinstance(bound, bool) or not 0 <= bound <= common:
        raise ValueError(f"bound must lie in 0..{common}, the common prefix of the inputs")
    classes = [names]
    levels, splits = [], []
    for volume in range(bound + 1):
        refined = []
        for members in classes:
            parts: list[list[str]] = []
            for name in members:
                for part in parts:
                    if _equal(rows[part[0]][volume], rows[name][volume], domain):
                        part.append(name)
                        break
                else:
                    parts.append([name])
            if len(parts) > 1:
                for part in parts[1:]:
                    splits.append({
                        "volume": volume, "left": parts[0][0], "right": part[0],
                        "discrepancy_left_minus_right": _witness(rows[parts[0][0]][volume], rows[part[0]][volume], domain),
                    })
            refined.extend(parts)
        classes = sorted(refined, key=lambda c: c[0])
        levels.append({"volume": volume, "classes": [
            {"id": f"v{volume}:c{index}", "members": members} for index, members in enumerate(classes)]})
    unresolved = [members for members in classes if len(members) > 1]
    return {
        "domain": _domain_json(domain), "bound": bound, "levels": levels, "splits": splits,
        "unresolved_at_bound": [{"members": m, "status": f"agreement through volume {bound} only"} for m in unresolved],
    }


def _domain_json(domain):
    if domain in ("polynomial", "marked"):
        return domain
    if isinstance(domain, (Fraction, int)):
        value = Fraction(domain)
        return {"q": f"{value.numerator}/{value.denominator}"}
    root = domain["root"]
    if "rational" in root:
        return {"q": str(root["rational"])}
    a, b = root["interval"]
    return {"q_root_of": polynomial_to_json(domain["defining"]), "isolating_interval": [str(a), str(b)]}


def first_split_volume(left, right, domain="polynomial", bound: int | None = None) -> int | None:
    """Least volume where two series differ in the domain, within the common prefix.

    None means agreement through the shared prefix only.
    """
    a, b = _rows(left, domain, bound), _rows(right, domain, bound)
    return next((v for v in range(min(len(a), len(b))) if not _equal(a[v], b[v], domain)), None)
