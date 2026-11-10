import sys
P=(1<<61)-1
def load(f):
    L=open(f).read().split('\n');N=int(L[0]);T=[]
    for l in L[1:N+1]:
        v=list(map(int,l.split()));T.append((v[0],v[2:]))
    return T
def rank(rows):
    piv=[];r=0
    for v in rows:
        v=list(v)
        for c,p in piv:
            f=v[c]
            if f:v=[(a-f*b)%P for a,b in zip(v,p)]
        c=next((i for i,x in enumerate(v) if x),None)
        if c is not None:
            iv=pow(v[c],P-2,P);piv.append((c,[a*iv%P for a in v]));r+=1
    return r
for f,Y in (('t8.txt',400),('t9.txt',400),('t10.txt',400)):
    T=load(f);Bm=Y+2;phi=[]
    for w,ch in T:
        k=len(ch);# psi(2b)
        psi=[sum(phi[c][min(2*b,Y)] if 2*b<=Y else 10**12 for c in ch) for b in range(Y//2+1)]
        row=[]
        for y in range(Y+1):
            row.append(min((1+k)*b*b-b*y+psi[b] for b in range(Y//2+1)))
        phi.append(row)
    rows=[r[:200] for r in phi]
    N=len(T);print(f,N,'tropical rank',rank([[x%P for x in r] for r in rows]),'distinct',len({tuple(r) for r in rows}),flush=True)
