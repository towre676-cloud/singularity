exec(open('ex.py').read().split("res={}")[0])
import random
def chain2(F):
    c=Counter()
    def rec(t,anc):
        s=size(t)
        for a in anc:c[(a,s)]+=1
        for k in t:rec(k,anc+[s])
    for t in F:rec(t,[])
    return tuple(sorted(c.items()))
def chain3(F):
    c=Counter()
    def rec(t,anc):
        s=size(t)
        for i in range(len(anc)):
            for j in range(i+1,len(anc)):c[(anc[i],anc[j],s)]+=1
        for k in t:rec(k,anc+[s])
    for t in F:rec(t,[])
    return tuple(sorted(c.items()))
def run(pairs,E):
    L=[];
    for a,b in pairs:L+= [enc(a+a,b+b),enc(a+b,a+b)]
    txt="\n".join(" ".join(l.split()) for l in L)+"\n"
    o=subprocess.run(['./fast',str(E)],input=txt,capture_output=True,text=True).stdout.split()
    return list(map(int,o))
# sanity: agree with shell tool
a,b=((((), ()), ((),)),((((),),), (), ()));print('sanity',run([(a,b)],7))
EM=int(sys.argv[2])
for w in range(5,int(sys.argv[1])+1):
    Fs=forests(w);g=defaultdict(list)
    for F in Fs:g[gen(F)].append(F)
    P1=[(a,b) for v in g.values() for a,b in itertools.combinations(v,2)]
    if len(P1)>400:P1s=random.Random(1).sample(P1,400)
    else:P1s=P1
    r1=Counter(run(P1s,EM))
    g2=defaultdict(list)
    for F in Fs:g2[(gen(F),chain2(F))].append(F)
    P2=[(a,b) for v in g2.values() for a,b in itertools.combinations(v,2)]
    P2s=P2 if len(P2)<=150 else random.Random(2).sample(P2,150)
    r2=Counter(run(P2s,EM)) if P2s else {}
    g3=defaultdict(list)
    for F in Fs:g3[(gen(F),chain2(F),chain3(F))].append(F)
    P3=[(a,b) for v in g3.values() for a,b in itertools.combinations(v,2)]
    P3s=P3 if len(P3)<=60 else random.Random(3).sample(P3,60)
    r3=Counter(run(P3s,EM)) if P3s else {}
    print(w,'gen',len(P1),dict(r1),'gen+2chain',len(P2),dict(r2),'gen+2+3',len(P3),dict(r3),flush=True)
