"""Read-only, chunked audit of the raw CSV against the prepared graph."""
import argparse
import csv
import gc
import json
from pathlib import Path
import resource
import time

import numpy as np
import pandas as pd
import torch

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
N = 5078345

def codes(values, mapping):
    local, unique = pd.factorize(values, sort=False)
    global_codes = np.fromiter((mapping.setdefault(value, len(mapping)) for value in unique), dtype=np.int64)
    return global_codes[local]



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args()
    ROOT = args.repo.resolve()
    OUT = args.out or ROOT / 'results'
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.time()
    raw_path = ROOT / 'data/raw/HI-Small_Trans.csv'
    with raw_path.open() as f:
        header = next(csv.reader(f))
    arrays = {k: np.empty(N, dtype=np.float64 if k == 'amount' else np.int64)
              for k in ('u', 'v', 'timestamp', 'amount', 'currency', 'format', 'y')}
    accounts, identities, currencies, formats = {}, {}, {}, {}
    collisions = []
    offset = 0


    for chunk in pd.read_csv(raw_path, dtype=str, chunksize=250000):
        count = len(chunk)
        stop = offset + count
        assert stop <= N
        idx = slice(offset, stop)
        banks = np.column_stack([chunk.iloc[:, 1], chunk.iloc[:, 3]]).ravel()
        numbers = np.column_stack([chunk.iloc[:, 2], chunk.iloc[:, 4]]).ravel()
        keys = np.asarray([bank + number for bank, number in zip(banks, numbers)], dtype=object)
        pair_codes = codes(keys, accounts)
        arrays['u'][idx], arrays['v'][idx] = pair_codes[0::2], pair_codes[1::2]
        unique_pairs = pd.DataFrame({'bank': banks, 'number': numbers}).drop_duplicates()
        for bank, number in unique_pairs.itertuples(index=False, name=None):
            key, pair = bank + number, (bank, number)
            previous = identities.setdefault(key, pair)
            if previous != pair:
                collisions.append({'key': key, 'previous': previous, 'current': pair})
        arrays['timestamp'][idx] = pd.to_datetime(chunk.iloc[:, 0], format='%Y/%m/%d %H:%M').to_numpy(dtype='datetime64[s]').astype(np.int64)
        arrays['amount'][idx] = chunk.iloc[:, 5].astype(float).to_numpy()
        raw_currencies = np.column_stack([chunk.iloc[:, 6], chunk.iloc[:, 8]]).ravel()
        arrays['currency'][idx] = codes(raw_currencies, currencies)[0::2]
        arrays['format'][idx] = codes(chunk.iloc[:, 9].to_numpy(), formats)
        arrays['y'][idx] = chunk.iloc[:, 10].astype(np.int64).to_numpy()
        offset = stop
        print(f'Read {offset:,}/{N:,} raw rows', flush=True)

    assert offset == N
    assert not collisions
    del chunk, banks, numbers, keys, pair_codes, unique_pairs, raw_currencies
    gc.collect()
    timestamp_min, timestamp_max = int(arrays['timestamp'].min()), int(arrays['timestamp'].max())
    order = np.lexsort((np.random.default_rng(0).permutation(N), arrays['timestamp']))
    d = torch.load(ROOT / 'data/hi_small.pt', weights_only=False)
    checks = {}
    for key, actual in [('u', d['edge_index'][0].numpy()), ('v', d['edge_index'][1].numpy()), ('y', d['y'].numpy())]:
        checks[key] = int(np.count_nonzero(arrays[key][order] != actual))
    for column, key in enumerate(('timestamp', 'amount', 'currency', 'format')):
        expected = arrays[key][order]
        if key == 'timestamp':
            expected = expected - timestamp_min
        checks['base_' + key] = int(np.count_nonzero(expected != d['base'][:, column].numpy()))
    assert all(value == 0 for value in checks.values()), checks
    assert len(accounts) == len(identities) == d['n_nodes'] == 515088
    result = {
        'status': 'passed',
        'raw_rows': offset,
        'raw_laundering': int(arrays['y'].sum()),
        'raw_header': header,
        'timestamp_min': str(np.datetime64(timestamp_min, 's')),
        'timestamp_max': str(np.datetime64(timestamp_max, 's')),
        'timestamp_timezone': 'not supplied by CSV',
        'accounts': len(accounts),
        'bank_account_concatenation_collisions': len(collisions),
        'currency_codes_in_first_seen_order': currencies,
        'payment_format_codes_in_first_seen_order': formats,
        'graph_mismatches': checks,
        'order': 'timestamp ascending, then numpy default_rng(0).permutation(row_count)',
        'runtime_seconds': round(time.time() - started, 3),
        'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
    }
    (OUT / 'raw-alignment.json').write_text(json.dumps(result, indent=2) + '\n')
    markdown = f'''# Raw CSV alignment audit

    The full raw CSV contains **{offset:,} transactions**, **{result['raw_laundering']:,} laundering labels**, and **{len(accounts):,} distinct bank/account identities**.

    Timestamps span **{result['timestamp_min']}** through **{result['timestamp_max']}**. The CSV does not specify a timezone.

    The audit read the raw file in chunks and independently recreated first-seen account, currency, and payment-format coding. It then applied timestamp order with the fixed seed-0 random tie-break and compared every row against the prepared graph.

    | Graph field | Mismatches |
    |---|---:|
    ''' + ''.join(f'| {key} | {value:,} |\n' for key, value in checks.items()) + f'''
    Bank-plus-account concatenation was checked against the original two-column identity: **{len(collisions)} collisions**. All {len(accounts):,} identities are distinct after concatenation in this dataset.

    This check establishes raw-to-graph alignment for labels, endpoints, timestamps, received amounts, receiving currencies, and payment formats. It does not validate scientific conclusions or training adequacy.

    Audit script: `scripts/audit_raw_alignment.py`. Machine-readable results: `raw-alignment.json`. Peak RSS: {result['peak_rss_bytes'] / 1024**3:.2f} GiB; elapsed: {result['runtime_seconds']:.1f} seconds.
    '''
    (OUT / 'raw-alignment.md').write_text(markdown)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
