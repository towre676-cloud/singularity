"""NX34 rational complex-domain bounds and improved connected-graph discs.

All comparisons use rational directed enclosures.  Polynomial zero counts and
zero-free lower bounds are deliberately separate records.  The graph span
estimate upgrades the retained *local* disc; no global continuation follows.
"""
from fractions import Fraction as Q
from math import comb
from .period_observations import _q


def combinatorial_tail(vertices, cutoff, radius):
    if type(vertices)is not int or vertices<1 or type(cutoff)is not int or cutoff<0:
        raise ValueError("positive order and nonnegative cutoff required")
    r=_q(radius)
    if not 0<=r<1:raise ValueError("radius must lie in [0,1)")
    return (1-r)**(-vertices)-sum((comb(n+vertices-1,vertices-1)*r**n
                                           for n in range(cutoff+1)),Q(0))


def _complex(v):
    if isinstance(v,(tuple,list)):
        if len(v)!=2:raise ValueError("complex pair required")
        return tuple(map(_q,v))
    return _q(v),Q(0)


def _add(z,w):return z[0]+w[0],z[1]+w[1]
def _mul(z,w):return z[0]*w[0]-z[1]*w[1],z[0]*w[1]+z[1]*w[0]
def _abs_upper(z):return abs(z[0])+abs(z[1])


def _taylor(poly,centre):
    result=[]
    for k in range(len(poly)):
        total=(Q(0),Q(0))
        for j in range(k,len(poly)):
            power=(Q(1),Q(0))
            for _ in range(j-k):power=_mul(power,centre)
            value=_mul(poly[j],power)
            total=_add(total,(comb(j,k)*value[0],comb(j,k)*value[1]))
        result.append(total)
    return tuple(result)


def polynomial_disc_lower_bound(coefficients,centre,radius):
    poly=tuple(map(_complex,coefficients));centre=_complex(centre);r=_q(radius)
    if not poly or r<0:raise ValueError("polynomial and nonnegative radius required")
    local=_taylor(poly,centre)
    return max(abs(local[0][0]),abs(local[0][1]))-sum(
        (_abs_upper(v)*r**k for k,v in enumerate(local)if k),Q(0))


def polynomial_rectangle_certificate(coefficients,rectangle,*,tail=0,max_depth=8):
    """Cover a rational rectangle by boxes, each enclosed by an L1 disc."""
    x0,x1,y0,y1=map(_q,rectangle);tail=_q(tail)
    if not x0<x1 or not y0<y1 or tail<0 or type(max_depth)is not int or max_depth<0:
        raise ValueError("ordered rectangle, nonnegative tail/depth required")
    queue=[((x0,x1,y0,y1),0)];leaves=[]
    while queue:
        box,depth=queue.pop();a,b,c,d=box
        centre=((a+b)/2,(c+d)/2);radius=(b-a+d-c)/2
        lower=polynomial_disc_lower_bound(coefficients,centre,radius)
        if lower>tail:leaves.append((box,lower));continue
        if depth>=max_depth:
            return {"zero_free":False,"zero_count":None,"reason":"lower-bound work limit",
                    "unresolved_box":box,"leaves":tuple(leaves)}
        m,n=(a+b)/2,(c+d)/2
        queue.extend(((sub,depth+1)for sub in ((a,m,c,n),(m,b,c,n),(a,m,n,d),(m,b,n,d))))
    return {"zero_free":True,"zero_count":0,"tail":tail,"leaves":tuple(leaves),
            "scope":"whole rectangle lower bound, including the supplied analytic tail"}


def factored_polynomial_zero_count(coefficients,roots,centre,radius):
    """Exact count for a supplied complete rational-complex factorization."""
    poly=tuple(map(_complex,coefficients));roots=tuple(map(_complex,roots))
    centre=_complex(centre);radius=_q(radius)
    if not poly or poly[-1]==(Q(0),Q(0)) or len(poly)!=len(roots)+1 or radius<=0:
        raise ValueError("complete factorization and positive disc radius required")
    replay=[poly[-1]]
    for root in roots:
        out=[(Q(0),Q(0))for _ in range(len(replay)+1)]
        for j,v in enumerate(replay):
            out[j]=_add(out[j],_mul(v,(-root[0],-root[1])))
            out[j+1]=_add(out[j+1],v)
        replay=out
    if tuple(replay)!=poly:raise ValueError("factorization identity does not replay")
    count=0
    for root in roots:
        d=(root[0]-centre[0])**2+(root[1]-centre[1])**2
        if d==radius**2:raise ValueError("root on boundary")
        count+=d<radius**2
    return {"zero_count":count,"zero_free":count==0,
            "method":"complete exact rational-complex factorization"}


def root_interval(value,degree,bits=64):
    value=_q(value)
    if value<0 or type(degree)is not int or degree<1 or type(bits)is not int or bits<1:
        raise ValueError("nonnegative radicand and positive degree/bits required")
    a,b=Q(0),max(Q(1),value)
    for _ in range(bits):
        m=(a+b)/2
        if m**degree<=value:a=m
        else:b=m
    return a,b


