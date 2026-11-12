#!/usr/bin/env python3
"""Replay the volume-eight reader design through PerfectJet's generic optimizer."""
from __future__ import annotations

import json
from pathlib import Path

import vol8_reader as local
from perfectjet.observation_design import optimize_coefficient_panel

HERE = Path(__file__).resolve().parent
CERT = json.loads((HERE/"connected_volume8/connected_certificate.json").read_text())


def perfectjet_report(mode):
    names, _ = local.model(mode, None)
    return optimize_coefficient_panel(
        [dict(p) for p in local.factors(mode)],
        names=list(names))


def local_report(mode):
    return local.optimize(mode=mode)


def compare(mode):
    pj = perfectjet_report(mode)
    native = local_report(mode)
    checks = {
        "panel": pj["optimal_panel"] == native["optimal_panel"],
        "gain": pj["inverse_infinity_norm"] == native["optimal_gain"],
        "determinant": pj["optimal_determinant"] == native["optimal_determinant"],
        "subsets_checked": pj["subsets_checked"] == native["panels_tested"],
        "invertible": pj["invertible"] == native["nonsingular"],
        "ties": pj["optimal_ties"] == native["optimal_panel_count"],
    }
    if not all(checks.values()):
        raise AssertionError((mode, checks, pj, native))
    return {"mode": mode, "checks": checks, "perfectjet": pj, "native": native}


def receipt():
    general = compare("general")
    connected = compare("connected")
    panel = CERT["panel"]
    if connected["perfectjet"]["optimal_panel"] != panel["degrees"]:
        raise AssertionError("connected panel disagrees with retained certificate")
    if connected["perfectjet"]["optimal_determinant"] != panel["determinant"]:
        raise AssertionError("connected determinant disagrees with retained certificate")
    if connected["perfectjet"]["inverse_infinity_norm"] != panel["inverse_infinity_norm"]:
        raise AssertionError("connected gain disagrees with retained certificate")
    return {
        "schema": "singularity/perfectjet-observation-bridge/1",
        "general": general,
        "connected": connected,
        "retained_connected_certificate_replayed": True,
        "scope": (
            "Independent cross-repository replay of the exact exhaustive optimization "
            "within distinct unscaled single q-coefficient observations. It does not "
            "claim optimality among arbitrary rational linear sensors."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(receipt(), indent=2, sort_keys=True))
