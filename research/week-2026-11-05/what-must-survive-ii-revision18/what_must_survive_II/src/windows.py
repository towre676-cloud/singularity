# Greedy ascending-energy pivots per volume and class; records whether new energies form an interval (step 2).
import sys,json
from analyze import load,pats,P
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows);out={}
for k in range(4):
    keep={0}|{j+1 for j,q in enumerate(Q) if q[2]>=k};basis={};res=[]
    for V in range(1,Vm+1):
        nw=[]
        for v,e,d in rows:
            if v!=V: continue
            r={c:x.numerator*pow(x.denominator,-1,P)%P for c,x in d.items() if c in keep}
            for pc in sorted(basis):
                f=r.get(pc,0)
                if f:
                    for c2,y in basis[pc].items(): r[c2]=(r.get(c2,0)-f*y)%P
            r={c:y for c,y in r.items() if y}
            if r:
                pc=min(r);iv=pow(r[pc],-1,P);basis[pc]={c:y*iv%P for c,y in r.items()};nw.append(e)
        interval=all(nw[i+1]-nw[i]==2 for i in range(len(nw)-1))
        res.append({"V":V,"new":len(nw),"emin":nw[0] if nw else None,"emax":nw[-1] if nw else None,"interval":interval})
    out[k]=res;print(k,[(r['V'],r['new'],r['emin'],r['emax'],r['interval']) for r in res],flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
