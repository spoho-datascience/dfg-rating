import os
import pandas as pd
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.international_network import CountryLeague, InternationalCompetition_Combine
from dfg_rating.model.rating.multi_mode_rating import ControlledRandomFunction, ControlledTrendRating
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast

import dfg_rating.viz.jupyter_widgets as Widgets


def setup_network(nr_teams, teams_level1, teams_level2, teams_level3, country_id, rat_level1, rat_level2, rat_level3,
                  min_match_1_2, avg_match_1_2, min_match_2_3, avg_match_2_3, min_match_3_1, avg_match_3_1, rat_mode):
    test_network = CountryLeague(
        teams=nr_teams,
        level1_teams=teams_level1,
        level2_teams=teams_level2,
        level3_teams=teams_level3,
        promotion_number=2,
        # prob_level1_level2=0.10,
        # prob_level1_level3=0.05,
        # prob_level2_level3=0.00,
        true_rating_level1=rat_level1,
        true_rating_level2=rat_level2,
        true_rating_level3=rat_level3,
        true_forecast=forecast_test,
        seasons=seasons,
        # days_between_rounds=3,
        country_id=country_id,
        rating_mode=rat_mode,
        min_match_per_team_level1_level2=min_match_1_2,
        avg_match_per_team_level1_level2=avg_match_1_2,
        min_match_per_team_level2_level3=min_match_2_3,
        avg_match_per_team_level2_level3=avg_match_2_3,
        min_match_per_team_level3_level1=min_match_3_1,
        avg_match_per_team_level3_level1=avg_match_3_1,
    )
    return test_network


seasons = 5
no_countries = 3
# set number of teams per 1st league that play internationally and avg and min of matches per team
teams_per_country_international = 6
avg_match_international = 6
min_match_international = 3
# names of the countries
countries = ('c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'c10')
# set number of teams for whole country (1st to 4th league) and for first three leagues separately
nr_teams_total = (72, 72, 72, 72, 72, 72, 72, 72, 72, 72)
nr_teams_level1 = (18, 18, 18, 18, 18, 18, 18, 18, 18, 18)
nr_teams_level2 = (18, 18, 18, 18, 18, 18, 18, 18, 18, 18)
nr_teams_level3 = (18, 18, 18, 18, 18, 18, 18, 18, 18, 18)
# set the starting mean rating for each level of each country and the deviation for all teams for that rating
ratings_level1 = (1300, 1250, 1200, 1200, 1200, 1150, 1100, 1100, 1100, 1050)
ratings_level2 = (1050, 1050, 950, 950, 1000, 900, 900, 950, 900, 850)
ratings_level3 = (900, 950, 800, 850, 850, 800, 750, 750, 700, 700)
rating_scale_level1 = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
rating_scale_level2 = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
rating_scale_level3 = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
# set rating transfer for promotion and relegation (keep = teams keep their ranking when promoted/relegated,
# mix= teams get difference of league rating means added (promotion) or subtracted (relegation),
# interchange =
rating_mode = ('mix', 'mix', 'mix', 'mix', 'mix', 'mix', 'mix',
               'mix', 'mix', 'mix')
# min and avg number of matches per team between each league
min_match_level1_level2 = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
avg_match_level1_level2 = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
min_match_level2_level3 = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
avg_match_level2_level3 = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
min_match_level3_level1 = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
avg_match_level3_level1 = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1)

df_networks = pd.DataFrame()
network = {}

rating_level1 = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=1200, scale=0),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    rating_name='true_rating'
)

rating_level2 = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=0),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    rating_name='true_rating'
)

rating_level3 = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=800, scale=0),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    rating_name='true_rating'
)

forecast_test = LogFunctionForecast(
    outcomes=['home', 'draw', 'away'],
    coefficients=[-0.9, 0.3],
    beta_parameter=0.006
)

for i in range(0, no_countries):
    rating_level1.starting_point.distribution_arguments['loc'] = ratings_level1[i]
    rating_level2.starting_point.distribution_arguments['loc'] = ratings_level2[i]
    rating_level3.starting_point.distribution_arguments['loc'] = ratings_level3[i]
    rating_level1.starting_point.distribution_arguments['scale'] = rating_scale_level1[i]
    rating_level2.starting_point.distribution_arguments['scale'] = rating_scale_level2[i]
    rating_level3.starting_point.distribution_arguments['scale'] = rating_scale_level3[i]
    network[i] = setup_network(nr_teams_total[i], nr_teams_level1[i], nr_teams_level2[i], nr_teams_level3[i],
                               countries[i], rating_level1, rating_level2, rating_level3, min_match_level1_level2[i],
                               avg_match_level1_level2[i], min_match_level2_level3[i], avg_match_level2_level3[i],
                               min_match_level3_level1[i], avg_match_level3_level1[i], rating_mode[i])

international_network = InternationalCompetition_Combine(
    countries_configs={countries[i]: network[i] for i in range(0, no_countries)},
    teams_per_country=teams_per_country_international,
    seasons=seasons,
    create_country_network=False,
    avg_match_per_team=avg_match_international,
    min_match_per_team=min_match_international,
)

international_network.export(printing_ratings=['true_rating', 'ranking'], file_name='full_network_5.csv')

app = Widgets.RatingsExplorer(network=international_network)
app.run('external', port=8001)
