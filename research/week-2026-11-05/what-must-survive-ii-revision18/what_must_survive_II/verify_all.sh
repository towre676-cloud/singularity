#!/usr/bin/env bash
# Clean-room replay through volume 12. Requires g++, python3 with sympy, networkx, python-flint. About 5 minutes on 2 cores.
set -euo pipefail
cd "$(dirname "$0")/src"; W=$(mktemp -d); R=../receipts_replay; mkdir -p $R
g++ -O2 -o $W/gen gen.cpp; g++ -O2 -o $W/engine engine.cpp 2>/dev/null; g++ -O2 -o $W/direct direct.cpp 2>/dev/null; g++ -O2 -o hist hist.cpp 2>/dev/null
$W/gen 12 > $W/p12.txt 2> $R/pattern_counts.txt
python3 brute_count.py > $R/brute_count.txt 2>/dev/null
python3 - > $W/val.txt <<'PY'
import networkx as nx
for g in [nx.complete_graph(4),nx.complete_bipartite_graph(3,3),nx.circular_ladder_graph(3),nx.cubical_graph(),nx.disjoint_union(nx.complete_graph(4),nx.complete_graph(4))]:
    g=nx.convert_node_labels_to_integers(g);print(g.number_of_nodes(),g.number_of_edges()," ".join(f"{a} {b}" for a,b in g.edges()))
PY
$W/engine 8 $W/p12.txt validate $W/val.txt > $R/validate.txt 2>/dev/null; ! grep -q "match=0" $R/validate.txt
$W/engine 12 $W/p12.txt rows $W/r1.txt > $R/rows_p1.log 2>/dev/null
$W/engine 12 $W/p12.txt rows $W/r2.txt 2305843009213693921 > $R/rows_p2.log 2>/dev/null
python3 exact_ranks.py $W/r1.txt $W/r2.txt $R/exact_ranks_V12.json
python3 windows.py $W/r1.txt $R/windows_V12.json >/dev/null
python3 girth.py $W/r1.txt $R/girth.json >/dev/null
python3 verify_analytic.py $R/analytic.json; python3 verify_jet.py $W/r1.txt $R/jet.json
python3 jet2.py $W/r1.txt $R/jet2.json; python3 jetdecomp.py $W/r1.txt $R/jetdecomp.json >/dev/null
python3 annular_toy.py $R/annular_toy.json; python3 shear_core_replay.py $R/shear_replay.json
$W/direct ../data/unseparated_pair_n14.txt 14 > $R/direct_pair_n14.txt
$W/engine 12 $W/p12.txt dumpclusters $W/cl.txt 2>/dev/null
python3 certify.py $W/r1.txt $W/r2.txt $W/cl.txt $R/cert_V12.json
python3 recover.py $W/r1.txt $R/recovery_V12.json >/dev/null
awk '2*$2==3*$1' $W/p12.txt > $W/hosts12.txt
$W/engine 12 $W/p12.txt counts $W/hosts12.txt $W/counts12.txt 2>/dev/null
python3 smallhost.py $W/r1.txt $R/windows_V12.json $W/counts12.txt $R/small_hosts.json
python3 - > $W/hid.txt <<'PY'
import networkx as nx
for g in [nx.complete_graph(4),nx.complete_bipartite_graph(3,3),nx.petersen_graph(),nx.cubical_graph(),nx.heawood_graph()]:
    g=nx.convert_node_labels_to_integers(g);print(g.number_of_nodes(),g.number_of_edges()," ".join(f"{a} {b}" for a,b in g.edges()))
PY
cat ../data/unseparated_pair_n14.txt >> $W/hid.txt
$W/engine 12 $W/p12.txt counts $W/hid.txt $W/cid.txt 2>/dev/null
python3 host_identity.py $W/r1.txt $W/cid.txt $R/host_identity.json >/dev/null
python3 j3.py $W/r1.txt $R/j3_check.json $R/j3_coefficients.json 9 > $R/j3.log; python3 shear_quadratic.py $R/shear_quadratic.json
sed -i "s#XX#XX#" omega.py j3factor.py
python3 j3factor.py > $R/j3factor.log; python3 omega.py $R/omega.json > $R/omega.log
python3 - > $W/h.txt <<'PY'
import sys
PY
cut -d'|' -f1 $W/cid.txt > $W/h.txt
python3 vlaw.py $W/r1.txt $W/h.txt $R/reflection_law.json
python3 jetdecomp2.py $W/r1.txt $R/jetdecomp_classes.json > /dev/null
python3 rrtable.py $W/r1.txt $R/rr_table.json > /dev/null
python3 - "$R" <<'PY'
import json,sys
R=sys.argv[1];e=json.load(open(R+'/exact_ranks_V12.json'))['ranks']
rec={'0':(24,34,48),'1':(21,31,43),'2':(19,28,40),'3':(15,23,33)}
for k,v in rec.items(): assert (e[k][7],e[k][8],e[k][9])==v
print("recorded table reproduced; ranks through 12:",{k:e[k][-1] for k in e})
PY
echo ALL PASSED
