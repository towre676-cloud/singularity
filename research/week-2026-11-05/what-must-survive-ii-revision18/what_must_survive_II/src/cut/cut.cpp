// Enumerate cut-lattice vectors: h on V with min h=0, energy<=EM. Output for each graph: e vol count table.
#include <bits/stdc++.h>
using namespace std;
int main(int c,char**v){int EM=atoi(v[1]);int n,m;int id=0;while(scanf("%d %d",&n,&m)==2){vector<vector<double>> L(n,vector<double>(n,0));vector<pair<int,int>> E(m);for(auto&p:E){scanf("%d %d",&p.first,&p.second);L[p.first][p.first]++;L[p.second][p.second]++;L[p.first][p.second]--;L[p.second][p.first]--;}
 int r=n-1;// reduced at vertex n-1; Cholesky q_ii, q_ij
 vector<vector<double>> q(r,vector<double>(r));for(int i=0;i<r;i++)for(int j=0;j<r;j++)q[i][j]=L[i][j];
 for(int i=0;i<r;i++){for(int j=i+1;j<r;j++){double t=q[i][j];q[j][i]=t;q[i][j]=t/q[i][i];}for(int k=i+1;k<r;k++)for(int l=k;l<r;l++)q[k][l]-=q[k][i]*q[i][l];}
 map<pair<int,int>,long long> T;vector<int> x(n,0);double U=EM+1e-6;
 function<void(int,double)> rec=[&](int i,double rem){ if(i<0){long long en=0;for(auto&p:E){int d=x[p.first]-x[p.second];en+=d*d;}int mn=*min_element(x.begin(),x.end());int vol=0;for(int a=0;a<n;a++)vol+=x[a]-mn;if(en<=EM)T[{(int)en,vol}]++;return;}
   double ctr=0;for(int j=i+1;j<r;j++)ctr+=q[i][j]*x[j];double rad=sqrt(max(0.0,rem/q[i][i]));int lo=ceil(-ctr-rad-1e-9),hi=floor(-ctr+rad+1e-9);for(int a=lo;a<=hi;a++){x[i]=a;double d=a+ctr;rec(i-1,rem-q[i][i]*d*d);}x[i]=0;};
 rec(r-1,U);printf("G %d %d %d\n",id++,n,m);for(auto&kv:T)printf("%d %d %lld\n",kv.first.first,kv.first.second,kv.second);fflush(stdout);}}
