// Caterpillars: pendant counts p_1..p_m, ends >=1 (m>=2) ; n=m+sum p. Test separation by (S1), (S1,S2) from the exact formula, up to reflection.
#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u64;
int main(int ac,char**av){int N0=atoi(av[1]),N1=atoi(av[2]);
 for(int n=N0;n<=N1;n++){unordered_map<u64,vector<vector<int>>> B;long long total=0;
  map<u64,int> ct1,ct2;vector<int> p;
  function<void(int)> gen=[&](int left){ // left = remaining vertices
    int m=p.size();
    if(m>=2&&p[0]>=1&&p.back()>=1&&left==0){ vector<int> r(p.rbegin(),p.rend()); if(r<p) return; total++;
      // positions a_i, leaf count
      vector<int> a;int s=0;for(int i=0;i<m-1;i++){s+=1+p[i];a.push_back(s);}
      int ell=0;for(int x:p)ell+=x;
      vector<int> S1(n+1,0),S2(2*n+2,0);
      for(int t:a){S1[t]++;S1[n-t]++;} S1[1]+=ell;S1[n-1]+=ell;
      auto add=[&](int A,int b,int c){S2[b]++;S2[A+c]++;S2[2*A+b]++;S2[b+2*c]++;};
      for(size_t i=0;i<a.size();i++)for(size_t j=i+1;j<a.size();j++)add(a[i],a[j]-a[i],n-a[j]);
      for(size_t i=0;i<a.size();i++){int L=a[i]-(int)i-1;int R=ell-L;for(int k=0;k<L;k++)add(1,a[i]-1,n-a[i]);for(int k=0;k<R;k++)add(a[i],n-a[i]-1,1);}
      for(int k=0;k<ell*(ell-1)/2;k++)add(1,n-2,1);
      u64 h=1469598103934665603ULL;for(int x:S1){h^=x;h*=1099511628211ULL;}ct1[h]++;
      for(int x:S2){h^=x+7;h*=1099511628211ULL;}ct2[h]++;
      auto&v=B[h];if(v.size()<3)v.push_back(p);
      return;}
    if(left==0)return;
    for(int x=0;x+1<=left;x++){p.push_back(x);gen(left-x-1);p.pop_back();}
  };
  gen(n);
  long long c1=0,c2=0;for(auto&k:ct1)c1+=k.second-1;for(auto&k:ct2)c2+=k.second-1;
  printf("n=%d caterpillars=%lld unsepS1=%lld unsepS1S2=%lld\n",n,total,c1,c2);int shown=0;for(auto&kv:B)if(kv.second.size()>1&&shown<2){printf(" ex:");for(auto&v:kv.second){printf(" [");for(int x:v)printf("%d ",x);printf("]");}puts("");shown++;}fflush(stdout);}
}
