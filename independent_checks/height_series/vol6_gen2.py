#!/usr/bin/env python3
"""Fresh random cubic pools at n=18 and n=20, I5 data only (for the
component-balance matching in vol6_search2.py)."""
import json, random, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol6_lib import *
# random_cubic comes from singularity_extension.py, which lives in this
# same directory in the repository (added by PR #4).
from singularity_extension import random_cubic
HERE = Path(__file__).resolve().parent

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
                    "I5": [N.get(NAMED[x], 0) for x in
                           ['N3_triangle', 'N4_square', 'Ndia', 'NK4',
                            'N5_pentagon', 'NK23', 'N_theta123', 'NK23_plus_e']]})
    print(f"{prefix}: {len(out)} graphs in {time.time()-t0:.1f} s", flush=True)
    return out

pools = {}
pools["n18"] = gen_pool(18, 3000, 20261029, "n18_g")
pools["n20"] = gen_pool(20, 2000, 20261030, "n20_g")
(HERE / "vol6_pools2.json").write_text(json.dumps(pools))
print("wrote vol6_pools2.json")
