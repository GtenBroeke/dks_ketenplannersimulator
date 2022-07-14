import matplotlib.pyplot as plt

import config
import run
import pandas as pd
import modelfunctions as mf
import DepotClasses as dep
import Trucks as truck
import numpy as np
import matplotlib.pyplot as plt

n_replicates = 5
n_runs = 30
arr_diff = list(range(n_runs))
n_unsorted = list()


def perform_run(unc_arr, sorting_limits):
    orders = mf.read_and_clean_orders()  # Read orderset
    DepotDict = dep.initialise_depots(sorting_limits)  # Read depot info and initialise depots
    TruckDict = truck.initialise_trucks(orders, DepotDict, unc_arr)  # Initialise trucks for collection, based on orderset

    for i in range(config.n_steps):
        truck.update_trucks(TruckDict)
        dep.update_depots(DepotDict)

    n_uns = sum(len(depot.unsorted_rc) + len(depot.rc_on_sorter) for depot in DepotDict.values())

    return n_uns

n_unsorted_dict = dict()
sorting_limit_list = []
for i in range(n_runs):
    print(i)
    sorting_limit = i * 0.005
    sorting_limit_list.append(sorting_limit)
    n_unsorted_dict[i] = []
    for j in range(n_replicates):
        n_unsorted_dict[i].append(perform_run(config.arrival_spread, sorting_limit))

n_mean = []
n_sd = []
for i in n_unsorted_dict.keys():
    n_mean.append(np.mean(n_unsorted_dict[i]))
    n_sd.append(np.std(n_unsorted_dict[i]))

plt.plot(sorting_limit_list, n_mean)
plt.plot(sorting_limit_list, [x + y for (x,y) in zip(n_mean, n_sd)])
plt.plot(sorting_limit_list, [x - y for (x,y) in zip(n_mean, n_sd)])
plt.xlabel('% reject + overloop + validatie')
plt.ylabel('# Unsorted RC')
plt.show()