// Loop-series engine for L_G(x,q)=sum_h x^{|h|} q^{h^T(3I-A)h}, G cubic.
// log L_G = -(n/2) log Z_v + sum_{Q connected leafless} N_Q(G) b_Q(x,q).
#include <bits/stdc++.h>
using namespace std; typedef unsigned long long u64; typedef __uint128_t u128;
u64 P=(1ULL<<61)-1;
inline u64 mul(u64 a,u64 b){return (u128)a*b%P;} inline u64 add(u64 a,u64 b){u64 c=a+b;return c>=P?c-P:c;} inline u64 sub(u64 a,u64 b){return a>=b?a-b:a+P-b;}
u64 pw(u64 a,u64 e){u64 r=1;while(e){if(e&1)r=mul(r,a);a=mul(a,a);e>>=1;}return r;} u64 inv(u64 a){return pw(a,P-2);}
int VM; typedef vector<u64> S;
S smul(const S&a,const S&b){S c(VM+1,0);for(int i=0;i<=VM;i++)if(a[i])for(int j=0;i+j<=VM;j++)if(b[j])c[i+j]=add(c[i+j],mul(a[i],b[j]));return c;}
S sinv(const S&a){S c(VM+1,0);u64 ia=inv(a[0]);c[0]=ia;for(int n=1;n<=VM;n++){u64 s=0;for(int i=1;i<=n;i++)s=add(s,mul(a[i],c[n-i]));c[n]=mul(sub(0,s),ia);}return c;}
S slog(const S&a){ // a[0]=1
  S c(VM+1,0);for(int n=1;n<=VM;n++){u64 s=mul(a[n],n);for(int k=1;k<n;k++)s=sub(s,mul(mul(c[k],k),a[n-k]));c[n]=mul(s,inv(n));}return c;}
struct Pat{int n,m;vector<pair<int,int>> e;vector<vector<int>> nb;vector<int> ord;int cutmin;};
vector<Pat> pats; map<string,int> idx;
string canon(int n,const vector<pair<int,int>>&E){
  vector<vector<int>> a(n);for(auto&p:E){a[p.first].push_back(p.second);a[p.second].push_back(p.first);}
  string best;function<void(vector<int>)> rec=[&](vector<int> col){
    while(true){vector<pair<pair<int,vector<int>>,int>> sig(n);
      for(int v=0;v<n;v++){vector<int> c;for(int w:a[v])c.push_back(col[w]);sort(c.begin(),c.end());sig[v]={{col[v],c},v};}
      sort(sig.begin(),sig.end());vector<int> nc(n);int cur=0;
      for(int i=0;i<n;i++){if(i&&sig[i].first!=sig[i-1].first)cur=i;nc[sig[i].second]=cur;}
      bool same=(nc==col);col=nc;if(same)break;}
    map<int,vector<int>> cls;for(int v=0;v<n;v++)cls[col[v]].push_back(v);
    vector<int>*tgt=nullptr;for(auto&kv:cls)if(kv.second.size()>1){tgt=&kv.second;break;}
    if(!tgt){vector<pair<int,int>> ed;for(auto&p:E){int x=col[p.first],y=col[p.second];if(x>y)swap(x,y);ed.push_back({x,y});}
      sort(ed.begin(),ed.end());string s;s.push_back(char(n));for(auto&p:ed){s.push_back(char(p.first));s.push_back(char(p.second));}
      if(best.empty()||s<best)best=s;return;}
    vector<int> t=*tgt;int base=col[t[0]];for(int v:t){vector<int> c2=col;for(int w:t)if(w!=v)c2[w]=base+1;rec(c2);}};
  rec(vector<int>(n,0));return best;}
struct Term{int num,den;vector<int> types;};
vector<vector<Term>> clusters;
int ursell(const vector<vector<char>>&g){int m=g.size();vector<pair<int,int>> ed;for(int i=0;i<m;i++)for(int j=i+1;j<m;j++)if(g[i][j])ed.push_back({i,j});
  int s=0;for(int mask=0;mask<(1<<ed.size());mask++){vector<int> f(m);iota(f.begin(),f.end(),0);function<int(int)> fd=[&](int x){return f[x]==x?x:f[x]=fd(f[x]);};int comps=m;
    for(size_t i=0;i<ed.size();i++)if(mask>>i&1){int a=fd(ed[i].first),b=fd(ed[i].second);if(a!=b){f[a]=b;comps--;}}
    if(comps==1)s+=__builtin_popcount(mask)%2?-1:1;}return s;}
