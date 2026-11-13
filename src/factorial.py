"""Run the four HI-Small GIN cells and write the paired five-seed report."""
import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.stats import t
from sklearn.metrics import average_precision_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/factorial"
CELLS = {"base": [], "ports": ["ports"], "counts": ["counts"], "counts+ports": ["counts", "ports"]}
SEEDS = range(5)
GROUPS = ("all", "first", "repeat", "repeat_free")
EPOCHS = 100


def check_graph(d):
    expected = [(3248921, 2530), (965524, 1036), (863900, 1611)]
    for s, size in enumerate(expected):
        mask = d["split"] == s
        if (int(mask.sum()), int(d["y"][mask].sum())) != size:
            raise ValueError(f"Unexpected edge or laundering count in split {s}")
    distinct = d["counts"][:, [3, 1]]
    first = d["first_contact"]
    if not ((d["ports"][first] == distinct[first]).all()
            and (d["ports"][~first] < distinct[~first]).all()):
        raise ValueError("Port/count ordering disagrees with the directed first-contact flag")


def paired_interval(values):
    mean = np.mean(values)
    half = t.ppf(.975, len(values) - 1) * np.std(values, ddof=1) / np.sqrt(len(values))
    return mean, mean - half, mean + half


def explained_share(gain, residual):
    """Fieller interval for 1 - mean(residual)/mean(gain), paired over seeds."""
    g, r = gain.mean(), residual.mean()
    vg, cov, _, vr = (np.cov(gain, residual) / len(gain)).ravel()
    q = t.ppf(.975, len(gain) - 1) ** 2
    a, b, c = g*g - q*vg, -2*(g*r - q*cov), r*r - q*vr
    if g <= 0 or a <= 0:
        return "Unresolved (baseline port gain is nonpositive or its interval includes zero)."
    delta = max(0., b*b - 4*a*c) ** .5
    lo, hi = (-b-delta)/(2*a), (-b+delta)/(2*a)
    return f"{1-r/g:.1%} (95% Fieller interval {1-hi:.1%} to {1-lo:.1%})."


def groups(d):
    # Include the current transfer. A later repeat cannot reclassify an earlier edge.
    u, v = d["edge_index"].numpy()
    first = d["first_contact"].numpy()
    repeated = np.flatnonzero(~first)
    earliest = np.full(d["n_nodes"], len(u))
    for endpoint in (u, v):
        np.minimum.at(earliest, endpoint[repeated], repeated)
    test = np.flatnonzero(d["split"].numpy() == 2)
    clean = (test < earliest[u[test]]) & (test < earliest[v[test]])
    return dict(all=np.ones(len(test), dtype=bool), first=first[test],
                repeat=~first[test], repeat_free=clean)


def sampled_logits(model, loader, batch, eval_mode):
    # IBM trains on seed edges present in the sampled graph. During evaluation
    # append missing seed edges so every test transfer receives one prediction.
    g = loader.data
    seed_ids = loader.course_seed_ids[batch.input_id]
    order = batch.e_id.argsort()
    sorted_ids = batch.e_id[order]
    positions = torch.searchsorted(sorted_ids, seed_ids)
    present = torch.zeros_like(seed_ids, dtype=torch.bool)
    inside = positions < len(sorted_ids)
    present[inside] = sorted_ids[positions[inside]] == seed_ids[inside]
    read = order[positions[present]]
    if eval_mode:
        missing = ~present
        tail = batch.edge_index.size(1) + torch.arange(int(missing.sum()))
        batch.edge_index = torch.cat([batch.edge_index, batch.edge_label_index[:, missing]], 1)
        batch.edge_attr = torch.cat([batch.edge_attr, g.edge_attr[seed_ids[missing]]])
        read_all = torch.empty_like(seed_ids)
        read_all[present], read_all[missing] = read, tail
        read = read_all
    logits = model(batch.x, batch.edge_index, batch.edge_attr)
    labels = batch.edge_label if eval_mode else batch.edge_label[present]
    return logits[read], labels


@torch.no_grad()
def score(model, loader):
    model.eval()
    scores = torch.empty(len(loader.course_seed_ids))
    for batch in loader:
        logits, _ = sampled_logits(model, loader, batch, True)
        scores[batch.input_id] = logits.softmax(1)[:, 1]
    return scores.numpy()


