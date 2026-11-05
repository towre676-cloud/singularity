exec(open('fl.py').read().split("tot={}")[0])
x=sp.Symbol('x')
def build(I,O,v,u):
    T={k*v+i for k in range(u) for i in I}|{k*v for k in O};return T
for I,O,v,u in [({1},{1},3,3),({1},{1},4,3),({1},{1},5,3),({1},{1},3,4),({1},{3},3,4),({1},{1},3,5),({1,2},{1},4,3),({1,3},{1},5,3),({2},{1},5,3),({1},{1,2},3,4)]:
    N=u*v;T1=build(I,O,v,u);T2=build(I,{u-k for k in O},v,u)
    h1,h2=H3(p_of(T1,N)),H3(p_of(T2,N))
    d=sum((h1[k]-h2[k])*x**k for k in set(h1)|set(h2))
    print(I,O,v,u,sp.factor(d))
