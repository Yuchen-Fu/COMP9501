# Project status

Status checked **16 November 2026, UTC+08:00**. The fixed experiment and all
requested reporting work are complete. No training or queue process is active.

| Work item | Status | Evidence |
|---|---|---|
| Dataset download and preparation | Complete | 5,078,345 transactions; archive checksum and full raw alignment verified |
| Primary counts × ports factorial | Complete | Four cells × five seeds = 20 runs |
| Supplementary counts + novelty cell | Complete | Five runs |
| Training budget | Complete | Five epochs per run; 125 saved epoch predictions |
| Queue execution | Successful | Exit code 0; completion recorded 14 November 2026 at 15:52 UTC+08:00 |
| Independent numerical audit | Passed | 2,638 numerical comparisons and 39,682 Fieller membership checks |
| Research report and interpretation | Complete | Full results, confidence intervals, sensitivities, and independent interpretation review |
| AML business presentation | Complete | 20 slides centered on the representation research question, 11 numbered Python figures, speaker notes, and rendered exports |
| Remaining planned training jobs | None | 25/25 run JSON files and 25/25 prediction archives present |

The two Base/Ports seed-0 runs were inherited and verified; the remaining 23
runs completed in this cloud environment. Completed artifacts were retained
when the launcher was resumed. No extra seeds, epochs, or outcome-driven
replacement runs were added.

The current presentation asks whether explicitly providing pair novelty improves
prediction when that fact is already recoverable from counts and ports. It gives
Egressy et al. one background slide and emphasizes our design, paired comparison,
five-epoch trajectories, errors, and sensitivities. The original primary factorial
and supplementary status of novelty are preserved. All research outputs remain
unchanged. See the [presentation update](presentation/representation-study/UPDATE_NOTES.md)
and [export verification](presentation/representation-study/README.md).

## Research outcome

The specified historical counts do not remove the port benefit in this
five-epoch HI-Small experiment. Ports add **7.48 F1 points [2.96, 12.00]** without
counts and **14.91 [10.11, 19.71]** after counts. The explained-share estimate is
**−99.35%, with 95% Fieller interval [−512.75%, +8.42%]**. This does not establish
exact amplification or a causal identity effect.

Counts+novelty exceeds Counts+Ports by **9.42 F1 points [5.73, 13.11]**. This
motivates further validation of current-pair history; deployment effectiveness,
investigator savings, and converged performance remain untested.

## Where to read the completed work

- [Research report](RESEARCH_REPORT.md)
- [AML business narrative and speaker script](AML_BUSINESS_PRESENTATION.md)
- [PowerPoint](presentation/representation-study/AML_REPRESENTATION_STUDY.pptx), [PDF](presentation/representation-study/AML_REPRESENTATION_STUDY.pdf), and [slide overview](presentation/representation-study/preview/contact-sheet.png)
- [Full numerical results](results/summary.md) and [machine-readable results](results/summary.json)
- [Independent numerical audit](results/final-results-audit.md) and [interpretation review](results/research-interpretation-review.md)
- [Execution record](results/execution/README.md) and [run manifest](results/run_manifest.json)
- [Complete code/results/presentation archive](research-results.zip)

The repository includes code, metric logs, compressed prediction archives,
audit records, figures, and presentation source and exports. The raw dataset,
prepared graph, virtual environment, and Python caches are excluded; `setup.sh`
downloads and rebuilds the data with its pinned checksum. This status is a
completion snapshot, not a continuously running monitor.

## Branch integration

The original research branch and `course/port-counts-factorial` are integrated
in one history. Shared setup uses `data/hi_small.pt`, and the completed study
retains its original training code and numerical artifacts. The course branch's
100-epoch implementation remains an optional, separate protocol under
`results/factorial/`; it has no completed full-data runs. See
[COURSE_PROJECT.md](COURSE_PROJECT.md) for the protocol comparison and
[INTEGRATION.md](INTEGRATION.md) for verification and provenance.
