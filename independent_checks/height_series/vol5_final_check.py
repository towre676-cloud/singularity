#!/usr/bin/env python3
"""Final check: the volume-5 formula on every agreeing-through-volume-4 pair
of the original pools (using the pair differences stored in vol5_results.json),
in full form (with the kappa^5 f^2 dNK23e term) and reduced form."""
import json
from fractions import Fraction as Fr
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
res = json.loads((HERE / "vol5_results.json").read_text())

def kappa5(j):
    outp = {}
    for s in range(5 + j + 1):
        outp[5 - 2 * j + 2 * s] = Fr(comb(5 + j, s)) * (-1) ** s
    return outp

def pdiff(A, B):
    outp = dict(A)
    for e, c in B.items(): outp[e] = outp.get(e, Fr(0)) - c
    return {e: c for e, c in outp.items() if c}

tot = {}
for use_f2 in (True, False):
    fails = {}
    npairs = 0
    for bn, pd in res["pairdata"].items():
        f = 0
        npairs += len(pd)
        for p in pd:
            acc = {}
            terms = [(p["dN"]["N5_pentagon"], 0), (p["dN"]["NK23"], 1),
                     (p["dN"]["N_theta123"], 1)]
            if use_f2: terms.append((p["dN"]["NK23_plus_e"], 2))
            for dN, j in terms:
                if dN:
                    for e, c in kappa5(j).items(): acc[e] = acc.get(e, Fr(0)) + dN * c
            dL = {int(e): Fr(c) for e, c in p["dL5"].items()}
            if pdiff(dL, acc): f += 1
        fails[bn] = f
    tot["with_f2" if use_f2 else "without_f2"] = {"pairs": npairs, "failures": fails}
    print(("WITH" if use_f2 else "WITHOUT"), "kappa^5 f^2 dNK23e term:",
          "pairs", npairs, "failures", fails)
(HERE / "vol5_final_check.json").write_text(json.dumps(tot, indent=1))
