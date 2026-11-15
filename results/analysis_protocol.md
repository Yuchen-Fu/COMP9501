# Fixed analysis protocol for the counts × ports study

This protocol was fixed after inspecting the two inherited Base/Ports seed-0
runs and before completing the remaining cells. Its primary epoch rule preserves
the original analysis. The additional sensitivities are post hoc and disclosed.

## Experiment and primary estimand

Use the checksum-verified IBM AML HI-Small graph, the day-based cut points at
days 6 and 8, fixed GIN hyperparameters, seeds 0–4, and exactly five epochs per
run. The primary 2×2 cells are Base, Counts, Ports, and Counts+Ports. Counts+
novelty is a five-seed supplementary cell. Do not change seeds, training budget,
features, inference behavior or stopping based on observed performance.

For each run, select the epoch with the maximum validation F1 among zero-based
epochs 1–4; break ties by selecting the earliest epoch. Use its threshold chosen
on validation and evaluate the entire test period. The primary estimand is

    share = 1 − mean_seed(F1_Counts+Ports − F1_Counts)
                  / mean_seed(F1_Ports − F1_Base).

Never select the epoch, threshold, seed, temporal subset, or reported metric by
its test performance. Require all four core cells and all five planned seeds,
with all five epochs and matching saved predictions, before reporting the main
experiment. Recompute every epoch's full-test F1 from labels and predictions.
Report supplementary effects only when all five novelty runs are complete;
otherwise mark that analysis incomplete.

## Seed inference

Match the four cells within seed blocks 0–4. Report all five paired differences,
means, standard deviations, and two-sided 95% t intervals with four degrees of
freedom. Core contrasts are Counts−Base, Ports−Base, Counts+Ports−Counts, and the
factorial interaction (Counts+Ports−Counts)−(Ports−Base). Supplementary contrasts
are Counts+novelty−Counts and Counts+Ports−Counts+novelty. These intervals describe
seed variability conditional on this single dataset, assuming independent seed
blocks and approximate normality; secondary intervals are exploratory and not
multiplicity adjusted. Failure to reject a residual difference does not establish
equivalence or prove that counts explain everything.

For the ratio, let N_s=F1_CP,s−F1_C,s and D_s=F1_P,s−F1_B,s. Preserve covariance
within seed blocks. With V_N, V_D and C_ND estimating the variance/covariance of
the means and t=t(.975,4), solve the Fieller inequality for r=N/D:

    A r² + B r + C <= 0,
    A = Dbar² − t² V_D,
    B = −2(Nbar Dbar − t² C_ND),
    C = Nbar² − t² V_N.

For A>0 the positive-discriminant solution is a bounded interval; zero
discriminant gives a singleton and negative discriminant an empty set. For A<0,
positive discriminant gives two rays; nonpositive discriminant gives the whole
real line. When A=0 solve the linear inequality; if B=0 it is all real for C<=0
and empty otherwise. Transform every interval [lo,hi] to [1−hi,1−lo] to obtain
the share confidence set, preserving unions and unbounded endpoints. JSON null
endpoints encode infinity with an explicit set type. Do not emit NaN/Infinity.

If the denominator interval includes zero, report the positive-gain share as
not identified; do not print a misleading finite percentage. Preserve the actual
Fieller topology (an empty degenerate set must not be called unbounded). A
negative denominator also has no interpretation as a share of a positive port
gain. Do not clamp valid shares to 0–100%.

An optional detectable-effect number is a descriptive sensitivity calculation:
(t(.975,4)+z(.8))*SD(paired differences)/sqrt(5). It is not achieved power.

## Sensitivities and interpretation

Keep the full test period primary. Show final-epoch results and days 8–9 alongside
it, transparently identified as additions prompted by the inherited seed-0
results. Show final validation AP, logged full-test AP, and F1 at 0.5. Same-sign
contrasts across these views are directional consistency, not independent
replication or statistical significance. Saved binary predictions cannot support
subset AP or alternative thresholds.

For first-contact, repeat and repeat-free-account strata, report prevalence,
F1 and TP/FP/FN by seed. Ports equal distinct counts on first-contact target
edges, but neighboring repeated edges can still transmit rank information.
Consequently these strata do not isolate a causal identity effect. Describe
Counts+Ports−Counts+novelty as incremental rank information beyond counts and
novelty. Strictly earlier features do not make transductive full-graph message
passing or graph-specific normalization online causal.

Verify per-day prevalence and the post-hoc day>=10 flag baseline directly from
the graph. Neither that baseline nor a selected temporal slice is a validated
detector. Five epochs cannot establish replication of the published performance
levels; the public reference code defaults to 100 epochs. The final conclusion must distinguish a bounded explanatory
share, evidence of residual improvement, and an inconclusive denominator;
significance is an outcome, never a condition for completing the study.

## Interpretation clarification, 14 November 2026, after completion

The experiment and numerical analysis above remain unchanged. The earlier phrase
“incremental rank information beyond counts and novelty” is too strong: CP−CN
substitutes port ranks for an explicit novelty bit; it does not compare C+N+P
against C+N. It is a representation comparison, not an isolated rank or identity
effect. Equality between ports and counts is conditional on first-contact status,
which a Counts-only model trained on all transactions is not given. This supplies
another reason, in addition to neighboring messages, that the first-contact
effect need not vanish.

For full provenance, historical partial Counts/Counts+Ports summaries in the
user-provided project background were also available when this protocol was
refined. It was not an outcome-blind preregistration. Primary selection, seed
count, training budget, contrasts, and all numerical results are unchanged.
