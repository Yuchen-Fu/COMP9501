"""One run of the 2x2 factorial: GIN (Multi-GNN's GINe) on HI-Small, edge features +counts / +ports.

Model, hyper-parameters, loaders, per-graph z-normalisation and best-validation model selection
follow IBM/Multi-GNN (models.GINe, model_settings.json["gin"], train_util, training.train_homo).
Usage: python src/train.py [--counts] [--ports] --seed 0 --epochs 5 --out results/runs
"""
import argparse
import json
import os
import random
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import f1_score
from torch_geometric.data import Data
from torch_geometric.loader import LinkNeighborLoader
from torch_geometric.nn import BatchNorm, GINEConv

# Multi-GNN model_settings.json["gin"]["params"] and main.py defaults.
HP = dict(lr=0.006213266113989207, n_hidden=66, n_gnn_layers=2, w_ce=(1.0000182882773443, 6.275014431494497),
          final_dropout=0.10527690625126304, batch_size=8192, num_neighbors=[100, 100])


class GINe(nn.Module):
    """Multi-GNN GINe without edge updates; the edge read-out is applied to the seed edges only."""

    def __init__(self, edge_dim, h=HP["n_hidden"], layers=HP["n_gnn_layers"], p=HP["final_dropout"]):
        super().__init__()
        self.node_emb, self.edge_emb = nn.Linear(1, h), nn.Linear(edge_dim, h)
        self.convs = nn.ModuleList(GINEConv(nn.Sequential(nn.Linear(h, h), nn.ReLU(), nn.Linear(h, h)), edge_dim=h)
                                   for _ in range(layers))
        self.bns = nn.ModuleList(BatchNorm(h) for _ in range(layers))
        self.mlp = nn.Sequential(nn.Linear(3 * h, 50), nn.ReLU(), nn.Dropout(p), nn.Linear(50, 25), nn.ReLU(),
                                 nn.Dropout(p), nn.Linear(25, 2))

    def forward(self, x, edge_index, edge_attr, seed_index, seed_attr):
        x, e = self.node_emb(x), self.edge_emb(edge_attr)
        for conv, bn in zip(self.convs, self.bns):
            x = (x + F.relu(bn(conv(x, edge_index, e)))) / 2
        src, dst = seed_index
        return self.mlp(torch.cat([x[src].relu(), x[dst].relu(), self.edge_emb(seed_attr)], 1))


def z_norm(a):
    std = a.std(0)
    std[std == 0] = 1
    return (a - a.mean(0)) / std


def loader(d, feats, s, shuffle):
    """Graph = all transactions up to split s (train / train+val / all, as in Multi-GNN); seeds = split s.
    Edge features are z-normalised per graph object, as in Multi-GNN's get_data."""
    m = d["split"] <= s
    attr = z_norm(torch.cat([d[k][m].double() for k in feats], 1)).float()
    seeds = torch.nonzero(d["split"][m] == s).squeeze(1)
    # Multi-GNN's node feature is a constant 1, which z_norm maps to 0.
    g = Data(x=torch.zeros(d["n_nodes"], 1), edge_index=d["edge_index"][:, m], edge_attr=attr, num_nodes=d["n_nodes"])
    return LinkNeighborLoader(g, num_neighbors=HP["num_neighbors"], edge_label_index=g.edge_index[:, seeds],
                              edge_label=d["y"][m][seeds], batch_size=HP["batch_size"], shuffle=shuffle), attr[seeds]


def step(model, batch, seed_attr):
    return model(batch.x, batch.edge_index, batch.edge_attr, batch.edge_label_index, seed_attr[batch.input_id])


@torch.no_grad()
def predict(model, ld, seed_attr):
    model.eval()
    pred = torch.empty(len(seed_attr), dtype=torch.int8)
    for b in ld:
        pred[b.input_id] = step(model, b, seed_attr).argmax(1).to(torch.int8)
    return pred.numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", action="store_true")
    ap.add_argument("--ports", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--data", default="data/hi_small.pt")
    ap.add_argument("--out", default="results/runs")
    args = ap.parse_args()

    random.seed(args.seed), np.random.seed(args.seed), torch.manual_seed(args.seed)
    d = torch.load(args.data, weights_only=False)
    feats = ["base"] + ["counts"] * args.counts + ["ports"] * args.ports
    cell = {(0, 0): "base", (1, 0): "counts", (0, 1): "ports", (1, 1): "counts+ports"}[(args.counts, args.ports)]
    (tr, tr_attr), (va, va_attr), (te, te_attr) = (loader(d, feats, s, s == 0) for s in range(3))
    y_va, y_te = (d["y"][d["split"] == s].numpy() for s in (1, 2))

    model = GINe(edge_dim=tr_attr.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=HP["lr"])
    loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(HP["w_ce"]))
    log, test_preds = [], []
    for epoch in range(args.epochs):
        t0 = time.time()
        model.train()
        for batch in tr:
            opt.zero_grad()
            loss = loss_fn(step(model, batch, tr_attr), batch.edge_label)
            loss.backward()
            opt.step()
        p_va, p_te = predict(model, va, va_attr), predict(model, te, te_attr)
        f_va, f_te = f1_score(y_va, p_va, zero_division=0), f1_score(y_te, p_te, zero_division=0)
        test_preds.append(p_te)
        log.append(dict(epoch=epoch, val_f1=f_va, test_f1=f_te, loss=loss.item(), sec=time.time() - t0))
        print(f"[{cell} s{args.seed}] epoch {epoch:3d} loss {loss.item():.4f} val F1 {f_va:.4f} test F1 {f_te:.4f} "
              f"({time.time() - t0:.0f}s)", flush=True)

    # Test predictions of every epoch are kept, so best-validation selection can be redone for any budget <= epochs.
    os.makedirs(args.out, exist_ok=True)
    tag = f"{cell}_s{args.seed}"
    np.savez_compressed(f"{args.out}/{tag}_test_pred.npz", pred=np.stack(test_preds))
    with open(f"{args.out}/{tag}.json", "w") as f:
        json.dump(dict(cell=cell, counts=args.counts, ports=args.ports, seed=args.seed, epochs=args.epochs,
                       hp=HP, log=log), f, indent=1)


if __name__ == "__main__":
    main()
