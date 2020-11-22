from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction


rr_network = s = RoundRobinNetwork(
    teams=6,
    days_between_rounds=3
)
rr_network.create_data()
rr_network.add_forecast(SimpleForecast(outcomes=['home', 'draw', 'away']), 'true_forecast')
rr_network.play()

tested_rating = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=200),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=75),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
)


def edge_fitler(e):
    return e[3]['round'] == 0


print(tested_rating.get_all_ratings(rr_network))
