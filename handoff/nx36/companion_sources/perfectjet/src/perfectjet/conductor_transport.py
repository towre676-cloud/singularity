"""Exact finite conductor transport, coupled-lattice theta, and torus skein.

Fourier operators are unnormalized: F_N[j,k]=zeta_N**(j*k). This keeps
all computations in cyclotomic quotient rings. The usual unitary formulas
follow by dividing F_N by sqrt(N), which is stated rather than approximated.
"""
from fractions import Fraction as Q
from itertools import product
from math import comb, gcd
from .rings import Element, QuotientRing, cyclotomic


def _integer(value, name, positive=False):
    if isinstance(value,bool) or not isinstance(value,int) or (positive and value<1):
        raise ValueError(name + (" must be a positive integer" if positive else " must be an integer"))
    return value


class FiniteFourier:
    """Usable exact Fourier/chirp operators at one finite conductor."""
    def __init__(self, conductor, *, max_conductor=128):
        _integer(conductor,"conductor",True); _integer(max_conductor,"max_conductor",True)
        if conductor>max_conductor:
            raise ValueError("conductor exceeds max_conductor")
        self.conductor=conductor
        self.ring=QuotientRing(cyclotomic(conductor))
        self.zeta=self.ring.generator
        self.powers=[self.zeta**j for j in range(conductor)]

    def _vector(self, values):
        values=list(values)
        if len(values)!=self.conductor:
            raise ValueError("vector length must equal conductor")
        return [self.ring.one.coerce(x) for x in values]

    def fourier(self, values, *, twist=1):
        _integer(twist,"twist")
        values=self._vector(values); n=self.conductor
        return [sum((self.powers[twist*j*k % n]*v for k,v in enumerate(values)),self.ring.zero)
                for j in range(n)]

    def chirp(self, values, *, power=1):
        _integer(power,"power")
        return [self.powers[power*j*j % self.conductor]*v
                for j,v in enumerate(self._vector(values))]


class ConductorTransport:
    """The two exact degeneracy maps for lower | upper."""
    def __init__(self, lower, upper, *, max_conductor=128):
        _integer(lower,"lower",True); _integer(upper,"upper",True)
        if upper % lower:
            raise ValueError("lower conductor must divide upper conductor")
        self.lower=FiniteFourier(lower,max_conductor=max_conductor)
        self.upper=FiniteFourier(upper,max_conductor=max_conductor)
        self.factor=upper//lower

    def lift(self, element):
        """Embed Q(zeta_lower) into Q(zeta_upper), zeta_lower=zeta_upper^d."""
        element=self.lower.ring.one.coerce(element)
        return sum((coefficient*self.upper.powers[self.factor*j % self.upper.conductor]
                    for j,coefficient in enumerate(element.coefficients)),self.upper.ring.zero)

    def embed_support(self, values):
        values=self.lower._vector(values)
        out=[self.upper.ring.zero for _ in range(self.upper.conductor)]
        for j,value in enumerate(values):
            out[self.factor*j]=self.lift(value)
        return out

    def pullback(self, values):
        values=[self.lift(v) for v in self.lower._vector(values)]
        return [values[j % self.lower.conductor] for j in range(self.upper.conductor)]

    def replay(self, *, max_entries=100_000):
        _integer(max_entries,"max_entries",True)
        l,m=self.lower.conductor,self.upper.conductor
        if 3*l*m>max_entries:
            raise ValueError("transport replay exceeds max_entries")
        first,second,chirp=True,True,True
        for k in range(l):
            vector=[int(j==k) for j in range(l)]
            low_fourier=self.lower.fourier(vector)
            first &= self.upper.fourier(self.embed_support(vector))==self.pullback(low_fourier)
            second &= self.upper.fourier(self.pullback(vector))==[
                self.factor*v for v in self.embed_support(low_fourier)]
            chirp &= self.upper.chirp(self.embed_support(vector))==self.embed_support(
                self.lower.chirp(vector,power=self.factor))
        return {"lower":l,"upper":m,"factor":self.factor,
                "fourier_support_to_pullback":bool(first),
                "fourier_pullback_to_support":bool(second),
                "chirp_transport":bool(chirp),"entries_checked":3*l*m,
                "normalization":"F_N is unnormalized; F_M iota=pi* F_L, F_M pi*=d iota F_L",
                "unitary_normalization":"S_M iota=d^(-1/2) pi* S_L; S_M pi*=d^(1/2) iota S_L",
                "arithmetic":"exact cyclotomic quotient rings"}


def crt_permutation(left, right):
    """Product index (a,b) -> right*a+left*b mod left*right; twists matter."""
    _integer(left,"left",True); _integer(right,"right",True)
    if gcd(left,right)!=1:
        raise ValueError("CRT conductor factors must be coprime")
    return [(right*a+left*b) % (left*right)
            for a in range(left) for b in range(right)]


