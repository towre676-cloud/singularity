// Energy shells of a tree: z on edges, sum z^2=e<=EM. Input: n parents (parent<child). Output: one line per tree with e vol count table hash and optional table.
#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u64;
int main(int ac,char**av){int EM=atoi(av[1]);bool pr=ac>2;int n;while(scanf("%d",&n)==1){vector<int> p(n);for(auto&x:p)scanf("%d",&x);vector<map<int,long long>> T(EM+1);vector<int> h(n,0),z(n,0);
 function<void(int,int)> rec=[&](int v,int left){if(v==n){int s=0,mn=1e9;for(int a:h){s+=a;mn=min(mn,a);}T[EM-left][s-n*mn]++;return;}
   for(int a=-(int)sqrt(left);a*a<=left;a++){h[v]=h[p[v]]+a;rec(v+1,left-a*a);}};
 h[0]=0;rec(1,EM);
 printf("%d",n);for(int e=0;e<=EM;e++){u64 H=1469598103934665603ULL;for(auto&kv:T[e]){H^=(u64)kv.first*1000003ULL+kv.second;H*=1099511628211ULL;}printf(" %llu",H);}puts("");
 if(pr)for(int e=0;e<=EM;e++)for(auto&kv:T[e])printf("%d %d %lld\n",e,kv.first,kv.second);
 fflush(stdout);}}
