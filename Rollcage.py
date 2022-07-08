import config


class Rollcage:
    def __init__(self, identifier=None, timer=None, origin=None, destination=None, n_parcels=None, fillgrade=None):
        self.identifier = identifier
        self.timer = timer
        self.origin = origin
        self.destination = destination
        self.n_parcels = n_parcels
        self.fillgrade = fillgrade

        self.sorting_timer = 0

    def add_to_sorter(self):
        """
        This function sets the time required for a packages parcels to be sorted, once they have been put on the sorter
        :return: No return
        """
        self.sorting_timer = config.sorting_time

    def complete_sorting(self):
        """
        This function finishes the sorting process for the RC. Based on the customer the RC was collected from, we
        obtain the distribution of outgoing directions. For each of these directions, the corresponding number of
        parcels is then added to an RC for that directions. 
        :return: No return
        """
        if self.origin in config.afzet.keys():
            for destination in config.afzet[self.origin].keys():
                parcels = self.n_parcels * config.afzet[self.origin][destination]
                self.destination.add_sorted_parcels(parcels, destination)
        else:
            print("Order number not found for afzetgebieden")
            # Note: below follows a temporary workaround. For some orders the distribution over the destinations seems
            # te be missing, so we use the distribution of another customer. This should still be fixed.
            for destination in config.afzet['C6801975680'].keys():
                parcels = self.n_parcels * config.afzet['C6801975680'][destination]
                self.destination.add_sorted_parcels(parcels, destination)
        return
