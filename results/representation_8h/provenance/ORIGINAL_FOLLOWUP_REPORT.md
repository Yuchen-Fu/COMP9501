# Explicit pair novelty: controlled follow-up

**Decision: inconclusive.** The primary F1 interval includes zero; the experiment does not establish a positive addition effect or equivalence.

The primary comparison retains all count and port information, replacing a constant zero input slot with the explicit novelty bit. All arms have the same parameter count and initialization within seed blocks. This follow-up does not pool the original 25 runs.

Novelty means the first observed directed account pair within this dataset window, not necessarily a new banking relationship. It is already derivable from the count and port inputs. The experiment therefore tests an explicit representation of available information, not an increase in information content or theoretical expressivity.

## Primary endpoint

Each model uses its exact highest validation-AP checkpoint, with earliest ties; its F1 threshold is selected on validation at that checkpoint. Test outcomes choose neither checkpoint nor threshold. Values below are percentage points, with nominal paired-seed 95% t intervals.

| Input group | Seeds (n) | Test F1, mean ± seed SD | Test AP, mean ± seed SD |
|---|---|---:|---:|
| Counts + Ports + zero | 15, 16, 17, 18, 19 (n=5) | 33.97 ± 9.13 | 32.43 ± 9.45 |
| Counts + Ports + novelty | 15, 16, 17, 18, 19 (n=5) | 26.76 ± 6.40 | 27.93 ± 15.94 |
| Counts + novelty (zero port slots) | 15, 16, 17, 18, 19 (n=5) | 38.55 ± 6.89 | 41.03 ± 6.33 |

These per-arm means describe different seed cohorts when the arm sizes differ. The contrasts below are computed within shared seed blocks; subtracting unmatched full-arm means is not the paired estimate.

| Paired comparison | Shared seeds (n) | F1 difference [95% CI] | AP difference [95% CI] |
|---|---|---:|---:|
| CPN − CP (primary) | 15, 16, 17, 18, 19 (n=5) | -7.21 [-15.46, +1.03] | -4.49 [-19.11, +10.13] |
| CN − CP (secondary) | 15, 16, 17, 18, 19 (n=5) | +4.58 [-11.45, +20.60] | +8.61 [-2.87, +20.08] |
| CPN − CN (secondary) | 15, 16, 17, 18, 19 (n=5) | -11.79 [-25.62, +2.03] | -13.10 [-31.99, +5.79] |

| Paired comparison | F1 means within shared seeds (positive arm / reference) | AP means within shared seeds (positive arm / reference) |
|---|---:|---:|
| CPN − CP (primary) | 26.76 / 33.97 | 27.93 / 32.43 |
| CN − CP (secondary) | 38.55 / 33.97 | 41.03 / 32.43 |
| CPN − CN (secondary) | 26.76 / 38.55 | 27.93 / 41.03 |

The addition contrast is primary. Replacement and rank-after-novelty contrasts are secondary and unadjusted. A nonsignificant result does not establish equivalence, and a favorable secondary result cannot rescue an unsupported primary claim.

![Paired test F1 and AP differences](figures/paired-contrasts.png)

**Figure 1.** Mean within-seed differences with nominal 95% Student t intervals. Each comparison uses only its shared seeds; secondary intervals are unadjusted.

## AML screening consequences

These are averages across each arm’s declared seeds on the same test transfers. Fractional counts are seed averages. Precision and recall are mean per-seed percentages, not ratios of the averaged counts.

| Group | True alerts (TP) | False alerts (FP) | Missed laundering (FN) | Total alerts | Precision (%) | Recall (%) |
|---|---:|---:|---:|---:|---:|---:|
| Counts + Ports + zero | 693.60 | 1751.40 | 917.40 | 2445.00 | 33.68 | 43.05 |
| Counts + Ports + novelty | 794.80 | 3545.60 | 816.20 | 4340.40 | 19.19 | 49.34 |
| Counts + novelty (zero port slots) | 967.20 | 2557.80 | 643.80 | 3525.00 | 29.13 | 60.04 |

