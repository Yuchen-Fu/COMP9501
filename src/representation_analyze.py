"""Audit and analyze the fixed, three-arm explicit-novelty follow-up.

All protocol-specified runs must be complete before effect estimates are reported. Scores and
thresholds are checked against the prepared graph and saved validation/test
probabilities. The original five-epoch study is not pooled into this analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.metrics import average_precision_score, precision_recall_curve
import torch

ROOT = Path(__file__).resolve().parents[1]
CELLS = ("cp", "cpn", "cn")
PAIRS = {"explicit_addition": ("cpn", "cp"),
         "explicit_replacement": ("cn", "cp"),
         "ranks_after_novelty": ("cpn", "cn")}
LABELS = {"cp": "Counts + Ports + zero", "cpn": "Counts + Ports + novelty",
          "cn": "Counts + novelty (zero port slots)",
          "explicit_addition": "CPN − CP (primary)",
          "explicit_replacement": "CN − CP (secondary)",
          "ranks_after_novelty": "CPN − CN (secondary)"}
SELECTIONS = ("best_validation", "epoch_5", "epoch_10", "epoch_20", "final")


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def design_from_protocol(protocol):
    analysis = protocol['analysis']
    cells = tuple(analysis['cells'])
    if (len(cells) != len(CELLS) or set(cells) != set(CELLS)
            or analysis['primary_selection'] != 'best_validation' or analysis['primary_metric'] != 'test_f1'):
        raise ValueError('Protocol differs from the prespecified analyzer design')
    supplied = analysis['seeds_by_cell']
    if set(supplied) != set(cells):
        raise ValueError('Protocol must specify a seed list for every analysis cell')
    seeds = {}
    for cell in cells:
        values = supplied[cell]
        if (len(values) < 2 or any(type(seed) is not int or seed < 0 for seed in values)
                or len(set(values)) != len(values)):
            raise ValueError(f'Expected at least two distinct nonnegative seed integers: {cell}')
        seeds[cell] = sorted(values)
    paired_seeds = {effect: sorted(set(seeds[a]) & set(seeds[b])) for effect, (a, b) in PAIRS.items()}
    if any(len(values) < 2 for values in paired_seeds.values()):
        raise ValueError('Every prespecified contrast requires at least two paired seed blocks')
    if seeds['cp'] != seeds['cpn']:
        raise ValueError('Primary addition contrast requires identical CP and CPN seed sets')
    return {'cells': list(cells), 'seeds_by_cell': seeds, 'paired_seeds': paired_seeds,
            'seeds': sorted({seed for values in seeds.values() for seed in values}),
            'n_runs': sum(map(len, seeds.values()))}


def paired_summary(values, seeds):
    a = np.asarray(values, dtype=float)
    n = len(seeds)
    if n < 2 or a.shape != (n,) or not np.isfinite(a).all():
        raise ValueError('Expected one finite value per declared seed, with at least two seeds')
    mean, sd = float(a.mean()), float(a.std(ddof=1))
    half = float(stats.t.ppf(.975, n - 1) * sd / math.sqrt(n))
    lo, hi = mean - half, mean + half
    return {"mean": mean, "sd": sd, "ci95": [lo, hi], "per_seed": a.tolist(),
            "n": n, "df": n - 1, "seeds": list(seeds),
            "interval_direction": "positive" if lo > 0 else ("negative" if hi < 0 else "unresolved")}


def metrics(y, probability, threshold):
    y = np.asarray(y, dtype=bool)
    prediction = np.asarray(probability) >= threshold
    tp = int(np.count_nonzero(y & prediction))
    fp = int(np.count_nonzero(~y & prediction))
    fn = int(np.count_nonzero(y & ~prediction))
    tn = int(np.count_nonzero(~y & ~prediction))
    return {"f1": 100 * 2 * tp / max(2 * tp + fp + fn, 1),
            "ap": 100 * float(average_precision_score(y, probability)),
            "precision": 100 * tp / max(tp + fp, 1),
            "recall": 100 * tp / max(tp + fn, 1),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn, "flagged": tp + fp}


def validation_threshold(y, probability):
    precision, recall, thresholds = precision_recall_curve(y, probability)
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    index = int(f1.argmax())
    return float(thresholds[index]), float(f1[index])


def require_close(found, expected, context, tolerance=1e-8):
    if not np.isclose(found, expected, rtol=0, atol=tolerance):
        raise ValueError(f"Metric mismatch ({context}): {found} != {expected}")


def inventory(directory, design):
    records, missing = {}, []
    for cell in design['cells']:
        for seed in design['seeds_by_cell'][cell]:
            path = directory / f"{cell}_s{seed}.json"
            if not path.is_file():
                missing.append(path.name)
                continue
            record = json.loads(path.read_text())
            if record.get("status") != "complete":
                missing.append(path.name + " (not complete)")
                continue
            if record.get("cell") != cell or record.get("seed") != seed:
                raise ValueError(f"Run identity mismatch: {path}")
            records[(cell, seed)] = record
    return records, missing


def verify_metadata(records, protocol_path, design):
    protocol = json.loads(protocol_path.read_text())
    expected_protocol_sha = file_sha(protocol_path)
    common = {}
    checks = 0
    for (cell, seed), run in records.items():
        if run["protocol_sha256"] != expected_protocol_sha:
            raise ValueError(f"Protocol differs for {cell}, seed {seed}")
        for key in ("source_sha256", "data_sha256", "hp", "parameter_count", "normalization_sha256", "device_info"):
            if key not in common:
                common[key] = run[key]
            if run[key] != common[key]:
                raise ValueError(f"Unmatched {key}: {cell}, seed {seed}")
            checks += 1
        history = run["history"]
        if len(history) != run["epochs_completed"] or [r["epoch"] for r in history] != list(range(1, len(history) + 1)):
            raise ValueError(f"Incomplete epoch history: {cell}, seed {seed}")
        for row in history:
            if not np.isfinite([row["val_ap"], row["val_f1"], row["threshold"], row["loss"], row["sec"]]).all():
                raise ValueError(f"Nonfinite history: {cell}, seed {seed}")
            if not 0 <= row["val_ap"] <= 1 or not 0 <= row["val_f1"] <= 1 or not 0 <= row["threshold"] <= 1:
                raise ValueError(f"Invalid probability metric: {cell}, seed {seed}")
        best = int(np.argmax([row["val_ap"] for row in history])) + 1
        if run["evaluations"]["best_validation"]["epoch"] != best:
            raise ValueError(f"Checkpoint not selected by exact validation AP with earliest ties: {cell}, seed {seed}")
        if run["evaluations"]["final"]["epoch"] != len(history):
            raise ValueError(f"Final checkpoint mismatch: {cell}, seed {seed}")
        config = run["config"]
        if 'device' not in common:
            common['device'] = config['device']
        if config['device'] != common['device'] or config['device'] != run['device_info']['type']:
            raise ValueError(f'Unmatched execution device: {cell}, seed {seed}')
        if 'device' in protocol['training'] and config['device'] != protocol['training']['device']:
            raise ValueError(f'Execution device differs from protocol: {cell}, seed {seed}')
        if config['smoke'] or config['max_train_batches'] is not None:
            raise ValueError(f'Smoke or truncated training cannot enter final inference: {cell}, seed {seed}')
        for key in ('max_epochs', 'min_epochs', 'patience', 'min_delta', 'threads'):
            if config[key] != protocol['training'][key]:
                raise ValueError(f'Training protocol mismatch for {key}: {cell}, seed {seed}')
        if (config['normalization'] != 'training_only_shared_port_count' or config['evaluation'] != 'eval_mode_fixed_sample_rng'
                or config['selection'] != 'maximum_validation_AP_earliest_tie'
                or config['input_slots'] != protocol['model']['slots'] or len(config['input_slots']) != 11):
            raise ValueError(f'Invalid matched protocol configuration: {cell}, seed {seed}')
        if len(history) < config["min_epochs"] or len(history) > config["max_epochs"]:
            raise ValueError(f"Run violates fixed epoch limits: {cell}, seed {seed}")
        progress_ap, stale, expected_stop = -1., 0, None
        for row in history:
            if row['val_ap'] >= progress_ap + config['min_delta']:
                progress_ap, stale = row['val_ap'], 0
            else:
                stale += 1
            if row['plateau_epochs'] != stale:
                raise ValueError(f'Incorrect validation patience count: {cell}, seed {seed}')
            expected_stop = ('validation_ap_plateau' if row['epoch'] >= config['min_epochs'] and stale >= config['patience']
                             else ('maximum_epochs' if row['epoch'] == config['max_epochs'] else None))
            if expected_stop is not None and row['epoch'] != len(history):
                raise ValueError(f'Training continued past its stopping rule: {cell}, seed {seed}')
        if expected_stop is None or run['stop_reason'] != expected_stop:
            raise ValueError(f'Incorrect training termination: {cell}, seed {seed}')
        for selection in SELECTIONS[1:-1]:
            expected = int(selection.split("_")[1])
            if expected <= len(history) and run["evaluations"].get(selection, {}).get("epoch") != expected:
                raise ValueError(f"Missing fixed checkpoint {selection}: {cell}, seed {seed}")
    if common['data_sha256'] != protocol['data']['sha256']:
        raise ValueError('Completed-run data hash differs from the frozen protocol')
    for seed in design['seeds']:
        hashes = {records[(cell, seed)]["initial_model_sha256"] for cell in design['cells']
                  if seed in design['seeds_by_cell'][cell]}
        if len(hashes) != 1:
            raise ValueError(f"Initial model states differ within seed {seed}")
        checks += 1
    return {"protocol_sha256": expected_protocol_sha, "matched_metadata_checks": checks, **common}


def graph_evaluation_data(path):
    graph = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
    split = graph["split"].numpy()
    test_ids, val_ids = np.flatnonzero(split == 2), np.flatnonzero(split == 1)
    labels = graph["y"].numpy()
    test_day = (graph["base"].numpy()[test_ids, 0] // 86400).astype(np.int64)
    first = graph["first_contact"].numpy()[test_ids].astype(bool)
    masks = {"all": np.ones(len(test_ids), dtype=bool),
             "days_8_9": (test_day >= 8) & (test_day < 10),
             "day_10_plus": test_day >= 10, "first_contact": first, "repeat": ~first}
    return test_ids, val_ids, labels[test_ids], labels[val_ids], masks


def audit_evaluations(records, directory, graph_data):
    test_ids, val_ids, test_y, val_y, masks = graph_data
    audited = {}
    archives = {}
    metric_checks = 0
    for (cell, seed), run in records.items():
        by_path = {}
        per_selection = {}
        for selection in SELECTIONS:
            evaluation = run["evaluations"].get(selection)
            if evaluation is None:
                continue
            path = directory / evaluation["predictions_file"]
            if path not in by_path:
                if file_sha(path) != evaluation['predictions_sha256']:
                    raise ValueError(f'Prediction archive checksum mismatch: {path}')
                with np.load(path, allow_pickle=False) as saved:
                    required = ("row_id", "y", "prob", "val_row_id", "val_y", "val_prob")
                    if not all(key in saved for key in required):
                        raise ValueError(f"Incomplete prediction archive: {path}")
                    if not np.array_equal(saved["row_id"], test_ids) or not np.array_equal(saved["val_row_id"], val_ids):
                        raise ValueError(f"Score rows do not align with temporal split: {path}")
                    if not np.array_equal(saved["y"], test_y) or not np.array_equal(saved["val_y"], val_y):
                        raise ValueError(f"Score labels do not match prepared data: {path}")
                    prob, val_prob = saved["prob"], saved["val_prob"]
                    for values, ids in [(prob, test_ids), (val_prob, val_ids)]:
                        if values.shape != ids.shape or not np.isfinite(values).all() or values.min() < 0 or values.max() > 1:
                            raise ValueError(f"Invalid saved probabilities: {path}")
                    threshold, val_f1 = validation_threshold(val_y, val_prob)
                    val_ap = float(average_precision_score(val_y, val_prob))
                    subsets = {name: metrics(test_y[mask], prob[mask], threshold) for name, mask in masks.items()}
                    by_path[path] = {"threshold": threshold, "val_f1": val_f1, "val_ap": val_ap,
                                     "subsets": subsets}
                archives[str(path.relative_to(directory))] = evaluation['predictions_sha256']
            checked = by_path[path]
            if evaluation['predictions_sha256'] != archives[str(path.relative_to(directory))]:
                raise ValueError(f'Conflicting checksum for an aliased prediction archive: {path}')
            for key in ("threshold", "val_f1", "val_ap"):
                require_close(checked[key], evaluation[key], f"{cell} s{seed} {selection} {key}")
                metric_checks += 1
            for stored, metric in [("test_f1", "f1"), ("test_ap", "ap")]:
                require_close(checked["subsets"]["all"][metric] / 100, evaluation[stored], f"{cell} s{seed} {selection} {stored}")
                metric_checks += 1
            history = run["history"][evaluation["epoch"] - 1]
            for key in ("threshold", "val_f1", "val_ap"):
                require_close(checked[key], history[key], f"{cell} s{seed} {selection} reproduced {key}", tolerance=1e-7)
                metric_checks += 1
            per_selection[selection] = {"epoch": evaluation["epoch"], **checked}
        audited[(cell, seed)] = per_selection
    return audited, {"unique_prediction_archives": len(archives), "recomputed_metric_checks": metric_checks,
                     "prediction_sha256": archives}


def summarize(audited, masks, test_y, design):
    results = {}
    for selection in SELECTIONS:
        if not all(selection in audited[(cell, seed)] for cell in design['cells'] for seed in design['seeds_by_cell'][cell]):
            results[selection] = {"status": "not_available_for_every_run"}
            continue
        subsets = {}
        for name, mask in masks.items():
            cells = {}
            for cell in design['cells']:
                seeds = design['seeds_by_cell'][cell]
                rows = [audited[(cell, seed)][selection]["subsets"][name] for seed in seeds]
                cells[cell] = {"f1": paired_summary([r["f1"] for r in rows], seeds),
                               "ap": paired_summary([r["ap"] for r in rows], seeds),
                               "seeds": seeds,
                               "confusion_per_seed": [{k: r[k] for k in ("tp", "fp", "fn", "tn", "flagged", "precision", "recall")} for r in rows]}
            effects = {}
            for effect, (a, b) in PAIRS.items():
                seeds = design['paired_seeds'][effect]
                effects[effect] = {'n': len(seeds), 'seeds': seeds, 'positive_arm': a, 'reference_arm': b}
                for metric in ('f1', 'ap'):
                    a_values = np.asarray([audited[(a, seed)][selection]['subsets'][name][metric] for seed in seeds])
                    b_values = np.asarray([audited[(b, seed)][selection]['subsets'][name][metric] for seed in seeds])
                    effects[effect][metric] = {**paired_summary(a_values - b_values, seeds),
                                               'paired_arm_means': {a: float(a_values.mean()), b: float(b_values.mean())}}
            subsets[name] = {"n_tx": int(mask.sum()), "n_positive": int(test_y[mask].sum()), "cells": cells, "effects": effects}
        results[selection] = {"status": "complete", "subsets": subsets,
                              "selected_epochs": {cell: [audited[(cell, seed)][selection]["epoch"] for seed in design['seeds_by_cell'][cell]] for cell in design['cells']},
                              "thresholds": {cell: [audited[(cell, seed)][selection]["threshold"] for seed in design['seeds_by_cell'][cell]] for cell in design['cells']}}
    return results


def decide(primary):
    f1 = primary["effects"]["explicit_addition"]["f1"]
    ap = primary["effects"]["explicit_addition"]["ap"]
    if f1["ci95"][0] > 0 and ap["ci95"][0] > 0:
        status = "supported"
        statement = "Explicit novelty improves both test F1 and AP while retaining ports under the new protocol."
    elif f1["ci95"][0] > 0:
        status = "f1_gain_only"
        statement = "A positive F1 gain is supported, but a general prediction improvement is not established because AP does not corroborate it with a positive interval."
    elif f1["ci95"][1] < 0:
        status = "contradicted_on_primary_metric"
        statement = "The primary F1 contrast favors the port control; the intended positive addition claim is contradicted under this protocol."
    else:
        status = "inconclusive"
        statement = "The primary F1 interval includes zero; the experiment does not establish a positive addition effect or equivalence."
    return {"status": status, "statement": statement,
            "rule": "The broad prediction claim requires positive 95% intervals for both primary F1 and corroborating AP.",
            "mechanism": "No outcome identifies failure to infer novelty inside the model; input effects are not a causal decomposition of internal computation."}


def stopping_diagnostics(records, design):
    result = []
    for cell in design['cells']:
        for seed in design['seeds_by_cell'][cell]:
            run = records[(cell, seed)]
            completed = run["epochs_completed"]
            config = run["config"]
            result.append({"cell": cell, "seed": seed, "epochs_completed": completed,
                           "stop_reason": run["stop_reason"],
                           "hit_epoch_cap": completed == config["max_epochs"],
                           "selected_epoch": run["evaluations"]["best_validation"]["epoch"],
                           "selected_within_last_five_epochs": run["evaluations"]["best_validation"]["epoch"] > completed - 5,
                           "last_plateau_epochs": run["history"][-1].get("plateau_epochs"),
                           "validation_ap_first": run["history"][0]["val_ap"],
                           "validation_ap_final": run["history"][-1]["val_ap"]})
    return result


def robustness_diagnostics(selections, conclusion, stopping):
    checks = []
    for selection, subset in [('best_validation', 'days_8_9'), ('epoch_20', 'all'), ('final', 'all')]:
        row = selections[selection]
        if row['status'] != 'complete':
            checks.append({'selection': selection, 'subset': subset, 'status': 'unavailable'})
            continue
        effect = row['subsets'][subset]['effects']['explicit_addition']
        positive = effect['f1']['mean'] > 0 and effect['ap']['mean'] > 0
        checks.append({'selection': selection, 'subset': subset,
                       'status': 'positive_both_metrics' if positive else 'direction_not_preserved',
                       'f1_mean_points': effect['f1']['mean'], 'ap_mean_points': effect['ap']['mean'],
                       'paired_n': effect['n']})
    all_positive = all(row['status'] == 'positive_both_metrics' for row in checks)
    status = ('supported_descriptively' if conclusion['status'] == 'supported' and all_positive
              else ('primary_not_supported' if conclusion['status'] != 'supported'
                    else ('incomplete_sensitivity' if any(row['status'] == 'unavailable' for row in checks)
                          else 'sensitivity_disagreement')))
    return {'status': status,
            'rule': 'Primary F1/AP intervals positive, and F1/AP point contrasts positive on days 8–9, fixed epoch 20 and final epoch.',
            'checks': checks, 'capped_runs': sum(row['hit_epoch_cap'] for row in stopping),
            'interpretation': 'Sensitivity directions are descriptive, reuse the same data, and do not establish convergence, cross-dataset generalization or additional multiplicity-controlled discoveries.'}


def interval(value):
    return f'{value["mean"]:+.2f} [{value["ci95"][0]:+.2f}, {value["ci95"][1]:+.2f}]'


def power_report(power):
    if not power:
        return ['No power-planning assumptions were included in the frozen protocol.', '']
    lines = [f'The frozen design targets {100 * power["target_power"]:.0f}% power at two-sided α = {power["alpha"]:.3g} using a {power["test"]} test. '
             f'The planning SD is {power["pilot_paired_sd_f1_points"]:.3f} F1 points. Its source is {power["planning_source"]}.', '',
             '| Paired seed blocks | Planning minimum detectable F1 difference (points) |', '|---:|---:|']
    for n, mdes in sorted(power['mdes_f1_points'].items(), key=lambda item: int(item[0])):
        lines.append(f'| {n} | {mdes:.3f} |')
    if power.get('sensitivity'):
        lines += ['', '| Assumed paired SD (F1 points) | Paired seed blocks | Planning detectable F1 difference (points) |', '|---:|---:|---:|']
        for row in power['sensitivity']:
            lines.append(f'| {row["paired_sd_f1_points"]:.3f} | {row["n_seeds"]} | {row["mdes_f1_points"]:.3f} |')
    return lines + ['', power['interpretation'],
                    'These are prospective sensitivity calculations, not achieved power calculated from the observed effect. The replacement pilot variance need not equal the addition-contrast variance. AP has a separate sampling variance; the planning F1 calculation does not guarantee the joint F1-and-AP support rule.', '']


def report(summary, path, include_figures=True):
    primary = summary["selections"]["best_validation"]["subsets"]["all"]
    decision = summary["conclusion"]
    design = summary['design']
    lines = ['# Explicit pair novelty: controlled follow-up', '', f'**Decision: {decision["status"]}.** {decision["statement"]}', '',
             'The primary comparison retains all count and port information, replacing a constant zero input slot with the explicit novelty bit. All arms have the same parameter count and initialization within seed blocks. This follow-up does not pool the original 25 runs.', '',
             'Novelty means the first observed directed account pair within this dataset window, not necessarily a new banking relationship. It is already derivable from the count and port inputs. The experiment therefore tests an explicit representation of available information, not an increase in information content or theoretical expressivity.', '',
             '## Primary endpoint', '',
             'Each model uses its exact highest validation-AP checkpoint, with earliest ties; its F1 threshold is selected on validation at that checkpoint. Test outcomes choose neither checkpoint nor threshold. Values below are percentage points, with nominal paired-seed 95% t intervals.', '',
             '| Input group | Seeds (n) | Test F1, mean ± seed SD | Test AP, mean ± seed SD |', '|---|---|---:|---:|']
    for cell in design['cells']:
        row = primary["cells"][cell]
        seeds = ', '.join(map(str, row['seeds']))
        lines.append(f'| {LABELS[cell]} | {seeds} (n={row["f1"]["n"]}) | {row["f1"]["mean"]:.2f} ± {row["f1"]["sd"]:.2f} | {row["ap"]["mean"]:.2f} ± {row["ap"]["sd"]:.2f} |')
    lines += ['', 'These per-arm means describe different seed cohorts when the arm sizes differ. The contrasts below are computed within shared seed blocks; subtracting unmatched full-arm means is not the paired estimate.', '',
              '| Paired comparison | Shared seeds (n) | F1 difference [95% CI] | AP difference [95% CI] |', '|---|---|---:|---:|']
    for effect in PAIRS:
        values = primary['effects'][effect]
        seeds = ', '.join(map(str, values['seeds']))
        lines.append(f'| {LABELS[effect]} | {seeds} (n={values["n"]}) | {interval(values["f1"])} | {interval(values["ap"])} |')
    lines += ['', '| Paired comparison | F1 means within shared seeds (positive arm / reference) | AP means within shared seeds (positive arm / reference) |', '|---|---:|---:|']
    for effect, (a, b) in PAIRS.items():
        values = primary['effects'][effect]
        f, ap = values['f1']['paired_arm_means'], values['ap']['paired_arm_means']
        lines.append(f'| {LABELS[effect]} | {f[a]:.2f} / {f[b]:.2f} | {ap[a]:.2f} / {ap[b]:.2f} |')
    lines += ['', 'The addition contrast is primary. Replacement and rank-after-novelty contrasts are secondary and unadjusted. A nonsignificant result does not establish equivalence, and a favorable secondary result cannot rescue an unsupported primary claim.', '']
    if include_figures:
        lines += ['![Paired test F1 and AP differences](figures/paired-contrasts.png)', '',
                  '**Figure 1.** Mean within-seed differences with nominal 95% Student t intervals. Each comparison uses only its shared seeds; secondary intervals are unadjusted.', '']
    lines += ['## AML screening consequences', '',
              'These are averages across each arm’s declared seeds on the same test transfers. Fractional counts are seed averages. Precision and recall are mean per-seed percentages, not ratios of the averaged counts.', '',
              '| Group | True alerts (TP) | False alerts (FP) | Missed laundering (FN) | Total alerts | Precision (%) | Recall (%) |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for cell in design['cells']:
        rows = primary['cells'][cell]['confusion_per_seed']
        values = [float(np.mean([row[key] for row in rows])) for key in ('tp', 'fp', 'fn', 'flagged', 'precision', 'recall')]
        lines.append('| ' + LABELS[cell] + ' | ' + ' | '.join(f'{value:.2f}' for value in values) + ' |')
    lines += ['', f'A and B use the same {len(design["seeds_by_cell"]["cp"])} seed blocks. C uses {len(design["seeds_by_cell"]["cn"])}; its matched contrasts are reported above. Each model has its own validation-selected threshold, so this table does not compare performance at a fixed investigator workload. Alerts are transactions, not distinct cases.', '',
              '## Fixed-checkpoint and temporal checks', '',
              '| Selection / test subset | Paired n | CPN − CP, F1 [95% CI] | CPN − CP, AP [95% CI] |', '|---|---:|---:|---:|']
    for selection, subset in [('best_validation','days_8_9'), ('epoch_5','all'), ('epoch_10','all'), ('epoch_20','all'), ('final','all')]:
        row = summary['selections'][selection]
        if row['status'] == 'complete':
            e = row['subsets'][subset]['effects']['explicit_addition']
            lines.append(f'| {selection}; {subset} | {e["n"]} | {interval(e["f1"])} | {interval(e["ap"])} |')
        else:
            lines.append(f'| {selection}; {subset} | — | Not available for every run | Not available |')
    lines += ['', 'These checks reuse the same models and dataset and are not independent replications. The final checkpoint can occur at different epochs under the shared validation-only stopping rule; fixed-checkpoint views address equal training duration.', '',
              f'**Within-benchmark robustness: {summary["within_benchmark_robustness"]["status"]}.** '
              + summary['within_benchmark_robustness']['rule'] + ' This descriptive check does not change the primary endpoint or its decision. '
              + summary['within_benchmark_robustness']['interpretation'], '',
              '## First-contact and repeat transfers', '',
              '| Subset | Positive / total transfers | CPN − CP, F1 [95% CI] | CN − CP, F1 [95% CI] | CPN − CN, F1 [95% CI] |', '|---|---:|---:|---:|---:|']
    for name in ['first_contact','repeat']:
        row = summary['selections']['best_validation']['subsets'][name]
        e = row['effects']
        lines.append(f'| {name} | {row["n_positive"]:,} / {row["n_tx"]:,} | {interval(e["explicit_addition"]["f1"])} | {interval(e["explicit_replacement"]["f1"])} | {interval(e["ranks_after_novelty"]["f1"])} |')
    sizes = ', '.join(f'{LABELS[effect]}: n={len(design["paired_seeds"][effect])}' for effect in PAIRS)
    lines += ['', f'Stratum comparisons use the same seed intersections as the overall contrasts ({sizes}).', '',
              'Confusion counts, validation-selected thresholds and every seed value are retained in `summary.json`. These comparisons use each model’s validation-selected threshold, not a common alert budget; flags are transactions, not unique investigations. A gain can support transaction-level screening on these data; it does not by itself estimate investigation workload savings, prevented losses or performance on another bank.', '',
              '## Training termination and scope', '',
              '| Group / seed | Epochs | Stop reason | Selected epoch | At epoch cap? |', '|---|---:|---|---:|---|']
    for row in summary['stopping']:
        lines.append(f'| {row["cell"]} / {row["seed"]} | {row["epochs_completed"]} | {row["stop_reason"]} | {row["selected_epoch"]} | {"Yes" if row["hit_epoch_cap"] else "No"} |')
    if include_figures:
        lines += ['', '![Individual validation AP trajectories](figures/validation-trajectories.png)', '',
                  '**Figure 2.** Every run’s validation AP through its own stopping epoch. Lines describe individual seeds; different stopping times are not pooled into a changing-cohort mean.', '']
    caps = sum(row['hit_epoch_cap'] for row in summary['stopping'])
    unplateaued = sum(row['stop_reason'] == 'maximum_epochs' for row in summary['stopping'])
    early_selected = sum(row['selected_epoch'] < 20 for row in summary['stopping'])
    late_selected = sum(row['selected_within_last_five_epochs'] for row in summary['stopping'])
    lines += ['', f'{caps} of {summary["n_runs"]} runs reached the epoch cap. Neither reaching the cap nor satisfying validation patience proves mathematical convergence. An incomplete plateau record or continuing improvement prevents a convergence claim.', '',
              f'{unplateaued} runs stopped at the cap without meeting validation patience; {late_selected} selected their best checkpoint within the last five completed epochs. '
              f'{early_selected} selected a checkpoint before epoch 20. The minimum training duration does not force the validation-selected model to come from a late epoch; the fixed-epoch-20 and final evaluations address this distinction.', '',
              f'The primary inference describes {len(design["paired_seeds"]["explicit_addition"])} paired training-seed blocks, and each secondary contrast uses its declared intersection, on one previously inspected synthetic dataset. Intervals use Student t with n−1 degrees of freedom, conditional on this fixed dataset. They quantify seed variability, not uncertainty over future banks or datasets. It is not a new untouched test set, cross-bank replication, or online deployment evaluation. Graph evaluation remains transductive. Training-only normalization, shared count/port scaling and evaluation mode control implementation differences; they mean the new scores should not be pooled with the original protocol.', '',
              'Each evaluated period’s graph can contain transactions later than an individual target transaction. Historical features alone do not turn this into an online causal prediction evaluation. Equal-timestamp transactions follow a reproducible ordering; earlier in that order is not the same as strictly earlier wall-clock time.', '',
              decision['mechanism'], '',
              '## Precision planned before the new runs', '']
    lines += power_report(summary['protocol']['analysis'].get('power'))
    lines += ['## Separate representation and drift checks', '',
              'The [representation probe report](probes/PROBE_REPORT.md) examines recoverability of novelty, and the [data drift report](DRIFT_REPORT.md) describes temporal data differences. These are separately generated analyses. Their existence or outcome is not a completion condition for the main paired model experiment; read their own status before citing them as evidence.', '',
              '## Integrity checks', '',
              f'All {summary["n_runs"]} runs passed protocol, common source, frozen-data, initialization, shared normalization, device and parameter-count checks. {summary["audit"]["unique_prediction_archives"]} unique score archives were checked against the prepared graph; {summary["audit"]["recomputed_metric_checks"]} saved metric values were independently recomputed. Model selection was checked against the complete validation histories.', '',
              'Prediction-file hashes and all machine-readable results are in `summary.json`. No significance-directed seed replacement, model selection or interval clipping is performed by this analyzer.', '']
    path.write_text('\n'.join(lines))


def plots(summary, directory):
    os.environ.setdefault('MPLCONFIGDIR', '/tmp/representation-followup-mpl')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'axes.spines.top':False,
                         'axes.spines.right':False, 'svg.fonttype':'none', 'pdf.fonttype':42})
    directory.mkdir(exist_ok=True)
    primary = summary['selections']['best_validation']['subsets']['all']
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, metric in zip(axes, ['f1','ap']):
        for y, effect in enumerate(PAIRS):
            e = primary['effects'][effect][metric]
            ax.errorbar(e['mean'], y, xerr=[[e['mean']-e['ci95'][0]],[e['ci95'][1]-e['mean']]], fmt='o', capsize=4,
                        color='#1F4F8A' if effect=='explicit_addition' else '#38786F')
        ax.axvline(0, color='#888888', lw=1)
        ax.set(yticks=range(len(PAIRS)),
               yticklabels=[f'{LABELS[x]} (n={primary["effects"][x]["n"]})' for x in PAIRS],
               xlabel=f'{metric.upper()} difference (points)', title=metric.upper())
        ax.invert_yaxis(); ax.grid(axis='x', alpha=.2)
    fig.tight_layout()
    for ext in ['png','svg']: fig.savefig(directory/f'paired-contrasts.{ext}',dpi=220)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = {'cp':'#1F4F8A','cpn':'#38786F','cn':'#A65F46'}
    for cell in CELLS:
        histories = summary['histories'][cell]
        seeds = summary['design']['seeds_by_cell'][cell]
        for seed, history in zip(seeds, histories):
            x = [r['epoch'] for r in history]; y=[100*r['val_ap'] for r in history]
            ax.plot(x, y, color=colors[cell], alpha=.35, lw=1,
                    label=f'{LABELS[cell]} (n={len(seeds)})' if seed==seeds[0] else None)
    ax.set(xlabel='Completed training epochs', ylabel='Validation AP (%)', title='Individual validation trajectories; runs end under the fixed stopping rule')
    ax.grid(alpha=.2); ax.legend(frameon=False); fig.tight_layout()
    for ext in ['png','svg']: fig.savefig(directory/f'validation-trajectories.{ext}',dpi=220)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, default=ROOT/'results/representation_followup/runs')
    parser.add_argument('--protocol', type=Path, default=ROOT/'results/representation_followup/protocol.json')
    parser.add_argument('--data', type=Path, default=ROOT/'data/hi_small.pt')
    parser.add_argument('--out', type=Path, default=ROOT/'results/representation_followup')
    parser.add_argument('--no-plots', action='store_true')
    args = parser.parse_args()
    torch.set_num_threads(2)
    args.out.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(args.protocol.read_text())
    design = design_from_protocol(protocol)
    records, missing = inventory(args.runs, design)
    if missing:
        partial = {'status':'incomplete', 'completed':len(records), 'required':design['n_runs'], 'missing':missing,
                   'design':design,
                   'inference':'No effect estimates or conclusions are produced before all fixed runs complete.'}
        write_json(args.out/'status.json', partial)
        print(json.dumps(partial, indent=2))
        return
    metadata = verify_metadata(records, args.protocol, design)
    if metadata['data_sha256'] != file_sha(args.data):
        raise ValueError('Prepared graph hash differs from completed runs')
    graph_data = graph_evaluation_data(args.data)
    audited, audit = audit_evaluations(records, args.runs, graph_data)
    test_ids, val_ids, test_y, val_y, masks = graph_data
    selections = summarize(audited, masks, test_y, design)
    stopping = stopping_diagnostics(records, design)
    conclusion = decide(selections['best_validation']['subsets']['all'])
    result = {'status':'complete', 'n_runs':design['n_runs'], 'seeds':design['seeds'], 'cells':design['cells'],
              'design':design,
              'protocol':protocol, 'audit':{**metadata, **audit}, 'selections':selections,
              'conclusion':conclusion, 'stopping':stopping,
              'within_benchmark_robustness':robustness_diagnostics(selections, conclusion, stopping),
              'histories':{cell:[records[(cell, seed)]['history'] for seed in design['seeds_by_cell'][cell]] for cell in design['cells']}}
    write_json(args.out/'summary.json', result)
    write_json(args.out/'analysis.json', {'status':'complete', 'n_runs':design['n_runs'], 'design':design,
                                         'primary_selection':'best_validation', 'primary_metric':'test_f1',
                                         'primary_effect':result['selections']['best_validation']['subsets']['all']['effects']['explicit_addition'],
                                         'conclusion':result['conclusion'], 'stopping':result['stopping'],
                                         'within_benchmark_robustness':result['within_benchmark_robustness']})
    report(result, args.out/'FOLLOWUP_REPORT.md', include_figures=not args.no_plots)
    if not args.no_plots: plots(result, args.out/'figures')
    write_json(args.out/'status.json', {'status':'complete','completed':design['n_runs'],'required':design['n_runs'],
                                       'conclusion':result['conclusion'], 'within_benchmark_robustness':result['within_benchmark_robustness']})
    print(json.dumps({'status':'complete', 'runs':design['n_runs'], 'output':str(args.out), 'conclusion':result['conclusion']}, indent=2))


if __name__ == '__main__':
    main()
