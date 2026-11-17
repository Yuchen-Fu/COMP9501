# Historical factorial extension proposal

Status: preserved from commit 7575a9c. No completed extension runs were supplied. This is separate from the completed 15-run GPU addition study and is not its protocol. The source branch’s proposal is retained below; preserving it does not validate or execute its sequential-testing procedure.

Optional source snapshots: `src/analyze_ten_seed.py` and `run_ten_seed_extension.sh`. The regular `run_all.sh` and `src/analyze.py` continue to describe the completed five-seed pilot.

### Extension to ten seeds: plan

Recorded on 16 November 2026, before the new runs started.

The five-seed analysis leaves one contrast open: whether the port gain is larger with counts than without (interaction +7.43, p = 0.070). Seeds 5–9 of the four factorial cells are added with the same code, prepared graph, package versions, and five-epoch budget, giving ten seeds per cell. Counts+novelty is not extended; its contrasts stay paired on seeds 0–4.

- **Test.** The interaction on all ten seeds, with the same paired t test on full-test F1 at the validation-selected epoch.
- **Threshold.** The difference counts as established only if p < 0.0294, the Pocock level for two looks.
- **Error rate.** The first look was tested at 0.05, not 0.0294. With no true difference, this two-step procedure gives a false positive in about 7.0% of simulated studies, against 5.0% for one planned test. The five new seeds are therefore also reported on their own.
- **Reporting.** Every factorial contrast is reported on all ten seeds whatever the outcome, and the five-seed results stay in the summary.

