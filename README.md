# Counts, ports and pair history in AML

GIN experiments on IBM AML HI-Small: do ports still help after account-history counts, and does an explicit first-contact flag improve laundering detection?

## Results

| Comparison | Test F1 difference, points [95% CI] |
|---|---:|
| Add ports to Counts, original study | +14.91 [10.11, 19.71] |
| Add the first-contact flag to Counts, original study | +24.33 [21.47, 27.19] |
| Replace ports with the flag, retaining Counts, original study | +9.42 [5.73, 13.11] |
| Add the flag while retaining Counts + Ports, follow-up | −7.21 [−15.46, +1.03] |

In the original study, replacement raises first-contact laundering recall from 47.1% to 64.0%. The follow-up addition result is inconclusive. The studies use different protocols and are reported separately; intervals describe five paired seeds on one synthetic dataset.

## Files

- `src/`: data preparation, training, analysis and research plots.
- `results/`: original 25 runs, saved predictions and reports.
- `results/representation_8h/`: completed 15-run follow-up, protocol and probes.
- `scripts/`: dependency installation, data preparation and experiment launchers.
- `docs/`: configuration, data provenance and reproduction instructions.

`RESEARCH_REPORT.md` contains the original study. The follow-up report is `results/representation_8h/FOLLOWUP_REPORT.md`.

## Usage

```bash
bash scripts/install.sh cpu   # use cuda for the GPU follow-up
.venv/bin/python src/plot_results.py
```

Saved results can be read without training. Full reproduction commands are in `docs/REPRODUCE.md`. The raw dataset and model checkpoints are external; follow-up transaction-level probabilities are also not included.

References: Egressy et al., AAAI 2024; Altman et al., NeurIPS 2023; IBM/Multi-GNN.
