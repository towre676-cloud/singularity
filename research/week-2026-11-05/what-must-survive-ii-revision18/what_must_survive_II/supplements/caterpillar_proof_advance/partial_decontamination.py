"""Exact verification of the pendant-free symmetrized difference histogram."""
from collections import Counter
from pathlib import Path
import json
from caterpillar import data,positions
from verify import sequences
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    count=0;compact=0
    for n in range(4,15):
      for p in sequences(n):
        A,B,C,D=data(p);_,ell,a=positions(p)
        S=Counter()
        for u in a:S[u]+=1;S[n-u]+=1
        clean=Counter(B);clean[n-2]-=ell*(ell-1)//2
        sym=Counter(clean)
        for e,c in clean.items():sym[n-2-e]+=c
        for e,c in S.items():sym[e-1]-=ell*c
        target=Counter(D)
        for e,c in D.items():target[n-2-e]+=c
        assert all(sym[e]==target[e] for e in sym.keys()|target.keys())
        if 2*(a[-1]-a[0])<=n-2:
            recovered=Counter()
            for e in range(1,(n-2)//2+1):
                v=sym[e]
                if 2*e==n-2:assert v%2==0;v//=2
                if v:recovered[e]=v
            assert recovered==D;compact+=1
        count+=1
    (ROOT/'partial_decontamination_checks.json').write_text(json.dumps({'all_caterpillars_orders':'4 through 14','checked':count,'short_span_recoveries':compact,'exact':True},indent=2)+'\n');print('Pendant symmetrization checked on',count,'caterpillars;',compact,'short-span histograms recovered.')
