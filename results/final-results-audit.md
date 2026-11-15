# Independent completed-results audit

Audit completed 2026-11-14T07:52:40.958578+00:00.

**PASS:** all 25 expected runs and all 125 saved epoch predictions were checked. 2,638 numerical comparisons passed; 39,682 independent Fieller membership comparisons passed (32 near-boundary numerical points excluded).

The audit did not import the production analyzer. Full-test F1 was recomputed with scikit-learn; subset F1 used 2TP/(positives+flags). Confidence intervals were reconstructed from the five paired differences. Ratio-set membership was checked by directly inverting the t test on N − (1−share)D, without solving the production quadratic.

## Primary five-seed results

| Cell | Mean F1 ± SD | Selected epochs | Five seed F1 values |
|---|---:|---|---|
| base | 23.681 ± 3.382 | [2, 4, 4, 4, 4] | 18.527, 23.609, 27.618, 23.133, 25.518 |
| counts | 24.662 ± 3.800 | [4, 4, 4, 4, 4] | 29.748, 27.273, 23.928, 21.558, 20.802 |
| ports | 31.160 ± 4.628 | [4, 4, 4, 4, 4] | 29.638, 29.474, 39.308, 27.712, 29.670 |
| counts+ports | 39.572 ± 0.812 | [4, 4, 4, 4, 3] | 40.276, 38.924, 38.738, 40.560, 39.359 |
| counts+novelty | 48.989 ± 2.452 | [4, 4, 4, 4, 4] | 50.178, 52.016, 49.742, 45.966, 47.045 |

| Contrast | Mean [95% CI], F1 points | Five paired differences |
|---|---:|---|
| count_gain | +0.981 [-7.182, +9.143] | +11.221, +3.664, -3.690, -1.575, -4.716 |
| port_gain | +7.479 [+2.959, +12.000] | +11.110, +5.865, +11.691, +4.579, +4.152 |
| ports_after_counts | +14.910 [+10.106, +19.714] | +10.529, +11.651, +14.810, +19.003, +18.557 |
| novelty_gain | +24.328 [+21.466, +27.190] | +20.430, +24.743, +25.814, +24.408, +26.244 |
| ports_beyond_novelty | -9.418 [-13.109, -5.727] | -9.901, -13.092, -11.003, -5.405, -7.686 |
| interaction | +7.431 [-0.969, +15.830] | -0.582, +5.786, +3.119, +14.424, +14.406 |

Primary share confidence-set record (fractions; null endpoints denote the corresponding infinity):

```json
{
  "status": "identified",
  "reason": "Bounded Fieller interval with a positive port-gain denominator.",
  "estimate": -0.9935304072015134,
  "confidence_set_type": "bounded",
  "ci95_set": [
    [
      -5.127467797913836,
      0.08424783871404062
    ]
  ],
  "numerator_mean": 14.91000160481516,
  "denominator_mean": 7.479194473760541,
  "denominator_ci95": [
    2.958860496406926,
    11.999528451114156
  ],
  "covariance_of_means": -1.7538377311477251
}
```

### Compatibility of the two endpoint explanations

- **0% share:** compatible with the nominal 95% set: **True**. This is the same paired test as the factorial interaction N−D=0.
- **100% share:** compatible with the nominal 95% set: **False**. This is the same paired test as the residual port gain N=0.
Both identities were checked against the reported Fieller set. Compatibility is not proof of equality or equivalence. If the port-gain denominator is uncertain, these contrast tests do not create a stable positive-gain percentage.

## Selection, temporal, and metric sensitivity

