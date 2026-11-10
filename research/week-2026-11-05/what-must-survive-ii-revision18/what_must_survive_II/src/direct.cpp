// direct volume-by-volume comparison of two cubic graphs: for V up to VM, histogram of energies, exact 64-bit counts.
#include <bits/stdc++.h>
using namespace std;
int n,m;vector<vector<int>> nb[2];int VM;
map<int,long long> H[2][40];
vector<int> lower[2][32];
void go(int g){ vector<int> h(n,0);
 function<void(int,int,int)> rec=[&](int v,int vol,int en){ if(v==n){H[g][vol][en]++;return;}
  for(int s=0;vol+s<=VM;s++){int e=3*s*s;for(int w:lower[g][v])e-=2*s*h[w];h[v]=s;rec(v+1,vol+s,en+e);}h[v]=0;};
 rec(0,0,0);}
int main(int ac,char**av){VM=atoi(av[2]);FILE*f=fopen(av[1],"r");for(int g=0;g<2;g++){fscanf(f,"%d %d",&n,&m);for(int i=0;i<m;i++){int a,b;fscanf(f,"%d %d",&a,&b);if(a<b)swap(a,b);lower[g][a].push_back(b);}}
 for(int g=0;g<2;g++)go(g);
 for(int V=0;V<=VM;V++){int diff=0;set<int> ks;for(auto&kv:H[0][V])ks.insert(kv.first);for(auto&kv:H[1][V])ks.insert(kv.first);map<int,long long> d;for(int k:ks){long long x=H[0][V].count(k)?H[0][V][k]:0,y=H[1][V].count(k)?H[1][V][k]:0;if(x!=y){diff++;d[k]=x-y;}}
  printf("V=%d energies differing=%d",V,diff);int c=0;for(auto&kv:d){if(c++<8)printf(" e%d:%lld",kv.first,kv.second);}puts("");fflush(stdout);}
}
