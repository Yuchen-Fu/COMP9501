# Data provenance

The upload package contains the prepared graph used by the completed pilot, with unchanged account IDs, transaction ordering, labels, split membership, counts and ports. New production runs use this exact graph, rather than redownloading a moving dataset revision.

- Dataset: IBM AML HI-Small, described by Altman et al., NeurIPS 2023 Datasets and Benchmarks.
- User-specified mirror: https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans
- Pinned mirror revision: `6412f57ab89c9c28633ce5e837eca4c9a35c5dbe`.
- Original archive: https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans/resolve/6412f57ab89c9c28633ce5e837eca4c9a35c5dbe/HI-Small_Trans.csv.zip
- Original archive SHA-256: `4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080`.
- Prepared graph SHA-256: `53892586fdbd04d32af19ec433d97d74ddb913b1680ff5671daae7215b42eeef`.
- Prepared graph size: 619,561,688 bytes; 5,078,345 transactions; 515,088 accounts; 5,177 laundering labels.
- Training / validation / test transfers: 3,248,921 / 965,524 / 863,900.

The CSV and its original archive are not duplicated in this package. The prepared graph is included, so training requires no data download. `src/prepare.py` retains the preprocessing implementation; the historical raw-alignment audit is supplied under `validation/`. It verified all edge endpoints, labels, base features and account identities against the raw CSV, including zero collisions in the account coding used here.

Every batch independently reconstructs historical counts, distinct counts, port ranks, novelty and the day split from the prepared edges. It also verifies the frozen graph checksum. This checks the entire 5,078,345-transfer graph, not merely a sampled subgraph.

To reconstruct independently, download and verify the pinned archive, extract the CSV and run `src/prepare.py` into a separate path. Compare tensor contents with the supplied graph. PyTorch serialization bytes can differ across paths or versions even when tensors agree; do not overwrite the supplied graph or edit its frozen hash during an existing batch.

The existing test period and its unusual late tail were examined before this follow-up was designed. This fact is disclosed in the protocol. The dataset is synthetic, and the package does not claim independent validation in a real bank.
