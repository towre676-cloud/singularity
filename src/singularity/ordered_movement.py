"""Rational level-two path signatures and exact segmentation populations.

These are geometric features with declared channels, not intrinsic ability.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import combinations
from ._application_exact import vector,matrix,dot,rational


@dataclass(frozen=True)
class RationalPath:
    points:tuple
    times:tuple
    channel_units:tuple
    coordinate_frame:str

    def __post_init__(self):
        p=matrix(self.points);t=vector(self.times);u=tuple(self.channel_units)
        if len(p)<2 or len(p)>65 or not 1<=len(u)<=4 or any(len(r)!=len(u) for r in p):raise ValueError("path/channel budget or shape")
        if len(t)!=len(p) or any(a>=b for a,b in zip(t,t[1:])):raise ValueError("strict sampling times required")
        if any(not isinstance(x,str) or not x.strip() for x in u) or not isinstance(self.coordinate_frame,str) or not self.coordinate_frame:raise ValueError("channel units and frame required")
        object.__setattr__(self,"points",p);object.__setattr__(self,"times",t);object.__setattr__(self,"channel_units",u)


@dataclass(frozen=True)
class TruncatedSignature:
    first:tuple
    second:tuple
    channel_units:tuple
    coordinate_frame:str

    def __post_init__(self):
        a,b=vector(self.first),matrix(self.second);u=tuple(self.channel_units)
        if len(a)!=len(u) or len(b)!=len(a) or any(len(r)!=len(a) for r in b):raise ValueError("signature dimension mismatch")
        if not isinstance(self.coordinate_frame,str) or not self.coordinate_frame:raise ValueError("signature coordinate frame required")
        object.__setattr__(self,"first",a);object.__setattr__(self,"second",b)


def signature_level_two(path):
    if not isinstance(path,RationalPath):raise TypeError("RationalPath required")
    d=len(path.channel_units);a=[Q()]*d;b=[[Q()]*d for _ in range(d)]
    for p,q in zip(path.points,path.points[1:]):
        v=tuple(y-x for x,y in zip(p,q))
        for i in range(d):
            for j in range(d):b[i][j]+=v[i]*v[j]/2+a[i]*v[j]
        a=[x+y for x,y in zip(a,v)]
    return TruncatedSignature(tuple(a),tuple(map(tuple,b)),path.channel_units,path.coordinate_frame)


def direct_segment_integral(path):
    """Independent triangular double integral over segment pairs.

    For equal segments the integration triangle has half the square's measure;
    for ordered unequal segments it is a Cartesian product.
    """
    vs=tuple(tuple(b-a for a,b in zip(p,q)) for p,q in zip(path.points,path.points[1:]));d=len(path.channel_units)
    a=tuple(sum((v[i] for v in vs),Q()) for i in range(d))
    b=tuple(tuple(sum((vs[r][i]*vs[s][j]*(Q(1,2) if r==s else Q(1)) for r in range(len(vs)) for s in range(r,len(vs))),Q()) for j in range(d)) for i in range(d))
    return TruncatedSignature(a,b,path.channel_units,path.coordinate_frame)


def chen_compose(x,y):
    if x.channel_units!=y.channel_units or x.coordinate_frame!=y.coordinate_frame:raise ValueError("incompatible channel units or coordinate frames")
    d=len(x.first)
    return TruncatedSignature(tuple(a+b for a,b in zip(x.first,y.first)),tuple(tuple(x.second[i][j]+y.second[i][j]+x.first[i]*y.first[j] for j in range(d)) for i in range(d)),x.channel_units,x.coordinate_frame)


def time_augment(path,time_unit="time"):
    if len(path.channel_units)>=4 or not time_unit:raise ValueError("channel budget or unit")
    return RationalPath(tuple((t,)+p for t,p in zip(path.times,path.points)),path.times,(time_unit,)+path.channel_units,path.coordinate_frame)


def flatten_signature(s):return s.first+tuple(v for r in s.second for v in r)


def signature_population(variants):
    """variants=(original identifier, RationalPath, positive multiplicity)."""
    variants=tuple(variants)
    if len(variants)>1024 or len({v[0] for v in variants})!=len(variants):raise ValueError("population budget or duplicate identity")
    groups={};original=[]
    for identifier,path,multiplicity in variants:
        if type(multiplicity) is not int or multiplicity<=0:raise ValueError("positive integer multiplicity required")
        sig=signature_level_two(path);key=(sig.coordinate_frame,sig.channel_units,flatten_signature(sig))
        original.append((identifier,sig,multiplicity))
        if key not in groups:groups[key]={"signature":sig,"multiplicity":0,"original_ids":[]}
        groups[key]["multiplicity"]+=multiplicity;groups[key]["original_ids"].append(identifier)
    return {"originals":tuple(original),"groups":tuple(groups.values()),"total_multiplicity":sum(v[2] for v in variants),"status":"exact_complete_finite_population"}


def segmentation_population(path,candidate_breakpoints,phases=3):
    cuts=tuple(candidate_breakpoints)
    if len(cuts)>8 or len(set(cuts))!=len(cuts) or type(phases) is not int or not 1<=phases<=3:raise ValueError("segmentation budget")
    if any(type(i) is not int or not 0<i<len(path.points)-1 for i in cuts):raise ValueError("breakpoint must be an interior sample")
    out=[]
    for middle in combinations(sorted(cuts),phases-1):
        boundaries=(0,)+middle+(len(path.points)-1,);sigs=[]
        for a,b in zip(boundaries,boundaries[1:]):
            phase=RationalPath(path.points[a:b+1],path.times[a:b+1],path.channel_units,path.coordinate_frame)
            sigs.append(signature_level_two(phase))
        out.append({"segmentation_id":middle,"multiplicity":1,"phase_signatures":tuple(sigs),"feature":tuple(v for s in sigs for v in flatten_signature(s))})
    if not out:raise ValueError("no admissible segmentations")
    return tuple(out)


def feature_uncertainty(features,weights=None):
    fs=matrix(features)
    if not fs or len(fs)>1024:raise ValueError("finite population required")
    w=(Q(1),)*len(fs) if weights is None else vector(weights)
    if len(w)!=len(fs) or any(v<=0 for v in w):raise ValueError("positive declared weights required")
    total=sum(w,Q());d=len(fs[0])
    return {"ranges":tuple((min(r[j] for r in fs),max(r[j] for r in fs)) for j in range(d)),"distinct_values":len(set(fs)),"weighted_mean":tuple(sum((a*r[j] for a,r in zip(w,fs)),Q())/total for j in range(d)),"weight_semantics":"declared_population_weights_not_biological_probability","independent_box_relaxation":False}


def finite_population_separation(left,right,error_radius=0):
    a,b=matrix(left),matrix(right);e=rational(error_radius)
    if not a or not b or e<0 or len(a[0])!=len(b[0]):raise ValueError("invalid candidate populations")
    distance=min(sum(((x-y)**2 for x,y in zip(r,s)),Q()) for r in a for s in b)
    return {"squared_minimum_distance":distance,"uniform_readout_radius":e,"guaranteed_distinction":distance>4*e*e,"attainable_overlap":bool(set(a)&set(b)),"strict_boundary":True}
