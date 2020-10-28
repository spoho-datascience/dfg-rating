from dfg_rating.model.bookmaker.base_bookmaker import SimpleBookmaker, SimulatedBookmakerError, BookmakerMargin
from dfg_rating.model.forecast.base_forecast import SimpleForecast

b = SimpleBookmaker(
    'simple',
    SimulatedBookmakerError(error=0.1),
    BookmakerMargin(0.1)
)
true_forecast_probabilities = [0.4523, 0.2975, 0.2501]
print(f"True forecast {true_forecast_probabilities}")
odds = b.get_odds(
    SimpleForecast('simple', ['home', 'draw', 'away'], true_forecast_probabilities)
)

print(f"Final odds {odds}")
