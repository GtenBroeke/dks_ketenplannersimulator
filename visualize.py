import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import config
import modelfunctions as mf


def plot_floor_cap(DepDict, Depot):
    plt.plot(DepDict[Depot].n_floor_hist)
    plt.axhline(y=DepDict[Depot].floor_in)
    plt.show()
    return plt


def lineplots_per_depot(aanvoerlijnen, verwerkingslijnen, voorraadlijnen, floorcaplijnen, quartertable, b_sol, l_sol,
                        A_sol, df_depots, depot_table, depdict, orders):
    """
    Displays the aanvoerlijnen, verwerkingslijnen, voorraadlijnen graph per depot in a plot.

    Args:
    aanvoerlijnen: df with rows=depots and columns=times, containing number of parcels unloaded (cumulative)
    verwerkingslijnen: df with rows=depots and columns=times, containing number of parcels sorted (cumulative)
    voorraadlijnen: df with rows=depots and columns=times, containing number of parcels at the floor
    floorcaplijnen: df with rows=depots and columns=times, containing maximum floorcapacity at each time
    quartertable: df with translation "real" quarters to model-quarters
    b_sol: df with the begin time of each depot (in model-quarters)
    l_sol: df with the end time of each depot (in model-quarters)
    A_sol: df with the state for each depot
    df_depots: df with depot characteristics
    depot_table: df with the number of MG and NMG parcels per depot

    Returns:
        No returns
    """
    f, axes = plt.subplots(16, 2, figsize=(15, 50), sharey=True, sharex=True)
    f.suptitle("Aanvoer/Verwerking/Voorraad", fontsize=16, y=0.93)
    positie_x = 0
    positie_y = 0
    aanvoerlijnen.index = aanvoerlijnen.index.astype(str)

    for depot in depdict.values():
        #abb_depot_real = df_depots.loc[df_depots.index == depot, "DEPOT"].iloc[0]
        abb_depot_real = depot.name
        totaal = info_depot_lineplots(depot.name, aanvoerlijnen, verwerkingslijnen, voorraadlijnen, floorcaplijnen)
        state = depot.state
        #eindtijd = l_sol.loc[l_sol.DEPOT == depot, "Eindtijd"].iloc[0]
        #begintijd = b_sol.loc[b_sol.DEPOT == depot, "Starttijd"].iloc[0]
        #eindtijd_time_str = quartertable.loc[quartertable.t == eindtijd, "beginTimes_str"].iloc[0]
        #begintijd_time_str = quartertable.loc[quartertable.t == begintijd, "beginTimes_str"].iloc[0]
        eindtijd = depot.sorting_end
        begintijd = depot.sorting_start
        eindtijd_time_str = mf.tick_to_string(eindtijd - config.sorting_time, config.StartTime)
        begintijd_time_str = mf.tick_to_string(begintijd, config.StartTime)
        #aantal_MG = int(depot_table.loc[depot_table.DEPOT2 == depot, "#Pakketten gerealiseerd (max)"].iloc[0])
        #aantal_NMG = int(depot_table.loc[depot_table.DEPOT2 == depot, "#Pakketten_NMG"].iloc[0])
        aantal_MG = int(depot.processed_parcels)
        ord = orders[orders['Name'] == depot.name]
        aantal_NMG = int(sum(ord['#Pakketten_NMG']))
        kwargs = {'cumulative': True}
        ax = axes[positie_y, positie_x]
        ax1 = sns.lineplot(data=totaal, x="index", y="Pkt_anvr", ax=axes[positie_y, positie_x]).set(
            title=str(abb_depot_real) + " (" + begintijd_time_str + " - " + eindtijd_time_str + ", state " + str(
                state) + ")", xlabel=' ')
        ax1 = sns.lineplot(data=totaal, x="index", y="Pkt_verw", ax=axes[positie_y, positie_x]).set(
            title=str(abb_depot_real) + " (" + begintijd_time_str + " - " + eindtijd_time_str + ", state " + str(
                state) + ")", xlabel=' ')
        ax1 = sns.lineplot(data=totaal, x="index", y="Pkt_voor", ax=axes[positie_y, positie_x]).set(
            title=str(abb_depot_real) + " (" + begintijd_time_str + " - " + eindtijd_time_str + ", state " + str(
                state) + ")", xlabel=' ')
        ax1 = sns.lineplot(data=totaal, x="index", y="Floorcap", color='g', linestyle=':',
                           ax=axes[positie_y, positie_x]).set(
            title=str(abb_depot_real) + " (" + begintijd_time_str + " - " + eindtijd_time_str + ", state " + str(
                state) + ", MG: " + str(aantal_MG) + ", NMG: " + str(aantal_NMG) + ")", xlabel=' ')

        # Begin and end time
        ax.axvline(x=eindtijd, color='r', linestyle='--')
        ax.axvline(x=begintijd, color='r', linestyle='--')

        # Floorcapacity
        # ax.axhline(y=df_depots.at[depot,"floorcap"] * config.FILLING_RATE,color='g',linestyle=':')
        ax.legend(labels=["Aanvoer", "Verwerking", "Voorraad", "Vloercap"])

        if positie_x == 1:
            positie_x = 0
            positie_y = positie_y + 1
        else:
            positie_x = 1
    f.show()


