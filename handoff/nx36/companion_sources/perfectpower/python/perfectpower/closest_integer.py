"""All closest integer lifts of exact linear observations in an SPD metric.

Smith coordinates preserve the full integer fibre. Exact weighted LLL is an
optional cost optimization, certified by unimodular basis operations. Exact
LDL branch-and-bound enumerates a finite incumbent ellipsoid and keeps ties.
This is exponential lattice enumeration with budgets, not a general speedup.
"""
from fractions import Fraction as Q
from copy import deepcopy
from math import isqrt
from . import exact_linear as E
from .integer_lifting import smith_certificate,verify_smith,_solve_with_certificate
from .weighted_hodge import metric
from .divisor_square import WorkLimit


def _vector(values,n):
    values=tuple(values)
    if len(values)!=n or any(type(x) not in (int,Q) for x in values):raise ValueError('matching exact vector required')
    return tuple(map(Q,values))


def _dot(x,m,y):return sum(a*b for a,b in zip(x,E.apply(m,y)))


def _round(q):
    lo=q.numerator//q.denominator
    return lo if q-lo<=Q(1,2) else lo+1


def _lll(basis,m,operation_limit):
    basis=[list(v) for v in basis];operations=[]
    def gs():
        orthogonal=[];mu=[];norm=[]
        for i,v in enumerate(basis):
            w=list(map(Q,v));coeff=[]
            for j,u in enumerate(orthogonal):
                c=_dot(v,m,u)/norm[j];coeff.append(c);w=[x-c*y for x,y in zip(w,u)]
            orthogonal.append(w);mu.append(coeff);norm.append(_dot(w,m,w))
        return mu,norm
    k=1
    while k<len(basis):
        mu,norm=gs()
        for j in range(k-1,-1,-1):
            r=_round(mu[k][j])
            if r:
                if len(operations)>=operation_limit:raise WorkLimit('exact kernel basis reduction budget exceeded')
                basis[k]=[x-r*y for x,y in zip(basis[k],basis[j])];operations.append(['add',k,j,-r]);mu,norm=gs()
        if norm[k]>=(Q(3,4)-mu[k][k-1]**2)*norm[k-1]:k+=1
        else:
            if len(operations)>=operation_limit:raise WorkLimit('exact kernel basis reduction budget exceeded')
            basis[k],basis[k-1]=basis[k-1],basis[k];operations.append(['swap',k,k-1,0]);k=max(1,k-1)
    return tuple(tuple(v) for v in basis),operations


def _geometry(basis,m):
    if not basis:return None
    g=tuple(tuple(_dot(x,m,y) for y in basis) for x in basis);r=len(g)
    lower=[[Q(i==j) for j in range(r)] for i in range(r)];diag=[]
    for i in range(r):
        di=g[i][i]-sum(lower[i][k]**2*diag[k] for k in range(i))
        if di<=0:raise ValueError('kernel basis must be independent in positive metric')
        diag.append(di)
        for j in range(i+1,r):lower[j][i]=(g[j][i]-sum(lower[j][k]*lower[i][k]*diag[k] for k in range(i)))/di
    upper=E.transpose(lower)
    if E.multiply(E.multiply(lower,tuple(tuple(diag[i] if i==j else Q(0) for j in range(r)) for i in range(r))),upper)!=g:
        raise AssertionError('LDL identity failed')
    return g,E.inverse(g),upper,tuple(diag)


