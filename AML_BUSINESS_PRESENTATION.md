# Does AML monitoring need relationship memory?

## Start with the AML business problem

Anti-money laundering (AML) transaction monitoring must identify payments worth investigating among a much larger volume of legitimate activity. A useful detection feature should help distinguish those payments while making its effect on review volume visible. A higher model score alone does not establish better investigator productivity.

Accounts can have similar activity totals but different relationships. An account that has made twelve transfers to four counterparties may be paying an established partner or a first-observed recipient on its next transfer. The totals do not answer that second question. This study examines whether explicitly representing the current sender–receiver relationship adds useful information beyond those totals.

That is the business importance of the research: **what transaction history should a monitoring team preserve and validate?** It informs feature design and the next validation experiment. It does not estimate financial savings, replace KYC/customer due diligence, or establish that a particular model should be deployed.

Here, “identity” in the original research title means an endpoint-local counterparty rank. It is not a legal customer identity. “New” means first observed interaction in this direction within the dataset window, not necessarily a new customer or a genuinely new real-world relationship.

## Presentation plan

Designed for a mixed AML business and PhD course audience: **16 main slides, approximately 16–18 minutes**, followed by three technical appendices for questions. The first four slides introduce the business problem and the necessary concepts before presenting the research result.

The visual edition uses transaction-network diagrams, a relationship-history
timeline, daily data plots, a literature map, an experimental-design diagram,
effect plots with uncertainty, and transaction-outcome charts. The tables below
retain the exact figures for reference and speaking preparation; the slides
present these comparisons graphically.

| Part | Slides | Audience question | Presentation purpose |
|---|---:|---|---|
| Introduction | 1–4 | What decision does AML monitoring face, and what is relationship history? | Establish the business problem; define counts, novelty, and ports without assuming GNN knowledge. |
| Data | 5–6 | What do the transactions and labels represent? | Explain the synthetic network, imbalance, temporal split, and unusual test tail. |
| Literature and research gap | 7–8 | What is known, and what explanation is still untested? | Connect GIN, the AML dataset, and multigraph ports to the counts-substitution question. |
| Methodology | 9–10 | How can the explanation be tested fairly? | Explain the factorial, fixed settings, selection, paired uncertainty, and estimand. |
| Results and AML interpretation | 11–14 | What remains after counts, and how do the errors change? | Present effects, mechanism evidence, transaction flags, and sensitivities. |
| Business implications and conclusion | 15–16 | What should a monitoring team investigate next? | Locate actionable validation priorities and state the scope of the conclusion. |
| Technical appendices | 17–19 | How should the ratio, mechanism, and references be defended? | Preserve rigor without overloading the introduction. |

Suggested opening:

> “A monitoring team sees that an account has made twelve transfers to four counterparties. Is that enough context for its next payment? What if the recipient is one it has paid many times—or one it has never paid within the observed history? This study asks whether account-level counts capture the useful signal, or whether the model still benefits from memory of the current relationship.”

Use the opening as a question, then build the explanation. Introduce the negative explained-share estimate only after the audience understands the original and residual port gains. Put the full Fieller calculation in the appendix.

## Slide-by-slide content and speaker notes

### 1. Does AML monitoring need relationship memory?

**INTRODUCTION** — Anti-money laundering (AML): what port numbers add beyond account activity counts

- A transaction-monitoring study of account activity, counterparty history, and detection quality.
- IBM AML HI-Small • GIN • 25 completed runs

**Takeaway:** Business question: what history should a monitoring system preserve about the current sender–receiver relationship?

**Speaker notes.** Open with the business problem, before introducing graph neural networks. A payment-monitoring team sees many legitimate transfers and a small number of potentially illicit ones. It must decide which events deserve review. This project examines one information-design choice: are counts of an account’s activity sufficient, or should the model also know the history of the particular sender–receiver pair? The experiment concerns transaction classification in synthetic labelled data. It does not evaluate an entire AML programme or make a production deployment recommendation.

*Evidence / scope:* COMP9501 course project • Completed 14 November 2026

