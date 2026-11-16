# What was actually verified before handoff

Validated on 2026-11-16. No new production HI-Small training batch has been launched. The original 55 protected pilot source/result artifacts retain their checksums.

## Fresh installation and integration

The supplied installer completed in a new Python 3.12 virtual environment using the CPU wheel index and the exact declared pins: PyTorch 2.8.0, pyg-lib 0.4.0, PyG 2.6.1, NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.6.1, pandas 2.2.3 and Matplotlib 3.10.1. `pip check` passed. Python 3.11 is supported by the available pinned wheels but was not separately tested here.

In this new environment, the entire sequential batch was executed on a clearly separated 600-transfer toy graph with genuine chronological counts and port ranks and nonempty early/late test subsets. All 25 runs completed (609 epochs in aggregate under the fixed stopping rule), followed by the complete prediction audit, paired analysis, all ten representation probes, figures and return ZIP. This checks integration; toy scores are not scientific evidence and are excluded from the delivery package.

## Real-data and model checks

- Every one of the 5,078,345 HI-Small transfers passed independently reconstructed history and split checks.
- Raw and float32-normalized count–port equalities reproduce novelty in both directions on the full graph.
- Shared normalization is fitted only on training transfers. Held-out-value changes cannot change its fitted statistics.
- All three input arms have identical parameter counts, initial weights and normalization hashes within paired seed blocks.
- CPU tests confirmed repeatable evaluation, preserved BatchNorm/encoder state, and restored training RNG.
- A real-data CPU preflight processed 8,192 training targets and 8,192 validation targets successfully. The discarded preflight computed no AML performance conclusion.
- Saved probability archives reproduce logged F1/AP, thresholds and selected epochs. Independent synthetic checks reject incomplete batches, corrupted scores and unmatched provenance, and confirm the secondary contrasts use five paired seeds rather than unmatched arm means.
- Probe tests confirmed training-only fitting/scaling, validation-only threshold selection, unchanged frozen representations, exact equality-oracle agreement, and idempotent reruns.
- Failure propagation, duplicate-batch protection, the 25-job enumeration, shell syntax and exclusion of checkpoints from the return archive were checked.
- The power calculation was independently recomputed in the pinned environment; the reported detectable differences agree.

Machine-readable real-data checks are included in `validation/`. `historical_raw_alignment.json` comes from the earlier full CSV-to-graph audit; the new history audit and pinned CPU preflight were run during this handoff.

## What remains unverified

This cloud machine has no GPU. Actual CUDA kernels, GPU memory use, the HKU scheduling policy and full-training runtime cannot be verified here. The submitted job first runs a device-specific toy test and a real-data batch test; it stops explicitly on failures. A successful sampled-batch memory test does not guarantee that every later neighborhood fits. The Slurm template follows the GPU syntax supplied in the HKU login banner; local partition/account/time-limit rules may require administrative adjustments.

The full scientific outcome remains pending. Neither these engineering checks nor earlier replacement results establish a positive B−A addition effect.
