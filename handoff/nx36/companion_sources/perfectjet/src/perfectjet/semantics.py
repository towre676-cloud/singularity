"""Finite partial Moore-machine quotient with explicit distinguishing words."""
from collections import deque


class PartialMachine:
    def __init__(self,observations,transitions):
        self.observations=tuple(observations)
        self.transitions=tuple(tuple(row) for row in transitions)
        n=len(self.observations)
        if len(self.transitions)!=n:raise ValueError("one transition row per state required")
        widths={len(row) for row in self.transitions}
        if len(widths)>1:raise ValueError("ragged actions")
        self.actions=next(iter(widths),0)
        if any(t is not None and (not isinstance(t,int) or not 0<=t<n)
               for row in self.transitions for t in row):raise ValueError("invalid target state")

    def distinguish(self,x,y):
        if not 0<=x<len(self.observations) or not 0<=y<len(self.observations):
            raise ValueError("state outside machine")
        queue=deque([(x,y,())]);seen={(x,y)}
        while queue:
            a,b,w=queue.popleft()
            if self.observations[a]!=self.observations[b]:return w
            for action in range(self.actions):
                aa,bb=self.transitions[a][action],self.transitions[b][action]
                if (aa is None)!=(bb is None):return w+(action,)
                if aa is not None and (aa,bb) not in seen:
                    seen.add((aa,bb));queue.append((aa,bb,w+(action,)))
        return None

    def behavior(self,state,word):
        obs=[self.observations[state]]
        for action in word:
            state=self.transitions[state][action]
            if state is None:return ("undefined",tuple(obs))
            obs.append(self.observations[state])
        return ("defined",tuple(obs))

    def quotient(self):
        n=len(self.observations);blocks=[];mapping=[]
        for state in range(n):
            found=next((i for i,b in enumerate(blocks) if self.distinguish(state,b[0]) is None),None)
            if found is None:found=len(blocks);blocks.append([])
            blocks[found].append(state);mapping.append(found)
        obs=[self.observations[b[0]] for b in blocks]
        trans=[[None if t is None else mapping[t] for t in self.transitions[b[0]]] for b in blocks]
        reduced=PartialMachine(obs,trans)
        for state,row in enumerate(self.transitions):
            assert obs[mapping[state]]==self.observations[state]
            assert trans[mapping[state]]==[None if t is None else mapping[t] for t in row]
        return reduced,mapping,blocks
