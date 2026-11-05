// Stable tower series: T_G = sum_v sum_{s>=0 on G-v} y^{kappa} w^{nu}, kappa=6|s|+2S, nu=3|s|^2+2|s|S+E'(s), S=sum over N(v) of s, E'=3 sum s^2-2 sum_{edges in G-v} s s'.
// Levels |s|<=R. Output per graph and level r: sorted histogram hash; with mode "print" the table.
#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u64;
int main(int ac,char**av){int R=atoi(av[1]);bool pr=ac>2;int n,m;int id=0;while(scanf("%d %d",&n,&m)==2){vector<vector<int>> adj(n);vector<pair<int,int>> E(m);for(auto&p:E){scanf("%d %d",&p.first,&p.second);adj[p.first].push_back(p.second);adj[p.second].push_back(p.first);}
 vector<map<pair<int,int>,long long>> T(R+1);vector<int> s(n,0);
 for(int v=0;v<n;v++){vector<char> nb(n,0);for(int w:adj[v])nb[w]=1;vector<int> vs;for(int w=0;w<n;w++)if(w!=v)vs.push_back(w);
  function<void(int,int)> rec=[&](int i,int left){ if(i==(int)vs.size()){int r=0,S=0;long long Ep=0;for(int w:vs){r+=s[w];if(nb[w])S+=s[w];Ep+=3*s[w]*s[w];}for(auto&p:E)if(p.first!=v&&p.second!=v)Ep-=2*s[p.first]*s[p.second];T[r][{6*r+2*S,3*r*r+2*r*S+(int)Ep}]++;return;}
   for(int a=0;a<=left;a++){s[vs[i]]=a;rec(i+1,left-a);}s[vs[i]]=0;};
  rec(0,R);}
 printf("G %d %d",id++,n);for(int r=0;r<=R;r++){u64 h=1469598103934665603ULL;for(auto&kv:T[r]){for(long long x:{(long long)kv.first.first,(long long)kv.first.second,kv.second}){h^=(u64)x+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2);h*=1099511628211ULL;}}printf(" %llu",h);}puts("");
 if(pr)for(int r=0;r<=R;r++)for(auto&kv:T[r])printf("%d %d %d %lld\n",r,kv.first.first,kv.first.second,kv.second);
 fflush(stdout);}}
