# %% [markdown]
# # Real example using components and different K factors

# %% [markdown]
# ## Import statements

# %%
import os
import numpy as np
import pandas as pd

import dfg_rating.viz.jupyter_widgets as DFGWidgets
import dfg_rating.viz.tables as DFGTables
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.rating.elo_rating import ELORating
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood

# %% [markdown]
# ## Loading real data file

# %%
real_data = pd.read_csv(os.path.join('experiments/notebooks/network_analysis/RealData/real_data.csv'), sep=",")
real_data

# %%
real_data["result"] = np.where(
    (real_data["team1_score"] > real_data["team2_score"]),
    "home",
    "draw"
)
real_data["result"] = np.where(
    (real_data["team1_score"] < real_data["team2_score"]),
    "away",
    real_data["result"]
)
real_data[["team1_score", "team2_score", "result"]]

# %%
real_data_network = WhiteNetwork(
    data=real_data,
    mapping={
        "node1": {
            "id": "team1_id",
            "name": "team1_name",
        },
        "node2": {
            "id": "team2_id",
            "name": "team2_name",
        },
        "day": "match_date",
        "dayIsTimestamp": True,
        "ts_format": "%Y-%m-%d %H:%M:%S",
        "season": "season_id",
        "winner": {
            "result": "result",
            "translation": {
                "home": "home",
                "draw": "draw",
                "away": "away"
            }
        },
        "round": "day"
    }
)
# %% [markdown]
# ## Adding a trained ELO Rating

# %%
elo = ELORating(trained=True, param_k=20)
real_data_network.add_rating(rating=elo, rating_name="test_elo_rating")

# %%
for match in real_data_network.iterate_over_games():
    print(match)

# %%
