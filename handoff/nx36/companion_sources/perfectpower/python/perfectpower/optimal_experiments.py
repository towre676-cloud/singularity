"""Exact global minimum-cost separating operator words, with work budgets."""
from fractions import Fraction as Q
from heapq import heappush,heappop
from .divisor_square import WorkLimit


def cheapest_experiment(machine,left,right,operator_costs=None,readout_costs=None,*,node_limit=100000,bit_limit=8192):
    from .integral_machine import project_state
    from .observable_machine import _apply,_word,_q
    from . import exact_linear as E
    a,b=project_state(machine,left),project_state(machine,right)
    operators=machine['operators_minimal'];readouts=machine['readouts_minimal']
    oc=[Q(1)]*len(operators) if operator_costs is None else list(map(_q,operator_costs))
    rc=[Q(1)]*len(readouts) if readout_costs is None else list(map(_q,readout_costs))
    if len(oc)!=len(operators) or len(rc)!=len(readouts) or any(x<=0 for x in oc) or any(x<0 for x in rc):
        raise ValueError('matching positive operator and nonnegative readout costs required')
    if type(node_limit) is not int or node_limit<1 or type(bit_limit) is not int or not 1<=bit_limit<=8192:
        raise ValueError('positive work and bit budgets required')
    difference=tuple(x-y for x,y in zip(a,b))
    if not any(difference):return dict(status='ALL_FUTURE_EQUAL',execution_verified=False)
    # A known finite witness supplies an incumbent before global search.
    original=machine['rational_certificate'];delta=tuple(x-y for x,y in zip(left,right));choices=[]
    for output,word in original['readout_words']:
        value=_apply([original['readouts'][output]],_word(original['operators'],delta,word))[0]
        if value:choices.append((sum((oc[i] for i in word),Q(0))+rc[output],output,tuple(word)))
    best,output,winner=min(choices);queue=[(Q(0),(),difference)];visited={difference:Q(0)};nodes=0
    while queue:
        price,word,state=heappop(queue)
        if price+min(rc)>=best:break
        if visited[state]!=price:continue
        nodes+=1
        if nodes>node_limit:raise WorkLimit('global experiment search exceeds node budget; no optimum returned')
        for i,value in enumerate(E.apply(readouts,state)):
            candidate=price+rc[i]
            if value and candidate<best:best,output,winner=candidate,i,word
        for i,operator in enumerate(operators):
            cost=price+oc[i]
            if cost+min(rc)>=best:continue
            child=tuple(E.apply(operator,state))
            if any(abs(x).bit_length()>bit_limit for x in child):raise WorkLimit('experiment state growth exceeds bit budget')
            if child not in visited or cost<visited[child]:
                if child not in visited and len(visited)>=node_limit:
                    raise WorkLimit('experiment frontier exceeds state budget; no optimum returned')
                visited[child]=cost;heappush(queue,(cost,word+(i,),child))
    left_value=_apply([original['readouts'][output]],_word(original['operators'],left,winner))[0]
    right_value=_apply([original['readouts'][output]],_word(original['operators'],right,winner))[0]
    return dict(status='OPTIMAL_SEPARATING_EXPERIMENT',word=winner,readout=output,left_value=left_value,
        right_value=right_value,cost=best,expanded_states=nodes,complete=True,execution_verified=False,
        operator_costs=oc,readout_costs=rc,scope='global minimum supplied cost over all finite chronological operator words and readouts; one winner returned')
