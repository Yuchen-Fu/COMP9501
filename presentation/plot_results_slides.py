#!/usr/bin/env python3
"""Render academic presentation figures from the audited 25-run summary.

Figures contain only data, axes, and short legends. Numbered captions and
interpretive claims belong in the slide text. Each figure is exported as a
300-dpi PNG, an editable SVG, and a vector PDF. The wide canvases are
composed for a full-width slide figure, with interpretation beneath the plot.
"""
from pathlib import Path
import argparse
import json
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/comp9501-slide-plot-cache')
os.environ.setdefault('XDG_CACHE_HOME', '/tmp/comp9501-slide-system-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
NAVY = '#243D57'
TEAL = '#267F78'
CLAY = '#B57B5C'
MUTED = '#75818B'
INK = '#263238'
LIGHT = '#E6EAED'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 17,
    'text.color': INK, 'axes.labelcolor': INK,
    'xtick.color': INK, 'ytick.color': INK,
    'axes.edgecolor': '#ADB5BC', 'axes.linewidth': .8,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.spines.left': False, 'axes.spines.bottom': True,
    'axes.titleweight': 'normal', 'axes.titlesize': 17,
    'axes.labelsize': 18, 'xtick.labelsize': 17, 'ytick.labelsize': 17,
    'legend.fontsize': 16, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
})


def save(fig, out, name):
    for extension in ('png', 'svg', 'pdf'):
        fig.savefig(out / f'{name}.{extension}', dpi=300)
    plt.close(fig)


def clean(ax, axis='x'):
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=LIGHT, linewidth=.8)
    ax.tick_params(length=0, pad=8)


def effect(ax, row, y, color, marker='o'):
    mean = row['mean']
    lo, hi = row['ci95']
    ax.errorbar(mean, y, xerr=[[mean-lo], [hi-mean]], fmt=marker,
                color=color, markersize=7, linewidth=2, capsize=4,
                capthick=1.5, zorder=3)


def factorial(s, out):
    a = s['selections']['best_validation']['subsets']['all']
    fig, ax = plt.subplots(figsize=(13.5, 4.4))
    fig.subplots_adjust(left=.24, right=.97, top=.94, bottom=.19)
    rows = [('port_gain', 'Ports − Base', NAVY),
            ('ports_after_counts', 'Counts + Ports\nminus Counts', NAVY),
            ('interaction', 'Difference between\nport gains', MUTED)]
    for y, (key, label, color) in zip([2, 1, 0], rows):
        row = a['effects'][key]
        effect(ax, row, y, color)
        # Ordinary-size numeric labels keep the interval readable without
        # turning the result into a dashboard metric.
        ax.text(row['mean'], y+.24,
                f"{row['mean']:+.2f} [{row['ci95'][0]:.2f}, {row['ci95'][1]:.2f}]",
                ha='center', va='bottom', color=color, fontsize=16)
    ax.axvline(0, color=MUTED, linewidth=1, linestyle='--')
    ax.set(xlim=(-3, 22), ylim=(-.5, 2.7),
           yticks=[2, 1, 0], yticklabels=[r[1] for r in rows],
           xticks=[0, 5, 10, 15, 20], xlabel='Test F1 difference (percentage points)')
    clean(ax)
    save(fig, out, 'factorial_gain')


