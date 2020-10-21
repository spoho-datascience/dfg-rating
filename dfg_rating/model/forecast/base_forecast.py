import numpy as np

from abc import ABC, abstractmethod
from typing import List

from dfg_rating.model.network.base_network import BaseNetwork


class BaseForecast(ABC):
    """Abstract class defining the interface of Forecast object.

    Attributes:
        type: Text descriptor of the forecast type.
        outcomes: List of outcomes.
    """

    def __init__(self, forecast_type: str, outcomes: List[str], probs: List[float] = None):
        self.type = type
        self.outcomes = outcomes
        self.probabilities = probs

    @abstractmethod
    def get_forecast(self, match=None):
        pass



class SimpleForecast(BaseForecast):

    def get_forecast(self, match=None):
        number_of_outcomes = len(self.outcomes)
        self.probabilities = self.probabilities or np.full(number_of_outcomes, float(1.0/float(number_of_outcomes)))
        return self.probabilities
