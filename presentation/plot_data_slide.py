#!/usr/bin/env python3
"""Render daily HI-Small volume and prevalence from audited summary values."""
from pathlib import Path
import json
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/comp9501-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent
COLORS = {'train': '#243D57', 'validation': '#75818B',
          'early': '#267F78', 'tail': '#B57B5C'}
INK = '#263238'


def main():
    data = json.loads((ROOT.parent/'results/summary.json').read_text())
    daily = data['daily_distribution']
    days = np.array([r['day'] for r in daily])
    n = np.array([r['n_tx'] for r in daily])
    positives = np.array([r['n_laundering'] for r in daily])
    assert n.sum() == 5_078_345 and positives.sum() == 5_177
    tail = days >= 10
    assert n[tail].sum() == 1108 and positives[tail].sum() == 655
    colors = [COLORS['train'] if d < 6 else COLORS['validation'] if d < 8
              else COLORS['early'] if d < 10 else COLORS['tail'] for d in days]
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 17,
        'text.color': INK, 'axes.labelcolor': INK,
        'xtick.color': INK, 'ytick.color': INK,
        'axes.spines.top': False, 'axes.spines.right': False,
        'svg.fonttype': 'none', 'pdf.fonttype': 42,
        'figure.facecolor': 'white', 'axes.facecolor': 'white',
    })
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))
    fig.subplots_adjust(left=.10, right=.98, bottom=.19, top=.70, wspace=.34)
    for ax in axes:
        ax.set_xticks([0, 4, 8, 12, 17])
        ax.set_xlim(-.7, 17.7)
        ax.set_xlabel('Dataset day', fontsize=17, labelpad=7)
        ax.tick_params(labelsize=17, length=0, pad=6)
        for boundary in (5.5, 7.5, 9.5):
            ax.axvline(boundary, color='#ADB5BC', linewidth=.8, linestyle=':', zorder=0)
        ax.spines['left'].set_color('#ADB5BC')
        ax.spines['bottom'].set_color('#ADB5BC')
        ax.set_axisbelow(True)
        ax.grid(axis='y', color='#E6EAED', linewidth=.8)
    axes[0].bar(days, n, color=colors, width=.72, zorder=3)
    axes[0].set_yscale('log')
    axes[0].set_ylim(6, 2e6)
    axes[0].set_yticks([10, 1000, 100000, 1000000])
    axes[0].yaxis.set_major_formatter(LogFormatterMathtext())
    axes[0].set_ylabel('Transfers (log scale)', fontsize=17)
    axes[0].set_title('(a) Transfer volume', loc='left', fontsize=17, pad=15)
    prevalence = 100*positives/n
    axes[1].plot(days, prevalence, color='#75818B', linewidth=1.5, zorder=2)
    axes[1].scatter(days, prevalence, c=colors, s=35, zorder=3)
    axes[1].set_ylim(-3, 82)
    axes[1].set_yticks([0, 20, 40, 60, 80])
    axes[1].set_ylabel('Laundering labels (%)', fontsize=17)
    axes[1].set_title('(b) Label prevalence', loc='left', fontsize=17, pad=15)
    segments = [('Train: days 0–5', 'train'), ('Validation: days 6–7', 'validation'),
                ('Test: days 8–9', 'early'), ('Test tail: days 10–17', 'tail')]
    fig.legend(handles=[Patch(color=COLORS[key], label=label) for label, key in segments],
               loc='upper center', bbox_to_anchor=(.55, .985), ncol=2,
               frameon=False, fontsize=16, handlelength=1, columnspacing=2)
    out = ROOT/'figures'
    out.mkdir(exist_ok=True)
    for extension in ('png', 'svg', 'pdf'):
        fig.savefig(out/f'temporal_shift.{extension}', dpi=300, facecolor='white')
    plt.close(fig)
    print(json.dumps({'figure': 'temporal_shift', 'transactions': int(n.sum()),
                      'laundering': int(positives.sum()),
                      'tail_transactions': int(n[tail].sum()),
                      'tail_laundering': int(positives[tail].sum())}))


if __name__ == '__main__':
    main()
