#!/usr/bin/env python3
"""Independent full-graph audit. Does not call the project's feature functions."""
import argparse
import gc
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA = '4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080'


def counts(y, p):
    tp = int(np.count_nonzero(y & p))
    fp = int(np.count_nonzero(~y & p))
    fn = int(np.count_nonzero(y & ~p))
    tn = int(np.count_nonzero(~y & ~p))
    return dict(tp=tp, fp=fp, fn=fn, tn=tn,
                f1=2 * tp / max(2 * tp + fp + fn, 1))


def population(y, mask):
    n = int(mask.sum())
    positive = int(y[mask].sum())
    return dict(transactions=n, laundering=positive,
                prevalence=positive / n if n else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args()
    ROOT = args.repo.resolve()
    OUT = args.out or ROOT / 'results'
    OUT.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256()
    with (ROOT / 'data/raw/HI-Small_Trans.csv.zip').open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            sha.update(chunk)
    assert sha.hexdigest() == EXPECTED_SHA
    data = torch.load(ROOT / 'data/hi_small.pt', weights_only=False)
    u, v = data['edge_index'].numpy()
    n = data['n_nodes']
    y = data['y'].numpy().astype(bool)
    split = data['split'].numpy()
    timestamp = data['base'][:, 0].numpy()
    day = (timestamp // 86400).astype(np.int64)
    print('Loaded full graph and verified archive checksum', flush=True)
    result = dict(archive_sha256=sha.hexdigest(), n_nodes=n,
                  n_transactions=len(y), n_laundering=int(y.sum()),
                  source_revision='6412f57ab89c9c28633ce5e837eca4c9a35c5dbe',
                  source_url='https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans')
    checks = {}
    checks['timestamps_nonmonotonic'] = int(np.count_nonzero(timestamp[1:] < timestamp[:-1]))
    checks['invalid_labels'] = int(np.count_nonzero(~np.isin(data['y'].numpy(), [0, 1])))
    checks['invalid_accounts'] = int(np.count_nonzero((u < 0) | (u >= n) | (v < 0) | (v >= n)))

    # Find the first occurrence of each directed pair globally, independently
    # of prepare.py's grouped sorting and local pair-index algorithm.
    _, first, inverse, frequency = np.unique(u * n + v, return_index=True,
                                             return_inverse=True, return_counts=True)
    novelty = np.zeros(len(y), dtype=bool)
    novelty[first] = True
    checks['first_contact_mismatches'] = int(np.count_nonzero(novelty != data['first_contact'].numpy()))
    checks['novelty_mismatches'] = int(np.count_nonzero(novelty != data['novelty'].numpy()[:, 0]))
    series = pd.Series(novelty.astype(np.int64))
    for endpoint, name, total_col, distinct_col, port_col in [
        (u, 'sender', 0, 1, 1), (v, 'receiver', 2, 3, 0)
    ]:
        grouped = series.groupby(endpoint, sort=False)
        total = grouped.cumcount().to_numpy()
        distinct = grouped.cumsum().to_numpy() - novelty
        port = distinct[first][inverse]
        checks[name + '_total_mismatches'] = int(np.count_nonzero(total != data['counts'].numpy()[:, total_col]))
        checks[name + '_distinct_mismatches'] = int(np.count_nonzero(distinct != data['counts'].numpy()[:, distinct_col]))
        checks[name + '_port_mismatches'] = int(np.count_nonzero(port != data['ports'].numpy()[:, port_col]))
        checks[name + '_first_contact_identity_failures'] = int(np.count_nonzero(port[novelty] != distinct[novelty]))
        checks[name + '_repeat_strict_inequality_failures'] = int(np.count_nonzero(port[~novelty] >= distinct[~novelty]))
        print('Reconstructed', name, 'causal history for', len(y), 'transactions', flush=True)
        del grouped, total, distinct, port
        gc.collect()

    repeaters = np.zeros(n, dtype=bool)
    repeaters[u[first[frequency > 1]]] = True
    repeaters[v[first[frequency > 1]]] = True
    repeat_free = ~repeaters[u] & ~repeaters[v]
    checks['repeat_free_mismatches'] = int(np.count_nonzero(repeat_free != data['repeat_free'].numpy()))
    del inverse, frequency, first, series
    gc.collect()

    daily = np.bincount(day)
    candidates = []
    for i, j in itertools.combinations(range(len(daily)), 2):
        shares = np.array([daily[:i].sum(), daily[i:j].sum(), daily[j:].sum()]) / len(y)
        error = float(np.max(np.abs(shares - [0.6, 0.2, 0.2]) / [0.6, 0.2, 0.2]))
        candidates.append((error, i, j))
    error, i, j = min(candidates)
    independent_split = np.where(day < i, 0, np.where(day < j, 1, 2))
    checks['temporal_split_mismatches'] = int(np.count_nonzero(independent_split != split))
    result['day_cut_points'] = [i, j]
    result['split_max_relative_error'] = error
    result['daily'] = [dict(day=d, **population(y, day == d)) for d in range(len(daily))]
    result['splits'] = {name: population(y, split == s)
                        for s, name in enumerate(['train', 'validation', 'test'])}
    test = split == 2
    result['test_strata'] = {
        name: population(y, test & mask) for name, mask in [
            ('all', np.ones(len(y), dtype=bool)), ('days_8_9', np.isin(day, [8, 9])),
            ('tail_day_10_plus', day >= 10), ('first_contact', novelty),
            ('repeat', ~novelty), ('repeat_free_accounts', repeat_free),
            ('repeating_accounts', ~repeat_free)]}
    result['tail_flag_baseline'] = counts(y[test], day[test] >= 10)
    result['tail_fraction_of_test_laundering'] = int(y[test & (day >= 10)].sum()) / int(y[test].sum())

    # Inspect only the two runs available before this audit. These metrics do
    # not affect epoch, seed, architecture, or stopping choices.
    yt = y[test]
    strata = {'all': np.ones(len(yt), dtype=bool), 'days_8_9': np.isin(day[test], [8, 9]),
              'tail_day_10_plus': day[test] >= 10, 'first_contact': novelty[test],
              'repeat': ~novelty[test], 'repeat_free_accounts': repeat_free[test]}
    result['existing_runs'] = {}
    for cell in ['base', 'ports']:
        tag = f'{cell}_s0'
        record = json.loads((ROOT / f'results/runs/{tag}.json').read_text())
        with np.load(ROOT / f'results/runs/{tag}_test_pred.npz', allow_pickle=False) as f:
            pred = f['pred'].astype(bool)
        assert pred.shape == (5, len(yt))
        discrepancies = []
        epochs = []
        for epoch, row in enumerate(record['log']):
            cm = counts(yt, pred[epoch])
            discrepancies.append(abs(cm['f1'] - row['test_f1']))
            epochs.append(dict(epoch=epoch, **cm, logged_f1=row['test_f1']))
        checks[tag + '_epoch_f1_mismatches'] = int(np.count_nonzero(np.array(discrepancies) > 1e-12))
        selected = 1 + int(np.argmax([row['val_f1'] for row in record['log'][1:]]))
        selection = {}
        for name, epoch in [('best_validation', selected), ('final', 4)]:
            selection[name] = dict(epoch=epoch, logged_metrics=record['log'][epoch],
                                   strata={s: counts(yt[mask], pred[epoch][mask]) for s, mask in strata.items()})
        result['existing_runs'][tag] = dict(epochs=epochs, selection=selection,
                                            max_f1_discrepancy=max(discrepancies))
    result['checks_mismatches'] = checks
    result['all_checks_passed'] = not any(checks.values())
    (OUT / 'data-audit.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    lines = ['# Independent full-data audit', '',
             'Archive SHA-256 verified: `' + EXPECTED_SHA + '`.', '',
             f'Graph: {len(y):,} transactions, {n:,} accounts, {int(y.sum()):,} laundering labels.',
             f'Independently selected day cuts: {i} and {j}; all causal feature checks have zero mismatches.'
             if result['all_checks_passed'] else 'Some integrity checks failed; inspect JSON before further use.', '',
             '| Day | Transactions | Laundering | Prevalence |', '|---:|---:|---:|---:|']
    lines += [f"| {r['day']} | {r['transactions']:,} | {r['laundering']:,} | {100*r['prevalence']:.3f}% |" for r in result['daily']]
    lines += ['', '| Test subset | Transactions | Laundering | Prevalence |', '|---|---:|---:|---:|']
    lines += [f"| {name} | {r['transactions']:,} | {r['laundering']:,} | {100*r['prevalence']:.3f}% |" for name, r in result['test_strata'].items()]
    b = result['tail_flag_baseline']
    lines += ['', f"Flagging all test transactions on day 10 or later gives TP={b['tp']}, FP={b['fp']}, FN={b['fn']}, and F1={100*b['f1']:.2f}%. This is a descriptive test-distribution diagnostic, not a deployable rule selected without test information.", '',
              'Both saved Base/Ports seed-0 prediction archives reproduce every logged epoch F1 against the regenerated test labels, within 1e-12.', '',
              'Counts and ports were reconstructed independently from global directed-pair first appearances and grouped cumulative sums; the project feature functions were not called. Both the first-contact equality and strict repeat inequality hold on every transaction. Account repeat-free flags were also independently reconstructed.', '',
              'These checks establish dataset and output integrity. Two runs do not establish the research estimand or a significant model effect. Raw CSV parsing alignment is audited separately.']
    (OUT / 'data-audit.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'all_checks_passed': result['all_checks_passed'],
                      'checks_mismatches': checks, 'tail': result['test_strata']['tail_day_10_plus'],
                      'tail_flag_baseline': b}, indent=2), flush=True)
    assert result['all_checks_passed']


if __name__ == '__main__':
    main()
