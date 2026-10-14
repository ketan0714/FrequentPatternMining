#!/usr/bin/env python3
"""Draw the graphs from results/*.csv  ->  graphs/*.png   (needs matplotlib)."""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COL = {"Apriori": "#1B7F6B", "DHP (hash only)": "#E8912D", "DHP (hash + trim)": "#5B7F95"}
MARK = {"Apriori": "o", "DHP (hash only)": "s", "DHP (hash + trim)": "^"}
os.makedirs("graphs", exist_ok=True)


def read(name):
    with open(f"results/{name}") as f:
        return list(csv.DictReader(f))


def series(rows, xkey, ykey, alg, sdkey=None):
    pts = sorted((float(r[xkey]), float(r[ykey]), float(r[sdkey]) if sdkey else 0) for r in rows if r["algorithm"] == alg)
    return [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]


def line_plot(rows, xkey, ykey, ylabel, xlabel, title, fname, sdkey=None, logx=False, invert=False, xfmt=None):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for alg in COL:
        x, y, sd = series(rows, xkey, ykey, alg, sdkey)
        if x:
            ax.errorbar(x, y, yerr=sd if sdkey else None, label=alg, color=COL[alg], marker=MARK[alg], lw=2, capsize=3)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title)
    if logx: ax.set_xscale("log")
    if invert: ax.invert_xaxis()
    xs = sorted({float(r[xkey]) for r in rows})
    ax.set_xticks(xs)
    ax.set_xticklabels([xfmt(v) if xfmt else f"{v:g}" for v in xs])
    ax.grid(alpha=0.3); ax.legend(); fig.tight_layout(); fig.savefig(f"graphs/{fname}", dpi=160); plt.close(fig)


size, sup, bk = read("results_size.csv"), read("results_support.csv"), read("results_buckets.csv")
cand = read("candidates_by_iteration.csv")

line_plot(size, "transactions", "mean_time_s", "Execution time (s), mean of repeats", "Number of transactions",
          "Graph 1: execution time vs dataset size (min support 1%)", "graph1_time_vs_size.png", sdkey="sd_time_s",
          xfmt=lambda v: f"{int(v):,}")
line_plot(size, "transactions", "peak_mem_mb", "Peak traced memory (MB)", "Number of transactions",
          "Graph 2: peak memory vs dataset size (min support 1%)", "graph2_memory_vs_size.png", xfmt=lambda v: f"{int(v):,}")
line_plot(sup, "min_support", "mean_time_s", "Execution time (s), mean of repeats", "Minimum support (%)",
          "Graph 3: execution time vs minimum support", "graph3_time_vs_support.png", sdkey="sd_time_s", invert=True,
          xfmt=lambda v: f"{v*100:g}")

# Graph 4: candidates per pass + records scanned per pass (largest support-experiment config at 1%)
n = max(int(r["transactions"]) for r in cand if r["experiment"] == "support")
rows4 = [r for r in cand if r["experiment"] == "support" and int(r["transactions"]) == n and float(r["min_support"]) == 0.01 and int(r["k"]) >= 2]
ks = sorted({int(r["k"]) for r in rows4})
get = lambda alg, key: [next(int(r[key]) for r in rows4 if r["algorithm"] == alg and int(r["k"]) == k) for k in ks]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
w = 0.27
x = range(len(ks))
a1.bar([i - w for i in x], get("Apriori", "cand_after_hash"), w, label="Apriori candidates", color=COL["Apriori"])
a1.bar(list(x), get("DHP (hash only)", "cand_before_hash"), w, label="DHP before hash prune", color="#C9B037")
a1.bar([i + w for i in x], get("DHP (hash only)", "cand_after_hash"), w, label="DHP after hash prune", color=COL["DHP (hash only)"])
a1.set_xticks(list(x)); a1.set_xticklabels([f"k={k}" for k in ks]); a1.set_yscale("log")
a1.set_ylabel("Candidate itemsets (log scale)"); a1.set_xlabel("Pass k"); a1.legend(fontsize=8)
a1.set_title(f"Candidates per pass ({n:,} transactions, 1%)"); a1.grid(alpha=0.3, axis="y")
for alg in ("Apriori", "DHP (hash + trim)"):
    a2.plot(ks, get(alg, "items_scanned"), marker=MARK[alg], color=COL[alg], lw=2, label=alg)
a2.set_ylabel("Items read in the pass (sum over transactions)"); a2.set_xlabel("Pass k"); a2.set_xticks(ks)
a2.set_title("Data read per pass (effect of transaction trimming)"); a2.grid(alpha=0.3); a2.legend()
fig.tight_layout(); fig.savefig("graphs/graph4_candidates_per_pass.png", dpi=160); plt.close(fig)

# Graph 5 (extra): bucket sweep
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
for alg in ("DHP (hash only)", "DHP (hash + trim)"):
    x_, t_, sd_ = series(bk, "buckets", "mean_time_s", alg, "sd_time_s")
    a2.errorbar(x_, t_, yerr=sd_, marker=MARK[alg], color=COL[alg], lw=2, capsize=3, label=alg)
x_, c2_, _ = series(bk, "buckets", "c2_after_hash", "DHP (hash only)")
a1.plot(x_, c2_, marker="s", color=COL["DHP (hash only)"], lw=2, label="C2 after hash prune")
before = float(next(r["c2_before_hash"] for r in bk if r["algorithm"] == "DHP (hash only)"))
a1.axhline(before, ls="--", color="gray", label="C2 before hash prune (= Apriori)")
for a in (a1, a2):
    a.set_xscale("log"); a.set_xlabel("Number of hash buckets B (log scale)"); a.grid(alpha=0.3); a.legend()
a1.set_ylabel("Candidate 2-itemsets"); a1.set_title("Pruning power vs bucket count")
a2.set_ylabel("Execution time (s)")
ap = next(float(r["mean_time_s"]) for r in sup if r["algorithm"] == "Apriori" and float(r["min_support"]) == 0.01)
a2.axhline(ap, ls="--", color=COL["Apriori"], label="Apriori (same data)"); a2.legend()
a2.set_title("Time vs bucket count (10k transactions, 1%)")
fig.tight_layout(); fig.savefig("graphs/graph5_bucket_sweep.png", dpi=160); plt.close(fig)
print("graphs written to graphs/")
