"""Finite cyclic cocycle repair and rational sector reach algebras.

Phases are exact elements of Q/Z, represented by Fractions in [0,1).
The reach theorem assumes the available algebra already contains every matrix
unit inside each declared sector. It does not infer that resource from data.
"""
from fractions import Fraction as Q
from math import prod


def _positive_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(name + " must be a positive integer")
    return value


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(name + " must be an integer")
    return value


def _phase(value):
    return Q(value) % 1


def cyclic_cocycle_phase(n, k, a, b, c):
    """Phase of the standard k class on Z/n, using canonical residues."""
    _positive_integer(n, "n")
    for name, value in (("k", k), ("a", a), ("b", b), ("c", c)):
        _integer(value, name)
    a, b, c = a % n, b % n, c % n
    return Q((k * a * ((b + c) // n)) % n, n)


def cyclic_invariant(n, k, generator=1):
    """Cyclic-product gauge invariant, around the full order of generator."""
    from math import gcd
    _positive_integer(n, "n")
    _integer(generator, "generator")
    generator %= n
    order = n // gcd(n, generator)
    return _phase(sum((cyclic_cocycle_phase(n, k, generator, j*generator,
                                           generator) for j in range(order)), Q(0)))


def extension_cochain_phase(n, k, a, b):
    """Constructive 2-cochain on Z/n² whose coboundary is q*omega_k."""
    _positive_integer(n, "n")
    for name, value in (("k", k), ("a", a), ("b", b)):
        _integer(value, name)
    modulus = n*n
    a, b = a % modulus, b % modulus
    return Q((k * (a % n) * (b // n)) % n, n)


def extension_coboundary_phase(n, k, a, b, c):
    """dB=B(b,c)B(a,b+c)/(B(a+b,c)B(a,b)), in additive phases."""
    return _phase(extension_cochain_phase(n,k,b,c)
                  + extension_cochain_phase(n,k,a,b+c)
                  - extension_cochain_phase(n,k,a+b,c)
                  - extension_cochain_phase(n,k,a,b))


def cyclic_repair(n, k, *, max_triples=1_000_000):
    """Exhaustively replay one repair on the whole finite enlarged group.

    The n^6 budget is checked before enumeration. This does not claim that
    n² is the minimal extension, or solve noncyclic group cohomology.
    """
    _positive_integer(n, "n"); _integer(k, "k")
    _positive_integer(max_triples, "max_triples")
    count = n**6
    if count > max_triples:
        raise ValueError("repair replay needs %d triples; raise max_triples explicitly" % count)
    modulus = n*n
    # Integer exponents modulo n are the same exact Q/Z computation, faster.
    def b(a, c):
        return (k * (a % n) * ((c % modulus) // n)) % n
    for a in range(modulus):
        for c in range(modulus):
            for d in range(modulus):
                actual = (b(c,d)+b(a,c+d)-b(a+c,d)-b(a,c)) % n
                expected = (k * (a % n) * ((c % n + d % n)//n)) % n
                if actual != expected:
                    return {"n":n,"k":k % n,"verified":False,
                            "counterexample":[a,c,d],"triples_checked":None}
    return {"n":n,"k":k % n,"source_group_order":n,
            "receiving_group_order":modulus,
            "source_invariant_phase":str(cyclic_invariant(n,k)),
            "source_class_trivial":k % n == 0,
            "pulled_back_class_trivial":True,"verified":True,
            "triples_checked":count,"arithmetic":"exact integer phases modulo n",
            "scope":"specified cyclic class and Z/n² extension; no minimality claim"}


def rank_one_projector(vector):
    """Orthogonal rational projector onto a nonzero rational vector."""
    vector = list(map(Q, vector))
    denominator = sum(x*x for x in vector)
    if not denominator:
        raise ValueError("nonzero projector vector required")
    return [[x*y/denominator for y in vector] for x in vector]


def _matmul(a, b):
    n = len(a)
    return [[sum(a[i][k]*b[k][j] for k in range(n))
             for j in range(n)] for i in range(n)]


def _reach_inputs(block_sizes, projector, max_dimension):
    block_sizes = list(block_sizes)
    if not block_sizes:
        raise ValueError("at least one sector required")
    for size in block_sizes:
        _positive_integer(size, "sector dimension")
    _positive_integer(max_dimension, "max_dimension")
    n = sum(block_sizes)
    if n > max_dimension:
        raise ValueError("matrix dimension exceeds max_dimension")
    p = [list(map(Q,row)) for row in projector]
    if len(p)!=n or any(len(row)!=n for row in p):
        raise ValueError("projector shape must equal total sector dimension")
    if any(p[i][j]!=p[j][i] for i in range(n) for j in range(n)):
        raise ValueError("a rational self-adjoint projector is required")
    if _matmul(p,p)!=p:
        raise ValueError("matrix is not idempotent")
    blocks, start = [], 0
    for size in block_sizes:
        blocks.append(list(range(start,start+size))); start += size
    return block_sizes,p,blocks


def generated_algebra_dimension(block_sizes, projector, *, max_dimension=10,
                                max_products=50_000):
    """Independent exact matrix-span closure under every supplied generator.

    Generators are all within-sector matrix units and P. Returned dimension
    is computed without using the sector-connectivity dimension formula.
    """
    sizes,p,blocks = _reach_inputs(block_sizes,projector,max_dimension)
    _positive_integer(max_products,"max_products")
    n = sum(sizes)
    generators = []
    for block in blocks:
        for i in block:
            for j in block:
                matrix = [[Q(0) for _ in range(n)] for _ in range(n)]
                matrix[i][j] = Q(1); generators.append(matrix)
    generators.append(p)
    basis, queue = {}, []
    def add(matrix):
        row = [v for values in matrix for v in values]
        for pivot, old in sorted(basis.items()):
            if row[pivot]:
                multiplier = row[pivot]
                row = [x-multiplier*y for x,y in zip(row,old)]
        pivot = next((i for i,x in enumerate(row) if x),None)
        if pivot is None:
            return
        multiplier = row[pivot]; row = [x/multiplier for x in row]
        basis[pivot] = row
        queue.append([row[i*n:(i+1)*n] for i in range(n)])
    for generator in generators:
        add(generator)
    offset, products = 0, 0
    while offset < len(queue):
        matrix = queue[offset]; offset += 1
        for generator in generators:
            products += 1
            if products > max_products:
                raise ValueError("algebra closure exceeded max_products")
            add(_matmul(generator,matrix))
    return len(basis)


def sector_reach(block_sizes, projector, *, verify_algebra=False,
                 max_dimension=64, max_products=50_000):
    """Predict the generated *-algebra from sector graph connectivity.

    Assumption: all End(V_c) are already available as independent blocks.
    A self-adjoint rational P supplies edges exactly where P_cd is nonzero.
    Then the algebra is the sum of full matrices on connected components.
    """
    sizes,p,blocks = _reach_inputs(block_sizes,projector,max_dimension)
    edges = [[c,d] for c in range(len(blocks)) for d in range(c+1,len(blocks))
             if any(p[i][j] for i in blocks[c] for j in blocks[d])]
    adjacent = [set() for _ in blocks]
    for c,d in edges:
        adjacent[c].add(d); adjacent[d].add(c)
    unseen, components = set(range(len(blocks))), []
    while unseen:
        todo = [min(unseen)]; component = set()
        while todo:
            c = todo.pop()
            if c in component:
                continue
            component.add(c); todo.extend(adjacent[c]-component)
        unseen -= component; components.append(sorted(component))
    dimensions = [sum(sizes[c] for c in component) for component in components]
    predicted = sum(d*d for d in dimensions)
    result = {"sector_dimensions":sizes,"sector_edges":edges,
              "components":components,"component_dimensions":dimensions,
              "initial_algebra_dimension":sum(d*d for d in sizes),
              "generated_algebra_dimension":predicted,
              "full_matrix_algebra":len(components)==1,
              "assumption":"available algebra is the full direct sum of within-sector matrix algebras",
              "arithmetic":"exact rational projector and graph"}
    if verify_algebra:
        actual = generated_algebra_dimension(sizes,p,max_dimension=max_dimension,
                                             max_products=max_products)
        result.update(replayed_algebra_dimension=actual,
                      algebra_dimension_matches=actual==predicted)
    return result


def receipt():
    rows = []
    for support in ([0],[0,1,2],list(range(6))):
        p = rank_one_projector([int(i in support) for i in range(6)])
        rows.append(sector_reach([1,2,3],p,verify_algebra=True,max_dimension=6))
    return {"arithmetic":"exact rational phases and matrices",
            "cyclic_repairs":[cyclic_repair(n,1) for n in (2,3,4)],
            "reach_algebras":rows,
            "scope":"finite cyclic extensions and declared rational sector algebras"}
