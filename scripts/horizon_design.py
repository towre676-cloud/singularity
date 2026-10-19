#!/usr/bin/env python3
"""NX10-A receipt: exact constant-input response-tail certificates.

Records, for the two scalar examples and the nonnormal example, the steady
output, contraction factor rho and tail constant K, and checks the bound
|y_k - y_inf| <= K rho^k against independent forward iteration for k < 40.
With --check the retained JSON must match.  Timings are not retained.
"""
import argparse
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from singularity.horizon_design import LinearCandidate, certify_response_tail, step_system  # noqa: E402

REPORT = ROOT / 'results' / 'horizon_design.json'
CASES = [("half_decay", ((F(1, 2),),), ((1,),), ((1,),), None, 1),
         ("alternating_decay", ((F(-1, 3),),), ((2,),), ((1,),), None, 1),
         ("nonnormal_step", ((F(1, 2), F(10)), (F(0), F(1, 2))), ((0,), (1,)), ((1, 0),), None, 1),
         ("nonnormal_free", ((F(1, 2), F(10)), (F(0), F(1, 2))), ((0,), (1,)), ((1, 0),), (0, 1), 0)]


def forward(s, count):
    n, x, out = len(s.A), list(s.x0), []
    for _ in range(count):
        out.append(sum(c * v for c, v in zip(s.c, x)) + s.e)
        x = [sum(s.A[i][j] * x[j] for j in range(n)) + s.b[i] for i in range(n)]
    return out


def experiment():
    rows = []
    for name, A, B, C, x0, u in CASES:
        system = step_system(LinearCandidate(name, A, B, C, initial=x0), (u,), 0)
        tail = certify_response_tail(system)
        ys = forward(system, 40)
        assert all(abs(y - tail.steady_output) <= tail.bound(k) for k, y in enumerate(ys))
        rows.append({'case': name, 'steady_output': str(tail.steady_output), 'rho': str(tail.metric.rho),
                     'K': str(tail.K), 'max_gap_first_40': str(max(abs(y - tail.steady_output) for y in ys)),
                     'bound_holds_first_40': True})
    return {'schema': 'singularity.horizon-design-receipt/1', 'unit': 'NX10-A',
            'scope': 'Constant-input step experiments from a declared reset; exact rational data. '
                     'NX10-B/C (horizon optimisation, thermal pairs) are not part of this receipt.',
            'cases': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    payload = experiment()
    if parser.parse_args().check:
        if not REPORT.exists() or json.loads(REPORT.read_text()) != payload:
            raise SystemExit('retained horizon-design receipt is missing or stale')
        print('NX10-A response-tail receipt matches')
    else:
        REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
        print(json.dumps(payload['cases'], indent=1))


if __name__ == '__main__':
    main()
