"""Exact multiplication and primitive rational spectral blocks of Weil commutants.

The finite dimension certificate remains the existing cyclotomic rank packet.
All spectral arithmetic is rational; no numerical diagonalization is used.
"""
from fractions import Fraction as Q
from functools import lru_cache
from math import gcd
from copy import deepcopy
import re
from .divisor_square import WorkLimit
from . import weil_commutant as W


def _mul(A,B):
    n=len(A);out=[[0]*n for _ in range(n)]
    sparse=[[(j,v) for j,v in enumerate(row) if v] for row in B]
    for i,row in enumerate(A):
        for k,a in enumerate(row):
            if a:
                for j,b in sparse[k]:out[i][j]+=a*b
    return tuple(map(tuple,out))


def _linear(basis,c):
    n=len(basis[0]);out=[[Q(0)]*n for _ in range(n)]
    for B,a in zip(basis,c):
        if a:
            for i,row in enumerate(B):
                for j,v in enumerate(row):
                    if v:out[i][j]+=a*v
    return tuple(map(tuple,out))


def _inner(A,B):return sum(a*b for rowa,rowb in zip(A,B) for a,b in zip(rowa,rowb))
def _trace(A):return sum(row[i] for i,row in enumerate(A))
def _strings(xs):return [str(x) for x in xs]


def _output_budget(values):
    if any(max(abs(x.numerator).bit_length(),x.denominator.bit_length())>14000 for x in values):
        raise WorkLimit('operator output bit budget exceeded')


@lru_cache(maxsize=63)
def _algebra(n):
    W._level(n);basis=W._basis(n);d=len(basis)
    if any(A[i][j]!=A[j][i] for A in basis for i in range(n) for j in range(n)):
        raise ArithmeticError('commuting basis is not symmetric')
    import sympy as S
    gram=S.Matrix([[_inner(A,B) for B in basis] for A in basis]);inverse=gram.inv()
    def coordinates(A):
        v=inverse*S.Matrix([_inner(B,A) for B in basis]);c=tuple(Q(int(x.p),int(x.q)) for x in v)
        if _linear(basis,c)!=A:raise ArithmeticError('product left the declared commutant span')
        return c
    table=[]
    for A in basis:
        row=[]
        for B in basis:
            product=_mul(A,B)
            if product!=_mul(B,A):raise ArithmeticError('commutant multiplication is not commutative')
            row.append(coordinates(product))
        table.append(tuple(row))
    return basis,tuple(table)


def _coordinate_mul(a,b,table):
    d=len(table);out=[Q(0)]*d
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            if x and y:
                for k,t in enumerate(table[i][j]):out[k]+=x*y*t
    return tuple(out)


@lru_cache(maxsize=63)
def _spectral(n):
    import sympy as S
    basis,table=_algebra(n);d=len(basis)
    plan=decomposition_plan(n)
    projects=[tuple(tuple(projector_entry(b['node'],x,y) for y in range(n)) for x in range(n)) for b in plan['blocks']]
    inverse=S.Matrix([[_inner(A,B) for B in basis] for A in basis]).inv()
    rows=[]
    for E,b in zip(projects,plan['blocks']):
        v=inverse*S.Matrix([_inner(B,E) for B in basis]);c=tuple(Q(int(x.p),int(x.q)) for x in v)
        if _linear(basis,c)!=E or _trace(E)!=b['rank']:raise ArithmeticError('recursive projector failed source-basis transport')
        rows.append({'coordinates':_strings(c),'rank':b['rank'],'label':b['label'],'node':b['node']})
    # Check the full algebraic decomposition independently of the regular eigensolver.
    for i,A in enumerate(projects):
        if _mul(A,A)!=A or any(A[x][y]!=A[y][x] for x in range(n) for y in range(n)):
            raise ArithmeticError('orthogonal projector identity failed')
        for j,B in enumerate(projects):
            if i!=j and any(v for row in _mul(A,B) for v in row):raise ArithmeticError('distinct projectors overlap')
    if _linear(projects,[Q(1)]*d)!=W._identity(n) or sum(r['rank'] for r in rows)!=n:
        raise ArithmeticError('projectors do not cover the original carrier')
    characters=[]
    for A in basis:
        chars=[]
        for E,r in zip(projects,rows):
            AE=_mul(A,E);chi=Q(_trace(AE))/r['rank']
            if AE!=_linear((E,),(chi,)):raise ArithmeticError('basis not scalar on primitive block')
            chars.append(chi)
        characters.append(tuple(chars))
    for t in range(2,18):
        weights=tuple(Q(t**i) for i in range(d))
        eigen=[sum(weights[i]*characters[i][j] for i in range(d)) for j in range(d)]
        if len(set(eigen))==d:break
    else:raise WorkLimit('no simple rational separator within 16 trials')
    for r,e in zip(rows,eigen):r['eigenvalue']=str(e)
    return basis,table,weights,tuple(projects),tuple(rows),tuple(characters)


