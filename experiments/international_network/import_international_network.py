import os
import pandas as pd
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.rating.multi_mode_rating import ELORating
# from dfg_rating.model.rating.elo_rating import ELORating

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

elo_adding = ELORating(
    rating_name='elo_rating_adding',
    trained=True,
    rating_mode='keep',
    rating_mean=1000,
)

for s in international_network.get_seasons():
    ratings, player_dict = elo_adding.get_all_ratings(international_network, season=s)
    for t, t_i in player_dict.items():
        international_network._add_rating_to_team(t, ratings[t_i], {}, 'elo_rating_adding', season=s)

international_network.print_data(schedule=True)

international_network.export_international(data, printing_ratings=['elo_rating_adding'],export_file_name='test_InternationalLeague_network_import.csv')