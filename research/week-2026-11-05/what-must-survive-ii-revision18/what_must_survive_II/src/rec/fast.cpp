// first differing energy shell of pairs of trees, by DP at random x modulo a prime. Input lines: two trees "n parents" alternately (parent<child). argv: Emax.
#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u;typedef __uint128_t U;const u P=(1ULL<<61)-1;
u mul(u a,u b){return (u)((U)a*b%P);}u pw(u a,u e){u r=1;while(e){if(e&1)r=mul(r,a);a=mul(a,a);e>>=1;}return r;}
int K;
vector<u> shell(const vector<int>&par,u x0,int lo){int n=par.size(),D=K;
 // f[v][a][e]
 vector<vector<vector<u>>> f(n,vector<vector<u>>(D+1,vector<u>(K+1,0)));
 for(int a=lo;a<=D;a++){u xa=pw(x0,a);for(int v=0;v<n;v++){f[v][a][0]=xa;}}
 for(int v=n-1;v>=1;v--){int p=par[v];
  for(int a=lo;a<=D;a++){vector<u> g(K+1,0);for(int b=lo;b<=D;b++){int c=(a-b)*(a-b);if(c>K)continue;for(int e=0;e+c<=K;e++)g[e+c]=(g[e+c]+f[v][b][e])%P;}
   vector<u> r(K+1,0);for(int i=0;i<=K;i++)if(f[p][a][i])for(int j=0;i+j<=K;j++)r[i+j]=(r[i+j]+mul(f[p][a][i],g[j]))%P;f[p][a]=r;}}
 vector<u> t(K+1,0);for(int a=lo;a<=D;a++)for(int e=0;e<=K;e++)t[e]=(t[e]+f[0][a][e])%P;return t;}
int main(int ac,char**av){K=atoi(av[1]);mt19937_64 R(12345);u xs[3]={R()%P,R()%P,R()%P};
 int n;vector<vector<int>> buf;while(scanf("%d",&n)==1){vector<int> p(n);for(auto&a:p)scanf("%d",&a);buf.push_back(p);
  if(buf.size()==2){int first=-1;
   for(int r=0;r<3&&first<0;r++){}
   vector<int> fd(3,-1);int best=K+1;for(int r=0;r<3;r++){auto a0=shell(buf[0],xs[r],0),a1=shell(buf[0],xs[r],1),b0=shell(buf[1],xs[r],0),b1=shell(buf[1],xs[r],1);for(int e=0;e<=K;e++){u A=(a0[e]+P-a1[e])%P,B=(b0[e]+P-b1[e])%P;if(A!=B){best=min(best,e);break;}}}
   printf("%d\n",best<=K?best:-1);buf.clear();}}
}
