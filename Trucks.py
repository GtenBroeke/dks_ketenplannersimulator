import random
from uuid import uuid4

import DepotClasses as dep
import Rollcage as rc
import config
import numpy as np
import modelfunctions as mf
import production_state as ps


class Truck:
    def __init__(self, identifier=None, timer=None, n_rc=None, destination=None, origin=None,
                 fillgrade=None, status=None, blue=None):
        self.identifier = identifier
        self.timer = timer
        self.n_rc = n_rc
        self.destination = destination
        self.origin = origin
        self.fillgrade = fillgrade
        self.status = status
        self.blue = blue

        self.rc = []

    def __str__(self):
        """
        String to alter the information displayed about trucks in the simulation. Mostly used for debugging purposes.
        :return: String for display
        """
        return f"Truck from {self.origin.name} to {self.destination.name} with {self.n_rc} RC"

    def update(self):
        """
        Function used to update trucks. Called each tick for each truck. Each truck contains a timer, which is reduced
        by 1 each tick. Once it reaches zero, the truck arrives at the depot and drops its rollcages at the depot. Note
        that in the present version we do not model unloading time or dock occupancy. This can still be added. An extra
        unloading time could be modelled by simply increasing the timer.
        :return: No return
        """
        self.timer -= 1
        if self.timer == 0:
            if self.status == 0:
                depot = self.destination
                self.drop_rc(depot)
            if self.status == 1:
                depot = self.origin
                self.pickup_rc(depot)
                self.timer = mf.get_drivetime(self.origin, self.destination)
                self.status = 2
            if self.status == 2:
                dropoff_location = self.destination
                self.unload_rc(dropoff_location)
        return

    def drop_rc(self, depot):
        """
        Function to let the truck drop its RC at the depot. The RC are created on arrival and immediately brought to the
        depot floor. Note that in the present version we do not model unloading time or dock occupancy. This can still
        be added. An extra unloading time could be modelled by simply increasing the timer of the truck carrying RC.
        Each RC is created with a predefined sorting time. This sorting time is based on the number of parcels in the
        RC (taken from the orderset) and on mean sorting speed. Usually the sorting time is not a rounded number of
        minutes. To make the sorting time fit with the discrete 1 minute time-steps of the model, we round each number
        up/down with a probability depending on the decimal sorting time. E.g., an RC with 1.8 min sorting time has a
        0.8 probability to be rounded up to 2, and a 0.2 probability to be rounded down to 1.
        :param depot:
        :return: No return
        """
        nrc = self.n_rc
        while nrc > 0:
            rcequiv = min(1, nrc)
            identifier = uuid4()
            sorting_time = self.fillgrade * rcequiv / (ps.get_productions_states(depot.sorting_limits)[depot.state]['production'] / depot.state / 60)
            min_time = int(np.floor(sorting_time))
            max_time = int(np.ceil(sorting_time))
            prob_high = sorting_time - min_time
            rc_timer = random.choices([min_time, max_time], weights=[1-prob_high, prob_high])[0]
            depot.unsorted_rc.append(rc.Rollcage(identifier, rc_timer, self.origin, self.destination,
                                                 self.fillgrade * rcequiv, self.fillgrade * rcequiv, self.blue))
            depot.total_rc_in += 1
            depot.parcels_dropped_cum += self.fillgrade * rcequiv
            nrc -= rcequiv
        return


    def unload_rc(self, location):
        rc_delivered = []
        if type(location) == str:
            self.rc = []
            self.n_rc = 0
            return
        for rollcage in self.rc:
            if location.name == rollcage.xdock:
                location.rc_crossdock.append(rollcage)
                location.rc_cum += 1
                rc_delivered.append(rollcage)
            else:
                location.rc_delivery.append(rollcage)
                rc_delivered.append(rollcage)
        #for rollcage in rc_delivered:
        #    self.rc.remove(rollcage)
        #self.n_rc = len(self.rc)


    def pickup_rc(self, depot):
        if type(self.destination) in [dep.Depot, dep.Crossdock]:
            name = self.destination.name
        else:
            name = self.destination
        if type(depot) == dep.Depot:
            n_rc = min(48, len([rollcage for rollcage in depot.sorted_rc if rollcage.xdock == name]))
            self.rc = [rollcage for rollcage in depot.sorted_rc if rollcage.xdock == name][0:n_rc]
            self.n_rc = n_rc
            depot.remove_loaded_rc(self.rc)
            if n_rc < 48:
                n_rc_cd = min(48-n_rc, len([rollcage for rollcage in depot.rc_crossdock if rollcage.destination == name]))
                self.rc.extend([rollcage for rollcage in depot.rc_crossdock if rollcage.destination == name][0:n_rc_cd])
                self.n_rc += n_rc_cd
                depot.remove_loaded_rc(self.rc[:-n_rc_cd])
        elif type(depot) == dep.Crossdock:
            n_rc = min(48, len([rollcage for rollcage in depot.rc_crossdock if rollcage.destination == name]))
            self.rc = [rollcage for rollcage in depot.rc_crossdock if rollcage.destination == name][0:n_rc]
            self.n_rc = n_rc
            depot.remove_loaded_rc(self.rc)


def initialise_trucks(orders, depot_dict, delay=config.unloading_time, arrival_window=0):
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
        timer = mf.datetime_to_ticks(row.LoadingTime, config.StartTime)
        timer += delay
        timer += random.randint(-arrival_window, arrival_window)
        destination = depot_dict[row[config.col_ord_dest]]
        origin = row[config.col_ord_cust_id]
        fillgrade = row[config.col_ord_mg] / row[config.col_ord_rc]
        rcp = row[config.col_ord_rc]
        blue = mf.check_blue(row[config.col_ord_aar], row[config.col_ord_dest])
        truck_dict[identifier] = Truck(identifier, timer, rcp, destination, origin, fillgrade, 0, blue)
    return truck_dict


def update_trucks(truck_dict):
    """
    Function to update the timer of all trucks used for collection or inter transport (currently only collection) when
    this function is called each tick. Once the timer reaches zero, the truck reaches its destination and is deleted.
    :param truck_dict: Dictionary with all trucks
    :return: No return
    """
    keys = list(truck_dict.keys())
    for key in keys:
        truck = truck_dict[key]
        truck.update()
        if truck.timer == 0 and truck.status == 0:
            del truck_dict[key]
        if truck.timer == 0 and truck.status ==2:
            del truck_dict[key]


def initialise_inter(interorders, depot_dict, crossdock_dict):
    inter_dict = dict()
    for ind, row in interorders.iterrows():
        identifier = row['ordernumber']
        destination = row['dropoff.locationname']
        origin = row['pickup.locationname']

        if destination == 'AMF':
            print("Pause debugger")

        if origin in depot_dict.keys():
            origin = depot_dict[origin]
        if destination in depot_dict.keys():
            destination = depot_dict[destination]
        if origin in crossdock_dict.keys():
            origin = crossdock_dict[origin]
        if destination in crossdock_dict.keys():
            destination = crossdock_dict[destination]

        timer = mf.datetime_to_ticks(row['pickup_time'], config.StartTime)
        fillgrade = 30
        inter_dict[identifier] = Truck(identifier, timer, 0, destination, origin, fillgrade, 1, 0)
    return inter_dict