def novelty(s, out):
    a = s['selections']['best_validation']['subsets']['all']
    cells = ['counts', 'counts+ports', 'counts+novelty']
    labels = ['Counts', 'Counts +\nPorts', 'Counts +\nnovelty']
    colors = [MUTED, NAVY, TEAL]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    fig.subplots_adjust(left=.13, right=.97, bottom=.23, top=.94)
    values = np.array([a['cells'][c]['per_seed'] for c in cells])
    for seed in range(5):
        ax.plot(range(3), values[:, seed], color='#ADB7BF', linewidth=1.2,
                marker='o', markersize=4.5, alpha=.8, zorder=2)
    for x, c, color in zip(range(3), cells, colors):
        mean = a['cells'][c]['mean']
        ax.scatter(x, mean, color=color, s=95, marker='D', edgecolor='white',
                   linewidth=1, zorder=4)
        ax.text(x+.08, mean+1.4, f'{mean:.2f}', color=color, fontsize=16,
                bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5, 'alpha': .94})
    ax.set(xlim=(-.2, 2.35), ylim=(10, 58),
           xticks=range(3), xticklabels=labels,
           yticks=[10, 20, 30, 40, 50], ylabel='Test F1 (%)')
    handles = [Line2D([0], [0], color='#ADB7BF', marker='o', markersize=4,
                      linewidth=1, label='Individual seed'),
               Line2D([0], [0], color=NAVY, marker='D', markersize=7,
                      linestyle='none', label='Five-seed mean')]
    ax.legend(handles=handles, loc='lower right', frameon=False, ncol=1)
    clean(ax, 'y')
    assert all(v < 0 for v in a['effects']['ports_beyond_novelty']['per_seed'])
    save(fig, out, 'novelty_comparison')


def outcomes(s, out):
    a = s['selections']['best_validation']['subsets']['all']
    cells = ['counts', 'counts+ports', 'counts+novelty']
    means = {c: {k: np.mean([r[k] for r in a['cells'][c]['confusion_per_seed']])
                 for k in ('tp', 'fp', 'fn')} for c in cells}
    fig, (flags, missed) = plt.subplots(1, 2, figsize=(13.5, 4.4),
                                      gridspec_kw={'width_ratios': [2.0, 1]})
    fig.subplots_adjust(left=.18, right=.99, bottom=.19, top=.83, wspace=.20)
    for y, c in zip([2, 1, 0], cells):
        m = means[c]
        flags.barh(y, m['tp'], height=.46, color=TEAL)
        flags.barh(y, m['fp'], left=m['tp'], height=.46, color=CLAY)
        for start, value in [(0, m['tp']), (m['tp'], m['fp'])]:
            flags.text(start+value/2, y, f'{value:,.1f}', ha='center', va='center',
                       color='white', fontsize=16)
        missed.barh(y, m['fn'], height=.46, color=MUTED)
        missed.text(m['fn']/2, y, f"{m['fn']:,.1f}", ha='center', va='center', color='white', fontsize=16)
        assert np.isclose(m['tp']+m['fn'], a['n_laundering'])
    flags.set(yticks=[2, 1, 0], yticklabels=['Counts', 'Counts + Ports', 'Counts + novelty'],
              xlim=(0, 2200), xticks=[0, 1000, 2000], xlabel='Flagged transactions')
    missed.set(yticks=[], xlim=(0, 1550), xticks=[0, 500, 1000], xlabel='Missed positives')
    for ax in (flags, missed):
        ax.set_ylim(-.55, 2.55)
        clean(ax)
    fig.legend(handles=[Patch(color=TEAL, label='True-positive flags'),
                        Patch(color=CLAY, label='False-positive flags'),
                        Patch(color=MUTED, label='Missed positives')],
               loc='upper center', bbox_to_anchor=(.56, 1.00), ncol=3,
               frameon=False, handlelength=1.1, columnspacing=1.1)
    save(fig, out, 'alert_outcomes')


