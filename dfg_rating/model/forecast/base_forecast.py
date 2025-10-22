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
        self.probabilities = np.array(probs) if probs is not None \
            else np.full(number_of_outcomes, float(1.0 / float(number_of_outcomes)))
        if self.probabilities.sum() < 0.99995:
            print(f"Warning: Forecast probabilities should sum 1 {self.probabilities}")


    @abstractmethod
    def get_forecast(self, match_data=None, home_team=None, away_team=None, base_ranking='true_rating', round_values=None):
        pass

    @abstractmethod
    def get_forecast_from_ratings(self, home_rating, away_rating):
        """
        use the existing rating to calculate forecast
        
        for CountryLeague and InternationalCompetition， where the national/international matches are not played 
        at the same time as the league matches (have ratings at that day/round), so the ratings are pre-requested with
        the function get_avaliable_rating().
        
        Args:
            home_rating
            away_rating
            
        Returns:
            self.outcomes
        """
        pass

    def print(self):
        forecast_string = ""
        for i in range(len(self.outcomes)):
            forecast_string += f" {self.outcomes[i][0]}: {self.probabilities[i]:.2f} -"
        forecast_string = forecast_string[:-1]
        return forecast_string


class SimpleForecast(BaseForecast):

    def __init__(self, **kwargs):
        super().__init__('simple', **kwargs)
        self.computed = True

    def get_forecast(self, match_data=None, home_team=None, away_team=None, base_ranking='true_forecast', round_values=None):
        return self.probabilities
    
    def get_forecast_from_ratings(self, home_rating, away_rating):
        return self.probabilities
