# Presentation notes

Working notes for the talk "What do port numbers add?": the story, a 17-slide plan with what to
show and say, the numbers to quote, and the questions to expect. Numbers come from
[results/summary.md](results/summary.md). The full argument is in
[RESEARCH_REPORT.md](RESEARCH_REPORT.md).

The deck in `presentation/AML_BUSINESS_SLIDES.pptx` is an earlier 19-slide version of the same
material. It uses the same figures and numbers, and its speaker notes go further into each caveat.

## The talk in four steps

1. **Concept.** AML screening chooses which transfers a person reviews. In the data, accounts are
   nodes and transfers are arrows. A port number is an account's own label for each counterparty:
   0 for the first one it meets, 1 for the second, and the same number again whenever that
   counterparty comes back.
2. **Question.** When an account meets someone new, the port number equals the number of
   counterparties it has already seen. So the published gain from ports might be a count in
   disguise. If it is, the gain should shrink once the model is given the counts.
3. **Method.** One model, retrained with and without counts and with and without ports, so the
   port gain is measured twice under identical conditions. Five seeds, five epochs, and
   validation alone picks the threshold and the epoch.
4. **Significance.** The gain does not shrink (+7.48 F1 points without counts, +14.91 with them)
   and counts explain at most 8.4% of it. What ports add is relationship history: whether these
   two accounts have transacted before. One explicit bit for that does better than ports here.

In one sentence: port numbers are not counts in disguise; they carry whether a pair is new, and
saying that outright works better at this training budget.

## Running example

Use one example all the way through. Account A pays B, then C, then B again
(`presentation/figures/academic_feature_history.png`).

| Transfer | Earlier transfers by A | Earlier distinct receivers | Port of the receiver | New pair? |
|---|---:|---:|---:|---|
| A -> B | 0 | 0 | 0 | yes |
| A -> C | 1 | 1 | 1 | yes |
| A -> B | 2 | 2 | 0 | no |

Two things to read off it:

- On the new pairs the port equals the distinct count. That is why counts are a fair suspect.
- A pair is new exactly when the port equals the distinct count. Counts alone cannot show that,
  ports alone cannot either, and together they can. That is the mechanism behind the result.

A second example shows that counts alone cannot tell a new pair from a repeat
(`presentation/figures/academic_counterexample.png`). After the transfers u -> a, u -> b and
d -> c, the next transfer could be any of these three, and the four counts are identical:

| Next transfer | Counts (sender total, distinct; receiver total, distinct) | Ports (in, out) | New pair? |
|---|---|---|---|
| u -> a | 2, 2; 1, 1 | 0, 0 | no |
| u -> b | 2, 2; 1, 1 | 0, 1 | no |
| u -> c | 2, 2; 1, 1 | 1, 2 | yes |

## Slide plan

About one minute per slide. Each title states the slide's conclusion.

### 1. What do port numbers add?

- Show: title, the subtitle "Counterparty counts and relationship history in anti-money-laundering
  models", your name, course and date.
- Say: A monitoring team sees millions of ordinary transfers and a few illicit ones, and has to
  decide which to look at. This talk asks one question about the inputs to that decision. Is it
  enough to count an account's activity, or does the model need the history between this
  particular sender and receiver?

### 2. Anti-money laundering starts by choosing which transfers a person reviews.

- Show: a small network with accounts as circles and transfers as arrows, one first-time transfer
  highlighted. 5,078,345 transfers, 515,088 accounts, 5,177 labelled (0.102%).
- Say: An account is a node and a transfer is an arrow. Screening means sending a small number of
  those arrows to a person. A model score puts a transfer in the queue. It does not establish
  laundering.
- Careful: the labels come from a simulator, and a flag is a transaction, not a case.

### 3. Equal transfer counts can hide entirely different relationships.

- Show: two small networks (`academic_counterparty_breadth.png`).
- Say: Both accounts make four transfers. One pays the same supplier four times and the other
  pays four different recipients. Counting distinct counterparties tells these apart, which is
  why counts are a serious candidate. But even that count does not say whether today's recipient
  is one of those already seen.
- Careful: neither pattern is suspicious on its own.

### 4. A port number labels each counterparty in order of first contact.

- Show: the running example (`academic_feature_history.png`).
- Say: An account numbers its counterparties from zero in the order it first meets them and
  reuses the number on repeats. The counts go up every time. The port for B is 0 the first time
  and 0 again on the repeat. On the two new pairs the port equals the distinct count. On the
  repeat it is smaller.