def info_depot_lineplots(depot, aanvoerlijnen, verwerkingslijnen, voorraadlijnen, floorcaplijnen):
    """
    Makes a dataframe containing aanvoer, verwerking and voorraad for a depot

    Parameters:
    depot (string): depot
    aanvoerlijnen (dataframe): dataframe containing aanvoerlijnen for depot
    verwerkingslijnen (dataframe): containing verwerkingslijnen for depot
    voorraadlijnen (dataframe): containing voorraadlijnen for depot

    Returns:
    df_totaal (dataframe): unified lines for selected depot
    """
    anvr = pd.DataFrame(aanvoerlijnen.loc[depot]).reset_index().rename(columns={depot: "Pkt_anvr"})
    verw = pd.DataFrame(verwerkingslijnen.loc[depot]).reset_index().rename(columns={depot: "Pkt_verw"})
    voor = pd.DataFrame(voorraadlijnen.loc[depot]).reset_index().rename(columns={depot: "Pkt_voor"})
    floor = pd.DataFrame(floorcaplijnen.loc[depot]).reset_index().rename(columns={depot: "Floorcap"})
    #df_totaal = pd.merge(pd.merge(pd.merge(anvr, verw, on="t", how='left'), voor, on="t", how='left'), floor, on="t",
    #                     how='left')
    df_totaal = pd.merge(pd.merge(pd.merge(anvr, verw, on="index", how='left'), voor, on="index", how='left'), floor, on="index", how='left')
    return df_totaal


def kp_visualization(DepotDict, orders):
    quartertable = pd.read_csv('input\\kwartierentabel.csv')
    df_dep = pd.read_csv('input\\depots.csv')

    df_aanvoer = pd.DataFrame()
    df_deptable = pd.DataFrame()
    df_aanvoer_parcels = pd.DataFrame()
    df_sorted_parcels = pd.DataFrame()
    df_dropped_parcels = pd.DataFrame()
    df_floorcap = pd.DataFrame()
    for depot in DepotDict.values():
        df_aanvoer = pd.concat([df_aanvoer, pd.DataFrame([depot.n_floor_hist], index=[depot.name])])
        df_deptable = pd.concat([df_dep, pd.DataFrame([depot.processed_parcels], index=[depot.name])])
        df_aanvoer_parcels = pd.concat(
            [df_aanvoer_parcels, pd.DataFrame([depot.n_floor_hist_parcels], index=[depot.name])])
        df_sorted_parcels = pd.concat(
            [df_sorted_parcels, pd.DataFrame([depot.hist_parcels_processed], index=[depot.name])])
        df_dropped_parcels = pd.concat(
            [df_dropped_parcels, pd.DataFrame([depot.hist_parcels_dropped], index=[depot.name])])
        floorcaprow = [(depot.floor_in + depot.floor_plus)*30] * (depot.sorting_start + 60) + \
                      [depot.floor_in*30] * (config.n_steps - depot.sorting_start - 60)
        df_floorcap = pd.concat([df_floorcap, pd.DataFrame([floorcaprow], index=[depot.name])])

    lineplots_per_depot(df_dropped_parcels, df_sorted_parcels, df_aanvoer_parcels, df_floorcap, quartertable,
                                  0, 0, 10, df_dep, df_deptable, DepotDict, orders)
    return


def kp_visualization_RC(DepotDict, orders):
    quartertable = pd.read_csv('input\\kwartierentabel.csv')
    df_dep = pd.read_csv('input\\depots.csv')

    df_aanvoer = pd.DataFrame()
    df_deptable = pd.DataFrame()
    df_aanvoer_parcels = pd.DataFrame()
    df_sorted_rc = pd.DataFrame()
    df_dropped_rc = pd.DataFrame()
    df_floorcap = pd.DataFrame()
    for depot in DepotDict.values():
        df_aanvoer = pd.concat([df_aanvoer, pd.DataFrame([depot.n_floor_hist], index=[depot.name])])
        df_deptable = pd.concat([df_dep, pd.DataFrame([depot.processed_parcels], index=[depot.name])])
        df_aanvoer_parcels = pd.concat(
            [df_aanvoer_parcels, pd.DataFrame([depot.n_floor_hist_parcels], index=[depot.name])])
        df_sorted_rc = pd.concat(
            [df_sorted_rc, pd.DataFrame([depot.hist_rc_processed], index=[depot.name])])
        df_dropped_rc = pd.concat(
            [df_dropped_rc, pd.DataFrame([depot.hist_rc_dropped], index=[depot.name])])
        floorcaprow = [(depot.floor_in + depot.floor_plus)] * (depot.sorting_start + 60) + \
                      [depot.floor_in] * (config.n_steps - depot.sorting_start - 60)
        df_floorcap = pd.concat([df_floorcap, pd.DataFrame([floorcaprow], index=[depot.name])])

    lineplots_per_depot(df_dropped_rc, df_sorted_rc, df_aanvoer, df_floorcap, quartertable,
                                  0, 0, 10, df_dep, df_deptable, DepotDict, orders)
    return