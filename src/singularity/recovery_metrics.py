"""Exact inverse conditioning with explicit physical box-noise contracts.

All amplification uses raw measurement noise. Scaling a reading scales its
noise; no error model is inferred from coefficient magnitude.
"""
from fractions import Fraction
from itertools import combinations, product
from math import comb


def _q(x):
    if isinstance(x,bool) or not isinstance(x,(int,Fraction)):raise TypeError('exact rational required')
    return Fraction(x)


def _mat(A):
    rows=tuple(tuple(_q(x) for x in r) for r in A)
    if rows and any(len(r)!=len(rows[0]) for r in rows):raise ValueError('ragged matrix')
    return rows


def _mul(A,B):
    if A and len(A[0])!=len(B):raise ValueError('matrix dimensions differ')
    return tuple(tuple(sum((a*b for a,b in zip(r,c)),Fraction(0)) for c in zip(*B)) for r in A)


def _inverse(A):
    A=_mat(A);n=len(A)
    if any(len(r)!=n for r in A):raise ValueError('square matrix required')
    rows=[list(r)+[Fraction(i==j) for j in range(n)] for i,r in enumerate(A)]
    for j in range(n):
        p=next((i for i in range(j,n) if rows[i][j]),None)
        if p is None:raise ValueError('rank deficient matrix')
        rows[p],rows[j]=rows[j],rows[p];z=rows[j][j];rows[j]=[x/z for x in rows[j]]
        for i in range(n):
            if i!=j:
                z=rows[i][j];rows[i]=[x-z*y for x,y in zip(rows[i],rows[j])]
    return tuple(tuple(r[n:]) for r in rows)


def _rank(A):
    rows=[list(r) for r in _mat(A)];j=0
    for c in range(len(rows[0]) if rows else 0):
        p=next((i for i in range(j,len(rows)) if rows[i][c]),None)
        if p is None:continue
        rows[p],rows[j]=rows[j],rows[p];z=rows[j][c];rows[j]=[x/z for x in rows[j]]
        for i in range(j+1,len(rows)):
            z=rows[i][c];rows[i]=[x-z*y for x,y in zip(rows[i],rows[j])]
        j+=1
    return j


def reconstruction_map(A):
    """Deterministic exact left inverse; not claimed noise-optimal."""
    A=_mat(A);m=len(A);n=len(A[0]) if m else 0
    kept=[]
    for i,r in enumerate(A):
        if _rank([A[j] for j in kept]+[r])>len(kept):kept.append(i)
        if len(kept)==n:break
    if len(kept)!=n:raise ValueError('measurement matrix lacks full column rank')
    inv=_inverse([A[i] for i in kept]);R=tuple(tuple(inv[j][kept.index(i)] if i in kept else Fraction(0) for i in range(m)) for j in range(n))
    return R


def box_amplification(R,epsilon):
    R=_mat(R);eps=tuple(_q(x) for x in epsilon)
    if R and len(R[0])!=len(eps) or any(e<0 for e in eps):raise ValueError('noise dimensions/bounds invalid')
    return tuple(sum(abs(a)*e for a,e in zip(r,eps)) for r in R)


def target_amplification(R,target,epsilon):
    R=_mat(R);g=tuple(_q(x) for x in target)
    if len(g)!=len(R):raise ValueError('target dimension mismatch')
    w=tuple(sum(g[j]*R[j][i] for j in range(len(g))) for i in range(len(R[0]) if R else 0))
    return box_amplification([w],epsilon)[0]


def rational_size(values):
    vals=[]
    def visit(x):
        if isinstance(x,(tuple,list)):
            for z in x:visit(z)
        else:vals.append(_q(x))
    visit(values)
    nums=[max(1,abs(v.numerator).bit_length()) for v in vals];dens=[v.denominator.bit_length() for v in vals]
    return {'cells':len(vals),'nonzero_cells':sum(bool(v) for v in vals),'numerator_bits':sum(nums),'denominator_bits':sum(dens),
            'sign_bits':len(vals),'total_bits':sum(nums)+sum(dens)+len(vals),'maximum_numerator_bits':max(nums,default=0),
            'maximum_denominator_bits':max(dens,default=0),'encoding':'one sign bit plus max(1,abs(numerator).bit_length()) plus denominator.bit_length() per cell'}


