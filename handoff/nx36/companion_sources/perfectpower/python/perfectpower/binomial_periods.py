"""Multiple binomial sums as rational constant terms; exact telescoping proofs."""
from copy import deepcopy
from math import comb
from fractions import Fraction as Q
from .rational_functions import RationalFunction as RF, solve_many
from . import field_polynomials as F
from .differential_modules import DifferentialModule


FAMILIES={
 'vandermonde':[[1,0,0,0,1,0],[1,0,0,0,1,0]],
 'apery2':[[1,0,0,0,1,0],[1,0,0,0,1,0],[1,1,0,0,1,0]],
 'apery3':[[1,0,0,0,1,0],[1,0,0,0,1,0],[1,1,0,0,1,0],[1,1,0,0,1,0]]}


class BinomialSum:
    def __init__(self,specification):
        if not isinstance(specification,dict) or set(specification)-{'factors','family'}:raise ValueError('factors or named family required')
        self.specification=deepcopy(specification);name=specification.get('family')
        if name is not None and (name not in FAMILIES or 'factors' in specification):raise ValueError('known family without conflicting factors required')
        self.factors=deepcopy(FAMILIES[name] if name else specification.get('factors',[]));self.family=name
        if not 1<=len(self.factors)<=4 or any(len(f)!=6 or any(type(v) is not int or abs(v)>8 for v in f) or f[0]<0 or f[0]+f[1]<0 or f[2]<0 for f in self.factors):raise ValueError('1 through 4 bounded affine binomial factors, nonnegative upper arguments required')
    def summary(self):return dict(schema='pp-binomial-sum/1',factors=self.factors,family=self.family)
    def term(self,n):
        if type(n) is not int or not 0<=n<=200:raise ValueError('index 0 through 200 required')
        total=0
        for k in range(n+1):
            value=1
            for a,b,c,d,e,f in self.factors:
                upper=a*n+b*k+c;lower=d*n+e*k+f
                value*=comb(upper,lower) if 0<=lower<=upper else 0
            total+=value
        return total
    def terms(self,start=0,size=12):
        if type(size) is not int or not 0<=size<=201 or type(start) is not int or not 0<=start<=200 or start+size>201:raise ValueError('bounded term window required')
        return [self.term(n) for n in range(start,start+size)]
    def evidence(self):
        return dict(self.summary(),constant_term=dict(A=[dict(variable=i,one_plus_power=a,variable_power=-d) for i,(a,b,c,d,e,f) in enumerate(self.factors)],
          B=[dict(variable=i,one_plus_power=b,variable_power=-e) for i,(a,b,c,d,e,f) in enumerate(self.factors)],
          C=[dict(variable=i,one_plus_power=c,variable_power=-f) for i,(a,b,c,d,e,f) in enumerate(self.factors)],
          generating_function='CT_z C / ((1-t A)(1-t A B))',formal_expansion='sum over n>=k>=0, in powers of t'),
          scope='exact rational constant-term compiler for the supplied sum; a general creative telescoper is not claimed')
    def telescoper(self):
        name=self.family
        if name is None:raise ValueError('certified telescopers currently supplied for the three named families')
        n=RF([0,1]);z=n.coerce(0);one=n.coerce(1)
        if name=='vandermonde':
            D=[(n+1)*(n+1),-2*(n+1),one];kpower=2
            numerator=F.add(F.scale([one],(n+1)*(n+1)*(n+1)),F.scale(D,-2*(2*n+1)))
            theta=[[0,0,1],[-2,-4]];degree=1;recurrence=['n+1','-2(2n+1)','0']
        elif name=='apery2':
            D=F.product([(n+1)*(n+1),-2*(n+1),one],[n,one]);kpower=3;degree=2
            # D*(L/T), where L=(n+1)^2 shift+ -(11n^2+11n+3)-n^2 shift-.
            numerator=F.add(F.scale(F.product([n+1,one],[n,one]),(n+1)*(n+1)*(n+1)),F.scale(D,-(11*n*n+11*n+3)))
            numerator=F.add(numerator,F.scale(F.product([n*n,-2*n,one],[(n+1)*(n+1),-2*(n+1),one]),-n))
            theta=[[0,0,1],[-3,-11,-11],[-1,-2,-1]];recurrence=['(n+1)^2','-(11n^2+11n+3)','-n^2']
        else:
            D=F.product([(n+1)*(n+1),-2*(n+1),one],[n*n,2*n,one]);kpower=4;degree=2
            numerator=F.add(F.scale(F.product(F.product([n+1,one],[n+1,one]),[n*n,2*n,one]),(n+1)*(n+1)*(n+1)),F.scale(D,-(2*n+1)*(17*n*n+17*n+5)))
            numerator=F.add(numerator,F.scale(F.product([(n+1)*(n+1),-2*(n+1),one],[n*n,-2*n,one]),n*n*n))
            theta=[[0,0,0,1],[-5,-27,-51,-34],[1,3,3,1]];recurrence=['(n+1)^3','-(2n+1)(17n^2+17n+5)','n^3']
        columns=[]
        for i in range(degree+1):
            p=[z]*i+[one];shift=F.shift(p,one)
            columns.append(F.add(F.product(D,shift),F.scale([z]*kpower+p,-1)))
        length=max(len(numerator),*(len(v) for v in columns));pad=lambda p:p+[z]*(length-len(p))
        solution=solve_many(list(zip(*(pad(c) for c in columns))),[[v] for v in pad(numerator)])
        if solution is None:raise AssertionError('exact telescoping ansatz failed')
        p=[v[0] for v in solution]
        if F.add(F.product(D,F.shift(p,one)),F.scale([z]*kpower+p,-1))!=F.trim(numerator):raise AssertionError('telescoper certificate replay failed')
        # Theta-polynomial convention: theta[j][k] multiplies t^j theta^k.
        if name=='vandermonde':theta=[[0,1],[-2,-4]]
        order=max(len(row)-1 for row in theta);stirling=[[0]*(order+1) for _ in range(order+1)];stirling[0][0]=1
        for k in range(1,order+1):
            for r in range(1,k+1):stirling[k][r]=stirling[k-1][r-1]+r*stirling[k-1][r]
        t=n;operators=[z for _ in range(order+1)]
        for j,row in enumerate(theta):
            for k,c in enumerate(row):
                for r in range(k+1):operators[r]+=c*stirling[k][r]*RF([0]*(j+r)+[1])
        a=[[z for _ in range(order)] for _ in range(order)]
        for i in range(order-1):a[i][i+1]=one
        a[-1]=[-v/operators[-1] for v in operators[:-1]]
        return dict(schema='pp-binomial-telescoper/1',family=name,recurrence=recurrence,theta_operator=theta,
          shift_certificate=dict(numerator_k_coefficients=[v.packet() for v in p],denominator_k_coefficients=[v.packet() for v in D],k_power=kpower,
            identity='D(k) P(k+1)-k^power P(k)=D(k) L(T)/T',boundary='G(n,0)=G(n,n+2)=0 after factorial cancellation; n>=1'),
          exact_polynomial_identity_checked=True,initial_values=self.terms(size=order+1),module=DifferentialModule.from_matrix(a,name+' period').evidence())
    def elliptic_bridge(self):
        if self.family!='apery2':raise ValueError('elliptic bridge supplied for Apery zeta(2) family')
        from .curve_families import CurveFamily
        curve=CurveFamily({'coefficients':[[0,0,16],[0,8,8],[1,6,1],1]})
        actual=curve.observable();expected=self.telescoper()['module'];module=DifferentialModule({'matrix':expected['connection']});op=module.observable()
        if actual['monic_operator']!=op['monic_operator']:raise AssertionError('binomial/elliptic differential operators differ')
        return dict(schema='pp-apery-elliptic-bridge/1',curve=curve.evidence(),observable=actual,operator_identity_checked=True,
          scope='same rank-two period operator and normalized analytic solution at t=0; no algebraic correspondence with every binomial sum')
