"""Corrected scalar PSG flip reduction. Root calculation is floating numerical evidence."""
from math import acos,exp,expm1,sqrt,log


def quantities(L):
    if L<=0:raise ValueError("positive L required")
    x=acos(exp(-L));T=sqrt(expm1(2*L));U=x*x+L*L;H=x+L*T;A=x*H/(2*U)
    return {"L":L,"x":x,"T":T,"U":U,"H":H,"A":A,"F":log(U)+4*A*log(x)}


def flip_root(lo=.3,hi=.8,steps=80):
    if quantities(lo)["F"]*quantities(hi)["F"]>=0:raise ValueError("sign-changing bracket required")
    sign=quantities(lo)["F"]
    for _ in range(steps):
        mid=(lo+hi)/2;value=quantities(mid)["F"]
        if value*sign>0:lo=mid
        else:hi=mid
    q=quantities((lo+hi)/2);alpha=1/(2*q["A"]);K=q["U"]**(-alpha/2)
    q.update(alpha=alpha,fixed_residual=K-q["x"],multiplier=-alpha*q["H"]/q["U"]*K,
             status="floating numerical replay; not interval certification or uniqueness proof")
    return q
