"""Aggregate the 2x2 x 5-seed runs into the estimand, the mechanism check and their uncertainty.

Per run: the epoch with the best validation F1 (within the first `budget` epochs) gives the test predictions
(thresholded at the validation-optimal threshold of that epoch, see train.py).
Uncertainty: hierarchical bootstrap, 5 seeds resampled within each cell x test transactions resampled
(Poisson weights, the same draw for all runs so cells stay paired on the test set).
F1 only depends on TP/FP/FN, so only transactions that are positive or predicted positive by some run matter.
Usage: python src/analyze.py [budget=5]  ->  results/summary.json, results/summary.md
"""
import glob
import json
import sys

import numpy as np
import torch

CELLS = ["base", "counts", "ports", "counts+ports"]
B = 4000


def load_runs(budget):
    runs = {c: [] for c in CELLS}
    for f in sorted(glob.glob("results/runs/*.json")):
        r = json.load(open(f))
        val = [e["val_f1"] for e in r["log"][:budget]]
        ep = int(np.argmax(val))
        pred = np.load(f.replace(".json", "_test_pred.npz"))["pred"][ep].astype(bool)
        runs[r["cell"]].append(dict(seed=r["seed"], epoch=ep, val_f1=val[ep], pred=pred, log=r["log"],
                                    test_ap=r["log"][ep]["test_ap"], test_f1_argmax=r["log"][ep]["test_f1_argmax"]))
    return runs


def effects(m):
    """m: dict cell -> mean F1 (arrays allowed). All contrasts in F1 points."""
    port_gain, identity = m["ports"] - m["base"], m["counts+ports"] - m["counts"]
    return {"count_gain": m["counts"] - m["base"], "port_gain": port_gain, "identity_effect": identity,
            "share_explained": 1 - identity / port_gain}


def analyse(runs, y, mask, rng):
    preds = {c: np.stack([r["pred"] for r in runs[c]], 1) for c in CELLS}          # [n_test, n_seeds]
    keep = mask & (y | np.any(np.concatenate(list(preds.values()), 1), 1))
    yk = y[keep]
    tp = {c: preds[c][keep] & yk[:, None] for c in CELLS}
    fp = {c: preds[c][keep] & ~yk[:, None] for c in CELLS}
    fn = {c: ~preds[c][keep] & yk[:, None] for c in CELLS}

    def cell_f1(c, w, seeds):
        TP, FP, FN = (w @ a[:, seeds].astype(np.float64) for a in (tp[c], fp[c], fn[c]))
        return 100 * 2 * TP / np.maximum(2 * TP + FP + FN, 1)                       # [n_boot, n_seeds]

    ones = np.ones((1, keep.sum()))
    per_seed = {c: cell_f1(c, ones, np.arange(len(runs[c])))[0] for c in CELLS}
    point = effects({c: per_seed[c].mean() for c in CELLS})
    w = rng.poisson(1.0, size=(B, keep.sum()))
    boot_means = {}
    for c in CELLS:
        n = len(runs[c])
        idx = rng.integers(0, n, size=(B, n))                                      # seed resample per draw
        f = cell_f1(c, w, np.arange(n))                                             # [B, n_seeds]
        boot_means[c] = np.take_along_axis(f, idx, 1).mean(1)
    boot = effects(boot_means)
    out = {"n_tx": int(mask.sum()), "n_laundering": int(y[mask].sum()),
           "cells": {c: {"mean": per_seed[c].mean(), "sd": per_seed[c].std(ddof=1), "per_seed": per_seed[c].tolist(),
                         "ci95": np.percentile(boot_means[c], [2.5, 97.5]).tolist()} for c in CELLS}}
    for k, v in point.items():
        out[k] = {"estimate": float(v), "ci95": np.percentile(boot[k], [2.5, 97.5]).tolist(),
                  "p_boot_le_0": float((boot[k] <= 0).mean())}
    return out


