# Model and training configuration

The shared hyperparameters were checked against all 25 original and all 15 follow-up JSON run records. The values describe the completed experiments.

| Setting | Value used |
|---|---|
| Architecture | Two-layer edge-feature GIN, implemented with GINEConv |
| Hidden width | 66 |
| Edge classifier | 198 → 50 → 25 → 2; ReLU and dropout |
| Classifier dropout | 0.10527690625126304 |
| Optimizer | Adam; default weight decay 0 |
| Learning rate | 0.006213266113989207 |
| Batch size | 8,192 target transfers |
| Two-hop neighbor sampling | [100, 100] |
| Loss | Weighted cross-entropy |
| Class weights, legitimate / laundering | 1.0000182882773443 / 6.275014431494497 |

The batch size refers to target transfers.

| Protocol choice | Original experiment | Controlled follow-up |
|---|---|---|
| Feature cells / runs | Five cells, 25 runs | Three cells, 15 runs |
| Seeds | 0–4 in each cell | 15–19 in each cell |
| Training budget | Five epochs | At least 20, at most 30 epochs |
| Stopping | Fixed budget | Patience 10; validation-AP progress threshold 0.001; maximum 30 epochs |
| Reported checkpoint | Maximum validation F1 among zero-based epochs 1–4 | Exact maximum validation AP; earliest tie |
| Decision threshold | Maximum validation F1 at the selected checkpoint | Maximum validation F1 at the selected checkpoint |
| Scaling | Separate normalization within each cumulative split graph | Train-only scaling, shared by each port/distinct-count pair |
| Scoring mode | Dropout and per-batch statistics remain active | Evaluation mode with fixed seed-specific sampling |
| Input layout | Dimensions vary with supplied features | Eleven matched slots; unused slots zeroed after scaling |
| Compute | CPU | RTX 3090; one GPU per training process, four concurrent GPUs in the batch workflow |

The follow-up runtime manifest records Python 3.12.16, PyTorch 2.8.0+cu126 and PyG 2.6.1. Per-run metadata identifies NVIDIA GeForce RTX 3090 GPUs with 25,296,044,032 bytes of available device memory (about 23.56 GiB). The submission requests 8 CPU cores and 64 GB RAM for the batch; these are requested resources, not measured peak usage. The original CPU model is not inferred from the current workspace.

HI-Small contains 5,078,345 transfers, 515,088 accounts and 5,177 laundering labels. Whole-day cut points six and eight yield training days 0–5, validation days 6–7 and test days 8–17. Both evaluations use cumulative transductive graphs. Epoch limits and validation patience do not establish convergence.

Sources: [original run record](../results/runs/base_s0.json), [follow-up run record](../results/representation_8h/runs/cp_s15.json), [original trainer](../src/train.py), [original analysis](../src/analyze.py), [follow-up trainer](../src/representation_train.py), [frozen protocol](../results/representation_8h/protocol.json), [runtime manifest](../results/representation_8h/batch_manifest.json), and [reproduction instructions](REPRODUCE.md).
