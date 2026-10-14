#!/usr/bin/env python3
"""Apriori vs DHP benchmark (Python 3.9+, standard library only).

Reads data/transactions_<N>.csv (see make_datasets.py) and writes results/*.csv.
Usage:  python apriori_dhp_experiments.py            (full run, about 10-15 minutes)
        python apriori_dhp_experiments.py --quick    (small demo run, about 1 minute)

ALGORITHMS
  Apriori            : Agrawal & Srikant 1994 -- join + prune candidate generation, one database pass per level.
  DHP (hash only)    : Park, Chen & Yu 1995 -- during pass 1 every item pair is hashed into a bucket table;
                       a candidate pair is dropped if its bucket count < min support (safe upper bound).
  DHP (hash + trim)  : the above plus the paper's transaction trimming: after each pass an item is kept in a
                       transaction only if it lies in >= k matched candidate k-itemsets of that transaction;
                       transactions too short for a (k+1)-itemset are removed.
SHARED CODE: apriori_gen (join+prune) and count_support are used by all three, so differences come only
from the DHP modifications. Support counting skips items that appear in no candidate (applies to all three).
Output is verified identical across the three algorithms on every run, and against brute force at start-up.
"""
import csv, gc, itertools, math, os, platform, statistics, sys, time, tracemalloc
from collections import Counter

HASH_MULT = 1009          # pair hash = (a * 1009 + b) mod B   (deterministic; items are < 1009)
DEFAULT_B = 20011         # bucket count (~ number of possible item pairs); see the bucket sweep experiment


# ------------------------------------------------------------------ input
def load_csv(path):
    D = []
    with open(path, newline="") as f:
        r = csv.reader(f)
        next(r)
        for _, items in r:
            D.append(tuple(sorted(int(x[1:]) for x in items.split(";"))))
    return D


# ------------------------------------------------------------------ shared pieces
def apriori_gen(prev, k):
    """Join step + prune step. prev: sorted list of (k-1)-tuples. Returns sorted list of k-tuples."""
    prev_set, out, n = set(prev), [], len(prev)
    for i in range(n):
        a = prev[i]
        for j in range(i + 1, n):
            b = prev[j]
            if a[:k - 2] != b[:k - 2]:
                break                                   # sorted: no later b shares the prefix
            c = a + (b[-1],)
            if all(c[:m] + c[m + 1:] in prev_set for m in range(k - 2)):   # prune step
                out.append(c)
    return out


def count_support(D, C, k, trim):
    """One pass over D. Returns (support dict, trimmed database or None)."""
    sup = dict.fromkeys(C, 0)
    cand_items = {i for c in C for i in c}
    newD = [] if trim else None
    for t in D:
        tt = [x for x in t if x in cand_items]
        if len(tt) < k:
            continue                                    # cannot hold any k-candidate => nothing for k+1 either
        if trim:
            hits = Counter()
            for comb in itertools.combinations(tt, k):
                if comb in sup:
                    sup[comb] += 1
                    hits.update(comb)
            keep = tuple(x for x in tt if hits[x] >= k)  # item needs >= k matched k-itemsets to be in a (k+1)-itemset
            if len(keep) > k:
                newD.append(keep)
        else:
            for comb in itertools.combinations(tt, k):
                if comb in sup:
                    sup[comb] += 1
    return sup, newD


def _stat(k, before, after, freq, D):
    return {"k": k, "cand_before_hash": before, "cand_after_hash": after, "frequent": freq,
            "txns_scanned": len(D), "items_scanned": sum(map(len, D))}


# ------------------------------------------------------------------ algorithms
def run_apriori(D, mc):
    cnt = Counter()
    for t in D:
        cnt.update(t)
    L = sorted((i,) for i, c in cnt.items() if c >= mc)
    out = {(i,): cnt[i] for (i,) in L}
    stats = [_stat(1, len(cnt), len(cnt), len(L), D)]
    k = 2
    while L:
        C = apriori_gen(L, k)
        if not C:
            break
        sup, _ = count_support(D, C, k, False)
        L = sorted(c for c in C if sup[c] >= mc)
        out.update({c: sup[c] for c in L})
        stats.append(_stat(k, len(C), len(C), len(L), D))
        k += 1
    return out, stats


def run_dhp(D, mc, B=DEFAULT_B, trim=True):
    cnt, buckets = Counter(), [0] * B
    for t in D:
        cnt.update(t)
        for a, b in itertools.combinations(t, 2):       # pass 1 also hashes every pair
            buckets[(a * HASH_MULT + b) % B] += 1
    L = sorted((i,) for i, c in cnt.items() if c >= mc)
    out = {(i,): cnt[i] for (i,) in L}
    stats = [_stat(1, len(cnt), len(cnt), len(L), D)]
    cur, k = D, 2
    while L:
        Cpre = apriori_gen(L, k)
        if not Cpre:
            break
        C = [c for c in Cpre if buckets[(c[0] * HASH_MULT + c[1]) % B] >= mc] if k == 2 else Cpre
        if not C:
            stats.append(_stat(k, len(Cpre), 0, 0, cur))
            break
        sup, newD = count_support(cur, C, k, trim)
        L = sorted(c for c in C if sup[c] >= mc)
        out.update({c: sup[c] for c in L})
        stats.append(_stat(k, len(Cpre), len(C), len(L), cur))
        if trim:
            cur = newD
        k += 1
    return out, stats


