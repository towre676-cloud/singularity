import json,re,sys
R='/root/wms/receipts/'
w=json.load(open(R+'windows_V14.json'));g=json.load(open(R+'girth.json'));ex=json.load(open(R+'exact_ranks_V12.json'))
try: ex13=json.load(open(R+'exact_ranks_V14.json'))
except: ex13=None
names=['All cubic','Connected','Bridgeless connected','3-edge-connected']
cum={k:[] for k in '0123'}
for k in '0123':
    t=0
    for r in w[k]: t+=r['new'];cum[k].append(t)
    assert cum[k][:12]==ex['ranks'][k]
vs=[8,9,10,11,12,13,14]
t='<div class="frame"><table><thead><tr><th>Class</th>'+''.join(f'<th>\\(\\le{v}\\)</th>' for v in vs)+'<th>new 12</th><th>new 13</th><th>new 14</th></tr></thead><tbody>'
for k in range(4):
    c=cum[str(k)];t+=f'<tr><td>{names[k]}</td>'+''.join(f'<td>{c[v-1]}</td>' for v in vs)+f'<td>{c[11]-c[10]}</td><td>{c[12]-c[11]}</td><td>{c[13]-c[12]}</td></tr>'
t+='<caption>Cumulative rank of rational linear measurements. The lower bound is over hosts of order above \\(V\\); the panels below also suffice for smaller hosts through volume 14. Columns 8 to 10 reproduce the record; 11 to 14 are new.</caption></table></div>'
wt='<div class="frame"><table><thead><tr><th>\\(V\\)</th>'+''.join(f'<th>{n}</th>' for n in ['All','Conn.','Bridgeless','3-e.c.'])+'</tr></thead><tbody>'
for V in range(7,15):
    wt+=f'<tr><td>{V}</td>'
    for k in '0123':
        r=w[k][V-1];assert r['interval'];wt+=f"<td>{r['emin']}..{r['emax']} ({r['new']})</td>"
    wt+='</tr>'
wt+='<caption>Energy window \\(e_{\\min}..T_k(V)\\) in steps of 2, with the number of new directions in parentheses.</caption></table></div>'
gt='<div class="frame"><table><thead><tr><th>Girth at least</th>'+''.join(f'<th>{v}</th>' for v in range(6,13))+'<th>Cumulative \\(\\le12\\)</th></tr></thead><tbody>'
for gg in '34567':
    gt+=f'<tr><td>{gg}</td>'+''.join(f"<td>{g[gg]['new'][v-1]}</td>" for v in range(6,13))+f"<td>{g[gg]['ranks'][-1]}</td></tr>"
gt+='<caption>New measurements at each volume within the class of cubic graphs of girth at least \\(g\\). Rank at 1 prime on rows confirmed at 2 primes.</caption></table></div>'
dt='''<div class="frame"><table><thead><tr><th>\\(P\\) degree \\(m\\)</th><th>\\(u\\) degree \\(d\\)</th><th>Core</th><th>Depth</th><th>Status</th></tr></thead><tbody>
<tr><td>2</td><td>2</td><td>\\(K[Q]\\oplus\\langle q,qQ,q^2\\rangle\\), infinite</td><td>2</td><td>box scan</td></tr>
<tr><td>2</td><td>\\(\\ge3\\)</td><td>\\(\\langle1,q,Q,q^2,qQ,Q^2\\rangle\\), dimension 6</td><td>2</td><td>imported, box scan</td></tr>
<tr><td>\\(\\ge3\\)</td><td>2</td><td>\\(K[Q]\\oplus\\langle q\\rangle\\), infinite</td><td>1</td><td>box scan</td></tr>
<tr><td>\\(\\ge3\\)</td><td>\\(\\ge3\\)</td><td>\\(\\langle1,H\\rangle\\), dimension 2</td><td>1</td><td>proved</td></tr>
</tbody><caption>Depth is the least \\(r\\) with \\(\\bigcap_{j\\le r}\\ker C_3D^j\\) equal to the core. Box scans cover \\(m,d\\le5\\), \\(\\varepsilon\\in\\{0,1\\}\\). For \\(d=2,m\\ge3\\) the \\(q\\) term is present for all \\(\\varepsilon\\).</caption></table></div>'''
# plot
W,H=640,300;L,Rr,T,B=44,150,14,36
xs=list(range(4,15));ymax=36
X=lambda v:L+(v-4)*(W-L-Rr)/10;Y=lambda y:H-B-y*(H-T-B)/ymax
sv=''
for y in range(0,36,5):
    sv+=f'<line x1="{L}" x2="{W-Rr}" y1="{Y(y):.1f}" y2="{Y(y):.1f}" stroke="#d8c9b1" stroke-width="1"/><text x="{L-8}" y="{Y(y)+4:.1f}" text-anchor="end" font-size="13">{y}</text>'
