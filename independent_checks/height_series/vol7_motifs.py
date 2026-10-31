#!/usr/bin/env python3
"""Exact seven-vertex core catalogue and a labelled SVG contact sheet.

Only the drawing routine uses floating point. All graph identities and
catalogue fields are discrete and derive from vol7_lib.
"""
import json, math, random
from collections import Counter, deque
from html import escape
from pathlib import Path
from vol7_lib import connected_types,edges_of,degrees_of,connected_mask,mask_from_edges

HERE=Path(__file__).resolve().parent


def topological_kernel(es):
    adj=[set() for _ in range(7)]
    for a,b in es: adj[a].add(b); adj[b].add(a)
    branches=[v for v in range(7) if len(adj[v])==3]
    if not branches: return {'kind':'cycle','cycle_length':7,'branch_vertices':[],'paths':[]}
    used=set();paths=[]
    for a in branches:
        for b in sorted(adj[a]):
            if tuple(sorted((a,b))) in used: continue
            path=[a,b];used.add(tuple(sorted((a,b))))
            while len(adj[b])==2:
                nxt=next(c for c in adj[b] if c!=path[-2]);path.append(nxt)
                used.add(tuple(sorted((b,nxt))));b=nxt
            paths.append({'endpoints':[a,b],'length':len(path)-1,'vertices':path})
    multiplicities=Counter(tuple(sorted(p['endpoints'])) for p in paths)
    loops=sum(a==b for a,b in multiplicities)
    kind='cubic_multigraph'
    if not loops and max(multiplicities.values())==1:
        kind='K4' if len(branches)==4 else 'simple_cubic'
    return {'kind':kind,'branch_vertices':branches,'paths':paths,
        'edge_multiplicities':[{'endpoints':list(p),'multiplicity':c} for p,c in sorted(multiplicities.items())]}


def shortest_cycle(es):
    adj=[set() for _ in range(7)]
    for a,b in es: adj[a].add(b);adj[b].add(a)
    best=8
    for a,b in es:
        dist={a:0};queue=deque([a])
        while queue:
            u=queue.popleft()
            for w in adj[u]:
                if {u,w}=={a,b}:continue
                if w not in dist:dist[w]=dist[u]+1;queue.append(w)
        if b in dist:best=min(best,dist[b]+1)
    return best if best<8 else None

NAMES={15796:'K4: triangle-edge subdivision',40564:'Double-pair ring: parallel arcs',
    44280:'K4: star-edge subdivision',44404:'K4: path-edge subdivision',
    44466:'Double-pair ring: subdivided link',269556:'K4: adjacent (3,2) paths',
    277669:'Triangle–diamond bridge',304358:'K4: opposite (3,2) paths',
    306277:'Double-pair ring: extended arc',789222:'K4: one path of length 4',
    48824:'Prism: subdivided triangle edge',111864:'K3,3: subdivided edge',
    111988:'Prism: subdivided spoke',113969:'Triangle–diamond double link'}


def catalogue():
    rows=[];j_by_e=Counter()
    for m in connected_types(7):
        if min(degrees_of(m,7))<2:continue
        es=edges_of(m,7);e=m.bit_count();j_by_e[e]+=1
        kernel=topological_kernel(es);name=NAMES.get(m)
        theta=None;barbell=None
        if e==7:name='C7 — heptagon'
        if e==8:
            paths=kernel['paths']
            if all(p['endpoints'][0]!=p['endpoints'][1] for p in paths):
                theta=sorted(p['length']for p in paths);name='Theta('+','.join(map(str,theta))+')'
            else:
                loops=sorted(p['length']for p in paths if p['endpoints'][0]==p['endpoints'][1])
                bridge=next(p['length']for p in paths if p['endpoints'][0]!=p['endpoints'][1])
                barbell={'cycle_lengths':loops,'joining_path_length':bridge}
                name='Barbell ('+','.join(map(str,loops))+'; path '+str(bridge)+')'
        bridges=[]
        for edge in es:
            remaining=[x for x in es if x!=edge]
            if not connected_mask(mask_from_edges(7,remaining),7):bridges.append(list(edge))
        row={'label':f'H7_{e}_{j_by_e[e]}','vertices':7,'mask':m,'edge_count':e,
            'edges':[list(x)for x in es],'degree_sequence':list(sorted(degrees_of(m,7),reverse=True)),
            'name':name,'girth':shortest_cycle(es),'bridges':bridges,'cycle_rank':e-6,
            'top_coefficient':'q^21 (q^-2 - 1)^'+str(e),
            'normalized_top_coefficient':'kappa^7 f^'+str(e-7),
            'topological_kernel':kernel}
        if theta:row['theta_path_lengths']=theta
        if barbell:row['barbell_parameters']=barbell
        if m in (48824,111864,111988):
            row['simple_cubic_suppression']={'host':'K3,3'if m==111864 else 'triangular prism',
                'edge_orbit':'edge'if m==111864 else 'triangle edge'if m==48824 else 'spoke'}
        rows.append(row)
    assert len(rows)==21 and dict(j_by_e)=={7:1,8:6,9:10,10:4}
    return {'schema':'singularity-volume7-core-motifs-v1',
        'convention':'canonical masks use vol7_lib degree-sorted canonical labelling; subgraphs are non-induced',
        'motif_count':21,'by_edges':dict(j_by_e),'motifs':rows}


