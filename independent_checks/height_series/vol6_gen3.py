#!/usr/bin/env python3
"""Fresh random cubic pools at n=24 (4000) and n=26 (1500), I5 only,
for the K3,3 component-balance hunt (vol6_search5.py)."""
import json, random, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol6_lib import *
# random_cubic comes from singularity_extension.py, which lives in this
# same directory in the repository (added by PR #4).
from singularity_extension import random_cubic
HERE = Path(__file__).resolve().parent
INV5NAMES = ['N3_triangle', 'N4_square', 'Ndia', 'NK4',
             'N5_pentagon', 'NK23', 'N_theta123', 'NK23_plus_e']

def gen_pool(n, count, seed, prefix):
    rng = random.Random(seed)
    seen = set(); out = []; tries = 0
    t0 = time.time()
    while len(out) < count and tries < count * 6:
        tries += 1
        ed = random_cubic(rng, n)
        if ed is None: continue
        key = tuple(sorted(tuple(sorted(e)) for e in ed))
        if key in seen: continue
        seen.add(key)
        s = induced_counts(n, ed, 5)
        N = subgraph_counts_all(s)
        out.append({"name": f"{prefix}{len(out)}", "edges": [list(e) for e in key],
                    "I5": [N.get(NAMED[x], 0) for x in INV5NAMES]})
    print(f"{prefix}: {len(out)} graphs in {time.time()-t0:.1f} s", flush=True)
    return out

pools = {}
pools["n24"] = gen_pool(24, 4000, 20261031, "n24_g")
pools["n26"] = gen_pool(26, 1500, 20261101, "n26_g")
(HERE / "vol6_pools3.json").write_text(json.dumps(pools))
print("wrote vol6_pools3.json")
