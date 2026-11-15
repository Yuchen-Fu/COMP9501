#!/usr/bin/env python3
"""Rebuild five AML slide plots directly from the audited numerical summary."""
from pathlib import Path
import argparse
import json
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/comp9501-slide-plot-cache")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/comp9501-slide-system-cache")
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
NAVY='#14273F'; TEAL='#007E87'; BLUE='#247BB4'; ORANGE='#C76225'; MUTED='#5E6D7D'; LIGHT='#E8EFF3'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':22,'axes.labelcolor':NAVY,'text.color':NAVY,
                     'xtick.color':MUTED,'ytick.color':NAVY,'axes.edgecolor':LIGHT,
                     'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,
                     'axes.spines.bottom':False,'svg.fonttype':'none','savefig.facecolor':'white'})


def save(fig,out,name):
    fig.savefig(out/f'{name}.png',dpi=160)
    fig.savefig(out/f'{name}.svg')
    plt.close(fig)


def clean(ax,axis='x'):
    ax.set_axisbelow(True);ax.grid(axis=axis,color=LIGHT,lw=1.2)
    ax.tick_params(length=0,pad=10)


def effect(ax,row,y,color,label=None):
    m=row['mean'];lo,hi=row['ci95']
    ax.errorbar(m,y,xerr=[[m-lo],[hi-m]],fmt='o',color=color,ms=11,lw=3.5,capsize=6)
    if label: ax.text(m,y+.23,label,ha='center',va='bottom',fontsize=22,color=color,fontweight='bold')


def factorial(s,out):
    a=s['selections']['best_validation']['subsets']['all']
    fig,(left,right)=plt.subplots(1,2,figsize=(18,5.625),gridspec_kw={'width_ratios':[1,1.12]})
    fig.subplots_adjust(left=.065,right=.98,bottom=.22,top=.84,wspace=.55)
    for cells,color,label,offset in [(('base','counts'),MUTED,'Ports absent',-.03),(('ports','counts+ports'),BLUE,'Ports present',.03)]:
        means=[a['cells'][c]['mean'] for c in cells]
        left.plot([0,1],means,color=color,lw=3.5,marker='o',ms=11,label=label)
        for x,c in enumerate(cells):
            ys=np.array(a['cells'][c]['per_seed'])
            left.scatter(x+np.linspace(-.08,.08,5)+offset,ys,s=48,color=color,alpha=.45,zorder=2)
            left.text(x+.18,means[x],f'{means[x]:.2f}',color=color,fontsize=23,va='center',fontweight='bold',bbox={'facecolor':'white','edgecolor':'none','pad':1},zorder=5)
    left.set_xlim(-.25,1.6);left.set_ylim(15,44)
    left.set_xticks([0,1],['Counts absent','Counts present']);left.set_yticks([20,30,40]);left.set_ylabel('Test F1 (%)',fontsize=23)
    left.set_title('Factorial comparison',loc='left',fontsize=27,pad=20,fontweight='bold')
    left.legend(loc='upper left',bbox_to_anchor=(-.03,1.07),frameon=False,ncol=2,fontsize=19,handlelength=1.5,columnspacing=1.0)
    clean(left,'y')
    rows=[a['effects']['port_gain'],a['effects']['ports_after_counts']]
    for y,row,color in zip([1,0],rows,[BLUE,ORANGE]):
        effect(right,row,y,color)
        right.text(.98,y+.21,f"+{row['mean']:.2f} [{row['ci95'][0]:.2f}, {row['ci95'][1]:.2f}]",transform=right.get_yaxis_transform(),ha='right',fontsize=22,color=color,fontweight='bold')
    right.set_xlim(0,22);right.set_ylim(-.5,1.55);right.set_xticks([0,5,10,15,20]);right.set_yticks([1,0],['Without counts\nP − B','After counts\nCP − C'],fontsize=22)
    right.set_xlabel('F1 improvement (percentage points)',fontsize=22)
    right.set_title('Port benefit remains',loc='left',fontsize=27,pad=20,fontweight='bold');clean(right)
    fig.text(.065,.035,'Left: five seed values and cell means.  Right: paired-seed means and 95% intervals.',fontsize=20,color=MUTED)
    save(fig,out,'factorial_gain')


