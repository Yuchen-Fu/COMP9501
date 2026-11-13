# What Do Port Numbers Add? Counterparty Counts vs. Counterparty Identity in Multigraph GNNs for AML

_COMP9501 course project (example) · IBM AML HI-Small · GIN from IBM/Multi-GNN · 2×2 factorial × 5 seeds_

<!-- RESULTS_TLDR -->

## 1. Motivation

On IBM AML HI-Small, adding multigraph **port numbering** to GIN raises minority-class F1 from 28.7 to 54.9
(Egressy et al., AAAI 2024): the largest gain from any single adaptation in that paper. The paper motivates ports as a way to tell
repeated transfers with one counterparty apart from transfers with different counterparties, which helps detect fan-in and fan-out.
But a port number also hands the model a simple scalar for free: **how many distinct counterparties the account has had so far**.
We test whether that scalar alone accounts for the gain.

## 2. Research question and predictions

> How much of the port-numbering gain remains once the model receives each account's historical transfer counts and
> distinct-counterparty counts?

Primary estimand (F1 in points, cell means over 5 seeds):

$$\text{share explained by counts} \;=\; 1-\frac{(\text{Counts+Ports})-\text{Counts}}{\text{Ports}-\text{Base}}$$

* **Counting hypothesis:** share ≈ 100% (ports add nothing once counts are present).
* **Identity hypothesis:** share ≈ 0% (counts reproduce none of the port gain).

**Mechanism check.** Let a transaction *u → v* be a **first contact** if no earlier *u → v* transaction exists. For a first contact,
the in-port equals the receiver's distinct-sender count, and the out-port equals the sender's distinct-receiver count. This holds
exactly, because ports and counts are computed in the same order (§4.1). For a repeat transaction the port is *strictly smaller*
than the distinct count, and it names the counterparty. So any identity effect, (Counts+Ports) − Counts, should be ≈ 0 on
first-contact transactions and appear only on repeat transactions.

## 3. Data

IBM AML **HI-Small** (Altman et al., NeurIPS 2023), from the Hugging Face mirror
[`eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans`](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans)
(revision `6412f57`, SHA-256 of the zip `4407435e…8e080`). Accounts (bank + account id) are nodes and transfers are directed edges.
The split is Multi-GNN's **day-based 60/20/20 temporal split**: it picks the day cut-points whose transaction shares are closest to 60/20/20.

| | transactions | laundering | rate |
|---|---:|---:|---:|
| all (18 days, 515,088 accounts) | 5,078,345 | 5,177 | 0.102% |
| train (days 0–5) | 3,248,921 (64.0%) | 2,530 | 0.078% |
| validation (days 6–7) | 965,524 (19.0%) | 1,036 | 0.107% |
| test (days 8–17) | 863,900 (17.0%) | 1,611 | 0.186% |
| test, first-contact | 37,221 | 1,276 | 3.43% |
| test, repeat | 826,679 | 335 | 0.041% |

Most test laundering (79%) is first-contact. The stricter account-level version of the mechanism stratum is "neither endpoint ever
repeats a counterparty". It is nearly empty (2,349 test transactions, 23 laundering), so the mechanism check uses the
transaction-level definition above.

## 4. Method

### 4.1 Features (`src/prepare.py`)

Every transaction gets one position in a **total order**: timestamp first, ties broken by row order in the raw file
(a stable sort, as in Multi-GNN's `format_kaggle_files.py`). For transaction *e = (u → v)*:

| feature | definition (transactions strictly earlier than *e* in the total order) |
|---|---|
| **in-port** | rank of *u* among *v*'s distinct senders, ordered by first contact (Multi-GNN `ports`) |
| **out-port** | rank of *v* among *u*'s distinct receivers, ordered by first contact |
| **counts** | sender: total out-transactions, distinct receivers · receiver: total in-transactions, distinct senders |

Multi-GNN orders each adjacency list with numpy's unstable quicksort on minute-resolution timestamps, so its tie order is
implementation-defined. Here ports and counts use the **same** deterministic order, which makes port = distinct count hold exactly on
first contacts. Checks:

* The vectorised ports match Multi-GNN's own `data_util.ports` on **100%** of the 268,756 transactions of a subgraph
  (accounts with id < 30,000).
* On the full data, port = distinct count on 100% of first-contact transactions and port < distinct count on 100% of repeats.

Ports and counts are appended as raw integers and z-normalised per graph object, the same way Multi-GNN treats ports.

### 4.2 Model and training (`src/train.py`)

GIN (`GINe` from Multi-GNN, no edge updates, no reverse message passing, no ego ids) with Multi-GNN's tuned hyper-parameters
(`model_settings.json["gin"]`): hidden 66, 2 GINE layers, Adam lr 0.00621, class-weighted cross-entropy (1, 6.275), read-out dropout 0.105,
batch 8,192 seed transactions, 2-hop neighbour sampling [100, 100] with `LinkNeighborLoader`. The three graphs follow Multi-GNN:
train = train edges, validation = train+validation edges, test = all edges. Seeds are the edges of the split being scored.
Edge features are the Multi-GNN base set (timestamp, amount received, received currency, payment format) plus the cell's extras.
Each run reports the test F1 at the epoch with the best validation F1.

### 4.3 Design and inference

2×2 factorial, counts (off/on) × ports (off/on), five seeds per cell, 20 runs, all with identical hyper-parameters and budget.
Uncertainty uses a hierarchical bootstrap: seeds are resampled within each cell, and test transactions are Poisson-resampled with
the same draw for all cells, so cells stay paired on the test set. The bootstrap has 4,000 draws and reports 95% percentile intervals
(`src/analyze.py`).

### 4.4 Deviations from the published protocol (and why)

<!-- DEVIATIONS -->

## 5. Results

<!-- RESULTS -->

## 6. Discussion

<!-- DISCUSSION -->

## 7. Reproduce

```bash
bash setup.sh                 # .venv (CPU torch 2.8 + PyG 2.6.1 + pyg-lib), downloads + checksums HI-Small, builds data/hi_small.pt (~40 s)
./run_all.sh                  # 20 runs, two 2-thread jobs at a time; EPOCHS=5 by default
.venv/bin/python src/analyze.py 5   # tables -> results/summary_E5.{md,json}
```

| file | role |
|---|---|
| `src/prepare.py` | raw CSV → formatted graph, temporal split, ports, counts, strata (`data/hi_small.pt`) |
| `src/train.py` | one run of one cell and seed; saves per-epoch validation/test F1 and per-epoch test predictions |
| `src/analyze.py` | best-validation selection, cell means, estimand, mechanism check, hierarchical bootstrap |
| `results/runs/` | per-run logs (`.json`) and test predictions (`.npz`) |

## References

* Egressy, Blanuša, von Niederhäusern, Altman, Wattenhofer, Atasu. *Provably Powerful Graph Neural Networks for Directed Multigraphs.* AAAI 2024.
* Altman, Blanuša, von Niederhäusern, Egressy, Anghel, Atasu. *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models.* NeurIPS 2023 (Datasets & Benchmarks).
* IBM/Multi-GNN, https://github.com/IBM/Multi-GNN (commit `252b0252`), Apache-2.0.
