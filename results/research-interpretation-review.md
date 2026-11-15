# Independent interpretation review of the completed experiment

Reviewed on 14 November 2026 after all 25 runs completed. This review reads the complete results, per-seed contrasts and trajectories, analysis protocol, README, and research report. It evaluates the scientific interpretation; the separate [numerical audit](final-results-audit.md) checks computational correctness. No training, data, model, or analysis-selection settings were changed for this review.

## Direct answer

**Historical transfer and distinct-counterparty counts do not substantially attenuate the port benefit under this five-epoch HI-Small protocol.** Ports improve F1 by 7.48 points without counts and 14.91 points after counts. Their paired-seed 95% intervals are [2.96, 12.00] and [10.11, 19.71]. Both improvements occur in all five seeds.

The requested explained-share estimate is **−99.35%, with a 95% Fieller interval [−512.75%, +8.42%]**. The wide negative side means the amount of possible amplification is estimated poorly. The small positive upper endpoint is nevertheless informative: under the stated statistical model, the results are incompatible with counts removing most of the gain. They permit no attenuation and a small positive attenuation, as well as substantial amplification. The estimate is not a percentage of causal information or an “identity fraction.”

**The supplementary experiment identifies a useful alternative representation, not a pure identity mechanism.** Counts plus an explicit new-counterparty flag scores 48.99 F1, versus 39.57 for Counts+Ports. Its advantage is 9.42 points [5.73, 13.11] and occurs in every seed. This distinguishes marginal account history from pair-specific history: the former does not tell the model whether the current sender and receiver have interacted before. However, these runs cannot isolate the incremental value of counterparty rank once novelty is explicitly supplied.

These findings are a research contribution because they test and constrain a proposed explanation of a representation's benefit. The contribution does not depend on beating the cited paper's score.

## 1. What the primary factorial establishes

Let D = Ports − Base, N = Counts+Ports − Counts, and I = N − D. The proposed share is S = 1 − N/D = −I/D, using mean seed contrasts. The question therefore concerns attenuation of the incremental port benefit, not whether Counts happens to score near Ports.

| Contrast | Mean F1-point difference | 95% paired-seed interval | Interpretation |
|---|---:|---:|---|
| Counts − Base | +0.98 | [−7.18, +9.14] | Counts alone show no precise, stable gain. This does not prove they are useless. |
| Ports − Base, D | +7.48 | [+2.96, +12.00] | The experiment establishes a positive port gain under its inference assumptions. |
| Counts+Ports − Counts, N | +14.91 | [+10.11, +19.71] | A substantial port gain remains when counts are supplied. |
| Interaction, I | +7.43 | [−0.97, +15.83] | The point estimate suggests complementarity, but the primary interval does not establish amplification. |

The distinction between the last two rows is essential. Evidence that N is positive rejects complete redundancy of ports after counts in this pipeline. It does not imply evidence that N exceeds D. The interaction interval includes zero, and the share interval includes zero explained share; these agree. Conversely, the share interval excludes 100%, consistent with the positive interval for N.

The practical effect is not just a few threshold crossings: Counts+Ports detects 213.2 more laundering transactions and produces 483.0 fewer false alerts than Counts on average. These are descriptive differences at each model's own validation-selected threshold, not comparisons at a common alert budget or false-positive rate.

The Fieller estimate should not be clipped to 0–100%, replaced by a ratio using the published 28.70/54.85 scores, or summarized as an exact doubling. Its inference is conditional on five approximately normal seed contrasts. It does not estimate uncertainty across independent financial systems or future datasets.

## 2. The mechanism argument requires conditioning on novelty

The proposal's first-contact observation is algebraically correct but does not imply zero predictive benefit from ports in that stratum. Ports equal distinct counts **conditional on the target being a first contact**. A Counts-only model trained on the entire dataset is not told that condition. It can average new and repeated relationships having the same marginal counts; a Counts+Ports model can infer which case applies.

For example, suppose the earlier transfers, in order, are `u→a`, `u→b`, and `d→c`. Consider three alternative next transactions:

| Candidate | Sender total, distinct; receiver total, distinct | Incoming, outgoing port | New pair? |
|---|---|---|---:|
| u→a | (2, 2; 1, 1) | (0, 0) | 0 |
| u→b | (2, 2; 1, 1) | (0, 1) | 0 |
| u→c | (2, 2; 1, 1) | (1, 2) | 1 |

Counts discard both pair novelty and the encounter rank of an already-seen partner. This example concerns raw feature vectors, not an impossibility theorem about GNNs with access to the surrounding graph. Even an edge-only predictor could benefit from knowing novelty when evaluated on first contacts. Neighboring repeated edges provide a further route for a GNN to use rank information.

Ports are local first-contact ranks, not global account identifiers. With earlier distinct count d and repeat port r, d − r − 1 measures how many partners were first encountered after that partner. Encounter order, relationship history, novelty, and ease of learning can therefore contribute to a residual port benefit. Calling it a pure “identity effect” would overstate what the experiment distinguishes.

The appropriate conceptual comparison is **marginal endpoint summaries versus an explicit encoding of pair history**, with rank as a possible additional component. Strictly earlier features do not establish that the complete model is online causal: its message-passing graphs and graph-specific normalization use later evaluation-period transactions.

## 3. What the novelty cell contributes, and what remains unresolved

