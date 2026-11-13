"""Train and evaluate one cell of the design: a GIN edge classifier on HI-Small.

Every cell uses the base edge features (timestamp, amount received, received currency, payment format);
--counts, --ports and --novelty append the corresponding history features from prepare.py.
Each transaction is classified from its 2-hop sampled neighbourhood. The model is never switched to eval mode,
so BatchNorm normalises every training, validation and test batch with its own statistics.
After each epoch the decision threshold is the F1-maximising threshold on validation; test F1 at that threshold,
test F1 at p > 0.5 and average precision are logged, and the test predictions of every epoch are saved.
Usage: python src/train.py [--counts] [--ports] [--novelty] --seed 0 --epochs 5 --out results/runs
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
from sklearn.metrics import average_precision_score, f1_score, precision_recall_curve
from torch_geometric.data import Data
from torch_geometric.loader import LinkNeighborLoader
from torch_geometric.nn import BatchNorm, GINEConv

# Fixed hyper-parameters for every cell: the tuned GIN setting for HI-Small reported by Egressy et al. (2024).
HP = dict(lr=0.006213266113989207, n_hidden=66, n_gnn_layers=2, w_ce=(1.0000182882773443, 6.275014431494497),
          final_dropout=0.10527690625126304, batch_size=8192, num_neighbors=[100, 100])


class GIN(nn.Module):
    """GINE message passing over edge features, then an MLP on [h_sender, h_receiver, edge embedding]."""

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
    """Graph = all transactions up to split s (train / train+val / all); seeds = transactions of split s.
    Edge features are z-normalised within each of the three graphs."""
    m = d["split"] <= s
    attr = z_norm(torch.cat([d[k][m].double() for k in feats], 1)).float()
    seeds = torch.nonzero(d["split"][m] == s).squeeze(1)
    # Accounts carry no features of their own: a constant node feature (z-normalised to 0).
    g = Data(x=torch.zeros(d["n_nodes"], 1), edge_index=d["edge_index"][:, m], edge_attr=attr, num_nodes=d["n_nodes"])
    return LinkNeighborLoader(g, num_neighbors=HP["num_neighbors"], edge_label_index=g.edge_index[:, seeds],
                              edge_label=d["y"][m][seeds], batch_size=HP["batch_size"], shuffle=shuffle), attr[seeds]


def step(model, batch, seed_attr):
    return model(batch.x, batch.edge_index, batch.edge_attr, batch.edge_label_index, seed_attr[batch.input_id])


@torch.no_grad()
def scores(model, ld, seed_attr):
    """P(laundering) for every seed transaction, in seed order."""
    s = torch.empty(len(seed_attr))
    for b in ld:
        s[b.input_id] = step(model, b, seed_attr).softmax(1)[:, 1]
    return s.numpy()


def val_threshold(y, s):
    """Decision threshold that maximises F1 on the validation transactions, and that F1."""
    p, r, t = precision_recall_curve(y, s)
    f = 2 * p[:-1] * r[:-1] / np.maximum(p[:-1] + r[:-1], 1e-12)
    return t[f.argmax()], f.max()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", action="store_true")
    ap.add_argument("--ports", action="store_true")
    ap.add_argument("--novelty", action="store_true", help="flag: no earlier transaction between this sender and receiver")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--data", default="data/hi_small.pt")
    ap.add_argument("--out", default="results/runs")
    args = ap.parse_args()

    random.seed(args.seed), np.random.seed(args.seed), torch.manual_seed(args.seed)
    d = torch.load(args.data, weights_only=False)
    extras = [k for k in ("counts", "novelty", "ports") if getattr(args, k)]
    feats, cell = ["base"] + extras, "+".join(extras) or "base"
    (tr, tr_attr), (va, va_attr), (te, te_attr) = (loader(d, feats, s, s == 0) for s in range(3))
    y_va, y_te = (d["y"][d["split"] == s].numpy() for s in (1, 2))

    model = GIN(edge_dim=tr_attr.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=HP["lr"])
    loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(HP["w_ce"]))
    log, test_preds = [], []
    for epoch in range(args.epochs):
        t0 = time.time()
        for batch in tr:
            opt.zero_grad()
            loss = loss_fn(step(model, batch, tr_attr), batch.edge_label)
            loss.backward()
            opt.step()
        s_va, s_te = scores(model, va, va_attr), scores(model, te, te_attr)
        thr, f_va = val_threshold(y_va, s_va)                 # chosen on validation only
        p_te = (s_te >= thr).astype(np.int8)
        f_te = f1_score(y_te, p_te, zero_division=0)
        test_preds.append(p_te)
        log.append(dict(epoch=epoch, val_f1=f_va, test_f1=f_te, threshold=float(thr),
                        val_ap=average_precision_score(y_va, s_va), test_ap=average_precision_score(y_te, s_te),
                        val_f1_argmax=f1_score(y_va, s_va > 0.5, zero_division=0),
                        test_f1_argmax=f1_score(y_te, s_te > 0.5, zero_division=0),
                        loss=loss.item(), sec=time.time() - t0))
        e = log[-1]
        print(f"[{cell} s{args.seed}] epoch {epoch:3d} loss {e['loss']:.4f} | val F1 {f_va:.4f} test F1 {f_te:.4f} "
              f"(thr {thr:.3f}) | AP val {e['val_ap']:.4f} test {e['test_ap']:.4f} | argmax F1 val "
              f"{e['val_f1_argmax']:.4f} test {e['test_f1_argmax']:.4f} ({e['sec']:.0f}s)", flush=True)

    # Test predictions of every epoch are kept, so best-validation selection can be redone for any budget <= epochs.
    os.makedirs(args.out, exist_ok=True)
    tag = f"{cell}_s{args.seed}"
    np.savez_compressed(f"{args.out}/{tag}_test_pred.npz", pred=np.stack(test_preds))
    with open(f"{args.out}/{tag}.json", "w") as f:
        json.dump(dict(cell=cell, features=feats, seed=args.seed, epochs=args.epochs,
                       hp=HP, log=log), f, indent=1)


if __name__ == "__main__":
    main()