### 2. Every transaction flag competes for review capacity

**INTRODUCTION** — Detection quality has two sides: useful findings and unnecessary review.

- Transactions → model scores → prioritized flags for human review.
- Precision: among flagged transactions, how many carry a laundering label?
- Recall: among labelled laundering transactions, how many are found?
- F1 balances precision and recall; it does not measure financial return or staffing needs.

**Takeaway:** The research matters if better history features improve which transactions enter the review queue.

**Speaker notes.** Explain AML as anti-money-laundering monitoring: payments can be examined individually and in their wider transaction network. A model score is an input to an investigation process, not a legal determination. In this benchmark, a true positive is a flagged transaction with a synthetic laundering label; a false positive is a flagged transaction without that label. Business teams care about both missed activity and the demand placed on investigators. F1 is a useful research summary, but the same F1 can arise from different alert volumes. Later we therefore show the underlying transaction counts. A transaction flag is not necessarily a unique case, customer investigation, or suspicious activity report.

*Evidence / scope:* Business framing; outcome unit throughout the experiment is a transaction.

### 3. The same transfer count can describe different networks

**INTRODUCTION** — Six transfers to one counterparty and six transfers to six counterparties have different structure.

- Repeated relationship: many transfers connect the same two accounts.
- Fan-out: one account transfers to several different counterparties.
- Structure supplies context; neither pattern alone proves money laundering.

**Takeaway:** A monitoring model needs to distinguish volume, breadth, and relationship history.

**Speaker notes.** Use the two simple networks as an introductory example. A repeated customer–supplier relationship and a distribution across multiple recipients can have the same number of transfers. Distinct-counterparty counts separate these patterns, which makes them a plausible simple explanation for gains attributed to graph adaptations. However, even after we know how many counterparties an account has used, we may still not know whether the current recipient is one of them. Fan-in and fan-out are structural motifs discussed in the multigraph literature; this study does not estimate separate performance for each laundering typology. Do not label either illustrative network as inherently suspicious.

*Evidence / scope:* Illustrative networks, not labelled examples from the dataset. Motivation: Egressy et al. (2024).

### 4. Three different questions about transaction history

**INTRODUCTION** — The research separates account summaries from the history of the current pair.

| Representation | Question answered | Example |
|---|---|---|
| Counts | How much activity and how many partners? | 12 outgoing transfers; 4 distinct recipients |
| Novelty flag | Have these accounts interacted in this direction? | First observed sender → receiver transfer |
| Port numbers | Which local first-contact rank belongs to this partner? | The partner’s rank is retained on repeats |

**Takeaway:** “New counterparty” means first observed directed pair in this data window—not a new customer.

**Speaker notes.** Define a counterparty as the account on the other side of a transfer. The four count features summarize the sender’s outgoing history and the receiver’s incoming history. Ports are local numerical ranks assigned when a counterparty is first encountered and reused on later transfers. They are unrelated to network communication ports and are not KYC identities or globally unique customer IDs. An explicit novelty bit says whether this sender has previously transferred to this receiver in the observed history. This distinction is central: an account can be established while the relationship is first observed. Features are limited by the observation window; unobserved earlier relationships can look new.

*Evidence / scope:* Definitions follow the completed study; counts and novelty use strictly earlier transactions in the fixed order.

### 5. A labelled synthetic transaction network

**DATA** — IBM AML HI-Small provides controlled labels at a scale where manual inspection is impractical.

- **5.08 million** — directed transactions
- **515,088** — accounts
- **0.102%** — labelled laundering prevalence

- Nodes represent accounts; directed edges represent individual transfers.
- Repeated transfers between the same accounts are retained.
- 5,177 laundering-labelled transactions; these are simulator labels, not adjudicated bank cases.

**Takeaway:** The dataset enables a controlled feature experiment; it does not establish performance on a bank’s live population.

