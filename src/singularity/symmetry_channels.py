"""Checked rational finite-group channels and finite-catalogue robust repair.

One-system commutant blindness and conjugate-model blindness are deliberately
separate tests. Projectors do not magically make projected sensors available.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations


def _q(x):
    if isinstance(x,bool) or not isinstance(x,(int,Fraction)):
        raise TypeError('exact rational required')
    return Fraction(x)


def _matrix(A):
    A=tuple(tuple(map(_q,row)) for row in A)
    if not A or any(len(row)!=len(A) for row in A):
        raise ValueError('nonempty square matrix required')
    return A


def _eye(n):
    return tuple(tuple(Fraction(i==j) for j in range(n)) for i in range(n))


def _mul(A,B):
    return tuple(tuple(sum((a*B[k][j] for k,a in enumerate(row)),Fraction())
                       for j in range(len(B[0]))) for row in A)


def _add(A,B,scale=1):
    return tuple(tuple(a+scale*b for a,b in zip(x,y)) for x,y in zip(A,B))


def _rank(rows):
    rows=[list(row) for row in rows if any(row)]
    if not rows:return 0
    rank=0
    for col in range(len(rows[0])):
        pivot=next((i for i in range(rank,len(rows)) if rows[i][col]),None)
        if pivot is None:continue
        rows[rank],rows[pivot]=rows[pivot],rows[rank]
        a=rows[rank][col]; rows[rank]=[x/a for x in rows[rank]]
        for i in range(len(rows)):
            if i!=rank and rows[i][col]:
                a=rows[i][col];rows[i]=[x-a*y for x,y in zip(rows[i],rows[rank])]
        rank+=1
    return rank


def _rowmul(row,A):
    return tuple(sum((row[i]*A[i][j] for i in range(len(row))),Fraction()) for j in range(len(row)))


@dataclass(frozen=True)
class FiniteRepresentation:
    elements: tuple
    multiplication: tuple
    matrices: tuple
    identity: int=0

    def __post_init__(self):
        object.__setattr__(self,'elements',tuple(self.elements))
        object.__setattr__(self,'multiplication',tuple(tuple(x) for x in self.multiplication))
        object.__setattr__(self,'matrices',tuple(_matrix(A) for A in self.matrices))
        verify_representation(self)


def verify_representation(rep, max_order=64,max_dimension=64):
    m=len(rep.elements)
    if not 1<=m<=max_order or len(set(rep.elements))!=m:
        raise ValueError('invalid or oversized finite group')
    if len(rep.matrices)!=m or len(rep.multiplication)!=m:
        raise ValueError('group data dimensions differ')
    n=len(rep.matrices[0]);e=rep.identity
    if not 1<=n<=max_dimension or not isinstance(e,int) or isinstance(e,bool) or not 0<=e<m:
        raise ValueError('representation resource/dimension limit')
    if any(len(A)!=n for A in rep.matrices):raise ValueError('matrix dimensions differ')
    T=rep.multiplication
    if any(len(row)!=m or any(isinstance(x,bool) or not isinstance(x,int) or not 0<=x<m for x in row) for row in T):
        raise ValueError('invalid multiplication table')
    for a in range(m):
        if T[e][a]!=a or T[a][e]!=a or not any(T[a][b]==e and T[b][a]==e for b in range(m)):
            raise ValueError('group identity/inverse failed')
        for b in range(m):
            if _mul(rep.matrices[a],rep.matrices[b])!=rep.matrices[T[a][b]]:
                raise ValueError('representation homomorphism failed')
            if any(T[T[a][b]][c]!=T[a][T[b][c]] for c in range(m)):
                raise ValueError('group associativity failed')
    if rep.matrices[e]!=_eye(n):raise ValueError('identity matrix failed')
    return True


def reflection_channels(involution):
    P=_matrix(involution);I=_eye(len(P))
    if _mul(P,P)!=I:raise ValueError('reflection must square to identity')
    return tuple(tuple(tuple((a+sign*b)/2 for a,b in zip(x,y)) for x,y in zip(I,P)) for sign in (1,-1))


def verify_channel_decomposition(projectors,operators=(),representation=()):
    Ps=tuple(_matrix(P) for P in projectors)
    if not Ps:raise ValueError('projectors required')
    n=len(Ps[0]);zero=tuple((Fraction(),)*n for _ in range(n));total=zero
    As=tuple(_matrix(A) for A in tuple(operators)+tuple(representation))
    if any(len(P)!=n for P in Ps+As):raise ValueError('dimension mismatch')
    for i,P in enumerate(Ps):
        if _mul(P,P)!=P:raise ValueError('not idempotent')
        if any(any(_mul(P,Q)[r][c] for r in range(n) for c in range(n)) for j,Q in enumerate(Ps) if i!=j):
            raise ValueError('projectors not orthogonal')
        if any(_mul(P,A)!=_mul(A,P) for A in As):raise ValueError('channel does not commute')
        total=_add(total,P)
    if total!=_eye(n):raise ValueError('projectors incomplete')
    return True


def observable_rows(operators,observations,max_dimension=128):
    As=tuple(_matrix(A) for A in operators)
    rows=tuple(tuple(map(_q,row)) for row in observations)
    if not rows:raise ValueError('observations required')
    n=len(rows[0])
    if n>max_dimension or any(len(row)!=n for row in rows) or any(len(A)!=n for A in As):
        raise ValueError('closure dimension/resource limit')
    basis=[]
    for row in rows:
        if _rank(basis+[row])>len(basis):basis.append(row)
    head=0
    while head<len(basis):
        row=basis[head];head+=1
        for A in As:
            w=_rowmul(row,A)
            if _rank(basis+[w])>len(basis):basis.append(w)
    return tuple(basis)


def channel_observability(operators,observations,projectors):
    verify_channel_decomposition(projectors,operators)
    full=observable_rows(operators,observations)
    channels=tuple(observable_rows(operators,tuple(_rowmul(row,P) for row in observations)) for P in projectors)
    ranks=tuple(len(W) for W in channels)
    # Reuse the original witness-carrying closure contract; this module's
    # straightforward span expansion is also an independent rank oracle.
    from .observability import OperatorSystem, observable_closure, verify_certificate
    system=OperatorSystem(len(projectors[0]),operators,observations)
    certificate=observable_closure(system)
    if not verify_certificate(system,certificate) or certificate.rank!=len(full):
        raise ArithmeticError('channel adapter disagrees with original closure certificate')
    # Equality is checked, never inferred merely from commutation.
    return {'full_rank':len(full),'channel_ranks':ranks,
            'sum_channel_ranks':sum(ranks),'closure_certificate_verified':True,'observations_decompose':len(full)==sum(ranks),
            'blind_channels':tuple(i for i,W in enumerate(channels) if not W)}


def conjugate_model_blindness(Aa,Ab,P,Ba,Bb,Ca,Cb,x0a,x0b):
    Aa,Ab,P=map(_matrix,(Aa,Ab,P));n=len(P)
    Ba,Bb,x0a,x0b=(tuple(map(_q,v)) for v in (Ba,Bb,x0a,x0b))
    Ca,Cb=tuple(tuple(map(_q,r)) for r in Ca),tuple(tuple(map(_q,r)) for r in Cb)
    if any(len(A)!=n for A in (Aa,Ab)) or any(len(v)!=n for v in (Ba,Bb,x0a,x0b)):
        raise ValueError('dimension mismatch')
    if len(Ca)!=len(Cb) or any(len(row)!=n for row in Ca+Cb):raise ValueError('sensor dimension mismatch')
    # P need not be involutory: intertwining and sensor/input identities suffice.
    def mv(A,x):return tuple(sum((a*b for a,b in zip(row,x)),Fraction()) for row in A)
    return (_mul(Ab,P)==_mul(P,Aa) and mv(P,Ba)==Bb and mv(P,x0a)==x0b
            and tuple(_rowmul(row,P) for row in Cb)==Ca)


@dataclass(frozen=True)
class RepairOption:
    identifier: str
    cost: Fraction
    readings: tuple
    errors: tuple
    word: tuple=()
    physical_sensor: str='declared local sensor'

    def __post_init__(self):
        if not isinstance(self.identifier,str) or not self.identifier:raise ValueError('identifier required')
        c=_q(self.cost);y=tuple(map(_q,self.readings));e=tuple(map(_q,self.errors))
        if c<=0 or len(y)<2 or len(e)!=len(y) or any(x<0 for x in e):raise ValueError('invalid repair data')
        object.__setattr__(self,'cost',c);object.__setattr__(self,'readings',y);object.__setattr__(self,'errors',e)
        object.__setattr__(self,'word',tuple(self.word))


def minimum_channel_repair(candidate_ids,targets,options,max_options=20):
    ids=tuple(candidate_ids);targets=tuple(targets);options=tuple(options)
    if len(ids)<2 or len(ids)!=len(set(ids)) or len(ids)!=len(targets) or len(options)>max_options:
        raise ValueError('invalid finite repair population/resource limit')
    if any(not isinstance(o,RepairOption) or len(o.readings)!=len(ids) for o in options):raise ValueError('repair dimension mismatch')
    if len({o.identifier for o in options})!=len(options):raise ValueError('duplicate option ID')
    required=tuple((a,b) for a in range(len(ids)) for b in range(a) if targets[a]!=targets[b])
    panels=[]
    for size in range(len(options)+1):
        for inds in combinations(range(len(options)),size):
            cost=sum((options[i].cost for i in inds),Fraction())
            good=all(any(abs(options[i].readings[a]-options[i].readings[b])>options[i].errors[a]+options[i].errors[b]
                         for i in inds) for a,b in required)
            panels.append((cost,tuple(options[i].identifier for i in inds),good))
    feasible=sorted(p for p in panels if p[2])
    if not feasible:return {'feasible':False,'exhausted':len(panels),'candidate_ids':ids}
    cost,panel,_=feasible[0]
    return {'feasible':True,'cost':cost,'panel':panel,'exhausted':len(panels),
            'cheaper_panels_checked':sum(p[0]<cost for p in panels),'candidate_ids':ids,
            'scope':'finite declared options; independent resets; absolute interval errors'}


def conjugate_permutation_blindness(first,second,permutation,sensor_indices=None):
    """Sparse original-model all-input blindness under a checked permutation.

    sensor_indices names actual existing sensor rows, never implicit negative
    contrasts. Fixed zero initial state is part of this adapter's contract.
    """
    from .thermal_diagnostics import AffineCandidate
    if not isinstance(first,AffineCandidate) or not isinstance(second,AffineCandidate):raise TypeError('AffineCandidate models required')
    p=tuple(permutation);n=first.dimension
    if second.dimension!=n or len(p)!=n or any(isinstance(i,bool) or not isinstance(i,int) for i in p) or set(p)!=set(range(n)):
        raise ValueError('a bijective original-state permutation is required')
    transformed={(p[i],p[j]):a for i,j,a in first.entries}
    if transformed!={(i,j):a for i,j,a in second.entries}:return False
    if any(second.heater[p[i]]!=first.heater[i] for i in range(n)):return False
    indices=tuple(range(len(first.sensors))) if sensor_indices is None else tuple(sensor_indices)
    if any(isinstance(s,bool) or not isinstance(s,int) or not 0<=s<min(len(first.sensors),len(second.sensors)) for s in indices):
        raise ValueError('invalid physical sensor channel')
    return all(second.sensors[s][p[i]]==first.sensors[s][i] for s in indices for i in range(n))


def transformed_noise_set(transform,radii,kind='box'):
    """Retain the actual linear image, including correlations after basis change.

    For a box this factor maps [-1,1]^n, rather than declaring a new independent
    box. For a Euclidean unit ball it records T diag(r)^2 T.T, the output Gram.
    Coordinate radii are only projections, never an independence assertion.
    """
    T=tuple(tuple(map(_q,row)) for row in transform);r=tuple(map(_q,radii))
    if not T or any(len(row)!=len(r) for row in T) or any(x<0 for x in r):raise ValueError('noise-set dimension or radius invalid')
    factor=tuple(tuple(a*b for a,b in zip(row,r)) for row in T)
    if kind=='box':return {'kind':'linear-image-of-box','factor':factor,'coordinate_bounds':tuple(sum(map(abs,row),Fraction()) for row in factor)}
    if kind=='ellipsoid':
        gram=tuple(tuple(sum((a*b for a,b in zip(x,y)),Fraction()) for y in factor) for x in factor)
        return {'kind':'ellipsoid-linear-image','factor':factor,'gram':gram}
    raise ValueError('noise kind must be box or ellipsoid')
