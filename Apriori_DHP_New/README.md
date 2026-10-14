# Apriori vs DHP: code, input data and results

## Run order
    python make_datasets.py                 # creates data/transactions_<N>.csv (+ dataset_summary.csv)
    python apriori_dhp_experiments.py       # full run, about 8 minutes; writes results/*.csv
    python apriori_dhp_experiments.py --quick   # ~1 minute demo run (smaller sizes, 2 repeats)
    python make_graphs.py                   # needs matplotlib; writes graphs/*.png

## Files
| File | What it is |
|---|---|
| make_datasets.py | Synthetic Quest-style generator (own code, idea from Agrawal & Srikant 1994 sec. 3.1). Seed 2026 |
| data/transactions_2000 / 5000 / 10000 / 20000.csv | Input, format `transaction_id,items` (e.g. `1,I010;I053`). 200-item universe, about 11 items per transaction |
| apriori_dhp_experiments.py | Apriori, DHP (hash only), DHP (hash + trim), self-test, experiments A/B/C |
| results/results_size.csv | Experiment A: dataset size at 1% support |
| results/results_support.csv | Experiment B: 5 support thresholds on 10,000 transactions |
| results/results_buckets.csv | Experiment C: DHP bucket count sweep |
| results/candidates_by_iteration.csv | Candidates before and after hash pruning, frequent itemsets and data read, per pass |
| graphs/graph1..4 | The four required graphs; graph5 is an extra bucket-sweep graph |

## What is source vs own work
* Published: Apriori and apriori-gen (Agrawal & Srikant 1994); DHP hash pruning of C2 and transaction trimming (Park, Chen & Yu 1995).
* Own: all Python code here, the dataset generator, the benchmark harness, the pair hash `(a*1009+b) mod B`, and the simplified trimming rule.
* Simplifications to state in the presentation: the DHP trimming rule is a simplified version of the paper's; no hash tree is used (dict + itertools.combinations); counting skips items that appear in no candidate in all three algorithms.

## Measurement notes
* Time: time.perf_counter(), mean and sample SD over 5 runs. Memory: tracemalloc peak in a separate run, measured after the data is loaded (not process RSS).
* Correctness: every run asserts the three algorithms return identical itemsets and counts; a start-up test also compares them with brute force.
