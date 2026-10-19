"""Exact finite-volume Fourier recovery with explicit no-alias degree bounds."""
from fractions import Fraction
from itertools import combinations
from math import comb
from .conductor import CyclotomicRing
from .graph import Graph
from .periodic import PeriodicModel, direct_coefficients, residue_numerator, series_from_numerator


def _nat(x,minimum=0):
    if isinstance(x,bool) or not isinstance(x,int) or x<minimum:raise ValueError('integer outside range')
    return x


def energy_degree_bound(graph,R):
    if not isinstance(graph,Graph):raise TypeError('Graph required')
    return max(graph.degrees,default=0)*_nat(R)**2


def phase_table(graph,R,M=None,route='direct',max_profiles=1_000_000,max_samples=1000):
    R=_nat(R);bound=energy_degree_bound(graph,R)
    M=bound+1 if M is None else _nat(M,1)
    if M>max_samples:raise ValueError('phase sample resource limit')
    if route not in ('direct','residue'):raise ValueError('unknown exact phase route')
    samples=[]
    for k in range(M):
        model=PeriodicModel(graph,M,{edge:k for edge in graph.edges})
        values=(direct_coefficients(model,R,max_profiles) if route=='direct' else
                series_from_numerator(model,residue_numerator(model,max_profiles),R))
        samples.append((k,tuple(values)))
    return {'schema':'singularity.phase-reconstruction/1','n':graph.n,'edges':graph.edges,
            'volume':R,'bound':bound,'order':M,'route':route,'samples':tuple(samples),
            'verified_graph_bound':True,'profiles_per_direct_phase':comb(R+graph.n,graph.n)}


def recover_energy_histograms(table,bound=None,allow_aliasing=False):
    allowed={'schema','n','edges','volume','bound','order','route','samples','verified_graph_bound','profiles_per_direct_phase'}
    if not isinstance(table,dict) or set(table)!=allowed or table['schema']!='singularity.phase-reconstruction/1':
        raise ValueError('strict phase certificate schema mismatch')
    graph=Graph(_nat(table['n'],1),table['edges']);R=_nat(table['volume']);M=_nat(table['order'],1)
    actual=energy_degree_bound(graph,R)
    if _nat(table['bound'])!=actual or table['verified_graph_bound'] is not True or table['route'] not in ('direct','residue'):
        raise ValueError('forged graph degree bound')
    bound=actual if bound is None else _nat(bound)
    if bound!=actual:raise ValueError('externally underestimated graph bound')
    if M<=bound and not allow_aliasing:raise ValueError('phase order must strictly exceed energy bound')
    ring=CyclotomicRing(M);samples=table['samples']
    if len(samples)!=M or sorted(k for k,_ in samples)!=list(range(M)):
        raise ValueError('missing or duplicate phase labels')
    values={}
    for k,rows in samples:
        _nat(k)
        if len(rows)!=R+1:raise ValueError('phase horizon mismatch')
        if any(len(row)!=ring.degree or any(isinstance(x,bool) or not isinstance(x,int) for x in row) for row in rows):
            raise ValueError('noncanonical exact cyclotomic sample')
        values[k]=rows
    hist=[]
    for r in range(R+1):
        row={}
        for e in range(M if allow_aliasing else bound+1):
            total=ring.zero
            for k in range(M):total=ring.add(total,ring.multiply(values[k][r],ring.phase(-k*e)))
            if any(total[j] for j in range(1,ring.degree)) or total[0]%M:
                raise ValueError('inverse transform is not an exact integer')
            a=total[0]//M
            if a<0:raise ValueError('negative profile multiplicity')
            if a:row[e]=a
        if sum(row.values())!=comb(r+graph.n-1,graph.n-1):raise ValueError('profile mass mismatch')
        hist.append(row)
    return tuple(hist)


def verify_phase_reconstruction(bundle,max_profiles=1_000_000):
    hist=recover_energy_histograms(bundle)
    replay=phase_table(Graph(bundle['n'],bundle['edges']),bundle['volume'],bundle['order'],bundle['route'],max_profiles)
    if replay!=bundle:raise ValueError('phase samples fail original model replay')
    return hist


