import json
import os
import dash_cytoscape as cyto
import pandas as pd
import dfg_rating.viz.jupyter_widgets as DFGWidgets
from dfg_rating.logic import controller
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.network.multiple_network import LeagueNetwork
from dfg_rating.model.network.random_network import ConfigurationModelNetwork, ClusteredNetwork, RandomRoundsNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating

cyto.load_extra_layouts()
"""df = None
for file in [
    "bundesliga.json", "europaleague.json", "laliga.json", "premierleague.json", "championsleague.json"
]:
    with open(os.path.join(".", "RealData", file)) as json_file:
        raw_file_data = json.load(json_file)
        matches = raw_file_data.get('data', {}).get('row')
        print(f"Data with {len(matches)} edges")
        if df is None:
            df = pd.DataFrame(matches)
        else:
            new_df = pd.DataFrame(matches)
            df = pd.concat([df, new_df])
"""

mc = controller.Controller()
"""mc.load_network_from_tabular(
    network_name='tennis_full',
    file_path='./RealData/atp_2019.csv',
    new_mapping='atp'
)"""
"""mc.load_network_from_tabular(
    network_name="football_national",
    file_path="./RealData/Data_Football_National.csv",
    new_mapping="soccer",
    delimiter=";",
)
loaded_network = mc.networks["football_national"]"""

"""loaded_network = LeagueNetwork(
    teams=6,
    days_between_rounds=3,
    seasons=1,
    league_teams=6,
    league_promotion=0,
    create=True
)"""
"""data_football_national = pd.read_csv(os.path.join('..', '..', '..', 'data', 'real', 'Data_Football_National.csv'),sep = ";")
loaded_network = WhiteNetwork(
    data=data_football_national,
    #node1 = away
    mapping={
        "node1": {
            "id": "AwayID",
            "name": "AwayTeam",
        },
        "node2": {
            "id": "HomeID",
            "name": "HomeTeam",
        },
        "day": "Date",
        "dayIsTimestamp": True,
        "ts_format": "%d.%m.%Y",
        "tournament": "Div",
        "season": "Season",
        "winner": {
            "result": "ResultFT",
            "translation": {
                "H": "home",
                "D": "draw",
                "A": "away"
            }
        },
        "round": "day",
        "odds": {
            "maximumodds": {
                "home": "OddsHomeMax",
                "draw": "OddsDrawMax",
                "away": "OddsAwayMax"
            },
            "averageodds": {
                "home": "OddsHomeAvg",
                "draw": "OddsDrawAvg",
                "away": "OddsAwayAvg"
            },
        },
        "bets": {}
    }
)"""

"""loaded_network = ConfigurationModelNetwork(
    teams=20,
    days_between_rounds=3,
    expected_matches=5,
    variance_matches=0
)"""
"""import math
rounds = 6
number_of_nodes = int(
    math.ceil(
        (rounds / (2 * 0.1)) + 1
    )
)
print(number_of_nodes)
loaded_network = RandomRoundsNetwork(
    teams=number_of_nodes,
    absolute_rounds=rounds
)"""
loaded_network = ClusteredNetwork(
    teams=60,
    clusters=3,
    out_probability=0.9
)
import random
import numpy as np

random.seed(1234)
np.random.seed(1234)

"""loaded_network = LeagueNetwork(
    teams=20,
    days_between_rounds=3,
    seasons=4,
    league_teams=20,
    league_promotion=0,
    create=True
)
print(loaded_network.data.nodes[2])"""
"""loaded_network = ConfigurationModelNetwork(
    teams=20,
    days_between_rounds=3,
    expected_matches=15,
    variance_matches=15
)"""

"""tested_rating = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=200),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=75),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
)"""
#elo_rating = ELORating(trained=True, rating_name="Added_elo_rating")
#loaded_network.add_rating(elo_rating, "Added_elo_rating")
#loaded_network.add_rating(tested_rating, "Added_true_rating")

"""loaded_network.add_forecast(
    forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[-0.9, 0.3], beta_parameter=0.006),
    forecast_name='player_forecast',
    base_ranking='Added_elo_rating'
)
"""
app = DFGWidgets.NetworkExplorer(
    network=loaded_network,
    edge_props=["round"]
)
app.run('internal', debug=True, port=8001)