**Speaker notes.** Introduce the source before model details. We downloaded the specified IBM AML HI-Small dataset, pinned its revision, and verified the archive checksum. It has 5,078,345 transfers involving 515,088 accounts, with 5,177 laundering labels. Severe class imbalance means that predicting every transaction as legitimate would have high accuracy while detecting no laundering, which is why we focus on minority-class F1 and average precision. Accounts are identified by bank and account ID. The synthetic data offer labels for controlled comparisons, but do not substitute for an evaluation of real investigators’ dispositions or real customer harm. All endpoint, label, and historical-feature alignments were independently audited.

*Evidence / scope:* Altman et al. (2023); downloaded HI-Small revision 6412f57. Data audit: results/data-audit.md.

### 6. Time matters: the test period contains a sharp shift

**DATA** — Use earlier days to train, later days to validate and test.

| Period | Transactions | Laundering labels |
|---|---|---|
| Train: days 0–5 | 3,248,921 | 2,530 |
| Validation: days 6–7 | 965,524 | 1,036 |
| Test: days 8–17 | 863,900 | 1,611 |

- Whole-day cuts target 60/20/20; realized shares are 64% / 19% / 17%.
- Late test days 10–17: only 1,108 transfers, but 655 laundering labels.

**Takeaway:** 0.128% of test volume holds 40.7% of its positives: an aggregate score needs a time-slice check.

**Speaker notes.** Explain why temporal separation is relevant to monitoring: the model should be assessed on a later period rather than an arbitrary mixture of the same days. Whole-day boundaries prevent an exact 60/20/20 allocation. The late test tail is unusual: its prevalence is 59.12%, compared with 0.111% on test days 8–9. A retrospective rule flagging everything from day 10 would score 48.18 full-test F1. We do not present that rule as a deployable detector because it was noticed after inspecting test data. Instead, the full test remains primary and days 8–9 form a disclosed sensitivity. Temporal splitting alone does not make this a live chronological simulation: evaluation graph construction still uses the cumulative period.

*Evidence / scope:* Verified dataset counts; time-slice analysis is post hoc and does not replace the primary test period.

### 7. Prior work establishes capability; the explanation remains open

**LITERATURE REVIEW** — The literature motivates a mechanism test rather than a new leaderboard comparison.

| Study | What it establishes | Open question / scope limit |
|---|---|---|
| Xu et al., ICLR 2019 | GIN provides a principled neighborhood-aggregation architecture. | Which transaction-history representation helps this AML task? |
| Altman et al., NeurIPS 2023 | Synthetic financial transactions with laundering labels. | Whether findings transfer beyond the synthetic benchmark. |
| Egressy et al., AAAI 2024 | Multigraph ports raise HI-Small GIN F1: 28.70 → 54.85. | Whether historical counts account for the port gain. |

**Takeaway:** This study asks why a useful representation helps, and whether simpler information can substitute for it.

**Speaker notes.** Introduce a GNN in one sentence: it learns account representations by combining information from neighboring accounts and transactions. Xu et al. motivate the GIN architecture; their work is not an AML result. Altman et al. provide the labelled synthetic financial environment. Egressy et al. show that local port numbering improves a directed multigraph GNN on HI-Small and connect it to distinguishing repeated edges and distinct neighbors. The reported 28.70 to 54.85 result motivates our question, but our five-epoch protocol has scoring and ordering differences and is not a numerical replication. The gap is explanatory: a port may help partly because it exposes counts or relationship novelty, rather than because a model needs a richer counterparty-rank signal. We test that explanation directly.

*Evidence / scope:* Xu et al. (2019), arXiv:1810.00826; Altman et al. (2023); Egressy et al. (2024), Table 2.

### 8. Can account counts substitute for port numbering?

**RESEARCH QUESTION** — If ports mainly reveal “how many partners,” supplying that information should reduce their benefit.

- Primary question: how much port benefit remains once four historical counts are supplied?
- Mechanism question: does explicitly stating whether the current pair is new help?
- Business importance: decide what relationship history deserves further validation in monitoring features.

**Takeaway:** The target is an explanation of performance—not simply which model has the highest score.