- Careful: a port is a local rank. It is not a network port and not a customer ID. "New" means
  not seen earlier in this data window.

### 5. Published port gains could be counts in disguise.

- Show: two columns, the established reading against this study.
- Say: Egressy and co-authors add port numbers to a GIN and F1 on this dataset goes from 28.70 to
  54.85. The credit goes to telling counterparties apart. But the last slide showed that on a new
  pair the port just restates a count. So would plain counts do the same job?
- Careful: this study is not a replication of that table. The published numbers only motivate
  the question.

### 6. If counts explain ports, the port gain should shrink.

- Show: hypothesis, test, reading, and the formula
  share = 1 - (port gain with counts) / (port gain without counts).
- Say: If ports mostly restate activity and breadth, then once the model has the counts, adding
  ports should add little. So we measure the port gain twice, without counts and with counts.
  A share of 100% means counts replace ports. A share of 0% means nothing changed.
- Careful: the share is a ratio of performance differences. It can be negative and it is not
  causal.

### 7. One model is held fixed while only the history features change.

- Show: the 2x2 grid plus the fifth cell (`academic_factorial_design.png`).
- Say: Four models that differ only in their inputs. Base has the four transaction fields. Counts
  adds four running tallies. Ports adds two ranks. The fourth has both. A fifth model, added to
  probe the mechanism, has counts plus one bit that says this pair is new. Same network, same
  settings, seeds 0 to 4, five epochs each: 25 runs.
- Careful: the fifth model swaps ports for the bit. It does not have both.

### 8. The labelled network is large, sparse, and split by time.

- Show: the split table: train days 0-5 (3,248,921 transfers, 2,530 labels), validation days 6-7
  (965,524 and 1,036), test days 8-17 (863,900 and 1,611).
- Say: About one transfer in a thousand is labelled, so accuracy would reward a model that flags
  nothing. We report F1 on the laundering class. The split follows time: six days to train, two
  to validate, the rest to test.

### 9. Validation, not the test set, makes every choice.

- Show: three statements on threshold, epoch and uncertainty.
- Say: After every epoch the cut-off is set on validation and applied unchanged to test. The
  epoch we report is also chosen on validation, among the last four. The test set never picks
  anything. Each model is trained with five seeds and compared seed by seed.
- Careful: dropout stays on during scoring, so scoring is itself random. That is the same for
  every model.

### 10. Counts do not remove the gain from port numbering.

- Show: `factorial_gain.png`.
- Say: Without counts, ports add 7.48 F1 points. With counts already in the model, ports add
  14.91. The gain did not shrink, and it is positive in all five seeds both times.
- Careful: do not say the gain doubled. The difference between the two gains is +7.43 with an
  interval from -0.97 to 15.83, which includes zero.

### 11. Counts can explain at most about eight percent of the port gain.

- Show: `share_interval.png`.
- Say: The share explained is minus 99 percent. It is negative because the gain is larger with
  counts than without. The interval is wide on the negative side, but its upper end is what
  matters: 8.4 percent. Counts explaining most of the gain is ruled out.
- Careful: do not clip the share to 0-100% and do not call it a causal fraction.

### 12. Counts and ports together reveal whether a pair is new.

- Show: the running example again, then the five-model table (`novelty_comparison.png`).
- Say: A pair is new exactly when the port equals the distinct count. Counts alone cannot tell,
  ports alone cannot tell, together they can. So the Counts+Ports model already holds the
  new-pair signal, as an equality it has to learn. Give the model that signal as one bit and F1
  reaches 48.99, which is 9.42 points above Counts+Ports.
- Careful: the bit replaced ports. With five epochs an explicit bit may simply be easier to
  learn. This does not show that ranks are useless.

### 13. The novelty advantage is concentrated on first contacts.

- Show: first contacts against repeats.
- Say: First contacts are 4.3 percent of test transfers and hold 82 percent of the labels. There
  the bit finds about 225 more labelled transfers than ports, with almost no extra false
  positives. On repeats ports look a little better, but that interval includes zero.
- Careful: about 96 percent of first contacts are legitimate. A new pair is a signal, not an
  alert.

### 14. Better detection can still lengthen the review queue.

- Show: `alert_outcomes.png`.
- Say: In flags instead of F1: moving from Counts to Counts+Ports finds 213 more labelled
  transfers and raises 483 fewer false flags. Moving on to the new-pair bit finds 217 more and
  adds 24 false flags.
