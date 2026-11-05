"""Independent direct-height/edge-inversion oracle and exact receipts."""
import sys
import json
import time
import hashlib
from pathlib import Path
from fractions import Fraction as Q
from itertools import combinations
from math import comb
from defect_kernel import defect_kernel

ROOT = Path(__file__).resolve().parent
REPO = ROOT / 'reference'
if not REPO.exists():
    REPO = ROOT.parent / 'singularity' / 'independent_checks' / 'height_series'
sys.path.insert(0, str(REPO))
import vol8_lib as lib
from vol8_offdiagonal import first_off_diagonal, second_off_diagonal


def oracle(k, edges, R, d):
    """Raw edge inversion of logZ, with independently written polynomial code.

    For connected H with k>1 every proper-support logarithm omits an edge
    incident to its missing vertex and hence vanishes under edge inversion.
    k=1 is directly logZ. No particle partitions or deletion components.
    """
    def plus(a, b, f=1):
        out = dict(a)
        for j, c in b.items():
            out[j] = out.get(j, Q(0))+f*c
        return {j: c for j, c in out.items() if c}
    def times(a, b):
        out = {}
        for i, a0 in a.items():
            for j, b0 in b.items():
                out[i+j] = out.get(i+j, Q(0))+a0*b0
        return {j: c for j, c in out.items() if c}
    def heights(r):
        for bars in combinations(range(r+k-1), k-1):
            b = (-1,)+bars+(r+k-1,)
            yield tuple(b[i+1]-b[i]-1 for i in range(k))
    ans = [{} for _ in range(R+1)]
    for mask in range(1 << len(edges)):
        F = [e for i, e in enumerate(edges) if mask >> i & 1]
        Z = [{0: Q(1)}]+[{} for _ in range(R)]
        for r in range(1, R+1):
            for h in heights(r):
                E = d*sum(a*a for a in h)-2*sum(h[u]*h[v] for u, v in F)
                Z[r][E] = Z[r].get(E, Q(0))+1
            assert sum(Z[r].values()) == comb(r+k-1, k-1)
        ell = [{} for _ in range(R+1)]
        for r in range(1, R+1):
            num = {E: r*c for E, c in Z[r].items()}
            for j in range(1, r):
                num = plus(num, times(ell[j], Z[r-j]), -j)
            ell[r] = {E: c/r for E, c in num.items()}
            ans[r] = plus(ans[r], ell[r], (-1)**(len(edges)-len(F)))
    return ans


def main():
    start = time.perf_counter()
    counts = {'raw_height_edge_inversion': 0, 'existing_offdiagonal': 0,
              'third_against_repository_beta': 0, 'relabel': 0}
    examples = []
    for k in range(1, 6):
        for m in lib.connected_types(k):
            edges = lib.edges_of(m, k)
            direct = oracle(k, edges, k+3, 3)
            for s in range(4):
                result = defect_kernel(k, edges, s)
                assert result == direct[k+s], (k, m, s)
                counts['raw_height_edge_inversion'] += 1
            for s, fn in ((1, first_off_diagonal), (2, second_off_diagonal)):
                assert defect_kernel(k, edges, s) == fn(m, k)
                counts['existing_offdiagonal'] += 1
            p = defect_kernel(k, edges, 3)
            perm = tuple(reversed(range(k)))
            assert p == defect_kernel(k, [(perm[u], perm[v]) for u,v in edges], 3)
            counts['relabel'] += 1
            examples.append({'k': k, 'mask': m, 'excess': 3,
                             'polynomial': {str(e): str(c) for e, c in sorted(p.items())}})
    # Every connected six-vertex subcubic type, at volume nine.
    for m in lib.connected_types(6):
        p = defect_kernel(6, lib.edges_of(m, 6), 3)
        assert p == lib.beta_coeffs(m, 6, 9)[9], (6, m)
        counts['third_against_repository_beta'] += 1
        examples.append({'k': 6, 'mask': m, 'excess': 3,
                         'polynomial': {str(e): str(c) for e, c in sorted(p.items())}})
    # General ambient degree and the singleton boundary case.
    for k, edges, d, s in ((1, (), 0, 5), (1, (), 4, 4),
                          (4, tuple(combinations(range(4), 2)), 4, 3),
                          (3, ((0,1),(1,2)), 2, 3)):
        assert defect_kernel(k, edges, s, d) == oracle(k, edges, k+s, d)[k+s]
        counts['raw_height_edge_inversion'] += 1
    # Input validation is part of the standalone public function contract.
    bad = [(2, [(0,0)], 1, 3), (2, [(0,1),(1,0)], 1, 3),
           (3, [(0,1)], 1, 3), (2, [(0,1)], -1, 3),
           (2, [(0,1)], 1, 0), (True, [], 1, 3)]
    for args in bad:
        try:
            defect_kernel(*args)
        except ValueError:
            pass
        else:
            raise AssertionError(args)
    report = {'schema': 'singularity.fixed-excess/1', 'counts': counts,
              'invalid_inputs_rejected': len(bad), 'failures': 0,
              'seconds': time.perf_counter()-start, 'examples': examples,
              'scope': 'Exact finite checks, not proof-assistant verification',
              'source_sha256': {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
                                for f in ('defect_kernel.py', 'check_defect.py')}}
    (ROOT/'defect_certificate.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k,v in report.items() if k != 'examples'}, indent=2))


if __name__ == '__main__':
    main()
