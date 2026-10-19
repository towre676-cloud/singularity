"""Coarsest observation/legality-preserving quotient of a finite partial DFA.

Construct shortest distinguishing words for every pair of inequivalent states.
Completeness concerns the supplied deterministic transition model only.
"""
from collections import defaultdict
from copy import deepcopy
from heapq import heappop,heappush
from itertools import combinations
from .semantic_fibres import canonical,identity
from .divisor_square import WorkLimit


def normalize(spec):
    spec=deepcopy(spec)
    if set(spec)!={'observations','actions'}:raise ValueError('observations and actions required')
    obs=spec['observations'];actions=spec['actions'];n=len(obs)
    if not 1<=n<=128 or not 1<=len(actions)<=16:raise WorkLimit('128 states and sixteen actions maximum')
    if any(type(a) is not str or not a for a in actions):raise ValueError('named actions required')
    for row in actions.values():
        if len(row)!=n or any(t is not None and (type(t) is not int or not 0<=t<n) for t in row):raise ValueError('partial transition outside state carrier')
    canonical(spec)
    return spec


def distinguishing_words(spec):
    """Reverse pair graph computes all shortest experiments at once."""
    spec=normalize(spec);obs=list(map(canonical,spec['observations']));actions=spec['actions'];n=len(obs)
    reverse=defaultdict(list);heap=[];best={}
    def offer(pair,word,reason):
        key=(len(word),tuple(word),reason)
        if pair not in best or key<best[pair]:best[pair]=key;heappush(heap,(*key,*pair))
    for i,j in combinations(range(n),2):
        if obs[i]!=obs[j]:offer((i,j),(),'observation')
        for a,row in sorted(actions.items()):
            u,v=row[i],row[j]
            if (u is None)!=(v is None):offer((i,j),(a,),'legality')
            elif u is not None and u!=v:reverse[tuple(sorted((u,v)))].append(((i,j),a))
    while heap:
        length,word,reason,i,j=heappop(heap)
        if best[i,j]!=(length,word,reason):continue
        for pair,a in reverse[i,j]:offer(pair,(a,)+word,reason)
    return {pair:{'word':list(key[1]),'reason':key[2]} for pair,key in best.items()}


def check_word(spec,i,j,witness):
    spec=normalize(spec);obs=spec['observations'];word=witness['word'];reason=witness['reason']
    if type(i) is not int or type(j) is not int or not 0<=i<len(obs) or not 0<=j<len(obs):raise ValueError('invalid witness states')
    for pos,a in enumerate(word):
        if a not in spec['actions']:raise ValueError('unknown experiment action')
        u,v=spec['actions'][a][i],spec['actions'][a][j]
        if u is None or v is None:
            if (u is None)!=(v is None) and pos==len(word)-1 and reason=='legality':return True
            raise ValueError('experiment not jointly executable before distinction')
        i,j=u,v
    if reason=='observation' and canonical(obs[i])!=canonical(obs[j]):return True
    raise ValueError('word does not distinguish supplied states')


def future_quotient(spec):
    spec=normalize(spec);observations=spec['observations'];actions=spec['actions'];n=len(observations)
    groups={}
    for i,o in enumerate(observations):groups.setdefault(canonical(o),[]).append(i)
    blocks=sorted(groups.values(),key=lambda b:b[0]);rounds=0
    while True:
        index={s:i for i,b in enumerate(blocks) for s in b};groups={}
        for s,o in enumerate(observations):
            signature=(canonical(o),tuple(None if row[s] is None else index[row[s]] for a,row in sorted(actions.items())))
            groups.setdefault(signature,[]).append(s)
        refined=sorted(groups.values(),key=lambda b:b[0]);rounds+=1
        if refined==blocks:break
        blocks=refined
    index={s:i for i,b in enumerate(blocks) for s in b};words=distinguishing_words(spec)
    witnesses=[{'first':a[0],'second':b[0],**words[a[0],b[0]]} for a,b in combinations(blocks,2)]
    quotient={'observations':[deepcopy(observations[b[0]]) for b in blocks],
              'actions':{a:[None if row[b[0]] is None else index[row[b[0]]] for b in blocks] for a,row in sorted(actions.items())}}
    return {'schema':'pp-future-quotient/1','model_id':identity('pp-partial-automaton/1',spec),
            'blocks':blocks,'projection':[index[s] for s in range(n)],'quotient':quotient,
            'distinguishing_witnesses':witnesses,'refinement_rounds':rounds,
            'scope':'coarsest exact observation-and-legality quotient of supplied finite deterministic model'}


def check_quotient(packet,spec):
    """Replay homomorphism and pair separation without partition refinement."""
    spec=normalize(spec);n=len(spec['observations']);blocks=packet['blocks'];projection=packet['projection'];quotient=packet['quotient']
    if packet['model_id']!=identity('pp-partial-automaton/1',spec):raise ValueError('source model binding mismatch')
    if not blocks or any(not isinstance(b,list) or not b or any(type(s) is not int for s in b) for b in blocks) or sorted(s for b in blocks for s in b)!=list(range(n)):raise ValueError('blocks do not partition the source carrier')
    if len(projection)!=n or projection!=[next(k for k,b in enumerate(blocks) if s in b) for s in range(n)]:raise ValueError('invalid quotient projection')
    normalize(quotient)
    if len(quotient['observations'])!=len(blocks) or set(quotient['actions'])!=set(spec['actions']):raise ValueError('quotient carrier mismatch')
    for s in range(n):
        k=projection[s]
        if canonical(spec['observations'][s])!=canonical(quotient['observations'][k]):raise ValueError('observation transport failed')
        for a,row in spec['actions'].items():
            expected=None if row[s] is None else projection[row[s]]
            if quotient['actions'][a][k]!=expected:raise ValueError('action/legality transport failed')
    pairs={(a[0],b[0]) for a,b in combinations(blocks,2)};seen=set()
    for w in packet['distinguishing_witnesses']:
        pair=(w['first'],w['second'])
        if pair not in pairs or pair in seen:raise ValueError('invalid minimality witness coverage')
        check_word(spec,*pair,w);seen.add(pair)
    if seen!=pairs:raise ValueError('missing minimality witnesses')
    return True


