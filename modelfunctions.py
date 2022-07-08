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
    depot_names = pd.read_csv(config.DEPOTNAMESFILE, sep=';')
    df['Name'] = df[config.col_ord_lospartij].replace(list(depot_names[config.col_name_3]),
                                                      list(depot_names[config.col_name_1]))
    df.dropna(subset=[config.col_ord_lostijd], inplace=True)

    df['LoadingTime'] = df[config.col_ord_lospartij]
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