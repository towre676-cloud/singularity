// Collision hunt on all trees of one order. Reads "n p1..pn". Stage 0: S1,D,J. Stage 1: M to volume 5 at 2 q's. Stage 2: shells<=3. Stage 3: volume 9. Stage 4: shells<=5. Stage 5: volume 13.
#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u64;typedef __uint128_t u128;const u64 P=(1ULL<<61)-1;
inline u64 mul(u64 a,u64 b){return (u128)a*b%P;}inline u64 add(u64 a,u64 b){u64 c=a+b;return c>=P?c-P:c;}
u64 pw(u64 a,u64 e){u64 r=1;while(e){if(e&1)r=mul(r,a);a=mul(a,a);e>>=1;}return r;}
int n;typedef array<uint8_t,32> Rec;
u64 mix(u64 h,u64 x){h^=x+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);return h*1099511628211ULL;}
u64 f0(const uint8_t*p){int sz[32],deg[32];for(int i=0;i<n;i++){sz[i]=1;deg[i]=0;}for(int i=n-1;i>=1;i--){sz[p[i]]+=sz[i];deg[i]++;deg[p[i]]++;}
 int S[33]={0},D[33]={0},J[66]={0};for(int i=1;i<n;i++){int a=min(sz[i],n-sz[i]);S[a]++;J[deg[i]+deg[p[i]]]++;}for(int i=0;i<n;i++)D[deg[i]]++;u64 h=1;for(int i=0;i<33;i++)h=mix(h,S[i]);for(int i=0;i<33;i++)h=mix(h,D[i]);for(int i=0;i<66;i++)h=mix(h,J[i]);return h;}
u64 volfp(const uint8_t*p,int V0){u64 hh=7;static vector<u64> Qs={1000003ULL,987654323ULL};for(u64 q:Qs){vector<u64> t(V0+1);for(int d=0;d<=V0;d++)t[d]=pw(q,(u64)d*d);
  vector<vector<vector<u64>>> F(n,vector<vector<u64>>(V0+1,vector<u64>(V0+1,0)));for(int v=0;v<n;v++)for(int h=0;h<=V0;h++)F[v][h][h]=1;
  for(int v=n-1;v>=1;v--){int pp=p[v];vector<vector<u64>> m(V0+1,vector<u64>(V0+1,0));for(int h=0;h<=V0;h++)for(int g=0;g<=V0;g++){u64 c=t[abs(h-g)];for(int w=g;w<=V0;w++)if(F[v][g][w])m[h][w]=add(m[h][w],mul(c,F[v][g][w]));}
   for(int h=0;h<=V0;h++){vector<u64> r(V0+1,0);for(int a=h;a<=V0;a++)if(F[pp][h][a])for(int b=0;a+b<=V0;b++)if(m[h][b])r[a+b]=add(r[a+b],mul(F[pp][h][a],m[h][b]));F[pp][h]=r;}}
  for(int w=0;w<=V0;w++){u64 s=0;for(int h=0;h<=V0;h++)s=add(s,F[0][h][w]);hh=mix(hh,s);}}return hh;}
u64 shfp(const uint8_t*p,int EM){vector<map<int,long long>> T(EM+1);int h[32];h[0]=0;function<void(int,int)> rec=[&](int v,int left){if(v==n){int s=0,mn=1e9;for(int i=0;i<n;i++){s+=h[i];mn=min(mn,h[i]);}T[EM-left][s-n*mn]++;return;}for(int a=-(int)sqrt(left);a*a<=left;a++){h[v]=h[p[v]]+a;rec(v+1,left-a*a);}};rec(1,EM);u64 H=11;for(int e=0;e<=EM;e++)for(auto&kv:T[e]){H=mix(H,e);H=mix(H,kv.first);H=mix(H,kv.second);}return H;}
int main(int ac,char**av){vector<Rec> R;vector<u64> K;int nn;while(scanf("%d",&nn)==1){n=nn;Rec r;r.fill(0);for(int i=0;i<n;i++){int x;scanf("%d",&x);r[i]=x;}R.push_back(r);K.push_back(f0(r.data()));}
 size_t N=R.size();vector<uint32_t> idx(N);iota(idx.begin(),idx.end(),0);sort(idx.begin(),idx.end(),[&](uint32_t a,uint32_t b){return K[a]<K[b];});
 vector<vector<uint32_t>> G;for(size_t i=0;i<N;){size_t j=i;while(j<N&&K[idx[j]]==K[idx[i]])j++;if(j-i>1)G.emplace_back(idx.begin()+i,idx.begin()+j);i=j;}
 auto stat=[&](const char*s){size_t ex=0;for(auto&g:G)ex+=g.size()-1;printf("n=%d trees=%zu after %s: classes=%zu excess=%zu\n",n,N,s,G.size(),ex);fflush(stdout);};stat("S1,D,J");
 auto refine=[&](function<u64(const uint8_t*)> f,const char*s){vector<vector<uint32_t>> H;for(auto&g:G){map<u64,vector<uint32_t>> b;for(uint32_t i:g)b[f(R[i].data())].push_back(i);for(auto&kv:b)if(kv.second.size()>1)H.push_back(kv.second);}G.swap(H);stat(s);};
 refine([&](const uint8_t*p){return volfp(p,4);},"volume 4");refine([&](const uint8_t*p){return shfp(p,3);},"shells<=3");refine([&](const uint8_t*p){return volfp(p,8);},"volume 8");refine([&](const uint8_t*p){return shfp(p,5);},"shells<=5");refine([&](const uint8_t*p){return volfp(p,12);},"volume 12");
 for(size_t i=0;i<G.size()&&i<20;i++){printf("SURVIVOR class:");for(uint32_t x:G[i]){printf(" [");for(int j=0;j<n;j++)printf("%d ",R[x][j]);printf("]");}puts("");}
}
