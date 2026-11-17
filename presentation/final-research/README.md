# Beyond Counterparty Counts

**Central finding:** under the original five-epoch protocol, replacing ports with a first-contact flag detects more laundering on first-contact transfers, with counts retained.

This 15-slide presentation revises the user's supplied deck directly. It preserves the introductory diagrams, cream/navy palette, typography and overall layout. The original factorial remains the starting point: four account-history counts do not remove the port benefit. The supplementary flag comparison and descriptive error analysis then identify a useful pair-history signal and locate the observed detection improvement. The completed controlled follow-up is reported separately.

## Deliverables

- [Editable PowerPoint](Beyond_Counterparty_Counts_FINAL.pptx)
- [Rendered PDF](Beyond_Counterparty_Counts_FINAL.pdf)
- [Complete English speaker notes](SPEAKER_NOTES.md)
- Slide overviews: [1–8](preview/overview-01.jpg), [9–15](preview/overview-09.jpg)
- [Python-generated figures](figures/) in PNG, PDF and SVG
- [Figure data and source hashes](figure_data.json)
- [Revision script](build_revision.py) and [original user deck](source/user_refined_2026-11-17.pptx)

## What changed

| Slides | Revision |
|---|---|
| 1 | Retitled **Beyond Counterparty Counts: Ports and Pair Novelty in AML Graph Learning**. |
| 2–5 | Kept the introductory diagrams and explanation of the published method. Clarified in notes that graph patterns are not proof of laundering, and first contact means first observed directed pair within the dataset window. |
| 6 | Connected three questions: do counts replace ports, does a first-contact flag improve detection, and which transfers account for the extra detections? The third question is explicitly descriptive error analysis. |
| 7–8 | Retained the data and factorial layout, clarified timestamp/tie order, and disclosed original split-specific normalisation, active dropout and batch statistics during scoring. |
| 9 | Replaced result graphics with a Python plot showing paired seeds. The headline is **Counts do not remove the port benefit**: +14.91 F1 points [10.11, 19.71] remain after counts. The planned ratio interval stays in a footnote. |
| 10 | Kept the worked example: identical account counts can accompany a new or repeated pair. Defined the flag in plain language. |
| 11 | Replaced result graphics with a Python plot and complete sentences: adding the flag to Counts gives +24.33 F1 points [21.47, 27.19]; replacing ports with the flag gives +9.42 [5.73, 13.11]. |
| 12 | Added **The flag detects more laundering on first contacts**. The paired plot shows recall rising from 47.1% to 64.0%. All five seeds detect more first-contact positives; mean true-positive changes are +224.6 on first contacts and −7.4 on repeated pairs. First-contact F1 rises by 11.40 points [7.54, 15.26]. |
| 13 | Retained the completed addition follow-up with its own Python interval plot. The primary F1 and AP intervals cross zero; no positive addition benefit was established. |
| 14 | Replaced the conclusion with three complete, evidence-supported sentences. The scope is stated beneath them: original five-epoch HI-Small protocol, five paired seeds, supplementary flag comparison. |
| 15 | Updated sources/materials links and consistent page numbering. |

Speaker notes provide the question, interpretation and transition for each slide. The presentation has no backup section and no oversized numerical cards.

## What the evidence means

The positive flag results belong to the original five-epoch experiment. The primary factorial shows that the tested counts leave a substantial port benefit. The supplementary comparison shows that a simple first-contact flag is useful beyond those counts. The new slide locates the additional detections on first-contact transfers; it does not show that the AML network causally uses a particular internal mechanism or that the flag explains a fixed proportion of the port benefit.

The controlled follow-up changes scaling, scoring, layout and training budget. Adding the flag while keeping ports gives F1 −7.21 points [−15.46, +1.03] and AP −4.49 [−19.11, +10.13]. It contains no Counts-only arm, so it does not repeat the original +24.33 comparison. It also does not establish harm, equivalence or convergence. Results from the two protocols are not pooled.

All reported intervals are existing nominal paired-seed intervals on a fixed graph, not uncertainty over independently sampled datasets. The supplementary comparisons and strata are not multiplicity-adjusted. Figure 3's count changes are descriptive differences in counts, not alert-set overlap or an additive decomposition of F1. Each model uses its own validation-selected threshold. Mean first-contact false alerts are 903.2 versus 903.4, but individual-seed changes vary; this is not evidence of equal investigation workload.

## Provenance and reproduction

The source deck is the user's uploaded `What Do Port Numbers Add Counterparty Counts vs. Counterparty Identity in Multigraph GNNs for AML (1).pptx`, SHA-256:

```text
c17f41d17d9f31762276eebfb0918da221d2e79d1ab96f6cf834a3c9c9a9cc71
```

The script reads the existing [original summary](../../results/summary.json) and [follow-up summary](../../results/representation_8h/summary.json). It does not train models, modify results or run new significance tests. Figure 3 computes recall and net count differences from saved confusion counts. All intervals are read from the completed analyses. The figure-data JSON records the input hashes.

From the repository root, using Python with `python-pptx`, `matplotlib`, `numpy` and `Pillow` installed:

```bash
python presentation/final-research/build_revision.py
soffice -env:UserInstallation=file:///tmp/aml-final-lo --headless --convert-to pdf --outdir presentation/final-research presentation/final-research/Beyond_Counterparty_Counts_FINAL.pptx
```

The PPTX was reopened and its package integrity, page bounds, 15-slide inventory and nonempty notes checked. The 15-page LibreOffice PDF was rendered and visually inspected, including the new evidence page. The source's eight embedded font files are retained. This is a LibreOffice preview; native PowerPoint rendering can differ slightly.
