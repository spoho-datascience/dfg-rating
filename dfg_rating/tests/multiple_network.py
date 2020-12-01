from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.multiple_network import LeagueNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.function_rating import FunctionRating

multiple_network = LeagueNetwork(
    teams=5,
    seasons=2,
    league_teams=4,
    league_promotion=1,
    days_between_rounds=3
)
multiple_network.create_data()
multiple_network.print_data(attributes=True, ratings=True, ratings_list=['true_rating'])
