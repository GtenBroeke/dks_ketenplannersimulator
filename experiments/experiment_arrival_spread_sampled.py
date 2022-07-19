import config
import run
import pandas as pd
import modelfunctions as mf
import DepotClasses as dep
import Trucks as truck
import random
import visualize as vis

def initialise_trucks(orders, depot_dict):
    """
    Function to initialize trucks for rollcages for collection. Each truck is given a timer. At the end of this
    timer, the truck drops its RC at a depot. The truck is then removed from the simulation.
    :param orders: DataFrame with one order per row
    :param depot_dict: Dictionary containing depot objects
    :param arrival_window: Parameter describing the uncertainty in the arrival times of trucks
    :return: Dictionary with all created truck objects
    """

    truck_dict = dict()
    for ind, row in orders.iterrows():
        identifier = row[config.col_ord_cust_id]
        #timer = mf.datetime_to_ticks(row.LoadingTime, config.StartTime)
        #timer = random.normalvariate(row['minutes_mean'], row['minutes_sd'])
        timer = row['minutes_mean'] - 360
        timer = round(timer)
        if timer < 1:
            timer = 1
        destination = depot_dict[row[config.col_ord_dest]]
        origin = row[config.col_ord_cust_id]
        fillgrade = row[config.col_ord_mg] / row[config.col_ord_rc]
        rcp = row[config.col_ord_rc]
        blue = mf.check_blue(row[config.col_ord_aar], row[config.col_ord_dest])
        truck_dict[identifier] = truck.Truck(identifier, timer, rcp, destination, origin, fillgrade, 0, blue)
    return truck_dict


def perform_run(unc_arr, sorting_limits):
    orders = mf.read_and_clean_orders('orderset_arrivals.csv')  # Read orderset
    DepotDict = dep.initialise_depots(sorting_limits)  # Read depot info and initialise depots
    TruckDict = initialise_trucks(orders, DepotDict)  # Initialise trucks for collection, based on orderset

    for i in range(config.n_steps):
        truck.update_trucks(TruckDict)
        dep.update_depots(DepotDict)

    n_uns = sum(len(depot.unsorted_rc) + len(depot.rc_on_sorter) for depot in DepotDict.values())

    return n_uns

n_runs = 100
n_unsorted = list()

for i in range(n_runs):
    print(i)
    n_unsorted.append(perform_run(config.arrival_spread, config.PERCENTAGE_TOTAAL))

df_out = pd.DataFrame()
for run in n_unsorted:
    row = pd.DataFrame(run, index=[0])
    df_out = pd.concat([df_out, row])