for v in xs: sv+=f'<text x="{X(v):.1f}" y="{H-B+18}" text-anchor="middle" font-size="13">{v}</text>'
sv+=f'<text x="{(L+W-Rr)/2:.0f}" y="{H-4}" text-anchor="middle" font-size="13">Volume</text>'
cols=['#6e1423','#a24a3a','#8a6d3b','#3d4f5c'];end=[]
for k,c in zip('0123',cols):
    pts=[(X(r['V']),Y(r['new'])) for r in w[k] if r['V']>=4]
    sv+=f'<polyline fill="none" stroke="{c}" stroke-width="2" points="'+' '.join(f'{a:.1f},{b:.1f}' for a,b in pts)+'"/>'
    sv+=''.join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.6" fill="{c}"/>' for a,b in pts)
pts=[(X(v),Y(v//2+1)) for v in xs]
sv+='<polyline fill="none" stroke="#6f5d52" stroke-width="1.5" stroke-dasharray="4 4" points="'+' '.join(f'{a:.1f},{b:.1f}' for a,b in pts)+'"/>'
labs=[('All cubic',cols[0]),('Connected',cols[1]),('Bridgeless',cols[2]),('3-edge-connected',cols[3]),('Top-jet bound','#6f5d52')]
for i,(n,c) in enumerate(labs):
    y=30+i*22;sv+=f'<line x1="{W-Rr+12}" x2="{W-Rr+32}" y1="{y-4}" y2="{y-4}" stroke="{c}" stroke-width="2"/><text x="{W-Rr+38}" y="{y}" font-size="13">{n}</text>'
s=open('template.html').read()
tseq=', '.join(str(w['0'][v-1]['emax']) for v in range(4,15))
cross=next(v for v in range(4,15) if w['0'][v-1]['emax']>3*v)
sep13="All 620 pairs among same-order graphs through 14 vertices... "
rep={'{{RANKTABLE}}':t,'{{WINDOWTABLE}}':wt,'{{GIRTHTABLE}}':gt,'{{DEPTHTABLE}}':dt,'{{PLOT}}':sv,'{{TSEQ}}':tseq+' for \\(V=4,\\dots,14\\)','{{TCROSS}}':str(cross),'{{SEPN}}':'14',
'{{SEPTEXT}}':"There are 621 such graphs, and the count matches the known numbers 1, 2, 5, 19, 85, 509 by order, which is a further check on the generator. Exactly 1 pair, both on 14 vertices, agrees through volume 12. Direct integer enumeration of its height histograms confirms that agreement and finds the first difference at volume 13, in 24 energies, so all 621 graphs are separated by volume 13. The largest first-separating volume by order is 3, 4, 5, 8, 13 for 6, 8, 10, 12, 14 vertices, a fast growth that the conjecture would have to accommodate."}
for a,b in rep.items(): s=s.replace(a,b)
if ex13:
    r=ex13['ranks']; assert all(r[k][13]==cum[k][13] for k in '0123')
    s=s.replace("""Cumulative ranks through volume 12 are <span class="lab">exact</span> over \\(\\mathbb Q\\)""","""Cumulative ranks through volume 14 are <span class="lab">exact</span> over \\(\\mathbb Q\\)""")
    s=s.replace("""Volume 13 is <span class="lab">modular</span> at 1 prime, so 109, 103, 96 and 84 are rigorous lower bounds and expected values. ""","")
    s=s.replace(f"{ex['cross_prime_entries']:,} entries",f"{ex13['cross_prime_entries']:,} entries")
    s=s.replace("13 at 1 prime","13")
    s=s.replace("Volume 13 awaits a second prime and an exact rank. ","")
    s=s.replace("regenerates every statement labelled exact or modular through volume 12; volume 13 is a separate long run, roughly 30 minutes on 2 cores.","regenerates every statement through volume 12; the volume-13 replay is a separate long run, roughly 30 minutes per prime, and its row files are included.")
pp=[('11','4','pr_11_4'),('13','4','pr_13_4'),('14','4','P'),('14','5','pr_14_5'),('14','6','pr_14_6'),('14','7','pr_14_7')]
def comp(pr):
    pr=sorted(pr);o=[];a_=pr[0];b_=a_
    for x in pr[1:]:
        if x==b_+1:b_=x
        else:o.append((a_,b_));a_=b_=x
    o.append((a_,b_));return ', '.join(f'{u}..{v}' if u!=v else str(u) for u,v in o)
import os
OUT='/root/wms/out/'
pf='<div class="frame"><table><thead><tr><th>\\(V\\)</th><th>\\(j\\)</th><th>\\(\\dim W(V,j)\\)</th><th>Pole orders present</th></tr></thead><tbody>'
for V_,j_,src in pp:
    fn_=R+'promo_14_4.json' if src=='P' else OUT+src+'.json'
    if not os.path.exists(fn_): continue
    d_=json.load(open(fn_));pf+=f"<tr><td>{V_}</td><td>{j_}</td><td>{d_['dim']}</td><td>{comp(d_['pole_profile'])}</td></tr>"
pf+='<caption>Pole profile: the orders at which \\(W(V,j)\\) has an element with that top exponent, from an echelon form of the row polynomials at 1 prime.</caption></table></div>'
s=s.replace('{{PROFILETABLE}}',pf)
wf=R+'witness17_V13.json'
s=s.replace('{{W17}}','verified exactly on all earlier rows and by the independent evaluation,' if os.path.exists(wf) else 'verified on the modular rows,')
import sympy as sp
co=json.load(open(R+'j3_coefficients.json'));q=sp.Symbol('q')
names_={'pi':'\\\\log\\\\pi','phi':'\\\\log\\\\varphi','r2':'\\\\log(1+r_2)','r3':'\\\\log(1+r_3)','G22':'\\\\log(1+G_{22})','G23':'\\\\log(1+G_{23})','G33':'\\\\log(1+G_{33})'}
names_={k:v.replace('\\\\','\\') for k,v in names_.items()}
jt='<div class="frame"><table><thead><tr><th>Term</th><th>\\(x^2\\)</th><th>\\(x^3\\)</th></tr></thead><tbody>'
for k,nm in names_.items():
    jt+=f'<tr><td>\\({nm}\\)</td><td style="text-align:left">\\({sp.latex(sp.sympify(co[k][2]))}\\)</td><td style="text-align:left">\\({sp.latex(sp.sympify(co[k][3]))}\\)</td></tr>'
jt+='<caption>Coefficients of \\(\\Lambda_2,\\Lambda_3\\). The \\(x^1\\) terms are in Theorem 2. Scroll sideways for the long entries.</caption></table></div>'
s=s.replace('{{J3TABLE}}',jt)
ck=json.load(open(R+'j3_check_V13.json'))
s=s.replace('{{J3CHECK}}',f"the formulas for \\(J_0,\\dots,J_3\\) were compared with the certified rows of volume 13 for all patterns on at most 10 vertices, at \\(q=3/7,5/2,11/13\\), in {sum(ck['evaluations']):,} exact rational evaluations, with {sum(ck['failures'])} failures. The \\(J_3\\) test covers all patterns with \\(k\\le10\\).")
rc=json.load(open(R+'recovery_V13.json'))
rt='<div class="frame"><table><thead><tr><th>\\(V\\)</th>'+''.join(f'<th>\\(|Q|={k}\\)</th>' for k in (5,6,7,8,9))+'<th>Rank</th><th>Column classes</th></tr></thead><tbody>'
for V in ('8','9','10','11','12','13'):
    by=rc[V]['recoverable_by_size']
    rt+=f'<tr><td>{V}</td>'+''.join(f"<td>{by[str(k)][0]}/{by[str(k)][1]}</td>" if str(k) in by else '<td></td>' for k in (5,6,7,8,9))+f"<td>{rc[V]['rank']}</td><td>{rc[V]['classes']}</td></tr>"
rt+='<caption>Counts recoverable in arbitrary hosts from all coefficients through volume \\(V\\): number recoverable over number of patterns.</caption></table></div>'
s=s.replace('{{RECTABLE}}',rt)
rr=json.load(open(R+'rr_table.json'))
rt2='<div class="frame"><table><thead><tr><th>\\(V\\)</th>'+''.join(f'<th>\\(j={j}\\)</th>' for j in (0,2,3,4,5,6))+'</tr></thead><tbody>'
for V in ('9','10','11','12','13'):
    rt2+=f'<tr><td>{V}</td>'
    for j in ('0','2','3','4','5','6'):
        d=rr[V].get(j)
        rt2+=f"<td>{d['dim']}/{d['L_dim']}, {(d['emax']-3*int(V))//2}</td>" if d and d['dim'] else '<td></td>'
    rt2+='</tr>'
rt2+='<caption>Entries: \\(\\dim W(V,j)\\) over the dimension of all polynomials with the same exponent range divisible by \\((q^2-1)^V\\), then the polar order \\((e_{\\max}-3V)/2\\). Rank at 1 prime on certified rows.</caption></table></div>'
s=s.replace('{{RRTABLE}}',rt2)
lc=[json.load(open(R+f'lift_eval_V{v}.json')) for v in (15,16) if os.path.exists(R+f'lift_eval_V{v}.json')]
s=s.replace('{{LIFTCHECK}}',' '.join(f"At \\(V={c['V']}\\) the {c['support']}-pattern lift at size {c['k']}, completed by top patterns, annihilates all lower rows at {c['points']} values of \\(q\\) modulo \\(2^{{61}}-1\\), and interpolation with {c['slack_points']} spare points gives coefficient {c['top_coefficient']} at \\(q^{{{c['coefficient_at_energy']}}}\\), as predicted for \\(B(-1)=1\\)." for c in lc))
assert '{{' not in s
open('monograph.html','w').write(s)
print(len(s),tseq,cross)
