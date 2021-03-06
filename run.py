import DepotClasses as dep
import Trucks as truck
import config
import modelfunctions as mf


def perform_run(unc_arr, sorting_limits):
    orders = mf.read_and_clean_orders()  # Read orderset
    DepotDict = dep.initialise_depots(sorting_limits)  # Read depot info and initialise depots
    TruckDict = truck.initialise_trucks(orders, DepotDict, unc_arr)  # Initialise trucks for collection, based on orderset

    for i in range(config.n_steps):
        truck.update_trucks(TruckDict)
        dep.update_depots(DepotDict)

    n_uns = sum(len(depot.unsorted_rc) + len(depot.rc_on_sorter) for depot in DepotDict.values())
    outcome_dict = {}
    for depot in DepotDict.values():
        if depot.name in outcome_dict.keys():
            outcome_dict[depot.name].append(DepotDict)
        else:
            outcome_dict[depot.name] = [len(depot.unsorted_rc) + len(depot.rc_on_sorter)]
    outcome_dict = {'ALR': len(DepotDict['ALR'].failed_rc),
                    'TB': len(DepotDict['TB'].failed_rc),
                    'WB': len(DepotDict['WB'].failed_rc)}
    return outcome_dict