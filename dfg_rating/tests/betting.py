from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import SimpleBookmaker, SimulatedBookmakerError, BookmakerMargin
from dfg_rating.model.forecast.base_forecast import SimpleForecast

true_forecast_probabilities = [0.4523, 0.2975, 0.2501]
true_forecast = SimpleForecast('simple', ['home', 'draw', 'away'], true_forecast_probabilities)
model_forecast = true_forecast

bm = SimpleBookmaker(
    'simple',
    SimulatedBookmakerError(error=0.1),
    BookmakerMargin(0.1)
)

betting = FixedBetting(1000)
bets = betting.bet(
    model_forecast,
    bm.get_odds(true_forecast)
)

print(bets)
