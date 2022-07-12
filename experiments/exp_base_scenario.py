import config
import run
import pandas as pd
import modelfunctions as mf
import DepotClasses as dep
import Trucks as truck


def perform_run(unc_arr, sorting_limits):
    orders = mf.read_and_clean_orders()  # Read orderset
    DepotDict = dep.initialise_depots(sorting_limits)  # Read depot info and initialise depots
    TruckDict = truck.initialise_trucks(orders, DepotDict, unc_arr)  # Initialise trucks for collection, based on orderset

    for i in range(config.n_steps):
        truck.update_trucks(TruckDict)
        dep.update_depots(DepotDict)

    n_uns = sum(len(depot.unsorted_rc) + len(depot.rc_on_sorter) for depot in DepotDict.values())

    return n_uns

n_runs = 100
n_unsorted = list()

for i in range(n_runs):
    print(i)
    n_unsorted.append(run.perform_run(config.arrival_spread, config.PERCENTAGE_TOTAAL))

df_out = pd.DataFrame()
for run in n_unsorted:
    row = pd.DataFrame(run, index=[0])
    df_out = pd.concat([df_out, row])