#!/usr/bin/env python3
"""Draw the exact graph inputs; layout is illustrative, edges are source-bound."""
from pathlib import Path
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from singularity.examples import GRAPHS

root=Path(__file__).resolve().parents[1]
figure,axes=plt.subplots(2,2,figsize=(10,8.1))
names=['spectral_g','spectral_h','binary_g','binary_h']
for axis,name in zip(axes.flat,names):
    graph=GRAPHS[name]
    positions={i:(math.cos(2*math.pi*i/graph.n+math.pi/2),math.sin(2*math.pi*i/graph.n+math.pi/2)) for i in range(graph.n)}
    for i,j in graph.edges:
        axis.plot([positions[i][0],positions[j][0]],[positions[i][1],positions[j][1]],color='#537481',linewidth=2,zorder=1)
    for i,(x,y) in positions.items():
        color='#b38a43' if graph.degrees[i]==4 else '#234b62'
        axis.scatter([x],[y],s=440,c=color,zorder=2,edgecolors='white',linewidths=1.5)
        axis.text(x,y,str(i),ha='center',va='center',color='white',fontsize=11,fontweight='bold',zorder=3)
    axis.set_title(name.replace('_',' ').title(),fontsize=14,pad=12)
    axis.set_aspect('equal');axis.set_xlim(-1.3,1.3);axis.set_ylim(-1.3,1.3);axis.axis('off')
figure.suptitle('Exact graph populations: spectra, binary cuts, and nested heights',fontsize=15,y=.98)
figure.tight_layout(rect=(0,0,1,.96))
target=root/'docs'/'assets';target.mkdir(parents=True,exist_ok=True)
figure.savefig(target/'graph_pairs.png',dpi=220,facecolor='white')
figure.savefig(target/'graph_pairs.svg',facecolor='white')
svg=target/'graph_pairs.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
print(target/'graph_pairs.png')