**Speaker notes.** State the competing explanation clearly. A port on a first contact equals the number of distinct partners previously encountered at that endpoint. Perhaps much of its benefit can be replaced by basic account counters. If so, the additional gain from ports should shrink once those counters are available. The factorial design tests this attenuation, rather than comparing Counts alone with Ports alone. The supplementary novelty cell asks whether making current-pair membership explicit is a useful alternative representation. This is a feature-design question with operational relevance, but the experiment does not compare GNNs with rule systems or tabular models, so it cannot establish that a GNN is necessary.

*Evidence / scope:* Primary research question and supplementary mechanism check; no test-driven additions to training.

### 9. One controlled factorial, plus a mechanism check

**METHODOLOGY** — All cells share the graph model, data split, settings, and training budget.

- **5 seeds** — per cell
- **5 epochs** — per run
- **25 runs** — 20 primary + 5 supplementary

|  | Ports absent | Ports present |
|---|---|---|
| Counts absent | Base (B) | Ports (P) |
| Counts present | Counts (C) | Counts + Ports (CP) |

- Counts: sender’s outgoing transfers and distinct recipients; receiver’s incoming transfers and distinct senders.
- Supplementary cell: Counts + explicit pair novelty (CN).

**Takeaway:** Changing one feature group at a time separates the original port gain from the gain that survives counts.

**Speaker notes.** Explain the 2×2 visually before the equation. The four core cells have base transaction attributes in common: elapsed timestamp, received amount, receiving currency, and payment format. The count factors add four prefix-history values. The port factor adds incoming and outgoing first-contact ranks. Five paired random seeds are used across every cell, with fixed hyperparameters and five epochs. The fifth cell replaces ports with a novelty bit alongside counts. Counts, ports, and novelty use one total order: timestamp and a fixed random tie-break within a minute. Earlier means earlier in this convention, not a claimed true intraminute ordering. We completed all planned runs without extending the budget based on final results.

*Evidence / scope:* 20-run primary factorial + 5-run supplementary experiment. No new training for this presentation.

### 10. Measure the port benefit that remains after counts

**METHODOLOGY** — Choose thresholds and epochs on validation; assess the complete later test period.

- Original gain: D = F1(Ports) − F1(Base).
- Residual gain: N = F1(Counts + Ports) − F1(Counts).
- Share explained: S = 1 − mean(N) / mean(D).
- Five paired seeds: 95% t intervals for differences; Fieller interval for the ratio.

**Takeaway:** 100% explained means no residual gain; 0% means no attenuation; negative means a larger estimated residual gain.

**Speaker notes.** Explain the estimand in words first: if counts are the explanation, the additional benefit of ports should become smaller. Use a ratio of mean paired differences, not the average of seed-wise ratios. Each epoch’s decision threshold maximizes validation F1 and is then applied unchanged to test. Primary selection uses the best validation F1 among zero-based epochs 1–4, with earliest ties. No test outcome chooses the epoch or threshold. The intervals describe variation across five training/scoring seeds conditional on this dataset and protocol; they do not estimate uncertainty across banks. The ratio needs Fieller inference because denominator uncertainty matters. Final-epoch, early-test, and AP views are disclosed sensitivities. The analysis was refined with inherited interim results available, not preregistered outcome-blind.

*Evidence / scope:* Primary = validation-selected full-test minority F1. Secondary intervals are exploratory and unadjusted.

### 11. Ports retain a substantial benefit after counts

**RESULTS** — The proposed account counters do not remove the performance gain.

| Contrast | Mean F1-point gain | 95% interval |
|---|---:|---:|
| Without counts: P − B | 7.48 | [2.96, 12.00] |
| With counts: CP − C | 14.91 | [10.11, 19.71] |

- Both improvements are positive in all five seeds.
- The primary interaction is +7.43 [−0.97, 15.83]: amplification itself is not established.

**Takeaway:** Counts do not remove the port gain; statistical evidence for amplification remains inconclusive.

