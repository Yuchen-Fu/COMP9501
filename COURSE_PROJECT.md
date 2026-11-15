# Integrated course project: what do port numbers add?

The two development branches now form one project. The completed study is in
[RESEARCH_REPORT.md](RESEARCH_REPORT.md), with its [25 run records](results/runs/),
[full analysis](results/summary.md), and [AML business slides](presentation/AML_BUSINESS_SLIDES.pdf).
The original course branch also contributes an optional 100-epoch implementation.
It is retained as a separate follow-up protocol; it did not generate the completed
study's results.

## Current scientific result

Historical transfer and distinct-counterparty counts do not remove the port gain
in the completed five-epoch experiment. Ports improve F1 by **7.48 points
[2.96, 12.00]** without counts and **14.91 [10.11, 19.71]** after counts. The
explained share is **−99.35%, with 95% Fieller interval [−512.75%, +8.42%]**.
This does not establish exact amplification. Counts+novelty exceeds Counts+Ports
by **9.42 points [5.73, 13.11]**, but this substitution comparison does not isolate
a causal identity effect or rank value after explicit novelty.

All 25 planned runs and 125 saved epoch predictions have been audited. Earlier
statements that the counts cells, seed variation, and archive verification were
missing described the two-run pilot, not the current project. The historical
course note is preserved in [commit 1637acc](https://github.com/Yuchen-Fu/COMP9501/blob/1637accdfe8d05fcf3b7a6d0d1043c1ba231a364/COURSE_PROJECT.md).

## One dataset, two explicitly different protocols

Both implementations use the checksum-verified HI-Small archive, the unchanged
feature builder, the same ordered count/port definitions, and the whole-day cuts
at days 6 and 8. Shared setup produces **`data/hi_small.pt`**. The legacy
`data/course-graph.pt` filename is no longer required.

| Choice | Completed study: canonical results | Optional course implementation |
|---|---|---|
| Entry point | `run_all.sh` / `src/train.py` | `src/factorial.py` |
| Full-data completion | 25/25 runs | No completed full-data runs |
| Budget and cells | Five epochs; four factorial cells plus novelty; five seeds | 100 epochs; four factorial cells; five seeds |
| Threshold | Maximizes validation F1 | Fixed probability > 0.5 |
| Epoch selection | Best validation F1 among zero-based epochs 1–4 | First best validation F1 among all 100 epochs |
| Scoring mode | Dropout active; BatchNorm uses batch statistics | `model.eval()`; dropout off and trained BatchNorm statistics |
| Seed-edge treatment | Every target scored directly from endpoint and seed-edge features | Reference GINe readout; sampled seed edges during training; missing target edges inserted for scoring |
| Test scoring | Logged after each epoch | Once at selected checkpoint |
| Repeat-free subgroup | Both endpoints never repeat a directed pair anywhere in the observed graph | Neither endpoint has participated in a repeat through the current transaction |
| Outputs | `results/runs/` and `results/summary.*` | `results/factorial/` and its `REPORT.md` |
| Report source | `src/analyze.py` | `src/factorial.py --report` |

These changes affect the experimental estimand and cannot be treated as harmless
implementation substitutions. Both protocols still use cumulative evaluation
graphs and graph-specific normalization; neither establishes online-causal
production performance. An as-of-transaction subgroup alone does not change that.

## Use the completed project

```bash
bash setup.sh
.venv/bin/python -I src/analyze.py
.venv/bin/python -I scripts/audit_results.py
```

These commands prepare the common environment and read the existing completed
results; they do not train models. `EPOCHS=5 ./run_all.sh` is the original training
queue if the completed protocol needs to be reproduced. Preserve paired JSON and
prediction archives together; existing valid completed runs are retained.

The pinned IBM model file used only by the optional implementation is downloaded
to `data/reference/models.py` and checksum-verified during shared setup. The
canonical trainer keeps its existing local model implementation.

## Optional follow-up implementation

The following command deliberately starts a **new 100-epoch experiment**, with a
substantial compute budget. It was not executed as part of branch integration:

```bash
OMP_NUM_THREADS=2 .venv/bin/python src/factorial.py --seed 0
```

The seed choices are 0–4. Without `--seed`, the runner schedules all four cells for
all five seeds. A `--data` argument can specify another compatible prepared-graph
path; the default is the shared `data/hi_small.pt`. Checkpoints support resumption
inside the separate `results/factorial/` directory. Results and checkpoints are
validated for the optional protocol before reuse.

To inspect completion and generate its own report when all 20 runs exist:

```bash
.venv/bin/python src/factorial.py --report
```

With no optional results this reports an incomplete optional design. Do not copy
the five-epoch JSON/NPZ files into this directory, and do not use optional results
as inputs to the completed study's analyzer. The protocols have different budgets,
scoring behavior, schemas, and subgroup definitions.

## References and integration evidence

- [Integration record](INTEGRATION.md): changes, checks, and preserved artifact provenance.
- Egressy et al., *Provably Powerful Graph Neural Networks for Directed Multigraphs*, AAAI 2024: [paper](https://arxiv.org/abs/2306.11586).
- Altman et al., *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models*, NeurIPS 2023: [dataset used](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans).
- [Pinned IBM model source](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/models.py).
