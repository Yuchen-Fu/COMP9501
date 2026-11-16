#!/usr/bin/env python3
"""Render the supplementary pair-novelty comparison from saved study results.

No training, checkpoint selection, or statistical estimation is performed here.
The uncertainty intervals are read from the completed study's summary. The
learning curves show all saved checkpoints as a descriptive, post-hoc view.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/aml-representation-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME', '/tmp/aml-representation-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BG = '#FAF9F5'
INK = '#15232F'
BLUE = '#1F4F8A'
TEAL = '#38786F'
MUTED = '#56646F'
GRID = '#CFCABC'
RUST = '#A65F46'
CP = 'counts+ports'
CN = 'counts+novelty'


def configure():
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 13,
        'axes.titlesize': 14, 'axes.labelsize': 13,
        'xtick.labelsize': 12, 'ytick.labelsize': 12,
        'text.color': INK, 'axes.labelcolor': INK,
        'xtick.color': MUTED, 'ytick.color': MUTED,
        'axes.edgecolor': GRID, 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.facecolor': BG,
        'figure.facecolor': BG, 'savefig.facecolor': BG,
        'svg.fonttype': 'none', 'pdf.fonttype': 42,
    })


def save(fig, out, name):
    for ext in ('png', 'svg', 'pdf'):
        fig.savefig(out / f'{name}.{ext}', dpi=300)
    plt.close(fig)


def positive_novelty_effect(record):
    """The saved contrast is CP−CN; invert its sign and interval endpoints."""
    e = record['effects']['ports_beyond_novelty']
    return -e['mean'], -e['ci95'][1], -e['ci95'][0]


def representation_comparison(summary, out):
    record = summary['selections']['best_validation']['subsets']['all']
    a = np.asarray(record['cells'][CP]['per_seed'])
    b = np.asarray(record['cells'][CN]['per_seed'])
    mean, lo, hi = positive_novelty_effect(record)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3),
                             gridspec_kw={'width_ratios': [1, 1.12]})
    left, right = axes
    for av, bv in zip(a, b):
        left.plot([0, 1], [av, bv], color=GRID, lw=1.4, zorder=1)
    left.scatter(np.zeros(5), a, color=BLUE, s=42, zorder=3)
    left.scatter(np.ones(5), b, color=TEAL, s=42, zorder=3)
    for x, values, color in [(0, a, BLUE), (1, b, TEAL)]:
        avg = values.mean()
        left.plot([x-.16, x+.16], [avg, avg], color=color, lw=3.5)
        left.text(x, 54.4, f'Mean {avg:.2f}', ha='center', color=color, fontsize=13)
    left.set(xlim=(-.4, 1.4), ylim=(35, 56), xticks=[0, 1],
             xticklabels=['Counts + Ports', 'Counts + novelty'],
             yticks=[35, 40, 45, 50, 55], ylabel='Minority-class F1 (%)',
             title='(a) Paired test scores')
    left.grid(axis='y', color=GRID, alpha=.45, zorder=0)
    right.axvline(0, color=GRID, lw=1)
    right.scatter(b-a, np.arange(5, 0, -1), color=TEAL, s=38, zorder=3)
    right.errorbar(mean, 0, xerr=[[mean-lo], [hi-mean]], fmt='D',
                   color=TEAL, lw=2.2, markersize=7, capsize=5)
    right.text(mean, -.55, f'{mean:+.2f} [{lo:.2f}, {hi:.2f}]',
               ha='center', color=TEAL, fontsize=12)
    right.set(xlim=(-.4, 16), ylim=(-1, 5.8),
              yticks=[5, 4, 3, 2, 1, 0],
              yticklabels=['Seed 0', 'Seed 1', 'Seed 2', 'Seed 3', 'Seed 4', 'Mean and 95% CI'],
              xticks=[0, 4, 8, 12, 16], xlabel='Novelty − Ports, with counts (F1 points)',
              title='(b) Improvement in every paired seed')
    right.grid(axis='x', color=GRID, alpha=.45)
    right.spines['left'].set_visible(False)
    right.tick_params(axis='y', length=0)
    fig.subplots_adjust(left=.075, right=.975, top=.87, bottom=.2, wspace=.55)
    save(fig, out, 'representation-comparison')


def learning_trajectories(repo, out):
    data = {cell: [json.loads((repo/'results'/'runs'/f'{cell}_s{s}.json').read_text())['log']
                   for s in range(5)] for cell in (CP, CN)}
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3))
    x = np.arange(1, 6)
    for ax, metric, title, ylabel in zip(
        axes, ('val_ap', 'test_f1'),
        ('(a) Validation average precision', '(b) Test F1 at each checkpoint'),
        ('Average precision (%)', 'Minority-class F1 (%)')):
        for cell, color, label in ((CP, BLUE, 'Counts + Ports'), (CN, TEAL, 'Counts + novelty')):
            y = np.asarray([[e[metric]*100 for e in run] for run in data[cell]])
            for seed_values in y:
                ax.plot(x, seed_values, color=color, alpha=.17, lw=1)
            ax.plot(x, y.mean(0), color=color, lw=2.5, marker='o', ms=5, label=label)
        ax.set(xticks=x, xlim=(.8, 5.2), xlabel='Completed training epochs',
               ylabel=ylabel, title=title)
        ax.grid(axis='y', color=GRID, alpha=.4)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=2, frameon=False,
               bbox_to_anchor=(.5, 1.0), fontsize=13)
    fig.subplots_adjust(left=.075, right=.975, top=.77, bottom=.18, wspace=.25)
    save(fig, out, 'learning-trajectories')


def first_contact_errors(summary, out):
    record = summary['selections']['best_validation']['subsets']['first_contact']
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3))
    for ax, key, title in zip(axes, ('tp', 'fp'),
                              ('(a) Labelled first contacts detected', '(b) False flags on first contacts')):
        all_values = []
        for x, cell, color in ((0, CP, BLUE), (1, CN, TEAL)):
            values = np.asarray([d[key] for d in record['cells'][cell]['confusion_per_seed']])
            all_values.extend(values.tolist())
            avg = values.mean()
            ax.bar(x, avg, width=.48, color=color, alpha=.82, zorder=2)
            ax.scatter(x+np.linspace(.31, .41, 5), values, s=26,
                       facecolor=BG, edgecolor=color, linewidth=.9, zorder=4)
            ax.text(x, avg+max(values)*.035, f'{avg:,.1f}', ha='center',
                     va='bottom', fontsize=13, color=INK, zorder=5)
        ax.set(xticks=[0, 1], xticklabels=['Counts + Ports', 'Counts + novelty'],
               ylabel='Transfers', ylim=(0, max(all_values)*1.16),
               title=title, xlim=(-.65, 1.75))
        ax.grid(axis='y', color=GRID, alpha=.4, zorder=0)
        ax.set_axisbelow(True)
    fig.subplots_adjust(left=.075, right=.975, top=.86, bottom=.19, wspace=.26)
    save(fig, out, 'first-contact-errors')


def novelty_robustness(summary, out):
    best = summary['selections']['best_validation']
    final = summary['selections']['final']
    records = [best['subsets']['all'], best['subsets']['days_8_9'], final['subsets']['all']]
    labels = ['Full test, selected epoch', 'Test days 8–9, selected epoch', 'Full test, final epoch']
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3),
                             gridspec_kw={'width_ratios': [1.65, 1]})
    left, right = axes
    for y, record in zip([2, 1, 0], records):
        mean, lo, hi = positive_novelty_effect(record)
        left.errorbar(mean, y, xerr=[[mean-lo], [hi-mean]], fmt='o',
                      color=TEAL, lw=2.1, ms=6, capsize=4)
        left.text(17.3, y, f'{mean:+.2f}', ha='right', va='center', fontsize=12)
    left.set(yticks=[2, 1, 0], yticklabels=labels, ylim=(-.65, 2.65),
             xlim=(-.3, 18), xticks=[0, 5, 10, 15],
             xlabel='Novelty − Ports, with counts (F1 points)',
             title='(a) F1 sensitivities')
    mean, lo, hi = positive_novelty_effect(best['metrics']['test_ap'])
    right.errorbar(mean, 0, xerr=[[mean-lo], [hi-mean]], fmt='o',
                   color=TEAL, lw=2.1, ms=6, capsize=4)
    right.text(mean, -.37, f'{mean:+.2f} [{lo:.2f}, {hi:.2f}]',
               ha='center', va='top', color=TEAL, fontsize=12)
    right.set(ylim=(-1, 1), yticks=[], xlim=(-.3, 20), xticks=[0, 5, 10, 15, 20],
              xlabel='AP difference (points)', title='(b) Average precision')
    right.text(.5, .86, 'Validation-selected checkpoint', transform=right.transAxes,
               ha='center', fontsize=11, color=MUTED)
    for ax in axes:
        ax.axvline(0, color=GRID, lw=1)
        ax.grid(axis='x', color=GRID, alpha=.4)
        ax.spines['left'].set_visible(False)
        ax.tick_params(axis='y', length=0)
    fig.subplots_adjust(left=.225, right=.975, top=.85, bottom=.2, wspace=.23)
    save(fig, out, 'novelty-robustness')


def factorial_result(summary, out):
    record = summary['selections']['best_validation']['subsets']['all']
    cells = ['base', 'ports', 'counts', CP]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3),
                             gridspec_kw={'width_ratios': [1.1, 1]})
    left, right = axes
    for x, cell in enumerate(cells):
        r = record['cells'][cell]
        values = np.asarray(r['per_seed'])
        color = BLUE if cell in ('ports', CP) else MUTED
        left.scatter(x+np.linspace(-.09, .09, 5), values, color=color, s=30,
                     alpha=.7, zorder=3)
        left.plot([x-.19, x+.19], [r['mean'], r['mean']], color=color, lw=3)
        left.text(x, values.max()+2.2, f'{r["mean"]:.2f}', ha='center',
                  fontsize=12, color=color)
    left.set(xticks=range(4), xticklabels=['Base', 'Ports', 'Counts', 'Counts\n+ Ports'],
             xlim=(-.45, 3.45), ylim=(0, 48), yticks=[0, 10, 20, 30, 40],
             ylabel='Minority-class F1 (%)', title='(a) The original four-cell factorial')
    left.grid(axis='y', color=GRID, alpha=.4)
    for y, key in [(1, 'port_gain'), (0, 'ports_after_counts')]:
        e = record['effects'][key]
        mean, (lo, hi) = e['mean'], e['ci95']
        right.errorbar(mean, y, xerr=[[mean-lo], [hi-mean]], color=BLUE,
                       fmt='o', ms=6, lw=2.1, capsize=4)
        right.text(mean, y-.22, f'{mean:+.2f} [{lo:.2f}, {hi:.2f}]',
                   ha='center', color=BLUE, fontsize=12)
    right.axvline(0, color=GRID, lw=1)
    right.set(yticks=[1, 0], yticklabels=['Without counts\nPorts − Base',
                                        'With counts\nCP − Counts'],
              xlim=(-.4, 23), ylim=(-.65, 1.65), xticks=[0, 5, 10, 15, 20],
              xlabel='Port benefit (F1 points)', title='(b) Paired gains and 95% intervals')
    right.spines['left'].set_visible(False)
    right.tick_params(axis='y', length=0)
    right.grid(axis='x', color=GRID, alpha=.4)
    fig.subplots_adjust(left=.075, right=.975, top=.86, bottom=.21, wspace=.48)
    save(fig, out, 'factorial-result')


def explained_share(summary, out):
    r = summary['selections']['best_validation']['subsets']['all']['share_explained']
    estimate = r['estimate']*100
    lo, hi = np.asarray(r['ci95_set'][0])*100
    fig, ax = plt.subplots(figsize=(13, 4.3))
    ax.axvline(0, color=MUTED, lw=1.2, ls='--', alpha=.8)
    ax.axvline(100, color=RUST, lw=1.2, ls='--', alpha=.8)
    ax.errorbar(estimate, .48, xerr=[[estimate-lo], [hi-estimate]], color=TEAL,
                fmt='o', ms=7, lw=2.2, capsize=6)
    ax.text(lo, .59, f'{lo:.2f}%', color=TEAL, ha='left', fontsize=13)
    ax.text(hi, .59, f'{hi:+.2f}%', color=TEAL, ha='left', fontsize=13)
    ax.text(estimate, .32, f'Estimate: {estimate:.2f}%', color=INK,
            ha='center', fontsize=13)
    ax.text(-7, .87, 'No attenuation', ha='right', color=MUTED, fontsize=13)
    ax.text(105, .87, 'Complete\nexplanation', ha='left', color=RUST,
            fontsize=13, va='top')
    ax.set(ylim=(0, 1), yticks=[], xlim=(-550, 190),
           xticks=[-500, -400, -300, -200, -100, 0, 100],
           xlabel='Share of the port gain explained by counts (%)')
    ax.spines['left'].set_visible(False)
    ax.grid(axis='x', color=GRID, alpha=.4)
    fig.subplots_adjust(left=.065, right=.975, top=.92, bottom=.2)
    save(fig, out, 'explained-share')


def full_strata(summary, out):
    subsets = summary['selections']['best_validation']['subsets']
    fig, ax = plt.subplots(figsize=(13, 4.3))
    names = ['first_contact', 'repeat', 'repeat_free_accounts']
    labels = ['First-contact transfers', 'Repeat transfers', 'Repeat-free accounts']
    for y, subset in zip([2, 1, 0], names):
        record = subsets[subset]
        e = record['effects']['ports_after_counts']
        for offset, (mean, lo, hi), color, marker, label in [
            (.13, (e['mean'], *e['ci95']), BLUE, 'o', 'Ports after counts (CP − C)'),
            (-.13, positive_novelty_effect(record), TEAL, 's', 'Novelty versus ports (CN − CP)')]:
            ax.errorbar(mean, y+offset, xerr=[[mean-lo], [hi-mean]],
                        fmt=marker, color=color, ms=6, lw=1.9, capsize=4,
                        label=label if y==2 else None)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set(yticks=[2, 1, 0], yticklabels=labels, ylim=(-.55, 2.55),
           xlim=(-16, 22), xticks=[-15, -10, -5, 0, 5, 10, 15, 20],
           xlabel='Difference in minority-class F1 (points)')
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, alpha=.4)
    fig.legend(*ax.get_legend_handles_labels(), loc='upper center', ncol=2,
               frameon=False, bbox_to_anchor=(.59, .99), fontsize=13)
    fig.subplots_adjust(left=.235, right=.975, top=.8, bottom=.2)
    save(fig, out, 'full-strata')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--out', type=Path, default=Path(__file__).parent/'figures')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summary = json.loads((args.repo/'results'/'summary.json').read_text())
    configure()
    representation_comparison(summary, args.out)
    learning_trajectories(args.repo, args.out)
    first_contact_errors(summary, args.out)
    novelty_robustness(summary, args.out)
    factorial_result(summary, args.out)
    explained_share(summary, args.out)
    full_strata(summary, args.out)
    print(json.dumps({'output': str(args.out), 'figures': 7, 'formats': ['png', 'svg', 'pdf']}))


if __name__ == '__main__':
    main()
