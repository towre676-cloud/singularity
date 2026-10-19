"""Exact Q(t) differential tensor constructions and bounded horizontal sections.

Convention: a column of period coordinates satisfies Y'=A Y. Completeness of
the section search is relative to its supplied numerator/denominator ansatz.
No differential Galois group is inferred from a finite invariant search.
"""
from copy import deepcopy
from itertools import combinations
from math import comb
from .rational_functions import RationalFunction as RF, AlgebraBudget, solve_many
from . import field_polynomials as F
from . import polyalg as P
from .exact_linear import kernel
from .differential_extensions import matrix_encode


def compose(r, s):
    def horner(p):
        v=s.coerce(0)
        for c in reversed(p):v=v*s+c
        return v
    return horner(r.n)/horner(r.d)


class DifferentialModule:
    def __init__(self, specification):
        if not isinstance(specification,dict) or set(specification)-{'matrix','label','work_limit','degree_limit','bit_limit'} or 'matrix' not in specification:
            raise ValueError('matrix and optional label/budgets required')
        self.specification=deepcopy(specification)
        self.budget=AlgebraBudget(**{k:specification[k] for k in ('work_limit','degree_limit','bit_limit') if k in specification})
        a=specification['matrix'];n=len(a)
        if not 1<=n<=48 or any(len(row)!=n for row in a):raise ValueError('square matrix of dimension 1 through 48 required')
        self.connection=[[RF.parse(v,self.budget) for v in row] for row in a]
        self.dimension=n;self.zero=self.connection[0][0].coerce(0)

    @classmethod
    def from_matrix(cls,a,label='derived module'):
        return cls({'matrix':matrix_encode(a),'label':label})

    def summary(self):return dict(schema='pp-differential-module/1',dimension=self.dimension,label=self.specification.get('label',''),convention="Y'=A Y")
    def evidence(self):return dict(self.summary(),connection=matrix_encode(self.connection))

    def dual(self):return self.from_matrix([[-v for v in row] for row in zip(*self.connection)],'dual').evidence()

    def tensor(self, other):
        b=DifferentialModule(other);n,m=self.dimension,b.dimension
        if n*m>48:raise ValueError('tensor dimension exceeds 48')
        a=self.connection;c=b.connection;z=self.zero
        return self.from_matrix([[ (a[i][k] if j==l else z)+(c[j][l] if i==k else z)
            for k in range(n) for l in range(m)] for i in range(n) for j in range(m)],'tensor product').evidence()

    def hom(self, other):
        b=DifferentialModule(other);n,m=self.dimension,b.dimension
        if n*m>48:raise ValueError('Hom dimension exceeds 48')
        a=self.connection;c=b.connection;z=self.zero
        h=[[(c[i][k] if j==l else z)-(a[l][j] if i==k else z)
            for k in range(m) for l in range(n)] for i in range(m) for j in range(n)]
        return self.from_matrix(h,'Hom: T\u2032=B T-T A').evidence()

    def power(self, degree=2, exterior=False):
        n=self.dimension
        if type(degree) is not int or not 0<=degree<=4 or type(exterior) is not bool:raise ValueError('degree 0 through 4 and Boolean exterior required')
        size=comb(n,degree) if exterior and degree<=n else (0 if exterior else comb(n+degree-1,degree))
        if not 1<=size<=48:raise ValueError('power dimension must be 1 through 48')
        if exterior:states=list(combinations(range(n),degree))
        else:
            def exponents(total,slots):
                if slots==1:return [(total,)]
                return [(i,)+v for i in range(total+1) for v in exponents(total-i,slots-1)]
            states=exponents(degree,n)
        index={v:i for i,v in enumerate(states)};z=self.zero;a=self.connection
        out=[[z for _ in states] for _ in states]
        for row,state in enumerate(states):
            if exterior:
                for pos,i in enumerate(state):
                    for j in range(n):
                        v=list(state);v[pos]=j
                        if len(set(v))<degree:continue
                        sign=(-1)**sum(v[k]>v[l] for k in range(degree) for l in range(k+1,degree))
                        col=index[tuple(sorted(v))];out[row][col]+=sign*a[i][j]
            else:
                for i,count in enumerate(state):
                    if not count:continue
                    for j in range(n):
                        v=list(state);v[i]-=1;v[j]+=1
                        out[row][index[tuple(v)]]+=count*a[i][j]
        return dict(self.from_matrix(out,'exterior power' if exterior else 'symmetric power').evidence(),basis=[list(v) for v in states])

    def pullback(self, parameter):
        s=RF.parse(parameter,self.budget)
        if not s.derivative():raise ValueError('nonconstant parameter change required')
        return self.from_matrix([[compose(v,s)*s.derivative() for v in row] for row in self.connection],'parameter pullback').evidence()

    def gauge(self, matrix):
        n=self.dimension;t=[[RF.parse(v,self.budget) for v in row] for row in matrix]
        if len(t)!=n or any(len(row)!=n for row in t):raise ValueError('square gauge required')
        inverse=solve_many(t,[[self.zero.coerce(int(i==j)) for j in range(n)] for i in range(n)])
        if inverse is None:raise ValueError('invertible gauge required')
        ta=F.matrix_product(t,self.connection)
        lhs=[[v.derivative()+ta[i][j] for j,v in enumerate(row)] for i,row in enumerate(t)]
        b=F.matrix_product(lhs,inverse)
        if F.matrix_product(b,t)!=lhs:raise AssertionError('gauge replay failed')
        return dict(self.from_matrix(b,'gauge transform').evidence(),intertwining_checked=True)

    def horizontal_sections(self, degree=1, denominator=None):
        if type(degree) is not int or not 0<=degree<=4 or self.dimension*(degree+1)>192:raise ValueError('bounded section degree/dimension exceeded')
        d=RF.parse(denominator or [1],self.budget)
        if d.d!=(1,) or not d:raise ValueError('nonzero polynomial denominator required')
        n=self.dimension;z=self.zero
        scalars=[RF([0]*k+[1],d.n,budget=self.budget) for k in range(degree+1)]
        columns=[]
        for i in range(n):
            for s in scalars:columns.append([(s.derivative() if j==i else z)-self.connection[j][i]*s for j in range(n)])
        rows=[]
        for j in range(n):
            common=P.ONE
            for col in columns:common=P.exact_div(P.mul(common,col[j].d),P.gcd_poly(common,col[j].d))
            polys=[P.mul(c[j].n,P.exact_div(common,c[j].d)) for c in columns]
            for k in range(max(map(len,polys))):rows.append([p[k] if k<len(p) else 0 for p in polys])
        basis=kernel(rows);sections=[]
        for v in basis:
            s=[sum((v[i*(degree+1)+k]*scalars[k] for k in range(degree+1)),z) for i in range(n)]
            if any(s[i].derivative()-sum((self.connection[i][j]*s[j] for j in range(n)),z) for i in range(n)):raise AssertionError('section replay failed')
            sections.append([x.packet() for x in s])
        return dict(schema='pp-horizontal-sections/1',degree=degree,denominator=d.packet(),dimension=len(sections),basis=sections,
            identities_checked=True,complete_within_ansatz=True,scope='rational horizontal sections with this shared denominator and numerator degree; no full Galois group classification')

    def observable(self, coefficients=None):
        # The observable algorithm needs only these attributes, not a curve.
        from .symmetry_quotients import PolynomialCurve
        self.one=self.zero.coerce(1)
        coefficients=None if coefficients is None else [RF.parse(v,self.budget) for v in coefficients]
        return PolynomialCurve.observable(self,coefficients)

    def involution_descent(self, matrix):
        """Matrix Hilbert 90 and connection descent for t -> -t, u=t^2."""
        n=self.dimension;z=self.zero;t=RF([0,1],budget=self.budget);minus=-t
        s=[[RF.parse(v,self.budget) for v in row] for row in matrix]
        if len(s)!=n or any(len(row)!=n for row in s):raise ValueError('square semilinear cocycle required')
        sigma=lambda a:[[compose(v,minus) for v in row] for row in a]
        ident=[[z.coerce(int(i==j)) for j in range(n)] for i in range(n)]
        if F.matrix_product(sigma(s),s)!=ident:raise ValueError('involution cocycle identity failed')
        b=[[-v for v in row] for row in sigma(self.connection)]
        sa=F.matrix_product(s,self.connection);bs=F.matrix_product(b,s)
        if any(s[i][j].derivative()+sa[i][j]-bs[i][j] for i in range(n) for j in range(n)):raise ValueError('cocycle does not intertwine the differential module')
        candidates=[[ident[i][j]+s[i][j] for j in range(n)] for i in range(n)]
        candidates.extend([[t*(ident[i][j]-s[i][j]) for j in range(n)] for i in range(n)])
        h=[]
        for row in candidates:
            if F.matrix_rank(h+[row])>len(h):h.append(row)
            if len(h)==n:break
        if len(h)!=n or F.matrix_product(sigma(h),s)!=h:raise AssertionError('matrix Hilbert 90 invariant frame failed')
        c=[[RF.parse(v,self.budget) for v in row] for row in self.gauge(matrix_encode(h))['connection']]
        descended=[]
        for row in c:
            target=[]
            for v in row:
                q=v/(2*t)
                if compose(q,minus)!=q or any(q.n[1::2]) or any(q.d[1::2]):raise AssertionError('connection did not descend to Q(t^2)')
                target.append(RF(q.n[::2],q.d[::2],budget=self.budget))
            descended.append(target)
        return dict(schema='pp-quadratic-differential-descent/1',invariant_frame=matrix_encode(h),descended=self.from_matrix(descended,'over u=t^2').evidence(),
          cocycle_identity_checked=True,horizontal_intertwining_checked=True,frame_descent_checked=True,
          scope='full rank matrix semilinear descent under the declared parameter involution, including chain-rule connection; no automatic arbitrary Galois descent search')

    def horizontal_endomorphisms(self,degree=0,denominator=None,holomorphic_indices=None,pairing=None):
        n=self.dimension
        h=self.hom(self.specification);search=DifferentialModule({'matrix':h['connection']}).horizontal_sections(degree,denominator)
        basis=[[[RF.parse(v,self.budget) for v in row[i*n:(i+1)*n]] for i in range(n)] for row in search['basis']]
        indices=set(holomorphic_indices or [])
        if any(type(i) is not int or not 0<=i<n for i in indices):raise ValueError('valid holomorphic basis indices required')
        j=None if pairing is None else [[RF.parse(v,self.budget) for v in row] for row in pairing]
        if j is not None and (len(j)!=n or any(len(row)!=n for row in j) or F.matrix_rank(j)!=n or any(j[i][k]!=-j[k][i] for i in range(n) for k in range(n))):raise ValueError('nondegenerate alternating pairing required')
        if j is not None:
            aj=F.matrix_product(self.connection,j);jat=F.matrix_product(j,list(map(list,zip(*self.connection))))
            if any(j[i][k].derivative()-aj[i][k]-jat[i][k] for i in range(n) for k in range(n)):raise ValueError('pairing is not horizontal')
        conditions=[]
        for p in basis:
            values=[p[i][k] for i in sorted(indices) for k in range(n) if k not in indices]
            if j is not None:
                pj=F.matrix_product(p,j);jpt=F.matrix_product(j,list(map(list,zip(*p))))
                values.extend(pj[i][k]-jpt[i][k] for i in range(n) for k in range(n))
            conditions.append(values)
        equations=[]
        for row in zip(*conditions):
            common=P.ONE
            for v in row:common=P.exact_div(P.mul(common,v.d),P.gcd_poly(common,v.d))
            polynomials=[P.mul(v.n,P.exact_div(common,v.d)) for v in row]
            equations.extend([[p[k] if k<len(p) else 0 for p in polynomials] for k in range(max(map(len,polynomials)))])
        if basis:
            vectors=kernel(equations) if equations else [[int(i==k) for k in range(len(basis))] for i in range(len(basis))]
        else:vectors=[]
        filtered=[[[sum((v[k]*basis[k][i][l] for k in range(len(basis))),self.zero) for l in range(n)] for i in range(n)] for v in vectors]
        idempotents=[matrix_encode(p) for p in filtered if F.matrix_product(p,p)==p and 0<F.matrix_rank(p)<n]
        return dict(schema='pp-module-filtered-horizontal-algebra/1',linear_space_dimension=len(filtered),basis=[matrix_encode(p) for p in filtered],
          projectors=idempotents,complete_linear_ansatz=True,filtration_checked=holomorphic_indices is not None,polarization_checked=j is not None,
          scope='complete horizontal endomorphism space within the supplied rational ansatz and linear filtration/polarization constraints; only basis elements tested for idempotence; no rational Betti descent or algebraic correspondence inferred')
