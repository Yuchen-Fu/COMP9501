# What Do Port Numbers Add? Counterparty Counts vs. Counterparty Identity in Multigraph GNNs for AML

_COMP9501 course project · IBM AML HI-Small · GIN · 2×2 factorial (counts × ports) × 5 seeds_

<!-- ABSTRACT -->

## 1. Motivation

On IBM AML HI-Small, adding multigraph **port numbering** to GIN raises minority-class F1 from 28.7 to 54.9
(Egressy et al., AAAI 2024). That is the largest gain from any single adaptation in that study. Ports are motivated as a way to
tell repeated transfers with one counterparty apart from transfers with different counterparties, which matters for
fan-in and fan-out detection. But a port number also hands the model a simple scalar: **how many distinct
counterparties the account has had so far**. This project tests whether that scalar alone accounts for the gain.

## 2. Research question and predictions

> How much of the port-numbering gain remains once the model receives each account's historical transfer counts and
> distinct-counterparty counts?

Primary estimand, on cell means of test F1 over five seeds:

$$\text{share explained by counts} \;=\; 1-\frac{(\text{Counts+Ports})-\text{Counts}}{\text{Ports}-\text{Base}}$$

* **Counting hypothesis:** share ≈ 100%. Once counts are given, ports add nothing.
* **Identity hypothesis:** share ≈ 0%. Counts reproduce none of the port gain.

**Mechanism check.** Call a transaction *u → v* a **first contact** if no earlier *u → v* transaction exists. For a first
contact, the in-port equals the receiver's distinct-sender count and the out-port equals the sender's distinct-receiver
count, exactly, because both are computed in the same order (§4.1). For a repeat transaction the port is *strictly
smaller* than the distinct count, and it identifies the counterparty. A genuine identity effect, (Counts+Ports) − Counts,
should therefore be small where the counterparty is new and appear where counterparties repeat.

## 3. Data

IBM AML **HI-Small** (Altman et al., NeurIPS 2023), from
[`eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans`](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans)
(revision `6412f57`, SHA-256 of the zip `4407435e…8e080`). Accounts (bank + account id) are nodes and transfers are
directed edges. The split is the **day-based 60/20/20 temporal split** of Egressy et al.: the two day cut points whose
transaction shares are closest to 60/20/20.

| | transactions | laundering | rate |
|---|---:|---:|---:|
| all (18 days, 515,088 accounts) | 5,078,345 | 5,177 | 0.102% |
| train (days 0–5) | 3,248,921 (64.0%) | 2,530 | 0.078% |
| validation (days 6–7) | 965,524 (19.0%) | 1,036 | 0.107% |
| test (days 8–17) | 863,900 (17.0%) | 1,611 | 0.186% |
| test, first contact | 37,221 | 1,325 | 3.56% |
| test, repeat | 826,679 | 286 | 0.035% |
| test, both accounts never repeat a counterparty | 2,349 | 23 | 0.98% |

