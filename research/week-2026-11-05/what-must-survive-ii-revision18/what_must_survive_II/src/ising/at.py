import subprocess,sys,collections,json
res={}
for n in range(9,20):
    g=subprocess.Popen(['python3','/root/wms/cat/genp.py',str(n)],stdout=subprocess.PIPE)
    o=subprocess.run(['/root/wms/tree/shell','3'],stdin=g.stdout,capture_output=True,text=True).stdout
    inp=subprocess.run(['python3','/root/wms/cat/genp.py',str(n)],capture_output=True,text=True).stdout.strip().split('\n')
    cl=collections.defaultdict(list)
    for L,I in zip(o.strip().split('\n'),inp):
        w=L.split();cl[tuple(w[1:])].append(I)
    def iscat(I):
        v=list(map(int,I.split()));n=v[0];p=v[1:];deg=[0]*n
        for i in range(1,n):deg[i]+=1;deg[p[i]]+=1
        idg=[0]*n
        for i in range(1,n):
            if deg[i]>1 and deg[p[i]]>1:idg[i]+=1;idg[p[i]]+=1
        return max(idg)<=2
    col=[v for v in cl.values() if len(v)>1];cc=sum(1 for v in col if any(iscat(i) for i in v))
    res[n]=dict(trees=len(inp),classes=len(col),with_cat=cc);print(n,res[n],flush=True)
json.dump(res,open('at.json','w'))
