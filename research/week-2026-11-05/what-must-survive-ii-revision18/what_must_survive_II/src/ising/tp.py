exec(open("mf.py").read().split("\nif __name__")[0])
c=Counter();ex=[];rows=[]
for n in range(8,31):
    for l in open(f'/root/wms/spine/d{n}.txt'):
        if not l.startswith('S2'):continue
        ps=[tuple(map(int,a.strip(',').split(','))) for a in l.split()[1:]];N=n-2
        T1,T2=T_of(ps[0])[0],T_of(ps[1])[0]
        s1,s2=spins(T1,N),spins(T2,N);ks=sorted(s1);r0=min(folds(T1,N))
        flip=[k for k in ks if s1[k]!=s2[k]]
        if ks[0] in flip: flip=[k for k in ks if k not in flip]
        qs=flip[0];r1=ks[0];nu=sum(1 for r in folds(T1,N) if r<r1)
        d=Counter(H3T(T1,N));d.subtract(H3T(T2,N));d={k:4*v for k,v in d.items() if v}
        top=max(d);pred=2*N-qs-r1;co=4*(2*r1-nu)/2*s1[r1]*s1[qs]*1
        # Sigma check
        sm=sum(s1[p] for p in ks if p<qs)
        if r0==r1:
            k_='end-unequal';okt=(top==pred and d[top]==4*r1*2*s1[r1]*s1[qs]/1 or top==pred and abs(d[top])==8*r1)
            c[(k_,'ok' if okt else 'FAIL')]+=1
            if not okt and len(ex)<5:ex.append((N,T1,T2,top,pred,d[top],r1))
        else:
            c[('end-equal','toppred' if top==pred else 'other')]+=1
            rows.append((N,top,pred,qs,r0,r1,d[top]))
        c[('sumzero',sm==0)]+=1
print(c);print(ex);print(rows[:25])
