# What do port numbers add?

**COMP9501 · IBM AML HI-Small · Directed multigraph GIN**

## What the evidence currently supports

Egressy et al. report minority-class F1 of **28.70 ± 1.13** for GIN and **54.85 ± 0.89** for GIN with ports on HI-Small. The difference is **26.15 F1 points**. Their comparison establishes a gain from adding ports. Both historical degree and counterparty-specific information change together in that comparison. [Egressy et al., AAAI 2024, Table 2](https://ojs.aaai.org/index.php/AAAI/article/download/29069/30025)

The original course repository includes two five-epoch runs for seed 0. Using the repository's best-validation-epoch rule and validation-tuned threshold gives the following pilot results. Each epoch number below starts at one. [Original run records](https://github.com/Yuchen-Fu/COMP9501/tree/a5f660056fd54661dc7902133e6dd82c20a23bc9/results/runs)

| Original pilot | Selected epoch | Validation threshold | Test F1 ×100 | Test AP ×100 | Test F1 ×100 at 0.5 |
|---|---:|---:|---:|---:|---:|
| Base | 3 | 0.2512 | 18.53 | 11.39 | 0.00 |
| Ports | 5 | 0.3837 | 29.64 | 18.52 | 0.37 |

The pilot gain is 11.11 points at validation-tuned thresholds and only 0.37 points at the fixed threshold. The two count cells and seed variation are missing. **The share explained by counts is therefore unknown.** The new runner stores results separately. No full-data training result from this runner was available when this note was written.

## Experiment

An edge is a transfer from a sending bank–account pair to a receiving bank–account pair. The base inputs are timestamp, amount received, receiving currency and payment format. All four cells share the original course feature builder, the two-layer IBM GINe, its 66-dimensional hidden representation, the same optimizer, the same five seeds and the same evaluation rule. Self-transfers and parallel edges are retained. [IBM HI-Small mirror](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans) · [Multi-GNN implementation](https://github.com/IBM/Multi-GNN/tree/252b0252afca109d1d216c411c59ff70753b25fc)

| Cell | Added edge features |
|---|---|
| Base | None |
| Ports | Receiver's local rank for this sender and sender's local rank for this receiver |
| Counts | Sender's prior transfer count and distinct receivers, receiver's prior transfer count and distinct senders |
| Counts + ports | All six features above |

**Data and timing.** The inherited feature builder orders by minute, with a fixed seed-0 permutation within tied minutes. Counts exclude the current transfer. Port ranks begin at zero and use the same order. A same-minute predecessor is earlier in this declared order. Its wall-clock precedence is unknown. Label-independent tie breaking is an explicit course-project choice. The day split minimizes the maximum relative deviation from 60/20/20. The runner checks the following repository totals before training. [Original data preparation and audit](https://github.com/Yuchen-Fu/COMP9501/blob/a5f660056fd54661dc7902133e6dd82c20a23bc9/README.md)

| Split | Days, zero-based | Transfers | Laundering |
|---|---|---:|---:|
| Train | 0–5 | 3,248,921 | 2,530 |
| Validation | 6–7 | 965,524 | 1,036 |
| Test | 8–17 | 863,900 | 1,611 |

**Model selection.** Use the upstream CLI default of 100 epochs for all cells, batch size 8,192, two-hop sampling with up to 100 neighbors per hop and IBM's tuned Adam and weighted cross-entropy parameters. Select the first epoch with the highest validation minority F1 at the fixed argmax rule. Score the test set once per run. In this runner evaluation disables dropout and uses training BatchNorm statistics. The pinned IBM training loop leaves the module in training mode during evaluation. The shared, randomized tie rule and evaluation-mode choice make this a controlled benchmark comparison. Reproduction of the published scores must be judged empirically. The upstream split-wide graph and within-graph normalization also allow later activity within a split to influence embeddings. The conclusions apply to retrospective graph classification. [IBM training loop](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/training.py) · [IBM CLI defaults](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/util.py)

## What would answer the question?

Write the four mean test F1 scores as $B,P,C,CP$. The raw port gain is $G=P-B$. The remaining gain is $R=CP-C$. The requested share is $1-R/G$, computed from cell means. The report retains values outside 0–100%. It reports paired 95% t intervals for absolute effects across seeds and a Fieller interval for the share when the denominator is reliably positive. Five seeds describe training variability on one fixed test period. The analysis gives no guarantee of generalization to another bank, generator or period.

On the first transfer from $u$ to $v$, the sender assigns its next unused rank. That rank equals its count of distinct prior receivers. The same equality holds at the receiver. On a repeat transfer, each stored rank is strictly below the corresponding distinct count. This yields an exact, checkable identity on each target edge. The GNN also reads neighboring edges. A first-contact target can consequently benefit from ports elsewhere in its neighborhood.

The report estimates $R$ separately for first contacts, repeats and the requested subset in which neither endpoint has repeated any directed pair through the current transfer. It also reports the paired repeat-minus-first-contact contrast. A larger residual on repeats supports the proposed mechanism. On repeats the residual can include both the ability to detect that the pair is familiar and information about its local rank. A wide interval around zero leaves the mechanism unresolved. The original repository reports 1,325 first-contact and 286 repeat laundering transfers in test. Its 23-positive repeat-free group used the *entire* history, including future transfers. The new runner computes this group's support as of each target.

## Run in Codex Cloud

Start a new ChatGPT task under **Work in → Cloud**, select an environment with access to **Yuchen-Fu/COMP9501**, and check out **course/port-counts-factorial**. Use an x86-64 Linux CPU environment with `uv`, `curl`, `unzip` and internet access during setup for Hugging Face, GitHub raw files, the Python package indexes, the PyTorch and PyG wheels and Python 3.13 if needed. [Codex Cloud quickstart](https://developers.openai.com/codex/cloud/)

Run from the repository root.

```bash
bash setup.sh && OMP_NUM_THREADS=2 .venv/bin/python src/factorial.py
```

Setup downloads the pinned 91.1 MB archive first, verifies its SHA-256, extracts the CSV, installs the environment and builds the graph. The fingerprint is `4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080`. Full training on CPU is substantial. The saved pilots took about 7–9 minutes per epoch on their original host. At that rate 20 × 100 epochs is roughly 250 serial compute-hours before accounting for differences in code and hardware. Record the first epoch time in the cloud before estimating completion.

For separate seed jobs, run `.venv/bin/python src/factorial.py --seed 0` with seed IDs 0 through 4 in distinct workers. Retain the per-seed JSONs and collect them in the same `results/factorial/` directory. A partially completed cell resumes from its last epoch checkpoint in the same working directory. Use persistent copies of the checkpoints to resume across disposable instances. Run `.venv/bin/python src/factorial.py --report` after all 20 JSON files are present. The report is written to `results/factorial/REPORT.md`. Each JSON records the selected validation epoch, test average precision, stratum support and minority F1.

**Verification at handoff.** The published table, pinned dataset listing and both committed pilot logs were inspected. The feature builder was checked on 76 actual transactions from the dataset viewer against a sequential calculation of directed counts and ranks. Missing-seed-edge scoring order, the as-of-time subgroup and report arithmetic were checked locally. A desktop task could not reach the Codex Cloud service to obtain a cloud task ID. A separate GitHub Actions attempt ended before runner assignment. The full archive checksum and end-to-end GNN training still require execution in the cloud environment. [Dataset listing](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans/tree/main) · [Actions attempt](https://github.com/Yuchen-Fu/COMP9501/actions/runs/43463259003)

**Dataset reference.** Altman et al. (2023), *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models*, NeurIPS Datasets and Benchmarks. [IBM AML-Data](https://github.com/IBM/AML-Data)