def phase_subset_identification(candidate_ids,tables,costs,max_phases=20):
    """Exact optimum for identifying a finite declared candidate population."""
    ids=tuple(candidate_ids);tables=tuple(tables)
    if len(ids)!=len(tables) or len(ids)!=len(set(ids)):raise ValueError('original candidate IDs must remain distinct')
    if not tables:raise ValueError('empty population')
    M=tables[0]['order'];R=tables[0]['volume']
    if M>max_phases or any(t['order']!=M or t['volume']!=R for t in tables):raise ValueError('incompatible or oversized panel problem')

    costs=tuple(costs)
    if any(isinstance(c,bool) or not isinstance(c,(int,Fraction)) for c in costs):raise TypeError('exact rational phase costs required')
    costs=tuple(Fraction(c) for c in costs)
    if len(costs)!=M or any(c<=0 for c in costs):raise ValueError('positive phase costs required')
    data=[dict(t['samples']) for t in tables]
    required=[(a,b) for a in range(len(ids)) for b in range(a)]
    best=None;checked=0
    for size in range(M+1):
        for panel in combinations(range(M),size):
            checked+=1
            if all(any(data[a][k]!=data[b][k] for k in panel) for a,b in required):
                item=(sum((costs[k] for k in panel),Fraction()),panel)
                if best is None or item<best:best=item
    return {'feasible':best is not None,'cost':None if best is None else best[0],
            'panel':() if best is None else best[1],'checked_panels':checked,'candidate_ids':ids,
            'claim':'finite-candidate identification only'}


def sparse_histogram_recovery(order,support,samples):
    """Unique recovery conditional on an externally declared exact support set.

    Each cyclotomic sample is expanded over Q. Full column rank is a checked
    uniqueness certificate. This is not support discovery/compressed sensing.
    """
    M=_nat(order,1);support=tuple(_nat(e) for e in support)
    if len(support)>128 or len(set(support))!=len(support):raise ValueError('oversized or duplicate support exponent set')
    ring=CyclotomicRing(M);rows=[]
    seen=set()
    for k,y in samples:
        k=_nat(k)
        if k>=M or k in seen:raise ValueError('invalid phase sample label')
        seen.add(k);y=tuple(y)
        if len(y)!=ring.degree or any(isinstance(x,bool) or not isinstance(x,int) for x in y):raise ValueError('sample field or exact coefficient mismatch')
        cols=[ring.phase(k*e) for e in support]
        for j in range(ring.degree):rows.append([Fraction(c[j]) for c in cols]+[Fraction(y[j])])
    rank=0;pivots=[]
    for col in range(len(support)):
        pivot=next((r for r in range(rank,len(rows)) if rows[r][col]),None)
        if pivot is None:continue
        rows[rank],rows[pivot]=rows[pivot],rows[rank]
        d=rows[rank][col];rows[rank]=[x/d for x in rows[rank]]
        for r in range(len(rows)):
            if r!=rank and rows[r][col]:
                a=rows[r][col];rows[r]=[x-a*y for x,y in zip(rows[r],rows[rank])]
        pivots.append(col);rank+=1
    if any(not any(row[:-1]) and row[-1] for row in rows):raise ValueError('inconsistent declared support')
    if rank!=len(support):raise ValueError('support-conditioned uniqueness fails')
    values=[Fraction() for _ in support]
    for r,c in enumerate(pivots):values[c]=rows[r][-1]
    if any(v.denominator!=1 or v<0 for v in values):raise ValueError('not nonnegative integer multiplicities')
    return {'histogram':{e:int(v) for e,v in zip(support,values) if v},'rank':rank,
            'support':support,'claim':'unique only among histograms on this exact declared support'}


def rational_histogram_interpolation(samples,bound):
    """Exact degree-bounded Vandermonde alternative to complete phase sampling."""
    D=_nat(bound);samples=tuple(samples)
    if D>128 or len(samples)!=D+1:raise ValueError('exactly D+1 samples within resource limit required')
    for q,y in samples:
        if any(isinstance(x,bool) or not isinstance(x,(int,Fraction)) for x in (q,y)):raise TypeError('exact rational samples required')
    samples=tuple((Fraction(q),Fraction(y)) for q,y in samples)
    if len({q for q,y in samples})!=D+1:raise ValueError('rational interpolation nodes must differ')
    rows=[[q**e for e in range(D+1)]+[y] for q,y in samples]
    for c in range(D+1):
        p=next(i for i in range(c,D+1) if rows[i][c]);rows[c],rows[p]=rows[p],rows[c]
        d=rows[c][c];rows[c]=[x/d for x in rows[c]]
        for i in range(D+1):
            if i!=c:
                d=rows[i][c];rows[i]=[x-d*y for x,y in zip(rows[i],rows[c])]
    values=tuple(rows[i][-1] for i in range(D+1))
    if any(x.denominator!=1 or x<0 for x in values):raise ValueError('not nonnegative integer histogram')
    return {i:int(x) for i,x in enumerate(values) if x}
