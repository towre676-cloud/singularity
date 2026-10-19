"""Word-Hankel realization and exact weighted quotient discovery.

A function f on words has a finite linear representation
f(w)=alpha*A[w1]*...*A[wl]*beta exactly when its word Hankel matrix has finite
rank over Q; the minimal dimension is that rank. From a finite Hankel block the
construction below is exact on the block. Agreement beyond it is a held-out
check, and a mismatch is returned as a witness word.
"""
from fractions import Fraction as Q
from itertools import product
from .exact import matrix,matmul,rank


def words(alphabet,length):
    """All words of length <= length over range(alphabet), shortlex order."""
    out=[]
    for n in range(length+1):out.extend(product(range(alphabet),repeat=n))
    return out


def _independent_rows(rows):
    chosen=[]
    for i,row in enumerate(rows):
        if rank([rows[j] for j in chosen]+[row])>len(chosen):chosen.append(i)
    return chosen


def _inverse(a):
    n=len(a);aug=[list(row)+[Q(int(i==j)) for j in range(n)] for i,row in enumerate(matrix(a))]
    for c in range(n):
        p=next((i for i in range(c,n) if aug[i][c]),None)
        if p is None:raise ZeroDivisionError("singular Hankel block")
        aug[c],aug[p]=aug[p],aug[c];z=aug[c][c];aug[c]=[x/z for x in aug[c]]
        for i in range(n):
            if i!=c and aug[i][c]:
                z=aug[i][c];aug[i]=[x-z*y for x,y in zip(aug[i],aug[c])]
    return [row[n:] for row in aug]


class LinearRepresentation:
    """f(w)=alpha*A[w1]*...*A[wl]*beta; beta is a vector (scalar output) or an n-by-k matrix."""
    def __init__(self,alpha,actions,beta):
        self.alpha=[Q(x) for x in alpha];self.actions=[matrix(a) for a in actions]
        self.vector=bool(beta) and isinstance(beta[0],(list,tuple))
        self.beta=[[Q(x) for x in row] for row in beta] if self.vector else [Q(x) for x in beta]
        n=len(self.alpha)
        if len(self.beta)!=n or any(len(a)!=n or any(len(r)!=n for r in a) for a in self.actions):
            raise ValueError("inconsistent dimensions")

    @property
    def dimension(self):return len(self.alpha)

    def state(self,word):
        x=self.alpha
        for letter in word:
            a=self.actions[letter];x=[sum((x[i]*a[i][j] for i in range(len(x))),Q(0)) for j in range(len(x))]
        return x

    def __call__(self,word):
        x=self.state(word)
        if self.vector:
            return tuple(sum((x[i]*self.beta[i][j] for i in range(len(x))),Q(0)) for j in range(len(self.beta[0])))
        return sum((p*q for p,q in zip(x,self.beta)),Q(0))


def _value(f,word,outputs):
    v=f(tuple(word))
    if outputs is None:return (Q(v),)
    v=tuple(Q(x) for x in v)
    if len(v)!=outputs:raise ValueError("output length differs")
    return v


def hankel_block(f,prefixes,suffixes,middle=(),outputs=None):
    """Rows are prefixes; columns are suffixes (times output coordinates when outputs is set)."""
    return [[x for s in suffixes for x in _value(f,tuple(p)+tuple(middle)+tuple(s),outputs)] for p in prefixes]


