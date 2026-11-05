#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using Poly=std::array<int64_t,193>;
struct Graph{int n;std::vector<uint32_t>a;};
Graph decode(std::string s){Graph g;g.n=int(s[0])-63;g.a.resize(g.n);int bit=0;for(int j=1;j<g.n;j++)for(int i=0;i<j;i++,bit++)if(((int(s[1+bit/6])-63)>>(5-bit%6))&1){g.a[i]|=1u<<j;g.a[j]|=1u<<i;}return g;}
void cycles(const Graph&g,int start,int last,uint32_t used,int depth,std::unordered_set<uint32_t>&seen){uint32_t b=g.a[last];while(b){int v=__builtin_ctz(b);b&=b-1;if(v==start&&depth>=3)seen.insert(used);else if(v>start&&!(used>>v&1)&&depth<8)cycles(g,start,v,used|(1u<<v),depth+1,seen);}}
int main(int argc,char**argv){if(argc!=5&&argc!=6)return 2;std::ifstream gi(argv[1]),wi(argv[2]),oi(argv[3]);std::ofstream out(argv[4]);int nt;int64_t scale;wi>>nt>>scale;std::vector<std::array<Poly,6>>W(nt);int k,m,id;
for(int i=0;i<nt;i++){wi>>k>>m;for(int r=0;r<6;r++){int len;wi>>len;for(int j=0;j<len;j++){int e;int64_t a;wi>>e>>a;W[i][r][e]=a;}}}std::array<Poly,6> targets{};for(int i=0;i<6;i++){int len;wi>>len;for(int j=0;j<len;j++){int e;int64_t a;wi>>e>>a;targets[i][e]=a;}}
std::unordered_map<uint64_t,int>lookup;while(oi>>k>>m>>id)lookup[(uint64_t(k)<<32)|uint32_t(m)]=id;std::vector<std::vector<int>>counts;std::string line;int n=0;
while(gi>>line){Graph g=decode(line);n=g.n;std::unordered_set<uint32_t>seen;for(int v=0;v<n;v++)cycles(g,v,v,1u<<v,1,seen);std::vector<uint32_t>sets(seen.begin(),seen.end());for(size_t j=0;j<sets.size();j++){uint32_t s=sets[j];if(__builtin_popcount(s)>=8)continue;uint32_t b=0,u=s;while(u){int v=__builtin_ctz(u);u&=u-1;b|=g.a[v];}b&=~s;while(b){uint32_t bit=b&-b;b-=bit;if(seen.insert(s|bit).second)sets.push_back(s|bit);}}
std::vector<int>row(nt);for(uint32_t s:sets){uint32_t u=s;int vs[8],size=0;bool ok=true;while(u){int v=__builtin_ctz(u);u&=u-1;if(__builtin_popcount(g.a[v]&s)<2){ok=false;break;}vs[size++]=v;}if(!ok)continue;uint32_t raw=0;int pos=0;for(int a=0;a<size;a++)for(int b=a+1;b<size;b++,pos++)if(g.a[vs[a]]>>vs[b]&1)raw|=1u<<pos;auto p=lookup.find((uint64_t(size)<<32)|raw);if(p==lookup.end())return 3;row[p->second]++;}counts.push_back(std::move(row));if(counts.size()%10000==0)std::cerr<<"counted "<<counts.size()<<"\n";}
auto poly=[&](int g,int r){Poly p{};for(int i=0;i<nt;i++)if(counts[g][i])for(int e=0;e<=192;e++)p[e]+=int64_t(counts[g][i])*W[i][r-3][e];return p;};std::vector<std::vector<int>>groups(1);for(int i=0;i<int(counts.size());i++)groups[0].push_back(i);for(int r=3;r<=7;r++){std::vector<std::vector<int>>next;for(auto&group:groups){if(group.size()<2)continue;std::map<Poly,std::vector<int>>by;for(int i:group)by[poly(i,r)].push_back(i);for(auto&kv:by)if(kv.second.size()>1)next.push_back(std::move(kv.second));}groups=std::move(next);}
if(argc==6){std::ofstream rf(argv[5]);rf<<"[";bool f=true;for(auto&group:groups){int a=group[0];Poly A=poly(a,8);for(size_t j=1;j<group.size();j++){int b=group[j];Poly B=poly(b,8);if(A==B)continue;if(!f)rf<<",";f=false;rf<<"{\"A\":"<<a<<",\"B\":"<<b<<",\"delta\":{";bool fp=true;for(int e=0;e<=192;e++)if(A[e]!=B[e]){if((B[e]-A[e])%scale)return 5;if(!fp)rf<<",";fp=false;rf<<"\""<<e<<"\":"<<(B[e]-A[e])/scale;}rf<<"}}";}}rf<<"]\n";}
out<<"{\"n\":"<<n<<",\"graphs\":"<<counts.size()<<",\"unit_pairs\":[";bool first=true;std::array<int,6>hits{};int refs=0;
for(auto&group:groups){std::map<Poly,int> points;Poly ref=poly(group[0],8);for(int g:group){Poly p=poly(g,8);points.emplace(p,g);if(p!=ref)refs++;}for(auto&kv:points){for(int i=0;i<6;i++){Poly p=kv.first;for(int e=0;e<=192;e++)p[e]+=targets[i][e];auto f=points.find(p);if(f!=points.end()){hits[i]++;if(!first)out<<",";first=false;out<<"{\"coordinate\":"<<i<<",\"A\":"<<kv.second<<",\"B\":"<<f->second<<"}";}}}}
out<<"],\"nonzero_reference_pairs\":"<<refs<<",\"unit_counts\":[";for(int i=0;i<6;i++){if(i)out<<",";out<<hits[i];}out<<"]}\n";std::cerr<<"done "<<n<<"\n";}