vector<vector<pair<int,uint32_t>>> polys_store;
// connected leafless edge subsets of a labelled graph -> (type index, edgemask)
void subpolys(int n,const vector<pair<int,int>>&E,int maxsize,vector<tuple<int,uint32_t,uint32_t>>&out){
  int m=E.size();
  for(uint32_t mask=1;mask<(1u<<m);mask++){ if(__builtin_popcount(mask)<3)continue;
    int deg[32]={0};uint32_t vm=0;for(int i=0;i<m;i++)if(mask>>i&1){deg[E[i].first]++;deg[E[i].second]++;vm|=1u<<E[i].first|1u<<E[i].second;}
    int sz=__builtin_popcount(vm);if(sz>maxsize)continue;bool ok=true;for(int v=0;v<n;v++)if((vm>>v&1)&&deg[v]<2){ok=false;break;}if(!ok)continue;
    // connected
    uint32_t seen=1u<<__builtin_ctz(vm);bool ch=true;while(ch){ch=false;for(int i=0;i<m;i++)if(mask>>i&1){bool a=seen>>E[i].first&1,b=seen>>E[i].second&1;if(a!=b){seen|=1u<<E[i].first|1u<<E[i].second;ch=true;}}}
    if(seen!=vm)continue;
    int rel[32];int c=0;for(int v=0;v<n;v++)if(vm>>v&1)rel[v]=c++;vector<pair<int,int>> ed;for(int i=0;i<m;i++)if(mask>>i&1)ed.push_back({rel[E[i].first],rel[E[i].second]});
    auto it=idx.find(canon(sz,ed));if(it==idx.end()){fprintf(stderr,"missing pattern!\n");exit(1);}
    out.push_back({it->second,mask,vm});}
}
void buildClusters(int V){clusters.assign(pats.size(),{});
  for(size_t qi=0;qi<pats.size();qi++){Pat&Q=pats[qi];if(Q.n+2>V)continue; // two polymers sharing an edge share >=2 vertices
    vector<tuple<int,uint32_t,uint32_t>> pl;subpolys(Q.n,Q.e,V-3,pl);
    uint32_t full=(Q.m==32)?~0u:((1u<<Q.m)-1);map<vector<int>,pair<long long,long long>> agg;
    vector<int> stack;
    function<void(int,int,uint32_t)> dfs=[&](int start,int bud,uint32_t cov){
      if(stack.size()>=2&&cov==full){int m=stack.size();vector<vector<char>> g(m,vector<char>(m,0));
        for(int i=0;i<m;i++)for(int j=i+1;j<m;j++)if(get<2>(pl[stack[i]])&get<2>(pl[stack[j]]))g[i][j]=g[j][i]=1;
        int phi=ursell(g);if(phi){long long den=1;map<int,int> mu;for(int s:stack)mu[s]++;for(auto&kv:mu)for(int t=2;t<=kv.second;t++)den*=t;
          vector<int> ty;for(int s:stack)ty.push_back(get<0>(pl[s]));sort(ty.begin(),ty.end());
          auto&a=agg[ty];long long nn=a.first*den+phi*(a.second?a.second:1);long long dd=(a.second?a.second:1)*den;if(!a.second){nn=phi;dd=den;}long long gg=__gcd(llabs(nn),dd);if(gg){nn/=gg;dd/=gg;}a={nn,dd};}}
      for(int i=start;i<(int)pl.size();i++){int sz=__builtin_popcount(get<2>(pl[i]));if(sz>bud)continue;stack.push_back(i);dfs(i,bud-sz,cov|get<1>(pl[i]));stack.pop_back();}
    };
    // single polymer clusters are Theta(Q) itself, added separately
    dfs(0,V,0);
    for(auto&kv:agg)if(kv.second.first)clusters[qi].push_back({(int)kv.second.first,(int)kv.second.second,kv.first});
  }
}
int HM; vector<vector<S>> F; vector<S> Pv; vector<vector<int>> ordF; vector<int> ordP; S Zv,aS;
void setupQ(u64 q){ u64 qi=inv(q);
  vector<S> B(HM+1,S(VM+1,0));
  auto qp=[&](long long e){return e>=0?pw(q,e):pw(qi,-e);};
  // order-by-order solution, branch B(h)[0]=1
  for(int h=0;h<=HM;h++)B[h][0]=1;
  for(int t=1;t<=VM;t++){
    // coefficient t of B(h)= [t] B0^2 + sum_{h'>=1} q^{3h'^2-2hh'} [t-h'] B(h')^2
    vector<S> sq(HM+1); for(int h=0;h<=HM;h++)sq[h]=smul(B[h],B[h]);
    u64 s0=0;for(int hp=1;hp<=min(t,HM);hp++)s0=add(s0,mul(qp(3LL*hp*hp),sq[hp][t-hp]));
    // B0[t]=[t]B0^2+s0; [t]B0^2=2B0[t]+R where R excludes B0[t]; sq computed with B0[t]=0 => R=sq[0][t]
    u64 b0t=sub(0,add(sq[0][t],s0)); B[0][t]=b0t; u64 sq0=add(sq[0][t],mul(2,b0t));
    for(int h=1;h<=HM;h++){u64 s=sq0;for(int hp=1;hp<=min(t,HM);hp++)s=add(s,mul(qp(3LL*hp*hp-2LL*h*hp),sq[hp][t-hp]));B[h][t]=s;}
  }
  Zv.assign(VM+1,0);vector<S> B3(HM+1);for(int h=0;h<=HM;h++){B3[h]=smul(smul(B[h],B[h]),B[h]);u64 w=qp(3LL*h*h);for(int i=0;i+h<=VM;i++)Zv[i+h]=add(Zv[i+h],mul(w,B3[h][i]));}
  aS=slog(Zv);u64 mh=sub(0,inv(2));for(auto&c:aS)c=mul(c,mh);
  S iZ=sinv(Zv);Pv.assign(HM+1,S(VM+1,0));for(int h=0;h<=HM;h++){S t=smul(B3[h],iZ);u64 w=qp(3LL*h*h);for(int i=0;i+h<=VM;i++)Pv[h][i+h]=mul(w,t[i]);}
  vector<S> iB(HM+1);for(int h=0;h<=HM;h++)iB[h]=sinv(B[h]);
  F.assign(HM+1,vector<S>(HM+1));
  for(int a=0;a<=HM;a++)for(int b=a;b<=HM;b++){S t=smul(smul(Zv,iB[a]),iB[b]);u64 w=qp(-2LL*a*b);for(auto&c:t)c=mul(c,w);t[0]=sub(t[0],1);F[a][b]=t;F[b][a]=t;}
}
void ordersQ(){ordF.assign(HM+1,vector<int>(HM+1,VM+1));ordP.assign(HM+1,VM+1);
  for(int a=0;a<=HM;a++){for(int i=0;i<=VM;i++)if(Pv[a][i]){ordP[a]=i;break;}for(int b=0;b<=HM;b++)for(int i=0;i<=VM;i++)if(F[a][b][i]){ordF[a][b]=i;break;}}}
