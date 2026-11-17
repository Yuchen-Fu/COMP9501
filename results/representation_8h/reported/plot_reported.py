"""Plot explicitly user-reported rounded results; no raw predictions are available here."""
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/aml-reported-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
d = json.loads((ROOT/'reported_summary.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
out=ROOT/'figures';out.mkdir(exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(9,3.9),layout='constrained')
for ax,metric,title in zip(axes,['f1','ap'],['Test F1','Test average precision']):
    values=d['primary'][f'per_seed_{metric}_points'];summary=d['primary'][metric]
    ax.scatter(values,np.arange(5),color='#294F76',s=30,zorder=3)
    mean=summary['mean'];lo,hi=summary['ci95']
    ax.errorbar(mean,6,xerr=[[mean-lo],[hi-mean]],fmt='D',color='#9F3D48',capsize=4,markersize=5)
    ax.axvline(0,color='.5',linewidth=1)
    ax.axhline(5,color='.8',linewidth=.7)
    ax.set(yticks=[0,1,2,3,4,6],yticklabels=[f'Seed {s}' for s in d['seeds']]+['Mean [95% CI]'],
           xlabel='B − A (percentage points)',title=title,ylim=(6.8,-.6))
    ax.grid(axis='x',alpha=.15)
for ext in ['png','pdf','svg']:fig.savefig(out/f'reported_paired_contrasts.{ext}',dpi=200)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(8,3.7),layout='constrained')
for ax,key,title in zip(axes,['mean_tp_rounded','mean_fp_rounded'],['Detected laundering transfers','False alerts']):
    values=[d['cells'][c][key] for c in ['cp','cpn']]
    bars=ax.bar([0,1],values,color=['#294F76','#9F3D48'],width=.55)
    ax.bar_label(bars,padding=4,fmt='%d')
    ax.set(xticks=[0,1],xticklabels=['A: Counts + Ports','B: A + novelty'],ylabel='Mean transfers per seed',
           title=title,ylim=(0,max(values)*1.2))
    ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
for ext in ['png','pdf','svg']:fig.savefig(out/f'reported_alert_tradeoff.{ext}',dpi=200)
plt.close(fig)
