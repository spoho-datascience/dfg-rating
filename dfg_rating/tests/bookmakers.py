from dfg_rating.model.bookmaker.base_bookmaker import SimpleBookmaker, SimulatedBookmakerError, BookmakerMargin
from dfg_rating.model.forecast.base_forecast import SimpleForecast

b = SimpleBookmaker(
    SimulatedBookmakerError(error='uniform', low=0, high=1),
    BookmakerMargin(0.1)
)
true_forecast_probabilities = [0.4523, 0.2975, 0.2502]
print(f"True forecast {true_forecast_probabilities} = {sum(true_forecast_probabilities)}")

odds = b.get_odds(
    SimpleForecast(outcome=['home', 'draw', 'away'], probs=true_forecast_probabilities)
)
print(f"Bookmaker forecast {b.forecast.get_forecast()} = {sum(b.forecast.get_forecast())}")

print(f"Final odds {odds}")