// Theta(Q) truncated at x^V by pruned DFS
S theta(const Pat&Q,int V){int n=Q.n;S res(VM+1,0);vector<int> h(n,-1);
  vector<int> pos(n);for(int i=0;i<n;i++)pos[Q.ord[i]]=i;
  function<void(int,const S&,int)> dfs=[&](int i,const S&cur,int cost){
    if(i==n){for(int t=0;t<=V;t++)res[t]=add(res[t],cur[t]);return;}
    int v=Q.ord[i];
    for(int s=0;s<=HM;s++){int c=cost+ordP[s];vector<int> back;
      for(int w:Q.nb[v])if(pos[w]<i){c+=ordF[s][h[w]];back.push_back(w);}
      // lower bound: remaining vertices >=1 each; zeros assigned with open edges add >=1
      int lb=c+(n-i-1);
      h[v]=s;
      for(int j=0;j<=i;j++){int u=Q.ord[j];if(h[u]==0)for(int w:Q.nb[u])if(pos[w]>i)lb+=1;}
      if(lb<=V){S nx=smul(cur,Pv[s]);for(int w:back)nx=smul(nx,F[s][h[w]]);for(int t=V+1;t<=VM;t++)nx[t]=0;dfs(i+1,nx,c);}
      h[v]=-1;
      if(s>=1&&cost+ordP[s]+(n-i-1)>V)break;
    }};
  S one(VM+1,0);one[0]=1;dfs(0,one,0);return res;}
