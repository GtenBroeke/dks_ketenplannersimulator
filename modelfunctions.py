import datetime as dt
import config
import pandas as pd


def read_and_clean_orders():
    """
    Function to read orderset from the ketenplanner. Orders without planned time are filtered out. Depot names are
    converted to be consistent with those used in the rest of the simulation. Loading times are converted to
    datetime format. Note that the returned dataframe is used to create truck objects. The DataFrame itself is
    then no longer used in the simulation.
    :return: DataFrame containing an order in each row.
    """
    df = pd.read_csv(config.ORDERFILE)
    depot_names = pd.read_csv(config.DEPOTNAMESFILE)
    df['Name'] = df[config.col_ord_lospartij].replace(list(depot_names[config.col_name_3]),
                                                      list(depot_names[config.col_name_1]))
    df.dropna(subset=[config.col_ord_lostijd], inplace=True)

    df['LoadingTime'] = df[config.col_ord_lostijd]
    df['LoadingTime'] = df['LoadingTime'].apply(
        lambda x: dt.time(hour=int(x[0:2]), minute=int(x[3:5]), second=int(x[6:8])))
    df['LoadingTime'] = df['LoadingTime'].apply(
        lambda x: dt.datetime.combine(config.date, x) if x > dt.time(hour=6) else dt.datetime.combine(
            config.date + dt.timedelta(days=1), x))

    return df


def datetime_to_ticks(t, t_start):
    """
    Function to convert datetime to ticks (the time unit used in the simulation)
    :param t: datetime to be converted
    :param t_start: start of the simulation in datetime format
    :return: Time converted to ticks
    """
    timediff = t - t_start
    ticks = int(timediff.seconds / 60)
    return ticks


def tick_to_string(ticks, t_start):
    """
    Function to convert ticks (simulation time units) to datetime. This function is used only for display purposes.
    Computations within the simulation are performed in terms of ticks.
    :param ticks: Tick to be converted
    :param t_start: Start of the simulation in datetime format
    :return: Converted time in string format (this is used only for display purposes)
    """
    t = t_start + dt.timedelta(minutes=ticks)
    return str(t.time())


def check_blue(aar, destination):
    if destination == 'ALR' and 'ND' in aar:
        return True
    elif destination == 'TB' and 'ZD' in aar:
        return True
    elif destination == 'WB' and 'BEL' in aar:
        return True
    else:
        return False


def read_afzet():
    """
    Function to read data on 'afzetgebieden' this data will be used to determine the proportions of parcel for each
    client going in each of the possible directions
    :param DepotDict: Dictionary containing all depots, used to match the destination with a depot object in the model
    :return:
    """
    df = pd.read_csv(config.HINTERLANDFILE)
    df.fillna(0, inplace=True)
    depot_names = pd.read_csv(config.DEPOTNAMESFILE)

    for ind, row in depot_names.iterrows():
        df.rename(columns={row.Depotnaam2: row.Depotnaam1}, inplace=True)

    hinterland = dict()
    for ind, row in df.iterrows():
        cust = row[config.col_ord_cust_id]
        if cust not in hinterland.keys():
            hinterland[cust] = row['ALR':'ASN'].to_dict()

    return hinterland


def read_and_clean_inter():
    var = pd.read_csv('input/kp_solution/var_2022_05_23.csv')
    var = var[var['operatorservicecode'].isin([70, 91])]
    var = var[var['orderstatus'] == 'Delivered']
    var['pickup_time'] = var['pickup.startdateactual'] + ' ' + var['pickup.starttimeactual']
    var['pickup_time'] = pd.to_datetime(var['pickup_time'])
    var['pickup_time'] = var['pickup_time'].apply(lambda x: x.tz_convert('Europe/Berlin'))
    var['pickup_time'] = var['pickup_time'].apply(lambda x: x.tz_localize(None))

    var['dropoff_time'] = var['dropoff.startdateactual'] + ' ' + var['dropoff.starttimeactual']
    var['dropoff_time'] = pd.to_datetime(var['dropoff_time'])
    var['dropoff_time'] = var['dropoff_time'].apply(lambda x: x.tz_convert('Europe/Berlin'))
    var['dropoff_time'] = var['dropoff_time'].apply(lambda x: x.tz_localize(None))

    var.dropna(subset=['pickup_time'], inplace=True)
    var = var[var['pickup_time'] >= config.StartTime]
    var = var[var['pickup_time'] <= (config.StartTime + dt.timedelta(hours=24))]

    depot_names = pd.read_csv(config.DEPOTNAMESFILE)
    var['dropoff.locationname'] = var['dropoff.locationshortname'].replace(list(depot_names['DepotnaamVAR']),
                                                      list(depot_names[config.col_name_1]))
    var['pickup.locationname'] = var['pickup.locationshortname'].replace(list(depot_names['DepotnaamVAR']),
                                                                    list(depot_names[config.col_name_1]))

    crossdock_names = pd.read_excel(config.CROSSDOCKNAMESFILE)
    var['dropoff.locationname'] = var['dropoff.locationname'].replace(list(crossdock_names['AfkVar']),
                                                                      list(crossdock_names['Afk']))
    var['pickup.locationname'] = var['pickup.locationname'].replace(list(crossdock_names['AfkVar']),
                                                                    list(crossdock_names['Afk']))
    return var


def get_drivetime(origin, destination):
    return 30