A and B use the same ten seed blocks. C uses five; its matched contrasts are reported above. Each model has its own validation-selected threshold, so this table does not compare performance at a fixed investigator workload. Alerts are transactions, not distinct cases.

## Fixed-checkpoint and temporal checks

| Selection / test subset | Paired n | CPN − CP, F1 [95% CI] | CPN − CP, AP [95% CI] |
|---|---:|---:|---:|
| best_validation; days_8_9 | 5 | -6.89 [-14.26, +0.47] | -2.39 [-11.68, +6.90] |
| epoch_5; all | 5 | +12.11 [+0.34, +23.88] | +12.31 [-7.00, +31.62] |
| epoch_10; all | 5 | +5.24 [-13.22, +23.70] | +4.96 [-9.41, +19.33] |
| epoch_20; all | 5 | -0.46 [-27.58, +26.65] | +4.74 [-30.83, +40.32] |
| final; all | 5 | -5.05 [-21.43, +11.33] | -3.90 [-26.13, +18.33] |

These checks reuse the same models and dataset and are not independent replications. The final checkpoint can occur at different epochs under the shared validation-only stopping rule; fixed-checkpoint views address equal training duration.

**Within-benchmark robustness: primary_not_supported.** Primary F1/AP intervals positive, and F1/AP point contrasts positive on days 8–9, fixed epoch 20 and final epoch. This descriptive check does not change the primary endpoint or its decision. Sensitivity directions are descriptive, reuse the same data, and do not establish convergence, cross-dataset generalization or additional multiplicity-controlled discoveries.

## First-contact and repeat transfers

| Subset | Positive / total transfers | CPN − CP, F1 [95% CI] | CN − CP, F1 [95% CI] | CPN − CN, F1 [95% CI] |
|---|---:|---:|---:|---:|
| first_contact | 1,325 / 37,221 | +0.43 [-16.63, +17.49] | +7.62 [-8.09, +23.34] | -7.19 [-28.89, +14.51] |
| repeat | 286 / 826,679 | -5.17 [-10.74, +0.41] | +0.49 [-9.98, +10.95] | -5.65 [-16.62, +5.32] |

Stratum comparisons use the same seed intersections as the overall contrasts (CPN − CP (primary): n=5, CN − CP (secondary): n=5, CPN − CN (secondary): n=5).

Confusion counts, validation-selected thresholds and every seed value are retained in `summary.json`. These comparisons use each model’s validation-selected threshold, not a common alert budget; flags are transactions, not unique investigations. A gain can support transaction-level screening on these data; it does not by itself estimate investigation workload savings, prevented losses or performance on another bank.

## Training termination and scope

| Group / seed | Epochs | Stop reason | Selected epoch | At epoch cap? |
|---|---:|---|---:|---|
| cp / 15 | 30 | maximum_epochs | 21 | Yes |
| cp / 16 | 30 | maximum_epochs | 28 | Yes |
| cp / 17 | 30 | maximum_epochs | 21 | Yes |
| cp / 18 | 30 | maximum_epochs | 23 | Yes |
| cp / 19 | 30 | maximum_epochs | 29 | Yes |
| cpn / 15 | 22 | validation_ap_plateau | 12 | No |
| cpn / 16 | 23 | validation_ap_plateau | 13 | No |
| cpn / 17 | 29 | validation_ap_plateau | 19 | No |
| cpn / 18 | 22 | validation_ap_plateau | 12 | No |
| cpn / 19 | 30 | maximum_epochs | 25 | Yes |
| cn / 15 | 22 | validation_ap_plateau | 12 | No |
| cn / 16 | 30 | maximum_epochs | 28 | Yes |
| cn / 17 | 30 | maximum_epochs | 27 | Yes |
| cn / 18 | 28 | validation_ap_plateau | 18 | No |
| cn / 19 | 30 | maximum_epochs | 30 | Yes |

