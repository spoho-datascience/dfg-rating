import time
import networkx as nx

from typing import List
import dfg_rating.viz.jupyter_widgets as DFGWidgets
from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.network.random_network import ConfigurationModelNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating


from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast

from dfg_rating.viz.tables import get_evaluation

import pandas as pd
import os
import datetime

in_degree = 180
out_degree = 180
initial_number_of_nodes = 60
maximum_number_of_nodes = 260
nodes_step = 5

minimum_k = 15
maximum_k = 65
k_options = [v for v in range(minimum_k, maximum_k + 1, 2)]
experiment_results = []
nodes_range = range(initial_number_of_nodes, maximum_number_of_nodes + 1, nodes_step)
for step, number_of_nodes in enumerate(nodes_range):
    start_time = time.time()
    current_network = ConfigurationModelNetwork(
        teams=number_of_nodes,
        days_between_rounds=3,
        true_forecast=LogFunctionForecast(
            outcomes=['home', 'draw', 'away'],
            coefficients=[-0.9, 0.3],
            beta_parameter=0.006
        ),
        true_rating=ControlledTrendRating(
            starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
            delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
            trend=ControlledRandomFunction(distribution='normal', loc=0, scale=20/365),
            season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
        ),
        expected_home_matches=in_degree - (step * 4),
        expected_away_matches=in_degree - (step * 4),
        variance_home_matches=0,
        variance_away_matches=0
    )
    print(in_degree - (step * 2))
    print(current_network.density(True))
    print(f"Added network with {number_of_nodes} number of nodes in {time.time() -  start_time} seconds.")

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
        current_network.add_evaluation(rps, f"{rating_name}_RPS")

        print(f"Added ELO Rating with k = {k_parameter} in {time.time() - start_time} seconds.")
        experiment_results += get_evaluation(
            current_network, k_parameter, evaluators=['RPS'],
            **{"Number_of_nodes": number_of_nodes, "Density": current_network.density(True)}
        )

print("Experiments gathered")

experiment_df = pd.DataFrame(experiment_results)
today = datetime.datetime.today().strftime("%A, %d. %B %Y %I:%M%p")
experiment_df.to_csv(os.path.join("Density_results", f"{today}.csv"))

print("Test finished")
