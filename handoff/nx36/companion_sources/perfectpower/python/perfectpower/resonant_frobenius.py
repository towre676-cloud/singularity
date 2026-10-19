"""Exact arbitrary-rank regular-singular normal forms with logarithms.

xY'=(R+E*x/(1-sigma*x))Y. R=D+J, D rational diagonal and J nilpotent
commuting with D. The caller supplies this constant Jordan-frame split;
automatic algebraic eigenframes and irregular singularities are separate.
"""
from fractions import Fraction as Q
from math import ceil
from sympy import Matrix, eye, zeros


def _matrix(a):
    if not a or any(len(row)!=len(a) for row in a):raise ValueError('nonempty square matrix required')
    if any(isinstance(x,float) for row in a for x in row):raise ValueError('exact rational matrices required')
    return Matrix([[Q(x) for x in row] for row in a])


def _packet(a):return [[str(x) for x in row] for row in a.tolist()]

def _max(a):return Q(max(abs(x) for x in a))


def normal_form(R,E,sigma=1,*,exponents=None,order=48):
    R,E=_matrix(R),_matrix(E);r=R.rows
    if E.shape!=R.shape or not 1<=r<=12 or type(order) is not int or not 2<=order<=256:
        raise ValueError('equal dimensions, rank <=12 and order 2..256 required')
    if isinstance(sigma,float):raise ValueError('exact sigma required')
    sigma=Q(sigma)
    d=[Q(R[i,i]) for i in range(r)] if exponents is None else list(map(Q,exponents))
    if len(d)!=r:raise ValueError('one exponent per frame vector required')
    D=Matrix.diag(*d);J=R-D
    if D*J!=J*D or J**r!=zeros(r):raise ValueError('R must be supplied in a rational constant Jordan frame D+J')
    resonances=sorted({int(a-b) for a in d for b in d if a-b>0 and (a-b).denominator==1})
    if resonances and max(resonances)>=order:raise ValueError('order must pass every positive resonance')
    H=[eye(r)];Ns={};events=[]
    for n in range(1,order):
        rhs=E*sigma**(n-1)
        for k in range(1,n):
            rhs+=E*sigma**(k-1)*H[n-k]
            if k in Ns:rhs-=H[n-k]*Ns[k]
        resonant=[(i,j) for i in range(r) for j in range(r) if n-d[i]+d[j]==0]
        N=zeros(r)
        for i,j in resonant:N[i,j]=rhs[i,j]
        remaining=[(i,j) for i in range(r) for j in range(r) if (i,j) not in resonant]
        # L_n(H)=nH-RH+HR; J preserves D-weight blocks.
        columns=[]
        for i,j in remaining:
            B=zeros(r);B[i,j]=1;LB=n*B-R*B+B*R
            if any(LB[a,b] for a,b in resonant):raise ArithmeticError('Jordan operator mixes weight blocks')
            columns.append([LB[a,b] for a,b in remaining])
        hn=zeros(r)
        if remaining:
            L=Matrix(len(remaining),len(remaining),lambda i,j:columns[j][i])
            vector=L.inv()*Matrix([rhs[i,j] for i,j in remaining])
            for (i,j),v in zip(remaining,vector):hn[i,j]=v
        if n*hn-R*hn+hn*R+N!=rhs:raise ArithmeticError('normal-form recurrence failed')
        if N!=zeros(r):Ns[n]=N
        if resonant:events.append(dict(order=n,positions=[list(x) for x in resonant],obstruction=_packet(N)))
        H.append(hn)
    N=J+sum(Ns.values(),zeros(r))
    if N**r!=zeros(r):raise ArithmeticError('normal-form logarithmic exponent not nilpotent')
    # Independent coefficient replay of xH'=AH-HB.
    for n in range(order):
        lhs=n*H[n];rhs=R*H[n]-H[n]*R
        for k in range(1,n+1):
            rhs+=E*sigma**(k-1)*H[n-k]
            if k in Ns:rhs-=H[n-k]*Ns[k]
        if lhs!=rhs:raise ArithmeticError('gauge identity failed')
    powers=[eye(r)]
    for k in range(1,r):powers.append(powers[-1]*N/k)
    degree=max(k for k,p in enumerate(powers) if p!=zeros(r))
    return dict(schema='pp-resonant-frobenius/1',rank=r,order=order,R=_packet(R),E=_packet(E),sigma=str(sigma),
        exponents=list(map(str,d)),gauge_coefficients=[_packet(h) for h in H],
        normal_form_terms={str(n):_packet(v) for n,v in Ns.items()},logarithmic_exponent=_packet(N),
        logarithm_polynomial=[_packet(p) for p in powers[:degree+1]],logarithm_degree=degree,
        resonance_events=events,coefficient_identity_checked=True,
        solution='Y(x)=H(x) x^D exp(N log(x))',
        monodromy='exp(2 pi i D) exp(2 pi i N); these factors commute because resonance gaps are integers',
        scope='Regular-singular rational Jordan-frame systems; finite exact coefficients with a separate analytic tail bound')


def gauge_tail(chart,radius,*,growth=None):
    """Exact geometric majorant of the analytic gauge tail, in max-entry norm.

    It bounds H, not x^D or its logarithmic factors. An invertible evaluation
    still requires a determinant enclosure at the requested endpoint.
    """
    x=Q(radius);r=chart['rank'];q=abs(Q(chart['sigma']))
    s=q+1 if growth is None else Q(growth)
    if not (x>0 and s>q and s*x<1):raise ValueError('positive radius and growth with q<s<1/radius required')
    R=_matrix(chart['R']);E=_matrix(chart['E'])
    Ns={int(n):_matrix(v) for n,v in chart['normal_form_terms'].items()}
    bound=Q(r)*_max(E)/(s-q)+sum(Q(r)*_max(v)/s**n for n,v in Ns.items())
    cutoff=max([0,*Ns])+1
    cutoff=max(cutoff,ceil(2*r*_max(R)+bound))
    H=[_matrix(h) for h in chart['gauge_coefficients']];order=len(H)
    if order<=cutoff:raise ValueError(f'order must exceed majorant cutoff {cutoff}')
    M=max(_max(h)/s**n for n,h in enumerate(H))
    tail=M*(s*x)**order/(1-s*x)
    return dict(radius=str(x),growth=str(s),cutoff=cutoff,coefficient_majorant=str(M),tail_max_entry=str(tail),
                bound_certified=True,argument='For n>cutoff, the Sylvester inverse is bounded by 1/(n-2 rank max|R|); induction gives max|H_n|<=M growth^n')