![Individual validation AP trajectories](figures/validation-trajectories.png)

**Figure 2.** Every run’s validation AP through its own stopping epoch. Lines describe individual seeds; different stopping times are not pooled into a changing-cohort mean.


9 of 15 runs reached the epoch cap. Neither reaching the cap nor satisfying validation patience proves mathematical convergence. An incomplete plateau record or continuing improvement prevents a convergence claim.

9 runs stopped at the cap without meeting validation patience; 5 selected their best checkpoint within the last five completed epochs. 6 selected a checkpoint before epoch 20. The minimum training duration does not force the validation-selected model to come from a late epoch; the fixed-epoch-20 and final evaluations address this distinction.

The primary inference describes 5 paired training-seed blocks, and each secondary contrast uses its declared intersection, on one previously inspected synthetic dataset. Intervals use Student t with n−1 degrees of freedom, conditional on this fixed dataset. They quantify seed variability, not uncertainty over future banks or datasets. It is not a new untouched test set, cross-bank replication, or online deployment evaluation. Graph evaluation remains transductive. Training-only normalization, shared count/port scaling and evaluation mode control implementation differences; they mean the new scores should not be pooled with the original protocol.

Each evaluated period’s graph can contain transactions later than an individual target transaction. Historical features alone do not turn this into an online causal prediction evaluation. Equal-timestamp transactions follow a reproducible ordering; earlier in that order is not the same as strictly earlier wall-clock time.

No outcome identifies failure to infer novelty inside the model; input effects are not a causal decomposition of internal computation.

## Precision planned before the new runs

The frozen design targets 80% power at two-sided α = 0.05 using a two-sided paired t with noncentral-t power test. The planning SD is 2.973 F1 points. Its source is Pilot CN-CP (replacement), not observed B-A variance; different protocol.

| Paired seed blocks | Planning minimum detectable F1 difference (points) |
|---:|---:|
| 5 | 5.000 |
| 10 | 2.961 |

| Assumed paired SD (F1 points) | Paired seed blocks | Planning detectable F1 difference (points) |
|---:|---:|---:|
| 2.000 | 5 | 3.364 |
| 2.000 | 10 | 1.992 |
| 3.000 | 5 | 5.046 |
| 3.000 | 10 | 2.988 |
| 4.000 | 5 | 6.728 |
| 4.000 | 10 | 3.984 |
| 5.000 | 5 | 8.410 |
| 5.000 | 10 | 4.980 |
| 6.000 | 5 | 10.092 |
| 6.000 | 10 | 5.976 |

Planning sensitivity, not guaranteed power or business materiality; primary F1 test only, not joint F1/AP success; no outcome-driven seed extensions. This budget revision uses5 seeds, so the planning detectable primary F1 difference is5.00 points, not2.96.
These are prospective sensitivity calculations, not achieved power calculated from the observed effect. The replacement pilot variance need not equal the addition-contrast variance. AP has a separate sampling variance; the planning F1 calculation does not guarantee the joint F1-and-AP support rule.

## Separate representation and drift checks

The [representation probe report](probes/PROBE_REPORT.md) examines recoverability of novelty, and the [data drift report](DRIFT_REPORT.md) describes temporal data differences. These are separately generated analyses. Their existence or outcome is not a completion condition for the main paired model experiment; read their own status before citing them as evidence.

## Integrity checks

All 15 runs passed protocol, common source, frozen-data, initialization, shared normalization, device and parameter-count checks. 74 unique score archives were checked against the prepared graph; 600 saved metric values were independently recomputed. Model selection was checked against the complete validation histories.

Prediction-file hashes and all machine-readable results are in `summary.json`. No significance-directed seed replacement, model selection or interval clipping is performed by this analyzer.
