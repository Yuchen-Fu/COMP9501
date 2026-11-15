# What Do Port Numbers Add? Counterparty Counts vs. Counterparty Identity in Multigraph GNNs for AML

_COMP9501 course project · IBM AML HI-Small · GIN · counts × ports · five seeds_

**Completed study:** [research report with conclusions and figures](RESEARCH_REPORT.md) · [all numerical results](results/summary.md) · [independent final audit](results/final-results-audit.md) · [download code and results](research-results.zip).

**AML business presentation:** [PowerPoint with speaker notes](presentation/AML_BUSINESS_SLIDES.pptx) · [PDF slides](presentation/AML_BUSINESS_SLIDES.pdf) · [browser presentation](presentation/AML_BUSINESS_SLIDES.html) · [slide overview](presentation/preview/contact-sheet.png) · [business narrative and script](AML_BUSINESS_PRESENTATION.md).

**Process status:** all 25 runs completed, all 125 saved epoch predictions audited, and the report and graphical presentation finished. See the [dated completion status](STATUS.md).

<!-- ABSTRACT -->
The proposed historical counts do not remove the port-numbering gain in this completed five-seed, five-epoch experiment. Ports improve F1 by **7.48 points [2.96, 12.00]** without counts and **14.91 [10.11, 19.71]** with counts. The explained share is **−99.35%, with 95% Fieller interval [−512.75%, +8.42%]**: no attenuation remains compatible, while substantial positive attenuation is excluded under this fixed-dataset statistical model. Exact amplification is not established. The supplementary Counts+novelty cell exceeds Counts+Ports by **9.42 points [5.73, 13.11]**. The result distinguishes marginal account counts from useful pair-history representation; it does not isolate a causal counterparty-identity effect.

## 1. Research question

On HI-Small, Egressy et al. report minority-class F1 of **28.70 ± 1.13** for GIN and **54.85 ± 0.89** for GIN with ports [1, Table 2]. Ports help distinguish repeated transfers involving one counterparty from transfers involving different counterparties. They also have a precise relationship with counts: on a counterparty's first contact, its zero-based port equals the number of distinct counterparties previously encountered. On subsequent transfers, that port remains its first-contact rank.

> How much of the port-numbering gain remains once the model receives each account's historical transfer counts and distinct-counterparty counts?

Let **B**, **C**, **P**, and **CP** denote mean test F1 across the five seeds for Base, Counts, Ports, and Counts+Ports. The primary estimand is

$$
\text{share explained by counts}
= 1 - \frac{CP-C}{P-B}.
$$

The numerator is the incremental port benefit after supplying counts; the denominator is the port benefit without counts. A share near 100% is consistent with a small residual benefit, while a share near 0% means a residual benefit comparable to the original gain. These are performance contrasts, not causal mediation estimates. A nonsignificant residual does not establish equivalence. If the denominator is uncertain or nonpositive, a stable share of a positive port gain is not identified; valid estimates are not clipped to 0–100%.

## 2. Data and integrity

The dataset is **IBM AML HI-Small**, a synthetic transaction dataset [2], downloaded from the specified [Hugging Face dataset](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans).

- Revision: `6412f57ab89c9c28633ce5e837eca4c9a35c5dbe`.
- Archive SHA-256: `4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080`.
- Accounts are identified by bank and account ID; transactions are directed edges.
- The 5,078,345 transactions involve 515,088 accounts and span September 1–18, 2022. The CSV does not supply a timezone.

Whole-day cut points minimize the maximum relative discrepancy from transaction shares 60/20/20 [3]. The resulting cuts are at days 6 and 8, where day 0 starts at the first transaction.

| Split or test subset | Transactions | Laundering | Prevalence |
|---|---:|---:|---:|
| All | 5,078,345 | 5,177 | 0.102% |
| Train, days 0–5 | 3,248,921 | 2,530 | 0.078% |
| Validation, days 6–7 | 965,524 | 1,036 | 0.107% |
| Test, days 8–17 | 863,900 | 1,611 | 0.186% |
| Test, days 8–9 | 862,792 | 956 | 0.111% |
| Test, days 10–17 | 1,108 | 655 | 59.116% |
| Test, first-contact transfers | 37,221 | 1,325 | 3.560% |
| Test, repeat transfers | 826,679 | 286 | 0.035% |
| Test, both endpoints are repeat-free | 2,349 | 23 | 0.979% |

The realized train/validation/test transaction shares are 64.0%/19.0%/17.0%. A repeat-free account has no repeated counterparty in the same direction anywhere in the observed graph; the account-level subset requires both endpoints to satisfy this condition. This is a descriptive subset, not an input feature.

