import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nba_api.stats.static import players
from nba_api.stats.endpoints import leaguedashptstats, leagueleaders, commonplayerinfo

###########################################################################################################################################
# K Means algorithm implementation
###########################################################################################################################################

# Get the distance of dataset from points in smaller dataset
def euclidean_distance(df, centroids, k, exclude = []):
    for i in centroids.keys():
        df['distance_from_{}'.format(i)] = (
            np.sqrt(
                sum([(df[df.keys(j)] - centroids[i][df.keys(j)]) ** 2
                      for j in len(df.ix[:, df.columns - exclude])])
            )
        )

# Plot multidimesional data as 2D LDA graph
def plotLDA(df, centroids, k, colmap, exclude = []):
    lda = LDA(n_components=2)

    lda_transformed = pd.DataFrame(lda.fit_transform(df.ix[:, df.columns - exclude], df['color']))
    lda_transformed_centroids = pd.DataFrame(lda.fit_transform(centroids, centroids.keys()))
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
        for j in len(df):
            centroids[i].append(np.random.randint(0, 80))

    #random color for each clasification
    colmap = {
        i: "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        for i in range(k)
    }

    #dont use the columns in the calculations, they are generated in the algorithm
    exclude = ['color', 'closest']
    for i in centroids.keys():
        exclude.append['distance_from_{}'.format(i)]

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
    euclidean_distance(df, centroids, k, exclude)
    centroid_distance_cols = ['distance_from_{}'.format(i) for i in centroids.keys()]
    df['closest'] = df.loc[:, centroid_distance_cols].idxmin(axis=1)
    df['closest'] = df['closest'].map(lambda x: int(x.lstrip('distance_from_')))
    df['color'] = df['closest'].map(lambda x: colmap[x])
    return df

# Update phase, move centroids' positions towards the center of their assigned datapoints
def _update(df, centroids, exclude = []):
    for i in centroids.keys():
        for j in len(df.ix[:, df.columns - exclude]):
            centroids[i][j] = np.mean(df[df['closest'] == i][df.keys()[j]])

    return centroids

###########################################################################################################################################
#Set Up data for algorithm
###########################################################################################################################################
df = pd.DataFrame({
    'height': [],
    'weight': []
})

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

player_ids = [player['id'] for player in players.get_active_players()]

player_heights = []
player_weights = []
for player_id in player_ids:
    height_string = commonplayerinfo.CommonPlayerInfo(player_id=player_id).common_player_info.data['data'][0][10].split('-')
    player_heights.append(int(height_string[0]) * 12 + int(height_string[1])) # convert height to inches
    player_weights.append(commonplayerinfo.CommonPlayerInfo(player_id=player_id).common_player_info.data['data'][0][11])
df['height'] = player_heights
df['weight'] = player_weights

#fill dicts with stats, rather than searching each dataset for each different player. This will speed it up a lot
# {<player_id> : stat}
# data is ordered by player ids
player_fgas = OrderedDict({
    entry[0]:entry[7]
    for entry in stats_leagueleaders.league_leaders.data['data']
    })

player_drives = OrderedDict({
    entry[0] : entry[10]
    for entry in stats_drives.league_dash_pt_stats.data['data']
    })
df['drives per attempt'] = [data / player_fgas[player_id] for player_id, data in player_drives]

player_catch_shoot = OrderedDict({
    entry[0] : entry[9]
    for entry in stats_catchshoot.league_dash_pt_stats.data['data']
    })
df['catch-and-shoots per attempt'] = [data / player_fgas[player_id] for player_id, data in player_catch_shoot]

player_pull_up = OrderedDict({
    entry[0] : entry[9]
    for entry in stats_pullup.league_dash_pt_stats.data['data']
    })
df['pull-ups per attempt'] = [data / player_fgas[player_id] for player_id, data in player_pull_up]

player_post_up = OrderedDict({
    entry[0] : entry[11]
    for entry in stats_postup.league_dash_pt_stats.data['data']
    })
df['post-ups per attempt'] = [data / player_fgas[player_id] for player_id, data in player_post_up]

player_passes_per_min = OrderedDict({
    entry[0] : entry[8]/entry[7]
    for entry in stats_passing.league_dash_pt_stats.data['data']
    })
df['passes made per minute'] = [data for data in player_passes_per_min]

player_dribbles_per_touch = OrderedDict({
    entry[0] : entry[13]
    for entry in stats_possession.league_dash_pt_stats.data['data']
    })
df['dribbles per touch'] = [data for data in player_dribbles_per_touch]

player_avg_speed_off = OrderedDict({
    entry[0] : entry[13]
    for entry in stats_distance.league_dash_pt_stats.data['data']
    })
df['avg speed off'] = [data for data in player_avg_speed_off]

player_avg_speed_def = OrderedDict({
    entry[0] : entry[14]
    for entry in stats_distance.league_dash_pt_stats.data['data']
    })
df['avg speed def'] = [data for data in player_avg_speed_def]

player_oreb_chance_per_min = OrderedDict({
    entry[0] : entry[12]/entry[7]
    for entry in stats_rebounding.league_dash_pt_stats.data['data']
    })
df['oreb chance per min'] = [data for data in player_oreb_chance_per_min]

player_dreb_chance_per_min = OrderedDict({
    entry[0] : entry[21]/entry[7]
    for entry in stats_rebounding.league_dash_pt_stats.data['data']
    })
df['dreb chance per min'] = [data for data in player_dreb_chance_per_min]


kmeans(df, 3)