def diagnosis_plan(spec,probes,*,work_limit=100000):
    """Minimum worst-case cost adaptive policy over resettable supplied probes.

Each probe starts from the same unknown original state; outcomes are complete
observation/legality traces. Positive rational probe costs, finite menu only.
"""
    from fractions import Fraction as Q
    from .psg_polynomial import rational
    spec=normalize(spec);n=len(spec['observations']);quotient=future_quotient(spec);classes=quotient['projection']
    if type(work_limit) is not int or not 1<=work_limit<=1_000_000 or not 1<=len(probes)<=16:raise WorkLimit('bounded diagnosis menu/work required')
    menu=[];names=set()
    for p in probes:
        if set(p)!={'name','word','cost'} or type(p['name']) is not str or not p['name'] or p['name'] in names:raise ValueError('distinct named probes required')
        names.add(p['name']);cost=rational(p['cost']);word=p['word']
        if cost<=0 or not isinstance(word,list) or len(word)>n*n or any(a not in spec['actions'] for a in word):raise ValueError('positive-cost bounded legal action words required')
        outcomes=[]
        for s in range(n):
            trace=[{'observation':deepcopy(spec['observations'][s])}]
            for k,a in enumerate(word):
                t=spec['actions'][a][s]
                if t is None:trace.append({'disabled_action':a,'position':k});break
                s=t;trace.append({'observation':deepcopy(spec['observations'][s])})
            outcomes.append(canonical(trace))
        menu.append((p['name'],word,cost,outcomes))
    memo={};work=0
    def solve(belief):
        nonlocal work
        if belief in memo:return memo[belief]
        work+=1
        if work>work_limit:raise WorkLimit('optimal diagnosis belief budget exceeded')
        if len({classes[s] for s in belief})==1:
            result=(Q(0),{'states':list(belief),'future_class':classes[belief[0]],'remaining_cost':'0'});memo[belief]=result;return result
        best=None
        for name,word,cost,outcomes in menu:
            groups={}
            for s in belief:groups.setdefault(outcomes[s],[]).append(s)
            if len(groups)<2:continue
            children={};values=[]
            for outcome,group in sorted(groups.items()):
                child=solve(tuple(group))
                if child is None:break
                values.append(child[0]);children[outcome]=child[1]
            else:
                value=rational(cost+max(values));node={'probe':name,'word':word,'cost':str(cost),'remaining_cost':str(value),'outcomes':children}
                if best is None or (value,name)<(best[0],best[1]['probe']):best=(value,node)
        memo[belief]=best;return best
    groups={}
    for s,o in enumerate(spec['observations']):groups.setdefault(canonical(o),[]).append(s)
    roots={};costs=[];blocked=[]
    for output,group in sorted(groups.items()):
        result=solve(tuple(group))
        if result is None:
            pair=next((i,j) for i,j in combinations(group,2) if classes[i]!=classes[j] and all(p[3][i]==p[3][j] for p in menu))
            blocked.append({'states':list(pair),'initial_observation':output,'all_probe_traces':{p[0]:p[3][pair[0]] for p in menu}})
        else:costs.append(result[0]);roots[output]=result[1]
    return {'schema':'pp-optimal-diagnosis/1','model_id':quotient['model_id'],'status':'menu_insufficient' if blocked else 'optimal',
            'worst_case_cost':None if blocked else str(max(costs,default=Q(0))),'policy':roots,'obstructions':blocked,
            'beliefs_solved':work,'menu':deepcopy(probes),
            'scope':'exact minimum worst-case additive probe cost; resettable probes; supplied finite menu/model; current observation free'}


def compare_models(left,right,left_initial=0,right_initial=0):
    """All-future behavioral equivalence across two supplied finite models."""
    left=normalize(left);right=normalize(right);n=len(left['observations']);m=len(right['observations'])
    if type(left_initial) is not int or type(right_initial) is not int or not 0<=left_initial<n or not 0<=right_initial<m:raise ValueError('initial state outside model carrier')
    actions={}
    for a in sorted(set(left['actions'])|set(right['actions'])):
        actions[a]=left['actions'].get(a,[None]*n)+[None if s is None else s+n for s in right['actions'].get(a,[None]*m)]
    union={'observations':left['observations']+right['observations'],'actions':actions}
    quotient=future_quotient(union);check_quotient(quotient,union)
    equivalent=quotient['projection'][left_initial]==quotient['projection'][n+right_initial]
    witness=None if equivalent else distinguishing_words(union)[left_initial,n+right_initial]
    if witness is not None:check_word(union,left_initial,n+right_initial,witness)
    return {'schema':'pp-model-equivalence/1','left_model_id':identity('pp-partial-automaton/1',left),
            'right_model_id':identity('pp-partial-automaton/1',right),'initial_states':[left_initial,right_initial],
            'equivalent':equivalent,'shortest_counterexample':witness,'common_quotient':quotient,
            'scope':'all finite action words in supplied deterministic partial models; observations and action legality preserved'}