Counts+novelty minus Counts is +24.33 F1 points [21.47, 27.19]. Counts+Ports minus Counts+novelty is −9.42 [−13.11, −5.73]. These are strong representation comparisons at this budget, but the latter is a **substitution contrast**. It compares counts with ranks against counts with a novelty bit. It is not `(Counts+novelty+ports) − (Counts+novelty)`.

Raw counts and ports determine novelty, but an explicit bit may be easier to learn than an equality relation between normalized inputs. The CN advantage can therefore reflect finite training, scaling, optimization, or sampling as well as the informativeness of pair history. The algebraic decomposition `CP−C = (CN−C) + (CP−CN)` does not create causal novelty and identity components.

The subgroup results clarify the errors behind the aggregate scores:

| Subset | CP − C, F1 points [95% CI] | CP − CN, F1 points [95% CI] | Error-count interpretation |
|---|---:|---:|---|
| First contact; 1,325 positives | +12.65 [7.14, 18.15] | −11.40 [−15.26, −7.54] | CN detects 224.6 more positives than CP with only 0.2 more false positives on average. |
| Repeat; 286 positives | +8.92 [3.28, 14.57] | +4.05 [−3.93, 12.03] | CP versus C mainly suppresses false positives: 643.8 to 175.2; true positives increase from 33.4 to 40.6. |
| Both endpoints repeat-free; 23 positives | −4.42 [−7.67, −1.18] | −0.84 [−9.70, 8.02] | CP and CN detect only 0.4 positives on average, versus 1.4 for C. Broad mechanism claims would be unsupported. |

The observed CN advantage is concentrated on first-contact positives. A repeat-specific CP advantage over CN is directionally plausible but unresolved; its interval includes zero. This is not evidence that rank is useless on repeats, and the result does not establish equivalence. The repeat-free-account subset has too little successful detection to validate the proposed mechanism, despite one nominally negative interval. Its definition also uses whole-graph information, making it descriptive rather than a prediction-time feature.

Novelty's large prevalence association is not itself a sufficient explanation for a useful detector. The actual trained-model error comparisons, rather than the association alone, support the representation claim.

## 4. Temporal composition and scoring do not overturn the central result

Days 10–17 contain only 1,108 test transactions but 655 laundering examples: 40.7% of all test positives. A retrospective day-10 rule achieves 48.18 F1, so an aggregate score near 49 does not by itself establish useful transaction discrimination. The rule is a distribution diagnostic, not a prospectively validated competing detector.

The early test period provides evidence against an explanation relying only on this tail. On days 8–9, the validation-selected port gain is +4.24 [2.89, 5.59], the residual port gain is +8.98 [6.59, 11.37], and CN's advantage over CP is +9.21 [6.96, 11.46]. CN detects 117.6 more positives than CP and produces 53.4 fewer false positives on these days. The main direction therefore persists in the large, ordinary-prevalence part of test.

Final-epoch full-test F1 also retains the residual benefit: +15.28 [9.87, 20.69]. Final validation AP gives +10.96 [6.14, 15.78] for CP−C and +11.01 [4.37, 17.65] for CN−CP. AP supports a ranking advantage beyond one selected threshold. These checks reuse models and data; validation AP also uses the period involved in checkpoint selection. They are sensitivities, not independent replications.

Counterevidence remains visible. The original port gain on final test AP has interval [−2.11, 13.48]. At a fixed 0.5 threshold, primary-checkpoint CP−C is +6.78 [−13.93, 27.49], much less precise than validation-calibrated F1. Thus, it would be inaccurate to claim significance under every scoring rule. The supported conclusion concerns the specified validation-calibrated protocol, with corroborating AP results for the residual and novelty comparisons.

## 5. Limits on the strength of the conclusion

Twenty-three of 25 validation-selected checkpoints are the last epoch. The curves generally continue improving, so this experiment studies a fixed five-epoch computational budget, not converged performance. Explicit novelty may be advantageous because it is readily learned. No extrapolation to a longer budget is established.

Seed intervals account for training and stochastic-scoring variability on one fixed synthetic graph. Five seed blocks cannot reliably verify the approximate-normality assumption. Secondary and sensitivity intervals are nominal, exploratory, and not multiplicity-adjusted. Neither a precise conditional difference nor an agreement of signs establishes generalization across institutions or datasets.

The study is a transparent completion, not an outcome-blind preregistration. Two inherited Base/Ports seed-0 runs, historical partial Counts/Counts+Ports summaries supplied by the user, and the unusual-tail observations were available when the analysis was refined. Primary validation-based selection was preserved; no seeds or training duration were added in response to the final results. This history should remain explicit.

Binary prediction audits establish label/prediction alignment and F1 consistency. They cannot reconstruct AP rankings, alternative thresholds, or subset AP; those metrics need saved scores. Correct computation does not remove the finite-budget, inference-randomness, transductive-evaluation, or dataset-composition limitations.

## Review conclusion

The detailed [research report](../RESEARCH_REPORT.md) supports a logically coherent, substantive answer: **the proposed marginal counts do not remove the port benefit, while an explicit current-pair novelty feature is more effective than the numerical port representation at the tested budget.** The small positive upper endpoint of the share interval constrains the count-only explanation; its wide negative side prevents a precise amplification claim.

The report should retain the distinction between a representation result and a causal identity claim. The narrow unresolved question is whether ranks help after explicit novelty is present. A future, independently specified `Counts+novelty+ports` versus `Counts+novelty` comparison, with an adequate fixed training budget and repeat-positive sample, would test that question directly. It is a proposed follow-up, not missing work required to report the completed 25-run experiment honestly.
