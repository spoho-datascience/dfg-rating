from operator import indexOf

import numpy as np

from dfg_rating.model.forecast.base_forecast import BaseForecast
from dfg_rating.model.rating.base_rating import RatingNullError


class LogFunctionForecast(BaseForecast):

    def __init__(self, **kwargs):
        super().__init__('logistic-function', **kwargs)
        self.coefficients = kwargs.get('coefficients')
        self.beta = kwargs.get('beta_parameter', 0.006)
        self.home_error = kwargs.get('home_team_error', RatingNullError())
        self.away_error = kwargs.get('away_team_error', RatingNullError())

    def get_forecast(self, match_data=None, home_team=None, away_team=None, base_ranking='true_rating', round_values=None, use_player_rating=False):
        round_pointer = indexOf(round_values, match_data['round'])
        if use_player_rating:
            if len(match_data['home_player_prev_ratings']) > 0:
                starting_home = np.asarray(match_data['lineup']['home']['starting'], dtype=bool)
                starting_away = np.asarray(match_data['lineup']['away']['starting'], dtype=bool)
                home_player_ratings = np.asarray(match_data['home_player_prev_ratings'], dtype=float)
                away_player_ratings = np.asarray(match_data['away_player_prev_ratings'], dtype=float)
                home_rating = np.mean(home_player_ratings[starting_home])
                away_rating = np.mean(away_player_ratings[starting_away])
            else:
                self.probabilities = np.array([np.nan, np.nan, np.nan])
                return self.probabilities
        else:
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

