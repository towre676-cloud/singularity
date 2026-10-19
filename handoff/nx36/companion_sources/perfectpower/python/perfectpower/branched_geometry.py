"""Exact topology and faithful cyclic connections for y^d=P(x).

Riemann-Hurwitz numbers use root multiplicities computed by Yun decomposition.
Cell complexes model the resulting topological type; no intrinsic Voronoi
coordinates, period matrix, smooth metric or new integer-height bound is claimed.
"""
from fractions import Fraction as Q
from functools import lru_cache
from math import gcd,isqrt
from . import polyalg as P
from .core import mul,power
from .divisor_sum import exact_root
from .quotient_algebra import QuotientAlgebra
from .exact_linear import rank,multiply,transpose


def profile(coefficients,d):
    if type(d) is not int or not 2<=d<=64:raise ValueError('degree must be 2 through 64')
    f=P.poly(coefficients)
    if P.is_zero(f) or any(c.denominator!=1 for c in f):raise ValueError('nonzero integer polynomial required')
    lead,parts=P.squarefree_decomposition(f)
    if P.expand_decomposition(lead,parts)!=f:raise AssertionError('decomposition replay failed')
    roots=[r for r,part in sorted(parts.items()) for _ in range(P.degree(part))]
    components=d
    for r in roots:components=gcd(components,r)
    cover=d//components;reduced=[r//components for r in roots]
    degree=sum(reduced)
    finite=sum(cover-gcd(cover,r) for r in reduced)
    infinity=cover-gcd(cover,degree)
    chi=2*cover-finite-infinity
    if chi>2 or (2-chi)%2:raise AssertionError('invalid component Euler characteristic')
    genus=(2-chi)//2
    content=0
    for c in f:content=gcd(content,abs(int(c)))
    if lead<0:content=-content
    all_divisible=all(r%d==0 for r in roots)
    scalar_root=exact_root(abs(content),d)
    signed_root=None if scalar_root is None or (content<0 and d%2==0) else (-scalar_root if content<0 else scalar_root)
    integer_root=None
    if all_divisible and signed_root is not None:
        lead_root=exact_root(abs(int(lead)),d)
        if lead_root is None:raise AssertionError('content criterion failed leading-root replay')
        candidate=P.poly([-lead_root if lead<0 else lead_root])
        for r,part in parts.items():candidate=mul(candidate,power(part,r//d))
        if any(z.denominator!=1 for z in candidate) or power(candidate,d)!=f:
            raise AssertionError('integer-root replay failed')
        integer_root=list(map(int,candidate))
    return {'coefficients':list(map(int,f)),'power':d,
      'multiplicity_blocks':[{'multiplicity':r,'distinct_roots':P.degree(part),
                              'monic_factor':list(map(str,part))} for r,part in sorted(parts.items())],
      'root_multiplicities':roots,'degree':P.degree(f),'components':components,
      'component_cover_degree':cover,'finite_ramification_per_component':finite,
      'infinity_ramification_per_component':infinity,'points_at_infinity_per_component':gcd(cover,degree),
      'genus_per_component':genus,'euler_per_component':chi,'euler_total':components*chi,
      'betti':[components,2*components*genus,components],
      'total_curvature_over_pi':2*components*chi,'trivalent_face_charge':6*components*chi,
      'complex_polynomial_power':all_divisible,'signed_content':content,
      'content_is_integer_power':signed_root is not None,'integer_polynomial_root':integer_root,
      'holonomic_operator':{'derivative_coefficient':list(map(int,P.scale(f,d))),
                            'zeroth_coefficient':list(map(int,P.scale(P.derivative(f),-1)))},
      'execution_verified':False,'scope':'exact arithmetic and classical normalized-cover formulas'}


@lru_cache(None)
def cyclotomic(d):
    if type(d) is not int or d<1:raise ValueError('positive cyclotomic index required')
    polynomial=P.poly([-1]+[0]*(d-1)+[1])
    for k in range(1,d):
        if d%k==0:polynomial=P.exact_div(polynomial,cyclotomic(k))
    return polynomial


def cycle_graph(labels,d):
    """Root-detecting bouquet; positive cycle 0->right->left->0 has label r."""
    if type(d) is not int or not 2<=d<=64:raise ValueError('power must be 2 through 64')
    if any(type(r) is not int for r in labels):raise ValueError('integer cycle labels required')
    edges=[]
    for i,r in enumerate(labels):
        a,b=2*i+1,2*i+2
        edges.extend([(0,a,0),(a,b,0),(0,b,r%d)])
    return 2*len(labels)+1,edges


def transport_certificate(vertices,edges,d):
    """Spanning-tree potentials and exact cycle residuals modulo d."""
    if type(vertices) is not int or vertices<1 or type(d) is not int or d<2:raise ValueError('invalid dimensions')
    adjacency=[[] for _ in range(vertices)]
    for i,(a,b,r) in enumerate(edges):
        if any(type(x) is not int for x in (a,b,r)) or not 0<=a<vertices or not 0<=b<vertices:
            raise ValueError('invalid voltage edge')
        adjacency[a].append((b,r%d,i));adjacency[b].append((a,-r%d,i))
    potentials=[None]*vertices;potentials[0]=0;queue=[0];tree=[]
    for a in queue:
        for b,r,i in adjacency[a]:
            if potentials[b] is None:
                potentials[b]=(potentials[a]+r)%d;queue.append(b);tree.append(i)
    if len(queue)!=vertices:raise ValueError('connected base graph required')
    residuals=[(potentials[a]+r-potentials[b])%d for a,b,r in edges]
    components=d
    for r in residuals:components=gcd(components,r)
    return {'potentials':potentials,'tree_edges':tree,'cycle_residuals':residuals,
            'faithful_character_kernel_dimension':int(all(r==0 for r in residuals)),
            'lift_components':components,'execution_verified':False}


def _block_matrix(matrix,field):
    n=len(matrix);h=field.degree
    out=[[Q(0) for _ in range(n*h)] for _ in range(n*h)]
    for i,row in enumerate(matrix):
        for j,z in enumerate(row):
            block=z.matrix()
            for a in range(h):
                for b in range(h):out[i*h+a][j*h+b]=block[a][b]
    return out


def faithful_laplacian(labels,d):
    """Exact cyclotomic connection matrix and kernel over its rational basis.

    The standard cyclotomic construction is used; quotient_algebra's generic
    irreducibility flag is not upgraded into a Lean field certificate.
    """
    if d>12 or len(labels)>12:raise ValueError('exact matrix work limit exceeded')
    n,edges=cycle_graph(labels,d);field=QuotientAlgebra(cyclotomic(d));zeta=field.element([0,1])
    if zeta**d!=field.element(1):raise AssertionError('root-of-unity identity failed')
    matrix=[[field.element(0) for _ in range(n)] for _ in range(n)]
    for a,b,r in edges:
        # Residual f_b-zeta^r f_a; its Hermitian Gram contribution.
        matrix[a][a]=matrix[a][a]+1;matrix[b][b]=matrix[b][b]+1
        matrix[a][b]=matrix[a][b]-(zeta**((-r)%d))
        matrix[b][a]=matrix[b][a]-(zeta**(r%d))
    block=_block_matrix(matrix,field)
    rational_nullity=n*field.degree-rank(block)
    expected=field.degree*int(all(r%d==0 for r in labels))
    if rational_nullity!=expected:raise AssertionError('spectral/holonomy mismatch')
    return {'vertices':n,'edges':[list(e) for e in edges],
            'cyclotomic_modulus':list(map(str,field.modulus)),
            'matrix':[[list(map(str,z.coefficients)) for z in row] for row in matrix],
            'rational_block_dimension':n*field.degree,'rational_nullity':rational_nullity,
            'character_kernel_dimension':rational_nullity//field.degree,
            'transport':transport_certificate(n,edges,d),'execution_verified':False,
            'scope':'exact faithful character matrix; no numerical eigenvalue criterion'}


def lift_components(vertices,edges,d):
    """Independent explicit d-sheet graph enumeration for validation."""
    if vertices*d>10000:raise ValueError('lift enumeration work limit exceeded')
    adjacency=[[] for _ in range(vertices*d)]
    for a,b,r in edges:
        for sheet in range(d):
            u=a*d+sheet;v=b*d+(sheet+r)%d
            adjacency[u].append(v);adjacency[v].append(u)
    seen=set();components=[]
    for v in range(vertices*d):
        if v in seen:continue
        queue=[v];seen.add(v)
        for u in queue:
            for w in adjacency[u]:
                if w not in seen:seen.add(w);queue.append(w)
        components.append(queue)
    return components


def cell_surface(genus):
    """Closed oriented delta-complex of genus g, with exact Hodge matrices.

    g=0 uses an octahedron. Higher genus uses a fan triangulation of the
    standard commutator polygon, retaining loops and multiple edges.
    Its trivalent dual is combinatorial, not a measured Voronoi diagram.
    """
    if type(genus) is not int or not 0<=genus<=20:raise ValueError('genus must be 0 through 20')
    if genus==0:
        triangles=[]
        for i in range(4):
            a,b=2+i,2+(i+1)%4
            triangles.extend([(0,a,b),(1,b,a)])
        edge_pairs=sorted({tuple(sorted((t[i],t[(i+1)%3]))) for t in triangles for i in range(3)})
        index={e:i for i,e in enumerate(edge_pairs)};signed=[]
        for t in triangles:
            signed.append([(index[tuple(sorted((a,b)))],1 if a<b else -1)
                           for a,b in zip(t,t[1:]+t[:1])])
        vertices=6;edges=len(edge_pairs)
        b1=[[0]*edges for _ in range(vertices)]
        for j,(a,b) in enumerate(edge_pairs):b1[a][j]=-1;b1[b][j]=1
        dual_face_sizes=[4]*6
    else:
        word=[]
        for h in range(genus):word.extend([(2*h,1),(2*h+1,1),(2*h,-1),(2*h+1,-1)])
        diagonals={j:(2*genus+j-2,1) for j in range(2,4*genus-1)}
        diagonals[1]=word[0];diagonals[4*genus-1]=(word[-1][0],-word[-1][1])
        signed=[]
        for j in range(1,4*genus-1):
            edge,sign=diagonals[j+1]
            signed.append([diagonals[j],word[j],(edge,-sign)])
        vertices=1;edges=6*genus-3;b1=[[0]*edges]
        dual_face_sizes=[3*len(signed)]
    faces=len(signed);b2=[[0]*faces for _ in range(edges)]
    occurrences=[[] for _ in range(edges)]
    for j,triangle in enumerate(signed):
        for e,sign in triangle:b2[e][j]+=sign;occurrences[e].append(sign)
    if any(sorted(signs)!=[-1,1] for signs in occurrences):raise AssertionError('closed orientation failed')
    if any(any(row) for row in multiply(b1,b2)):raise AssertionError('boundary squared nonzero')
    l0=multiply(b1,transpose(b1));l2=multiply(transpose(b2),b2)
    first=multiply(transpose(b1),b1);second=multiply(b2,transpose(b2))
    l1=[[x+y for x,y in zip(a,b)] for a,b in zip(first,second)]
    nullities=[vertices-rank(l0),edges-rank(l1),faces-rank(l2)]
    if nullities!=[1,2*genus,1]:raise AssertionError('Hodge dimensions failed')
    dual_edges=[]
    for edge in range(edges):
        owners=[(j,sign) for j,triangle in enumerate(signed) for e,sign in triangle if e==edge]
        dual_edges.append([next(j for j,s in owners if s==1),next(j for j,s in owners if s==-1)])
    degrees=[0]*faces
    for a,b in dual_edges:degrees[a]+=1;degrees[b]+=1
    if degrees!=[3]*faces:raise AssertionError('dual trivalence failed')
    chi=vertices-edges+faces;charge=sum(6-q for q in dual_face_sizes)
    if charge!=6*chi or chi!=2-2*genus:raise AssertionError('Gauss-Bonnet face charge failed')
    return {'genus':genus,'vertices':vertices,'edges':edges,'faces':faces,
            'oriented_triangles':signed,'boundary1':b1,'boundary2':b2,
            'hodge0':l0,'hodge1':l1,'hodge2':l2,'harmonic_dimensions':nullities,
            'euler':chi,'curvature_over_pi':2*chi,'dual_face_sizes':dual_face_sizes,
            'dual_face_charge':charge,'dual_edges':dual_edges,
            'lipschitz_killing':{'L0':chi,'L1':0,'L2_over_sqrt3':str(Q(faces,4))},
            'execution_verified':False,
            'scope':'canonical topological polyhedral model; not the original conformal metric or an intrinsic Voronoi computation'}
