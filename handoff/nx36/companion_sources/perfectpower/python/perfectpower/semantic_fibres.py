"""Exact finite implementation families and three distinct transport semirings.

All completeness claims are relative to the supplied finite carrier. Original
identities survive semantic projection; target valuation happens after legality.
"""
from copy import deepcopy
from fractions import Fraction as Q
from hashlib import sha256
import json
from .divisor_square import WorkLimit
from .psg_polynomial import parse, rational


def canonical(value):
    def visit(x):
        if type(x) in (str,int,bool) or x is None:return
        if type(x) is list:
            for v in x:visit(v)
            return
        if type(x) is dict and all(type(k) is str for k in x):
            for v in x.values():visit(v)
            return
        raise ValueError('exact JSON labels required; no floats or arbitrary objects')
    visit(value)
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def identity(schema,value):return sha256((schema+'\n'+canonical(value)).encode()).hexdigest()


class ImplementationFamily:
    def __init__(self,specification):
        spec=deepcopy(specification)
        if set(spec)!={'variables','semantics','rows'}:raise ValueError('variables, semantics, rows required')
        if not 0<=len(spec['rows'])<=4096:raise WorkLimit('at most 4096 supplied implementations required')
        self.variables=tuple(spec['variables']);self.outputs=tuple(parse(s,self.variables) for s in spec['semantics'])
        if not 1<=len(self.outputs)<=16:raise ValueError('one through sixteen semantic outputs required')
        self.rows=[];seen=set()
        for r in spec['rows']:
            if set(r)-{'id','values','weight'} or not {'id','values'}<=set(r):raise ValueError('invalid implementation row')
            if type(r['id']) is not str or not r['id'] or r['id'] in seen:raise ValueError('distinct nonempty implementation IDs required')
            seen.add(r['id']);values=tuple(map(rational,r['values']))
            if len(values)!=len(self.variables):raise ValueError('coordinate dimension mismatch')
            weight=rational(r.get('weight',1))
            if weight<0:raise ValueError('negative implementation weight')
            self.rows.append((r['id'],values,weight,tuple(p.evaluate(values) for p in self.outputs)))
        self.rows.sort(key=lambda r:r[0]);self._spec=canonical(spec);self.family_id=identity('pp-implementation-family/1',spec)

    @property
    def specification(self):return json.loads(self._spec)

    @classmethod
    def from_population(cls,population,semantics,*,row_limit=4096):
        count=population.count()
        if type(row_limit) is not int or not 1<=row_limit<=4096 or not 0<=count<=row_limit:raise WorkLimit('population materialization budget exceeded')
        records=[population.select(i) for i in range(count)]
        # Existing population ranks retain original parameter/point identities.
        if population.specification['kind']=='domain':
            variables=tuple(population.specification['fields'])
            rows=[{'id':str(r['parameter']),'values':[r['values'][v] for v in variables]} for r in records]
        else:
            variables=('x','y');rows=[{'id':canonical(r['values']),'values':[r['values'][v] for v in variables]} for r in records]
        return cls({'variables':list(variables),'semantics':semantics,'rows':rows})

    def query(self,*,semantic_value=None,constraints=(),objectives=(),work_limit=2_000_000):
        if type(work_limit) is not int or not 1<=work_limit<=10_000_000:raise ValueError('bounded work limit required')
        if len(constraints)>32 or len(objectives)>8:raise WorkLimit('query expression budget exceeded')
        conditions=[]
        for c in constraints:
            if set(c)!={'expression','relation','value'} or c['relation'] not in ('eq','le','ge'):raise ValueError('invalid legal constraint')
            conditions.append((parse(c['expression'],self.variables),c['relation'],rational(c['value'])))
        costs=tuple(parse(s,self.variables) for s in objectives)
        target=None if semantic_value is None else tuple(map(rational,semantic_value))
        if target is not None and len(target)!=len(self.outputs):raise ValueError('semantic output dimension mismatch')
        rows=[]
        for id,values,w,outputs in self.rows:
            if target is not None and outputs!=target:continue
            ok=True
            for p,relation,value in conditions:
                lhs=p.evaluate(values)
                if not {'eq':lhs==value,'le':lhs<=value,'ge':lhs>=value}[relation]:ok=False;break
            if ok:rows.append((id,values,w,outputs,tuple(p.evaluate(values) for p in costs)))
        front=[];work=0
        for r in rows:
            dominated=False
            if costs:
                for s in rows:
                    work+=1
                    if work>work_limit:raise WorkLimit('Pareto comparison budget exceeded')
                    if all(a<=b for a,b in zip(s[4],r[4])) and any(a<b for a,b in zip(s[4],r[4])):dominated=True;break
            if not dominated:front.append(r[0])
        groups={}
        for id,values,w,outputs,cost in rows:
            key=tuple(map(str,outputs));g=groups.setdefault(key,{'ids':[],'mass':Q(0)})
            g['ids'].append(id);g['mass']=rational(g['mass']+w)
        fibres=[{'semantic_value':list(k),'ids':v['ids'],'count':len(v['ids']),'mass':str(v['mass'])} for k,v in sorted(groups.items())]
        return {'schema':'pp-implementation-query/1','family_id':self.family_id,
                'scope':'complete within supplied finite carrier; no global implementation-space claim',
                'count':len(rows),'mass':str(rational(sum((r[2] for r in rows),Q(0)))),
                'fibres':fibres,'pareto_ids':front,'rows':[{'id':r[0],'values':list(map(str,r[1])),
                    'weight':str(r[2]),'semantics':list(map(str,r[3])),'costs':list(map(str,r[4]))} for r in rows],
                'minimum':None if len(costs)!=1 or not rows else str(min(r[4][0] for r in rows)),
                'valuation':list(objectives),'legality':deepcopy(list(constraints))}


