// All caterpillars of order n (canonical non-leaf spine, up to reversal): classes under (A,B), then under (A,B,H3). Hashes are screened; printed classes are rechecked exactly in Python.
#include <bits/stdc++.h>
using namespace std; typedef unsigned long long u; typedef __uint128_t U;
int n; u R[512]; 
u rnd(){static u s=0x9E3779B97F4A7C15ULL; s^=s<<13;s^=s>>7;s^=s<<17;return s*0xD1342543DE82EF95ULL;}
struct E{u k;unsigned c;};
static inline void H3add(u&h,long long mult,int a,int b,int c,int d){h+=mult*(R[a+c]+R[b+d]+R[a+2*b+c]+R[b+2*c+d]);}
static inline void H3star(u&h,long long mult,int w,int p,int q,int r){h+=mult*(R[w]+R[w+n]+R[w+2*p]+R[w+2*q]+R[w+2*r]);}
u h3(const vector<int>&p){int m=p.size(),ell=0;for(int x:p)ell+=x;vector<int> pre(m+1,0);for(int i=0;i<m;i++)pre[i+1]=pre[i]+1+p[i];u h=0;
 auto seg=[&](int i,int j){return pre[j]-pre[i];}; // spine i..j-1 with all pendants
 auto pp=[&](int i,int j){int s=0;for(int k=i;k<j;k++)s+=p[k];return s;};
 for(int i=1;i<m;i++)for(int j=i+1;j<m;j++)for(int k=j+1;k<m;k++)H3add(h,1,seg(0,i),seg(i,j),seg(j,k),seg(k,m));
 for(int i=1;i<m;i++)for(int j=i+1;j<m;j++){int A=seg(0,i),B=seg(i,j),C=seg(j,m);int la=pp(0,i),lb=pp(i,j),lc=pp(j,m);
  if(la)H3add(h,la,1,A-1,B,C); if(lc)H3add(h,lc,A,B,C-1,1); if(lb)H3star(h,lb,B-1,A,C,1);}
 for(int i=1;i<m;i++){int A=seg(0,i),C=seg(i,m),la=pp(0,i),lc=ell-la;
  if(la>=2)H3star(h,la*(la-1)/2,A-2,1,1,C); if(lc>=2)H3star(h,lc*(lc-1)/2,C-2,1,1,A); if(la&&lc)H3add(h,(long long)la*lc,1,A-1,C-1,1);}
 long long l3=(long long)ell*(ell-1)*(ell-2)/6; if(l3)H3star(h,l3,n-3,1,1,1);
 return h;}
vector<array<u,2>> recs; vector<int> cur; 
u sAB(const vector<int>&p,u&ha){int m=p.size(),ell=0;for(int x:p)ell+=x;u a=0,b=0;vector<int> pos;int t=0,l=0;for(int i=0;i<m-1;i++){t+=1+p[i];l+=p[i];pos.push_back(t);a+=R[t]+R[n-t];b+=(u)l*R[t-1]+(u)(ell-l)*R[n-t-1];}
 for(int i=0;i<m-1;i++)for(int j=i+1;j<m-1;j++)b+=R[pos[j]-pos[i]];ha=a;return b;}
vector<u> keyA; long long tot=0; int shards,shard;
FILE*out;
void gen(int left){ if(left==0){ if(cur.size()<2||cur[0]<1||cur.back()<1)return; for(size_t i=0,N=cur.size();i<N;i++){if(cur[i]<cur[N-1-i])break; if(cur[i]>cur[N-1-i])return;} u a,b=sAB(cur,a);tot++; if((a%shards)!=(u)shard)return; recs.push_back({a*0x9E3779B97F4A7C15ULL+b,0});keyA.push_back(0);return;} for(int x=0;x<left;x++){cur.push_back(x);gen(left-x-1);cur.pop_back();}}
int main(int ac,char**av){n=atoi(av[1]);shards=ac>2?atoi(av[2]):1;long long ex2=0,cl2=0,ex3=0,cl3=0;for(int i=0;i<512;i++)R[i]=rnd();
 for(shard=0;shard<shards;shard++){recs.clear();keyA.clear();tot=0;gen(n);vector<u> ks;ks.reserve(recs.size());for(auto&r:recs)ks.push_back(r[0]);keyA.clear();keyA.shrink_to_fit();recs.clear();recs.shrink_to_fit();sort(ks.begin(),ks.end());
  vector<u> dup;for(size_t i=0;i+1<ks.size();){size_t j=i;while(j+1<ks.size()&&ks[j+1]==ks[i])j++;if(j>i){dup.push_back(ks[i]);ex2+=j-i;cl2++;}i=j+1;}vector<u>().swap(ks);
  // second pass: H3 on members of dup classes
  unordered_map<u,vector<pair<u,vector<int>>>> mp;for(u k:dup)mp[k];
  function<void(int)> g2=[&](int left){ if(left==0){ if(cur.size()<2||cur[0]<1||cur.back()<1)return; for(size_t i=0,N=cur.size();i<N;i++){if(cur[i]<cur[N-1-i])break; if(cur[i]>cur[N-1-i])return;} u a,b=sAB(cur,a); if((a%shards)!=(u)shard)return; auto it=mp.find(a*0x9E3779B97F4A7C15ULL+b); if(it!=mp.end()){it->second.push_back({h3(cur),cur});} return;} for(int x=0;x<left;x++){cur.push_back(x);g2(left-x-1);cur.pop_back();}};
  g2(n);
  for(auto&kv:mp){auto&v=kv.second;sort(v.begin(),v.end());if(getenv("DUMP")){printf("S2");for(auto&q:v){printf(" ");for(int x:q.second)printf("%d,",x);}puts("");}for(size_t i=0;i+1<v.size();){size_t j=i;while(j+1<v.size()&&v[j+1].first==v[i].first)j++;if(j>i){ex3+=j-i;cl3++;printf("S3COLL");for(size_t k=i;k<=j;k++){printf(" [");for(int x:v[k].second)printf("%d,",x);printf("]");}puts("");}i=j+1;}}
 }
 printf("n=%d total=%lld excessS2=%lld classesS2=%lld excessS3=%lld classesS3=%lld\n",n,tot,ex2,cl2,ex3,cl3);}
