import numpy as np
import random
from sklearn.preprocessing import normalize
from abc import ABC, abstractmethod

from dfg_rating.model.forecast.base_forecast import BaseForecast, SimpleForecast


# Types of Bookmaker errors
class BookmakerError:

    def apply(self, f: BaseForecast):
        pass


class FactorBookmakerError(BookmakerError):

    def __init__(self, error: float, scope: str = None):
        self.type = 'PercentageBookmakerError'
        self.error = error
        self.scope = scope

    def apply(self, f: BaseForecast):
        error_factor = random.uniform(-1.0, 1.0)
        true_probabilities = f.get_forecast()
        abs_error = error_factor * self.error
        if self.scope == "single":
            abs_error = abs(error_factor) * self.error
        applied_probabilities = abs_error + true_probabilities
        return applied_probabilities / sum(applied_probabilities)


class SimulatedBookmakerError(BookmakerError):
    # TODO: Bettor error is assumed to be the same as the Bookmaker error

    def __init__(self, error: str, *args):
        try:
            self.error_method = getattr(np.random.default_rng(), error)
        except AttributeError as attr:
            print("Error method not available")
            return
        self.error_arguments = []
        for arg in args:
            self.error_arguments.append(arg)

    def apply(self, true_forecast: BaseForecast):
        p = true_forecast.get_forecast()
        logit_probs = np.log(p / (1 - p))
        error = self.error_method(*(self.error_arguments + [len(logit_probs)]))
        final_probs = 1 / (1 + (np.exp((-1 * (logit_probs + error)))))
        return final_probs / sum(final_probs)


# Types of Bookmaker marking
class BookmakerMargin:

    def __init__(self, margin):
        self.margin = margin

    def apply(self, f: BaseForecast):
        return (1 / f.get_forecast()) + (1 - self.margin)


# Bookmaker implementation
class BaseBookmaker(ABC):
    """Abstract class defining the interface of a Bookmaker object

    Attributes:
        type: Text descriptor of the forecast type.
        error: Bookmaker error.
        margin: Bookmaker margin.
    """

    def __init__(self, bookmaker_type: str, error: BookmakerError, margin: BookmakerMargin):
        self.type = bookmaker_type
        self.error = error
        self.margin = margin

    @abstractmethod
    def _compute_forecast(self, true_forecast: BaseForecast):
        pass

    @abstractmethod
    def _compute_odds(self):
        pass

    def get_odds(self, true_forecast: BaseForecast):
        self._compute_forecast(true_forecast)
        return self._compute_odds()


class SimpleBookmaker(BaseBookmaker):

    def _compute_forecast(self, true_forecast: BaseForecast):
        self.forecast = SimpleForecast('simple', true_forecast.outcomes, self.error.apply(true_forecast))
        pass

    def _compute_odds(self):
        odds = self.margin.apply(self.forecast)
        return odds
