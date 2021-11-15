import time
import networkx as nx
import numpy as np

from typing import List
import dfg_rating.viz.jupyter_widgets as DFGWidgets
from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.network.random_network import ClusteredNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating

import pandas as pd
import os
import datetime

from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast

from dfg_rating.viz.tables import get_evaluation

number_of_clusters = 10
in_probability = 100
initial_out_probability = 0

minimum_k = 15
maximum_k = 65
k_options = [v for v in range(minimum_k, maximum_k + 1, 2)]

experiment_results = []
probs_range = [float(p / 100) for p in range(initial_out_probability, 101, 2)]
n = 300
d_between = 36000000 / (n * (n - 1) * 2)
for prob in probs_range:
    start_time = time.time()
    current_network = ClusteredNetwork(
        teams=n,
        days_between_rounds=d_between,
        true_forecast=LogFunctionForecast(
            outcomes=['home', 'draw', 'away'],
            coefficients=[-0.9, 0.3],
            beta_parameter=0.006
        ),
        true_rating=ControlledTrendRating(
            starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
            delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.1),
            trend=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
            season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
        ),
        clusters=number_of_clusters,
        in_probability=float(in_probability / 100),
        out_probability=prob
    )
    print(f"Added network with {number_of_clusters} clusters, intra-cluster probability of {float(in_probability / 100)} and inter-cluster probability of {prob} in {time.time() -  start_time} seconds.")
    for k_parameter in k_options:
        start_time = time.time()
        rating_name = f"elo_rating_{k_parameter}"
        forecast_name = f"elo_forecast_{k_parameter}"
        elo = ELORating(trained=True, param_k=k_parameter)
        rps = RankProbabilityScore(
            outcomes=['home', 'draw', 'away'],
            forecast_name=forecast_name
        )
        l = Likelihood(
            outcomes=['home', 'draw', 'away'],
            forecast_name=forecast_name
        )
        current_network.add_rating(
            rating=elo,
            rating_name=rating_name
        )
        current_network.add_forecast(
            LogFunctionForecast(
                outcomes=['home', 'draw', 'away'],
                coefficients=[-0.9, 0.3],
                beta_parameter=0.006
            ),
            forecast_name,
            rating_name
        )
        current_network.add_evaluation([(rps, f"{rating_name}_RPS")])
        print(f"Added ELO Rating with k = {k_parameter} in {time.time() - start_time} seconds.")

        experiment_results += get_evaluation(
            current_network, k_parameter, evaluators=['RPS'],
            **{"Clusters": number_of_clusters, "InProbability": float(in_probability/100), "OutProbability": prob}
        )

del current_network

print("Saving results")

today = datetime.datetime.today().strftime("%A, %d. %B %Y %I:%M%p")
pd.DataFrame(experiment_results).to_csv(os.path.join("Cluster_results", f"{today}.csv"))

print("Test finished")
