import os
import pandas as pd
import numpy as np
import random
import dash_cytoscape as cyto

from dfg_rating.model.evaluators.accuracy import RankProbabilityScore
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.network.multiple_network import LeagueNetwork

import dfg_rating.viz.jupyter_widgets as DFGWidgets
from dfg_rating.model.network.random_network import RandomNetwork, ConfigurationModelNetwork, ClusteredNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating

random.seed(321)
np.random.seed(1234)

n = 20

"""random_network = RandomNetwork(
    teams=n,
    days_between_rounds=3,
    true_rating=ControlledTrendRating(
        starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
        delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
        trend=ControlledRandomFunction(distribution='normal', loc=0, scale=20/365),
        season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
    ),
    edge_probability=1
)"""

"""random_network = ConfigurationModelNetwork(
    teams=n,
    days_between_rounds=3,
    true_rating=ControlledTrendRating(
        starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
        delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
        trend=ControlledRandomFunction(distribution='normal', loc=0, scale=20/365),
        season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
    ),
    expected_home_matches=5,
    expected_away_matches=5,
    variance_home_matches=5,
    variance_away_matches=5
)"""

random_network = ClusteredNetwork(
    teams=n,
    days_between_rounds=3,
    true_rating=ControlledTrendRating(
        starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
        delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
        trend=ControlledRandomFunction(distribution='normal', loc=0, scale=20/365),
        season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
    ),
    clusters=4,
    out_probability=0.05
)

print("random network created")

elo = ELORating(trained=True)
random_network.add_rating(rating=elo, rating_name='elo_rating')
"""
rr_network.add_forecast(
    LogFunctionForecast(
        outcomes=['home', 'draw', 'away'],
        coefficients=[-0.9, 0.3],
        beta_parameter=0.006
    ),
    "elo_forecast",
    "elo_rating"
)

rps = RankProbabilityScore(
    outcomes=['home', 'draw', 'away'],
    forecast_name='elo_forecast'
)
rr_network.add_evaluation(rps, 'elo_rating')"""

cyto.load_extra_layouts()
ratings_app = DFGWidgets.NetworkExplorer(network=random_network, offline=True)
print("running app")
ratings_app.run('external', debug=True, port=8001)
