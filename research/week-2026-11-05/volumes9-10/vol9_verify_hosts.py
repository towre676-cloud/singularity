"""Independent motif matching enumeration versus direct height populations."""
from pathlib import Path
from itertools import combinations
from collections import Counter
from fractions import Fraction as Q
import json,time,sys
from vol9_build import lib,canonical9,parse_g6,red
HERE=Path(__file__).resolve().parent

def matchings(edges):
    def rec(i,used,chosen):
        if i==len(edges):yield tuple(chosen);return
        yield from rec(i+1,used,chosen)
        u,v=edges[i]
        if not (used>>u&1 or used>>v&1):
            chosen.append((u,v));yield from rec(i+1,used|1<<u|1<<v,chosen);chosen.pop()
    yield from rec(0,0,[])

def core_counts(n,edges,R=9):
    adj=[set() for _ in range(n)]
    for u,v in edges:adj[u].add(v);adj[v].add(u)
    counts=Counter({(1,0):n})
    for k in range(3,min(R,n)+1):
        for vs in combinations(range(n),k):
            ds=[sum(w in adj[v] for w in vs) for v in vs]
            if min(ds)<2:continue
            es=[(u,v) for u,v in combinations(range(k),2) if vs[v] in adj[vs[u]]]
            eligible=[(u,v) for u,v in es if ds[u]==ds[v]==3]
            for removed in matchings(eligible):
                remaining=set(es)-set(removed)
                mask=lib.mask_from_edges(k,remaining)
                if not lib.connected_mask(mask,k):continue
                m=red.canonical(k,mask) if k>=9 else lib.canonical(mask,k)
                counts[k,m]+=1
    return dict(counts)


def direct_core_counts(n,edges,R=9):
    """A distinct raw edge-subset counter for tiny host cross-checks."""
    out=Counter({(1,0):n})
    for bits in range(1,1<<len(edges)):
        if bits.bit_count()<3:continue
        E=[e for j,e in enumerate(edges) if bits>>j&1]
        deg=Counter(v for e in E for v in e)
        if len(deg)>R or min(deg.values())<2:continue
        vs=sorted(deg);inv={v:i for i,v in enumerate(vs)};k=len(vs)
        mask=lib.mask_from_edges(k,[(inv[u],inv[v]) for u,v in E])
        if lib.connected_mask(mask,k):
            out[k,red.canonical(k,mask) if k>=9 else lib.canonical(mask,k)]+=1
    return dict(out)


def coefficients_from_counts(counts,data):
    R=max(data);ell=[{} for _ in range(R+1)]
    for r in range(1,R+1):
        for h,p in data[r].items():
            ell[r]=lib.padd(ell[r],p,counts.get(h,0))
    Z=[{0:Q(1)}]+[{} for _ in range(R)]
    for r in range(1,R+1):
        for j in range(1,r+1):Z[r]=lib.padd(Z[r],lib.pmul(ell[j],Z[r-j]),Q(j,r))
    return Z


def main():
    t=time.time();src=json.loads((HERE/'vol9_law.json').read_text())
    data={int(r):{(x['k'],x['mask']):{int(e):Q(c) for e,c in x['polynomial'].items()} for x in rs}
          for r,rs in src['coefficient_rows'].items()}
    hosts=json.loads((HERE/'direct9.json').read_text());checked=[];oraclechecks=0
    for i,h in enumerate(hosts):
        n,edges=parse_g6(h['g6']);counts=core_counts(n,edges)
        if n<=8:
            assert counts==direct_core_counts(n,edges);oraclechecks+=1
        Z=coefficients_from_counts(counts,data)
        for r in range(10):
            expected={int(e):Q(c) for e,c in h['coefficients'][str(r)].items()}
            assert Z[r]==expected,(i,n,r,lib.padd(Z[r],expected,-1))
        checked.append({'index':i,'n':n,'core_types_present':len(counts)-1})
        if (i+1)%20==0:print('host checks',i+1,'seconds',round(time.time()-t,2),flush=True)
    out={'direct_height_hosts':len(hosts),'coefficients_per_host':10,'through_volume':9,
         'raw_edge_subset_counter_checks':oraclechecks,'failures':0,'seconds':time.time()-t,'hosts':checked}
    (HERE/'vol9_host_checks.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASSED',len(hosts),'hosts',oraclechecks,'edge-subset crosschecks',flush=True)
if __name__=='__main__':main()
