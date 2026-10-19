"""Rational enclosures and exact lazy decisions at z=exp(2*pi*i/order).

No floating-point probability decision. Machin's identity, alternating
arctangent bounds, cosine Taylor remainder and its Lipschitz bound provide
the analytic premises. These Python routines are not Lean-certified.
"""
from fractions import Fraction as Q
from functools import lru_cache
from math import factorial
from .divisor_square import WorkLimit


def _outward(lo,hi,bits):
    scale=1<<bits
    return Q((lo*scale).numerator//(lo*scale).denominator,scale),Q(-((-hi*scale).numerator//(-hi*scale).denominator),scale)


@lru_cache(maxsize=32)
def pi_interval(bits=64):
    if type(bits) is not int or not 8 <= bits <= 1024:
        raise ValueError('precision 8 through 1024 bits required')
    tolerance = Q(1, 1 << (bits+8))
    def atan_inverse(n):
        total, power, k = Q(0), Q(1,n), 0
        while True:
            total += (-1)**k * power/(2*k+1)
            power /= n*n; k += 1
            tail = power/(2*k+1)
            if tail < tolerance:
                other = total+(-1)**k*tail
                return min(total,other), max(total,other)
    a,b=atan_inverse(5);c,d=atan_inverse(239)
    return _outward(16*a-4*d,16*b-4*c,bits+8)


@lru_cache(maxsize=4096)
def cosine_interval(order, power, bits=64):
    if type(order) is not int or not 2 <= order <= 64 or type(power) is not int:
        raise ValueError('cyclotomic order 2 through 64 and integer power required')
    lo,hi=pi_interval(bits+8 if bits<=1016 else 1024)
    r=power%order;r=min(r,order-r)
    if not r:return Q(1),Q(1)
    if 2*r==order:return Q(-1),Q(-1)
    if 4*r==order:return Q(0),Q(0)
    lower,upper=2*r*lo/order,2*r*hi/order
    center=(lower+upper)/2;term=Q(1);total=term;n=0
    # Truncate at degree 2*n+1 (whose odd coefficient is zero).
    while True:
        error=upper**(2*n+2)/factorial(2*n+2)+(upper-lower)/2
        if error<Q(1,1<<bits):return _outward(max(Q(-1),total-error),min(Q(1),total+error),bits+4)
        n+=1;term *= -center*center/((2*n-1)*(2*n));total+=term
        if n>1024:raise WorkLimit('cosine remainder budget exceeded')


@lru_cache(maxsize=1024)
def real_interval(element, order, bits=64):
    from .connection_polytope import cyclotomic, ConnectionGraph
    if element.algebra.modulus != cyclotomic(order):
        raise ValueError('element/order mismatch')
    # A real element must equal its algebraic complex conjugate.
    if ConnectionGraph(1,(),order).conjugate(element) != element:
        raise ValueError('real cyclotomic element required')
    lower,upper=Q(0),Q(0)
    for k,c in enumerate(element.coefficients):
        if not c:continue
        lo,hi=cosine_interval(order,k,bits)
        lower+=c*(lo if c>=0 else hi);upper+=c*(hi if c>=0 else lo)
    return _outward(lower,upper,bits+4)


def exact_bernoulli(probability, order, rng, *, bit_limit=512):
    """Compare a lazy uniform dyadic real with an exact algebraic probability.

    A budget failure returns no draw. Accepted decisions have disjoint closed
    comparison intervals, so none depends on rounded approximations.
    """
    if type(bit_limit) is not int or not 1 <= bit_limit <= 512:
        raise ValueError('random bit budget 1 through 512 required')
    coefficients=probability.coefficients
    if not any(coefficients[1:]):
        p=Q(coefficients[0])
        if not 0 <= p <= 1:raise ValueError('probability outside unit interval')
        draw=None if p in (0,1) else rng.randrange(p.denominator)
        if draw is not None and (type(draw) is not int or not 0<=draw<p.denominator):raise ValueError('invalid random draw')
        take=p==1 or (p!=0 and draw<p.numerator)
        return take,dict(kind='rational',probability=str(p),draw=draw,included=take)
    prefix=0;precision=32
    for used in range(1,bit_limit+1):
        bit=rng.randrange(2)
        if type(bit) is not int or bit not in (0,1):raise ValueError('invalid random bit')
        prefix=2*prefix+bit
        if used>=precision//2:precision=min(1024,precision*2)
        p_lo,p_hi=real_interval(probability,order,precision)
        p_lo=max(Q(0),p_lo);p_hi=min(Q(1),p_hi)
        if p_lo>p_hi:raise ValueError('probability outside unit interval')
        u_lo,u_hi=Q(prefix,1<<used),Q(prefix+1,1<<used)
        if u_hi<=p_lo or u_lo>=p_hi:
            take=u_hi<=p_lo
            return take,dict(kind='algebraic',order=order,coefficients=list(map(str,coefficients)),
                random_bits=used,prefix=prefix,precision_bits=precision,
                probability_interval=list(map(str,(p_lo,p_hi))),
                uniform_interval=list(map(str,(u_lo,u_hi))),included=take)
    raise WorkLimit('algebraic probability decision exceeds random-bit budget; no sample returned')


def verify_decision(receipt):
    try:
        if type(receipt['included']) is not bool:return False
        if receipt['kind']=='rational':
            p=Q(receipt['probability']);draw=receipt['draw']
            if not 0<=p<=1:return False
            if p in (0,1):return draw is None and receipt['included']==bool(p)
            return type(draw) is int and 0<=draw<p.denominator and receipt['included']==(draw<p.numerator)
        from .connection_polytope import cyclotomic
        from .quotient_algebra import QuotientAlgebra
        if receipt['kind']!='algebraic':return False
        bits,prefix=receipt['random_bits'],receipt['prefix']
        if type(bits) is not int or not 1<=bits<=512 or type(prefix) is not int or not 0<=prefix<1<<bits:return False
        element=QuotientAlgebra(cyclotomic(receipt['order'])).element(list(map(Q,receipt['coefficients'])))
        lo,hi=real_interval(element,receipt['order'],receipt['precision_bits']);lo=max(Q(0),lo);hi=min(Q(1),hi)
        a,b=Q(prefix,1<<bits),Q(prefix+1,1<<bits)
        return receipt['probability_interval']==list(map(str,(lo,hi))) and receipt['uniform_interval']==list(map(str,(a,b))) and (b<=lo if receipt['included'] else a>=hi)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError):return False