def realize(f,alphabet,depth,outputs=None):
    """Minimal representation consistent with the Hankel block on words of length <= depth.

    Queries f on words of length <= 2*depth+1. The returned model reproduces f on
    every word p+s and p+a+s with |p|,|s| <= depth. With outputs=k, f returns a
    length-k vector and the stacked multi-output Hankel block is used.
    """
    if alphabet<1 or depth<0:raise ValueError("need a nonempty alphabet and depth >= 0")
    k=1 if outputs is None else outputs
    ws=words(alphabet,depth);h=hankel_block(f,ws,ws,(),outputs)
    columns=[(s,j) for s in ws for j in range(k)]
    rows=_independent_rows(h)
    if not rows:
        return _ZeroModel(outputs),{"rank":0,"prefixes":[],"suffixes":[]}
    cols=_independent_rows([list(c) for c in zip(*[h[i] for i in rows])])
    p0,c0=[ws[i] for i in rows],[columns[j] for j in cols]

    def block(middle):
        return [[_value(f,tuple(p)+tuple(middle)+tuple(s),outputs)[j] for s,j in c0] for p in p0]
    minv=_inverse(block(()))
    alpha=[_value(f,s,outputs)[j] for s,j in c0]
    beta=matmul(minv,[list(_value(f,p,outputs)) for p in p0])
    if outputs is None:beta=[row[0] for row in beta]
    actions=[matmul(minv,block((a,))) for a in range(alphabet)]
    model=LinearRepresentation(alpha,actions,beta)
    norm=(lambda v:(v,)) if outputs is None else tuple
    for p in ws:
        for s in ws:
            assert norm(model(p+s))==_value(f,p+s,outputs)
            for a in range(alphabet):assert norm(model(p+(a,)+s))==_value(f,p+(a,)+s,outputs)
    return model,{"rank":len(rows),"prefixes":p0,"suffixes":c0 if outputs is not None else [s for s,_ in c0]}


class _ZeroModel:
    dimension=0

    def __init__(self,outputs):self.outputs=outputs

    def __call__(self,word):
        return Q(0) if self.outputs is None else (Q(0),)*self.outputs


def held_out(model,f,alphabet,length):
    """First word of length <= length on which model and f differ, or None."""
    for w in words(alphabet,length):
        value=f(w);value=tuple(Q(x) for x in value) if isinstance(value,(list,tuple)) else Q(value)
        if model(w)!=value:return {"word":w,"model":model(w),"value":value}
    return None


def coarsest_lumping(actions,output=None,initial=None):
    """Coarsest partition with R*A_c = Abar_c*R for every transition matrix A_c.

    Column-state convention: A[i][j] is the weight from source j to destination i,
    so a valid block structure gives every source in a block the same total weight
    into each destination block. Columns of the output map H must also be constant
    on blocks, so H = Hbar*R. Optional initial labels refine the start partition.
    """
    actions=[matrix(a) for a in actions];n=len(actions[0])
    if any(len(a)!=n or any(len(r)!=n for r in a) for a in actions):raise ValueError("square matrices of one size required")
    h=matrix(output) if output else []
    labels=[(tuple(row[j] for row in h),None if initial is None else initial[j]) for j in range(n)]
    block=_relabel(labels)
    while True:
        k=max(block)+1
        sig=[(block[j],)+tuple(tuple(sum((a[i][j] for i in range(n) if block[i]==b),Q(0)) for b in range(k))
                                for a in actions) for j in range(n)]
        new=_relabel(sig)
        if max(new)+1==k:break
        block=new
    k=max(block)+1;reps=[block.index(b) for b in range(k)]
    r=[[Q(int(block[j]==b)) for j in range(n)] for b in range(k)]
    reduced=[[[sum((a[i][reps[c]] for i in range(n) if block[i]==b),Q(0)) for c in range(k)] for b in range(k)]
             for a in actions]
    for a,ab in zip(actions,reduced):assert matmul(r,a)==matmul(ab,r)
    hbar=[[row[reps[c]] for c in range(k)] for row in h]
    return {"blocks":[[j for j in range(n) if block[j]==b] for b in range(k)],
            "aggregation":r,"reduced":reduced,"output":hbar}


def _relabel(keys):
    seen={};return [seen.setdefault(key,len(seen)) for key in keys]


def realization_receipt():
    fib=[0,1]
    for _ in range(30):fib.append(fib[-1]+fib[-2])
    seq,info=realize(lambda w:fib[len(w)],1,3)
    # Count occurrences of the factor "01" in binary words: a three-state signed-free example.
    count=lambda w:sum(1 for i in range(len(w)-1) if w[i:i+2]==(0,1))
    model,winfo=realize(count,2,2)
    lump=coarsest_lumping([[[0,1,1],[1,0,0],[1,1,1]]],[[1,0,0]])
    return {"fibonacci_dimension":info["rank"],"fibonacci_held_out":held_out(seq,lambda w:fib[len(w)],1,25),
            "factor_count_dimension":winfo["rank"],"factor_count_held_out":held_out(model,count,2,8),
            "lumping":lump}
