import config
import run
import pandas as pd

n_replicates = 10
n_runs = 15
arr_diff = list(range(n_runs))
n_unsorted = list()


sorting_limit = 0.09
for i in range(n_runs):
    print(i)
    n_unsorted.append(run.perform_run(config.arrival_spread, config.PERCENTAGE_TOTAAL))

df_out = pd.DataFrame()
for run in n_unsorted:
    row = pd.DataFrame(run, index=[0])
    df_out = pd.concat([df_out, row])