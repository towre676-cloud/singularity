from pathlib import Path
import json,math,html
P=Path(__file__).resolve().parent
D={R:json.loads((P/f'vol{R}_law.json').read_text()) for R in (9,10)}
C={R:json.loads((P/f'vol{R}_connectivity.json').read_text()) for R in (9,10)}
readers={R:json.loads((P/f'vol{R}_reader.json').read_text()) for R in (9,10)}
labels=['Possibly disconnected','Connected','Bridgeless connected','3-edge-connected']
rows=''.join(f'<tr><td>{labels[i]}</td><td>{C[9][i]["lower_rank"]}</td><td>{C[9][i]["total_rank"]}</td><td>{C[10][i]["total_rank"]}</td><td><b>{C[9][i]["new_rank"]}</b></td><td><b>{C[10][i]["new_rank"]}</b></td></tr>' for i in range(4))
chart=['<svg viewBox="0 0 1000 370" role="img" aria-label="Exact cumulative ranks through volumes eight, nine and ten">']
for x in (0,10,20,30,40,50):
 xx=230+14*x;chart.append(f'<path d="M{xx} 35V320" stroke="#293c4a"/><text x="{xx}" y="347" text-anchor="middle" fill="#adc0cc">{x}</text>')
for i,label in enumerate(labels):
 y=45+i*70;chart.append(f'<text x="212" y="{y+30}" text-anchor="end" fill="#eaf2f5" font-size="16">{label}</text>')
 for j,n in enumerate((C[9][i]['lower_rank'],C[9][i]['total_rank'],C[10][i]['total_rank'])):
  yy=y+j*18;col=['#6a8294','#65ded0','#ffcc7f'][j]
  chart.append(f'<rect x="230" y="{yy}" width="{14*n}" height="13" rx="3" fill="{col}"/><text x="{237+14*n}" y="{yy+11}" fill="{col}" font-size="13">{n}</text>')
chart.append('</svg>');chart=''.join(chart)
from vol9_build import lib
atlas=[]
patterns=json.loads((P/'high_girth_law.json').read_text())[0]['top_patterns']
for index,d in enumerate(patterns):
 x0=15+index%5*194;y0=25+index//5*190
 k=d['k'];E=d['edges'];xy=[[math.cos(2*math.pi*j/k),math.sin(2*math.pi*j/k)] for j in range(k)]
 # Deterministic force layout is illustrative only; exact edges stay unchanged.
 for it in range(180):
  forces=[[0.,0.] for _ in range(k)]
  for u in range(k):
   for v in range(u):
    dx=xy[u][0]-xy[v][0];dy=xy[u][1]-xy[v][1];r2=max(.02,dx*dx+dy*dy);f=.07/r2
    forces[u][0]+=dx*f;forces[v][0]-=dx*f;forces[u][1]+=dy*f;forces[v][1]-=dy*f
  for u,v in E:
   dx=xy[u][0]-xy[v][0];dy=xy[u][1]-xy[v][1];r=math.sqrt(dx*dx+dy*dy);f=.15*(r-.9)/max(r,.01)
   forces[u][0]-=dx*f;forces[v][0]+=dx*f;forces[u][1]-=dy*f;forces[v][1]+=dy*f
  for u in range(k):
   for a in range(2):xy[u][a]+=max(-.05,min(.05,forces[u][a]));xy[u][a]*=.998
 extent=max(abs(z) for v in xy for z in v);xy=[(x0+92+62*x/extent,y0+83+62*y/extent) for x,y in xy]
 atlas.append(f'<rect x="{x0}" y="{y0}" width="184" height="179" rx="10" fill="#152735" stroke="#294251"/>')
 for u,v in E:
  x,y=xy[u];xx,yy=xy[v];atlas.append(f'<path d="M{x:.2f} {y:.2f}L{xx:.2f} {yy:.2f}" stroke="#91b9ca" stroke-width="2"/>')
 ds=[sum(j in e for e in E) for j in range(k)]
 for u,(x,y) in enumerate(xy):atlas.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="{"#ffcc7f" if ds[u]==3 else "#65ded0"}"/>')
 atlas.append(f'<text x="{x0+92}" y="{y0+166}" fill="#dfedf3" font-size="13" text-anchor="middle">9 vertices · {len(E)} edges</text>')
