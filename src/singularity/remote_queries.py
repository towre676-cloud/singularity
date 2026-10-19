"""Source-bound exact rational response queries, optional DynaComp integration."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
import hashlib
import json
from .dynacomp_adapter import exact, bundled_adapter


def _encode(x):
    if isinstance(x, Q): return [x.numerator, x.denominator]
    if isinstance(x, (tuple, list)): return [_encode(v) for v in x]
    if isinstance(x, dict): return {k:_encode(v) for k,v in x.items()}
    return x


def _hash(x):
    return hashlib.sha256(json.dumps(_encode(x), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _matrix(A):
    A = tuple(tuple(exact(x) for x in row) for row in A)
    if not A or len(A) > 128 or any(len(row) != len(A) for row in A):
        raise ValueError('square matrix with dimension 1..128 required')
    return A


@dataclass(frozen=True)
class SequenceQuery:
    candidate_id: str
    source_id: str
    initial_id: str = 'declared-reset'
    protocol_family: str = 'autonomous'
    sensor_id: str = 'scalar'
    sample_convention: str = 'y_n=C A^n x0; n=0 included'

    def __post_init__(self):
        if any(not isinstance(v,str) or not v for v in self.__dict__.values()):
            raise ValueError('nonempty source and interpretation labels required')


@dataclass(frozen=True)
class CompiledResponse:
    query: SequenceQuery
    source: dict
    sequence_packet: dict
    source_binding: dict
    index_map: dict

    @property
    def dimension(self): return self.sequence_packet['dimension']


def compile_response(query, A, initial, C, adapter=None, *, index_map=None):
    if not isinstance(query, SequenceQuery): raise TypeError('SequenceQuery required')
    adapter = adapter or bundled_adapter()
    A = _matrix(A)
    initial, C = tuple(map(exact, initial)), tuple(map(exact, C))
    if len(initial) != len(A) or len(C) != len(A): raise ValueError('matching vectors required')
    index_map={'offset':0,'stride':1,'meaning':query.sample_convention} if index_map is None else dict(index_map)
    if set(index_map)!={'offset','stride','meaning'} or type(index_map['offset']) is not int or index_map['offset']<0 or type(index_map['stride']) is not int or index_map['stride']<1 or not isinstance(index_map['meaning'],str):raise ValueError('valid physical index map required')
    source = {'A':A, 'initial':initial, 'C':C, 'query':query.__dict__,'index_map':index_map}
    gf = adapter.module('generating').from_state(A, initial, C)
    packet = gf.packet()
    return CompiledResponse(query, source, packet, {'source_sha256':_hash(source), 'upstream':adapter.binding()}, index_map)


def replay_compiled(compiled, adapter=None):
    adapter = adapter or bundled_adapter()
    if compiled.source_binding['upstream'] != adapter.binding(): raise ValueError('upstream source mismatch')
    module=adapter.module('generating');source=compiled.source
    if 'A' in source:
        fresh=compile_response(compiled.query,source['A'],source['initial'],source['C'],adapter,index_map=source['index_map'])
    elif source.get('operation')=='difference':
        first,second=source['first'],source['second']
        replay_compiled(first,adapter);replay_compiled(second,adapter)
        fresh=compile_pair_difference(first,second,adapter)
    elif source.get('operation')=='progression':
        fresh=query_progression(source['original'],source['stride'],source['offset'],adapter)
    else:raise ValueError('unknown source operation')
    if fresh.query!=compiled.query or fresh.source_binding!=compiled.source_binding or fresh.index_map!=compiled.index_map or fresh.sequence_packet!=compiled.sequence_packet:raise ValueError('source, interpretation or fraction does not replay')
    module.replay_generating(compiled.sequence_packet)
    return True


def compile_pair_difference(first, second, adapter=None):
    adapter = adapter or bundled_adapter()
    replay_compiled(first, adapter); replay_compiled(second, adapter)
    if first.query.sample_convention != second.query.sample_convention or first.index_map != second.index_map:
        raise ValueError('incompatible physical indexing')
    m = adapter.module('generating')
    a = m.RationalGF(first.sequence_packet['numerator'],first.sequence_packet['denominator'])
    b = m.RationalGF(second.sequence_packet['numerator'],second.sequence_packet['denominator'])
    source = {'operation':'difference', 'first':first, 'second':second}
    # Hash nested compiled records through their already checked source bindings.
    binding_hash = _hash({'operation':'difference','first':first.source_binding,'second':second.source_binding})
    query = SequenceQuery(first.query.candidate_id+' minus '+second.query.candidate_id, binding_hash,
                          protocol_family=first.query.protocol_family, sample_convention=first.query.sample_convention)
    result = CompiledResponse(query, source, (a+m.RationalGF(tuple(-v for v in b.numerator),b.denominator)).packet(),
                              {'source_sha256':binding_hash,'upstream':adapter.binding()}, first.index_map)
    return result


def _size_bound(compiled, n):
    # A deliberately conservative preflight bound for source-state powering.
    source = compiled.source
    if 'A' not in source:
        if source.get('operation')=='progression':return _size_bound(source['original'],source['stride']*n+source['offset'])
        return _size_bound(source['first'],n)+_size_bound(source['second'],n)+2
    values = sum(source['A'],()) + source['initial'] + source['C']
    denominators = 1
    from math import lcm
    for v in values: denominators = lcm(denominators,v.denominator)
    magnitude = max([1]+[abs(v.numerator)*(denominators//v.denominator) for v in values])
    return (n+2)*(denominators.bit_length()+magnitude.bit_length()+len(source['A']).bit_length()+2)


@dataclass(frozen=True)
class RemoteValue:
    index: int
    value: object
    arithmetic_mode: str
    cost_metadata: dict


def query_index(compiled, n, max_bits=4096, adapter=None, modulus=None):
    if type(n) is not int or n < 0: raise ValueError('nonnegative integer index required')
    if type(max_bits) is not int or max_bits < 1: raise ValueError('positive bit budget required')
    adapter = adapter or bundled_adapter()
    replay_compiled(compiled, adapter)
    packet = compiled.sequence_packet
    module = adapter.module('generating')
    gf = module.RationalGF(packet['numerator'], packet['denominator'])
    estimate = 0 if not gf.dimension else _size_bound(compiled,n)
    if modulus is None:
        if estimate > max_bits: raise ValueError('resource_limit: conservative exact-output bit bound exceeds max_bits')
        value = gf.nth(n)
        bits = max(abs(value.numerator).bit_length(),value.denominator.bit_length())
        if bits > max_bits: raise ValueError('resource_limit: exact output exceeds max_bits')
        return RemoteValue(n,value,'exact_rational',{'estimated_bits':estimate,'output_bits':bits,'powering_stages_upper':n.bit_length()})
    if type(modulus) is not int or modulus < 2: raise ValueError('integer modulus >=2 required')
    A,x,c = gf.realize()
    def mod(v): return (v.numerator*pow(v.denominator,-1,modulus))%modulus
    A,x,c = tuple(tuple(mod(v) for v in row) for row in A),tuple(map(mod,x)),tuple(map(mod,c))
    def mm(a,b): return tuple(tuple(sum(v*w for v,w in zip(row,col))%modulus for col in zip(*b)) for row in a)
    power = tuple(tuple(int(i==j) for j in range(len(A))) for i in range(len(A)))
    k=n
    while k:
        if k&1: power=mm(power,A)
        k//=2
        if k:A=mm(A,A)
    value=sum(c[i]*sum(power[i][j]*x[j] for j in range(len(x))) for i in range(len(c)))%modulus
    return RemoteValue(n,value,'modular_residue',{'modulus':modulus,'powering_stages_upper':n.bit_length(),'meaning':'residue only; no real-valued noise margin'})


def verify_remote_value(compiled, result, adapter=None, max_bits=4096):
    return result == query_index(compiled,result.index,max_bits,adapter,result.cost_metadata.get('modulus'))


def query_progression(compiled, stride, offset=0, adapter=None):
    if type(stride) is not int or stride<1 or type(offset) is not int or offset<0: raise ValueError('positive stride/nonnegative offset required')
    adapter=adapter or bundled_adapter();replay_compiled(compiled,adapter)
    m=adapter.module('generating');gf=m.RationalGF(compiled.sequence_packet['numerator'],compiled.sequence_packet['denominator']).subsequence(stride,offset)
    source={'operation':'progression','original':compiled,'stride':stride,'offset':offset}
    binding_hash=_hash({'operation':'progression','original':compiled.source_binding,'stride':stride,'offset':offset})
    index_map={'offset':compiled.index_map['offset']+compiled.index_map['stride']*offset,'stride':compiled.index_map['stride']*stride,'meaning':f'original y_({compiled.index_map["stride"]*stride}n+{compiled.index_map["offset"]+compiled.index_map["stride"]*offset})'}
    return CompiledResponse(compiled.query,source,gf.packet(),{'source_sha256':binding_hash,'upstream':adapter.binding()},index_map)


def compile_constant_input(candidate, sensor, amplitude=1, initial=None, adapter=None):
    amplitude=exact(amplitude); n=candidate.dimension
    initial=tuple(Q(0) for _ in range(n)) if initial is None else tuple(map(exact,initial))
    A=[[Q(0)]*(n+1) for _ in range(n+1)]
    for i,j,v in candidate.entries:A[i][j]=v
    for i,v in enumerate(candidate.heater):A[i][n]=amplitude*v
    A[n][n]=Q(1)
    query=SequenceQuery(candidate.identifier,_hash((candidate.entries,candidate.heater,candidate.sensors)),protocol_family='constant_input',sensor_id=str(sensor),sample_convention='declared exact reset; held constant input; y_n after n updates; no feedthrough')
    return compile_response(query,A,initial+(Q(1),),candidate.sensors[sensor]+(Q(0),),adapter)


def compile_repeated_block(candidate, word, sensor, phase=0, adapter=None):
    word=tuple(map(exact,word))
    if not word or type(phase) is not int or not 0<=phase<len(word):raise ValueError('nonempty block and valid phase required')
    n=candidate.dimension; adapter=adapter or bundled_adapter(); r=adapter.module('rational')
    A=[[Q(0)]*n for _ in range(n)]
    for i,j,v in candidate.entries:A[i][j]=v
    block=r.identity(n),tuple(Q(0) for _ in range(n))
    f=adapter.module('fastforward')
    for u in word:block=f.compose((A,tuple(u*v for v in candidate.heater)),block)
    offset=tuple(Q(0) for _ in range(n))
    phase_A=r.identity(n)
    for u in word[:phase]:
        offset=r.addv(r.mv(A,offset),tuple(u*v for v in candidate.heater));phase_A=r.mul(A,phase_A)
    C=tuple(sum(candidate.sensors[sensor][i]*phase_A[i][j] for i in range(n)) for j in range(n))
    D=sum(v*w for v,w in zip(candidate.sensors[sensor],offset))
    H=tuple(tuple(block[0][i])+(block[1][i],) for i in range(n))+((Q(0),)*n+(Q(1),),)
    query=SequenceQuery(candidate.identifier,_hash((candidate.entries,candidate.heater,candidate.sensors,word,phase)),protocol_family='repeated_block',sensor_id=str(sensor),sample_convention=f'block index k; y_(k*{len(word)}+{phase}); no feedthrough')
    return compile_response(query,H,(Q(0),)*n+(Q(1),),C+(D,),adapter,index_map={'offset':phase,'stride':len(word),'meaning':query.sample_convention})


def response_receipt(compiled,result):
    """Portable canonical rationals; source semantics travel with the fraction."""
    def source(c):
        if 'A' in c.source:
            evidence={'kind':'state','A':_encode(c.source['A']),'initial':_encode(c.source['initial']),'C':_encode(c.source['C']),'index_map':c.source['index_map']}
        elif c.source.get('operation')=='difference':
            evidence={'kind':'difference','first':source(c.source['first']),'second':source(c.source['second'])}
        else:
            evidence={'kind':'progression','original':source(c.source['original']),'stride':c.source['stride'],'offset':c.source['offset']}
        return {'query':dict(c.query.__dict__),'evidence':evidence,'source_binding':c.source_binding,'sequence_packet':c.sequence_packet,'index_map':c.index_map}
    return {'schema':'singularity.remote-response/1','compiled':source(compiled),'index':result.index,'value':_encode(result.value),'arithmetic_mode':result.arithmetic_mode,'cost_metadata':result.cost_metadata}


def replay_remote_receipt(receipt,adapter=None,max_bits=4096):
    from math import gcd
    adapter=adapter or bundled_adapter()
    if not isinstance(receipt,dict) or set(receipt)!= {'schema','compiled','index','value','arithmetic_mode','cost_metadata'} or receipt['schema']!='singularity.remote-response/1':raise ValueError('strict remote-response receipt required')
    def rational(v):
        if not isinstance(v,list) or len(v)!=2 or any(type(a) is not int for a in v) or v[1]<=0 or gcd(abs(v[0]),v[1])!=1:raise ValueError('canonical numerator/positive denominator pair required')
        return Q(*v)
    def reconstruct(p):
        if set(p)!={'query','evidence','source_binding','sequence_packet','index_map'}:raise ValueError('unknown compiled fields')
        q=SequenceQuery(**p['query']);e=p['evidence']
        if e['kind']=='state':
            if set(e)!={'kind','A','initial','C','index_map'}:raise ValueError('unknown source-state fields')
            c=compile_response(q,tuple(tuple(rational(v) for v in row) for row in e['A']),tuple(map(rational,e['initial'])),tuple(map(rational,e['C'])),adapter,index_map=e['index_map'])
        elif e['kind']=='difference':
            if set(e)!={'kind','first','second'}:raise ValueError('unknown difference fields')
            c=compile_pair_difference(reconstruct(e['first']),reconstruct(e['second']),adapter)
            if c.query!=q:raise ValueError('difference interpretation mismatch')
        elif e['kind']=='progression':
            if set(e)!={'kind','original','stride','offset'}:raise ValueError('unknown progression fields')
            c=query_progression(reconstruct(e['original']),e['stride'],e['offset'],adapter)
            if c.query!=q:raise ValueError('progression interpretation mismatch')
        else:raise ValueError('unknown source kind')
        if c.source_binding!=p['source_binding'] or c.sequence_packet!=p['sequence_packet']:raise ValueError('source-derived fraction mismatch')
        m=p['index_map']
        if set(m)!={'offset','stride','meaning'} or type(m['offset']) is not int or m['offset']<0 or type(m['stride']) is not int or m['stride']<1 or not isinstance(m['meaning'],str):raise ValueError('invalid index map')
        if c.index_map!=m:raise ValueError('index map does not derive from source operations')
        return c
    c=reconstruct(receipt['compiled']);meta=receipt['cost_metadata'];mode=receipt['arithmetic_mode']
    modulus=meta.get('modulus') if mode=='modular_residue' else None
    if mode not in ('exact_rational','modular_residue'):raise ValueError('unknown arithmetic mode')
    result=query_index(c,receipt['index'],max_bits,adapter,modulus)
    value=rational(receipt['value']) if mode=='exact_rational' else receipt['value']
    if type(value) is bool or value!=result.value or meta!=result.cost_metadata:raise ValueError('remote value/cost does not replay')
    return True


def remote_panel_pool(responses,indices,*,cost_per_index=1,reset_cost=1,max_bits=4096,adapter=None):
    """Finite physical-time menu from exact queries; compilation is accounted separately.

    This exposes only the declared indices and never claims an all-time optimum.
    """
    from .panels import reading_pool
    responses=tuple(responses);indices=tuple(indices)
    if not responses or len({c.query.candidate_id for c in responses})!=len(responses):raise ValueError('distinct compiled candidate responses required')
    if any(c.index_map!=responses[0].index_map or c.query.sample_convention!=responses[0].query.sample_convention or c.query.protocol_family!=responses[0].query.protocol_family for c in responses):raise ValueError('incompatible physical index maps or protocol semantics')
    elapsed,reset=exact(cost_per_index),exact(reset_cost)
    if elapsed<=0 or reset<0:raise ValueError('positive elapsed and nonnegative reset costs required')
    rows=tuple(tuple(query_index(c,n,max_bits,adapter).value for c in responses) for n in indices)
    return reading_pool(tuple(reset+elapsed*(responses[0].index_map['offset']+responses[0].index_map['stride']*n) for n in indices),rows,labels=tuple('remote-index:'+str(n) for n in indices),candidates=len(responses))
