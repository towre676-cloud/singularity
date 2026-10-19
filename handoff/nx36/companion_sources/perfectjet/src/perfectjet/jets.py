"""Rational finite jets, Riccati rejection residuals, and reflection obstruction."""
from fractions import Fraction as Q


def multiply(a,b,order):
    out=[Q(0)]*(order+1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            if i+j<=order:out[i+j]+=Q(x)*Q(y)
    return out


def compose(a,b,order):
    out=[Q(0)]*(order+1);power=[Q(1)]+[Q(0)]*order
    for c in a:
        out=[x+Q(c)*y for x,y in zip(out,power)]
        power=multiply(power,b,order)
    return out


def iterate_defect(coefficients,order):
    if len(coefficients)<2 or Q(coefficients[0])!=0 or Q(coefficients[1])!=-1:
        raise ValueError("a centered flip germ is required")
    out=compose(coefficients,coefficients,order)
    out[1]-=1
    return out


def riccati_residual(coefficients,a,b,c):
    coeff=list(map(Q,coefficients));a,b,c=Q(a),Q(b),Q(c)
    return [(n+1)*coeff[n+1]-a*int(n==0)-b*coeff[n]
            -c*sum((coeff[j]*coeff[n-j] for j in range(n+1)),Q(0))
            for n in range(len(coeff)-1)]


def floating_transfer_predictions(ka,kb,kc=None):
    """Historical heuristics ONLY: these are not general IEEE-754 prefix guarantees."""
    result={"ADD":min(ka,kb),"MUL":max(0,ka+kb-53),"DIV":max(0,ka-kb),"SQRT":max(0,ka-1)}
    if kc is not None:result["FMA"]=min(result["MUL"],kc)
    return {"status":"historical restricted-semantics heuristic","predictions":result}