- Careful: each model uses its own threshold, so this is not a comparison at equal alert volume.
  Flags are transactions, not investigations, and nothing here measures analyst time.

### 15. The result holds outside an unusual late tail.

- Show: `robustness_effects.png`, or `temporal_shift.png` for the tail itself.
- Say: Days 10 to 17 hold 0.128 percent of the test transfers and 40.7 percent of the labels.
  Without them, on days 8 and 9, ports still add 8.98 points after counts and the bit still beats
  ports by 9.21.
- Careful: these checks reuse the same models, so they are not replications. Show what does not
  hold too: at a fixed 0.5 threshold both port-gain intervals include zero.

### 16. Monitoring features should ask whether two accounts have met before.

- Show: three cards.
- Say: Feature design: account totals miss whether this sender has paid this receiver before.
  Review capacity: compare detectors at one alert budget before claiming a lighter queue.
  Validation: score with what is known at decision time. This study used the full graph.
- Careful: keeping pair history needs identity resolution, a lookback window and stored state.
  None of that was tested here.

### 17. Ports add pair history that counts cannot supply.

- Show: two columns, what the evidence supports and what to test next.
- Say: The four counts do not explain away the port gain. An explicit new-pair bit is the
  strongest input we tested at five epochs. Next: train longer, add ports on top of the bit, and
  rescore a later period using only what is known at decision time. All of this rests on one
  synthetic dataset, five epochs and full-graph scoring.

## Numbers to quote

Test set: 863,900 transfers, 1,611 labelled. F1 is for the laundering class, in percent. Counts
of transfers are five-seed means at each model's own validation threshold.

| Model | Test F1, mean ± SD | Labelled found | False flags | Labelled missed |
|---|---:|---:|---:|---:|
| Base | 23.68 ± 3.38 | 450.2 | 1,708.2 | 1,160.8 |
| Counts | 24.66 ± 3.80 | 451.2 | 1,561.4 | 1,159.8 |
| Ports | 31.16 ± 4.63 | 510.2 | 1,148.4 | 1,100.8 |
| Counts+Ports | 39.57 ± 0.81 | 664.4 | 1,078.4 | 946.6 |
| Counts+novelty | 48.99 ± 2.45 | 881.6 | 1,102.4 | 729.4 |

| Contrast | F1 points [95% interval] |
|---|---:|
| Counts - Base | +0.98 [-7.18, +9.14] |
| Ports - Base (port gain without counts) | +7.48 [+2.96, +12.00] |
| Counts+Ports - Counts (port gain with counts) | +14.91 [+10.11, +19.71] |
| Difference between the two port gains | +7.43 [-0.97, +15.83] |
| Counts+novelty - Counts | +24.33 [+21.47, +27.19] |
| Counts+novelty - Counts+Ports | +9.42 [+5.73, +13.11] |

Share of the port gain explained by counts: -99.35%, 95% Fieller interval -512.75% to +8.42%.

| Test subset | Labels / transfers | Counts | Counts+Ports | Counts+novelty | Counts+novelty - Counts+Ports |
|---|---:|---:|---:|---:|---:|
| First contact | 1,325 / 37,221 | 31.09 | 43.74 | 55.13 | +11.40 [+7.54, +15.26] |
| Repeat | 286 / 826,679 | 6.91 | 15.83 | 11.78 | -4.05 [-12.03, +3.93] |

On first contacts Counts+novelty finds 848.4 labelled transfers with 903.4 false flags, against
623.8 and 903.2 for Counts+Ports. On repeats it finds 33.2 with 199.0 false flags, against 40.6
and 175.2.

| View | Ports - Base | Counts+Ports - Counts | Counts+novelty - Counts+Ports |
|---|---:|---:|---:|
| Full test F1 (primary) | +7.48 [+2.96, +12.00] | +14.91 [+10.11, +19.71] | +9.42 [+5.73, +13.11] |
| Days 8-9 F1 | +4.24 [+2.89, +5.59] | +8.98 [+6.59, +11.37] | +9.21 [+6.96, +11.46] |
| Full test F1, final epoch | +6.04 [+2.01, +10.07] | +15.28 [+9.87, +20.69] | +9.05 [+4.91, +13.19] |
| Full test AP | +7.12 [+0.42, +13.82] | +17.64 [+12.73, +22.54] | +11.26 [+6.75, +15.77] |
| Full test F1 at a fixed 0.5 threshold | +8.04 [-10.00, +26.08] | +6.78 [-13.93, +27.49] | +18.46 [+3.96, +32.95] |

