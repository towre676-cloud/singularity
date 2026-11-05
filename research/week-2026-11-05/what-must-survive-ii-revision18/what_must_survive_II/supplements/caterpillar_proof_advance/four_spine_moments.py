import sympy as s,itertools
n,a,b,c=s.symbols('n a b c',real=True)
candidates=[[a,b,c],[a,b,n-c],[a,c,n-b],[b,c,n-a]]
def moment(points,r):
    ell=n-4;v=sum((y-x)**r for x,y in itertools.combinations(points,2))
    for i,x in enumerate(points,1):
        L=x-i;R=ell-L;v+=L*(x-1)**r+R*(n-x-1)**r
    return s.expand(v)
if __name__=='__main__':
 for i,j in itertools.combinations(range(4),2):
    print(i,j,'M2=',s.factor(moment(candidates[i],2)-moment(candidates[j],2)))
