"""Integer lattice stage: Smith form, integer solvability, integer kernels, saturation.

Rational span answers whether a solution exists over Q. These kernels answer the
integer question and return a failing invariant-factor coordinate when it fails.
"""
from fractions import Fraction as Q
from math import gcd
from .exact import rank


def _integer_matrix(a):
    rows=[list(row) for row in a]
    if rows and any(len(row)!=len(rows[0]) for row in rows):raise ValueError("ragged matrix")
    out=[]
    for row in rows:
        new=[]
        for x in row:
            if isinstance(x,Q):
                if x.denominator!=1:raise ValueError("integer entries required")
                x=x.numerator
            if isinstance(x,bool) or not isinstance(x,int):raise ValueError("integer entries required")
            new.append(x)
        out.append(new)
    return out


def _identity(n):
    return [[int(i==j) for j in range(n)] for i in range(n)]


def _mul(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def smith_form(a):
    """Return (U,D,V) with U*A*V=D, U and V unimodular, D diagonal with d1|d2|... and di>0."""
    d=_integer_matrix(a)
    m=len(d);n=len(d[0]) if d else 0
    u,v=_identity(m),_identity(n)

    def swap_rows(i,j):
        d[i],d[j]=d[j],d[i];u[i],u[j]=u[j],u[i]

    def swap_cols(i,j):
        for row in d:row[i],row[j]=row[j],row[i]
        for row in v:row[i],row[j]=row[j],row[i]

    def add_row(src,dst,k):  # row dst += k*row src
        d[dst]=[x+k*y for x,y in zip(d[dst],d[src])];u[dst]=[x+k*y for x,y in zip(u[dst],u[src])]

    def add_col(src,dst,k):
        for row in d:row[dst]+=k*row[src]
        for row in v:row[dst]+=k*row[src]

    t=0
    while t<min(m,n):
        nonzero=[(abs(d[i][j]),i,j) for i in range(t,m) for j in range(t,n) if d[i][j]]
        if not nonzero:break
        _,i,j=min(nonzero);swap_rows(t,i);swap_cols(t,j)
        while True:
            changed=False
            for i in range(t+1,m):
                if d[i][t]:
                    add_row(t,i,-(d[i][t]//d[t][t]))
                    if d[i][t]:swap_rows(t,i);changed=True
            for j in range(t+1,n):
                if d[t][j]:
                    add_col(t,j,-(d[t][j]//d[t][t]))
                    if d[t][j]:swap_cols(t,j);changed=True
            if changed:continue
            bad=next(((i,j) for i in range(t+1,m) for j in range(t+1,n) if d[i][j]%d[t][t]),None)
            if bad is None:break
            add_row(bad[0],t,1)
        if d[t][t]<0:
            d[t]=[-x for x in d[t]];u[t]=[-x for x in u[t]]
        t+=1
    assert _mul(_mul(u,_integer_matrix(a)),v)==d if m and n else True
    return u,d,v


def invariant_factors(a):
    _,d,_=smith_form(a)
    return [d[i][i] for i in range(min(len(d),len(d[0]) if d else 0)) if d[i][i]]


def _determinant(a):
    """Exact integer determinant by fraction elimination."""
    a=[[Q(x) for x in row] for row in a];n=len(a);det=Q(1)
    for c in range(n):
        p=next((i for i in range(c,n) if a[i][c]),None)
        if p is None:return 0
        if p!=c:a[c],a[p]=a[p],a[c];det=-det
        det*=a[c][c]
        for i in range(c+1,n):
            z=a[i][c]/a[c][c];a[i]=[x-z*y for x,y in zip(a[i],a[c])]
    return int(det)


def determinantal_divisors(a,k):
    """gcd of all k-by-k minors; an independent route to d1*...*dk."""
    from itertools import combinations
    a=_integer_matrix(a);g=0
    for rows in combinations(range(len(a)),k):
        for cols in combinations(range(len(a[0])),k):
            g=gcd(g,_determinant([[a[i][j] for j in cols] for i in rows]))
    return g


def integer_solve(a,b):
    """Decide Ax=b over Z. Returns a solution or a certificate of infeasibility.

    The certificate is a rational row y with yA integral and yb not an integer
    (yA=0 and yb nonzero when the system already fails over Q).
    """
    a=_integer_matrix(a);b=_integer_matrix([[x] for x in b])
    if len(b)!=len(a):raise ValueError("right side length differs from row count")
    n=len(a[0]) if a else 0
    u,d,v=smith_form(a);c=[row[0] for row in _mul(u,b)]
    y=[0]*n
    for i,ci in enumerate(c):
        di=d[i][i] if i<n else 0
        if di==0:
            if ci:return {"solvable":False,"rational":False,"coordinate":i,"invariant":0,"residue":ci,
                          "certificate":[Q(x) for x in u[i]],"solution":None}
        elif ci%di:
            return {"solvable":False,"rational":True,"coordinate":i,"invariant":di,"residue":ci%di,
                    "certificate":[Q(x,di) for x in u[i]],"solution":None}
        else:y[i]=ci//di
    x=[sum(v[i][j]*y[j] for j in range(n)) for i in range(n)]
    assert [sum(p*q for p,q in zip(row,x)) for row in a]==[row[0] for row in b]
    return {"solvable":True,"rational":True,"coordinate":None,"invariant":None,"residue":None,
            "certificate":None,"solution":x}


def integer_kernel(a):
    """Z-basis of {x in Z^n : Ax=0}, read from the free columns of V."""
    a=_integer_matrix(a);n=len(a[0]) if a else 0
    _,d,v=smith_form(a)
    r=sum(1 for i in range(min(len(d),n)) if d[i][i])
    return [[v[i][j] for i in range(n)] for j in range(r,n)]


def saturation(generators):
    """Index of the lattice spanned by integer rows inside its rational span intersected with Z^n.

    Index 1 means saturated. Otherwise a primitive witness w is in the rational span,
    w is integral, and w is not an integer combination of the generators.
    """
    g=_integer_matrix(generators)
    if not g:raise ValueError("need at least one generator")
    n=len(g[0]);factors=invariant_factors(g);index=1
    for f in factors:index*=f
    if index==1:return {"rank":len(factors),"index":1,"invariants":factors,"witness":None}
    u,d,v=smith_form(g)
    # Rows of D*V^{-1} = U*G span the same lattice; row i of V^{-1} lies in the saturation.
    vinv=integer_inverse(v)
    i=next(i for i,f in enumerate(factors) if f>1)
    w=vinv[i]
    assert rank(g+[w])==rank(g) and not integer_solve(list(map(list,zip(*g))),w)["solvable"]
    return {"rank":len(factors),"index":index,"invariants":factors,"witness":w}


def integer_inverse(v):
    """Inverse of a unimodular integer matrix."""
    v=_integer_matrix(v);n=len(v)
    aug=[[Q(x) for x in row]+[Q(int(i==j)) for j in range(n)] for i,row in enumerate(v)]
    for c in range(n):
        p=next(i for i in range(c,n) if aug[i][c])
        aug[c],aug[p]=aug[p],aug[c];z=aug[c][c];aug[c]=[x/z for x in aug[c]]
        for i in range(n):
            if i!=c and aug[i][c]:
                z=aug[i][c];aug[i]=[x-z*y for x,y in zip(aug[i],aug[c])]
    out=[[x for x in row[n:]] for row in aug]
    if any(x.denominator!=1 for row in out for x in row):raise ValueError("matrix is not unimodular")
    return [[int(x) for x in row] for row in out]


def lattice_receipt():
    b=[[2,4,4],[-6,6,12],[10,-4,-16]]
    return {"matrix":b,"invariant_factors":invariant_factors(b),
            "rational_but_not_integral":integer_solve([[2,0],[0,3]],[1,3]),
            "integral":integer_solve([[2,0],[0,3]],[4,3]),
            "integer_kernel":integer_kernel([[2,4,6]]),
            "unsaturated":saturation([[2,0],[0,1]]),
            "saturated":saturation([[1,1,0],[0,1,1]])}


def hermite_form(a):
    """Row Hermite normal form H=UA: echelon, positive pivots, entries above each pivot in [0,pivot)."""
    h=_integer_matrix(a);m=len(h);n=len(h[0]) if h else 0
    u=_identity(m);row=0;pivots=[]
    for col in range(n):
        if row==m:break
        while True:
            live=[i for i in range(row,m) if h[i][col]]
            if not live:break
            p=min(live,key=lambda i:abs(h[i][col]))
            h[row],h[p]=h[p],h[row];u[row],u[p]=u[p],u[row]
            done=True
            for i in range(row+1,m):
                q=h[i][col]//h[row][col]
                if q:
                    h[i]=[x-q*y for x,y in zip(h[i],h[row])];u[i]=[x-q*y for x,y in zip(u[i],u[row])]
                if h[i][col]:done=False
            if done:break
        if not any(h[i][col] for i in range(row,m)):continue
        if h[row][col]<0:h[row]=[-x for x in h[row]];u[row]=[-x for x in u[row]]
        for i in range(row):
            q=h[i][col]//h[row][col]
            if q:h[i]=[x-q*y for x,y in zip(h[i],h[row])];u[i]=[x-q*y for x,y in zip(u[i],u[row])]
        pivots.append(col);row+=1
    assert _mul(u,_integer_matrix(a))==h if m and n else True
    return u,h,pivots


def same_lattice(a,b):
    """Row lattices are equal exactly when their nonzero Hermite rows agree."""
    ha,hb=hermite_form(a)[1],hermite_form(b)[1]
    return [r for r in ha if any(r)]==[r for r in hb if any(r)]