atlas='<svg viewBox="0 0 1000 420" role="img" aria-label="The ten nine-vertex leafless patterns of girth at least five">'+''.join(atlas)+'</svg>'
girth9=json.loads((P/'vol9_girth.json').read_text());girth10=json.loads((P/'vol10_girth.json').read_text())
grows=''
for g in range(4,11):
 n=next(x['new_rank'] for x in girth9 if x['girth_at_least']==g and x['edge_connectivity']==0)
 d=next(x for x in girth10 if x['girth_at_least']==g)
 grows+=f'<tr><td>At least {g}</td><td>{n}</td><td>{d["new_rank"]}</td><td>{"Yes" if d["lower_support_cancels"] else "No"}</td></tr>'
readerblocks=''
for R in (9,10):
 r=readers[R];readerblocks+=f'<div class="card"><h3>Volume {R}</h3><p>{r["dimension"]} coefficients reconstruct the entire difference, conditional on complete agreement through {R-1}.</p><pre>q degrees: '+', '.join(map(str,r['coefficient_degrees']))+f'\nDeterminant: {r["determinant"]}</pre><p class="small">Exact inverse and every source-row witness are included. This panel is invertible; it has not been optimized for noise amplification.</p></div>'
s='''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Singularity — Volume Nine and Ten</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1621;color:#eaf2f5;font:17px/1.65 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:42px 28px 80px}h1{font-size:clamp(37px,6vw,68px);line-height:1.05;letter-spacing:-.04em}h2{font-size:29px;margin-top:48px;line-height:1.2}h3{color:#65ded0}.eyebrow{color:#65ded0;font-size:13px;letter-spacing:.14em;text-transform:uppercase}.lede{font-size:22px;color:#b4c6d1}.cards{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card,.note{background:#142432;border:1px solid #294251;border-radius:13px;padding:23px}.metric{font-size:48px;line-height:1.1;color:#ffcc7f;font-weight:750}.small{font-size:14px;color:#b4c6d1}svg{width:100%;height:auto;background:#10202d;border:1px solid #294251;border-radius:12px;margin:20px 0}table{width:100%;border-collapse:collapse;font-size:15px}th,td{text-align:left;border-bottom:1px solid #294251;padding:14px 11px}th{color:#ffcc7f}pre{background:#07111b;border-left:3px solid #65ded0;padding:20px;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.65;font-size:15px}a{color:#65ded0}.tablewrap{overflow:auto}details{padding:18px;background:#142432;border:1px solid #294251;border-radius:10px;margin:16px 0}summary{cursor:pointer;color:#65ded0;font-weight:650}@media(max-width:700px){main{padding:26px 16px}.cards{grid-template-columns:1fr}table{min-width:620px}}@media print{body{background:white;color:#142432}.card,.note,details,svg,pre{background:#f5f8fa}.small,.lede{color:#415a6a}h2{break-after:avoid}th{color:#415a6a}}
</style></head><body><main><div class="eyebrow">Exact mathematics · 4 November 2026 · Singularity</div><h1>Two more layers of hidden graph structure.</h1><p class="lede">The ninth-order and tenth-order cubic height-series laws are complete, with exact coefficient readers, connectivity-dependent minima and realizable witness recipes.</p>
<div class="cards"><div class="card"><div class="metric">24 → 34 → 48</div><h3>Cumulative unrestricted observation rank</h3><p>Ten new directions appear at volume nine. Fourteen more appear at volume ten. Every direction has an exact count-coordinate definition.</p></div><div class="card"><div class="metric">112 / 112</div><h3>Independent direct-height host checks</h3><p>Every connected cubic graph through twelve vertices agrees with the computed law through volume ten: 1,232 coefficient comparisons, zero failures.</p></div></div>
<h2>The measurement minima now depend on both volume and connectivity</h2><p>Assume full coefficientwise height-series agreement through the preceding volume. The last two columns give the exact uniform minimum number of fixed rational linear observations needed to recover the next difference.</p><div class="tablewrap"><table><thead><tr><th>Graph class</th><th>Rank ≤8</th><th>Rank ≤9</th><th>Rank ≤10</th><th>New at 9</th><th>New at 10</th></tr></thead><tbody>ROWS</tbody></table></div><p class="small">Cumulative ranks include vertex order. The minima concern unbounded classes and exact rational linear measurements. They do not assert the same minimum at a fixed small graph order, under nonlinear encodings or under measurement noise.</p>CHART<p class="small">Grey: through eight. Cyan: through nine. Gold: through ten. Bar lengths encode the exact cumulative ranks in the table.</p>
<h2>These are complete formulas, not fitted regressions</h2><p>For a cubic graph, energy equals 3Σh²−2Σhᵤhᵥ. Connected-support and edge inversion express log L as a finite sum of ordinary subgraph counts. The leaf recurrence removes forced tree extensions, leaving leafless cores. Exact rational elimination then identifies precisely what the previous observations left hidden.</p><pre>L_G(x,q)=Σ_h x^(Σh) q^(Σ_edges(hᵤ−hᵥ)²)
κ=q(1−q²),  f=q⁻²−1

If all lower coefficients agree:
ΔL_R=κ^R Σ_j f^j ΔS_(R,R+j)
      + Σ_(smaller cores H) ρ_(R,H)(q) ΔN_H,  R=9,10.</pre><p>The ninth correction has 25 lower-core columns; the tenth has 123. The package gives every exact polynomial, every leaf reduction and the lower-row elimination certificates. The ninth law compresses to five corrected top-size sums and five delayed lower coordinates. The tenth compresses to six corrected sums and eight delayed coordinates.</p><div class="cards">READERS</div>
<details><summary>The explicit ninth-order coefficient functions</summary><p>Set t=q² and a=(1+t)³−1. In the certified coordinate order, divide the difference by κ⁹. Its ten functions are:</p><pre>1, f, f², f³, f⁴,
f P_A(t), P_B(t)/t, −2f² P_C(t), a, f(1+t)³

P_A=t⁶+4t⁵+4t⁴−5t³−15t²−14t−6
P_B=t⁷+3t⁶+t⁵−6t⁴−9t³−5t²−t+1
P_C=t⁶+5t⁵+9t⁴+5t³−5t²−9t−3</pre><p>The lower coordinates are defined as count combinations in the reader, rather than being inferred from names. For example they include K₃,₃ minus an edge mixed with half the eight-vertex nine-edge sum. Delayed information genuinely crosses support sizes.</p></details>
<h2>High girth exposes a simpler structure—and its limit</h2><div class="tablewrap"><table><thead><tr><th>Girth</th><th>New directions at 9</th><th>New directions at 10</th><th>Lower supports cancel at 10?</th></tr></thead><tbody>GIRTH</tbody></table></div><p class="small">This table concerns the unrestricted cubic class with the displayed girth restriction. The same separated-site realization argument applies. Every statement assumes agreement at all earlier volumes.</p><p>At volume nine and girth at least five, all lower-support contributions cancel. The ten surviving top patterns form four edge classes:</p><pre>ΔL₉=κ⁹[ΔS₉,₉+fΔS₉,₁₀+f²ΔS₉,₁₁+f³ΔS₉,₁₂].</pre>ATLAS<p class="small">The ten exact nine-vertex cores of girth at least five: 1, 4, 4 and 1 types by edge class. Gold vertices have degree three; cyan vertices degree two. Layouts are illustrative; exact edge lists are included.</p><p>At girth six this becomes κ⁹ times the nine-cycle difference plus f times the sum of Θ(2,4,4) and Θ(3,3,4). At girth at least seven only C₉ remains. At volume ten, girth seven leaves C₁₀ and Θ(3,4,4); girth at least eight leaves only C₁₀.</p><p class="note"><b>A useful negative result:</b> girth five does not eliminate delayed lower-support information at volume ten. Its seven-dimensional difference space cannot be replaced by the six top edge-count sums alone.</p>
<h2>Why a rank calculation becomes a theorem about actual graphs</h2><p>The realization proof extends the earlier reservoir construction to every cutoff at most eleven. Admissible seed cores satisfy 3|U|−2|E(U)|≥λ for every nonempty vertex subset. Their ordinary-count matrix is unitriangular, hence has an integral inverse. An integer core vector can therefore be isolated by a signed seed combination.</p><p>Attach missing seed half-edges to separate sites in a large 3-edge-connected reservoir assembled from the explicit girth-twelve cubic graph. Distinct sites are at distance at least eleven. A new leafless core through ten vertices cannot cross the reservoir: it would need either a twelve-cycle or a tree connecting two distant sites. Core counts are preserved, including bridge-containing patterns. Singleton and edge fillers equalize the two graph orders without scaling the core vector.</p><p>For unrestricted graphs, separate high-girth cap completions plus the core-free order identity 510−382−126=2 equalize every even discrepancy. This strengthens the realization statement to unit scale there as well. Each class has exact isolated target-measurement witnesses. Rational kernels for fewer measurements clear to integer core vectors and hence to actual compatible graph pairs.</p><p class="small">The witness recipes can specify very large graphs. Their exact seed arithmetic and structural construction are certified; those large graphs were not allocated or exhaustively height-enumerated. Their orders are construction upper bounds, not minimum witness sizes.</p>
<h2>What was independently checked</h2><p>The catalogue contains 531 connected subcubic types at order nine and 1,733 at order ten. Canonical augmentation agrees with extending every smaller connected type by one vertex. All 2,264 automorphism orders also agree with an independently written adjacency-preserving backtracker.</p><p>For host verification, a new counter enumerates induced subsets and matchings of removable edges. In a subcubic induced graph, deleting edges while keeping every degree at least two means deleting a matching between degree-three vertices. This gives exact ordinary leafless counts; eight tiny hosts additionally agree with raw edge-subset enumeration. Direct C++ weak-composition enumeration then checks every height coefficient through ten on all 112 connected cubic hosts through twelve vertices.</p><p>The inherited pure Q₀ and Q₁ twenty-vertex witnesses also pass direct height enumeration and bridgelessness checks. The reservoir parent passes fresh girth and connectivity checks; a fully materialized 756-vertex triangle-seed example passes simplicity, cubicity and three-edge-connectivity checks. Their minimum possible orders remain separate questions.</p>
<h2>Proof boundary and next target</h2><p>These are mathematical arguments with exact integer/rational computation, conditional on the established support expansion and earlier off-diagonal identities. They are not proof-assistant formalizations. Every reader has both coordinate source-row witnesses and complete polynomial reconstruction checks. The package includes fast saved-certificate audits, full regeneration scripts, source hashes and pinned dependencies.</p><p>The next coefficient target is <b>volume eleven</b>. The new realization lemma already covers it, but its coefficient table and observation rank have not been computed here. Noise-optimal ninth/tenth panels and minimum-order pure witnesses also remain open. Canonical repository files were not changed.</p><p class="small">Source baseline: <a href="https://github.com/towre676-cloud/singularity/tree/17f033ea9a1e6d93224e946a341f7a0e545ee64a">Singularity 17f033e</a>. The complete human-readable proof is VOLUME9_10_THEOREMS.md inside the downloadable package.</p></main></body></html>'''
s=s.replace('ROWS',rows).replace('CHART',chart).replace('READERS',readerblocks).replace('GIRTH',grows).replace('ATLAS',atlas)
(P/'Singularity_Volume9_10_Theorems_2026-11-04.html').write_text(s)
print('Wrote illustrated report')
