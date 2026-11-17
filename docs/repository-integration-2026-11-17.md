# Repository consolidation — 17 November 2026

The repository is consolidated on `main`. The merge preserves the previous completed-study head (`5504ede`) and the independent presentation/statistics head (`7575a9c`) as ancestors. The course implementation was already contained in the completed-study history. No branch history was discarded to obtain a single branch.

The uploaded 15-run GPU review archive is imported under `results/representation_8h/`, with its original ZIP and import notes. Its primary result is inconclusive under the frozen rule; the original five-epoch study remains a separate historical experiment.

Integration decisions:

- Retain the presentation builder revisions, presentation notes, rebuilt historical deck and five-seed statistical reporting improvements from the parallel development line.
- Preserve existing audit records, course code, original run outputs and historical packages that the parallel cleanup had removed; removing branch names does not remove research evidence.
- Keep the regular factorial runner and analyzer aligned with the completed five-seed pilot. The five-seed analyzer comes from `ba4cedb`, before the proposed ten-seed changes.
- Preserve the unexecuted extension separately as `src/analyze_ten_seed.py`, `run_ten_seed_extension.sh`, and [its historical proposal](ten_seed_factorial_proposal.md). No extension result is claimed and no additional training was started.
- Present the actual GPU results as current evidence. Historical decks and notes are labelled as pilot material; they do not establish a positive addition effect in the follow-up.
- Correct one report-only seed-count sentence in the GPU report. Preserve the original uploaded report and its checksum provenance.

Current links use `main`; archived commits and immutable server artifacts retain their original provenance. The former branch tips were retained as ancestors of the published merge. On 17 November 2026, a fresh remote check confirmed that **`main` is both the default and the only remote branch**. The last former default branch had already been removed when this final check was made. Local stale remote-tracking references were pruned, and `origin/HEAD` now points to `origin/main`.

## Detailed follow-up interpretation

The [full Chinese report](../DETAILED_FOLLOWUP_REPORT.md) now separates the unsupported addition claim from the original replacement finding. It adds descriptive error decompositions, mathematical clarification of the novelty predicate, probe interpretation, and concrete manuscript changes. The [presentation revision plan](../presentation/representation-study/REVISION_PLAN.md) provides 14 main slides plus four backup slides and seven Python-generated figures. The historical binary deck is retained, not silently replaced with an unrendered update.

`src/report_followup.py` reads the saved JSON records and writes `analysis_notes.json` plus PNG/PDF/SVG figures. No training run, endpoint, frozen protocol or saved prediction was changed; no additional hypothesis test or probe fit was run. Newly reported alert decompositions are explicitly labelled post-hoc and descriptive.