def log_interval(integer,terms=96):
    if type(integer)is not int or integer<1 or type(terms)is not int or terms<1:
        raise ValueError("positive integer and series budget required")
    t=Q(integer-1,integer+1)
    lower=2*sum((t**(2*k+1)/(2*k+1)for k in range(terms)),Q(0))
    return lower,lower+2*t**(2*terms+1)/((2*terms+1)*(1-t*t))


def prime_image_disc(prime,depth,eta):
    """Enclose exp(-s log p), |s-1/depth|<=eta, without floating point."""
    eta=_q(eta)
    if type(prime)is not int or prime<2 or type(depth)is not int or depth<1 or eta<0:
        raise ValueError("valid prime/depth/radius required")
    lo,hi=root_interval(Q(1,prime),depth);_,loghi=log_interval(prime)
    a=eta*loghi
    if a>=1:raise ValueError("exponential enclosure requires eta log(p)<1")
    return {"prime":prime,"centre":(lo+hi)/2,
            "radius":(hi-lo)/2+hi*a/(1-a),"log_interval":log_interval(prime),
            "rounding":"exact rational outward bounds; exp(a)-1<=a/(1-a)"}


def graph_diameter(graph):
    if not graph.connected or graph.n<2:raise ValueError("connected order at least two required")
    diameter=0
    for start in range(graph.n):
        seen={start:0};queue=[start]
        for v in queue:
            for w in graph.neighbors[v]:
                if w not in seen:seen[w]=seen[v]+1;queue.append(w)
        diameter=max(diameter,max(seen.values()))
    return diameter


def span_derivative_majorant(graph,q,x,cutoff=16):
    """Bound L'(x) via B=(1-x^n)L and Gaussian span counting.

    N_n(h) counts the box profiles with minimum zero and maximum h. Every
    such profile has E>=ceil(h^2/diam), and volume in [h,(n-1)h].
    """
    q,x=_q(q),_q(x);n=graph.n;d=graph_diameter(graph)
    if not 0<q<1 or not 0<x<1 or type(cutoff)is not int or cutoff<1:
        raise ValueError("q,x in (0,1), positive cutoff required")
    b=Q(1);bp=Q(0)
    for h in range(1,cutoff+1):
        count=(h+1)**n-2*h**n+(h-1)**n
        weight=q**((h*h+d-1)//d)
        b+=count*x**h*weight
        bp+=count*(n-1)*h*x**(h-1)*weight
    h=cutoff+1
    first=n*(n-1)*(h+1)**(n-2)*x**h*q**((h*h+d-1)//d)
    ratio=Q(h+2,h+1)**(n-2)*x*q**((2*h+1)//d)
    derivative_ratio=ratio*Q(h+1,h)
    if derivative_ratio>=1:raise ValueError("Gaussian tail ratio not contractive; increase cutoff")
    b+=first/(1-ratio)
    bp+=(n-1)*h*first/x/(1-derivative_ratio)
    derivative=bp/(1-x**n)+n*x**(n-1)*b/(1-x**n)**2
    return {"B_upper":b,"Bprime_upper":bp,"Lprime_upper":derivative,
            "tail_ratio":ratio,"derivative_tail_ratio":derivative_ratio,
            "diameter":d,"span_cutoff":cutoff}


def improved_visibility_certificate(left,right,q,depth,eta):
    from .heights import local_coefficients
    from .polynomials import evaluate
    from .arithmetic import normalized_ratio_tail_constant
    q,eta=_q(q),_q(eta);n=left.n
    if right.n!=n or type(depth)is not int or depth<1 or eta<=0:
        raise ValueError("same-order graphs, positive depth/radius required")
    lc,rc=local_coefficients(left,depth),local_coefficients(right,depth)
    differences=[evaluate(a,q)-evaluate(b,q)for a,b in zip(lc,rc)]
    first=next((i for i,v in enumerate(differences)if v),None)
    if first!=depth:raise ValueError("declared first discrepancy does not recompute")
    delta=differences[depth];sigma=Q(1,depth)-eta
    if (depth+1)*sigma<=1 or depth*eta>Q(1,4):
        raise ValueError("holomorphic-tail or regularized-zeta disc hypothesis fails")
    # 2^-sigma <= 2^(-1/r)(1+eta), since exp(eta log 2)<=1+eta for eta<=1.
    _,root=root_interval(Q(1,2),depth)
    x=root*(1+eta)
    bounds=tuple(span_derivative_majorant(g,q,x)for g in (left,right))
    perturbation=eta*max(b['Lprime_upper']for b in bounds)/(Q(27,10)*sigma)
    if perturbation>=1:raise ValueError("local right-half-plane bound fails")
    rho=Q(1,2*n+2)
    return {"schema":"singularity.improved-complex-visibility/1","q":q,"depth":depth,
            "delta":delta,"center":Q(1,depth),"radius":eta,"sigma":sigma,
            "local_real_part_lower":1-perturbation,"span_bounds":bounds,
            "local_radius_rho":rho,
            "schwarz_constant":normalized_ratio_tail_constant(n,depth,delta,rho),
            "prime_cutoff":int((1/rho)**(depth+1))+1,
            "small_prime_images":tuple(prime_image_disc(p,depth,eta)for p in (2,3,5)),
            "branches":"principal local logarithms; regularized zeta; cut for (r*s-1)^(-delta)",
            "scope":"same SNG-F35 local domain with graph-dependent derivative majorant; no global continuation"}
