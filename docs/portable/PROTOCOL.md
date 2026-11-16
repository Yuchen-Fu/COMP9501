# Does explicit pair novelty improve AML prediction when it is already derivable?

Status: prospective follow-up protocol, fixed before any production run of this study. The same synthetic HI-Small dataset has already been examined in the earlier five-epoch study. Fresh training seeds do not make this a new, untouched dataset. The machine-readable protocol is authoritative for the numerical settings.

## Motivation and contribution

AML investigators must distinguish concentration of transfers, repeated counterparties and genuinely different transaction patterns while managing false alerts. A transaction representation can contain enough information to identify a pattern without the AML training objective learning to use that information effectively. This study tests whether explicitly representing an already available relationship predicate changes predictive performance.

Egressy et al. introduce graph adaptations including port ranks to distinguish multigraph structures; their HI-Small GIN result motivates examining the representation. Their discussion already includes distinct-neighbor counting. Altman et al. provide the synthetic AML benchmark. This study does not propose a new GNN architecture, rediscover counting, or claim a literal replication of the published 28.7/54.9 F1 scores. Its contribution is the controlled **addition comparison**, with an explicit relation feature, matched input capacity and a frozen evaluation protocol.

The earlier five-epoch result compared Counts + Novelty with Counts + Ports. That replacement improved mean test F1 by 9.42 points, but simultaneously removed ports and added novelty. It cannot isolate the effect of adding the flag while retaining ports. It also used a different normalization, scoring and selection protocol. The follow-up addresses that identification gap.

## Data and feature definitions

HI-Small has 5,078,345 directed transfers between 515,088 accounts. Day-based cut points 6 and 8 give training days 0–5, validation days 6–7 and test days 8–17. Counts describe the sender's earlier outgoing transfers/distinct receivers and the receiver's earlier incoming transfers/distinct senders.

Transfers follow one fixed total order: timestamp, then a label-independent random permutation for equal timestamps. “Earlier” refers to this order; the dataset does not reveal physical ordering inside the same minute. A port is a zero-based counterparty rank in first-observed order. Novelty is one exactly when that directed sender–receiver pair has no earlier transfer in this observation window.

For the sender, let d be the previous distinct receiver count and p the current receiver's port rank. Always p ≤ d. A new pair has p=d; a repeated pair has p≤d−1. Therefore novelty is equivalent to d−p<0.5, a **linearly separable deterministic predicate**. The corresponding receiver equality gives the same bit. It is not extra information or additional theoretical expressivity.

Neighborhood graphs contain the training period, training plus validation, or the full observed graph at the corresponding stage. Target-edge histories are causal in the chosen order, but message passing can see later transactions within each period. The study is an offline, transductive temporal evaluation, not an online causal alerting evaluation.

## Arms, scaling and randomness

All arms use the same two-layer GIN settings and eleven edge-input slots: four base features, four counts, two ports and one novelty slot. Unused slots are zero after scaling.

| Arm | Representation | Seeds |
|---|---|---|
| A (`cp`) | Base + Counts + Ports + zero novelty slot | 5–14 |
| B (`cpn`) | Base + Counts + Ports + Novelty | 5–14 |
| C (`cn`) | Base + Counts + zero port slots + Novelty | 5–9 |

C is mandatory. Its two comparisons use only seeds 5–9; the main B−A comparison uses ten pairs. Paired initialization and epoch/sampler RNG schedules are shared across arms. The matched dimension controls parameter count, while activating an input necessarily changes the optimization problem; this is the intended treatment.

Training transfers alone determine all affine transformations. Each port column and its corresponding distinct-count column share one mean and sample standard deviation, fitted to their pooled training values with equal weight. This preserves literal equality in normalized inputs. Other columns have independent train-only means and sample standard deviations; constant columns use scale one. Novelty remains 0/1. No clipping, log transform or test refitting is performed. Shared scaling intentionally departs from the published encoding and applies to every follow-up arm.

The full graph is checked for raw and float32-normalized equality. The two-count difference remains separated by an affine threshold. Counts may drift outside training ranges, and novelty prevalence changes as history accumulates; these are quantified before training, without adapting the design.

## Training, model selection and stopping

All 25 runs use fixed hyperparameters, Adam, the original batch size 8,192 and two 100-neighbor sampling layers. The optimizer and encoder are the same in every arm. Scores use `model.eval()`, fixed split-specific sampling and preserved training RNG; BatchNorm and dropout cannot change during scoring.

Train at least 20 and at most 50 epochs. Reset the patience counter after validation AP exceeds its plateau reference by at least 0.001; otherwise increment it. At or after epoch 20, stop after ten stale epochs, or stop at epoch 50. This plateau rule is not a proof of optimization convergence.

The primary model is the checkpoint with the exact highest validation AP over all completed epochs; choose the earliest tie. It may be earlier than epoch 20. Independently select its decision threshold by maximum validation F1, taking the first maximizing threshold. No test scores select epochs or thresholds. Test scoring starts only after each run finishes training. Fixed checkpoints 5, 10, 20 and the final checkpoint are evaluated as prespecified sensitivities. Main contrasts are released only after all 25 runs pass integrity checks.

