"""Build the HI-Small graph once: formatting, temporal split, port numbers, causal counts.

Accounts (bank + account id) are nodes and transfers are directed edges. Every transaction gets
one position in a total order: timestamp first, same-minute ties broken by a fixed random
permutation. Ports and counts are both computed in this order, so for a first-contact
transaction the port equals the distinct-counterparty count exactly. Raw-file row order is not
used for ties: in HI-Small it is label-correlated (laundering rows tend to be written after
their same-minute siblings), which would leak the label into "strictly earlier" counts.

Usage: python src/prepare.py data/raw/HI-Small_Trans.csv data/hi_small.pt
"""
import itertools
import sys

import numpy as np
import pandas as pd
import torch


def load_formatted(path):
    """Raw CSV -> one row per transaction: integer account ids, integer codes for currency and payment
    format (in order of first appearance), timestamps in seconds from the first transaction, total order."""
    raw = pd.read_csv(path, dtype=str)
    raw.columns = ["Timestamp", "From Bank", "From Acc", "To Bank", "To Acc", "Amount Received",
                   "Receiving Currency", "Amount Paid", "Payment Currency", "Payment Format", "Is Laundering"]
    n = len(raw)
    # Same first-seen coding as get_dict_val (receiving currency before payment currency; from before to).
    cur_codes, _ = pd.factorize(np.column_stack([raw["Receiving Currency"], raw["Payment Currency"]]).ravel())
    acc_codes, _ = pd.factorize(np.column_stack([raw["From Bank"] + raw["From Acc"],
                                                 raw["To Bank"] + raw["To Acc"]]).ravel())
    ts = pd.to_datetime(raw["Timestamp"], format="%Y/%m/%d %H:%M").dt.as_unit("s").astype("int64").to_numpy()
    df = pd.DataFrame({
        "from_id": acc_codes[0::2], "to_id": acc_codes[1::2], "Timestamp": ts,
        "Amount Received": raw["Amount Received"].astype(float).to_numpy(),
        "Received Currency": cur_codes[0::2],
        "Payment Format": pd.factorize(raw["Payment Format"])[0],
        "Is Laundering": raw["Is Laundering"].astype(int).to_numpy(),
    })
    tie = np.random.default_rng(0).permutation(n)                     # label-independent tie-break
    df = df.iloc[np.lexsort((tie, df["Timestamp"].to_numpy()))].reset_index(drop=True)
    df["Timestamp"] -= df["Timestamp"].min()
    assert len(df) == n
    return df


def day_split(ts, split_per=(0.6, 0.2, 0.2)):
    """Day-based 60/20/20 temporal split: the day cut points (i, j) whose transaction shares have the
    smallest maximum relative error to 60/20/20."""
    day = ts // 86400
    d_ts = np.bincount(day)
    best = min(((max(abs(s / d_ts.sum() - t) / t for s, t in
                     zip((d_ts[:i].sum(), d_ts[i:j].sum(), d_ts[j:].sum()), split_per)), (i, j))
                for i, j in itertools.combinations(range(len(d_ts)), 2)))
    i, j = best[1]
    return np.where(day < i, 0, np.where(day < j, 1, 2)), (i, j, len(d_ts))


def side_history(key, other, n_nodes):
    """For each transaction, at node `key`: #earlier transactions, #distinct earlier counterparties,
    and the port = rank of `other` among key's counterparties by first contact.
    Transactions are assumed to be indexed in the global (time, row) order."""
    E = len(key)
    order = np.lexsort((np.arange(E), key))              # group by key, keep global order inside
    k, o = key[order], other[order]
    pos = np.arange(E)
    grp_start = np.maximum.accumulate(np.where(np.r_[True, k[1:] != k[:-1]], pos, 0))
    total_before = pos - grp_start
    _, first, inv = np.unique(k.astype(np.int64) * n_nodes + o, return_index=True, return_inverse=True)
    is_first = np.zeros(E, dtype=np.int64)
    is_first[first] = 1
    excl = np.cumsum(is_first) - is_first
    distinct_before = excl - excl[grp_start]
    port = distinct_before[first][inv]
    out = np.empty((3, E), dtype=np.int64)
    out[:, order] = np.stack([total_before, distinct_before, port])
    return out


def main(src, dst):
    df = load_formatted(src)
    E = len(df)
    u, v = df["from_id"].to_numpy(), df["to_id"].to_numpy()
    n_nodes = int(max(u.max(), v.max()) + 1)
    split, (i, j, n_days) = day_split(df["Timestamp"].to_numpy())

    out_total, out_distinct, out_port = side_history(u, v, n_nodes)   # sender side
    in_total, in_distinct, in_port = side_history(v, u, n_nodes)      # receiver side

    # Mechanism-check strata. A transaction is a "first contact" if no earlier u->v transaction exists.
    first_contact = (out_port == out_distinct)                         # also the "novelty" feature
    assert np.array_equal(first_contact, in_port == in_distinct)
    # An account "repeats" if it has >=2 transactions with the same counterparty in the same direction
    # anywhere in the observed graph (the test graph the model sees contains all transactions).
    pair_count = pd.Series(1, index=u.astype(np.int64) * n_nodes + v).groupby(level=0).transform("size").to_numpy()
    repeater = np.zeros(n_nodes, dtype=bool)
    repeater[u[pair_count > 1]] = True
    repeater[v[pair_count > 1]] = True
    repeat_free = ~repeater[u] & ~repeater[v]

    base = df[["Timestamp", "Amount Received", "Received Currency", "Payment Format"]].to_numpy(np.float64)
    data = {
        "edge_index": torch.from_numpy(np.stack([u, v])),
        "y": torch.from_numpy(df["Is Laundering"].to_numpy()),
        "split": torch.from_numpy(split),
        "base": torch.from_numpy(base),
        "ports": torch.from_numpy(np.stack([in_port, out_port], 1)),
        "counts": torch.from_numpy(np.stack([out_total, out_distinct, in_total, in_distinct], 1)),
        "first_contact": torch.from_numpy(first_contact),
        "novelty": torch.from_numpy(first_contact[:, None].astype(np.int64)),  # 1 = no earlier u->v transaction
        "repeat_free": torch.from_numpy(repeat_free),
        "n_nodes": n_nodes,
    }
    torch.save(data, dst)

    y = data["y"].numpy()
    print(f"transactions={E:,} accounts={n_nodes:,} laundering={y.sum():,} ({100*y.mean():.3f}%) days={n_days} cut=(day {i}, day {j})")
    for s, name in enumerate(["train", "val", "test"]):
        m = split == s
        print(f"  {name:5s}: {m.sum():9,} tx ({100*m.mean():.1f}%)  laundering={y[m].sum():5,} ({100*y[m].mean():.3f}%)")
    te = split == 2
    for name, mask in [("first-contact", first_contact), ("repeat tx", ~first_contact),
                       ("repeat-free accounts", repeat_free), ("repeating accounts", ~repeat_free)]:
        m = te & mask
        print(f"  test {name:22s}: {m.sum():9,} tx  laundering={y[m].sum():5,} ({100*y[m].mean():.3f}%)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