def run(d, cell, seed, masks):
    from train import HP, loader
    sys.path.insert(0, str(ROOT / "data/reference"))
    from models import GINe

    dest = RESULTS / f"{cell}_s{seed}.json"
    checkpoint = dest.with_suffix(".pt")
    if dest.exists():
        return
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    feats = ["base", *CELLS[cell]]
    loaders = []
    for s in range(3):
        ld, _ = loader(d, feats, s, s == 0)
        # Prepared rows are globally time sorted. Each loader graph is a prefix.
        ld.course_seed_ids = torch.where(d["split"] == s)[0]
        loaders.append(ld)
    train, val, test = loaders
    model = GINe(1, HP["n_gnn_layers"], n_hidden=HP["n_hidden"],
                 edge_dim=train.data.edge_attr.shape[1], final_dropout=HP["final_dropout"])
    opt = torch.optim.Adam(model.parameters(), lr=HP["lr"])
    loss = torch.nn.CrossEntropyLoss(weight=torch.tensor(HP["w_ce"]))
    y_val = d["y"][val.course_seed_ids].numpy()
    best, epoch0 = -1., 0
    if checkpoint.exists():
        state = torch.load(checkpoint, weights_only=True)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["optimizer"])
        best, best_model, best_epoch, epoch0 = (state[k] for k in ("best", "best_model", "best_epoch", "next"))
    for epoch in range(epoch0, EPOCHS):
        torch.manual_seed(seed * 10000 + epoch)
        model.train()
        for batch in train:
            logits, labels = sampled_logits(model, train, batch, False)
            if len(labels):
                opt.zero_grad()
                loss(logits, labels).backward()
                opt.step()
        torch.manual_seed(seed + 500000)
        val_f1 = float(f1_score(y_val, score(model, val) > .5, zero_division=0))
        if val_f1 > best:
            best, best_epoch = val_f1, epoch + 1
            best_model = {k: v.clone() for k, v in model.state_dict().items()}
        tmp = checkpoint.with_suffix(".part")
        torch.save(dict(model=model.state_dict(), optimizer=opt.state_dict(), best=best,
                        best_model=best_model, best_epoch=best_epoch, next=epoch+1), tmp)
        tmp.replace(checkpoint)
        print(f"{cell} seed {seed} epoch {epoch+1}/{EPOCHS} validation F1 {val_f1:.4f}", flush=True)
    model.load_state_dict(best_model)
    torch.manual_seed(seed + 600000)
    p = score(model, test)
    y = d["y"][test.course_seed_ids].numpy()
    result = dict(cell=cell, seed=seed, epochs=EPOCHS, selected_epoch=best_epoch,
                  val_f1=best, ap=float(100 * average_precision_score(y, p)), groups={})
    for name, m in masks.items():
        result["groups"][name] = dict(n=int(m.sum()), positive=int(y[m].sum()),
                                      f1=float(100 * f1_score(y[m], p[m] > .5, zero_division=0)))
    tmp = dest.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, indent=2))
    tmp.replace(dest)
    checkpoint.unlink()


def format_interval(values):
    return "{:+.2f} [{:+.2f}, {:+.2f}]".format(*paired_interval(values))


def report():
    scores = {c: [json.loads((RESULTS / f"{c}_s{s}.json").read_text()) for s in SEEDS] for c in CELLS}
    for c, rows in scores.items():
        if any((r["cell"], r["seed"], r["epochs"]) != (c, s, EPOCHS) for s, r in enumerate(rows)):
            raise ValueError("Mixed cells, seeds or training budgets")
    lines = ["# What do port numbers add?", "", "HI-Small. Minority F1 in points. Five paired seeds.",
             "", "| Test set | Transfers | Laundering | Base | Ports | Counts | Counts + ports | Residual [95% CI] |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    residuals = {}
    for name in GROUPS:
        m = {c: np.array([r["groups"][name]["f1"] for r in rows]) for c, rows in scores.items()}
        r = residuals[name] = m["counts+ports"] - m["counts"]
        group = scores["base"][0]["groups"][name]
        means = " | ".join(f"{v.mean():.2f} ± {v.std(ddof=1):.2f}" for v in m.values())
        lines.append(f"| {name} | {group['n']:,} | {group['positive']:,} | {means} | {format_interval(r)} |")
        if name == "all":
            gain = m["ports"] - m["base"]
            share = explained_share(gain, r)
    _, lower, upper = paired_interval(residuals["all"])
    if lower > 0:
        verdict = "Ports improved F1 after counts were supplied."
    elif upper < 0:
        verdict = "Adding ports to counts reduced F1 under this protocol."
    else:
        verdict = "The five-seed interval spans zero. The incremental value of ports remains unresolved."
    lines += ["", verdict, "", f"Ports − Base in F1 points: {format_interval(gain)}.",
              f"Share of the gain explained by counts: {share}",
              f"Repeat minus first-contact residual, paired by seed: {format_interval(residuals['repeat'] - residuals['first'])}.",
              "", "Intervals describe variation across initializations conditional on this single test period.",
              "", "| Seed | " + " | ".join(CELLS) + " |", "|---|---:|---:|---:|---:|"]
    for s in SEEDS:
        lines.append(f"| {s} | " + " | ".join(f"{scores[c][s]['groups']['all']['f1']:.2f}" for c in CELLS) + " |")
    aps = ", ".join(f"{c} {np.mean([r['ap'] for r in rows]):.2f}" for c, rows in scores.items())
    lines += ["", f"Threshold-free test average precision (×100): {aps}.", ""]
    (RESULTS / "REPORT.md").write_text("\n".join(lines))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--seed", type=int, choices=SEEDS, help="Run the four cells for one seed")
    cli.add_argument("--report", action="store_true", help="Read the twenty completed runs")
    args = cli.parse_args()
    if args.report:
        report()
    else:
        RESULTS.mkdir(parents=True, exist_ok=True)
        graph = torch.load(ROOT / "data/course-graph.pt", weights_only=True)
        check_graph(graph)
        masks = groups(graph)
        for seed in SEEDS if args.seed is None else [args.seed]:
            for cell in CELLS:
                run(graph, cell, seed, masks)
        if args.seed is None:
            report()
