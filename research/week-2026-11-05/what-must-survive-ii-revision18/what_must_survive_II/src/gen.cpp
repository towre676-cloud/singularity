// Own generator of connected leafless subcubic simple graphs (no external graph tools).
// Moves: ear (l>=0 internal vertices) between distinct degree-2 vertices; bridge-path join of two graphs.
// Completeness: subcubic 2-edge-connected graphs have open ear decompositions; a bridge path splits into two leafless graphs.
#include <bits/stdc++.h>
using namespace std;
struct G{int n; vector<pair<int,int>> e;};
static string canon(const G&g){
  int n=g.n; vector<vector<int>> a(n); for(auto&p:g.e){a[p.first].push_back(p.second);a[p.second].push_back(p.first);}
  // colour refinement + individualisation search, minimum edge code
  string best; 
  function<void(vector<int>)> rec=[&](vector<int> col){
    // refine
    while(true){
      vector<pair<pair<int,vector<int>>,int>> sig(n);
      for(int v=0;v<n;v++){vector<int> c;for(int w:a[v])c.push_back(col[w]);sort(c.begin(),c.end());sig[v]={{col[v],c},v};}
      sort(sig.begin(),sig.end());
      vector<int> nc(n);int cur=0;
      for(int i=0;i<n;i++){ if(i&&sig[i].first!=sig[i-1].first)cur=i; nc[sig[i].second]=cur;}
      bool same=(nc==col); col=nc; if(same)break;
    }
    map<int,vector<int>> cls; for(int v=0;v<n;v++)cls[col[v]].push_back(v);
    vector<int>* tgt=nullptr; for(auto&kv:cls) if(kv.second.size()>1){tgt=&kv.second;break;}
    if(!tgt){
      vector<pair<int,int>> ed; for(auto&p:g.e){int x=col[p.first],y=col[p.second]; if(x>y)swap(x,y); ed.push_back({x,y});}
      sort(ed.begin(),ed.end());
      string s; s.push_back(char(n)); for(auto&p:ed){s.push_back(char(p.first));s.push_back(char(p.second));}
      if(best.empty()||s<best)best=s; return;
    }
    vector<int> t=*tgt; int base=col[t[0]];
    for(int v:t){ vector<int> c2=col; // individualise v: keep v at base, push others up
      for(int w:t) if(w!=v) c2[w]=base+1; rec(c2);}
  };
  rec(vector<int>(n,0)); return best;
}
static G fromcode(const string&s){G g;g.n=s[0];for(size_t i=1;i+1<s.size();i+=2)g.e.push_back({s[i],s[i+1]});return g;}
int main(int ac,char**av){int N=atoi(av[1]);
  vector<map<string,int>> L(N+1); deque<string> q;
  auto add=[&](const G&g){ string c=canon(g); if(!L[g.n].count(c)){L[g.n][c]=1;q.push_back(c);} };
  // process by increasing edges: BFS closure; joins handled by pairing with all known
  for(int k=3;k<=N;k++){G g;g.n=k;for(int i=0;i<k;i++)g.e.push_back({i,(i+1)%k});add(g);}
  vector<string> done;
  while(!q.empty()){
    string c=q.front();q.pop_front();G g=fromcode(c);done.push_back(c);
    vector<int> d(g.n,0);for(auto&p:g.e){d[p.first]++;d[p.second]++;}
    vector<int> two;for(int v=0;v<g.n;v++)if(d[v]==2)two.push_back(v);
    set<pair<int,int>> ad;for(auto&p:g.e){ad.insert(p);ad.insert({p.second,p.first});}
    for(size_t i=0;i<two.size();i++)for(size_t j=i+1;j<two.size();j++){
      int u=two[i],v=two[j];
      for(int l=0;g.n+l<=N;l++){ if(l==0&&ad.count({u,v}))continue;
        G h=g;int prev=u;for(int t=0;t<l;t++){int w=h.n++;h.e.push_back({prev,w});prev=w;}h.e.push_back({prev,v});add(h);}
    }
    // joins with all done graphs (including itself)
    size_t lim=done.size();
    for(size_t di=0;di<lim;di++){G o=fromcode(done[di]);
      if(g.n+o.n>N)continue;
      vector<int> od(o.n,0);for(auto&p:o.e){od[p.first]++;od[p.second]++;}
      for(int u:two)for(int w=0;w<o.n;w++)if(od[w]==2)
        for(int l=0;g.n+o.n+l<=N;l++){
          G h=g;int off=h.n;h.n+=o.n;for(auto&p:o.e)h.e.push_back({p.first+off,p.second+off});
          int prev=u;for(int t=0;t<l;t++){int x=h.n++;h.e.push_back({prev,x});prev=x;}h.e.push_back({prev,w+off});add(h);}
    }
  }
  for(int n=3;n<=N;n++){fprintf(stderr,"n=%d %zu\n",n,L[n].size());
    for(auto&kv:L[n]){G g=fromcode(kv.first);printf("%d %zu",g.n,g.e.size());for(auto&p:g.e)printf(" %d %d",p.first,p.second);puts("");}}
}
