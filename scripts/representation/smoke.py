"""Exercise the chosen device and graph sampler without producing research results."""
from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import math
from pathlib import Path
import time

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("representation_trainer", ROOT / "src/representation_train.py")
trainer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trainer)


def toy_graph():
    """Generate valid chronological pair histories, including repeats in every split."""
    rng = np.random.default_rng(81203)
    n, nodes = 600, 64
    pool = rng.integers(nodes, size=(100, 2))
    pairs = pool[rng.integers(len(pool), size=n)]
    pairs[::4] = rng.integers(nodes, size=(len(pairs[::4]), 2))
    out_seen, in_seen = [{} for _ in range(nodes)], [{} for _ in range(nodes)]
    out_total, in_total = np.zeros(nodes, int), np.zeros(nodes, int)
    counts, ports, novelty = [], [], []
    for sender, receiver in pairs:
        out_d, in_d = len(out_seen[sender]), len(in_seen[receiver])
        new = receiver not in out_seen[sender]
        assert new == (sender not in in_seen[receiver])
        counts.append([out_total[sender], out_d, in_total[receiver], in_d])
        if new:
            out_seen[sender][receiver] = out_d
            in_seen[receiver][sender] = in_d
        ports.append([in_seen[receiver][sender], out_seen[sender][receiver]])
        novelty.append(new)
        out_total[sender] += 1
        in_total[receiver] += 1
    return {
        "edge_index": torch.as_tensor(pairs.T.copy(), dtype=torch.long),
        "n_nodes": nodes,
        "base": torch.as_tensor(np.column_stack((np.arange(n) * 1800, rng.uniform(1, 100, n),
                                                  rng.integers(0, 4, n), rng.integers(0, 5, n)))),
        "counts": torch.as_tensor(counts), "ports": torch.as_tensor(ports),
        "first_contact": torch.as_tensor(novelty),
        "novelty": torch.as_tensor(novelty, dtype=torch.long)[:, None],
        "repeat_free": torch.zeros(n, dtype=torch.bool),
        "split": torch.tensor([0] * 360 + [1] * 120 + [2] * 120),
        "y": (torch.arange(n) % 17 == 0).long(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), required=True)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--data", type=Path, help="Also check one full-size training batch and one validation batch.")
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    device, info = trainer.configure_device(args.device)
    graph = toy_graph()
    initial_hashes, norm_hashes, arm_checks = [], [], []
    started = time.monotonic()
    for cell in ("cp", "cpn", "cn"):
        features, normalization = trainer.prepare_features(graph, cell)
        norm_hashes.append(trainer.json_hash(normalization))
        if cell != "cn":
            assert torch.equal(features[:, 5] == features[:, 9], graph["first_contact"])
            assert torch.equal(features[:, 7] == features[:, 8], graph["first_contact"])
        assert torch.equal(features[:, 10], graph["first_contact"].float() if cell != "cp" else torch.zeros(len(features)))
        if cell == "cn":
            assert torch.count_nonzero(features[:, 8:10]) == 0
        trainer.seed_all(918)
        model = trainer.GIN(edge_dim=11)
        initial_hashes.append(trainer.model_hash(model))
        model.to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=trainer.HP["lr"])
        train, train_features, _ = trainer.make_loader(graph, features, 0, True)
        val, val_features, _ = trainer.make_loader(graph, features, 1, False)
        loss, batches, targets = trainer.train_epoch(model, optimizer, train, train_features)
        assert math.isfinite(loss) and targets == 360 and batches >= 1
        before_hash = trainer.model_hash(model)
        before_rng = torch.get_rng_state().clone()
        p1 = trainer.score(model, val, val_features, 819)
        p2 = trainer.score(model, val, val_features, 819)
        assert np.array_equal(p1, p2), "Repeated evaluation scores differ"
        assert before_hash == trainer.model_hash(model), "Evaluation changed model or BatchNorm state"
        assert torch.equal(before_rng, torch.get_rng_state()), "Evaluation changed training RNG"
        arm_checks.append({"cell": cell, "training_targets": targets, "evaluation_targets": len(p1),
                           "finite_loss": True, "repeatable_eval": True, "state_preserved": True})
    assert len(set(initial_hashes)) == len(set(norm_hashes)) == 1
    full_batch = None
    if args.data:
        del train, val, train_features, val_features, features, model, optimizer
        gc.collect()
        if args.device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        full_started = time.monotonic()
        full_graph = torch.load(args.data, map_location="cpu", weights_only=False, mmap=True)
        features, _ = trainer.prepare_features(full_graph, "cp")
        trainer.seed_all(11918)
        model = trainer.GIN(edge_dim=11).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=trainer.HP["lr"])
        train, train_features, _ = trainer.make_loader(full_graph, features, 0, True)
        loss, _, targets = trainer.train_epoch(model, optimizer, train, train_features, max_batches=1)
        assert math.isfinite(loss), "Full-data training batch has a non-finite loss"
        del train, train_features
        val, val_features, _ = trainer.make_loader(full_graph, features, 1, False)
        model.eval()
        with torch.no_grad():
            batch = next(iter(val))
            scores = trainer.forward(model, batch, val_features)
            assert torch.isfinite(scores).all(), "Full-data validation batch has non-finite logits"
        full_batch = {"training_targets": targets, "validation_targets": len(batch.input_id),
                      "seconds": time.monotonic() - full_started,
                      "cuda_peak_allocated_bytes": torch.cuda.max_memory_allocated() if args.device == "cuda" else None,
                      "note": "One training batch and one validation batch, discarded; no AML performance metrics computed."}
    result = {"status": "passed", "toy_data_only": args.data is None, "device": info,
              "seconds": time.monotonic() - started, "arms": arm_checks,
              "matched_initialization": True, "matched_scaling": True,
              "shared_scaling_preserves_novelty_equality": True,
              "full_data_batch_check": full_batch,
              "limitations": "A sampled batch checks likely memory needs; later neighborhoods can be larger."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    trainer.atomic_json(args.out, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
