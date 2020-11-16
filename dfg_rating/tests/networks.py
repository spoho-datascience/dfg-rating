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
s.print_data(schedule=True)
true_forecast = SimpleForecast(outcomes=['home', 'draw', 'away'], probs=[0.4523, 0.2975, 0.2502])
s.add_forecast(true_forecast, 'True')
s.play()
s.print_data(schedule=True, winner=True, forecasts=True, forecasts_list=['true_forecast'])
print(">> Creating winner rating")
s.add_rating(WinnerRating(), 'winner')

print(">> Creating True rating")
s.add_rating(FunctionRating(distribution='normal', loc=10, scale=1), 'True')
print(">> Printing network")
s.print_data(attributes=True, ratings=True, ratings_list=['winner', 'True'])
