import numpy as np
from sklearn.preprocessing import normalize
from abc import ABC, abstractmethod

from dfg_rating.model.forecast.base_forecast import BaseForecast, SimpleForecast
from dfg_rating.model.forecast.forecast_error import ForecastError, ForecastNullError


class BookmakerMargin:

    def __init__(self, margin):
        self.margin = margin

    def apply(self, forecast_probabilities):
        raw_odds = (1 / forecast_probabilities) * (1 - self.margin)
        return np.maximum(np.full_like(raw_odds, 1), (1 / forecast_probabilities) * (1 - self.margin))


# Bookmaker implementation
class BaseBookmaker(ABC):
    """Abstract class defining the interface of a Bookmaker object

    Attributes:
        type: Text descriptor of the forecast type.
        error: Bookmaker error.
        margin: Bookmaker margin.
    """

    def __init__(self, bookmaker_type: str, error: ForecastError, margin: BookmakerMargin, **kwargs):
        self.type = bookmaker_type
        self.error = error if error is not None else ForecastNullError()
        self.margin = margin

    @abstractmethod
    def _compute_forecast(self, base_probabilities):
        pass

    @abstractmethod
    def _compute_odds(self):
        pass

    def get_odds(self, true_probs):
        self._compute_forecast(true_probs)
        return self._compute_odds()


class SimpleBookmaker(BaseBookmaker):

    def __init__(self, error: ForecastError, margin: BookmakerMargin, **kwargs):
        super().__init__('simple', error, margin, **kwargs)

    def _compute_forecast(self, true_probs):
        self.forecast = self.error.apply(true_probs)

    def _compute_odds(self):
        odds = self.margin.apply(self.forecast)
        return odds
