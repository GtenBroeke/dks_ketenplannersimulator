import pandas as pd
import Rollcage as rc
from uuid import uuid4
import datetime as dt
import config
import modelfunctions as mf
import production_state as ps
import Trucks as tr


class PostnlLocation:
    def __init__(self, name=None, latitude=None, longitude=None):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude


class Depot(PostnlLocation):
    def __init__(self, name=None, latitude=None, longitude=None, state=None, docks=None, floor_in=None, floor_plus=None,
                 floor_out=None, sorting_start=None, sorting_end=None, sorting_limits=None):
        super().__init__(name, latitude, longitude)
        self.state = state
        self.docks = docks
        self.floor_in = floor_in
        self.floor_plus = floor_plus
        self.floor_out = floor_out
        self.sorting_start = sorting_start
        self.sorting_end = sorting_end
        self.sorting_limits = sorting_limits

        # Below attributes are used in running the model
        self.timer = 0                     # Timer, used to keep track of sorting times
        self.unsorted_rc = list()          # List of unsorted RC on the depot floor
        self.rc_on_sorter = list()         # List of RC of which the contents are currently being sorted at the depot
        self.sorted_rc = list()            # List of sorted RC on the depot floor
        self.rc_at_opvoer = list()         # RC currently at opvoer
        self.afvoer_rc = dict()            # RC currently being filled with sorted parcels

        # Below attributes are intended only to keep track of results and visualise the model outcomes. They are
        # not needed for the model to run
        self.n_floor_hist = []             # List that will contain a time series of unsorted RC on the depot floor
        self.n_floor_hist_parcels = []     # List that will contain a time series of unsorted parcels on the depot floor
        self.parcels_dropped_cum = 0       # Total number of parcels dropped at depot
        self.hist_rc_dropped = []          # Timeseries of RC dropped at depot
        self.hist_parcels_dropped = []     # List that will contain a time series of number of parcels dropped at depot
        self.hist_parcels_processed = []   # List that will contain a time series of the number of sorted parcels
        self.hist_rc_processed = []        # List that will contain a time series of the number of sorted incoming RC
        self.processed_parcels = 0         # Total number of sorted parcels
        self.processed_rc = 0
        self.total_rc_in = 0               # Total number of RC dropped at depot
        self.failed_rc = []
        self.rc_processed = []
        self.rc_crossdock = []
        self.rc_delivery = []

    def __str__(self):
        """
        Function used to display the depot characteristics. Mostly for debugging purposes
        :return:String with name of depot, unsorted and sorted RC
        """
        return f"Depot {self.name} with {self.total_rc_in} total " \
               f"RC and {len(self.unsorted_rc) + len(self.rc_on_sorter)} unsorted remaining"

    def update(self):
        """
        Update of depot. This function is called each tick for each depot and arranges the basic processes taking place
        in the depot. These processes include, in order, bringing RC to the locations for opvoer (if there are empty
        spots), processing of RC at the opvoerlocation (these are added to the sorter at the end of their processing
        time), updating the sorter (which includes adding parcels to outgoing RC and moving these outgoing RC to the
        floor for outbound transport). At the last tick of the sorting process, any remaining RC that are partially
        filled are added to the floor for outbound transport)
        :return: No return
        """
        self.timer += 1
        if self.sorting_start <= self.timer <= self.sorting_end:
            self.fill_opvoer_locations()
            self.process_opvoer()
            self.update_sorter()
            #truck_list = self.call_inter()
        if self.timer == self.sorting_end:
            self.process_restcontainers()
        # Note: Below lines are used only to keep track of results, and are not needed to run the simulation
        self.n_floor_hist.append(len(self.unsorted_rc))
        self.n_floor_hist_parcels.append(sum(rollcage.n_parcels for rollcage in self.unsorted_rc))
        self.hist_parcels_processed.append(self.processed_parcels)
        self.hist_rc_processed.append(self.processed_rc)
        self.hist_parcels_dropped.append(self.parcels_dropped_cum)
        self.hist_rc_dropped.append(self.total_rc_in)

    def fill_opvoer_locations(self):
        """
        Function to move RC from the depot floor to the positions where parcels are added on the sorter.
        This distinction is made to keep track of which RC are currently in the process of sorting, and how many RC are
        on the depot floor. Note that some rc have a sorting time of zero and are sorted immediately. This is counter
        intuitive, but ensures that RC with a sorting time below 1 minute can fit the discrete time structure of the
        model (if the sorting time is 0.5, it will be rounded down to 0 or up to 1, each with 0.5 probability to ensure
        that the mean sorting time is 0.5)
        :return: No return
        """
        if self.name in config.blue_dict.keys():
            self.blue_reorder()
        while len(self.rc_at_opvoer) < self.state and len(self.unsorted_rc) > 0:
            rollcage = self.unsorted_rc[0]
            if rollcage.timer == 0:
                rollcage.add_to_sorter()
                self.processed_parcels += rollcage.n_parcels
                self.processed_rc += 1
                self.rc_on_sorter.append(rollcage)
                self.rc_processed.append(rollcage)
            else:
                self.rc_at_opvoer.append(rollcage)
            self.unsorted_rc.remove(rollcage)
        return

    def process_restcontainers(self):
        """
        Function to process remaining RC with sorted parcels that are not completely filled at the end of the sorting
        process.
        :return: No return
        """
        for rollcage in self.afvoer_rc.values():
            self.sorted_rc.append(rollcage)
            if type(rollcage) == str:
                print('Wrong datatype for RC!')
        self.afvoer_rc = []
        return

    def process_opvoer(self):
        """
        Function to update RC that are currently at the location where its parcels are put on the sorted. Each RC has a
        timer. When this timer runs out, all parcels have been added to the sorter and the RC will be moved from the
        opvoer location. In the next tick, a new RC can take its place.
        current one.
        :return: No return
        """
        for rollcage in self.rc_at_opvoer:
            rollcage.timer -= 1
            if rollcage.timer == 0:
                rollcage.add_to_sorter()
                self.processed_parcels += rollcage.n_parcels
                self.processed_rc += 1
                self.rc_on_sorter.append(rollcage)
                self.rc_processed.append(rollcage)
        self.rc_at_opvoer = list(filter(lambda x: x.timer > 0, self.rc_at_opvoer))
        return

    def update_sorter(self):
        """
        We assume that once the parcels of an rc have been added to the sorter, it takes some time for the sorting to be
        finished. This function keeps track of this time. At the end of this time, sorting is completed and the RC is
        deleted and its contents distributed over the different outgoing destinations
        :return: No return
        """
        for rollcage in self.rc_on_sorter:
            rollcage.sorting_timer -= 1
            if rollcage.sorting_timer == 0:
                rollcage.complete_sorting()
        self.rc_on_sorter = list(filter(lambda x: x.sorting_timer > 0, self.rc_on_sorter))  # Remove completed rc
        return

    def add_sorted_parcels(self, n_parcels, destination):
        """
        Function to add sorted parcels to an RC for the right direction. This function is called when an RC with
        collected parcels completes sorting. The contents of this RC are then distributed at once over the outgoing
        directions. For each of these directions, the present function is called. It is also checked whether the added
        parcels fit in the outgoing RC. If they don't fit, the outgoing RC is readied for transport and a new RC is
        generated for the remaining parcels. For now, we assume that 30 parcels fit in each RC. This assumption is to
        be replaced by fillgrades based on data.
        :param n_parcels: Total number of newly sorted parcels
        :param destination: Destination of the outgoing parcels
        :return: No return
        """
        # If an outgoing RC for the destination was already generated, the parcels are added to it.
        if destination in self.afvoer_rc.keys():
            rollcage = self.afvoer_rc[destination]
            if rollcage.fillgrade - rollcage.n_parcels > n_parcels:
                rollcage.n_parcels += n_parcels
            else:
                left = n_parcels - (rollcage.fillgrade - rollcage.n_parcels)
                rollcage.n_parcels = rollcage.fillgrade
                self.sorted_rc.append(rollcage)
                if type(rollcage) == str:
                    print('Wrong datatype for RC!')
                ident = uuid4()
                self.afvoer_rc[destination] = rc.Rollcage(ident, 0, self.name, destination, left, config.interfillgrade)
                self.afvoer_rc[destination].assign_crossdock()
        # If no outgoing RC was yet generated, a new one is made and added to a dictionary containing the RC that are
        # currently being filled
        else:
            ident = uuid4()
            self.afvoer_rc[destination] = rc.Rollcage(ident, 0, self.name, destination, n_parcels, config.interfillgrade)
            self.afvoer_rc[destination].assign_crossdock()
        return

    def blue_reorder(self):
        if self.timer < config.blue_dict[self.name]:
            self.unsorted_rc.sort(key=lambda x: x.blue)
        else:
            self.failed_rc += [rollcage for rollcage in self.unsorted_rc if rollcage.blue == False]
            self.unsorted_rc = list(filter(lambda x: x.blue == True, self.unsorted_rc))
        return

    #def call_inter(self):
    #    xdocks = {rollcage.xdock for rollcage in self.sorted_rc}
    #    truck_list = []
    #    for xdock in xdocks:
    #        n_rc = len([rollcage for rollcage in self.sorted_rc if rollcage.xdock == xdock])
    #        if n_rc >= 48:
    #            id = uuid4()
    #            rc_list = [rollcage for rollcage in self.sorted_rc if rollcage.xdock == xdock]
    #            while len(rc_list) > 48:
    #                rc_list.pop(-1)
    #            new_truck = tr.Truck(id, 999999, 48, xdock, self.name, 48)
    #            new_truck.rc = rc_list
    #            for rollcage in rc_list:
    #                self.sorted_rc.remove(rollcage)
    #            truck_list.append(new_truck)
    #    return truck_list


