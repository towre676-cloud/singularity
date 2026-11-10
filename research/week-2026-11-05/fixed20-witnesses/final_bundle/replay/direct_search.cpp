// Direct integer weak-composition height enumeration. No source law is used.
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>
using Poly=std::array<int64_t,193>;
struct Graph {int n;std::vector<std::vector<int>> prev;};
Graph decode(const std::string&s){Graph g;g.n=int(s[0])-63;g.prev.resize(g.n);int bit=0;
 for(int j=1;j<g.n;j++)for(int i=0;i<j;i++,bit++)if(((int(s[1+bit/6])-63)>>(5-bit%6))&1)g.prev[j].push_back(i);return g;}
void visit(const Graph&g,int v,int rem,int energy,std::vector<int>&h,Poly&p){
 if(!rem){p[energy]++;return;}int sum=0;for(int u:g.prev[v])sum+=h[u];
 if(v==g.n-1){p[energy+3*rem*rem-2*rem*sum]++;return;}
 for(int x=0;x<=rem;x++){h[v]=x;visit(g,v+1,rem-x,energy+3*x*x-2*x*sum,h,p);}}
Poly coefficient(const Graph&g,int r){Poly p{};std::vector<int>h(g.n);visit(g,0,r,0,h,p);return p;}
int main(int argc,char**argv){if(argc!=3)return 2;std::ifstream in(argv[1]);std::ofstream out(argv[2]);
 std::string line;std::vector<Graph>g;while(in>>line)g.push_back(decode(line));if(g.empty())return 3;
 std::vector<std::vector<int>>groups(1);for(int i=0;i<int(g.size());i++)groups[0].push_back(i);
 for(int r=3;r<=7;r++){std::vector<std::vector<int>>next;
  for(auto&group:groups){if(group.size()<2)continue;std::map<Poly,std::vector<int>>by;
   for(int i:group)by[coefficient(g[i],r)].push_back(i);
   for(auto&kv:by)if(kv.second.size()>1)next.push_back(std::move(kv.second));}
  groups=std::move(next);std::cerr<<"order "<<g[0].n<<" volume "<<r<<" groups "<<groups.size()<<"\n";}
 out<<"{\"n\":"<<g[0].n<<",\"graphs\":"<<g.size()<<",\"pairs\":[";bool first=true;
 for(auto&group:groups){int a=group[0];Poly A=coefficient(g[a],8);
  for(size_t j=1;j<group.size();j++){int b=group[j];Poly B=coefficient(g[b],8);if(A==B)continue;
   if(!first)out<<",";first=false;out<<"{\"A\":"<<a<<",\"B\":"<<b<<",\"delta\":{";bool fp=true;
   for(int e=0;e<=192;e++)if(B[e]!=A[e]){if(!fp)out<<",";fp=false;out<<"\""<<e<<"\":"<<B[e]-A[e];}
   out<<"}}";}}
 out<<"]}\n";
}