## Figures

All in `presentation/figures/`, as PNG, SVG and PDF.

| File | Use |
|---|---|
| `academic_workflow.png` | Screening and human review (slide 2) |
| `academic_counterparty_breadth.png` | Equal counts, different relationships (slide 3) |
| `academic_feature_history.png` | The running example (slides 4 and 12) |
| `academic_factorial_design.png` | The 2x2 and the fifth cell (slide 7) |
| `temporal_shift.png` | Daily volume and label prevalence (slides 8 and 15) |
| `factorial_gain.png` | The two port gains and their difference (slide 10) |
| `share_interval.png` | Share explained and its interval (slide 11) |
| `novelty_comparison.png` | Counts, Counts+Ports and Counts+novelty by seed (slide 12) |
| `academic_counterexample.png` | Same counts, different pair history (slide 12, backup) |
| `alert_outcomes.png` | Found, false and missed transfers (slide 14) |
| `robustness_effects.png` | Days 8-9, final epoch and AP checks (slide 15) |
| `academic_estimand.png` | The two gains as a diagram (slide 6, backup) |

## Questions to expect

**Is the result driven by the late test days?** No. On days 8-9 alone the port gain with counts
is +8.98 [6.59, 11.37] and the bit's advantage over ports is +9.21 [6.96, 11.46]. First contacts
hold 734 of the 956 labels on those two days (76.8%).

**Is "new pair" an artefact of where the data start?** Partly, at the start. On day 0, 60.7% of
transfers are first contacts because there is no history yet. By days 4-5 the share is about 4%,
and validation and test have at least six days of history behind them. First contacts hold 79.2%
of the training labels, 77.0% of the validation labels and 82.2% of the test labels. In a real
system "new" would depend on the lookback window.

**Why do counts alone not help?** Counts - Base is +0.98 with an interval from -7.18 to +9.14, so
there is no detectable effect. That is not proof that counts are useless: with ports they reach
39.57, against 31.16 for ports alone. Counts describe each account. None of them describes the
pair.

**Why is the share negative?** Because the port gain with counts (14.91) is larger than the gain
without (7.48): 1 - 14.91 / 7.48 = -0.99.

**Why only five epochs?** A CPU budget fixed in advance. 23 of the 25 selected checkpoints are
the last epoch and validation F1 is still rising (Counts+Ports from 14.24 to 30.30, Counts+novelty
from 22.32 to 39.54), so the ranking after convergence is unknown.

**Why is F1 so far below the paper's 54.85?** A different budget and protocol: five epochs,
thresholds chosen on validation, and a different tie order and scoring. The study compares models
inside one setup. It does not replicate the published numbers.

**Does the bit explain the port gain?** That is not shown. The fifth model swaps ports for the
bit. The missing comparison is Counts+novelty+ports against Counts+novelty.

**What do the intervals mean?** Five seeds compared pairwise, with 95% t intervals on four
degrees of freedom. They describe training and scoring randomness on this dataset, not variation
across banks.

**Why not accuracy?** With 0.1% positives, flagging nothing is 99.9% accurate. F1 balances the
share of flags that are correct against the share of labelled transfers found.

**Could this be deployed?** Not on this evidence. The labels are simulated, message passing uses
the full graph including later transactions, and flags are not cases.

## Do not claim

- That ports are useless, or that counts are useless.
- That the new-pair bit explains the port gain, or that ranks add nothing once the bit is known.
- That the port gain doubles with counts.
- That the share is a causal fraction, or that it lies between 0 and 100%.
- That the review queue gets shorter.
- That anything here is ready to deploy.

## Numbers that are not in the report

The first-contact shares by period in "Questions to expect" come straight from the prepared graph:

```python
import torch

d = torch.load("data/hi_small.pt", weights_only=False)
y, first, split = d["y"].bool(), d["first_contact"].bool(), d["split"]
day = (d["base"][:, 0] // 86400).long()
groups = {"train": split == 0, "validation": split == 1, "test": split == 2,
          "test days 8-9": (split == 2) & (day <= 9), "day 0": day == 0, "days 4-5": (day >= 4) & (day <= 5)}
for name, m in groups.items():
    share = 100 * first[m].float().mean()
    labels = 100 * (y & first & m).sum() / (y & m).sum()
    print(f"{name}: first contacts are {share:.1f}% of transfers and hold {labels:.1f}% of labels")
```

Run it with `.venv/bin/python -I` from the repository root after `bash setup.sh`.
