#!/usr/bin/env python3
"""Draw the report figures from results/summary.json (needs numpy and matplotlib).

Usage: python3 src/plot_results.py
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(tempfile.gettempdir()) / 'comp9501-matplotlib'
os.environ.setdefault('MPLCONFIGDIR', str(CONFIG))
os.environ.setdefault('XDG_CACHE_HOME', str(Path(tempfile.gettempdir()) / 'comp9501-font-cache'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

BLUE, ORANGE, GREEN, PURPLE, GREY = '#0072B2', '#D55E00', '#009E73', '#CC79A7', '#666666'
CELLS = ('base', 'counts', 'ports', 'counts+ports', 'counts+novelty')


def completed_summary(path):
    summary = json.loads(path.read_text())
    core = {summary['n_runs'].get(cell) for cell in CELLS[:4]}
    if len(core) != 1 or None in core or not summary['supplementary_complete']:
        raise SystemExit('Figures require a summary of all planned runs.')
    return summary


def style():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.titlesize': 12, 'axes.labelsize': 10,
                         'xtick.labelsize': 9, 'ytick.labelsize': 9,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.axisbelow': True, 'svg.fonttype': 'none',
                         'savefig.facecolor': 'white'})


def export(fig, directory, name):
    directory.mkdir(parents=True, exist_ok=True)
    for suffix in ('svg', 'png'):
        path = directory / f'{name}.{suffix}'
        fig.savefig(path, dpi=200, bbox_inches='tight', pad_inches=0.18)
        print(path)
    plt.close(fig)


def errors(item):
    lo, hi = item['ci95']
    return np.array([[item['mean'] - lo], [hi - item['mean']]])


def factorial(summary, directory):
    full = summary['selections']['best_validation']['subsets']['all']
    fig, (interaction, forest) = plt.subplots(1, 2, figsize=(13.5, 5.8), gridspec_kw={'width_ratios': [1.05, 1]})
    fig.subplots_adjust(left=0.075, right=0.98, top=0.82, bottom=0.22, wspace=0.77)
    fig.suptitle('Counts and ports in the completed factorial experiment', fontsize=16, x=0.5, y=0.97)
    interaction.set_title('Primary 2×2 factorial', loc='left', pad=13)
    for names, color, marker, offset, label in ((('base', 'counts'), GREY, 'o', -0.025, 'Ports absent'),
                                               (('ports', 'counts+ports'), BLUE, 's', 0.025, 'Ports present')):
        x = np.array([0., 1.]) + offset
        items = [full['cells'][name] for name in names]
        means = [item['mean'] for item in items]
        ci = np.array([[item['mean'] - item['ci95'][0] for item in items],
                       [item['ci95'][1] - item['mean'] for item in items]])
        interaction.errorbar(x, means, yerr=ci, color=color, marker=marker, ms=7,
                             markeredgecolor='white', capsize=5, lw=1.8, label=label, zorder=4)
        for center, item in zip(x, items):
            interaction.scatter(center + np.linspace(-0.075, 0.075, len(item['per_seed'])), item['per_seed'],
                                color=color, marker=marker, s=28, alpha=0.6, linewidths=0, zorder=3)
    interaction.set_xticks([0, 1], ['Absent', 'Present'])
    interaction.set_xlim(-0.24, 1.24)
    interaction.set_xlabel('Historical count features')
    interaction.set_ylabel('Test F1 (%)')
    interaction.grid(axis='y', color='#dddddd', lw=0.6)
    handles, labels = interaction.get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc='upper left', bbox_to_anchor=(0.075, 0.915), ncol=2, fontsize=9)
    forest.set_title('Paired factorial contrasts', loc='left', pad=13)
    names = [('port_gain', 'Port gain: P − B', BLUE),
             ('ports_after_counts', 'Ports after counts: CP − C', ORANGE),
             ('interaction', 'Interaction: (CP − C) − (P − B)', PURPLE),
             ('count_gain', 'Count gain: C − B', GREEN)]
    labels = []
    for y, (key, label, color) in zip(range(3, -1, -1), names):
        item = full['effects'][key]
        forest.errorbar(item['mean'], y, xerr=errors(item), fmt='o', color=color, capsize=5, ms=6, lw=1.6)
        lo, hi = item['ci95']
        labels.append(f"{label}\n{item['mean']:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    forest.set_yticks(range(3, -1, -1), labels)
    forest.set_ylim(-0.65, 3.65)
    forest.axvline(0, color='#555555', lw=1, ls='--')
    forest.set_xlabel('F1 difference (percentage points)')
    forest.grid(axis='x', color='#dddddd', lw=0.6)
    fig.text(0.075, 0.105, 'B = Base; C = Counts; P = Ports; CP = Counts+Ports. Primary: full test at each run’s validation-selected epoch.', fontsize=9)
    fig.text(0.075, 0.057, f"Each cell has {summary['n_runs']['base']} seeds. Left: cell means with 95% t intervals and individual seeds. Right: paired-seed 95% t intervals.", fontsize=9)
    fig.text(0.075, 0.014, 'Intervals condition on this dataset and protocol; secondary comparisons are exploratory and unadjusted. No causal decomposition is implied.', fontsize=8.5)
    export(fig, directory, 'factorial_effects')


def paired_panel(ax, rows, xlabel):
    ax.axvline(0, color='#555555', lw=1, ls='--')
    y_positions = np.arange(len(rows) - 1, -1, -1)
    for y, (_, effects) in zip(y_positions, rows):
        for key, color, offset, marker in (('port_gain', BLUE, 0.12, 'o'),
                                          ('ports_after_counts', ORANGE, -0.12, 's')):
            item = effects[key]
            ax.errorbar(item['mean'], y + offset, xerr=errors(item), color=color,
                        fmt=marker, capsize=4, ms=5.5, lw=1.5)
    ax.set_yticks(y_positions, [label for label, _ in rows])
    ax.set_ylim(-0.5, len(rows) - 0.5)
    ax.set_xlabel(xlabel)
    ax.grid(axis='x', color='#dddddd', lw=0.6)


def sensitivities(summary, directory):
    selections = summary['selections']
    f1_rows, ap_rows = [], []
    for selection, name in (('best_validation', 'Validation-selected'), ('final', 'Final epoch')):
        for subset, label in (('all', 'full test'), ('days_8_9', 'test days 8–9')):
            f1_rows.append((f'{name}\n{label}', selections[selection]['subsets'][subset]['effects']))
        for metric, label in (('val_ap', 'validation'), ('test_ap', 'full test')):
            ap_rows.append((f'{name}\n{label}', selections[selection]['metrics'][metric]['effects']))
    fig, (f1, ap) = plt.subplots(1, 2, figsize=(13.5, 6.3))
    fig.subplots_adjust(left=0.13, right=0.98, top=0.76, bottom=0.20, wspace=0.62)
    fig.suptitle('Sensitivity of the incremental port contrasts', fontsize=16, y=0.98)
    handles = [Line2D([0], [0], color=BLUE, marker='o', label='Port gain: Ports − Base'),
               Line2D([0], [0], color=ORANGE, marker='s', label='Ports after counts: Counts+Ports − Counts')]
    fig.legend(handles=handles, frameon=False, loc='upper center', bbox_to_anchor=(0.53, 0.925), ncol=2, fontsize=10)
    f1.set_title('Thresholded F1', loc='left', pad=13)
    ap.set_title('Average precision (AP)', loc='left', pad=13)
    paired_panel(f1, f1_rows, 'F1 difference (percentage points)')
    paired_panel(ap, ap_rows, 'AP difference (percentage points)')
    fig.text(0.075, 0.105, f"Each point is a mean paired contrast across {summary['n_runs']['base']} seeds; bars are 95% t intervals conditional on this dataset and protocol.", fontsize=9)
    fig.text(0.075, 0.061, 'F1 and AP are different outcomes and use separate axes. Full-test validation-selected F1 is primary; added sensitivities are post hoc.', fontsize=9)
    fig.text(0.075, 0.018, 'Secondary comparisons are exploratory and unadjusted. Agreement in direction does not establish significance or independent replication.', fontsize=8.5)
    export(fig, directory, 'sensitivity_effects')


def temporal(summary, directory):
    rows = summary['daily_distribution']
    days = np.array([row['day'] for row in rows])
    count = np.array([row['n_tx'] for row in rows])
    positive = np.array([row['n_laundering'] for row in rows])
    prevalence = 100 * positive / count
    colors = [BLUE if d < 6 else GREEN if d < 8 else '#E69F00' if d < 10 else ORANGE for d in days]
    tail, test = days >= 10, days >= 8
    nt, pt = int(count[tail].sum()), int(positive[tail].sum())
    fig, (volume, rate) = plt.subplots(2, 1, figsize=(12.5, 7.5), sharex=True, gridspec_kw={'height_ratios': [1.15, 1]})
    fig.subplots_adjust(left=0.09, right=0.98, top=0.83, bottom=0.17, hspace=0.2)
    fig.suptitle('The test period has a small, high-prevalence temporal tail', fontsize=16, y=0.98)
    fig.text(0.5, 0.925, f"HI-Small: {count.sum():,} transactions; {positive.sum():,} laundering transactions", ha='center', fontsize=11)
    volume.bar(days, count, color=colors, width=0.8)
    volume.set_yscale('log')
    volume.set_ylabel('Transactions per day\n(log scale)')
    volume.grid(axis='y', color='#dddddd', lw=0.6, which='major')
    text = (f"Days 10–{int(days.max())}: {nt:,} transactions; {pt:,} laundering\n"
            f"{100 * pt / nt:.2f}% prevalence\n"
            f"{100 * nt / count[test].sum():.3f}% of test volume; {100 * pt / positive[test].sum():.1f}% of test laundering")
    volume.text(0.98, 0.97, text, transform=volume.transAxes, va='top', ha='right', fontsize=10,
                bbox={'boxstyle': 'round,pad=0.45', 'facecolor': 'white', 'edgecolor': '#bbbbbb', 'alpha': 0.96})
    rate.plot(days, prevalence, color='#555555', lw=1.3, zorder=2)
    rate.scatter(days, prevalence, c=colors, s=42, edgecolor='white', linewidth=0.6, zorder=3)
    rate.set_ylabel('Laundering prevalence (%)')
    rate.set_ylim(-2, 102)
    rate.set_yticks([0, 25, 50, 75, 100])
    head = (days >= 8) & (days < 10)
    rate.text(0.025, 0.17, f"Test days 8–9 prevalence: {100 * positive[head].sum() / count[head].sum():.3f}%",
              transform=rate.transAxes, fontsize=10, color='#444444')
    rate.set_xlabel('Dataset day (day 0 = first transaction)')
    rate.set_xticks(days)
    rate.grid(axis='y', color='#dddddd', lw=0.6)
    for ax in (volume, rate):
        ax.set_xlim(-0.6, int(days.max()) + 0.6)
        for boundary in (5.5, 7.5, 9.5):
            ax.axvline(boundary, color='#999999', lw=0.8, ls=':')
    fig.legend(handles=[Patch(color=BLUE, label='Train: days 0–5'), Patch(color=GREEN, label='Validation: days 6–7'),
                        Patch(color='#E69F00', label='Test: days 8–9'), Patch(color=ORANGE, label='Test tail: days 10–17')],
               loc='lower center', bbox_to_anchor=(0.53, 0.07), ncol=4, frameon=False, fontsize=9)
    fig.text(0.09, 0.025, 'Daily counts come directly from the verified graph via summary.json. The tail was identified post hoc; the full test period remains primary.', fontsize=8.7)
    export(fig, directory, 'temporal_distribution')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, default=ROOT / 'results/summary.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'results/figures')
    args = parser.parse_args()
    summary = completed_summary(args.summary)
    style()
    output = args.out
    factorial(summary, output)
    sensitivities(summary, output)
    temporal(summary, output)


if __name__ == '__main__':
    main()