**Speaker notes.** Present the directly interpretable differences before the negative ratio. Ports add 7.48 F1 points without the counters, and 14.91 points after counters are supplied. Their respective paired intervals are [2.96,12.00] and [10.11,19.71]. The requested explained share is −99.35% with Fieller interval [−512.75%,+8.42%]. Under the stated model, large positive attenuation is incompatible with the results, whereas zero attenuation and substantial amplification remain possible. Do not say that ports have proven to become twice as valuable: the interaction interval includes zero. Counts alone shows an imprecise gain, but that does not mean counts are useless. This finding is about substitution within this five-epoch GIN experiment.

*Evidence / scope:* Means and 95% paired-seed intervals; fixed dataset and five-epoch protocol. Full ratio interpretation in Appendix A.

### 12. Making pair novelty explicit is effective at this budget

**MECHANISM** — A simple input says whether the current sender has previously paid this receiver.

- **39.57** — Counts + Ports: mean F1
- **48.99** — Counts + novelty: mean F1
- **+9.42** — CN − CP; 95% CI [5.73, 13.11]

- On first contacts, CN finds 224.6 more positives than CP with 0.2 more false positives, on average.
- Repeat-specific CP advantage over CN is uncertain: +4.05 F1 [−3.93, 12.03].

**Takeaway:** The useful distinction is account activity versus current-pair history; a pure identity effect remains unresolved.

**Speaker notes.** Connect the finding back to the introductory questions. The supplementary novelty representation outperforms counts plus ranks in every seed. Its advantage is concentrated among first-contact transactions. This does not mean every new relationship should trigger an alert: most first-contact transfers are legitimate even in this synthetic test set. Nor does it prove that ranks never help. CP versus CN replaces a rank representation with an explicit bit; it does not test adding ranks to a model that already has explicit novelty. A model may learn the explicit bit more easily than infer it from normalized counts and ranks in five epochs. Ports are local ranks, not global customer identities. Appendix B explains why the first-contact determinism argument does not imply a zero gain.

*Evidence / scope:* Supplementary feature comparison; model-specific validation thresholds; counts are means across five seeds.

### 13. Translate F1 into findings, misses, and transaction flags

**AML BUSINESS INTERPRETATION** — These are observed benchmark trade-offs at each model’s validation-selected threshold.

| Mean across seeds | Counts | Counts + Ports | Counts + novelty |
|---|---|---|---|
| Labelled positives found | 451.2 | 664.4 | 881.6 |
| False-positive flags | 1,561.4 | 1,078.4 | 1,102.4 |
| Labelled positives missed | 1,159.8 | 946.6 | 729.4 |
| Total transaction flags | 2,012.6 | 1,742.8 | 1,984.0 |

- CP versus C: 213.2 more positives found; 483.0 fewer false-positive flags.
- CN versus CP: 217.2 more positives found; 241.2 more total flags, including 24.0 more false positives.

**Takeaway:** Novelty improves detection here; lower investigator workload or financial savings have not been established.

**Speaker notes.** This is the main business translation. The whole test set contains 863,900 transfers and 1,611 labelled positives. Moving from counts to counts plus ports improves both detection and false positives at the selected thresholds. Moving from counts plus ports to explicit novelty finds still more positives, but increases the total number of flags. It would therefore be misleading to sell the novelty result as lower workload. All entries are arithmetic means across seeds; each actual run has integer counts. Different models have different validation-selected thresholds, so these are not comparisons at equal alert volume or false-positive rate. Real AML teams group transactions into cases, assign varying review effort, and use information outside this benchmark. We did not measure case yield, investigator hours, suspicious activity reporting, prevented loss, or return on investment.

*Evidence / scope:* Synthetic transaction outcomes—not unique cases, investigations, SARs, or a matched-capacity comparison.

### 14. The central differences persist outside the late tail

**ROBUSTNESS** — Temporal and ranking checks support the residual-port and novelty findings.

| Outcome | Ports − Base | CP − C | CN − CP |
|---|---|---|---|
| Primary full-test F1 | +7.48 [2.96, 12.00] | +14.91 [10.11, 19.71] | +9.42 [5.73, 13.11] |
| Early-test days 8–9 F1 | +4.24 [2.89, 5.59] | +8.98 [6.59, 11.37] | +9.21 [6.96, 11.46] |
| Final validation AP | +8.18 [5.00, 11.37] | +10.96 [6.14, 15.78] | +11.01 [4.37, 17.65] |

