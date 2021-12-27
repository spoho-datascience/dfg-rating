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
    "eurocup.json"
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
mc.load_network_from_tabular(
    network_name="football_national",
    file_path="./RealData/Data_Football_National.csv",
    new_mapping="soccer",
    delimiter=";",
)
loaded_network = mc.networks["football_national"]

"""created_network = LeagueNetwork(
    teams=20,
    days_between_rounds=3,
    seasons=4,
    league_teams=20,
    league_promotion=0,
    create=True
)"""

"""loaded_network = WhiteNetwork(
    data=df,
    mapping={
        "node1": {
            "id": "team2_id",
            "name": "team2_name"
        },
        "node2": {
            "id": "team1_id",
            "name": "team1_name"
        },
        "day": "match_date",
        "dayIsTimestamp": True,
        "ts_format": "%Y-%m-%d %H:%M:%S",
        "round": "round_name",
        "season": "tournament_name"
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
"""loaded_network = ClusteredNetwork(
    teams=40,
    clusters=10,
    out_probability=0.01
)"""
"""import random
import numpy as np

random.seed(1234)
np.random.seed(1234)

loaded_network = LeagueNetwork(
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

tested_rating = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=200),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=75),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
)
elo_rating = ELORating(trained=True, rating_name="Added_elo_rating")
loaded_network.add_rating(elo_rating, "Added_elo_rating")
#loaded_network.add_rating(tested_rating, "Added_true_rating")

loaded_network.add_forecast(
    forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[-1.2, 0.0], beta_parameter=0.006),
    forecast_name='player_forecast',
    base_ranking='Added_elo_rating'
)

print("Done")

app = DFGWidgets.RatingsExplorer(
    network=loaded_network,
    edge_props=["round"],
    offline=True
)
app.run('internal', debug=True, port=8001)