def crt_factorization(left, right, *, max_conductor=128, max_entries=100_000):
    """Replay twisted Fourier and chirp tensor factorizations entrywise."""
    permutation=crt_permutation(left,right); n=left*right
    _integer(max_entries,"max_entries",True)
    if n*n+n>max_entries:
        raise ValueError("CRT replay exceeds max_entries")
    space=FiniteFourier(n,max_conductor=max_conductor)
    pairs=list(product(range(left),range(right)))
    fourier,chirp=True,True
    for i,(a,b) in enumerate(pairs):
        j=permutation[i]
        chirp &= space.powers[j*j % n]==space.powers[(right*right*a*a+left*left*b*b) % n]
        for k,(c,d) in enumerate(pairs):
            fourier &= space.powers[j*permutation[k] % n]==space.powers[
                (right*right*a*c+left*left*b*d) % n]
    return {"left":left,"right":right,"conductor":n,
            "permutation":permutation,"left_twist":right,"right_twist":left,
            "fourier_factorization":bool(fourier),"chirp_factorization":bool(chirp),
            "entries_checked":n*n+n,"arithmetic":"exact cyclotomic quotient rings",
            "scope":"coprime CRT factors, with both Fourier and chirp twists retained"}


def type_a_cartan(rank):
    _integer(rank,"rank",True)
    if rank>32:
        raise ValueError("rank exceeds supported construction limit 32")
    return [[2 if i==j else -1 if abs(i-j)==1 else 0
             for j in range(rank)] for i in range(rank)]


def _even_lattice(matrix):
    matrix=[list(row) for row in matrix]
    rank=len(matrix)
    if not rank or any(len(row)!=rank for row in matrix):
        raise ValueError("nonempty square lattice matrix required")
    for row in matrix:
        for value in row:
            _integer(value,"lattice entry")
    if any(matrix[i][i] % 2 for i in range(rank)):
        raise ValueError("even diagonal required for an integral quadratic form")
    if any(matrix[i][j]!=matrix[j][i] for i in range(rank) for j in range(rank)):
        raise ValueError("symmetric lattice matrix required")
    return matrix


