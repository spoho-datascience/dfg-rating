from dfg_rarting.model.network.international_network import CountryLeague, InternationalCompetition

import dfg_rating.viz.jupyter_widgets as DFGWidgets
test_network = CountryLeague(
    teams=10,
    level1_teams=4,
    level2_teams=4,
    level3_teams=2,
    prob_within_level1=1.0,
    prob_within_level2=1.0,
    prob_within_level3=1.0,
    prob_level1_level2=0.1,
    prob_level1_level3=0.05,
    prob_level2_level3=0.1,
    oneleg=True,
    # true_forecast=LogFunctionForecast(
    #     outcomes=['home', 'draw', 'away'],
    #     coefficients=[-0.9, 0.3],
    #     beta_parameter=0.006
    # ),
    # true_rating=ControlledTrendRating(
    #     starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
    #     delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.1),
    #     trend=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    #     season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0)
    # ),
    # team_labels={1: 1, 3: 3, 5: 5, 7: 7, 9: 9, 11: 11, 13: 13, 15: 15, 17: 17, 19: 19},
)
# countries_config = {
#     0:{
#         'teams': 10,
#         'level1_teams': 4,
#         'level2_teams': 4,
#         'level3_teams': 2,
#         'prob_within_level1': 1.0,
#         'prob_within_level2': 1.0,
#         'prob_within_level3': 1.0,
#         'prob_level1_level2': 0.00,
#         'prob_level1_level3': 0.00,
#         'prob_level2_level3': 0.00,
#         'oneleg': True
#     },
#     1:{
#         'teams': 6,
#         'level1_teams': 3,
#         'level2_teams': 3,
#         'level3_teams': 0,
#         'prob_within_level1': 1.0,
#         'prob_within_level2': 1.0,
#         'prob_within_level3': 1.0,
#         'prob_level1_level2': 0.00,
#         'prob_level1_level3': 0.00,
#         'prob_level2_level3': 0.00,
#         'oneleg': True
#     }
# }

# test_network = InternationalCompetition(
#     countries_configs=countries_config,
#     teams_per_country=3,
#     match_prob=0.5
# )
# Display the network to verify the structure
app = DFGWidgets.NetworkExplorer(
    network=test_network,
    edge_props=["round"]
)
app.run('internal', debug=True, port=8001)