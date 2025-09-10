from dfg_rating.model.bookmaker.base_bookmaker import SimpleBookmaker, SimulatedBookmakerError, BookmakerMargin
from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork

b = SimpleBookmaker(
    SimulatedBookmakerError(error='uniform', low=0, high=1),
    BookmakerMargin(0.1)
)
true_forecast_probabilities = [0.4523, 0.2975, 0.2502]

odds = b.get_odds(
    SimpleForecast(outcome=['home', 'draw', 'away'], probs=true_forecast_probabilities),
    None,
    None,
    None
)

rr_network = s = RoundRobinNetwork(
    teams=6,
    days_between_rounds=3
)
rr_network.create_data()
rr_network.play()

rr_network.add_odds('simple_bookmaker', b)




