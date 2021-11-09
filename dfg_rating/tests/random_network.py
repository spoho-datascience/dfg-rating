import math
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
from dfg_rating.model.network.random_network import RandomNetwork, RandomRoundsNetwork, ConfigurationModelNetwork, ClusteredNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating

import configuration_model_mcmc as CM

from dfg_rating.viz.tables import get_evaluation

"""random.seed(321)
np.random.seed(1234)"""

#n = 12
r = 98
d = 0.98
n = int(math.ceil((r / (2 * d)) + 1))
if (n%2) != 0:
    n += 1

initial_density = 98
maximum_density = 98
density_step = 2
rounds = 98

minimum_k = 15
maximum_k = 65
k_options = [v for v in range(minimum_k, maximum_k + 1, 2)]
experiment_results = []
density_range = range(initial_density, maximum_density + 1, density_step)
for step, current_density in enumerate(density_range):
    d = float(current_density / 100.00)
    number_of_nodes = int(
        math.ceil(
            (rounds / (2 * d)) + 1
        )
    )
    print(f"{number_of_nodes} teams, network with {d}")

random_network = ClusteredNetwork(
    teams=10,
    days_between_rounds=3,
    clusters=5,
    in_probability=1.0,
    out_probability=0.0
)
random_network.add_rating(ELORating(trained=True), "elo_rating")
print("random network created")

cyto.load_extra_layouts()
ratings_app = DFGWidgets.NetworkExplorer(network=random_network, offline=True)
print("running app")
ratings_app.run('external', debug=True, port=8001)