def spectral_packet(level, *, include_matrices=False, certify_dimension=False, work_limit=20_000_000):
    W._level(level)
    if type(include_matrices) is not bool or type(certify_dimension) is not bool:raise ValueError('boolean flags required')
    if type(work_limit) is not int or not 1<=work_limit<=100_000_000:raise ValueError('invalid work budget')
    # Deterministic assembly budget; no partial table is returned.
    if level*level*len(W._basis(level))**3>work_limit:raise WorkLimit('spectral assembly work budget exceeded')
    basis,table,weights,projects,rows,chars=_spectral(level)
    packet={'schema':'pp-weil-spectral/1','level':level,'dimension':len(basis),'field':'rational operators inside Q(zeta_N)',
            'separator_coordinates':_strings(weights),'blocks':deepcopy(list(rows)),
            'basis_characters':[_strings(r) for r in chars],
            'multiplication_table':[[_strings(v) for v in r] for r in table],
            'commutative':True,'rational_split':True,'complete_projector_partition':True,
            'kernel_checked':False,'all_level_Lean_dimension_proof':False,
            'scope':'exact finite rational spectral algebra; completeness uses the existing cyclotomic dimension certificate'}
    if include_matrices:
        packet['basis']=[[list(row) for row in A] for A in basis]
        packet['projectors']=[[_strings(row) for row in A] for A in projects]
    if certify_dimension:packet['dimension_certificate']=W.certify_commutant(level,work_limit=work_limit)
    return packet


def operator_packet(level,coefficients):
    basis,table,weights,projects,rows,chars=_spectral(level);d=len(basis)
    if not isinstance(coefficients,(list,tuple)) or len(coefficients)!=d or any(type(c) not in (str,int) for c in coefficients):
        raise ValueError('one exact rational coefficient per basis operator required')
    if any(len(str(c))>1300 for c in coefficients):raise WorkLimit('operator coefficient text budget exceeded')
    if any(type(c) is str and not re.fullmatch(r'[+-]?[0-9]+(?:/[0-9]+)?',c) for c in coefficients):
        raise ValueError('integer or numerator/denominator coefficient text required')
    c=tuple(Q(x) for x in coefficients)
    if max(max(abs(x.numerator).bit_length(),x.denominator.bit_length()) for x in c)>2048:
        raise WorkLimit('operator coefficient bit budget exceeded')
    eigen=tuple(sum(c[i]*chars[i][j] for i in range(d)) for j in range(d))
    _output_budget(eigen)
    traces=sum(r['rank']*v for r,v in zip(rows,eigen));det=Q(1)
    for r,v in zip(rows,eigen):det*=v**r['rank']
    _output_budget((traces,det))
    inverse=None
    if all(eigen):
        inverse=tuple(sum(Q(rows[j]['coordinates'][i])/eigen[j] for j in range(d)) for i in range(d))
        _output_budget(inverse)
        if _coordinate_mul(c,inverse,table)!=tuple(Q(i==0) for i in range(d)):
            raise ArithmeticError('operator inverse identity failed')
    return {'schema':'pp-weil-spectral-operator/1','level':level,'coefficients':_strings(c),
            'eigenvalues':_strings(eigen),'multiplicities':[r['rank'] for r in rows],
            'trace':str(traces),'determinant':str(det),'inverse_coordinates':None if inverse is None else _strings(inverse),
            'kernel_checked':False}