**Verified integrity.** Independent full-data audits reproduced every endpoint, label, timestamp, received amount, currency code, and payment-format code from the raw CSV. Bank/account concatenation has zero identity collisions. Separate reconstructions found zero mismatches in all four counts, both ports, novelty, repeat-free flags, and the temporal split. The two inherited Base/Ports seed-0 prediction archives reproduce every logged epoch's test F1 exactly. Audit evidence is retained in the [data audit](results/data-audit.md), its [JSON output](results/data-audit.json), and the [raw CSV alignment audit](results/raw-alignment.md).

**Temporal-tail caveat.** Days 10–17 contain only 0.128% of test transactions but 40.7% of test laundering. Retrospectively flagging all transactions in that tail gives 655 true positives, 453 false positives, and 956 false negatives: **48.18% full-test F1**. This describes the test distribution; the rule was noticed after inspecting test data and is not a validation-selected competing detector. The full test period remains primary, with days 8–9 reported as a disclosed sensitivity.

## 3. Experimental design

Every cell uses the same GIN architecture, optimization settings, split, and training budget. Seeds are fixed at 0–4; each run completes five epochs.

| Cell | Base transaction features | Historical counts | Ports |
|---|:---:|:---:|:---:|
| Base | ✓ | | |
| Counts | ✓ | ✓ | |
| Ports | ✓ | | ✓ |
| Counts+Ports | ✓ | ✓ | ✓ |

These **20 runs are the primary factorial experiment**. Five additional Counts+novelty runs form a **supplementary analysis**. Training budget, seed count, features, and stopping do not change in response to interim performance.

### Features and common order

All transactions share one total order: timestamp first, then a fixed seed-0 random permutation to break same-minute ties. Counts and port assignment use this same order. It supplies a reproducible convention within a recorded minute, not evidence of the true transaction ordering.

| Feature group | Definition for transfer u → v |
|---|---|
| Base | Current transaction's elapsed timestamp, amount received, receiving-currency code, and payment-format code |
| Counts | Sender's number of earlier out-transfers and distinct receivers; receiver's number of earlier in-transfers and distinct senders |
| Ports | Incoming rank of u among v's senders and outgoing rank of v among u's receivers, assigned by first contact and retained on repeat transfers |
| Novelty, supplementary | 1 when no earlier u → v transfer exists; otherwise 0 |

History features use the prefix strictly before the target transaction. Port ranks are zero-based and local to the endpoint, not global account identifiers. On every first-contact transaction, each port equals its corresponding earlier distinct-counterparty count; on every repeat, it is strictly smaller. Both identities were checked over the full dataset.

Each cumulative graph's edge features are z-normalized separately. Currency and payment-format codes are supplied as numerical inputs. The account feature is a constant zero.

### Model, training, and scoring

The model has two GINE layers with hidden width 66, BatchNorm, and residual averaging. Its edge classifier combines the sender embedding, receiver embedding, and seed-edge embedding in a 198→50→25→2 MLP with dropout 0.1053.

Adam uses learning rate 0.0062133 and weighted cross-entropy with class weights approximately 1:6.275. Each batch contains 8,192 seed transactions, with 100 sampled neighbors per hop over two hops. These fixed settings have documented provenance in the published study and public model configuration [1, 3].

Training uses the train graph. Validation uses the train+validation graph; test uses the full graph. Every seed transaction is classified using its endpoint embeddings and own attributes, whether or not its edge was sampled for message passing. During scoring, dropout remains active and BatchNorm uses batch statistics. Neighbor sampling and scoring therefore contribute randomness alongside optimization.

The budget is **five epochs per run**, with no early stopping. After each epoch, the threshold maximizing laundering-class F1 on validation is applied unchanged to test. Primary model selection chooses the highest validation F1 among zero-based epochs 1–4, with the earliest epoch winning a tie; epoch 0 is excluded under the original rule. Test outcomes do not choose the epoch or threshold.

### Mechanism checks

First-contact versus repeat transfers and the proposal's repeat-free-account subset are reported with F1 and true/false-positive and false-negative counts. The account-level subset contains only 23 positive test examples, limiting precision.

Equality of ports and distinct counts holds **conditional on first-contact status**, which the Counts-only model is not given. Counts and ports together can reveal that status even to an edge-only classifier trained on all transactions. Neighboring repeated edges can additionally contribute rank information through message passing. A near-zero first-contact effect is therefore a hypothesis, not a mathematical guarantee.

