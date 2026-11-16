#!/usr/bin/env python3
"""Render explanatory AML figures; these illustrations are not observed cases."""
from pathlib import Path
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/aml-conceptual-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/aml-conceptual-cache")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
BG = "#FAF9F5"
INK = "#15232F"
BLUE = "#1F4F8A"
TEAL = "#38786F"
MUTED = "#56646F"
LIGHT = "#CFCABC"
RUST = "#A65F46"
plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":18,
                     "text.color":INK, "svg.fonttype":"none", "pdf.fonttype":42,
                     "savefig.facecolor":BG, "figure.facecolor":BG})


def canvas(height=4.3):
    fig, ax = plt.subplots(figsize=(13, height))
    fig.subplots_adjust(left=.012, right=.988, top=.975, bottom=.025)
    ax.set(xlim=(0,13), ylim=(0,height), aspect="equal")
    ax.axis("off")
    return fig, ax


def txt(ax,x,y,s,size=18,color=INK,weight="normal",ha="center",**kw):
    return ax.text(x,y,s,fontsize=size,color=color,fontweight=weight,ha=ha,va="center",**kw)


def edge(ax,a,b,color=MUTED,curve=0,lw=1.8,shrink=17):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=14,
                 connectionstyle=f"arc3,rad={curve}",color=color,lw=lw,
                 shrinkA=shrink,shrinkB=shrink,zorder=2))


def node(ax,x,y,s="",color=BLUE,r=.25):
    ax.add_patch(Circle((x,y),r,facecolor=BG,edgecolor=color,lw=1.8,zorder=3))
    if s: txt(ax,x,y,s,17,color,zorder=4)


def save(fig,name):
    OUT.mkdir(exist_ok=True,parents=True)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    for ax in fig.axes:
        for artist in ax.texts:
            bounds=artist.get_window_extent(renderer)
            if bounds.x0 < 0 or bounds.y0 < 0 or bounds.x1 > fig.bbox.width or bounds.y1 > fig.bbox.height:
                raise ValueError(f'Text outside {name}: {artist.get_text()}')
    for ext in ("png","svg","pdf"):
        fig.savefig(OUT/f"{name}.{ext}",dpi=300)
    plt.close(fig)


def aml_relationships():
    fig,ax=canvas()
    for x,label in [(2.12,"Fan-in"),(6.5,"Fan-out"),(10.88,"Cycle")]:
        txt(ax,x,3.86,label,22,weight="bold")
    for x in [4.28,8.72]: ax.plot([x,x],[.65,3.4],color=LIGHT,lw=1)
    for y in [2.95,2.05,1.15]:
        edge(ax,(.8,y),(3.2,2.05),BLUE)
        node(ax,.8,y)
    node(ax,3.2,2.05,"v",TEAL)
    txt(ax,2.12,.38,"Several senders → one receiver",16,MUTED)
    for y in [2.95,2.05,1.15]:
        edge(ax,(5.3,2.05),(7.7,y),BLUE)
        node(ax,7.7,y)
    node(ax,5.3,2.05,"u",TEAL)
    txt(ax,6.5,.38,"One sender → several receivers",16,MUTED)
    points=[(10.86,3.12),(12.05,1.4),(9.69,1.4)]
    for a,b in zip(points,points[1:]+points[:1]):edge(ax,a,b,BLUE)
    for x,y in points:node(ax,x,y)
    txt(ax,10.88,.38,"A sequence returns to its origin",16,MUTED)
    save(fig,"aml-relationships")


