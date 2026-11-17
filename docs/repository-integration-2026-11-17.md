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

Current links use `main`; archived commits and immutable server artifacts retain their original provenance. The former remote branches may be deleted only after their recorded tips are ancestors of the published `main` head.
