"""Bounded actual-graph searches and necessary charge compatibility filters.

Formal interface null vectors are never serialized as graph realizations.
A search exclusion is complete only for its enumerated finite constructor.
"""
from collections import defaultdict
from fractions import Fraction
from itertools import combinations, permutations, product
from math import comb
from .graph import Graph
from .contexts import interface_status, symmetrize
from .terminals import terminal_kernel, kernel_by_enumeration


def frontier_vectors(q=Fraction(1,2)):
    if isinstance(q,bool) or not isinstance(q,(int,Fraction)):raise TypeError('exact rational pinning required')
    q=Fraction(q)
    if not 0<q<1:raise ValueError('rational pinning must lie in (0,1)')
    y=(q**289,q**121,q**25);v=(y[2]-y[1],y[0]-y[2],y[1]-y[0])
    return {'terminal_edge':{'budget':38,'states':((1,18),(6,17),(10,15)), 'interior_volumes':(19,15,13),'vector':v,
                            'annihilator':(sum(v),sum(a*b for a,b in zip(y,v)))},
            'edge_free':{'budget':11,'states':((0,5),(3,4)),'interior_volumes':(6,4),'vector':(Fraction(1),Fraction(-1)),
                         'annihilator':(Fraction(0),)},'scope':'formal candidates only; no realizing pair asserted'}


def charge_relaxation_contains(interface,interior_count):
    """Necessary nonnegative-population and charge-semigroup constraints.

    These linear/combinatorial restrictions are not sufficient adjacency or
    slice realizability certificates. Counts retain original labeled tuples.
    """
    try:
        if isinstance(interior_count,bool) or not isinstance(interior_count,int) or interior_count<0:return False
        R=interface['max_volume'];k=len(interface['terminals']);patterns=tuple(tuple(p) for p in interface['patterns'])
        if isinstance(R,bool) or not isinstance(R,int) or R<0:return False
        if any(len(p)!=k or any(type(v) is not int or v not in (0,1) for v in p) for p in patterns):return False
        reachable={(0,)*k};totals=[0]*(R+1)
        for j in range(R+1):
            if j:reachable={tuple(a+b for a,b in zip(Q,p)) for Q in reachable for p in patterns}
            for (v,Q),poly in interface['charges'].items():
                if type(v) is not int or not 0<=v<=R or len(Q)!=k:return False
                if v!=j:continue
                if tuple(Q) not in reachable:return False
                for energy,count in poly.items():
                    if type(energy) is not int or energy<0 or type(count) is not int or count<=0:return False
                    totals[j]+=count
            expected=(1 if j==0 else 0) if interior_count==0 else comb(j+interior_count-1,interior_count-1)
            if totals[j]!=expected:return False
        return True
    except (KeyError,TypeError,ValueError):return False


def block_isomorphism_key(graph):
    """Canonical edge tuple, terminals 0,1 allowed to swap; interiors permute."""
    if graph.n<2:raise ValueError('two terminals required')
    keys=[]
    for middle in permutations(range(2,graph.n)):
        for ts in ((0,1),(1,0)):
            order=ts+middle;image={v:i for i,v in enumerate(order)}
            keys.append(tuple(sorted(tuple(sorted((image[u],image[v]))) for u,v in graph.edges)))
    return (graph.n,min(keys))


def prufer_tree(n,word):
    if n<2 or len(word)!=n-2 or any(type(v) is not int or not 0<=v<n for v in word):raise ValueError('Pruefer word contract violated')
    degrees=[1]*n
    for v in word:degrees[v]+=1
    edges=[]
    for v in word:
        leaf=next(i for i,d in enumerate(degrees) if d==1);edges.append((leaf,v));degrees[leaf]-=1;degrees[v]-=1
    rest=[i for i,d in enumerate(degrees) if d==1];edges.append(tuple(rest))
    return Graph(n,edges)


def tree_family(max_vertices=5):
    if type(max_vertices) is not int or not 2<=max_vertices<=6:raise ValueError('declared finite tree bound 2..6 required')
    return tuple(prufer_tree(n,w) for n in range(2,max_vertices+1) for w in product(range(n),repeat=n-2))


