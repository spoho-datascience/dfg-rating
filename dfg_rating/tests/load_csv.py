import plotly.graph_objects as go
import pandas as pd
import networkx as nx
from datetime import date

from dfg_rating.model.network.base_network import WhiteNetwork

df = pd.read_csv('/home/marc/Development/dshs/dfg-rating/data/real/ATP_Network_2010_2019.csv')

# %%
white_network = WhiteNetwork(
    data=df,
    mapping={
        "node1": {
            "id": "WinnerID",
            "name": "Winner",
            "rankings": {
                "rank": "WRank",
                "Pts": "WPts"
            }
        },
        "node2": {
            "id": "LoserID",
            "name": "Loser",
            "rankings": {
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
# %%

white_network.print_data(attributes=True)