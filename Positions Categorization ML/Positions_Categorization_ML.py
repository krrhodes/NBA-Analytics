import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from collections import OrderedDict
import random
from nba_api.stats.static import players
from nba_api.stats.endpoints import leaguedashptstats, leagueleaders, commonplayerinfo

###########################################################################################################################################
# K Means algorithm implementation
###########################################################################################################################################

# Get the distance of dataset from points in smaller dataset
def euclidean_distance(df, centroids, exclude = []):
    for i in centroids.keys():
        df['distance_from_{}'.format(i)] = [
            np.sqrt(
                sum([(df[df.columns[j]][k] - centroids[i][j]) ** 2
                      for j in range(len(df.columns) - len(exclude))])
            )
            for k in range(len(df[df.columns[0]]))
        ]

# Plot multidimesional data as 2D LDA graph
def plotLDA(df, centroids, k, colmap, exclude = []):
    lda = LDA(n_components=2)
    lda_transformed = pd.DataFrame(lda.fit_transform(df.loc[:,[column for column in df.columns
                                                               if column not in exclude]], df['color']))
    lda_transformed_centroids = pd.DataFrame(lda.fit_transform(centroids.loc[:,[column for column in df.columns
                                                               if column not in exclude]], centroids.keys()))
    # Plot each series
    for i in range(k):
        plt.scatter(lda_transformed[y==i][0], lda_transformed[y==i][1], label='Position ' + i, c=colmap[i], alpha=0.5, edgecolor='k')
        plt.scatter(lda_transformed_centroids[y==i][0], lda_transformed_centroids[y==i][1], label='Centroid ' + i, c=colmap[i])
    # Display legend and show plot
    plt.legend(loc=k)
    plt.show()

# Use the K means algorithm to sort NBA players into undefined categories
def kmeans(df, k):

    # Initialize centroids as random datapoints
    np.random.seed(200)
    centroids = {
        i: []
        for i in range(k)
    }
    for i in centroids.keys():
        for j in range(len(df.columns)):
            centroids[i].append(np.random.randint(0, 80))

    #random color for each clasification
    colmap = {
        i: "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        for i in range(k)
    }

    #dont use the columns in the calculations, they are generated in the algorithm
    exclude = ['color', 'closest']
    for i in centroids.keys():
        exclude.append('distance_from_{}'.format(i))

    df = _assignment(df, centroids, colmap, exclude)
    #Repeat assingment and update phases until assignments no longer change
    while True:
        closest_centroids = df['closest'].copy(deep=True)
        centroids = _update(df, centroids, exclude)
        df = _assignment(df, centroids, colmap, exclude)

        plotLDA(df, centroids, k, colmap, exclude)

        if closest_centroids.equals(df['closest']):
            break

    #finally plot the result
    plotLDA(df, centroids, k, colmap, exclude)

# Assignment phase, assign each datapoint to the nearest centroid
def _assignment(df, centroids, colmap, exclude):
    euclidean_distance(df, centroids, exclude)
    centroid_distance_cols = ['distance_from_{}'.format(i) for i in centroids.keys()]
    df['closest'] = df.loc[:, centroid_distance_cols].idxmin(axis=1)
    df['closest'] = df['closest'].map(lambda x: int(x.lstrip('distance_from_')))
    df['color'] = df['closest'].map(lambda x: colmap[x])
    return df

# Update phase, move centroids' positions towards the center of their assigned datapoints
def _update(df, centroids, exclude = []):
    for i in centroids.keys():
        for j in range(len(df.columns) - len(exclude)):
            centroids[i][j] = np.mean(df[df['closest'] == i][df.keys()[j]])

    return centroids

###########################################################################################################################################
#Set Up data for algorithm
###########################################################################################################################################
df = pd.DataFrame({})

# API calls
stats_distance = leaguedashptstats.LeagueDashPtStats(player_or_team="Player", pt_measure_type="SpeedDistance")
stats_drives = leaguedashptstats.LeagueDashPtStats(player_or_team="Player", pt_measure_type="Drives")
stats_catchshoot = leaguedashptstats.LeagueDashPtStats(player_or_team="Player", pt_measure_type="CatchShoot")
stats_pullup = leaguedashptstats.LeagueDashPtStats(player_or_team="Player", pt_measure_type="PullUpShot")
stats_postup = leaguedashptstats.LeagueDashPtStats(player_or_team="Player", pt_measure_type="PostTouch")
stats_passing = leaguedashptstats.LeagueDashPtStats(player_or_team="Player", pt_measure_type="Passing")
stats_possession = leaguedashptstats.LeagueDashPtStats(player_or_team="Player", pt_measure_type="Possessions")
stats_rebounding = leaguedashptstats.LeagueDashPtStats(player_or_team="Player", pt_measure_type="Rebounding")
stats_leagueleaders = leagueleaders.LeagueLeaders()

