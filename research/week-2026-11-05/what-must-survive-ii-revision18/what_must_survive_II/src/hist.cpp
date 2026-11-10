// exact height histogram of a cubic graph: lines "V e count"
#include <bits/stdc++.h>
using namespace std;int main(int c,char**v){int VM=atoi(v[1]);int n,m;while(scanf("%d %d",&n,&m)==2){vector<vector<int>> lo(n);for(int i=0;i<m;i++){int a,b;scanf("%d %d",&a,&b);if(a<b)swap(a,b);lo[a].push_back(b);}
 vector<map<int,long long>> H(VM+1);vector<int> h(n,0);function<void(int,int,int)> r=[&](int u,int vol,int en){if(u==n){H[vol][en]++;return;}for(int s=0;vol+s<=VM;s++){int e=3*s*s;for(int w:lo[u])e-=2*s*h[w];h[u]=s;r(u+1,vol+s,en+e);}h[u]=0;};r(0,0,0);
 printf("G %d\n",n);for(int V=0;V<=VM;V++)for(auto&k:H[V])printf("%d %d %lld\n",V,k.first,k.second);}}
