import os
import pandas as pd

from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.network.multiple_network import LeagueNetwork

import dfg_rating.viz.jupyter_widgets as DFGWidgets

rr_network = LeagueNetwork(
    teams=4,
    seasons=7,
    league_teams=4,
    league_promotion=0,
    days_between_rounds=3,
    create=True
)
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
