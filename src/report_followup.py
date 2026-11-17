"""Describe the completed follow-up and draw publication figures from saved JSON.

No model fitting, prediction scoring, hypothesis tests or endpoint selection.
The inferential intervals are copied from the frozen study's saved summary.
New confusion-count decompositions are explicitly post-hoc descriptions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ARMS = ("cp", "cpn", "cn")
LABELS = {"cp": "A: Counts + Ports", "cpn": "B: Counts + Ports + Novelty",
          "cn": "C: Counts + Novelty"}
COLORS = {"cp": "#315b7d", "cpn": "#ac513d", "cn": "#417b62"}


def read(path):
    return json.loads(path.read_text())


def save(fig, directory, name):
    for extension in ("png", "pdf", "svg"):
        fig.savefig(directory / f"{name}.{extension}", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path(__file__).resolve().parents[1] / "results/representation_8h")
    args = parser.parse_args()
    root = args.results
    summary, diagnostics, probes = [read(root / x) for x in
                                    ("summary.json", "diagnostics.json", "probes/probe_summary.json")]
    primary = summary["selections"]["best_validation"]["subsets"]
    output = root / "detailed_figures"
    output.mkdir(exist_ok=True)
    seeds = summary["seeds"]
    runs = {arm: [read(root / f"runs/{arm}_s{seed}.json") for seed in seeds] for arm in ARMS}
    means, changes = {}, {}
    for subset, result in primary.items():
        means[subset] = {}
        for arm in ARMS:
            rows = result["cells"][arm]["confusion_per_seed"]
            means[subset][arm] = {key: float(np.mean([row[key] for row in rows])) for key in rows[0]}
        changes[subset] = {}
        for key in ("tp", "fp", "fn", "flagged", "precision", "recall"):
            a = result["cells"]["cp"]["confusion_per_seed"]
            b = result["cells"]["cpn"]["confusion_per_seed"]
            values = [bb[key] - aa[key] for aa, bb in zip(a, b)]
            changes[subset][key] = {"per_seed": values, "mean": float(np.mean(values))}
    shares = {
        "first_contact_share_of_net_tp_change": changes["first_contact"]["tp"]["mean"] / changes["all"]["tp"]["mean"],
        "repeat_share_of_net_fp_change": changes["repeat"]["fp"]["mean"] / changes["all"]["fp"]["mean"],
        "days_8_9_share_of_net_fp_change": changes["days_8_9"]["fp"]["mean"] / changes["all"]["fp"]["mean"],
        "tail_share_of_net_tp_change": changes["day_10_plus"]["tp"]["mean"] / changes["all"]["tp"]["mean"],
    }
    split_data = {}
    for split, label in enumerate(("train", "validation", "test")):
        rows = [r for r in diagnostics["daily"] if r["split"] == split]
        total = sum(r["transactions"] for r in rows)
        split_data[label] = {"transactions": total, "positive": sum(r["laundering"] for r in rows),
                             "novelty_prevalence": sum(r["transactions"] * r["novelty_prevalence"] for r in rows) / total}
    selected_validation = {}
    for arm, records in runs.items():
        selected = [next(h for h in r["history"] if h["epoch"] == r["best_epoch"]) for r in records]
        selected_validation[arm] = {"mean_f1_percent": float(np.mean([h["val_f1"] for h in selected]) * 100),
                                    "mean_ap_percent": float(np.mean([h["val_ap"] for h in selected]) * 100),
                                    "selected_epochs": [r["best_epoch"] for r in records],
                                    "completed_epochs": [r["epochs_completed"] for r in records]}
    first, all_tx = primary["first_contact"], primary["all"]
    illustration = {"status": "post-hoc base-rate illustration, not a prespecified model baseline",
                    "precision_percent": first["n_positive"] / first["n_tx"] * 100,
                    "recall_percent": first["n_positive"] / all_tx["n_positive"] * 100,
                    "f1_percent": 2 * first["n_positive"] / (first["n_tx"] + all_tx["n_positive"]) * 100}
    sources = [root / name for name in ("summary.json", "diagnostics.json", "probes/probe_summary.json")]
    sources += [root / f"runs/{arm}_s{seed}.json" for arm in ARMS for seed in seeds]
    notes = {"status": "descriptive analysis of saved results; no additional fits or tests",
             "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
             "seeds": seeds, "confusion_means": means, "addition_confusion_changes": changes,
             "net_change_shares": shares, "split_data": split_data,
             "selected_validation": selected_validation, "first_contact_rule_illustration": illustration,
             "limitations": ["Net count changes do not identify overlapping alert sets.",
                             "Novelty and time partitions overlap; do not add their decompositions.",
                             "Seed averages of precision/F1 differ from metrics computed from averaged counts.",
                             "Transaction predictions and checkpoints are absent from the review archive."]}
    (root / "analysis_notes.json").write_text(json.dumps(notes, indent=2) + "\n")
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 11, "axes.titlesize": 12,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "pdf.fonttype": 42, "figure.facecolor": "white"})

    # Figure 2: a transparent example, not an empirical estimate.
    fig, ax = plt.subplots(figsize=(10.5, 3.2))
    ax.axis("off")
    rows = [[1, "u → v", 0, 0, 0, 1], [2, "u → v", 1, 1, 0, 0],
            [3, "u → w", 2, 1, 1, 1], [4, "u → v", 3, 2, 0, 0], [5, "u → z", 4, 2, 2, 1]]
    table = ax.table(cellText=rows, colLabels=["Event", "Transfer", "Earlier transfers", "Earlier distinct (d)", "Port (p)", "Novelty (N)"],
                     colWidths=[.08, .13, .21, .25, .13, .14], loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.7)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#d4d9dd")
        if row == 0:
            cell.set_facecolor("#e8eef3")
        elif rows[row - 1][-1] == 1:
            cell.set_facecolor("#f1f6f2")
    ax.set_title("A first observed pair has p = d; a repeated pair has p < d.\nSender-side history shown; ports start at zero.", pad=15)
    save(fig, output, "fig02_relationship")

    # Figure 1: rates are association, not a model evaluation or causal effect.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    subsets = ("first_contact", "repeat", "days_8_9", "day_10_plus")
    rates = [primary[x]["n_positive"] / primary[x]["n_tx"] * 100 for x in subsets]
    axes[0].bar(np.arange(4), rates, color=[COLORS["cn"], COLORS["cp"], "#8e9dac", "#ac8261"], width=.65)
    axes[0].set_xticks(np.arange(4), ["First\ncontact", "Repeat", "Days\n8–9", "Day\n10+"])
    axes[0].set_yscale("log"); axes[0].set_ylim(.01, 150)
    axes[0].set_ylabel("Laundering prevalence (%) — log scale")
    axes[0].set_title("(a) Test-set base rates")
    for i, value in enumerate(rates):
        axes[0].text(i, value * 1.2, f"{value:.3g}%", ha="center", fontsize=10)
    daily = diagnostics["daily"]
    axes[1].plot([r["day"] for r in daily], [r["novelty_prevalence"] * 100 for r in daily], "o-", color=COLORS["cp"], ms=4)
    axes[1].axvline(5.5, ls="--", color=".55"); axes[1].axvline(7.5, ls="--", color=".55")
    axes[1].set(xlabel="Dataset day", ylabel="First observed directed pairs (%)", ylim=(0, 105), title="(b) Novelty changes across time")
    for x, label in ((2.5, "Train"), (6.5, "Val."), (12.5, "Test")):
        axes[1].text(x, 99, label, ha="center", fontsize=10)
    save(fig, output, "fig01_data_context")

    def forest(name, entries, labels):
        fig, axes = plt.subplots(1, 2, figsize=(11.2, .65 * len(entries) + 1.55), sharey=True, layout="constrained")
        for ax, metric in zip(axes, ("f1", "ap")):
            for y, entry in enumerate(entries):
                values = entry[metric]
                lo, hi = values["ci95"]; mean = values["mean"]
                ax.scatter(values["per_seed"], y + np.linspace(-.12, .12, len(seeds)), s=22, color=".65", zorder=2)
                ax.errorbar(mean, y, xerr=[[mean - lo], [hi - mean]], fmt="D", color=COLORS["cp"], capsize=4, ms=5, zorder=3)
            ax.axvline(0, color=".35", ls="--", lw=1)
            ax.set_xlabel(f"{'F1' if metric == 'f1' else 'AP'} difference (percentage points)")
            ax.set_yticks(np.arange(len(labels)), labels)
            ax.grid(axis="x", alpha=.15)
        axes[0].invert_yaxis()
        axes[0].set_title("Mean and paired-seed 95% t interval")
        axes[1].set_title("Small dots: individual paired differences")
        save(fig, output, name)

    effects = primary["all"]["effects"]
    forest("fig03_paired_effects", [effects[x] for x in ("explicit_addition", "explicit_replacement", "ranks_after_novelty")],
           ["B − A: add novelty\n(primary)", "C − A: replace ports\n(secondary)", "B − C: retain ports\n(secondary)"])
    sensitivity = [("best_validation", "all"), ("best_validation", "days_8_9"), ("epoch_5", "all"),
                   ("epoch_10", "all"), ("epoch_20", "all"), ("final", "all")]
    forest("fig05_sensitivity", [summary["selections"][s]["subsets"][sub]["effects"]["explicit_addition"] for s, sub in sensitivity],
           ["Selected model (primary)", "Selected model, days 8–9", "Fixed epoch 5", "Fixed epoch 10", "Fixed epoch 20", "Final checkpoint"])

    # Figure 4: only descriptive count differences; no new intervals/tests.
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4), layout="constrained")
    for ax, metric, title in zip(axes, ("tp", "fp"), ("(a) Change in true alerts", "(b) Change in false alerts")):
        for i, subset in enumerate(("first_contact", "repeat")):
            item = changes[subset][metric]
            ax.scatter(i + np.linspace(-.10, .10, len(seeds)), item["per_seed"], s=30, color=".65")
            ax.scatter(i, item["mean"], marker="D", s=55, color=COLORS["cpn"], zorder=3)
            ax.annotate(f"Mean {item['mean']:+.1f}", (i, item["mean"]), xytext=(10, 6), textcoords="offset points", fontsize=10)
        ax.axhline(0, ls="--", color=".4", lw=1)
        ax.set_xticks([0, 1], ["First contact", "Repeat"])
        ax.set(xlim=(-.35, 1.7), title=title, ylabel="B − A (transactions)")
        ax.grid(axis="y", alpha=.15)
    save(fig, output, "fig04_error_decomposition")

    fig, axes = plt.subplots(1, 3, figsize=(12.8, 3.8), sharex=True, sharey=True, layout="constrained")
    seed_colors = plt.cm.viridis(np.linspace(.12, .85, len(seeds)))
    for ax, arm in zip(axes, ARMS):
        for record, color, seed in zip(runs[arm], seed_colors, seeds):
            h = record["history"]
            ax.plot([x["epoch"] for x in h], [100 * x["val_ap"] for x in h], color=color, alpha=.75, lw=1, label=f"Seed {seed}")
            selected = next(x for x in h if x["epoch"] == record["best_epoch"])
            ax.scatter(selected["epoch"], 100 * selected["val_ap"], color=color, marker="o", s=24)
        common = np.mean([[100 * x["val_ap"] for x in r["history"][:20]] for r in runs[arm]], axis=0)
        ax.plot(np.arange(1, 21), common, color="black", lw=2, label="Mean, epochs 1–20")
        ax.set(xlabel="Epoch", title=LABELS[arm], xlim=(1, 30), ylim=(0, 65))
        ax.grid(alpha=.15)
    axes[0].set_ylabel("Validation average precision (%)")
    axes[1].legend(loc="upper center", bbox_to_anchor=(.5, -.23), ncol=3, fontsize=9, frameon=False)
    save(fig, output, "fig06_validation_trajectories")

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 3.8), layout="constrained")
    probe_runs = sorted(probes["runs"], key=lambda r: r["seed"])
    for ax, metric, title in zip(axes, ("average_precision", "roc_auc"), ("(a) Novelty prediction AP", "(b) Novelty prediction AUROC")):
        for kind, label, color, marker in (("raw_input", "Raw counts + ports", COLORS["cp"], "o"),
                                            ("penultimate", "Frozen 25-D representation", COLORS["cpn"], "s")):
            ax.plot(seeds, [r["probes"][kind]["test"][metric] for r in probe_runs], marker=marker, color=color, label=label)
        if metric == "average_precision":
            ax.plot(seeds, [r["probes"]["raw_input"]["test"]["novelty_prevalence"] for r in probe_runs], ls="--", color=".45", label="Novelty prevalence")
        ax.set(xticks=seeds, xlabel="Seed", ylim=(0, 1.04), title=title)
        ax.grid(alpha=.15)
    axes[0].legend(fontsize=9, frameon=False, loc="center left")
    save(fig, output, "fig07_probe")
    print(f"Wrote {root / 'analysis_notes.json'} and seven figures (PNG, PDF, SVG) in {output}")


if __name__ == "__main__":
    main()
