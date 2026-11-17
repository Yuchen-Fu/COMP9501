# Imported completed GPU study

The user supplied `AML_EXPLICIT_PAIR_8H_REVIEW.zip` on 17 November 2026. The original [archive](provenance/AML_EXPLICIT_PAIR_8H_REVIEW.zip) is retained unchanged, with SHA-256 `a655632b923e94017b33b2cc0c9af22e1108a0b32f2f2c773164d15ba45a06dc`.

All 83 payload files matched the archive's checksum manifest before import. They include the 15 completed run records and progress records, training logs, summary and analysis JSON, figures, data diagnostics, and five probe records. The frozen protocol matches the repository byte for byte. All eight runtime source hashes matched the pre-import code; that code is preserved in commit `4fecca3` and its history.

From the per-run JSON records, the imported primary paired differences, sample SDs and two-sided t intervals were independently recomputed. The results agree with `analysis.json`: F1 −7.2139485 points [−15.4567430,+1.0288459], AP −4.4931125 points [−19.1128171,+10.1265921]. The recorded validation selections, seed inventory, 416 total epochs and nine capped runs were also checked. These checks did not train a model, change an endpoint or execute an additional experiment.

**Review scope:** the supplied archive deliberately excludes transaction-level prediction NPZ files and model checkpoints. This import verifies metadata and summary consistency, not an independent reconstruction of F1/AP from transaction-level predictions or a fresh probe fit. The server-generated analysis records its own prediction audit. The original full result archive and checkpoints remain on the university server.

## Editorial correction

The generated report had one stale sentence saying A/B used ten seed blocks while C used five. In this completed budget protocol, all three arms use the same five seeds, 15–19; the report tables, JSON and calculations were already correct. Only that sentence was corrected in [FOLLOWUP_REPORT.md](FOLLOWUP_REPORT.md). The [original report](provenance/ORIGINAL_FOLLOWUP_REPORT.md) and uploaded ZIP retain the server's exact text. The report generator now formats the cohort sizes from the protocol instead of hardcoding them. No model, selection, prediction or numerical result changed.

The earlier `reported/` directory retains the interpretation and illustrative figures initially made from the user's rounded message. Use the imported full-precision `summary.json`, `analysis.json` and official `figures/` as the numerical source for future presentation updates. This study remains separate from the original five-epoch factorial and the unexecuted ten-seed factorial proposal.
