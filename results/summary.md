# What do port numbers add beyond counterparty counts?

## Primary experiment

The primary 2×2 comparison uses five seeds and five epochs per run. Each run selects the epoch with the highest validation F1 among epochs 1–4 (earliest tie), and applies that epoch's validation-selected threshold to the full test set. Counts+novelty is supplementary. All F1 and AP values below are percentage points. Each contrast shows its mean, 95% paired-seed t interval and two-sided p-value.

| Cell | Test F1, mean ± SD | Test AP, mean ± SD | Selected epochs, seeds 0–4 |
|---|---:|---:|---|
| base | 23.68 ± 3.38 | 15.18 ± 2.57 | [2, 4, 4, 4, 4] |
| counts | 24.66 ± 3.80 | 17.91 ± 3.68 | [4, 4, 4, 4, 4] |
| ports | 31.16 ± 4.63 | 22.29 ± 5.80 | [4, 4, 4, 4, 4] |
| counts+ports | 39.57 ± 0.81 | 35.55 ± 3.33 | [4, 4, 4, 4, 3] |
| counts+novelty | 48.99 ± 2.45 | 46.81 ± 5.70 | [4, 4, 4, 4, 4] |

| Core contrast | Mean [95% paired-seed t interval] | Five seed differences |
|---|---:|---|
| Counts − Base | +0.98 [-7.18, +9.14], p=0.755 | +11.22, +3.66, -3.69, -1.58, -4.72 |
| Ports − Base | +7.48 [+2.96, +12.00], p=0.010 | +11.11, +5.86, +11.69, +4.58, +4.15 |
| Counts+Ports − Counts | +14.91 [+10.11, +19.71], p<0.001 | +10.53, +11.65, +14.81, +19.00, +18.56 |
| (Counts+Ports − Counts) − (Ports − Base) | +7.43 [-0.97, +15.83], p=0.070 | -0.58, +5.79, +3.12, +14.42, +14.41 |

**Primary estimand: share of the port gain explained by counts.** -99.4% (95% Fieller interval -512.7% to 8.4%).

This is a ratio of cell-mean contrasts, not a causal mediation proportion. Values are not constrained to 0–100%. Failure to detect a residual gain does not establish that counts explain all of it.

## Mechanism checks

| Test stratum | Transactions | Laundering | Counts+Ports − Counts [95% CI] |
|---|---:|---:|---:|
| first_contact | 37,221 | 1,325 | +12.65 [+7.14, +18.15], p=0.003 |
| repeat | 826,679 | 286 | +8.92 [+3.28, +14.57], p=0.012 |
| repeat_free_accounts | 2,349 | 23 | -4.42 [-7.67, -1.18], p=0.019 |

Supplementary representation comparison:

| Stratum | Counts+novelty − Counts [95% CI] | Counts+Ports − Counts+novelty [95% CI] |
|---|---:|---:|
| all | +24.33 [+21.47, +27.19], p<0.001 | -9.42 [-13.11, -5.73], p=0.002 |
| first_contact | +24.05 [+21.00, +27.09], p<0.001 | -11.40 [-15.26, -7.54], p=0.001 |
| repeat | +4.87 [-5.32, +15.07], p=0.255 | +4.05 [-3.93, +12.03], p=0.231 |
| repeat_free_accounts | -3.58 [-9.73, +2.57], p=0.181 | -0.84 [-9.70, +8.02], p=0.805 |

Ports equal distinct counts conditional on first contact, but the Counts-only model is not given that status. Counts and ports together reveal novelty; neighboring repeated edges can also transmit rank information. These strata do not isolate a causal identity mechanism. The supplementary contrast substitutes the port representation for an explicit novelty flag; it does not add ports to Counts+novelty. The JSON key ports_beyond_novelty is retained for compatibility and denotes this substitution contrast only.

## Post-hoc sensitivity analyses

Final-epoch and day-specific analyses were added after inspection of Base and Ports seed 0. They do not replace the original primary selection and are not independent replications.

| Selection / subset | Ports − Base [95% CI] | Counts+Ports − Counts [95% CI] | Share explained |
|---|---:|---:|---|
| best validation / all | +7.48 [+2.96, +12.00], p=0.010 | +14.91 [+10.11, +19.71], p<0.001 | -99.4% (95% Fieller interval -512.7% to 8.4%). |
| best validation / days_8_9 | +4.24 [+2.89, +5.59], p<0.001 | +8.98 [+6.59, +11.37], p<0.001 | -111.9% (95% Fieller interval -233.0% to -39.3%). |
| final epoch / all | +6.04 [+2.01, +10.07], p=0.014 | +15.28 [+9.87, +20.69], p=0.001 | -152.9% (95% Fieller interval -714.5% to -23.7%). |
| final epoch / days_8_9 | +4.01 [+3.06, +4.97], p<0.001 | +9.10 [+6.44, +11.76], p<0.001 | -126.7% (95% Fieller interval -216.0% to -57.8%). |

