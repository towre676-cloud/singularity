#!/usr/bin/env python3
"""Exact eight-vertex core catalogue and a labelled SVG contact sheet.

Only the drawing routine uses floating point. All graph identities and
catalogue fields are discrete and derive from vol8_lib.
"""
import json, math, random
from collections import Counter, deque
from html import escape
from pathlib import Path
from vol8_lib import connected_types,edges_of,degrees_of,connected_mask,mask_from_edges,canonical

HERE=Path(__file__).resolve().parent


def topological_kernel(es):
    adj=[set() for _ in range(8)]
    for a,b in es: adj[a].add(b); adj[b].add(a)
    branches=[v for v in range(8) if len(adj[v])==3]
    if not branches: return {'kind':'cycle','cycle_length':8,'branch_vertices':[],'paths':[]}
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
    adj=[set() for _ in range(8)]
    for a,b in es: adj[a].add(b);adj[b].add(a)
    best=9
    for a,b in es:
        dist={a:0};queue=deque([a])
        while queue:
            u=queue.popleft()
            for w in adj[u]:
                if {u,w}=={a,b}:continue
                if w not in dist:dist[w]=dist[u]+1;queue.append(w)
        if b in dist:best=min(best,dist[b]+1)
    return best if best<9 else None

CUBIC8_NAMES={2022000:'Cube Q3',5683824:'Wagner graph M8',
    5192304:'Triangle-expanded K3,3',5691760:'Triangle-expanded prism',6215777:'Diamond-pair cubic core'}


def kernel_name(kernel,e,m):
    if e==8:return 'C8 — octagon'
    paths=kernel['paths'];branches=kernel['branch_vertices']
    if len(branches)==2:
        if all(p['endpoints'][0]!=p['endpoints'][1] for p in paths):
            return 'Theta('+','.join(map(str,sorted(p['length']for p in paths)))+')'
        loops=sorted(p['length']for p in paths if p['endpoints'][0]==p['endpoints'][1])
        joining=next(p['length']for p in paths if p['endpoints'][0]!=p['endpoints'][1])
        return 'Barbell ('+','.join(map(str,loops))+'; path '+str(joining)+')'
    if len(branches)==8:return CUBIC8_NAMES[m]
    lengths=','.join(map(str,sorted(p['length']for p in paths)))
    if kernel['kind']=='K4':return 'K4 paths ['+lengths+']'
    if kernel['kind']=='simple_cubic':
        ix={v:i for i,v in enumerate(branches)}
        km=canonical(mask_from_edges(len(branches),[(ix[p['endpoints'][0]],ix[p['endpoints'][1]])for p in paths]),len(branches))
        name='K3,3'if km==canonical(mask_from_edges(6,[(a,b)for a in range(3)for b in range(3,6)]),6)else 'Prism'
        return name+' subdivision ['+lengths+']'
    loops=sum(p['endpoints'][0]==p['endpoints'][1]for p in paths)
    return ('Looped'if loops else 'Parallel-edge')+' cubic kernel; '+str(len(branches))+' branches'


