from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import SimpleBookmaker, FactorBookmakerError, BookmakerMargin
from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.function_rating import FunctionRating

print(">> Pipeline start")
print(">> Testing Simple Network model")
s = RoundRobinNetwork(
    "type",
    {
        "number_of_teams": 6,
        "days_between_rounds": 3
    }
)
print(">> Creating network")
s.create_data()
print(">> Printing network")
s.print_data()
print(">> Creating true rating")
s.add_rating(FunctionRating('normal', 5, 1), 'normal')
print(">> Printing network")
s.print_data(print_schedule=False)
print(">> Creating simple True Forecast with predefined probabilities")
true_forecast = SimpleForecast('simple', ['home', 'draw', 'away'], [0.4523, 0.2975, 0.2501])
print(true_forecast.get_forecast())
print(">> Creating simple Model Forecast with equally distributed probabilities")
model_forecast = SimpleForecast('simple', ['home', 'draw', 'away'])
print(model_forecast.get_forecast())
print(">> Creating simple Bookmaker with factor error and margin")
b = SimpleBookmaker(
    'simple',
    FactorBookmakerError(error=0.1),
    BookmakerMargin(0.1)
)
print(">> Creating simple fixed betting")
betting = FixedBetting(1000)

print(">> Playing season")
s.play_data(true_forecast)
s.print_data(print_attributes=False)

print(">> Simulation:")
print("##########################################################")
init = True
current_round = None

for away_team, home_team, edge_attributes in s.iterate_over_games():
    if init:
        init = False
        current_round = edge_attributes['round']
        print(f"Round {current_round}")
    if current_round != edge_attributes['round']:
        current_round = edge_attributes['round']
        print("##########################################################")
        print(f"Round {current_round}")
    print(f"({away_team} -> {home_team}), winner = {edge_attributes['winner']}")
    print(f"True proabilities {true_forecast.get_forecast()}")
    print(f"Model probabilities {model_forecast.get_forecast()}")
    bm_odds = b.get_odds(true_forecast)
    print(f"Bookmaker odds {bm_odds}")
    print(f"Bets {betting.bet(model_forecast, bm_odds)}")

    print("--------------------------------------------------------------")
