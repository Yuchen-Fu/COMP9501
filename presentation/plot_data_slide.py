#!/usr/bin/env python3
"""Plot audited daily transaction volume and laundering prevalence for a slide."""
from pathlib import Path
import json
import os

os.environ.setdefault('MPLCONFIGDIR', '/tmp/comp9501-matplotlib')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogFormatterMathtext

ROOT=Path(__file__).resolve().parent
COLORS={'train':'#247BB4','validation':'#007E87','early':'#C76225','tail':'#8061A8'}
NAVY='#14273F'
MUTED='#5E6D7D'


def main():
    data=json.loads((ROOT.parent/'results/summary.json').read_text())
    daily=data['daily_distribution']
    days=np.array([r['day'] for r in daily])
    n=np.array([r['n_tx'] for r in daily])
    p=np.array([r['n_laundering'] for r in daily])
    assert n.sum()==5_078_345 and p.sum()==5_177
    tail=days>=10
    assert n[tail].sum()==1108 and p[tail].sum()==655
    colors=[COLORS['train'] if d<6 else COLORS['validation'] if d<8 else
            COLORS['early'] if d<10 else COLORS['tail'] for d in days]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':18,
                         'text.color':NAVY,'axes.labelcolor':NAVY,
                         'xtick.color':MUTED,'ytick.color':MUTED,
                         'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(16,5.16),gridspec_kw={'width_ratios':[1.06,1]},facecolor='#F7F9FB')
    fig.subplots_adjust(left=.068,right=.985,bottom=.19,top=.72,wspace=.23)
    for ax in axes:
        ax.set_facecolor('#F7F9FB')
        ax.set_xticks([0,4,8,12,17])
        ax.set_xlim(-.7,17.7)
        ax.tick_params(labelsize=16)
        ax.set_xlabel('Dataset day',fontsize=18,labelpad=7)
        for boundary in (5.5,7.5,9.5):ax.axvline(boundary,color='#B9C5CF',lw=1,ls=':',zorder=0)
        ax.spines['left'].set_color('#B9C5CF');ax.spines['bottom'].set_color('#B9C5CF')
    axes[0].bar(days,n,color=colors,width=.76,zorder=3)
    axes[0].set_yscale('log');axes[0].set_ylim(6,2e6)
    axes[0].set_yticks([10,1000,100000,1000000])
    axes[0].yaxis.set_major_formatter(LogFormatterMathtext())
    axes[0].set_ylabel('Daily transfers · log scale',fontsize=18)
    axes[0].set_title('Volume falls sharply after day 9',loc='left',fontsize=20,fontweight='bold',pad=14)
    axes[0].grid(axis='y',alpha=.17,zorder=0)
    prevalence=100*p/n
    axes[1].plot(days,prevalence,color=NAVY,lw=2,zorder=2)
    axes[1].scatter(days,prevalence,c=colors,s=48,zorder=3)
    axes[1].set_ylim(-3,82);axes[1].set_yticks([0,20,40,60,80])
    axes[1].set_ylabel('Laundering prevalence (%)',fontsize=18)
    axes[1].set_title('Prevalence rises sharply',loc='left',fontsize=20,fontweight='bold',pad=14)
    axes[1].grid(axis='y',alpha=.17,zorder=0)
    axes[1].annotate('Days 8–9: 0.111%',xy=(8.5,.111),xytext=(1,18),
                     fontsize=16,color=COLORS['early'],arrowprops={'arrowstyle':'-','color':COLORS['early'],'lw':1.4})
    axes[1].text(10.1,30,'Days 10–17\n1,108 transfers\n655 positives',fontsize=16,
                 color=COLORS['tail'],bbox={'boxstyle':'round,pad=.35','facecolor':'white','edgecolor':'#D8DFE5'})
    segments=[('Train 0–5','train'),('Validation 6–7','validation'),
              ('Test 8–9','early'),('Test tail 10–17','tail')]
    handles=[plt.Line2D([0],[0],marker='s',color='none',markerfacecolor=COLORS[k],markersize=10,label=label) for label,k in segments]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.52,.99),ncol=4,frameon=False,fontsize=17,handletextpad=.4,columnspacing=1.0)
    out=ROOT/'figures';out.mkdir(exist_ok=True)
    for extension in ('png','svg'):fig.savefig(out/f'temporal_shift.{extension}',dpi=180,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(json.dumps({'figure':'temporal_shift','transactions':int(n.sum()),'laundering':int(p.sum()),
                      'tail_transactions':int(n[tail].sum()),'tail_laundering':int(p[tail].sum())}))


if __name__=='__main__':main()
