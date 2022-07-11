import run

n_runs = 30
arr_diff = list(range(n_runs))
n_unsorted = list()
sorting_limit = 0.09
for i in range(n_runs):
    print(i)
    n_unsorted.append(run.perform_run(arr_diff[i], sorting_limit))