#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")
from vol6_lib import *

def nm(mask): return describe(mask, 6)
def edges(mask): return sorted((min(u,v),max(u,v)) for u,v in edges_of(mask,6))

out = []
def p(*a): out.append(" ".join(str(x) for x in a))

pm = [t for t in ctypes[6] if pat_index[(6,t)]==NAMED["Nprism"]][0]
km = [t for t in ctypes[6] if pat_index[(6,t)]==NAMED["NK33"]][0]
pm = types[6][pm]; km = types[6][km]
p("prism mask:", pm, "K33 mask:", km)
def minus_edge_types(mask):
    res = {}
    for (u,v) in edges_of(mask,6):
        m2 = mask ^ (1<<PIDX[6][(min(u,v),max(u,v))])
        res.setdefault(type_of(m2,6), []).append((u,v))
    return res
p("prism minus edge types:", {nm(types[6][t]): len(es) for t, es in minus_edge_types(pm).items()})
for t, es in minus_edge_types(pm).items():
    p("  prism-e:", nm(types[6][t]), "edges:", es[:3])
p("K33 minus edge types:", {nm(types[6][t]): len(es) for t, es in minus_edge_types(km).items()})
for m in (122, 659):
    p("tree", nm(m), edges(m))
for m in (633, 694):
    p("tri+tails", nm(m), edges(m))
for m in (246, 693):
    p("C4+2pend", nm(m), edges(m))
for m in (1749, 762):
    p("house+pend", nm(m), edges(m))
for m in (1916, 5948, 5941):
    p("e8", nm(m), edges(m))
open("vol6_identify.log","w").write("\n".join(out)+"\n")
print("done")
