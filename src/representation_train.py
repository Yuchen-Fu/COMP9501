"""Train one matched representation arm; test scoring follows training completion.

All arms use eleven fixed input slots: base(4), counts(4), ports(2), novelty(1).
Continuous features use training-only normalization, with each distinct-count
and corresponding port sharing a scale so their equality remains explicit.
Missing slots are zeroed after normalization. Evaluation uses eval mode and a fixed sampling RNG while
preserving the training RNG. Existing research runs are never read or modified.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import time

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import average_precision_score, f1_score, precision_recall_curve
from torch_geometric.data import Data
from torch_geometric.loader import LinkNeighborLoader

_spec = importlib.util.spec_from_file_location("representation_reference_train", Path(__file__).with_name("train.py"))
_reference = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reference)
GIN, HP = _reference.GIN, _reference.HP

FIXED_EPOCHS = (5, 10, 20)
INPUT_SLOTS = ["time", "amount", "currency", "format", "out_total", "out_distinct",
               "in_total", "in_distinct", "in_port", "out_port", "novelty"]
NORMALIZATION_POLICY = "training_only_shared_port_count"
SHARED_SCALE_PAIRS = ((5, 9), (7, 8))


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def model_hash(model):
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def atomic_torch(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(value, temporary)
    os.replace(temporary, path)


def atomic_predictions(path, **values):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **values)
    os.replace(temporary, path)


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    if torch.cuda.is_initialized():
        torch.cuda.manual_seed_all(seed)


def rng_state():
    state = {"python": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state()}
    if torch.cuda.is_initialized():
        state["cuda"] = torch.cuda.get_rng_state_all()
    return state


def restore_rng(state):
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    if "cuda" in state:
        torch.cuda.set_rng_state_all(state["cuda"])


def configure_device(name):
    """Use one declared device; unsupported deterministic GPU kernels fail loudly."""
    info = {"type": name, "torch_version": torch.__version__}
    if name == "cpu":
        return torch.device("cpu"), info
    workspace = os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    if workspace not in (":4096:8", ":16:8"):
        raise RuntimeError("CUDA deterministic execution requires CUBLAS_WORKSPACE_CONFIG=:4096:8 or :16:8")
    if not torch.cuda.is_available():
        raise RuntimeError("--device cuda requires a CUDA-enabled PyTorch build and an available GPU")
    torch.cuda.set_device(0)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cuda.matmul.allow_tf32 = False
    props = torch.cuda.get_device_properties(0)
    info.update({"index": 0, "name": props.name, "capability": [props.major, props.minor],
                 "memory_bytes": props.total_memory, "visible_device_count": torch.cuda.device_count(),
                 "cuda_runtime": torch.version.cuda, "cudnn_version": torch.backends.cudnn.version(),
                 "deterministic_algorithms": True, "cublas_workspace": workspace, "tf32": False})
    return torch.device("cuda:0"), info


def prepare_features(data, cell):
    """Fit training statistics, preserving count/port equality before arm masking."""
    raw = torch.cat([data[key].double() for key in ("base", "counts", "ports")], dim=1)
    train = raw[data["split"] == 0]
    mean, scale = train.mean(0), train.std(0)
    for count_column, port_column in SHARED_SCALE_PAIRS:
        pooled = train[:, [count_column, port_column]].reshape(-1)
        mean[[count_column, port_column]] = pooled.mean()
        scale[[count_column, port_column]] = pooled.std()
    scale[scale == 0] = 1
    if not torch.isfinite(mean).all() or not torch.isfinite(scale).all():
        raise ValueError("Training normalization requires finite statistics and at least two observations")
    features = torch.empty((len(raw), 11), dtype=torch.float32)
    features[:, :10] = ((raw - mean) / scale).float()
    novelty = data["first_contact"].reshape(-1).float()
    if not torch.all((novelty == 0) | (novelty == 1)):
        raise ValueError("Novelty must be a binary first-contact indicator")
    # Check the complete graph before CN masks ports and CP masks novelty.
    for start in range(0, len(raw), 1_000_000):
        rows = slice(start, start + 1_000_000)
        expected = novelty[rows].bool()
        for count_column, port_column in SHARED_SCALE_PAIRS:
            raw_equal = raw[rows, count_column] == raw[rows, port_column]
            normalized_equal = features[rows, count_column] == features[rows, port_column]
            if not torch.equal(raw_equal, expected):
                raise ValueError("Raw count/port equality does not reproduce the first-contact indicator")
            if not torch.equal(normalized_equal, expected):
                raise ValueError("Float32 normalization changed count/port equality")
    features[:, 10] = novelty if cell != "cp" else 0
    if cell == "cn":
        features[:, 8:10] = 0
    stats = {"policy": NORMALIZATION_POLICY,
             "mean": mean.tolist(), "scale": scale.tolist(), "fit_split": "train",
             "shared_scale_pairs": [[INPUT_SLOTS[i], INPUT_SLOTS[j]] for i, j in SHARED_SCALE_PAIRS],
             "shared_scale_fit": "pooled_values_from_both_columns_sample_std_ddof_1",
             "equality_verified_rows": len(raw),
             "novelty_scaling": "raw_0_or_1", "input_slots": INPUT_SLOTS}
    return features, stats


def make_loader(data, features, split, shuffle, target_rows=None):
    """Build a cumulative graph; optional global target IDs retain caller order."""
    graph_mask = data["split"] <= split
    graph_ids = torch.nonzero(graph_mask).flatten()
    if target_rows is None:
        target_ids = torch.nonzero(data["split"] == split).flatten()
    else:
        target_ids = torch.as_tensor(target_rows, dtype=torch.long, device="cpu")
        if target_ids.ndim != 1 or not len(target_ids):
            raise ValueError("target_rows must be a nonempty one-dimensional list of global row IDs")
        if (target_ids < 0).any() or (target_ids >= len(data["split"])).any():
            raise ValueError("target_rows contains an out-of-range global row ID")
        if len(torch.unique(target_ids)) != len(target_ids):
            raise ValueError("target_rows must contain unique global row IDs")
        if not torch.all(data["split"][target_ids] == split):
            raise ValueError("Every target_rows entry must belong to the requested split")
    local_targets = torch.searchsorted(graph_ids, target_ids)
    graph = Data(x=torch.zeros(data["n_nodes"], 1),
                 edge_index=data["edge_index"][:, graph_mask],
                 edge_attr=features[graph_mask], num_nodes=data["n_nodes"])
    assert torch.equal(graph_ids[local_targets], target_ids)
    loader = LinkNeighborLoader(
        graph, num_neighbors=HP["num_neighbors"], edge_label_index=graph.edge_index[:, local_targets],
        edge_label=data["y"][target_ids], batch_size=HP["batch_size"],
        shuffle=shuffle, num_workers=0)
    return loader, features[target_ids], target_ids.numpy()


def forward(model, batch, target_features):
    # Sampling and the large feature table remain on CPU; only this batch moves.
    device = next(model.parameters()).device
    target = target_features[batch.input_id].to(device)
    return model(batch.x.to(device), batch.edge_index.to(device), batch.edge_attr.to(device),
                 batch.edge_label_index.to(device), target)


@torch.no_grad()
def score(model, loader, target_features, seed):
    """Every call uses the same sampled neighborhoods, without consuming training RNG."""
    state, was_training = rng_state(), model.training
    try:
        seed_all(seed)
        model.eval()
        probabilities = torch.empty(len(target_features), dtype=torch.float32)
        visited = torch.zeros(len(target_features), dtype=torch.bool)
        for batch in loader:
            ids = batch.input_id
            if visited[ids].any():
                raise RuntimeError("An evaluation target edge was scored more than once")
            probabilities[ids] = forward(model, batch, target_features).softmax(1)[:, 1].cpu()
            visited[ids] = True
        if not visited.all() or not torch.isfinite(probabilities).all():
            raise RuntimeError("Incomplete or non-finite evaluation scores")
        return probabilities.numpy()
    finally:
        model.train(was_training)
        restore_rng(state)


def validation_metrics(labels, probabilities):
    precision, recall, thresholds = precision_recall_curve(labels, probabilities)
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    index = int(f1.argmax())
    return {"val_ap": float(average_precision_score(labels, probabilities)),
            "val_f1": float(f1[index]), "threshold": float(thresholds[index])}


def train_epoch(model, optimizer, loader, target_features, max_batches=None):
    model.train()
    device = next(model.parameters()).device
    weights = torch.tensor(HP["w_ce"], dtype=torch.float32, device=device)
    weighted_loss, denominator, batches, targets = 0.0, 0.0, 0, 0
    for batch in loader:
        optimizer.zero_grad(set_to_none=True)
        labels = batch.edge_label.to(device)
        logits = forward(model, batch, target_features)
        # Equivalent weighted mean cross entropy using deterministic reductions.
        per_target = -F.log_softmax(logits, dim=1).gather(1, labels[:, None]).flatten()
        target_weights = weights[labels]
        weight_total = target_weights.sum()
        loss = (per_target * target_weights).sum() / weight_total
        loss.backward()
        optimizer.step()
        weight_sum = float(weight_total.detach())
        weighted_loss += float(loss.detach()) * weight_sum
        denominator += weight_sum
        batches += 1
        targets += len(batch.edge_label)
        if max_batches is not None and batches >= max_batches:
            break
    return weighted_loss / denominator, batches, targets


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", choices=("cp", "cpn", "cn"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-epochs", type=int, default=50)
    parser.add_argument("--min-epochs", type=int, default=20)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--min-delta", type=float, default=.001)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--data", type=Path, default=Path("data/hi_small.pt"))
    parser.add_argument("--out", type=Path, default=Path("results/representation_followup"))
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--evaluate-only", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="Mark toy-data validation runs; never combine with production")
    parser.add_argument("--max-train-batches", type=int)
    args = parser.parse_args()
    if not 1 <= args.min_epochs <= args.max_epochs or args.patience < 1 or args.min_delta < 0:
        parser.error("Require 1 <= min-epochs <= max-epochs, patience >= 1, min-delta >= 0")
    if not args.smoke and (args.protocol is None or args.max_train_batches is not None):
        parser.error("Production requires --protocol and complete training epochs")
    if args.max_train_batches is not None and args.max_train_batches < 1:
        parser.error("max-train-batches must be positive")
    return args


def main():
    args = parse_args()
    if not args.smoke:
        protocol = json.loads(args.protocol.read_text())
        for setting in ("max_epochs", "min_epochs", "patience", "min_delta", "threads"):
            if protocol["training"][setting] != getattr(args, setting):
                raise ValueError(f"CLI {setting} differs from the frozen protocol")
        if (args.cell not in protocol["analysis"]["cells"]
                or args.seed not in protocol["analysis"]["seeds_by_cell"].get(args.cell, [])):
            raise ValueError("Cell or seed is outside the frozen protocol")
        if "device" in protocol["training"] and protocol["training"]["device"] != args.device:
            raise ValueError("CLI device differs from the frozen protocol")
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    device, device_info = configure_device(args.device)
    args.out.mkdir(parents=True, exist_ok=True)
    tag = f"{args.cell}_s{args.seed}"
    checkpoint_dir = args.out / "checkpoints" / tag
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    predictions_dir = args.out / "predictions"
    predictions_dir.mkdir(exist_ok=True)
    result_path, progress_path = args.out / f"{tag}.json", args.out / f"{tag}.progress.json"
    config = {"cell": args.cell, "seed": args.seed, "max_epochs": args.max_epochs,
              "min_epochs": args.min_epochs, "patience": args.patience, "min_delta": args.min_delta,
              "threads": args.threads, "device": args.device, "smoke": args.smoke,
              "max_train_batches": args.max_train_batches,
              "fixed_epochs": list(FIXED_EPOCHS), "selection": "maximum_validation_AP_earliest_tie",
              "normalization": NORMALIZATION_POLICY, "evaluation": "eval_mode_fixed_sample_rng",
              "input_slots": INPUT_SLOTS, "hp": HP}
    actual_data_hash = file_hash(args.data)
    if not args.smoke and actual_data_hash != protocol["data"]["sha256"]:
        raise ValueError("Prepared data checksum differs from the frozen protocol")
    metadata = {"cell": args.cell, "seed": args.seed, "config": config, "hp": HP, "device_info": device_info,
                "protocol_sha256": file_hash(args.protocol) if args.protocol else None,
                "source_sha256": {"representation_train.py": file_hash(__file__),
                                  "train.py": file_hash(Path(__file__).with_name("train.py"))},
                "data_sha256": actual_data_hash}
    fingerprint = json_hash(metadata)
    metadata["fingerprint"] = fingerprint
    if result_path.exists():
        existing = json.loads(result_path.read_text())
        if existing.get("fingerprint") != fingerprint or existing.get("status") != "complete":
            raise RuntimeError("Existing result belongs to a different run configuration")
        print(f"[{tag}] already complete", flush=True)
        return

    data = torch.load(args.data, map_location="cpu", weights_only=False, mmap=True)
    features, normalization = prepare_features(data, args.cell)
    tr, tr_features, tr_ids = make_loader(data, features, 0, True)
    va, va_features, va_ids = make_loader(data, features, 1, False)
    val_labels = data["y"][torch.from_numpy(va_ids)].numpy()
    seed_all(args.seed)
    model = GIN(edge_dim=11)
    initial_model_hash = model_hash(model)
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=HP["lr"])
    metadata.update({"initial_model_sha256": initial_model_hash,
                     "parameter_count": sum(p.numel() for p in model.parameters()),
                     "normalization": normalization, "normalization_sha256": json_hash(normalization)})
    history, best_ap, best_epoch, progress_ap, stale = [], -1.0, None, -1.0, 0
    stop_reason, stage = None, "training"
    last_path = checkpoint_dir / "last.pt"
    if last_path.exists():
        state = torch.load(last_path, map_location="cpu", weights_only=False)
        if state["fingerprint"] != fingerprint:
            raise RuntimeError("Checkpoint source, data, protocol or configuration changed")
        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        restore_rng(state["rng"])
        history, best_ap, best_epoch = state["history"], state["best_ap"], state["best_epoch"]
        progress_ap, stale, stop_reason, stage = state["progress_ap"], state["stale"], state["stop_reason"], state["stage"]
        print(f"[{tag}] resumed after epoch {len(history)} ({stage})", flush=True)
    if args.evaluate_only and stage != "trained":
        raise RuntimeError("evaluate-only requires a checkpoint whose training has finished")

    if stage != "trained":
        for epoch in range(len(history) + 1, args.max_epochs + 1):
            started = time.monotonic()
            seed_all(1_000_000 + args.seed * 10_000 + epoch)
            loss, batches, targets = train_epoch(model, optimizer, tr, tr_features, args.max_train_batches)
            if not args.smoke and targets != len(tr_ids):
                raise RuntimeError("Training epoch did not cover every target edge")
            val_prob = score(model, va, va_features, 2_000_000 + args.seed * 10 + 1)
            metrics = validation_metrics(val_labels, val_prob)
            if not np.isfinite(loss):
                raise RuntimeError("Non-finite training loss")
            improved = metrics["val_ap"] > best_ap
            if improved:
                best_ap, best_epoch = metrics["val_ap"], epoch
            if metrics["val_ap"] >= progress_ap + args.min_delta:
                progress_ap, stale = metrics["val_ap"], 0
            else:
                stale += 1
            record = {"epoch": epoch, "loss": loss, "batches": batches, "targets": targets,
                      **metrics, "sec": time.monotonic() - started, "plateau_epochs": stale}
            history.append(record)
            if epoch >= args.min_epochs and stale >= args.patience:
                stop_reason, stage = "validation_ap_plateau", "trained"
            elif epoch == args.max_epochs:
                stop_reason, stage = "maximum_epochs", "trained"
            state = {"fingerprint": fingerprint, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                     "rng": rng_state(), "epoch": epoch, "history": history, "best_ap": best_ap,
                     "best_epoch": best_epoch, "progress_ap": progress_ap, "stale": stale,
                     "stop_reason": stop_reason, "stage": stage}
            if improved:
                atomic_torch(checkpoint_dir / "best_validation.pt", state)
            if epoch in FIXED_EPOCHS:
                atomic_torch(checkpoint_dir / f"epoch_{epoch:03d}.pt", state)
            atomic_torch(last_path, state)
            atomic_json(progress_path, {**metadata, "status": "training" if stage == "training" else "evaluating",
                                       "epochs_completed": epoch, "best_epoch": best_epoch, "stop_reason": stop_reason,
                                       "history": history})
            print(f"[{tag}] epoch {epoch:02d} loss {loss:.6f} val AP {metrics['val_ap']:.5f} "
                  f"val F1 {metrics['val_f1']:.5f} stale {stale}/{args.patience} ({record['sec']:.1f}s)", flush=True)
            if stage == "trained":
                break

    # Test labels and test scores are first used after the run's training stops.
    te, te_features, te_ids = make_loader(data, features, 2, False)
    test_labels = data["y"][torch.from_numpy(te_ids)].numpy()
    checkpoints = {"best_validation": checkpoint_dir / "best_validation.pt"}
    checkpoints.update({f"epoch_{e}": checkpoint_dir / f"epoch_{e:03d}.pt"
                        for e in FIXED_EPOCHS if e <= len(history)})
    checkpoints["final"] = last_path
    evaluations, by_epoch = {}, {}
    for selection, checkpoint_path in checkpoints.items():
        state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if state["fingerprint"] != fingerprint:
            raise RuntimeError("Evaluation checkpoint provenance mismatch")
        epoch = state["epoch"]
        if epoch not in by_epoch:
            model.load_state_dict(state["model"])
            val_prob = score(model, va, va_features, 2_000_000 + args.seed * 10 + 1)
            vm = validation_metrics(val_labels, val_prob)
            saved = state["history"][-1]
            for key in ("val_ap", "val_f1", "threshold"):
                if not np.isclose(vm[key], saved[key], atol=1e-10, rtol=0):
                    raise RuntimeError(f"Fixed validation scoring failed to reproduce {key}")
            test_prob = score(model, te, te_features, 2_000_000 + args.seed * 10 + 2)
            prediction_path = predictions_dir / f"{tag}_epoch_{epoch:03d}.npz"
            atomic_predictions(prediction_path, row_id=te_ids, y=test_labels, prob=test_prob,
                               val_row_id=va_ids, val_y=val_labels, val_prob=val_prob)
            by_epoch[epoch] = {"epoch": epoch, **vm,
                               "test_f1": float(f1_score(test_labels, test_prob >= vm["threshold"], zero_division=0)),
                               "test_ap": float(average_precision_score(test_labels, test_prob)),
                               "test_f1_argmax": float(f1_score(test_labels, test_prob > .5, zero_division=0)),
                               "predictions_file": str(prediction_path.relative_to(args.out)),
                               "predictions_sha256": file_hash(prediction_path), "model_sha256": model_hash(model)}
        evaluations[selection] = by_epoch[epoch]
        print(f"[{tag}] scored {selection} epoch {epoch} test F1 {by_epoch[epoch]['test_f1']:.5f} "
              f"AP {by_epoch[epoch]['test_ap']:.5f}", flush=True)
    result = {**metadata, "status": "complete", "epochs_completed": len(history),
              "stop_reason": stop_reason, "best_epoch": best_epoch,
              "history": history, "evaluations": evaluations}
    atomic_json(result_path, result)
    atomic_json(progress_path, result)
    print(f"[{tag}] COMPLETE epochs={len(history)} best={best_epoch} stop={stop_reason}", flush=True)


if __name__ == "__main__":
    main()
