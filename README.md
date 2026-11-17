# Counts, ports and pair novelty in AML

This project studies what transaction-relationship features contribute to a GIN for anti-money-laundering detection. The original experiment asks whether account transfer counts and distinct-counterparty counts explain the gain from port ranks. A controlled follow-up asks whether explicitly adding pair novelty helps when counts and ports already make that fact derivable.

**Current follow-up result:** all 15 GPU runs and five representation probes completed. Adding novelty while retaining counts and ports gave a paired mean F1 difference of **−7.21 points [−15.46,+1.03]**, with AP **−4.49 [−19.11,+10.13]**. The prespecified decision is **inconclusive**: a positive addition benefit was not established, and neither harm nor equivalence is proved. The earlier replacement result cannot substitute for this addition comparison.

**Start here:** [详细结果、分析与文章修改方案（中文）](DETAILED_FOLLOWUP_REPORT.md). This full report explains the research question, each comparison, seed uncertainty, alert consequences, probe interpretation, limitations, and revised abstract/conclusion. The [slide-by-slide revision plan](presentation/representation-study/REVISION_PLAN.md) provides a 20-minute presentation structure with seven [Python-generated figures](results/representation_8h/detailed_figures/).

## Completed studies

| Study | Design and budget | Evidence |
|---|---|---|
| Historical factorial | Counts × ports, plus a supplementary Counts+Novelty cell; seeds 0–4; 25 runs × 5 epochs | [Research report](RESEARCH_REPORT.md), [numerical summary](results/summary.md), [original run outputs](results/runs/) |
| Controlled addition follow-up | A=Counts+Ports; B=A+Novelty; C=Counts+Novelty; seeds 15–19; 15 runs, 20–30 epochs | [Official report](results/representation_8h/FOLLOWUP_REPORT.md), [full-precision summary](results/representation_8h/summary.json), [primary analysis](results/representation_8h/analysis.json) |

The follow-up completed 416 epochs; nine runs reached the 30-epoch cap. Neither the cap nor validation patience proves convergence. The two studies use different preprocessing and evaluation protocols and must not be pooled.

## Latest results and provenance

- [Detailed follow-up analysis and research revisions](DETAILED_FOLLOWUP_REPORT.md), with [full-precision descriptive calculations](results/representation_8h/analysis_notes.json)
- [Interpretation with figures](results/representation_8h/reported/INTERPRETATION.md)
- [Representation probe report](results/representation_8h/probes/PROBE_REPORT.md)
- [Data history and drift report](results/representation_8h/DRIFT_REPORT.md)
- [Training records](results/representation_8h/runs/) and [logs](results/representation_8h/logs/)
- [Import notes and review scope](results/representation_8h/IMPORT_NOTES.md)
- [Original uploaded review ZIP](results/representation_8h/provenance/AML_EXPLICIT_PAIR_8H_REVIEW.zip)

The uploaded archive's 83 payload checksums, frozen protocol, runtime source hashes, seed inventory and primary paired calculations were checked. It contains reports, JSON, plots and logs, but excludes transaction-level probability archives and model checkpoints. Those remain on the university server; this import is not an independent prediction-level recomputation. One stale sentence saying “ten seeds” was corrected to “five,” with the original server report preserved.

At each model's validation-selected threshold, adding novelty increased mean true alerts from 693.6 to 794.8 and false alerts from 1,751.4 to 3,545.6. This is a transaction-level tradeoff, not a fixed-investigator-budget comparison. Probe decodability does not establish causal use by the AML output.

A post-hoc decomposition of saved confusion counts locates **81.6% of the net false-alert increase in repeated pairs**, while first contacts account for 94.5% of the net true-alert increase. In a separate temporal partition, days 8–9 account for 96.8% of the net false-alert increase. These are descriptive shares of net count changes, not new significance tests, alert-set overlap estimates, or causal mechanisms.

## Data and method

IBM AML HI-Small contains 5,078,345 transfers, 515,088 accounts and 5,177 laundering labels. Whole-day cut points 6 and 8 define train/validation/test periods. Historical counts and port ranks follow a fixed timestamp-plus-random-tie order. Novelty means a first observed directed pair within this dataset window, not necessarily a new banking relationship.

The follow-up uses shared train-only scaling for each port/distinct-count pair, matching input slots and initialization, evaluation-mode scoring, validation-AP model selection and validation-F1 thresholds. Its [frozen protocol](results/representation_8h/protocol.json) specifies the primary contrast and sensitivity checks. The graphs remain cumulative and transductive; this is not an online causal deployment evaluation.

## Code and execution

- Historical pilot: [preparation](src/prepare.py), [model and original trainer](src/train.py), [five-seed analysis](src/analyze.py), [figures](src/plot_results.py).
- Controlled follow-up: [trainer](src/representation_train.py), [analysis](src/representation_analyze.py), [probe](src/representation_probe.py), [data diagnostics](src/representation_diagnostics.py).
- Detailed reporting: [report_followup.py](src/report_followup.py) reads completed JSON records and generates seven PNG/PDF/SVG figures and descriptive decompositions. Run `python src/report_followup.py`; it does not train or add hypothesis tests.
- [Eight-hour server instructions](docs/portable/README_8H.md) and [delivery packages](downloads/README.md) retain the exact execution workflow. No new training is needed to read these completed results.
- The [ten-seed factorial proposal](docs/ten_seed_factorial_proposal.md) and its optional scripts are preserved as **unexecuted work**. They are separate from the completed GPU study. The earlier 25-run GPU plan is likewise not the executed 15-run protocol.

## Presentation and repository history

The [detailed presentation revision plan](presentation/representation-study/REVISION_PLAN.md) follows the controlled addition result: 14 main slides and four backup slides, with complete claims, supporting evidence, captions and speaking guidance. Existing [representation-study slides](presentation/representation-study/README.md) and [pilot speaking notes](PRESENTATION_NOTES.md) are historical pilot material; the binary deck has not been rebuilt for this follow-up.

All development lines and the supplied results are integrated on **main**, verified as the default and only remote branch on 17 November 2026. The [integration record](docs/repository-integration-2026-11-17.md) explains how presentation changes, statistical code, original evidence and unexecuted plans were preserved. Legacy coursework and audit artifacts remain available in this repository and its commit history.

## References

1. Egressy et al. *Provably Powerful Graph Neural Networks for Directed Multigraphs*. AAAI 2024. https://arxiv.org/abs/2306.11586
2. Altman et al. *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models*. NeurIPS 2023 Datasets and Benchmarks. [Dataset mirror](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans).
3. [IBM/Multi-GNN](https://github.com/IBM/Multi-GNN), for prior model conventions and hyperparameters.