- Early-period results show that the effects do not rely solely on the small high-prevalence tail.
- Average precision assesses ranking across thresholds; it is a different metric from F1.

**Takeaway:** The evidence supports a feature-validation priority, with remaining uncertainty about convergence and production transfer.

**Speaker notes.** Do not claim three independent confirmations: these views reuse the same models and dataset, and the additional checks were motivated by interim results and the tail. The early-test comparison removes the unusual late-period transactions. Final validation AP concerns a period without that test tail and assesses ranking rather than one cutoff, although validation has also informed model selection. The residual and novelty advantages have positive intervals in these views. Counterevidence remains important: the original port gain on final test AP has an interval crossing zero, and at a fixed 0.5 threshold the primary residual-gain interval also crosses zero. The conclusion applies to the specified validation-calibrated protocol, not every possible threshold.

*Evidence / scope:* 95% paired intervals; F1/AP percentage points. Sensitivities are post hoc, correlated, and unadjusted.

### 15. Use the evidence to set the next validation priorities

**BUSINESS IMPLICATIONS AND LIMITS** — Three practical decisions follow; deployment effectiveness still needs a different evaluation.

| Priority | Why it matters | Next evidence required |
|---|---|---|
| Preserve pair-history context | Counters did not substitute for ports. | Compare counts, novelty, and ranks on prospective bank data. |
| Test explicit novelty as a candidate | Strong supplementary benefit at five epochs. | Adequate training; test CN+Ports versus CN. |
| Compare at review capacity | Better F1 can change total flag volume. | Precision/recall at fixed alert budgets; case-level yield and review effort. |

- Current limits: synthetic labels, five epochs, one dataset, and evaluation graphs containing later-period edges.
- A one-bit novelty input still needs reliable identities and historical directed-pair state.

**Takeaway:** This study guides feature design and validation; it does not select a production AML system.

**Speaker notes.** Locate the importance at the right decision level. A feature-engineering or model-risk team should not assume that aggregate counters preserve all useful relationship context. An explicit first-observed-pair feature deserves careful testing because it is effective here and has a clear meaning. But a simple model input does not guarantee inexpensive infrastructure: maintaining pair history requires identity resolution, an observation window, data completeness, and state storage. A production validation should construct features and message-passing neighborhoods only from information actually available at scoring time, normalize from training data, and evaluate later periods. Compare models at a common review capacity, then measure case-level outcomes if available. Training convergence is unestablished: 23 of 25 chosen checkpoints were the last epoch. None of these follow-up studies has been completed in this experiment.

*Evidence / scope:* Validation recommendations, not measured deployment benefits. No new experiment is implied.

### 16. These account counts do not replace relationship memory

**CONCLUSION** — The study answers an explanation question with a controlled completed experiment.

- Research answer: ports retain +14.91 F1 points after the specified counts; substantial attenuation is unsupported under this protocol.
- Mechanism refinement: explicit pair novelty performs strongly, while extra rank value after explicit novelty remains unresolved.
- AML importance: validate how monitoring represents relationships, then assess detection at realistic review capacity.

**Takeaway:** Keep the current pair’s history in the research question—not only how active each account has been.

**Speaker notes.** Close in the same vocabulary used at the beginning. We started with frequency, breadth, and the current relationship. The experiment shows that the specified frequency and breadth counts do not remove the value of ports. The novelty comparison points to a useful, explicit representation of current-pair history at this budget. That is the original contribution: testing and constraining an explanation, rather than simply repeating a published performance ranking. Keep the scope in the final spoken sentence: these are results on a synthetic dataset, with five-epoch GIN training and transductive scoring. They justify focused feature validation, not an identity-causation claim or immediate deployment. Direct the audience to the report, all five seed results, code, and audits.

*Evidence / scope:* Full report: RESEARCH_REPORT.md • Reproducible code, predictions, confidence intervals, and audits are retained.

### 17. Why the explained share is negative