| Final-epoch diagnostic | Ports − Base [95% CI] | Counts+Ports − Counts [95% CI] |
|---|---:|---:|
| val_ap | +8.18 [+5.00, +11.37], p=0.002 | +10.96 [+6.14, +15.78], p=0.003 |
| test_ap | +5.68 [-2.11, +13.48], p=0.113 | +18.22 [+12.33, +24.11], p=0.001 |
| test_f1_argmax | +8.04 [-10.00, +26.08], p=0.284 | +9.06 [-15.45, +33.58], p=0.363 |

The interaction is the port gain with counts minus the port gain without them. A positive value means the gain is larger with counts, which is the same statement as a negative share.

| Outcome | Interaction, best validation epoch | Interaction, final epoch |
|---|---:|---:|
| Full test F1 | +7.43 [-0.97, +15.83], p=0.070 | +9.24 [+2.10, +16.37], p=0.023 |
| Days 8–9 F1 | +4.74 [+1.97, +7.51], p=0.009 | +5.09 [+2.46, +7.72], p=0.006 |
| Full test AP | +10.52 [+3.85, +17.19], p=0.012 | +12.54 [+3.53, +21.54], p=0.018 |
| Validation AP | +3.63 [-2.65, +9.91], p=0.184 | +2.78 [-3.79, +9.34], p=0.306 |
| Full test F1 at a fixed 0.5 threshold | -1.26 [-22.60, +20.08], p=0.877 | +1.02 [-24.93, +26.97], p=0.918 |

The post-hoc rule ‘flag day 10 onward’ has test F1 48.18, TP=655, FP=453, FN=956. This diagnoses temporal composition; it is not a validated detector.

| Contrast | Same nonzero sign: full-test F1, days 8–9 F1, final validation AP |
|---|---|
| Counts − Base | no |
| Ports − Base | yes |
| Counts+Ports − Counts | yes |
| Counts+novelty − Counts | yes |
| Counts+Ports − Counts+novelty | yes |
| (Counts+Ports − Counts) − (Ports − Base) | yes |

Agreement in sign is directional consistency, not statistical significance.

## Confusion counts

Counts below are means across seeds at the primary selection; individual-seed TP, FP, FN and TN are retained in summary.json.

| Subset | Cell | TP | FP | FN |
|---|---|---:|---:|---:|
| all | base | 450.2 | 1708.2 | 1160.8 |
| all | counts | 451.2 | 1561.4 | 1159.8 |
| all | ports | 510.2 | 1148.4 | 1100.8 |
| all | counts+ports | 664.4 | 1078.4 | 946.6 |
| all | counts+novelty | 881.6 | 1102.4 | 729.4 |
| days_8_9 | base | 242.6 | 1537.2 | 713.4 |
| days_8_9 | counts | 220.4 | 1397.2 | 735.6 |
| days_8_9 | ports | 256.0 | 1121.8 | 700.0 |
| days_8_9 | counts+ports | 295.8 | 1033.6 | 660.2 |
| days_8_9 | counts+novelty | 413.4 | 980.2 | 542.6 |
| day_10_plus | base | 207.6 | 171.0 | 447.4 |
| day_10_plus | counts | 230.8 | 164.2 | 424.2 |
| day_10_plus | ports | 254.2 | 26.6 | 400.8 |
| day_10_plus | counts+ports | 368.6 | 44.8 | 286.4 |
| day_10_plus | counts+novelty | 468.2 | 122.2 | 186.8 |
| first_contact | base | 416.4 | 906.8 | 908.6 |
| first_contact | counts | 417.8 | 917.6 | 907.2 |
| first_contact | ports | 469.2 | 806.6 | 855.8 |
| first_contact | counts+ports | 623.8 | 903.2 | 701.2 |
| first_contact | counts+novelty | 848.4 | 903.4 | 476.6 |
| repeat | base | 33.8 | 801.4 | 252.2 |
| repeat | counts | 33.4 | 643.8 | 252.6 |
| repeat | ports | 41.0 | 341.8 | 245.0 |
| repeat | counts+ports | 40.6 | 175.2 | 245.4 |
| repeat | counts+novelty | 33.2 | 199.0 | 252.8 |
| repeat_free_accounts | base | 0.8 | 15.0 | 22.2 |
| repeat_free_accounts | counts | 1.4 | 15.6 | 21.6 |
| repeat_free_accounts | ports | 0.2 | 5.2 | 22.8 |
| repeat_free_accounts | counts+ports | 0.4 | 6.0 | 22.6 |
| repeat_free_accounts | counts+novelty | 0.4 | 0.8 | 22.6 |

## Scope of the evidence

Intervals use five independent matched seed blocks and approximate normality of seed contrasts. They quantify training/inference seed variability on this fixed dataset, not population-wide uncertainty. Secondary intervals are unadjusted exploratory comparisons. Approximate 80%-power sensitivity thresholds based on observed paired-seed SDs are retained in JSON; these are not achieved-power claims.

The benchmark uses full evaluation graphs, graph-specific normalization, stochastic neighbor sampling, dropout and batch statistics at inference. Causal history features therefore do not make the complete model an online-causal detector. Five epochs do not establish replication of the published performance levels; the public reference code defaults to 100 epochs. Binary saved test predictions support subset F1/confusion counts, but not subset AP. An inconclusive or unstable share estimate is a valid research outcome.
