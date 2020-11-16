from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.winner_rating import WinnerRating

rr_network = s = RoundRobinNetwork(
    teams=5,
    days_between_rounds=3
)
rr_network.create_data()
rr_network.add_forecast(SimpleForecast(outcomes=['home', 'draw', 'away']), 'true_forecast')
rr_network.play()

normal_rating = FunctionRating(distribution='normal', loc=10, scale=1)


def edge_fitler(e):
    return e[3]['round'] == 0


print(normal_rating.get_all_ratings(rr_network, edge_fitler))
print('---')
print(normal_rating.get_all_ratings(rr_network))

winner_rating = WinnerRating()
print(winner_rating.get_all_ratings(rr_network))