**APPENDIX A** — A negative estimate describes a performance interaction—not negative information.

- **−99.35%** — estimated share explained
- **[−512.75%, +8.42%]** — 95% Fieller interval

- S = 1 − 14.91 / 7.48. The estimated residual gain is larger than the original gain.
- The interval allows zero attenuation and substantial amplification; it allows at most 8.42% positive attenuation.
- Interaction = +7.43 [−0.97, 15.83]: do not claim a statistically established doubling.

**Takeaway:** Counts do not explain away the gain in this protocol; the amount of amplification is imprecise.

**Speaker notes.** For a technical question, define D and N as mean seed contrasts and I=N−D. Then S=−I/D. The original port-gain interval is positive, so the Fieller set is bounded. Zero explained share corresponds to I=0 and remains compatible; complete explanation corresponds to N=0 and is excluded. The asymmetric interval contains useful information about attenuation even though amplification is very imprecise. Inference assumes independent seed blocks and approximately normal paired differences on one fixed dataset. These five seeds are not independent financial populations. Do not substitute the paper’s 26.15-point gain into our denominator, clip the estimate to 0–100%, or call the ratio a causal identity fraction.

*Evidence / scope:* Ratio of mean paired differences; nominal 95% Fieller confidence set with numerator–denominator covariance.

### 18. First-contact equality does not imply zero model benefit

**APPENDIX B** — The Counts-only model is not told that a transaction belongs to the first-contact group.

| Next transfer | Sender total/distinct; receiver total/distinct | Incoming/outgoing ports | Novelty |
|---|---|---|---|
| u → a | (2, 2; 1, 1) | (0, 0) | 0 |
| u → b | (2, 2; 1, 1) | (0, 1) | 0 |
| u → c | (2, 2; 1, 1) | (1, 2) | 1 |

- Earlier history: u→a, u→b, d→c. These are three alternative next transfers.
- Counts are identical; ports distinguish pair membership and first-contact rank.
- CP versus CN replaces one representation with another; CN+Ports versus CN would test extra rank value.

**Takeaway:** Conditioning evaluation on first contacts does not reveal that condition to a model trained on all transfers.

**Speaker notes.** This small counterexample clarifies the mechanism and prevents overclaiming. The raw count vector is identical for all three alternatives. A port equals its corresponding distinct count on a first contact and is lower on a repeat, so counts plus ports can reveal novelty. Equality holds conditional on group membership; it is not a global function of counts alone. A pooled predictor can therefore improve on first contacts when ports help it identify the group. Neighboring repeated edges create another route through which GNN messages can carry rank information. This example concerns the raw features, not an impossibility theorem for full graphs. The observed comparison with explicit novelty does not isolate rank after novelty; a future sixth cell would do so.

*Evidence / scope:* Illustrative raw-feature counterexample. Repeat-free-account test stratum has only 23 positives and near-zero detection.

### 19. Sources and reproducible evidence

**REFERENCES** — Prior work supplies context; the completed experiment supplies the conclusions.

- Xu et al. (2019). How Powerful are Graph Neural Networks? ICLR. arXiv:1810.00826.
- Altman et al. (2023). Realistic Synthetic Financial Transactions for Anti-Money Laundering Models. NeurIPS Datasets and Benchmarks.
- Egressy et al. (2024). Provably Powerful Graph Neural Networks for Directed Multigraphs. AAAI. arXiv:2306.11586.
- IBM/Multi-GNN: pinned commit 252b025; HI-Small dataset: pinned revision 6412f57.
- Local evidence: RESEARCH_REPORT.md; results/summary.json; data and numerical audits; all 25 run outputs.

**Takeaway:** All 25 runs completed; all 125 saved epoch predictions passed independent verification.