def dominating_family(max_interiors=4):
    if type(max_interiors) is not int or not 0<=max_interiors<=5:raise ValueError('declared finite interior bound 0..5 required')
    out=[]
    for m in range(max_interiors+1):
        possible=tuple(combinations(range(2,m+2),2));base=[(t,v) for t in (0,1) for v in range(2,m+2)]
        for mask in range(1<<len(possible)):
            out.append(Graph(m+2,base+[e for i,e in enumerate(possible) if mask>>i&1]))
    return tuple(out)


def _signature(kernel,q):
    return tuple((o,j,sum(Fraction(c)*q**e for (v,e),c in cells.items() if v==j))
                 for o,cells in sorted(symmetrize(kernel).items()) for j in sorted({v for v,e in cells}))


def complete_bounded_exclusion(graphs,*,prefix_volume=4,frontier_volume=11,q=Fraction(1,2),max_profiles=2000000):
    """Exhaust constructor; independently compare bag and composition engines.

    If no nonisomorphic class survives the exact prefix, no nonzero frontier
    direction is realized within this family. No full-series equivalence is
    inferred for surviving pairs.
    """
    q=Fraction(q);graphs=tuple(graphs)
    if not 0<q<1 or type(prefix_volume) is not int or not 0<=prefix_volume<frontier_volume:raise ValueError('invalid pinning or prefix/frontier volumes')
    classes={}
    for g in graphs:classes.setdefault(block_isomorphism_key(g),g)
    work=sum(comb(prefix_volume+g.n,g.n) for g in classes.values())
    if work>max_profiles:raise ArithmeticError('composition profile preflight budget exhausted')
    buckets=defaultdict(list);degree_buckets=defaultdict(int);oracle_checks=0
    for key,g in sorted(classes.items()):
        # Necessary zero-interior slice signature, not an unproved degree
        # sequence filter at arbitrary rational pinning.
        ds=q**g.degrees[0]+q**g.degrees[1];degree_buckets[(g.n,ds)]+=1
        a=terminal_kernel(g,(0,1),prefix_volume);b=kernel_by_enumeration(g,(0,1),prefix_volume)
        if a!=b:raise ArithmeticError('independent terminal-kernel disagreement')
        oracle_checks+=1;buckets[(g.n,ds,_signature(a,q))].append(key)
    survivors=[group for group in buckets.values() if len(group)>1]
    return {'schema':'singularity.realizability-search/1','state':'complete_bounded_exclusion' if not survivors else 'incomplete_budget',
            'constructor_count':len(graphs),'isomorphism_classes':len(classes),'prefix_volume':prefix_volume,'frontier_volume':frontier_volume,
            'parameter':[q.numerator,q.denominator],'language':'simple swap-symmetric edge-free contexts; symmetric interface sums without averaging',
            'equality':'fixed rational specialization within each known graph-order stratum; original labeled heights','composition_profiles':work,'independent_kernel_checks':oracle_checks,
            'surviving_nonisomorphic_groups':len(survivors),'groups':survivors,
            'scope':'nonzero frontier differences excluded only when every distinct graph class already differs in this required lower kernel prefix'}


def threshold_dominating_exclusion(volume,q=Fraction(1,2)):
    """FR05 corollary: all dominating threshold interiors below explicit order.

    For rational q=A/B, every known order m < B^(2(volume-1)) is
    reconstructible from any supported raw single closure at this budget.
    The block order is m+2. The interiors must be promised threshold graphs.
    """
    if type(volume) is not int or volume<2:raise ValueError('volume at least two required')
    if isinstance(q,bool) or not isinstance(q,(int,Fraction)):raise TypeError('exact rational required')
    q=Fraction(q)
    if not 0<q<1:raise ValueError('q in (0,1) required')
    return {'volume':volume,'parameter':[q.numerator,q.denominator],'maximum_interior_order':q.denominator**(2*(volume-1))-1,
            'theorem':'FR05 threshold inverse plus unit-triangular raw closure transport',
            'excluded':'distinct dominating blocks with promised threshold interiors of equal known order and equal closure prefix',
            'scope':'structural family exclusion; no unrestricted graph completeness or general symmetric-kernel realizability claim'}