def catalogue():
    rows=[];j_by_e=Counter()
    for m in connected_types(8):
        if min(degrees_of(m,8))<2:continue
        es=edges_of(m,8);e=m.bit_count();j_by_e[e]+=1
        kernel=topological_kernel(es);name=kernel_name(kernel,e,m)
        bridges=[]
        for edge in es:
            if not connected_mask(mask_from_edges(8,[x for x in es if x!=edge]),8):bridges.append(list(edge))
        row={'label':f'H8_{e}_{j_by_e[e]}','vertices':8,'mask':m,'edge_count':e,
            'edges':[list(x)for x in es],'degree_sequence':list(sorted(degrees_of(m,8),reverse=True)),
            'name':name,'girth':shortest_cycle(es),'bridges':bridges,'cycle_rank':e-7,
            'top_coefficient':'q^24 (q^-2 - 1)^'+str(e),
            'normalized_top_coefficient':'kappa^8 f^'+str(e-8),
            'topological_kernel':kernel}
        if len(kernel['branch_vertices'])==2:
            paths=kernel['paths']
            if all(p['endpoints'][0]!=p['endpoints'][1]for p in paths):row['theta_path_lengths']=sorted(p['length']for p in paths)
            else:row['barbell_parameters']={'cycle_lengths':sorted(p['length']for p in paths if p['endpoints'][0]==p['endpoints'][1]),'joining_path_length':next(p['length']for p in paths if p['endpoints'][0]!=p['endpoints'][1])}
        rows.append(row)
    assert len(rows)==60 and dict(j_by_e)=={8:1,9:10,10:25,11:19,12:5}
    return {'schema':'singularity-volume8-core-motifs-v1',
        'convention':'canonical masks use vol8_lib degree-sorted canonical labelling; subgraphs are non-induced',
        'motif_count':60,'by_edges':dict(j_by_e),'motifs':rows}


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
        exact_embedding=[list(coords[v])for v in range(8)]
    if kernel['kind']=='simple_cubic' and len(kernel['branch_vertices'])==6:
        branches=kernel['branch_vertices'];paths=kernel['paths']
        core={tuple(sorted(p['endpoints']))for p in paths}
        from itertools import combinations
        triangles=[t for t in combinations(branches,3)if all(tuple(sorted(e))in core for e in combinations(t,2))]
        if triangles:
            outer=triangles[0];inner=[v for v in branches if v not in outer];coords={}
            for i,v in enumerate(outer):
                ang=-math.pi/2+2*math.pi*i/3;coords[v]=(math.cos(ang),math.sin(ang))
                partner=next(w for w in inner if tuple(sorted((v,w)))in core)
                coords[partner]=(.4*math.cos(ang),.4*math.sin(ang))
            for path in paths:
                vs=path['vertices'];a=coords[vs[0]];b=coords[vs[-1]]
                for i,v in enumerate(vs[1:-1],1):
                    t=i/(len(vs)-1);coords[v]=((1-t)*a[0]+t*b[0],(1-t)*a[1]+t*b[1])
            exact_embedding=[list(coords[v])for v in range(8)]
    if row['mask']==2022000:
        from itertools import combinations
        edge_set={tuple(sorted(e))for e in es}
        face=next(vs for vs in combinations(range(8),4)
                  if sum(tuple(sorted(e))in edge_set for e in combinations(vs,2))==4
                  and all(sum(tuple(sorted((v,w)))in edge_set for w in vs if w!=v)==2 for v in vs))
        cycle=[face[0]]
        while len(cycle)<4:
            cycle.append(next(w for w in face if w not in cycle and tuple(sorted((cycle[-1],w)))in edge_set))
        coords={}
        for i,v in enumerate(cycle):
            ang=math.pi/4+math.pi*i/2;coords[v]=(math.cos(ang),math.sin(ang))
            partner=next(w for w in range(8)if w not in face and tuple(sorted((v,w)))in edge_set)
            coords[partner]=(.43*math.cos(ang),.43*math.sin(ang))
        exact_embedding=[list(coords[v])for v in range(8)]
    if row['mask']==5691760:
        from itertools import combinations
        edge_set={tuple(sorted(e))for e in es}
        triangles=[t for t in combinations(range(8),3)if all(tuple(sorted(e))in edge_set for e in combinations(t,2))]
        for triangle in triangles:
            verts=[v for v in range(8)if v not in triangle]+[8]
            core={tuple(sorted((8 if a in triangle else a,8 if b in triangle else b)))for a,b in es if not(a in triangle and b in triangle)}
            outer=next((t for t in combinations(verts,3)if all(tuple(sorted(e))in core for e in combinations(t,2))),None)
            if outer is None:continue
            inner=[v for v in verts if v not in outer];coords={}
            if any(sum(tuple(sorted((v,w)))in core for w in inner)!=1 for v in outer):continue
            for i,v in enumerate(outer):
                ang=-math.pi/2+2*math.pi*i/3;coords[v]=(math.cos(ang),math.sin(ang))
                partner=next(w for w in inner if tuple(sorted((v,w)))in core)
                coords[partner]=(.42*math.cos(ang),.42*math.sin(ang))
            center=coords[8]
            for v in triangle:
                other=next(w for edge in es if v in edge for w in edge if w!=v and w not in triangle)
                target=coords[other];dx=target[0]-center[0];dy=target[1]-center[1];dist=math.hypot(dx,dy)
                coords[v]=(center[0]+.16*dx/dist,center[1]+.16*dy/dist)
            exact_embedding=[list(coords[v])for v in range(8)]
            break
    if exact_embedding is not None:
        xs=[x for x,y in exact_embedding];ys=[y for x,y in exact_embedding]
        scale=min(205/(max(xs)-min(xs)),140/(max(ys)-min(ys)))
        cx=(max(xs)+min(xs))/2;cy=(max(ys)+min(ys))/2
        return [(150+(x-cx)*scale,131+(y-cy)*scale)for x,y in exact_embedding]
    for attempt in range(20):
        order=list(range(8));rng.shuffle(order)
        pos=[[math.cos(2*math.pi*order[v]/8),math.sin(2*math.pi*order[v]/8)]for v in range(8)]
        if attempt:
            for p in pos:p[0]+=rng.uniform(-.2,.2);p[1]+=rng.uniform(-.2,.2)
        for it in range(220):
            force=[[0.,0.]for _ in range(8)]
            for a in range(8):
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
            for v in range(8):
                d=math.hypot(*force[v])+.0001
                pos[v][0]+=force[v][0]*min(temp/d,.3);pos[v][1]+=force[v][1]*min(temp/d,.3)
        cx=sum(p[0]for p in pos)/8;cy=sum(p[1]for p in pos)/8
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
    colors={8:'#326b8e',9:'#307c72',10:'#765b9c',11:'#b06c34',12:'#9a4d64'}
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="3800" viewBox="0 0 1280 3800">',
        '<rect width="1280" height="3800" fill="#f7f7f3"/>',
        '<text x="30" y="42" font-family="Georgia,serif" font-size="27" fill="#182c35">The 60 eight-vertex cubic-support cores</text>',
        '<text x="30" y="67" font-family="Arial,sans-serif" font-size="13" fill="#56636a">Non-induced motifs · minimum degree 2 · exact graph labels match vol8_motifs.json</text>']
    for i,row in enumerate(data['motifs']):
        col=i%4;line=i//4;x=20+col*315;y=90+line*245;color=colors[row['edge_count']]
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
    out.append('<text x="30" y="3780" font-family="Arial,sans-serif" font-size="12" fill="#65727a">Each motif has leading kernel q²⁴ fᵉ = κ⁸ fᵉ⁻⁸; reduced laws also contain inherited-core terms.</text></svg>')
    return '\n'.join(out)+'\n'

if __name__=='__main__':
    data=catalogue()
    (HERE/'vol8_motifs.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    (HERE/'vol8_motifs.svg').write_text(svg(data))
    print('Wrote 60 exact motifs and SVG contact sheet')