The supplementary Counts+novelty cell makes new-counterparty status explicit. Counts+Ports minus Counts+novelty compares rank representation with an explicit novelty flag. It replaces features; it does not add ports to Counts+novelty. It therefore cannot isolate rank value conditional on explicit novelty or a pure causal identity component. Feature representation, scaling, and optimization can affect this comparison.

## 4. Analysis and uncertainty

The primary outcome is laundering-class F1 on the entire test period at each run's validation-selected epoch. Report all five seed values, cell means, seed spread, and these additive contrasts:

- Counts − Base.
- Ports − Base.
- Counts+Ports − Counts.
- The factorial interaction: (Counts+Ports − Counts) − (Ports − Base).

Cells are matched by seed. Each contrast has a two-sided 95% paired t interval with four degrees of freedom. The ratio uses a Fieller confidence set that retains covariance between its numerator and denominator. Unbounded or disjoint sets are reported as such; an uncertain denominator is not replaced by a misleading finite percentage.

These intervals describe seed variation **conditional on this dataset and protocol**, assuming independent seed blocks and approximate normality. Five blocks cannot establish that assumption reliably. Secondary intervals are exploratory and not multiplicity-adjusted. Any approximate detectable-effect figure describes sensitivity at the observed seed variability, not achieved power.

Supplementary contrasts are Counts+novelty − Counts and Counts+Ports − Counts+novelty. They are reported only after all five supplementary runs finish. The analysis checks complete run metadata and recomputes all per-epoch test F1 values from saved predictions before producing results.

**Selection transparency.** The [analysis protocol](results/analysis_protocol.md) was refined after the inherited Base/Ports seed-0 outputs and historical partial Counts/Counts+Ports summaries supplied in the project background were available, and before completing the remaining cells. This is a transparent completion study, not an outcome-blind preregistration. It preserves the original validation-selected epoch as primary. Final-epoch results, the days 8–9 slice, and final validation average precision are disclosed post-hoc sensitivities prompted by interim outputs and the test-tail inspection. They are not independent confirmatory replications.

Full-test average precision and F1 at a fixed 0.5 threshold are also reported. Saved binary test predictions permit subset F1 and confusion counts, but not subset average precision or alternative thresholds. Agreement in effect direction across metrics is directional consistency, not proof of significance or robustness.

## 5. Results

<!-- RESULTS -->
All **25 runs completed**: 20 in the primary factorial and five in the supplementary novelty analysis. The original validation-selected epoch remains primary.

| Cell | Primary test F1, mean ± SD |
|---|---:|
| base | 23.68 ± 3.38 |
| counts | 24.66 ± 3.80 |
| ports | 31.16 ± 4.63 |
| counts+ports | 39.57 ± 0.81 |
| counts+novelty | 48.99 ± 2.45 |

Ports − Base was **+7.48 [+2.96, +12.00]** F1 points; Counts+Ports − Counts was **+14.91 [+10.11, +19.71]** (means and 95% paired-seed t intervals).

**Share of the port gain explained by counts:** -99.4% (95% Fieller interval -512.7% to 8.4%).

| Selection / subset | Ports − Base [95% CI] | Counts+Ports − Counts [95% CI] |
|---|---:|---:|
| best_validation / all | +7.48 [+2.96, +12.00] | +14.91 [+10.11, +19.71] |
| best_validation / days_8_9 | +4.24 [+2.89, +5.59] | +8.98 [+6.59, +11.37] |
| final / all | +6.04 [+2.01, +10.07] | +15.28 [+9.87, +20.69] |
| final / days_8_9 | +4.01 [+3.06, +4.97] | +9.10 [+6.44, +11.76] |

The disclosed sensitivity signs and intervals are reported in Results and the full analysis; agreement in direction is not independent confirmation.

Counts+novelty exceeds Counts+Ports by **9.42 [5.73, 13.11]** F1 points. On first-contact transfers it finds 224.6 more positives with only 0.2 additional false positives, averaged over seeds. The reverse contrast on repeat transfers favors Counts+Ports by 4.05 points, but its interval [−3.93, 12.03] includes zero. This substitution comparison does not isolate rank value after explicit novelty.

Complete seed values, AP diagnostics, strata, confusion counts and confidence sets: [full analysis](results/summary.md) and [machine-readable results](results/summary.json).

## 6. Discussion and conclusion

<!-- DISCUSSION -->
The completed results have the following interpretation limits:

