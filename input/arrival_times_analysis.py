# Analysis of historic arrival times of trucks used for collection at depots.

import pandas as pd
import datetime as dt
import config

df = pd.read_csv('input\VAR_hist.csv')
df = df[df['orderstatus'] == 'Delivered']
df.dropna(subset=['dropoff.starttimeactual'], inplace=True)
df['dropoff_time'] = pd.to_datetime(df['dropoff.starttimeactual'])
df['dropoff_time'] = df['dropoff_time'].apply(lambda x: x.tz_convert('Europe/Berlin'))
df['dropoff_time'] = df['dropoff_time'].apply(lambda x: x.tz_localize(None))

df['dropoff.endtimescheduled'] = pd.to_datetime(df['dropoff.endtimescheduled'])
df['dropoff.endtimescheduled'] = df['dropoff.endtimescheduled'].apply(lambda x: x.tz_convert('Europe/Berlin'))
df['dropoff.endtimescheduled'] = df['dropoff.endtimescheduled'].apply(lambda x: x.tz_localize(None))

date = df['dropoff_time_ticks'].iloc[0].date()
starttime = dt.datetime.combine(date, dt.time(hour=6))
df['minutes'] = (df['dropoff_time'] - starttime)
df['minutes'] = df['minutes'].apply(lambda x: x.total_seconds() / 60)
df['minutes'] = df['minutes'].apply(lambda x: x + (24*60) if x < 0 else x)

names = pd.read_csv('input\\vertaling_depotnamen.csv')
df['dropoff.locationname'] = df['dropoff.locationshortname'].replace(list(names['DepotnaamVAR']),
                                                      list(names[config.col_name_1]))
df_grouped = df.groupby(['aarnumber', 'dropoff.endtimescheduled', 'dropoff.locationname']).agg({'minutes': ['mean', 'std']}).reset_index()
df_grouped.columns = ['aar', 'endtime_scheduled', 'location', 'minutes_mean', 'minutes_sd']
df_grouped['endtime_scheduled'] = df_grouped['endtime_scheduled'].apply(lambda x: x.time())

orders = pd.read_csv('input\kp_solution\ketenmanagement.csv')

orders['Lospartij huidig'] = orders['Lospartij huidig'].replace(list(names['Depotnaam3']),
                                                      list(names[config.col_name_1]))
orders['planned_time'] = pd.to_datetime(orders['Gepland lossen tot huidig'])
orders['planned_time'] = orders['planned_time'].apply(lambda x: x.time())

orders_merged = pd.merge(left=orders, right=df_grouped,
                         left_on=['AAR nummer', 'Lospartij huidig', 'planned_time'],
                         right_on=['aar', 'location', 'endtime_scheduled'])
orders_merged.to_csv('orderset_arrivals.csv')