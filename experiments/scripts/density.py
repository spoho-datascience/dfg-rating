import math
import time
import networkx as nx

from typing import List
import dfg_rating.viz.jupyter_widgets as DFGWidgets
from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.network.random_network import ConfigurationModelNetwork, RandomRoundsNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating

from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood, ForecastError, \
    ExpectedRankProbabilityScore
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast

from dfg_rating.viz.tables import get_evaluation, get_evaluation_list

import pandas as pd
import os
import datetime


maximum_density = 100
density_step = -2
rounds = 98

minimum_k = 15
maximum_k = 25
k_options = [v for v in range(minimum_k, maximum_k + 1, 2)]
experiment_results = []
density_range = range(maximum_density, 98, density_step)
for step, current_density in enumerate(density_range):
    d = float(current_density / 100.00)
    start_time = time.time()
    number_of_nodes = int(
        math.ceil(
            (rounds / (2 * d)) + 1
        )
    )
    d_between = math.floor(36000000 / ((number_of_nodes - 1) * 2))
    print(d_between)
    print(f"Network {number_of_nodes}:{d}")
    current_network = RandomRoundsNetwork(
        teams=number_of_nodes,
        days_between_rounds=d_between,
        absolute_rounds=rounds,
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
        )
    )
    print("Density ", current_network.density(True))
    print(f"Added network {number_of_nodes}:{d} in {time.time() - start_time} seconds.")

    for k_parameter in k_options:
        start_time = time.time()
        rating_name = f"elo_rating_{k_parameter}"
        forecast_name = f"elo_forecast_{k_parameter}"
        elo = ELORating(trained=True, param_k=k_parameter)
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
        current_network.add_evaluation(
            get_evaluation_list(rating_name, forecast_name)
        )
        print(f"Added ELO Rating with k = {k_parameter} in {time.time() - start_time} seconds.")
        experiment_results += get_evaluation(
            current_network, k_parameter,
            evaluators=['RPS', 'Likelihood', 'ForecastError', 'ExpectedRPS', 'Forecastability'],
            **{"Number_of_nodes": number_of_nodes, "Density": current_network.density(True)}
        )

print("Experiments gathered")

experiment_df = pd.DataFrame(experiment_results)
today = datetime.datetime.today().strftime("%A, %d. %B %Y %I:%M%p")
experiment_df.to_csv(os.path.join("Density_results", f"{today}.csv"))

print("Test finished")
