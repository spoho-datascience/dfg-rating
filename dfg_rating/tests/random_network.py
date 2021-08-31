import os
import pandas as pd
import numpy as np
import random
import dash_cytoscape as cyto

from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.base_network import WhiteNetwork, BaseNetwork
from dfg_rating.model.network.multiple_network import LeagueNetwork

import dfg_rating.viz.jupyter_widgets as DFGWidgets
from dfg_rating.model.network.random_network import RandomNetwork, ConfigurationModelNetwork, ClusteredNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating

import configuration_model_mcmc as CM

from dfg_rating.viz.tables import get_evaluation

random.seed(321)
np.random.seed(1234)

n = 48
d = 10
v = 40

random_network = ClusteredNetwork(
    teams=n,
    days_between_rounds=3,
    true_rating=ControlledTrendRating(
        starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
        delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
        trend=ControlledRandomFunction(distribution='normal', loc=0, scale=20 / 365),
        season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
    ),
    clusters=4,
    out_probability=0.3
)

print("random network created")

cyto.load_extra_layouts()
ratings_app = DFGWidgets.NetworkExplorer(network=random_network, offline=True)
print("running app")
ratings_app.run('external', debug=True, port=8001)
