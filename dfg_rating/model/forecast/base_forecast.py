import numpy as np

from abc import ABC, abstractmethod
from typing import List


class BaseForecast(ABC):
    """Abstract class defining the interface of Forecast object.

    Attributes:
        type: Text descriptor of the forecast type.
        outcomes: List of outcomes.
    """

    def __init__(self, forecast_type: str, outcomes: List[str], probs: List[float] = None):
        self.type = forecast_type
        self.outcomes = outcomes
        number_of_outcomes = len(self.outcomes)
        self.probabilities = np.array(probs) if probs is not None else np.full(number_of_outcomes, float(1.0 / float(number_of_outcomes)))


    @abstractmethod
    def get_forecast(self, match=None):
        pass

    def print(self):
        forecast_string = ""
        for i in range(len(self.outcomes)):
            forecast_string += f" {self.outcomes[i]}: {self.probabilities[i]} -"
        forecast_string = forecast_string[:-1]
        print(forecast_string)


class SimpleForecast(BaseForecast):

    def get_forecast(self, match=None):
        return self.probabilities
