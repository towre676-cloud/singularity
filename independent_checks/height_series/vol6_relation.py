#!/usr/bin/env python3
"""Search for exact I5 relations among disjoint unions of library
components: multisets u != v with equal total n and equal I5, differing
in K3,3 / prism / K3,3-e profile.  Any hit gives an immediate decisive
component test pair."""
import sys
from itertools import product
sys.path.insert(0, ".")
from vol6_lib import *

INV5 = ['N3_triangle', 'N4_square', 'Ndia', 'NK4',
        'N5_pentagon', 'NK23', 'N_theta123', 'NK23_plus_e']
pm_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["Nprism"]][0]
km_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["NK33"]][0]
LIB = {"K4": (4, [(i, j) for i in range(4) for j in range(i + 1, 4)]),
       "K33": (6, edges_of(types[6][km_t], 6)),
       "prism": (6, edges_of(types[6][pm_t], 6)),
       "cube": (8, [(i, j) for i in range(8) for j in range(i + 1, 8) if bin(i ^ j).count("1") == 1]),
       "M8": (8, [(i, (i + 1) % 8) for i in range(8)] + [(i, i + 4) for i in range(4)]),
       "petersen": (10, [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)]
                    + [(5 + i, 5 + (i + 2) % 5) for i in range(5)])}
names = list(LIB)
data = {}
for nm, (n, ed) in LIB.items():
    s = induced_counts(n, ed, 6)
    N = subgraph_counts_all(s)
    data[nm] = (n, tuple(N.get(NAMED[x], 0) for x in INV5),
                N.get(pat_index[(6, km_t)], 0), N.get(pat_index[(6, pm_t)], 0),
                N.get(pat_index[(6, [t for t in ctypes[6] if types[6][t] == 2012][0])], 0))
    print(nm, "n=", n, "I5=", data[nm][1], "NK33=", data[nm][2], "Nprism=", data[nm][3], "Nm2012=", data[nm][4])

sols = {}
R = range(0, 5)
for coeffs in product(R, repeat=len(names)):
    if sum(coeffs) == 0: continue
    n = sum(c * data[nm][0] for c, nm in zip(coeffs, names))
    if n > 30: continue
    i5 = tuple(sum(c * data[nm][1][k] for c, nm in zip(coeffs, names)) for k in range(8))
    prof = (sum(c * data[nm][2] for c, nm in zip(coeffs, names)),
            sum(c * data[nm][3] for c, nm in zip(coeffs, names)),
            sum(c * data[nm][4] for c, nm in zip(coeffs, names)))
    key = (n, i5)
    for prev_coeffs, prev_prof in sols.get(key, []):
        if prev_prof != prof:
            print("RELATION:", dict(zip(names, prev_coeffs)), "==I5==", dict(zip(names, coeffs)),
                  "| profiles (NK33, Nprism, Nm2012):", prev_prof, "vs", prof)
    sols.setdefault(key, []).append((coeffs, prof))
print("done")
