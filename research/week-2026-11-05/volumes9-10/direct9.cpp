// Independent direct height enumeration: every weak composition through volume 9.
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using Poly=std::array<int64_t,244>;
struct Graph {int n;std::vector<std::vector<int>> prev;};
Graph decode(const std::string&s){Graph g;g.n=int(s[0])-63;g.prev.resize(g.n);int bit=0;
 for(int j=1;j<g.n;j++)for(int i=0;i<j;i++,bit++)if(((int(s[1+bit/6])-63)>>(5-bit%6))&1)g.prev[j].push_back(i);return g;}
void visit(const Graph&g,int v,int rem,int energy,std::vector<int>&h,Poly&p){
 if(!rem){p[energy]++;return;}int sum=0;for(int u:g.prev[v])sum+=h[u];
 if(v==g.n-1){p[energy+3*rem*rem-2*rem*sum]++;return;}
 for(int x=0;x<=rem;x++){h[v]=x;visit(g,v+1,rem-x,energy+3*x*x-2*x*sum,h,p);}}
int main(int argc,char**argv){if(argc!=3)return 2;std::ifstream in(argv[1]);std::ofstream out(argv[2]);
 std::string s;out<<"[";bool first=true;while(in>>s){if(!first)out<<",";first=false;auto g=decode(s);out<<"{\"g6\":\"";
 for(char c:s){if(c=='\\'||c=='\"')out<<'\\';out<<c;}out<<"\",\"coefficients\":{";
 for(int r=0;r<=9;r++){if(r)out<<",";Poly p{};std::vector<int>h(g.n);visit(g,0,r,0,h,p);
 out<<"\""<<r<<"\":{";bool fp=true;for(int e=0;e<244;e++)if(p[e]){if(!fp)out<<",";fp=false;out<<"\""<<e<<"\":"<<p[e];}out<<"}";}
 out<<"}}";}out<<"]\n";}
