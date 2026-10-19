"""NX36 independently replayable finite robust decision certificates.

The checker uses only canonical rational arithmetic, finite local dynamic-table
equations, and primitive source/semantic bindings. It imports no proposal
optimizer, protocol compiler, or uncertainty-set optimizer.
"""
from __future__ import annotations
from fractions import Fraction as Q
from math import gcd,lcm
import hashlib
import json

SCHEMA="nx.experiment_decision/1"


def _integer(v):
    if type(v)is not int or v.bit_length()>16384:raise ValueError("bounded exact integer required")
    return v


def _decode(v):
    if type(v)is not list or len(v)!=2:raise ValueError("canonical rational pair required")
    n,d=map(_integer,v)
    if d<=0 or gcd(n,d)!=1:raise ValueError("reduced numerator/positive denominator required")
    return Q(n,d)


def _encode(v):
    if isinstance(v,bool)or not isinstance(v,(int,Q)):raise TypeError("int or Fraction required")
    v=Q(v);return [v.numerator,v.denominator]


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def make_problem(candidate_ids,target_labels,experiment_ids,costs,intervals,*,
                 model_revision,source_bindings,reset="independent-zero-reset",
                 units="model_output",parameter="fixed",catalogue_scope="finite supplied catalogue"):
    ids=list(candidate_ids);labels=list(target_labels);experiments=list(experiment_ids)
    problem={"candidate_ids":ids,"target_labels":labels,"experiment_ids":experiments,
        "costs":[_encode(v)for v in costs],
        "intervals":[[[_encode(a),_encode(b)]for a,b in row]for row in intervals],
        "semantics":{"model_revision":model_revision,"source_bindings":list(source_bindings),
            "reset":reset,"units":units,"parameter":parameter,"order":"chronological",
            "geometry":"independent-scalar-closed-intervals","catalogue_scope":catalogue_scope}}
    _parse_problem(problem)
    return problem


def _parse_problem(p):
    keys={"candidate_ids","target_labels","experiment_ids","costs","intervals","semantics"}
    if type(p)is not dict or set(p)!=keys:raise ValueError("unknown or missing problem semantics")
    ids,labels,experiments=p['candidate_ids'],p['target_labels'],p['experiment_ids']
    if type(ids)is not list or len(ids)<2 or any(type(v)is not str or not v for v in ids)or len(set(ids))!=len(ids):
        raise ValueError("distinct original candidate IDs required")
    if type(labels)is not list or len(labels)!=len(ids)or any(type(v)is not str for v in labels):
        raise ValueError("explicit matching target labels required")
    if type(experiments)is not list or any(type(v)is not str or not v for v in experiments)or len(set(experiments))!=len(experiments):
        raise ValueError("distinct experiment labels required")
    costs=tuple(map(_decode,p['costs']))
    if len(costs)!=len(experiments)or any(c<=0 for c in costs):raise ValueError("one positive cost per experiment required")
    intervals=[]
    if type(p['intervals'])is not list or len(p['intervals'])!=len(experiments):raise ValueError("interval row mismatch")
    for row in p['intervals']:
        if type(row)is not list or len(row)!=len(ids):raise ValueError("candidate interval dimension mismatch")
        parsed=[]
        for item in row:
            if type(item)is not list or len(item)!=2:raise ValueError("interval endpoints required")
            a,b=map(_decode,item)
            if a>b:raise ValueError("ordered interval endpoints required")
            parsed.append((a,b))
        intervals.append(tuple(parsed))
    semantics=p['semantics']
    if type(semantics)is not dict or set(semantics)!={"model_revision","source_bindings","reset","units","parameter","order","geometry","catalogue_scope"}:
        raise ValueError("complete typed semantics required")
    if semantics['geometry']!="independent-scalar-closed-intervals"or semantics['order']!='chronological' or semantics['reset']!='independent-zero-reset':
        raise ValueError("unsupported uncertainty/order/reset semantics")
    for k in ('model_revision','units','parameter','catalogue_scope'):
        if type(semantics[k])is not str or not semantics[k]:raise ValueError("nonempty semantic labels required")
    if type(semantics['source_bindings'])is not list or not semantics['source_bindings']or any(type(v)is not str or not v for v in semantics['source_bindings']):
        raise ValueError("external source premises required")
    pairs=tuple((a,b)for a in range(len(ids))for b in range(a+1,len(ids))if labels[a]!=labels[b])
    masks=tuple(sum(1<<i for i,(a,b)in enumerate(pairs)if row[a][1]<row[b][0]or row[b][1]<row[a][0])for row in intervals)
    return costs,tuple(intervals),pairs,masks


def contrast_gap(left_centre,left_generators,right_centre,right_generators,witness):
    """Rational symmetric-zonotope separating contrast; not an LP oracle."""
    def row(v):return tuple(_decode(x)if type(x)is list else Q(x)if type(x)in(int,Q)else (_ for _ in ()).throw(ValueError("exact contrast entries required"))for x in v)
    a,b,w=map(row,(left_centre,right_centre,witness));ga=tuple(map(row,left_generators));gb=tuple(map(row,right_generators))
    n=len(a)
    if len(b)!=n or len(w)!=n or any(len(g)!=n for g in ga+gb):raise ValueError("contrast dimensions differ")
    dot=lambda x,y:sum((u*v for u,v in zip(x,y)),Q(0))
    return abs(dot(w,tuple(x-y for x,y in zip(a,b))))-sum((abs(dot(w,g))for g in ga+gb),Q(0))