player_ids = set()#[player['id'] for player in players.get_active_players()]
player_ids_ignore = set()
# Heights and weights were causing issues trying to connect to the commonplayerinfo endpoint, so they have been omitted
#player_heights = []
#player_weights = []
#for player_id in player_ids:
#    try:
#        height_string = commonplayerinfo.CommonPlayerInfo(player_id=player_id).common_player_info.data['data'][0][10].split('-')
#        if len(height_string) is 2:
#            player_heights.append(int(height_string[0]) * 12 + int(height_string[1])) # convert height to inches
#        else: #No data available
#            player_ids_ignore.append(player_id)
#    except:#connection error
#        player_ids_ignore.append(player_id)
#    try:
#        weight_string = commonplayerinfo.CommonPlayerInfo(player_id=player_id).common_player_info.data['data'][0][11]
#        if weight_string.isdigit() and (len(player_ids_ignore) is 0 or player_ids_ignore[-1] is not player_id):
#            player_weights.append(int(weight_string))
#        else: #No data available
#            if len(player_ids_ignore) is not 0 and player_ids_ignore[-1] is not player_id:
#                player_ids_ignore.append(player_id)
#                player_heights.pop()
#    except:#connection error
#        player_ids_ignore.append(player_id)
#        player_heights.pop()

#df['height'] = player_heights
#df['weight'] = player_weights

#Make sure data is consistent
for entry in stats_leagueleaders.league_leaders.data['data']:
    player_ids.add(entry[0])
player_ids_new = set()
for entry in stats_drives.league_dash_pt_stats.data['data']:
    if entry[0] in player_ids:
        player_ids_new.add(entry[0])
player_ids.clear()
player_ids = player_ids_new.copy()
player_ids_new.clear()
for entry in stats_catchshoot.league_dash_pt_stats.data['data']:
    if entry[0] in player_ids:
        player_ids_new.add(entry[0])
player_ids.clear()
player_ids = player_ids_new.copy()
player_ids_new.clear()
for entry in stats_pullup.league_dash_pt_stats.data['data']:
    if entry[0] in player_ids:
        player_ids_new.add(entry[0])
player_ids.clear()
player_ids = player_ids_new.copy()
player_ids_new.clear()
for entry in stats_postup.league_dash_pt_stats.data['data']:
    if entry[0] in player_ids:
        player_ids_new.add(entry[0])
player_ids.clear()
player_ids = player_ids_new.copy()
player_ids_new.clear()
for entry in stats_passing.league_dash_pt_stats.data['data']:
    if entry[0] in player_ids:
        player_ids_new.add(entry[0])
player_ids.clear()
player_ids = player_ids_new.copy()
player_ids_new.clear()
for entry in stats_possession.league_dash_pt_stats.data['data']:
    if entry[0] in player_ids:
        player_ids_new.add(entry[0])
player_ids.clear()
player_ids = player_ids_new.copy()
player_ids_new.clear()
for entry in stats_distance.league_dash_pt_stats.data['data']:
    if entry[0] in player_ids:
        player_ids_new.add(entry[0])
player_ids.clear()
player_ids = player_ids_new.copy()
player_ids_new.clear()
for entry in stats_rebounding.league_dash_pt_stats.data['data']:
    if entry[0] in player_ids:
        player_ids_new.add(entry[0])
player_ids.clear()
player_ids = player_ids_new.copy()
player_ids_new.clear()


#fill dicts with stats, rather than searching each dataset for each different player. This will speed it up a lot
# {<player_id> : stat}
# data is ordered by player ids
for entry in stats_leagueleaders.league_leaders.data['data']:
    if entry[7] <= 0:
        player_ids_ignore.add(entry[0])
player_fgas = OrderedDict({
    entry[0]:entry[7]
    for entry in stats_leagueleaders.league_leaders.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })

player_drives = OrderedDict({
    entry[0] : entry[10]
    for entry in stats_drives.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['drives_per_attempt'] = [data / player_fgas[player_id] for player_id, data in player_drives.items()]

player_catch_shoot = OrderedDict({
    entry[0] : entry[9]
    for entry in stats_catchshoot.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['catch-and-shoots_per_attempt'] = [data / player_fgas[player_id] for player_id, data in player_catch_shoot.items()]

player_pull_up = OrderedDict({
    entry[0] : entry[9]
    for entry in stats_pullup.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['pull-ups_per_attempt'] = [data / player_fgas[player_id] for player_id, data in player_pull_up.items()]

player_post_up = OrderedDict({
    entry[0] : entry[11]
    for entry in stats_postup.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['post-ups_per_attempt'] = [data / player_fgas[player_id] for player_id, data in player_post_up.items()]

player_passes_per_min = OrderedDict({
    entry[0] : entry[8]/entry[7]
    for entry in stats_passing.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['passes_made_per_minute'] = [data for data in player_passes_per_min.values()]

player_dribbles_per_touch = OrderedDict({
    entry[0] : entry[13]
    for entry in stats_possession.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['dribbles_per_touch'] = [data for data in player_dribbles_per_touch.values()]

player_avg_speed_off = OrderedDict({
    entry[0] : entry[13]
    for entry in stats_distance.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['avg_speed_off'] = [data for data in player_avg_speed_off.values()]

player_avg_speed_def = OrderedDict({
    entry[0] : entry[14]
    for entry in stats_distance.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['avg_speed_def'] = [data for data in player_avg_speed_def.values()]

player_oreb_chance_per_min = OrderedDict({
    entry[0] : entry[12]/entry[7]
    for entry in stats_rebounding.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['oreb_chance_per_min'] = [data for data in player_oreb_chance_per_min.values()]

player_dreb_chance_per_min = OrderedDict({
    entry[0] : entry[21]/entry[7]
    for entry in stats_rebounding.league_dash_pt_stats.data['data']
    if entry[0] not in player_ids_ignore and entry[0] in player_ids
    })
df['dreb_chance _per_min'] = [data for data in player_dreb_chance_per_min.values()]


kmeans(df, 3)