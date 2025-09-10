import os
import pandas as pd

from dfg_rating.model.evaluators.accuracy import RankProbabilityScore
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.base_network import BaseNetwork, WhiteNetwork

from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating


# Reading the data into a Pandas DataFrame
data_folder = os.environ['DATA_FOLDER']
training_df = pd.read_csv(os.path.join(data_folder, 'real', 'all_seasons.csv'))

# Uploading the data into a basic network
matches_network = WhiteNetwork(
    data=training_df[training_df['Lge'] == 'SPA1'],
    mapping={
        #Away team is the source of the edge
        "node1": {
            "id": "AT",
            "name": "AT",
        },
        #Home team is the target of the edge
        "node2": {
            "id": "HT",
            "name": "HT",
        },
        "day": "Date",
        "dayIsTimestamp": True,
        "ts_format": "%d/%m/%Y",
        "season": "Sea",
        "tournament": "Lge",
        "winner": {
            "result": "WDL",
            "translation": {
                "W": "home",
                "D": "draw",
                "L": "away"
            }
        },
        "round": "day",
        "odds": {},
        "bets": {}
    }
)

elo = ELORating(
    trained=True,
    rating_name="elo_rating_trained"
)
elo_forecast = LogFunctionForecast(
    outcomes=['home', 'draw', 'away'],
    coefficients=[-0.9, 0.3],
    beta_parameter=0.006
)
rps = RankProbabilityScore(
    outcomes=['home', 'draw', 'away'],
    forecast_name='elo_forecast'
)

matches_network.add_rating(rating=elo, rating_name='elo_rating_trained')
matches_network.add_forecast(forecast=elo_forecast, forecast_name='elo_forecast', base_ranking="elo_rating_trained")
matches_network.add_evaluation([(rps, "elo_rating_trained")])


import dfg_rating.viz.jupyter_widgets as DFGViz

# app_forecast = DFGViz.ForecastExplorer(
#     network=matches_network,
#     ratings=["elo_rating_trained"]
# )

# app_forecast.run('external')

app_ratings = DFGViz.RatingsEvaluation(network=matches_network)
app_ratings.run('external')

