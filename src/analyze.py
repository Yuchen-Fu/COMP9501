"""Aggregate the runs into the estimand, the mechanism check and their uncertainty.

Per run: the epoch with the best validation F1 (epochs >= 1; epoch 0 only warms up) is selected, and its test
predictions are thresholded at that epoch's validation-optimal threshold (train.py).
Uncertainty, two ways, and the wider one is the one to trust:
  * hierarchical bootstrap: seeds resampled within each cell x test transactions resampled with Poisson weights,
    laundering transactions in whole patterns (connected components of the test laundering subgraph), the same draw
    for every run so cells stay paired on the test set;
  * Welch t-interval over the 5 per-seed F1s of each cell (differences only).
Usage: python src/analyze.py  ->  results/summary.json, results/summary.md
"""
import glob
import json

import numpy as np
import torch
from scipy import stats
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

CELLS = ["base", "counts", "ports", "counts+ports", "counts+novelty"]
PUBLISHED = {"base": 28.7, "ports": 54.9}               # Egressy et al. (AAAI 2024), GIN on HI-Small, minority F1
B = 4000


def load_runs():
    runs = {c: [] for c in CELLS}
    for f in sorted(glob.glob("results/runs/*.json")):
        r = json.load(open(f))
        val = [e["val_f1"] for e in r["log"]]
        ep = 1 + int(np.argmax(val[1:]))               # best validation epoch, epoch 0 excluded
        e = r["log"][ep]
        runs[r["cell"]].append(dict(seed=r["seed"], epoch=ep, log=r["log"], test_ap=100 * e["test_ap"],
                                    test_f1_argmax=100 * e["test_f1_argmax"],
                                    pred=np.load(f.replace(".json", "_test_pred.npz"))["pred"][ep].astype(bool)))
    return {c: v for c, v in runs.items() if v}


def effects(m):
    """Contrasts between cell means (F1 points). share = 1 - [(C+P) - C] / [P - B]."""
    out = {"count_gain": m["counts"] - m["base"], "port_gain": m["ports"] - m["base"],
           "identity_effect": m["counts+ports"] - m["counts"]}
    out["share_explained"] = 1 - out["identity_effect"] / out["port_gain"]
    if "counts+novelty" in m:                          # decomposition of the identity effect
        out["novelty_effect"] = m["counts+novelty"] - m["counts"]
        out["rank_identity_effect"] = m["counts+ports"] - m["counts+novelty"]
        out["share_explained_counts_novelty"] = 1 - out["rank_identity_effect"] / out["port_gain"]
    return out


def welch(a, b):
    """95% Welch t-interval for mean(a) - mean(b)."""
    va, vb = np.var(a, ddof=1) / len(a), np.var(b, ddof=1) / len(b)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    h = stats.t.ppf(0.975, df) * np.sqrt(va + vb)
    return [np.mean(a) - np.mean(b) - h, np.mean(a) - np.mean(b) + h]


PAIRS = {"count_gain": ("counts", "base"), "port_gain": ("ports", "base"), "identity_effect": ("counts+ports", "counts"),
         "novelty_effect": ("counts+novelty", "counts"), "rank_identity_effect": ("counts+ports", "counts+novelty")}


def analyse(runs, y, cluster, mask, rng):
    cells = list(runs)
    preds = {c: np.stack([r["pred"] for r in runs[c]], 1) for c in cells}               # [n_test, n_seeds]
    keep = mask & (y | np.any(np.concatenate(list(preds.values()), 1), 1))               # TN never affect F1
    yk = y[keep]
    parts = {c: [(preds[c][keep] & yk[:, None]), (preds[c][keep] & ~yk[:, None]), (~preds[c][keep] & yk[:, None])]
             for c in cells}

    def f1(c, w):                                                                         # w: [n_draws, n_keep]
        tp, fp, fn = (w @ a.astype(np.float64) for a in parts[c])
        return 100 * 2 * tp / np.maximum(2 * tp + fp + fn, 1)                            # [n_draws, n_seeds]

    per_seed = {c: f1(c, np.ones((1, keep.sum())))[0] for c in cells}
    _, inv = np.unique(cluster[keep], return_inverse=True)
    w = rng.poisson(1.0, size=(B, inv.max() + 1))[:, inv]                                 # one weight per pattern
    boot = {c: np.take_along_axis(f1(c, w), rng.integers(0, len(runs[c]), (B, len(runs[c]))), 1).mean(1)
            for c in cells}
    point, bt = effects({c: per_seed[c].mean() for c in cells}), effects(boot)
    out = {"n_tx": int(mask.sum()), "n_laundering": int(y[mask].sum()),
           "cells": {c: {"mean": per_seed[c].mean(), "sd": per_seed[c].std(ddof=1), "per_seed": per_seed[c].tolist()}
                     for c in cells}}
    for k, v in point.items():
        out[k] = {"estimate": float(v), "ci95_boot": np.nanpercentile(bt[k], [2.5, 97.5]).tolist(),
                  "p_boot_le_0": float(np.mean(bt[k] <= 0))}
        if k in PAIRS:
            out[k]["ci95_welch"] = welch(per_seed[PAIRS[k][0]], per_seed[PAIRS[k][1]])
    out["p_port_gain_draw_le_0"] = float(np.mean(bt["port_gain"] <= 0))                  # ratio unreliable if > 0
    return out


