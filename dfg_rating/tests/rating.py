from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.winner_rating import WinnerRating

rr_network = s = RoundRobinNetwork(
    "type",
    teams=5,
    days_between_rounds=3
)
rr_network.create_data()
rr_network.add_forecast(SimpleForecast('simple', outcomes=['home', 'draw', 'away']), 'True')
rr_network.play()

normal_rating = FunctionRating('function_rating', distribution='normal', loc=10, scale=1)
print(normal_rating.get_all_ratings(rr_network))

winner_rating = WinnerRating('winner_rating')
print(winner_rating.get_all_ratings(rr_network))