- Strictly earlier history features do not make the complete procedure online-causal. Message passing and graph-specific normalization use the cumulative evaluation graph, including transactions later than a target.
- The five-epoch CPU budget is shorter than the public code's default of 100 epochs. The paper does not establish an exact 100-epoch budget for the quoted table; this study does not claim numerical replication.
- Validation-selected thresholds, the explicit same-minute tie order, and seed-edge scoring differ from the public comparison pipeline [3]. The published F1 values motivate the question; they are not a target the present results must match.
- Active dropout and sampled neighborhoods make evaluation stochastic. These settings remain fixed across all cells to preserve the experiment.
- A ratio of model-performance contrasts is not a proportion of an underlying causal mechanism. Weak evidence for the port gain can leave the requested share unidentified.
- The severe temporal tail and rare account-level stratum constrain interpretation. Sensitivity agreement cannot repair the lack of independent datasets.

<!-- CONCLUSION -->
**These four historical counts are not an adequate substitute for ports.** The residual port improvement is +14.91 F1 points [10.11, 19.71]; the explained-share interval permits at most 8.42% positive attenuation within the stated statistical model. Zero attenuation is compatible, and the primary interaction interval [−0.97, 15.83] does not establish amplification.

The supplementary result identifies a useful distinction: endpoint counts omit the history of the current sender–receiver pair, and making its novelty explicit is effective. Counts+novelty exceeds Counts+Ports overall and on the early test period; a repeat-specific rank advantage remains uncertain. The residual and novelty benefits also appear in AP sensitivities. Their interpretation is representation usefulness at this budget, not a causal decomposition into counts and identity.

These conclusions concern this dataset, split, five-epoch budget, and stochastic inference protocol. Twenty-three of 25 selected checkpoints are the final epoch, so convergence is unestablished. The [research report](RESEARCH_REPORT.md) gives the full logical argument, error analysis, uncertainty, provenance, and a focused next experiment.

## 7. Reproduce

Run from the repository root with Python 3.13, `uv`, `curl`, and `unzip` available:

```bash
bash setup.sh
EPOCHS=5 ./run_all.sh
.venv/bin/python -I src/analyze.py
```

Setup installs the pinned CPU dependencies, verifies the archive checksum, and builds `data/hi_small.pt`. The queue uses two workers with two threads each on four effective CPU cores. It skips existing run JSON files; preserve matching prediction archives and validate completed outputs before trusting a resumed experiment. Training has no epoch checkpoints, so an interrupted incomplete run restarts its five epochs. A log watcher only observes progress; its termination does not establish that training stopped.

To audit the saved experiment without training, run `.venv/bin/python -I scripts/audit_results.py`. Full-data checks are available as `scripts/audit_data.py` and `scripts/audit_raw_alignment.py` with the same interpreter. Figures can be regenerated with `python3 src/plot_results.py` in an interpreter with NumPy and Matplotlib; plotting dependencies are separate from the fixed training environment. The archive retains all 25 metric logs and prediction files plus console logs for the 23 runs executed here. It excludes the raw data, prepared graph, and virtual environment; setup downloads and rebuilds these.

| File | Role |
|---|---|
| `src/prepare.py` | CSV → graph, split, ordered histories, ports, counts, novelty, and strata |
| `src/train.py` | One cell and seed; per-epoch metrics and binary test predictions |
| `src/analyze.py` | Integrity checks, primary selection, paired contrasts, Fieller sets, and sensitivities |
| `src/plot_results.py`, `scripts/audit_*.py` | Reproduce figures and independent integrity checks |
| `results/runs/` | Completed per-run JSON logs and prediction archives |
| `results/summary.md`, `results/summary.json` | Complete-design analysis, generated after the required runs finish |
| `RESEARCH_REPORT.md` | Direct answer, factorial interpretation, mechanism checks, sensitivities, and limitations |

## References

1. Egressy, B., Blanuša, J., von Niederhäusern, L., Altman, E., Wattenhofer, R., and Atasu, K. *Provably Powerful Graph Neural Networks for Directed Multigraphs.* AAAI 2024. [Paper](https://arxiv.org/abs/2306.11586).
2. Altman, E., Blanuša, J., von Niederhäusern, L., Egressy, B., Anghel, A., and Atasu, K. *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models.* NeurIPS 2023, Datasets and Benchmarks. [Dataset used here](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans).
3. IBM/Multi-GNN, public code at [commit `252b025`](https://github.com/IBM/Multi-GNN/tree/252b0252afca109d1d216c411c59ff70753b25fc): [day-split objective](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/data_loading.py#L46), [fixed model settings](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/model_settings.json#L1), and [training defaults](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/util.py#L34).