class Transport:
    """Finite typed sparse relations over N, Q>=0 or the min-plus semiring.

Mass composition sums products, count composition counts path multiplicity,
min-plus composition finds cheapest fixed-length paths. None merges identities.
"""
    MODES=('count','mass','minplus')
    def __init__(self,source,target,entries,*,mode='count'):
        self.source=tuple(source);self.target=tuple(target);self.mode=mode
        if mode not in self.MODES:raise ValueError('unknown transport semiring')
        for labels in (self.source,self.target):
            if not 0<=len(labels)<=4096 or len(set(labels))!=len(labels) or any(type(s) is not str or not s for s in labels):raise ValueError('bounded distinct carrier IDs required')
        self._entries={}
        if len(entries)>100000:raise WorkLimit('transport edge budget exceeded')
        for i,j,value in entries:
            if i not in self.source or j not in self.target:raise ValueError('edge outside typed carrier')
            v=self.value(value)
            if not self.nonzero(v):continue
            self._entries[i,j]=self.add(self._entries.get((i,j),self.zero),v)
        self.transport_id=identity('pp-semiring-transport/1',self.packet())

    @property
    def zero(self):return None if self.mode=='minplus' else Q(0)
    def nonzero(self,v):return v is not None if self.mode=='minplus' else bool(v)
    def value(self,v):
        if v is None and self.mode=='minplus':return None
        q=rational(v)
        if self.mode=='count' and (q.denominator!=1 or q<0):raise ValueError('natural path multiplicities required')
        if self.mode=='mass' and q<0:raise ValueError('nonnegative transport mass required')
        return q
    def add(self,a,b):
        if self.mode!='minplus':return rational(a+b)
        return b if a is None else a if b is None else min(a,b)
    def multiply(self,a,b):
        if self.mode!='minplus':return rational(a*b)
        return None if a is None or b is None else rational(a+b)
    def packet(self):
        return {'source':list(self.source),'target':list(self.target),'mode':self.mode,
                'entries':[[i,j,str(v)] for (i,j),v in sorted(self._entries.items())]}
    @classmethod
    def from_packet(cls,p):
        if set(p)!={'source','target','mode','entries'}:raise ValueError('invalid transport packet')
        return cls(p['source'],p['target'],p['entries'],mode=p['mode'])
    def compose(self,other,*,work_limit=2_000_000):
        if self.target!=other.source or self.mode!=other.mode:raise ValueError('transport carriers or semirings do not match')
        if type(work_limit) is not int or not 1<=work_limit<=10_000_000:raise ValueError('bounded composition work required')
        right={};out={};work=0
        for (j,k),v in other._entries.items():right.setdefault(j,[]).append((k,v))
        for (i,j),a in self._entries.items():
            for k,b in right.get(j,[]):
                work+=1
                if work>work_limit:raise WorkLimit('transport composition budget exceeded')
                out[i,k]=self.add(out.get((i,k),self.zero),self.multiply(a,b))
                if len(out)>100000:raise WorkLimit('composed transport edge budget exceeded')
        return Transport(self.source,other.target,[(i,k,v) for (i,k),v in out.items()],mode=self.mode)
    def apply(self,values,*,backward=False):
        domain=self.target if backward else self.source;codomain=self.source if backward else self.target
        if set(values)!=set(domain):raise ValueError('complete input carrier values required')
        values={k:self.value(v) for k,v in values.items()};out={k:self.zero for k in codomain}
        for (i,j),v in self._entries.items():
            a,b=(j,i) if backward else (i,j)
            out[b]=self.add(out[b],self.multiply(values[a],v))
        return {k:None if v is None else str(v) for k,v in out.items()}
    def mass_preserving(self):
        if self.mode!='mass':raise ValueError('mass preservation is a Q>=0 statement')
        totals={i:Q(0) for i in self.source}
        for (i,j),v in self._entries.items():totals[i]=rational(totals[i]+v)
        return {'preserving':all(v==1 for v in totals.values()),'row_sums':{i:str(v) for i,v in totals.items()}}


