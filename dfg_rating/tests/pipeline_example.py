from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import SimpleBookmaker, FactorBookmakerError, BookmakerMargin, \
    SimulatedBookmakerError
from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.winner_rating import WinnerRating

print(">> Pipeline start")
print(">> Testing Simple Network model")
s = RoundRobinNetwork(
    number_of_teams=6, days_between_rounds=3
)
print(">> Creating network")
s.create_data()
print(">> Printing network")
s.print_data(schedule=True)
print(">> Creating true rating")
s.add_rating(FunctionRating(rating_type='function', distribution='normal', loc=5, scale=1), 'True_rating')
s.print_data(attributes=True, ratings=True, ratings_list=['True_rating'])
true_forecast = SimpleForecast('simple', outcomes=['home', 'draw', 'away'], probs=[0.4523, 0.2975, 0.2502])
print(">> Adding simple forecast to the network and simulating observed results")
true_forecast.print()
s.add_forecast(true_forecast, 'true_forecast')
s.play()
s.print_data(schedule=True, winner=True)
print(">> Creating winner rating")
s.add_rating(WinnerRating('winner'), 'winner')
print(">> Printing network")
s.print_data(
    attributes=True, ratings=True, ratings_list=['winner', 'True_rating'], forecasts=True, forecasts_list=['true_forecast']
)
print(">> Creating simple Model Forecast with equally distributed probabilities")
model_forecast = SimpleForecast('simple', outcomes=['home', 'draw', 'away'])
model_forecast.print()
s.add_forecast(model_forecast, 'model_forecast')
print(">> Creating simple Bookmaker with factor error and margin")
b = SimpleBookmaker(
    'simple',
    SimulatedBookmakerError(error='uniform', low=0, high=1),
    BookmakerMargin(0.1)
)
print(">> Creating simple fixed betting")
betting = FixedBetting(1000)

print(">> Simulation:")
print("##########################################################")
init = True
current_round = None

for away_team, home_team, edge_key, edge_attributes in s.iterate_over_games():
    if init:
        init = False
        current_round = edge_attributes['round']
        print(f"Round {current_round}")
    if current_round != edge_attributes['round']:
        current_round = edge_attributes['round']
        print("##########################################################")
        print(f"Round {current_round}")
    print(f"({away_team} -> {home_team}), winner = {edge_attributes['winner']}")
    tf = edge_attributes['forecasts']['true_forecast']
    mf = edge_attributes['forecasts']['model_forecast']
    print(f"True probablities {tf.get_forecast()}")
    print(f"Model probabilities {mf.get_forecast()}")
    bm_odds = b.get_odds(tf)
    print(f"Bookmaker odds {bm_odds}")
    print(f"Bets {betting.bet(mf, bm_odds)}")
    print("--------------------------------------------------------------")
