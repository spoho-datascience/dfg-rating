from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.function_rating import FunctionRating

print(">> Testing network module in Model package")
print(">> Testing Simple Network model")
network = s = RoundRobinNetwork(
    "type",
    {
        "number_of_teams": 3,
        "days_between_rounds": 3
    }
)
print(">> Creating network")
s.create_data()
print(">> Printing network")
s.print_data()
true_forecast = SimpleForecast('simple', ['home', 'draw', 'away'], [0.4523, 0.2975, 0.2502])
s.play(true_forecast)
s.print_data()
"""print(">> Creating rating")
s.add_rating(FunctionRating('normal', 5, 1), 'normal')
print(">> Printing network")
s.print_data()"""