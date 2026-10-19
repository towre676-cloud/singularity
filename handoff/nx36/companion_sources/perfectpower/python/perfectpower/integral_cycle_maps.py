"""Integral H1 maps from declared simplicial maps of oriented closed surfaces.

Vertices determine an actual simplicial map, including collapsed simplices.
Smith reductions construct integral homology bases and boundary witnesses.
They do not identify these meshes with an algebraic quotient's cycle marking.
"""
from itertools import combinations
from .integer_lifting import smith_certificate, _solve_with_certificate
from . import exact_linear as E
from .symplectic_surface import surface_basis


def transpose(a):return [list(row) for row in zip(*a)]
def multiply(a,b):return [list(row) for row in E.multiply(a,b)]
def integral_inverse(a):
    inverse=E.inverse(a)
    if any(v.denominator!=1 for row in inverse for v in row):raise AssertionError('nonunimodular Smith basis')
    return [[int(v) for v in row] for row in inverse]


def complex_data(mesh):
    if not isinstance(mesh,dict) or not {'vertices','triangles','face_orientation_signs'}<=set(mesh):raise ValueError('oriented closed triangulation required')
    if type(mesh['vertices']) is not int or not 4<=mesh['vertices']<=128 or not 4<=len(mesh['triangles'])<=256:raise ValueError('surface budget: at most 128 vertices and 256 triangles')
    topology=surface_basis(mesh)
    triangles=[tuple(t) if sign==1 else (t[0],t[2],t[1]) for t,sign in zip(mesh['triangles'],mesh['face_orientation_signs'])]
    edges=sorted({tuple(sorted(e)) for t in triangles for e in combinations(t,2)});edge_index={e:i for i,e in enumerate(edges)}
    d1=[[0]*len(edges) for _ in range(mesh['vertices'])];d2=[[0]*len(triangles) for _ in edges]
    for k,(u,v) in enumerate(edges):d1[u][k]=-1;d1[v][k]=1
    for k,t in enumerate(triangles):
        for i in range(3):
            u,v=t[i],t[(i+1)%3];d2[edge_index[tuple(sorted((u,v)))]][k]=1 if u<v else -1
    if any(v for row in multiply(d1,d2) for v in row):raise AssertionError('surface boundary does not square to zero')
    cert1=smith_certificate(d1,operation_limit=1000000);rank1=cert1['rank'];kernel=[row[rank1:] for row in cert1['right']]
    inverse1=integral_inverse(cert1['right']);boundary_coordinates=multiply(inverse1,d2)[rank1:]
    cert2=smith_certificate(boundary_coordinates,operation_limit=1000000);rank2=cert2['rank'];torsion=cert2['smith_factors']
    if any(v!=1 for v in torsion):raise ValueError('surface homology unexpectedly has torsion')
    inv2=integral_inverse(cert2['left']);free=[row[rank2:] for row in inv2];basis=multiply(kernel,free)
    projection=multiply(cert2['left'],inverse1[rank1:])[rank2:]
    if len(projection)!=2*topology['genus']:raise AssertionError('homology rank disagrees with surface topology')
    cert_top=smith_certificate(d2,operation_limit=1000000);cycles2=[row[cert_top['rank']:] for row in cert_top['right']]
    if len(cycles2[0])!=1:raise ValueError('connected closed surface needs rank-one H2')
    fundamental=[row[0] for row in cycles2]
    if fundamental[0]<0:fundamental=[-v for v in fundamental]
    if fundamental!=[1]*len(triangles):raise AssertionError('oriented fundamental class is not primitive')
    return dict(vertices=mesh['vertices'],triangles=triangles,edges=edges,edge_index=edge_index,d1=d1,d2=d2,
        basis=basis,projection=projection,genus=topology['genus'],fundamental=fundamental,
        smith_certificates=[cert1,cert2,cert_top])


def simplicial_cycle_map(source,target,vertex_map):
    s,t=complex_data(source),complex_data(target)
    if not isinstance(vertex_map,list) or len(vertex_map)!=s['vertices'] or any(type(v) is not int or not 0<=v<t['vertices'] for v in vertex_map):raise ValueError('one target vertex per source vertex required')
    c0=[[int(vertex_map[j]==i) for j in range(s['vertices'])] for i in range(t['vertices'])]
    c1=[[0]*len(s['edges']) for _ in t['edges']]
    for j,(u,v) in enumerate(s['edges']):
        a,b=vertex_map[u],vertex_map[v]
        if a==b:continue
        edge=tuple(sorted((a,b)))
        if edge not in t['edge_index']:raise ValueError('vertex map sends an edge outside the target complex')
        c1[t['edge_index'][edge]][j]=1 if a<b else -1
    face_index={tuple(sorted(face)):i for i,face in enumerate(t['triangles'])}
    c2=[[0]*len(s['triangles']) for _ in t['triangles']]
    for j,face in enumerate(s['triangles']):
        image=tuple(vertex_map[v] for v in face)
        if len(set(image))<3:continue
        if tuple(sorted(image)) not in face_index:raise ValueError('vertex map sends a face outside the target complex')
        k=face_index[tuple(sorted(image))];ordered=t['triangles'][k];permutation=[ordered.index(v) for v in image]
        c2[k][j]=(-1)**sum(permutation[a]>permutation[b] for a in range(3) for b in range(a+1,3))
    if multiply(t['d1'],c1)!=multiply(c0,s['d1']) or multiply(t['d2'],c2)!=multiply(c1,s['d2']):raise AssertionError('simplicial chain map failed')
    image_top=list(E.apply(c2,s['fundamental']));pivot=next(i for i,v in enumerate(t['fundamental']) if v)
    degree=image_top[pivot]//t['fundamental'][pivot]
    if image_top!=[degree*v for v in t['fundamental']]:raise AssertionError('top homology map not integral')
    images=multiply(c1,s['basis']) if s['genus'] else [[] for _ in t['edges']]
    homology_map=multiply(t['projection'],images) if s['genus'] and t['genus'] else [[] for _ in range(2*t['genus'])]
    boundaries=[]
    if s['genus']:
        reconstructed=multiply(t['basis'],homology_map) if t['genus'] else [[0]*(2*s['genus']) for _ in t['edges']]
        boundary_certificate=t['smith_certificates'][2]
        for k in range(2*s['genus']):
            difference=[images[i][k]-reconstructed[i][k] for i in range(len(t['edges']))]
            witness=_solve_with_certificate(boundary_certificate,difference)
            if witness['status']!='INTEGER_AFFINE_FIBRE':raise AssertionError('homology image differs by a nonboundary')
            boundaries.append(witness['particular'])
    return dict(schema='pp-integral-simplicial-cycle-map/1',source_genus=s['genus'],target_genus=t['genus'],degree=degree,
        source_cycle_basis=s['basis'],target_cycle_basis=t['basis'],homology_matrix=homology_map,
        chain_maps=dict(vertices=c0,edges=c1,faces=c2),boundary_witnesses=boundaries,
        chain_identities_checked=True,homology_boundary_identities_checked=True,
        source_smith_certificates=s['smith_certificates'],target_smith_certificates=t['smith_certificates'],
        execution_verified=False,algebraic_cycle_identification=False,
        scope='exact induced integral H1 map of this declared simplicial surface map; no automatic identification with an algebraic quotient or period marking, and the returned Smith homology basis is not claimed symplectic')
