from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import SimpleBookmaker, BookmakerMargin

from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.forecast.forecast_error import ForecastSimulatedError, ForecastFactorError

true_forecast_probabilities = [0.4523, 0.2975, 0.2501]
true_forecast = SimpleForecast(outcomes=['home', 'draw', 'away'], probs=true_forecast_probabilities)
true_forecast.print()
model_forecast = true_forecast

forecast_error = ForecastFactorError(error=0.1, scope='positive')

bm = SimpleBookmaker(
    forecast_error,
    BookmakerMargin(0.1)
)

betting = FixedBetting(1000, forecast_error)

bookmaker_odds = bm.get_odds(true_forecast.get_forecast())
print(f"Bookmaker odds {bookmaker_odds}")
bets = betting.bet(
    model_forecast.get_forecast(),
    bookmaker_odds
)

print(f"Bets {bets}")