def main(budget=5):
    d = torch.load("data/hi_small.pt", weights_only=False)
    te = d["split"].numpy() == 2
    y = d["y"].numpy()[te].astype(bool)
    first = d["first_contact"].numpy()[te]
    runs = load_runs(budget)
    rng = np.random.default_rng(0)
    res = {"budget_epochs": budget, "n_runs": {c: len(runs[c]) for c in CELLS},
           "selected_epochs": {c: [r["epoch"] for r in runs[c]] for c in CELLS},
           "all": analyse(runs, y, np.ones_like(y), rng),
           "first_contact": analyse(runs, y, first, rng),
           "repeat": analyse(runs, y, ~first, rng)}
    # Threshold-free check: the same contrasts on test average precision (seed bootstrap only).
    ap = {c: 100 * np.array([r["test_ap"] for r in runs[c]]) for c in CELLS}
    boot_ap = {c: ap[c][rng.integers(0, len(ap[c]), size=(B, len(ap[c])))].mean(1) for c in CELLS}
    pt, bt = effects({c: ap[c].mean() for c in CELLS}), effects(boot_ap)
    res["test_ap"] = {"cells": {c: {"mean": ap[c].mean(), "sd": ap[c].std(ddof=1)} for c in CELLS},
                      **{k: {"estimate": float(pt[k]), "ci95": np.percentile(bt[k], [2.5, 97.5]).tolist()} for k in pt}}
    res["test_f1_argmax"] = {c: {"mean": 100 * np.mean([r["test_f1_argmax"] for r in runs[c]]),
                                 "sd": 100 * np.std([r["test_f1_argmax"] for r in runs[c]], ddof=1)} for c in CELLS}
    curves = {c: {k: np.mean([[e[k] for e in r["log"][:budget]] for r in runs[c]], 0).round(4).tolist()
                  for k in ("val_f1", "test_f1", "test_ap")} for c in CELLS}
    res["mean_curves"] = curves
    json.dump(res, open(f"results/summary_E{budget}.json", "w"), indent=1)

    fmt = lambda e: f"{e['estimate']:+.1f} [{e['ci95'][0]:+.1f}, {e['ci95'][1]:+.1f}]"
    L = [f"## Results (best-val epoch within {budget} epochs; runs per cell: {res['n_runs']})", "",
         "| Test subset | tx | laundering | Base | Counts | Ports | Counts+Ports |", "|---|---:|---:|---:|---:|---:|---:|"]
    for s in ("all", "first_contact", "repeat"):
        r = res[s]
        L.append(f"| {s} | {r['n_tx']:,} | {r['n_laundering']:,} | " +
                 " | ".join(f"{r['cells'][c]['mean']:.1f} ± {r['cells'][c]['sd']:.1f}" for c in CELLS) + " |")
    L += ["", "| Test subset | Count gain C−B | Port gain P−B | Identity effect (C+P)−C | Share of port gain explained by counts |",
          "|---|---:|---:|---:|---:|"]
    for s in ("all", "first_contact", "repeat"):
        r = res[s]
        sh = r["share_explained"]
        L.append(f"| {s} | {fmt(r['count_gain'])} | {fmt(r['port_gain'])} | {fmt(r['identity_effect'])} | "
                 f"{100*sh['estimate']:.0f}% [{100*sh['ci95'][0]:.0f}%, {100*sh['ci95'][1]:.0f}%] |")
    a = res["test_ap"]
    L += ["", "Threshold-free check (test average precision ×100, seed bootstrap) and Multi-GNN's argmax F1:", "",
          "| Metric | Base | Counts | Ports | Counts+Ports | Port gain | Identity effect | Share explained |", "|---|---:|---:|---:|---:|---:|---:|---:|",
          "| test AP | " + " | ".join(f"{a['cells'][c]['mean']:.1f} ± {a['cells'][c]['sd']:.1f}" for c in CELLS) +
          f" | {fmt(a['port_gain'])} | {fmt(a['identity_effect'])} | {100*a['share_explained']['estimate']:.0f}% "
          f"[{100*a['share_explained']['ci95'][0]:.0f}%, {100*a['share_explained']['ci95'][1]:.0f}%] |",
          "| test F1, argmax | " + " | ".join(f"{res['test_f1_argmax'][c]['mean']:.1f} ± {res['test_f1_argmax'][c]['sd']:.1f}"
                                              for c in CELLS) + " | | | |"]
    L += ["", "Mean validation / test F1 by epoch:", "", "| Cell | " + " | ".join(f"ep {i}" for i in range(budget)) + " |",
          "|---|" + "---:|" * budget]
    for c in CELLS:
        L.append(f"| {c} | " + " | ".join(f"{100*v:.1f} / {100*t:.1f}" for v, t in
                                          zip(curves[c]["val_f1"], curves[c]["test_f1"])) + " |")
    open(f"results/summary_E{budget}.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(*map(int, sys.argv[1:2]))
