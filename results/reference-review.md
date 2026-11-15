# Research-method and reference check

This is a read-only check of the current experiment against the paper and the
public reference code. It does not establish the current study's results.
No training, preparation, configuration, or run-output files were changed.

## Sources checked

- Egressy et al., *Provably Powerful Graph Neural Networks for Directed
  Multigraphs*, AAAI 2024, [arXiv:2306.11586v3](https://arxiv.org/abs/2306.11586v3).
  The PDF, extracted text, and detailed paper check are retained in `reference/`.
- IBM/Multi-GNN, pinned public commit
  [`252b0252afca109d1d216c411c59ff70753b25fc`](https://github.com/IBM/Multi-GNN/tree/252b0252afca109d1d216c411c59ff70753b25fc).
  Relevant source files are retained in `reference/`; no new Git checkout was made.
- Current `src/train.py`, `src/prepare.py`, and `README.md` in `/workspace/COMP9501`.

## Verified reference facts

| Topic | Evidence and implication |
|---|---|
| Published motivation | Paper Table 2, PDF p. 7: Small HI minority-class F1 is **28.70 ± 1.13** for GIN and **54.85 ± 0.89** for GIN+Ports. Ports have the largest listed gain among individual adaptations. Appendix F.1, p. 14, describes final reporting over five random seeds. |
| Port definition | Paper §4.2, p. 4: ports are endpoint-local neighbor IDs/ranks, shared across parallel edges with that counterparty, assigned using earliest transaction times. Both incoming and outgoing ranks are supplied. They are not global account identifiers. |
| Chronological graphs | Paper Appendix E.1, p. 13, describes 60/20/20 chronological division and cumulative train, train+validation, and full-test graphs. |
| Exact day cuts | [`data_loading.py` lines 46–85](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/data_loading.py#L46) searches whole-day cut pairs and minimizes maximum relative error to 60/20/20. The current `day_split` uses this same objective. |
| Feature normalization | [`data_loading.py` lines 95–127](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/data_loading.py#L95) constructs cumulative graphs and normalizes each graph's edge features separately. This matches the current protocol; it is transductive normalization rather than training-only normalization. |
| Exact GIN settings | [`model_settings.json` lines 1–5](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/model_settings.json#L1) supplies learning rate 0.0062132661, hidden size rounded to 66, two layers, class weights 1.0000183 and 6.2750144, and final dropout 0.1052769. The current trainer uses these values. The GIN's separate `dropout` setting is unused by the reference GIN forward pass. |
| Architecture | [`models.py` lines 7–55](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/models.py#L7) uses GINE layers, BatchNorm, residual averaging, and a 198→50→25→2 edge/endpoint readout. The current architecture follows those choices without edge-update or reverse-message-passing adaptations. |
| Sampling and batch size | Paper Appendix F.4, p. 14, gives 100/100 neighbor sampling. [`util.py` lines 34–36](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/util.py#L34) defaults to batch size 8,192 and 100/100 sampling. |
| Evaluation mode | [`training.py` lines 12–65](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/training.py#L12) and [`train_util.py` lines 98–142](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/train_util.py#L98) do not call `model.eval()`. Thus the public code retains active dropout and batch statistics during scoring, as does this experiment. The paper's evaluation-mode statement concerns throughput timing and does not establish the scoring behavior. |

## Comparability limits that should remain explicit

1. **The paper does not state a 100-epoch AML budget.** The public code defaults
   to 100 epochs (`util.py:35`), but a default is not proof of the exact budget
   used for Table 2. Write “our five-epoch budget is shorter than the public
   code's default of 100,” not “the paper definitively trained every result for
   100 epochs.” The five-epoch study does not claim numerical replication.
2. **The decision rule differs.** Reference `evaluate_homo` uses `argmax`,
   whereas this study chooses an F1-maximizing threshold on validation and
   applies it unchanged to test. F1 at 0.5 and global AP are useful disclosed
   checks, but do not make the primary F1 numerically comparable to Table 2.
3. **The tie rule differs.** Reference [`data_util.py:31–44`](https://github.com/IBM/Multi-GNN/blob/252b0252afca109d1d216c411c59ff70753b25fc/data_util.py#L31)
   sorts timestamps using NumPy `argsort()` without requesting a stable sort.
   It does not guarantee file-order ties. This study deliberately uses one
   fixed random total order within timestamp ties. The paper does not specify
   the equal-timestamp rule. Neither protocol is evidence of the true ordering
   within a recorded minute.
4. **Seed-edge handling differs.** Reference `evaluate_homo` constructs a mask
   for seed edges present in the sampled edge set; its explicit missing-edge
   insertion is limited to named `Small_J`/`Small_Q` datasets. The current
   trainer explicitly classifies every seed edge using endpoint embeddings
   and its seed attributes, even if that edge was not sampled for message
   passing. This review did not quantify how often the reference masks omit
   edges on HI-Small. Do not call the two executable pipelines identical.
5. **Active dropout is a protocol choice, not an inferential guarantee.**
   Preserve it across all completed and new runs for comparability. Results
   include stochastic evaluation and neighbor sampling as well as optimization
   randomness. Turning dropout off mid-experiment would change the protocol.

These differences do not invalidate the internal fixed-hyperparameter
counts×ports comparison: each cell shares the same pipeline and budget.
They do restrict claims about reproducing published levels or isolating a
particular theoretical mechanism.

## Interpretation corrections for a direct research report

- A port equals the corresponding historical distinct-counterparty count on
  a **first contact** under the chosen order. On a repeat it is the rank of
  that counterparty's first contact, not the current distinct count. Replace
  the unconditional claim that “a port number gives the count so far” with
  this qualified relation.
- “Identity” means a locally consistent counterparty rank in this ablation,
  not a global account ID or an identified causal mediation effect.
- A target edge being first-contact does not make the two GNN inputs
  equivalent: messages may traverse neighboring repeat edges carrying
  different port ranks. The account-level nonrepeating stratum can still have
  informative multi-hop neighbors. A zero effect in these strata is a
  hypothesis, not a mathematical guarantee.
- Counts+Ports versus Counts+novelty is a supplementary comparison of rank
  information beyond an explicit novelty feature. It does not cleanly
  subtract a causal “identity component”: architecture, feature scaling, and
  optimization can affect how the signals are used. Keep the 2×2 factorial
  primary as requested.
- Prefix-history counts avoid using later edges to construct that edge's raw
  counts under the chosen order. The full procedure remains a transductive
  graph benchmark: message passing and normalization use the evaluation
  graph, potentially including transactions later than the target. Do not
  describe it as online-causal fraud detection.
- The estimand is a ratio of performance contrasts, not a proportion of a
  latent mechanism. Uncertain or nonpositive Ports−Base prevents interpreting
  a stable share of a positive gain. Values need not lie between 0% and 100%.

## Dataset claims needing direct evidence

The paper and reference code do not establish this repository's exact
same-minute rank statistics, percentage of changed port assignments, or
claimed 268,756-edge subgraph agreement. Retain such numbers only if their
reproduction is saved in an audit artifact. In particular, “11.9% of
laundering transactions have a changed port under random ties” would not mean
“11.9% leaked labels.” Label association and changed assignments are different
quantities.

Likewise, the day-10+ tail count and time-only F1 must come from the actual
downloaded graph. If the tail rule was selected after inspecting test labels,
report it as a retrospective dataset diagnostic, not a validation-selected
deployable competing model.

The final report should answer the question directly from the complete
fixed-design results, retaining these citations as motivation and method
provenance. The current review does not justify a positive, significant, or
robust result in advance.
