# Completed cloud execution record

The fixed 25-run experiment completed successfully on 14 November 2026.
`exit_code` is 0; `completion.log` records successful queue completion,
source/data fingerprint verification, and full 25-run artifact validation.

This folder preserves console logs for the 23 runs executed in this cloud
session. Base and Ports seed 0 were inherited from the repository and have
metric JSON and prediction archives in `../runs/`; their original console
logs and runtime manifest were not available. All 25 metric JSON logs and
all 125 epoch predictions were independently audited against current labels.

Counts and Counts+Ports seed 0 finished in the first execution attempt. The
remaining 21 jobs used a detached launcher with persistent stdout/stderr after
the earlier launcher stopped. Completed artifacts were retained, and no valid
run was replaced. Absolute paths in the archived completion log describe that
execution environment; portable reproduction uses the scripts in the repository.

The primary analysis and its sensitivity checks are in `../summary.md` and
`../../RESEARCH_REPORT.md`. No additional seeds or epochs were run after the
fixed experiment completed.
