exec(open('fl.py').read().split("tot={}")[0])
exec(open('m.py').read().split("# C's short")[1].split("tot=0;fail")[0].replace("spine claim: exact, among caterpillars",""))
import json
r={};allok=True;span=0;tot=0;mins=None
for n in range(8,31):
    N=n-2
    for l in open(f'd{n}.txt'):
        if not l.startswith('S2'):continue
        ps=[tuple(map(int,x.strip(',').split(','))) for x in l.split()[1:]];tot+=1
        ab=[AB(p)[:2] for p in ps];allok&=all(a==ab[0] for a in ab)
        sp_=[(max(T_of(p)[0])-min(T_of(p)[0]))*2<=N for p in ps]
        if all(sp_):span+=1
        m=min(len(p) for p in ps);mins=m if mins is None else min(mins,m)
r=dict(classes=tot,exact_equal_AB=bool(allok),classes_all_in_span_subclass=span,min_spine=mins);print(r);json.dump(r,open('ex.json','w'))
