# Certified reconstruction: proved l1 majorants for every coefficient, then CRT uniqueness at p1*p2.
# Denominators are proved: Theta has integer coefficients, b_Q=Theta+sum (num/den) prod Theta, and -1/2 log Z_v has denominator dividing 2*lcm(1..V).
import sys,json,math
from fractions import Fraction as Fr
from analyze import pats
f1,f2,f3,clf,out,rowsout=sys.argv[1:7];P1=2**61-1;P2=2**61-31;P3=2**60-93;Q=pats(f1+'.pats')
VM=max(int(l.split()[0]) for l in open(f1))
def mul(a,b):
    r=[0]*(VM+1)
    for i,x in enumerate(a):
        if x:
            for j,y in enumerate(b):
                if i+j>VM:break
                r[i+j]+=x*y
    return r
def inv1(a): # majorant of 1/(1+u) where |u|<=a, a[0]=0 part: a is series with a[0]=1
    u=[0]+a[1:];r=[1]+[0]*VM;t=[1]+[0]*VM
    for _ in range(VM):
        t=mul(t,u);r=[x+y for x,y in zip(r,t)]
    return r
# M dominates every B(h): B(0)[t]=-(sq'+s0), B(h)[t]=2B(0)[t]+sq'+s
M=[1]+[0]*VM
for t in range(1,VM+1):
    sq=mul(M,M)
    sqp=sum(M[i]*M[t-i] for i in range(1,t))
    s=sum(sq[t-h] for h in range(1,t+1))
    M[t]=3*(sqp+s)
M3=mul(mul(M,M),M)
Z=[0]*(VM+1)
for h in range(0,VM+1):
    for i in range(0,VM+1-h): Z[i+h]+=M3[i]
Z[0]=1
IZ=inv1(Z);IM=inv1(M)
T=mul(mul(Z,IM),IM)
Fh=list(T);Fh[0]=2   # F(a,b)[0]=q^{-2ab}-1 has l1 norm at most 2; higher coefficients bounded by T
pb=mul(M3,IZ);Ph=[0]*(VM+1)
for h in range(0,VM+1):
    for i in range(0,VM+1-h): Ph[i+h]+=pb[i]
Ph[0]=1  # p(h) at order 0 only for h=0, value 1
def power(a,n):
    r=[1]+[0]*VM
    for _ in range(n): r=mul(r,a)
    return r
cache={}
def Th(k,E):
    if (k,E) not in cache: cache[(k,E)]=mul(power(Ph,k),power(Fh,E))
    return cache[(k,E)]
cl={}
for l in open(clf):
    w=list(map(int,l.split()));cl.setdefault(w[0],[]).append((w[1],w[2],w[4:]))
Dcol={};Bcol={}
for j,q in enumerate(Q):
    b=list(Th(q[0],q[1]));D=1
    for num,den,ty in cl.get(j,[]):
        D=D*den//math.gcd(D,den);t=[1]+[0]*VM
        for x in ty: t=mul(t,Th(Q[x][0],Q[x][1]))
        for i in range(VM+1): b[i]+=abs(num)*t[i]  # den>=1 only reduces
    Dcol[j+1]=D;Bcol[j+1]=b
# n column: log series majorant
u=[0]+Z[1:];lg=[0]*(VM+1);pw=[1]+[0]*VM
for n in range(1,VM+1):
    pw=mul(pw,u)
    for i in range(VM+1): lg[i]+=pw[i]   # dropping 1/n only enlarges
L=2
for i in range(1,VM+1): L=L*i//math.gcd(L,i)
Dcol[0]=L;Bcol[0]=lg
mod=P1*P2*P3;imax=0;n=0;bad=0
def crt(a,b,c):
    t=(b-a)*pow(P1,-1,P2)%P2;x=a+P1*t
    u=(c-x)*pow(P1*P2,-1,P3)%P3;x=x+P1*P2*u
    return x-mod if x>mod//2 else x
def rd(f):
    o={}
    for l in open(f):
        w=l.split();o[(int(w[0]),int(w[1]))]={int(w[3+2*i]):int(w[4+2*i]) for i in range(int(w[2]))}
    return o
d2=rd(f2);d3=rd(f3);O=open(rowsout,'w');Lall=1;seen2=0
for l in open(f1):
    w=l.split();v,e,nz=int(w[0]),int(w[1]),int(w[2]);a1={int(w[3+2*i]):int(w[4+2*i]) for i in range(nz)};a2=d2[(v,e)];a3=d3[(v,e)]
    assert set(a1)==set(a2)==set(a3);seen2+=1
    out_=[]
    for c,a in a1.items():
        D=Dcol[c];x=crt(a*D%P1,a2[c]*D%P2,a3[c]*D%P3);lim=D*Bcol[c][v]
        n+=1;imax=max(imax,abs(x))
        if abs(x)>lim or lim*2>=mod: bad+=1
        fr=Fr(x,D);out_.append(f"{c} {fr.numerator} {fr.denominator}")
    O.write(f"{v} {e} {len(out_)} "+" ".join(out_)+"\n")
assert seen2==len(d2)==len(d3);O.close()
res={"entries":n,"violations":bad,"max_recovered_scaled_numerator":imax,"max_proved_bound_bits":max(math.log2(max(1,Dcol[c]*Bcol[c][v])) for c in Bcol for v in range(VM+1) if Bcol[c][v]),"crt_modulus_bits":math.log2(mod),"V":VM}
print(res);json.dump(res,open(out,'w'),indent=1)
