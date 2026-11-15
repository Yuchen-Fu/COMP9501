# Independent full-data audit

Archive SHA-256 verified: `4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080`.

Graph: 5,078,345 transactions, 515,088 accounts, 5,177 laundering labels.
Independently selected day cuts: 6 and 8; all causal feature checks have zero mismatches.

| Day | Transactions | Laundering | Prevalence |
|---:|---:|---:|---:|
| 0 | 1,114,921 | 322 | 0.029% |
| 1 | 754,449 | 408 | 0.054% |
| 2 | 207,382 | 391 | 0.189% |
| 3 | 207,430 | 407 | 0.196% |
| 4 | 482,650 | 471 | 0.098% |
| 5 | 482,089 | 531 | 0.110% |
| 6 | 482,751 | 497 | 0.103% |
| 7 | 482,773 | 539 | 0.112% |
| 8 | 654,467 | 514 | 0.079% |
| 9 | 208,325 | 442 | 0.212% |
| 10 | 396 | 232 | 58.586% |
| 11 | 281 | 170 | 60.498% |
| 12 | 184 | 106 | 57.609% |
| 13 | 121 | 70 | 57.851% |
| 14 | 46 | 28 | 60.870% |
| 15 | 46 | 26 | 56.522% |
| 16 | 23 | 15 | 65.217% |
| 17 | 11 | 8 | 72.727% |

| Test subset | Transactions | Laundering | Prevalence |
|---|---:|---:|---:|
| all | 863,900 | 1,611 | 0.186% |
| days_8_9 | 862,792 | 956 | 0.111% |
| tail_day_10_plus | 1,108 | 655 | 59.116% |
| first_contact | 37,221 | 1,325 | 3.560% |
| repeat | 826,679 | 286 | 0.035% |
| repeat_free_accounts | 2,349 | 23 | 0.979% |
| repeating_accounts | 861,551 | 1,588 | 0.184% |

Flagging all test transactions on day 10 or later gives TP=655, FP=453, FN=956, and F1=48.18%. This is a descriptive test-distribution diagnostic, not a deployable rule selected without test information.

Both saved Base/Ports seed-0 prediction archives reproduce every logged epoch F1 against the regenerated test labels, within 1e-12.

Counts and ports were reconstructed independently from global directed-pair first appearances and grouped cumulative sums; the project feature functions were not called. Both the first-contact equality and strict repeat inequality hold on every transaction. Account repeat-free flags were also independently reconstructed.

These checks establish dataset and output integrity. Two runs do not establish the research estimand or a significant model effect.

The separate [raw CSV alignment audit](raw-alignment.md) also passed: every endpoint, label, timestamp, amount, currency code, and payment-format code matches the prepared graph. Bank/account concatenation has zero collisions across all 515,088 identities. The source dates span September 1–18, 2022; the CSV supplies no timezone.
