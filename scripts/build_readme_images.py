#!/usr/bin/env python3
"""Build three exact, self-contained SVG figures for the README.

Standard library only. --preview additionally uses Pillow to render the same
SVG primitives to PNG for review. Inputs/claims: docs/assets/readme-figures.json.
"""
from fractions import Fraction as F
from math import cos, sin, pi
from pathlib import Path
from xml.sax.saxutils import escape
import argparse
import json

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'docs/assets'
BG='#0a1120'; PANEL='#101c2d'; LINE='#294157'; WHITE='#f1f6fc'
MUTED='#9db3cb'; TEAL='#79e3d1'; PURPLE='#c2a5f5'; AMBER='#f2c17e'

class Figure:
    def __init__(self,name,h,title,desc):
        self.name=name;self.h=h
        self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{h}" viewBox="0 0 1200 {h}" role="img" aria-labelledby="title desc">',f'<title id="title">{escape(title)}</title>',f'<desc id="desc">{escape(desc)}</desc>']
        self.rect(0,0,1200,h,BG,rx=20)
    def rect(self,x,y,w,h,fill,stroke='none',rx=0,sw=1):
        self.parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def line(self,a,b,fill=LINE,sw=2):
        self.parts.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke="{fill}" stroke-width="{sw}" stroke-linecap="round"/>')
    def circle(self,x,y,r,fill,stroke='none',sw=1):
        self.parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def poly(self,pts,fill,stroke='none',sw=1):
        self.parts.append(f'<polygon points="'+ ' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+f'" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def text(self,x,y,s,size=18,color=MUTED,bold=False,anchor='middle',mono=False):
        face='DejaVu Sans Mono' if mono else 'DejaVu Sans'
        self.parts.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{face},sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}">{escape(str(s))}</text>')
    def header(self,k,title,subtitle):
        self.text(600,43,k,13,TEAL,mono=True)
        self.text(600,88,title,32,WHITE,True)
        self.text(600,123,subtitle,17,MUTED)
    def node(self,p,color=TEAL,label=None):
        x,y=p;self.circle(x,y,15,PANEL,color,2);self.circle(x,y,5,color)
        if label is not None:self.text(x,y+36,label,15,MUTED,mono=True)
    def save(self,preview=False):
        p=ASSETS/(self.name+'.svg');p.write_text('\n'.join(self.parts+['</svg>'])+'\n')
        if preview: render(p,ROOT/'previews'/(self.name+'.png'))


