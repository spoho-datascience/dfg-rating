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
        print(f"Factor of the error: {error_factor}")
        true_probabilities = f.get_forecast()
        print(f"True probs {true_probabilities}")
        abs_error = error_factor * self.error
        if self.scope == "single":
            abs_error = abs(error_factor) * self.error
        applied_probabilities = abs_error + true_probabilities
        print(f"Error applied: {applied_probabilities}")
        return applied_probabilities / sum(applied_probabilities)


class SimulatedBookmakerError(BookmakerError):
    # TODO: Bettor error is assumed to be the same as the Bookmaker error

    def __init__(self, error: float):
        self.error = error
        self.bettor_error = error
        pass

    def apply(self, true_forecast: BaseForecast):
        p = true_forecast.get_forecast()
        logit_probs = np.log(p / (1 - p))
        correlation = 1.0
        covariance_reversed_diagonal = self.error * self.bettor_error * correlation
        bookmaker, bettor = np.random.multivariate_normal(
            mean=[0, 0],
            cov=[
                [np.square(self.error), covariance_reversed_diagonal],
                [covariance_reversed_diagonal, np.square(self.bettor_error)]
            ]
        )
        return 1 / (1 + (np.exp((-1 * logit_probs) + bookmaker)))


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
        print(f"Bookmaker forecast {self.forecast.get_forecast()}")
        odds = self.margin.apply(self.forecast)
        return odds