def make_decision_certificate(problem,panel,*,max_states=1000000):
    costs,intervals,pairs,masks=_parse_problem(problem)
    panel=tuple(sorted(panel))
    if len(set(panel))!=len(panel)or any(type(i)is not int or not 0<=i<len(costs)for i in panel):raise ValueError("valid selected subset required")
    full=(1<<len(pairs))-1;covered=0
    for e in panel:covered|=masks[e]
    if covered!=full:raise ValueError("selected panel does not strictly separate every required pair")
    tables=[{0:Q(0)}]
    for cost,mask in zip(costs,masks):
        new=dict(tables[-1])
        for old,value in tables[-1].items():
            key=old|mask
            if key not in new or value+cost<new[key]:new[key]=value+cost
        if len(new)>max_states:raise ValueError("certificate table state budget exhausted")
        tables.append(new)
    selected_cost=sum((costs[e]for e in panel),Q(0))
    if tables[-1].get(full)!=selected_cost:raise ValueError("supplied feasible panel is not catalogue-optimal")
    witnesses=[]
    for p,(a,b)in enumerate(pairs):
        e=next(e for e in panel if masks[e]>>p&1)
        gap=max(intervals[e][b][0]-intervals[e][a][1],intervals[e][a][0]-intervals[e][b][1])
        witnesses.append({"pair":[a,b],"experiment":e,"gap":_encode(gap)})
    denominator=lcm(*(v.denominator for v in costs))if costs else 1
    return {"schema":SCHEMA,"problem":problem,"problem_digest":_hash(problem),"selected_panel":list(panel),
        "selected_cost":_encode(selected_cost),"pair_witnesses":witnesses,
        "optimality":{"method":"complete-prefix-pair-mask-dp","tables":[[[m,_encode(v)]for m,v in sorted(t.items())]for t in tables],
            "positive_common_denominator":denominator,"scaled_costs":[int(v*denominator)for v in costs]},
        "claim":"target identification and optimality within the bound finite catalogue"}


def verify_decision_certificate(certificate,expected_problem,*,max_states=1000000):
    """Pure verifier. External expected_problem prevents stale-domain rebinding."""
    try:
        c=certificate
        if type(c)is not dict or set(c)!={"schema","problem","problem_digest","selected_panel","selected_cost","pair_witnesses","optimality","claim"}or c['schema']!=SCHEMA:
            return False
        if c['claim']!="target identification and optimality within the bound finite catalogue":return False
        if json.dumps(c['problem'],sort_keys=True)!=json.dumps(expected_problem,sort_keys=True)or c['problem_digest']!=_hash(expected_problem):return False
        costs,intervals,pairs,masks=_parse_problem(expected_problem)
        panel=c['selected_panel']
        if type(panel)is not list or panel!=sorted(set(panel))or any(type(i)is not int or not 0<=i<len(costs)for i in panel):return False
        price=sum((costs[e]for e in panel),Q(0))
        if _decode(c['selected_cost'])!=price:return False
        if type(c['pair_witnesses'])is not list or len(c['pair_witnesses'])!=len(pairs):return False
        for (a,b),w in zip(pairs,c['pair_witnesses']):
            if type(w)is not dict or set(w)!={"pair","experiment","gap"}or w['pair']!=[a,b]or type(w['experiment'])is not int or w['experiment']not in panel:return False
            e=w['experiment'];gap=max(intervals[e][b][0]-intervals[e][a][1],intervals[e][a][0]-intervals[e][b][1])
            if gap<=0 or _decode(w['gap'])!=gap:return False
        proof=c['optimality']
        if type(proof)is not dict or set(proof)!={"method","tables","positive_common_denominator","scaled_costs"}or proof['method']!='complete-prefix-pair-mask-dp':return False
        d=_integer(proof['positive_common_denominator'])
        if d<=0 or proof['scaled_costs']!=[int(v*d)for v in costs]or any((v*d).denominator!=1 for v in costs):return False
        if any(type(v)is not int or v<=0 for v in proof['scaled_costs']):return False
        tables=proof['tables']
        if type(tables)is not list or len(tables)!=len(costs)+1:return False
        prior={0:Q(0)}
        for stage,encoded in enumerate(tables):
            if type(encoded)is not list or len(encoded)>max_states:return False
            parsed={}
            for item in encoded:
                if type(item)is not list or len(item)!=2:return False
                mask=_integer(item[0]);value=_decode(item[1])
                if mask<0 or mask>=(1<<len(pairs))or mask in parsed:return False
                parsed[mask]=value
            if parsed!=prior:return False
            if stage<len(costs):
                nxt=dict(prior)
                for mask,value in prior.items():
                    new=mask|masks[stage];v=value+costs[stage]
                    if new not in nxt or v<nxt[new]:nxt[new]=v
                prior=nxt
        return prior.get((1<<len(pairs))-1)==price
    except(ValueError,TypeError,KeyError,IndexError,OverflowError):return False
