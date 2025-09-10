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
d = 0.1
n = int(math.ceil((r / (2 * d)) + 1))
d_between = math.floor(36000000 / ((n - 1) * 2))

print(f"New network {n}:{d_between}")
random_network = RandomRoundsNetwork(
    teams=n,
    days_between_rounds=d_between,
    absolute_rounds=r
)

#print([m for m in random_network.iterate_over_games()])

rounds_data = [(m[2]['round'], m[2]['day']) for m in random_network.data.edges(data=True)]
active_rounds_data = [(m[2]['round'], m[2]['day']) for m in random_network.data.edges(data=True) if m[2].get('state') == 'active']
inactive_rounds_data = [(m[2]['round'], m[2]['day']) for m in random_network.data.edges(data=True) if m[2].get('state') != 'active']

if len(active_rounds_data) > 0:
    print(f"Active edges ({len(active_rounds_data)}) info:")
    print(f"Min day {min([t[1] for t in active_rounds_data])} - Max day {max([t[1] for t in active_rounds_data])}")
    print(f"Min round {min([t[0] for t in active_rounds_data])} - Max Round {max([t[0] for t in active_rounds_data])}")

if len(inactive_rounds_data) > 0:
    print(f"Inactive edges ({len(inactive_rounds_data)}) info:")
    print(f"Min day {min([t[1] for t in inactive_rounds_data])} - Max day {max([t[1] for t in inactive_rounds_data])}")
    print(f"Min round {min([t[0] for t in inactive_rounds_data])} - Max Round {max([t[0] for t in inactive_rounds_data])}")
print(f"All edges ({len(rounds_data)} info:")
print(f"Min day {min([t[1] for t in rounds_data])} - Max day {max([t[1] for t in rounds_data])}")
print(f"Min round {min([t[0] for t in rounds_data])} - Max Round {max([t[0] for t in rounds_data])}")

"""cyto.load_extra_layouts()
ratings_app = DFGWidgets.NetworkExplorer(network=random_network, offline=True)
print("running app")
ratings_app.run('external', debug=True, port=8001)"""