VARIANTS = {
    "Apriori": run_apriori,
    "DHP (hash only)": lambda D, mc, B=DEFAULT_B: run_dhp(D, mc, B, trim=False),
    "DHP (hash + trim)": lambda D, mc, B=DEFAULT_B: run_dhp(D, mc, B, trim=True),
}


# ------------------------------------------------------------------ self-test
def brute_force(D, mc, max_k=5):
    cnt = Counter()
    for t in D:
        for k in range(1, max_k + 1):
            cnt.update(itertools.combinations(t, k))
    return {s: c for s, c in cnt.items() if c >= mc}


def self_test():
    D = load_csv("data/transactions_2000.csv")[:200]
    mc = 10
    bf = brute_force(D, mc)
    for name, fn in VARIANTS.items():
        out, _ = fn(D, mc)
        out = {s: c for s, c in out.items() if len(s) <= 5}
        assert out == bf, f"{name} differs from brute force"
    print("self-test OK: all three algorithms equal brute force on a 200-transaction sample")


# ------------------------------------------------------------------ measurement
def measure(fn, D, mc, B, repeats):
    """Mean/SD time over `repeats` runs, then peak memory in a separate tracemalloc run."""
    kw = {} if (B is None or fn is run_apriori) else {"B": B}
    times, out, stats = [], None, None
    for _ in range(repeats):
        gc.collect()
        t0 = time.perf_counter()
        out, stats = fn(D, mc, **kw)
        times.append(time.perf_counter() - t0)
    gc.collect()
    tracemalloc.start()
    fn(D, mc, **kw)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"mean": statistics.mean(times), "sd": statistics.stdev(times) if len(times) > 1 else 0.0,
            "peak_mb": peak / 1048576, "out": out, "stats": stats}


RES_COLS = ["experiment", "transactions", "distinct_items", "avg_txn_length", "min_support", "min_count",
            "buckets", "algorithm", "repeats", "mean_time_s", "sd_time_s", "peak_mem_mb", "n_frequent",
            "n_passes", "c2_before_hash", "c2_after_hash", "identical_to_apriori"]
CAND_COLS = ["experiment", "transactions", "min_support", "buckets", "algorithm", "k", "cand_before_hash",
             "cand_after_hash", "frequent", "txns_scanned", "items_scanned"]


def run_config(exp, D, minsup, B, variants, repeats, res_rows, cand_rows):
    mc = math.ceil(len(D) * minsup)
    distinct = len({i for t in D for i in t})
    avg_len = sum(map(len, D)) / len(D)
    ref = None
    for name in variants:
        m = measure(VARIANTS[name], D, mc, B, repeats)
        if name == "Apriori":
            ref = m["out"]
        same = (m["out"] == ref) if ref is not None else ""
        assert same in (True, ""), f"output mismatch: {name} n={len(D)} minsup={minsup}"
        c2 = [s for s in m["stats"] if s["k"] == 2]
        usesB = name != "Apriori"
        res_rows.append([exp, len(D), distinct, round(avg_len, 2), minsup, mc, B if usesB else "", name, repeats,
                         round(m["mean"], 5), round(m["sd"], 5), round(m["peak_mb"], 4), len(m["out"]),
                         len(m["stats"]), c2[0]["cand_before_hash"] if c2 else "", c2[0]["cand_after_hash"] if c2 else "",
                         same])
        for s in m["stats"]:
            cand_rows.append([exp, len(D), minsup, B if usesB else "", name, s["k"], s["cand_before_hash"],
                              s["cand_after_hash"], s["frequent"], s["txns_scanned"], s["items_scanned"]])
        print(f"  {exp:8s} n={len(D):6d} sup={minsup:<6} B={B if usesB else '-':<7} {name:18s} "
              f"{m['mean']:7.3f}s  {m['peak_mb']:7.3f} MB  frequent={len(m['out'])}", flush=True)


def main():
    quick = "--quick" in sys.argv
    sizes = [2000, 5000] if quick else [2000, 5000, 10000, 20000]
    size_sup = 0.01
    sup_n = 5000 if quick else 10000
    supports = [0.02, 0.01] if quick else [0.02, 0.015, 0.01, 0.0075, 0.005]
    buckets = [997, 20011] if quick else [997, 4999, 20011, 100003]
    repeats = 2 if quick else 5
    os.makedirs("results", exist_ok=True)
    self_test()
    allv = list(VARIANTS)
    dhp_only = [v for v in allv if v != "Apriori"]
    res, cand = [], []
    print("Experiment A: dataset size")
    for n in sizes:
        run_config("size", load_csv(f"data/transactions_{n}.csv"), size_sup, DEFAULT_B, allv, repeats, res, cand)
    print("Experiment B: minimum support")
    D = load_csv(f"data/transactions_{sup_n}.csv")
    for s in supports:
        run_config("support", D, s, DEFAULT_B, allv, repeats, res, cand)
    print("Experiment C: DHP bucket count")
    for B in buckets:
        run_config("buckets", D, size_sup, B, dhp_only, repeats, res, cand)
    for exp, fname in (("size", "results_size.csv"), ("support", "results_support.csv"), ("buckets", "results_buckets.csv")):
        with open(f"results/{fname}", "w", newline="") as f:
            w = csv.writer(f); w.writerow(RES_COLS); w.writerows(r for r in res if r[0] == exp)
    with open("results/candidates_by_iteration.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(CAND_COLS); w.writerows(cand)
    with open("results/environment.txt", "w") as f:
        f.write(f"Python {platform.python_version()}\n{platform.platform()}\nrepeats={repeats}\nquick={quick}\n")
    print("done. Files written to results/")


if __name__ == "__main__":
    main()