def gnn_ports():
    fig,ax=canvas()
    txt(ax,2.1,3.87,"Incoming messages",20,weight="bold")
    txt(ax,6.85,3.87,"Target representation",20,weight="bold")
    txt(ax,11.15,3.87,"Transfer score",20,weight="bold")
    points={"a":(.55,2.8),"b":(2,2.8),"u":(3.45,2.8),"c":(2,1.4),"v":(3.45,1.4)}
    for a,b in [("a","b"),("b","u"),("c","v")]:edge(ax,points[a],points[b],BLUE)
    edge(ax,points['u'],points['v'],RUST)
    for name,(x,y) in points.items():node(ax,x,y,name,color=RUST if name in ('u','v') else BLUE)
    txt(ax,2.1,.57,"Two GINE layers",18,MUTED)
    edge(ax,(4.15,2.15),(4.9,2.15),MUTED,shrink=0)
    rows=[(2.95,"Sender state",BLUE),(2.1,"Receiver state",BLUE),(1.25,"Target-edge features",TEAL)]
    for y,s,col in rows:
        ax.add_patch(Rectangle((5.1,y-.29),3.5,.58,facecolor=BG,edgecolor=LIGHT,lw=1.2))
        txt(ax,6.85,y,s,18,col)
    txt(ax,6.85,.43,"Inputs vary by experimental group",16,MUTED)
    edge(ax,(8.84,2.1),(9.55,2.1),MUTED,shrink=0)
    ax.add_patch(Rectangle((9.8,1.68),2.7,.84,facecolor=BG,edgecolor=BLUE,lw=1.5))
    txt(ax,11.15,2.1,"Edge classifier",19,BLUE)
    txt(ax,11.15,1.03,"Laundering score",18,TEAL)
    edge(ax,(11.15,1.65),(11.15,1.31),TEAL,shrink=0)
    save(fig,"gnn-ports")


def derivable_novelty():
    fig,ax=canvas()
    xs=[5.5,8.55,11.6]
    for i,(x,receiver) in enumerate(zip(xs,['A','B','A'])):
        txt(ax,x,4.0,f'Transfer {i+1}',17,MUTED)
        node(ax,x-.57,3.41,'S',r=.23)
        node(ax,x+.57,3.41,receiver,TEAL,r=.23)
        edge(ax,(x-.29,3.41),(x+.29,3.41),BLUE,shrink=0)
    ax.plot([.32,12.8],[2.96,2.96],color=LIGHT,lw=1.2)
    for y,name,vals,col in [(2.5,'Prior distinct recipients, d',['0','1','2'],INK),
                            (1.76,'Outgoing port, p',['0','1','0'],BLUE),
                            (1.02,'Explicit novelty, N',['1','1','0'],TEAL)]:
        txt(ax,.35,y,name,18,col,ha='left')
        for x,val in zip(xs,vals):txt(ax,x,y,val,21,col)
    ax.plot([.32,12.8],[.61,.61],color=LIGHT,lw=1.2)
    txt(ax,6.5,.23,r'New pair exactly when $p=d$:  $N=\mathbf{1}[p=d]$',20,TEAL)
    save(fig,'derivable-novelty')


def experimental_design():
    fig,ax=canvas()
    txt(ax,4.35,4.0,'Original primary experiment',20,weight='bold')
    txt(ax,10.58,4.0,'Supplementary comparison',20,weight='bold')
    x0,x1,x2=1.55,4.85,8.1
    for x,s in [(3.2,'Ports absent'),(6.48,'Ports present')]:txt(ax,x,3.47,s,17,MUTED)
    for y in [3.1,1.88,.65]:ax.plot([x0,x2],[y,y],color=LIGHT,lw=1.2)
    ax.plot([x1,x1],[.65,3.1],color=LIGHT,lw=1.2)
    for y,s in [(2.48,'Counts\nabsent'),(1.26,'Counts\npresent')]:txt(ax,.7,y,s,17,MUTED)
    for x,y,s,abbr,col in [(3.2,2.48,'Base','B',BLUE),(6.48,2.48,'Ports','P',BLUE),
                            (3.2,1.26,'Counts','C',BLUE),(6.48,1.26,'Counts + Ports','CP',BLUE)]:
        txt(ax,x,y+.13,s,19,col,weight='bold')
        txt(ax,x,y-.29,abbr,15,MUTED)
    ax.plot([8.7,8.7],[.56,3.47],color=LIGHT,lw=1.2)
    txt(ax,10.65,2.88,'Counts + novelty',20,TEAL,weight='bold')
    txt(ax,10.65,2.45,'CN',16,MUTED)
    txt(ax,10.65,1.75,'CP  ↔  CN',22,TEAL)
    txt(ax,10.65,.95,'Replace two port ranks\nwith one new-pair bit.',17,MUTED)
    txt(ax,4.35,.23,'The counts × ports design measures the port gain twice.',16,MUTED)
    save(fig,'experimental-design')


if __name__=='__main__':
    aml_relationships();gnn_ports();derivable_novelty();experimental_design()
    print('Rendered four conceptual figures as 300-dpi PNG, SVG, and PDF.')
