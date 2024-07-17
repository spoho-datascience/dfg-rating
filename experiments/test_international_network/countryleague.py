from dfg_rating.model.network.international_network import CountryLeague, InternationalCompetition
from dfg_rating.model.rating.controlled_trend_rating import ControlledRandomFunction, ControlledTrendRating
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
    starting_point=ControlledRandomFunction(distribution='normal', loc=500, scale=100),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
    rating_name='true_rating'
)

rating_level3 = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=200, scale=100),
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

test_network = CountryLeague(
    # teams=10,
    level1_teams=4,
    level2_teams=4,
    level3_teams=4,
    promotion_number=1,
    prob_within_level1=1.0,
    prob_within_level2=1.0,
    prob_within_level3=1.0,
    prob_level1_level2=0.05,
    prob_level1_level3=0.05,
    prob_level2_level3=0.05,
    oneleg=False,
    true_rating_level1=rating_level1,
    true_rating_level2=rating_level2,
    true_rating_level3=rating_level3,
    true_forecast=forecast_test,
    seasons=5,
    # team_labels={1: 1, 3: 3, 5: 5, 7: 7, 9: 9, 11: 11, 13: 13, 15: 15, 17: 17, 19: 19},
)


countries_config = {
    0:{
        'teams': 10,
        'level1_teams': 4,
        'level2_teams': 4,
        'level3_teams': 2,
        'prob_within_level1': 1.0,
        'prob_within_level2': 1.0,
        'prob_within_level3': 1.0,
        'prob_level1_level2': 0.00,
        'prob_level1_level3': 0.00,
        'prob_level2_level3': 0.00,
        'oneleg': True
    },
    1:{
        'teams': 6,
        'level1_teams': 3,
        'level2_teams': 3,
        'level3_teams': 0,
        'prob_within_level1': 1.0,
        'prob_within_level2': 1.0,
        'prob_within_level3': 1.0,
        'prob_level1_level2': 0.00,
        'prob_level1_level3': 0.00,
        'prob_level2_level3': 0.00,
        'oneleg': True
    }
}

# test_network = InternationalCompetition(
#     countries_configs=countries_config,
#     teams_per_country=3,
#     match_prob=0.5
# )

# display network explorer
app = DFGWidgets.NetworkExplorer(
    network=test_network,
    edge_props=["round"]
)
app.run('internal', debug=True, port=8001)