def crossing(a,b,c,d):
    def side(x,y,z):return (y[0]-x[0])*(z[1]-x[1])-(y[1]-x[1])*(z[0]-x[0])
    return side(a,b,c)*side(a,b,d)<-1e-9 and side(c,d,a)*side(c,d,b)<-1e-9


def layout(row):
    """Deterministic spring layout; floats affect the SVG only."""
    rng=random.Random(row['mask']);es=row['edges'];best=None
    kernel=row['topological_kernel']
    exact_embedding=None
    if kernel['kind']=='K4':
        branch=kernel['branch_vertices']
        coords={branch[0]:(0,-1),branch[1]:(math.sqrt(3)/2,.5),
                branch[2]:(-math.sqrt(3)/2,.5),branch[3]:(0,0)}
        for path in kernel['paths']:
            vs=path['vertices'];a=coords[vs[0]];b=coords[vs[-1]]
            for i,v in enumerate(vs[1:-1],1):
                t=i/(len(vs)-1);coords[v]=((1-t)*a[0]+t*b[0],(1-t)*a[1]+t*b[1])
        exact_embedding=[list(coords[v])for v in range(7)]
    if row.get('simple_cubic_suppression',{}).get('host')=='triangular prism':
        from itertools import combinations
        sub=next(v for v,d in enumerate(degrees_of(row['mask'],7))if d==2)
        nbr=[w for edge in es if sub in edge for w in edge if w!=sub]
        core=[tuple(sorted(e))for e in es if sub not in e]+[tuple(sorted(nbr))]
        verts=[v for v in range(7)if v!=sub]
        outer=next(t for t in combinations(verts,3)if all(tuple(sorted(e))in core for e in combinations(t,2)))
        inner=[v for v in verts if v not in outer];coords={}
        for i,v in enumerate(outer):
            ang=-math.pi/2+2*math.pi*i/3;coords[v]=(math.cos(ang),math.sin(ang))
            partner=next(w for w in inner if tuple(sorted((v,w)))in core)
            coords[partner]=(.42*math.cos(ang),.42*math.sin(ang))
        a,b=(coords[v]for v in nbr);coords[sub]=((a[0]+b[0])/2,(a[1]+b[1])/2)
        exact_embedding=[list(coords[v])for v in range(7)]
    if exact_embedding is not None:
        xs=[x for x,y in exact_embedding];ys=[y for x,y in exact_embedding]
        scale=min(205/(max(xs)-min(xs)),140/(max(ys)-min(ys)))
        cx=(max(xs)+min(xs))/2;cy=(max(ys)+min(ys))/2
        return [(150+(x-cx)*scale,131+(y-cy)*scale)for x,y in exact_embedding]
    for attempt in range(30):
        order=list(range(7));rng.shuffle(order)
        pos=[[math.cos(2*math.pi*order[v]/7),math.sin(2*math.pi*order[v]/7)]for v in range(7)]
        if attempt:
            for p in pos:p[0]+=rng.uniform(-.2,.2);p[1]+=rng.uniform(-.2,.2)
        for it in range(220):
            force=[[0.,0.]for _ in range(7)]
            for a in range(7):
                for b in range(a):
                    dx=pos[a][0]-pos[b][0];dy=pos[a][1]-pos[b][1];d2=dx*dx+dy*dy+.001
                    for v,sgn in ((a,1),(b,-1)):
                        force[v][0]+=sgn*dx*.35/d2;force[v][1]+=sgn*dy*.35/d2
            for a,b in es:
                dx=pos[a][0]-pos[b][0];dy=pos[a][1]-pos[b][1];d=math.hypot(dx,dy)+.001
                f=(d-.75)*.7
                force[a][0]-=dx/d*f;force[a][1]-=dy/d*f
                force[b][0]+=dx/d*f;force[b][1]+=dy/d*f
            temp=.12*(1-it/220)+.002
            for v in range(7):
                d=math.hypot(*force[v])+.0001
                pos[v][0]+=force[v][0]*min(temp/d,.3);pos[v][1]+=force[v][1]*min(temp/d,.3)
        cx=sum(p[0]for p in pos)/7;cy=sum(p[1]for p in pos)/7
        pos=[[p[0]-cx,p[1]-cy]for p in pos]
        scale=max(max(p[0]for p in pos)-min(p[0]for p in pos),max(p[1]for p in pos)-min(p[1]for p in pos))
        pos=[[x/scale,y/scale]for x,y in pos]
        score=0.
        for i,(a,b)in enumerate(es):
            for c,d in es[:i]:
                if len({a,b,c,d})==4 and crossing(pos[a],pos[b],pos[c],pos[d]):score+=100
        score+=sum((math.dist(pos[a],pos[b])-.44)**2 for a,b in es)
        if best is None or score<best[0]:best=(score,pos)
    pos=best[1]
    # Rotate the principal axis horizontally for stable, compact composition.
    xx=sum(x*x for x,y in pos);yy=sum(y*y for x,y in pos);xy=sum(x*y for x,y in pos)
    angle=.5*math.atan2(2*xy,xx-yy);co=math.cos(angle);si=math.sin(angle)
    pos=[[co*x+si*y,-si*x+co*y]for x,y in pos]
    scale=min(205/(max(x for x,y in pos)-min(x for x,y in pos)+.001),140/(max(y for x,y in pos)-min(y for x,y in pos)+.001))
    cx=(max(x for x,y in pos)+min(x for x,y in pos))/2;cy=(max(y for x,y in pos)+min(y for x,y in pos))/2
    return [(150+(x-cx)*scale,131+(y-cy)*scale)for x,y in pos]


