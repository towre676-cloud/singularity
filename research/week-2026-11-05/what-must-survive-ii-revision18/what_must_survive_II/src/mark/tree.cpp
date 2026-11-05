// Height series of a tree via exact DP at random q modulo p, truncated at volume V0. Output per tree: V-sequence fingerprint.
#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u64;typedef __uint128_t u128;const u64 P=(1ULL<<61)-1;
inline u64 mul(u64 a,u64 b){return (u128)a*b%P;}inline u64 add(u64 a,u64 b){u64 c=a+b;return c>=P?c-P:c;}
u64 pw(u64 a,u64 e){u64 r=1;while(e){if(e&1)r=mul(r,a);a=mul(a,a);e>>=1;}return r;}
int main(int ac,char**av){int V0=atoi(av[1]);vector<u64> Q={1000003ULL,987654323ULL};vector<vector<u64>> tb;for(u64 q:Q){vector<u64> t(2*V0*V0+1);t.assign(V0+1,0);for(int d=0;d<=V0;d++)t[d]=pw(q,(u64)d*d);tb.push_back(t);}
 int n;while(scanf("%d",&n)==1){vector<int> par(n);for(int i=0;i<n;i++)scanf("%d",&par[i]);printf("%d",n);
  for(auto&tt:tb){ // nodes listed so parent index < child index
   vector<vector<vector<u64>>> F(n,vector<vector<u64>>(V0+1,vector<u64>(V0+1,0)));
   for(int v=0;v<n;v++)for(int h=0;h<=V0;h++)F[v][h][h]=1;
   for(int v=n-1;v>=1;v--){int p=par[v];
     // message m[h][w]=sum_{h'} q^{(h-h')^2} F[v][h'][w]
     vector<vector<u64>> m(V0+1,vector<u64>(V0+1,0));for(int h=0;h<=V0;h++)for(int g=0;g<=V0;g++){u64 c=tt[abs(h-g)];for(int w=g;w<=V0;w++)if(F[v][g][w])m[h][w]=add(m[h][w],mul(c,F[v][g][w]));}
     for(int h=0;h<=V0;h++){vector<u64> r(V0+1,0);for(int a=h;a<=V0;a++)if(F[p][h][a])for(int b=0;a+b<=V0;b++)if(m[h][b])r[a+b]=add(r[a+b],mul(F[p][h][a],m[h][b]));F[p][h]=r;}
     F[v].clear();}
   vector<u64> tot(V0+1,0);for(int h=0;h<=V0;h++)for(int w=0;w<=V0;w++)tot[w]=add(tot[w],F[0][h][w]);
   for(int w=0;w<=V0;w++)printf(" %llu",tot[w]);}
  puts("");}}
