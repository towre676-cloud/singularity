"""Exact real nodal-endpoint enclosures for K(m), with m the parameter k^2.

Uses the convergent complementary-modulus expansion DLMF 19.12.1/3.
This analytic identification and the Python interpreter are not proved in Lean.
At m=1 the ordinary period diverges; only its specified finite part is returned.
"""
from fractions import Fraction as Q
from math import comb
from .elliptic_arithmetic import q
from .analytic_cert import logI,logOK
from .elliptic_certificate_verifier import CheckBudget


def _interval(lo,hi):return [str(lo),str(hi)]


def endpoint_packet(complement,terms=32,bits=128,log_terms=96):
    z=q(complement,512)
    if not 0<=z<=Q(1,4):raise ValueError('real complementary parameter in [0,1/4] required')
    for value,lo,hi in ((terms,1,128),(bits,16,512),(log_terms,4,256)):
        if type(value) is not int or not lo<=value<=hi:raise ValueError('endpoint control out of range')
    if not logOK(bits,(Q(2),Q(2))):raise ValueError('logarithm side conditions')
    l2=logI(bits,log_terms,(Q(2),Q(2)));finite_part=(2*l2[0],2*l2[1])
    result=dict(schema='pp-real-legendre-endpoint/1',complement=str(z),terms=terms,
        bits=bits,log_terms=log_terms,parameter=str(1-z),normalization='K(m)=integral_0^(pi/2) (1-m sin(t)^2)^(-1/2) dt',
        log_coefficient='-1/2',finite_part=_interval(*finite_part),ordinary_endpoint_finite=False,
        endpoint_regularization='K(1-z)+(1/2) log(z) tends to log(4)',
        analytic_identity='DLMF 19.12.1 and 19.12.3, real positive complementary modulus',
        execution_verified=False,lean_endpoint_identity_verified=False)
    if not z:
        result.update(method='regularized_endpoint',coefficients=[],log_complement=None,
                      period_interval=None,regularized_interval=_interval(*finite_part),tail_upper_bound='0')
        return result
    if not logOK(bits,(z,z)):raise ValueError('logarithm side conditions')
    lz=logI(bits,log_terms,(z,z));L=(-lz[1]/2,-lz[0]/2)
    lower=upper=Q(0);S=Q(0);rows=[]
    # d_n=2 log(2)-2(H_(2n)-H_n), and a_n=binom(2n,n)^2/16^n.
    for n in range(terms):
        a=Q(comb(2*n,n)**2,16**n);delta=sum((Q(1,j) for j in range(n+1,2*n+1)),Q(0))
        w=a*z**n;S+=w
        lower+=w*(L[0]+2*l2[0]-2*delta)
        upper+=w*(L[1]+2*l2[1]-2*delta)
        rows.append(dict(index=n,coefficient=str(a),harmonic_difference=str(delta)))
    # 0<a_n<=1 and 0<d_n<=2log(2)<2; the omitted tail is positive.
    tail=z**terms*(L[1]+2)/(1-z)
    # Recompute the regularized expression with the shared logarithm cancelled.
    correction=sum((Q(row['coefficient'])*z**row['index']*2*Q(row['harmonic_difference']) for row in rows),Q(0))
    reglo=L[0]*(S-1)+2*l2[0]*S-correction
    reghi=L[1]*(S-1)+2*l2[1]*S-correction+tail
    result.update(method='convergent_log_series',coefficients=rows,log_complement=_interval(*lz),
        period_interval=_interval(lower,upper+tail),regularized_interval=_interval(reglo,reghi),
        tail_upper_bound=str(tail))
    CheckBudget(2000000).packet(result)
    return result


def verify_endpoint(cert,*,work_limit=2000000):
    try:
        budget=CheckBudget(work_limit);budget.packet(cert)
        if type(cert) is not dict:return False
        if (cert.get('execution_verified') is not False or cert.get('lean_endpoint_identity_verified') is not False
            or cert.get('ordinary_endpoint_finite') is not False):return False
        expected=endpoint_packet(cert['complement'],cert['terms'],cert['bits'],cert['log_terms'])
        # Typed preflight rejects bool-as-int through endpoint controls and exact keys.
        return cert==expected and all(type(row.get('index')) is int for row in cert['coefficients'])
    except (ValueError,TypeError,KeyError,ArithmeticError):return False
