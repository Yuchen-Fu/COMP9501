# Complete server upload

[Download AML_EXPLICIT_PAIR_STUDY.zip](https://raw.githubusercontent.com/Yuchen-Fu/COMP9501/claude/cloud-setup-port-gnn-research-o13ou8/downloads/AML_EXPLICIT_PAIR_STUDY.zip)

This is the complete 88,964,863-byte package, including prepared HI-Small data. Its contents are identical to the handoff archive built from commit `5d1efd9902f958a021efb212bf91b5fb60dd0396`; the experiment has not changed. GitHub's ordinary repository source download also includes this archive now, but the direct link avoids downloading unrelated presentation files.

From the university server:

```bash
curl -fL -o AML_EXPLICIT_PAIR_STUDY.zip https://raw.githubusercontent.com/Yuchen-Fu/COMP9501/claude/cloud-setup-port-gnn-research-o13ou8/downloads/AML_EXPLICIT_PAIR_STUDY.zip
unzip AML_EXPLICIT_PAIR_STUDY.zip
cd AML_EXPLICIT_PAIR_STUDY
sha256sum -c PACKAGE_SHA256SUMS
```

Read `README.md` inside the package for installation and Slurm submission. Check the `debug` partition's `MaxTime` before submitting the 24-hour template; scheduler walltime may be adjusted without changing the fixed research protocol. Keep the same GPU model when resuming.

Archive SHA-256: `61c4fbbac7de9daacc41055d06ab28eb7381ea6efec46b7cbc16c03d25b292a5`.

The full production experiment is still pending; the archive contains no new model results.