def novelty(s,out):
    a=s['selections']['best_validation']['subsets']['all']
    cells=['counts','counts+ports','counts+novelty'];labels=['Counts','Counts + Ports','Counts + novelty'];colors=[MUTED,BLUE,TEAL]
    fig,(ax,detail)=plt.subplots(1,2,figsize=(18,5.625),gridspec_kw={'width_ratios':[1.6,1]})
    fig.subplots_adjust(left=.065,right=.97,bottom=.21,top=.88,wspace=.24)
    for x,c,color in zip(range(3),cells,colors):
        row=a['cells'][c];ys=row['per_seed']
        ax.bar(x,row['mean'],color=color,width=.58,alpha=.18)
        ax.plot([x-.3,x+.3],[row['mean']]*2,color=color,lw=5)
        ax.scatter(x+np.linspace(-.12,.12,5),ys,color=color,s=75,zorder=3)
        ax.text(x,max(ys)+3.0,f"{row['mean']:.2f}",ha='center',color=color,fontsize=29,fontweight='bold')
    ax.set_xticks(range(3),labels,fontsize=22);ax.set_ylim(0,60);ax.set_yticks([0,20,40,60]);ax.set_ylabel('Test F1 (%)',fontsize=23);clean(ax,'y')
    ax.set_title('Counts, ports, and explicit novelty',loc='left',fontsize=27,pad=18,fontweight='bold')
    detail.axis('off')
    e=a['effects']['ports_beyond_novelty'];mean=-e['mean'];lo,hi=-e['ci95'][1],-e['ci95'][0]
    detail.text(0,.85,'Novelty versus ports',fontsize=25,fontweight='bold',transform=detail.transAxes)
    detail.text(0,.57,f'+{mean:.2f}',fontsize=55,color=TEAL,fontweight='bold',transform=detail.transAxes)
    detail.text(0,.45,'F1 percentage points',fontsize=24,transform=detail.transAxes,va='top')
    detail.text(0,.28,f'95% paired interval\n[{lo:.2f}, {hi:.2f}]',fontsize=24,color=TEAL,transform=detail.transAxes,va='top')
    detail.text(0,.01,'Higher in all five seeds',fontsize=23,color=MUTED,transform=detail.transAxes)
    assert all(v<0 for v in e['per_seed'])
    fig.text(.065,.035,'Dots: individual seeds. Bars/lines: cell means. CN and CP use different representations.',fontsize=20,color=MUTED)
    save(fig,out,'novelty_comparison')


def outcomes(s,out):
    a=s['selections']['best_validation']['subsets']['all'];cells=['counts','counts+ports','counts+novelty']
    means={c:{k:np.mean([r[k] for r in a['cells'][c]['confusion_per_seed']]) for k in ('tp','fp','fn')} for c in cells}
    fig,(ax,miss)=plt.subplots(1,2,figsize=(18,5.625),gridspec_kw={'width_ratios':[1.9,1]})
    fig.subplots_adjust(left=.22,right=.97,bottom=.22,top=.79,wspace=.26)
    ys=np.array([2,1,0])
    for y,c in zip(ys,cells):
        m=means[c];total=m['tp']+m['fp']
        ax.barh(y,m['tp'],height=.54,color=TEAL)
        ax.barh(y,m['fp'],left=m['tp'],height=.54,color=ORANGE)
        ax.text(m['tp']/2,y,f"{m['tp']:,.1f}",ha='center',va='center',color='white',fontsize=22,fontweight='bold')
        ax.text(m['tp']+m['fp']/2,y,f"{m['fp']:,.1f}",ha='center',va='center',color='white',fontsize=22,fontweight='bold')
        ax.text(total+35,y,f'{total:,.1f}',ha='left',va='center',fontsize=22,color=NAVY,fontweight='bold')
        miss.barh(y,m['fn'],height=.54,color=MUTED,alpha=.75)
        miss.text(m['fn']+25,y,f"{m['fn']:,.1f}",ha='left',va='center',fontsize=22,color=NAVY,fontweight='bold')
    ax.set_yticks(ys,['Counts','Counts + Ports','Counts + novelty'],fontsize=22);miss.set_yticks([])
    ax.set_xlim(0,2440);ax.set_xticks([0,1000,2000]);ax.set_xlabel('Mean transaction flags',fontsize=23)
    miss.set_xlim(0,1520);miss.set_xticks([0,500,1000]);miss.set_xlabel('Mean missed positives',fontsize=23)
    for axis in (ax,miss):axis.set_ylim(-.65,2.65);clean(axis)
    ax.set_title('Transaction flags',loc='left',fontsize=26,pad=45,fontweight='bold')
    miss.set_title('Missed positives',loc='left',fontsize=25,pad=45,fontweight='bold')
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=TEAL,label='Labelled positives found'),Patch(color=ORANGE,label='False-positive flags')],loc='upper left',bbox_to_anchor=(.215,.895),frameon=False,ncol=2,fontsize=21,handlelength=1.1,columnspacing=1.2)
    fig.text(.065,.035,'Five-seed means. Each model uses its own validation-selected threshold.',fontsize=20,color=MUTED)
    for c,m in means.items():assert np.isclose(m['tp']+m['fn'],a['n_laundering'])
    save(fig,out,'alert_outcomes')