def heights(preview):
    f=Figure('height-profile',790,'A height profile becomes an exact coefficient','Illustrated five-cycle with heights 0, 1, 3, 2, 0. Volume six, squared-edge energy ten, and three nested threshold sets.')
    f.header('01 / THE OBSERVATION LANGUAGE','A network becomes a coefficient.','One labeled height profile on a five-cycle.')
    f.rect(45,161,600,435,PANEL,LINE,16);f.rect(673,161,482,435,PANEL,LINE,16)
    p=[(340+214*cos(-pi/2+i*2*pi/5),405+100*sin(-pi/2+i*2*pi/5)) for i in range(5)]
    hs=[0,1,3,2,0];edges=[(i,(i+1)%5) for i in range(5)]
    volume=sum(hs);contributions=[(hs[u]-hs[v])**2 for u,v in edges]
    assert volume==6 and sum(contributions)==10
    # Floor and vertical guides retain all five original vertex positions.
    f.poly(p,'#132638',LINE)
    for u,v in edges:f.line(p[u],p[v],'#365168',2)
    tops=[(x,y-58*h) for (x,y),h in zip(p,hs)]
    for i in sorted(range(5),key=lambda i:p[i][1]):
        x,y=p[i];z=58*hs[i];w=31;d=12
        if z:
            f.poly([(x-w/2,y),(x+w/2,y),(x+w/2,y-z),(x-w/2,y-z)],'#226e78')
            f.poly([(x+w/2,y),(x+w/2+d,y-d),(x+w/2+d,y-z-d),(x+w/2,y-z)],'#174957')
            f.poly([(x-w/2,y-z),(x+w/2,y-z),(x+w/2+d,y-z-d),(x-w/2+d,y-z-d)],'#86e4d0')
        f.circle(x,y,5,'#507387')
    for u,v in edges:f.line(tops[u],tops[v],TEAL,3)
    for i,((x,y),h) in enumerate(zip(tops,hs)):
        f.circle(x,y,6,WHITE)
        f.text(x,y-20,f'h = {h}',17,WHITE,True)
        f.text(p[i][0],p[i][1]+29,f'v{i}',14,MUTED,mono=True)
    f.text(345,564,'HEIGHTS  0 + 1 + 3 + 2 + 0',17,MUTED,mono=True)
    for level,y,col in [(1,247,TEAL),(2,381,PURPLE),(3,515,AMBER)]:
        f.text(715,y-29,f'HEIGHT ≥ {level}',15,col,True,'start',True)
        q=[(959+100*cos(-pi/2+i*2*pi/5),y+44*sin(-pi/2+i*2*pi/5)) for i in range(5)]
        for u,v in edges:f.line(q[u],q[v],'#35485d',2)
        for i,(x,yy) in enumerate(q):f.circle(x,yy,10,col if hs[i]>=level else '#24354a',col if hs[i]>=level else '#40566e',1)
        f.text(715,y+5,f'{sum(h>=level for h in hs)} active',16,MUTED,False,'start')
    f.line((75,627),(1125,627))
    f.text(282,674,'TOTAL HEIGHT',14,MUTED,mono=True);f.text(282,722,'6',40,TEAL,True)
    f.text(600,674,'SQUARED-EDGE ENERGY',14,MUTED,mono=True);f.text(600,722,'1 + 4 + 1 + 4 + 0 = 10',20,WHITE,True)
    f.text(951,674,'SERIES CONTRIBUTION',14,MUTED,mono=True);f.text(951,722,'x⁶q¹⁰',40,AMBER,True)
    f.text(600,766,'One profile is shown; the coefficient counts every original labeled profile with these totals.',14,MUTED)
    f.save(preview)


def intervention(preview,data):
    f=Figure('chosen-experiment',820,'One chosen experiment reveals the difference','Two terminal choices on the same path have volume-one reading 5/4. A shared-neighbor attachment changes the readings to 1 and 9/8 at q=1/2, giving the cheapest distinguishing experiment at cost one.')
    f.header('02 / CHOOSE WHAT TO OBSERVE','One chosen experiment reveals the difference.','The same path, with two different choices of accessible terminals.')
    for x,title,col in [(45,'ENDPOINT TERMINALS',TEAL),(625,'ADJACENT TERMINALS',PURPLE)]:
        f.rect(x,160,530,536,PANEL,LINE,16);f.text(x+265,199,title,16,col,True,mono=True)
        pts=[(x+110,258),(x+265,258),(x+420,258)]
        for u,v in [(0,1),(1,2)]:f.line(pts[u],pts[v],'#7690a8',3)
        terminal={0,2} if x==45 else {0,1}
        for i,p in enumerate(pts):f.node(p,col if i in terminal else '#7290aa',i)
        f.text(x+265,337,'PASSIVE READOUT  5/4',21,WHITE,True)
    f.rect(332,365,536,49,'#253041','#5b4b38',11)
    f.text(600,396,'ADD ONE SHARED NEIGHBOR · COST 1',18,AMBER,True)
    graphs=[([(155,542),(310,618),(465,542),(310,456)],[(0,1),(1,2)],[(0,3),(2,3)],{0,2},TEAL),
            ([(735,571),(890,571),(1045,571),(812,461)],[(0,1),(1,2)],[(0,3),(1,3)],{0,1},PURPLE)]
    for idx,(pts,old,new,terms,col) in enumerate(graphs):
        degrees=[sum(i in edge for edge in old+new) for i in range(4)]
        assert sum(F(1,2)**d for d in degrees)==F(data['readings']['endpoints' if idx==0 else 'adjacent'])
        for u,v in old:f.line(pts[u],pts[v],'#7690a8',3)
        for u,v in new:f.line(pts[u],pts[v],AMBER,3)
        for i,p in enumerate(pts):f.node(p,AMBER if i==3 else col if i in terms else '#7290aa')
        f.text(310 if idx==0 else 890,667,'AFTER: 1' if idx==0 else 'AFTER: 9/8',25,col,True)
    assert F(data['readings']['adjacent'])-F(data['readings']['endpoints'])==F(1,8)
    f.text(600,744,'EXACT GAP  1/8',35,AMBER,True)
    f.text(600,783,'q = 1/2 · volume-one coefficients · cheapest in the declared attachment language',15,MUTED)
    f.save(preview)