def compare_recovery_designs(designs):
    out=[]
    for d in designs:
        A=_mat(d['A']);m=len(A);P=_mat(d.get('preprocessing',tuple(tuple(Fraction(i==j) for j in range(m)) for i in range(m))))
        if P and len(P[0])!=m:raise ValueError('preprocessing dimension mismatch')
        R=_mat(d.get('left_inverse',reconstruction_map(_mul(P,A))))
        C=_mul(R,P);n=len(A[0]) if A else 0
        if _mul(C,A)!=tuple(tuple(Fraction(i==j) for j in range(n)) for i in range(n)):raise ValueError('R P A is not identity')
        eps=tuple(_q(e) for e in d['noise'])
        amps=box_amplification(C,eps)
        out.append({'name':d['name'],'A':A,'P':P,'R':R,'raw_reconstruction':C,'amplification':amps,
                    'target_amplification':target_amplification(C,d.get('target',[1]+[0]*(n-1)),eps) if n else Fraction(0),
                    'measurement_count':m,'cost':sum((_q(c) for c in d.get('costs',[1]*m)),Fraction(0)),
                    'volume_budget':d.get('volume_budget'),'matrix_size':rational_size(A),'inverse_size':rational_size(C)})
    return out


def optimize_target(A,target,epsilon,*,max_active_sets=100000):
    """Exact tiny LP: min sum eps_i |w_i| subject A^T w=g.

    Enumerates basic feasible supports (including degenerate zero weights),
    then certifies the optimum by a rational dual z satisfying |A z|<=eps.
    """
    A=_mat(A);g=tuple(_q(x) for x in target);eps=tuple(_q(x) for x in epsilon);m=len(A);n=len(g)
    if any(len(r)!=n for r in A) or len(eps)!=m or any(e<0 for e in eps):raise ValueError('LP dimensions/noise invalid')
    if isinstance(max_active_sets,bool) or not isinstance(max_active_sets,int) or max_active_sets<1:raise ValueError('positive active-set budget required')
    if comb(m,n)>max_active_sets:raise ArithmeticError('target LP active-set budget exhausted')
    if n==0:return {'weights':tuple(Fraction(0) for _ in A),'dual':(),'objective':Fraction(0)}
    best=None
    for I in combinations(range(m),n):
        try:inv=_inverse(tuple(zip(*(A[i] for i in I))))
        except ValueError:continue
        wi=tuple(sum(a*b for a,b in zip(row,g)) for row in inv)
        w=tuple(wi[I.index(i)] if i in I else Fraction(0) for i in range(m));value=sum(e*abs(t) for e,t in zip(eps,w))
        if best is None or value<best[0]:best=(value,w)
    if best is None:raise ValueError('target constraints infeasible or measurement map rank deficient')
    # Enumerate vertices of dual box-slab polytope. Equal objective certifies.
    tested=0
    for I in combinations(range(m),n):
        try:inv=_inverse([A[i] for i in I])
        except ValueError:continue
        for signs in product((-1,1),repeat=n):
            tested+=1
            if tested>max_active_sets:raise ArithmeticError('target dual active-set budget exhausted')
            rhs=tuple(s*eps[i] for s,i in zip(signs,I));z=tuple(sum(a*b for a,b in zip(row,rhs)) for row in inv)
            if all(abs(sum(a*b for a,b in zip(row,z)))<=e for row,e in zip(A,eps)) and sum(a*b for a,b in zip(g,z))==best[0]:
                cert={'weights':best[1],'dual':z,'objective':best[0]}
                if not verify_target_certificate(A,g,eps,cert):raise ArithmeticError('LP certificate failure')
                return cert
    raise ArithmeticError('no primal/dual equality certificate within declared enumeration')


def verify_target_certificate(A,target,epsilon,cert):
    try:
        A=_mat(A);g=tuple(_q(x) for x in target);eps=tuple(_q(x) for x in epsilon)
        w=tuple(_q(x) for x in cert['weights']);z=tuple(_q(x) for x in cert['dual']);value=_q(cert['objective'])
        return (len(w)==len(A)==len(eps) and len(z)==len(g) and all(len(r)==len(g) for r in A)
            and all(e>=0 for e in eps) and all(sum(w[i]*A[i][j] for i in range(len(A)))==g[j] for j in range(len(g)))
            and all(abs(sum(a*b for a,b in zip(r,z)))<=e for r,e in zip(A,eps))
            and sum(e*abs(v) for e,v in zip(eps,w))==value==sum(a*b for a,b in zip(g,z)))
    except (TypeError,ValueError,KeyError,IndexError):return False


