from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.winner_rating import WinnerRating

print(">> Testing network module in Model package")
print(">> Testing Simple Network model")
network = s = RoundRobinNetwork(
    teams=4,
    days_between_rounds=3
)
print(">> Creating network")
s.create_data()
print(">> Printing network")

s.print_data(attributes=True, ratings=True, ratings_list=['true_rating'])