| Selection/view | Port gain | Ports after counts | Counts+Ports − Counts+novelty |
|---|---:|---:|---:|
| best_validation/all | +7.479 [+2.959, +12.000] | +14.910 [+10.106, +19.714] | -9.418 [-13.109, -5.727] |
| best_validation/days_8_9 | +4.238 [+2.890, +5.587] | +8.979 [+6.588, +11.371] | -9.209 [-11.462, -6.955] |
| best_validation/day_10_plus | +14.309 [-1.034, +29.652] | +25.503 [+8.318, +42.688] | -6.338 [-19.861, +7.186] |
| best_validation/first_contact | +5.007 [+0.160, +9.854] | +12.648 [+7.144, +18.151] | -11.398 [-15.258, -7.537] |
| best_validation/repeat | +6.278 [+0.821, +11.735] | +8.924 [+3.281, +14.568] | +4.050 [-3.925, +12.026] |
| best_validation/repeat_free_accounts | -2.803 [-7.105, +1.500] | -4.423 [-7.669, -1.178] | -0.840 [-9.698, +8.018] |
| best_validation/test_ap | +7.117 [+0.415, +13.819] | +17.635 [+12.732, +22.538] | -11.259 [-15.766, -6.753] |
| best_validation/val_ap | +7.641 [+4.628, +10.653] | +11.270 [+6.112, +16.428] | -10.698 [-17.891, -3.504] |
| best_validation/test_f1_argmax | +8.042 [-10.000, +26.083] | +6.778 [-13.934, +27.490] | -18.457 [-32.951, -3.964] |
| final/all | +6.041 [+2.011, +10.072] | +15.277 [+9.866, +20.687] | -9.051 [-13.187, -4.915] |
| final/days_8_9 | +4.013 [+3.056, +4.971] | +9.100 [+6.440, +11.761] | -9.088 [-11.555, -6.620] |
| final/day_10_plus | +9.505 [-3.951, +22.961] | +26.230 [+8.309, +44.150] | -5.611 [-19.731, +8.509] |
| final/first_contact | +3.021 [-1.993, +8.034] | +13.357 [+6.435, +20.279] | -10.688 [-15.477, -5.899] |
| final/repeat | +5.546 [+0.783, +10.309] | +9.009 [+3.297, +14.720] | +4.135 [-3.712, +11.982] |
| final/repeat_free_accounts | -2.375 [-7.149, +2.400] | -5.600 [-8.439, -2.760] | -2.017 [-9.675, +5.642] |
| final/test_ap | +5.682 [-2.111, +13.476] | +18.218 [+12.327, +24.108] | -10.677 [-16.206, -5.149] |
| final/val_ap | +8.183 [+4.999, +11.367] | +10.958 [+6.136, +15.781] | -11.009 [-17.648, -4.370] |
| final/test_f1_argmax | +8.042 [-10.000, +26.083] | +9.062 [-15.452, +33.576] | -16.173 [-31.983, -0.363] |

## What this verification establishes

- The effects come from the full planned experiment, with the original validation-only epoch selection and all five seeds retained.
- Artifact integrity and numerical correctness do not by themselves establish a causal mechanism, equivalence, or population-wide robustness.
- Confidence intervals are conditional on this single dataset and the fixed five-epoch stochastic-inference protocol. Five seed blocks provide limited precision and a weak basis for checking normality.
- AP and validation metrics were checked against every source log. They cannot be recomputed independently from saved binary test predictions; no probability scores were saved.
- The temporal and final-epoch views are disclosed post-hoc sensitivities. Same-direction estimates are not independent replications; sign reversals or wide intervals must remain visible.
- The supplementary rank contrast is a comparison of feature representations. First-contact target edges can receive information from repeated neighboring edges, so this does not isolate a pure causal identity component.

## Interpretation of the audited contrasts

Counts do not make ports redundant in this fixed experiment: the residual gain after counts is positive in every seed, and its interval excludes zero. The estimated explained share is negative because the residual gain exceeds the port gain without counts. This is an operational interaction between feature representations, not a negative causal mediation fraction. The primary interaction interval includes zero, so the primary analysis does not establish superadditivity. The Fieller set excludes complete explanation by counts but retains zero explanation; its upper endpoint permits at most 8.4% explained under this paired-seed model, while the wide negative endpoint leaves the size of complementarity poorly determined.

The supplementary novelty representation provides a more specific clue: Counts+novelty exceeds Counts+Ports by 9.42 F1 points [5.73, 13.11], with the same direction in all five seeds, days 8–9, and final-epoch validation AP. For first-contact transfers it gains 224.6 true positives with only 0.2 additional false positives on average across seeds. On repeated transfers it loses 7.4 true positives and adds 23.8 false positives. The repeat-specific Counts+Ports advantage, 4.05 F1 points [−3.93, 12.03], remains uncertain. These results support explicit novelty as an effective representation under the tested protocol; they do not establish that counterparty ranks are universally unnecessary.

Even a model using only target-edge features could gain from ports on first-contact transfers: comparing a current port with historical distinct counts can reveal that the transfer belongs to the first-contact group. Restricting the evaluation to that group does not supply its membership to a model trained on all transfers. Thus deterministic equality within a stratum does not by itself imply zero predictive benefit after pooled training. Neighbor messages provide an additional route. Counts+novelty addresses the local membership ambiguity, but its comparison with Counts+Ports still mixes representation, encounter order, and optimization effects. The original repeat-free-account stratum has only 23 positive transfers and almost no true detections, so it provides little direct evidence about identity.

Summary SHA-256: `dfd65b1ecd4f4a46ba3ff130fb636ce8b3da656b44dc96244389c584e8f8e2bc`.
