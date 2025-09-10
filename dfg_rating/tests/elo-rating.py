import itertools
from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.multiple_network import LeagueNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.ranking_rating import LeagueRating
from dfg_rating.model.rating.winner_rating import WinnerRating

rr_network = s = RoundRobinNetwork(
    teams=10,
    days_between_rounds=3
)


def season_filter(edge):
    return edge[3]["season"] == 0


games_by_round = {}
for k, g in itertools.groupby(filter(season_filter, rr_network.data.edges(keys=True, data=True)),
                              lambda x: x[3]['round']):
    games_by_round.setdefault(k, []).append(next(g))
print(games_by_round)