def decomposition_plan(level):
    """All-level compressed primitive-projector construction; no dense matrices.

    Completeness and primitivity use the imported all-exponent orbit paper proof.
    This is not advertised as an all-level Lean dimension theorem.
    """
    from .weil_orbit import closed_form
    if type(level) is not int or level<1:raise ValueError('positive integer level required')
    if level>1000000:raise WorkLimit('compressed level 1000000 budget exceeded')
    m=level;factors=[];p=2
    while p*p<=m:
        a=0
        while m%p==0:a+=1;m//=p
        if a:factors.append((p,a))
        p=3 if p==2 else p+2
    if m>1:factors.append((m,1))
    if not factors:
        return {'schema':'pp-weil-projector-plan/1','level':1,'dimension':1,
                'blocks':[{'rank':1,'label':'unit','node':['identity',1]}],
                'kernel_checked':False,'proof_scope':'all-level paper decomposition; generic Lean calculus and finite native examples'}
    def local(p,a):
        n=p**a
        if a==0:return [{'rank':1,'label':'unit','node':['identity',1]}]
        if p==2 and a==1:return [{'rank':2,'label':'dyadic_base','node':['identity',2]}]
        result=[]
        if a>=2:
            for child in local(p,a-2):
                result.append({'rank':child['rank'],'label':'old/'+child['label'],
                               'node':['embed',n,p,child['node']]})
        if p!=2:
            if a==1:
                base=['identity',n];ranks=[(n+1)//2,(n-1)//2]
            else:
                base=['difference',n,['identity',n],['embed',n,p,['identity',n//(p*p)]]]
                ranks=[(n-n//(p*p))//2]*2
            for sign,rank in zip([1,-1],ranks):
                result.append({'rank':rank,'label':'new_'+('plus' if sign==1 else 'minus'),
                               'node':['parity_split',n,sign,base]})
        else:
            for name,ranks in [('dyadic_mm',[0,1] if a==2 else [n//8]*2),
                               ('dyadic_mixed',[2,0] if a==2 else [n//4]*2)]:
                for sign,rank in zip([1,-1],ranks):
                    if rank:result.append({'rank':rank,'label':name+'_'+('plus' if sign==1 else 'minus'),
                                           'node':['parity_split',n,sign,[name,n]]})
        return result
    import itertools
    blocks=[]
    locals_=[local(p,a) for p,a in factors]
    for choices in itertools.product(*locals_):
        rank=1;parts=[];labels=[]
        for (p,a),child in zip(factors,choices):
            q=p**a;rank*=child['rank'];parts.append([q,pow(level//q,-1,q),child['node']]);labels.append(str(q)+':'+child['label'])
        node=choices[0]['node'] if len(choices)==1 else ['crt_tensor',level,parts]
        blocks.append({'rank':rank,'label':'|'.join(labels),'node':node})
    if sum(b['rank'] for b in blocks)!=level or len(blocks)!=closed_form(level):
        raise ArithmeticError('recursive rank partition disagrees with orbit dimension')
    return {'schema':'pp-weil-projector-plan/1','level':level,'dimension':len(blocks),'factors':[[p,a] for p,a in factors],
            'blocks':blocks,'kernel_checked':False,
            'proof_scope':'all-level paper decomposition; generic Lean calculus and finite native examples'}


def projector_entry(node,x,y):
    """Exact original-coordinate entry of a compressed projector node."""
    op,n=node[:2];x%=n;y%=n
    if op=='identity':return Q(x==y)
    if op=='embed':
        p,child=node[2:];m=n//(p*p)
        return Q(0) if x%p or y%p else projector_entry(child,(x//p)%m,(y//p)%m)/p
    if op=='difference':return projector_entry(node[2],x,y)-projector_entry(node[3],x,y)
    if op=='parity_split':return (projector_entry(node[3],x,y)+node[2]*projector_entry(node[3],-x,y))/2
    if op in ('dyadic_mm','dyadic_mixed'):
        I=Q(x==y);A=Q(x==(y+n//2)%n);B=Q((-1)**x if x==y else 0);AB=Q((-1)**y if x==(y+n//2)%n else 0)
        return (I-A-B+AB)/4 if op=='dyadic_mm' else (I-AB)/2
    if op=='crt_tensor':
        result=Q(1)
        for q,inv,child in node[2]:result*=projector_entry(child,x*inv%q,y*inv%q)
        return result
    raise ValueError('unsupported internal projector node')