## Estimands and uncertainty

The primary estimand is the paired mean **F1(B)−F1(A)** at the validation-selected checkpoints. Report nominal two-sided 95% Student t intervals over ten seed differences (df=9). AP(B)−AP(A) corroborates the ranking change independently of a chosen threshold. “Supported” requires both intervals strictly above zero; a positive F1 result with inconclusive AP supports only the narrower F1 claim.

Secondary C−A and B−C contrasts use five shared seeds (df=4), with unadjusted intervals. C−A bridges the earlier replacement comparison under the new protocol; B−C measures the effect of retaining port ranks given novelty, not a pure counterparty-identity effect. Per-arm means based on different seed cohorts must not be subtracted as a paired estimate.

Intervals describe training variability conditional on this graph. Transactions are not treated as independent experimental replicates, and these intervals do not establish cross-bank or cross-dataset uncertainty. Report the actual seed differences, TP/FP, precision, recall and alert counts. F1-selected thresholds do not hold investigation workload fixed; no operational cost savings are claimed.

The separate descriptive robustness flag requires positive primary F1/AP intervals and positive B−A F1/AP point contrasts for (i) test days 8–9, (ii) fixed epoch 20 and (iii) final checkpoints. Sensitivity disagreement narrows the conclusion; it cannot change the primary endpoint. The late test tail and first-contact/repeat strata are reported transparently. No outcome-driven seed additions, extra training, arm removal or checkpoint switching is allowed.

## Prospective detectable effect

The earlier replacement contrast's five paired differences have SD 2.9726 F1 points. A noncentral-t calculation at two-sided alpha .05 and 80% power gives a minimum detectable difference of 5.00 points for five seeds or 2.96 for ten. The full inputs and assumptions are in `results/representation_followup/planning_power.json`; `scripts/representation/check_power.py` recomputes them.

| Assumed paired SD, F1 points | Detectable difference with 10 seeds |
|---:|---:|
| 2 | 1.99 |
| 3 | 2.99 |
| 4 | 3.98 |
| 5 | 4.98 |
| 6 | 5.98 |

The true B−A variance is unknown. The pilot involves a different contrast and protocol and has only five pairs; its normal-theory SD interval is approximately 1.78–8.54. These are planning sensitivities, not guaranteed or post-hoc achieved power. They apply to the primary F1 test, not the joint F1/AP criterion. A detectable difference is not a business minimum meaningful effect; no equivalence margin is assumed.

## Exploratory representation probe

For each A seed, freeze its validation-selected checkpoint and extract the 25-dimensional representation supplied to the last classification layer, in evaluation mode. Uniformly sample at most 100,000 training, 50,000 validation and 100,000 test transfers using prespecified seeds; sample membership is independent of labels. All probe controls within a seed use the same rows.

Fit a train-standardized L2 logistic classifier (C=1, lbfgs, at most 2,000 iterations) to predict novelty. Compare this representation probe with the same linear classifier on A's original inputs and an exact count–port equality oracle. Probe coefficients and scaling use training data only. Report AUROC, AP with the novelty-prevalence baseline, and balanced accuracy both at 0.5 and at a validation-selected threshold. Report nonconvergence rather than silently changing fitting budgets.

A successful probe shows linear decodability at one layer. It does not show causal use by the AML output or explain why the explicit feature helps. A weak probe does not prove the model lacks a nonlinear encoding. Probe results cannot alter the primary analysis, model selection or stopping rule.

## Interpretation before observing outcomes

| Outcome | Permitted conclusion |
|---|---|
| B−A positive with AP support and sensitivity agreement | Explicit novelty improves prediction with counts and ports retained, robust across these within-benchmark checks. |
| B−A positive but later-checkpoint or days 8–9 results disagree | The primary benefit is supported, but its stability is limited in the identified setting. |
| C−A positive; B−A inconclusive | The replacement finding can persist without establishing an isolated addition benefit. Removal of ports and optimization interactions remain possible explanations. |
| B−A interval includes zero | The study does not establish an addition benefit at this precision; it does not establish equivalence. |
| B−A negative | Adding novelty harms the primary metric under this protocol. |
| Runs hit the epoch cap or trajectories remain unsettled | Report unresolved training duration; do not claim convergence. |

No possible outcome here establishes that a learned network is incapable of deriving novelty. A second dataset would address a different generalization question and should be a separately frozen study, not selected after seeing favorable or unfavorable results here. This package does not claim or silently add that replication.

## References

1. Egressy et al. *Provably Powerful Graph Neural Networks for Directed Multigraphs*. AAAI 2024. https://arxiv.org/abs/2306.11586
2. Altman et al. *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models*. NeurIPS 2023 Datasets and Benchmarks. Data provenance is supplied separately.
3. IBM/Multi-GNN. https://github.com/IBM/Multi-GNN. Prior model conventions and fixed hyperparameters are credited; the addition experiment and its interpretation are the subject of this study.
