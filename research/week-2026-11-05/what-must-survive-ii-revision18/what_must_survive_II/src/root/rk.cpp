#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u;typedef __uint128_t U;const u P=(1ULL<<61)-1;
static inline u mul(u a,u b){U t=(U)a*b;u r=(u)(t&P)+(u)(t>>61);if(r>=P)r-=P;return r;}
u pw(u a,u e){u r=1;while(e){if(e&1)r=mul(r,a);a=mul(a,a);e>>=1;}return r;}
int main(int ac,char**av){int V=atoi(av[1]),nq=atoi(av[2]),A=atoi(av[3]);int N;scanf("%d",&N);vector<vector<int>> ch(N);vector<int> W(N);for(int i=0;i<N;i++){int k;scanf("%d %d",&W[i],&k);ch[i].resize(k);for(auto&c:ch[i])scanf("%d",&c);}
 int D=V;int perq=(A+1)*V;vector<vector<u>> rows(N,vector<u>());
 mt19937_64 R(99);vector<u> inv(V+2,1);for(int i=1;i<=V+1;i++)inv[i]=pw(i,P-2);
 for(int qi=0;qi<nq;qi++){u q=R()%P;vector<u> qq(2*D*D+4*D*D+1);int M=(D+1)*(D+1);vector<u> qs(M+1);qs[0]=1;for(int i=1;i<=M;i++)qs[i]=mul(qs[i-1],q);
  // G[t][a][k], a in 0..D
  vector<vector<u>> G(N);int S=(D+1)*(V+1);
  for(int t=0;t<N;t++){vector<u> g(S,0);
    for(int b=0;b<=D;b++){vector<u> s(V+1,0);if(b<=V)s[b]=1;for(int c:ch[t]){vector<u> n(V+1,0);const u*gc=&G[c][b*(V+1)];for(int i=0;i<=V;i++)if(s[i])for(int j=0;i+j<=V;j++)if(gc[j]){n[i+j]+=mul(s[i],gc[j]);if(n[i+j]>=P)n[i+j]-=P;}s.swap(n);}
     for(int a=0;a<=D;a++){u w=qs[(a-b)*(a-b)];for(int k=0;k<=V;k++)if(s[k]){g[a*(V+1)+k]=(g[a*(V+1)+k]+mul(w,s[k]))%P;}}}
    G[t].swap(g);
    for(int a=0;a<=A;a++){const u*gg=&G[t][a*(V+1)];u i0=pw(gg[0],P-2);vector<u> h(V+1),L(V+1,0);for(int k=0;k<=V;k++)h[k]=mul(gg[k],i0);
      for(int k=1;k<=V;k++){u s=mul(k,h[k]);for(int j=1;j<k;j++){s=(s+P-mul(mul(j,L[j]),h[k-j]))%P;}L[k]=mul(s,inv[k]);rows[t].push_back(L[k]);}}
   }
 }
 for(auto&r:rows)r.push_back(1);
 // rank incremental in order of weight, report rank per weight
 int C=rows[0].size();vector<int> pivcol;vector<vector<u>> piv;int r=0;int cw=1;int cnt=0;
 for(int t=0;t<N;t++){if(W[t]!=cw){printf("weight<=%d trees=%d rank=%d\n",cw,t,r);fflush(stdout);cw=W[t];}
  auto v=rows[t];for(size_t p=0;p<piv.size();p++){u f=v[pivcol[p]];if(f){const auto&pp=piv[p];for(int i=0;i<C;i++)if(pp[i]){u m=mul(f,pp[i]);v[i]=v[i]>=m?v[i]-m:v[i]+P-m;}}}
  int c=-1;for(int i=0;i<C;i++)if(v[i]){c=i;break;}
  if(c>=0){u iv=pw(v[c],P-2);for(auto&x:v)x=mul(x,iv);piv.push_back(v);pivcol.push_back(c);r++;}else{printf("DEPENDENT tree %d weight %d\n",t,W[t]);}
  rows[t].clear();rows[t].shrink_to_fit();}
 printf("weight<=%d trees=%d rank=%d cols=%d\n",cw,N,r,C);}
