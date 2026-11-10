# Fast free-tree enumeration using networkx's level-sequence iterator, printing "n parents".
import sys,warnings
warnings.filterwarnings("ignore")
from networkx.generators.nonisomorphic_trees import _next_rooted_tree,_next_tree,_split_tree
n=int(sys.argv[1]);out=sys.stdout
ls=list(range(n//2+1))+list(range(1,(n+1)//2))
buf=[]
while ls is not None:
    ls=_next_tree(ls)
    if ls is not None:
        last=[0]*(n+2);par=[0]*n
        for i,l in enumerate(ls):
            if i: par[i]=last[l-1]
            last[l]=i
        buf.append(f"{n} "+" ".join(map(str,par)))
        if len(buf)>20000: out.write("\n".join(buf)+"\n");buf=[]
        ls=_next_rooted_tree(ls)
if buf: out.write("\n".join(buf)+"\n")
