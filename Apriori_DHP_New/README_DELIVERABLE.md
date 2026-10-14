# Apriori vs DHP — updated presentation bundle

## Included
- `Apriori_vs_DHP_Attractive.pptx`: 15-slide presentation with a refreshed navy/teal/coral theme.
- `graphs/graph1...graph5.png`: the five figures embedded in the deck.
- `results/results_size.csv`, `results/results_support.csv`, `results/results_buckets.csv`: the measured values used by those figures.
- `results/candidates_by_iteration.csv`: pass-level candidate and scan counters for the 5,000-transaction, 1% support run.
- `data/transactions_*.csv` and `data/dataset_summary.csv`: the supplied synthetic data generated with seed 2026.
- `apriori_dhp_experiments.py`, `make_datasets.py`, `make_graphs.py`: source files from the supplied code bundle.

## How to read the results
- The charts and deck use a **curated, completed subset**: size sweep at 2,000, 5,000 and 10,000 transactions; support sweep at 2% and 1% on 5,000 transactions; bucket sweep at 997, 4,999 and 20,011 buckets on 5,000 transactions.
- Timing values are **single-run observations**, not means over repeated runs. Treat small differences as indicative only. Memory is peak `tracemalloc` allocation measured separately after the input data was loaded; it is not process RSS.
- The synthetic dataset contains up to 200 item IDs and averages about 11.3 items per transaction. It is reproducible but not a real-world benchmark.
- The startup self-test passed against brute force on a 200-transaction sample. The experiment source asserts equality with Apriori on configurations that include Apriori. The bucket sweep only runs DHP variants, so it does not independently assert those sweep outputs against Apriori.
- The 20,000-transaction dataset is included, but the full 20k benchmark was not completed in this session; the presentation does not claim 20k timing results.
- This implementation measures frequent itemsets; it does not implement association-rule generation or confidence reporting. Those concepts are explained for context.
- The DHP transaction-trimming rule is simplified for this educational implementation; the code does not reproduce every optimization from the original paper.

## Re-run
From this directory, install `matplotlib` and run `python make_datasets.py`, `python apriori_dhp_experiments.py`, and `python make_graphs.py` for the original full experiment plan. The full plan may take substantially longer than the quick-run estimate in the original README; check generated CSVs before relying on results. The figures currently included are the curated completed outputs described above.

## References in the deck
1. Agrawal & Srikant (1994), *Fast Algorithms for Mining Association Rules in Large Databases*, VLDB.
2. Park, Chen & Yu (1995), *An Effective Hash-Based Algorithm for Mining Association Rules*, SIGMOD '95.
3. Han, Pei & Yin (2000), *Mining Frequent Patterns without Candidate Generation*, SIGMOD 2000.

The Lewis paper was removed as requested.
