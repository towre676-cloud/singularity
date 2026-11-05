"""Exact B and H_3 formulas, separated by the number of retained pendant edges."""
from collections import Counter
from itertools import combinations
import math
import networkx as nx

def build(p):
    T=nx.path_graph(len(p));v=len(p)
    for i,c in enumerate(p):
        for _ in range(c):T.add_edge(i,v);v+=1
    return T

def positions(p):
    m=len(p);n=m+sum(p);ell=sum(p);a=[];s=0
    for c in p[:-1]:s+=c+1;a.append(s)
    return n,ell,a

def data(p):
    n,ell,a=positions(p);m=len(p);A=Counter({1:ell,n-1:ell});B=Counter();C=Counter();D=Counter()
    for i,t in enumerate(a,1):
        A[t]+=1;A[n-t]+=1
        L=t-i;R=ell-L
        C[t-1]+=L;C[n-t-1]+=R
    for u,v in combinations(a,2):D[v-u]+=1
    B.update(D);B.update(C);B[n-2]+=math.comb(ell,2)
    return A,B,C,D

def h3(p):
    n,ell,a=positions(p);m=len(p);parts=[Counter() for _ in range(4)]
    def add(r,e,c=1):
        if c:parts[r][e]+=c
    # No pendant edges: three retained spine edges.
    for u,v,w in combinations(a,3):
        for e in (u-v+w,n-u+v-w,-u+v+w,n-u-v+w):add(0,e)
    # One pendant and two spine edges.
    for (i,u),(j,v) in combinations(enumerate(a,1),2):
        d=v-u;M=d-(j-i);Lj=v-j;Ri=ell-u+i
        for e,c in [(d+1,ell),(n+d-1,ell),(n-d-1,ell-M),(d-1,M),(u+v-1,Lj),(2*n-u-v-1,Ri)]:add(1,e,c)
    # Two pendants and one spine edge.
    for i,t in enumerate(a,1):
        L=t-i;R=ell-L
        for e,c in [(t-2,math.comb(L,2)),(n-t-2,math.comb(R,2)),(t,(ell-1)*L),(n-t,(ell-1)*R),(n+t-2,math.comb(ell,2)),(2*n-t-2,math.comb(ell,2))]:add(2,e,c)
    # Three pendant edges.
    for e,c in [(n-3,1),(2*n-3,1),(n-1,3)]:add(3,e,c*math.comb(ell,3))
    H=Counter()
    for c in parts:H.update(c)
    return H,parts

def elementary3(p):
    n,ell,a=positions(p);sides=[1]*ell+a;out=Counter()
    for s,t,u in combinations(sides,3):
        for a0 in (s,n-s):
          for b0 in (t,n-t):
            for c0 in (u,n-u):out[a0+b0+c0]+=1
    return out

def predicted_shell3(p):
    n,_,_=positions(p);Q=elementary3(p);H,_=h3(p)
    for e,c in H.items():Q[e]+=c;Q[e+n]-=c
    return Counter({e:c for e,c in Q.items() if c})
