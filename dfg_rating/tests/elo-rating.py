from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.multiple_network import LeagueNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.ranking_rating import LeagueRating
from dfg_rating.model.rating.winner_rating import WinnerRating

rr_network = s = LeagueNetwork(
    teams=18,
    league_teams=18,
    league_promotion=0,
    days_between_rounds=3,
    seasons=2,
    create=True
)

tested_rating = ELORating(trained=True)

rr_network.add_rating(tested_rating, "elo_rating")

for team in rr_network.data.nodes:
    print(rr_network.data.nodes[team]['ratings']['elo_rating'])

