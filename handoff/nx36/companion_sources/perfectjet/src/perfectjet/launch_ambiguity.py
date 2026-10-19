"""Exact C2 launch-time ambiguity, even with a known common starting position.

Two nonnegative-velocity, nonnegative-acceleration histories launch at -1 and -2,
respectively, and agree in position and their first two derivatives from t=0 on.
The proof is for the declared piecewise-polynomial class, not arbitrary physical
force constraints. It explains why a rolling readout need not identify a launch.
"""
from fractions import Fraction as Q

# Polynomials in normalized progress z in [0,1]. Physical duration is 1 or 2.
PATHS = {
    'late': {'launch':Q(-1),'duration':Q(1),
             'position':[Q(-5,12),Q(0),Q(0),Q(2,3),Q(-1,4)]},
    'early':{'launch':Q(-2),'duration':Q(2),
             'position':[Q(-5,12)]+[Q(0)]*6+[Q(1),Q(-1,4),Q(-1,3)]}}
TAIL = [Q(0),Q(1),Q(1,2)]


def derivative(p):
    return [i*p[i] for i in range(1,len(p))]


def evaluate(p,t):
    return sum(c*t**i for i,c in enumerate(p))


def state(which,t,order=0):
    if which not in PATHS or order not in (0,1,2):raise ValueError('unknown path or derivative')
    t=Q(t);r=PATHS[which]
    if t<r['launch']:return Q(-5,12) if order==0 else Q(0)
    if t>=0:
        p=TAIL
        for _ in range(order):p=derivative(p)
        return evaluate(p,t)
    p=r['position']
    for _ in range(order):p=derivative(p)
    return evaluate(p,(t-r['launch'])/r['duration'])/r['duration']**order


def ambiguity_receipt():
    boundary={}
    for name,r in PATHS.items():
        p=r['position'];jets=[]
        for k in range(3):
            jets.append((evaluate(p,Q(0))/r['duration']**k,
                         evaluate(p,Q(1))/r['duration']**k));p=derivative(p)
        if jets!=[(Q(-5,12),Q(0)),(Q(0),Q(1)),(Q(0),Q(1))]:
            raise AssertionError('piecewise C2 boundary matching failed')
        boundary[name]={'launch_time':str(r['launch']),
            'start_jet':[str(v[0]) for v in jets],'end_jet':[str(v[1]) for v in jets]}
    return {'schema':'perfectjet/launch-ambiguity/1','verified_boundary_jets':boundary,
        'common_observed_tail':'x(t)=t+t^2/2 for t>=0',
        'common_starting_position':'-5/12',
        'late_velocity':'z^2(2-z)', 'late_acceleration':'z(4-3z)',
        'early_velocity':'z^6(7-2z-3z^2)/2',
        'early_acceleration':'z^5(21-7z-12z^2)/2',
        'positivity_argument':'For 0<=z<=1, 2-z>=1, 4-3z>=1, 7-2z-3z^2>=2, and 21-7z-12z^2>=2.',
        'conclusion':'Launch time is not identifiable from the observed tail, even with the common starting position, C2 regularity, nonnegative speed and nonnegative acceleration.',
        'scope':'exact rational piecewise-polynomial witness; not a universal impossibility under stronger global motion assumptions'}