82% of test laundering is first-contact. The account-level stratum in the proposal ("accounts that have never repeated a
counterparty") holds only 23 test laundering transactions. The mechanism check therefore uses the transaction-level
split (first contact vs repeat) and reports the account-level stratum as a secondary row.

## 4. Method

### 4.1 Edge features (`src/prepare.py`)

Every transaction gets one position in a **total order**: timestamp first, then a fixed random permutation (seed 0) to
break same-minute ties. Raw-file row order is not used for ties because it is label-correlated: within a sender's
same-minute group, laundering rows sit at mean relative position 0.895, against 0.362 for legitimate rows, which would
leak the label into "strictly earlier" counts. After the random tie-break the two values are 0.481 and 0.506.

For a transaction *e = (u → v)*, all features use only transactions strictly earlier than *e* in this order:

| feature | definition |
|---|---|
| base | timestamp, amount received, received currency, payment format |
| **ports** | in-port: rank of *u* among *v*'s distinct senders by first contact · out-port: rank of *v* among *u*'s distinct receivers by first contact |
| **counts** | sender: total out-transfers, distinct receivers · receiver: total in-transfers, distinct senders |
| novelty (supplementary) | 1 if no earlier *u → v* transaction, else 0 |

Checks:
* on the full data, port = distinct count on 100% of first-contact transactions, and port < distinct count on 100% of
  repeats;
* with file-order ties, the port numbers agree with the reference implementation of the published port numbering on
  all 268,756 transactions of a test subgraph (accounts with id < 30,000). On the full data, random ties change the
  ports of 6.8% of transactions (11.9% of laundering transactions).

Raw integer features are z-normalised within each graph: train, train+validation, all.

### 4.2 Model and training (`src/train.py`)

A GIN edge classifier with fixed hyper-parameters in every cell: the tuned HI-Small setting of Egressy et al.

* **Architecture:** two GINE layers (hidden 66) with BatchNorm and residual averaging. The read-out MLP (198 → 50 → 25 → 2,
  dropout 0.105) acts on [h_sender, h_receiver, edge embedding].
* **Optimisation:** Adam, learning rate 0.00621, class-weighted cross-entropy (1 : 6.275), 8,192 seed transactions per
  batch, 2-hop neighbour sampling with 100 neighbours per hop.
* **Graphs scored:** training uses the train graph; validation and test transactions are scored on the train+validation
  graph and the full graph respectively. BatchNorm uses batch statistics throughout.
* **Budget:** 5 epochs (≈2,000 updates) per run. The machine has 4 CPU cores and no GPU, and one epoch takes ≈ 8 min.
* **Decision rule:** after each epoch, the F1-maximising threshold on validation is applied unchanged to test. With 5
  epochs, scores rarely exceed 0.5 yet, so F1 at p > 0.5 is mostly 0 (§5).
* **Model selection:** the epoch with the best validation F1 (epochs 1–4).

### 4.3 Design and inference (`run_all.sh`, `src/analyze.py`)

* **Primary design:** 2×2 factorial, counts (off/on) × ports (off/on), five seeds per cell, all settings identical.
* **Supplementary cell:** Counts + novelty, five seeds. It splits the identity effect into "the counterparty is new"
  (novelty) and "which counterparty it is" (rank identity beyond novelty), because Counts+Ports can read novelty off
  port = distinct count while Counts alone cannot.
* **Metric:** test F1 on the laundering class, plus two checks: test average precision (threshold-free) and test F1
  at p > 0.5.
* **Uncertainty, two ways** (the wider one is the one to trust):
  1. a hierarchical bootstrap with 4,000 draws: seeds are resampled within each cell, and test transactions are
     Poisson-resampled with laundering transactions resampled as whole patterns (connected components of the test
     laundering subgraph); the same draw is used for every run, so cells stay paired on the test set;
  2. Welch t-intervals over the five per-seed F1 values.

## 5. Results

<!-- RESULTS -->

## 6. Discussion and limitations

<!-- DISCUSSION -->

## 7. Reproduce

```bash
bash setup.sh            # .venv (CPU torch 2.8, PyG 2.6.1, pyg-lib), downloads + checks HI-Small, builds data/hi_small.pt (~40 s)
./run_all.sh             # 25 runs (20 primary + 5 supplementary), two 2-thread jobs at a time, 5 epochs each (~9 h on 4 cores)
.venv/bin/python src/analyze.py   # -> results/summary.md, results/summary.json
```

| file | role |
|---|---|
| `src/prepare.py` | raw CSV → graph, temporal split, total order, ports, counts, novelty, strata (`data/hi_small.pt`) |
| `src/train.py` | one run of one cell and seed: per-epoch validation threshold, F1, AP; per-epoch test predictions |
| `src/analyze.py` | epoch selection, cell means, estimand, mechanism check, bootstrap and Welch intervals |
| `results/runs/` | per-run logs (`.json`) and test predictions (`.npz`) |

## References

* Egressy, B., Blanuša, J., von Niederhäusern, L., Altman, E., Wattenhofer, R., Atasu, K. *Provably Powerful Graph Neural Networks for Directed Multigraphs.* AAAI 2024.
* Altman, E., Blanuša, J., von Niederhäusern, L., Egressy, B., Anghel, A., Atasu, K. *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models.* NeurIPS 2023 (Datasets and Benchmarks).
* IBM/Multi-GNN, https://github.com/IBM/Multi-GNN (reference implementation of the above).