def _ordered(lo,hi,center):
    left=min(hi,center.numerator//center.denominator);right=max(lo,left+1)
    while left>=lo or right<=hi:
        if right>hi or (left>=lo and center-left<=right-center):yield left;left-=1
        else:yield right;right+=1


def _minimize(particular,basis,m,target,geometry,node_limit):
    delta=tuple(Q(x)-t for x,t in zip(particular,target));energy0=_dot(delta,m,delta);r=len(basis)
    if r==0:return {'minimizers':[tuple(particular)],'minimum_energy':energy0,'continuous_minimum':energy0,
        'continuous_point':tuple(map(Q,particular)),'enumeration_nodes':0,'initial_radius_squared':Q(0),'minimizer_parameters':[()]}
    g,inv,upper,diag=geometry;h=tuple(_dot(v,m,delta) for v in basis);center=tuple(-x for x in E.apply(inv,h))
    floor_energy=energy0+sum(x*y for x,y in zip(h,center))
    continuous=tuple(Q(x)+sum(basis[j][i]*center[j] for j in range(r)) for i,x in enumerate(particular))
    def local(i,z):return center[i]-sum(upper[i][j]*(z[j]-center[j]) for j in range(i+1,r))
    seed=[0]*r
    for i in range(r-1,-1,-1):seed[i]=_round(local(i,seed))
    def radius(z):return sum(diag[i]*(z[i]-local(i,z))**2 for i in range(r))
    best=radius(seed);initial=best;winners={tuple(seed)};nodes=0;z=[0]*r
    def visit(i,partial):
        nonlocal best,nodes,winners
        if i<0:
            if partial<best:best=partial;winners=set()
            if partial==best:winners.add(tuple(z))
            return
        c=local(i,z);room=(best-partial)/diag[i]
        if room<0:return
        p,q=c.numerator,c.denominator;s=isqrt((room*q*q).numerator//(room*q*q).denominator)
        lo=-((s-p)//q);hi=(p+s)//q
        for value in _ordered(lo,hi,c):
            nodes+=1
            if nodes>node_limit:raise WorkLimit('complete closest-lift enumeration exceeds node budget; no optimum returned')
            term=diag[i]*(value-c)**2
            if partial+term>best:break
            z[i]=value;visit(i-1,partial+term)
    visit(r-1,Q(0));parameters=sorted(winners)
    points=sorted(tuple(x+sum(basis[j][i]*t[j] for j in range(r)) for i,x in enumerate(particular)) for t in parameters)
    minimum=floor_energy+best
    if any(_dot(tuple(Q(x)-y for x,y in zip(v,target)),m,tuple(Q(x)-y for x,y in zip(v,target)))!=minimum for v in points):
        raise AssertionError('closest-lift energy replay failed')
    return {'minimizers':points,'minimum_energy':minimum,'continuous_minimum':floor_energy,'continuous_point':continuous,
            'enumeration_nodes':nodes,'initial_radius_squared':initial,'minimizer_parameters':parameters}


class IntegerLiftOptimizer:
    """Reuse one exact Smith/metric decomposition for many right-hand sides."""
    def __init__(self,matrix,mass=None,*,parameter_limit=12,node_limit=100000,reduce_basis=True):
        a=tuple(tuple(row) for row in matrix)
        if not a or not a[0] or len(a)>64 or len(a[0])>64:raise ValueError('matrix dimensions at most 64 required')
        if any(type(v) is not int or v<1 for v in (parameter_limit,node_limit)):raise ValueError('positive budgets required')
        if type(reduce_basis) is not bool:raise ValueError('reduce_basis must be boolean')
        self._certificate=smith_certificate(a);n=len(a[0]);rank=self._certificate['rank'];self.node_limit=node_limit
        if n-rank>parameter_limit:raise WorkLimit('integer kernel exceeds parameter dimension budget')
        self.mass=metric(E.identity(n) if mass is None else mass,n)
        basis=tuple(tuple(self._certificate['right'][i][j] for i in range(n)) for j in range(rank,n))
        self.basis,self.operations=_lll(basis,self.mass,node_limit) if reduce_basis else (basis,[])
        self.geometry=_geometry(self.basis,self.mass);self.calls=0

    @property
    def certificate(self):
        return deepcopy(self._certificate)

    def nearest(self,vector,target):
        n=len(self.mass);target=_vector(target,n);self.calls+=1
        fibre=_solve_with_certificate(self._certificate,vector)
        proof={'smith':self.certificate,'mass':self.mass,'kernel_basis':self.basis,'basis_operations':deepcopy(self.operations)}
        base={'rhs':list(vector),'target':target,'proof':proof,'execution_verified':False}
        if fibre['status']!='INTEGER_AFFINE_FIBRE':return {**base,**fibre,'complete':True}
        result=_minimize(fibre['particular'],self.basis,self.mass,target,self.geometry,self.node_limit)
        for v in result['minimizers']:
            if list(E.apply(self._certificate['matrix'],v))!=list(vector):raise AssertionError('optimizer violates observation')
        return {**base,**result,'status':'OPTIMAL_INTEGER_LIFTS','complete':True,
                'parameter_dimension':len(self.basis),'basis_reduction_operations':len(self.operations),
                'shared_decomposition_calls':self.calls,'scope':'all minimum-energy integer points satisfying the exact observation'}


def verify_optimum(result,*,node_limit=100000,parameter_limit=12):
    """Replay an optimizer certificate without Smith or LLL discovery."""
    try:
        if any(type(v) is not int or v<1 for v in (node_limit,parameter_limit)) or result['execution_verified'] is not False or result['complete'] is not True:return False
        proof=result['proof'];cert=proof['smith']
        if not verify_smith(cert):return False
        n=len(cert['right']);m=metric([[Q(x) if isinstance(x,str) else x for x in row] for row in proof['mass']],n)
        rhs=result['rhs'];fibre=_solve_with_certificate(cert,rhs)
        if fibre['status']!='INTEGER_AFFINE_FIBRE':
            return result['status']==fibre['status'] and all(result[k]==v for k,v in fibre.items())
        rank=cert['rank'];basis=[[cert['right'][i][j] for i in range(n)] for j in range(rank,n)]
        if len(basis)>parameter_limit or len(proof['basis_operations'])>node_limit:return False
        for op in proof['basis_operations']:
            if not isinstance(op,(list,tuple)) or len(op)!=4:return False
            kind,i,j,c=op
            if any(type(x) is not int for x in (i,j,c)) or abs(c).bit_length()>100000 or not 0<=i<len(basis) or not 0<=j<len(basis) or i==j:return False
            if kind=='swap' and c==0:basis[i],basis[j]=basis[j],basis[i]
            elif kind=='add':basis[i]=[x+c*y for x,y in zip(basis[i],basis[j])]
            else:return False
        if [list(v) for v in proof['kernel_basis']]!=basis or any(type(x) is not int for v in proof['kernel_basis'] for x in v):return False
        target=_vector([Q(x) if isinstance(x,str) else x for x in result['target']],n)
        actual=_minimize(fibre['particular'],basis,m,target,_geometry(basis,m),node_limit)
        return result['status']=='OPTIMAL_INTEGER_LIFTS' and all(type(x) is int for v in result['minimizers'] for x in v) and sorted(tuple(v) for v in result['minimizers'])==actual['minimizers'] and Q(result['minimum_energy'])==actual['minimum_energy'] and Q(result['continuous_minimum'])==actual['continuous_minimum']
    except (KeyError,ValueError,TypeError,IndexError,ArithmeticError):return False
