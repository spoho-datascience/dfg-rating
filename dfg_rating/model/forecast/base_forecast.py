import numpy as np

from abc import ABC, abstractmethod


class BaseForecast(ABC):
    """Abstract class defining the interface of Forecast object.

    Attributes:
        type: Text descriptor of the forecast type.
        outcomes: List of outcomes.
    """

    def __init__(self, forecast_type: str, **kwargs):
        self.computed = False
        self.type = forecast_type
        self.outcomes = kwargs.get('outcomes', [])
        number_of_outcomes = len(self.outcomes)
        probs = kwargs.get('probs', None)
        self.probabilities = np.array(probs) if probs is not None else np.full(number_of_outcomes, float(1.0 / float(number_of_outcomes)))


    @abstractmethod
    def get_forecast(self, match_data=None, home_team=None, away_team=None):
        pass

    def print(self):
        if not self.computed:
            self.get_forecast()
        forecast_string = ""
        for i in range(len(self.outcomes)):
            forecast_string += f" {self.outcomes[i]}: {self.probabilities[i]} -"
        forecast_string = forecast_string[:-1]
        return forecast_string


class SimpleForecast(BaseForecast):

    def __init__(self, **kwargs):
        super().__init__('simple', **kwargs)
        self.computed = True

    def get_forecast(self, match_data=None, home_team=None, away_team=None):
        return self.probabilities
