"""Decode pair novelty from a frozen AML model; this is an exploratory probe.

Fit a prespecified linear classifier on training-period representations only.
Compare it with the same classifier on the model's raw input, and an exact
count/port oracle. Decodability is not evidence that the AML classifier uses
the information, and failure of a linear probe does not exclude nonlinear
encoding. Probe outcomes never select or modify an AML training run.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import warnings

import numpy as np
import torch
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             confusion_matrix, roc_auc_score, roc_curve)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

_spec = importlib.util.spec_from_file_location("representation_probe_training", Path(__file__).with_name("representation_train.py"))
training = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(training)

SPLITS = ("train", "validation", "test")
DEFAULT_PROBE = {
    "arm": "cp", "selection": "best_validation", "representation": "penultimate_25d",
    "sample_sizes": {"train": 100000, "validation": 50000, "test": 100000},
    "C": 1.0, "max_iter": 2000, "sample_seed_offset": 4000000,
    "sampling_seed_offset": 5000000,
}


def validate_settings(settings):
    """Allow explanatory protocol notes without changing executable choices."""
    if any(settings.get(key) != value for key, value in DEFAULT_PROBE.items()):
        raise ValueError("Probe settings differ from the prespecified implementation")
    explanatory = {"interpretation", "controls", "fit", "threshold"}
    if set(settings) - set(DEFAULT_PROBE) - explanatory:
        raise ValueError("Unrecognized probe protocol setting")


def sample_rows(data, seed, settings, smoke=False):
    """Uniform samples without replacement; neither AML nor novelty labels select rows."""
    result = {}
    for split, name in enumerate(SPLITS):
        available = torch.nonzero(data["split"] == split).flatten().numpy()
        limit = 100 if smoke else settings["sample_sizes"][name]
        rng = np.random.default_rng(settings["sample_seed_offset"] + seed * 10 + split)
        result[name] = np.sort(rng.choice(available, size=min(limit, len(available)), replace=False))
    return result


@torch.no_grad()
def representations(model, data, features, rows, split, sampling_seed):
    """Return the 25-D vector supplied to the final AML classification layer."""
    loader, target_features, target_ids = training.make_loader(data, features, split, False, target_rows=torch.from_numpy(rows))
    if not np.array_equal(target_ids, rows):
        raise RuntimeError("Probe target rows changed in the graph loader")
    result = np.empty((len(rows), 25), dtype=np.float32)
    visited = np.zeros(len(rows), dtype=bool)
    captured = []

    def hook(_module, args):
        captured.append(args[0].detach().cpu().numpy().copy())

    state, was_training = training.rng_state(), model.training
    handle = model.mlp[-1].register_forward_pre_hook(hook)
    try:
        model.eval()
        training.seed_all(sampling_seed)
        for batch in loader:
            captured.clear()
            training.forward(model, batch, target_features)
            ids = batch.input_id.numpy()
            if len(captured) != 1 or captured[0].shape != (len(ids), 25) or visited[ids].any():
                raise RuntimeError("Unexpected probe representation shape or duplicate target")
            result[ids] = captured[0]
            visited[ids] = True
        if not visited.all() or not np.isfinite(result).all():
            raise RuntimeError("Incomplete or non-finite probe representations")
    finally:
        handle.remove()
        model.train(was_training)
        training.restore_rng(state)
    return result


def choose_threshold(labels, probability):
    """Largest threshold among ties for maximal validation balanced accuracy."""
    fpr, tpr, thresholds = roc_curve(labels, probability, drop_intermediate=False)
    finite = np.isfinite(thresholds)
    return float(thresholds[finite][np.argmax((tpr - fpr)[finite])])


def score(labels, probability, threshold):
    predicted = probability >= threshold
    tn, fp, fn, tp = confusion_matrix(labels, predicted, labels=[0, 1]).ravel()
    return {"n": int(len(labels)), "n_novel": int(labels.sum()),
            "novelty_prevalence": float(np.mean(labels)),
            "roc_auc": float(roc_auc_score(labels, probability)),
            "average_precision": float(average_precision_score(labels, probability)),
            "balanced_accuracy": float(balanced_accuracy_score(labels, predicted)),
            "threshold": float(threshold), "tn": int(tn), "fp": int(fp),
            "fn": int(fn), "tp": int(tp)}


def fit_probe(features, labels, settings):
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(
        C=settings["C"], max_iter=settings["max_iter"], solver="lbfgs"))
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", ConvergenceWarning)
        pipeline.fit(features["train"], labels["train"])
    converged = not any(issubclass(item.category, ConvergenceWarning) for item in recorded)
    probabilities = {name: pipeline.predict_proba(features[name])[:, 1] for name in ("validation", "test")}
    if not all(np.isfinite(values).all() for values in probabilities.values()):
        raise RuntimeError("Non-finite linear probe probabilities")
    threshold = choose_threshold(labels["validation"], probabilities["validation"])
    result = {"converged": converged,
              "iterations": int(pipeline.named_steps["logisticregression"].n_iter_.max()),
              "validation_selected_threshold": threshold,
              "validation": score(labels["validation"], probabilities["validation"], threshold),
              "test": score(labels["test"], probabilities["test"], threshold),
              "test_fixed_threshold": score(labels["test"], probabilities["test"], .5),
              "scaler_mean": pipeline.named_steps["standardscaler"].mean_.tolist(),
              "scaler_scale": pipeline.named_steps["standardscaler"].scale_.tolist(),
              "coefficient": pipeline.named_steps["logisticregression"].coef_.tolist(),
              "intercept": pipeline.named_steps["logisticregression"].intercept_.tolist(),
              "warnings": [str(item.message) for item in recorded]}
    return result, probabilities


def verify_run(args, seed, protocol_hash, data_hash):
    path = args.runs / f"cp_s{seed}.json"
    record = json.loads(path.read_text())
    if record["status"] != "complete" or record["cell"] != "cp" or record["seed"] != seed:
        raise RuntimeError(f"Incomplete or incorrect arm A result: {path}")
    if bool(record["config"]["smoke"]) != args.smoke:
        raise RuntimeError("Cannot mix smoke tests and production probe inputs")
    if record["data_sha256"] != data_hash:
        raise RuntimeError("Probe graph does not match AML training graph")
    if not args.smoke and record["protocol_sha256"] != protocol_hash:
        raise RuntimeError("Probe protocol does not match AML training protocol")
    for filename, expected in record["source_sha256"].items():
        if training.file_hash(Path(__file__).with_name(filename)) != expected:
            raise RuntimeError(f"AML source changed since training: {filename}")
    if record["config"]["device"] != args.device:
        raise RuntimeError("Use the same device type for AML training and the frozen encoder")
    checkpoint_path = args.runs / "checkpoints" / f"cp_s{seed}" / "best_validation.pt"
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if checkpoint["fingerprint"] != record["fingerprint"]:
        raise RuntimeError("Frozen probe checkpoint provenance mismatch")
    if checkpoint["epoch"] != record["evaluations"]["best_validation"]["epoch"]:
        raise RuntimeError("Probe is not using the selected AML checkpoint")
    return record, checkpoint_path, checkpoint


def write_summary(records, output, settings, smoke):
    metrics = ("roc_auc", "average_precision", "balanced_accuracy")
    summary = {"status": "complete", "smoke": smoke, "settings": settings,
               "seeds": [record["seed"] for record in records], "runs": records,
               "summary": {name: {metric: {
                   "mean": float(np.mean([r["probes"][name]["test"][metric] for r in records])),
                   "min": float(min(r["probes"][name]["test"][metric] for r in records)),
                   "max": float(max(r["probes"][name]["test"][metric] for r in records))}
                   for metric in metrics} for name in ("raw_input", "penultimate")}}
    training.atomic_json(output / "probe_summary.json", summary)
    lines = ["# Pair-novelty decoding from frozen AML representations", "",
             "This exploratory analysis asks whether pair novelty is linearly decodable from arm A's 25-dimensional penultimate representation. The AML encoder and its validation-selected checkpoint remain frozen. All probe coefficients and standardization statistics are fitted on training-period transfers; only the balanced-accuracy threshold uses validation transfers.", "",
             f"The prespecified sampling limits are {settings['sample_sizes']['train']:,} training, {settings['sample_sizes']['validation']:,} validation and {settings['sample_sizes']['test']:,} test transfers per seed. Sampling is uniform without replacement and independent of both labels. Smaller splits are used in full. The probe uses L2 logistic regression with C = {settings['C']} and at most {settings['max_iter']} iterations. All raw-input and representation probes use identical transfer samples within a seed.", "",
             "| Seed | Test novelty prevalence | Raw-input AUROC | Representation AUROC | Raw-input AP | Representation AP | Raw-input balanced accuracy | Representation balanced accuracy |", 
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for record in records:
        raw, hidden = (record["probes"][name]["test"] for name in ("raw_input", "penultimate"))
        lines.append(f"| {record['seed']} | {raw['novelty_prevalence']:.4f} | {raw['roc_auc']:.4f} | {hidden['roc_auc']:.4f} | {raw['average_precision']:.4f} | {hidden['average_precision']:.4f} | {raw['balanced_accuracy']:.4f} | {hidden['balanced_accuracy']:.4f} |")
    not_converged = [(r["seed"], name) for r in records for name in ("raw_input", "penultimate") if not r["probes"][name]["converged"]]
    lines.extend(["", "Balanced accuracy uses a validation-selected threshold. Results at the fixed threshold 0.5, confusion counts, coefficients and saved validation/test probabilities are also provided in the JSON and NPZ outputs. AP's no-skill reference is the test novelty prevalence, and AUROC's no-skill reference is 0.5. These are novelty-prediction metrics, not AML detection metrics.", "",
                  f"The deterministic equality oracle matched novelty on every sampled transfer in every split. Logistic-regression fits that reached the iteration limit: {not_converged or 'none'}. Any unconverged fit is descriptive and requires caution; the protocol does not silently increase its fitting budget.", "",
                  "**Interpretation.** A successful representation probe establishes linear decodability at this layer under this sampling protocol. It does not show that the AML decision uses that information, nor explain causally why an explicit flag helps. A weak probe can reflect a nonlinear representation or a limited probe; it does not prove the model failed to compute novelty. The raw-input classifier and exact oracle distinguish information availability from decodability after AML training.", "",
                  "In the raw integer features, port ranks satisfy port <= distinct count: a new pair has difference zero and a repeated pair has difference at least one. Thus novelty is linearly separable by distinct_count - port < 0.5; shared normalization preserves an affine separating rule. Imperfect performance of the finite, regularized raw-input logistic probe does not make that relation intrinsically nonlinear or invalidate the exact oracle.", "",
                  "The probes are exploratory, share one previously inspected synthetic dataset, and do not add independent datasets or confirmations of the primary AML contrast. Graph neighborhoods use the same cumulative transductive scopes as AML training/evaluation. Probe outcomes never change AML selection, stopping, seeds, or the primary endpoint.", "",
                  "![Figure 1. Novelty decoding from raw inputs and frozen representations.](figure_probe.png)", "",
                  "Figure 1. Each connected pair is one training seed, evaluated on its identical sampled test transfers. The AP baseline marks mean test novelty prevalence across the sampled cohorts. No intervals across transactions are presented as independent training-seed uncertainty.", ""])
    if smoke:
        lines.insert(2, "**TOY SMOKE TEST ONLY — not research evidence.**\n")
    (output / "PROBE_REPORT.md").write_text("\n".join(lines))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
        figure, axes = plt.subplots(1, 2, figsize=(8, 3.5), constrained_layout=True)
        for axis, metric, title in zip(axes, ("roc_auc", "average_precision"), ("AUROC", "Average precision")):
            for record in records:
                values = [record["probes"][name]["test"][metric] for name in ("raw_input", "penultimate")]
                axis.plot([0, 1], values, color="#65778b", alpha=.6, marker="o", linewidth=1)
            baseline = .5 if metric == "roc_auc" else np.mean([r["probes"]["raw_input"]["test"]["novelty_prevalence"] for r in records])
            axis.axhline(baseline, color="#a14f3e", linestyle="--", linewidth=1, label="No-skill reference")
            axis.set(xticks=[0, 1], xticklabels=["Raw model inputs", "Frozen representation"], ylabel=title, ylim=(-.02, 1.02), xlim=(-.2, 1.2))
        axes[0].legend(frameon=False, fontsize=8)
        figure.savefig(output / "figure_probe.png", dpi=220)
        figure.savefig(output / "figure_probe.pdf")
        plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Study output root; probe files go in its probes/ directory")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--seeds", nargs="+", type=int, help="Smoke-only override")
    args = parser.parse_args()
    if not args.smoke and (args.protocol is None or args.seeds is not None):
        parser.error("Production requires a frozen protocol and its seeds; manual seeds are smoke-only")
    protocol = json.loads(args.protocol.read_text()) if args.protocol else {}
    settings = protocol.get("probe", DEFAULT_PROBE)
    validate_settings(settings)
    seeds = args.seeds if args.smoke else protocol["analysis"]["seeds_by_cell"]["cp"]
    if not seeds:
        parser.error("Specify --seeds for a smoke test")
    if not args.smoke and args.threads != protocol["training"]["threads"]:
        parser.error("Probe threads must match the execution protocol")
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    device, device_info = training.configure_device(args.device)
    output = args.out / "probes"
    output.mkdir(parents=True, exist_ok=True)
    data_hash = training.file_hash(args.data)
    protocol_hash = training.file_hash(args.protocol) if args.protocol else None
    if not args.smoke and data_hash != protocol["data"]["sha256"]:
        raise RuntimeError("Probe data differs from the frozen protocol")
    data = torch.load(args.data, map_location="cpu", weights_only=False, mmap=True)
    features, normalization = training.prepare_features(data, "cp")
    results = []
    for seed in seeds:
        record, checkpoint_path, checkpoint = verify_run(args, seed, protocol_hash, data_hash)
        if training.json_hash(normalization) != record["normalization_sha256"]:
            raise RuntimeError("Probe feature normalization differs from AML training")
        metadata = {"seed": seed, "arm": "cp", "smoke": args.smoke,
                    "source_sha256": training.file_hash(__file__), "protocol_sha256": protocol_hash,
                    "data_sha256": data_hash, "checkpoint_sha256": training.file_hash(checkpoint_path),
                    "checkpoint_epoch": checkpoint["epoch"], "aml_fingerprint": record["fingerprint"],
                    "normalization_sha256": record["normalization_sha256"], "settings": settings,
                    "device_info": device_info}
        fingerprint = training.json_hash(metadata)
        destination = output / f"cp_s{seed}.json"
        if destination.exists():
            previous = json.loads(destination.read_text())
            archive = output / previous["predictions_file"]
            if previous.get("fingerprint") != fingerprint or previous.get("status") != "complete" or training.file_hash(archive) != previous["predictions_sha256"]:
                raise RuntimeError("Existing probe result has different provenance or damaged predictions")
            results.append(previous)
            print(f"[probe cp_s{seed}] already complete", flush=True)
            continue
        model = training.GIN(edge_dim=11).to(device)
        model.load_state_dict(checkpoint["model"])
        before = training.model_hash(model)
        if before != record["evaluations"]["best_validation"]["model_sha256"]:
            raise RuntimeError("Frozen checkpoint weights differ from selected AML model")
        rows = sample_rows(data, seed, settings, args.smoke)
        labels = {name: data["first_contact"][torch.from_numpy(ids)].numpy().reshape(-1).astype(np.int64) for name, ids in rows.items()}
        if any(set(np.unique(y)) != {0, 1} for y in labels.values()):
            raise RuntimeError("Every probe split must contain both novelty classes")
        hidden, raw, archive = {}, {}, {}
        for split, name in enumerate(SPLITS):
            ids = rows[name]
            raw[name] = features[torch.from_numpy(ids)].numpy()
            oracle = ((raw[name][:, 5] == raw[name][:, 9]) & (raw[name][:, 7] == raw[name][:, 8])).astype(np.int64)
            if not np.array_equal(oracle, labels[name]):
                raise RuntimeError("Normalized count/port equality fails the novelty oracle")
            hidden[name] = representations(model, data, features, ids, split, settings["sampling_seed_offset"] + seed * 10 + split)
            archive[f"{name}_row_id"], archive[f"{name}_novelty"] = ids, labels[name]
        if training.model_hash(model) != before:
            raise RuntimeError("Representation extraction modified the frozen AML encoder")
        probes = {}
        for name, inputs in (("raw_input", raw), ("penultimate", hidden)):
            probes[name], probabilities = fit_probe(inputs, labels, settings)
            archive.update({f"{name}_{split}_prob": values for split, values in probabilities.items()})
        archive_path = output / f"cp_s{seed}_predictions.npz"
        training.atomic_predictions(archive_path, **archive)
        result = {**metadata, "fingerprint": fingerprint, "status": "complete", "probes": probes,
                  "sample_counts": {name: len(ids) for name, ids in rows.items()}, "oracle_mismatches": 0,
                  "predictions_file": archive_path.name, "predictions_sha256": training.file_hash(archive_path)}
        training.atomic_json(destination, result)
        results.append(result)
        print(f"[probe cp_s{seed}] COMPLETE raw AUROC={probes['raw_input']['test']['roc_auc']:.4f} representation AUROC={probes['penultimate']['test']['roc_auc']:.4f}", flush=True)
    write_summary(results, output, settings, args.smoke)


if __name__ == "__main__":
    main()
