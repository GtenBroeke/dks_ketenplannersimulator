import pandas as pd
import datetime as dt
import json
import os

# Filepaths
os.chdir('C:\\Users\\BroekeGuusten\\OneDrive - PostNL\\Documents\\Python Scripts\\kp-simulator')
ORDERFILE = 'input/kp_solution/ketenmanagement.csv'
DEPOTFILE = 'input/PostNL_depots.xlsx'
SORTINGTIMESFILE = 'input/kp_solution/DepotStateTime.csv'
DEPOTNAMESFILE = 'input/vertaling_depotnamen.csv'
HINTERLANDFILE = 'input/OrdersPrepped_23052022.csv'
CROSSDOCKNAMESFILE = 'input/crossdock_namen.xlsx'

sorting_time = 5                                          # Time parcels on average are on the sorter
date = dt.date(2022, 5, 23)                               # Date of simulation run
StartTime = dt.datetime.combine(date, dt.time(6, 0, 0))   # Start time of simulation
n_steps = 60*24                                           # Total number of time-steps in one run (equivalent to 24 hours)
unloading_time = 8

arrival_spread = 0
PERCENTAGE_REJECT = 0.045
PERCENTAGE_OVERLOOP = 0.01
PERCENTAGE_VALIDATIE = 0.03
PERCENTAGE_TOTAAL = PERCENTAGE_VALIDATIE + PERCENTAGE_REJECT + PERCENTAGE_OVERLOOP

#n_sorted_per_state = 13.116   # Sorting speed per state, in parcels per minute

interfillgrade = 30    # Number of parcels per RC in inter transport (to be replaced by fillgrade based on data)
blue = True
blue_dict = {'ALR': 60*18, 'TB': 60*16, 'WB': 60*18}


# Below we define all columns used from datafiles that are read from csv/excel
col_ord_cust_id = 'Customerorder nummer'
col_ord_dest = 'Name'
col_ord_fillgrade = 'Vulgraad'
col_ord_rc = '#RCP equiv gerealiseerd (max)'
col_ord_nmg = '#Pakketten_NMG'
col_ord_mg = '#Pakketten gerealiseerd (max)'
col_ord_lospartij = 'Lospartij voorstel'
col_ord_lostijd = 'Lostijd voorstel'
col_ord_aar = 'AAR nummer'

col_dep_type = 'DepotType'
col_dep_name = 'Name'
col_dep_lat = 'lat'
col_dep_lon = 'lon'
col_dep_docks = 'Aantal docks'
col_dep_floorcap = 'Floorcap'
col_dep_pluscap = 'Pluscap'
col_dep_outmax = 'Max Stock Output'
col_dep_xdocks = 'Aantal docks  cross docking'
col_dep_buffer = 'Cross dock buffer'

col_sort_dep = 'DEPOT2'
col_sort_start = 'beginTimes_str_x'
col_sort_end = 'beginTimes_str_y'
col_sort_state = 'state'

col_name_1 = 'Depotnaam1'
col_name_2 = 'Depotnaam2'
col_name_3 = 'Depotnaam3'

# Below we create a dictionary of the 'afzetgebieden' Note: this piece of code should still be improved
orders = pd.read_csv(HINTERLANDFILE)
orders.fillna(0, inplace=True)
depot_names = pd.read_csv(DEPOTNAMESFILE)
for ind, row in depot_names.iterrows():
    orders.rename(columns={row.Depotnaam2: row.Depotnaam1}, inplace=True)

afzet = dict()
for ind, row in orders.iterrows():
    cust = row[col_ord_cust_id]
    if cust not in afzet.keys():
        afzet[cust] = row['ALR':'ASN'].to_dict()

with open('intermediate/routes.json') as json_file:
    routes = json.load(json_file)
