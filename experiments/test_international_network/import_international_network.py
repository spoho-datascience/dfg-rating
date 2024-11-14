import os
import pandas as pd
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast

data = pd.read_csv('/home/haiyu/workspace/test_InternationalLeague_network.csv')

international_network = WhiteNetwork(
    data=data,
    mapping={
        "node1": {
            "id": "Away",
            "name": "Away",
            "ratings": {"true_rating": "true_rating#Away",
                        "ranking": "ranking#Away",
                        "elo_rating": "elo_rating#Away"},
        },
        "node2": {
            "id": "Home",
            "name": "Home",
            "ratings": {"true_rating": "true_rating#Home",
                        "ranking": "ranking#Home",
                        "elo_rating": "elo_rating#Home"},
        },
        "day": "Day",
        "dayIsTimestamp": False,
        "season": "Season",
        "result": "ResultFT",
        "round": "Round",
        "winner": {"result":"Result",
                   "translation": {"home": "Home", "draw": "Draw", "away": "Away"}},
        "odds": {},
        "forecasts": {},
        "odds": {},
        "bets": {}
    }
)

international_network.print_data(schedule=True)

international_network.add_forecast(
            forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[-1.0, 0.0], beta_parameter=0.006),
            forecast_name='player_forecast',
            base_ranking='true_rating'
            )