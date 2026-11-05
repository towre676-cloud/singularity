// All spin configurations on fold sites of N: energy collisions, optionally counting; flags "dangerous" configs (a gathering could fit).
#include <bits/stdc++.h>
using namespace std;typedef unsigned long long u;typedef __uint128_t U;const u P=(1ULL<<61)-1;
static inline u mul(u a,u b){U t=(U)a*b;u r=(u)(t&P)+(u)(t>>61);if(r>=P)r-=P;return r;}
u pw(u a,u e){u r=1;while(e){if(e&1)r=mul(r,a);a=mul(a,a);e>>=1;}return r;}
int main(int ac,char**av){int N=atoi(av[1]);int mode=ac>2?atoi(av[2]):0;mt19937_64 R(4242);u x=R()%P,xi=pw(x,P-2);int H=(N-1)/2; // sites 1..H, H<N/2
 vector<u> xp(2*N+1,1),xn(2*N+1,1);for(int i=1;i<=2*N;i++){xp[i]=mul(xp[i-1],x);xn[i]=mul(xn[i-1],xi);}
 vector<vector<u>> K(H+1,vector<u>(H+1,0));for(int p=1;p<=H;p++)for(int q=p+1;q<=H;q++){u g=(xn[p]+P-1)%P,h=(xp[q]+P-xp[N-q])%P;K[p][q]=K[q][p]=mul(g,h);}
 long long classesW=0,excess=0,danger=0,dangerHit=0,sets=0;vector<int> st;vector<pair<u,unsigned>> v;
 u tot=1ULL<<H;for(u m=1;m<tot;m++){int k=__builtin_popcountll(m);if(k<4)continue;st.clear();for(int i=1;i<=H;i++)if(m>>(i-1)&1)st.push_back(i);int Q=st.back();
  if(mode==1){if(3*Q<N)continue;if(st[0]>N/2-2-Q||2*st[0]+4>N/2)continue;} // dangerous requires small site below limit
  int top=k-1; v.resize(1u<<top);vector<int> s(k,1);u E=0;for(int i=0;i<k;i++)for(int j=i+1;j<k;j++)E=(E+K[st[i]][st[j]])%P; // all +, Q fixed +
  unsigned code=0;v[0]={E,0};for(unsigned c=1;c<(1u<<top);c++){int b=__builtin_ctz(c);u d=0;for(int j=0;j<k;j++)if(j!=b){u t=K[st[b]][st[j]];if(s[j]*s[b]>0){d+=t;if(d>=P)d-=P;}else{d+=P-t;if(d>=P)d-=P;}}
    u dd=(d+d)%P;E=(E+P-dd)%P;s[b]=-s[b];code^=1u<<b;v[c]={E,code};}
  sort(v.begin(),v.end());sets++;int freeb=H-k+((N%2==0)?1:0);
  for(size_t i=0;i<v.size();){size_t j=i;while(j+1<v.size()&&v[j+1].first==v[i].first)j++;if(j>i){classesW+=1LL<<freeb;excess+=(j-i);bool dang=false;for(size_t t=i;t<=j;t++){int Yv=0;for(int b=0;b<top;b++)if(v[t].second>>b&1)Yv=st[b];if(Yv&&Q+Yv+2<=N/2&&3*Q>=N){dang=true;}}
     if(dang){dangerHit++;printf("DANGER N=%d",N);for(size_t t=i;t<=j;t++){printf(" [");for(int b=0;b<k;b++){printf("%d%s,",st[b],(b<top&&(v[t].second>>b&1))?"-":"+");}printf("]");}puts("");fflush(stdout);}}i=j+1;}
 }
 printf("N=%d n=%d mode=%d sets=%lld weighted_classes=%lld excess=%lld danger_classes=%lld\n",N,N+2,mode,sets,classesW,excess,dangerHit);}
