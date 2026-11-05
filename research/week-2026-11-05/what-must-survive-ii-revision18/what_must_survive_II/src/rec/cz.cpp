// All trees of order n from stdin ("n parents"): does any non-caterpillar share (A,B,degree multiset) with a caterpillar? Also counts mixtures at (A,B).
#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u;
int n;u R1[256],R2[256],RD[256];u sm(){static u s=88172645463325252ULL;s^=s<<13;s^=s>>7;s^=s<<17;return s*0x9E3779B97F4A7C15ULL;}
struct K{u ab,d;};
K key(const vector<int>&par){vector<int> sz(n,1),deg(n,0);for(int i=n-1;i>=1;i--){sz[par[i]]+=sz[i];deg[i]++;deg[par[i]]++;}
 u a=0,b=0,d=0;for(int v=0;v<n;v++)d+=RD[deg[v]];
 // ancestor flags via Euler: parents<children; tin/tout from sizes need dfs; use anc walk
 for(int i=1;i<n;i++)a+=R1[min(sz[i],n-sz[i])];
 static vector<int> anc;anc.assign(n,0);
 // b(e,f): edges identified by child. e ancestor of f => sz[e]-sz[f], else n-sz[e]-sz[f]
 u tot=0;u ss=0;for(int i=1;i<n;i++){ }
 for(int f=1;f<n;f++){vector<char> isanc(n,0);int v=par[f];while(v!=0){isanc[v]=1;v=par[v];}
  for(int e=1;e<f;e++){if(isanc[e])b+=R2[sz[e]-sz[f]];else b+=R2[n-sz[e]-sz[f]];}}
 return {a*0x100000001B3ULL+b,d};}
bool iscat(const vector<int>&par){vector<int> deg(n,0);for(int i=1;i<n;i++){deg[i]++;deg[par[i]]++;}vector<int> id(n,0);for(int i=1;i<n;i++)if(deg[i]>1&&deg[par[i]]>1){id[i]++;id[par[i]]++;}for(int v=0;v<n;v++)if(id[v]>2)return false;return true;}
unordered_set<u> ab,abd;vector<int> cur;
void gen(int left){if(left==0){if(cur.size()<2||cur[0]<1||cur.back()<1)return;int m=cur.size();vector<int> par(n);for(int i=1;i<m;i++)par[i]=i-1;int k=m;for(int i=0;i<m;i++)for(int j=0;j<cur[i];j++)par[k++]=i;K x=key(par);ab.insert(x.ab);abd.insert(x.ab*31+x.d);return;}for(int x=0;x<left;x++){cur.push_back(x);gen(left-x-1);cur.pop_back();}}
int main(int ac,char**av){n=atoi(av[1]);for(int i=0;i<256;i++){R1[i]=sm();R2[i]=sm();RD[i]=sm();}gen(n);long long tot=0,non=0,mix=0,eq=0;int m;vector<int> p;while(scanf("%d",&m)==1){p.resize(m);for(auto&a:p)if(scanf("%d",&a)!=1)return 1;tot++;if(iscat(p))continue;non++;K x=key(p);if(ab.count(x.ab)){mix++;if(abd.count(x.ab*31+x.d)){eq++;printf("EQUAL");for(int a:p)printf(" %d",a);puts("");fflush(stdout);}}}printf("n=%d trees=%lld noncat=%lld mixAB=%lld equalAll=%lld\n",n,tot,non,mix,eq);}
