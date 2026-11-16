"""Audit historical features and quantify temporal distribution shift before training."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["time", "amount", "currency", "format", "out_total", "out_distinct",
         "in_total", "in_distinct", "in_port", "out_port"]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(data):
    """Reconstruct histories from global pair first appearances, independently of prepare.py."""
    u, v = data["edge_index"].numpy()
    n = data["n_nodes"]
    counts, ports = data["counts"].numpy(), data["ports"].numpy()
    _, first, inverse = np.unique(u * n + v, return_index=True, return_inverse=True)
    novelty = np.zeros(len(u), dtype=bool)
    novelty[first] = True
    checks = {"novelty": int(np.count_nonzero(novelty != data["first_contact"].numpy()))}
    for endpoint, label, total_col, distinct_col, port_col in [(u, "out", 0, 1, 1), (v, "in", 2, 3, 0)]:
        grouped = pd.Series(novelty.astype(np.int64)).groupby(endpoint, sort=False)
        total = grouped.cumcount().to_numpy()
        distinct = grouped.cumsum().to_numpy() - novelty
        rank = distinct[first][inverse]
        for name, actual, expected in [("total", counts[:, total_col], total),
                                       ("distinct", counts[:, distinct_col], distinct),
                                       ("port", ports[:, port_col], rank)]:
            checks[f"{label}_{name}"] = int(np.count_nonzero(actual != expected))
        checks[f"{label}_equality"] = int(np.count_nonzero((rank == distinct) != novelty))
        checks[f"{label}_repeat_order"] = int(np.count_nonzero(rank[~novelty] >= distinct[~novelty]))
    timestamp = data["base"][:, 0].numpy()
    checks["time_order"] = int(np.count_nonzero(timestamp[1:] < timestamp[:-1]))
    daily = np.bincount((timestamp // 86400).astype(int))
    _, i, j = min((float(np.max(np.abs(np.array([daily[:a].sum(), daily[a:b].sum(), daily[b:].sum()])
                                    / len(u) - [.6, .2, .2]) / [.6, .2, .2])), a, b)
                  for a, b in itertools.combinations(range(len(daily)), 2))
    day = (timestamp // 86400).astype(int)
    checks["day_split"] = int(np.count_nonzero(np.where(day < i, 0, np.where(day < j, 1, 2)) != data["split"].numpy()))
    if any(checks.values()):
        raise ValueError(f"Data history integrity failed: {checks}")
    return checks, [i, j]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/hi_small.pt")
    parser.add_argument("--protocol", type=Path, default=ROOT / "results/representation_followup/protocol.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results/representation_followup")
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    digest = sha256(args.data)
    if digest != protocol["data"]["sha256"]:
        raise ValueError("Graph differs from the frozen protocol")
    torch.set_num_threads(2)
    data = torch.load(args.data, map_location="cpu", weights_only=False, mmap=True)
    checks, cuts = audit(data)
    split, y = data["split"].numpy(), data["y"].numpy()
    novelty = data["first_contact"].numpy()
    raw = np.column_stack([data[k].numpy() for k in ("base", "counts", "ports")])
    day = (raw[:, 0] // 86400).astype(int)
    training = raw[split == 0]
    minimum, maximum = training.min(0), training.max(0)
    del training
    ranges = []
    for col, name in enumerate(NAMES):
        row = {"feature": name, "train_min": float(minimum[col]), "train_max": float(maximum[col])}
        for s, label in [(1, "validation"), (2, "test")]:
            values = raw[split == s, col]
            row[label] = {"below_train_fraction": float(np.mean(values < minimum[col])),
                          "above_train_fraction": float(np.mean(values > maximum[col])),
                          "minimum": float(values.min()), "maximum": float(values.max())}
        ranges.append(row)
    daily = []
    for d in range(int(day.max()) + 1):
        mask = day == d
        if not mask.any():
            continue
        daily.append({"day": d, "split": int(split[mask][0]), "transactions": int(mask.sum()),
                      "laundering": int(y[mask].sum()), "laundering_prevalence": float(y[mask].mean()),
                      "novelty_prevalence": float(novelty[mask].mean())})
    result = {"data_sha256": digest, "protocol_sha256": sha256(args.protocol),
              "source_sha256": sha256(__file__), "history_mismatches": checks,
              "day_cut_points": cuts, "ranges": ranges, "daily": daily,
              "interpretation": "Novelty has the same definition in every split; its prevalence changes as observed history accumulates. Range shift is descriptive and cannot trigger protocol changes."}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "diagnostics.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    figdir = args.out / "figures"
    figdir.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True, layout="constrained")
    axes[0].plot([r["day"] for r in daily], [100 * r["novelty_prevalence"] for r in daily], "o-", color="#235789")
    axes[0].set_ylabel("First-contact transfers (%)")
    axes[1].bar([r["day"] for r in daily], [r["transactions"] for r in daily], color="#7098B5")
    axes[1].set(yscale="log", ylabel="Transfers (log scale)", xlabel="Day since the first observed transfer")
    for ax in axes:
        for cut in cuts:
            ax.axvline(cut - .5, color="#8A3842", linestyle="--", linewidth=1)
    for ext in ("png", "pdf"):
        fig.savefig(figdir / f"novelty_by_day.{ext}", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    positions = np.arange(len(NAMES))
    for offset, label, color in [(-.18, "validation", "#235789"), (.18, "test", "#A23E48")]:
        values = [100 * (r[label]["below_train_fraction"] + r[label]["above_train_fraction"]) for r in ranges]
        ax.barh(positions + offset, values, .35, label=label.capitalize(), color=color)
    ax.set(yticks=positions, yticklabels=NAMES, xlabel="Values outside the observed training range (%)", xlim=(0, 105))
    ax.legend(frameon=False)
    for ext in ("png", "pdf"):
        fig.savefig(figdir / f"feature_drift.{ext}", dpi=180)
    plt.close(fig)
    lines = ["# Data integrity and temporal drift", "",
             f"All {len(y):,} transfers passed independently reconstructed total-count, distinct-count, port-rank and novelty checks. Day cuts are {cuts[0]} and {cuts[1]}.", "",
             "History is strictly earlier in the fixed timestamp-plus-random-tie order. Equal timestamps are not claims about unobserved within-minute physical order. Graph neighborhoods remain cumulative and transductive: an evaluation transfer can receive messages from later transfers within its evaluation graph. These experiments do not establish performance of a causal online alerting system.", "",
             "![Novelty prevalence and transfer volume](figures/novelty_by_day.png)", "",
             "**Figure D1.** First-contact prevalence changes as observed history accumulates. Dashed lines mark the train/validation/test boundaries. The flag retains the same meaning; the mixture changes. Day 0 starts with an empty observed history.", "",
             "![Feature range shift](figures/feature_drift.png)", "",
             "**Figure D2.** Fraction of validation/test values outside each feature's training minimum–maximum. All transformations are fitted on training transfers only. No clipping or refitting uses test values. Cumulative counts need not all exceed their training ranges; the fractions quantify the actual shift.", "",
             "| Day | Transfers | Laundering | First-contact share |", "|---:|---:|---:|---:|"]
    lines += [f"| {r['day']} | {r['transactions']:,} | {r['laundering']:,} | {100*r['novelty_prevalence']:.2f}% |" for r in daily]
    lines += ["", "These are distribution diagnostics, not model outcomes. They cannot justify changing the frozen seed count, endpoint, scaling or stopping rules. The small late test tail has a different class mixture; the prespecified days 8–9 analysis shows how much the main comparison depends on it.", ""]
    (args.out / "DRIFT_REPORT.md").write_text("\n".join(lines))
    print(json.dumps({"history_checks": "passed", "transactions": len(y), "output": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
