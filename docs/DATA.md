# Data and provenance

IBM AML HI-Small, Altman et al., NeurIPS 2023: 5,078,345 transfers, 515,088 accounts and 5,177 laundering labels.

- Dataset mirror: https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans
- Pinned revision: `6412f57ab89c9c28633ce5e837eca4c9a35c5dbe`.
- Archive: `HI-Small_Trans.csv.zip`.
- Archive SHA-256: `4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080`.
- Frozen prepared graph SHA-256: `53892586fdbd04d32af19ec433d97d74ddb913b1680ff5671daae7215b42eeef`.
- Frozen graph size: 619,561,688 bytes.

Accounts are nodes and transfers are directed edges. Training, validation and test contain 3,248,921 / 965,524 / 863,900 transfers, using whole-day cuts six and eight. Counts, ports and novelty use timestamp order, with a fixed label-independent ordering of equal timestamps. First contact means the first observed directed pair in this window. Both studies evaluate cumulative transductive graphs.

The archived raw-alignment and data-audit JSON files in `results/` record checks against the original CSV and the historical features. Raw data and the prepared graph are external. `scripts/prepare_data.sh` downloads the pinned archive and reproduces the preprocessing; it preserves an existing prepared graph. The frozen follow-up requires its exact graph checksum. Copy the original `data/hi_small.pt` from the completed university-server run when replaying that protocol.

The original study retains all 25 per-run JSON records and all 25 prediction archives. The GPU study retains all 15 completed run records, validation histories, full-precision summaries, frozen protocol, diagnostics and five probe records. Its imported results were checked against the source archive before cleanup. Transaction-level GPU probability archives and model checkpoints remain on the university server, so the retained GPU reports are not a new independent prediction-level audit.

The uploaded GPU archive had SHA-256 `a655632b923e94017b33b2cc0c9af22e1108a0b32f2f2c773164d15ba45a06dc`; all 83 payload checksums matched at import. One stale prose sentence about ten seeds was corrected to five; the numerical records already contained seeds 15–19. Duplicate ZIPs, progress snapshots and console logs have been removed from the current tree. Completed numerical records and the frozen protocol have not been edited.