def thermal_field(blocked):
    n=12;k=F(1,8);loss=F(1,100);x=[F(0)]*(n*n)
    for _ in range(8):
        y=[]
        for r in range(n):
            for c in range(n):
                i=r*n+c
                val=(1-loss)*x[i]+(F(1,2) if r in (5,6) and c in (5,6) else 0)
                for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    j=rr*n+cc
                    if 0<=rr<n and 0<=cc<n and tuple(sorted((i,j)))!=blocked:
                        val+=k*(x[j]-x[i])
                y.append(val)
        x=y
    return x


def mix(a,b,t):
    aa=[int(a[i:i+2],16) for i in (1,3,5)];bb=[int(b[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{round(v+(w-v)*t):02x}' for v,w in zip(aa,bb))
def heatcolor(t):
    stops=['#122135','#20566b','#399b9f','#91d7bf','#f7d39a']
    v=max(0,min(1,t))*4;i=min(3,int(v));return mix(stops[i],stops[i+1],v-i)


def thermal(preview,data):
    left=thermal_field((64,65));right=thermal_field((66,67));nominal=thermal_field(None)
    nominal_read=(nominal[65]+nominal[77])/2
    reads=[(left[65]+left[77])/2,(right[65]+right[77])/2]
    assert nominal_read==F(data['nominal_reading'])
    assert reads==[F(data['blocked_left_reading']),F(data['blocked_right_reading'])]
    assert sum(nominal)==2*(1-F(99,100)**8)/F(1,100)
    vmax=max(map(float,left+right));cell=24
    f=Figure('thermal-diagnosis',890,'A simulated diagnostic separates reflected faults','Exact 12 by 12 source-model heat fields after eight heater inputs of amplitude two. A localized left sensor distinguishes blocked-left from blocked-right bonds. Optimal robust diagnostic cost20, greedy31, fixed44; normalized synthetic-model units.')
    f.header('03 / FROM STRUCTURE TO DIAGNOSIS','Break the symmetry. Identify the fault.','12 × 12 source-model simulation · eight heater inputs of amplitude 2')
    for x,field,title,reading,bond in [(150,left,'BLOCKED LEFT',reads[0],(64,65)),(762,right,'BLOCKED RIGHT',reads[1],(66,67))]:
        f.text(x+144,182,title,18,WHITE,True,mono=True)
        for r in range(12):
            for c in range(12):f.rect(x+c*cell,210+r*cell,cell-1,cell-1,heatcolor(float(field[r*12+c])/vmax),rx=2)
        # The same left-center sensor is used on both physical fault models.
        f.rect(x+5*cell-2,210+5*cell-2,cell+3,2*cell+3,'none',TEAL,4,3)
        a,b=bond;rr=a//12;ca=a%12;cb=b%12
        mid=x+(ca+cb+1)*cell/2;yy=210+(rr+.5)*cell
        f.line((x+(ca+.5)*cell,yy),(x+(cb+.5)*cell,yy),'#ff857c',4)
        f.line((mid-5,yy-7),(mid+5,yy+7),'#ffd1bb',2)
        f.line((mid-5,yy+7),(mid+5,yy-7),'#ffd1bb',2)
        f.text(x+144,539,f'LEFT SENSOR  {float(reading):.5f}',20,TEAL,True)
    # Common temperature scale; zero stays dark, no normalization per panel.
    for i in range(100):f.rect(590,498-(i+1)*2.88,20,3.0,heatcolor(i/99))
    f.text(600,193,f'{vmax:.2f}',14,MUTED,mono=True);f.text(600,524,'0',14,MUTED,mono=True)
    f.text(600,568,'Teal outline: fixed left sensor · coral mark: removed bond',15,MUTED)
    f.text(600,591,'Simulated excess temperature · normalized model units',14,MUTED)
    f.line((75,613),(1125,613))
    for x,value,label,col in [(80,data['optimal_cost'],'OPTIMAL ROBUST',TEAL),(450,data['greedy_cost'],'GREEDY',MUTED),(820,data['fixed_cost'],'FIXED PROTOCOL',MUTED)]:
        f.rect(x,628,300,156,'#13283a' if col==TEAL else PANEL,LINE,14)
        f.text(x+150,665,label,16,col,True,mono=True)
        f.text(x+150,735,value,56,WHITE if col==TEAL else MUTED,True)
        f.text(x+150,766,'diagnostic cost units',14,MUTED)
    f.text(600,828,'The robust panel distinguishes all six supplied fault hypotheses.',20,WHITE,True)
    f.text(600,862,'Constructed model and fault hypotheses; these are simulated fields, not measured equipment data.',14,MUTED)
    f.save(preview)


def render(src,target):
    """Render our restricted SVG vocabulary through Pillow; optional QA only."""
    import xml.etree.ElementTree as ET
    from PIL import Image, ImageDraw, ImageFont
    tree=ET.parse(src).getroot();S=2;im=Image.new('RGB',(int(tree.attrib['width'])*S,int(tree.attrib['height'])*S),BG);d=ImageDraw.Draw(im)
    fonts=Path('/usr/share/fonts/truetype/dejavu')
    for e in tree:
        a=e.attrib;t=e.tag.split('}')[-1]
        def n(k,default=0):return float(a.get(k,default))*S
        def col(k):return a.get(k) if a.get(k)!='none' else None
        if t=='rect':
            x,y,w,h=map(n,('x','y','width','height'));d.rounded_rectangle((x,y,x+w,y+h),radius=n('rx'),fill=col('fill'),outline=col('stroke'),width=max(1,round(n('stroke-width',1))))
        elif t=='line':d.line((n('x1'),n('y1'),n('x2'),n('y2')),fill=col('stroke'),width=max(1,round(n('stroke-width',1))))
        elif t=='circle':
            x,y,r=map(n,('cx','cy','r'));d.ellipse((x-r,y-r,x+r,y+r),fill=col('fill'),outline=col('stroke'),width=max(1,round(n('stroke-width',1))))
        elif t=='polygon':d.polygon([tuple(float(v)*S for v in p.split(',')) for p in a['points'].split()],fill=col('fill'),outline=col('stroke'),width=max(1,round(n('stroke-width',1))))
        elif t=='text':
            face='DejaVuSans'+('Mono' if 'Mono' in a['font-family'] else '')+('-Bold' if int(a['font-weight'])>=600 else '')+'.ttf'
            font=ImageFont.truetype(str(fonts/face),round(n('font-size')))
            d.text((n('x'),n('y')),e.text or '',font=font,fill=col('fill'),anchor={'middle':'ms','start':'ls','end':'rs'}[a['text-anchor']])
    target.parent.mkdir(exist_ok=True);im.save(target)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preview',action='store_true');args=parser.parse_args()
    data=json.loads((ASSETS/'readme-figures.json').read_text())
    heights(args.preview);intervention(args.preview,data['experiment']);thermal(args.preview,data['thermal'])
    print('Three SVG figures generated; profile energy, intervention gap, and exact thermal readings verified.')
if __name__=='__main__':main()
