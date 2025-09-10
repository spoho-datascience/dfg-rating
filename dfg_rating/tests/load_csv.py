import plotly.graph_objects as go
import pandas as pd
import networkx as nx
from datetime import date

from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.base_network import WhiteNetwork

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
# %%
white_network.add_forecast(SimpleForecast(outcomes=['home', 'draw', 'away'], probs=[0.45, 0.29, 0.26]), 'simple_forecast')
white_network.print_data(schedule=True, forecasts=True, forecasts_list=['simple_forecast'])