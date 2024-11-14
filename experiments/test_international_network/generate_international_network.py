from dfg_rating.model.network.international_network import CountryLeague, InternationalCompetition_Combine
from dfg_rating.model.rating.multi_mode_rating import ControlledRandomFunction, ControlledTrendRating
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
import dfg_rating.viz.jupyter_widgets as DFGWidgets

rating_level1 = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=800, scale=100),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
    rating_name='true_rating'
)

rating_level2 = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=500, scale=50),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
    rating_name='true_rating'
)

rating_level3 = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=200, scale=10),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
    rating_name='true_rating'
)

forecast_test = LogFunctionForecast(
    outcomes=['home', 'draw', 'away'],
    coefficients=[-0.9, 0.3],
    beta_parameter=0.006
)

country_network1 = CountryLeague(
    teams=16,
    level1_teams=6,
    level2_teams=4,
    level3_teams=4,
    promotion_number=1,
    # prob_level1_level2=0.10,
    # prob_level1_level3=0.05,
    # prob_level2_level3=0.00,
    true_rating_level1=rating_level1,
    true_rating_level2=rating_level2,
    true_rating_level3=rating_level3,
    true_forecast=forecast_test,
    seasons=3,
    # days_between_rounds=7,
    country_id='c1',
    rating_mode='interchange',
    min_match_per_team_level1_level2=1,
    avg_match_per_team_level1_level2=4,
    min_match_per_team_level2_level3=1,
    avg_match_per_team_level2_level3=2,
    min_match_per_team_level3_level1=1,
    avg_match_per_team_level3_level1=3,
)


# test_network1.export(printing_ratings=['true_rating','ranking'],file_name='test_NationalLeague_network.csv')


country_network2 = CountryLeague(
    teams=14,
    level1_teams=4,
    level2_teams=4,
    level3_teams=4,
    promotion_number=1,
    # prob_level1_level2=0.10,
    # prob_level1_level3=0.05,
    # prob_level2_level3=0.00,
    true_rating_level1=rating_level1,
    true_rating_level2=rating_level2,
    true_rating_level3=rating_level3,
    true_forecast=forecast_test,
    seasons=3,
    # days_between_rounds=7,
    country_id='c2',
    rating_mode='interchange',
    min_match_per_team_level1_level2=1,
    avg_match_per_team_level1_level2=4,
    min_match_per_team_level2_level3=1,
    avg_match_per_team_level2_level3=2,
    min_match_per_team_level3_level1=1,
    avg_match_per_team_level3_level1=3,
)
'''
countries_config = {
    0:{
        'teams':30,
        'level1_teams': 10,
        'level2_teams': 10,
        'level3_teams': 8,
        'promotion_number': 2,
        'prob_level1_level2': 0.05,
        'prob_level1_level3': 0.05,
        'prob_level2_level3': 0.05,
        'rating_mode': 'keep',
        'days_between_rounds': 7,
        'true_rating_level1':rating_level1,
        'true_rating_level2':rating_level2,
        'true_rating_level3':rating_level3,
    },
    1:{
        'teams':8,
        'level1_teams': 2,
        'level2_teams': 2,
        'level3_teams': 2,
        'promotion_number': 1,
        'prob_level1_level2': 0.00,
        'prob_level1_level3': 0.00,
        'prob_level2_level3': 0.00,
        'rating_mode': 'mix',
        'days_between_rounds': 6
    }
}
'''
Inter_network = InternationalCompetition_Combine(
    countries_configs={'c1':country_network1, 'c2':country_network2},
    teams_per_country=2,
    # match_prob=0.0,
    seasons=3,
    # days_between_rounds=7,
    choose_mode='top',
    create_country_network=False,
    avg_match_per_team=3,
    min_match_per_team=1,
    oneleg=False,
)

from dfg_rating.model.rating.multi_mode_rating import ELORating
elo_rating1 = ELORating(
    rating_name='elo_rating',
    trained=True,
    rating_mode='keep',
    rating_mean=1000,
)
Inter_network.add_rating(elo_rating1, 'elo_rating')
Inter_network.export(printing_ratings=['true_rating','ranking','elo_rating'],file_name='test_InternationalLeague_network.csv')

country_network1.export(printing_ratings=['true_rating','ranking','elo_rating'],file_name='test_NationalLeague_network.csv')
'''
file_name='test_InternationalLeague_network.csv')
# # display network explorer
app = DFGWidgets.NetworkExplorer(
    network=test_network,
    edge_props=["round"]
)
app.run('internal', debug=True, port=8001)
'''