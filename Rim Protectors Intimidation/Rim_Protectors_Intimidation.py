from nba_api.stats.endpoints import teamvsplayer, leaguedashplayerstats, commonplayerinfo
from nba_api.stats.static import teams, players
import pandas

# mpg threshold to include players from above
MINUTES_THRESHOLD = 25

def get_ra_fga_percentchange():
    centers = leaguedashplayerstats.LeagueDashPlayerStats(player_position_abbreviation_nullable="C")
    teams = teams.get_teams()

    # really just centers who play more than an mpg limit
    # mpg is calculated here as min / gp
    starting_centers = [center for center in centers.data_sets[0].data['data']
             if center[9] / center[5] > MINUTES_THRESHOLD]

    result = {}

    # iterate through every combination of starting center and opposing team
    for center in starting_centers:
        percent_change_sum = 0

        for team in teams:
            # ignore matchup if center is facing own team (sanity check)
            if not team['id'] is center[2]:

                matchup_stats = teamvsplayer.TeamVsPlayer(center[0], team['id'])

                #check if there were games played / is data
                if len(matchup_stats.shot_area_on_court.data['data']) == 0:
                    continue

                games_played = matchup_stats.overall.data['data'][0][4]
                games_played_matchup = matchup_stats.on_off_court.data['data'][0][7]

                fga = matchup_stats.overall.data['data'][0][10] / games_played
                fga_oncourt = matchup_stats.on_off_court.data['data'][0][13] / games_played_matchup
                ra_fga = matchup_stats.shot_area_overall.data['data'][0][6] / games_played
                ra_fga_oncourt = matchup_stats.shot_area_on_court.data['data'][0][9] / games_played_matchup

                # percent change of porportion of field goals attempted in
                # restricted area with center on the court
                percent_change = ((ra_fga_oncourt / fga_oncourt) - (ra_fga / fga)) / (ra_fga / fga)
                percent_change_sum += percent_change

        average_rim_intimidation = percent_change_sum / len(teams)
        result[center[1]] = average_rim_intimidation

    return result

#result = get_ra_fga_percentchange()
#result_sorted = sorted((value, key) for (key,value) in result.items())
# results from previous run
result_sorted = ((-0.2440371047101562, 'Brook Lopez'),
(-0.12795969997011533, 'Bam Adebayo'),
(-0.11638238040994511, 'Nikola Vucevic'),
(-0.11212607415968386, 'Jonas Valanciunas'),
(-0.1118494876446006, 'Rudy Gobert'),
(-0.10657561160731932, 'Marc Gasol'),
(-0.08982435602093239, 'Joel Embiid'),
(-0.07709758507584899, 'Jarrett Allen'),
(-0.06598735575908186, 'Steven Adams'),
(-0.05186616461167437, 'LaMarcus Aldridge'),
(-0.04275859261525937, 'Kristaps Porzingis'),
(-0.02740154847483295, 'Montrezl Harrell'),
(-0.023806392044860392, 'Jaren Jackson Jr.'),
(-0.021782565281510544, 'Zach Collins'),
(-0.021682906142816476, 'Domantas Sabonis'),
(-0.01995751930381053, 'Julius Randle'),
(0.008157479789599376, 'Andre Drummond'),
(0.008709344911596377, 'Myles Turner'),
(0.010075681445731755, 'Dwight Powell'),
(0.020201083947722843, 'Karl-Anthony Towns'),
(0.02160176060319431, 'Nikola Jokic'),
(0.024782518470126864, 'Hassan Whiteside'),
(0.03196052389301537, 'Al Horford'),
(0.03841157991908462, 'Larry Nance Jr.'),
(0.04206678015801269, 'Anthony Davis'),
(0.0701154735747214, 'Clint Capela'),
(0.07577797280144634, 'Deandre Ayton'),
(0.08857105546886211, 'Wendell Carter Jr.'),
(0.11515071396136453, 'Kevin Love'),
(0.11859779245522946, 'Tristan Thompson'),
(0.16102045750214924, 'Lauri Markkanen'))

# format data for dataframe
df = pandas.DataFrame(result_sorted)
df.columns = ["Percent Change in Opp. RA FGA", "Player"]
cols = df.columns.tolist()
cols = cols[::-1]
df = df[cols]
print(df)

# format data for html table
print("<table><tr><td>Player</td><td>Percent Change in <br />Opp. RA FGA</td></tr>")
for entry in result_sorted:
    print("\n<tr><td>" + entry[1] + "</td><td>" + str(entry[0]) + "</td></tr>")
print("\n</table>")

# correlation with height
# api calls
results_with_height = []
for entry in result_sorted:
    playerid = players.find_players_by_full_name(entry[1])[0]['id']
    height = commonplayerinfo.CommonPlayerInfo(player_id=playerid).common_player_info.data['data'][0][10]
    height_inches = height.split("-")[0] * 12 + height.split("-")[1] #convert to inches
    results_with_height.append((entry[1], entry[0], height_inches))

#correlation
df = pandas.DataFrame(results_with_height)
df.corr()
print(df.corr())