def robustness(s, out):
    primary = s['selections']['best_validation']
    final = s['selections']['final']
    views = [primary['subsets']['all'], primary['subsets']['days_8_9'],
             final['subsets']['all']]
    fig, (f1, ap) = plt.subplots(1, 2, figsize=(13.5, 4.4),
                                gridspec_kw={'width_ratios': [1.45, 1]})
    fig.subplots_adjust(left=.18, right=.98, bottom=.19, top=.77, wspace=.24)
    for j, (key, color, marker) in enumerate([
            ('ports_after_counts', NAVY, 'o'), ('ports_beyond_novelty', TEAL, 's')]):
        def oriented(row):
            if key != 'ports_beyond_novelty':
                return row
            return {'mean': -row['mean'], 'ci95': [-row['ci95'][1], -row['ci95'][0]]}
        for i, view in enumerate(views):
            effect(f1, oriented(view['effects'][key]), 2-i+(.14 if j == 0 else -.14),
                   color, marker)
        effect(ap, oriented(final['metrics']['val_ap']['effects'][key]),
               1 if j == 0 else 0, color, marker)
    f1.set(xlim=(0, 23), ylim=(-.5, 2.5), xticks=[0, 5, 10, 15, 20],
           yticks=[2, 1, 0], yticklabels=['Full test', 'Test days 8–9', 'Final-epoch test'],
           xlabel='F1 difference (points)')
    ap.set(xlim=(0, 20), ylim=(-.5, 1.5), xticks=[0, 5, 10, 15, 20],
           yticks=[], xlabel='AP difference (points)')
    f1.set_title('(a) Test F1', loc='left', pad=15)
    ap.set_title('(b) Validation AP', loc='left', pad=15)
    for ax in (f1, ap):
        clean(ax)
    fig.legend(handles=[Line2D([0], [0], color=NAVY, marker='o', linewidth=2,
                               label='Ports after counts (CP − C)'),
                        Line2D([0], [0], color=TEAL, marker='s', linewidth=2,
                               label='Novelty versus ports (CN − CP)')],
               loc='upper center', bbox_to_anchor=(.57, 1.015), ncol=2,
               frameon=False, handlelength=1.4)
    save(fig, out, 'robustness_effects')


def share_interval(s, out):
    row = s['selections']['best_validation']['subsets']['all']['share_explained']
    assert row['confidence_set_type'] == 'bounded'
    lo, hi = np.array(row['ci95_set'][0])*100
    estimate = row['estimate']*100
    fig, ax = plt.subplots(figsize=(13.5, 4.4))
    fig.subplots_adjust(left=.055, right=.97, bottom=.21, top=.94)
    ax.axvline(0, color=MUTED, linewidth=1.2, linestyle='--')
    ax.axvline(100, color=CLAY, linewidth=1.2, linestyle='--')
    ax.errorbar(estimate, 0, xerr=[[estimate-lo], [hi-estimate]], fmt='o',
                color=TEAL, markersize=8, linewidth=2.5, capsize=7)
    ax.text(lo, .14, f'{lo:.2f}%', ha='left', fontsize=17, color=TEAL)
    ax.text(hi, .14, f'{hi:+.2f}%', ha='left', fontsize=17, color=TEAL)
    ax.text(estimate, -.22, f'Estimate: {estimate:.2f}%', ha='center', fontsize=17)
    ax.text(-15, .62, 'No attenuation', ha='right', fontsize=17, color=MUTED)
    ax.text(105, .62, 'Complete\nexplanation', ha='left', fontsize=17, color=CLAY)
    ax.set(xlim=(-550, 230), ylim=(-.55, .9), yticks=[],
           xticks=[-500, -400, -300, -200, -100, 0, 100],
           xlabel='Share of port gain explained by counts (%)')
    clean(ax)
    save(fig, out, 'share_interval')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--summary', type=Path, default=ROOT/'results/summary.json')
    p.add_argument('--out', type=Path, default=ROOT/'presentation/figures')
    args = p.parse_args()
    s = json.loads(args.summary.read_text())
    assert s['supplementary_complete'] and sum(s['n_runs'].values()) == 25
    args.out.mkdir(parents=True, exist_ok=True)
    for f in (factorial, novelty, outcomes, robustness, share_interval):
        f(s, args.out)
    print('Created five 300-dpi PNG/SVG/PDF figures from the audited summary.')


if __name__ == '__main__':
    main()