def main():
    d = torch.load("data/hi_small.pt", weights_only=False)
    te = d["split"].numpy() == 2
    y = d["y"].numpy()[te].astype(bool)
    u, v = d["edge_index"].numpy()[:, te]
    n = d["n_nodes"]
    _, comp = connected_components(coo_matrix((np.ones(y.sum()), (u[y], v[y])), shape=(n, n)), directed=False)
    cluster = np.where(y, comp[u], n + np.arange(len(y)))                                # laundering: pattern id
    first = d["first_contact"].numpy()[te]
    runs = load_runs()
    rng = np.random.default_rng(0)
    strata = {"all": np.ones_like(y), "first_contact": first, "repeat": ~first,
              "repeat_free_accounts": d["repeat_free"].numpy()[te]}
    res = {"n_runs": {c: len(r) for c, r in runs.items()},
           "selected_epochs": {c: [r["epoch"] for r in runs[c]] for c in runs},
           **{s: analyse(runs, y, cluster, m, rng) for s, m in strata.items()}}
    ap = {c: np.array([r["test_ap"] for r in runs[c]]) for c in runs}                  # threshold-free check
    apb = effects({c: ap[c][rng.integers(0, len(ap[c]), (B, len(ap[c])))].mean(1) for c in runs})
    res["test_ap"] = {"cells": {c: {"mean": ap[c].mean(), "sd": ap[c].std(ddof=1)} for c in runs},
                      **{k: {"estimate": float(v), "ci95_boot": np.nanpercentile(apb[k], [2.5, 97.5]).tolist()}
                         for k, v in effects({c: ap[c].mean() for c in runs}).items()}}
    res["test_f1_argmax"] = {c: {"mean": np.mean([r["test_f1_argmax"] for r in runs[c]]),
                                 "sd": np.std([r["test_f1_argmax"] for r in runs[c]], ddof=1)} for c in runs}
    res["mean_curves"] = {c: {k: np.mean([[100 * e[k] for e in r["log"]] for r in runs[c]], 0).round(2).tolist()
                              for k in ("val_f1", "test_f1", "test_ap")} for c in runs}
    json.dump(res, open("results/summary.json", "w"), indent=1)
    open("results/summary.md", "w").write(report(res, list(runs)))
    print(report(res, list(runs)))


def report(res, cells):
    ci = lambda e, k="ci95_boot": f"[{e[k][0]:+.1f}, {e[k][1]:+.1f}]"
    eff = lambda e: f"{e['estimate']:+.1f} {ci(e)}" + (f" / {ci(e, 'ci95_welch')}" if "ci95_welch" in e else "")
    pct = lambda e: f"{100 * e['estimate']:.0f}% [{100 * e['ci95_boot'][0]:.0f}%, {100 * e['ci95_boot'][1]:.0f}%]"
    L = [f"Runs per cell: {res['n_runs']}. Test F1 ×100 at the validation-chosen threshold; mean ± sd over seeds.", "",
         "| Test subset | tx | laundering | " + " | ".join(cells) + " |", "|---|---:|---:|" + "---:|" * len(cells)]
    for s in ("all", "first_contact", "repeat", "repeat_free_accounts"):
        r = res[s]
        L.append(f"| {s} | {r['n_tx']:,} | {r['n_laundering']:,} | " +
                 " | ".join(f"{r['cells'][c]['mean']:.1f} ± {r['cells'][c]['sd']:.1f}" for c in cells) + " |")
    keys = [k for k in ("count_gain", "port_gain", "identity_effect", "novelty_effect", "rank_identity_effect")
            if k in res["all"]]
    L += ["", "Contrasts in F1 points: estimate [95% cluster/seed bootstrap] / [95% Welch t over seeds].", "",
          "| Test subset | " + " | ".join(keys) + " |", "|---|" + "---:|" * len(keys)]
    for s in ("all", "first_contact", "repeat"):
        L.append(f"| {s} | " + " | ".join(eff(res[s][k]) for k in keys) + " |")
    a = res["all"]
    L += ["", f"**Share of the port gain explained by counts** = 1 − [(C+P) − C] / [P − B] = {pct(a['share_explained'])}"
              f" (bootstrap draws with P − B ≤ 0: {100 * a['p_port_gain_draw_le_0']:.1f}%)."]
    if "share_explained_counts_novelty" in a:
        L.append(f"**Share explained by counts + novelty flag** = 1 − [(C+P) − (C+N)] / [P − B] = "
                 f"{pct(a['share_explained_counts_novelty'])}.")
    t, g = res["test_ap"], res["test_f1_argmax"]
    L += ["", "| Check | " + " | ".join(cells) + " | share explained |", "|---|" + "---:|" * (len(cells) + 1),
          "| test AP ×100 | " + " | ".join(f"{t['cells'][c]['mean']:.1f} ± {t['cells'][c]['sd']:.1f}" for c in cells) +
          f" | {pct(t['share_explained'])} |",
          "| test F1 at p > 0.5 | " + " | ".join(f"{g[c]['mean']:.1f} ± {g[c]['sd']:.1f}" for c in cells) + " | |",
          "| published (100 epochs, p > 0.5) | " + " | ".join(f"{PUBLISHED[c]:.1f}" if c in PUBLISHED else "" for c in cells) + " | |",
          "", "Mean validation / test F1 by epoch (selected epochs: " + str(res["selected_epochs"]) + "):", "",
          "| Cell | " + " | ".join(f"ep {i}" for i in range(len(res["mean_curves"][cells[0]]["val_f1"]))) + " |",
          "|---|" + "---:|" * len(res["mean_curves"][cells[0]]["val_f1"])]
    for c in cells:
        cv = res["mean_curves"][c]
        L.append(f"| {c} | " + " | ".join(f"{a:.1f} / {b:.1f}" for a, b in zip(cv["val_f1"], cv["test_f1"])) + " |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
