import os
import pandas as pd
import numpy as np
import random

from dfg_rating.model.evaluators.accuracy import RankProbabilityScore
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.network.multiple_network import LeagueNetwork

import dfg_rating.viz.jupyter_widgets as DFGWidgets
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating

random.seed(123)
np.random.seed(1234)

rr_network = LeagueNetwork(
    teams=18,
    seasons=10,
    league_teams=18,
    league_promotion=0,
    days_between_rounds=3,
    create=True,
    true_rating=ControlledTrendRating(
        starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
        delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
        trend=ControlledRandomFunction(distribution='normal', loc=0, scale=20/365),
        season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
    )
)

elo = ELORating(trained=True)
rr_network.add_rating(rating=elo, rating_name='elo_rating')

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
rr_network.add_evaluation([(rps, 'elo_rating')])

"""
df = pd.read_csv('/home/marc/Development/dshs/dfg-rating/data/real/ATP_Network_2010_2019.csv')

# %%
white_network = WhiteNetwork(
    data=df,
    mapping={
        "node1": {
            "id": "WinnerID",
            "name": "Winner",
            "ratings": {
                "rank": "WRank",
                "Pts": "WPts"
            }
        },
        "node2": {
            "id": "LoserID",
            "name": "Loser",
            "ratings": {
                "rank": "LRank",
                "Pts": "LPts"
            }
        },
        "day": "Date",
        "dayIsTimestamp": True,
        "round": "Round",
        "season": "Year",
        "forecasts": {},
        "odds": {
            "b365": {
                "node1": "B365W",
                "node2": "B365L"
            }
        },
        "bets": {}
    }
)
"""
ratings_app = DFGWidgets.RatingsExplorer(network=rr_network)
ratings_app.run('external', debug=True)