class Crossdock(PostnlLocation):
    def __init__(self, name=None, latitude=None, longitude=None, docks=None, buffer=None):
        super().__init__(name, latitude, longitude)
        self.name = name
        self.docks = docks
        self.docks = docks
        self.buffer = buffer

        self.rc = []


    def __str__(self):
        """
        Function used to display the crossdock characteristics. Mostly for debugging purposes
        :return: String with name of crossdock
        """
        return f"Crossdock {self.name}"


def update_depots(depot_dict):
    """
    Function that loops over all depots and performs the update for the depot for the tick
    :param depot_dict:
    :return:
    """
    for depot in depot_dict.values():
        depot.update()



def initialise_depots(sorting_limits=0.09):
    """
    Read depot info and initialise depots. Basic info like name, latitude, longitude, etc. is read from a csv file
    which contains all depot info that will not change frequently. For each depot, we read the start and end times of
    the sorting process from a different file, which is generated by the 'Ketenplanner'. These times are used as
    constants during a simulation run.
    :return: Dictionary containing all depots
    """
    depots = pd.read_excel(config.DEPOTFILE, sheet_name='DepotData')
    depots = depots[depots[config.col_dep_type].str.contains('DEPOT')]    # Filter out crossdocks

    sorting_time = pd.read_csv(config.SORTINGTIMESFILE)

    name_conversion = pd.read_csv(config.DEPOTNAMESFILE)
    sorting_time['DEPOT'] = sorting_time[config.col_sort_dep].replace(list(name_conversion[config.col_name_2]),
                                                                      list(name_conversion[config.col_name_1]))
    sorting_time.set_index(['DEPOT'], inplace=True)

    depdict = dict()
    for ind, row in depots.iterrows():
        if row['Name'] in sorting_time.index:
            start = sorting_time.loc[row[config.col_dep_name], config.col_sort_start]
            start = dt.time(hour=int(start.split(':')[0]), minute=int(start.split(':')[1]))
            start = dt.datetime.combine(config.date, start)
            start = mf.datetime_to_ticks(start, config.StartTime)

            end = sorting_time.loc[row[config.col_dep_name], config.col_sort_end]
            end = dt.time(hour=int(end.split(':')[0]), minute=int(end.split(':')[1]))
            end = dt.datetime.combine(config.date, end)
            end = mf.datetime_to_ticks(end, config.StartTime) + config.sorting_time
            state = sorting_time.loc[row[config.col_dep_name], config.col_sort_state]
        else:
            start = 0
            end = 0
            state = 0

        depdict[row[config.col_dep_name]] = Depot(row[config.col_dep_name], row[config.col_dep_lat],
                                                  row[config.col_dep_lon], state, row[config.col_dep_docks],
                                                  row[config.col_dep_floorcap], row[config.col_dep_pluscap],
                                                  row[config.col_dep_outmax], start, end, sorting_limits)
    return depdict


def initialise_crossdocks():
    """
    Function to initialize crossdocks. Note that these are not yet used in the present version of the simulation. But
    these will be needed to model inter transport and the arrival of rollcages at distribution depots
    :return: A dictionary with crossdocks
    """
    crossdocks = pd.read_excel(config.DEPOTFILE, sheet_name='DepotData')
    crossdocks = crossdocks[crossdocks[config.col_dep_type].str.contains('PLUS')
                            | crossdocks[config.col_dep_type].str.contains('CROSS')]
    crossdockdict = dict()
    for ind, row in crossdocks.iterrows():
        crossdockdict[row[config.col_dep_name]] = Crossdock(row[config.col_dep_name], row[config.col_dep_lat],
                                                            row[config.col_dep_lon], row[config.col_dep_xdocks],
                                                            row[config.col_dep_buffer])
    return crossdockdict