// memory-light b_Q evaluation for one q
void evalB(vector<S>&th,vector<S>&b){int N=pats.size();th.resize(N);b.resize(N);
  static vector<char> need; if(need.empty()){need.assign(N,1);const char*ms=getenv("MINSIZE");if(ms){int m=atoi(ms);for(int i=0;i<N;i++)need[i]=pats[i].n>=m;for(int i=0;i<N;i++)if(pats[i].n>=m)for(auto&T:clusters[i])for(int t:T.types)need[t]=1;}}
  const char*ms2=getenv("MINSIZE");int m2=ms2?atoi(ms2):0;
  for(int i=0;i<N;i++)th[i]=need[i]?theta(pats[i],VM):S(VM+1,0);
  for(int i=0;i<N;i++){b[i]=th[i];if(pats[i].n<m2){for(auto&c:b[i])c=0;continue;}for(auto&T:clusters[i]){S c(VM+1,0);c[0]=1;for(int t:T.types)c=smul(c,th[t]);u64 co=T.num>=0?mul(T.num,inv(T.den)):sub(0,mul(-T.num,inv(T.den)));for(int k=0;k<=VM;k++)b[i][k]=add(b[i][k],mul(co,c[k]));}}
}
static const vector<vector<pair<int,int>>>* dummy;
int main(int ac,char**av){ // engine V patsfile mode [args]
  VM=atoi(av[1]);HM=VM;string mode=av[3];
  FILE*f=fopen(av[2],"r");int n,m;while(fscanf(f,"%d %d",&n,&m)==2){if(n>VM){int a,b;for(int i=0;i<m;i++)fscanf(f,"%d %d",&a,&b);continue;}
    Pat Q;Q.n=n;Q.m=m;Q.e.resize(m);Q.nb.assign(n,{});for(auto&p:Q.e){fscanf(f,"%d %d",&p.first,&p.second);Q.nb[p.first].push_back(p.second);Q.nb[p.second].push_back(p.first);}
    // BFS order
    vector<char> s(n,0);Q.ord.push_back(0);s[0]=1;for(size_t i=0;i<Q.ord.size();i++)for(int w:Q.nb[Q.ord[i]])if(!s[w]){s[w]=1;Q.ord.push_back(w);}
    // cut statistic min_X (3|X|-2e(X))
    int cm=99;for(uint32_t X=1;X<(1u<<n);X++){int ex=0;for(auto&p:Q.e)if((X>>p.first&1)&&(X>>p.second&1))ex++;cm=min(cm,3*__builtin_popcount(X)-2*ex);}Q.cutmin=cm;
    idx[canon(n,Q.e)]=pats.size();pats.push_back(Q);}
  fprintf(stderr,"patterns %zu\n",pats.size());
  buildClusters(VM);size_t tt=0,mx=0;for(auto&c:clusters){tt+=c.size();mx=max(mx,c.size());}fprintf(stderr,"cluster terms %zu max %zu\n",tt,mx);
  setupQ(1234567891ULL);ordersQ();
  if(mode=="orders"){for(int a=0;a<=4;a++){for(int b=0;b<=4;b++)printf("%d ",ordF[a][b]);printf("| p=%d\n",ordP[a]);}return 0;}
  if(mode=="validate"){ // read cubic graphs from av[4]: n m edges; compare direct log series vs formula at random q
    FILE*g=fopen(av[4],"r");int cnt=0,nn,mm;while(fscanf(g,"%d %d",&nn,&mm)==2){vector<pair<int,int>> E(mm);for(auto&p:E)fscanf(g,"%d %d",&p.first,&p.second);
      for(u64 q:{987654321ULL,31337ULL}){setupQ(q);vector<S> th,b;evalB(th,b);S pred(VM+1,0);for(int t=0;t<=VM;t++)pred[t]=mul(nn%P,aS[t]);
        vector<tuple<int,uint32_t,uint32_t>> pl;subpolys(nn,E,VM,pl);for(auto&x:pl){auto&bb=b[get<0>(x)];for(int t=0;t<=VM;t++)pred[t]=add(pred[t],bb[t]);}
        // direct enumeration
        S Z(VM+1,0);vector<int> h(nn,0);vector<vector<int>> nbr(nn);for(auto&p:E){nbr[p.first].push_back(p.second);}
        function<void(int,int,long long)> rec=[&](int v,int vol,long long en){if(v==nn){Z[vol]=add(Z[vol],pw(q,en));return;}
          for(int s=0;vol+s<=VM;s++){h[v]=s;long long e2=en+3LL*s*s;for(auto&p:E){if(p.first==v&&p.second<v)e2-=2*s*h[p.second];if(p.second==v&&p.first<v)e2-=2*s*h[p.first];}rec(v+1,vol+s,e2);}h[v]=0;};
        rec(0,0,0);S lg=slog(Z);bool ok=true;for(int t=0;t<=VM;t++)if(lg[t]!=pred[t])ok=false;printf("graph %d n=%d q=%llu match=%d\n",cnt,nn,q,ok);}
      cnt++;}return 0;}




  if(mode=="evals"){ // av[4]=index list, av[5]=out, av[6]=number of q points: raw b_Q series at each q for listed patterns
    vector<int> L;{FILE*g=fopen(av[4],"r");int x;while(fscanf(g,"%d",&x)==1)L.push_back(x);fclose(g);}
    int MP=atoi(av[6]);FILE*o=fopen(av[5],"w");int N=pats.size();
    vector<char> need(N,0);for(int i:L){need[i]=1;for(auto&T:clusters[i])for(int t:T.types)need[t]=1;}
    for(int w=0;w<MP;w++){u64 q=1000003+w*7919;setupQ(q);vector<S> th(N);
      for(int i=0;i<N;i++)if(need[i])th[i]=theta(pats[i],VM);
      for(int i:L){S b=th[i];for(auto&T:clusters[i]){S c(VM+1,0);c[0]=1;for(int t:T.types)c=smul(c,th[t]);u64 co=T.num>=0?mul(T.num,inv(T.den)):sub(0,mul(-T.num,inv(T.den)));for(int k=0;k<=VM;k++)b[k]=add(b[k],mul(co,c[k]));}
        fprintf(o,"%d %llu %d",w,q,i);for(int k=0;k<=VM;k++)fprintf(o," %llu",b[k]);fputc('\n',o);}
      fflush(o);fprintf(stderr,"q %d/%d\n",w,MP);}
    fclose(o);return 0;}
  if(mode=="dumpclusters"){FILE*o=fopen(av[4],"w");for(size_t i=0;i<pats.size();i++)for(auto&T:clusters[i]){fprintf(o,"%zu %d %d %zu",i,T.num,T.den,T.types.size());for(int t:T.types)fprintf(o," %d",t);fputc('\n',o);}fclose(o);return 0;}
  if(mode=="counts"){ // hosts file av[4]; output: host n, then (col count) for patterns up to VM vertices
    FILE*g=fopen(av[4],"r");FILE*o=fopen(av[5],"w");int nn,mm;while(fscanf(g,"%d %d",&nn,&mm)==2){vector<pair<int,int>> E(mm);for(auto&p:E)fscanf(g,"%d %d",&p.first,&p.second);
      if(ac>6&&nn>atoi(av[6]))continue;
      vector<tuple<int,uint32_t,uint32_t>> pl;subpolys(nn,E,VM,pl);map<int,int> c;for(auto&x:pl)c[get<0>(x)]++;
      fprintf(o,"%d %d",nn,mm);for(auto&p:E)fprintf(o," %d %d",p.first,p.second);fprintf(o," | %zu",c.size());for(auto&kv:c)fprintf(o," %d %d",kv.first+1,kv.second);fputc('\n',o);}
    fclose(o);return 0;}
  if(mode=="separate"){ // cubic graphs (closed patterns from file av[4], connected, n<=av[5]) : first volume separating each pair of equal order
    int nmax=atoi(av[5]);FILE*g=fopen(av[4],"r");vector<vector<pair<int,int>>> Gs;vector<int> ns;int nn,mm;
    while(fscanf(g,"%d %d",&nn,&mm)==2){vector<pair<int,int>> E(mm);for(auto&p:E)fscanf(g,"%d %d",&p.first,&p.second);if(nn<=nmax&&2*mm==3*nn){Gs.push_back(E);ns.push_back(nn);}}
    vector<u64> qq={987654321ULL,31337ULL,777767777ULL};vector<vector<S>> bs;vector<S> as;
    for(u64 q:qq){setupQ(q);vector<S> th,b;evalB(th,b);bs.push_back(b);as.push_back(aS);}
    vector<vector<S>> val(Gs.size());
    for(size_t i=0;i<Gs.size();i++){vector<tuple<int,uint32_t,uint32_t>> pl;subpolys(ns[i],Gs[i],VM,pl);
      for(size_t w=0;w<qq.size();w++){S pred(VM+1,0);for(int t=0;t<=VM;t++)pred[t]=mul(ns[i],as[w][t]);for(auto&x:pl){auto&bb=bs[w][get<0>(x)];for(int t=0;t<=VM;t++)pred[t]=add(pred[t],bb[t]);}val[i].push_back(pred);}}
    map<int,map<int,int>> hist;int unsep=0;
    for(size_t i=0;i<Gs.size();i++)for(size_t j=i+1;j<Gs.size();j++)if(ns[i]==ns[j]){int sep=-1;for(int t=1;t<=VM&&sep<0;t++)for(size_t w=0;w<qq.size();w++)if(val[i][w][t]!=val[j][w][t]){sep=t;break;}hist[ns[i]][sep]++;if(sep<0){unsep++;FILE*u=fopen("unsep.txt","a");for(size_t I:{i,j}){fprintf(u,"%d %zu",ns[I],Gs[I].size());for(auto&p:Gs[I])fprintf(u," %d %d",p.first,p.second);fputc(10,u);}fclose(u);}if(sep>=9)printf("late %d %zu %zu\n",sep,i,j);}
    for(auto&kv:hist){printf("n=%d:",kv.first);for(auto&h:kv.second)printf(" sepV%d:%d",h.first,h.second);puts("");}
    printf("graphs %zu unseparated pairs %d\n",Gs.size(),unsep);return 0;}
  if(mode=="rows"){ // rows by energy e: interpolate, verify degree bound, write sparse integer rows.
    if(ac>5) P=strtoull(av[5],0,10);
    int Vs=VM,N=pats.size();FILE*o=fopen(av[4],"w");
    // per V: exponents e=V mod 2, 0<=e<=3V^2 -> t=q^2, D+1 unknowns; 4 slack points verify the bound
    int M=0;vector<int> Dv(Vs+1);for(int v=1;v<=Vs;v++){Dv[v]=(3*v*v-(v%2))/2;M=max(M,Dv[v]+1+4);}
    vector<vector<vector<u64>>> R(Vs+1);vector<u64> qs;
    for(int i=0;i<M;i++){u64 q=1000003+i*7919;qs.push_back(q);setupQ(q);vector<S> th,b;evalB(th,b);
      for(int v=1;v<=Vs;v++)if(i<Dv[v]+5){vector<u64> row(N+1);row[0]=aS[v];for(int j=0;j<N;j++)row[j+1]=b[j][v];R[v].push_back(row);}
      if(i%40==0)fprintf(stderr,"q %d/%d\n",i,M);}
    printf("cols %d\n",N+1);
    for(int v=1;v<=Vs;v++){int m=Dv[v]+1;
      // normalise value y_i -> y_i/q^{v%2}; unknown poly in t=q^2 of degree D; Newton/Vandermonde via Gaussian inverse
      vector<vector<u64>> A(m,vector<u64>(2*m,0));for(int i=0;i<m;i++){u64 t=mul(qs[i],qs[i]),c=1;for(int j=0;j<m;j++){A[i][j]=c;c=mul(c,t);}A[i][m+i]=1;}
      for(int c=0;c<m;c++){int pv=c;while(!A[pv][c])pv++;swap(A[pv],A[c]);u64 iv=inv(A[c][c]);for(auto&x:A[c])x=mul(x,iv);
        for(int r=0;r<m;r++)if(r!=c&&A[r][c]){u64 f=A[r][c];for(int j=c;j<2*m;j++)if(A[c][j])A[r][j]=sub(A[r][j],mul(f,A[c][j]));}}
      vector<u64> sc(m+4);for(int i=0;i<m+4;i++)sc[i]=(v%2)?inv(qs[i]):1;
      vector<vector<u64>> co(m,vector<u64>(N+1,0));
      for(int e=0;e<m;e++)for(int i=0;i<m;i++){u64 w=mul(A[e][m+i],sc[i]);if(w)for(int c=0;c<=N;c++)if(R[v][i][c])co[e][c]=add(co[e][c],mul(w,R[v][i][c]));}
      // slack verification
      int bad=0;for(int i=m;i<m+4;i++){u64 t=mul(qs[i],qs[i]);for(int c=0;c<=N;c++){u64 val=0;for(int e=m-1;e>=0;e--)val=add(mul(val,t),co[e][c]);if(val!=mul(sc[i],R[v][i][c]))bad++;}}
      printf("V %d degree-bound violations %d\n",v,bad);
      for(int e=0;e<m;e++){int nz=0;for(auto x:co[e])if(x)nz++;if(!nz)continue;fprintf(o,"%d %d %d",v,2*e+(v%2),nz);for(int c=0;c<=N;c++)if(co[e][c])fprintf(o," %d %llu",c,co[e][c]);fputc('\n',o);}
      R[v].clear();R[v].shrink_to_fit();fflush(stdout);}
    FILE*pf=fopen((string(av[4])+".pats").c_str(),"w");for(auto&Q:pats){fprintf(pf,"%d %d %d",Q.n,Q.m,Q.cutmin);for(auto&p:Q.e)fprintf(pf," %d %d",p.first,p.second);fputc('\n',pf);}
    fclose(o);fclose(pf);
  }
  if(mode=="rank"){ // pts per volume then incremental rank for classes k=0,1,2,3
    int Vs=VM;int M=0;vector<int> Mv(Vs+1);for(int v=1;v<=Vs;v++){Mv[v]=(3*v*v)/2+6;M=max(M,Mv[v]);}
    int N=pats.size();vector<vector<u64>> rowsAll; // rows stored per V
    vector<vector<vector<u64>>> R(Vs+1);
    for(int i=0;i<M;i++){u64 q=1000003+i*7919;setupQ(q);vector<S> th,b;evalB(th,b);
      for(int v=1;v<=Vs;v++)if(i<Mv[v]){vector<u64> row(N+1);row[0]=aS[v];for(int j=0;j<N;j++)row[j+1]=b[j][v];R[v].push_back(row);}
      if(i%20==0)fprintf(stderr,"q %d/%d\n",i,M);}
    for(int k=0;k<=3;k++){vector<int> cols;cols.push_back(0);for(int j=0;j<N;j++)if(pats[j].cutmin>=k)cols.push_back(j+1);
      vector<vector<u64>> basis;vector<int> piv;int total=0;printf("class k=%d cols=%zu:",k,cols.size());
      for(int v=1;v<=Vs;v++){int newr=0;for(auto&r0:R[v]){vector<u64> r;r.reserve(cols.size());for(int c:cols)r.push_back(r0[c]);
          for(size_t b=0;b<basis.size();b++){u64 c=r[piv[b]];if(c)for(size_t j=0;j<r.size();j++)if(basis[b][j])r[j]=sub(r[j],mul(c,basis[b][j]));}
          int pi=-1;for(size_t j=0;j<r.size();j++)if(r[j]){pi=j;break;}if(pi<0)continue;u64 iv=inv(r[pi]);for(auto&x:r)x=mul(x,iv);basis.push_back(r);piv.push_back(pi);newr++;}
        total+=newr;printf(" V%d:+%d=%d",v,newr,total);fflush(stdout);}
      puts("");}
  }
}
