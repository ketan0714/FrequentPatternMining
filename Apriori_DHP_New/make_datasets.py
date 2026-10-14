#!/usr/bin/env python3
"""Create the input transaction files (data/transactions_<N>.csv) and data/dataset_summary.csv.

Data source: SYNTHETIC. Own simplified version of the IBM Quest-style generator described in
Agrawal & Srikant (VLDB 1994), section 3.1: transactions are built from a pool of 'potentially
frequent' patterns (with some corruption) plus random filler items, so that many items are
frequent but most item PAIRS are not -- the situation where hash pruning of C2 can help.
Fixed seed => identical files on every run. The smaller files are prefixes of the largest one.
File format (same as the earlier sample): transaction_id,items   e.g.  1,I012;I047;I150
"""
import csv, os, random

N_ITEMS, AVG_LEN, N_PATTERNS, AVG_PAT_LEN, SEED = 200, 10, 400, 4, 2026
SIZES = [2000, 5000, 10000, 20000]


def gen_quest(n_trans, n_items=N_ITEMS, avg_len=AVG_LEN, n_patterns=N_PATTERNS,
              avg_pat_len=AVG_PAT_LEN, seed=SEED):
    rng = random.Random(seed)
    items = list(range(n_items))
    weights = [rng.expovariate(1.0) for _ in items]            # item popularity
    patterns = []
    for _ in range(n_patterns):
        size = min(8, max(1, int(rng.expovariate(1.0 / avg_pat_len)) + 1))
        patterns.append(rng.choices(items, weights, k=size))
    pat_w = [rng.expovariate(1.0) for _ in range(n_patterns)]  # pattern popularity
    db = []
    for _ in range(n_trans):
        target = max(2, int(rng.gauss(avg_len, 2)))
        t = set()
        while len(t) < target:
            for it in rng.choices(patterns, pat_w, k=1)[0]:
                if rng.random() > 0.15:                        # corruption
                    t.add(it)
            if rng.random() < 0.2:
                t.add(rng.choices(items, weights, k=1)[0])
        db.append(tuple(sorted(t)))
    return db


def write_csv(path, db):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["transaction_id", "items"])
        for i, t in enumerate(db, 1):
            w.writerow([i, ";".join(f"I{x:03d}" for x in t)])


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    big = gen_quest(max(SIZES))
    rows = []
    for n in SIZES:
        db = big[:n]
        write_csv(f"data/transactions_{n}.csv", db)
        rows.append([n, len({i for t in db for i in t}), round(sum(map(len, db)) / n, 2), N_ITEMS, SEED])
        print(f"wrote data/transactions_{n}.csv")
    with open("data/dataset_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["transactions", "distinct_items_observed", "avg_transaction_length", "item_universe", "seed"])
        w.writerows(rows)
