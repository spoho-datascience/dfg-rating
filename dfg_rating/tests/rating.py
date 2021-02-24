from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.multiple_network import LeagueNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.ranking_rating import LeagueRating
from dfg_rating.model.rating.winner_rating import WinnerRating

rr_network = s = LeagueNetwork(
    teams=25,
    league_teams=20,
    league_promotion=3,
    days_between_rounds=3,
    seasons=2,
    create=True
)

tessted_rating = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='poisson', lam=100),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0)
)

tested_rating = LeagueRating()

def edge_fitler(e):
    return e[3]['round'] == 0

"""

fr = FunctionRating(
    distribution='normal',
    loc=100,
    scale=2
)
"""

rr_network.add_rating(tested_rating, 'test_rating')
rr_network.print_data(attributes=True, ratings=True)

