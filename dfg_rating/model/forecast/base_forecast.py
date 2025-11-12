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
    def get_forecast(self, match_data=None, home_team=None, away_team=None, base_ranking='true_rating', 
                     round_values=None, home_rating=None, away_rating=None):
        """
        calculate forecast probabilities.
        
        work in two ways:
        1. simple networks: provide match_data, home_team, away_team to retrieve ratings internally
        2. countryLeague/InternationalCompetition: provide pre-fetched home_rating 
           and away_rating via get_available_rating()
        
        args:
            match_data: Match information dict
            home_team: Home team dict
            away_team: Away team dict
            base_ranking: Rating key to use
            round_values: List of round values
            home_rating: Pre-fetched home team rating (for country/international networks)
            away_rating: Pre-fetched away team rating (for country/international networks)

        returns:
            [probabilities of home win, draw, away win]
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

    def get_forecast(self, match_data=None, home_team=None, away_team=None, base_ranking='true_forecast', 
                     round_values=None, home_rating=None, away_rating=None):
        return self.probabilities
