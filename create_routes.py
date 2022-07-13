# create output files: routes and trajects
# routes: for all options: all nodes from verzend depot to distributie depot
# trajects: for all options in routes: all nodes and their successive node

import json

inputfile = 'input/directions_crossdock_shifts.csv'

routes = dict()
trajects = dict()
with open(inputfile, 'r') as infile:
    for i, line in enumerate(infile):

        if i == 0:
            header = line.strip().split(";")

            if len(header) < 5:
                print('Wrong separator?')
                print(header)
                break

            # find position of columns
            j_destination = header.index('destination')
            j_origin = header.index('origin')
            j_shift = header.index('shift_indicator')
            j_crossdock = header.index('crossdock')
            j_direction = header.index('transport_direction')

            continue

        # split new line into callable variables
        items = line.strip().split(";")

        # give depots a new name based on role as VERZEND or DISTRIBUTION
        # let x-dock names start with a 'x_'
        destination = items[j_destination].strip() + "_distr"
        origin = items[j_origin].strip() + "_verz"
        shift = items[j_shift].strip()
        crossdock = "x_" + items[j_crossdock].strip()
        direction = items[j_direction].strip()

        if not origin in routes:
            routes[origin] = dict()


        if not crossdock in routes[origin]:

            # skip bad x-dock names
            if crossdock == 'x_nvt' or crossdock == 'x_':
                continue
            else:
                routes[origin][crossdock] = list()

        if not destination in routes[origin][crossdock]:
            routes[origin][crossdock].append(destination)

        if not origin in trajects:
            trajects[origin] = list()

        if not crossdock in trajects[origin]:

            # skip bad x-dock names
            if crossdock == 'x_nvt' or crossdock == 'x_':
                continue
            else:
                trajects[origin].append(crossdock)

        if not crossdock in trajects:

            # skip bad x-dock names
            if len(crossdock) <= 1 or crossdock == 'x_nvt' or crossdock == 'x_':
                continue
            else:
                trajects[crossdock] = list()

        if not destination in trajects[crossdock]:
            trajects[crossdock].append(destination)

with open('intermediate/trajects.json', 'w') as outfile:
    json.dump(trajects, outfile, sort_keys=True, indent=4)

with open('intermediate/routes.json', 'w') as outfile:
    json.dump(routes, outfile, sort_keys=True, indent=4)