**Speaker notes.** Use this slide for source questions rather than reading it aloud. The GIN source concerns graph representation; the synthetic-data source concerns labels and simulation; the multigraph source motivates ports and provides published comparisons. Numerical differences, intervals, time-stratum facts, and operational count translations come from our verified experiment, not from those papers. Dataset: https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans . GIN: https://arxiv.org/abs/1810.00826 . Multigraph paper: https://arxiv.org/abs/2306.11586 . Reference code: https://github.com/IBM/Multi-GNN/tree/252b0252afca109d1d216c411c59ff70753b25fc . The numerical audit checked 2,638 quantities and 39,682 Fieller memberships. Audit consistency does not remove the stated design limits.

*Evidence / scope:* Research completed 14 November 2026. Sources and links are also provided in the accompanying Markdown speaker notes.

## Where the AML importance is located

| Decision | Evidence from this study | Appropriate business interpretation |
|---|---|---|
| Can aggregate activity counts replace the tested relationship representation? | Ports retain +14.91 F1 points [10.11, 19.71] after counts. | Do not assume that those counters preserve all useful current-pair context. |
| Is explicit novelty worth further validation? | Counts+novelty exceeds Counts+Ports by +9.42 points [5.73, 13.11]. | Include a first-observed-pair feature in the next controlled validation, alongside rank and count alternatives. |
| Does higher F1 mean a smaller review queue? | CN adds 217.2 true positives and 241.2 total flags relative to CP, including 24.0 additional false positives. | Inspect the detection/workload trade-off and compare at a common review capacity. |
| Can an aggregate benchmark result be trusted across time? | 0.128% of test transactions contain 40.7% of test positives. | Assess periods and relationship segments separately before drawing operational conclusions. |
| Is this deployment evidence? | Synthetic labels, five epochs, one graph, and transductive scoring. | Treat it as a feature-design finding and a validation priority; live effectiveness remains untested. |

The contribution is an **explanation test**: the proposed counts do not account for the port benefit under this protocol, and the novelty comparison refines the question toward pair history. It neither proves that counts are useless nor identifies a causal identity effect. A simple one-bit input also does not establish cheaper infrastructure: historical pair state and reliable account identification are still required.

## Delivery guidance

- Lead with the monitoring decision and the concrete account example; introduce GNNs after the audience understands why relationships matter.
- Define precision as the yield of transaction flags and recall as coverage of labelled laundering. F1 is their harmonic mean, not a financial objective.
- Present the 2×2 visually before showing the ratio. A comparison of Counts with Ports alone cannot establish how much port benefit counts explain.
- On results slides, distinguish F1 **percentage points** from relative percentages and distinguish confidence intervals from seed standard deviations.
- Explain that error counts use each model’s own validation-selected threshold. They do not measure performance at equal alert budgets or translate directly into case or staffing counts.
- Keep the synthetic-data, five-epoch, and evaluation-graph limits visible. Do not turn “explicit novelty performed better here” into “new relationships are suspicious” or “ranks are universally unnecessary.”
- End with a concrete next decision: test counts, explicit novelty, and ranks in an evaluation that respects information available at scoring time and compares models at realistic review capacity.

## Files and sources

- [Editable PowerPoint with speaker notes](presentation/AML_BUSINESS_SLIDES.pptx)
- [Slide PDF](presentation/AML_BUSINESS_SLIDES.pdf)
- [Browser presentation](presentation/AML_BUSINESS_SLIDES.html)
- [Slide content](presentation/slides.json) · [rebuild script](presentation/build_slides.py)
- [Full technical research report](RESEARCH_REPORT.md) · [complete results](results/summary.md) · [independent audit](results/final-results-audit.md)
- Xu et al. (2019), *How Powerful are Graph Neural Networks?* ICLR. [Paper](https://arxiv.org/abs/1810.00826).
- Altman et al. (2023), *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models.* NeurIPS Datasets and Benchmarks. [Dataset used here](https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans).
- Egressy et al. (2024), *Provably Powerful Graph Neural Networks for Directed Multigraphs.* AAAI. [Paper](https://arxiv.org/abs/2306.11586).
- IBM/Multi-GNN, [pinned reference code](https://github.com/IBM/Multi-GNN/tree/252b0252afca109d1d216c411c59ff70753b25fc).

All research estimates come from the completed experiment. The presentation introduces no new model runs, outcome selection, or production evaluation.