class FiniteLatticeTheta:
    """Finite numerator, boundary reciprocity, and remote-index coefficients.

    C is symmetric integral with even diagonal, Q(a)=a^T C a/2.
    Positive definiteness is not needed for this root-of-unity formal-series
    identity. No modularity or analytic continuation assertion is made.
    """
    def __init__(self, matrix, conductor, *, max_terms=250_000, max_conductor=128):
        self.matrix=_even_lattice(matrix)
        self.rank=len(self.matrix)
        self.space=FiniteFourier(conductor,max_conductor=max_conductor)
        self.conductor=conductor; self.ring=self.space.ring
        _integer(max_terms,"max_terms",True)
        if conductor**self.rank>max_terms:
            raise ValueError("finite lattice residue population exceeds max_terms")
        self.residue_terms=conductor**self.rank
        self.degree=self.rank*(conductor-1)
        self.boundary=[sum(row) for row in self.matrix]
        self.numerator=[self.ring.zero for _ in range(self.degree+1)]
        self.twisted_numerator=[self.ring.zero for _ in range(self.degree+1)]
        for residue in product(range(conductor),repeat=self.rank):
            q=self.quadratic(residue); grade=sum(residue)
            self.numerator[grade]+=self.space.powers[q % conductor]
            twist=sum(s*a for s,a in zip(self.boundary,residue))
            self.twisted_numerator[grade]+=self.space.powers[(q+twist) % conductor]

    def quadratic(self, vector):
        vector=list(vector)
        if len(vector)!=self.rank:
            raise ValueError("lattice vector dimension mismatch")
        for value in vector:
            _integer(value,"lattice coordinate")
        return (sum(self.matrix[i][i]*vector[i]*vector[i]//2 for i in range(self.rank))
                +sum(self.matrix[i][j]*vector[i]*vector[j]
                     for i in range(self.rank) for j in range(i+1,self.rank)))

    def coefficient(self, index):
        """Coefficient of N(x)/(1-x^L)^rank, including arbitrarily remote n."""
        _integer(index,"index")
        if index<0:
            return self.ring.zero
        return sum((value*comb((index-grade)//self.conductor+self.rank-1,self.rank-1)
                    for grade,value in enumerate(self.numerator)
                    if grade<=index and (index-grade) % self.conductor==0),self.ring.zero)

    def direct_coefficient(self, index, *, max_terms=250_000):
        """Independent sum over all weak compositions of index."""
        _integer(index,"index"); _integer(max_terms,"max_terms",True)
        if index<0:
            return self.ring.zero
        if comb(index+self.rank-1,self.rank-1)>max_terms:
            raise ValueError("direct coefficient population exceeds max_terms")
        def compositions(total,count,prefix=()):
            if count==1:
                yield prefix+(total,)
            else:
                for a in range(total+1):
                    yield from compositions(total-a,count-1,prefix+(a,))
        return sum((self.space.powers[self.quadratic(v) % self.conductor]
                    for v in compositions(index,self.rank)),self.ring.zero)

    def reciprocity(self):
        phase=self.space.powers[self.quadratic([self.conductor-1]*self.rank) % self.conductor]
        return all(self.numerator[self.degree-k]==phase*self.twisted_numerator[k]
                   for k in range(self.degree+1))

    def record(self, *, direct_through=12, remote_index=10**100):
        _integer(direct_through,"direct_through")
        if direct_through<0:
            raise ValueError("direct_through must be nonnegative")
        return {"matrix":self.matrix,"conductor":self.conductor,"rank":self.rank,
                "residue_terms":self.residue_terms,"numerator_degree":self.degree,
                "numerator":[v.record() for v in self.numerator],
                "boundary_character":self.boundary,"reciprocity":self.reciprocity(),
                "direct_coefficients_match":all(self.coefficient(n)==self.direct_coefficient(n)
                                                 for n in range(direct_through+1)),
                "direct_through":direct_through,"remote_index":str(remote_index),
                "remote_coefficient":self.coefficient(remote_index).record(),
                "denominator":"(1-x^%d)^%d" % (self.conductor,self.rank),
                "arithmetic":"exact cyclotomic quotient rings"}


def _curve(curve):
    values=list(curve)
    if len(values)!=2:
        raise ValueError("torus curve must have two integer coordinates")
    p,q=values; _integer(p,"p"); _integer(q,"q")
    return (-p,-q) if p<0 or (p==0 and q<0) else (p,q)


class TorusSkein:
    """Frohman-Gelca torus basis e_(p,q)=e_(-p,-q), A=zeta_(2L).

    Coefficients are cyclotomic. The basis is not silently reduced modulo L;
    centrality is not the same as imposing a finite matrix quotient.
    """
    def __init__(self, conductor, *, max_conductor=128):
        _integer(conductor,"conductor",True)
        self.conductor=conductor
        self.space=FiniteFourier(2*conductor,max_conductor=2*max_conductor)
        self.ring=self.space.ring

    def basis_product(self, left, right):
        p,q=_curve(left); r,s=_curve(right); d=p*s-q*r
        out={}
        for curve,exponent in (((p+r,q+s),d),((p-r,q-s),-d)):
            key=_curve(curve)
            out[key]=out.get(key,self.ring.zero)+self.space.powers[exponent % (2*self.conductor)]
        return {key:value for key,value in out.items() if value!=0}

    def multiply(self, left, right):
        """Multiply sparse linear combinations {curve: coefficient}."""
        out={}
        for curve,a in left.items():
            for other,b in right.items():
                for key,value in self.basis_product(curve,other).items():
                    out[key]=out.get(key,self.ring.zero)+value*a*b
        return {key:value for key,value in out.items() if value!=0}

    def commutator(self, left, right):
        out=self.basis_product(left,right)
        for key,value in self.basis_product(right,left).items():
            out[key]=out.get(key,self.ring.zero)-value
        return {key:value for key,value in out.items() if value!=0}

    def central_basis_curve(self, curve):
        p,q=_curve(curve)
        return p % self.conductor==0 and q % self.conductor==0


def half_lift_parity(coroot_sum, conductor):
    """Integer-height sign criterion only, not a complete quantum-dimension fan.

    For even L, sigma_(L+1) acts on an integer-height sine product of weight
    lambda by (-1)^<lambda,2rho^vee>. The supplied coroot_sum is 2rho^vee
    in the simple-coroot basis. No root normalization is inferred.
    """
    _integer(conductor,"conductor",True)
    if conductor % 2:
        raise ValueError("the half-lift units involution requires even conductor")
    coroot_sum=list(coroot_sum)
    if not coroot_sum:
        raise ValueError("nonempty coroot-sum vector required")
    for value in coroot_sum:
        _integer(value,"coroot coordinate")
    return {"conductor":conductor,"galois_unit":conductor+1,
            "coroot_sum":coroot_sum,
            "fundamental_weight_signs":[-1 if v % 2 else 1 for v in coroot_sum],
            "half_lift_blind":all(v % 2==0 for v in coroot_sum),
            "scope":"integer-height sine-product sign criterion; no full fan classification"}


def receipt():
    skein=TorusSkein(5)
    return {"transport":[ConductorTransport(2,6).replay(),ConductorTransport(3,9).replay()],
            "crt":crt_factorization(3,4),
            "theta":FiniteLatticeTheta(type_a_cartan(2),3).record(),
            "skein":{"conductor":5,"noncommuting_pair":bool(skein.commutator((1,0),(0,1))),
                     "central_multiple_commutes":not skein.commutator((5,0),(0,1)),
                     "basis_is_not_reduced_modulo_conductor":True},
            "half_lift":[half_lift_parity([2,2],6),half_lift_parity([3,4,3],6)],
            "arithmetic":"exact cyclotomic quotient rings and integer parities"}
