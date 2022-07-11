import DepotClasses as dep
import Trucks as truck
import config
import modelfunctions as mf


def perform_run(unc_arr):
    orders = mf.read_and_clean_orders()  # Read orderset
    DepotDict = dep.initialise_depots()  # Read depot info and initialise depots
    TruckDict = truck.initialise_trucks(orders, DepotDict, unc_arr)  # Initialise trucks for collection, based on orderset

    for i in range(config.n_steps):
        truck.update_trucks(TruckDict)
        dep.update_depots(DepotDict)

    n_uns = sum(len(depot.unsorted_rc) for depot in DepotDict.values())
    return n_uns