def robustness(s,out):
    primary=s['selections']['best_validation'];final=s['selections']['final']
    views=[primary['subsets']['all'],primary['subsets']['days_8_9'],final['subsets']['all']]
    labels=['Primary full test','Early test: days 8–9','Final epoch: full test']
    fig,(f1,ap)=plt.subplots(1,2,figsize=(18,5.625),gridspec_kw={'width_ratios':[1.45,1]})
    fig.subplots_adjust(left=.21,right=.97,bottom=.22,top=.76,wspace=.35)
    for j,(key,color) in enumerate([('ports_after_counts',ORANGE),('ports_beyond_novelty',TEAL)]):
        for i,v in enumerate(views):
            row=dict(v['effects'][key])
            if key=='ports_beyond_novelty':row['mean']=-row['mean'];row['ci95']=[-row['ci95'][1],-row['ci95'][0]]
            effect(f1,row,2-i+(.13 if j==0 else -.13),color)
        row=dict(final['metrics']['val_ap']['effects'][key])
        if key=='ports_beyond_novelty':row['mean']=-row['mean'];row['ci95']=[-row['ci95'][1],-row['ci95'][0]]
        y=1 if j==0 else 0
        effect(ap,row,y,color)
        ap.text(.99,y+.24,f"+{row['mean']:.2f} [{row['ci95'][0]:.2f}, {row['ci95'][1]:.2f}]",transform=ap.get_yaxis_transform(),ha='right',fontsize=20,color=color,fontweight='bold')
    f1.set_ylim(-.55,2.55);f1.set_xlim(0,23);f1.set_xticks([0,5,10,15,20]);f1.set_yticks([2,1,0],labels,fontsize=22);f1.set_xlabel('F1 difference (points)',fontsize=22);clean(f1)
    ap.set_ylim(-.5,1.5);ap.set_xlim(0,20);ap.set_xticks([0,5,10,15,20]);ap.set_yticks([]);ap.set_xlabel('AP difference (points)',fontsize=22);clean(ap)
    f1.set_title('Full and early-period F1',loc='left',fontsize=24,pad=20,fontweight='bold')
    ap.set_title('Final validation AP',loc='left',fontsize=24,pad=20,fontweight='bold')
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([0],[0],color=ORANGE,marker='o',lw=3,label='Ports after counts: CP − C'),Line2D([0],[0],color=TEAL,marker='o',lw=3,label='Novelty versus ports: CN − CP')],loc='upper center',bbox_to_anchor=(.58,.985),ncol=2,frameon=False,fontsize=23,handlelength=1.2,columnspacing=1.6)
    fig.text(.065,.035,'95% paired intervals. F1/AP differences are percentage points. Sensitivities reuse the same models and data.',fontsize=20,color=MUTED)
    save(fig,out,'robustness_effects')



def share_interval(s,out):
    row=s['selections']['best_validation']['subsets']['all']['share_explained']
    assert row['confidence_set_type']=='bounded'
    lo,hi=np.array(row['ci95_set'][0])*100;estimate=row['estimate']*100
    fig,ax=plt.subplots(figsize=(18,5.625))
    fig.subplots_adjust(left=.065,right=.96,bottom=.30,top=.83)
    ax.axvspan(lo,hi,color=TEAL,alpha=.10)
    ax.axvline(0,color=MUTED,lw=2,ls='--');ax.axvline(100,color=ORANGE,lw=2,ls='--')
    ax.errorbar(estimate,0,xerr=[[estimate-lo],[hi-estimate]],fmt='o',color=TEAL,ms=14,lw=5,capsize=14)
    ax.text(lo,.22,f'{lo:.2f}%',ha='left',fontsize=26,color=TEAL,fontweight='bold')
    ax.text(hi,.22,f'+{hi:.2f}%',ha='center',fontsize=26,color=TEAL,fontweight='bold')
    ax.text(estimate,-.28,f'Estimate: {estimate:.2f}%',ha='center',fontsize=27,color=NAVY,fontweight='bold')
    ax.text(-500,.75,'95% Fieller interval',ha='left',fontsize=25,color=TEAL,fontweight='bold')
    ax.text(-10,.75,'0%: no attenuation',ha='right',fontsize=25,color=MUTED)
    ax.text(100,.75,'100%: complete\nexplanation',ha='center',fontsize=24,color=ORANGE)
    ax.set_xlim(-560,190);ax.set_ylim(-.65,1);ax.set_yticks([]);ax.set_xticks([-500,-400,-300,-200,-100,0,100])
    ax.set_xlabel('Share of port gain explained by counts (%)',fontsize=24,labelpad=12);clean(ax)
    fig.text(.065,.04,'Zero is compatible; complete explanation is excluded. The magnitude of amplification is imprecise.',fontsize=22,color=MUTED)
    save(fig,out,'share_interval')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--summary',type=Path,default=ROOT/'results/summary.json');p.add_argument('--out',type=Path,default=ROOT/'presentation/figures');args=p.parse_args()
    s=json.loads(args.summary.read_text());assert s['supplementary_complete'] and sum(s['n_runs'].values())==25
    args.out.mkdir(parents=True,exist_ok=True)
    for f in (factorial,novelty,outcomes,robustness,share_interval):f(s,args.out)
    print('Created five PNG/SVG figure pairs from the complete audited summary.')

if __name__=='__main__':main()
