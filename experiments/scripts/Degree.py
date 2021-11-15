import time
import networkx as nx
import numpy as np

from typing import List
import dfg_rating.viz.jupyter_widgets as DFGWidgets
from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.network.random_network import ConfigurationModelNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating


from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast

import pandas as pd
import os
import datetime

from dfg_rating.viz.tables import get_evaluation

in_degree = 120
out_degree = 120
initial_variance = 0
maximum_variance = 240
variance_step = 6

minimum_k = 15
maximum_k = 65
k_options = [v for v in range(minimum_k, maximum_k + 1, 2)]
experiment_results = []
networks_list: List[BaseNetwork] = []
variance_range = range(initial_variance, maximum_variance + 1, variance_step)
n = 300
d_between = 36000000 / (n * (n - 1) * 2)
for variance in variance_range:
    start_time = time.time()
    current_network = ConfigurationModelNetwork(
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
                season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0)
            ),
            expected_home_matches=in_degree,
            expected_away_matches=out_degree,
            variance_home_matches=variance,
            variance_away_matches=variance
        )
    print(f"Added network with Degree variance of {variance} in {time.time() -  start_time} seconds.")
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
            **{"Variance": variance, "Density": current_network.density(True)}
        )

print("Saving results")

today = datetime.datetime.today().strftime("%A, %d. %B %Y %I:%M%p")
pd.DataFrame(experiment_results).to_csv(os.path.join("Degree_results", f"{today}.csv"))

print("Test finished")