def svg(data):
    colors={7:'#326b8e',8:'#307c72',9:'#765b9c',10:'#b06c34'}
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="1820" viewBox="0 0 960 1820">',
        '<rect width="960" height="1820" fill="#f7f7f3"/>',
        '<text x="30" y="42" font-family="Georgia,serif" font-size="27" fill="#182c35">The 21 seven-vertex cubic-support cores</text>',
        '<text x="30" y="67" font-family="Arial,sans-serif" font-size="13" fill="#56636a">Non-induced motifs · minimum degree 2 · exact graph labels match vol7_motifs.json</text>']
    for i,row in enumerate(data['motifs']):
        col=i%3;line=i//3;x=20+col*315;y=90+line*245;color=colors[row['edge_count']]
        out.append(f'<g transform="translate({x},{y})">')
        out.append('<rect width="300" height="230" rx="8" fill="white" stroke="#d7dedc"/>')
        out.append(f'<text x="15" y="24" font-family="Arial,sans-serif" font-size="15" font-weight="700" fill="{color}">{row["label"]}</text>')
        out.append(f'<text x="285" y="24" text-anchor="end" font-family="Arial,sans-serif" font-size="12" fill="#58666d">e = {row["edge_count"]} · g = {row["girth"]}</text>')
        out.append(f'<text x="15" y="44" font-family="Arial,sans-serif" font-size="12" fill="#283d48">{escape(row["name"])}</text>')
        ps=layout(row)
        for a,b in row['edges']:
            ax,ay=ps[a];bx,by=ps[b]
            out.append(f'<line x1="{ax:.2f}" y1="{ay:.2f}" x2="{bx:.2f}" y2="{by:.2f}" stroke="{color}" stroke-width="2.5"/>')
        for v,(vx,vy)in enumerate(ps):
            out.append(f'<circle cx="{vx:.2f}" cy="{vy:.2f}" r="7.5" fill="white" stroke="{color}" stroke-width="2"/>')
            out.append(f'<text x="{vx:.2f}" y="{vy+3.2:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="9" fill="#213741">{v}</text>')
        out.append(f'<text x="15" y="217" font-family="Arial,sans-serif" font-size="11" fill="#68757a">mask {row["mask"]} · {len(row["bridges"])} bridge'+('s'if len(row['bridges'])!=1 else '')+'</text>')
        out.append('</g>')
    out.append('<text x="30" y="1805" font-family="Arial,sans-serif" font-size="12" fill="#65727a">Each motif has leading kernel q²¹ fᵉ = κ⁷ fᵉ⁻⁷; reduced laws also contain inherited-core terms.</text></svg>')
    return '\n'.join(out)+'\n'

if __name__=='__main__':
    data=catalogue()
    (HERE/'vol7_motifs.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    (HERE/'vol7_motifs.svg').write_text(svg(data))
    print('Wrote 21 exact motifs and SVG contact sheet')
