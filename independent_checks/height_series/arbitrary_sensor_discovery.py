#!/usr/bin/env python3
"""Exact dual proof of global optimality among arbitrary l1-normalized sensors."""
from __future__ import annotations
import json
import vol8_reader as reader
from perfectjet.observation_design import certify_l1_sensor_global_optimum


def replay():
    results={}
    for mode, panel, critical, expected in (
        ("general",(4,8,12,14,18,24,26),1,"93093/14165"),
        ("connected",(6,10,14,18,24,26),1,"44191/19786"),
    ):
        names,_=reader.model(mode,None)
        cert=certify_l1_sensor_global_optimum(
            [dict(p) for p in reader.factors(mode)],panel,critical,names)
        if cert["global_optimal_gain"]!=expected:
            raise AssertionError((mode,cert["global_optimal_gain"],expected))
        results[mode]=cert
    return {
        "schema":"singularity/arbitrary-l1-sensor-global-optimum/1",
        "results":results,
        "scope":"Global over arbitrary rational coefficient sensors of l1 cost <=1, with adversarial coefficientwise errors bounded equally.",
        "not_claimed":"No optimality statement under correlated, stochastic, or differently scaled noise models."
    }


if __name__=="__main__":
    print(json.dumps(replay(),indent=2,sort_keys=True))
