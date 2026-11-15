#!/usr/bin/env python3
"""Independently verify all 25 completed runs against the prepared graph and summary.

This reads saved artifacts only; it does not train models or scan the raw CSV.
Dependencies: NumPy, SciPy, scikit-learn, and PyTorch.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import math
import statistics

import numpy as np
from scipy import stats
from sklearn.metrics import f1_score
import torch

CELLS = ('base', 'counts', 'ports', 'counts+ports', 'counts+novelty')
PAIRS = {'count_gain': ('counts', 'base'), 'port_gain': ('ports', 'base'),
         'ports_after_counts': ('counts+ports', 'counts'),
         'novelty_gain': ('counts+novelty', 'counts'),
         'ports_beyond_novelty': ('counts+ports', 'counts+novelty')}
HP = dict(lr=0.006213266113989207, n_hidden=66, n_gnn_layers=2,
          w_ce=[1.0000182882773443, 6.275014431494497], final_dropout=0.10527690625126304,
          batch_size=8192, num_neighbors=[100, 100])
checks = 0
membership_checks = 0
boundary_points = 0


def check(actual, expected, atol=1e-9):
    global checks
    np.testing.assert_allclose(actual, expected, rtol=0, atol=atol)
    checks += 1


def numeric_summary(values):
    values = list(map(float, values))
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    half = float(stats.t.ppf(.975, 4)) * sd / math.sqrt(5)
    return {'mean': mean, 'sd': sd, 'ci95': [mean-half, mean+half], 'per_seed': values}


def verify_stats(values, reported):
    own = numeric_summary(values)
    for key in ('mean', 'sd', 'ci95', 'per_seed'):
        check(own[key], reported[key])
    return own


def confusion(y, p):
    # Separate denominator form from the production analyzer; sklearn also
    # checks every full-test epoch independently below.
    tp = int(np.sum(p[y])); positives = int(y.sum()); flagged = int(p.sum())
    return {'tp': tp, 'fp': flagged-tp, 'fn': positives-tp,
            'tn': len(y)-positives-flagged+tp,
            'f1': 200*tp/(positives+flagged) if positives+flagged else 0.0}


def set_contains(value, intervals):
    return any((lo is None or value >= lo) and (hi is None or value <= hi) for lo, hi in intervals)


def verify_fieller(numerator, denominator, reported):
    global membership_checks, boundary_points
    n, d = np.asarray(numerator), np.asarray(denominator)
    check(reported['numerator_mean'], n.mean())
    check(reported['denominator_mean'], d.mean())
    covariance = float(np.dot(n-n.mean(), d-d.mean()) / (4*5))
    check(reported['covariance_of_means'], covariance)
    check(reported['denominator_ci95'], numeric_summary(d)['ci95'])
    if reported['estimate'] is not None:
        check(reported['estimate'], 1-n.mean()/d.mean())
    endpoints = [x for pair in reported['ci95_set'] for x in pair if x is not None]
    candidates = list(np.linspace(-10, 10, 2001)) + list(np.logspace(1, 8, 100)) + list(-np.logspace(1, 8, 100))
    for endpoint in endpoints:
        step = max(1, abs(endpoint))*1e-6
        candidates += [endpoint-step, endpoint, endpoint+step]
    critical = float(stats.t.ppf(.975, 4))
    for share in candidates:
        residual = n - (1-share)*d
        mean = float(residual.mean()); se = float(residual.std(ddof=1)/np.sqrt(5))
        limit = critical*se
        if se > 0 and abs(abs(mean)-limit) <= 1e-10*max(abs(mean), limit, 1):
            boundary_points += 1
            continue
        accepted = abs(mean) <= limit
        assert set_contains(share, reported['ci95_set']) == accepted, (share, n, d, reported)
        membership_checks += 1


def verify_contrasts(values, reported):
    diffs = {key: np.asarray(values[a])-np.asarray(values[b]) for key, (a,b) in PAIRS.items()}
    diffs['interaction'] = diffs['ports_after_counts']-diffs['port_gain']
    own = {key: verify_stats(v, reported['effects'][key]) for key,v in diffs.items()}
    for key,row in own.items():
        expected=(float(stats.t.ppf(.975,4))+float(stats.norm.ppf(.8)))*row['sd']/math.sqrt(5)
        check(expected,reported['effects'][key]['approx_detectable_80pct'])
    verify_fieller(diffs['ports_after_counts'], diffs['port_gain'], reported['share_explained'])
    return own


def effect_text(row):
    return f"{row['mean']:+.3f} [{row['ci95'][0]:+.3f}, {row['ci95'][1]:+.3f}]"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1],
                        help='Repository root (default: parent of scripts/)')
    parser.add_argument('--out', type=Path,
                        help='Save Markdown to this new file (default: stdout only)')
    args = parser.parse_args()
    ROOT = args.repo.resolve()
    if args.out is not None and args.out.exists():
        parser.error(f'Refusing to overwrite an existing audit: {args.out}')
    summary_path = ROOT/'results/summary.json'
    reported = json.loads(summary_path.read_text())
    report_text = (ROOT/'results/summary.md').read_text()
    assert reported['n_runs'] == {cell:5 for cell in CELLS} and reported['supplementary_complete']
    assert '## Primary experiment' in report_text and '## Mechanism checks' in report_text
    graph = torch.load(ROOT/'data/hi_small.pt', weights_only=False)
    test = graph['split'].numpy() == 2
    y = graph['y'].numpy()[test].astype(bool)
    day = (graph['base'].numpy()[test,0]/86400).astype(int)
    masks = {'all': np.ones(len(y),dtype=bool), 'days_8_9': (day==8)|(day==9),
             'day_10_plus': day>=10, 'first_contact': graph['first_contact'].numpy()[test].astype(bool),
             'repeat': ~graph['first_contact'].numpy()[test].astype(bool),
             'repeat_free_accounts': graph['repeat_free'].numpy()[test].astype(bool)}
    assert len(y)==863900 and int(y.sum())==1611
    epochs, logs, predictions = {}, {}, {}
    for cell in CELLS:
        epochs[cell], logs[cell], predictions[cell] = [], [], []
        for seed in range(5):
            tag = ROOT/'results/runs'/f'{cell}_s{seed}'
            record = json.loads(tag.with_suffix('.json').read_text())
            assert record['cell']==cell and record['seed']==seed and record['epochs']==5
            assert record['hp']==HP and len(record['log'])==5
            expected_features = ['base']+[name for name in ('counts','novelty','ports') if name in cell]
            assert record['features']==expected_features
            with np.load(str(tag)+'_test_pred.npz',allow_pickle=False) as archive:
                assert archive.files == ['pred']; pred=archive['pred']
            assert pred.shape==(5,len(y)) and pred.dtype==np.int8 and np.isin(pred,[0,1]).all()
            log=record['log']; assert [row['epoch'] for row in log]==list(range(5))
            for epoch in range(5):
                check(f1_score(y,pred[epoch],zero_division=0),log[epoch]['test_f1'],1e-12)
                assert all(math.isfinite(value) for value in log[epoch].values())
            selected = max(range(1,5), key=lambda e: (log[e]['val_f1'],-e))
            epochs[cell].append(selected); logs[cell].append(log); predictions[cell].append(pred.astype(bool))
    own_selections = {}
    for selection in ('best_validation','final'):
        picked = epochs if selection=='best_validation' else {cell:[4]*5 for cell in CELLS}
        assert reported['selections'][selection]['selected_epochs']==picked
        subsets={}
        for subset, mask in masks.items():
            target=reported['selections'][selection]['subsets'][subset]
            assert target['n_tx']==int(mask.sum()) and target['n_laundering']==int(y[mask].sum())
            values={}
            for cell in CELLS:
                conf=[confusion(y[mask],predictions[cell][seed][picked[cell][seed],mask]) for seed in range(5)]
                for seed in range(5):
                    for key in ('tp','fp','fn','tn','f1'):
                        check(conf[seed][key],target['cells'][cell]['confusion_per_seed'][seed][key])
                values[cell]=[row['f1'] for row in conf]
                verify_stats(values[cell],target['cells'][cell])
            subsets[subset]={'values':values,'effects':verify_contrasts(values,target)}
        metrics={}
        for metric in ('test_ap','test_f1_argmax','val_ap'):
            target=reported['selections'][selection]['metrics'][metric]
            values={cell:[100*logs[cell][seed][picked[cell][seed]][metric] for seed in range(5)] for cell in CELLS}
            for cell in CELLS:verify_stats(values[cell],target['cells'][cell])
            metrics[metric]={'values':values,'effects':verify_contrasts(values,target)}
        own_selections[selection]={'subsets':subsets,'metrics':metrics}
    for key, item in reported['directional_consistency'].items():
        values=[own_selections['best_validation']['subsets'][subset]['effects'][key]['mean'] for subset in ('all','days_8_9')]
        values.append(own_selections['final']['metrics']['val_ap']['effects'][key]['mean'])
        check(values,[item[k] for k in ('full_test_f1','days_8_9_f1','final_validation_ap')])
        assert item['same_nonzero_sign']==bool(all(np.sign(x)==np.sign(values[0]) for x in values) and values[0]!=0)
    for cell in CELLS:
        for metric in ('val_f1','test_f1','val_ap','test_ap'):
            check([[100*row[metric] for row in seed_log] for seed_log in logs[cell]], reported['curves_per_seed'][cell][metric])
    full_days=(graph['base'].numpy()[:,0]/86400).astype(int)
    full_y=graph['y'].numpy()
    daily=[{'day':int(d), 'n_tx':int(np.sum(full_days==d)), 'n_laundering':int(full_y[full_days==d].sum())} for d in np.unique(full_days)]
    assert reported['daily_distribution']==daily
    tail=confusion(y,day>=10)
    for key,value in tail.items():check(value,reported['tail_flag_baseline'][key])
    p=own_selections['best_validation']['subsets']['all']
    lines=['# Independent completed-results audit','',f"Audit completed {dt.datetime.now(dt.timezone.utc).isoformat()}.", '',
           f'**PASS:** all 25 expected runs and all 125 saved epoch predictions were checked. {checks:,} numerical comparisons passed; '
           f'{membership_checks:,} independent Fieller membership comparisons passed ({boundary_points} near-boundary numerical points excluded).', '',
           'The audit did not import the production analyzer. Full-test F1 was recomputed with scikit-learn; subset F1 used 2TP/(positives+flags). '
           'Confidence intervals were reconstructed from the five paired differences. Ratio-set membership was checked by directly inverting the '
           't test on N − (1−share)D, without solving the production quadratic.', '',
           '## Primary five-seed results','', '| Cell | Mean F1 ± SD | Selected epochs | Five seed F1 values |','|---|---:|---|---|']
    for cell in CELLS:
        row=numeric_summary(p['values'][cell]);lines.append(f"| {cell} | {row['mean']:.3f} ± {row['sd']:.3f} | {epochs[cell]} | "+', '.join(f'{v:.3f}' for v in row['per_seed'])+' |')
    lines += ['', '| Contrast | Mean [95% CI], F1 points | Five paired differences |','|---|---:|---|']
    for key,row in p['effects'].items():
        lines.append(f"| {key} | {effect_text(row)} | "+', '.join(f'{v:+.3f}' for v in row['per_seed'])+' |')
    share=reported['selections']['best_validation']['subsets']['all']['share_explained']
    zero_share_compatible=p['effects']['interaction']['ci95'][0] <= 0 <= p['effects']['interaction']['ci95'][1]
    full_share_compatible=p['effects']['ports_after_counts']['ci95'][0] <= 0 <= p['effects']['ports_after_counts']['ci95'][1]
    assert set_contains(0,share['ci95_set']) == zero_share_compatible
    assert set_contains(1,share['ci95_set']) == full_share_compatible
    lines += ['', 'Primary share confidence-set record (fractions; null endpoints denote the corresponding infinity):','', '```json',json.dumps(share,indent=2),'```', '',
              '### Compatibility of the two endpoint explanations', '',
              f"- **0% share:** compatible with the nominal 95% set: **{zero_share_compatible}**. This is the same paired test as the factorial interaction N−D=0.",
              f"- **100% share:** compatible with the nominal 95% set: **{full_share_compatible}**. This is the same paired test as the residual port gain N=0.",
              'Both identities were checked against the reported Fieller set. Compatibility is not proof of equality or equivalence. '
              'If the port-gain denominator is uncertain, these contrast tests do not create a stable positive-gain percentage.', '',
              '## Selection, temporal, and metric sensitivity','', '| Selection/view | Port gain | Ports after counts | Counts+Ports − Counts+novelty |','|---|---:|---:|---:|']
    for selection in ('best_validation','final'):
        for subset in ('all','days_8_9','day_10_plus','first_contact','repeat','repeat_free_accounts'):
            effects=own_selections[selection]['subsets'][subset]['effects']
            lines.append(f'| {selection}/{subset} | '+' | '.join(effect_text(effects[k]) for k in ('port_gain','ports_after_counts','ports_beyond_novelty'))+' |')
        for metric in ('test_ap','val_ap','test_f1_argmax'):
            effects=own_selections[selection]['metrics'][metric]['effects']
            lines.append(f'| {selection}/{metric} | '+' | '.join(effect_text(effects[k]) for k in ('port_gain','ports_after_counts','ports_beyond_novelty'))+' |')
    lines += ['', '## What this verification establishes','',
              '- The effects come from the full planned experiment, with the original validation-only epoch selection and all five seeds retained.',
              '- Artifact integrity and numerical correctness do not by themselves establish a causal mechanism, equivalence, or population-wide robustness.',
              '- Confidence intervals are conditional on this single dataset and the fixed five-epoch stochastic-inference protocol. Five seed blocks provide limited precision and a weak basis for checking normality.',
              '- AP and validation metrics were checked against every source log. They cannot be recomputed independently from saved binary test predictions; no probability scores were saved.',
              '- The temporal and final-epoch views are disclosed post-hoc sensitivities. Same-direction estimates are not independent replications; sign reversals or wide intervals must remain visible.',
              '- The supplementary rank contrast is a comparison of feature representations. First-contact target edges can receive information from repeated neighboring edges, so this does not isolate a pure causal identity component.', '',
              'Summary SHA-256: `'+hashlib.sha256(summary_path.read_bytes()).hexdigest()+'`.']
    if args.out is not None:
        args.out.write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__=='__main__': main()
