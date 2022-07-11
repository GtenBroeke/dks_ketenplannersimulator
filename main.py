import DepotClasses as dep
import Trucks as truck
import visualize
import config
import modelfunctions as mf
import run

# Running this file corresponds to performing a single model run. A run begins at 06:00am and runs in discrete
# time-steps of 1 minute (ticks) until 06:00am the next day. Each tick, trucks and depots are updated.
# The status of rollcages is also updated, within the truck/depot where they are located. The current version
# of the simulation includes trucks dropping collected parcels at the depot, and sorting within the depot. The
# sorting results in filled rollcages with destinations. For each collection order, the rollcages are distributed
# over the possible destinations based on historic proportions collected per customer. Collection fill grades are
# also included at customer level. These fill grades are taken into account when calculating sorting speeds.

# TO DO
# Definieer kolommen voor het inlezen van data

orders = mf.read_and_clean_orders()                      # Read orderset
DepotDict = dep.initialise_depots()                      # Read depot info and initialise depots
TruckDict = truck.initialise_trucks(orders, DepotDict)   # Initialise trucks for collection, based on orderset
CrossdockDict = dep.initialise_crossdocks()              # Initialise cross-docks
hinterland = mf.read_afzet(DepotDict)                    # Read 'hinterland' per customer

for i in range(config.n_steps):
    truck.update_trucks(TruckDict)
    dep.update_depots(DepotDict)

