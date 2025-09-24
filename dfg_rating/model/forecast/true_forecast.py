from operator import indexOf

import numpy as np
import math

from dfg_rating.model.forecast.base_forecast import BaseForecast
from dfg_rating.model.rating.base_rating import RatingNullError


class LogFunctionForecast(BaseForecast):

    def __init__(self, **kwargs):
        super().__init__('logistic-function', **kwargs)
        self.coefficients = kwargs.get('coefficients')
        self.beta = kwargs.get('beta_parameter', 0.006)
        self.home_error = kwargs.get('home_team_error', RatingNullError())
        self.away_error = kwargs.get('away_team_error', RatingNullError())

    def get_forecast(self, match_data=None, home_team=None, away_team=None, base_ranking='true_rating', round_values=None):
        round_pointer = indexOf(round_values, match_data['round'])
        home_rating = home_team.get(
            'ratings', {}
        ).get(
            base_ranking, {}
        ).get(
            match_data['season'], []
        )[round_pointer]
        away_rating = away_team.get(
            'ratings', {}
        ).get(
            base_ranking, {}
        ).get(
            match_data['season'], []
        )[round_pointer]
        diff = self.home_error.apply(home_rating) - self.away_error.apply(away_rating)
        for i in range(len(self.outcomes)):
            n = len(self.outcomes)
            j = i + 1
            self.probabilities[i] = self.logit_link_function(
                outcome_number=n-j+1, covar=diff
            ) - self.logit_link_function(
                outcome_number=n-j, covar=diff
            )
        self.computed = True
        return self.probabilities

    def logit_link_function(self, outcome_number, covar):
        if outcome_number == 0:
            return 0
        if outcome_number == len(self.outcomes):
            return 1
        z = -(self.coefficients[outcome_number - 1]) + (self.beta * covar)
        f = 1 / (1 + np.exp(z))
        return f
    
#implementing a Bradley-Terry forecast, partly adopted from Hankin (2020), as an alternative true forecast
#The specific BT model is only applicable for three outcomes
class BradleyTerryForecast(BaseForecast):

    def __init__(self, **kwargs):
        super().__init__('bradley-terry', **kwargs)
        if(len(self.outcomes) != 3):
            raise Exception(f"Bradley-Terry not applicable if number of outcomes does not equal 3")
        self.exponent = kwargs.get('exponent', 10)
        self.ha = kwargs.get('ha', 100)
        self.home_error = kwargs.get('home_team_error', RatingNullError())
        self.away_error = kwargs.get('away_team_error', RatingNullError())

            

    def get_forecast(self, match_data=None, home_team=None, away_team=None, base_ranking='true_rating', round_values=None):
        round_pointer = indexOf(round_values, match_data['round'])
        home_rating = home_team.get(
            'ratings', {}
        ).get(
            base_ranking, {}
        ).get(
            match_data['season'], []
        )[round_pointer]
        away_rating = away_team.get(
            'ratings', {}
        ).get(
            base_ranking, {}
        ).get(
            match_data['season'], []
        )[round_pointer]
        #to ensure realistic probabilities, ratings need to be transformed
        home_rating_transformed = (home_rating+self.ha)**self.exponent
        away_rating_transformed = away_rating**self.exponent
        home_strength = home_rating_transformed / (home_rating_transformed + away_rating_transformed)
        away_strength = away_rating_transformed / (home_rating_transformed + away_rating_transformed)
        draw_strength = math.sqrt(home_strength * away_strength)

        self.probabilities[0] = home_strength/(home_strength + draw_strength + away_strength)
        self.probabilities[1] = draw_strength/(home_strength + draw_strength + away_strength)
        self.probabilities[2] = away_strength/(home_strength + draw_strength + away_strength)
        self.computed = True
        return self.probabilities