def projection_transport(family,*,mode='count'):
    if mode not in ('count','mass'):raise ValueError('semantic projection uses count or mass')
    labels={r[0]:canonical(list(map(str,r[3]))) for r in family.rows}
    return Transport(tuple(r[0] for r in family.rows),tuple(sorted(set(labels.values()))),[(i,j,1) for i,j in labels.items()],mode=mode)


def check_composition(packet,left,right):
    """Independent dense coefficient replay, bound to caller-supplied arrows."""
    candidate=Transport.from_packet(packet)
    if candidate.source!=left.source or candidate.target!=right.target or candidate.mode!=left.mode or left.target!=right.source or left.mode!=right.mode:raise ValueError('composition binding mismatch')
    work=len(left.source)*len(left.target)*len(right.target)
    if work>2_000_000:raise WorkLimit('dense replay budget exceeded')
    expected={}
    for i in left.source:
        for k in right.target:
            v=left.zero
            for j in left.target:v=left.add(v,left.multiply(left._entries.get((i,j),left.zero),right._entries.get((j,k),right.zero)))
            if left.nonzero(v):expected[i,k]=v
    if candidate._entries!=expected:raise ValueError('transport composition identity failed')
    return True


def polynomial_chart(variables,forward,inverse,source_outputs,target_outputs):
    """Exact reversible polynomial chart and semantic/Jacobian transport.

Rational polynomial inverse identities are global. Integral lattice equivalence
is asserted only when both coordinate maps have integer coefficients.
"""
    variables=tuple(variables);n=len(variables)
    if len(forward)!=n or len(inverse)!=n or not 1<=len(source_outputs)==len(target_outputs)<=16:raise ValueError('chart dimensions mismatch')
    phi=tuple(parse(s,variables) for s in forward);psi=tuple(parse(s,variables) for s in inverse)
    source=tuple(parse(s,variables) for s in source_outputs);target=tuple(parse(s,variables) for s in target_outputs)
    replacements=dict(zip(variables,phi));back=dict(zip(variables,psi));prototype=phi[0]
    for i,v in enumerate(variables):
        if phi[i].substitute(back)!=prototype.variable(v) or psi[i].substitute(replacements)!=prototype.variable(v):raise ValueError('coordinate maps are not mutual polynomial inverses')
    pulled=tuple(p.substitute(replacements) for p in target)
    if pulled!=source:raise ValueError('global semantic transport identity failed')
    jacobian=[[p.derivative(v) for v in variables] for p in phi]
    chain=[]
    for p,q in zip(source,target):
        row=[]
        for j,v in enumerate(variables):
            rhs=sum((q.derivative(w).substitute(replacements)*jacobian[k][j] for k,w in enumerate(variables)),prototype.constant(0))
            if rhs!=p.derivative(v):raise ArithmeticError('polynomial chain rule replay failed')
            row.append(rhs.packet())
        chain.append(row)
    integral=all(c.denominator==1 for p in phi+psi for e,c in p._terms)
    return {'schema':'pp-polynomial-chart/1','variables':list(variables),'forward':[p.packet() for p in phi],
            'inverse':[p.packet() for p in psi],'source_outputs':[p.packet() for p in source],
            'target_outputs':[p.packet() for p in target],'jacobian':[[p.packet() for p in row] for row in jacobian],
            'transported_output_jacobian':chain,'integer_lattice_equivalence':integral,
            'scope':'global rational polynomial automorphism and output/derivative identities; integer equivalence requires both maps integral'}
