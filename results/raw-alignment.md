# Raw CSV alignment audit

The full raw CSV contains **5,078,345 transactions**, **5,177 laundering labels**, and **515,088 distinct bank/account identities**.

Timestamps span **2022-09-01T00:00:00** through **2022-09-18T16:18:00**. The CSV does not specify a timezone.

The audit read the raw file in chunks and independently recreated first-seen account, currency, and payment-format coding. It then applied timestamp order with the fixed seed-0 random tie-break and compared every row against the prepared graph.

| Graph field | Mismatches |
|---|---:|
| u | 0 |
| v | 0 |
| y | 0 |
| base_timestamp | 0 |
| base_amount | 0 |
| base_currency | 0 |
| base_format | 0 |

Bank-plus-account concatenation was checked against the original two-column identity: **0 collisions**. All 515,088 identities are distinct after concatenation in this dataset.

This check establishes raw-to-graph alignment for labels, endpoints, timestamps, received amounts, receiving currencies, and payment formats. It does not validate scientific conclusions or training adequacy.

Audit script: `audit_raw_alignment.py`. Machine-readable results: `raw-alignment.json`. Peak RSS: 1.54 GiB; elapsed: 36.6 seconds.
