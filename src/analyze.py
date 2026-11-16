"""Estimate what counts explain of the port gain in the GIN study.

The 2x2 factorial has ten seeds. Seeds 0-4 were analysed first; seeds 5-9 were added to settle the
interaction, with the test level for that second look fixed beforehand. Counts+novelty has seeds 0-4,
and contrasts with it are paired on those seeds.
Primary: full-test F1 at each run's best validation epoch among epochs 1--4.
Final-epoch and day-restricted results are explicitly post-hoc sensitivities.
Intervals describe matched-seed variation conditional on this dataset; the
ratio uses Fieller confidence sets and may be unbounded. No model is retrained.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from scipy import stats

CORE = ("base", "counts", "ports", "counts+ports")
NOVELTY = "counts+novelty"
CORE_SEEDS = tuple(range(10))
NOVELTY_SEEDS = tuple(range(5))
FIRST_LOOK = 5               # seeds 0-4 were analysed before seeds 5-9 were run
SECOND_LOOK_ALPHA = 0.0294   # Pocock level for two looks; applies to the interaction on all seeds
EPOCHS = 5
PAIRS = {
    "count_gain": ("counts", "base"),
    "port_gain": ("ports", "base"),
    "ports_after_counts": ("counts+ports", "counts"),
    "novelty_gain": (NOVELTY, "counts"),
    "ports_beyond_novelty": ("counts+ports", NOVELTY),
}
LABELS = {
    "count_gain": "Counts − Base",
    "port_gain": "Ports − Base",
    "ports_after_counts": "Counts+Ports − Counts",
    "interaction": "(Counts+Ports − Counts) − (Ports − Base)",
    "novelty_gain": "Counts+novelty − Counts",
    "ports_beyond_novelty": "Counts+Ports − Counts+novelty",
}


def summary(values):
    """Two-sided 95% t interval over independent matched seed blocks."""
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or len(a) < 2 or not np.isfinite(a).all():
        raise ValueError("Expected at least two finite per-seed values in seed order")
    mean, sd = float(a.mean()), float(a.std(ddof=1))
    se = sd / np.sqrt(len(a))
    half = float(stats.t.ppf(0.975, len(a) - 1) * se)
    return {"mean": mean, "sd": sd, "per_seed": a.tolist(), "ci95": [mean - half, mean + half]}


def p_value(values):
    """Two-sided p-value of the paired t test that the mean seed difference is zero."""
    a = np.asarray(values, dtype=float)
    if a.std(ddof=1) == 0:
        return 1.0 if a.mean() == 0 else 0.0
    return float(stats.ttest_1samp(a, 0.0).pvalue)


def quadratic_set(a, b, c):
    """Solve a*x*x+b*x+c <= 0; None denotes an infinite endpoint in JSON."""
    scale = max(abs(a), abs(b), abs(c))
    if scale == 0:
        return "all_real", [[None, None]]
    a, b, c = a / scale, b / scale, c / scale
    # A small nonzero leading coefficient can still bound a very wide set.
    # Do not discard polynomial degree based on the sizes of other coefficients.
    if a == 0:
        if b == 0:
            return ("all_real", [[None, None]]) if c <= 0 else ("empty", [])
        root = -c / b
        return "half_line", [[None, root]] if b > 0 else [[root, None]]
    discriminant = b * b - 4 * a * c
    disc_tol = 64 * np.finfo(float).eps * max(b * b, abs(4 * a * c))
    if discriminant < -disc_tol:
        return ("empty", []) if a > 0 else ("all_real", [[None, None]])
    if abs(discriminant) <= disc_tol:
        root = -b / (2 * a)
        return ("bounded", [[root, root]]) if a > 0 else ("all_real", [[None, None]])
    # Stable quadratic roots avoid subtracting nearly equal numbers.
    q = -0.5 * (b + np.copysign(np.sqrt(discriminant), b))
    lo, hi = sorted((float(q / a), float(c / q)))
    return ("bounded", [[lo, hi]]) if a > 0 else ("disjoint", [[None, lo], [hi, None]])


def fieller_share(numerator, denominator):
    """Confidence set for 1 - mean(numerator)/mean(denominator), retaining covariance."""
    n, d = np.asarray(numerator, dtype=float), np.asarray(denominator, dtype=float)
    ns, ds = summary(n), summary(d)
    vn, vd = np.var(n, ddof=1) / len(n), np.var(d, ddof=1) / len(d)
    cov = np.cov(n, d, ddof=1)[0, 1] / len(n)
    t2 = stats.t.ppf(0.975, len(n) - 1) ** 2
    nm, dm = ns["mean"], ds["mean"]
    kind, ratio_set = quadratic_set(dm * dm - t2 * vd,
                                     -2 * (nm * dm - t2 * cov), nm * nm - t2 * vn)
    share_set = [[None if hi is None else float(1 - hi),
                  None if lo is None else float(1 - lo)] for lo, hi in reversed(ratio_set)]
    identified = kind == "bounded" and ds["ci95"][0] > 0
    if ds["ci95"][0] <= 0 <= ds["ci95"][1]:
        reason = "Port gain is not distinguished from zero; a bounded positive-gain share is not identified."
    elif dm <= 0:
        reason = "There is no positive port gain to decompose."
    elif not identified:
        reason = "The Fieller confidence set does not identify a bounded positive-gain share."
    else:
        reason = "Bounded Fieller interval with a positive port-gain denominator."
    return {"status": "identified" if identified else "not_identified", "reason": reason,
            "estimate": float(1 - nm / dm) if identified else None,
            "confidence_set_type": kind, "ci95_set": share_set,
            "numerator_mean": nm, "denominator_mean": dm,
            "denominator_ci95": ds["ci95"], "covariance_of_means": float(cov)}


def contrasts(values):
    """Paired contrasts. Values are in seed order; two cells are compared on the seeds both have."""
    def paired(a, b):
        n = min(len(values[a]), len(values[b]))
        return np.asarray(values[a][:n]) - np.asarray(values[b][:n])

    differences = {key: paired(a, b) for key, (a, b) in PAIRS.items() if a in values and b in values}
    differences["interaction"] = differences["ports_after_counts"] - differences["port_gain"]
    result = {key: {**summary(value), "p_value": p_value(value)} for key, value in differences.items()}
    for item in result.values():
        n = len(item["per_seed"])
        # Descriptive sensitivity, not an achieved-power claim.
        item["approx_detectable_80pct"] = float((stats.t.ppf(0.975, n - 1) + stats.norm.ppf(0.8)) * item["sd"] / np.sqrt(n))
    return {"effects": result,
            "share_explained": fieller_share(differences["ports_after_counts"], differences["port_gain"])}


def looks(cells):
    """Factorial contrasts after the first seeds, on the added seeds alone, and on all seeds."""
    values = {cell: cells[cell]["per_seed"] for cell in CORE}
    n = len(CORE_SEEDS)

    def block(start, stop):
        return {"seeds": list(CORE_SEEDS[start:stop]),
                **contrasts({cell: per_seed[start:stop] for cell, per_seed in values.items()})}

    result = {"first_look": block(0, FIRST_LOOK), "added_seeds": block(FIRST_LOOK, n), "all_seeds": block(0, n)}
    final = result["all_seeds"]["effects"]["interaction"]
    half = float(stats.t.ppf(1 - SECOND_LOOK_ALPHA / 2, n - 1) * final["sd"] / np.sqrt(n))
    result["decision"] = {"contrast": "interaction", "alpha": SECOND_LOOK_ALPHA, "p_value": final["p_value"],
                          "interval_at_alpha": [final["mean"] - half, final["mean"] + half],
                          "significant": bool(final["p_value"] < SECOND_LOOK_ALPHA)}
    return result


def select_epoch(log, selection):
    if len(log) != EPOCHS:
        raise ValueError("The fixed design requires five completed epochs")
    if selection == "best_validation":
        return 1 + int(np.argmax([row["val_f1"] for row in log[1:]]))
    if selection == "final":
        return EPOCHS - 1
    raise ValueError(f"Unknown selection: {selection}")


def confusion(y, pred):
    y, pred = np.asarray(y, dtype=bool), np.asarray(pred, dtype=bool)
    tp = int(np.count_nonzero(y & pred))
    fp = int(np.count_nonzero(~y & pred))
    fn = int(np.count_nonzero(y & ~pred))
    tn = int(np.count_nonzero(~y & ~pred))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "f1": 100 * 2 * tp / max(2 * tp + fp + fn, 1)}


def load_runs(directory, y):
    """Reject incomplete core experiments and mismatched predictions before analysis."""
    directory = Path(directory)

    def saved(cell, seed):
        return ((directory / f"{cell}_s{seed}.json").is_file()
                and (directory / f"{cell}_s{seed}_test_pred.npz").is_file())

    missing = [f"{cell}_s{seed}" for cell in CORE for seed in CORE_SEEDS if not saved(cell, seed)]
    if missing:
        raise ValueError("Core experiment incomplete; missing " + ", ".join(missing))
    seeds = {cell: CORE_SEEDS for cell in CORE}
    if all(saved(NOVELTY, seed) for seed in NOVELTY_SEEDS):
        seeds[NOVELTY] = NOVELTY_SEEDS
    runs, common_hp = {}, None
    for cell, cell_seeds in seeds.items():
        runs[cell] = []
        for seed in cell_seeds:
            tag = directory / f"{cell}_s{seed}"
            record = json.loads(tag.with_suffix(".json").read_text())
            features = ["base"] + [key for key in ("counts", "novelty", "ports") if key in cell]
            if (record["cell"], record["seed"], record["epochs"], record["features"]) != (cell, seed, EPOCHS, features):
                raise ValueError(f"Run metadata disagrees with fixed design: {tag}")
            if common_hp is None:
                common_hp = record["hp"]
            if record["hp"] != common_hp:
                raise ValueError(f"Hyperparameters differ between cells/seeds: {tag}")
            log = record["log"]
            if len(log) != EPOCHS or [row["epoch"] for row in log] != list(range(EPOCHS)):
                raise ValueError(f"Expected epochs 0..4: {tag}")
            with np.load(str(tag) + "_test_pred.npz", allow_pickle=False) as archive:
                pred = archive["pred"]
            if pred.shape != (EPOCHS, len(y)) or not np.isin(pred, [0, 1]).all():
                raise ValueError(f"Invalid prediction shape or labels: {tag}")
            for epoch, row in enumerate(log):
                for key in ("val_f1", "test_f1", "val_ap", "test_ap", "val_f1_argmax", "test_f1_argmax", "threshold"):
                    if not np.isfinite(row[key]) or not 0 <= row[key] <= 1:
                        raise ValueError(f"Invalid {key}: {tag}, epoch {epoch}")
                if not np.isfinite(row["loss"]) or row["loss"] < 0:
                    raise ValueError(f"Invalid loss: {tag}, epoch {epoch}")
                if not np.isclose(confusion(y, pred[epoch])["f1"] / 100, row["test_f1"], rtol=0, atol=1e-12):
                    raise ValueError(f"Saved predictions disagree with test F1: {tag}, epoch {epoch}")
            runs[cell].append({"seed": seed, "log": log, "pred": pred.astype(bool)})
    return runs


def evaluate(runs, y, masks, selection):
    epochs = {cell: [select_epoch(run["log"], selection) for run in group] for cell, group in runs.items()}
    subsets = {}
    for name, mask in masks.items():
        cells = {}
        for cell, group in runs.items():
            counts = [confusion(y[mask], run["pred"][epoch, mask]) for run, epoch in zip(group, epochs[cell])]
            cells[cell] = {**summary([item["f1"] for item in counts]), "confusion_per_seed": counts}
        subsets[name] = {"n_tx": int(mask.sum()), "n_laundering": int(y[mask].sum()), "cells": cells,
                         **contrasts({cell: row["per_seed"] for cell, row in cells.items()})}
    metrics = {}
    for metric in ("test_ap", "test_f1_argmax", "val_ap"):
        values = {cell: [100 * run["log"][epoch][metric] for run, epoch in zip(group, epochs[cell])]
                  for cell, group in runs.items()}
        metrics[metric] = {"cells": {cell: summary(value) for cell, value in values.items()}, **contrasts(values)}
    return {"selected_epochs": epochs, "subsets": subsets, "metrics": metrics}


def build_summary(data, runs):
    te = data["split"].numpy() == 2
    y = data["y"].numpy()[te].astype(bool)
    day = (data["base"].numpy()[:, 0] // 86400).astype(np.int64)
    test_day = day[te]
    first = data["first_contact"].numpy()[te].astype(bool)
    masks = {"all": np.ones(len(y), dtype=bool), "days_8_9": (test_day >= 8) & (test_day < 10),
             "day_10_plus": test_day >= 10, "first_contact": first, "repeat": ~first,
             "repeat_free_accounts": data["repeat_free"].numpy()[te].astype(bool)}
    selections = {key: evaluate(runs, y, masks, key) for key in ("best_validation", "final")}
    distribution = [{"day": int(d), "n_tx": int((day == d).sum()),
                     "n_laundering": int(data["y"].numpy()[day == d].sum())} for d in np.unique(day)]
    primary = selections["best_validation"]["subsets"]
    final_val = selections["final"]["metrics"]["val_ap"]
    consistency = {}
    for effect in primary["all"]["effects"]:
        values = [primary["all"]["effects"][effect]["mean"], primary["days_8_9"]["effects"][effect]["mean"],
                  final_val["effects"][effect]["mean"]]
        signs = np.sign(values)
        consistency[effect] = {"full_test_f1": values[0], "days_8_9_f1": values[1], "final_validation_ap": values[2],
                               "same_nonzero_sign": bool(np.all(signs == signs[0]) and signs[0] != 0)}
    curves = {cell: {metric: [[100 * row[metric] for row in run["log"]] for run in group]
                     for metric in ("val_f1", "test_f1", "val_ap", "test_ap")}
              for cell, group in runs.items()}
    return {"protocol": {"primary_selection": "best_validation", "eligible_epochs": [1, 2, 3, 4],
                         "core_seeds": list(CORE_SEEDS), "supplementary_seeds": list(NOVELTY_SEEDS),
                         "first_look_seeds": list(CORE_SEEDS[:FIRST_LOOK]), "second_look_alpha": SECOND_LOOK_ALPHA,
                         "epochs": EPOCHS, "core_cells": list(CORE),
                         "supplementary_cell": NOVELTY, "uncertainty": "paired seed t, Fieller ratio; conditional on dataset",
                         "posthoc_sensitivities": ["final epoch", "days 8-9", "day 10+", "final validation AP"],
                         "infinite_endpoint_encoding": "null denotes negative infinity for a lower endpoint and positive infinity for an upper endpoint"},
            "n_runs": {cell: len(group) for cell, group in runs.items()},
            "supplementary_complete": NOVELTY in runs, "daily_distribution": distribution,
            "tail_flag_baseline": {**confusion(y, test_day >= 10), "rule": "flag every test edge on day >=10; post-hoc diagnostic"},
            "looks": looks(primary["all"]["cells"]),
            "selections": selections, "directional_consistency": consistency, "curves_per_seed": curves}


def fmt_effect(item):
    lo, hi = item["ci95"]
    p = "p<0.001" if item["p_value"] < 0.001 else f"p={item['p_value']:.3f}"
    return f"{item['mean']:+.2f} [{lo:+.2f}, {hi:+.2f}], {p}"


def fmt_share(item):
    if item["status"] != "identified":
        intervals = []
        for lo, hi in item["ci95_set"]:
            left = "(−∞" if lo is None else f"[{100 * lo:.1f}%"
            right = "+∞)" if hi is None else f"{100 * hi:.1f}%]"
            intervals.append(left + ", " + right)
        confidence_set = " ∪ ".join(intervals) or "∅"
        return f"Not identified. {item['reason']} Fieller share set: {confidence_set} ({item['confidence_set_type']})."
    lo, hi = item["ci95_set"][0]
    return f"{100 * item['estimate']:.1f}% (95% Fieller interval {100 * lo:.1f}% to {100 * hi:.1f}%)."


def fmt_share_short(item):
    if item["status"] != "identified":
        return "not identified"
    lo, hi = item["ci95_set"][0]
    return f"{100 * item['estimate']:.1f}% [{100 * lo:.1f}%, {100 * hi:.1f}%]"


def seed_range(seeds):
    return f"{seeds[0]}–{seeds[-1]}"


def look_report(look):
    """The factorial contrasts at the first look, on the added seeds alone, and on all seeds."""
    first, added = seed_range(CORE_SEEDS[:FIRST_LOOK]), seed_range(CORE_SEEDS[FIRST_LOOK:])
    decision, final = look["decision"], look["all_seeds"]["effects"]["interaction"]
    lines = ["## Two looks at the factorial", "",
             f"Seeds {first} were analysed first. Seeds {added} of the four factorial cells were added to settle whether the port "
             "gain differs with and without counts. The rule was fixed before the new runs: the difference counts as established "
             f"only if the test on all {len(CORE_SEEDS)} seeds has p < {decision['alpha']}, the Pocock level for two looks.", "",
             "| Seeds | Ports − Base | Counts+Ports − Counts | Difference between the two | Share explained [95% Fieller interval] |",
             "|---|---:|---:|---:|---:|"]
    for key, label in (("first_look", f"{first}, first look"), ("added_seeds", f"{added}, added runs alone"),
                       ("all_seeds", f"{seed_range(CORE_SEEDS)}, all")):
        e = look[key]["effects"]
        lines.append(f"| {label} | {fmt_effect(e['port_gain'])} | {fmt_effect(e['ports_after_counts'])} | "
                     f"{fmt_effect(e['interaction'])} | {fmt_share_short(look[key]['share_explained'])} |")
    if decision["significant"]:
        verdict = f"The port gain is {'larger' if final['mean'] > 0 else 'smaller'} with counts than without."
    else:
        verdict = "A difference between the two port gains is not established."
    lo, hi = decision["interval_at_alpha"]
    lines += ["", f"On all {len(CORE_SEEDS)} seeds the difference has p = {decision['p_value']:.4f}, "
              f"{'below' if decision['significant'] else 'not below'} {decision['alpha']}. {verdict} "
              f"The interval that matches this level is [{lo:+.2f}, {hi:+.2f}].", "",
              "The first look was tested at 0.05, so the two looks together do not hold the false-positive rate at 5%. "
              "The added runs alone are an independent check and carry no adjustment.", ""]
    return lines


def report(res):
    cells = list(res["n_runs"])
    primary = res["selections"]["best_validation"]
    final = res["selections"]["final"]
    full = primary["subsets"]["all"]
    extra = seed_range(NOVELTY_SEEDS)
    lines = ["# What do port numbers add beyond counterparty counts?", "",
             "## Primary experiment", "",
             f"The primary 2×2 comparison uses {len(CORE_SEEDS)} seeds ({seed_range(CORE_SEEDS)}) and five epochs per run. "
             "Each run selects the epoch with the highest "
             "validation F1 among epochs 1–4 (earliest tie), and applies that epoch's validation-selected threshold to the full test set. "
             f"Counts+novelty is supplementary and uses seeds {extra}; contrasts with it are paired on those seeds. "
             "All F1 and AP values below are percentage points. Each contrast shows its mean, "
             "95% paired-seed t interval and two-sided p-value.", "",
             "| Cell | Seeds | Test F1, mean ± SD | Test AP, mean ± SD | Selected epochs, in seed order |", "|---|---:|---:|---:|---|"]
    for cell in cells:
        f, ap = full["cells"][cell], primary["metrics"]["test_ap"]["cells"][cell]
        lines.append(f"| {cell} | {len(f['per_seed'])} | {f['mean']:.2f} ± {f['sd']:.2f} | {ap['mean']:.2f} ± {ap['sd']:.2f} | "
                     f"{primary['selected_epochs'][cell]} |")
    lines += ["", "| Core contrast | Mean [95% paired-seed t interval] | Seed differences |", "|---|---:|---|"]
    for key in ("count_gain", "port_gain", "ports_after_counts", "interaction"):
        item = full["effects"][key]
        lines.append(f"| {LABELS[key]} | {fmt_effect(item)} | " + ", ".join(f"{x:+.2f}" for x in item["per_seed"]) + " |")
    lines += ["", "**Primary estimand: share of the port gain explained by counts.** " + fmt_share(full["share_explained"]), "",
              "This is a ratio of cell-mean contrasts, not a causal mediation proportion. Values are not constrained to 0–100%. "
              "Failure to detect a residual gain does not establish that counts explain all of it.", ""]
    lines += look_report(res["looks"])
    lines += ["## Mechanism checks", "",
              "| Test stratum | Transactions | Laundering | Counts+Ports − Counts [95% CI] |", "|---|---:|---:|---:|"]
    for name in ("first_contact", "repeat", "repeat_free_accounts"):
        row = primary["subsets"][name]
        lines.append(f"| {name} | {row['n_tx']:,} | {row['n_laundering']:,} | {fmt_effect(row['effects']['ports_after_counts'])} |")
    if res["supplementary_complete"]:
        m = len(NOVELTY_SEEDS)
        lines += ["", f"Supplementary representation comparison, on seeds {extra}:", "",
                  "| Stratum | Counts F1 | Counts+Ports F1 | Counts+novelty F1 | Counts+novelty − Counts [95% CI] | "
                  "Counts+Ports − Counts+novelty [95% CI] |", "|---|---:|---:|---:|---:|---:|"]
        for name in ("all", "days_8_9", "first_contact", "repeat", "repeat_free_accounts"):
            row = primary["subsets"][name]
            f1 = [np.mean(row["cells"][cell]["per_seed"][:m]) for cell in ("counts", "counts+ports", NOVELTY)]
            lines.append(f"| {name} | {f1[0]:.2f} | {f1[1]:.2f} | {f1[2]:.2f} | {fmt_effect(row['effects']['novelty_gain'])} | "
                         f"{fmt_effect(row['effects']['ports_beyond_novelty'])} |")
    else:
        lines += ["", "Supplementary Counts+novelty runs are incomplete; no supplementary effect is reported."]
    lines += ["", "Ports equal distinct counts conditional on first contact, but the Counts-only model is not given that status. "
              "Counts and ports together reveal novelty; neighboring repeated edges can also transmit rank information. "
              "These strata do not isolate a causal identity mechanism. The supplementary contrast substitutes the port "
              "representation for an explicit novelty flag; it does not add ports to Counts+novelty. The JSON key "
              "ports_beyond_novelty is retained for compatibility and denotes this substitution contrast only.", "", "## Post-hoc sensitivity analyses", "",
              "Final-epoch and day-specific analyses were added after inspection of Base and Ports seed 0. They do not replace the "
              "original primary selection and are not independent replications.", "",
              "| Selection / subset | Ports − Base [95% CI] | Counts+Ports − Counts [95% CI] | Share explained |", "|---|---:|---:|---|"]
    for selection, data in (("best validation", primary), ("final epoch", final)):
        for name in ("all", "days_8_9"):
            row = data["subsets"][name]
            lines.append(f"| {selection} / {name} | {fmt_effect(row['effects']['port_gain'])} | {fmt_effect(row['effects']['ports_after_counts'])} | {fmt_share(row['share_explained'])} |")
    lines += ["", "| Final-epoch diagnostic | Ports − Base [95% CI] | Counts+Ports − Counts [95% CI] |", "|---|---:|---:|"]
    for metric in ("val_ap", "test_ap", "test_f1_argmax"):
        e = final["metrics"][metric]["effects"]
        lines.append(f"| {metric} | {fmt_effect(e['port_gain'])} | {fmt_effect(e['ports_after_counts'])} |")
    lines += ["", "The interaction is the port gain with counts minus the port gain without them. A positive value means the gain is "
              "larger with counts, which is the same statement as a negative share.", "",
              "| Outcome | Interaction, best validation epoch | Interaction, final epoch |", "|---|---:|---:|"]
    for label, kind, key in (("Full test F1", "subsets", "all"), ("Days 8–9 F1", "subsets", "days_8_9"),
                             ("Full test AP", "metrics", "test_ap"), ("Validation AP", "metrics", "val_ap"),
                             ("Full test F1 at a fixed 0.5 threshold", "metrics", "test_f1_argmax")):
        lines.append(f"| {label} | {fmt_effect(primary[kind][key]['effects']['interaction'])} | {fmt_effect(final[kind][key]['effects']['interaction'])} |")
    baseline = res["tail_flag_baseline"]
    lines += ["", f"The post-hoc rule ‘flag day 10 onward’ has test F1 {baseline['f1']:.2f}, TP={baseline['tp']:,}, "
              f"FP={baseline['fp']:,}, FN={baseline['fn']:,}. This diagnoses temporal composition; it is not a validated detector.", "",
              "| Contrast | Same nonzero sign: full-test F1, days 8–9 F1, final validation AP |", "|---|---|"]
    for key, item in res["directional_consistency"].items():
        lines.append(f"| {LABELS[key]} | {'yes' if item['same_nonzero_sign'] else 'no'} |")
    lines += ["", "Agreement in sign is directional consistency, not statistical significance.", "", "## Confusion counts", "",
              "Counts below are means across seeds at the primary selection; individual-seed TP, FP, FN and TN are retained in summary.json.", "",
              "| Subset | Cell | Seeds | TP | FP | FN |", "|---|---|---:|---:|---:|---:|"]

    def mean_counts(rows):
        return " | ".join(f"{np.mean([row[k] for row in rows]):.1f}" for k in ("tp", "fp", "fn"))

    for name, subset in primary["subsets"].items():
        for cell, item in subset["cells"].items():
            rows = item["confusion_per_seed"]
            lines.append(f"| {name} | {cell} | {len(rows)} | {mean_counts(rows)} |")
    if res["supplementary_complete"]:
        lines += ["", f"The same counts on seeds {extra} only, for comparing Counts and Counts+Ports with Counts+novelty:", "",
                  "| Subset | Cell | TP | FP | FN |", "|---|---|---:|---:|---:|"]
        for name in ("all", "days_8_9", "first_contact", "repeat"):
            for cell in ("counts", "counts+ports", NOVELTY):
                rows = primary["subsets"][name]["cells"][cell]["confusion_per_seed"][:len(NOVELTY_SEEDS)]
                lines.append(f"| {name} | {cell} | {mean_counts(rows)} |")
    lines += ["", "## Scope of the evidence", "",
              f"Intervals use matched seed blocks, {len(CORE_SEEDS)} for the factorial contrasts and {len(NOVELTY_SEEDS)} for contrasts with "
              "Counts+novelty, and approximate normality of seed contrasts. They quantify training/inference "
              "seed variability on this fixed dataset, not population-wide uncertainty. Secondary intervals are unadjusted exploratory comparisons. "
              "Approximate 80%-power sensitivity thresholds based on observed paired-seed SDs are retained in JSON; these are not achieved-power claims.", "",
              "The benchmark uses full evaluation graphs, graph-specific normalization, stochastic neighbor sampling, dropout and batch statistics "
              "at inference. Causal history features therefore do not make the complete model an online-causal detector. Five epochs do not "
              "establish replication of the published performance levels; the public reference code defaults to 100 epochs. Binary saved test "
              "predictions support subset F1/confusion counts, but not subset AP. "
              "An inconclusive or unstable share estimate is a valid research outcome."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/hi_small.pt"))
    parser.add_argument("--runs", type=Path, default=Path("results/runs"))
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    data = torch.load(args.data, weights_only=False)
    y = data["y"].numpy()[data["split"].numpy() == 2].astype(bool)
    runs = load_runs(args.runs, y)
    result = build_summary(data, runs)
    payload, markdown = json.dumps(result, indent=2, allow_nan=False), report(result)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(payload + "\n")
    (args.out / "summary.md").write_text(markdown)
    print(markdown)


if __name__ == "__main__":
    main()