def select_target_design(menu,target,max_error):
    """Least total declared sensor cost among this finite menu only."""
    tol=_q(max_error)
    if tol<0:raise ValueError('nonnegative tolerance required')
    results=[]
    for d in menu:
        c=optimize_target(d['A'],target,d['noise']);cost=sum((_q(x) for x in d.get('costs',[1]*len(d['A']))),Fraction(0))
        results.append({'name':d['name'],'cost':cost,'certificate':c,'feasible':c['objective']<=tol})
    feasible=[r for r in results if r['feasible']]
    return {'menu':results,'selected':min(feasible,key=lambda r:(r['cost'],r['name'])) if feasible else None,
            'scope':'finite supplied design menu with physical noise bounds'}


def vandermonde(nodes):
    z=tuple(_q(x) for x in nodes)
    if len(set(z))!=len(z):raise ValueError('distinct nodes required')
    return tuple(tuple(x**i for x in z) for i in range(len(z)))


def vandermonde_uniform_bound(nodes_count,absolute_node_bound,gap_lower_bound,noise=1):
    """Certified Lagrange inverse row-sum bound on any declared compact domain.

    If |z_i|<=M and |z_i-z_j|>=gamma>0, each recovered coordinate error is
    <= noise*(1+M)^(m-1)/gamma^(m-1). The hypotheses are explicit obligations,
    not inferred from samples. At m=2 the sum of interpolation coefficients
    gives this bound directly; the general proof expands product(X-z_j).
    """
    if isinstance(nodes_count,bool) or not isinstance(nodes_count,int) or nodes_count<1:raise ValueError('positive node count required')
    M,g,e=map(_q,(absolute_node_bound,gap_lower_bound,noise))
    if M<0 or g<=0 or e<0:raise ValueError('invalid certified bounds')
    return e*((1+M)/g)**(nodes_count-1)


def interface_reconstruction_data(method,volume,q,*,max_measurements=1000):
    """Linear wrapper for a complete symmetric-interface probe family.

    The forward matrix includes every generic interface coordinate, before
    any dominating-interior promise. The exact left inverse defines an
    explicit extension to inconsistent noisy measurements; the older exact
    recovery APIs rightly reject such inconsistent data. This wrapper does
    not silently assign them an undeclared numerical noise policy.
    """
    from .contexts import (orbits,finite_difference_probe_set,finite_difference_budget,
                           symmetric_probe_set,_context_series,max_group_size)
    if type(volume) is not int or volume<0:raise ValueError('nonnegative volume required')
    q=_q(q)
    if not 0<q<1:raise ValueError('q in (0,1) required')
    if method=='finite_difference':
        probes=finite_difference_probe_set(volume);B=finite_difference_budget(volume)
        if B!=volume:raise ArithmeticError('generic full-left-inverse wrapper currently supports zero-delay budgets only; delayed moments need nuisance-coordinate elimination')
        specs=[(d,0,c) for d,c in probes]
    elif method=='weighted':
        probes=symmetric_probe_set(volume,max(1,max_group_size(volume)-1));B=volume;specs=[(d,w,0) for d,w in probes]
    else:raise ValueError('unknown recovery method')
    if type(max_measurements) is not int or max_measurements<1:raise ValueError('positive measurement limit required')
    if len(probes)*(B+1)>max_measurements:raise ArithmeticError('measurement materialization budget exhausted')
    coords=tuple((o,j) for o in orbits(volume) for j in range(sum(o),volume+1));rows=[]
    for d,w,c in specs:
        factors={o:_context_series(o,d,w,c,B,q) for o in orbits(volume)}
        for v in range(B+1):rows.append(tuple(factors[o][v-j] if v>=j else F0 for o,j in coords))
    R=reconstruction_map(rows)
    return {'coordinates':coords,'probes':tuple(probes),'measurement_volume':B,'A':tuple(rows),'R':R,
            'semantics':'all generic Y_orbit[volume] coordinates; no graph-family prior',
            'noise_policy':'declared exact left inverse on raw readings; original exact APIs reject inconsistent data'}


F0=Fraction(0)
