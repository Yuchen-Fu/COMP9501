# Beyond Counterparty Counts

**Central finding:** under the original five-epoch protocol, replacing ports with a first-contact flag detects more laundering on first-contact transfers, with counts retained.

This 16-slide presentation revises the user's supplied deck directly. It preserves the AML/GNN introductory diagrams, cream/navy palette, typography and overall layout. Two definition pages explain Counts and Ports before the research question. The original factorial remains the starting point: four account-history counts do not remove the port benefit. The supplementary flag comparison and descriptive error analysis then identify a useful pair-history signal and locate the observed detection improvement. The completed controlled follow-up is reported separately.

## Deliverables

- [Editable PowerPoint](Beyond_Counterparty_Counts_FINAL.pptx)
- [Rendered PDF](Beyond_Counterparty_Counts_FINAL.pdf)
- [Complete English speaker notes](SPEAKER_NOTES.md)
- Revised conclusion: [one-slide PowerPoint](Conclusion_Three_Findings.pptx), [one-page PDF](Conclusion_Three_Findings.pdf), [Chinese speaking notes](CONCLUSION_ZH.md). The standalone slide has no fixed page number and can replace the conclusion in a different version of the deck.
- Slide overviews: [1–8](preview/overview-01.jpg), [9–16](preview/overview-09.jpg)
- [Counts and Ports explained in Chinese](COUNTS_PORTS_ZH.md)
- [Python-generated figures](figures/) in PNG, PDF and SVG
- [Figure data and source hashes](figure_data.json)
- [Revision script](build_revision.py) and [original user deck](source/user_refined_2026-11-17.pptx)

## What changed

| Slides | Revision |
|---|---|
| 1 | Retitled **Beyond Counterparty Counts: Ports and Pair Novelty in AML Graph Learning**. |
| 2–4 | Kept the introductory diagrams and explanation of the published method. Clarified in notes that graph patterns are not proof of laundering. |
| 5 | Defined transfer counts, distinct-counterparty counts and local port labels. A four-transfer table distinguishes all three: S pays A, B, A, then C. Before the fourth transfer the values are 3 earlier transfers, 2 earlier distinct receivers and outgoing port 2. |
| 6 | Added a complete sender/receiver example showing the four count features and two port features. Counts are [3,2,2,2]; Ports are [0,1] in the code's incoming/outgoing order. Defined the separate first-contact flag, which is 0 for this repeated pair. |
| 7 | States the three questions precisely: do ports still help when counts are provided; does a first-contact flag improve detection beyond counts; and where are the extra detections when the flag replaces ports? The third question is explicitly descriptive error analysis. |
| 8–9 | Retained the data and factorial layout, clarified timestamp/tie order, and disclosed original split-specific normalisation, active dropout and batch statistics during scoring. |
| 10 | Repeats the exact RQ1, **Do ports still help when counts are provided?**, and answers it directly: **Yes. Ports add 14.91 F1 points beyond counts (95% CI [10.11, 19.71]).** The Python plot shows paired seeds and the planned ratio interval stays in a footnote. |
| 11 | Kept the worked example: identical account counts can accompany a new or repeated pair. Defined the flag in plain language. |
| 12 | Repeats RQ2: **Does a first-contact flag improve detection beyond counts?** The subtitle answers: **Yes. The flag adds 24.33 F1 points beyond counts (95% CI [21.47, 27.19]).** The separate replacement comparison, +9.42 [5.73, 13.11], leads into Q3. |
| 13 | Repeats RQ3: **Where are the extra detections when the flag replaces ports?** The subtitle answers: **On first contacts: laundering recall rises from 47.1% to 64.0%.** The caption names Counts + flag versus Counts + Ports and the original protocol. All five seeds detect more first-contact positives; mean true-positive changes are +224.6 on first contacts and −7.4 on repeated pairs. First-contact F1 rises by 11.40 points [7.54, 15.26]. |
| 14 | Retained the completed addition follow-up with its own Python interval plot. The primary F1 and AP intervals cross zero; no positive addition benefit was established. |
| 15 | Restored the user's approved three complete conclusions in a vertical layout: the residual port gain, both flag comparisons, and first-contact recall with agreement across all five seeds. The research contribution appears beneath them, and the notes explain the AML feature-design implication. The scope remains explicit. A standalone copy is supplied for replacing the conclusion in other deck versions. |
| 16 | Updated sources/materials links and consistent page numbering. |

Speaker notes provide the question, interpretation and transition for each slide. The presentation has no backup section and no oversized numerical cards.

RQ1's wording now names the tested conditional contrast: (Counts + Ports) − Counts. The earlier phrase “Do counts replace ports?” could be read as the separate comparison Counts − Ports. The research question slide, result slide, conclusion and notes now consistently describe the incremental port benefit after counts. This is a wording correction; the factorial design, saved estimates and original ratio estimand are unchanged.

RQ2 names the addition contrast (Counts + flag) − Counts. Its result page also shows the separate replacement contrast (Counts + flag) − (Counts + Ports), which supplies the comparison for RQ3's descriptive breakdown by first-contact/repeat status. These are distinct from the controlled follow-up's (Counts + Ports + flag) − (Counts + Ports). The question slide, result titles, subtitles, conclusion and notes now make the sequence explicit. The supplementary and descriptive labels remain; no analysis has been newly declared primary.

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

The PPTX was reopened and its package integrity, page bounds, 16-slide inventory and nonempty notes checked. The LibreOffice PDF was rendered and the two new definition pages visually inspected; the result pages retain their previously inspected layouts. The source's eight embedded font files are retained. This is a LibreOffice preview; native PowerPoint rendering can differ slightly.
